# research_assistant/modules/dashboard/dashboard_module.py
import tkinter as tk
from tkinter import ttk
import logging
from tkinter import messagebox

logger = logging.getLogger(__name__)

class DashboardModule(ttk.Frame):
    def __init__(self, parent, app, config):
        super().__init__(parent)
        self.app = app
        self.config = config
        logger.info("سازنده DashboardModule فراخوانی شد")
        
        # تنظیم layout برای پر کردن فضای disponible
        self.pack(fill=tk.BOTH, expand=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """ایجاد رابط کاربری داشبورد"""
        logger.info("تنظیم رابط کاربری داشبورد")
        
        # عنوان اصلی
        title_label = ttk.Label(
            self,
            text="📊 " + self.config.t("dashboard"),
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # فریم برای کارت‌های اطلاعاتی
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill=tk.X, pady=10, padx=20)
        
        # ایجاد کارت‌های اطلاعاتی
        self.create_info_cards(cards_frame)
        
        # فریم برای آمار سریع
        stats_frame = ttk.LabelFrame(
            self, 
            text=" " + self.config.t("quick_stats") + " ",
            padding=10
        )
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=20)
        
        # ایجاد آمار سریع
        self.create_quick_stats(stats_frame)
        
        # دکمه بروزرسانی
        refresh_btn = ttk.Button(
            self, 
            text=self.config.t("refresh_stats"), 
            command=self.refresh_data
        )
        refresh_btn.pack(pady=10)
        
        logger.info("رابط کاربری داشبورد تنظیم شد")
        
    def create_info_cards(self, parent):
        """ایجاد کارت‌های اطلاعاتی"""
        # داده‌های کارت‌ها
        cards_data = [
            {"title": self.config.t("papers"), "value": "12", "icon": "📄", "color": "#3498db"},
            {"title": self.config.t("study_time"), "value": "8.5 ساعت", "icon": "⏱️", "color": "#2ecc71"},
            {"title": self.config.t("notes"), "value": "23", "icon": "📝", "color": "#e74c3c"},
            {"title": self.config.t("projects"), "value": "3", "icon": "📁", "color": "#f39c12"}
        ]
        
        for i, card in enumerate(cards_data):
            card_frame = ttk.Frame(
                parent, 
                relief=tk.RAISED, 
                borderwidth=1,
                padding=10
            )
            
            if i < 2:
                card_frame.grid(row=0, column=i, padx=5, pady=5, sticky='nsew')
            else:
                card_frame.grid(row=1, column=i-2, padx=5, pady=5, sticky='nsew')
                
            parent.columnconfigure(i % 2, weight=1)
            parent.rowconfigure(i // 2, weight=1)
            
            # آیکون و عنوان
            icon_title_frame = ttk.Frame(card_frame)
            icon_title_frame.pack(fill=tk.X)
            
            # آیکون
            icon_label = ttk.Label(icon_title_frame, text=card["icon"], font=("Tahoma", 16))
            icon_label.pack(side=tk.RIGHT, padx=(5, 0))
            
            # عنوان
            title_label = ttk.Label(
                icon_title_frame, 
                text=card["title"], 
                font=("Tahoma", 10, "bold"),
                anchor='e'
            )
            title_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            # خط جداکننده
            separator = ttk.Separator(card_frame, orient=tk.HORIZONTAL)
            separator.pack(fill=tk.X, pady=5)
            
            # مقدار
            value_label = ttk.Label(
                card_frame, 
                text=card["value"], 
                font=("Tahoma", 18, "bold"),
                anchor='center'
            )
            value_label.pack(fill=tk.BOTH, expand=True)
        
    def create_quick_stats(self, parent):
        """ایجاد بخش آمار سریع"""
        # آمار نمونه
        stats_data = [
            (self.config.t("read_papers"), "8"),
            (self.config.t("reading_papers"), "4"),
            (self.config.t("planned_papers"), "5"),
            (self.config.t("avg_study_time"), "45 دقیقه")
        ]
        
        for stat_name, stat_value in stats_data:
            stat_frame = ttk.Frame(parent)
            stat_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(
                stat_frame, 
                text=stat_name, 
                width=25,
                anchor='e'
            ).pack(side=tk.RIGHT, padx=(10, 0))
            
            value_label = ttk.Label(
                stat_frame, 
                text=stat_value, 
                font=("Tahoma", 10, "bold"),
                anchor='w'
            )
            value_label.pack(side=tk.RIGHT)
    
    def refresh_data(self):
        """بروزرسانی داده‌های داشبورد"""
        # این متد می‌تواند داده‌های واقعی از پایگاه داده بگیرد
        messagebox.showinfo(
            self.config.t("info"), 
            "داده‌های داشبورد بروزرسانی شدند"
        )
    
    def on_activate(self):
        """هنگام فعال شدن ماژول فراخوانی می‌شود"""
        logger.info("ماژول داشبورد فعال شد")