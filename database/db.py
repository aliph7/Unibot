from pymongo import MongoClient
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

client = MongoClient(os.getenv("MONGO_URI", "YOUR_MONGODB_CONNECTION_STRING"))
db = client["university_bot"]

# مجموعه‌های موجود
pamphlets_collection = db["pamphlets"]
books_collection = db["books"]
videos_collection = db["videos"]
users_collection = db["users"]

# مجموعه برای تعاملات AI
ai_interactions_collection = db["ai_interactions"]

def setup_database():
    """اتصال به MongoDB و تنظیمات اولیه"""
    try:
        client.server_info()
        logger.info("Connected to MongoDB successfully")
        
        # تنظیم TTL Index برای مجموعه ai_interactions
        try:
            ai_interactions_collection.create_index("expire_at", expireAfterSeconds=3600)
            logger.info("TTL Index برای ai_interactions تنظیم شد")
        except Exception as e:
            logger.error(f"خطا در تنظیم TTL Index برای ai_interactions: {e}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

# توابع مربوط به جزوات
def add_pamphlet(title, file_id, department, course, uploaded_by, upload_date):
    pamphlet = {
        "id": pamphlets_collection.count_documents({}) + 1,
        "title": title,
        "file_id": file_id,
        "department": department,
        "course": course,
        "uploaded_by": str(uploaded_by),
        "upload_date": upload_date
    }
    result = pamphlets_collection.insert_one(pamphlet)
    users_collection.update_one(
        {"user_id": str(uploaded_by)},
        {"$set": {"banned": False}},
        upsert=True
    )
    logger.info(f"Added pamphlet with ID: {pamphlet['id']} and registered user: {uploaded_by}")
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

# توابع مربوط به کتاب‌ها
def add_book(title, file_id, uploaded_by, upload_date):
    book = {
        "id": books_collection.count_documents({}) + 1,
        "title": title,
        "file_id": file_id,
        "uploaded_by": str(uploaded_by),
        "upload_date": upload_date
    }
    result = books_collection.insert_one(book)
    users_collection.update_one(
        {"user_id": str(uploaded_by)},
        {"$set": {"banned": False}},
        upsert=True
    )
    logger.info(f"Added book with ID: {book['id']} and registered user: {uploaded_by}")
    return book["id"]

def get_books():
    try:
        books = list(books_collection.find({}))
        logger.info(f"Retrieved {len(books)} books from database")
        return books
    except Exception as e:
        logger.error(f"Error in get_books: {e}")
        return []

def delete_book(book_id_or_title):
    try:
        if isinstance(book_id_or_title, int):
            result = books_collection.delete_one({"id": book_id_or_title})
            logger.info(f"Deleted book with ID: {book_id_or_title}, count: {result.deleted_count}")
            return result.deleted_count > 0
        else:
            result = books_collection.delete_one({"title": book_id_or_title})
            logger.info(f"Deleted book with title: {book_id_or_title}, count: {result.deleted_count}")
            return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error in delete_book: {e}")
        return False

# توابع مربوط به ویدیوها
def add_video(file_id, file_unique_id, caption, uploaded_by, upload_date):
    video = {
        "id": videos_collection.count_documents({}) + 1,
        "file_id": file_id,
        "file_unique_id": file_unique_id,
        "caption": caption,
        "uploaded_by": str(uploaded_by),
        "upload_date": upload_date
    }
    result = videos_collection.insert_one(video)
    users_collection.update_one(
        {"user_id": str(uploaded_by)},
        {"$set": {"banned": False}},
        upsert=True
    )
    logger.info(f"Added video with ID: {video['id']} and registered user: {uploaded_by}")
    return video["id"]

def get_videos():
    try:
        videos = list(videos_collection.find({}))
        logger.info(f"Retrieved {len(videos)} videos from database")
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

# توابع مربوط به کاربران
def ban_user(user_id):
    try:
        result = users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {"banned": True}},
            upsert=True
        )
        logger.info(f"Banned user: {user_id}, matched: {result.matched_count}, modified: {result.modified_count}")
        user = users_collection.find_one({"user_id": str(user_id)})
        if user and user.get("banned", False):
            logger.info(f"Confirmed ban for user: {user_id}")
        else:
            logger.error(f"Failed to confirm ban for user: {user_id}, doc: {user}")
    except Exception as e:
        logger.error(f"Error in ban_user: {e}")

def is_user_banned(user_id):
    try:
        user = users_collection.find_one({"user_id": str(user_id)})
        banned = user and user.get("banned", False)
        logger.info(f"Checked ban status for {user_id}: {banned}, doc: {user}")
        return banned
    except Exception as e:
        logger.error(f"Error in is_user_banned: {e}")
        return False

