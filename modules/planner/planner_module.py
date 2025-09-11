import customtkinter as ctk
from core.base_module import BaseModule
from tkinter import ttk
from datetime import datetime, timedelta
import calendar

class PlannerModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        self.current_date = datetime.now()
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری برنامه‌ریزی"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # هدر با کنترل‌های تاریخ
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = self.create_label(
            header_frame,
            text="برنامه‌ریزی" if self.language.is_rtl() else "Planner",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="right" if self.language.is_rtl() else "left")
        
        # کنترل‌های ناوبری تاریخ
        nav_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        nav_frame.pack(side="left" if self.language.is_rtl() else "right")
        
        prev_btn = self.create_button(
            nav_frame,
            text="◀",
            command=self.previous_month,
            font=ctk.CTkFont(size=16),
            width=30,
            height=30
        )
        prev_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        month_year = self.current_date.strftime("%B %Y")
        if self.language.is_rtl():
            # تبدیل به تاریخ شمسی یا نمایش به فارسی
            month_year = self.get_persian_month_year()
        
        self.date_label = self.create_label(
            nav_frame,
            text=month_year,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.date_label.pack(side="right" if self.language.is_rtl() else "left", padx=10)
        
        next_btn = self.create_button(
            nav_frame,
            text="▶",
            command=self.next_month,
            font=ctk.CTkFont(size=16),
            width=30,
            height=30
        )
        next_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        today_btn = self.create_button(
            nav_frame,
            text="امروز" if self.language.is_rtl() else "Today",
            command=self.go_to_today,
            font=ctk.CTkFont(size=12),
            height=30
        )
        today_btn.pack(side="right" if self.language.is_rtl() else "left", padx=10)
        
        # ایجاد تقویم
        self.create_calendar(main_frame)
        
        # بخش وظایف
        tasks_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tasks_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        tasks_title = self.create_label(
            tasks_frame,
            text="وظایف امروز" if self.language.is_rtl() else "Today's Tasks",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        tasks_title.pack(pady=(0, 10))
        
        # لیست وظایف
        self.create_task_list(tasks_frame)
    
    def get_persian_month_year(self):
        """دریافت ماه و سال به فارسی"""
        # این تابع می‌تواند برای تبدیل تاریخ میلادی به شمسی توسعه یابد
        months = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 
            4: "تیر", 5: "مرداد", 6: "شهریور",
            7: "مهر", 8: "آبان", 9: "آذر",
            10: "دی", 11: "بهمن", 12: "اسفند"
        }
        return f"{months[self.current_date.month]} {self.current_date.year}"
    
    def create_calendar(self, parent):
        """ایجاد تقویم"""
        calendar_frame = ctk.CTkFrame(parent, fg_color="transparent")
        calendar_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # ایجاد جدول تقویم
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # هدر روزهای هفته
        days_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
        days_frame.pack(fill="x")
        
        weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
        if not self.language.is_rtl():
            weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        
        for i, day in enumerate(weekdays):
            day_label = self.create_label(
                days_frame,
                text=day,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("#666666", "#AAAAAA")
            )
            day_label.grid(row=0, column=i, padx=2, pady=5, sticky="nsew")
            days_frame.grid_columnconfigure(i, weight=1)
        
        # ایجاد خانه‌های تقویم
        for week_num, week in enumerate(cal):
            week_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
            week_frame.pack(fill="x", pady=2)
            
            for day_num, day in enumerate(week):
                if day == 0:
                    # روز خارج از ماه
                    day_cell = ctk.CTkFrame(week_frame, width=40, height=40, fg_color="transparent")
                else:
                    # روز داخل ماه
                    is_today = (day == datetime.now().day and 
                               self.current_date.month == datetime.now().month and 
                               self.current_date.year == datetime.now().year)
                    
                    day_cell = ctk.CTkFrame(
                        week_frame, 
                        width=40, 
                        height=40, 
                        corner_radius=20,
                        fg_color="#2196F3" if is_today else ("#F0F0F0", "#2A2A2A"),
                        border_color="#1976D2" if is_today else ("#E0E0E0", "#3A3A3A"),
                        border_width=1 if is_today else 0
                    )
                    
                    day_label = self.create_label(
                        day_cell,
                        text=str(day),
                        font=ctk.CTkFont(size=12, weight="bold" if is_today else "normal"),
                        text_color="#FFFFFF" if is_today else ("#333333", "#E0E0E0")
                    )
                    day_label.place(relx=0.5, rely=0.5, anchor="center")
                
                day_cell.grid(row=0, column=day_num, padx=2, sticky="nsew")
                week_frame.grid_columnconfigure(day_num, weight=1)
    
    def create_task_list(self, parent):
        """ایجاد لیست وظایف"""
        # نمونه داده‌های وظایف
        tasks = [
            {"title": "تکمیل گزارش تحقیق", "time": "10:00", "priority": "high"},
            {"title": "مرور مقالات جدید", "time": "14:30", "priority": "medium"},
            {"title": "جلسه با تیم تحقیق", "time": "16:00", "priority": "high"},
            {"title": "بررسی داده‌های جمع‌آوری شده", "time": "18:00", "priority": "low"}
        ]
        
        for task in tasks:
            task_frame = ctk.CTkFrame(
                parent, 
                fg_color=("#F5F5F5", "#2A2A2A"),
                corner_radius=8,
                height=50
            )
            task_frame.pack(fill="x", pady=5)
            task_frame.pack_propagate(False)
            
            # رنگ بر اساس اولویت
            priority_color = {
                "high": "#F44336",
                "medium": "#FF9800",
                "low": "#4CAF50"
            }
            
            # نشانگر اولویت
            priority_indicator = ctk.CTkFrame(
                task_frame, 
                width=5,
                fg_color=priority_color[task["priority"]],
                corner_radius=2
            )
            priority_indicator.pack(side="right" if self.language.is_rtl() else "left", fill="y", padx=5)
            
            # اطلاعات وظیفه
            info_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
            info_frame.pack(fill="both", expand=True, padx=10)
            
            title_label = self.create_label(
                info_frame,
                text=task["title"],
                font=ctk.CTkFont(size=14)
            )
            title_label.pack(anchor="w" if not self.language.is_rtl() else "e")
            
            time_label = self.create_label(
                info_frame,
                text=task["time"],
                font=ctk.CTkFont(size=12),
                text_color=("#666666", "#AAAAAA")
            )
            time_label.pack(anchor="w" if not self.language.is_rtl() else "e")
            
            # دکمه تکمیل
            complete_btn = ctk.CTkButton(
                task_frame,
                text="✓",
                width=30,
                height=30,
                font=ctk.CTkFont(size=12),
                fg_color="#4CAF50",
                hover_color="#45a049",
                command=lambda t=task: self.complete_task(t)
            )
            complete_btn.pack(side="left" if self.language.is_rtl() else "right", padx=10)
    
    def previous_month(self):
        """ماه قبلی"""
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.setup_ui()
    
    def next_month(self):
        """ماه بعدی"""
        next_month = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = next_month.replace(day=1)
        self.setup_ui()
    
    def go_to_today(self):
        """برو به تاریخ امروز"""
        self.current_date = datetime.now()
        self.setup_ui()
    
    def complete_task(self, task):
        """تکمیل وظیفه"""
        print(f"تکمیل وظیفه: {task['title']}")
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()