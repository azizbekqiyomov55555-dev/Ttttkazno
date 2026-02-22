import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8001146442:AAG5oPF_FmKsDZC-yaHgbNIMl8xU0IrLFzI"
ADMIN_ID = 8537782289  # BU YERGA O'Z TELEGRAM ID INGIZ

API_URL = "https://saleseen.uz/api/v2"  # API manzil

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

services = {}  # vaqtincha saqlash (database o‘rniga)

# ================== USER TUGMALAR ==================

user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar")]
    ],
    resize_keyboard=True
)

# ================== ADMIN TUGMALAR ==================

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Xizmat qo‘shish")],
        [KeyboardButton(text="⬅ Ortga")]
    ],
    resize_keyboard=True
)

# ================== STATE ==================

class AddService(StatesGroup):
    waiting_for_id = State()

# ================== START ==================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Bo‘limni tanlang 👇", reply_markup=user_keyboard)

# ================== ADMIN PANEL ==================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panel 👑", reply_markup=admin_keyboard)
    else:
        await message.answer("Siz admin emassiz ❌")

@dp.message(lambda m: m.text == "➕ Xizmat qo‘shish")
async def add_service(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Xizmat ID kiriting:")
        await state.set_state(AddService.waiting_for_id)

@dp.message(AddService.waiting_for_id)
async def get_service_id(message: types.Message, state: FSMContext):
    service_id = message.text

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL + service_id) as response:
            if response.status == 200:
                data = await response.json()

                services[service_id] = {
                    "name": data.get("name"),
                    "price": data.get("price"),
                    "desc": data.get("description")
                }

                await message.answer(f"✅ {data.get('name')} qo‘shildi")
            else:
                await message.answer("❌ API dan ma'lumot topilmadi")

    await state.clear()

# ================== USER XIZMATLAR ==================

@dp.message(lambda m: m.text == "🛍 Xizmatlar")
async def show_services(message: types.Message):
    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return

    text = "📋 Xizmatlar:\n\n"
    for sid, s in services.items():
        text += f"🆔 {sid}\n📌 {s['name']}\n💰 {s['price']}\n\n"

    await message.answer(text)

# ================== MAIN ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
