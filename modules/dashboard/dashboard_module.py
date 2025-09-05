import customtkinter as ctk
from core.theme_manager import ThemeManager

class DashboardModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config = config
        self.theme = ThemeManager()
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """ایجاد رابط کاربری داشبورد"""
        # فریم اصلی با قابلیت اسکرول
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        
        # کارت‌های آمار
        self.create_stats_section()
        
        # نمودارهای اخیر
        self.create_charts_section()
        
        # فعالیت‌های اخیر
        self.create_activity_section()
    
    def create_stats_section(self):
        """ایجاد بخش آمار"""
        stats_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10, padx=20)
        
        stats_data = [
            {"icon": "📄", "title": "مقالات", "value": "157", "color": "primary"},
            {"icon": "📖", "title": "خوانده شده", "value": "89", "color": "success"},
            {"icon": "⏳", "title": "در حال مطالعه", "value": "23", "color": "warning"},
            {"icon": "📌", "title": "برنامه‌ریزی شده", "value": "45", "color": "secondary"}
        ]
        
        for i, stat in enumerate(stats_data):
            card = self.create_stat_card(stat)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
    
    def create_stat_card(self, data):
        """ایجاد کارت آمار"""
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.theme.get_color("surface"),
            corner_radius=15,
            height=120,
            border_width=1,
            border_color=self.theme.get_color("border")
        )
        
        # آیکون
        icon_label = ctk.CTkLabel(
            card,
            text=data["icon"],
            font=ctk.CTkFont(size=24),
            text_color=self.theme.get_color(data["color"])
        )
        icon_label.pack(pady=(15, 5))
        
        # مقدار
        value_label = ctk.CTkLabel(
            card,
            text=data["value"],
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.theme.get_color("fg")
        )
        value_label.pack()
        
        # عنوان
        title_label = ctk.CTkLabel(
            card,
            text=data["title"],
            font=ctk.CTkFont(size=12),
            text_color=self.theme.get_color("secondary")
        )
        title_label.pack(pady=(0, 15))
        
        return card
    
    def create_charts_section(self):
        """ایجاد بخش نمودارها"""
        charts_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        charts_frame.pack(fill="x", pady=20, padx=20)
        
        # عنوان بخش
        section_title = ctk.CTkLabel(
            charts_frame,
            text="📊 آمار و نمودارها",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(anchor="w", pady=(0, 15))
        
        # نمودارها
        charts_container = ctk.CTkFrame(charts_frame, fg_color="transparent")
        charts_container.pack(fill="x")
        
        # نمودار وضعیت مقالات
        status_chart_frame = ctk.CTkFrame(
            charts_container,
            fg_color=self.theme.get_color("surface"),
            corner_radius=15,
            height=200,
            border_width=1,
            border_color=self.theme.get_color("border")
        )
        status_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # نمودار توزیع موضوعی
        topic_chart_frame = ctk.CTkFrame(
            charts_container,
            fg_color=self.theme.get_color("surface"),
            corner_radius=15,
            height=200,
            border_width=1,
            border_color=self.theme.get_color("border")
        )
        topic_chart_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # جایگزین برای نمودارها (تا زمانی که نمودارهای واقعی پیاده‌سازی شوند)
        ctk.CTkLabel(
            status_chart_frame,
            text="نمودار وضعیت مقالات",
            font=ctk.CTkFont(size=14)
        ).pack(expand=True)
        
        ctk.CTkLabel(
            topic_chart_frame,
            text="نمودار توزیع موضوعی",
            font=ctk.CTkFont(size=14)
        ).pack(expand=True)
    
    def create_activity_section(self):
        """ایجاد بخش فعالیت‌های اخیر"""
        activity_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        activity_frame.pack(fill="x", pady=20, padx=20)
        
        # عنوان بخش
        section_title = ctk.CTkLabel(
            activity_frame,
            text="📋 فعالیت‌های اخیر",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(anchor="w", pady=(0, 15))
        
        # لیست فعالیت‌ها
        activities = [
            {"action": "افزودن مقاله", "title": "مقاله جدید در زمینه هوش مصنوعی", "time": "2 ساعت پیش"},
            {"action": "بروزرسانی", "title": "یادداشت‌های تحقیق", "time": "5 ساعت پیش"},
            {"action": "مطالعه", "title": "مقاله مروری ML", "time": "1 روز پیش"},
            {"action": "برنامه‌ریزی", "title": "جلسه مطالعه هفتگی", "time": "2 روز پیش"}
        ]
        
        for activity in activities:
            self.create_activity_item(activity_frame, activity)
    
    def create_activity_item(self, parent, activity):
        """ایجاد آیتم فعالیت"""
        item_frame = ctk.CTkFrame(
            parent,
            fg_color=self.theme.get_color("surface"),
            corner_radius=10,
            height=60,
            border_width=1,
            border_color=self.theme.get_color("border")
        )
        item_frame.pack(fill="x", pady=5)
        
        # محتوای آیتم
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=10)
        
        # عمل و عنوان
        action_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        action_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            action_frame,
            text=activity["action"],
            font=ctk.CTkFont(weight="bold"),
            text_color=self.theme.get_color("primary")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            action_frame,
            text=activity["title"],
            font=ctk.CTkFont(size=12),
            text_color=self.theme.get_color("fg")
        ).pack(anchor="w")
        
        # زمان
        ctk.CTkLabel(
            content_frame,
            text=activity["time"],
            font=ctk.CTkFont(size=11),
            text_color=self.theme.get_color("secondary")
        ).pack(side="right")
    
    def load_data(self):
        """بارگذاری داده‌های داشبورد"""
        # این تابع می‌تواند داده‌های واقعی از پایگاه داده بارگذاری کند
        pass