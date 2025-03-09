from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from database.db import get_pamphlets, get_books, get_videos, delete_pamphlet, delete_book, delete_video, ban_user, is_user_banned, get_user_count, get_all_users, unban_user
from aiogram.fsm.state import State, StatesGroup
import logging

logger = logging.getLogger(__name__)

# تعریف استیت‌ها
class AdminStates(StatesGroup):
    admin_panel = State()
    delete_menu = State()
    delete_pamphlet_menu = State()
    delete_book_menu = State()
    delete_video_menu = State()
    waiting_for_delete_pamphlet = State()
    waiting_for_delete_book = State()
    waiting_for_delete_video = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()  # اضافه شد

# ID تلگرام شما
ADMIN_ID = 100851995

# منوی مدیریت
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📂 لیست فایل‌ها")],
        [KeyboardButton(text="📊 آمار ربات")],
        [KeyboardButton(text="🚫 بن کردن کاربر")],
        [KeyboardButton(text="❌ حذف محتوا")],
        [KeyboardButton(text="🔙 خروج از مدیریت")]
    ],
    resize_keyboard=True
)

# منوی حذف محتوا
delete_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 حذف جزوه")],
        [KeyboardButton(text="📚 حذف کتاب")],
        [KeyboardButton(text="🎬 حذف ویدیو")],
        [KeyboardButton(text="🔙 بازگشت به منوی مدیریت")]
    ],
    resize_keyboard=True
)

# منوی بن کردن کاربر
ban_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚫 بن کردن"), KeyboardButton(text="✅ آن‌بن کردن")],
        [KeyboardButton(text="🔙 بازگشت به منوی مدیریت")]
    ],
    resize_keyboard=True
)

async def cmd_boss(message: types.Message, state: FSMContext):
    """دستور ورود به بخش مدیریت"""
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ شما دسترسی به این بخش را ندارید!")
        return
    
    await message.reply("به بخش مدیریت خوش اومدی! لطفاً انتخاب کن:", reply_markup=admin_menu)
    await state.set_state(AdminStates.admin_panel)

async def list_files(message: types.Message, state: FSMContext):
    """نمایش لیست فایل‌ها"""
    if message.from_user.id != ADMIN_ID:
        return
    
    pamphlets = get_pamphlets()
    books = get_books()
    videos = get_videos()
    
    response = "📂 **لیست فایل‌ها:**\n\n"
    
    response += "📝 **جزوات:**\n"
    if pamphlets:
        for p in pamphlets:
            response += f"- فایل شماره {p['id']}\n"
            if 'caption' in p and p['caption']:
                response += f"  📄 توضیحات: {p['caption']}\n"
            response += f"  👤 آپلودکننده: `{p['uploaded_by']}`\n\n"
    else:
        response += "❌ هیچ جزوه‌ای موجود نیست\n\n"
    
    response += "📚 **کتاب‌ها:**\n"
    if books:
        for b in books:
            response += f"- فایل شماره {b['id']}\n"
            if 'caption' in b and b['caption']:
                response += f"  📄 توضیحات: {b['caption']}\n"
            response += f"  👤 آپلودکننده: `{b['uploaded_by']}`\n\n"
    else:
        response += "❌ هیچ کتابی موجود نیست\n\n"
    
    response += "🎬 **ویدیوها:**\n"
    if videos:
        for v in videos:
            response += f"- فایل شماره {v['id']}\n"
            if 'caption' in v and v['caption']:
                response += f"  📄 توضیحات: {v['caption']}\n"
            response += f"  👤 آپلودکننده: `{v['uploaded_by']}`\n\n"
    else:
        response += "❌ هیچ ویدیویی موجود نیست\n\n"
    
    if len(response) > 4096:
        parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
        for part in parts:
            await message.reply(part, parse_mode="Markdown")
    else:
        await message.reply(response, parse_mode="Markdown")

