# research_assistant/modules/dashboard/dashboard_module.py
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class DashboardModule(ttk.Frame):
    def __init__(self, parent, app, config):
        super().__init__(parent)
        self.app = app
        self.config = config
        self.setup_ui()
        
    def setup_ui(self):
        """ایجاد رابط کاربری داشبورد"""
        # عنوان
        title_label = ttk.Label(
            self,
            text="📊 " + self.config.t("dashboard"),
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # کارت‌های اطلاعاتی
        self.create_info_cards()
        
        # بخش آمار سریع
        self.create_quick_stats()
        
        # دکمه بروزرسانی
        refresh_btn = ttk.Button(
            self, 
            text=self.config.t("refresh_stats"), 
            command=self.refresh_data
        )
        refresh_btn.pack(pady=10)
        
        # بارگذاری اولیه داده‌ها
        self.refresh_data()
        
    def create_info_cards(self):
        """ایجاد کارت‌های اطلاعاتی"""
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill=tk.X, pady=10, padx=20)
        
        # داده‌های نمونه با استفاده از ترجمه‌ها
        self.cards_data = [
            {"title": self.config.t("papers"), "value": "0", "icon": "📄", "color": "#3498db"},
            {"title": self.config.t("study_time"), "value": "0 ساعت", "icon": "⏱️", "color": "#2ecc71"},
            {"title": self.config.t("notes"), "value": "0", "icon": "📝", "color": "#e74c3c"},
            {"title": self.config.t("projects"), "value": "0", "icon": "📁", "color": "#f39c12"}
        ]
        
        self.card_widgets = []
        for i, card in enumerate(self.cards_data):
            card_frame = ttk.Frame(
                cards_frame, 
                relief=tk.RAISED, 
                borderwidth=1,
                padding=10
            )
            
            if i < 2:
                card_frame.grid(row=0, column=i, padx=5, pady=5, sticky='nsew')
            else:
                card_frame.grid(row=1, column=i-2, padx=5, pady=5, sticky='nsew')
                
            cards_frame.columnconfigure(i % 2, weight=1)
            cards_frame.rowconfigure(i // 2, weight=1)
            
            # آیکون و عنوان در یک خط
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
            
            self.card_widgets.append(value_label)
        
    def create_quick_stats(self):
        """ایجاد بخش آمار سریع"""
        stats_frame = ttk.LabelFrame(
            self, 
            text=" " + self.config.t("quick_stats") + " ",
            padding=15
        )
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=20)
        
        # آمار نمونه با استفاده از ترجمه‌ها
        self.stats_data = [
            (self.config.t("read_papers"), "0"),
            (self.config.t("reading_papers"), "0"),
            (self.config.t("planned_papers"), "0"),
            (self.config.t("avg_study_time"), "0 دقیقه")
        ]
        
        self.stat_widgets = []
        for stat_name, stat_value in self.stats_data:
            stat_frame = ttk.Frame(stats_frame)
            stat_frame.pack(fill=tk.X, pady=8)
            
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
            self.stat_widgets.append(value_label)
    
    def refresh_data(self, data=None):
        """به‌روزرسانی داده‌های داشبورد"""
        try:
            # دریافت داده‌های واقعی از پایگاه داده
            papers_count = self.app.db.fetch_one("SELECT COUNT(*) FROM papers")[0] or 0
            notes_count = self.app.db.fetch_one("SELECT COUNT(*) FROM notes")[0] or 0
            
            # محاسبه زمان مطالعه کل
            total_time = self.app.db.fetch_one("SELECT SUM(time_spent) FROM study_plans")[0] or 0
            total_hours = total_time / 60  # تبدیل به ساعت
            
            # مقالات خوانده شده
            completed_papers = self.app.db.fetch_one("SELECT COUNT(*) FROM study_plans WHERE completed = TRUE")[0] or 0
            
            # مقالات برنامه‌ریزی شده
            planned_papers = self.app.db.fetch_one("SELECT COUNT(*) FROM study_plans WHERE completed = FALSE")[0] or 0
            
            # به‌روزرسانی کارت‌ها
            self.card_widgets[0].config(text=str(papers_count))
            self.card_widgets[1].config(text=f"{total_hours:.1f} ساعت")
            self.card_widgets[2].config(text=str(notes_count))
            self.card_widgets[3].config(text=str(planned_papers))
            
            # به‌روزرسانی آمار
            self.stat_widgets[0].config(text=str(completed_papers))
            self.stat_widgets[1].config(text=str(papers_count - completed_papers))
            self.stat_widgets[2].config(text=str(planned_papers))
            
            # میانگین زمان مطالعه
            avg_study_time = total_time / (papers_count or 1)
            self.stat_widgets[3].config(text=f"{avg_study_time:.1f} دقیقه")
            
            logger.info(self.config.t("dashboard_data_updated"))
            
        except Exception as e:
            logger.error(f"{self.config.t('error_updating_dashboard')}: {e}")