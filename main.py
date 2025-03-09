import logging
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config.config import Config
from database.db import setup_database
from handlers import start, pamphlets, books, videos, admin
from middlewares import BanMiddleware

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات Webhook
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("BASE_URL", "https://unibot-vfzt.onrender.com") + WEBHOOK_PATH
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

async def on_startup(bot: Bot):
    """تنظیم Webhook موقع شروع"""
    logger.info("Setting up webhook...")
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)

async def main():
    try:
        # تنظیمات اولیه
        logger.info("Starting bot...")
        config = Config()
        storage = MemoryStorage()
        bot = Bot(token=config.TOKEN)
        dp = Dispatcher(storage=storage)
        
        # اضافه کردن میدلور بن
        dp.message.middleware(BanMiddleware())
        
        # راه‌اندازی دیتابیس
        logger.info("Setting up database...")
        setup_database()
        
        # ثبت هندلرها
        logger.info("Registering handlers...")
        start.register_handlers(dp)
        books.register_handlers(dp)
        pamphlets.register_handlers(dp)
        videos.register_handlers(dp)
        admin.register_handlers(dp)
        
        # تنظیم Webhook
        dp.startup.register(on_startup)
        
        # تنظیم سرور aiohttp
        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        # شروع سرور
        logger.info(f"Starting webhook server on {WEBAPP_HOST}:{WEBAPP_PORT}...")
        await web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise e
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
