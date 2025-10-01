import customtkinter as ctk
from core.base_module import BaseModule
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime
import psutil

class DashboardModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        
        # داده‌های event handling
        self.activity_logs = []
        
        # setup event listeners
        self.setup_event_listeners()
        self.setup_ui()
    
    def setup_event_listeners(self):
        """تنظیم شنوندگان رویداد"""
        # فقط eventهای اصلی رو اضافه می‌کنیم
        events = ["module_changed", "settings_changed", "language_changed"]
        
        for event in events:
            self.app.event_bus.subscribe(event, self.on_activity_event)
    
    def on_activity_event(self, data):
        """وقتی رویداد جدید دریافت می‌شود"""
        event_type = data.get("event_type", "unknown")
        module = data.get("module", "system")
        
        # ایجاد لاگ فعالیت ساده
        log_entry = {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "module": module,
            "message": self.get_event_message(event_type, data)
        }
        
        # اضافه کردن به لاگ‌ها
        self.activity_logs.append(log_entry)
        
        # محدود کردن تعداد
        if len(self.activity_logs) > 20:
            self.activity_logs = self.activity_logs[-20:]
        
        print(f"📝 Dashboard: {log_entry['message']}")
    
    def get_event_message(self, event_type, data):
        """ایجاد پیام خوانا برای رویداد"""
        # استفاده از language_manager به جای language برای compatibility
        language_manager = getattr(self.app, 'language_manager', self.app.language)
        
        if language_manager.is_rtl():
            messages = {
                "module_changed": f"تغییر به ماژول {data.get('module', 'نامشخص')}",
                "settings_changed": "تنظیمات تغییر کرد",
                "language_changed": f"زبان تغییر کرد به: {data.get('language', 'نامشخص')}"
            }
        else:
            messages = {
                "module_changed": f"Switched to {data.get('module', 'unknown')} module",
                "settings_changed": "Settings changed",
                "language_changed": f"Language changed to: {data.get('language', 'unknown')}"
            }
        
        return messages.get(event_type, event_type)
    
    def setup_ui(self):
        """ایجاد رابط کاربری داشبورد با طراحی متریال"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی با قابلیت اسکرول
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # استفاده از language_manager به جای language
        language_manager = getattr(self.app, 'language_manager', self.app.language)
        
        # عنوان داشبورد
        title_text = "داشبورد اصلی" if language_manager.is_rtl() else "Main Dashboard"
        title = ctk.CTkLabel(
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
            {"title": "مقالات", "count": "۱۲", "icon": "📄", "color": "#2196F3", "light_color": "#E3F2FD"},
            {"title": "یادداشت‌ها", "count": "۸", "icon": "📝", "color": "#4CAF50", "light_color": "#E8F5E9"},
            {"title": "وظایف", "count": "۵", "icon": "📅", "color": "#FF9800", "light_color": "#FFF3E0"},
            {"title": "پروژه‌ها", "count": "۳", "icon": "🔍", "color": "#9C27B0", "light_color": "#F3E5F5"}
        ]
        
        for i, stat in enumerate(stats):
            stat_frame = ctk.CTkFrame(
                stats_frame, 
                corner_radius=12,
                fg_color=stat["light_color"],
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
            title_text = stat["title"] if not language_manager.is_rtl() else self.translate_stat(stat["title"])
            title_label = ctk.CTkLabel(
                stat_frame,
                text=title_text,
                font=ctk.CTkFont(size=14)
            )
            title_label.pack(pady=(0, 15))
        
        # بخش فعالیت‌های اخیر
        self.create_recent_activities_section(main_frame, language_manager)
        
        # نمودار فعالیت‌های اخیر
        chart_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        chart_frame.pack(fill="x", padx=20, pady=20)
        
        chart_title = ctk.CTkLabel(
            chart_frame,
            text="فعالیت‌های اخیر" if language_manager.is_rtl() else "Recent Activities",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        chart_title.pack(pady=15)
        
        # ایجاد نمودار
        self.create_activity_chart(chart_frame, language_manager)
        
        # اعلان‌های اخیر
        notifications_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        notifications_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        notif_title = ctk.CTkLabel(
            notifications_frame,
            text="اعلان‌ها" if language_manager.is_rtl() else "Notifications",
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
            self.create_notification_item(notifications_frame, notif, language_manager)
    
    def create_recent_activities_section(self, parent, language_manager):
        """ایجاد بخش فعالیت‌های اخیر"""
        activities_frame = ctk.CTkFrame(parent, corner_radius=12)
        activities_frame.pack(fill="x", padx=20, pady=20)
        
        activities_title = ctk.CTkLabel(
            activities_frame,
            text="فعالیت‌های سیستم" if language_manager.is_rtl() else "System Activities",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        activities_title.pack(pady=15)
        
        # نمایش فعالیت‌های واقعی
        activities_content = ctk.CTkFrame(activities_frame, fg_color="transparent")
        activities_content.pack(fill="x", padx=20, pady=(0, 15))
        
        if not self.activity_logs:
            empty_text = "هیچ فعالیتی ثبت نشده است" if language_manager.is_rtl() else "No activities recorded"
            empty_label = ctk.CTkLabel(
                activities_content,
                text=empty_text,
                font=ctk.CTkFont(size=12),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(pady=10)
        else:
            # نمایش ۵ فعالیت اخیر
            for activity in reversed(self.activity_logs[-5:]):
                self.create_activity_item(activities_content, activity, language_manager)
    
    def create_activity_item(self, parent, activity, language_manager):
        """ایجاد آیتم فعالیت"""
        activity_frame = ctk.CTkFrame(parent, fg_color=("#F5F5F5", "#2A2A2A"), corner_radius=8)
        activity_frame.pack(fill="x", pady=3)
        
        content_frame = ctk.CTkFrame(activity_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=8)
        
        # آیکون بر اساس نوع فعالیت
        icon = self.get_activity_icon(activity["event_type"])
        
        if language_manager.is_rtl():
            # برای RTL: متن سپس آیکون
            text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            text_frame.pack(side="right", fill="x", expand=True)
            
            message_label = ctk.CTkLabel(
                text_frame,
                text=activity["message"],
                font=ctk.CTkFont(size=11)
            )
            message_label.pack(anchor="e")
            
            time_text = activity["timestamp"].strftime("%H:%M")
            time_label = ctk.CTkLabel(
                text_frame,
                text=time_text,
                font=ctk.CTkFont(size=10),
                text_color=("#666666", "#AAAAAA")
            )
            time_label.pack(anchor="e")
            
            icon_label = ctk.CTkLabel(
                content_frame,
                text=icon,
                font=ctk.CTkFont(size=12)
            )
            icon_label.pack(side="right", padx=(10, 0))
        else:
            # برای LTR: آیکون سپس متن
            icon_label = ctk.CTkLabel(
                content_frame,
                text=icon,
                font=ctk.CTkFont(size=12)
            )
            icon_label.pack(side="left", padx=(0, 10))
            
            text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)
            
            message_label = ctk.CTkLabel(
                text_frame,
                text=activity["message"],
                font=ctk.CTkFont(size=11)
            )
            message_label.pack(anchor="w")
            
            time_text = activity["timestamp"].strftime("%H:%M")
            time_label = ctk.CTkLabel(
                text_frame,
                text=time_text,
                font=ctk.CTkFont(size=10),
                text_color=("#666666", "#AAAAAA")
            )
            time_label.pack(anchor="w")
    
    def get_activity_icon(self, event_type):
        """دریافت آیکون مناسب برای نوع فعالیت"""
        icons = {
            "module_changed": "🔄",
            "settings_changed": "⚙️",
            "language_changed": "🌐"
        }
        return icons.get(event_type, "📌")
    
    def translate_stat(self, text):
        """ترجمه آماری برای نمایش در حالت RTL"""
        translations = {
            "مقالات": "مقالات",
            "یادداشت‌ها": "یادداشت‌ها",
            "وظایف": "وظایف",
            "پروژه‌ها": "پروژه‌ها"
        }
        return translations.get(text, text)
    
    def create_activity_chart(self, parent, language_manager):
        """ایجاد نمودار فعالیت‌های اخیر"""
        try:
            # داده‌های نمونه برای نمودار
            days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
            activities = [5, 7, 3, 8, 6, 4, 9]
            
            if not language_manager.is_rtl():
                days = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
            
            # ایجاد نمودار
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(days, activities, color=['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#F44336', '#607D8B', '#795548'])
            ax.set_ylabel('تعداد فعالیت' if language_manager.is_rtl() else 'Activity Count')
            ax.set_title('فعالیت‌های هفتگی' if language_manager.is_rtl() else 'Weekly Activities')
            
            # قرار دادن نمودار در Tkinter
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=20, pady=10)
        except Exception as e:
            print(f"خطا در ایجاد نمودار: {e}")
            error_label = ctk.CTkLabel(
                parent,
                text="خطا در نمایش نمودار" if language_manager.is_rtl() else "Chart display error",
                font=ctk.CTkFont(size=14)
            )
            error_label.pack(pady=20)
    
    def create_notification_item(self, parent, notif, language_manager):
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
        icon_label.pack(side="right" if language_manager.is_rtl() else "left", padx=(0, 10))
        
        # متن و زمان
        text_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        text_frame.pack(side="right" if language_manager.is_rtl() else "left", fill="x", expand=True)
        
        text_label = ctk.CTkLabel(
            text_frame,
            text=notif["text"],
            font=ctk.CTkFont(size=14)
        )
        text_label.pack(anchor="w" if not language_manager.is_rtl() else "e")
        
        time_label = ctk.CTkLabel(
            text_frame,
            text=notif["time"],
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#AAAAAA")
        )
        time_label.pack(anchor="w" if not language_manager.is_rtl() else "e")
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()