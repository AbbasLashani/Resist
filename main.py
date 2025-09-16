import customtkinter as ctk
import sys
import os
import arabic_reshaper
from bidi.algorithm import get_display
import json

# اضافه کردن مسیر ماژول‌ها به sys.path
#sys.path.append(os.path.join(os.path.dirname(__file__)))
# اضافه کردن مسیر ماژول‌ها به sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "modules"))
from core.app import ResearchAssistantApp

# پیکربندی جدید برای arabic-reshaper
reshaper_config = {
    'language': 'Arabic',
    'use_unshaped_instead_of_isolated': False,
    'delete_harakat': True,
    'support_ligatures': True,
    'digits': 'arabic'
}

# ایجاد نمونه reshaper با پیکربندی
reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

def reshape_arabic_text(text):
    """تغییر شکل حروف فارسی و راست‌چین کردن متن"""
    try:
        reshaped_text = reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # تنظیمات اولیه برنامه
        self.title(reshape_arabic_text("Research Assistant - دستیار تحقیقاتی"))
        self.geometry("1400x800")
        self.minsize(1200, 700)
        
        # بارگذاری تنظیمات
        self.settings = self.load_settings()
        
        # تنظیم تم و ظاهر بر اساس تنظیمات
        ctk.set_appearance_mode(self.settings.get("theme_mode", "System"))
        ctk.set_default_color_theme("blue")
        
        # تنظیم فونت فارسی
        self.setup_persian_font()
        
        # ایجاد برنامه اصلی
        self.app = ResearchAssistantApp(self, self.settings)
        self.app.pack(fill="both", expand=True)
        
        # مرکز پنجره
        self.center_window()
        
        # ذخیره تنظیمات هنگام بسته شدن برنامه
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_settings(self):
        """بارگذاری تنظیمات از فایل"""
        settings_file = os.path.join(os.path.dirname(__file__), "config", "settings.json")
        default_settings = {
            "theme_mode": "System",
            "font_size": 14,
            "sidebar_width": 250,
            "language": "fa",
            "auto_save": True,
            "notifications": True,
            "backup_interval": 24,
            "font_family": "Vazirmatn"
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # ادغام تنظیمات پیش‌فرض با تنظیمات بارگذاری شده
                    for key in default_settings:
                        if key in loaded_settings:
                            default_settings[key] = loaded_settings[key]
        except Exception as e:
            print(f"خطا در بارگذاری تنظیمات: {e}")
        
        return default_settings
    
    def save_settings(self):
        """ذخیره تنظیمات در فایل"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), "config", "settings.json")
            config_dir = os.path.dirname(settings_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"خطا در ذخیره تنظیمات: {e}")
            return False
    
    def setup_persian_font(self):
        """تنظیم فونت فارسی"""
        try:
            # مسیر فونت را نسبت به فایل اصلی برنامه می‌سازیم
            base_dir = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(base_dir, "assets", "fonts", "Vazirmatn-Regular.ttf")
            
            if os.path.exists(font_path):
                # اضافه کردن فونت به مدیریت فونت‌های customtkinter
                ctk.FontManager.load_font(font_path)
                print("فونت فارسی با موفقیت بارگذاری شد.")
            else:
                print("فونت فارسی یافت نشد، از فونت پیش‌فرض استفاده می‌شود")
                print("مسیر جستجو شده:", font_path)
        except Exception as e:
            print(f"خطا در تنظیمات فونت: {e}")
    
    def center_window(self):
        """مرکز کردن پنجره در صفحه"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def apply_settings(self, new_settings):
        """اعمال تنظیمات جدید"""
        self.settings.update(new_settings)
        
        # اعمال تغییرات تم
        ctk.set_appearance_mode(self.settings.get("theme_mode", "System"))
        
        # ذخیره تنظیمات
        self.save_settings()
        
        # به روزرسانی UI برنامه
        if hasattr(self, 'app'):
            self.app.update_ui_with_settings(self.settings)
    
    def on_closing(self):
        """ذخیره تنظیمات هنگام بستن برنامه"""
        try:
            # ذخیره تنظیمات فعلی
            self.save_settings()
            print("تنظیمات ذخیره شدند.")
        except Exception as e:
            print(f"خطا در ذخیره تنظیمات: {e}")
        finally:
            self.quit()

def run_app():
    """اجرای برنامه در thread اصلی"""
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    # اجرای برنامه
    run_app()