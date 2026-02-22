import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKENINGIZNI_QOYING")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8537782289"))

API_URL = os.getenv("API_URL", "https://saleseen.uz/api/v2")
API_KEY = os.getenv("API_KEY", "API_KEYINGIZ")

DB_PATH = os.getenv("DB_PATH", "db.sqlite")
ORDER_STATUS_POLL_SECONDS = int(os.getenv("ORDER_STATUS_POLL_SECONDS", "90"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

# =========================
# DB LAYER (sqlite3 + asyncio.to_thread)
# =========================
class DB:
    def __init__(self, path: str):
        self.path = path
        self._lock = asyncio.Lock()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    async def init(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            balance REAL DEFAULT 0,
            referal_from INTEGER,
            created_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            api_id TEXT NOT NULL,
            base_price REAL NOT NULL,
            percent REAL DEFAULT 0
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            number TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS topups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            receipt_file_id TEXT NOT NULL,
            status TEXT NOT NULL,              -- pending/approved/rejected
            created_at TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            api_order_id TEXT,
            quantity INTEGER NOT NULL,
            link TEXT NOT NULL,
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,              -- sent/processing/completed/canceled/partial/error
            created_at TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    async def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> None:
        async with self._lock:
            await asyncio.to_thread(self._execute_sync, sql, params)

    def _execute_sync(self, sql: str, params: Tuple[Any, ...]) -> None:
        conn = self._connect()
        conn.execute(sql, params)
        conn.commit()
        conn.close()

    async def fetchone(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        async with self._lock:
            return await asyncio.to_thread(self._fetchone_sync, sql, params)

    def _fetchone_sync(self, sql: str, params: Tuple[Any, ...]) -> Optional[sqlite3.Row]:
        conn = self._connect()
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        return row

    async def fetchall(self, sql: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        async with self._lock:
            return await asyncio.to_thread(self._fetchall_sync, sql, params)

    def _fetchall_sync(self, sql: str, params: Tuple[Any, ...]) -> List[sqlite3.Row]:
        conn = self._connect()
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return rows

db = DB(DB_PATH)

# =========================
# HELPERS
# =========================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def cb(*parts: str) -> str:
    return "|".join(parts)[:64]

def money(x: float) -> str:
    try:
        v = float(x)
    except:
        return str(x)
    if v.is_integer():
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ")

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# =========================
# API CLIENT
# =========================
class PanelAPI:
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key

    async def _post(self, payload: Dict[str, Any]) -> Any:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.url, data=payload) as resp:
                ct = resp.headers.get("Content-Type", "")
                if "application/json" in ct:
                    return await resp.json()
                text = await resp.text()
                try:
                    import json
                    return json.loads(text)
                except:
                    return {"raw": text}

    async def services(self) -> Any:
        return await self._post({"key": self.key, "action": "services"})

    async def add_order(self, service_api_id: str, link: str, quantity: int) -> Any:
        return await self._post({
            "key": self.key,
            "action": "add",
            "service": service_api_id,
            "link": link,
            "quantity": quantity
        })

    async def status(self, api_order_id: str) -> Any:
        return await self._post({"key": self.key, "action": "status", "order": api_order_id})

api = PanelAPI(API_URL, API_KEY)

# =========================
# FSM STATES
# =========================
class AdminAddService(StatesGroup):
    category = State()
    name = State()
    api_id = State()
    base_price = State()

class AdminAddPercent(StatesGroup):
    service_id = State()
    percent = State()

class AdminAddCard(StatesGroup):
    name = State()
    number = State()

class AdminAddBalance(StatesGroup):
    user_id = State()
    amount = State()

class UserOrder(StatesGroup):
    service_id = State()
    quantity = State()
    link = State()

class UserTopup(StatesGroup):
    amount = State()
    receipt = State()

# =========================
# MENUS
# =========================
def kb_user() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="💰 Hisobim")],
            [KeyboardButton(text="💳 Hisob to‘ldirish"), KeyboardButton(text="🛒 Buyurtmalarim")],
            [KeyboardButton(text="👥 Referal"), KeyboardButton(text="☎ Yordam")],
        ],
        resize_keyboard=True
    )

def kb_admin() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Xizmat qo‘shish"), KeyboardButton(text="❌ Xizmat o‘chirish")],
            [KeyboardButton(text="💹 Foiz qo‘shish"), KeyboardButton(text="💳 Karta qo‘shish")],
            [KeyboardButton(text="➕ Balans qo‘shish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="⬅ Ortga")],
        ],
        resize_keyboard=True
    )

