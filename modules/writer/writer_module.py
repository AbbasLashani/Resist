import customtkinter as ctk
from core.base_module import BaseModule
import tkinter as tk
from tkinter import ttk

class WriterModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری ماژول نوشتن"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # طرح دو ستونی
        left_frame = ctk.CTkFrame(main_frame, width=300, fg_color=("#F0F0F0", "#2A2A2A"))
        left_frame.pack(side="right" if self.language.is_rtl() else "left", fill="y")
        left_frame.pack_propagate(False)
        
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.pack(side="left" if self.language.is_rtl() else "right", fill="both", expand=True, padx=10, pady=10)
        
        # ستون سمت چپ - لیست documents
        list_title = self.create_label(
            left_frame,
            text="اسناد من" if self.language.is_rtl() else "My Documents",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        list_title.pack(pady=15)
        
        # نوار جستجو
        search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="جستجوی اسناد..." if self.language.is_rtl() else "Search documents...",
            height=35
        )
        search_entry.pack(side="right" if self.language.is_rtl() else "left", fill="x", expand=True, padx=(10, 0))
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=40,
            height=35,
            command=lambda: self.search_documents(search_entry.get())
        )
        search_btn.pack(side="right" if self.language.is_rtl() else "left")
        
        # لیست documents
        documents_list = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        documents_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # نمونه documents
        documents = [
            {"title": "مقاله تحقیقاتی", "type": "مقاله", "date": "1402/05/۱۵", "word_count": "۲۵۰۰"},
            {"title": "گزارش پروژه", "type": "گزارش", "date": "1402/05/۱۰", "word_count": "۱۲۰۰"},
            {"title": "خلاصه کتاب", "type": "خلاصه", "date": "1402/04/۲۸", "word_count": "۸۰۰"},
            {"title": "یادداشت‌های جلسه", "type": "یادداشت", "date": "1402/05/۰۵", "word_count": "۵۰۰"}
        ]
        
        for doc in documents:
            self.create_document_item(documents_list, doc)
        
        # دکمه ایجاد سند جدید
        new_doc_btn = self.create_button(
            left_frame,
            text="📄 سند جدید",
            command=self.create_new_document,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        new_doc_btn.pack(fill="x", padx=10, pady=10)
        
        # ستون سمت راست - ویرایشگر
        editor_title = self.create_label(
            right_frame,
            text="ویرایشگر متن" if self.language.is_rtl() else "Text Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        editor_title.pack(pady=10)
        
        # فیلد عنوان
        title_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=5)
        
        title_label = self.create_label(
            title_frame,
            text="عنوان:" if self.language.is_rtl() else "Title:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(anchor="w" if not self.language.is_rtl() else "e")
        
        self.title_entry = ctk.CTkEntry(
            title_frame,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.title_entry.pack(fill="x", pady=5)
        
        # ویرایشگر متن
        editor_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        editor_container.pack(fill="both", expand=True, pady=5)
        
        self.text_editor = tk.Text(
            editor_container,
            wrap="word",
            font=("Tahoma", 12),
            relief="flat",
            bg="#FFFFFF",
            fg="#000000",
            selectbackground="#0078D7"
        )
        
        # نوار اسکرول
        editor_scrollbar = ttk.Scrollbar(editor_container, orient="vertical", command=self.text_editor.yview)
        self.text_editor.configure(yscrollcommand=editor_scrollbar.set)
        
        self.text_editor.pack(side="right" if self.language.is_rtl() else "left", fill="both", expand=True)
        editor_scrollbar.pack(side="left" if self.language.is_rtl() else "right", fill="y")
        
        # نوار وضعیت
        status_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=10)
        
        self.word_count_label = self.create_label(
            status_frame,
            text="تعداد کلمات: ۰" if self.language.is_rtl() else "Word count: 0",
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#AAAAAA")
        )
        self.word_count_label.pack(side="right" if self.language.is_rtl() else "left")
        
        # دکمه‌های action
        action_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=10)
        
        save_btn = self.create_button(
            action_frame,
            text="💾 ذخیره",
            command=self.save_document,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        save_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        export_btn = self.create_button(
            action_frame,
            text="📤 خروجی",
            command=self.export_document,
            font=ctk.CTkFont(size=14),
            height=40
        )
        export_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)
        
        # اتصال رویداد برای شمارش کلمات
        self.text_editor.bind("<KeyRelease>", self.update_word_count)
        
        # بارگذاری یک سند نمونه
        self.load_sample_document()
    
    def create_document_item(self, parent, doc):
        """ایجاد آیتم سند در لیست"""
        doc_frame = ctk.CTkFrame(
            parent,
            fg_color=("#FFFFFF", "#333333"),
            corner_radius=8,
            height=70
        )
        doc_frame.pack(fill="x", pady=5)
        doc_frame.pack_propagate(False)
        
        # bind event for selection
        doc_frame.bind("<Button-1>", lambda e, d=doc: self.select_document(d))
        
        content_frame = ctk.CTkFrame(doc_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title_label = self.create_label(
            content_frame,
            text=doc["title"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(anchor="w" if not self.language.is_rtl() else "e")
        
        meta_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        meta_frame.pack(fill="x", pady=2)
        
        type_label = self.create_label(
            meta_frame,
            text=doc["type"],
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#AAAAAA")
        )
        type_label.pack(side="right" if self.language.is_rtl() else "left")
        
        date_label = self.create_label(
            meta_frame,
            text=doc["date"],
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#AAAAAA")
        )
        date_label.pack(side="left" if self.language.is_rtl() else "right")
    
    def select_document(self, doc):
        """انتخاب یک سند برای ویرایش"""
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, doc["title"])
        
        self.text_editor.delete("1.0", "end")
        sample_text = f"""این یک نمونه سند با عنوان '{doc["title"]}' است.

می‌توانید اینجا شروع به نوشتن کنید. ویرایشگر از قالب‌بندی متن پشتیبانی می‌کند.

ویژگی‌ها:
- پشتیبانی از متن پررنگ و ایتالیک
- ترازبندی متن
- درج لینک
- شمارش خودکار کلمات

متن خود را اینجا بنویسید..."""
        
        self.text_editor.insert("1.0", sample_text)
        self.update_word_count()
    
    def load_sample_document(self):
        """بارگذاری یک سند نمونه"""
        sample_doc = {
            "title": "مقاله تحقیقاتی",
            "type": "مقاله",
            "date": "1402/05/۱۵",
            "word_count": "۲۵۰۰"
        }
        self.select_document(sample_doc)
    
    def create_new_document(self):
        """ایجاد سند جدید"""
        self.title_entry.delete(0, "end")
        self.text_editor.delete("1.0", "end")
        
        self.title_entry.insert(0, "سند جدید" if self.language.is_rtl() else "New Document")
        self.text_editor.insert("1.0", "محتوا را اینجا بنویسید..." if self.language.is_rtl() else "Write your content here...")
        self.update_word_count()
    
    def search_documents(self, query):
        """جستجوی اسناد"""
        print(f"جستجو برای: {query}")
    
    def update_word_count(self, event=None):
        """به روزرسانی تعداد کلمات"""
        content = self.text_editor.get("1.0", "end-1c")
        words = content.split()
        word_count = len(words)
        
        count_text = f"تعداد کلمات: {word_count}" if self.language.is_rtl() else f"Word count: {word_count}"
        self.word_count_label.configure(text=count_text)
    
    def save_document(self):
        """ذخیره سند"""
        title = self.title_entry.get()
        content = self.text_editor.get("1.0", "end-1c")
        
        if title and content:
            print(f"ذخیره سند: {title}")
        else:
            print("لطفا عنوان و محتوا را پر کنید")
    
    def export_document(self):
        """صدور سند"""
        title = self.title_entry.get()
        if title:
            print(f"صدور سند: {title}")
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()