import logging
import os
from aiogram import Router, types, Bot, Dispatcher
from aiogram.filters import Command, RegexpCommandsFilter
from pymongo import MongoClient
from datetime import datetime
import google.generativeai as genai

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# کلید جمینای
GEMINI_API_KEY = "AIzaSyA8ul-8F7f1c_FUeO3jPqghHWGctkjv6FE"

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

# اتصال به MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["bot_database"]
interactions_collection = db["ai_interactions"]

# هندلر برای دستور /ai
@ai_router.message(Command("ai"))
async def ai_start(message: types.Message):
    welcome_text = "سلام! من توت یار هستم، دوستت برای درس و مشق! 😊 سؤالت رو بپرس، باهم حلش می‌کنیم!"
    try:
        await message.reply(welcome_text)
        logger.info(f"AI welcome sent to user: {message.from_user.id}")
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
        
        # ذخیره تعامل در MongoDB
        interactions_collection.insert_one({
            "user_id": user_id,
            "username": message.from_user.username or "unknown",
            "input": user_input,
            "response": reply,
            "timestamp": datetime.now()
        })
        logger.info(f"تعامل AI برای کاربر {user_id} در MongoDB ذخیره شد")
        
    except Exception as e:
        error_message = f"اوه، یه مشکلی پیش اومد: {str(e)}.\nلطفاً دوباره امتحان کن!"
        logger.error(f"خطا در پردازش پیام AI از کاربر {user_id}: {e}")
        await message.reply(error_message)

def register_handlers(dp: Dispatcher):
    dp.include_router(ai_router)
    logger.info("هندلرهای AI ثبت شدند")
