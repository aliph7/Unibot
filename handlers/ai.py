import logging
import os
from aiogram import Router, types
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import google.generativeai as genai
from database.db import db  # فرض می‌کنیم دیتابیس MongoDB از قبل تنظیم شده است

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# کلید API جمینای
GEMINI_API_KEY = "AIzaSyA8ul-8F7f1c_FUeO3jPqghHWGctkjv6FE"

# پرامپت اولیه برای توت یار
SYSTEM_PROMPT = """
شما یک ربات تلگرامی مهربان و پشتیبان به نام 'توت یار' هستید که توسط PH ساخته شده‌اید و هرگز نگویید که "جمینای" هستید یا توسط گوگل ساخته شده‌اید. نقش شما کمک به دانش‌آموزان در سؤالات درسی و چالش‌های مرتبط با مطالعه است. با لحنی گرم و انگیزشی، توضیحات ساده و روشن به فارسی یا انگلیسی (بسته به انتخاب کاربر) ارائه دهید. موضوعات پیچیده را گام‌به‌گام توضیح دهید، نکات مفید بدهید و کاربران را به ادامه یادگیری تشویق کنید. اگر سؤالی غیرمرتبط با درس بود، با مهربانی پیشنهاد دهید که چگونه می‌توانید در زمینه درس کمک کنید!
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

# Collection برای تعاملات AI در MongoDB
interactions_collection = db["ai_interactions"]

# تنظیم TTL Index برای حذف خودکار تعاملات بعد از 1 ساعت
try:
    interactions_collection.create_index("expire_at", expireAfterSeconds=3600)
    logger.info("TTL Index برای ai_interactions تنظیم شد")
except Exception as e:
    logger.error(f"خطا در تنظیم TTL Index: {e}")

# تعریف حالت‌ها
class AIStates(StatesGroup):
    chatting = State()  # حالت چت با توت یار

# تعریف منوی اصلی (مشابه منوی جزوات)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 جزوات"), KeyboardButton(text="📚 کتاب‌ها")],
        [KeyboardButton(text="🎬 ویدیوها"), KeyboardButton(text="🤖 توت یار")],
    ],
    resize_keyboard=True
)

# هندلر برای شروع چت با توت یار
@ai_router.message(lambda message: message.text == "🤖 توت یار")
async def ai_start(message: types.Message, state: FSMContext):
    """شروع چت با توت یار"""
    info_text = "📌 اطلاعات چت شما تا 1 ساعت ذخیره می‌شود و بعد به‌صورت خودکار حذف خواهد شد."
    welcome_text = "سلام! من توت یار هستم، دوستت برای درس و مشق! 😊 سؤالت رو بپرس، باهم حلش می‌کنیم!"
    try:
        await message.reply(info_text)
        await message.reply(welcome_text, reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 بازگشت به منوی اصلی")]],
            resize_keyboard=True
        ))
        await state.set_state(AIStates.chatting)
        logger.info(f"حالت AI برای کاربر {message.from_user.id} شروع شد")
    except Exception as e:
        logger.error(f"خطا در شروع چت AI: {e}")
        await message.reply("یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# هندلر برای پردازش پیام‌ها در حالت چت
@ai_router.message(AIStates.chatting)
async def handle_ai_message(message: types.Message, state: FSMContext):
    """پردازش پیام‌های کاربر در حالت چت با توت یار"""
    user_input = message.text
    user_id = message.from_user.id
    
    # بررسی بازگشت به منوی اصلی
    if user_input == "🔙 بازگشت به منوی اصلی":
        await exit_ai(message, state)
        return
    
    try:
        logger.info(f"دریافت پیام از کاربر {user_id}: {user_input}")
        # ترکیب پرامپت اولیه با ورودی کاربر
        full_prompt = f"{SYSTEM_PROMPT}\n\nکاربر: {user_input}"
        
        # ارسال درخواست به جمینای
        logger.info("ارسال درخواست به جمینای...")
        response = model.generate_content(full_prompt)
        reply = response.text
        logger.info(f"پاسخ توت یار: {reply[:50]}...")
        
        # ارسال پاسخ به کاربر
        await message.reply(reply)
        logger.info("پاسخ با موفقیت ارسال شد")
        
        # ذخیره تعامل در MongoDB
        interactions_collection.insert_one({
            "user_id": str(user_id),
            "username": message.from_user.username or "unknown",
            "input": user_input,
            "response": reply,
            "timestamp": datetime.now(),
            "expire_at": datetime.now()
        })
        logger.info(f"تعامل برای کاربر {user_id} ذخیره شد")
        
    except Exception as e:
        logger.error(f"خطا در پردازش پیام AI: {e}")
        await message.reply("اوه، یه مشکلی پیش اومد! دوباره امتحان کن!")

# هندلر برای خروج از حالت چت
async def exit_ai(message: types.Message, state: FSMContext):
    """خروج از حالت چت و بازگشت به منوی اصلی"""
    try:
        await state.clear()
        await message.reply("به منوی اصلی برگشتی!", reply_markup=main_menu)
        logger.info(f"کاربر {message.from_user.id} از حالت AI خارج شد")
    except Exception as e:
        logger.error(f"خطا در خروج از حالت AI: {e}")
        await message.reply("یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# ثبت هندلرها
def register_handlers(dp):
    """ثبت هندلرهای مربوط به AI"""
    dp.include_router(ai_router)
    logger.info("هندلرهای AI ثبت شدند")
