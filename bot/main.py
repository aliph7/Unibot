import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import Config
from database.db import setup_database
from handlers import start, pamphlets, books, videos

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        # تنظیمات اولیه
        logger.info("Starting bot...")
        config = Config()
        storage = MemoryStorage()
        bot = Bot(token=config.TOKEN)
        dp = Dispatcher(storage=storage)
        
        # راه‌اندازی دیتابیس
        logger.info("Setting up database...")
        setup_database()
        
        # ثبت هندلرها
        logger.info("Registering handlers...")
        start.register_handlers(dp)
        books.register_handlers(dp)
        pamphlets.register_handlers(dp)
        videos.register_handlers(dp)
        
        # شروع پولینگ
        logger.info("Bot is running...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise e
    finally:
        logger.info("Bot stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!") 