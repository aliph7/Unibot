from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 جزوات"), KeyboardButton(text="📖 کتاب‌ها")],
            [KeyboardButton(text="🎥 ویدیوهای آموزشی")],
            [KeyboardButton(text="🔄 شروع مجدد")]
        ],
        resize_keyboard=True
    )

def get_pamphlets_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="مشاهده جزوات 📖"), KeyboardButton(text="آپلود جزوه 📤")],
            [KeyboardButton(text="🔍 جستجوی جزوه")],
            [KeyboardButton(text="🔙 برگشت به منوی اصلی")]
        ],
        resize_keyboard=True
    ) 