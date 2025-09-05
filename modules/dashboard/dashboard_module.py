import customtkinter as ctk
from core.theme_manager import ThemeManager
from core.rtl_support import reshape_text, set_widget_rtl

class DashboardModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config = config
        self.theme = ThemeManager()
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """ایجاد رابط کاربری داشبورد با پشتیبانی RTL"""
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
        from core.rtl_support import reshape_text, set_widget_rtl
        
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
        title_text = reshape_text(data["title"])
        title_label = ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(size=12),
            text_color=self.theme.get_color("secondary")
        )
        title_label.pack(pady=(0, 15))
        set_widget_rtl(title_label)
        
        return card
    
    def create_charts_section(self):
        """ایجاد بخش نمودارها"""
        from core.rtl_support import reshape_text, set_widget_rtl
        
        charts_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        charts_frame.pack(fill="x", pady=20, padx=20)
        
        # عنوان بخش
        section_title_text = reshape_text("📊 آمار و نمودارها")
        section_title = ctk.CTkLabel(
            charts_frame,
            text=section_title_text,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(anchor="w", pady=(0, 15))
        set_widget_rtl(section_title)
        
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
        status_chart_text = reshape_text("نمودار وضعیت مقالات")
        status_chart_label = ctk.CTkLabel(
            status_chart_frame,
            text=status_chart_text,
            font=ctk.CTkFont(size=14)
        )
        status_chart_label.pack(expand=True)
        set_widget_rtl(status_chart_label)
        
        topic_chart_text = reshape_text("نمودار توزیع موضوعی")
        topic_chart_label = ctk.CTkLabel(
            topic_chart_frame,
            text=topic_chart_text,
            font=ctk.CTkFont(size=14)
        )
        topic_chart_label.pack(expand=True)
        set_widget_rtl(topic_chart_label)
    
    def create_activity_section(self):
        """ایجاد بخش فعالیت‌های اخیر"""
        from core.rtl_support import reshape_text, set_widget_rtl
        
        activity_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        activity_frame.pack(fill="x", pady=20, padx=20)
        
        # عنوان بخش
        section_title_text = reshape_text("📋 فعالیت‌های اخیر")
        section_title = ctk.CTkLabel(
            activity_frame,
            text=section_title_text,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(anchor="w", pady=(0, 15))
        set_widget_rtl(section_title)
        
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
        from core.rtl_support import reshape_text, set_widget_rtl
        
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
        action_frame.pack(side="right", fill="x", expand=True)  # تغییر به سمت راست
        
        action_text = reshape_text(activity["action"])
        action_label = ctk.CTkLabel(
            action_frame,
            text=action_text,
            font=ctk.CTkFont(weight="bold"),
            text_color=self.theme.get_color("primary")
        )
        action_label.pack(anchor="e")  # تراز به راست
        set_widget_rtl(action_label)
        
        title_text = reshape_text(activity["title"])
        title_label = ctk.CTkLabel(
            action_frame,
            text=title_text,
            font=ctk.CTkFont(size=12),
            text_color=self.theme.get_color("fg")
        )
        title_label.pack(anchor="e")  # تراز به راست
        set_widget_rtl(title_label)
        
        # زمان
        time_text = reshape_text(activity["time"])
        time_label = ctk.CTkLabel(
            content_frame,
            text=time_text,
            font=ctk.CTkFont(size=11),
            text_color=self.theme.get_color("secondary")
        )
        time_label.pack(side="left")  # تغییر به سمت چپ
        set_widget_rtl(time_label)
    
    def load_data(self):
        """بارگذاری داده‌های داشبورد"""
        # این تابع می‌تواند داده‌های واقعی از پایگاه داده بارگذاری کند
        pass