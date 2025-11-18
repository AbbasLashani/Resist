import json
import os
from .rtl_support import reshape_text, set_widget_rtl, set_widget_ltr

class LanguageManager:
    def __init__(self, config=None):
        self.config = config
        self.current_language = self.get_initial_language()
        self.translations = self.load_translations()
        
        print(f"🌍 LanguageManager initialized:")
        print(f"   - Current language: {self.current_language}")
        print(f"   - Loaded translations: {len(self.translations.get('fa', {}))} FA, {len(self.translations.get('en', {}))} EN")
        
        # تست ترجمه‌های مهم
        self.debug_key_translations()
    
    def debug_key_translations(self):
        """تست ترجمه‌های مهم برای دیباگ"""
        test_keys = [
            "papers_module_title", "new_article", "categories", "all",
            "search_placeholder", "sort_by", "read_status", "papers"
        ]
        
        print("🔍 تست ترجمه‌های مهم:")
        for key in test_keys:
            result = self.get_text(key)
            status = "✅" if result != key else "❌"
            print(f"   {status} {key}: '{result}'")
    
    def get_initial_language(self):
        """دریافت زبان اولیه"""
        if self.config:
            try:
                if hasattr(self.config, 'get'):
                    return self.config.get("language", "fa")
                else:
                    return self.config.get("language", "fa")
            except:
                pass
        return "fa"
    
    def load_translations(self):
        """بارگذاری ترجمه‌ها از فایل JSON"""
        translations_file = self.find_translations_file()
        
        if not translations_file:
            print("❌ فایل ترجمه یافت نشد!")
            return {"fa": {}, "en": {}}
        
        print(f"📖 بارگذاری از: {translations_file}")
        
        try:
            with open(translations_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            result = {
                "fa": loaded.get("fa", {}),
                "en": loaded.get("en", {})
            }
            
            fa_count = len(result["fa"])
            en_count = len(result["en"])
            
            print(f"✅ ترجمه‌ها: {fa_count} فارسی, {en_count} انگلیسی")
            
            # اگر ترجمه‌ها کم هستند، هشدار بده
            if fa_count < 50 or en_count < 50:
                print("⚠️ هشدار: تعداد ترجمه‌ها بسیار کم است!")
            
            return result
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری ترجمه‌ها: {e}")
            return {"fa": {}, "en": {}}
    
    def find_translations_file(self):
        """پیدا کردن فایل ترجمه"""
        paths = [
            "config/translations.json",
            "./config/translations.json",
            "../config/translations.json",
            os.path.join(os.path.dirname(__file__), "..", "config", "translations.json"),
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def set_language(self, language_code):
        """تغییر زبان"""
        if language_code in ["fa", "en"]:
            old_lang = self.current_language
            self.current_language = language_code
            
            if self.config:
                try:
                    if hasattr(self.config, 'set'):
                        self.config.set("language", language_code)
                    elif hasattr(self.config, 'update'):
                        self.config.update({"language": language_code})
                    else:
                        self.config["language"] = language_code
                except:
                    pass
            
            print(f"🌍 تغییر زبان: {old_lang} → {language_code}")
            return True
        
        return False
    
    def get_text(self, key):
        """دریافت متن ترجمه شده"""
        if not key:
            return ""
        
        try:
            # جستجو در زبان فعلی
            if self.current_language in self.translations:
                translation = self.translations[self.current_language].get(key)
                if translation:
                    return translation
            
            # جستجو در زبان دیگر
            other_lang = "en" if self.current_language == "fa" else "fa"
            if other_lang in self.translations:
                translation = self.translations[other_lang].get(key)
                if translation:
                    return translation
            
            return key
            
        except Exception as e:
            print(f"❌ خطا در get_text('{key}'): {e}")
            return key
    
    def get_current_language(self):
        return self.current_language
    
    def is_rtl(self):
        return self.current_language == "fa"
    
    def reshape_text(self, text):
        return reshape_text(text)
    
    def set_widget_rtl(self, widget):
        set_widget_rtl(widget)
    
    def set_widget_ltr(self, widget):
        set_widget_ltr(widget)