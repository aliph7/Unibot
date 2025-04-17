import logging
import os
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import google.generativeai as genai
from database.db import db, add_ai_interaction, get_ai_interactions, users_collection, check_and_update_ai_quota

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# کلید جمینای
GEMINI_API_KEY = "AIzaSyA8ul-8F7f1c_FUeO3jPqghHWGctkjv6FE"
# پرامپت اولیه
SYSTEM_PROMPT = """
You are a friendly and supportive Telegram bot named 'TUT ai' created by PH( سید علی پورحسینی) and never say that you are "gemini" or created by Google. Your role is to help students with their academic questions and study-related challenges. Answer in a warm, encouraging tone, using simple and clear explanations, in Persian or English based on the user's preference. Break down complex topics step-by-step, offer helpful tips, and motivate users to keep learning. If a question isn't study-related, kindly suggest how you can assist with their studies instead!
**دستورات مهم**:
1. تاریخچه مکالمه را با دقت بخوانید.
2. اگر سؤال جدید به سؤالات قبلی ربط دارد، پاسخ را با توجه به آن‌ها بنویسید و به موضوع قبلی ارجاع دهید.
3. فقط به سؤال فعلی پاسخ ندهید؛ زمینه (context) مکالمه را حفظ کنید.

**شروع مکالمه**:
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

# تعریف حالت‌ها
class AIStates(StatesGroup):
    chatting = State()

# تعریف منوی اصلی
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 جزوات"), KeyboardButton(text="📚 کتاب‌ها")],
        [KeyboardButton(text="🎬 ویدیوها"), KeyboardButton(text="🤖 توت یار")],
    ],
    resize_keyboard=True
)

# تابع کمکی برای ساخت تاریخچه مکالمه
def build_conversation_history(user_id: str) -> str:
    """بازیابی و ساخت تاریخچه مکالمه برای کاربر"""
    try:
        interactions = get_ai_interactions(user_id=user_id, limit=3)
        if not interactions:
            logger.info(f"No interactions found for user {user_id}")
            return ""
        history = "--- تاریخچه مکالمه ---\n"
        for interaction in interactions:
            history += f"کاربر: {interaction['input']}\nتوت یار: {interaction['response']}\n\n"
        logger.info(f"Conversation history for user {user_id}: {history[:100]}...")
        return history
    except Exception as e:
        logger.error(f"خطا در ساخت تاریخچه مکالمه: {e}")
        return ""

# هندلر برای شروع چت با توت یار
@ai_router.message(lambda message: message.text == "🤖 هوش مصنوعی TUT")
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

        # ثبت کاربر
        users_collection.update_one(
            {"user_id": str(message.from_user.id)},
            {"$set": {
                "username": message.from_user.username or "unknown",
                "banned": False
            }},
            upsert=True
        )
        logger.info(f"کاربر {message.from_user.id} در users_collection ثبت شد")
    except Exception as e:
        logger.error(f"خطا در شروع چت AI: {e}")
        await message.reply("یه مشکلی پیش اومد، لطفاً دوباره امتحان کن!")

# هندلر برای پیام‌ها در حالت چت
@ai_router.message(AIStates.chatting)
async def handle_ai_message(message: types.Message, state: FSMContext):
    """پردازش پیام‌های کاربر در حالت چت"""
    user_input = message.text
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # بررسی بازگشت به منوی اصلی
    if user_input == "🔙 بازگشت به منوی اصلی":
        await exit_ai(message, state)
        return

    try:
        # چک کردن سهمیه روزانه
        can_send, message_count = check_and_update_ai_quota(user_id, username)
        daily_limit = 10

        if not can_send:
            await message.reply(
                f"❌ شما به سقف {daily_limit} پیام روزانه رسیدید. لطفاً فردا دوباره امتحان کنید!"
            )
            return

        logger.info(f"دریافت پیام از کاربر {user_id}: {user_input}")
        
        # گرفتن تاریخچه مکالمه
        conversation_history = build_conversation_history(str(user_id))
        
        # ترکیب پرامپت اولیه، تاریخچه و ورودی جدید
        full_prompt = f"{SYSTEM_PROMPT}\n\n{conversation_history}کاربر: {user_input}\nپاسخ بده:"

        # ارسال درخواست به جمینای
        logger.info("ارسال درخواست به جمینای...")
        response = model.generate_content(full_prompt)
        reply = response.text
        logger.info(f"پاسخ توت یار: {reply[:50]}...")

        # ارسال پاسخ به کاربر با نمایش سهمیه
        await message.reply(
            f"{reply}\n\n📊 سهمیه امروز: {message_count}/{daily_limit} پیام استفاده شده."
        )
        logger.info("پاسخ AI با موفقیت ارسال شد")

        # ذخیره تعامل در MongoDB
        interaction_id = add_ai_interaction(
            user_id=user_id,
            username=username,
            input_text=user_input,
            response_text=reply
        )
        if not interaction_id:
            logger.error(f"Failed to save interaction for user {user_id}")

    except Exception as e:
        logger.error(f"خطا در پردازش پیام AI: {e}")
        await message.reply("اوه، یه مشکلی پیش اومد! لطفاً دوباره امتحان کن!")

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

# هندلر برای تست تاریخچه
@ai_router.message(lambda message: message.text == "/history")
async def check_history(message: types.Message):
    """چک کردن تاریخچه مکالمه برای دیباگ"""
    user_id = str(message.from_user.id)
    history = build_conversation_history(user_id)
    if history:
        await message.reply(f"تاریخچه مکالمه شما:\n{history}")
    else:
        await message.reply("هیچ تاریخچه‌ای برای شما پیدا نشد!")

def register_handlers(dp):
    """ثبت هندلرهای AI"""
    dp.include_router(ai_router)
    logger.info("هندلرهای AI ثبت شدند")