# =========================
# BOT INIT
# =========================
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# =========================
# START / ADMIN
# =========================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    ref = None
    parts = message.text.split(maxsplit=1)
    if len(parts) == 2:
        try:
            ref = int(parts[1])
        except:
            ref = None

    await db.execute(
        "INSERT OR IGNORE INTO users(user_id, full_name, balance, referal_from, created_at) VALUES(?,?,?,?,?)",
        (message.from_user.id, message.from_user.full_name, 0.0, ref, now_str())
    )
    await message.answer("Assalomu alaykum 👋", reply_markup=kb_user())

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ Siz admin emassiz.")
    await message.answer("👑 Admin panel", reply_markup=kb_admin())

@dp.message(F.text == "⬅ Ortga")
async def back_to_user(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu", reply_markup=kb_user())

# =========================
# USER: BALANCE / REFERAL / HELP
# =========================
@dp.message(F.text == "💰 Hisobim")
async def my_balance(message: types.Message):
    row = await db.fetchone("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = float(row["balance"]) if row else 0.0
    await message.answer(f"💰 Balansingiz: <b>{money(bal)}</b> so‘m")

@dp.message(F.text == "👥 Referal")
async def referal(message: types.Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={message.from_user.id}"
    await message.answer(f"👥 Referal link:\n<code>{link}</code>")

@dp.message(F.text == "☎ Yordam")
async def help_msg(message: types.Message):
    await message.answer(
        "☎ Yordam:\n"
        "🛍 Xizmatlar — xizmat tanlash\n"
        "💰 Hisobim — balans\n"
        "💳 Hisob to‘ldirish — chek yuborish\n"
        "🛒 Buyurtmalarim — buyurtmalar\n\n"
        "Admin: /admin"
    )

# =========================
# ADMIN: CARD ADD
# =========================
@dp.message(F.text == "💳 Karta qo‘shish")
async def admin_add_card(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Karta nomi (HUMO/UZCARD):")
    await state.set_state(AdminAddCard.name)

@dp.message(AdminAddCard.name)
async def admin_add_card_2(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Karta raqami:")
    await state.set_state(AdminAddCard.number)

@dp.message(AdminAddCard.number)
async def admin_add_card_3(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    number = message.text.strip()
    try:
        await db.execute("INSERT INTO cards(name, number) VALUES(?,?)", (name, number))
        await message.answer(f"✅ Karta qo‘shildi: <b>{name}</b>\n<code>{number}</code>")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    await state.clear()

# =========================
# ADMIN: SERVICE ADD
# =========================
@dp.message(F.text == "➕ Xizmat qo‘shish")
async def admin_add_service(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Kategoriya (Telegram/Instagram/YouTube/TikTok):")
    await state.set_state(AdminAddService.category)

@dp.message(AdminAddService.category)
async def admin_add_service_2(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer("Xizmat nomi:")
    await state.set_state(AdminAddService.name)

@dp.message(AdminAddService.name)
async def admin_add_service_3(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("API Service ID:")
    await state.set_state(AdminAddService.api_id)

@dp.message(AdminAddService.api_id)
async def admin_add_service_4(message: types.Message, state: FSMContext):
    api_id = message.text.strip()
    # paneldan tekshirish (ixtiyoriy)
    try:
        all_services = await api.services()
        found = None
        if isinstance(all_services, list):
            for s in all_services:
                if str(s.get("service")) == str(api_id):
                    found = s
                    break
        if not found:
            await message.answer("❌ Panelda bunday Service ID topilmadi. Qaytadan kiriting:")
            return
    except Exception as e:
        await message.answer(f"⚠️ Panel tekshiruvida xato: {e}\nDavom etamiz...")

    await state.update_data(api_id=api_id)
    await message.answer("Bazaviy narx (1 dona uchun):")
    await state.set_state(AdminAddService.base_price)

@dp.message(AdminAddService.base_price)
async def admin_add_service_5(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        base_price = float(message.text.replace(",", "."))
    except:
        return await message.answer("❌ Narx raqam bo‘lsin. Qayta kiriting:")

    await db.execute(
        "INSERT INTO services(category, name, api_id, base_price, percent) VALUES(?,?,?,?,?)",
        (data["category"], data["name"], data["api_id"], base_price, 0.0)
    )
    await message.answer("✅ Xizmat qo‘shildi.")
    await state.clear()

# =========================
# ADMIN: SERVICE DELETE
# =========================
@dp.message(F.text == "❌ Xizmat o‘chirish")
async def admin_delete_service_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    rows = await db.fetchall("SELECT id, category, name FROM services ORDER BY id DESC")
    if not rows:
        return await message.answer("Hali xizmat yo‘q.")

    kb = []
    for r in rows[:50]:
        kb.append([InlineKeyboardButton(
            text=f"{r['category']} • {r['name']}",
            callback_data=cb("svc_del", str(r["id"]))
        )])
    await message.answer("O‘chirmoqchi bo‘lgan xizmatni tanlang:",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("svc_del|"))
async def admin_delete_service(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Admin emas!", show_alert=True)
    _, sid = callback.data.split("|", 1)
    await db.execute("DELETE FROM services WHERE id=?", (int(sid),))
    await callback.message.edit_text("✅ O‘chirildi.")
    await callback.answer()

# =========================
# ADMIN: PERCENT
# =========================
@dp.message(F.text == "💹 Foiz qo‘shish")
async def admin_percent_menu(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    rows = await db.fetchall("SELECT id, name, percent FROM services ORDER BY id DESC")
    if not rows:
        return await message.answer("Xizmat yo‘q.")

    kb = []
    for r in rows[:50]:
        kb.append([InlineKeyboardButton(
            text=f"{r['name']} ({r['percent']}%)",
            callback_data=cb("pct_pick", str(r["id"]))
        )])
    await message.answer("Foiz qo‘shiladigan xizmatni tanlang:",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("pct_pick|"))
async def admin_percent_pick(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Admin emas!", show_alert=True)
    _, sid = callback.data.split("|", 1)
    await state.update_data(service_id=int(sid))
    await callback.message.answer("Necha % qo‘shamiz? (masalan: 10)")
    await state.set_state(AdminAddPercent.percent)
    await callback.answer()

@dp.message(AdminAddPercent.percent)
async def admin_percent_apply(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        pct = float(message.text.replace(",", "."))
    except:
        return await message.answer("❌ Foiz raqam bo‘lsin. Qayta kiriting:")

    data = await state.get_data()
    sid = int(data["service_id"])
    await db.execute("UPDATE services SET percent=? WHERE id=?", (pct, sid))
    await message.answer("✅ Foiz saqlandi.")
    await state.clear()

# =========================
# ADMIN: ADD BALANCE
# =========================
@dp.message(F.text == "➕ Balans qo‘shish")
async def admin_add_balance_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("User ID kiriting:")
    await state.set_state(AdminAddBalance.user_id)

@dp.message(AdminAddBalance.user_id)
async def admin_add_balance_2(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except:
        return await message.answer("❌ User ID raqam bo‘lsin.")
    await state.update_data(user_id=uid)
    await message.answer("Qancha qo‘shamiz? (so‘m):")
    await state.set_state(AdminAddBalance.amount)

@dp.message(AdminAddBalance.amount)
async def admin_add_balance_3(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = int(data["user_id"])
    try:
        amount = float(message.text.replace(",", "."))
    except:
        return await message.answer("❌ Raqam kiriting.")

    row = await db.fetchone("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not row:
        await message.answer("❌ Bunday user topilmadi.")
        await state.clear()
        return

    await db.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    await message.answer("✅ Qo‘shildi.")
    try:
        await bot.send_message(uid, f"✅ Hisobingizga <b>{money(amount)}</b> so‘m qo‘shildi.")
    except:
        pass
    await state.clear()

# =========================
# USER: SHOW SERVICES (category)
# =========================
@dp.message(F.text == "🛍 Xizmatlar")
async def user_services(message: types.Message):
    rows = await db.fetchall("SELECT DISTINCT category FROM services ORDER BY category")
    if not rows:
        return await message.answer("❌ Hali xizmatlar yo‘q.")
    kb = [[InlineKeyboardButton(text=r["category"], callback_data=cb("cat", r["category"]))] for r in rows]
    await message.answer("Kategoriya tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("cat|"))
async def user_services_by_cat(callback: types.CallbackQuery):
    _, category = callback.data.split("|", 1)
    rows = await db.fetchall(
        "SELECT id, name, base_price, percent FROM services WHERE category=? ORDER BY id DESC",
        (category,)
    )
    if not rows:
        await callback.message.edit_text("Bu kategoriyada xizmat yo‘q.")
        return await callback.answer()

    kb = []
    for r in rows[:50]:
        price = float(r["base_price"]) * (1 + float(r["percent"]) / 100.0)
        kb.append([InlineKeyboardButton(
            text=f"{r['name']} — {money(price)}",
            callback_data=cb("ord_pick", str(r["id"]))
        )])

    await callback.message.edit_text("Xizmat tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()

# =========================
# USER: ORDER FLOW
# =========================
@dp.callback_query(F.data.startswith("ord_pick|"))
async def user_order_pick(callback: types.CallbackQuery, state: FSMContext):
    _, sid = callback.data.split("|", 1)
    await state.update_data(service_id=int(sid))
    await callback.message.answer("Miqdor kiriting (quantity):")
    await state.set_state(UserOrder.quantity)
    await callback.answer()

@dp.message(UserOrder.quantity)
async def user_order_qty(message: types.Message, state: FSMContext):
    try:
        qty = int(message.text.strip())
        if qty <= 0:
            raise ValueError()
    except:
        return await messag
