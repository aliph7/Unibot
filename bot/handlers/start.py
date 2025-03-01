from aiogram import types, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from keyboards.keyboards import get_main_keyboard

async def cmd_start(message: types.Message):
    """هندلر دستور /start"""
    await message.reply(
        "👋 سلام! به ربات دانشگاه خوش آمدید!\n"
        "از منوی زیر بخش مورد نظر خود را انتخاب کنید:",
        reply_markup=get_main_keyboard()
    )

async def cmd_help(message: types.Message):
    """هندلر دستور /help"""
    help_text = """
🤖 راهنمای ربات:

/start - شروع مجدد ربات
/help - نمایش این راهنما
/cancel - لغو عملیات فعلی

از دکمه‌های زیر برای کار با ربات استفاده کنید.
"""
    await message.reply(help_text)

async def return_to_main_menu(message: types.Message, state: FSMContext):
    """برگشت به منوی اصلی"""
    await state.clear()
    await message.reply(
        "به منوی اصلی بازگشتید.",
        reply_markup=get_main_keyboard()
    )

def register_handlers(dp: Dispatcher):
    """ثبت هندلرها"""
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(return_to_main_menu, lambda message: message.text == "🔙 برگشت به منوی اصلی") 