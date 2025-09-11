import customtkinter as ctk
from core.base_module import BaseModule
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class DashboardModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری داشبورد با طراحی متریال"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی با قابلیت اسکرول
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # عنوان داشبورد
        title_text = "داشبورد اصلی" if self.language.is_rtl() else "Main Dashboard"
        title = self.create_label(
            main_frame,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # کارت‌های آمار
        stats_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        # آمار در ۴ ستون
        stats = [
            {"title": "مقالات", "count": "۱۲", "icon": "📄", "color": "#2196F3"},
            {"title": "یادداشت‌ها", "count": "۸", "icon": "📝", "color": "#4CAF50"},
            {"title": "وظایف", "count": "۵", "icon": "📅", "color": "#FF9800"},
            {"title": "پروژه‌ها", "count": "۳", "icon": "🔍", "color": "#9C27B0"}
        ]
        
        for i, stat in enumerate(stats):
            stat_frame = ctk.CTkFrame(
                stats_frame, 
                corner_radius=12,
                fg_color=stat["color"] + "20",  # alpha 20%
                border_color=stat["color"],
                border_width=1
            )
            stat_frame.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            
            # آیکون
            icon_label = ctk.CTkLabel(
                stat_frame,
                text=stat["icon"],
                font=ctk.CTkFont(size=24),
                text_color=stat["color"]
            )
            icon_label.pack(pady=(15, 5))
            
            # تعداد
            count_label = ctk.CTkLabel(
                stat_frame,
                text=stat["count"],
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=stat["color"]
            )
            count_label.pack(pady=5)
            
            # عنوان
            title_text = stat["title"] if not self.language.is_rtl() else self.translate_stat(stat["title"])
            title_label = self.create_label(
                stat_frame,
                text=title_text,
                font=ctk.CTkFont(size=14),
                text_color=("#37474F", "#E0E0E0")
            )
            title_label.pack(pady=(0, 15))
        
        # نمودار فعالیت‌های اخیر
        chart_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        chart_frame.pack(fill="x", padx=20, pady=20)
        
        chart_title = self.create_label(
            chart_frame,
            text="فعالیت‌های اخیر" if self.language.is_rtl() else "Recent Activities",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        chart_title.pack(pady=15)
        
        # ایجاد نمودار
        self.create_activity_chart(chart_frame)
        
        # اعلان‌های اخیر
        notifications_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        notifications_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        notif_title = self.create_label(
            notifications_frame,
            text="اعلان‌ها" if self.language.is_rtl() else "Notifications",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        notif_title.pack(pady=15)
        
        # لیست اعلان‌ها
        notifications = [
            {"text": "مقاله جدید اضافه شد", "time": "۲ ساعت پیش", "icon": "📄"},
            {"text": "یادداشت شما ذخیره شد", "time": "۵ ساعت پیش", "icon": "📝"},
            {"text": "مهلت انجام وظیفه نزدیک است", "time": "۱ روز پیش", "icon": "⏰"},
            {"text": "پروژه تحقیق به روز شد", "time": "۲ روز پیش", "icon": "🔍"}
        ]
        
        for notif in notifications:
            self.create_notification_item(notifications_frame, notif)
    
    def translate_stat(self, text):
        """ترجمه آماری برای نمایش در حالت RTL"""
        translations = {
            "مقالات": "مقالات",
            "یادداشت‌ها": "یادداشت‌ها",
            "وظایف": "وظایف",
            "پروژه‌ها": "پروژه‌ها"
        }
        return translations.get(text, text)
    
    def create_activity_chart(self, parent):
        """ایجاد نمودار فعالیت‌های اخیر"""
        # داده‌های نمونه برای نمودار
        days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        activities = [5, 7, 3, 8, 6, 4, 9]
        
        if not self.language.is_rtl():
            days = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
        
        # ایجاد نمودار
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(days, activities, color=['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#F44336', '#607D8B', '#795548'])
        ax.set_ylabel('تعداد فعالیت' if self.language.is_rtl() else 'Activity Count')
        ax.set_title('فعالیت‌های هفتگی' if self.language.is_rtl() else 'Weekly Activities')
        
        # تنظیمات نمودار برای RTL
        if self.language.is_rtl():
            ax.set_ylabel('تعداد فعالیت', fontname='B Nazanin')
            ax.set_title('فعالیت‌های هفتگی', fontname='B Nazanin')
            for label in ax.get_xticklabels():
                label.set_fontname('B Nazanin')
            for label in ax.get_yticklabels():
                label.set_fontname('B Nazanin')
        
        # قرار دادن نمودار در Tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=20, pady=10)
    
    def create_notification_item(self, parent, notif):
        """ایجاد آیتم اعلان"""
        notif_frame = ctk.CTkFrame(parent, fg_color=("#F5F5F5", "#2A2A2A"), corner_radius=8)
        notif_frame.pack(fill="x", padx=20, pady=5)
        
        # محتوای اعلان
        content_frame = ctk.CTkFrame(notif_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=10)
        
        # آیکون
        icon_label = ctk.CTkLabel(
            content_frame,
            text=notif["icon"],
            font=ctk.CTkFont(size=16)
        )
        icon_label.pack(side="right" if self.language.is_rtl() else "left", padx=(0, 10))
        
        # متن و زمان
        text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        text_frame.pack(side="right" if self.language.is_rtl() else "left", fill="x", expand=True)
        
        text_label = self.create_label(
            text_frame,
            text=notif["text"],
            font=ctk.CTkFont(size=14)
        )
        text_label.pack(anchor="w" if not self.language.is_rtl() else "e")
        
        time_label = self.create_label(
            text_frame,
            text=notif["time"],
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#AAAAAA")
        )
        time_label.pack(anchor="w" if not self.language.is_rtl() else "e")
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()