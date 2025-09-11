import sqlite3
import os

class Database:
    def __init__(self, config):
        self.config = config
        self.db_file = "research_assistant.db"
        self.init_database()
    
    def init_database(self):
        """ایجاد جداول پایگاه داده در صورت عدم وجود"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # ایجاد جدول مقالات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    authors TEXT,
                    journal TEXT,
                    year INTEGER,
                    abstract TEXT,
                    tags TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ایجاد جدول یادداشت‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ایجاد جدول برنامه‌ریزی
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS planner (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date DATE,
                    priority INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"خطا در ایجاد پایگاه داده: {e}")
    
    def get_connection(self):
        """دریافت اتصال به پایگاه داده"""
        return sqlite3.connect(self.db_file)