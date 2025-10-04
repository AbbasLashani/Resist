import customtkinter as ctk
from datetime import datetime, timedelta
import sqlite3
import json
import jdatetime
from tkinter import messagebox

class PlanningModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app
        self.config = config
        
        # مدیریت زبان و فونت
        if hasattr(app, 'language_manager'):
            self.language_manager = app.language_manager
        elif hasattr(app, 'language'):
            self.language_manager = app.language
            
        if hasattr(app, 'font_manager'):
            self.font_manager = app.font_manager
        else:
            from core.font_manager import FontManager
            self.font_manager = FontManager(config)
        
        # داده‌ها
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        self.tasks = []
        self.goals = []
        self.plans = []
        
        # تنظیم event listeners
        self.setup_event_listeners()
        
        # بارگذاری داده‌ها
        self.load_data()
        
        # ایجاد UI
        self.setup_ui()
    
    def setup_event_listeners(self):
        """تنظیم شنوندگان رویداد"""
        try:
            self.app.event_bus.subscribe("font_changed", self.on_font_changed)
            self.app.event_bus.subscribe("task_added", self.on_task_changed)
            self.app.event_bus.subscribe("task_completed", self.on_task_changed)
            self.app.event_bus.subscribe("goal_added", self.on_goal_changed)
            self.app.event_bus.subscribe("plan_added", self.on_plan_changed)
            print("✅ Event listeners برای ماژول برنامه‌ریزی ثبت شدند")
        except Exception as e:
            print(f"⚠️ خطا در ثبت event listeners برنامه‌ریزی: {e}")
    
    def load_data(self):
        """بارگذاری داده‌ها از دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            # ایجاد جداول اگر وجود ندارند
            self.create_tables(cursor)
            
            # بارگذاری تسک‌ها
            cursor.execute('''
                SELECT id, title, description, due_date, priority, completed, category 
                FROM tasks 
                ORDER BY due_date, priority DESC
            ''')
            self.tasks = cursor.fetchall()
            
            # بارگذاری اهداف
            cursor.execute('''
                SELECT id, title, description, target_date, progress, priority, category 
                FROM goals 
                ORDER BY target_date, priority DESC
            ''')
            self.goals = cursor.fetchall()
            
            # بارگذاری پلن‌ها
            cursor.execute('''
                SELECT id, title, description, start_date, end_date, color, completed, progress 
                FROM plans 
                ORDER BY start_date
            ''')
            self.plans = cursor.fetchall()
            
            conn.close()
            print("✅ داده‌های برنامه‌ریزی بارگذاری شدند")
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری داده‌های برنامه‌ریزی: {e}")
    
    def create_tables(self, cursor):
        """ایجاد جداول مورد نیاز"""
        # جدول اهداف
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                target_date TEXT,
                progress INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'medium',
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول پلن‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                color TEXT DEFAULT '#2196F3',
                completed BOOLEAN DEFAULT FALSE,
                progress INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def setup_ui(self):
        """ایجاد رابط کاربری ماژول برنامه‌ریزی"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # عنوان اصلی
        title_text = "📅 برنامه‌ریزی و مدیریت زمان" if self.language_manager.is_rtl() else "📅 Planning & Time Management"
        title_label = ctk.CTkLabel(
            self,
            text=title_text,
            font=self.font_manager.get_font(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # فریم اصلی با تب‌ها
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ایجاد تب‌های مختلف
        self.daily_tab = self.tabview.add("📝 روزانه")
        self.goals_tab = self.tabview.add("🎯 اهداف")
        self.calendar_tab = self.tabview.add("📅 تقویم")
        self.plans_tab = self.tabview.add("📊 پلن‌ها")
        
        # ایجاد محتوای هر تب
        self.setup_daily_tab()
        self.setup_goals_tab()
        self.setup_calendar_tab()
        self.setup_plans_tab()
    
    def setup_daily_tab(self):
        """تب مدیریت تسک‌های روزانه"""
        # فریم اصلی
        main_frame = ctk.CTkFrame(self.daily_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # سمت چپ: لیست تسک‌ها
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # عنوان و دکمه اضافه کردن
        header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        tasks_title = ctk.CTkLabel(
            header_frame,
            text="✅ تسک‌های امروز" if self.language_manager.is_rtl() else "✅ Today's Tasks",
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        tasks_title.pack(side="left")
        
        add_task_btn = ctk.CTkButton(
            header_frame,
            text="➕ جدید",
            width=80,
            font=self.font_manager.get_font(),
            command=self.show_add_task_dialog
        )
        add_task_btn.pack(side="right")
        
        # لیست تسک‌ها
        self.tasks_list_frame = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.tasks_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # سمت راست: آمار و خلاصه
        right_frame = ctk.CTkFrame(main_frame, width=300)
        right_frame.pack(side="right", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # آمار روزانه
        stats_frame = ctk.CTkFrame(right_frame, corner_radius=10)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 آمار امروز" if self.language_manager.is_rtl() else "📊 Today's Stats",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        stats_title.pack(pady=10)
        
        self.stats_content = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_content.pack(fill="both", expand=True, padx=10, pady=5)
        
        # به‌روزرسانی نمایش
        self.refresh_daily_tasks()
        self.refresh_daily_stats()
    
    def refresh_daily_tasks(self):
        """به‌روزرسانی لیست تسک‌های روزانه"""
        # پاک کردن لیست قبلی
        for widget in self.tasks_list_frame.winfo_children():
            widget.destroy()
        
        today = self.current_date.strftime('%Y-%m-%d')
        today_tasks = [task for task in self.tasks 
                      if task[3] == today and not task[5]]  # تسک‌های امروز که کامل نشده‌اند
        
        if not today_tasks:
            empty_text = "🎉 هیچ تسکی برای امروز ندارید!" if self.language_manager.is_rtl() else "🎉 No tasks for today!"
            empty_label = ctk.CTkLabel(
                self.tasks_list_frame,
                text=empty_text,
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for task in today_tasks:
            self.create_task_item(task)
    
    def create_task_item(self, task):
        """ایجاد آیتم تسک در لیست"""
        task_id, title, description, due_date, priority, completed, category = task
        
        # رنگ بر اساس اولویت
        priority_colors = {
            'high': ('#FF5252', '#D32F2F'),
            'medium': ('#FFB74D', '#F57C00'),
            'low': ('#4CAF50', '#388E3C')
        }
        bg_color, border_color = priority_colors.get(priority, ('#E0E0E0', '#757575'))
        
        task_frame = ctk.CTkFrame(
            self.tasks_list_frame,
            fg_color=bg_color,
            border_color=border_color,
            border_width=2,
            corner_radius=8
        )
        task_frame.pack(fill="x", pady=3)
        
        content_frame = ctk.CTkFrame(task_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)
        
        # چک‌باکس و عنوان
        top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_frame.pack(fill="x")
        
        # چک‌باکس
        var = ctk.BooleanVar(value=completed)
        checkbox = ctk.CTkCheckBox(
            top_frame,
            text="",
            variable=var,
            command=lambda tid=task_id: self.toggle_task_completion(tid),
            font=self.font_manager.get_font()
        )
        checkbox.pack(side="right" if self.language_manager.is_rtl() else "left")
        
        # عنوان تسک
        title_label = ctk.CTkLabel(
            top_frame,
            text=title,
            font=self.font_manager.get_font(weight="bold"),
            wraplength=200
        )
        title_label.pack(side="right" if self.language_manager.is_rtl() else "left", 
                        padx=10, fill="x", expand=True)
        
        # اطلاعات پایین (دسته‌بندی و اولویت)
        if description or category:
            bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            bottom_frame.pack(fill="x", pady=(5, 0))
            
            if description:
                desc_label = ctk.CTkLabel(
                    bottom_frame,
                    text=description,
                    font=self.font_manager.get_font(size=10),
                    text_color=("#666666", "#AAAAAA"),
                    wraplength=250
                )
                desc_label.pack(side="right" if self.language_manager.is_rtl() else "left")
            
            if category:
                cat_label = ctk.CTkLabel(
                    bottom_frame,
                    text=f"🏷️ {category}",
                    font=self.font_manager.get_font(size=10),
                    text_color=("#666666", "#AAAAAA")
                )
                cat_label.pack(side="left" if self.language_manager.is_rtl() else "right")
    
    def refresh_daily_stats(self):
        """به‌روزرسانی آمار روزانه"""
        for widget in self.stats_content.winfo_children():
            widget.destroy()
        
        today = self.current_date.strftime('%Y-%m-%d')
        today_tasks = [task for task in self.tasks if task[3] == today]
        completed_tasks = [task for task in today_tasks if task[5]]
        pending_tasks = [task for task in today_tasks if not task[5]]
        
        total_tasks = len(today_tasks)
        completion_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
        
        stats = [
            {"label": "کل تسک‌ها", "value": total_tasks, "icon": "📋"},
            {"label": "تکمیل شده", "value": len(completed_tasks), "icon": "✅"},
            {"label": "در انتظار", "value": len(pending_tasks), "icon": "⏳"},
            {"label": "پیشرفت", "value": f"{completion_rate:.0f}%", "icon": "📊"}
        ]
        
        for stat in stats:
            stat_frame = ctk.CTkFrame(self.stats_content, fg_color=("#F5F5F5", "#2A2A2A"))
            stat_frame.pack(fill="x", pady=3)
            
            content_frame = ctk.CTkFrame(stat_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=10, pady=8)
            
            icon_label = ctk.CTkLabel(content_frame, text=stat["icon"], font=self.font_manager.get_font(size=14))
            value_label = ctk.CTkLabel(content_frame, text=str(stat["value"]), font=self.font_manager.get_font(weight="bold"))
            label_label = ctk.CTkLabel(content_frame, text=stat["label"], font=self.font_manager.get_font(size=12))
            
            if self.language_manager.is_rtl():
                icon_label.pack(side="right")
                value_label.pack(side="right", padx=(10, 5))
                label_label.pack(side="right", fill="x", expand=True)
            else:
                icon_label.pack(side="left")
                value_label.pack(side="left", padx=(5, 10))
                label_label.pack(side="left", fill="x", expand=True)
    
    def setup_goals_tab(self):
        """تب مدیریت اهداف"""
        main_frame = ctk.CTkFrame(self.goals_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # هدر
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        goals_title = ctk.CTkLabel(
            header_frame,
            text="🎯 اهداف من" if self.language_manager.is_rtl() else "🎯 My Goals",
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        goals_title.pack(side="left")
        
        add_goal_btn = ctk.CTkButton(
            header_frame,
            text="➕ هدف جدید",
            font=self.font_manager.get_font(),
            command=self.show_add_goal_dialog
        )
        add_goal_btn.pack(side="right")
        
        # لیست اهداف
        self.goals_list_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.goals_list_frame.pack(fill="both", expand=True)
        
        self.refresh_goals_list()
    
    def refresh_goals_list(self):
        """به‌روزرسانی لیست اهداف"""
        for widget in self.goals_list_frame.winfo_children():
            widget.destroy()
        
        if not self.goals:
            empty_text = "🎯 هنوز هدفی تعریف نکرده‌اید" if self.language_manager.is_rtl() else "🎯 No goals defined yet"
            empty_label = ctk.CTkLabel(
                self.goals_list_frame,
                text=empty_text,
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for goal in self.goals:
            self.create_goal_item(goal)
    
    def create_goal_item(self, goal):
        """ایجاد آیتم هدف"""
        goal_id, title, description, target_date, progress, priority, category = goal
        
        goal_frame = ctk.CTkFrame(self.goals_list_frame, corner_radius=10)
        goal_frame.pack(fill="x", pady=5)
        
        # هدر هدف
        header_frame = ctk.CTkFrame(goal_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.font_manager.get_font(weight="bold")
        )
        title_label.pack(side="right" if self.language_manager.is_rtl() else "left")
        
        # پیشرفت
        progress_frame = ctk.CTkFrame(goal_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.pack(fill="x", pady=5)
        progress_bar.set(progress / 100)
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text=f"{progress}% تکمیل",
            font=self.font_manager.get_font(size=12)
        )
        progress_label.pack()
        
        # اطلاعات پایین
        info_frame = ctk.CTkFrame(goal_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        if target_date:
            date_label = ctk.CTkLabel(
                info_frame,
                text=f"📅 {target_date}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            date_label.pack(side="right" if self.language_manager.is_rtl() else "left")
        
        if category:
            cat_label = ctk.CTkLabel(
                info_frame,
                text=f"🏷️ {category}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            cat_label.pack(side="left" if self.language_manager.is_rtl() else "right")
    
    def setup_calendar_tab(self):
        """تب تقویم ترکیبی میلادی-شمسی"""
        main_frame = ctk.CTkFrame(self.calendar_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # کنترل‌های تقویم
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 10))
        
        # ماه و سال فعلی
        self.month_year_label = ctk.CTkLabel(
            controls_frame,
            text=self.get_persian_month_year(),
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        self.month_year_label.pack(side="left")
        
        # دکمه‌های کنترل
        nav_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        nav_frame.pack(side="right")
        
        prev_btn = ctk.CTkButton(
            nav_frame, 
            text="◀", 
            width=40, 
            font=self.font_manager.get_font(),
            command=self.prev_month
        )
        prev_btn.pack(side="left", padx=5)
        
        today_btn = ctk.CTkButton(
            nav_frame, 
            text="امروز", 
            width=60, 
            font=self.font_manager.get_font(),
            command=self.go_to_today
        )
        today_btn.pack(side="left", padx=5)
        
        next_btn = ctk.CTkButton(
            nav_frame, 
            text="▶", 
            width=40, 
            font=self.font_manager.get_font(),
            command=self.next_month
        )
        next_btn.pack(side="left", padx=5)
        
        # تقویم
        self.calendar_frame = ctk.CTkFrame(main_frame)
        self.calendar_frame.pack(fill="both", expand=True)
        
        self.refresh_calendar()
    
    def get_persian_month_year(self):
        """دریافت ماه و سال به شمسی"""
        jalali_date = jdatetime.date.fromgregorian(date=self.current_date)
        months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        month = months[jalali_date.month - 1]
        year = jalali_date.year
        return f"{month} {year} - {self.current_date.strftime('%B %Y')}"
    
    def refresh_calendar(self):
        """به‌روزرسانی تقویم"""
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # ایجاد هدر روزهای هفته
        days = ["ش" if self.language_manager.is_rtl() else "Su", 
                "ی" if self.language_manager.is_rtl() else "Mo", 
                "د" if self.language_manager.is_rtl() else "Tu",
                "س" if self.language_manager.is_rtl() else "We", 
                "چ" if self.language_manager.is_rtl() else "Th", 
                "پ" if self.language_manager.is_rtl() else "Fr",
                "ج" if self.language_manager.is_rtl() else "Sa"]
        
        for i, day in enumerate(days):
            day_label = ctk.CTkLabel(
                self.calendar_frame,
                text=day,
                font=self.font_manager.get_font(weight="bold"),
                width=80,
                height=35
            )
            day_label.grid(row=0, column=i, padx=2, pady=2)
        
        # محاسبات تاریخ
        first_day = self.current_date.replace(day=1)
        start_day = first_day - timedelta(days=first_day.weekday())
        
        # ایجاد روزهای تقویم
        for week in range(6):
            for day in range(7):
                current_date = start_day + timedelta(days=week*7 + day)
                self.create_calendar_day(current_date, week+1, day)
    
    def create_calendar_day(self, date, week, day):
        """ایجاد یک روز در تقویم ترکیبی"""
        is_today = date.date() == datetime.now().date()
        is_current_month = date.month == self.current_date.month
        
        # تبدیل به تاریخ شمسی
        jalali_date = jdatetime.date.fromgregorian(date=date.date())
        
        # رنگ‌ها
        bg_color = "#FFFFFF" if not is_today else "#E3F2FD"
        text_color = "#000000" if is_current_month else "#CCCCCC"
        border_color = "#2196F3" if is_today else "#E0E0E0"
        
        day_frame = ctk.CTkFrame(
            self.calendar_frame,
            fg_color=bg_color,
            border_color=border_color,
            border_width=2 if is_today else 1,
            width=80,
            height=80
        )
        day_frame.grid(row=week, column=day, padx=2, pady=2, sticky="nsew")
        day_frame.grid_propagate(False)
        
        # شماره روز میلادی
        miladi_label = ctk.CTkLabel(
            day_frame,
            text=str(date.day),
            text_color=text_color,
            font=self.font_manager.get_font(size=12, weight="bold")
        )
        miladi_label.place(x=5, y=5)
        
        # شماره روز شمسی
        shamsi_label = ctk.CTkLabel(
            day_frame,
            text=str(jalali_date.day),
            text_color="#FF5722",
            font=self.font_manager.get_font(size=10)
        )
        shamsi_label.place(x=5, y=25)
        
        # نمایش تعداد تسک‌ها در این روز
        tasks_count = self.get_tasks_count_for_date(date)
        if tasks_count > 0:
            tasks_label = ctk.CTkLabel(
                day_frame,
                text=f"📝{tasks_count}",
                text_color="#FF5722",
                font=self.font_manager.get_font(size=8)
            )
            tasks_label.place(x=5, y=45)
        
        # نام روز شمسی کوچک
        day_name = jalali_date.strftime("%a")
        day_name_label = ctk.CTkLabel(
            day_frame,
            text=day_name,
            text_color="#666666",
            font=self.font_manager.get_font(size=8)
        )
        day_name_label.place(x=45, y=5)
    
    def get_tasks_count_for_date(self, date):
        """تعداد تسک‌های یک تاریخ خاص"""
        date_str = date.strftime('%Y-%m-%d')
        return len([task for task in self.tasks if task[3] == date_str and not task[5]])
    
    def setup_plans_tab(self):
        """تب مدیریت پلن‌های بلندمدت"""
        main_frame = ctk.CTkFrame(self.plans_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # هدر
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        plans_title = ctk.CTkLabel(
            header_frame,
            text="📊 پلن‌های بلندمدت" if self.language_manager.is_rtl() else "📊 Long-term Plans",
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        plans_title.pack(side="left")
        
        add_plan_btn = ctk.CTkButton(
            header_frame,
            text="➕ پلن جدید",
            font=self.font_manager.get_font(),
            command=self.show_add_plan_dialog
        )
        add_plan_btn.pack(side="right")
        
        # لیست پلن‌ها
        self.plans_list_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.plans_list_frame.pack(fill="both", expand=True)
        
        self.refresh_plans_list()
    
    def refresh_plans_list(self):
        """به‌روزرسانی لیست پلن‌ها"""
        for widget in self.plans_list_frame.winfo_children():
            widget.destroy()
        
        if not self.plans:
            empty_text = "📊 هنوز پلنی تعریف نکرده‌اید" if self.language_manager.is_rtl() else "📊 No plans defined yet"
            empty_label = ctk.CTkLabel(
                self.plans_list_frame,
                text=empty_text,
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(expand=True, pady=20)
            return
        
        for plan in self.plans:
            self.create_plan_item(plan)
    
    def create_plan_item(self, plan):
        """ایجاد آیتم پلن"""
        plan_id, title, description, start_date, end_date, color, completed, progress = plan
        
        plan_frame = ctk.CTkFrame(
            self.plans_list_frame, 
            corner_radius=10,
            border_color=color,
            border_width=2
        )
        plan_frame.pack(fill="x", pady=5)
        
        # هدر پلن
        header_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.font_manager.get_font(weight="bold")
        )
        title_label.pack(side="right" if self.language_manager.is_rtl() else "left")
        
        # وضعیت
        status_text = "✅ تکمیل شده" if completed else f"🔄 {progress}% پیشرفت"
        status_label = ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=self.font_manager.get_font(size=12),
            text_color=("#4CAF50" if completed else "#FF9800")
        )
        status_label.pack(side="left" if self.language_manager.is_rtl() else "right")
        
        # پیشرفت
        progress_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        progress_bar = ctk.CTkProgressBar(progress_frame)
        progress_bar.pack(fill="x", pady=5)
        progress_bar.set(progress / 100)
        
        # تاریخ‌ها
        dates_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
        dates_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        if start_date:
            start_label = ctk.CTkLabel(
                dates_frame,
                text=f"📅 شروع: {start_date}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            start_label.pack(side="right" if self.language_manager.is_rtl() else "left")
        
        if end_date:
            end_label = ctk.CTkLabel(
                dates_frame,
                text=f"⏰ پایان: {end_date}",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            end_label.pack(side="left" if self.language_manager.is_rtl() else "right")
        
        # توضیحات
        if description:
            desc_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
            desc_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            desc_label = ctk.CTkLabel(
                desc_frame,
                text=description,
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA"),
                wraplength=400
            )
            desc_label.pack(anchor="w" if not self.language_manager.is_rtl() else "e")
    
    def show_add_task_dialog(self):
        """نمایش دیالوگ اضافه کردن تسک"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("اضافه کردن تسک جدید")
        dialog.geometry("500x450")
        dialog.transient(self)
        dialog.grab_set()
        
        # استفاده از فونت
        font = self.font_manager.get_font()
        
        # محتوای دیالوگ
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(content_frame, text="عنوان تسک:", font=font).pack(anchor="w", pady=(10, 5))
        title_entry = ctk.CTkEntry(content_frame, width=400, font=font)
        title_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="توضیحات:", font=font).pack(anchor="w", pady=(10, 5))
        desc_entry = ctk.CTkTextbox(content_frame, width=400, height=80, font=font)
        desc_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="تاریخ (YYYY-MM-DD):", font=font).pack(anchor="w", pady=(10, 5))
        date_entry = ctk.CTkEntry(content_frame, width=400, font=font, placeholder_text="YYYY-MM-DD")
        date_entry.pack(fill="x", pady=(0, 10))
        # پیش‌پر کردن با تاریخ امروز
        date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(content_frame, text="اولویت:", font=font).pack(anchor="w", pady=(10, 5))
        priority_var = ctk.StringVar(value="medium")
        priority_combo = ctk.CTkComboBox(content_frame, 
                                       values=["low", "medium", "high"],
                                       variable=priority_var,
                                       font=font)
        priority_combo.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="دسته‌بندی:", font=font).pack(anchor="w", pady=(10, 5))
        category_entry = ctk.CTkEntry(content_frame, width=400, font=font, placeholder_text="اختیاری")
        category_entry.pack(fill="x", pady=(0, 10))
        
        def save_task():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "لطفاً عنوان تسک را وارد کنید")
                return
                
            self.save_new_task(
                title_entry.get().strip(),
                desc_entry.get("1.0", "end-1c").strip(),
                date_entry.get().strip(),
                priority_var.get(),
                category_entry.get().strip()
            )
            dialog.destroy()
        
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        save_btn = ctk.CTkButton(button_frame, text="ذخیره", command=save_task, font=font)
        save_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(button_frame, text="انصراف", command=dialog.destroy, font=font, fg_color="gray")
        cancel_btn.pack(side="left", padx=5)
    
    def save_new_task(self, title, description, due_date, priority, category):
        """ذخیره تسک جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tasks (title, description, due_date, priority, completed, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, description, due_date, priority, False, category))
            
            conn.commit()
            conn.close()
            
            # به‌روزرسانی داده‌ها و UI
            self.load_data()
            self.refresh_daily_tasks()
            self.refresh_daily_stats()
            self.refresh_calendar()
            
            # ارسال event
            self.app.event_bus.publish("task_added", {"title": title})
            
            messagebox.showinfo("موفقیت", "تسک جدید با موفقیت اضافه شد")
            
        except Exception as e:
            print(f"❌ خطا در ذخیره تسک: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره تسک: {e}")
    
    def show_add_goal_dialog(self):
        """نمایش دیالوگ اضافه کردن هدف"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("اضافه کردن هدف جدید")
        dialog.geometry("500x500")
        dialog.transient(self)
        dialog.grab_set()
        
        font = self.font_manager.get_font()
        
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(content_frame, text="عنوان هدف:", font=font).pack(anchor="w", pady=(10, 5))
        title_entry = ctk.CTkEntry(content_frame, width=400, font=font)
        title_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="توضیحات:", font=font).pack(anchor="w", pady=(10, 5))
        desc_entry = ctk.CTkTextbox(content_frame, width=400, height=80, font=font)
        desc_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="تاریخ هدف (YYYY-MM-DD):", font=font).pack(anchor="w", pady=(10, 5))
        target_date_entry = ctk.CTkEntry(content_frame, width=400, font=font, placeholder_text="YYYY-MM-DD")
        target_date_entry.pack(fill="x", pady=(0, 10))
        # پیش‌پر کردن با تاریخ 3 ماه بعد
        future_date = datetime.now() + timedelta(days=90)
        target_date_entry.insert(0, future_date.strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(content_frame, text="اولویت:", font=font).pack(anchor="w", pady=(10, 5))
        priority_var = ctk.StringVar(value="medium")
        priority_combo = ctk.CTkComboBox(content_frame, 
                                       values=["low", "medium", "high"],
                                       variable=priority_var,
                                       font=font)
        priority_combo.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="دسته‌بندی:", font=font).pack(anchor="w", pady=(10, 5))
        category_entry = ctk.CTkEntry(content_frame, width=400, font=font, placeholder_text="اختیاری")
        category_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="پیشرفت اولیه (%):", font=font).pack(anchor="w", pady=(10, 5))
        progress_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 10))
        
        progress_var = ctk.IntVar(value=0)
        progress_slider = ctk.CTkSlider(progress_frame, from_=0, to=100, variable=progress_var)
        progress_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        progress_label = ctk.CTkLabel(progress_frame, text="0%", font=font, width=40)
        progress_label.pack(side="right")
        
        def update_progress_label(value):
            progress_label.configure(text=f"{int(value)}%")
        
        progress_slider.configure(command=update_progress_label)
        
        def save_goal():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "لطفاً عنوان هدف را وارد کنید")
                return
                
            self.save_new_goal(
                title_entry.get().strip(),
                desc_entry.get("1.0", "end-1c").strip(),
                target_date_entry.get().strip(),
                progress_var.get(),
                priority_var.get(),
                category_entry.get().strip()
            )
            dialog.destroy()
        
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        save_btn = ctk.CTkButton(button_frame, text="ذخیره", command=save_goal, font=font)
        save_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(button_frame, text="انصراف", command=dialog.destroy, font=font, fg_color="gray")
        cancel_btn.pack(side="left", padx=5)
    
    def save_new_goal(self, title, description, target_date, progress, priority, category):
        """ذخیره هدف جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO goals (title, description, target_date, progress, priority, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, description, target_date, progress, priority, category))
            
            conn.commit()
            conn.close()
            
            # به‌روزرسانی داده‌ها و UI
            self.load_data()
            self.refresh_goals_list()
            
            # ارسال event
            self.app.event_bus.publish("goal_added", {"title": title})
            
            messagebox.showinfo("موفقیت", "هدف جدید با موفقیت اضافه شد")
            
        except Exception as e:
            print(f"❌ خطا در ذخیره هدف: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره هدف: {e}")
    
    def show_add_plan_dialog(self):
        """نمایش دیالوگ اضافه کردن پلن"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("اضافه کردن پلن جدید")
        dialog.geometry("500x500")
        dialog.transient(self)
        dialog.grab_set()
        
        font = self.font_manager.get_font()
        
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(content_frame, text="عنوان پلن:", font=font).pack(anchor="w", pady=(10, 5))
        title_entry = ctk.CTkEntry(content_frame, width=400, font=font)
        title_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="توضیحات:", font=font).pack(anchor="w", pady=(10, 5))
        desc_entry = ctk.CTkTextbox(content_frame, width=400, height=80, font=font)
        desc_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="تاریخ شروع (YYYY-MM-DD):", font=font).pack(anchor="w", pady=(10, 5))
        start_date_entry = ctk.CTkEntry(content_frame, width=400, font=font, placeholder_text="YYYY-MM-DD")
        start_date_entry.pack(fill="x", pady=(0, 10))
        start_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(content_frame, text="تاریخ پایان (YYYY-MM-DD):", font=font).pack(anchor="w", pady=(10, 5))
        end_date_entry = ctk.CTkEntry(content_frame, width=400, font=font, placeholder_text="YYYY-MM-DD")
        end_date_entry.pack(fill="x", pady=(0, 10))
        future_date = datetime.now() + timedelta(days=30)
        end_date_entry.insert(0, future_date.strftime('%Y-%m-%d'))
        
        ctk.CTkLabel(content_frame, text="رنگ پلن:", font=font).pack(anchor="w", pady=(10, 5))
        color_var = ctk.StringVar(value="#2196F3")
        color_combo = ctk.CTkComboBox(content_frame, 
                                    values=["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#607D8B"],
                                    variable=color_var,
                                    font=font)
        color_combo.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(content_frame, text="پیشرفت اولیه (%):", font=font).pack(anchor="w", pady=(10, 5))
        progress_var = ctk.IntVar(value=0)
        progress_slider = ctk.CTkSlider(content_frame, from_=0, to=100, variable=progress_var)
        progress_slider.pack(fill="x", pady=(0, 10))
        
        def save_plan():
            if not title_entry.get().strip():
                messagebox.showerror("خطا", "لطفاً عنوان پلن را وارد کنید")
                return
                
            self.save_new_plan(
                title_entry.get().strip(),
                desc_entry.get("1.0", "end-1c").strip(),
                start_date_entry.get().strip(),
                end_date_entry.get().strip(),
                color_var.get(),
                progress_var.get()
            )
            dialog.destroy()
        
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        save_btn = ctk.CTkButton(button_frame, text="ذخیره", command=save_plan, font=font)
        save_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(button_frame, text="انصراف", command=dialog.destroy, font=font, fg_color="gray")
        cancel_btn.pack(side="left", padx=5)
    
    def save_new_plan(self, title, description, start_date, end_date, color, progress):
        """ذخیره پلن جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO plans (title, description, start_date, end_date, color, completed, progress)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, start_date, end_date, color, False, progress))
            
            conn.commit()
            conn.close()
            
            # به‌روزرسانی داده‌ها و UI
            self.load_data()
            self.refresh_plans_list()
            
            # ارسال event
            self.app.event_bus.publish("plan_added", {"title": title})
            
            messagebox.showinfo("موفقیت", "پلن جدید با موفقیت اضافه شد")
            
        except Exception as e:
            print(f"❌ خطا در ذخیره پلن: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره پلن: {e}")
    
    def toggle_task_completion(self, task_id):
        """تغییر وضعیت تکمیل تسک"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE tasks SET completed = NOT completed WHERE id = ?
            ''', (task_id,))
            
            conn.commit()
            conn.close()
            
            self.load_data()
            self.refresh_daily_tasks()
            self.refresh_daily_stats()
            self.refresh_calendar()
            
            self.app.event_bus.publish("task_completed", {"task_id": task_id})
            
        except Exception as e:
            print(f"❌ خطا در تغییر وضعیت تسک: {e}")
            messagebox.showerror("خطا", f"خطا در تغییر وضعیت تسک: {e}")
    
    def prev_month(self):
        """ماه قبل"""
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.current_date = self.current_date.replace(day=1)
        self.refresh_calendar()
        self.month_year_label.configure(text=self.get_persian_month_year())
    
    def next_month(self):
        """ماه بعد"""
        next_month = self.current_date.month % 12 + 1
        next_year = self.current_date.year + (1 if next_month == 1 else 0)
        self.current_date = self.current_date.replace(month=next_month, year=next_year, day=1)
        self.refresh_calendar()
        self.month_year_label.configure(text=self.get_persian_month_year())
    
    def go_to_today(self):
        """برو به امروز"""
        self.current_date = datetime.now()
        self.refresh_calendar()
        self.month_year_label.configure(text=self.get_persian_month_year())
    
    def on_font_changed(self, data):
        """واکنش به تغییر فونت"""
        try:
            self.after(100, self.update_fonts)
        except Exception as e:
            print(f"⚠️ خطا در تغییر فونت برنامه‌ریزی: {e}")
    
    def on_task_changed(self, data):
        """واکنش به تغییر تسک"""
        self.load_data()
        self.refresh_daily_tasks()
        self.refresh_daily_stats()
        self.refresh_calendar()
    
    def on_goal_changed(self, data):
        """واکنش به تغییر هدف"""
        self.load_data()
        self.refresh_goals_list()
    
    def on_plan_changed(self, data):
        """واکنش به تغییر پلن"""
        self.load_data()
        self.refresh_plans_list()
    
    def update_fonts(self):
        """به‌روزرسانی فونت‌ها"""
        # این متد باید فونت تمام ویجت‌ها را به‌روزرسانی کند
        # برای سادگی، کل UI را بازسازی می‌کنیم
        self.setup_ui()