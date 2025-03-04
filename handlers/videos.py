from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import logging
import sys
from pathlib import Path

# اضافه کردن مسیر اصلی پروژه به sys.path
sys.path.append(str(Path(__file__).parent.parent))

from states.states import BotStates
from keyboards.keyboards import get_main_keyboard
from database.db import add_video, get_videos  # توابع MongoDB

logger = logging.getLogger(__name__)

async def show_videos_menu(message: types.Message):
    """نمایش منوی اصلی ویدیوها"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="آپلود ویدیو 📤")],
            [KeyboardButton(text="🔍 جستجوی ویدیو")],
            [KeyboardButton(text="🔙 برگشت به منوی اصلی")]
        ],
        resize_keyboard=True
    )
    await message.reply("بخش ویدیوهای آموزشی - لطفا انتخاب کنید:", reply_markup=keyboard)

async def start_upload_video(message: types.Message, state: FSMContext):
    """شروع فرایند آپلود ویدیو"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 برگشت به بخش ویدیوها")]],
        resize_keyboard=True
    )
    await message.reply(
        "لطفاً ویدیوی آموزشی خود را ارسال کنید.\n"
        "برای لغو، دستور /cancel را بفرستید.",
        reply_markup=keyboard
    )
    await state.set_state(BotStates.waiting_for_video)

async def process_video_upload(message: types.Message, state: FSMContext):
    """پردازش آپلود ویدیو"""
    logger.info("Starting video upload process.")
    
    if not message.video:
        await message.reply("❌ لطفاً فقط فایل ویدیویی ارسال کنید.")
        return

    # ذخیره موقت اطلاعات ویدیو
    await state.update_data(
        video_file_id=message.video.file_id,
        video_file_unique_id=message.video.file_unique_id
    )
    
    # درخواست کپشن از کاربر
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 برگشت به بخش ویدیوها")]],
        resize_keyboard=True
    )
    await message.reply(
        "✍️ لطفاً یک توضیح کامل برای ویدیو بنویسید.\n\n"
        "💡 نکته مهم: برای سهولت در جستجوی بعدی، لطفاً:\n"
        "- نام ویدیو و موضوع را دقیق ذکر کنید\n"
        "- کلمات کلیدی مهم را حتماً بنویسید\n"
        "- از توضیحات کامل و جامع استفاده کنید\n\n"
        "مثال: ویدیو درس ریاضی 2 - حل تمرین مشتق و انتگرال - جلسه سوم",
        reply_markup=keyboard
    )
    await state.set_state(BotStates.waiting_for_video_caption)

async def process_video_caption(message: types.Message, state: FSMContext):
    """پردازش کپشن ویدیو و ذخیره نهایی"""
    data = await state.get_data()
    video_file_id = data.get('video_file_id')
    caption = message.text

    logger.info(f"Video ID: {video_file_id}, Caption: {caption}")

    if not all([video_file_id, caption]):
        await message.reply("❌ خطا در پردازش اطلاعات. لطفاً دوباره تلاش کنید.")
        await state.clear()
        return

    try:
        add_video(
            file_id=video_file_id,
            file_unique_id=data.get('video_file_unique_id'),
            caption=caption,
            uploaded_by=message.from_user.id,
            upload_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        await message.reply("✅ ویدیو با موفقیت آپلود و ذخیره شد.")
        # ارسال مجدد ویدیو با کپشن جدید
        await message.reply_video(
            video_file_id,
            caption=caption
        )
    except Exception as e:
        logger.error(f"Error in process_video_caption: {e}")
        await message.reply("❌ خطا در ذخیره‌سازی ویدیو. لطفاً دوباره تلاش کنید.")
    finally:
        await state.clear()  # پاک کردن وضعیت
        await show_videos_menu(message)  # برگشت به منوی ویدیوها بعد از اتمام کار

    logger.info(f"Current state after processing: {await state.get_state()}")

async def search_video(message: types.Message, state: FSMContext):
    """شروع جستجوی ویدیو"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 برگشت به بخش ویدیوها")]],
        resize_keyboard=True
    )
    await message.reply("لطفاً عنوان ویدیوی مورد نظر را وارد کنید:", reply_markup=keyboard)
    await state.set_state(BotStates.waiting_for_video_search)

async def process_video_search(message: types.Message, state: FSMContext):
    """پردازش جستجوی ویدیو"""
    search_term = message.text
    
    if message.text == "🔙 برگشت به بخش ویدیوها":
        await state.clear()
        await show_videos_menu(message)
        return
        
    try:
        videos = get_videos()
        filtered_videos = [v for v in videos if search_term.lower() in v["caption"].lower()]
        
        if not filtered_videos:
            await message.reply("❌ ویدیویی با این عنوان یافت نشد.")
            return
            
        for video in filtered_videos:
            await message.reply_video(
                video["file_id"],
                caption=f"🎥 {video['caption']}"
            )
    except Exception as e:
        logger.error(f"Error in process_video_search: {e}")
        await message.reply("❌ خطا در جستجوی ویدیو.")

async def return_to_video_section(message: types.Message, state: FSMContext):
    """برگشت به بخش ویدیوها از هر وضعیتی"""
    logger.info(f"Current state before returning: {await state.get_state()}")
    
    await state.clear()
    await show_videos_menu(message)
    
    logger.info(f"Current state after returning: {await state.get_state()}")

async def return_to_main_menu(message: types.Message, state: FSMContext):
    """برگشت به منوی اصلی"""
    await state.clear()
    await message.reply("به منوی اصلی بازگشتید.", reply_markup=get_main_keyboard())

def register_handlers(dp: Dispatcher):
    """ثبت تمام هندلرهای مربوط به ویدیوها"""
    dp.message.register(show_videos_menu, lambda message: message.text == "🎥 ویدیوهای آموزشی")
    dp.message.register(start_upload_video, lambda message: message.text == "آپلود ویدیو 📤")
    dp.message.register(search_video, lambda message: message.text == "🔍 جستجوی ویدیو")
    dp.message.register(return_to_main_menu, lambda message: message.text == "🔙 برگشت به منوی اصلی")
    
    dp.message.register(process_video_search, BotStates.waiting_for_video_search)
    dp.message.register(process_video_upload, lambda message: message.video is not None, BotStates.waiting_for_video)
    dp.message.register(process_video_caption, BotStates.waiting_for_video_caption)
    
    dp.message.register(return_to_video_section, lambda message: message.text == "🔙 برگشت به بخش ویدیوها", BotStates.waiting_for_video)
    dp.message.register(return_to_video_section, lambda message: message.text == "🔙 برگشت به بخش ویدیوها", BotStates.waiting_for_video_caption)
    dp.message.register(return_to_video_section, lambda message: message.text == "🔙 برگشت به بخش ویدیوها", BotStates.waiting_for_video_search)
