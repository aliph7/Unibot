from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    """کلاس مدیریت وضعیت‌های ربات"""
    # وضعیت‌های آپلود
    waiting_for_upload_department = State()
    waiting_for_upload_course = State()
    waiting_for_pamphlet = State()
    
    # وضعیت‌های مشاهده
    waiting_for_view_department = State()
    waiting_for_view_course = State()
    
    # وضعیت جستجو
    waiting_for_pamphlet_search = State()
    
    # وضعیت‌های مربوط به کتاب‌ها
    waiting_for_book = State()
    waiting_for_book_search = State()
    
    # وضعیت‌های مربوط به ویدیوها
    waiting_for_video = State()
    waiting_for_video_caption = State()
    waiting_for_video_search = State()
    waiting_for_department = State()
    waiting_for_course = State()
    
    # وضعیت‌های مربوط به ویدیوها
    waiting_for_video = State()
    waiting_for_video_caption = State()
    waiting_for_video_search = State() 