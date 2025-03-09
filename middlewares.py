from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from database.db import is_user_banned
from config.config import Config

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # چک کردن وضعیت بن کاربر
        user_id = event.from_user.id
        
        # اگر کاربر بن شده باشد
        if is_user_banned(user_id):
            await event.answer(
                "⛔️ شما از استفاده از ربات محروم شده‌اید!\n\n"
                f"📩 برای رفع محرومیت با ادمین در ارتباط باشید: @{Config.ADMIN_USERNAME}"
            )
            return
        
        # اگر کاربر بن نشده باشد، اجازه ادامه می‌دهیم
        return await handler(event, data)
