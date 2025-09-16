import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, Menu
from core.base_module import BaseModule
from core.database import Database

class PapersModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        self.db = Database(config)
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری مدیریت مقالات"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی با قابلیت اسکرول
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # عنوان ماژول
        title_text = "مدیریت مقالات" if self.language.is_rtl() else "Papers Management"
        title = self.create_label(
            main_frame,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # نوار ابزار
        toolbar_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        toolbar_frame.pack(fill="x", padx=20, pady=10)
        
        # دکمه‌های نوار ابزار
        buttons = [
            {"text": "مقاله جدید", "icon": "➕", "command": self.add_paper},
            {"text": "ویرایش", "icon": "✏️", "command": self.edit_paper},
            {"text": "حذف", "icon": "🗑️", "command": self.delete_paper},
            {"text": "نمایش", "icon": "👁️", "command": self.view_paper}
        ]
        
        for i, btn in enumerate(buttons):
            button = ctk.CTkButton(
                toolbar_frame,
                text=f"{btn['icon']} {btn['text']}" if not self.language.is_rtl() else f"{btn['text']} {btn['icon']}",
                command=btn["command"],
                height=35,
                width=120
            )
            button.grid(row=0, column=i, padx=5)
        
        # لیست مقالات
        list_frame = ctk.CTkFrame(main_frame, corner_radius=12)
        list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # عنوان لیست
        list_title = self.create_label(
            list_frame,
            text="لیست مقالات" if self.language.is_rtl() else "Papers List",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        list_title.pack(pady=15)
        
        # ایجاد Treeview برای نمایش مقالات
        self.create_papers_treeview(list_frame)
        
        # بارگذاری مقالات
        self.load_papers()
    
    def create_papers_treeview(self, parent):
        """ایجاد Treeview برای نمایش مقالات"""
        # ایجاد فریم برای Treeview
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # ایجاد Treeview با ستون‌ها
        columns = ("title", "author", "year", "journal")
        column_names = {
            "title": "عنوان",
            "author": "نویسنده",
            "year": "سال",
            "journal": "ژورنال"
        }
        
        if not self.language.is_rtl():
            column_names = {
                "title": "Title",
                "author": "Author",
                "year": "Year",
                "journal": "Journal"
            }
        
        self.tree = tk.ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # تعریف ستون‌ها
        for col in columns:
            self.tree.heading(col, text=column_names[col])
            self.tree.column(col, width=150, anchor="center")
        
        # نوار اسکرول
        scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # قرار دادن Treeview و نوار اسکرول
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # اتصال رویداد کلیک
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.on_right_click)  # کلیک راست
    
    def on_tree_click(self, event):
        """واکنش به کلیک روی Treeview"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
    
    def on_right_click(self, event):
        """واکنش به کلیک راست روی Treeview"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # ایجاد منوی زمینه
            self.create_context_menu(event)
    
    def create_context_menu(self, event):
        """ایجاد منوی زمینه"""
        # حذف منوی قبلی اگر وجود دارد
        if hasattr(self, 'context_menu'):
            self.context_menu.destroy()
        
        # ایجاد منوی زمینه با tkinter
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="نمایش" if self.language.is_rtl() else "View",
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
        
        # نمایش منو در موقعیت کلیک
        self.context_menu.post(event.x_root, event.y_root)
    
    def load_papers(self):
        """بارگذاری مقالات از پایگاه داده"""
        # پاک کردن Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # داده‌های نمونه (موقت)
        sample_data = [
            ("تحقیق در مورد هوش مصنوعی", "علی محمدی", "2023", "ژورنال علوم کامپیوتر"),
            ("یادگیری عمیق و کاربردهای آن", "رضا احمدی", "2022", "کنفرانس بین‌المللی"),
            ("پردازش زبان طبیعی", "فاطمه زهرا حسینی", "2023", "مجله مهندسی نرم‌افزار")
        ]
        
        if not self.language.is_rtl():
            sample_data = [
                ("Research on Artificial Intelligence", "Ali Mohammadi", "2023", "Computer Science Journal"),
                ("Deep Learning and Applications", "Reza Ahmadi", "2022", "International Conference"),
                ("Natural Language Processing", "Fatima Zahra Hosseini", "2023", "Software Engineering Journal")
            ]
        
        # اضافه کردن داده‌ها به Treeview
        for data in sample_data:
            self.tree.insert("", "end", values=data)
    
    def add_paper(self):
        """افزودن مقاله جدید"""
        messagebox.showinfo(
            "مقاله جدید" if self.language.is_rtl() else "New Paper",
            "افزودن مقاله جدید" if self.language.is_rtl() else "Add new paper"
        )
    
    def edit_paper(self):
        """ویرایش مقاله انتخاب شده"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "هشدار" if self.language.is_rtl() else "Warning",
                "لطفاً یک مقاله انتخاب کنید" if self.language.is_rtl() else "Please select a paper"
            )
            return
        
        messagebox.showinfo(
            "ویرایش مقاله" if self.language.is_rtl() else "Edit Paper",
            "ویرایش مقاله" if self.language.is_rtl() else "Edit paper"
        )
    
    def delete_paper(self):
        """حذف مقاله انتخاب شده"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "هشدار" if self.language.is_rtl() else "Warning",
                "لطفاً یک مقاله انتخاب کنید" if self.language.is_rtl() else "Please select a paper"
            )
            return
        
        result = messagebox.askyesno(
            "تأیید حذف" if self.language.is_rtl() else "Confirm Delete",
            "آیا از حذف مقاله انتخاب شده مطمئن هستید؟" if self.language.is_rtl() else "Are you sure you want to delete the selected paper?"
        )
        
        if result:
            for item in selected:
                self.tree.delete(item)
    
    def view_paper(self):
        """نمایش مقاله انتخاب شده"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "هشدار" if self.language.is_rtl() else "Warning",
                "لطفاً یک مقاله انتخاب کنید" if self.language.is_rtl() else "Please select a paper"
            )
            return
        
        item = self.tree.item(selected[0])
        messagebox.showinfo(
            "نمایش مقاله" if self.language.is_rtl() else "View Paper",
            f"نمایش مقاله: {item['values'][0]}" if self.language.is_rtl() else f"Viewing paper: {item['values'][0]}"
        )
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()