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
videos_collection = db["educational_videos"]

def setup_database():
    """راه‌اندازی دیتابیس و ایجاد مجموعه‌های مورد نیاز"""
    try:
        # MongoDB خودش مجموعه‌ها رو موقع اولین استفاده می‌سازه
        # نیازی به ایجاد دستی نیست، ولی می‌تونیم چک کنیم اتصال برقراره
        client.server_info()  # تست اتصال به سرور MongoDB
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise e

# توابع برای مدیریت pamphlets
def add_pamphlet(title, file_id, department, course, uploaded_by, upload_date):
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
    query = {}
    if department:
        query["department"] = department
    if course:
        query["course"] = course
    return list(pamphlets_collection.find(query))

# توابع برای مدیریت books
def add_book(title, file_id, uploaded_by, upload_date):
    book = {
        "title": title,
        "file_id": file_id,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = books_collection.insert_one(book)
    return result.inserted_id

def get_books():
    return list(books_collection.find({}))

# توابع برای مدیریت videos
def add_video(title, file_id, uploaded_by, upload_date):
    video = {
        "title": title,
        "file_id": file_id,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = videos_collection.insert_one(video)
    return result.inserted_id

def get_videos():
    return list(videos_collection.find({}))
