from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import logging
from itertools import chain

from states.states import BotStates
from config.config import DEPARTMENTS, COURSES
from keyboards.keyboards import get_main_keyboard, get_pamphlets_keyboard
from database import add_pamphlet, get_pamphlets  # توابع MongoDB

logger = logging.getLogger(__name__)

async def show_pamphlets_menu(message: types.Message):
    """نمایش منوی اصلی جزوات"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="مشاهده جزوات 📖"), KeyboardButton(text="آپلود جزوه 📤")],
            [KeyboardButton(text="جستجوی جزوه 🔍")],
            [KeyboardButton(text="🔙 برگشت به منوی اصلی")]
        ],
        resize_keyboard=True
    )
    await message.reply(
        "به بخش جزوات خوش آمدید!\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=keyboard
    )

async def return_to_pamphlets(message: types.Message, state: FSMContext):
    """برگشت به منوی جزوات"""
    await state.clear()
    await show_pamphlets_menu(message)

async def start_upload_pamphlet(message: types.Message, state: FSMContext):
    """شروع فرایند آپلود جزوه"""
    await state.set_state(BotStates.waiting_for_upload_department)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="مهندسی کامپیوتر 💻 📤"), KeyboardButton(text="مهندسی برق ⚡ 📤")],
            [KeyboardButton(text="مهندسی مکانیک 🔧 📤"), KeyboardButton(text="مهندسی عمران 🏗 📤")],
            [KeyboardButton(text="مهندسی شیمی 🧪 📤")],
            [KeyboardButton(text="🔙 برگشت به بخش جزوات")]
        ],
        resize_keyboard=True
    )
    await message.reply("لطفاً رشته مورد نظر برای آپلود جزوه را انتخاب کنید:", reply_markup=keyboard)

async def process_upload_department(message: types.Message, state: FSMContext):
    """پردازش انتخاب رشته برای آپلود"""
    dept_text = message.text.replace(" 📤", "")
    if dept_text not in DEPARTMENTS:
        await message.reply("❌ لطفاً یک رشته معتبر انتخاب کنید.")
        return

    await state.update_data(department=DEPARTMENTS[dept_text])
    await state.set_state(BotStates.waiting_for_upload_course)
    
    courses = COURSES[DEPARTMENTS[dept_text]]
    keyboard_rows = []
    for i in range(0, len(courses), 2):
        row = [KeyboardButton(text=f"{courses[i]} 📤")]
        if i + 1 < len(courses):
            row.append(KeyboardButton(text=f"{courses[i + 1]} 📤"))
        keyboard_rows.append(row)
    keyboard_rows.append([KeyboardButton(text="🔙 برگشت به لیست رشته‌ها")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)
    await message.reply("لطفاً درس مورد نظر را انتخاب کنید:", reply_markup=keyboard)

async def process_upload_course(message: types.Message, state: FSMContext):
    """پردازش انتخاب درس برای آپلود"""
    course = message.text.replace(" 📤", "")
    data = await state.get_data()
    department = data.get('department')
    
    if not department or course not in COURSES[department]:
        await message.reply("❌ لطفاً یک درس معتبر انتخاب کنید.")
        return
    
    await state.update_data(course=course)
    await state.set_state(BotStates.waiting_for_pamphlet)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 برگشت به لیست درس‌ها")]],
        resize_keyboard=True
    )
    await message.reply(
        "لطفاً جزوه خود را به صورت PDF ارسال کنید.\n"
        "برای لغو، دستور /cancel را بفرستید.",
        reply_markup=keyboard
    )

async def process_pamphlet_upload(message: types.Message, state: FSMContext):
    """پردازش آپلود جزوه"""
    if not message.document or not message.document.mime_type == "application/pdf":
        await message.reply("❌ لطفاً فقط فایل PDF ارسال کنید.")
        return
        
    data = await state.get_data()
    department = data.get('department')
    course = data.get('course')
    
    try:
        add_pamphlet(
            title=message.document.file_name,
            file_id=message.document.file_id,
            department=department,
            course=course,
            uploaded_by=message.from_user.username or str(message.from_user.id),
            upload_date=datetime.now().strftime("%Y-%m-%d")
        )
        await message.reply("✅ جزوه با موفقیت آپلود شد.", reply_markup=get_pamphlets_keyboard())
        await state.clear()
    except Exception as e:
        logger.error(f"Error uploading pamphlet: {e}")
        await message.reply("❌ خطا در آپلود جزوه.")

async def view_pamphlets(message: types.Message, state: FSMContext):
    """نمایش لیست جزوات"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="مهندسی کامپیوتر 💻"), KeyboardButton(text="مهندسی برق ⚡")],
            [KeyboardButton(text="مهندسی مکانیک 🔧"), KeyboardButton(text="مهندسی عمران 🏗")],
            [KeyboardButton(text="مهندسی شیمی 🧪")],
            [KeyboardButton(text="🔙 برگشت به بخش جزوات")]
        ],
        resize_keyboard=True
    )
    await message.reply("لطفاً رشته مورد نظر را انتخاب کنید:", reply_markup=keyboard)
    await state.set_state(BotStates.waiting_for_view_department)

