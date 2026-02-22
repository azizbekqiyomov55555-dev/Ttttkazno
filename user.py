from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import main_menu, share_phone

router = Router()

# ─── /start ──────────────────────────────────────────────────────
@router.message(CommandStart())
async def start(message: Message):
    user = await db.get_user(message.from_user.id)
    
    await db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    if not user or not user[4]:  # phone not set
        await message.answer(
            f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n"
            "📱 Ro'yxatdan o'tish uchun telefon raqamingizni ulashing:",
            parse_mode="HTML",
            reply_markup=share_phone()
        )
    else:
        await message.answer(
            f"👋 Xush kelibsiz, <b>{message.from_user.first_name}</b>!\n\n"
            "🔥 Eng so'nggi chegirmalardan xabardor bo'ling!",
            parse_mode="HTML",
            reply_markup=main_menu()
        )

# ─── Phone contact ────────────────────────────────────────────────
@router.message(F.contact)
async def get_contact(message: Message):
    phone = message.contact.phone_number
    await db.update_user_phone(message.from_user.id, phone)
    await message.answer(
        "✅ <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
        "🔔 Endi chegirmalar haqida bildirishnomalar olasiz.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ─── Chegirmalar ──────────────────────────────────────────────────
@router.message(F.text == "🔥 Chegirmalar")
async def show_sales(message: Message):
    products = await db.get_active_products()
    if not products:
        await message.answer("😔 Hozircha chegirmali mahsulotlar yo'q.")
        return
    
    await message.answer("🔥 <b>Joriy chegirmalar:</b>", parse_mode="HTML")
    for p in products:
        pid, name, op, sp, disc, desc, img, active, created = p
        text = (
            f"🏷 <b>{name}</b>\n"
            f"💰 Narx: <s>{op:,.0f} so'm</s> → <b>{sp:,.0f} so'm</b>\n"
            f"🎯 Chegirma: <b>{disc}%</b>\n"
            f"📝 {desc or ''}"
        )
        if img:
            await message.answer_photo(photo=img, caption=text, parse_mode="HTML")
        else:
            await message.answer(text, parse_mode="HTML")

# ─── Mahsulotlar ──────────────────────────────────────────────────
@router.message(F.text == "📦 Mahsulotlar")
async def show_products(message: Message):
    await show_sales(message)

# ─── Profil ───────────────────────────────────────────────────────
@router.message(F.text == "👤 Profilim")
async def profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if user:
        tid, tgid, uname, fname, phone, reg_at, subscribed = user
        sub_status = "✅ Faol" if subscribed else "❌ O'chirilgan"
        await message.answer(
            f"👤 <b>Profilingiz:</b>\n\n"
            f"📛 Ism: {fname}\n"
            f"📱 Telefon: {phone or 'Kiritilmagan'}\n"
            f"🔔 Obuna: {sub_status}\n"
            f"📅 Ro'yxatdan o'tgan: {reg_at[:10]}",
            parse_mode="HTML"
        )

# ─── Obuna ────────────────────────────────────────────────────────
@router.message(F.text == "🔔 Obuna")
async def subscription(message: Message):
    await message.answer(
        "🔔 <b>Bildirishnomalar</b>\n\n"
        "Chegirmalar e'lon qilinganda avtomatik xabar olasiz.\n"
        "Hozirda obunangiz <b>faol</b> ✅",
        parse_mode="HTML"
    )
