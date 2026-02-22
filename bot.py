import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8001146442:AAG5oPF_FmKsDZC-yaHgbNIMl8xU0IrLFzI"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Tugmalar yaratish
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish")],
        [KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="👥 Pul ishlash")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💳 Hisob To'ldirish")],
        [KeyboardButton(text="📞 Murojaat"), KeyboardButton(text="☎ Qo'llab-quvvatlash")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum! Kerakli bo‘limni tanlang 👇", reply_markup=keyboard)

@dp.message()
async def buttons(message: types.Message):
    text = message.text

    if text == "🛍 Xizmatlar":
        await message.answer("Xizmatlar bo‘limi")
    elif text == "📱 Nomer olish":
        await message.answer("Nomer olish bo‘limi")
    elif text == "🛒 Buyurtmalarim":
        await message.answer("Buyurtmalarim bo‘limi")
    elif text == "👥 Pul ishlash":
        await message.answer("Pul ishlash bo‘limi")
    elif text == "💰 Hisobim":
        await message.answer("Hisobingiz")
    elif text == "💳 Hisob To'ldirish":
        await message.answer("Hisob to‘ldirish")
    elif text == "📞 Murojaat":
        await message.answer("Murojaat bo‘limi")
    elif text == "☎ Qo'llab-quvvatlash":
        await message.answer("Qo‘llab-quvvatlash xizmati")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())    
