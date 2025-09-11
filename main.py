import customtkinter as ctk
import sys
import os
import arabic_reshaper
from bidi.algorithm import get_display

# اضافه کردن مسیر ماژول‌ها به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__)))

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
        
        # تنظیم تم و ظاهر
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # تنظیم فونت فارسی
        self.setup_persian_font()
        
        # ایجاد برنامه اصلی
        self.app = ResearchAssistantApp(self)
        self.app.pack(fill="both", expand=True)
        
        # مرکز پنجره
        self.center_window()
        
        # ذخیره تنظیمات هنگام بسته شدن برنامه
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
    
    def on_closing(self):
        """ذخیره تنظیمات هنگام بستن برنامه"""
        try:
            # ذخیره تنظیمات فعلی
            if hasattr(self, 'app') and hasattr(self.app, 'config'):
                self.app.config.set("theme_mode", self.app.theme_mode)
                self.app.config.set("font_size", self.app.font_size)
                self.app.config.set("sidebar_width", self.app.sidebar_width)
                self.app.config.set("language", self.app.language.get_current_language())
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