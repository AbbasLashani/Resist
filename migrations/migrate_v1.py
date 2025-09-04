import sqlite3
import os
from pathlib import Path

def migrate_database():
    """مهاجرت پایگاه داده به نسخه جدید"""
    db_path = Path(__file__).parent.parent / "research_db.sqlite"
    
    if not db_path.exists():
        print("پایگاه داده یافت نشد. نیازی به مهاجرت نیست.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # بررسی وجود ستون url در جدول datasheets
        cursor.execute("PRAGMA table_info(datasheets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'url' not in columns:
            print("اضافه کردن ستون url به جدول datasheets...")
            cursor.execute("ALTER TABLE datasheets ADD COLUMN url TEXT")
            conn.commit()
            print("ستون url با موفقیت اضافه شد.")
        else:
            print("ستون url از قبل وجود دارد.")
            
    except Exception as e:
        print(f"خطا در مهاجرت پایگاه داده: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()