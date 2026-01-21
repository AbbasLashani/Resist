import customtkinter as ctk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
import json
import os

class DashboardModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app
        self.config = config
        
        # پیدا کردن language_manager و font_manager
        if hasattr(app, 'language_manager'):
            self.language_manager = app.language_manager
        elif hasattr(app, 'language'):
            self.language_manager = app.language
            
        if hasattr(app, 'font_manager'):
            self.font_manager = app.font_manager
        else:
            from core.font_manager import FontManager
            self.font_manager = FontManager(config)
        
        # داده‌های event handling
        self.activity_logs = []
        self.is_ui_built = False
        self.font_widgets = []  # لیست ویجت‌هایی که فونت دارند
        self.current_date = datetime.now()
        
        # آمار واقعی از دیتابیس
        self.stats_data = {
            'articles': 0,
            'datasheets': 0,
            'notes': 0,
            'tasks': 0,
            'goals': 0,
            'plans': 0
        }
        
        # ثبت event listeners با مدیریت بهتر
        self.setup_event_listeners()
        
        # بارگذاری داده‌های واقعی
        self.load_real_stats()
        
        # ایجاد UI
        self.setup_ui()
    
    def load_real_stats(self):
        """بارگذاری آمار واقعی از دیتابیس"""
        try:
            # اتصال به دیتابیس
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            # بررسی وجود جداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"📊 جداول موجود در دیتابیس: {tables}")
            
            # تعداد مقالات
            if 'articles' in tables:
                cursor.execute('SELECT COUNT(*) FROM articles')
                self.stats_data['articles'] = cursor.fetchone()[0]
            else:
                self.stats_data['articles'] = 0
                print("⚠️ جدول articles وجود ندارد")
            
            # تعداد دیتاشیت‌ها
            if 'datasheets' in tables:
                cursor.execute('SELECT COUNT(*) FROM datasheets')
                self.stats_data['datasheets'] = cursor.fetchone()[0]
            else:
                self.stats_data['datasheets'] = 0
                print("⚠️ جدول datasheets وجود ندارد")
            
            # تعداد یادداشت‌ها
            if 'notes' in tables:
                cursor.execute('SELECT COUNT(*) FROM notes')
                notes_result = cursor.fetchone()
                self.stats_data['notes'] = notes_result[0] if notes_result else 0
            else:
                self.stats_data['notes'] = 0
            
            # تعداد وظایف
            if 'tasks' in tables:
                cursor.execute('SELECT COUNT(*) FROM tasks WHERE completed = 0')
                tasks_result = cursor.fetchone()
                self.stats_data['tasks'] = tasks_result[0] if tasks_result else 0
            else:
                self.stats_data['tasks'] = 0
            
            # تعداد اهداف
            if 'goals' in tables:
                cursor.execute('SELECT COUNT(*) FROM goals')
                goals_result = cursor.fetchone()
                self.stats_data['goals'] = goals_result[0] if goals_result else 0
            else:
                self.stats_data['goals'] = 0
            
            # تعداد پلن‌ها
            if 'plans' in tables:
                cursor.execute('SELECT COUNT(*) FROM plans')
                plans_result = cursor.fetchone()
                self.stats_data['plans'] = plans_result[0] if plans_result else 0
            else:
                self.stats_data['plans'] = 0
            
            conn.close()
            
            print(f"📊 آمار واقعی بارگذاری شد: {self.stats_data}")
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری آمار واقعی: {e}")
            # استفاده از مقادیر پیش‌فرض در صورت خطا
            self.stats_data = {'articles': 0, 'datasheets': 0, 'notes': 0, 'tasks': 0, 'goals': 0, 'plans': 0}
    
    def get_recent_activities(self):
        """دریافت فعالیت‌های اخیر از دیتابیس"""
        activities = []
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            # بررسی وجود جداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            
            # فعالیت‌های مقالات
            if 'articles' in tables:
                cursor.execute('''
                    SELECT 'article' as type, title, created_at 
                    FROM articles 
                    ORDER BY created_at DESC 
                    LIMIT 3
                ''')
                articles = cursor.fetchall()
                
                for article in articles:
                    activities.append({
                        'type': 'article',
                        'message': f'مقاله جدید: {article[1]}',
                        'timestamp': datetime.strptime(article[2], '%Y-%m-%d %H:%M:%S') if isinstance(article[2], str) else article[2],
                        'icon': '📄'
                    })
            
            # فعالیت‌های دیتاشیت‌ها
            if 'datasheets' in tables:
                cursor.execute('''
                    SELECT 'datasheet' as type, name, created_at 
                    FROM datasheets 
                    ORDER BY created_at DESC 
                    LIMIT 3
                ''')
                datasheets = cursor.fetchall()
                
                for datasheet in datasheets:
                    activities.append({
                        'type': 'datasheet',
                        'message': f'دیتاشیت جدید: {datasheet[1]}',
                        'timestamp': datetime.strptime(datasheet[2], '%Y-%m-%d %H:%M:%S') if isinstance(datasheet[2], str) else datasheet[2],
                        'icon': '📋'
                    })
            
            # فعالیت‌های تسک‌ها
            if 'tasks' in tables:
                cursor.execute('''
                    SELECT 'task' as type, title, created_at 
                    FROM tasks 
                    ORDER BY created_at DESC 
                    LIMIT 2
                ''')
                tasks = cursor.fetchall()
                
                for task in tasks:
                    activities.append({
                        'type': 'task',
                        'message': f'تسک جدید: {task[1]}',
                        'timestamp': datetime.strptime(task[2], '%Y-%m-%d %H:%M:%S') if isinstance(task[2], str) else task[2],
                        'icon': '✅'
                    })
            
            conn.close()
            
            # مرتب‌سازی بر اساس زمان
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            return activities[:5]  # 5 فعالیت اخیر
            
        except Exception as e:
            print(f"❌ خطا در دریافت فعالیت‌های اخیر: {e}")
            return []
    
    def get_category_distribution(self):
        """دریافت توزیع دسته‌بندی‌ها"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            # بررسی وجود جداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            
            distribution = {'articles': {}, 'datasheets': {}}
            
            # توزیع دسته‌بندی مقالات
            if 'articles' in tables:
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM articles 
                    GROUP BY category
                ''')
                article_categories = cursor.fetchall()
                distribution['articles'] = dict(article_categories)
            
            # توزیع دسته‌بندی دیتاشیت‌ها
            if 'datasheets' in tables:
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM datasheets 
                    GROUP BY category
                ''')
                datasheet_categories = cursor.fetchall()
                distribution['datasheets'] = dict(datasheet_categories)
            
            conn.close()
            
            return distribution
            
        except Exception as e:
            print(f"❌ خطا در دریافت توزیع دسته‌بندی‌ها: {e}")
            return {'articles': {}, 'datasheets': {}}
    
    def get_today_tasks(self):
        """دریافت تسک‌های امروز"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT id, title, completed 
                FROM tasks 
                WHERE due_date = ? AND completed = 0
                ORDER BY priority DESC
                LIMIT 5
            ''', (today,))
            
            tasks = cursor.fetchall()
            conn.close()
            return tasks
            
        except Exception as e:
            print(f"❌ خطا در دریافت تسک‌های امروز: {e}")
            return []
    
    def get_active_goals(self):
        """دریافت اهداف فعال"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, target_date, progress 
                FROM goals 
                WHERE progress < 100
                ORDER BY target_date
                LIMIT 3
            ''')
            
            goals = cursor.fetchall()
            conn.close()
            return goals
            
        except Exception as e:
            print(f"❌ خطا در دریافت اهداف فعال: {e}")
            return []
    
    def setup_event_listeners(self):
        """تنظیم شنوندگان رویداد با مدیریت خطا"""
        try:
            # لغو اشتراک قبلی برای جلوگیری از duplicate
            self.app.event_bus.unsubscribe("font_changed", self.on_font_changed)
            self.app.event_bus.unsubscribe("settings_changed", self.on_settings_changed)
            self.app.event_bus.unsubscribe("article_added", self.on_content_changed)
            self.app.event_bus.unsubscribe("datasheet_added", self.on_content_changed)
            self.app.event_bus.unsubscribe("task_added", self.on_task_changed)
            self.app.event_bus.unsubscribe("task_completed", self.on_task_changed)
            self.app.event_bus.unsubscribe("goal_added", self.on_goal_changed)
            
            # ثبت مجدد
            self.app.event_bus.subscribe("font_changed", self.on_font_changed)
            self.app.event_bus.subscribe("settings_changed", self.on_settings_changed)
            self.app.event_bus.subscribe("article_added", self.on_content_changed)
            self.app.event_bus.subscribe("datasheet_added", self.on_content_changed)
            self.app.event_bus.subscribe("task_added", self.on_task_changed)
            self.app.event_bus.subscribe("task_completed", self.on_task_changed)
            self.app.event_bus.subscribe("goal_added", self.on_goal_changed)
            print("✅ Event listeners برای داشبورد ثبت شدند")
        except Exception as e:
            print(f"⚠️ خطا در ثبت event listeners داشبورد: {e}")
    
    def on_content_changed(self, data):
        """واکنش به تغییر محتوا (مقاله یا دیتاشیت جدید)"""
        try:
            print("🔄 دریافت تغییر محتوا در داشبورد")
            # بارگذاری مجدد آمار و تازه‌سازی UI
            self.load_real_stats()
            if self.is_ui_built:
                self.refresh_stats_cards()
                self.refresh_activities_list()
                self.refresh_chart()
        except Exception as e:
            print(f"⚠️ خطا در مدیریت تغییر محتوا: {e}")
    
    def on_task_changed(self, data):
        """واکنش به تغییر تسک"""
        try:
            print("🔄 دریافت تغییر تسک در داشبورد")
            self.load_real_stats()
            if self.is_ui_built:
                self.refresh_stats_cards()
                self.refresh_planning_overview()
        except Exception as e:
            print(f"⚠️ خطا در مدیریت تغییر تسک: {e}")
    
    def on_goal_changed(self, data):
        """واکنش به تغییر هدف"""
        try:
            print("🔄 دریافت تغییر هدف در داشبورد")
            self.load_real_stats()
            if self.is_ui_built:
                self.refresh_stats_cards()
                self.refresh_planning_overview()
        except Exception as e:
            print(f"⚠️ خطا در مدیریت تغییر هدف: {e}")
    
    def on_settings_changed(self, data):
        """واکنش به تغییر تنظیمات"""
        try:
            print("🔄 دریافت تنظیمات جدید در داشبورد")
            
            # اگر فونت تغییر کرده
            if "font_size" in data or "font_family" in data:
                self.after(100, self.safe_delayed_font_update)
                
        except Exception as e:
            print(f"⚠️ خطا در مدیریت تنظیمات داشبورد: {e}")
    
    def on_font_changed(self, data):
        """واکنش به تغییر فونت - کاملاً ایمن"""
        try:
            if not self.winfo_exists():
                return
                
            print("🔤 دریافت درخواست تغییر فونت در داشبورد")
            
            # تأخیر برای اطمینان از ثبات
            self.after(50, self.safe_delayed_font_update)
            
        except Exception as e:
            print(f"⚠️ خطا در مدیریت تغییر فونت داشبورد: {e}")

    def safe_delayed_font_update(self):
        """آپدیت فونت با تأخیر ایمن"""
        try:
            if not self.winfo_exists():
                return
                
            print("🔤 اجرای آپدیت فونت در داشبورد")
            self.update_all_fonts()
            
        except Exception as e:
            print(f"⚠️ خطا در آپدیت فونت با تأخیر: {e}")

    def update_all_fonts(self):
        """به روزرسانی تمام فونت‌ها در داشبورد"""
        try:
            if not self.winfo_exists():
                return
                
            print("🔤 آپدیت تمام فونت‌های داشبورد...")
            
            # آپدیت تمام ویجت‌های ثبت شده
            for widget_info in self.font_widgets:
                try:
                    widget = widget_info['widget']
                    font_type = widget_info['font_type']
                    
                    if widget.winfo_exists():
                        if font_type == "title":
                            new_font = self.font_manager.get_font(size=16, weight="bold")
                        elif font_type == "heading":
                            new_font = self.font_manager.get_font(size=14, weight="bold")
                        elif font_type == "small":
                            new_font = self.font_manager.get_font(size=10)
                        else:
                            new_font = self.font_manager.get_font()
                        
                        widget.configure(font=new_font)
                except Exception as e:
                    continue
            
            print(f"✅ {len(self.font_widgets)} فونت در داشبورد به روز شدند")
            
        except Exception as e:
            print(f"⚠️ خطا در آپدیت فونت داشبورد: {e}")
    
    def register_font_widget(self, widget, font_type="normal"):
        """ثبت ویجت برای مدیریت فونت"""
        self.font_widgets.append({
            'widget': widget,
            'font_type': font_type
        })
    
    def setup_ui(self):
        """ایجاد رابط کاربری داشبورد - نسخه بهبود یافته با برنامه‌ریزی"""
        if self.is_ui_built:
            return
            
        print("🔧 ایجاد UI داشبورد جدید...")
        
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except:
                pass
        
        self.font_widgets = []  # ریست لیست فونت‌ها
        
        # استفاده از Grid برای چیدمان دقیق
        self.grid_rowconfigure(0, weight=0)  # عنوان
        self.grid_rowconfigure(1, weight=1)  # محتوای اصلی
        self.grid_columnconfigure(0, weight=1)
        
        # عنوان داشبورد
        title_text = "📊 داشبورد اصلی" if self.language_manager.is_rtl() else "📊 Main Dashboard"
        self.title_label = ctk.CTkLabel(
            self,
            text=title_text,
            font=self.font_manager.get_font(size=18, weight="bold"),
            height=50
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.register_font_widget(self.title_label, "title")
        
        # فریم اصلی
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # تنظیم Grid برای فریم اصلی (2 ردیف، 2 ستون)
        self.main_frame.grid_rowconfigure(0, weight=0)  # آمار
        self.main_frame.grid_rowconfigure(1, weight=1)  # محتوای پایین
        self.main_frame.grid_columnconfigure(0, weight=2)  # ستون چپ (فعالیت‌ها و نمودار)
        self.main_frame.grid_columnconfigure(1, weight=1)  # ستون راست (برنامه‌ریزی و تقویم)
        
        # ایجاد بخش‌های مختلف
        self.create_stats_section()
        self.create_activities_section()
        self.create_planning_section()
        
        self.is_ui_built = True
        print("✅ UI داشبورد جدید با موفقیت ایجاد شد")
    
    def create_stats_section(self):
        """ایجاد بخش آمار - نسخه گسترده با 6 آیتم"""
        stats_frame = ctk.CTkFrame(self.main_frame, corner_radius=15, height=120)
        stats_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        stats_frame.grid_propagate(False)
        
        # 6 ستون برای آمار جدید
        for i in range(6):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # کارت‌های آمار با داده‌های جدید
        stats_cards = [
            {
                "title": "مقالات", 
                "count": self.stats_data['articles'], 
                "icon": "📄", 
                "color": "#2196F3",
                "description": "مقاله علمی"
            },
            {
                "title": "دیتاشیت‌ها", 
                "count": self.stats_data['datasheets'], 
                "icon": "📋", 
                "color": "#4CAF50",
                "description": "دیتاشیت فنی"
            },
            {
                "title": "یادداشت‌ها", 
                "count": self.stats_data['notes'], 
                "icon": "📝", 
                "color": "#FF9800",
                "description": "یادداشت شخصی"
            },
            {
                "title": "وظایف", 
                "count": self.stats_data['tasks'], 
                "icon": "⏰", 
                "color": "#9C27B0",
                "description": "وظیفه فعال"
            },
            {
                "title": "اهداف", 
                "count": self.stats_data['goals'], 
                "icon": "🎯", 
                "color": "#F44336",
                "description": "هدف تعریف شده"
            },
            {
                "title": "پلن‌ها", 
                "count": self.stats_data['plans'], 
                "icon": "📊", 
                "color": "#607D8B",
                "description": "پلن فعال"
            }
        ]
        
        for i, stat in enumerate(stats_cards):
            stat_card = self.create_stat_card(stats_frame, stat, i)
            stat_card.grid(row=0, column=i, padx=5, pady=15, sticky="nsew")
    
    def create_stat_card(self, parent, stat, index):
        """ایجاد کارت آمار"""
        card = ctk.CTkFrame(
            parent, 
            corner_radius=12,
            fg_color=("#E3F2FD", "#1A237E"),
            border_color=stat["color"],
            border_width=2,
        )
        
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # ردیف بالا: آیکون و عدد
        top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 8))
        
        # آیکون
        icon_label = ctk.CTkLabel(
            top_frame,
            text=stat["icon"],
            font=self.font_manager.get_font(size=20),
            text_color=stat["color"],
            width=40
        )
        self.register_font_widget(icon_label)
        
        # عدد
        count_label = ctk.CTkLabel(
            top_frame,
            text=str(stat["count"]),
            font=self.font_manager.get_font(size=24, weight="bold"),
            text_color=stat["color"]
        )
        self.register_font_widget(count_label, "heading")
        
        # ردیف پایین: عنوان و توضیحات
        bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        bottom_frame.pack(fill="x")
        
        title_label = ctk.CTkLabel(
            bottom_frame,
            text=stat["title"],
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        self.register_font_widget(title_label)
        
        desc_label = ctk.CTkLabel(
            bottom_frame,
            text=stat["description"],
            font=self.font_manager.get_font(size=10),
            text_color=("#666666", "#AAAAAA")
        )
        self.register_font_widget(desc_label, "small")
        
        # چیدمان بر اساس RTL/LTR
        if self.language_manager.is_rtl():
            icon_label.pack(side="right")
            count_label.pack(side="right", padx=(10, 0))
            title_label.pack(side="right", anchor="e")
            desc_label.pack(side="right", anchor="e")
        else:
            icon_label.pack(side="left")
            count_label.pack(side="left", padx=(10, 0))
            title_label.pack(side="left", anchor="w")
            desc_label.pack(side="left", anchor="w")
        
        return card
    
    def create_activities_section(self):
        """ایجاد بخش فعالیت‌ها و نمودار در ستون چپ"""
        # فریم سمت چپ
        left_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        left_frame.grid_rowconfigure(0, weight=1)  # فعالیت‌ها
        left_frame.grid_rowconfigure(1, weight=1)  # نمودار
        left_frame.grid_columnconfigure(0, weight=1)
        
        # بخش فعالیت‌ها
        activities_frame = ctk.CTkFrame(left_frame, corner_radius=12)
        activities_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        activities_title = ctk.CTkLabel(
            activities_frame,
            text="📈 فعالیت‌های اخیر" if self.language_manager.is_rtl() else "📈 Recent Activities",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        activities_title.pack(pady=15)
        self.register_font_widget(activities_title, "heading")
        
        # محتوای فعالیت‌ها
        self.activities_content = ctk.CTkScrollableFrame(activities_frame, fg_color="transparent", height=200)
        self.activities_content.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_activities_list()
        
        # بخش نمودار
        chart_frame = ctk.CTkFrame(left_frame, corner_radius=12)
        chart_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        chart_title = ctk.CTkLabel(
            chart_frame,
            text="📊 توزیع محتوا" if self.language_manager.is_rtl() else "📊 Content Distribution",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        chart_title.pack(pady=15)
        self.register_font_widget(chart_title, "heading")
        
        # ایجاد فریم برای نمودار
        self.chart_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_chart()
    
    def create_planning_section(self):
        """ایجاد بخش برنامه‌ریزی و تقویم در ستون راست"""
        # فریم سمت راست
        right_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        
        right_frame.grid_rowconfigure(0, weight=1)  # برنامه‌ریزی
        right_frame.grid_rowconfigure(1, weight=1)  # تقویم
        right_frame.grid_columnconfigure(0, weight=1)
        
        # بخش برنامه‌ریزی
        planning_frame = ctk.CTkFrame(right_frame, corner_radius=12)
        planning_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        planning_title = ctk.CTkLabel(
            planning_frame,
            text="📅 خلاصه برنامه‌ریزی" if self.language_manager.is_rtl() else "📅 Planning Overview",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        planning_title.pack(pady=15)
        self.register_font_widget(planning_title, "heading")
        
        # محتوای برنامه‌ریزی
        self.planning_content = ctk.CTkScrollableFrame(planning_frame, fg_color="transparent", height=200)
        self.planning_content.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.refresh_planning_overview()
        
        # بخش تقویم
        calendar_frame = ctk.CTkFrame(right_frame, corner_radius=12)
        calendar_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        calendar_title = ctk.CTkLabel(
            calendar_frame,
            text="📅 تقویم" if self.language_manager.is_rtl() else "📅 Calendar",
            font=self.font_manager.get_font(size=14, weight="bold")
        )
        calendar_title.pack(pady=15)
        self.register_font_widget(calendar_title, "heading")
        
        # نمایش ماه جاری
        month_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
        month_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # نمایش تقویم فشرده
        self.create_mini_calendar(month_frame)
    
    def create_mini_calendar(self, parent):
        """ایجاد تقویم کوچک"""
        # هدر ماه
        month_header = ctk.CTkFrame(parent, fg_color="transparent")
        month_header.pack(fill="x", pady=(0, 10))
        
        month_text = self.get_persian_month_year()
        month_label = ctk.CTkLabel(
            month_header,
            text=month_text,
            font=self.font_manager.get_font(weight="bold")
        )
        month_label.pack()
        self.register_font_widget(month_label)
        
        # روزهای هفته
        days_frame = ctk.CTkFrame(parent, fg_color="transparent")
        days_frame.pack(fill="x")
        
        days = ["ش", "ی", "د", "س", "چ", "پ", "ج"] if self.language_manager.is_rtl() else ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
        
        for i, day in enumerate(days):
            day_label = ctk.CTkLabel(
                days_frame,
                text=day,
                font=self.font_manager.get_font(size=10, weight="bold"),
                width=30,
                height=25
            )
            day_label.grid(row=0, column=i, padx=1, pady=1)
            self.register_font_widget(day_label, "small")
        
        # روزهای ماه
        first_day = self.current_date.replace(day=1)
        start_day = first_day - timedelta(days=first_day.weekday())
        
        for week in range(6):
            for day in range(7):
                current_date = start_day + timedelta(days=week*7 + day)
                self.create_mini_calendar_day(days_frame, current_date, week+1, day)
    
    def create_mini_calendar_day(self, parent, date, week, day):
        """ایجاد یک روز در تقویم کوچک"""
        is_today = date.date() == datetime.now().date()
        is_current_month = date.month == self.current_date.month
        
        bg_color = "#2196F3" if is_today else ("#F5F5F5" if is_current_month else "#E0E0E0")
        text_color = "#FFFFFF" if is_today else ("#000000" if is_current_month else "#CCCCCC")
        
        day_frame = ctk.CTkFrame(
            parent,
            fg_color=bg_color,
            corner_radius=12,
            width=30,
            height=30
        )
        day_frame.grid(row=week, column=day, padx=1, pady=1)
        day_frame.grid_propagate(False)
        
        day_label = ctk.CTkLabel(
            day_frame,
            text=str(date.day),
            font=self.font_manager.get_font(size=10),
            text_color=text_color
        )
        day_label.place(relx=0.5, rely=0.5, anchor="center")
        self.register_font_widget(day_label, "small")
    
    def get_persian_month_year(self):
        """دریافت ماه و سال به شمسی"""
        months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", 
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        month = months[self.current_date.month - 1]
        year = self.current_date.year
        return f"{month} {year}"
    
    def refresh_activities_list(self):
        """تازه‌سازی لیست فعالیت‌ها با داده‌های واقعی"""
        # پاک کردن فعالیت‌های قبلی
        for widget in self.activities_content.winfo_children():
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except:
                pass
        
        activities = self.get_recent_activities()
        
        if not activities:
            empty_text = "📭 هیچ فعالیتی ثبت نشده است" if self.language_manager.is_rtl() else "📭 No activities recorded"
            empty_label = ctk.CTkLabel(
                self.activities_content,
                text=empty_text,
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(expand=True, pady=20)
            self.register_font_widget(empty_label)
        else:
            for activity in activities:
                self.create_activity_item(activity)
    
    def create_activity_item(self, activity):
        """ایجاد آیتم فعالیت"""
        activity_frame = ctk.CTkFrame(self.activities_content, fg_color=("#F5F5F5", "#2A2A2A"), corner_radius=8, height=50)
        activity_frame.pack(fill="x", pady=3)
        activity_frame.pack_propagate(False)
        
        content_frame = ctk.CTkFrame(activity_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=12, pady=8)
        
        icon = activity["icon"]
        message = activity["message"]
        time_text = self.format_timestamp(activity["timestamp"])
        
        # ایجاد ویجت‌ها
        icon_label = ctk.CTkLabel(content_frame, text=icon, font=self.font_manager.get_font(size=14), width=25)
        self.register_font_widget(icon_label)
        
        message_label = ctk.CTkLabel(
            content_frame, 
            text=message, 
            font=self.font_manager.get_font(size=11),
            wraplength=200,
            justify="right" if self.language_manager.is_rtl() else "left"
        )
        self.register_font_widget(message_label, "small")
        
        time_label = ctk.CTkLabel(
            content_frame, 
            text=time_text, 
            font=self.font_manager.get_font(size=10), 
            text_color=("#666666", "#AAAAAA"), 
            width=40
        )
        self.register_font_widget(time_label, "small")
        
        if self.language_manager.is_rtl():
            time_label.pack(side="right", padx=(5, 0))
            message_label.pack(side="right", fill="x", expand=True, padx=8)
            icon_label.pack(side="right", padx=(0, 5))
        else:
            icon_label.pack(side="left", padx=(0, 5))
            message_label.pack(side="left", fill="x", expand=True, padx=8)
            time_label.pack(side="left", padx=(5, 0))
    
    def refresh_planning_overview(self):
        """تازه‌سازی نمای کلی برنامه‌ریزی"""
        # پاک کردن محتوای قبلی
        for widget in self.planning_content.winfo_children():
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except:
                pass
        
        # امروز
        today_section = ctk.CTkFrame(self.planning_content, fg_color=("#F0F8FF", "#1E1E1E"), corner_radius=8)
        today_section.pack(fill="x", pady=5)
        
        today_title = ctk.CTkLabel(
            today_section,
            text="📝 امروز",
            font=self.font_manager.get_font(weight="bold")
        )
        today_title.pack(anchor="w" if not self.language_manager.is_rtl() else "e", padx=10, pady=5)
        self.register_font_widget(today_title)
        
        today_tasks = self.get_today_tasks()
        if today_tasks:
            for task in today_tasks[:3]:  # فقط 3 تسک اول
                task_text = f"• {task[1]}"
                task_label = ctk.CTkLabel(
                    today_section,
                    text=task_text,
                    font=self.font_manager.get_font(size=11),
                    wraplength=200,
                    justify="left" if not self.language_manager.is_rtl() else "right"
                )
                task_label.pack(anchor="w" if not self.language_manager.is_rtl() else "e", padx=20, pady=2)
                self.register_font_widget(task_label, "small")
        else:
            empty_label = ctk.CTkLabel(
                today_section,
                text="✅ هیچ تسکی برای امروز",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(anchor="w" if not self.language_manager.is_rtl() else "e", padx=20, pady=5)
            self.register_font_widget(empty_label, "small")
        
        # اهداف فعال
        goals_section = ctk.CTkFrame(self.planning_content, fg_color=("#FFF8E1", "#2A2A2A"), corner_radius=8)
        goals_section.pack(fill="x", pady=5)
        
        goals_title = ctk.CTkLabel(
            goals_section,
            text="🎯 اهداف فعال",
            font=self.font_manager.get_font(weight="bold")
        )
        goals_title.pack(anchor="w" if not self.language_manager.is_rtl() else "e", padx=10, pady=5)
        self.register_font_widget(goals_title)
        
        active_goals = self.get_active_goals()
        if active_goals:
            for goal in active_goals[:2]:  # فقط 2 هدف اول
                goal_text = f"• {goal[1]} ({goal[3]}%)"
                goal_label = ctk.CTkLabel(
                    goals_section,
                    text=goal_text,
                    font=self.font_manager.get_font(size=11),
                    wraplength=200,
                    justify="left" if not self.language_manager.is_rtl() else "right"
                )
                goal_label.pack(anchor="w" if not self.language_manager.is_rtl() else "e", padx=20, pady=2)
                self.register_font_widget(goal_label, "small")
        else:
            empty_label = ctk.CTkLabel(
                goals_section,
                text="🎯 هدف فعالی وجود ندارد",
                font=self.font_manager.get_font(size=11),
                text_color=("#666666", "#AAAAAA")
            )
            empty_label.pack(anchor="w" if not self.language_manager.is_rtl() else "e", padx=20, pady=5)
            self.register_font_widget(empty_label, "small")
    
    def refresh_chart(self):
        """تازه‌سازی نمودار با داده‌های واقعی"""
        # پاک کردن نمودار قبلی
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        try:
            distribution = self.get_category_distribution()
            
            # ترکیب داده‌های مقالات و دیتاشیت‌ها
            all_categories = {}
            for category, count in distribution['articles'].items():
                all_categories[category] = all_categories.get(category, 0) + count
            for category, count in distribution['datasheets'].items():
                all_categories[category] = all_categories.get(category, 0) + count
            
            if not all_categories:
                # اگر هیچ داده‌ای وجود نداشت، پیام نشان بده
                empty_text = "📊 هیچ داده‌ای برای نمایش موجود نیست" if self.language_manager.is_rtl() else "📊 No data available for chart"
                empty_label = ctk.CTkLabel(
                    self.chart_container, 
                    text=empty_text,
                    font=self.font_manager.get_font(),
                    text_color=("#666666", "#AAAAAA")
                )
                empty_label.pack(expand=True, pady=20)
                self.register_font_widget(empty_label)
                return
            
            # ایجاد نمودار
            fig, ax = plt.subplots(figsize=(5, 3))
            
            categories = list(all_categories.keys())
            counts = list(all_categories.values())
            
            colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#F44336', '#607D8B']
            
            bars = ax.bar(categories, counts, color=colors[:len(categories)])
            
            # تنظیمات نمودار
            ax.set_ylabel('تعداد' if self.language_manager.is_rtl() else 'Count')
            ax.set_facecolor('#f8f9fa')
            fig.patch.set_facecolor('#f8f9fa')
            
            # چرخش برچسب‌ها برای خوانایی بهتر
            plt.xticks(rotation=45, ha='right')
            
            # تنظیم فونت برای پشتیبانی از فارسی
            if self.language_manager.is_rtl():
                plt.rcParams['font.family'] = 'DejaVu Sans'
            
            plt.tight_layout()
            
            # نمایش نمودار در Tkinter
            canvas = FigureCanvasTkAgg(fig, self.chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"❌ خطا در ایجاد نمودار: {e}")
            error_text = "📉 خطا در نمایش نمودار" if self.language_manager.is_rtl() else "📉 Chart display error"
            error_label = ctk.CTkLabel(
                self.chart_container, 
                text=error_text, 
                font=self.font_manager.get_font(),
                text_color=("#666666", "#AAAAAA")
            )
            error_label.pack(expand=True, pady=20)
            self.register_font_widget(error_label)
    
    def format_timestamp(self, timestamp):
        """فرمت‌دهی زمان به صورت خوانا"""
        now = datetime.now()
        
        # اگر timestamp یک رشته است، آن را به datetime تبدیل کن
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except:
                return timestamp
        
        diff = now - timestamp
        
        if diff.days > 7:
            return timestamp.strftime("%Y/%m/%d")
        elif diff.days > 0:
            return f"{diff.days} روز پیش"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ساعت پیش"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} دقیقه پیش"
        else:
            return "همین الان"
    
    def refresh_stats_cards(self):
        """تازه‌سازی کارت‌های آمار"""
        # این متد می‌تواند برای به‌روزرسانی کارت‌های آمار بدون بازسازی کامل UI استفاده شود
        pass
    
    def refresh_language(self):
        """تازه‌سازی زبان"""
        print("🔄 تازه‌سازی زبان در داشبورد")
        self.is_ui_built = False
        self.setup_ui()
    
    def __del__(self):
        """تمیزکاری"""
        try:
            self.app.event_bus.unsubscribe("font_changed", self.on_font_changed)
            self.app.event_bus.unsubscribe("settings_changed", self.on_settings_changed)
            self.app.event_bus.unsubscribe("article_added", self.on_content_changed)
            self.app.event_bus.unsubscribe("datasheet_added", self.on_content_changed)
            self.app.event_bus.unsubscribe("task_added", self.on_task_changed)
            self.app.event_bus.unsubscribe("task_completed", self.on_task_changed)
            self.app.event_bus.unsubscribe("goal_added", self.on_goal_changed)
        except:
            pass