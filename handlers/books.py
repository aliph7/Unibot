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
from db import add_book, get_books  # توابع MongoDB

logger = logging.getLogger(__name__)

async def show_books_menu(message: types.Message):
    """نمایش منوی اصلی کتاب‌ها"""
    logger.info("Showing books menu")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="مشاهده کتاب‌ها 📚"), KeyboardButton(text="آپلود کتاب 📤")],
            [KeyboardButton(text="🔍 جستجوی کتاب")],
            [KeyboardButton(text="🔙 برگشت به منوی اصلی")]
        ],
        resize_keyboard=True
    )
    await message.reply("بخش کتاب‌ها - لطفا انتخاب کنید:", reply_markup=keyboard)

async def start_upload_book(message: types.Message, state: FSMContext):
    """شروع فرایند آپلود کتاب"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 برگشت به بخش کتاب‌ها")]],
        resize_keyboard=True
    )
    await message.reply(
        "لطفاً کتاب خود را به صورت PDF ارسال کنید.\n"
        "برای لغو، دستور /cancel را بفرستید.",
        reply_markup=keyboard
    )
    await state.set_state(BotStates.waiting_for_book)

async def process_book_upload(message: types.Message, state: FSMContext):
    """پردازش آپلود کتاب"""
    if not message.document or not message.document.mime_type == "application/pdf":
        await message.reply("❌ لطفاً فقط فایل PDF ارسال کنید.")
        return

    try:
        add_book(
            title=message.document.file_name,
            file_id=message.document.file_id,
            uploaded_by=message.from_user.username or str(message.from_user.id),
            upload_date=datetime.now().strftime("%Y-%m-%d")
        )
        await message.reply("✅ کتاب با موفقیت آپلود شد.")
        await show_books_menu(message)
        await state.clear()
    except Exception as e:
        logger.error(f"Error uploading book: {e}")
        await message.reply("❌ خطا در آپلود کتاب.")

async def search_book(message: types.Message, state: FSMContext):
    """شروع جستجوی کتاب"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 برگشت به بخش کتاب‌ها")]],
        resize_keyboard=True
    )
    await message.reply("لطفاً عنوان کتاب مورد نظر را وارد کنید:", reply_markup=keyboard)
    await state.set_state(BotStates.waiting_for_book_search)

async def process_book_search(message: types.Message, state: FSMContext):
    """پردازش جستجوی کتاب"""
    search_term = message.text
    
    if message.text == "🔙 برگشت به بخش کتاب‌ها":
        await state.clear()
        await show_books_menu(message)
        return
        
    try:
        books = get_books()
        filtered_books = [b for b in books if search_term.lower() in b["title"].lower()]
        
        if not filtered_books:
            await message.reply("❌ کتابی با این عنوان یافت نشد.")
            return
            
        for book in filtered_books:
            await message.reply_document(
                book["file_id"],
                caption=f"📚 عنوان: {book['title']}"
            )
    except Exception as e:
        logger.error(f"Error in book search: {e}")
        await message.reply("❌ خطا در جستجوی کتاب.")

async def return_to_books(message: types.Message, state: FSMContext):
    """برگشت به منوی کتاب‌ها"""
    logger.info("Returning to books menu")
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    await show_books_menu(message)

async def view_books(message: types.Message):
    """نمایش لیست کتاب‌ها"""
    logger.info("Viewing books list")
    try:
        books = get_books()
        if not books:
            await message.reply("❌ هیچ کتابی موجود نیست.")
            return
            
        # محدود کردن به 10 کتاب آخر (مثل کد قبلی)
        recent_books = sorted(books, key=lambda x: x["upload_date"], reverse=True)[:10]
        
        await message.reply("📚 آخرین کتاب‌های آپلود شده:")
        for book in recent_books:
            await message.reply_document(
                book["file_id"],
                caption=f"📖 عنوان: {book['title']}"
            )
    except Exception as e:
        logger.error(f"Error in view_books: {e}")
        await message.reply("❌ خطا در نمایش کتاب‌ها.")

def register_handlers(dp: Dispatcher):
    """ثبت تمام هندلرهای مربوط به کتاب‌ها"""
    dp.message.register(show_books_menu, lambda message: message.text == "📖 کتاب‌ها")
    dp.message.register(return_to_books, lambda message: message.text == "🔙 برگشت به بخش کتاب‌ها")
    dp.message.register(start_upload_book, lambda message: message.text == "آپلود کتاب 📤")
    dp.message.register(search_book, lambda message: message.text == "🔍 جستجوی کتاب")
    dp.message.register(view_books, lambda message: message.text == "مشاهده کتاب‌ها 📚")
    dp.message.register(process_book_search, BotStates.waiting_for_book_search)
    dp.message.register(process_book_upload, BotStates.waiting_for_book)
