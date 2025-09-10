import json
import os

class LanguageManager:
    def __init__(self, config):
        self.config = config
        self.current_language = self.config.get("language", "fa")
        self.translations = self.load_translations()
    
    def load_translations(self):
        """بارگذاری ترجمه‌ها از فایل‌های JSON"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            lang_dir = os.path.join(base_dir, "assets", "lang")
            
            # ایجاد پوشه اگر وجود ندارد
            os.makedirs(lang_dir, exist_ok=True)
            
            # مسیر فایل زبان
            lang_file = os.path.join(lang_dir, f"{self.current_language}.json")
            
            # اگر فایل زبان وجود ندارد، ایجادش کن
            if not os.path.exists(lang_file):
                self.create_language_file(lang_file)
            
            # بارگذاری ترجمه‌ها از فایل
            with open(lang_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"خطا در بارگذاری ترجمه‌ها: {e}")
            return self.get_default_translations()
    
    def create_language_file(self, file_path):
        """ایجاد فایل زبان اگر وجود ندارد"""
        try:
            # تعیین ترجمه‌های پیش‌فرض بر اساس زبان
            if "fa" in file_path:
                translations = self.get_default_translations("fa")
            else:
                translations = self.get_default_translations("en")
            
            # ذخیره ترجمه‌ها در فایل
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=4)
                
            print(f"فایل زبان ایجاد شد: {file_path}")
            
        except Exception as e:
            print(f"خطا در ایجاد فایل زبان: {e}")
    
    def get_default_translations(self, language=None):
        """دریافت ترجمه‌های پیش‌فرض"""
        if language is None:
            language = self.current_language
            
        if language == "fa":
            return {
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
                "english": "انگلیسی"
            }
        else:
            return {
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
                "changes_saved": "Settings saved successfully",
                "module_development": "{} module is under development",
                "notes_development": "Notes module will be added soon",
                "persian": "Persian",
                "english": "English"
            }
    
    def set_language(self, language_code):
        """تغییر زبان"""
        self.current_language = language_code
        self.translations = self.load_translations()
        return True
    
    def get_text(self, key, default=None):
        """دریافت متن ترجمه شده"""
        return self.translations.get(key, default) if default is None else self.translations.get(key, default)
    
    def get_current_language(self):
        """دریافت زبان فعلی"""
        return self.current_language
    
    def is_rtl(self):
        """آیا زبان راست به چپ است؟"""
        return self.current_language == "fa"