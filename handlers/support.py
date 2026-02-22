from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "📞 Murojaat")
async def contact_admin(message: Message):
    await message.answer("📞 <b>Admin:</b> @your_admin")

@router.message(F.text == "🎧 Qo'llab-quvvatlash")
async def support(message: Message):
    await message.answer("🎧 <b>Support:</b> @support\n⏰ 24/7")

@router.message(F.text == "🤝 Hamkorlik")
async def partnership(message: Message):
    await message.answer("🤝 <b>Hamkorlik uchun:</b> @admin")

@router.message(F.text == "💰 Pul ishlash")
async def earn_money(message: Message):
    user = await db.get_user(message.from_user.id)
    await message.answer(
        f"💰 <b>Referral kodingiz:</b>\n"
        f"<code>{user['referral_code']}</code>\n\n"
        f"Har bir do'stingizdan 10% komissiya oling!"
    )

@router.message(F.text == "📱 Nomer olish")
async def get_number(message: Message):
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("📱 Raqamingizni yuboring:", reply_markup=keyboard)
