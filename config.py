from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
API_URL = getenv("API_URL", "https://saleseen.uz/api/v2")
API_KEY = getenv("API_KEY", "your_api_key")

DB_USER = getenv("DB_USER", "postgres")
DB_PASSWORD = getenv("DB_PASSWORD", "postgres")
DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = getenv("DB_PORT", "5432")
DB_NAME = getenv("DB_NAME", "smm_bot")

ADMIN_ID = int(getenv("ADMIN_ID", "123456789"))
