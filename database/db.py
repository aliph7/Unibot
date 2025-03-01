import sqlite3
import logging

logger = logging.getLogger(__name__)

def setup_database():
    """راه‌اندازی دیتابیس و ایجاد جداول مورد نیاز"""
    try:
        conn = sqlite3.connect('university_bot.db')
        c = conn.cursor()
        
        # جدول جزوات
        c.execute('''CREATE TABLE IF NOT EXISTS pamphlets
                     (id INTEGER PRIMARY KEY,
                      title TEXT,
                      file_id TEXT,
                      department TEXT,
                      course TEXT,
                      uploaded_by TEXT,
                      upload_date TEXT)''')
        
        # جدول کتاب‌ها
        c.execute('''CREATE TABLE IF NOT EXISTS books
                     (id INTEGER PRIMARY KEY,
                      title TEXT,
                      file_id TEXT,
                      uploaded_by TEXT,
                      upload_date TEXT)''')
        
        # جدول ویدیوها
        c.execute('''CREATE TABLE IF NOT EXISTS educational_videos
                     (id INTEGER PRIMARY KEY,
                      title TEXT,
                      file_id TEXT,
                      uploaded_by TEXT,
                      upload_date TEXT)''')
        
        conn.commit()
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise e
        
    finally:
        conn.close() 