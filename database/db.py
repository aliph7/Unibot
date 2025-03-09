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
    logger.info(f"Added pamphlet with ID: {pamphlet['id']}")
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
        for p in pamphlets:
            missing_fields = [field for field in ["title", "id", "uploaded_by"] if field not in p]
            if missing_fields:
                logger.warning(f"Pamphlet missing fields {missing_fields}: {p}")
        return pamphlets
    except Exception as e:
        logger.error(f"Error in get_pamphlets: {e}")
        return []

def delete_pamphlet(pamphlet_id):
    try:
        result = pamphlets_collection.delete_one({"id": pamphlet_id})
        logger.info(f"Deleted pamphlet with ID: {pamphlet_id}, count: {result.deleted_count}")
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error in delete_pamphlet: {e}")
        return False

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
    logger.info(f"Added book with ID: {book['id']}")
    return book["id"]

def get_books():
    try:
        books = list(books_collection.find({}))
        logger.info(f"Retrieved {len(books)} books from database")
        for b in books:
            missing_fields = [field for field in ["title", "id", "uploaded_by"] if field not in b]
            if missing_fields:
                logger.warning(f"Book missing fields {missing_fields}: {b}")
        return books
    except Exception as e:
        logger.error(f"Error in get_books: {e}")
        return []

def delete_book(book_id_or_title):
    try:
        # اگه عدد باشه، با id حذف می‌کنه
        if isinstance(book_id_or_title, int):
            result = books_collection.delete_one({"id": book_id_or_title})
            logger.info(f"Deleted book with ID: {book_id_or_title}, count: {result.deleted_count}")
            return result.deleted_count > 0
        # اگه "نامشخص" یا رشته باشه، با title حذف می‌کنه
        else:
            result = books_collection.delete_one({"title": book_id_or_title})
            logger.info(f"Deleted book with title: {book_id_or_title}, count: {result.deleted_count}")
            return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error in delete_book: {e}")
        return False

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
    logger.info(f"Added video with ID: {video['id']}")
    return video["id"]

def get_videos():
    try:
        videos = list(videos_collection.find({}))
        logger.info(f"Retrieved {len(videos)} videos from database")
        for v in videos:
            missing_fields = [field for field in ["id", "uploaded_by"] if field not in v]
            if missing_fields:
                logger.warning(f"Video missing fields {missing_fields}: {v}")
        return videos
    except Exception as e:
        logger.error(f"Error in get_videos: {e}")
        return []

def delete_video(video_id):
    try:
        result = videos_collection.delete_one({"id": video_id})
        logger.info(f"Deleted video with ID: {video_id}, count: {result.deleted_count}")
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error in delete_video: {e}")
        return False

# توابع مدیریت کاربران
def ban_user(user_id):
    try:
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {"banned": True}},
            upsert=True
        )
        logger.info(f"Banned user: {user_id}")
    except Exception as e:
        logger.error(f"Error in ban_user: {e}")

def is_user_banned(user_id):
    try:
        user = users_collection.find_one({"user_id": str(user_id)})
        return user and user.get("banned", False)
    except Exception as e:
        logger.error(f"Error in is_user_banned: {e}")
        return False

def get_user_count():
    try:
        unique_users = set()
        for collection in [pamphlets_collection, books_collection, videos_collection]:
            users = collection.distinct("uploaded_by")
            unique_users.update(users)
        logger.info(f"Retrieved {len(unique_users)} unique users")
        return len(unique_users)
    except Exception as e:
        logger.error(f"Error in get_user_count: {e}")
        return 0

def get_all_users():
    try:
        users = users_collection.find()
        result = [(user["user_id"], user.get("banned", False)) for user in users]
        logger.info(f"Retrieved {len(result)} users")
        return result
    except Exception as e:
        logger.error(f"Error in get_all_users: {e}")
        return []

def unban_user(user_id):
    try:
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {"banned": False}},
            upsert=True
        )
        logger.info(f"Unbanned user: {user_id}")
    except Exception as e:
        logger.error(f"Error in unban_user: {e}")

def add_user(user_id):
    try:
        if not users_collection.find_one({"user_id": str(user_id)}):
            users_collection.insert_one({"user_id": str(user_id), "banned": False})
            logger.info(f"Added user: {user_id}")
    except Exception as e:
        logger.error(f"Error in add_user: {e}")
