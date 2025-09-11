import customtkinter as ctk
from core.base_module import BaseModule
from tkinter import ttk
import sqlite3
from datetime import datetime

class PapersModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری مدیریت مقالات"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی با قابلیت اسکرول
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # هدر با دکمه actions
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = self.create_label(
            header_frame,
            text="مدیریت مقالات" if self.language.is_rtl() else "Papers Management",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="right" if self.language.is_rtl() else "left")
        
        # دکمه‌های action
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="left" if self.language.is_rtl() else "right")
        
        add_btn = self.create_button(
            actions_frame,
            text="➕ افزودن مقاله",
            command=self.add_paper,
            font=ctk.CTkFont(size=14),
            height=35,
            width=120,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        add_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        import_btn = self.create_button(
            actions_frame,
            text="📥 وارد کردن",
            command=self.import_papers,
            font=ctk.CTkFont(size=14),
            height=35,
            width=100
        )
        import_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        # نوار جستجو
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="جستجوی مقالات..." if self.language.is_rtl() else "Search papers...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        search_entry.pack(side="right" if self.language.is_rtl() else "left", fill="x", expand=True, padx=(10, 0))
        
        search_btn = self.create_button(
            search_frame,
            text="🔍",
            command=lambda: self.search_papers(search_entry.get()),
            font=ctk.CTkFont(size=16),
            height=40,
            width=50
        )
        search_btn.pack(side="right" if self.language.is_rtl() else "left")
        
        # جدول مقالات
        table_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # ایجاد Treeview با سبک مدرن
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="#333333", font=('Tahoma', 10, 'bold'))
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#333333", font=('Tahoma', 9))
        style.map("Treeview", background=[('selected', '#0078D7')])
        
        columns = ("title", "authors", "journal", "year", "tags")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # تعریف ستون‌ها
        self.tree.heading("title", text="عنوان" if self.language.is_rtl() else "Title")
        self.tree.heading("authors", text="نویسندگان" if self.language.is_rtl() else "Authors")
        self.tree.heading("journal", text="ژورنال" if self.language.is_rtl() else "Journal")
        self.tree.heading("year", text="سال" if self.language.is_rtl() else "Year")
        self.tree.heading("tags", text="برچسب‌ها" if self.language.is_rtl() else "Tags")
        
        # تنظیم عرض ستون‌ها
        self.tree.column("title", width=250)
        self.tree.column("authors", width=150)
        self.tree.column("journal", width=120)
        self.tree.column("year", width=60)
        self.tree.column("tags", width=120)
        
        # نوار اسکرول
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="right" if self.language.is_rtl() else "left", fill="both", expand=True)
        scrollbar.pack(side="left" if self.language.is_rtl() else "right", fill="y")
        
        # بارگذاری داده‌ها
        self.load_papers_data()
        
        # منوی راست‌کلیک
        self.setup_context_menu()
    
    def load_papers_data(self):
        """بارگذاری داده‌های مقالات از پایگاه داده"""
        # پاک کردن داده‌های موجود
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # نمونه داده‌های تست
        sample_data = [
            ("تحلیل داده‌های بزرگ در تحقیقات پزشکی", "احمدی، محمدی", "مجله پزشکی", "2023", "داده‌کاوی,پزشکی"),
            ("یادگیری عمیق در پردازش تصویر", "رضایی، حسینی", "کنفرانس هوش مصنوعی", "2022", "یادگیری عمیق,پردازش تصویر"),
            ("بررسی روش‌های رمزنگاری جدید", "جعفری، کریمی", "مجله امنیت", "2023", "امنیت,رمزنگاری"),
            ("کاربردهای IoT در صنعت", "محمودی، قاسمی", "کنفرانس فناوری", "2022", "IoT,صنعت"),
            ("تحلیل احساسات در شبکه‌های اجتماعی", "اکبری، امینی", "مجله پردازش زبان", "2023", "پردازش زبان,شبکه اجتماعی")
        ]
        
        # اضافه کردن داده‌ها به جدول
        for data in sample_data:
            self.tree.insert("", "end", values=data)
    
    def setup_context_menu(self):
        """تنظیم منوی راست‌کلیک"""
        self.context_menu = ctk.CTkMenu(self, tearoff=0)
        self.context_menu.add_command(
            label="مشاهده" if self.language.is_rtl() else "View",
            command=self.view_paper
        )
        self.context_menu.add_command(
            label="ویرایش" if self.language.is_rtl() else "Edit",
            command=self.edit_paper
        )
        self.context_menu.add_command(
            label="حذف" if self.language.is_rtl() else "Delete",
            command=self.delete_paper
        )
        
        # اتصال رویداد راست‌کلیک
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """نمایش منوی راست‌کلیک"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def add_paper(self):
        """افزودن مقاله جدید"""
        print("افزودن مقاله جدید")
        # اینجا می‌توانید دیالوگ افزودن مقاله را باز کنید
    
    def import_papers(self):
        """وارد کردن مقالات"""
        print("وارد کردن مقالات")
    
    def search_papers(self, query):
        """جستجوی مقالات"""
        print(f"جستجو برای: {query}")
    
    def view_paper(self):
        """مشاهده مقاله انتخاب شده"""
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item[0])
            print(f"مشاهده مقاله: {item_data['values'][0]}")
    
    def edit_paper(self):
        """ویرایش مقاله انتخاب شده"""
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item[0])
            print(f"ویرایش مقاله: {item_data['values'][0]}")
    
    def delete_paper(self):
        """حذف مقاله انتخاب شده"""
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item[0])
            print(f"حذف مقاله: {item_data['values'][0]}")
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()