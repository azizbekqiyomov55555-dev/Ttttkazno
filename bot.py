import asyncio
import sqlite3
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

TOKEN = "8390342230:AAFIAyiSJj6sxsZzePaO-srY2qy8vBC7bCU"
ADMIN_ID = 8537782289

# API sozlamalari (umumiy service API uchun)
API_URL = "https://saleseen.uz/api/v2"
API_KEY = "aee8149aa4fe37368499c64f63193153"

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ================= DATABASE =================

db = sqlite3.connect("smm.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0
)
""")

db.commit()

# ================= MAIN MENU =================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish")],
            [KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="👥 Pul ishlash")],
            [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💳 Hisob To'ldirish")],
            [KeyboardButton(text="📞 Murojaat"), KeyboardButton(text="☎️ Qo'llab-quvvatlash")],
            [KeyboardButton(text="🤝 Hamkorlik")]
        ],
        resize_keyboard=True
    )

# ================= START =================

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        db.commit()

    text = f"""
👋 Assalomu alaykum, <b>{message.from_user.first_name}</b>

📌 Quyidagi menyudan birini tanlang:
"""
    await message.answer(text, reply_markup=main_menu())

# ================= BALANCE =================

@dp.message(F.text == "💰 Hisobim")
async def balance_handler(message: Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    balance = cursor.fetchone()[0]

    await message.answer(f"💰 Balans: <b>{balance} so'm</b>")

# ================= SERVICES MENU =================

def services_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔵 Telegram", callback_data="platform_telegram"),
            InlineKeyboardButton(text="🟣 Instagram", callback_data="platform_instagram")
        ],
        [
            InlineKeyboardButton(text="⚫ TikTok", callback_data="platform_tiktok"),
            InlineKeyboardButton(text="🔴 YouTube", callback_data="platform_youtube")
        ],
        [
            InlineKeyboardButton(text="📦 Barcha xizmatlar", callback_data="platform_all")
        ]
    ])

@dp.message(F.text == "🛍 Xizmatlar")
async def services_handler(message: Message):
    text = """
✅ <b>Xizmatlarimizni tanlaganingizdan xursandmiz!</b>

👇 Ijtimoiy tarmoqlardan birini tanlang:
"""
    await message.answer(text, reply_markup=services_menu())

# ================= API DAN XIZMAT OLISH =================

async def get_services():
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data={
            "key": API_KEY,
            "action": "services"
        }) as response:
            return await response.json()

# ================= PLATFORMA TANLANGANDA =================

@dp.callback_query(F.data.startswith("platform_"))
async def show_platform_services(callback: CallbackQuery):
    platform = callback.data.split("_")[1]

    try:
        services = await get_services()
    except:
        await callback.message.edit_text("❌ API bilan bog'lanib bo'lmadi.")
        return

    text = ""

    count = 0
    for service in services:

        name = service.get("name", "").lower()

        if platform == "all" or platform in name:
            text += (
                f"🆔 <b>ID:</b> {service.get('service')}\n"
                f"📌 <b>Nomi:</b> {service.get('name')}\n"
                f"💵 <b>Narx:</b> {service.get('rate')} / 1000\n"
                f"📊 <b>Min:</b> {service.get('min')} | "
                f"<b>Max:</b> {service.get('max')}\n\n"
            )
            count += 1

        if count >= 15:
            break

    if text == "":
        text = "❌ Xizmat topilmadi."

    await callback.message.edit_text(text)

# ================= ADMIN =================

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    await message.answer(f"👑 Admin Panel\n\n👥 Foydalanuvchilar: {users}")

# ================= RUN =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
