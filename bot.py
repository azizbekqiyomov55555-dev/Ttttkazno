import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8001146442:AAG5oPF_FmKsDZC-yaHgbNIMl8xU0IrLFzI"
ADMIN_ID = 8537782289

API_URL = "https://saleseen.uz/api/v2"
API_KEY = "aee8149aa4fe37368499c64f63193153"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

services = {}

# ================= USER MENU =================

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish")],
        [KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="👥 Pul ishlash")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💳 Hisob To'ldirish")],
        [KeyboardButton(text="📞 Murojaat"), KeyboardButton(text="☎ Qo'llab-quvvatlash")]
    ],
    resize_keyboard=True
)

# ================= ADMIN MENU =================

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Xizmat qo‘shish")],
        [KeyboardButton(text="⬅ Ortga")]
    ],
    resize_keyboard=True
)

# ================= STATE =================

class AddService(StatesGroup):
    waiting_for_id = State()

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum 👋", reply_markup=user_keyboard)

# ================= ADMIN PANEL =================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panel 👑", reply_markup=admin_keyboard)
    else:
        await message.answer("Siz admin emassiz ❌")

@dp.message(lambda m: m.text == "⬅ Ortga")
async def back_to_user(message: types.Message):
    await message.answer("Asosiy menyu", reply_markup=user_keyboard)

@dp.message(lambda m: m.text == "➕ Xizmat qo‘shish")
async def add_service(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Xizmat ID kiriting:")
        await state.set_state(AddService.waiting_for_id)

# ================= API ORQALI XIZMAT OLISH =================

@dp.message(AddService.waiting_for_id)
async def get_service_id(message: types.Message, state: FSMContext):
    service_id = message.text

    payload = {
        "key": API_KEY,
        "action": "services"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data=payload) as response:
            data = await response.json()

            found = None
            for s in data:
                if str(s["service"]) == service_id:
                    found = s
                    break

            if found:
                services[service_id] = {
                    "name": found["name"],
                    "price": found["rate"],
                    "min": found["min"],
                    "max": found["max"]
                }

                await message.answer(f"✅ {found['name']} qo‘shildi")
            else:
                await message.answer("❌ Bunday ID topilmadi")

    await state.clear()

# ================= USER XIZMATLAR =================

@dp.message(lambda m: m.text == "🛍 Xizmatlar")
async def show_services(message: types.Message):
    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return

    text = "📋 Xizmatlar:\n\n"
    for sid, s in services.items():
        text += (
            f"🆔 {sid}\n"
            f"📌 {s['name']}\n"
            f"💰 Narx: {s['price']}\n"
            f"📊 Min: {s['min']} | Max: {s['max']}\n\n"
        )

    await message.answer(text)

# ================= QOLGAN TUGMALAR =================

@dp.message(lambda m: m.text == "📱 Nomer olish")
async def nomer(message: types.Message):
    await message.answer("Nomer olish bo‘limi")

@dp.message(lambda m: m.text == "🛒 Buyurtmalarim")
async def buyurtma(message: types.Message):
    await message.answer("Buyurtmalarim bo‘limi")

@dp.message(lambda m: m.text == "👥 Pul ishlash")
async def pul(message: types.Message):
    await message.answer("Pul ishlash bo‘limi")

@dp.message(lambda m: m.text == "💰 Hisobim")
async def hisob(message: types.Message):
    await message.answer("Hisobingiz")

@dp.message(lambda m: m.text == "💳 Hisob To'ldirish")
async def toldirish(message: types.Message):
    await message.answer("Hisob to‘ldirish")

@dp.message(lambda m: m.text == "📞 Murojaat")
async def murojaat(message: types.Message):
    await message.answer("Murojaat bo‘limi")

@dp.message(lambda m: m.text == "☎ Qo'llab-quvvatlash")
async def support(message: types.Message):
    await message.answer("Qo‘llab-quvvatlash xizmati")

# ================= MAIN =================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