def get_user_count():
    try:
        unique_users = set()
        for collection in [pamphlets_collection, books_collection, videos_collection, ai_interactions_collection]:
            users = collection.distinct("user_id")
            unique_users.update(users)
        logger.info(f"Retrieved {len(unique_users)} unique users")
        return len(unique_users)
    except Exception as e:
        logger.error(f"Error in get_user_count: {e}")
        return 0

def get_all_users():
    try:
        unique_users = set()
        for collection in [pamphlets_collection, books_collection, videos_collection, ai_interactions_collection]:
            users = collection.distinct("user_id")
            for user in users:
                if user:
                    unique_users.add(str(user))
        result = []
        for user_id in unique_users:
            user = users_collection.find_one({"user_id": user_id})
            is_banned = user.get("banned", False) if user else False
            result.append((user_id, is_banned))
        logger.info(f"Retrieved {len(result)} uploaders: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in get_all_users: {e}")
        return []

def unban_user(user_id):
    try:
        result = users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {"banned": False}},
            upsert=True
        )
        logger.info(f"Unbanned user: {user_id}, matched: {result.matched_count}, modified: {result.modified_count}")
    except Exception as e:
        logger.error(f"Error in unban_user: {e}")

def add_user(user_id, username="unknown"):
    try:
        if not users_collection.find_one({"user_id": str(user_id)}):
            users_collection.insert_one({
                "user_id": str(user_id),
                "username": username,
                "banned": False,
                "ai_messages": 0,
                "last_reset": datetime.now()
            })
            logger.info(f"Added user: {user_id}")
    except Exception as e:
        logger.error(f"Error in add_user: {e}")

# توابع مربوط به تعاملات AI
def add_ai_interaction(user_id, username, input_text, response_text):
    """ذخیره تعامل جدید با AI"""
    try:
        interaction = {
            "user_id": str(user_id),
            "username": username or "unknown",
            "input": input_text,
            "response": response_text,
            "timestamp": datetime.now(),
            "expire_at": datetime.now() + timedelta(seconds=3600)  # دقیقاً 1 ساعت بعد
        }
        result = ai_interactions_collection.insert_one(interaction)
        logger.info(f"Added AI interaction for user {user_id}: ID={result.inserted_id}, input={input_text[:50]}...")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error in add_ai_interaction: {e}")
        return None

def get_ai_interactions(user_id=None, limit=3):
    """بازیابی تعاملات AI (اختیاری: بر اساس کاربر) با محدودیت تعداد"""
    try:
        query = {}
        if user_id:
            query["user_id"] = str(user_id)
        interactions = list(
            ai_interactions_collection.find(query)
            .sort("timestamp", 1)  # از قدیمی به جدید
            .limit(limit)  # محدود به 3 تعامل آخر
        )
        logger.info(f"Retrieved {len(interactions)} AI interactions for user: {user_id or 'all'}, interactions={interactions}")
        return interactions
    except Exception as e:
        logger.error(f"Error in get_ai_interactions: {e}")
        return []

# تابع برای مدیریت سهمیه روزانه
def check_and_update_ai_quota(user_id, username="unknown"):
    """چک کردن و به‌روزرسانی سهمیه روزانه پیام‌های AI"""
    try:
        user = users_collection.find_one({"user_id": str(user_id)})
        now = datetime.now()
        daily_limit = 10

        if user and "ai_messages" in user:
            last_reset = user.get("last_reset", now)
            message_count = user.get("ai_messages", 0)

            # ریست سهمیه روزانه
            if now.date() > last_reset.date():
                users_collection.update_one(
                    {"user_id": str(user_id)},
                    {"$set": {
                        "ai_messages": 0,
                        "last_reset": now,
                        "username": username
                    }}
                )
                message_count = 0
                logger.info(f"Quota reset for user {user_id}")

            # چک کردن سهمیه
            if message_count >= daily_limit:
                logger.info(f"User {user_id} reached daily limit: {message_count}/{daily_limit}")
                return False, message_count

            # افزایش تعداد پیام‌ها
            users_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {
                    "ai_messages": message_count + 1,
                    "username": username,
                    "last_reset": last_reset
                }}
            )
            logger.info(f"Updated quota for user {user_id}: {message_count + 1}/{daily_limit}")
            return True, message_count + 1

        else:
            # کاربر جدید
            users_collection.insert_one({
                "user_id": str(user_id),
                "username": username,
                "banned": False,
                "ai_messages": 1,
                "last_reset": now
            })
            logger.info(f"New user {user_id} added with quota: 1/{daily_limit}")
            return True, 1

    except Exception as e:
        logger.error(f"Error in check_and_update_ai_quota: {e}")
        return False, 0
