import customtkinter as ctk
import json
import os

class FontManager:
    def __init__(self, config=None):
        self.config = config
        self.font_family = self.get_font_family()
        self.font_size = self.get_font_size()
        
        # فونت‌های پایه
        self.fonts = {}
        self.update_fonts()
        
        print(f"🔤 FontManager initialized: {self.font_family}, size: {self.font_size}")
    
    def get_font_family(self):
        """دریافت خانواده فونت از config"""
        if self.config:
            try:
                if hasattr(self.config, 'get'):
                    return self.config.get("font_family", "Tahoma")
                else:
                    return self.config.get("font_family", "Tahoma")
            except:
                pass
        return "Tahoma"
    
    def get_font_size(self):
        """دریافت سایز فونت از config"""
        if self.config:
            try:
                if hasattr(self.config, 'get'):
                    return int(self.config.get("font_size", 14))
                else:
                    return int(self.config.get("font_size", 14))
            except:
                pass
        return 14
    
    def update_fonts(self):
        """بروزرسانی تمام فونت‌ها با تنظیمات فعلی"""
        try:
            # فونت‌های اصلی با سایزهای مختلف
            self.fonts = {
                "title": ctk.CTkFont(family=self.font_family, size=self.font_size + 6, weight="bold"),
                "heading": ctk.CTkFont(family=self.font_family, size=self.font_size + 2, weight="bold"),
                "subheading": ctk.CTkFont(family=self.font_family, size=self.font_size, weight="bold"),
                "normal": ctk.CTkFont(family=self.font_family, size=self.font_size),
                "small": ctk.CTkFont(family=self.font_family, size=self.font_size - 2),
                "tiny": ctk.CTkFont(family=self.font_family, size=self.font_size - 4)
            }
            print(f"✅ فونت‌ها بروزرسانی شدند: {self.font_family} - سایز: {self.font_size}")
        except Exception as e:
            print(f"❌ خطا در بروزرسانی فونت‌ها: {e}")
            # فونت‌های fallback
            self.fonts = {
                "title": ctk.CTkFont(size=20, weight="bold"),
                "heading": ctk.CTkFont(size=16, weight="bold"),
                "subheading": ctk.CTkFont(size=14, weight="bold"),
                "normal": ctk.CTkFont(size=14),
                "small": ctk.CTkFont(size=12),
                "tiny": ctk.CTkFont(size=10)
            }
    
    def get_font(self, size=None, weight="normal"):
        """دریافت فونت با سایز و وزن مشخص"""
        if size is None:
            size = self.font_size
            
        try:
            if weight == "bold":
                if size >= 18:
                    return self.fonts["title"]
                elif size >= 16:
                    return self.fonts["heading"]
                else:
                    return self.fonts["subheading"]
            else:
                if size <= 10:
                    return self.fonts["tiny"]
                elif size <= 12:
                    return self.fonts["small"]
                else:
                    return self.fonts["normal"]
        except:
            return ctk.CTkFont(size=size, weight=weight)
    
    def set_font_size(self, size):
        """تنظیم سایز فونت جدید"""
        try:
            self.font_size = int(size)
            self.update_fonts()
            print(f"🔤 سایز فونت تغییر کرد به: {self.font_size}")
            return True
        except Exception as e:
            print(f"❌ خطا در تنظیم سایز فونت: {e}")
            return False
    
    def set_font_family(self, family):
        """تنظیم خانواده فونت جدید"""
        try:
            self.font_family = family
            self.update_fonts()
            print(f"🔤 خانواده فونت تغییر کرد به: {self.font_family}")
            return True
        except Exception as e:
            print(f"❌ خطا در تنظیم خانواده فونت: {e}")
            return False
    
    def get_current_font_info(self):
        """دریافت اطلاعات فونت فعلی"""
        return {
            "family": self.font_family,
            "size": self.font_size,
            "fonts": list(self.fonts.keys())
        }