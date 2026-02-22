from aiogram import Router, F
from aiogram.types import Message
from database import db
from keyboards.inline import payment_methods_keyboard, back_keyboard

router = Router()

@router.message(F.text == "💳 Hisobim")
async def show_account(message: Message):
    user = await db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi")
        return
    
    text = f"""
💳 <b>Sizning hisobingiz</b>

👤 Ism: {user['first_name']}
💰 Balans: {user['balance']} so'm
🎫 Referral: <code>{user['referral_code']}</code>
    """
    
    await message.answer(text, reply_markup=back_keyboard())

@router.message(F.text == "💵 Hisob To'ldirish")
async def top_up_account(message: Message):
    await message.answer(
        "💵 <b>Hisobni to'ldirish</b>\n\n💳 Usulni tanlang:",
        reply_markup=payment_methods_keyboard()
    )

@router.message(F.text == "🛒 Buyurtmalarim")
async def show_orders(message: Message):
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("📭 Hali buyurtmalar yo'q")
        return
    
    text = "🛒 <b>Sizning buyurtmalaringiz</b>\n\n"
    for order in orders[:10]:
        text += f"🔢 #{order['order_id']} - {order['service_type']} ({order['quantity']} dona) - {order['price']} so'm\n"
    
    await message.answer(text)
