import customtkinter as ctk
import sys
import os

# اضافه کردن مسیر ماژول‌ها به sys.path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.app import ResearchAssistantApp

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # تنظیمات اولیه برنامه
        self.title("Research Assistant - دستیار تحقیقاتی")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        
        # تنظیم تم و ظاهر
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # تنظیم پشتیبانی RTL و فونت فارسی
        self.setup_rtl_support()
        
        # ایجاد برنامه اصلی
        self.app = ResearchAssistantApp(self)
        self.app.pack(fill="both", expand=True)
        
        # مرکز پنجره
        self.center_window()
        
    def setup_rtl_support(self):
        """تنظیم پشتیبانی از راست به چپ و فونت فارسی"""
        try:
            # بارگذاری فونت فارسی
            font_path = "assets/fonts/Vazirmatn-Regular.ttf"
            if os.path.exists(font_path):
                ctk.FontManager.load_font(font_path)
                ctk.CTkFont.default_family = "Vazirmatn"
            else:
                print("فونت فارسی یافت نشد، از فونت پیش‌فرض استفاده می‌شود")
                ctk.CTkFont.default_family = "Tahoma"
                
        except Exception as e:
            print(f"خطا در تنظیمات RTL: {e}")
            ctk.CTkFont.default_family = "Tahoma"
    
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