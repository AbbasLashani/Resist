import customtkinter as ctk
import sys
import os
import arabic_reshaper
from bidi.algorithm import get_display

# اضافه کردن مسیر ماژول‌ها به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.app import ResearchAssistantApp

# تنظیمات arabic_reshaper
arabic_reshaper.config_for_arabic_reshaper(
    language='farsi',
    use_unshaped_instead_of_isolated=False,
    delete_harakat=True,
    support_ligatures=True,
    digits='arabic'
)

def reshape_arabic_text(text):
    """تغییر شکل حروف فارسی و راست‌چین کردن متن"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
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
        
    def setup_persian_font(self):
        """تنظیم فونت فارسی"""
        try:
            # بارگذاری فونت فارسی
            font_path = "assets/fonts/Vazirmatn-Regular.ttf"
            if os.path.exists(font_path):
                ctk.FontManager.load_font(font_path)
                # تنظیم فونت پیش‌فرض برای تمام ویجت‌ها
                ctk.CTkFont.default_family = "Vazirmatn"
            else:
                print("فونت فارسی یافت نشد، از فونت پیش‌فرض استفاده می‌شود")
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

def run_app():
    """اجرای برنامه در thread اصلی"""
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    # اجرای برنامه
    run_app()