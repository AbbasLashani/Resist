# research_assistant/core/app.py
import tkinter as tk
from tkinter import ttk
import json
import os

class ResearchAssistantApp:
    def __init__(self, root):
        self.root = root
        self.setup_app()
        self.load_config()
        self.setup_ui()
        
    def setup_app(self):
        """تنظیمات اولیه برنامه"""
        self.root.title("دستیار هوشمند تحقیقات")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # مسیرهای مهم
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.data_dir = os.path.join(self.base_dir, "data")
        
        # ایجاد پوشه‌های لازم
        os.makedirs(self.data_dir, exist_ok=True)
        
        # سیستم ماژول‌ها
        self.modules = {}
        self.current_module = None
        
    def load_config(self):
        """بارگذاری تنظیمات"""
        self.config = {
            "theme": "default",
            "language": "fa",
            "recent_files": [],
            "user_preferences": {}
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except:
                pass
                
    def save_config(self):
        """ذخیره تنظیمات"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
            
    def setup_ui(self):
        """ایجاد رابط کاربری اصلی"""
        # فریم اصلی
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # نوار وضعیت
        self.setup_status_bar()
        
        # نمایش صفحه خوش‌آمدگویی
        self.show_welcome_screen()
        
    def setup_status_bar(self):
        """ایجاد نوار وضعیت"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_frame, text="آماده")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.status_frame, text="دستیار هوشمند تحقیقات v0.1").pack(side=tk.RIGHT, padx=5)
        
    def show_welcome_screen(self):
        """نمایش صفحه خوش‌آمدگویی"""
        welcome_frame = ttk.Frame(self.main_frame)
        welcome_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)
        
        # عنوان
        title_label = ttk.Label(
            welcome_frame, 
            text="🌟 به دستیار هوشمند تحقیقات خوش آمدید",
            font=("Tahoma", 20, "bold")
        )
        title_label.pack(pady=20)
        
        # توضیحات
        description = """
        این نرم‌افزار به شما در مدیریت و سازماندهی تحقیقات کمک می‌کند.
        
        قابلیت‌های اصلی:
        • مدیریت مقالات و منابع تحقیقاتی
        • برنامه‌ریزی و زمان‌بندی مطالعه
        • جستجوی هوشمند در پایگاه‌های علمی
        • تحلیل و تولید گزارش‌های آماری
        • سیستم یادداشت‌گذاری و حاشیه‌نویسی
        
        برای شروع، از منوی بالا ماژول مورد نظر را انتخاب کنید.
        """
        
        desc_label = ttk.Label(
            welcome_frame, 
            text=description,
            font=("Tahoma", 12),
            justify=tk.CENTER
        )
        desc_label.pack(pady=20)
        
        # دکمه شروع
        start_button = ttk.Button(
            welcome_frame,
            text="شروع کار",
            command=self.on_start
        )
        start_button.pack(pady=10)
        
    def on_start(self):
        """وقتی کاربر دکمه شروع را می‌زند"""
        self.status_label.config(text="برنامه آماده است")
        
    def register_module(self, module_name, module_class):
        """ثبت یک ماژول جدید"""
        self.modules[module_name] = module_class
        
    def activate_module(self, module_name):
        """فعال کردن یک ماژول"""
        if module_name in self.modules and self.current_module != module_name:
            # غیرفعال کردن ماژول قبلی
            if self.current_module:
                pass  # اینجا بعداً پیاده‌سازی می‌شود
                
            # فعال کردن ماژول جدید
            self.current_module = module_name
            module_instance = self.modules[module_name](self)
            return module_instance
            
    def __del__(self):
        """تمیزکاری هنگام بسته شدن"""
        self.save_config()