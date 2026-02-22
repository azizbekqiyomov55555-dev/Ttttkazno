import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN, DEBUG
from database import db
from handlers import start, services, account, support

logging.basicConfig(level=logging.INFO)

async def main():
    # Database ulanish
    await db.create_pool()
    await db.init_tables()
    
    # Bot yaratish
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Routerlarni qo'shish
    dp.include_routers(
        start.router,
        services.router,
        account.router,
        support.router,
    )
    
    print("🤖 Bot ishga tushdi...")
    
    # Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
