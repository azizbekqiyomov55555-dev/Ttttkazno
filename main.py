import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN
from database import db

from handlers import start, services, account, support

logging.basicConfig(level=logging.INFO)

async def main():
    await db.create_pool()
    await db.init_tables()
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    dp.include_routers(
        start.router,
        services.router,
        account.router,
        support.router,
    )
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
