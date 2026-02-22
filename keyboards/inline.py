from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish"))
    builder.row(KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="💰 Pul ishlash"))
    builder.row(KeyboardButton(text="💳 Hisobim"), KeyboardButton(text="💵 Hisob To'ldirish"))
    builder.row(KeyboardButton(text="📞 Murojaat"), KeyboardButton(text="🎧 Qo'llab-quvvatlash"))
    builder.row(KeyboardButton(text="🤝 Hamkorlik"))
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def services_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔵 Telegram", callback_data="service_telegram"),
        InlineKeyboardButton(text="🟣 Instagram", callback_data="service_instagram")
    )
    builder.row(
        InlineKeyboardButton(text="⚫ TikTok", callback_data="service_tiktok"),
        InlineKeyboardButton(text="🔴 YouTube", callback_data="service_youtube")
    )
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_main"))
    return builder.as_markup()

def telegram_services_keyboard():
    builder = InlineKeyboardBuilder()
    services = [
        ("👥 Obunachilar", "tg_subscribers"),
        ("👁 Ko'rishlar", "tg_views"),
        ("❤️ Reaksiyalar", "tg_reactions"),
        ("💬 Kommentariyalar", "tg_comments"),
        ("🔄 Repostlar", "tg_reposts"),
    ]
    for text, callback in services:
        builder.button(text=text, callback_data=callback)
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_services"))
    return builder.as_markup()

def instagram_services_keyboard():
    builder = InlineKeyboardBuilder()
    services = [
        ("👥 Followers", "ig_followers"),
        ("❤️ Likes", "ig_likes"),
        ("👁 Views", "ig_views"),
        ("💬 Comments", "ig_comments"),
    ]
    for text, callback in services:
        builder.button(text=text, callback_data=callback)
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_services"))
    return builder.as_markup()

def tiktok_services_keyboard():
    builder = InlineKeyboardBuilder()
    services = [
        ("👥 Followers", "tt_followers"),
        ("❤️ Likes", "tt_likes"),
        ("👁 Views", "tt_views"),
        ("💬 Comments", "tt_comments"),
    ]
    for text, callback in services:
        builder.button(text=text, callback_data=callback)
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_services"))
    return builder.as_markup()

def youtube_services_keyboard():
    builder = InlineKeyboardBuilder()
    services = [
        ("👥 Subscribers", "yt_subscribers"),
        ("👁 Views", "yt_views"),
        ("❤️ Likes", "yt_likes"),
        ("💬 Comments", "yt_comments"),
    ]
    for text, callback in services:
        builder.button(text=text, callback_data=callback)
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_services"))
    return builder.as_markup()

def payment_methods_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Click/Payme", callback_data="pay_click"),
        InlineKeyboardButton(text="🏦 Karta", callback_data="pay_card")
    )
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_main"))
    return builder.as_markup()

def back_keyboard(callback_data="back_main"):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Orqaga", callback_data=callback_data))
    return builder.as_markup()
