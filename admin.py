from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import admin_menu, main_menu, product_list_inline
from config import ADMIN_IDS

router = Router()

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ─── States ───────────────────────────────────────────────────────
class AddProduct(StatesGroup):
    name = State()
    original_price = State()
    sale_price = State()
    description = State()
    image = State()

class Broadcast(StatesGroup):
    message = State()

# ─── Admin panel ──────────────────────────────────────────────────
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ Sizda admin huquqi yo'q.")
    await message.answer("👑 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_menu())

@router.message(F.text == "🔙 Chiqish")
async def exit_admin(message: Message):
    await message.answer("Asosiy menyu:", reply_markup=main_menu())

# ─── Statistika ───────────────────────────────────────────────────
@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    if not is_admin(message.from_user.id):
        return
    count = await db.count_users()
    products = await db.get_active_products()
    await message.answer(
        f"📊 <b>Statistika:</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{count}</b>\n"
        f"📦 Faol mahsulotlar: <b>{len(products)}</b>",
        parse_mode="HTML"
    )

# ─── Foydalanuvchilar ro'yxati ────────────────────────────────────
@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = await db.get_all_users()
    if not users:
        return await message.answer("Foydalanuvchilar yo'q.")
    
    text = "👥 <b>Foydalanuvchilar:</b>\n\n"
    for u in users[:20]:
        tid, tgid, uname, fname, phone, reg_at, sub = u
        text += f"• {fname} | @{uname or '-'} | {phone or '-'}\n"
    
    if len(users) > 20:
        text += f"\n... va yana {len(users)-20} ta"
    
    await message.answer(text, parse_mode="HTML")

# ─── Mahsulot qo'shish ────────────────────────────────────────────
@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddProduct.name)
    await message.answer("📦 Mahsulot nomini kiriting:")

@router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.original_price)
    await message.answer("💰 Asl narxini kiriting (so'mda):")

@router.message(AddProduct.original_price)
async def add_product_oprice(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "").replace(" ", ""))
        await state.update_data(original_price=price)
        await state.set_state(AddProduct.sale_price)
        await message.answer("🏷 Chegirmali narxini kiriting:")
    except ValueError:
        await message.answer("❌ Iltimos, raqam kiriting:")

@router.message(AddProduct.sale_price)
async def add_product_sprice(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "").replace(" ", ""))
        await state.update_data(sale_price=price)
        await state.set_state(AddProduct.description)
        await message.answer("📝 Tavsif kiriting (yoki 'o'tkazib yuborish' yozing):")
    except ValueError:
        await message.answer("❌ Iltimos, raqam kiriting:")

@router.message(AddProduct.description)
async def add_product_desc(message: Message, state: FSMContext):
    desc = None if message.text.lower() in ["o'tkazib yuborish", "skip"] else message.text
    await state.update_data(description=desc)
    await state.set_state(AddProduct.image)
    await message.answer("🖼 Rasm yuboring (yoki 'o'tkazib yuborish' yozing):")

@router.message(AddProduct.image)
async def add_product_image(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    image_id = None
    if message.photo:
        image_id = message.photo[-1].file_id
    
    await db.add_product(
        name=data["name"],
        original_price=data["original_price"],
        sale_price=data["sale_price"],
        description=data.get("description"),
        image_url=image_id
    )
    await state.clear()
    
    discount = round((data["original_price"] - data["sale_price"]) / data["original_price"] * 100, 1)
    await message.answer(
        f"✅ <b>Mahsulot qo'shildi!</b>\n\n"
        f"📦 {data['name']}\n"
        f"💰 {data['original_price']:,.0f} → {data['sale_price']:,.0f} so'm ({discount}% chegirma)\n\n"
        "📢 Foydalanuvchilarga xabar yuborishni xohlaysizmi? /broadcast buyrug'ini ishlating.",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )

# ─── Mahsulotlar ro'yxati ─────────────────────────────────────────
@router.message(F.text == "📋 Mahsulotlar ro'yxati")
async def products_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    products = await db.get_all_products()
    if not products:
        return await message.answer("📦 Mahsulotlar yo'q.")
    
    active = [p for p in products if p[7] == 1]
    await message.answer(
        f"📋 <b>Jami: {len(products)} ta | Faol: {len(active)} ta</b>\n\nO'chirish uchun bosing:",
        parse_mode="HTML",
        reply_markup=product_list_inline(active)
    )

@router.callback_query(F.data.startswith("del_product_"))
async def delete_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[-1])
    await db.delete_product(product_id)
    await callback.answer("✅ Mahsulot o'chirildi!")
    await callback.message.edit_text("✅ Mahsulot muvaffaqiyatli o'chirildi.")

# ─── Broadcast ────────────────────────────────────────────────────
@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(Broadcast.message)
    await message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:")

@router.message(Broadcast.message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await db.get_all_subscribed_users()
    
    sent = 0
    failed = 0
    
    await message.answer(f"⏳ {len(users)} ta foydalanuvchiga yuborilmoqda...")
    
    for user in users:
        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=user[0],
                    photo=message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            else:
                await bot.send_message(chat_id=user[0], text=message.text)
            sent += 1
        except Exception:
            failed += 1
    
    await message.answer(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"📤 Muvaffaqiyatli: {sent}\n"
        f"❌ Xatolik: {failed}",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )
