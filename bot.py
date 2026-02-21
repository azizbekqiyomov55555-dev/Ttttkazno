import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

TOKEN = "8390342230:AAFIAyiSJj6sxsZzePaO-srY2qy8vBC7bCU"
ADMIN_ID = 123456789  # admin id
CHANNEL_USERNAME = "@Azizbekl2026"

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ================= DATABASE =================

async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            quantity INTEGER,
            status TEXT
        )
        """)
        await db.commit()

# ================= STATE =================

class OrderState(StatesGroup):
    choosing_service = State()
    waiting_quantity = State()

# ================= START =================

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id

    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["left"]:
            raise Exception
    except:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
        ])
        await message.answer("Botdan foydalanish uchun kanalga obuna bo‘ling.", reply_markup=keyboard)
        return

    await message.answer("Xush kelibsiz!", reply_markup=main_menu())

# ================= MENU =================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="💰 Hisobim")],
            [KeyboardButton(text="📦 Buyurtmalarim"), KeyboardButton(text="➕ Hisob to‘ldirish")],
            [KeyboardButton(text="☎️ Aloqa")]
        ],
        resize_keyboard=True
    )

# ================= SUB CHECK =================

@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status != "left":
            await callback.message.delete()
            await callback.message.answer("Obuna tasdiqlandi ✅", reply_markup=main_menu())
        else:
            await callback.answer("Hali obuna bo‘lmagansiz", show_alert=True)
    except:
        await callback.answer("Xatolik", show_alert=True)

# ================= SERVICES =================

@dp.message(F.text == "🛍 Xizmatlar")
async def services_handler(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama xizmati", callback_data="service_ads")],
        [InlineKeyboardButton(text="📊 Marketing xizmati", callback_data="service_marketing")],
        [InlineKeyboardButton(text="🎥 Media xizmati", callback_data="service_media")]
    ])
    await message.answer("Xizmat turini tanlang:", reply_markup=keyboard)
    await state.set_state(OrderState.choosing_service)

# ================= SERVICE SELECT =================

@dp.callback_query(F.data.startswith("service_"))
async def select_service(callback: CallbackQuery, state: FSMContext):
    service = callback.data.split("_")[1]
    await state.update_data(service=service)
    await callback.message.answer("Miqdorni kiriting:")
    await state.set_state(OrderState.waiting_quantity)

# ================= QUANTITY =================

@dp.message(OrderState.waiting_quantity)
async def get_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting.")
        return

    quantity = int(message.text)
    data = await state.get_data()
    service = data["service"]

    async with aiosqlite.connect("bot.db") as db:
        await db.execute(
            "INSERT INTO orders (user_id, service, quantity, status) VALUES (?, ?, ?, ?)",
            (message.from_user.id, service, quantity, "pending")
        )
        await db.commit()

    await message.answer("Buyurtma qabul qilindi ✅", reply_markup=main_menu())
    await state.clear()

# ================= MY ORDERS =================

@dp.message(F.text == "📦 Buyurtmalarim")
async def my_orders(message: Message):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT service, quantity, status FROM orders WHERE user_id = ?", (message.from_user.id,)) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("Buyurtmalar yo‘q.")
        return

    text = "<b>Sizning buyurtmalaringiz:</b>\n\n"
    for row in rows:
        text += f"Xizmat: {row[0]}\nMiqdor: {row[1]}\nHolat: {row[2]}\n\n"

    await message.answer(text)

# ================= BALANCE =================

@dp.message(F.text == "💰 Hisobim")
async def balance_handler(message: Message):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()

    balance = row[0] if row else 0
    await message.answer(f"Hisobingiz: {balance} so‘m")

# ================= TOP UP =================

@dp.message(F.text == "➕ Hisob to‘ldirish")
async def topup_handler(message: Message):
    await message.answer("Hisob to‘ldirish uchun admin bilan bog‘laning.")

# ================= CONTACT =================

@dp.message(F.text == "☎️ Aloqa")
async def contact_handler(message: Message):
    await message.answer("Admin: @admin_username")

# ================= ADMIN PANEL =================

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Admin panel\n/buyurtmalar - barcha buyurtmalar")

@dp.message(F.text == "/buyurtmalar")
async def all_orders(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT user_id, service, quantity, status FROM orders") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await message.answer("Buyurtma yo‘q.")
        return

    text = "<b>Barcha buyurtmalar:</b>\n\n"
    for row in rows:
        text += f"User: {row[0]}\nXizmat: {row[1]}\nMiqdor: {row[2]}\nHolat: {row[3]}\n\n"

    await message.answer(text)

# ================= RUN =================

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
