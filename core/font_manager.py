import customtkinter as ctk
import os

class FontManager:
    def __init__(self, config):
        self.config = config
        self.font_families = self.load_font_families()
        self.current_font = self.config.get("font_family", "Vazirmatn")
        self.font_size = self.config.get("font_size", 14)
        
    def load_font_families(self):
        """بارگذاری فونت‌های موجود"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fonts_dir = os.path.join(base_dir, "assets", "fonts")
        
        font_families = {
            "Vazirmatn": os.path.join(fonts_dir, "Vazirmatn-Regular.ttf"),
            "B Nazanin": os.path.join(fonts_dir, "B-Nazanin.ttf"),
            "Iran Sans": os.path.join(fonts_dir, "IRANSans.ttf"),
            "Default": None  # فونت پیش‌فرض سیستم
        }
        
        # بررسی وجود فایل‌های فونت
        for font_name, font_path in font_families.items():
            if font_path and not os.path.exists(font_path):
                print(f"هشدار: فونت {font_name} در مسیر {font_path} یافت نشد.")
        
        return font_families
    
    def get_font(self, size=None, weight="normal"):
        """دریافت فونت با اندازه و وزن مشخص"""
        if size is None:
            size = self.font_size
        
        # اگر فونت سفارشی وجود دارد، از آن استفاده کن
        if self.current_font in self.font_families and self.font_families[self.current_font]:
            try:
                # بارگذاری فونت اگر قبلاً بارگذاری نشده
                if self.font_families[self.current_font]:
                    ctk.FontManager.load_font(self.font_families[self.current_font])
                
                # ایجاد فونت با مشخصات داده شده
                font_family = self.current_font
                if weight == "bold":
                    font_family += " Bold"
                
                return ctk.CTkFont(family=font_family, size=size)
            except Exception as e:
                print(f"خطا در بارگذاری فونت: {e}")
                return ctk.CTkFont(size=size)
        
        # استفاده از فونت پیش‌فرض
        return ctk.CTkFont(size=size)
    
    def set_font_family(self, font_family):
        """تغییر خانواده فونت"""
        if font_family in self.font_families:
            self.current_font = font_family
            self.config.set("font_family", font_family)
            return True
        return False
    
    def set_font_size(self, size):
        """تغییر اندازه فونت"""
        self.font_size = size
        self.config.set("font_size", size)
    
    def get_available_fonts(self):
        """دریافت لیست فونت‌های موجود"""
        return list(self.font_families.keys())