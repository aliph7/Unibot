from pymongo import MongoClient
import os
import logging

logger = logging.getLogger(__name__)

# اتصال به MongoDB
client = MongoClient(os.getenv("MONGO_URI", "YOUR_MONGODB_CONNECTION_STRING"))
db = client["university_bot"]

# مجموعه‌ها (معادل جداول SQLite)
pamphlets_collection = db["pamphlets"]
books_collection = db["books"]
videos_collection = db["videos"]  # اسم رو با handlers هماهنگ کردم

def setup_database():
    """تست اتصال به دیتابیس MongoDB"""
    try:
        client.server_info()  # چک کردن اتصال
        logger.info("Connected to MongoDB successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

# توابع برای مدیریت pamphlets
def add_pamphlet(title, file_id, department, course, uploaded_by, upload_date):
    """اضافه کردن یه جزوه جدید"""
    pamphlet = {
        "title": title,
        "file_id": file_id,
        "department": department,
        "course": course,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = pamphlets_collection.insert_one(pamphlet)
    return result.inserted_id

def get_pamphlets(department=None, course=None):
    """گرفتن لیست جزوات با فیلتر اختیاری"""
    query = {}
    if department:
        query["department"] = department
    if course:
        query["course"] = course
    return list(pamphlets_collection.find(query))

# توابع برای مدیریت books
def add_book(title, file_id, uploaded_by, upload_date):
    """اضافه کردن یه کتاب جدید"""
    book = {
        "title": title,
        "file_id": file_id,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = books_collection.insert_one(book)
    return result.inserted_id

def get_books():
    """گرفتن لیست همه کتاب‌ها"""
    return list(books_collection.find({}))

# توابع برای مدیریت videos
def add_video(file_id, file_unique_id, caption, uploaded_by, upload_date):
    """اضافه کردن یه ویدیو جدید"""
    video = {
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "caption": caption,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = videos_collection.insert_one(video)
    return result.inserted_id

def get_videos():
    """گرفتن لیست همه ویدیوها"""
    return list(videos_collection.find({}))
