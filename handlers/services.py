from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards.inline import (
    services_keyboard, telegram_services_keyboard,
    instagram_services_keyboard, tiktok_services_keyboard,
    youtube_services_keyboard, back_keyboard
)
from config import SERVICE_PRICES

router = Router()

class OrderState(StatesGroup):
    platform = State()
    service = State()
    link = State()
    quantity = State()
    confirm = State()

@router.message(F.text == "🛍 Xizmatlar")
async def show_services(message: Message):
    text = "🛍 <b>Xizmatlarimiz</b>\n\n📱 Ijtimoiy tarmoqni tanlang:"
    await message.answer(text, reply_markup=services_keyboard())

@router.callback_query(F.data == "service_telegram")
async def telegram_services(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔵 <b>Telegram xizmatlari</b>\n\nKerakli xizmatni tanlang:",
        reply_markup=telegram_services_keyboard()
    )

@router.callback_query(F.data == "service_instagram")
async def instagram_services(callback: CallbackQuery):
    await callback.message.edit_text(
        "🟣 <b>Instagram xizmatlari</b>\n\nKerakli xizmatni tanlang:",
        reply_markup=instagram_services_keyboard()
    )

@router.callback_query(F.data == "service_tiktok")
async def tiktok_services(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚫ <b>TikTok xizmatlari</b>\n\nKerakli xizmatni tanlang:",
        reply_markup=tiktok_services_keyboard()
    )

@router.callback_query(F.data == "service_youtube")
async def youtube_services(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔴 <b>YouTube xizmatlari</b>\n\nKerakli xizmatni tanlang:",
        reply_markup=youtube_services_keyboard()
    )

@router.callback_query(F.data.startswith(("tg_", "ig_", "tt_", "yt_")))
async def service_selected(callback: CallbackQuery, state: FSMContext):
    service_data = callback.data.split("_")
    platform = service_data[0]
    service = service_data[1]
    
    await state.update_data(platform=platform, service=service)
    
    platform_names = {"tg": "Telegram", "ig": "Instagram", "tt": "TikTok", "yt": "YouTube"}
    
    await callback.message.answer(
        f"📎 <b>{platform_names[platform]} - {service}</b>\n\n🔗 Havolani yuboring:",
        reply_markup=back_keyboard("back_services")
    )
    await state.set_state(OrderState.link)

@router.message(OrderState.link)
async def process_link(message: Message, state: FSMContext):
    link = message.text
    
    if not link.startswith(("https://", "http://")):
        await message.answer("❌ <b>Noto'g'ri havola!</b>")
        return
    
    await state.update_data(link=link)
    await message.answer(
        "📊 <b>Miqdorni kiriting</b>\n\nMasalan: 100, 1000, 10000",
        reply_markup=back_keyboard("back_services")
    )
    await state.set_state(OrderState.quantity)

@router.message(OrderState.quantity)
async def process_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity < 10:
            await message.answer("❌ <b>Minimal miqdor: 10</b>")
            return
    except ValueError:
        await message.answer("❌ <b>Faqat raqam kiriting!</b>")
        return
    
    data = await state.get_data()
    price = calculate_price(data.get("platform"), data.get("service"), quantity)
    await state.update_data(quantity=quantity, price=price)
    
    user = await db.get_user(message.from_user.id)
    balance = float(user['balance']) if user else 0
    
    await message.answer(
        f"✅ <b>Buyurtma tasdiqlash</b>\n\n"
        f"📊 Miqdor: {quantity}\n"
        f"💰 Narx: {price} so'm\n"
        f"💳 Balans: {balance} so'm\n\n"
        f"Tasdiqlash uchun '✅ Tasdiqlash' deb yozing",
        reply_markup=back_keyboard("back_services")
    )
    await state.set_state(OrderState.confirm)

@router.message(OrderState.confirm, F.text == "✅ Tasdiqlash")
async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    balance = float(user['balance']) if user else 0
    
    if balance < data.get("price", 0):
        await message.answer("❌ <b>Balans yetarli emas!</b>")
        await state.clear()
        return
    
    order_id = await db.add_order(
        user_id=user_id,
        service_type=data.get("service"),
        platform=data.get("platform"),
        link=data.get("link"),
        quantity=data.get("quantity"),
        price=data.get("price")
    )
    
    await db.update_balance(user_id, -data.get("price"))
    await db.add_transaction(user_id, -data.get("price"), "order", f"Buyurtma #{order_id}")
    
    await message.answer(f"✅ <b>Buyurtma #{order_id} qabul qilindi!</b>")
    await state.clear()

def calculate_price(platform, service, quantity):
    key = f"{platform}_{service}"
    price_per_1000 = SERVICE_PRICES.get(key, 50)
    return (quantity * price_per_1000) / 1000

@router.callback_query(F.data == "back_services")
async def back_to_services(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛍 <b>Xizmatlar</b>\n\n📱 Tanlang:",
        reply_markup=services_keyboard()
    )

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    from keyboards.inline import main_menu_keyboard
    await callback.message.edit_text(
        "🏠 <b>Bosh sahifa</b>",
        reply_markup=main_menu_keyboard()
    )
