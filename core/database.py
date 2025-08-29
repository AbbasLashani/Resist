# research_assistant/core/database.py
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config):
        self.config = config
        db_path = config.get("database_path", "research_db.sqlite")
        self.connection = sqlite3.connect(db_path)
        self.init_tables()
    
    def init_tables(self):
        """ایجاد جداول پایگاه داده در صورت عدم وجود"""
        cursor = self.connection.cursor()
        
        # جدول مقالات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                publication_date TEXT,
                abstract TEXT,
                file_path TEXT UNIQUE,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول یادداشت‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                content TEXT NOT NULL,
                page_number INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
        ''')
        
        # جدول برنامه‌ریزی مطالعه
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                planned_date TEXT,
                completed BOOLEAN DEFAULT FALSE,
                time_spent INTEGER DEFAULT 0,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
        ''')
        
        self.connection.commit()
        logger.info("جداول پایگاه داده با موفقیت ایجاد شدند")
    
    def execute_query(self, query, parameters=()):
        """اجرای یک query و بازگشت نتیجه"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, parameters)
            self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"خطا در اجرای query: {e}")
            raise
    
    def fetch_all(self, query, parameters=()):
        """اجرای query و بازگشت تمامی نتایج"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, parameters)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"خطا در fetch_all: {e}")
            return []
    
    def fetch_one(self, query, parameters=()):
        """اجرای query و بازگشت یک نتیجه"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, parameters)
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"خطا در fetch_one: {e}")
            return None
    
    def close(self):
        """بستن اتصال به پایگاه داده"""
        self.connection.close()
        logger.info("اتصال به پایگاه داده بسته شد")