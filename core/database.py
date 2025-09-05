import sqlite3
import os
import logging
from typing import List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config=None):
        # اگر config ارائه نشده، از مقادیر پیش‌فرض استفاده کنید
        if config is None:
            config = {
                'database': {
                    'path': 'data/research_assistant.db',
                    'backup_enabled': True,
                    'backup_path': 'backups/'
                }
            }
        
        self.config = config
        db_config = config.get('database', {})
        self.db_path = db_config.get('path', 'data/research_assistant.db')
        
        # اطمینان از وجود پوشه داده
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """اتصال به پایگاه داده SQLite"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"اتصال به پایگاه داده در {self.db_path} برقرار شد")
        except sqlite3.Error as e:
            logger.error(f"خطا در اتصال به پایگاه داده: {e}")
            raise
    
    def create_tables(self):
        """ایجاد جداول مورد نیاز در پایگاه داده"""
        tables = [
            # جدول مقالات
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                publication_date TEXT,
                journal TEXT,
                status TEXT DEFAULT 'planned',
                rating INTEGER DEFAULT 0,
                doi TEXT,
                url TEXT,
                file_path TEXT,
                notes TEXT,
                project_id INTEGER,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # جدول یادداشت‌ها
            """
            CREATE TABLE IF NOT EXISTS research_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                content TEXT,
                tags TEXT,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
            """,
            # جدول برنامه‌ریزی مطالعه
            """
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,
                scheduled_date DATETIME,
                duration INTEGER,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers (id)
            )
            """,
            # جدول پروژه‌های تحقیقاتی
            """
            CREATE TABLE IF NOT EXISTS research_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                target_date DATETIME
            )
            """
        ]
        
        try:
            cursor = self.connection.cursor()
            for table in tables:
                cursor.execute(table)
            self.connection.commit()
            logger.info("جداول پایگاه داده با موفقیت ایجاد شدند")
        except sqlite3.Error as e:
            logger.error(f"خطا در ایجاد جداول: {e}")
            raise
    
    def execute_query(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Cursor]:
        """اجرای یک کوئری و بازگرداندن cursor"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"خطا در اجرای کوئری: {e}")
            return None
    
    def fetch_all(self, query: str, params: Tuple = ()) -> List[Any]:
        """اجرای کوئری و بازگرداندن تمام نتایج"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"خطا در دریافت داده: {e}")
            return []
    
    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """اجرای کوئری و بازگرداندن یک نتیجه"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"خطا در دریافت داده: {e}")
            return None
    
    def close(self):
        """بستن اتصال به پایگاه داده"""
        if self.connection:
            self.connection.close()
            logger.info("اتصال به پایگاه داده بسته شد")
    
    def __del__(self):
        """دمارک برای بستن اتصال هنگام از بین رفتن شیء"""
        self.close()