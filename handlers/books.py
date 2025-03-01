from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import sqlite3
import logging
import sys
from pathlib import Path

# اضافه کردن مسیر اصلی پروژه به sys.path
sys.path.append(str(Path(__file__).parent.parent))

from states.states import BotStates
from keyboards.keyboards import get_main_keyboard

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

    conn = sqlite3.connect('university_bot.db')
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO books (title, file_id, uploaded_by, upload_date)
                     VALUES (?, ?, ?, ?)''',
                     (message.document.file_name,
                      message.document.file_id,
                      message.from_user.username,
                      datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        await message.reply("✅ کتاب با موفقیت آپلود شد.")
        await show_books_menu(message)
        await state.clear()
    except Exception as e:
        await message.reply("❌ خطا در آپلود کتاب.")
    finally:
        conn.close()

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
        
    conn = sqlite3.connect('university_bot.db')
    c = conn.cursor()
    try:
        c.execute('SELECT title, file_id FROM books WHERE title LIKE ?', (f'%{search_term}%',))
        results = c.fetchall()
        
        if not results:
            await message.reply("❌ کتابی با این عنوان یافت نشد.")
            return
            
        for title, file_id in results:
            await message.reply_document(
                file_id,
                caption=f"📚 عنوان: {title}"
            )
    except Exception as e:
        await message.reply("❌ خطا در جستجوی کتاب.")
    finally:
        conn.close()

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
    conn = sqlite3.connect('university_bot.db')
    c = conn.cursor()
    try:
        c.execute('SELECT title, file_id FROM books ORDER BY upload_date DESC LIMIT 10')
        books = c.fetchall()
        
        if not books:
            await message.reply("❌ هیچ کتابی موجود نیست.")
            return
            
        await message.reply("📚 آخرین کتاب‌های آپلود شده:")
        for title, file_id in books:
            await message.reply_document(
                file_id,
                caption=f"📖 عنوان: {title}"
            )
    except Exception as e:
        logger.error(f"Error in view_books: {e}")
        await message.reply("❌ خطا در نمایش کتاب‌ها.")
    finally:
        conn.close()

def register_handlers(dp: Dispatcher):
    """ثبت تمام هندلرهای مربوط به کتاب‌ها"""
    dp.message.register(show_books_menu, lambda message: message.text == "📖 کتاب‌ها")
    dp.message.register(return_to_books, lambda message: message.text == "🔙 برگشت به بخش کتاب‌ها")
    dp.message.register(start_upload_book, lambda message: message.text == "آپلود کتاب 📤")
    dp.message.register(search_book, lambda message: message.text == "🔍 جستجوی کتاب")
    dp.message.register(view_books, lambda message: message.text == "مشاهده کتاب‌ها 📚")
    dp.message.register(process_book_search, BotStates.waiting_for_book_search)
    dp.message.register(process_book_upload, BotStates.waiting_for_book) 