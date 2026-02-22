from aiogram import Router, F
from aiogram.types import Message
from config import ADMIN_ID

router = Router()

@router.message(F.text == "📞 Murojaat")
async def contact_admin(message: Message):
    text = """
📞 <b>Admin bilan bog'lanish</b>

📝 Xabaringizni yozing:
    """
    await message.answer(text)

@router.message(F.text == "🎧 Qo'llab-quvvatlash")
async def support(message: Message):
    text = """
🎧 <b>Qo'llab-quvvatlash xizmati</b>

📱 Biz bilan bog'laning:
• @support_username
• Telefon: +998 90 123 45 67

⏰ Ish vaqti: 24/7
    """
    await message.answer(text)

@router.message(F.text == "🤝 Hamkorlik")
async def partnership(message: Message):
    text = """
🤝 <b>Hamkorlik</b>

💼 Biz bilan hamkorlik qilish uchun:

✅ Referral dasturi - 10%
✅ Reseller imkoniyatlari
✅ API access
✅ Maxsus chegirmalar

📩 Batafsil ma'lumot uchun:
@admin_username
    """
    await message.answer(text)

@router.message(F.text == "💰 Pul ishlash")
async def earn_money(message: Message):
    user = await db.get_user(message.from_user.id)
    
    text = f"""
💰 <b>Pul ishlash</b>

👥 <b>Referral tizimi:</b>

Sizning kodingiz: <code>{user['referral_code']}</code>

💵 Har bir taklif qilingan do'stingizdan:
• 10% komissiya
• Doimiy daromad
• Cheksiz imkoniyat

📊 <b>Statistika:</b>
• Taklif qilinganlar: 0
• Ishlangan: 0 so'm

🔗 Havolani do'stlaringizga yuboring:
t.me/{(await message.bot.get_me()).username}?start={user['referral_code']}
    """
    await message.answer(text)

@router.message(F.text == "📱 Nomer olish")
async def get_number(message: Message):
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer(
        "📱 <b>Raqamingizni yuboring</b>\n\n"
        "Bu xizmatlar uchun kerak bo'ladi",
        reply_markup=keyboard
    )
