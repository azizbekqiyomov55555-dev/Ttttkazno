from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards.inline import (
    services_keyboard, telegram_services_keyboard,
    instagram_services_keyboard, tiktok_services_keyboard,
    youtube_services_keyboard, back_keyboard
)
import aiohttp
from config import API_URL, API_KEY

router = Router()

class OrderState(StatesGroup):
    platform = State()
    service = State()
    link = State()
    quantity = State()
    confirm = State()

@router.message(F.text == "🛍 Xizmatlar")
async def show_services(message: Message):
    text = """
🛍 <b>Xizmatlarimiz</b>

📱 Quyidagi ijtimoiy tarmoqlardan birini tanlang:
    """
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
    
    platform_names = {
        "tg": "Telegram", "ig": "Instagram",
        "tt": "TikTok", "yt": "YouTube"
    }
    
    await callback.message.answer(
        f"📎 <b>{platform_names[platform]} - {service}</b>\n\n"
        "🔗 Havolani yuboring:",
        reply_markup=back_keyboard("back_services")
    )
    await state.set_state(OrderState.link)

@router.message(OrderState.link)
async def process_link(message: Message, state: FSMContext):
    link = message.text
    
    if not link.startswith(("https://", "http://")):
        await message.answer("❌ <b>Noto'g'ri havola! http:// yoki https:// bilan boshlang</b>")
        return
    
    await state.update_data(link=link)
    await message.answer(
        "📊 <b>Miqdorni kiriting</b>\n\n"
        "Masalan: 100, 1000, 10000",
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
    platform = data.get("platform")
    service = data.get("service")
    
    price = calculate_price(platform, service, quantity)
    await state.update_data(quantity=quantity, price=price)
    
    await message.answer(
        f"✅ <b>Buyurtma tasdiqlash</b>\n\n"
        f"📱 Platforma: {platform.upper()}\n"
        f"🎯 Xizmat: {service}\n"
        f"🔗 Havola: {data.get('link')}\n"
        f"📊 Miqdor: {quantity}\n"
        f"💰 Narx: {price} so'm\n\n"
        f"💳 Balansingiz: {await get_user_balance(message.from_user.id)} so'm\n\n"
        f"<i>Tasdiqlash uchun '✅ Tasdiqlash' deb yozing yoki /cancel</i>",
        reply_markup=back_keyboard("back_services")
    )
    await state.set_state(OrderState.confirm)

@router.message(OrderState.confirm, F.text == "✅ Tasdiqlash")
async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    balance = await get_user_balance(user_id)
    
    if balance < data.get("price", 0):
        await message.answer("❌ <b>Balansingiz yetarli emas! Hisobni to'ldiring</b>")
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
    
    await db.add_transaction(
        user_id=user_id,
        amount=-data.get("price"),
        type_="order",
        description=f"Buyurtma #{order_id}"
    )
    
    await message.answer(
        f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
        f"🔢 Buyurtma raqami: #{order_id}\n"
        f"💰 Summa: {data.get('price')} so'm\n\n"
        f"🕐 Buyurtma ishga tushirildi..."
    )
    await state.clear()

@router.message(OrderState.confirm, F.text == "/cancel")
async def cancel_order(message: Message, state: FSMContext):
    await message.answer("❌ <b>Buyurtma bekor qilindi</b>")
    await state.clear()

def calculate_price(platform, service, quantity):
    prices = {
        "tg_subscribers": 50,
        "tg_views": 5,
        "tg_reactions": 30,
        "tg_comments": 100,
        "tg_reposts": 40,
        "tg_profile_views": 10,
        "ig_followers": 80,
        "ig_likes": 20,
        "ig_views": 10,
        "ig_comments": 150,
        "tt_followers": 60,
        "tt_likes": 15,
        "tt_views": 8,
        "tt_comments": 120,
        "yt_subscribers": 100,
        "yt_views": 12,
        "yt_likes": 25,
        "yt_comments": 200,
    }
    key = f"{platform}_{service}"
    price_per_item = prices.get(key, 50)
    return (quantity * price_per_item) / 1000

async def get_user_balance(user_id):
    user = await db.get_user(user_id)
    return float(user['balance']) if user else 0

@router.callback_query(F.data == "back_services")
async def back_to_services(callback: CallbackQuery):
    text = "🛍 <b>Xizmatlarimiz</b>\n\n📱 Ijtimoiy tarmoqni tanlang:"
    await callback.message.edit_text(text, reply_markup=services_keyboard())

@router.callback_query(F.data == "back_main")
async def back_to_main_menu(callback: CallbackQuery):
    from handlers.start import main_menu_keyboard
    text = "🏠 <b>Bosh sahifa</b>"
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
