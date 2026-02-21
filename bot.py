import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================== CONFIG ==================

BOT_TOKEN = "8390342230:AAFIAyiSJj6sxsZzePaO-srY2qy8vBC7bCU"
ADMIN_ID = 8537782289
REFERAL_BONUS = 1000

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
DB = "database.db"

# ================== DATABASE ==================

async def create_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            referal INTEGER
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS promocodes(
            code TEXT PRIMARY KEY,
            amount INTEGER,
            used INTEGER DEFAULT 0
        )
        """)
        await db.commit()

async def add_user(user_id, referal=None):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, referal) VALUES (?, ?)",
            (user_id, referal)
        )
        await db.commit()

        if referal:
            await db.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id=?",
                (REFERAL_BONUS, referal)
            )
            await db.commit()

async def get_balance(user_id):
    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0

async def update_balance(user_id, amount):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (amount, user_id)
        )
        await db.commit()

async def get_users_count():
    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0]

async def create_promocode(code, amount):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO promocodes (code, amount) VALUES (?, ?)",
            (code, amount)
        )
        await db.commit()

async def use_promocode(code):
    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(
            "SELECT amount, used FROM promocodes WHERE code=?",
            (code,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        amount, used = row
        if used == 1:
            return "USED"
        await db.execute("UPDATE promocodes SET used=1 WHERE code=?", (code,))
        await db.commit()
        return amount

# ================== STATES ==================

class PromoState(StatesGroup):
    waiting_code = State()

class TopUpState(StatesGroup):
    waiting_amount = State()

class AdminPromoState(StatesGroup):
    waiting_data = State()

# ================== MENU ==================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish")],
        [KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="👥 Pul ishlash")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💵 Hisob To'ldirish")],
        [KeyboardButton(text="🎁 Promo kod")],
        [KeyboardButton(text="🤝 Hamkorlik")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="🎁 Promo yaratish")]
    ],
    resize_keyboard=True
)

# ================== START ==================

@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    referal = None
    if len(args) > 1 and args[1].isdigit():
        referal = int(args[1])

    await add_user(message.from_user.id, referal)

    text = f"""
👋 Assalomu alaykum <b>{message.from_user.first_name}</b>

🛡 Botimizga xush kelibsiz!

📲 Telegram
📸 Instagram
🎵 TikTok
▶️ YouTube xizmatlari mavjud.
"""
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu)

# ================== HISOB ==================

@dp.message(F.text == "💰 Hisobim")
async def balance(message: types.Message):
    bal = await get_balance(message.from_user.id)
    await message.answer(f"💰 Balansingiz: {bal} so'm")

# ================== PROMO ==================

@dp.message(F.text == "🎁 Promo kod")
async def promo_start(message: types.Message, state: FSMContext):
    await message.answer("Promo kodni kiriting:")
    await state.set_state(PromoState.waiting_code)

@dp.message(PromoState.waiting_code)
async def promo_use(message: types.Message, state: FSMContext):
    result = await use_promocode(message.text.strip())
    if result is None:
        await message.answer("❌ Promo kod topilmadi")
    elif result == "USED":
        await message.answer("⚠️ Promo kod ishlatilgan")
    else:
        await update_balance(message.from_user.id, result)
        await message.answer(f"✅ {result} so'm qo'shildi")
    await state.clear()

# ================== TOP UP ==================

@dp.message(F.text == "💵 Hisob To'ldirish")
async def topup_start(message: types.Message, state: FSMContext):
    await message.answer("Summani kiriting:")
    await state.set_state(TopUpState.waiting_amount)

@dp.message(TopUpState.waiting_amount)
async def topup_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting")
        return
    amount = int(message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}_{amount}")]
    ])
    await bot.send_message(ADMIN_ID, f"To'ldirish so'rovi\nUser: {message.from_user.id}\nSumma: {amount}", reply_markup=kb)
    await message.answer("So'rov yuborildi")
    await state.clear()

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: types.CallbackQuery):
    _, user_id, amount = callback.data.split("_")
    await update_balance(int(user_id), int(amount))
    await bot.send_message(int(user_id), f"✅ {amount} so'm qo'shildi")
    await callback.message.edit_text("Tasdiqlandi")

# ================== ADMIN ==================

@dp.message(F.text == "📊 Statistika")
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = await get_users_count()
    await message.answer(f"👥 Foydalanuvchilar: {count}")

@dp.message(F.text == "🎁 Promo yaratish")
async def create_promo_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Format: KOD SUMMA\nMasalan: BONUS 5000")
    await state.set_state(AdminPromoState.waiting_data)

@dp.message(AdminPromoState.waiting_data)
async def create_promo_process(message: types.Message, state: FSMContext):
    code, amount = message.text.split()
    await create_promocode(code.upper(), int(amount))
    await message.answer("Promo yaratildi")
    await state.clear()

# ================== RUN ==================

async def main():
    await create_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
