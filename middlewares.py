from aiogram import BaseMiddleware
from aiogram.types import Message
from database.db import is_user_banned
import logging

logger = logging.getLogger(__name__)

class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        if is_user_banned(user_id):
            logger.info(f"Blocked message from banned user: {user_id}")
            await event.answer("❌ شما بن شدید و نمی‌تونید با ربات تعامل کنید!")
            return  # پیام به هندلر نمی‌ره
        # اگه بن نباشه، پیام به هندلر می‌ره
        return await handler(event, data)
