from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from database.db import get_pamphlets, get_books, get_videos, delete_pamphlet, delete_book, delete_video, ban_user, is_user_banned, get_user_count, get_all_users, unban_user
from aiogram.fsm.state import State, StatesGroup
import logging

logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    admin_panel = State()
    delete_menu = State()
    waiting_for_delete_pamphlet = State()
    waiting_for_delete_book = State()
    waiting_for_delete_video = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()

ADMIN_ID = 100851995

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

delete_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 حذف جزوه")],
        [KeyboardButton(text="📚 حذف کتاب")],
        [KeyboardButton(text="🎬 حذف ویدیو")],
        [KeyboardButton(text="🔙 بازگشت به منوی مدیریت")]
    ],
    resize_keyboard=True
)

ban_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚫 بن کردن"), KeyboardButton(text="✅ آن‌بن کردن")],
        [KeyboardButton(text="🔙 بازگشت به منوی مدیریت")]
    ],
    resize_keyboard=True
)

async def cmd_boss(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ شما دسترسی به این بخش را ندارید!")
        return
    try:
        await message.reply("به بخش مدیریت خوش اومدی! لطفاً انتخاب کن:", reply_markup=admin_menu)
        await state.set_state(AdminStates.admin_panel)
        logger.info(f"Admin panel opened for user: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_boss: {e}", exc_info=True)
        await message.reply("❌ خطا در باز کردن پنل مدیریت! دوباره تلاش کن.")

async def list_files(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        pamphlets = get_pamphlets()
        books = get_books()
        videos = get_videos()
        
        response = "📂 لیست فایل‌ها:\n\n"
        response += "📝 جزوات:\n" + ("".join(f"- {p['title']} (ID: {p.get('id', 'نامشخص')})\n  👤 ID: {p.get('uploaded_by', 'ناشناس')}\n\n" for p in pamphlets) or "❌ هیچ جزوه‌ای نیست\n\n")
        response += "📚 کتاب‌ها:\n" + ("".join(f"- {b['title']} (ID: {b.get('id', 'نامشخص')})\n  👤 ID: {b.get('uploaded_by', 'ناشناس')}\n\n" for b in books) or "❌ هیچ کتابی نیست\n\n")
        response += "🎬 ویدیوها:\n" + ("".join(f"- {v.get('caption', 'بدون کپشن')} (ID: {v.get('id', 'نامشخص')})\n  👤 ID: {v.get('uploaded_by', 'ناشناس')}\n\n" for v in videos) or "❌ هیچ ویدیویی نیست\n\n")
        
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response)
        logger.info(f"File list sent to admin: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in list_files: {e}", exc_info=True)
        await message.reply("❌ خطا در گرفتن لیست فایل‌ها! دوباره تلاش کن.", reply_markup=admin_menu)

async def show_stats(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID or await state.get_state() != AdminStates.admin_panel:
        return
    try:
        stats = "📊 آمار ربات:\n\n"
        stats += f"تعداد جزوات: {len(get_pamphlets())}\n"
        stats += f"تعداد کتاب‌ها: {len(get_books())}\n"
        stats += f"تعداد ویدیوها: {len(get_videos())}\n"
        stats += f"تعداد کاربران: {get_user_count()}\n"
        await message.reply(stats)
        logger.info(f"Stats sent to admin: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in show_stats: {e}", exc_info=True)
        await message.reply("❌ خطا در گرفتن آمار! دوباره تلاش کن.", reply_markup=admin_menu)

async def ban_user_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        from database.db import users_collection
        users = get_all_users()
        logger.info(f"Users retrieved: {users}")
        if not users:
            await message.reply("❌ هیچ کاربری یافت نشد! لطفاً مطمئن شو کاربران توی دیتابیس ثبت شدن.", reply_markup=admin_menu)
            return
        response = "👥 لیست کاربران:\n\n"
        for user_id, is_banned in users:
            numeric_id = user_id
            username = None
            if not user_id.isdigit():
                user_doc = users_collection.find_one({"user_id": user_id})
                numeric_id = user_doc.get("user_id") if user_doc and user_doc.get("user_id").isdigit() else "نامشخص"
                username = user_doc.get("username") if user_doc and user_doc.get("username") else user_id
                response += f"👤 {username} (ID: {numeric_id}) - {'🚫 بن شده' if is_banned else '✅ فعال'}\n"
            else:
                user_doc = users_collection.find_one({"user_id": user_id})
                username = user_doc.get("username") if user_doc and user_doc.get("username") else "نامشخص"
                response += f"👤 {username} (ID: {user_id}) - {'🚫 بن شده' if is_banned else '✅ فعال'}\n"
        response += "\nبرای بن یا آن‌بن کردن، ID عددی یا username رو وارد کن:"
        logger.info(f"Sending response: {response}")
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response, reply_markup=ban_menu)
        await state.set_state(AdminStates.admin_panel)
    except Exception as e:
        logger.error(f"Error in ban_user_cmd: {e}", exc_info=True)
        await message.reply(f"❌ خطا در گرفتن لیست کاربران: {str(e)}. دوباره تلاش کن.", reply_markup=admin_menu)

async def ban_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        await message.reply("🚫 ID عددی یا username کاربر رو برای بن کردن وارد کن (مثلاً 7488819947 یا super_boob_man):", reply_markup=ban_menu)
        await state.set_state(AdminStates.waiting_for_ban_id)
    except Exception as e:
        logger.error(f"Error in ban_user_start: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن.", reply_markup=admin_menu)

async def unban_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        await message.reply("✅ ID عددی یا username کاربر رو برای آن‌بن کردن وارد کن (مثلاً 7488819947 یا super_boob_man):", reply_markup=ban_menu)
        await state.set_state(AdminStates.waiting_for_unban_id)
    except Exception as e:
        logger.error(f"Error in unban_user_start: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن.", reply_markup=admin_menu)

async def process_ban_user(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    try:
        from database.db import users_collection
        input_value = message.text.strip()
        
        if input_value.isdigit():
            user_id = input_value
        else:
            user_doc = users_collection.find_one({"username": input_value})
            if not user_doc or not user_doc.get("user_id"):
                await message.reply("❌ این username پیدا نشد یا user_id ثبت نشده! دوباره تلاش کن.", reply_markup=ban_menu)
                return
            user_id = user_doc["user_id"]
        
        ban_user(user_id)
        await message.reply(f"✅ کاربر {input_value} (ID: {user_id}) بن شد.", reply_markup=admin_menu)
        await state.set_state(AdminStates.admin_panel)
    except Exception as e:
        logger.error(f"Error in process_ban_user: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن.", reply_markup=ban_menu)

async def process_unban_user(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    try:
        from database.db import users_collection
        input_value = message.text.strip()
        
        if input_value.isdigit():
            user_id = input_value
        else:
            user_doc = users_collection.find_one({"username": input_value})
            if not user_doc or not user_doc.get("user_id"):
                await message.reply("❌ این username پیدا نشد یا user_id ثبت نشده! دوباره تلاش کن.", reply_markup=ban_menu)
                return
            user_id = user_doc["user_id"]
        
        unban_user(user_id)
        await message.reply(f"✅ کاربر {input_value} (ID: {user_id}) آن‌بن شد.", reply_markup=admin_menu)
        await state.set_state(AdminStates.admin_panel)
    except Exception as e:
        logger.error(f"Error in process_unban_user: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن.", reply_markup=ban_menu)

async def delete_content_menu(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        await message.reply("لطفاً نوع محتوا برای حذف رو انتخاب کن:", reply_markup=delete_menu)
        await state.set_state(AdminStates.delete_menu)
        logger.info(f"Delete menu opened for admin: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in delete_content_menu: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن.", reply_markup=admin_menu)

async def back_to_admin(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        await state.clear()
        await state.set_state(AdminStates.admin_panel)
        await message.reply("به منوی مدیریت بازگشتید:", reply_markup=admin_menu)
    except Exception as e:
        logger.error(f"Error in back_to_admin: {e}", exc_info=True)
        await message.reply("❌ خطا در بازگشت! دوباره تلاش کن.")

async def delete_pamphlet_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID or await state.get_state() != AdminStates.delete_menu:
        logger.warning(f"Invalid state or user for delete_pamphlet_cmd: {message.from_user.id}, state: {await state.get_state()}")
        return
    try:
        pamphlets = get_pamphlets()
        if not pamphlets:
            await message.reply("❌ هیچ جزوه‌ای نیست!", reply_markup=delete_menu)
            return
        response = "📝 لیست جزوات:\n\n" + "".join(f"- {p['title']} (ID: {p.get('id', 'نامشخص')})\n  👤 ID: {p.get('uploaded_by', 'ناشناس')}\n\n" for p in pamphlets) + "ID جزوه رو وارد کن:"
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response, reply_markup=delete_menu)
        await state.set_state(AdminStates.waiting_for_delete_pamphlet)
        logger.info(f"Pamphlet list sent to admin: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in delete_pamphlet_cmd: {e}", exc_info=True)
        await message.reply("❌ خطا در گرفتن لیست جزوات! دوباره تلاش کن.", reply_markup=delete_menu)

async def process_delete_pamphlet(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    try:
        pamphlet_id = int(message.text)
        if delete_pamphlet(pamphlet_id):
            await message.reply(f"✅ جزوه {pamphlet_id} حذف شد.", reply_markup=admin_menu)
            await state.set_state(AdminStates.admin_panel)
        else:
            await message.reply("❌ جزوه پیدا نشد! دوباره تلاش کن:", reply_markup=delete_menu)
    except ValueError:
        await message.reply("❌ ID باید عدد باشه!", reply_markup=delete_menu)
    except Exception as e:
        logger.error(f"Error in process_delete_pamphlet: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن:", reply_markup=delete_menu)

async def delete_book_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        logger.warning(f"Unauthorized access to delete_book_cmd: {message.from_user.id}")
        return
    current_state = await state.get_state()
    if current_state != AdminStates.delete_menu:
        logger.warning(f"Wrong state for delete_book_cmd: {current_state}")
        return
    try:
        books = get_books()
        if not books:
            await message.reply("❌ هیچ کتابی نیست!", reply_markup=delete_menu)
            logger.info("No books found in database")
            return
        response = "📚 لیست کتاب‌ها:\n\n" + "".join(f"- {b['title']} (ID: {b.get('id', 'نامشخص')})\n  👤 ID: {b.get('uploaded_by', 'ناشناس')}\n\n" for b in books) + "ID کتاب رو وارد کن (یا عنوان کامل برای کتاب‌های بدون ID):"
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response, reply_markup=delete_menu)
        await state.set_state(AdminStates.waiting_for_delete_book)
        logger.info(f"Book list sent to admin: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in delete_book_cmd: {e}", exc_info=True)
        await message.reply("❌ خطا در گرفتن لیست کتاب‌ها! دوباره تلاش کن.", reply_markup=delete_menu)

async def process_delete_book(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    try:
        try:
            book_id = int(message.text)
            if delete_book(book_id):
                await message.reply(f"✅ کتاب {book_id} حذف شد.", reply_markup=admin_menu)
                await state.set_state(AdminStates.admin_panel)
            else:
                await message.reply("❌ کتاب پیدا نشد! دوباره تلاش کن:", reply_markup=delete_menu)
        except ValueError:
            book_title = message.text.strip()
            if book_title == "نامشخص":
                await message.reply("❌ لطفاً عنوان کامل کتاب رو وارد کن!", reply_markup=delete_menu)
            elif delete_book(book_title):
                await message.reply(f"✅ کتاب '{book_title}' حذف شد.", reply_markup=admin_menu)
                await state.set_state(AdminStates.admin_panel)
            else:
                await message.reply("❌ کتاب پیدا نشد! دوباره تلاش کن:", reply_markup=delete_menu)
    except Exception as e:
        logger.error(f"Error in process_delete_book: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن:", reply_markup=delete_menu)

async def delete_video_cmd(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID or await state.get_state() != AdminStates.delete_menu:
        return
    try:
        videos = get_videos()
        if not videos:
            await message.reply("❌ هیچ ویدیویی نیست!", reply_markup=delete_menu)
            return
        response = "🎬 لیست ویدیوها:\n\n" + "".join(f"- {v.get('caption', 'بدون کپشن')} (ID: {v.get('id', 'نامشخص')})\n  👤 ID: {v.get('uploaded_by', 'ناشناس')}\n\n" for v in videos) + "ID ویدیو رو وارد کن:"
        if len(response) > 4096:
            parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for part in parts:
                await message.reply(part)
        else:
            await message.reply(response, reply_markup=delete_menu)
        await state.set_state(AdminStates.waiting_for_delete_video)
        logger.info(f"Video list sent to admin: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in delete_video_cmd: {e}", exc_info=True)
        await message.reply("❌ خطا در گرفتن لیست ویدیوها! دوباره تلاش کن.", reply_markup=delete_menu)

async def process_delete_video(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == "🔙 بازگشت به منوی مدیریت":
        await back_to_admin(message, state)
        return
    try:
        video_id = int(message.text)
        if delete_video(video_id):
            await message.reply(f"✅ ویدیو {video_id} حذف شد.", reply_markup=admin_menu)
            await state.set_state(AdminStates.admin_panel)
        else:
            await message.reply("❌ ویدیو پیدا نشد! دوباره تلاش کن:", reply_markup=delete_menu)
    except ValueError:
        await message.reply("❌ ID باید عدد باشه!", reply_markup=delete_menu)
    except Exception as e:
        logger.error(f"Error in process_delete_video: {e}", exc_info=True)
        await message.reply("❌ خطا! دوباره تلاش کن:", reply_markup=delete_menu)

async def exit_admin(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        await state.clear()
        await message.reply("از بخش مدیریت خارج شدی.", reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"Error in exit_admin: {e}", exc_info=True)
        await message.reply("❌ خطا در خروج! دوباره تلاش کن.")

def register_handlers(dp: Dispatcher):
    try:
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
        logger.info("Handlers registered successfully")
    except Exception as e:
        logger.error(f"Error registering handlers: {e}", exc_info=True)
