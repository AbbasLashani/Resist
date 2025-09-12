import customtkinter as ctk
from core.base_module import BaseModule
import tkinter as tk
from tkinter import ttk

class ResearchModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری ماژول تحقیق"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی با قابلیت اسکرول
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # عنوان
        title_text = "تحقیق و پژوهش" if self.language.is_rtl() else "Research"
        title = self.create_label(
            main_frame,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # جستجوی تحقیقات
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="جستجوی تحقیقات..." if self.language.is_rtl() else "Search research...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        search_entry.pack(side="right" if self.language.is_rtl() else "left", fill="x", expand=True, padx=(10, 0))
        
        search_btn = self.create_button(
            search_frame,
            text="🔍",
            command=lambda: self.search_research(search_entry.get()),
            font=ctk.CTkFont(size=16),
            height=40,
            width=50
        )
        search_btn.pack(side="right" if self.language.is_rtl() else "left")
        
        # فیلترهای تحقیق
        filter_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        filter_options = ["همه", "در حال انجام", "تکمیل شده", "متوقف شده"]
        if not self.language.is_rtl():
            filter_options = ["All", "In Progress", "Completed", "Paused"]
            
        filter_var = ctk.StringVar(value=filter_options[0])
        filter_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=filter_options,
            variable=filter_var,
            command=self.filter_research,
            width=150
        )
        filter_menu.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        sort_options = ["جدیدترین", "قدیمی ترین", "الفبا"]
        if not self.language.is_rtl():
            sort_options = ["Newest", "Oldest", "Alphabetical"]
            
        sort_var = ctk.StringVar(value=sort_options[0])
        sort_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=sort_options,
            variable=sort_var,
            command=self.sort_research,
            width=150
        )
        sort_menu.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        # دکمه ایجاد تحقیق جدید
        new_research_btn = self.create_button(
            filter_frame,
            text="➕ تحقیق جدید",
            command=self.create_new_research,
            font=ctk.CTkFont(size=14),
            height=35,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        new_research_btn.pack(side="left" if self.language.is_rtl() else "right")
        
        # لیست تحقیقات
        research_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        research_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ایجاد Treeview برای نمایش تحقیقات
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", background="#f0f0f0", foreground="#333333", font=('Tahoma', 10, 'bold'))
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#333333", font=('Tahoma', 9))
        style.map("Treeview", background=[('selected', '#0078D7')])
        
        columns = ("title", "status", "progress", "start_date", "deadline")
        self.tree = ttk.Treeview(research_frame, columns=columns, show="headings", height=12)
        
        # تعریف ستون‌ها
        self.tree.heading("title", text="عنوان تحقیق" if self.language.is_rtl() else "Research Title")
        self.tree.heading("status", text="وضعیت" if self.language.is_rtl() else "Status")
        self.tree.heading("progress", text="پیشرفت" if self.language.is_rtl() else "Progress")
        self.tree.heading("start_date", text="تاریخ شروع" if self.language.is_rtl() else "Start Date")
        self.tree.heading("deadline", text="ددلاین" if self.language.is_rtl() else "Deadline")
        
        # تنظیم عرض ستون‌ها
        self.tree.column("title", width=250)
        self.tree.column("status", width=100)
        self.tree.column("progress", width=80)
        self.tree.column("start_date", width=100)
        self.tree.column("deadline", width=100)
        
        # نوار اسکرول
        scrollbar = ttk.Scrollbar(research_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="right" if self.language.is_rtl() else "left", fill="both", expand=True)
        scrollbar.pack(side="left" if self.language.is_rtl() else "right", fill="y")
        
        # بارگذاری داده‌ها
        self.load_research_data()
        
        # منوی راست‌کلیک
        self.setup_context_menu()
    
    def load_research_data(self):
        """بارگذاری داده‌های تحقیق از پایگاه داده"""
        # پاک کردن داده‌های موجود
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # نمونه داده‌های تست
        sample_data = [
            ("تحلیل داده‌های پزشکی", "در حال انجام", "۶۰٪", "1402/05/01", "1402/08/30"),
            ("پروژه یادگیری ماشین", "تکمیل شده", "۱۰۰٪", "1402/03/15", "1402/07/15"),
            ("بررسی الگوریتم‌های جدید", "متوقف شده", "۳۰٪", "1402/04/10", "1402/09/10"),
            ("تحلیل شبکه‌های اجتماعی", "در حال انجام", "۴۵٪", "1402/05/20", "1402/10/20"),
            ("پژوهش در مورد IoT", "در حال انجام", "۲۵٪", "1402/06/01", "1402/11/01")
        ]
        
        # اضافه کردن داده‌ها به جدول
        for data in sample_data:
            self.tree.insert("", "end", values=data)
    
    def setup_context_menu(self):
        """تنظیم منوی راست‌کلیک"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="مشاهده جزئیات",
            command=self.view_research
        )
        self.context_menu.add_command(
            label="ویرایش",
            command=self.edit_research
        )
        self.context_menu.add_command(
            label="حذف",
            command=self.delete_research
        )
        self.context_menu.add_command(
            label="گزارش پیشرفت",
            command=self.generate_report
        )
        
        # اتصال رویداد راست‌کلیک
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """نمایش منوی راست‌کلیک"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def create_new_research(self):
        """ایجاد تحقیق جدید"""
        print("ایجاد تحقیق جدید")
    
    def search_research(self, query):
        """جستجوی تحقیقات"""
        print(f"جستجو برای: {query}")
    
    def filter_research(self, filter_type):
        """فیلتر کردن تحقیقات"""
        print(f"فیلتر: {filter_type}")
    
    def sort_research(self, sort_type):
        """مرتب‌سازی تحقیقات"""
        print(f"مرتب‌سازی: {sort_type}")
    
    def view_research(self):
        """مشاهده تحقیق انتخاب شده"""
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item[0])
            print(f"مشاهده تحقیق: {item_data['values'][0]}")
    
    def edit_research(self):
        """ویرایش تحقیق انتخاب شده"""
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item[0])
            print(f"ویرایش تحقیق: {item_data['values'][0]}")
    
    def delete_research(self):
        """حذف تحقیق انتخاب شده"""
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item[0])
            print(f"حذف تحقیق: {item_data['values'][0]}")
    
    def generate_report(self):
        """تولید گزارش پیشرفت"""
        selected_item = self.tree.selection()
        if selected_item:
            item_data = self.tree.item(selected_item[0])
            print(f"تولید گزارش برای: {item_data['values'][0]}")
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()