import asyncio
import os
import sqlite3
from datetime import datetime

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8537782289"))
API_URL = os.getenv("API_URL", "https://saleseen.uz/api/v2")
API_KEY = os.getenv("API_KEY")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN qo‘yilmagan!")

# ================= DATABASE =================
conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS services(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    api_id TEXT,
    price REAL,
    percent REAL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service_id INTEGER,
    api_order_id TEXT,
    quantity INTEGER,
    total REAL,
    status TEXT,
    created_at TEXT
)
""")

conn.commit()

# ================= BOT =================
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= MENUS =================
user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="💰 Hisobim")],
        [KeyboardButton(text="🛒 Buyurtmalarim")]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Xizmat qo‘shish"), KeyboardButton(text="❌ Xizmat o‘chirish")],
        [KeyboardButton(text="💹 Foiz qo‘shish"), KeyboardButton(text="➕ Balans qo‘shish")],
        [KeyboardButton(text="⬅ Ortga")]
    ],
    resize_keyboard=True
)

# ================= STATES =================
class AddService(StatesGroup):
    name = State()
    api_id = State()
    price = State()

class AddPercent(StatesGroup):
    service_id = State()
    percent = State()

class AddBalance(StatesGroup):
    user_id = State()
    amount = State()

class OrderState(StatesGroup):
    service_id = State()
    quantity = State()

# ================= START =================
@dp.message(Command("start"))
async def start(message: Message):
    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (message.from_user.id,))
    conn.commit()
    await message.answer("Assalomu alaykum 👋", reply_markup=user_kb)

@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panel", reply_markup=admin_kb)

@dp.message(F.text == "⬅ Ortga")
async def back(message: Message):
    await message.answer("Menu", reply_markup=user_kb)

# ================= BALANCE =================
@dp.message(F.text == "💰 Hisobim")
async def balance(message: Message):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cur.fetchone()[0]
    await message.answer(f"💰 Balans: {bal}")

# ================= ADD SERVICE =================
@dp.message(F.text == "➕ Xizmat qo‘shish")
async def add_service_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Xizmat nomi:")
    await state.set_state(AddService.name)

@dp.message(AddService.name)
async def add_service_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("API ID:")
    await state.set_state(AddService.api_id)

@dp.message(AddService.api_id)
async def add_service_api(message: Message, state: FSMContext):
    await state.update_data(api_id=message.text)
    await message.answer("Narxi:")
    await state.set_state(AddService.price)

@dp.message(AddService.price)
async def add_service_price(message: Message, state: FSMContext):
    data = await state.get_data()
    price = float(message.text)
    cur.execute(
        "INSERT INTO services(name, api_id, price) VALUES(?,?,?)",
        (data["name"], data["api_id"], price)
    )
    conn.commit()
    await message.answer("✅ Xizmat qo‘shildi")
    await state.clear()

# ================= DELETE SERVICE =================
@dp.message(F.text == "❌ Xizmat o‘chirish")
async def delete_service(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    cur.execute("SELECT id, name FROM services")
    rows = cur.fetchall()
    if not rows:
        return await message.answer("Xizmat yo‘q")

    kb = []
    for r in rows:
        kb.append([InlineKeyboardButton(text=r[1], callback_data=f"del_{r[0]}")])
    await message.answer("Tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("del_"))
async def delete_service_cb(callback):
    sid = int(callback.data.split("_")[1])
    cur.execute("DELETE FROM services WHERE id=?", (sid,))
    conn.commit()
    await callback.message.edit_text("O‘chirildi")
    await callback.answer()

# ================= SHOW SERVICES =================
@dp.message(F.text == "🛍 Xizmatlar")
async def show_services(message: Message):
    cur.execute("SELECT id, name, price, percent FROM services")
    rows = cur.fetchall()
    if not rows:
        return await message.answer("Xizmat yo‘q")

    kb = []
    for r in rows:
        final_price = r[2] * (1 + r[3]/100)
        kb.append([InlineKeyboardButton(
            text=f"{r[1]} - {final_price}",
            callback_data=f"buy_{r[0]}"
        )])

    await message.answer("Tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= BUY =================
@dp.callback_query(F.data.startswith("buy_"))
async def buy_service(callback, state: FSMContext):
    sid = int(callback.data.split("_")[1])
    await state.update_data(service_id=sid)
    await callback.message.answer("Miqdor kiriting:")
    await state.set_state(OrderState.quantity)
    await callback.answer()

@dp.message(OrderState.quantity)
async def order_quantity(message: Message, state: FSMContext):
    qty = int(message.text)
    data = await state.get_data()
    sid = data["service_id"]

    cur.execute("SELECT price, percent, api_id FROM services WHERE id=?", (sid,))
    row = cur.fetchone()

    price = row[0] * (1 + row[1]/100)
    total = price * qty

    cur.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cur.fetchone()[0]

    if bal < total:
        await message.answer("❌ Balans yetarli emas")
        await state.clear()
        return

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data={
            "key": API_KEY,
            "action": "add",
            "service": row[2],
            "link": "https://example.com",
            "quantity": qty
        }) as resp:
            res = await resp.json()
            api_order_id = str(res.get("order"))

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?",
                (total, message.from_user.id))

    cur.execute("""
        INSERT INTO orders(user_id, service_id, api_order_id, quantity, total, status, created_at)
        VALUES(?,?,?,?,?,?,?)
    """, (message.from_user.id, sid, api_order_id, qty, total, "sent", datetime.now()))

    conn.commit()

    await message.answer("✅ Buyurtma yuborildi")
    await state.clear()

# ================= MY ORDERS =================
@dp.message(F.text == "🛒 Buyurtmalarim")
async def my_orders(message: Message):
    cur.execute("SELECT api_order_id, total, status FROM orders WHERE user_id=?",
                (message.from_user.id,))
    rows = cur.fetchall()
    if not rows:
        return await message.answer("Buyurtma yo‘q")

    text = ""
    for r in rows:
        text += f"Order: {r[0]} | {r[1]} | {r[2]}\n"
    await message.answer(text)

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
