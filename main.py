import customtkinter as ctk
import sys
import os
import json
from typing import Dict, Any

# اضافه کردن مسیر ماژول‌ها به sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.app import ResearchAssistantApp

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # تنظیمات اولیه برنامه
        self._setup_basic_config()
        
        # بارگذاری تنظیمات
        self.settings = self._load_settings()
        
        # اعمال تنظیمات ظاهری
        self._apply_appearance_settings()
        
        # راه‌اندازی فونت فارسی
        self._setup_persian_font()
        
        # ایجاد برنامه اصلی
        self._create_main_app()
        
        # تنظیمات پنجره
        self._setup_window()
        
        # مدیریت رویداد بسته شدن
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_basic_config(self):
        """تنظیمات پایه برنامه"""
        self.title("Research Assistant - دستیار تحقیقاتی")
        self.geometry("1400x800")
        self.minsize(1200, 700)

    def _load_settings(self) -> Dict[str, Any]:
        """بارگذاری تنظیمات از فایل"""
        settings_file = os.path.join(
            os.path.dirname(__file__), 
            "config", 
            "settings.json"
        )
        
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
                    # به روزرسانی تنظیمات پیش‌فرض با مقادیر بارگذاری شده
                    default_settings.update({
                        k: v for k, v in loaded_settings.items() 
                        if k in default_settings
                    })
        except Exception as e:
            print(f"خطا در بارگذاری تنظیمات: {e}")
        
        return default_settings

    def _apply_appearance_settings(self):
        """اعمال تنظیمات ظاهری"""
        ctk.set_appearance_mode(self.settings.get("theme_mode", "System"))
        ctk.set_default_color_theme("blue")

    def _setup_persian_font(self):
        """تنظیم و بارگذاری فونت فارسی"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            fonts_dir = os.path.join(base_dir, "assets", "fonts")
            
            # اطمینان از وجود پوشه فونت
            os.makedirs(fonts_dir, exist_ok=True)
            
            # لیست فونت‌های مورد نیاز
            required_fonts = {
                "Vazirmatn-Regular.ttf": "https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/Vazirmatn-Regular.ttf",
                "Vazirmatn-Bold.ttf": "https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/Vazirmatn-Bold.ttf"
            }
            
            # بارگذاری فونت‌های موجود
            for font_file in required_fonts:
                font_path = os.path.join(fonts_dir, font_file)
                if os.path.exists(font_path):
                    ctk.FontManager.load_font(font_path)
                    print(f"فونت {font_file} با موفقیت بارگذاری شد")
                else:
                    print(f"⚠️ فونت {font_file} یافت نشد")
                    print(f"   لطفاً از این آدرس دانلود کنید: {required_fonts[font_file]}")
                    
        except Exception as e:
            print(f"خطا در راه‌اندازی فونت: {e}")

    def _create_main_app(self):
        """ایجاد نمونه برنامه اصلی"""
        self.app = ResearchAssistantApp(self, self.settings)
        self.app.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_window(self):
        """تنظیمات نهایی پنجره"""
        self._center_window()
        self._set_window_icon()

    def _center_window(self):
        """مرکز کردن پنجره در صفحه"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _set_window_icon(self):
        """تنظیم آیکون پنجره"""
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__), 
                "assets", 
                "icons", 
                "app_icon.ico"
            )
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"خطا در تنظیم آیکون: {e}")

    def apply_settings(self, new_settings: Dict[str, Any]):
        """اعمال تنظیمات جدید"""
        self.settings.update(new_settings)
        
        # اعمال تغییرات تم
        ctk.set_appearance_mode(self.settings.get("theme_mode", "System"))
        
        # ذخیره تنظیمات
        self._save_settings()
        
        # به روزرسانی رابط کاربری
        if hasattr(self, 'app'):
            self.app.update_ui_with_settings(self.settings)

    def _save_settings(self) -> bool:
        """ذخیره تنظیمات در فایل"""
        try:
            settings_file = os.path.join(
                os.path.dirname(__file__), 
                "config", 
                "settings.json"
            )
            
            # ایجاد پوشه config اگر وجود ندارد
            config_dir = os.path.dirname(settings_file)
            os.makedirs(config_dir, exist_ok=True)
            
            # ذخیره تنظیمات
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.settings, 
                    f, 
                    ensure_ascii=False, 
                    indent=4
                )
            return True
            
        except Exception as e:
            print(f"خطا در ذخیره تنظیمات: {e}")
            return False

    def _on_closing(self):
        """مدیریت رویداد بسته شدن برنامه"""
        try:
            # ذخیره نهایی تنظیمات
            if self._save_settings():
                print("✅ تنظیمات با موفقیت ذخیره شد")
            else:
                print("❌ خطا در ذخیره تنظیمات")
                
        except Exception as e:
            print(f"خطا در عملیات بسته شدن: {e}")
        finally:
            self.quit()

    def show_error(self, title: str, message: str):
        """نمایش پیغام خطا"""
        import tkinter.messagebox as mb
        mb.showerror(title, message)

    def show_info(self, title: str, message: str):
        """نمایش پیغام اطلاعات"""
        import tkinter.messagebox as mb
        mb.showinfo(title, message)

    def show_warning(self, title: str, message: str):
        """نمایش پیغام هشدار"""
        import tkinter.messagebox as mb
        mb.showwarning(title, message)


def run_app():
    """تابع اصلی اجرای برنامه"""
    try:
        # ایجاد و اجرای برنامه
        app = MainApp()
        app.mainloop()
        
    except Exception as e:
        print(f"خطای غیرمنتظره در اجرای برنامه: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # اجرای برنامه
    run_app()