async def show_department_pamphlets(message: types.Message, state: FSMContext):
    """نمایش جزوات یک رشته خاص"""
    department = None
    for dept_name, dept_code in DEPARTMENTS.items():
        if message.text == dept_name:
            department = dept_code
            break
    
    if not department:
        return

    await state.update_data(department=department)
    await state.set_state(BotStates.waiting_for_view_course)
    
    courses = COURSES[department]
    keyboard_rows = []
    for i in range(0, len(courses), 2):
        row = [KeyboardButton(text=courses[i])]
        if i + 1 < len(courses):
            row.append(KeyboardButton(text=courses[i + 1]))
        keyboard_rows.append(row)
    keyboard_rows.append([KeyboardButton(text="🔙 برگشت به لیست رشته‌ها")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)
    await message.reply("لطفاً درس مورد نظر را انتخاب کنید:", reply_markup=keyboard)

async def return_to_upload_departments(message: types.Message, state: FSMContext):
    """برگشت به لیست رشته‌ها در حالت آپلود"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="مهندسی کامپیوتر 💻 📤"), KeyboardButton(text="مهندسی برق ⚡ 📤")],
            [KeyboardButton(text="مهندسی مکانیک 🔧 📤"), KeyboardButton(text="مهندسی عمران 🏗 📤")],
            [KeyboardButton(text="مهندسی شیمی 🧪 📤")],
            [KeyboardButton(text="🔙 برگشت به بخش جزوات")]
        ],
        resize_keyboard=True
    )
    await message.reply("لطفاً رشته مورد نظر برای آپلود جزوه را انتخاب کنید:", reply_markup=keyboard)
    await state.set_state(BotStates.waiting_for_upload_department)

async def return_to_upload_courses(message: types.Message, state: FSMContext):
    """برگشت به لیست درس‌ها در حالت آپلود"""
    data = await state.get_data()
    department = data.get('department')
    
    if not department:
        await show_pamphlets_menu(message)
        return
        
    await state.set_state(BotStates.waiting_for_upload_course)
    courses = COURSES[department]
    keyboard_rows = []
    for i in range(0, len(courses), 2):
        row = [KeyboardButton(text=f"{courses[i]} 📤")]
        if i + 1 < len(courses):
            row.append(KeyboardButton(text=f"{courses[i + 1]} 📤"))
        keyboard_rows.append(row)
    keyboard_rows.append([KeyboardButton(text="🔙 برگشت به لیست رشته‌ها")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)
    await message.reply("لطفاً درس مورد نظر را انتخاب کنید:", reply_markup=keyboard)

async def start_pamphlet_search(message: types.Message, state: FSMContext):
    """شروع جستجوی جزوه"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 برگشت به بخش جزوات")]],
        resize_keyboard=True
    )
    await message.reply(
        "لطفاً عبارت مورد نظر برای جستجو در عنوان جزوات را وارد کنید:",
        reply_markup=keyboard
    )
    await state.set_state(BotStates.waiting_for_pamphlet_search)

