import logging
import os
from aiogram import Router, types
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import google.generativeai as genai
from database.db import db, users_collection

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

# روتر برای هندلرها
router = Router()

# Collection برای تعاملات AI
interactions_collection = db["ai_interactions"]

# تنظیم TTL Index برای حذف خودکار بعد از 1 ساعت
try:
    interactions_collection.create_index("expire_at", expireAfterSeconds=3600)
    logger.info("TTL Index برای ai_interactions تنظیم شد")
except Exception as e:
    logger.error(f"خطا در تنظیم TTL Index: {e}")

# تعریف منوی اصلی
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 جزوات"), KeyboardButton(text="📚 کتاب‌ها")],
        [KeyboardButton(text="🎬 ویدیوها"), KeyboardButton(text="🤖 توت یار")],
    ],
    resize_keyboard=True
)

# تعریف حالت‌ها
class AIStates(StatesGroup):
    chatting = State()

# هندلر برای /start
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    welcome_text = "سلام! به بات دانشگاه خوش اومدی! 😊 گزینه مورد نظرت رو انتخاب کن:"
    try:
        await state.clear()  # پاک کردن هر حالت قبلی
        await message.reply(welcome_text, reply_markup=main_menu)
        logger.info(f"Main menu sent to user: {message.from_user.id}")
    except Exception as e:
        logger.error(f"خطا در ارسال منوی اصلی: {e}")
        await message.reply("یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# هندلر برای دکمه "توت یار"
@router.message(Text(text="🤖 توت یار"))
async def ai_start(message: types.Message, state: FSMContext):
    info_text = "📌 اطلاعات چت شما تا 1 ساعت ذخیره می‌شود و بعد به‌صورت خودکار از دیتابیس حذف خواهد شد."
    welcome_text = "سلام! من توت یار هستم، دوستت برای درس و مشق! 😊 سؤالت رو بپرس، باهم حلش می‌کنیم!"
    try:
        await message.reply(info_text)
        await message.reply(welcome_text, reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 بازگشت به منوی اصلی")]],
            resize_keyboard=True
        ))
        await state.set_state(AIStates.chatting)
        logger.info(f"AI mode started for user: {message.from_user.id}")
        
        # ثبت کاربر در users_collection
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
        logger.error(f"خطا در شروع چت AI: {e}")
        await message.reply("یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# هندلر برای پیام‌های متنی در حالت چت
@router.message(AIStates.chatting)
async def handle_ai_message(message: types.Message, state: FSMContext):
    user_input = message.text
    user_id = message.from_user.id
    if user_input == "🔙 بازگشت به منوی اصلی":
        await exit_ai(message, state)
        return
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
            "user_id": str(user_id),
            "username": message.from_user.username or "unknown",
            "input": user_input,
            "response": reply,
            "timestamp": datetime.now(),
            "expire_at": datetime.now()
        })
        logger.info(f"تعامل AI برای کاربر {user_id} در ai_interactions ذخیره شد")
        
        # ثبت کاربر در users_collection
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

# هندلر برای خروج از حالت AI
@router.message(Text(text="🔙 بازگشت به منوی اصلی"))
async def exit_ai(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        await message.reply("به منوی اصلی برگشتی!", reply_markup=main_menu)
        logger.info(f"User {message.from_user.id} exited AI mode")
    except Exception as e:
        logger.error(f"خطا در خروج از حالت AI: {e}")
        await message.reply("یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

def register_handlers(dp: Dispatcher):
    dp.include_router(router)
    logger.info("هندلرهای عمومی و AI ثبت شدند")