async def show_stats(message: types.Message, state: FSMContext):
    """نمایش آمار ربات"""
    if message.from_user.id != ADMIN_ID:
        return
    
    current_state = await state.get_state()
    if current_state != AdminStates.admin_panel:
        return
        
    pamphlets = get_pamphlets()
    books = get_books()
    videos = get_videos()
    
    stats = "📊 **آمار ربات:**\n\n"
    stats += f"تعداد جزوات: {len(pamphlets)}\n"
    stats += f"تعداد کتاب‌ها: {len(books)}\n"
    stats += f"تعداد ویدیوها: {len(videos)}\n"
    stats += f"تعداد کاربران: {get_user_count()}\n"
    
    await message.reply(stats)

async def ban_user_cmd(message: types.Message, state: FSMContext):
    """بن کردن کاربر"""
    if message.from_user.id != ADMIN_ID:
        return
    
    users = get_all_users()
    if not users:
        await message.reply("❌ هیچ کاربری یافت نشد!")
        return

    response = "👥 **لیست کاربران:**\n\n"
    for user_id, is_banned in users:
        status = "🚫 بن شده" if is_banned else "✅ فعال"
        response += f"👤 کاربر: `{user_id}`\n"
        response += f"وضعیت: {status}\n\n"
    
    response += "برای بن یا آن‌بن کردن کاربر، از دکمه‌های زیر استفاده کنید:"
    
    await message.reply(response, parse_mode="Markdown", reply_markup=ban_menu)
    await state.set_state(AdminStates.admin_panel)

async def ban_user_start(message: types.Message, state: FSMContext):
    """شروع فرایند بن کردن"""
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.reply(
        "🚫 لطفاً ID کاربر مورد نظر برای بن کردن را وارد کنید:\n\n"
        "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
        reply_markup=ban_menu
    )
    await state.set_state(AdminStates.waiting_for_ban_id)

async def unban_user_start(message: types.Message, state: FSMContext):
    """شروع فرایند آن‌بن کردن (اضافه شده)"""
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.reply(
        "✅ لطفاً ID کاربر مورد نظر برای آن‌بن کردن را وارد کنید:\n\n"
        "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
        reply_markup=ban_menu
    )
    await state.set_state(AdminStates.waiting_for_unban_id)

async def process_ban_user(message: types.Message, state: FSMContext):
    """پردازش بن کردن"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    
    try:
        user_id = message.text
        ban_user(user_id)
        await message.reply(f"✅ کاربر با ID {user_id} بن شد.")
        await message.reply("به منوی مدیریت بازگشتید:", reply_markup=admin_menu)
        await state.set_state(AdminStates.admin_panel)
    except Exception as e:
        logger.error(f"خطا در بن کردن کاربر: {e}")
        await message.reply(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=ban_menu
        )

async def process_unban_user(message: types.Message, state: FSMContext):
    """پردازش آن‌بن کردن"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    
    try:
        user_id = message.text
        unban_user(user_id)
        await message.reply(f"✅ کاربر با ID {user_id} آن‌بن شد.")
        await message.reply("به منوی مدیریت بازگشتید:", reply_markup=admin_menu)
        await state.set_state(AdminStates.admin_panel)
    except Exception as e:
        logger.error(f"خطا در آن‌بن کردن کاربر: {e}")
        await message.reply(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=ban_menu
        )

async def delete_content_menu(message: types.Message, state: FSMContext):
    """نمایش منوی حذف محتوا"""
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.reply(
        "لطفاً نوع محتوا برای حذف را انتخاب کنید:", 
        reply_markup=delete_menu
    )
    await state.set_state(AdminStates.delete_menu)

async def back_to_admin(message: types.Message, state: FSMContext):
    """بازگشت به منوی مدیریت"""
    if message.from_user.id != ADMIN_ID:
        return
    
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await state.set_state(AdminStates.admin_panel)
    await message.reply(
        "به منوی مدیریت بازگشتید:", 
        reply_markup=admin_menu
    )

