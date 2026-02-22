import asyncio
import aiohttp

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
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


# ================= DATABASE (oddiy RAM) =================
services = {}        # {category: {service_name: {id, min, max, price}}}
cards = {}           # {card_name: card_number}
users_balance = {}   # {user_id: balance}


# ================= HELPERS =================
def cb(*parts: str) -> str:
    """callback_data uchun xavfsiz format: 'a|b|c'"""
    return "|".join(parts)

def fmt_amount(x: float) -> str:
    """Callback va matn uchun chiroyli ko‘rinish"""
    if float(x).is_integer():
        return str(int(x))
    return str(round(float(x), 2))


# ================= STATES =================
class AddService(StatesGroup):
    category = State()
    name = State()
    service_id = State()

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


# ================= START / ADMIN =================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum 👋", reply_markup=user_menu)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Admin panel 👑", reply_markup=admin_menu)
    else:
        await message.answer("❌ Siz admin emassiz")

@dp.message(F.text == "⬅ Ortga")
async def back_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu", reply_markup=user_menu)


# ================== ADMIN: KARTA QO‘SHISH =================
@dp.message(F.text == "💳 Karta qo‘shish")
async def add_card_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz")
    await message.answer("Kartaga nom bering:")
    await state.set_state(AddCard.name)

@dp.message(AddCard.name)
async def add_card_number(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Kartaning raqamini kiriting:")
    await state.set_state(AddCard.number)

@dp.message(AddCard.number)
async def save_card(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    number = message.text.strip()
    cards[name] = number
    await message.answer(f"✅ {name} kartasi qo‘shildi:\n`{number}`", parse_mode="Markdown")
    await state.clear()


# ================== ADMIN: XIZMAT QO‘SHISH =================
@dp.message(F.text == "➕ Xizmat qo‘shish")
async def add_category(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz")
    await message.answer("Kategoriya nomini kiriting (Telegram / Instagram / YouTube / TikTok):")
    await state.set_state(AddService.category)

@dp.message(AddService.category)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer("Xizmat nomini kiriting:")
    await state.set_state(AddService.name)

@dp.message(AddService.name)
async def add_service_id(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("API Service ID kiriting:")
    await state.set_state(AddService.service_id)

@dp.message(AddService.service_id)
async def save_service(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data["category"]
    name = data["name"]
    service_id = message.text.strip()

    payload = {"key": API_KEY, "action": "services"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=payload, timeout=30) as response:
                all_services = await response.json()
    except Exception as e:
        await message.answer(f"❌ API bilan ulanishda xatolik: {e}")
        await state.clear()
        return

    found = None
    for s in all_services:
        if str(s.get("service")) == str(service_id):
            found = s
            break

    if not found:
        await message.answer("❌ Service ID topilmadi")
        await state.clear()
        return

    services.setdefault(category, {})
    services[category][name] = {
        "id": str(service_id),
        "min": int(found.get("min", 0)),
        "max": int(found.get("max", 0)),
        "price": float(found.get("rate", 0))
    }

    await message.answer(
        f"✅ Xizmat qo‘shildi:\n"
        f"📦 Kategoriya: {category}\n"
        f"🛍 Xizmat: {name}\n"
        f"🆔 ID: {service_id}\n"
        f"📉 Min: {services[category][name]['min']}\n"
        f"📈 Max: {services[category][name]['max']}\n"
        f"💰 Narx: {services[category][name]['price']}"
    )
    await state.clear()


# ================== ADMIN: XIZMAT O‘CHIRISH =================
@dp.message(F.text == "❌ Xizmat o‘chirish")
async def delete_service_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz")

    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return

    buttons = []
    for category, cat_services in services.items():
        for name in cat_services:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{category} - {name}",
                    callback_data=cb("del", category, name)
                )
            ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("O‘chirmoqchi bo‘lgan xizmatni tanlang:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("del|"))
async def delete_service_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Admin emas!", show_alert=True)
        return

    _, category, name = callback.data.split("|", 2)

    if category in services and name in services[category]:
        del services[category][name]
        if not services[category]:
            del services[category]
        await callback.message.edit_text(f"✅ `{name}` xizmati o‘chirildi", parse_mode="Markdown")
    else:
        await callback.message.edit_text("❌ Bunday xizmat topilmadi")

    await callback.answer()


# ================== ADMIN: FOIZ QO‘SHISH =================
@dp.message(F.text == "💹 Foiz qo‘shish")
async def add_percent_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz")

    if not services:
        await message.answer("Hozircha xizmat yo‘q")
        return

    buttons = []
    for category, cat_services in services.items():
        for name in cat_services:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{category} - {name}",
                    callback_data=cb("percent", category, name)
                )
            ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Foiz qo‘shmoqchi bo‘lgan xizmatni tanlang:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("percent|"))
async def percent_service_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Admin emas!", show_alert=True)
        return

    _, category, name = callback.data.split("|", 2)
    await state.update_data(category=category, service=name)

    await callback.message.answer("Foiz miqdorini kiriting (%):")
    await state.set_state(AddPercent.percent)
    await callback.answer()

@dp.message(AddPercent.percent)
async def apply_percent(message: types.Message, state: FSMContext):
    try:
        percent = float(message.text.replace(",", "."))
    except:
        await message.answer("❌ Iltimos raqam kiriting")
        return

    data = await state.get_data()
    category = data["category"]
    service_name = data["service"]

    if category not in services or service_name not in services[category]:
        await message.answer("❌ Xizmat topilmadi (o‘chirilgan bo‘lishi mumkin)")
        await state.clear()
        return

    service = services[category][service_name]
    old_price = float(service["price"])
    new_price = old_price + (old_price * percent / 100.0)
    service["price"] = round(new_price, 2)

    await message.answer(f"✅ {service_name}\n💰 {old_price} ➡ {service['price']}")
    await state.clear()


# ================== USER: HISOB TO'LDIRISH =================
@dp.message(F.text == "💳 Hisob To'ldirish")
async def topup_start(message: types.Message, state: FSMContext):
    await message.answer("Qancha miqdorda to‘ldirmoqchisiz?")
    await state.set_state(TopUp.amount)

@dp.message(TopUp.amount)
async def topup_card(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError()
    except:
        await message.answer("❌ Iltimos to‘g‘ri raqam kiriting")
        return

    await state.update_data(amount=amount)

    if not cards:
        await message.answer("❌ Hozircha karta mavjud emas, admin bilan bog‘laning")
        await state.clear()
        return

    buttons = []
    for name in cards.keys():
        buttons.append([
            InlineKeyboardButton(text=name, callback_data=cb("card", name))
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("To‘lov qilish uchun kartani tanlang:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("card|"))
async def topup_comment(callback: types.CallbackQuery, state: FSMContext):
    _, card_name = callback.data.split("|", 1)
    await state.update_data(card=card_name)

    await callback.message.answer("Izoh qoldiring (ixtiyoriy):\nAgar izoh yo‘q bo‘lsa `-` yuboring.")
    await state.set_state(TopUp.comment)
    await callback.answer()

@dp.message(TopUp.comment)
async def topup_receipt(message: types.Message, state: FSMContext):
    comment = message.text.strip()
    await state.update_data(comment=comment)

    await message.answer("To‘lov чекини yuboring (rasm sifatida):")
    await state.set_state(TopUp.receipt)

# ✅ Aiogram 3: PHOTO filter
@dp.message(TopUp.receipt, F.photo)
async def send_to_admin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    amount = float(data["amount"])
    card_name = data["card"]
    comment = data.get("comment", "-")
    receipt_file_id = message.photo[-1].file_id

    # Admin tasdiqlash uchun inline tugmalar
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=cb("approve", str(user_id), fmt_amount(amount))
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=cb("reject", str(user_id), fmt_amount(amount))
                )
            ]
        ]
    )

    text = (
        "💳 To‘lov kelib tushdi!\n"
        f"👤 Foydalanuvchi: {user_name}\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Miqdor: {fmt_amount(amount)} so‘m\n"
        f"💳 Karta: {card_name}\n"
        f"📝 Izoh: {comment}"
    )

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=receipt_file_id,
        caption=text,
        reply_markup=keyboard
    )

    await message.answer("✅ To‘lovingiz adminga yuborildi. 12 soat ichida tasdiqlanadi.")
    await state.clear()

# Agar user rasm emas, boshqa narsa yuborsa:
@dp.message(TopUp.receipt)
async def receipt_not_photo(message: types.Message):
    await message.answer("❌ Iltimos чекni rasm (PHOTO) ko‘rinishida yuboring.")


# ================== ADMIN: TASDIQLASH / BEKOR QILISH =================
@dp.callback_query(F.data.startswith("approve|") | F.data.startswith("reject|"))
async def admin_approval(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Admin emas!", show_alert=True)
        return

    action, user_id_str, amount_str = callback.data.split("|", 2)
    user_id = int(user_id_str)
    amount = float(amount_str)

    if action == "approve":
        users_balance[user_id] = users_balance.get(user_id, 0) + amount

        await bot.send_message(user_id, f"✅ Hisobingiz {fmt_amount(amount)} so‘mga to‘ldirildi.")
        # Caption update
        if callback.message.caption:
            await callback.message.edit_caption(callback.message.caption + "\n✅ Tasdiqlandi")
        await callback.answer("Tasdiqlandi ✅")
    else:
        await bot.send_message(user_id, "❌ Admin to‘lovni qabul qilmadi.")
        if callback.message.caption:
            await callback.message.edit_caption(callback.message.caption + "\n❌ Bekor qilindi")
        await callback.answer("Bekor qilindi ❌")


# ================== MAIN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
