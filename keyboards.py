from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ─── User Keyboards ───────────────────────────────────────────────
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔥 Chegirmalar"), KeyboardButton(text="📦 Mahsulotlar")],
            [KeyboardButton(text="🔔 Obuna"), KeyboardButton(text="👤 Profilim")],
        ],
        resize_keyboard=True
    )

def share_phone():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ─── Admin Keyboards ──────────────────────────────────────────────
def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="📋 Mahsulotlar ro'yxati")],
            [KeyboardButton(text="📢 Xabar yuborish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="🔙 Chiqish")],
        ],
        resize_keyboard=True
    )

def product_list_inline(products):
    buttons = []
    for p in products:
        pid, name, op, sp, disc, desc, img, active, created = p
        buttons.append([InlineKeyboardButton(
            text=f"❌ {name} ({disc}% off)",
            callback_data=f"del_product_{pid}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
