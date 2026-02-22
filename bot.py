import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================
TOKEN = "8001146442:AAG5oPF_FmKsDZC-yaHgbNIMl8xU0IrLFzI"
ADMIN_ID = 8537782289
API_URL = "https://saleseen.uz/api/v2"
API_KEY = "aee8149aa4fe37368499c64f63193153"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= DATABASE =================
services = {}  # {category: {service_name: {id, min, max, price}}}
cards = {}     # {card_name: card_number}
users_balance = {}  # {user_id: balance}

# ================= STATES =================
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

class AddCard(StatesGroup):
    name = State()
    number = State()

class TopUp(StatesGroup):
    amount = State()
    card = State()
    comment = State()
    receipt = State()

# ================= MENUS =================
user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish")],
        [KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="👥 Pul ishlash")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💳 Hisob To'ldirish")],
        [KeyboardButton(text="📞 Murojaat"), KeyboardButton(text="☎ Qo'llab-quvvatlash")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Xizmat qo‘shish"), KeyboardButton(text="❌ Xizmat o‘chirish")],
        [KeyboardButton(text="💹 Foiz qo‘shish"), KeyboardButton(text="💳 Karta qo‘shish")],
        [KeyboardButton(text="⬅ Ortga")]
    ],
    resize_keyboard=True
)

# ================= START =================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum 👋", reply_markup=user_menu)

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

# ================== ADMIN: KARTA =================
@dp.message(lambda m: m.text == "💳 Karta qo‘shish")
async def add_card_start(message: types.Message):
    await message.answer("Kartaga nom bering:")
    await dp.current_state(user=message.from_user.id).set_state(AddCard.name)

@dp.message(AddCard.name)
async def add_card_number(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Kartaning raqamini kiriting:")
    await state.set_state(AddCard.number)

@dp.message(AddCard.number)
async def save_card(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    number = message.text
    cards[name] = number
    await message.answer(f"✅ {name} kartasi qo‘shildi: {number}")
    await state.clear()

# ================== ADMIN: XIZMAT QO‘SHISH =================
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

# ================== ADMIN: XIZMAT O‘CHIRISH =================
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

# ================== ADMIN: FOIZ QO‘SHISH =================
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

# ================== USER: HISOB TO'LDIRISH =================
@dp.message(lambda m: m.text == "💳 Hisob To'ldirish")
async def topup_start(message: types.Message):
    await message.answer("Qancha miqdorda to‘ldirmoqchisiz?")
    await dp.current_state(user=message.from_user.id).set_state(TopUp.amount)

@dp.message(TopUp.amount)
async def topup_card(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except:
        await message.answer("❌ Iltimos raqam kiriting")
        return
    await state.update_data(amount=amount)
    if not cards:
        await message.answer("❌ Hozircha karta mavjud emas, admin bilan bog‘laning")
        await state.clear()
        return
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"card_{name}")] for name in cards]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("To‘lov qilish uchun kartani tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("card_"))
async def topup_comment(callback: types.CallbackQuery, state: FSMContext):
    card_name = callback.data.replace("card_", "")
    await state.update_data(card=card_name)
    await callback.message.answer("Izoh qoldiring (ixtiyoriy):")
    await state.set_state(TopUp.comment)

@dp.message(TopUp.comment)
async def topup_receipt(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await message.answer("To‘lov chekini yuboring (rasm sifatida):")
    await state.set_state(TopUp.receipt)

@dp.message(TopUp.receipt, content_types=types.ContentType.PHOTO)
async def send_to_admin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    amount = data["amount"]
    card_name = data["card"]
    comment = data["comment"]
    receipt_file_id = message.photo[-1].file_id

    # Admin tasdiqlash uchun inline tugmalar
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{user_id}_{amount}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"reject_{user_id}_{amount}")
            ]
        ]
    )
    text = f"💳 To‘lov kelib tushdi!\nFoydalanuvchi: {user_name}\nMiqdor: {amount}\nKarta: {card_name}\nIzoh: {comment}"
    await bot.send_photo(chat_id=ADMIN_ID, photo=receipt_file_id, caption=text, reply_markup=keyboard)
    await message.answer("✅ To‘lovingiz adminga yuborildi. 12 soat ichida tasdiqlanadi")
    await state.clear()

# ================== ADMIN: TASDIQLASH =================
@dp.callback_query(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def admin_approval(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action = parts[0]
    user_id = int(parts[1])
    amount = float(parts[2])
    if action == "approve":
        users_balance[user_id] = users_balance.get(user_id, 0) + amount
        await bot.send_message(user_id, f"✅ Sizning hisobingiz {amount} so‘mga to‘ldirildi")
        await callback.message.edit_caption(callback.message.caption + "\n✅ Tasdiqlandi")
    else:
        await bot.send_message(user_id, f"❌ Admin to‘lovni qabul qilmadi")
        await callback.message.edit_caption(callback.message.caption + "\n❌ Bekor qilindi")

# ================== MAIN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