async def process_pamphlet_search(message: types.Message, state: FSMContext):
    """پردازش جستجوی جزوه"""
    if message.text == "🔙 برگشت به بخش جزوات":
        await show_pamphlets_menu(message)
        await state.clear()
        return

    search_term = message.text.lower()
    
    try:
        pamphlets = get_pamphlets()  # همه جزوات رو می‌گیره
        filtered_pamphlets = [
            p for p in pamphlets
            if search_term in p["title"].lower() or search_term in p["course"].lower()
        ]
        
        if not filtered_pamphlets:
            await message.reply("❌ هیچ جزوه‌ای با این عبارت پیدا نشد.")
            return
            
        await message.reply(f"🔍 نتایج جستجو برای '{message.text}':")
        for pamphlet in filtered_pamphlets:
            await message.reply_document(
                pamphlet["file_id"],
                caption=f"📝 عنوان: {pamphlet['title']}\n📚 درس: {pamphlet['course']}"
            )
    except Exception as e:
        logger.error(f"Error in process_pamphlet_search: {e}")
        await message.reply("❌ خطا در جستجوی جزوه.")

async def show_course_pamphlets(message: types.Message, state: FSMContext):
    """نمایش جزوات یک درس خاص"""
    data = await state.get_data()
    department = data.get('department')
    
    if not department or message.text not in COURSES[department]:
        return

    try:
        pamphlets = get_pamphlets(department=department, course=message.text)
        
        if not pamphlets:
            await message.reply("❌ هیچ جزوه‌ای برای این درس موجود نیست.")
            return
            
        await message.reply(f"📚 جزوات درس {message.text}:")
        for pamphlet in pamphlets:
            await message.reply_document(
                pamphlet["file_id"],
                caption=f"📝 عنوان: {pamphlet['title']}"
            )
    except Exception as e:
        logger.error(f"Error in show_course_pamphlets: {e}")
        await message.reply("❌ خطا در نمایش جزوات.")

async def return_to_departments(message: types.Message, state: FSMContext):
    """برگشت به لیست رشته‌ها"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="مهندسی کامپیوتر 💻"), KeyboardButton(text="مهندسی برق ⚡")],
            [KeyboardButton(text="مهندسی مکانیک 🔧"), KeyboardButton(text="مهندسی عمران 🏗")],
            [KeyboardButton(text="مهندسی شیمی 🧪")],
            [KeyboardButton(text="🔙 برگشت به بخش جزوات")]
        ],
        resize_keyboard=True
    )
    await message.reply("لطفاً رشته مورد نظر را انتخاب کنید:", reply_markup=keyboard)
    await state.clear()

def register_handlers(dp: Dispatcher):
    """ثبت تمام هندلرهای مربوط به جزوات"""
    dp.message.register(show_pamphlets_menu, lambda message: message.text == "📚 جزوات")
    dp.message.register(return_to_pamphlets, lambda message: message.text == "🔙 برگشت به بخش جزوات")
    dp.message.register(start_upload_pamphlet, lambda message: message.text == "آپلود جزوه 📤")
    dp.message.register(view_pamphlets, lambda message: message.text == "مشاهده جزوات 📖")
    dp.message.register(start_pamphlet_search, lambda message: message.text == "جستجوی جزوه 🔍")
    
    dp.message.register(process_upload_department, lambda message: message.text and message.text.endswith("📤"), BotStates.waiting_for_upload_department)
    dp.message.register(process_upload_course, lambda message: message.text and message.text.endswith("📤"), BotStates.waiting_for_upload_course)
    dp.message.register(return_to_upload_departments, lambda message: message.text == "🔙 برگشت به لیست رشته‌ها", BotStates.waiting_for_upload_course)
    dp.message.register(return_to_upload_courses, lambda message: message.text == "🔙 برگشت به لیست درس‌ها", BotStates.waiting_for_pamphlet)
    dp.message.register(process_pamphlet_upload, BotStates.waiting_for_pamphlet)
    
    dp.message.register(show_department_pamphlets, lambda message: message.text in DEPARTMENTS, BotStates.waiting_for_view_department)
    dp.message.register(show_course_pamphlets, lambda message: message.text in list(chain.from_iterable(COURSES.values())), BotStates.waiting_for_view_course)
    dp.message.register(return_to_departments, lambda message: message.text == "🔙 برگشت به لیست رشته‌ها", BotStates.waiting_for_view_course)
    
    dp.message.register(process_pamphlet_search, BotStates.waiting_for_pamphlet_search)
