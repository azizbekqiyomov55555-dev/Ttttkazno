from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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

👤 <b>Ism:</b> {user['first_name']}
🆔 <b>ID:</b> <code>{user['user_id']}</code>
💰 <b>Balans:</b> {user['balance']} so'm

📊 <b>Statistika:</b>
• Jami buyurtmalar: {await get_user_orders_count(message.from_user.id)}
• referral kod: <code>{user['referral_code']}</code>
    """
    
    await message.answer(text, reply_markup=back_keyboard())

@router.message(F.text == "💵 Hisob To'ldirish")
async def top_up_account(message: Message):
    text = """
💵 <b>Hisobni to'ldirish</b>

💳 To'lov usulini tanlang:
    """
    await message.answer(text, reply_markup=payment_methods_keyboard())

@router.callback_query(F.data.startswith("pay_"))
async def payment_method_selected(callback: CallbackQuery):
    method = callback.data.replace("pay_", "")
    
    methods = {
        "click": "💳 Click/Payme",
        "card": "🏦 Karta",
        "cash": "💵 Naqd",
        "crypto": "🔄 Crypto"
    }
    
    await callback.message.answer(
        f"💰 <b>To'lov summasini kiriting</b>\n\n"
        f"Tanlangan usul: {methods[method]}\n\n"
        f"<i>Minimal: 10,000 so'm</i>",
        reply_markup=back_keyboard("back_main")
    )

@router.message(F.text == "🛒 Buyurtmalarim")
async def show_orders(message: Message):
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("📭 <b>Hali buyurtmalar yo'q</b>")
        return
    
    text = "🛒 <b>Sizning buyurtmalaringiz</b>\n\n"
    
    for order in orders[:10]:
        status_emoji = {"pending": "⏳", "completed": "✅", "processing": "🔄", "cancelled": "❌"}
        text += f"""
🔢 <b>#{order['order_id']}</b>
📱 {order['platform'].upper()} - {order['service_type']}
📊 {order['quantity']} dona
💰 {order['price']} so'm
{status_emoji.get(order['status'], "⏳")} {order['status']}
-------------------
"""
    
    await message.answer(text)

async def get_user_orders_count(user_id):
    orders = await db.get_user_orders(user_id)
    return len(orders)
