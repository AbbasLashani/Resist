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
            
            # ایجاد جدول تسک‌ها (جدید)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    priority TEXT DEFAULT 'medium',
                    completed BOOLEAN DEFAULT FALSE,
                    category TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ایجاد جدول اهداف (جدید)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    target_date TEXT,
                    progress INTEGER DEFAULT 0,
                    priority TEXT DEFAULT 'medium',
                    category TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ایجاد جدول پلن‌ها (جدید)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    color TEXT DEFAULT '#2196F3',
                    completed BOOLEAN DEFAULT FALSE,
                    progress INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ تمام جداول دیتابیس ایجاد شدند")
            
        except Exception as e:
            print(f"❌ خطا در ایجاد پایگاه داده: {e}")
    
    def get_connection(self):
        """دریافت اتصال به پایگاه داده"""
        return sqlite3.connect(self.db_file)