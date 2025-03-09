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
users_collection = db["users"]

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
    pamphlet = {
        "id": pamphlets_collection.count_documents({}) + 1,
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
    try:
        query = {}
        if department:
            query["department"] = department
        if course:
            query["course"] = course
        pamphlets = list(pamphlets_collection.find(query))
        logger.info(f"Retrieved {len(pamphlets)} pamphlets from database")
        # چک کردن داده‌ها
        for p in pamphlets:
            if "title" not in p or "id" not in p or "uploaded_by" not in p:
                logger.warning(f"Invalid pamphlet data: {p}")
        return pamphlets
    except Exception as e:
        logger.error(f"Error in get_pamphlets: {e}")
        return []

def delete_pamphlet(pamphlet_id):
    result = pamphlets_collection.delete_one({"id": pamphlet_id})
    return result.deleted_count > 0

# توابع برای مدیریت books
def add_book(title, file_id, uploaded_by, upload_date):
    book = {
        "id": books_collection.count_documents({}) + 1,
        "title": title,
        "file_id": file_id,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = books_collection.insert_one(book)
    return book["id"]

def get_books():
    try:
        books = list(books_collection.find({}))
        logger.info(f"Retrieved {len(books)} books from database")
        # چک کردن داده‌ها
        for b in books:
            if "title" not in b or "id" not in b or "uploaded_by" not in b:
                logger.warning(f"Invalid book data: {b}")
        return books
    except Exception as e:
        logger.error(f"Error in get_books: {e}")
        return []

def delete_book(book_id):
    result = books_collection.delete_one({"id": book_id})
    return result.deleted_count > 0

# توابع برای مدیریت videos
def add_video(file_id, file_unique_id, caption, uploaded_by, upload_date):
    video = {
        "id": videos_collection.count_documents({}) + 1,
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "caption": caption,
        "uploaded_by": uploaded_by,
        "upload_date": upload_date
    }
    result = videos_collection.insert_one(video)
    return video["id"]

def get_videos():
    try:
        videos = list(videos_collection.find({}))
        logger.info(f"Retrieved {len(videos)} videos from database")
        # چک کردن داده‌ها
        for v in videos:
            if "id" not in v or "uploaded_by" not in v:
                logger.warning(f"Invalid video data: {v}")
        return videos
    except Exception as e:
        logger.error(f"Error in get_videos: {e}")
        return []

def delete_video(video_id):
    result = videos_collection.delete_one({"id": video_id})
    return result.deleted_count > 0

# توابع مدیریت کاربران
def ban_user(user_id):
    users_collection.update_one(
        {"user_id": str(user_id)},
        {"$set": {"banned": True}},
        upsert=True
    )

def is_user_banned(user_id):
    user = users_collection.find_one({"user_id": str(user_id)})
    return user and user.get("banned", False)

def get_user_count():
    unique_users = set()
    for collection in [pamphlets_collection, books_collection, videos_collection]:
        users = collection.distinct("uploaded_by")
        unique_users.update(users)
    return len(unique_users)

def get_all_users():
    users = users_collection.find()
    return [(user["user_id"], user.get("banned", False)) for user in users]

def unban_user(user_id):
    users_collection.update_one(
        {"user_id": str(user_id)},
        {"$set": {"banned": False}},
        upsert=True
    )

def add_user(user_id):
    if not users_collection.find_one({"user_id": str(user_id)}):
        users_collection.insert_one({"user_id": str(user_id), "banned": False})
