import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite

# ================= CONFIG =================

BOT_TOKEN = "8390342230:AAFIAyiSJj6sxsZzePaO-srY2qy8vBC7bCU"
ADMIN_ID = 8537782289  # int bo'lishi shart
CHANNEL = "@KANAL_USERNAME"  # @ bilan yoziladi

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DB = "database.db"

# ================= DATABASE =================

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

async def get_balance(user_id):
    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def update_balance(user_id, amount):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (amount, user_id)
        )
        await db.commit()

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
        await db.execute(
            "UPDATE promocodes SET used=1 WHERE code=?",
            (code,)
        )
        await db.commit()
        return amount

# ================= STATES =================

class PromoState(StatesGroup):
    waiting_code = State()

class TopUpState(StatesGroup):
    waiting_amount = State()

# ================= KEYBOARDS =================

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="🎁 Promo kod")],
        [KeyboardButton(text="💳 Hisob to‘ldirish"), KeyboardButton(text="👥 Referal")],
    ],
    resize_keyboard=True
)

def admin_keyboard(user_id, amount):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"approve_{user_id}_{amount}"
            ),
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="cancel"
            )
        ]
    ])

# ================= CHANNEL CHECK =================

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    referal = None
    if len(args) > 1 and args[1].isdigit():
        referal = int(args[1])

    await add_user(message.from_user.id, referal)

    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📢 Obuna bo‘lish",
                url=f"https://t.me/{CHANNEL.replace('@','')}"
            )],
            [InlineKeyboardButton(
                text="✅ Tekshirish",
                callback_data="check_sub"
            )]
        ])
        await message.answer(
            "Botdan foydalanish uchun kanalga obuna bo‘ling!",
            reply_markup=kb
        )
        return

    await message.answer("Xush kelibsiz!", reply_markup=main_menu)

# ================= SUB CHECK =================

@dp.callback_query(F.data == "check_sub")
async def sub_check(callback: types.CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.answer(
            "Rahmat! Endi foydalanishingiz mumkin.",
            reply_markup=main_menu
        )
    else:
        await callback.answer(
            "Hali obuna bo‘lmadingiz!",
            show_alert=True
        )

# ================= BALANCE =================

@dp.message(F.text == "💰 Hisobim")
async def balance(message: types.Message):
    bal = await get_balance(message.from_user.id)
    await message.answer(f"Sizning balansingiz: {bal} so'm")

# ================= PROMO =================

@dp.message(F.text == "🎁 Promo kod")
async def promo_start(message: types.Message, state: FSMContext):
    await message.answer("Promo kodni kiriting:")
    await state.set_state(PromoState.waiting_code)

@dp.message(PromoState.waiting_code)
async def promo_process(message: types.Message, state: FSMContext):
    result = await use_promocode(message.text.strip())
    if result is None:
        await message.answer("Promo kod topilmadi!")
    elif result == "USED":
        await message.answer("Bu promo kod ishlatilgan!")
    else:
        await update_balance(message.from_user.id, result)
        await message.answer(f"{result} so'm qo‘shildi!")
    await state.clear()

# ================= REFERAL =================

@dp.message(F.text == "👥 Referal")
async def referal(message: types.Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={message.from_user.id}"
    await message.answer(f"Sizning referal linkingiz:\n{link}")

# ================= TOP UP =================

@dp.message(F.text == "💳 Hisob to‘ldirish")
async def topup_start(message: types.Message, state: FSMContext):
    await message.answer("To‘ldirish summasini kiriting:")
    await state.set_state(TopUpState.waiting_amount)

@dp.message(TopUpState.waiting_amount)
async def topup_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting!")
        return

    amount = int(message.text)

    await bot.send_message(
        ADMIN_ID,
        f"Foydalanuvchi: {message.from_user.id}\nSumma: {amount}",
        reply_markup=admin_keyboard(message.from_user.id, amount)
    )

    await message.answer("So‘rov yuborildi. Admin tasdiqlashini kuting.")
    await state.clear()

# ================= ADMIN =================

@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: types.CallbackQuery):
    _, user_id, amount = callback.data.split("_")
    await update_balance(int(user_id), int(amount))
    await bot.send_message(
        int(user_id),
        f"{amount} so'm balansingizga qo‘shildi!"
    )
    await callback.message.edit_text("Tasdiqlandi!")

@dp.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("Bekor qilindi!")

# ================= RUN =================

async def main():
    await create_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
