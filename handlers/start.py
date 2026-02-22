from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from keyboards.inline import main_menu_keyboard
import random
import string

router = Router()

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    referral_code = generate_referral_code()
    referred_by = None
    
    args = message.text.split()
    if len(args) > 1:
        ref_code = args[1]
        if ref_code != referral_code:
            referred_by = await get_user_by_referral(ref_code)
    
    await db.add_user(user_id, username, first_name, referral_code, referred_by)
    
    text = f"""
👋 <b>Assalomu alaykum, {first_name}!</b>

🎯 <b>SMM xizmatlarimizga xush kelibsiz!</b>

📊 <b>Bizning xizmatlar:</b>
• Telegram, Instagram, TikTok, YouTube
• Obunachilar, like, ko'rishlar
• Tez va sifatli xizmat
• 24/7 qo'llab-quvvatlash

👇 Quyidagi tugmalardan birini tanlang:
    """
    
    await message.answer(text, reply_markup=main_menu_keyboard())

async def get_user_by_referral(code):
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow('SELECT user_id FROM users WHERE referral_code = $1', code)
        return user['user_id'] if user else None
