import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config.config import Config
from database.db import setup_database
from handlers.start import register_handlers as register_start_handlers
from handlers.pamphlets import register_handlers as register_pamphlets_handlers
from handlers.books import register_handlers as register_books_handlers
from handlers.videos import register_handlers as register_videos_handlers
from handlers.admin import register_handlers as register_admin_handlers
from middlewares import BanMiddleware
from handlers.ai import register_handlers as register_ai_handlers

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات Webhook
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("BASE_URL", "https://unibot-vfzt.onrender.com") + WEBHOOK_PATH
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

async def on_startup(bot: Bot):
    logger.info("Setting up webhook...")
    await bot.set_webhook(url=WEBHOOK_URL)

# تابع جدید برای پینگ
async def handle_ping(request):
    logger.info("Received ping request")
    return web.Response(text="Pong", status=200)

def main():
    try:
        logger.info("Starting bot...")
        config = Config()
        storage = MemoryStorage()
        bot = Bot(token=config.TOKEN)
        dp = Dispatcher(storage=storage)
        
        # اضافه کردن میدلور بن
        dp.message.middleware(BanMiddleware())
        
        logger.info("Setting up database...")
        setup_database()
        
        logger.info("Registering handlers...")
        register_start_handlers(dp)
        register_books_handlers(dp)
        register_pamphlets_handlers(dp)
        register_videos_handlers(dp)
        register_admin_handlers(dp)
        register_ai_handlers(dp)
        
        dp.startup.register(on_startup)
        
        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=WEBHOOK_PATH)
        app.router.add_get("/ping", handle_ping)  # اضافه کردن مسیر پینگ
        setup_application(app, dp, bot=bot)
        
        logger.info(f"Starting webhook server on {WEBAPP_HOST}:{WEBAPP_PORT}...")
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise e
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
