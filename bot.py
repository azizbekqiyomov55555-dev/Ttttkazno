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

# ======== DATABASE (temporary memory) ========
services = {}  # {category: {service_name: {id, price, min, max}}}

# ======== STATES ========
class AddService(StatesGroup):
    category = State()
    name = State()
    service_id = State()

class OrderService(StatesGroup):
    category = State()
    service = State()
    quantity = State()
    link = State()

# ======== USER MENU ========
user_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🛍 Xizmatlar")]],
    resize_keyboard=True
)

# ======== ADMIN MENU ========
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Xizmat qo‘shish")],
        [KeyboardButton(text="⬅ Ortga")]
    ],
    resize_keyboard=True
)

# ======== START ========
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum 👋", reply_markup=user_menu)

# ======== ADMIN PANEL ========
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panel 👑", reply_markup=admin_menu)
    else:
        await message.answer("❌ Siz admin emassiz")

@dp.message(lambda m: m.text == "⬅ Ortga")
async def back_menu(message: types.Message):
    await message.answer("Asosiy menyu", reply_markup=user_menu)

@dp.message(lambda m: m.text == "➕ Xizmat qo‘shish")
async def add_category(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Kategoriya nomini kiriting (Telegram / Instagram / YouTube / TikTok):")
    await state.set_state(AddService.category)

@dp.message(AddService.category)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Xizmat nomini kiriting:")
    await state.set_state(AddService.name)

@dp.message(AddService.name)
async def add_service_id(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("API Service ID kiriting:")
    await state.set_state(AddService.service_id)

@dp.message(AddService.service_id)
async def save_service(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    name = data["name"]
    service_id = message.text

    payload = {"key": API_KEY, "action": "services"}

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, data=payload) as response:
            all_services = await response.json()

    found = None
    for s in all_services:
        if str(s["service"]) == service_id:
            found = s
            break

    if not found:
        await message.answer("❌ Service ID topilmadi")
        await state.clear()
        return

    if category not in services:
        services[category] = {}

    services[category][name] = {
        "id": service_id,
        "price": float(found["rate"]),
        "min": int(found["min"]),
        "max": int(found["max"])
    }

    await message.answer(f"✅ {name} qo‘shildi")
    await state.clear()

# ======== USER SIDE ========
@dp.message(lambda m: m.text == "🛍 Xizmatlar")
async def show_categories(message: types.Message):
    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cat)] for cat in services.keys()],
        resize_keyboard=True
    )
    await message.answer("Kategoriya tanlang:", reply_markup=keyboard)
    await dp.storage.set_state(message.from_user.id, OrderService.category)

@dp.message()
async def user_flow(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    text = message.text

    data = await state.get_data()

    # CATEGORY
    if text in services:
        await state.update_data(category=text)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=s)] for s in services[text].keys()],
            resize_keyboard=True
        )
        await message.answer("Xizmat tanlang:", reply_markup=keyboard)
        await state.set_state(OrderService.service)
        return

    # SERVICE
    if current_state == OrderService.service.state:
        category = data["category"]
        if text in services[category]:
            await state.update_data(service=text)
            await message.answer("Miqdorni kiriting:")
            await state.set_state(OrderService.quantity)
            return

    # QUANTITY
    if current_state == OrderService.quantity.state:
        try:
            qty = int(text)
        except:
            await message.answer("Faqat raqam kiriting")
            return
        await state.update_data(quantity=qty)
        await message.answer("Linkni kiriting:")
        await state.set_state(OrderService.link)
        return

    # LINK
    if current_state == OrderService.link.state:
        category = data["category"]
        service_name = data["service"]
        qty = data["quantity"]
        link = text

        service = services[category][service_name]

        if qty < service["min"] or qty > service["max"]:
            await message.answer("❌ Miqdor limitdan tashqarida")
            await state.clear()
            return

        payload = {
            "key": API_KEY,
            "action": "add",
            "service": service["id"],
            "link": link,
            "quantity": qty
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=payload) as response:
                result = await response.json()

        if "order" in result:
            await message.answer(f"✅ Buyurtma yuborildi!\nOrder ID: {result['order']}")
        else:
            await message.answer("❌ Buyurtma xatosi")

        await state.clear()

# ======== MAIN ========
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
