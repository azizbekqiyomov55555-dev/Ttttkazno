import asyncio
import sqlite3
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

TOKEN = "8390342230:AAFIAyiSJj6sxsZzePaO-srY2qy8vBC7bCU"
ADMIN_ID = 8537782289   # admin id
API_URL = "https://saleseen.uz/api/v2"  # API link
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service TEXT,
    link TEXT,
    quantity INTEGER,
    status TEXT
)
""")

db.commit()

# ================= MENU =================

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

Ushbu bot orqali siz turli xizmatlardan foydalanishingiz mumkin.

📌 Quyidagi menyudan birini tanlang:
"""

    await message.answer(text, reply_markup=main_menu())

# ================= BALANCE =================

@dp.message(F.text == "💰 Hisobim")
async def balance_handler(message: Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    balance = cursor.fetchone()[0]

    await message.answer(f"💰 Sizning balansingiz: <b>{balance} so'm</b>")

# ================= TOP UP =================

@dp.message(F.text == "💳 Hisob To'ldirish")
async def topup_handler(message: Message):
    await message.answer("To'lov uchun admin bilan bog'laning.")

# ================= SERVICES =================

@dp.message(F.text == "🛍 Xizmatlar")
async def services_handler(message: Message):
    text = """
📌 Mavjud xizmatlar:

1️⃣ Telegram obuna
2️⃣ Instagram like
3️⃣ TikTok ko'rish
4️⃣ YouTube view

Xizmat raqamini yuboring:
"""
    await message.answer(text)

# ================= ORDER CREATE =================

@dp.message(F.text.in_(["1", "2", "3", "4"]))
async def service_select(message: Message):
    service_map = {
        "1": "Telegram obuna",
        "2": "Instagram like",
        "3": "TikTok view",
        "4": "YouTube view"
    }

    service = service_map[message.text]

    cursor.execute("""
    INSERT INTO orders (user_id, service, link, quantity, status)
    VALUES (?, ?, ?, ?, ?)
    """, (message.from_user.id, service, "kutilmoqda", 0, "pending"))

    db.commit()

    await message.answer("🔗 Endi link yuboring:")

# ================= SUPPORT =================

@dp.message(F.text == "📞 Murojaat")
async def support_handler(message: Message):
    await message.answer("Admin: @admin_username")

# ================= ADMIN PANEL =================

@dp.message(F.text.startswith("/admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    orders = cursor.fetchone()[0]

    await message.answer(f"""
👑 ADMIN PANEL

👥 Foydalanuvchilar: {users}
🛒 Buyurtmalar: {orders}
""")

# ================= RUN =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
