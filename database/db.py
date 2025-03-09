from pymongo import MongoClient
import os
import logging

logger = logging.getLogger(__name__)

# اتصال به MongoDB
client = MongoClient(os.getenv("MONGO_URI", "YOUR_MONGODB_CONNECTION_STRING"))
db = client["university_bot"]

# مجموعه‌ها
pamphlets_collection = db["pamphlets"]
books_collection = db["books"]
videos_collection = db["videos"]
users_collection = db["users"]  # برای مدیریت کاربران

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
        "id": pamphlets_collection.count_documents({}) + 1,  # اضافه کردن id برای سازگاری با admin
        "title": title,
        "file_id": file_id,
        "department": department,
        "course": course,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = pamphlets_collection.insert_one(pamphlet)
    return pamphlet["id"]

def get_pamphlets(department=None, course=None):
    """گرفتن لیست جزوات با فیلتر اختیاری"""
    query = {}
    if department:
        query["department"] = department
    if course:
        query["course"] = course
    return list(pamphlets_collection.find(query))

def delete_pamphlet(pamphlet_id):
    """حذف جزوه با id"""
    result = pamphlets_collection.delete_one({"id": pamphlet_id})
    return result.deleted_count > 0

# توابع برای مدیریت books
def add_book(title, file_id, uploaded_by, upload_date):
    """اضافه کردن یه کتاب جدید"""
    book = {
        "id": books_collection.count_documents({}) + 1,  # اضافه کردن id
        "title": title,
        "file_id": file_id,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = books_collection.insert_one(book)
    return book["id"]

def get_books():
    """گرفتن لیست همه کتاب‌ها"""
    return list(books_collection.find({}))

def delete_book(book_id):
    """حذف کتاب با id"""
    result = books_collection.delete_one({"id": book_id})
    return result.deleted_count > 0

# توابع برای مدیریت videos
def add_video(file_id, file_unique_id, caption, uploaded_by, upload_date):
    """اضافه کردن یه ویدیو جدید"""
    video = {
        "id": videos_collection.count_documents({}) + 1,  # اضافه کردن id
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "caption": caption,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = videos_collection.insert_one(video)
    return video["id"]

def get_videos():
    """گرفتن لیست همه ویدیوها"""
    return list(videos_collection.find({}))

def delete_video(video_id):
    """حذف ویدیو با id"""
    result = videos_collection.delete_one({"id": video_id})
    return result.deleted_count > 0

# توابع مدیریت کاربران (برای admin و middleware)
def ban_user(user_id):
    """بن کردن کاربر"""
    users_collection.update_one(
        {"user_id": str(user_id)},
        {"$set": {"banned": True}},
        upsert=True
    )

def is_user_banned(user_id):
    """چک کردن وضعیت بن کاربر"""
    user = users_collection.find_one({"user_id": str(user_id)})
    return user and user.get("banned", False)

def get_user_count():
    """گرفتن تعداد کاربران منحصربه‌فرد"""
    unique_users = set()
    for collection in [pamphlets_collection, books_collection, videos_collection]:
        users = collection.distinct("uploaded_by")
        unique_users.update(users)
    return len(unique_users)

def get_all_users():
    """گرفتن لیست همه کاربران"""
    users = users_collection.find()
    return [(user["user_id"], user.get("banned", False)) for user in users]

def unban_user(user_id):
    """آن‌بن کردن کاربر"""
    users_collection.update_one(
        {"user_id": str(user_id)},
        {"$set": {"banned": False}},
        upsert=True
    )

def add_user(user_id):
    """اضافه کردن کاربر جدید"""
    if not users_collection.find_one({"user_id": str(user_id)}):
        users_collection.insert_one({"user_id": str(user_id), "banned": False})
