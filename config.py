import os
from dotenv import load_dotenv

load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API
API_URL = os.getenv("API_URL", "https://saleseen.uz/api/v2")
API_KEY = os.getenv("API_KEY")

# Admin
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Railway uchun DATABASE_URL (muhim!)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("⚠️ DATABASE_URL topilmadi! Railway'da PostgreSQL qo'shing.")

# Qo'shimcha
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

# Narxlar
SERVICE_PRICES = {
    "tg_subscribers": 50,
    "tg_views": 5,
    "tg_reactions": 30,
    "tg_comments": 100,
    "tg_reposts": 40,
    "ig_followers": 80,
    "ig_likes": 20,
    "ig_views": 10,
    "tt_followers": 60,
    "tt_likes": 15,
    "tt_views": 8,
    "yt_subscribers": 100,
    "yt_views": 12,
    "yt_likes": 25,
}

print("✅ Config yuklandi")
if DEBUG:
    print(f" Debug mode: {DEBUG}")
    print(f"📡 API URL: {API_URL}")
