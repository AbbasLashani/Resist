# research_assistant/core/config.py
import json
import os
from pathlib import Path

class Config:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config.json"
        self.locales_path = Path(__file__).parent.parent / "locales"
        self.settings = self.load_config()
        self.current_language = self.settings.get("language", "fa")
        self.translations = self.load_translations()
    
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
    
    def load_translations(self):
        """بارگذاری ترجمه‌ها از فایل‌های زبان"""
        translation_file = self.locales_path / f"{self.current_language}.json"
        if translation_file.exists():
            with open(translation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Fallback به انگلیسی اگر فایل زبان وجود نداشت
            en_file = self.locales_path / "en.json"
            if en_file.exists():
                with open(en_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
    
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
        
        # اگر زبان تغییر کرد، ترجمه‌ها را مجدداً بارگذاری کن
        if key == "language" and value != self.current_language:
            self.current_language = value
            self.translations = self.load_translations()
    
    def add_recent_file(self, file_path):
        """افزودن فایل به لیست اخیر"""
        if file_path in self.settings["recent_files"]:
            self.settings["recent_files"].remove(file_path)
        self.settings["recent_files"].insert(0, file_path)
        # حفظ فقط ۱۰ مورد اخیر
        self.settings["recent_files"] = self.settings["recent_files"][:10]
        self.save_config()
    
    def t(self, key, default=None):
        """دریافت متن ترجمه شده"""
        return self.translations.get(key, default or key)
    
    def set_language(self, language):
        """تغییر زبان برنامه"""
        if language in ["fa", "en"]:
            self.set("language", language)
            return True
        return False