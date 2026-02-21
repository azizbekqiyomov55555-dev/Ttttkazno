import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8390342230:AAFIAyiSJj6sxsZzePaO-srY2qy8vBC7bCU"
ADMIN_ID = 8537782289

API_KEY = "aee8149aa4fe37368499c64f63193153"
API_URL = "https://saleseen.uz/api/v2"

bot = Bot(TOKEN)
dp = Dispatcher()

# ================== MENU ==================
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Balans")],
        [KeyboardButton(text="🚀 Buyurtma berish")],
    ],
    resize_keyboard=True
)

# ================== START ==================
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Xush kelibsiz 👋", reply_markup=menu)

# ================== BALANCE ==================
@dp.message(F.text == "📊 Balans")
async def check_balance(message: Message):
    async with aiohttp.ClientSession() as session:
        payload = {
            "key": API_KEY,
            "action": "balance"
        }
        async with session.post(API_URL, data=payload) as resp:
            data = await resp.json()
            await message.answer(f"💰 Balans: {data}")

# ================== ORDER ==================
@dp.message(F.text == "🚀 Buyurtma berish")
async def order_request(message: Message):
    await message.answer("Link yuboring:")
    dp.message.register(get_link)

async def get_link(message: Message):
    link = message.text
    await message.answer("Soni kiriting:")
    dp.message.register(lambda msg: create_order(msg, link))

async def create_order(message: Message, link):
    quantity = message.text

    async with aiohttp.ClientSession() as session:
        payload = {
            "key": API_KEY,
            "action": "add",
            "service": 1,  # xizmat ID
            "link": link,
            "quantity": quantity
        }
        async with session.post(API_URL, data=payload) as resp:
            data = await resp.json()
            await message.answer(f"✅ Buyurtma javobi:\n{data}")

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
