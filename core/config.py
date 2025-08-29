# research_assistant/core/config.py
import json
import os
from pathlib import Path

class Config:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config.json"
        self.settings = self.load_config()
        self.language = self.settings.get("language", "fa")
    
    def load_config(self):
        """بارگذاری تنظیمات از فایل JSON"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # تنظیمات پیش‌فرض
            default_config = {
                "theme": "default",
                "language": "fa",
                "recent_files": [],
                "user_preferences": {},
                "database_path": "research_db.sqlite"
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config_data=None):
        """ذخیره تنظیمات در فایل JSON"""
        if config_data is None:
            config_data = self.settings
            
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
    
    def get(self, key, default=None):
        """دریافت مقدار یک تنظیم"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """تعیین مقدار یک تنظیم"""
        self.settings[key] = value
        self.save_config()
    
    def add_recent_file(self, file_path):
        """افزودن فایل به لیست اخیر"""
        if file_path in self.settings["recent_files"]:
            self.settings["recent_files"].remove(file_path)
        self.settings["recent_files"].insert(0, file_path)
        # حفظ فقط ۱۰ مورد اخیر
        self.settings["recent_files"] = self.settings["recent_files"][:10]
        self.save_config()
    
    def get_text(self, key, default=None):
        """دریافت متن ترجمه شده (برای پشتیبانی از چندزبانه در آینده)"""
        # در این نسخه اولیه، مستقیماً مقدار را برمی‌گردانیم
        # در آینده می‌توانیم سیستم ترجمه اضافه کنیم
        return default