async def delete_pamphlet_cmd(message: types.Message, state: FSMContext):
    """نمایش لیست جزوات برای حذف"""
    if message.from_user.id != ADMIN_ID:
        return
    
    current_state = await state.get_state()
    if current_state != AdminStates.delete_menu:
        return
        
    pamphlets = get_pamphlets()
    if not pamphlets:
        await message.reply(
            "❌ هیچ جزوه‌ای موجود نیست!\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )
        return
    
    response = "📝 **لیست جزوات:**\n\n"
    for p in pamphlets:
        response += f"- {p['title']} (ID: {p['id']})\n"
        response += f"  👤 آپلود توسط: {p['uploaded_by']}\n\n"
    
    response += "\nبرای حذف، ID جزوه را وارد کنید:"
    
    await message.reply(response, reply_markup=delete_menu)
    await state.set_state(AdminStates.waiting_for_delete_pamphlet)

async def process_delete_pamphlet(message: types.Message, state: FSMContext):
    """پردازش حذف جزوه"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    
    try:
        pamphlet_id = int(message.text)
        result = delete_pamphlet(pamphlet_id)
        if result:
            await message.reply(f"✅ جزوه با ID {pamphlet_id} حذف شد.")
            await message.reply("به منوی مدیریت بازگشتید:", reply_markup=admin_menu)
            await state.set_state(AdminStates.admin_panel)
        else:
            await message.reply(
                "❌ جزوه با این ID یافت نشد! لطفاً دوباره امتحان کنید:\n\n"
                "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
                reply_markup=delete_menu
            )
    except ValueError:
        await message.reply(
            "❌ ID باید عدد باشه! لطفاً دوباره امتحان کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )
    except Exception as e:
        logger.error(f"خطا در حذف جزوه: {e}")
        await message.reply(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )

async def delete_book_cmd(message: types.Message, state: FSMContext):
    """نمایش لیست کتاب‌ها برای حذف"""
    if message.from_user.id != ADMIN_ID:
        return
    
    current_state = await state.get_state()
    if current_state != AdminStates.delete_menu:
        return
        
    books = get_books()
    if not books:
        await message.reply(
            "❌ هیچ کتابی موجود نیست!\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )
        return
    
    response = "📚 **لیست کتاب‌ها:**\n\n"
    for b in books:
        response += f"- {b['title']} (ID: {b['id']})\n"
        response += f"  👤 آپلود توسط: {b['uploaded_by']}\n\n"
    
    response += "\nبرای حذف، ID کتاب را وارد کنید:"
    
    await message.reply(response, reply_markup=delete_menu)
    await state.set_state(AdminStates.waiting_for_delete_book)

async def process_delete_book(message: types.Message, state: FSMContext):
    """پردازش حذف کتاب"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    
    try:
        book_id = int(message.text)
        result = delete_book(book_id)
        if result:
            await message.reply(f"✅ کتاب با ID {book_id} حذف شد.")
            await message.reply("به منوی مدیریت بازگشتید:", reply_markup=admin_menu)
            await state.set_state(AdminStates.admin_panel)
        else:
            await message.reply(
                "❌ کتاب با این ID یافت نشد! لطفاً دوباره امتحان کنید:\n\n"
                "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
                reply_markup=delete_menu
            )
    except ValueError:
        await message.reply(
            "❌ ID باید عدد باشه! لطفاً دوباره امتحان کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )
    except Exception as e:
        logger.error(f"خطا در حذف کتاب: {e}")
        await message.reply(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )

async def delete_video_cmd(message: types.Message, state: FSMContext):
    """نمایش لیست ویدیوها برای حذف"""
    if message.from_user.id != ADMIN_ID:
        return
    
    current_state = await state.get_state()
    if current_state != AdminStates.delete_menu:
        return
        
    videos = get_videos()
    if not videos:
        await message.reply(
            "❌ هیچ ویدیویی موجود نیست!\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )
        return
    
    response = "🎬 **لیست ویدیوها:**\n\n"
    for v in videos:
        response += f"📌 **ویدیو شماره {v['id']}:**\n"
        response += f"🆔 شناسه فایل: `{v['file_id']}`\n"
        if v['caption']:
            response += f"📝 کپشن: {v['caption']}\n"
        response += f"👤 آپلودکننده: `{v['uploaded_by']}`\n"
        response += "➖➖➖➖➖➖➖➖➖➖\n\n"
    
    response += "برای حذف، ID ویدیو را وارد کنید:"
    
    if len(response) > 4096:
        parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
        for part in parts[:-1]:
            await message.reply(part, parse_mode="Markdown")
        await message.reply(parts[-1], reply_markup=delete_menu, parse_mode="Markdown")
    else:
        await message.reply(response, reply_markup=delete_menu, parse_mode="Markdown")
    
    await state.set_state(AdminStates.waiting_for_delete_video)

async def process_delete_video(message: types.Message, state: FSMContext):
    """پردازش حذف ویدیو"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    
    try:
        video_id = int(message.text)
        result = delete_video(video_id)
        if result:
            await message.reply(f"✅ ویدیو با ID {video_id} حذف شد.")
            await message.reply("به منوی مدیریت بازگشتید:", reply_markup=admin_menu)
            await state.set_state(AdminStates.admin_panel)
        else:
            await message.reply(
                "❌ ویدیو با این ID یافت نشد! لطفاً دوباره امتحان کنید:\n\n"
                "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
                reply_markup=delete_menu
            )
    except ValueError:
        await message.reply(
            "❌ ID باید عدد باشه! لطفاً دوباره امتحان کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )
    except Exception as e:
        logger.error(f"خطا در حذف ویدیو: {e}")
        await message.reply(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید:\n\n"
            "⚠️ برای بازگشت به منوی مدیریت، روی دکمه زیر کلیک کنید.",
            reply_markup=delete_menu
        )

async def exit_admin(message: types.Message, state: FSMContext):
    """خروج از بخش مدیریت"""
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.clear()
    await message.reply("از بخش مدیریت خارج شدی.", reply_markup=types.ReplyKeyboardRemove())

def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_boss, Command("boss"))
    dp.message.register(list_files, lambda message: message.text == "📂 لیست فایل‌ها", StateFilter(AdminStates.admin_panel))
    dp.message.register(show_stats, lambda message: message.text == "📊 آمار ربات", StateFilter(AdminStates.admin_panel))
    dp.message.register(ban_user_cmd, lambda message: message.text == "🚫 بن کردن کاربر", StateFilter(AdminStates.admin_panel))
    dp.message.register(delete_content_menu, lambda message: message.text == "❌ حذف محتوا", StateFilter(AdminStates.admin_panel))
    dp.message.register(exit_admin, lambda message: message.text == "🔙 خروج از مدیریت", StateFilter(AdminStates.admin_panel))
    
    dp.message.register(delete_pamphlet_cmd, lambda message: message.text == "📝 حذف جزوه", StateFilter(AdminStates.delete_menu))
    dp.message.register(delete_book_cmd, lambda message: message.text == "📚 حذف کتاب", StateFilter(AdminStates.delete_menu))
    dp.message.register(delete_video_cmd, lambda message: message.text == "🎬 حذف ویدیو", StateFilter(AdminStates.delete_menu))
    
    dp.message.register(process_delete_pamphlet, StateFilter(AdminStates.waiting_for_delete_pamphlet))
    dp.message.register(process_delete_book, StateFilter(AdminStates.waiting_for_delete_book))
    dp.message.register(process_delete_video, StateFilter(AdminStates.waiting_for_delete_video))
    
    dp.message.register(ban_user_start, lambda message: message.text == "🚫 بن کردن", StateFilter(AdminStates.admin_panel))
    dp.message.register(unban_user_start, lambda message: message.text == "✅ آن‌بن کردن", StateFilter(AdminStates.admin_panel))
    dp.message.register(process_ban_user, StateFilter(AdminStates.waiting_for_ban_id))
    dp.message.register(process_unban_user, StateFilter(AdminStates.waiting_for_unban_id))
    
    dp.message.register(back_to_admin, lambda message: message.text == "🔙 بازگشت به منوی مدیریت")
