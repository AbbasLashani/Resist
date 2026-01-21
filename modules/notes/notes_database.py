# modules/notes/notes_database.py
import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger("modules.notes.database")

class NotesDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join('data', 'notes.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """ایجاد جداول پایگاه داده یادداشت‌ها"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # ایجاد جدول یادداشت‌ها با ساختار کامل
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT,
                        category TEXT,
                        tags TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        format_json TEXT,
                        is_pinned BOOLEAN DEFAULT 0,
                        word_count INTEGER DEFAULT 0
                    )
                ''')
                
                # ایجاد جدول دسته‌بندی‌ها
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        color TEXT DEFAULT '#3498db',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # ایجاد ایندکس برای بهبود عملکرد
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(is_pinned)')
                
                # درج دسته‌بندی‌های پیش‌فرض
                default_categories = [
                    ('عمومی', '#3498db'),
                    ('کار', '#e74c3c'), 
                    ('شخصی', '#2ecc71'),
                    ('تحقیق', '#9b59b6'),
                    ('ایده‌ها', '#f39c12'),
                    ('پروژه', '#1abc9c')
                ]
                
                cursor.executemany(
                    'INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)',
                    default_categories
                )
                
                conn.commit()
            logger.info(f"✅ پایگاه داده یادداشت‌ها در {self.db_path} ایجاد شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در ایجاد پایگاه داده یادداشت‌ها: {e}")
            raise
    
    def get_connection(self):
        """دریافت اتصال به پایگاه داده یادداشت‌ها"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query, params=()):
        """اجرای کوئری و مدیریت خطا"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
        except Exception as e:
            logger.error(f"خطا در اجرای کوئری: {e}")
            raise
    
    def fetch_all(self, query, params=()):
        """دریافت تمام ردیف‌ها"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌ها: {e}")
            return []
    
    def fetch_one(self, query, params=()):
        """دریافت یک ردیف"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"خطا در دریافت داده: {e}")
            return None