import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

# Bot tokeni
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API sozlamalari
API_URL = os.getenv("API_URL", "https://saleseen.uz/api/v2")
API_KEY = os.getenv("API_KEY")

# Database sozlamalari
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "smm_bot")

# Admin ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Database URL ni yaratish
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Agar DATABASE_URL berilmagan bo'lsa, alohida parametrlardan yaratamiz
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

# To'lov tizimlari
PAYMENT_ENABLED = os.getenv("PAYMENT_ENABLED", "True").lower() == "true"

# Referral bonus (foiz)
REFERRAL_BONUS_PERCENT = float(os.getenv("REFERRAL_BONUS_PERCENT", "10"))

# Minimal to'lov summasi
MIN_PAYMENT_AMOUNT = int(os.getenv("MIN_PAYMENT_AMOUNT", "10000"))

# Xizmat narxlari (so'mda)
SERVICE_PRICES = {
    # Telegram
    "tg_subscribers": int(os.getenv("TG_SUBSCRIBERS_PRICE", "50")),
    "tg_views": int(os.getenv("TG_VIEWS_PRICE", "5")),
    "tg_reactions": int(os.getenv("TG_REACTIONS_PRICE", "30")),
    "tg_comments": int(os.getenv("TG_COMMENTS_PRICE", "100")),
    "tg_reposts": int(os.getenv("TG_REPOSTS_PRICE", "40")),
    "tg_profile_views": int(os.getenv("TG_PROFILE_VIEWS_PRICE", "10")),
    
    # Instagram
    "ig_followers": int(os.getenv("IG_FOLLOWERS_PRICE", "80")),
    "ig_likes": int(os.getenv("IG_LIKES_PRICE", "20")),
    "ig_views": int(os.getenv("IG_VIEWS_PRICE", "10")),
    "ig_comments": int(os.getenv("IG_COMMENTS_PRICE", "150")),
    
    # TikTok
    "tt_followers": int(os.getenv("TT_FOLLOWERS_PRICE", "60")),
    "tt_likes": int(os.getenv("TT_LIKES_PRICE", "15")),
    "tt_views": int(os.getenv("TT_VIEWS_PRICE", "8")),
    "tt_comments": int(os.getenv("TT_COMMENTS_PRICE", "120")),
    
    # YouTube
    "yt_subscribers": int(os.getenv("YT_SUBSCRIBERS_PRICE", "100")),
    "yt_views": int(os.getenv("YT_VIEWS_PRICE", "12")),
    "yt_likes": int(os.getenv("YT_LIKES_PRICE", "25")),
    "yt_comments": int(os.getenv("YT_COMMENTS_PRICE", "200")),
}

# Bot sozlamalari
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@admin")

# Session sozlamalari
SESSION_STRING = os.getenv("SESSION_STRING")

# Redis (agar kerak bo'lsa)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Webhook sozlamalari
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

# Polling yoki Webhook
USE_POLLING = os.getenv("USE_POLLING", "True").lower() == "true"

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Maxsus xabarlar
WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", """
👋 <b>Assalomu alaykum!</b>

🎯 <b>SMM xizmatlarimizga xush kelibsiz!</b>

📊 <b>Bizning xizmatlar:</b>
• Telegram, Instagram, TikTok, YouTube
• Obunachilar, like, ko'rishlar
• Tez va sifatli xizmat
• 24/7 qo'llab-quvvatlash

👇 Menyudan kerakli bo'limni tanlang!
""")

# Tekshirish
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida ko'rsatilmagan!")

# Ma'lumotlarni chop etish (debug uchun)
if DEBUG:
    print(f"🤖 Bot token: {'✅' if BOT_TOKEN else '❌'}")
    print(f"📡 API URL: {API_URL}")
    print(f"💾 Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"🔧 Debug mode: {DEBUG}")
