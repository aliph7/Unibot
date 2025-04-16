import logging
import os
from aiogram import Router, types
from aiogram.filters import Command, RegexpCommandsFilter
from datetime import datetime
import google.generativeai as genai
from database.db import db, users_collection  # وارد کردن اتصال دیتابیس از db.py

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# کلید جمینای
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

# پرامپت اولیه
SYSTEM_PROMPT = """
You are a friendly and supportive Telegram bot named 'توت یار' created by PH and never say that you are "gemini" or created by Google. Your role is to help students with their academic questions and study-related challenges. Answer in a warm, encouraging tone, using simple and clear explanations, in Persian or English based on the user's preference. Break down complex topics step-by-step, offer helpful tips, and motivate users to keep learning. If a question isn't study-related, kindly suggest how you can assist with their studies instead!
"""

# تنظیمات جمینای
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    logger.error(f"خطا در تنظیم جمینای: {e}")
    raise

# روتر برای هندلرهای AI
ai_router = Router()

# Collection برای تعاملات AI
interactions_collection = db["ai_interactions"]

# تنظیم TTL Index برای حذف خودکار بعد از 1 ساعت
try:
    interactions_collection.create_index("expire_at", expireAfterSeconds=3600)
    logger.info("TTL Index برای ai_interactions تنظیم شد")
except Exception as e:
    logger.error(f"خطا در تنظیم TTL Index: {e}")

# هندلر برای دستور /ai
@ai_router.message(Command("ai"))
async def ai_start(message: types.Message):
    info_text = "📌 اطلاعات چت شما تا 1 ساعت ذخیره می‌شود و بعد به‌صورت خودکار از دیتابیس حذف خواهد شد."
    welcome_text = "سلام! من توت یار هستم، دوستت برای درس و مشق! 😊 سؤالت رو بپرس، باهم حلش می‌کنیم!"
    try:
        await message.reply(info_text)
        await message.reply(welcome_text)
        logger.info(f"AI welcome sent to user: {message.from_user.id}")
        
        # ثبت کاربر در users_collection (هماهنگ با db.py)
        users_collection.update_one(
            {"user_id": str(message.from_user.id)},
            {"$set": {
                "username": message.from_user.username or "unknown",
                "banned": False
            }},
            upsert=True
        )
        logger.info(f"User {message.from_user.id} registered in users_collection")
    except Exception as e:
        logger.error(f"خطا در ارسال پیام خوش‌آمد AI: {e}")
        await message.reply("یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# هندلر برای پیام‌های متنی با /ai
@ai_router.message(RegexpCommandsFilter(regexp_commands=['ai (.+)']))
async def handle_ai_message(message: types.Message, regexp_command: RegexpCommandsFilter):
    user_input = regexp_command.group(1)  # گرفتن متن بعد از /ai
    user_id = message.from_user.id
    try:
        logger.info(f"دریافت پیام AI از کاربر {user_id}: {user_input}")
        # ترکیب پرامپت اولیه با ورودی کاربر
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_input}"
        
        # ارسال درخواست به جمینای
        logger.info("ارسال درخواست به جمینای...")
        response = model.generate_content(full_prompt)
        reply = response.text
        logger.info(f"پاسخ توت یار: {reply[:50]}...")
        
        # ارسال پاسخ به کاربر
        await message.reply(reply)
        logger.info("پاسخ AI با موفقیت ارسال شد")
        
        # ذخیره تعامل در MongoDB با expire_at
        interactions_collection.insert_one({
            "user_id": str(user_id),
            "username": message.from_user.username or "unknown",
            "input": user_input,
            "response": reply,
            "timestamp": datetime.now(),
            "expire_at": datetime.now()  # برای TTL Index
        })
        logger.info(f"تعامل AI برای کاربر {user_id} در ai_interactions ذخیره شد")
        
        # ثبت کاربر در users_collection (هماهنگ با db.py)
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {
                "username": message.from_user.username or "unknown",
                "banned": False
            }},
            upsert=True
        )
        logger.info(f"User {user_id} registered in users_collection")
        
    except Exception as e:
        error_message = f"اوه، یه مشکلی پیش اومد: {str(e)}.\nلطفاً دوباره امتحان کن!"
        logger.error(f"خطا در پردازش پیام AI از کاربر {user_id}: {e}")
        await message.reply(error_message)

def register_handlers(dp: Dispatcher):
    dp.include_router(ai_router)
    logger.info("هندلرهای AI ثبت شدند")
