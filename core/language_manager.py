import json
import os

class LanguageManager:
    def __init__(self, config=None):
        self.config = config
        self.current_language = self.get_initial_language()
        self.translations = self.load_translations()
    
    def get_initial_language(self):
        """دریافت زبان اولیه از config یا استفاده از پیش‌فرض"""
        if self.config:
            return self.config.get("language", "fa")
        return "fa"
    
    def load_translations(self):
        """بارگذاری ترجمه‌ها از فایل"""
        translations_file = os.path.join(os.path.dirname(__file__), "..", "config", "translations.json")
        
        default_translations = {
            "fa": {
                "app_title": "دستیار تحقیقاتی",
                "status_ready": "آماده",
                "db_status": "پایگاه داده: فعال",
                "dashboard": "داشبورد",
                "papers": "مقالات",
                "planner": "برنامه‌ریزی",
                "notes": "یادداشت‌ها",
                "research": "تحقیق",
                "writer": "نوشتن",
                "settings": "تنظیمات",
                "settings_title": "تنظیمات برنامه",
                "theme": "تم",
                "font_size": "اندازه فونت",
                "sidebar_width": "عرض سایدبار",
                "language": "زبان",
                "save_changes": "ذخیره تغییرات",
                "changes_saved": "تنظیمات ذخیره شد",
                "module_development": "ماژول {} در حال توسعه است",
                "notes_development": "ماژول یادداشت‌ها به زودی اضافه خواهد شد",
                "persian": "فارسی",
                "english": "انگلیسی",
                "auto_save": "ذخیره خودکار",
                "notifications": "اعلان‌ها",
                "backup_interval": "فاصله پشتیبان‌گیری",
                "success": "موفقیت"
            },
            "en": {
                "app_title": "Research Assistant",
                "status_ready": "Ready",
                "db_status": "Database: Active",
                "dashboard": "Dashboard",
                "papers": "Papers",
                "planner": "Planner",
                "notes": "Notes",
                "research": "Research",
                "writer": "Writer",
                "settings": "Settings",
                "settings_title": "Application Settings",
                "theme": "Theme",
                "font_size": "Font Size",
                "sidebar_width": "Sidebar Width",
                "language": "Language",
                "save_changes": "Save Changes",
                "changes_saved": "Settings saved",
                "module_development": "Module {} is under development",
                "notes_development": "Notes module will be added soon",
                "persian": "Persian",
                "english": "English",
                "auto_save": "Auto Save",
                "notifications": "Notifications",
                "backup_interval": "Backup Interval",
                "success": "Success"
            }
        }
        
        try:
            if os.path.exists(translations_file):
                with open(translations_file, 'r', encoding='utf-8') as f:
                    loaded_translations = json.load(f)
                    # ادغام ترجمه‌های پیش‌فرض با ترجمه‌های بارگذاری شده
                    for lang in ["fa", "en"]:
                        if lang in loaded_translations:
                            default_translations[lang].update(loaded_translations[lang])
        except Exception as e:
            print(f"خطا در بارگذاری ترجمه‌ها: {e}")
        
        return default_translations
    
    def set_language(self, language_code):
        """تغییر زبان برنامه"""
        if language_code in self.translations:
            self.current_language = language_code
            # ذخیره در config اگر وجود دارد
            if self.config:
                self.config.set("language", language_code)
            return True
        return False
    
    def get_text(self, key):
        """دریافت متن ترجمه شده"""
        return self.translations.get(self.current_language, {}).get(key, key)
    
    def get_current_language(self):
        """دریافت زبان فعلی"""
        return self.current_language
    
    def is_rtl(self):
        """بررسی آیا زبان فعلی راست به چپ است"""
        return self.current_language == "fa"