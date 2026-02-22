import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================== CONFIG ==================
TOKEN = "8001146442:AAG5oPF_FmKsDZC-yaHgbNIMl8xU0IrLFzI"
ADMIN_ID = 8537782289
API_URL = "https://saleseen.uz/api/v2"
API_KEY = "aee8149aa4fe37368499c64f63193153"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================== DATABASE ==================
services = {}  # {category: {service_name: {id, min, max, price}}}

# ================== STATES ==================
class AddService(StatesGroup):
    category = State()
    name = State()
    service_id = State()

class OrderService(StatesGroup):
    category = State()
    service = State()
    quantity = State()
    link = State()

class AddPercent(StatesGroup):
    category = State()
    service = State()
    percent = State()

# ================== USER MENU ==================
user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish")],
        [KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="👥 Pul ishlash")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💳 Hisob To'ldirish")],
        [KeyboardButton(text="📞 Murojaat"), KeyboardButton(text="☎ Qo'llab-quvvatlash")]
    ],
    resize_keyboard=True
)

# ================== ADMIN MENU ==================
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Xizmat qo‘shish"), KeyboardButton(text="❌ Xizmat o‘chirish")],
        [KeyboardButton(text="💹 Foiz qo‘shish")],
        [KeyboardButton(text="⬅ Ortga")]
    ],
    resize_keyboard=True
)

# ================== START ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum 👋", reply_markup=user_menu)

# ================== ADMIN PANEL ==================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panel 👑", reply_markup=admin_menu)
    else:
        await message.answer("❌ Siz admin emassiz")

@dp.message(lambda m: m.text == "⬅ Ortga")
async def back_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu", reply_markup=user_menu)

# ================== ADD SERVICE ==================
@dp.message(lambda m: m.text == "➕ Xizmat qo‘shish")
async def add_category(message: types.Message, state: FSMContext):
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
        "min": int(found["min"]),
        "max": int(found["max"]),
        "price": float(found.get("rate", 0))
    }

    await message.answer(f"✅ {name} qo‘shildi\n💰 Narxi: {services[category][name]['price']}")
    await state.clear()

# ================== DELETE SERVICE ==================
@dp.message(lambda m: m.text == "❌ Xizmat o‘chirish")
async def delete_service_menu(message: types.Message):
    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return

    buttons = []
    for category, cat_services in services.items():
        for name in cat_services:
            buttons.append([InlineKeyboardButton(text=f"{category} - {name}", callback_data=f"del_{category}_{name}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("O‘chirmoqchi bo‘lgan xizmatni tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("del_"))
async def delete_service_callback(callback: types.CallbackQuery):
    _, category, name = callback.data.split("_", 2)
    if category in services and name in services[category]:
        del services[category][name]
        if not services[category]:
            del services[category]
        await callback.message.edit_text(f"✅ {name} xizmati o‘chirildi")
    else:
        await callback.message.edit_text("❌ Bunday xizmat topilmadi")

# ================== ADD PERCENT ==================
@dp.message(lambda m: m.text == "💹 Foiz qo‘shish")
async def add_percent_start(message: types.Message, state: FSMContext):
    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return
    buttons = []
    for category, cat_services in services.items():
        for name in cat_services:
            buttons.append([InlineKeyboardButton(text=f"{category} - {name}", callback_data=f"percent_{category}_{name}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Foiz qo‘shmoqchi bo‘lgan xizmatni tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("percent_"))
async def percent_service_callback(callback: types.CallbackQuery, state: FSMContext):
    _, category, name = callback.data.split("_", 2)
    await state.update_data(category=category, service=name)
    await callback.message.answer("Foiz miqdorini kiriting (%):")
    await state.set_state(AddPercent.percent)

@dp.message(AddPercent.percent)
async def apply_percent(message: types.Message, state: FSMContext):
    try:
        percent = float(message.text)
    except:
        await message.answer("❌ Iltimos raqam kiriting")
        return
    data = await state.get_data()
    category = data["category"]
    service_name = data["service"]
    service = services[category][service_name]
    old_price = service["price"]
    new_price = old_price + old_price * percent / 100
    service["price"] = round(new_price, 2)
    await message.answer(f"✅ {service_name} narxi {old_price} ➡ {service['price']}")
    await state.clear()

# ================== USER SERVICES ==================
@dp.message(lambda m: m.text == "🛍 Xizmatlar")
async def show_categories(message: types.Message, state: FSMContext):
    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return

    buttons = []
    row = []
    for i, cat in enumerate(services.keys(), start=1):
        row.append(InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("✅ Xizmatlarimizni tanlang:", reply_markup=keyboard)
    await state.set_state(OrderService.category)

# ================== USER FLOW ==================
@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def open_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    buttons = [[InlineKeyboardButton(text=s, callback_data=f"service_{s}")] for s in services[category]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Xizmatni tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("service_"))
async def select_service(callback: types.CallbackQuery, state: FSMContext):
    service_name = callback.data.replace("service_", "")
    await state.update_data(service=service_name)
    await callback.message.answer("Miqdorni kiriting:")
    await state.set_state(OrderService.quantity)

@dp.message(OrderService.quantity)
async def enter_quantity(message: types.Message, state: FSMContext):
    try:
        qty = int(message.text)
    except:
        await message.answer("❌ Faqat raqam kiriting")
        return
    await state.update_data(quantity=qty)
    await message.answer("Linkni kiriting:")
    await state.set_state(OrderService.link)

@dp.message(OrderService.link)
async def enter_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    service_name = data.get("service")
    qty = data.get("quantity")
    link = message.text

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

# ================== OTHER USER BUTTONS ==================
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

# ================== MAIN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
