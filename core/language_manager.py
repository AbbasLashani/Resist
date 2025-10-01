import json
import os
from .rtl_support import reshape_text, set_widget_rtl, set_widget_ltr

class LanguageManager:
    def __init__(self, config=None):
        self.config = config
        self.current_language = self.get_initial_language()
        self.translations = self.load_translations()
        
        # دیباگ: نمایش ترجمه‌های موجود
        print(f"📚 ترجمه‌های بارگذاری شده:")
        for lang, texts in self.translations.items():
            print(f"   - {lang}: {len(texts)} متن")
    
    def get_initial_language(self):
        """دریافت زبان اولیه از config یا استفاده از پیش‌فرض"""
        if self.config:
            try:
                # استفاده از متد get اگر موجود باشد
                if hasattr(self.config, 'get'):
                    lang = self.config.get("language", "fa")
                else:
                    # اگر config یک دیکشنری ساده است
                    lang = self.config.get("language", "fa")
                print(f"   - زبان اولیه از config: {lang}")
                return lang
            except Exception as e:
                print(f"⚠️ خطا در دریافت زبان از config: {e}")
        return "fa"
    
    def load_translations(self):
        """بارگذاری ترجمه‌ها از فایل"""
        # مسیر فایل ترجمه
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        translations_file = os.path.join(base_dir, "config", "translations.json")
        
        print(f"   - جستجوی فایل ترجمه: {translations_file}")
        
        # ترجمه‌های پیش‌فرض کامل
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
                "font_family": "نوع فونت",
                "font_size": "اندازه فونت",
                "sidebar_width": "عرض سایدبار",
                "language": "زبان",
                "save_changes": "ذخیره تغییرات",
                "changes_saved": "تنظیمات ذخیره شد",
                "notes_development": "ماژول یادداشت‌ها در حال توسعه است",
                "module_development": "ماژول {} در حال توسعه است",
                "back_to_dashboard": "بازگشت به داشبورد",
                "persian": "فارسی",
                "english": "انگلیسی",
                "auto_save": "ذخیره خودکار",
                "notifications": "اعلان‌ها",
                "backup_interval": "فاصله پشتیبان‌گیری",
                "success": "موفقیت",
                "on": "روشن",
                "off": "خاموش",
                "light": "روشن",
                "dark": "تاریک",
                "system": "سیستم"
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
                "font_family": "Font Family",
                "font_size": "Font Size",
                "sidebar_width": "Sidebar Width",
                "language": "Language",
                "save_changes": "Save Changes",
                "changes_saved": "Settings saved",
                "notes_development": "Notes module is under development",
                "module_development": "{} module is under development",
                "back_to_dashboard": "Back to Dashboard",
                "persian": "Persian",
                "english": "English",
                "auto_save": "Auto Save",
                "notifications": "Notifications",
                "backup_interval": "Backup Interval",
                "success": "Success",
                "on": "On",
                "off": "Off",
                "light": "Light",
                "dark": "Dark",
                "system": "System"
            }
        }
        
        try:
            if os.path.exists(translations_file):
                print("   - فایل ترجمه یافت شد، در حال بارگذاری...")
                with open(translations_file, 'r', encoding='utf-8') as f:
                    loaded_translations = json.load(f)
                    print("   - فایل ترجمه با موفقیت بارگذاری شد")
                    
                    # ادغام ترجمه‌های پیش‌فرض با ترجمه‌های بارگذاری شده
                    for lang in ["fa", "en"]:
                        if lang in loaded_translations:
                            default_translations[lang].update(loaded_translations[lang])
                            print(f"   - ترجمه‌های {lang} به روز شد")
            else:
                print("   - فایل ترجمه یافت نشد، استفاده از ترجمه‌های پیش‌فرض")
                
        except Exception as e:
            print(f"❌ خطا در بارگذاری ترجمه‌ها: {e}")
        
        return default_translations
    
    def set_language(self, language_code):
        """تغییر زبان برنامه"""
        if language_code in self.translations:
            old_lang = self.current_language
            self.current_language = language_code
            
            # ذخیره در config اگر وجود دارد
            if self.config:
                try:
                    # استفاده از متد set اگر موجود باشد
                    if hasattr(self.config, 'set'):
                        self.config.set("language", language_code)
                    elif hasattr(self.config, 'update'):
                        self.config.update({"language": language_code})
                    else:
                        # اگر config یک دیکشنری ساده است
                        self.config["language"] = language_code
                    print(f"✅ زبان در config ذخیره شد: {language_code}")
                except Exception as e:
                    print(f"⚠️ خطا در ذخیره زبان در config: {e}")
            
            print(f"🌍 تغییر زبان از {old_lang} به {language_code}")
            return True
        
        print(f"⚠️ زبان {language_code} پشتیبانی نمی‌شود")
        return False
    
    def get_text(self, key):
        """دریافت متن ترجمه شده"""
        translation = self.translations.get(self.current_language, {}).get(key, key)
        return translation
    
    def get_current_language(self):
        """دریافت زبان فعلی"""
        return self.current_language
    
    def is_rtl(self):
        """بررسی آیا زبان فعلی راست به چپ است"""
        return self.current_language == "fa"
    
    def reshape_text(self, text):
        """تغییر شکل متن برای نمایش در زبان RTL"""
        return reshape_text(text)
    
    def set_widget_rtl(self, widget):
        """تنظیم ویجت برای راست به چپ"""
        set_widget_rtl(widget)
    
    def set_widget_ltr(self, widget):
        """تنظیم ویجت برای چپ به راست"""
        set_widget_ltr(widget)