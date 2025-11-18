import customtkinter as ctk
import os
import json
import sqlite3
from tkinter import filedialog, messagebox
import webbrowser
from datetime import datetime
import requests
import threading
import re
import tkinter as tk
import pandas as pd
from pathlib import Path
import shutil
import logging
from core.base_module import BaseModule

class PapersModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        
        # ابتدا language_manager را تنظیم کنید
        self.language_manager = app.language_manager if hasattr(app, 'language_manager') else None
        
        # سپس داده‌ها را با استفاده از get_text مقداردهی کنید
        self.articles = []
        self.categories = self.load_categories()
        self.current_filter = self.get_text("all")
        self.search_term = ""
        self.sort_by = "newest"
        self.selected_file_path = None
        self.article_widgets = []
        
        # تنظیمات جدید
        self.pdf_storage_path = Path("data/pdfs")
        self.pdf_storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()
        self._cache = {}
        self._last_refresh = None
        self._search_thread = None
        self._search_lock = threading.Lock()
        
        # ایجاد دیتابیس
        self.init_database()
        
        # ایجاد UI
        self.setup_ui()
        
        # بارگذاری داده‌ها
        self.load_articles()
    
    def _setup_logging(self):
        """تنظیم سیستم لاگینگ"""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _show_error(self, error_key, details=""):
        """نمایش خطا به صورت یکپارچه"""
        message = self.get_text(error_key)
        if details:
            message += f": {details}"
        messagebox.showerror(self.get_text("error"), message)
    
    def setup_ui(self):
        """ایجاد رابط کاربری"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # چیدمان اصلی
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # نوار ابزار بالا
        self.create_toolbar()
        
        # بخش اصلی
        self.create_main_section()
        
        # اعمال تنظیمات RTL/LTR
        self.apply_language_settings()
    
    def apply_language_settings(self):
        """اعمال تنظیمات زبان بر روی ویجت‌ها"""
        if self.language_manager:
            if self.language_manager.is_rtl():
                self.language_manager.set_widget_rtl(self)
            else:
                self.language_manager.set_widget_ltr(self)
    
    def get_text(self, key):
        """دریافت متن ترجمه شده"""
        if hasattr(self, 'language_manager') and self.language_manager:
            return self.language_manager.get_text(key)
        return key
    
    def create_toolbar(self):
        """ایجاد نوار ابزار بهبود یافته"""
        toolbar = ctk.CTkFrame(self, height=80, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(0, weight=1)
        
        # عنوان با استایل بهتر
        title_text = self.get_text("papers_module_title")
        title = ctk.CTkLabel(
            toolbar,
            text=title_text,
            font=self.get_font(20, "bold"),
            justify="right"
        )
        title.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        
        # دکمه‌های action با طراحی بهتر
        button_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_frame.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        buttons = [
            ("categories", self.manage_categories, "#2196F3", "🗂️"),
            ("import_from_doi", self.import_from_doi, "#2196F3", "🌐"),
            ("statistics", self.show_statistics, "#4CAF50", "📊"),
            ("export_bibtex", self.export_bibtex, "#9C27B0", "📥"),
            ("export_excel", self.export_excel, "#4CAF50", "📤"),
            ("import_excel", self.import_excel, "#2196F3", "📥"),
            ("new_article", self.show_add_dialog, "#2196F3", "➕")
        ]
        
        for i, (text_key, command, color, icon) in enumerate(buttons):
            text = f"{icon} {self.get_text(text_key)}"
                
            btn = ctk.CTkButton(
                button_frame,
                text=text,
                command=command,
                width=140,
                height=38,
                font=self.get_font(12, "bold"),
                fg_color=color,
                hover_color=self.darken_color(color),
                corner_radius=10,
                border_width=0
            )
            btn.grid(row=0, column=i, padx=4, sticky="w")
    
    def darken_color(self, color):
        """تیره کردن رنگ برای hover effect"""
        colors = {
            "#2196F3": "#1976D2",
            "#4CAF50": "#388E3C", 
            "#9C27B0": "#7B1FA2",
            "#f44336": "#d32f2f",
            "#FF9800": "#F57C00"
        }
        return colors.get(color, color)
    
    def create_main_section(self):
        """ایجاد بخش اصلی بهبود یافته"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        
        # تنظیم grid
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # نوار فیلتر و جستجوی بهبود یافته
        self.create_filter_bar(main_frame)
        
        # لیست مقالات
        self.create_articles_list(main_frame)
    
    def create_filter_bar(self, parent):
        """ایجاد نوار فیلتر و جستجوی پیشرفته"""
        filter_frame = ctk.CTkFrame(parent, height=70, corner_radius=12)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_propagate(False)
        filter_frame.grid_columnconfigure(0, weight=1)
        
        # سمت راست: جستجوی پیشرفته
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.grid(row=0, column=1, padx=20, pady=15, sticky="e")
        
        # دکمه جستجوی پیشرفته
        advanced_btn = ctk.CTkButton(
            search_frame,
            text="🎛️",
            width=40,
            height=38,
            command=self.show_advanced_search,
            font=self.get_font(14),
            corner_radius=8,
            fg_color="#6c757d"
        )
        advanced_btn.pack(side="right", padx=(5, 0))
        
        # دکمه جستجو
        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=40,
            height=38,
            command=self.perform_search,
            font=self.get_font(14),
            corner_radius=8,
            fg_color="#2196F3"
        )
        search_btn.pack(side="right", padx=(5, 0))
        
        # فیلد جستجو
        search_placeholder = self.get_text("search_placeholder")
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=search_placeholder,
            width=300,
            height=38,
            font=self.get_font(12),
            justify="right",
            corner_radius=8,
            border_width=2
        )
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        # سمت چپ: فیلترها با طراحی بهتر
        filter_btn_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_btn_frame.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # فیلتر دسته‌بندی
        category_label_text = self.get_text("category") + ":"
        category_label = ctk.CTkLabel(
            filter_btn_frame,
            text=category_label_text,
            font=self.get_font(12, "bold"),
            justify="right"
        )
        category_label.grid(row=0, column=3, padx=(10, 5), pady=5, sticky="e")
        
        # مقادیر فیلتر دسته‌بندی
        category_values = [self.get_text("all")] + self.categories
        self.filter_combo = ctk.CTkComboBox(
            filter_btn_frame,
            values=category_values,
            width=160,
            height=38,
            font=self.get_font(12),
            command=self.on_filter_changed,
            justify="right",
            corner_radius=8,
            dropdown_font=self.get_font(12),
            border_width=2
        )
        self.filter_combo.set(self.get_text("all"))
        self.filter_combo.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # مرتب‌سازی
        sort_label_text = self.get_text("sort_by") + ":"
        sort_label = ctk.CTkLabel(
            filter_btn_frame,
            text=sort_label_text,
            font=self.get_font(12, "bold"),
            justify="right"
        )
        sort_label.grid(row=0, column=1, padx=(10, 5), pady=5, sticky="e")
        
        # مقادیر مرتب‌سازی
        sort_values = [
            self.get_text("newest"),
            self.get_text("oldest"), 
            self.get_text("highest_rated"),
            self.get_text("alphabetical")
        ]
        self.sort_combo = ctk.CTkComboBox(
            filter_btn_frame,
            values=sort_values,
            width=140,
            height=38,
            font=self.get_font(12),
            command=self.on_sort_changed,
            justify="right",
            corner_radius=8,
            dropdown_font=self.get_font(12),
            border_width=2
        )
        self.sort_combo.set(self.get_text("newest"))
        self.sort_combo.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    def create_articles_list(self, parent):
        """ایجاد لیست مقالات با طراحی بهتر"""
        # فریم لیست
        self.list_frame = ctk.CTkScrollableFrame(
            parent, 
            fg_color="transparent",
            scrollbar_button_color="#E0E0E0",
            scrollbar_button_hover_color="#BDBDBD"
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        # برچسب خالی با طراحی بهتر
        empty_text = self.get_text("no_articles_found")
        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text=f"📚 {empty_text}",
            font=self.get_font(16),
            text_color=("#666666", "#AAAAAA"),
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=100, sticky="nsew")
        
        self.article_widgets = []
    
    def load_categories(self):
        """بارگذاری دسته‌بندی‌های مقالات"""
        categories_file = "data/article_categories.json"
        
        # استفاده از مقادیر ترجمه شده برای دسته‌بندی‌های پیش‌فرض
        default_categories = [
            self.get_text("computer_science"),
            self.get_text("artificial_intelligence"),
            self.get_text("machine_learning"),
            self.get_text("computer_networks"),
            self.get_text("information_security"),
            self.get_text("data_mining"),
            self.get_text("programming"),
            self.get_text("database"),
            self.get_text("iot"),
            self.get_text("robotics"),
            self.get_text("computer_vision"),
            self.get_text("natural_language_processing")
        ]
        
        try:
            os.makedirs('data', exist_ok=True)
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    loaded_categories = json.load(f)
                    # اطمینان از اینکه دسته‌بندی‌های بارگذاری شده نیز ترجمه شوند
                    translated_categories = []
                    for category in loaded_categories:
                        # سعی کنید دسته‌بندی را ترجمه کنید، اگر ترجمه وجود نداشت از مقدار اصلی استفاده کنید
                        translated = self.get_text(category.lower().replace(" ", "_")) or category
                        translated_categories.append(translated)
                    return translated_categories
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری دسته‌بندی‌ها: {e}")
        
        return default_categories
    
    def save_categories(self):
        """ذخیره دسته‌بندی‌ها در فایل"""
        try:
            categories_file = "data/article_categories.json"
            os.makedirs('data', exist_ok=True)
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"❌ خطا در ذخیره دسته‌بندی‌ها: {e}")
            self._show_error("save_categories_error", str(e))
            return False
    
    def init_database(self):
        """ایجاد جدول مقالات در دیتابیس با مدیریت خطای بهتر"""
        try:
            # اطمینان از وجود پوشه دیتابیس
            os.makedirs('data', exist_ok=True)
            
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        authors TEXT NOT NULL,
                        abstract TEXT,
                        journal TEXT,
                        conference TEXT,
                        year INTEGER,
                        volume TEXT,
                        issue TEXT,
                        pages TEXT,
                        publisher TEXT,
                        doi TEXT UNIQUE,
                        url TEXT,
                        pdf_path TEXT,
                        citation TEXT,
                        keywords TEXT,
                        category TEXT NOT NULL,
                        rating INTEGER DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
                        read_status BOOLEAN DEFAULT FALSE,
                        favorite BOOLEAN DEFAULT FALSE,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_sync TIMESTAMP
                    )
                ''')
                
                # ایجاد ایندکس برای بهبود عملکرد
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_rating ON articles(rating)')
                
            self.logger.info("✅ جدول مقالات ایجاد شد")
        except sqlite3.Error as e:
            self.logger.error(f"❌ خطای دیتابیس: {e}")
            self._show_error("database_error", str(e))
        except Exception as e:
            self.logger.error(f"❌ خطای غیرمنتظره در ایجاد دیتابیس: {e}")
            self._show_error("database_error", str(e))
    
    def refresh_articles_list(self):
        """تازه‌سازی لیست مقالات با کشینگ"""
        # پاک کردن ویجت‌های قبلی
        for widget in self.article_widgets:
            widget.destroy()
        self.article_widgets = []
        
        # فیلتر کردن و مرتب‌سازی داده‌ها
        filtered_data = self.filter_articles()
        sorted_data = self.sort_articles(filtered_data)
        
        # نمایش برچسب خالی اگر داده‌ای نیست
        if not sorted_data:
            self.empty_label.grid(row=0, column=0, pady=80, sticky="nsew")
            return
        else:
            self.empty_label.grid_forget()
        
        # ایجاد کارت برای هر مقاله
        for i, article in enumerate(sorted_data):
            self.create_article_card(article, i)
    
    def filter_articles(self):
        """فیلتر کردن مقالات"""
        filtered = self.articles
        
        if self.current_filter != self.get_text("all"):
            filtered = [article for article in filtered if article['category'] == self.current_filter]
        
        if self.search_term:
            search_lower = self.search_term.lower()
            filtered = [
                article for article in filtered 
                if (search_lower in article['title'].lower() or 
                    search_lower in article['authors'].lower() or 
                    search_lower in article['abstract'].lower() or
                    search_lower in article['keywords'].lower() or
                    search_lower in article['journal'].lower() or
                    search_lower in article['doi'].lower())
            ]
        
        return filtered
    
    def sort_articles(self, articles):
        """مرتب‌سازی مقالات"""
        if self.sort_by == "newest":
            return sorted(articles, key=lambda x: x.get('created_at', ''), reverse=True)
        elif self.sort_by == "oldest":
            return sorted(articles, key=lambda x: x.get('created_at', ''))
        elif self.sort_by == "rating":
            return sorted(articles, key=lambda x: x.get('rating', 0), reverse=True)
        elif self.sort_by == "alphabetical":
            return sorted(articles, key=lambda x: x.get('title', '').lower())
        return articles
    
    def create_article_card(self, article, index):
        """ایجاد کارت مقاله با طراحی مدرن"""
        card = ctk.CTkFrame(
            self.list_frame,
            corner_radius=15,
            border_width=2,
            border_color=("#E0E0E0", "#404040"),
            fg_color=("#FFFFFF", "#2B2B2B")
        )
        card.grid(row=index, column=0, sticky="ew", padx=5, pady=8)
        card.grid_columnconfigure(0, weight=1)
        
        # افزودن effect hover
        self._add_hover_effect(card)
        
        # محتوای کارت
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # هدر کارت
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # عنوان و ستاره‌ها
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        
        # عنوان مقاله با قابلیت کلیک
        title_label = ctk.CTkLabel(
            title_frame,
            text=article['title'],
            font=self.get_font(15, "bold"),
            wraplength=600,
            justify="right",
            anchor="e",
            cursor="hand2"
        )
        title_label.grid(row=0, column=0, sticky="ew", padx=(0, 15))
        title_label.bind("<Button-1>", lambda e: self.show_article_details(article))
        
        # ستاره‌های امتیاز
        rating_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        rating_frame.grid(row=0, column=1, sticky="e")
        
        rating_text = "★" * article['rating'] + "☆" * (5 - article['rating'])
        rating_label = ctk.CTkLabel(
            rating_frame,
            text=rating_text,
            font=self.get_font(13),
            text_color="#FFD700"
        )
        rating_label.pack()
        
        # اطلاعات مقاله
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # نویسندگان
        authors_text = f"👤 {article['authors']}"
        authors_label = ctk.CTkLabel(
            info_frame,
            text=authors_text,
            font=self.get_font(13),
            wraplength=600,
            justify="right",
            anchor="e"
        )
        authors_label.grid(row=0, column=0, sticky="ew")
        
        # ژورنال و سال
        journal_text = ""
        if article['journal']:
            journal_text = f"📰 {article['journal']}"
        elif article['conference']:
            journal_text = f"🎤 {article['conference']}"
        
        if journal_text and article['year']:
            journal_text += f" | {article['year']}"
        
        if journal_text:
            journal_label = ctk.CTkLabel(
                info_frame,
                text=journal_text,
                font=self.get_font(12),
                text_color=("#666666", "#AAAAAA"),
                justify="right",
                anchor="e"
            )
            journal_label.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # چکیده کوتاه
        if article['abstract']:
            abstract_short = article['abstract'][:200] + "..." if len(article['abstract']) > 200 else article['abstract']
            abstract_label = ctk.CTkLabel(
                content_frame,
                text=abstract_short,
                font=self.get_font(11),
                wraplength=600,
                justify="right",
                anchor="e"
            )
            abstract_label.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # فوتر کارت
        footer_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # برچسب‌ها و دسته‌بندی
        tags_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        tags_frame.grid(row=0, column=1, sticky="e")
        
        # دسته‌بندی
        category_badge = ctk.CTkLabel(
            tags_frame,
            text=f"🏷️ {article['category']}",
            font=self.get_font(10, "bold"),
            text_color=("#2196F3", "#64B5F6"),
            padx=12,
            pady=6,
            corner_radius=15,
            fg_color=("#E3F2FD", "#0D47A1")
        )
        category_badge.pack(side="right", padx=(5, 0))
        
        # وضعیت مطالعه
        status_text = "✅ " + self.get_text("read") if article['read_status'] else "📖 " + self.get_text("unread")
        status_color = ("#4CAF50", "#81C784") if article['read_status'] else ("#FF9800", "#FFB74D")
        status_label = ctk.CTkLabel(
            tags_frame,
            text=status_text,
            font=self.get_font(10, "bold"),
            text_color=status_color,
            justify="right"
        )
        status_label.pack(side="right", padx=(10, 0))
        
        # علاقه‌مندی
        if article['favorite']:
            favorite_text = "❤️ " + self.get_text("favorite")
            favorite_label = ctk.CTkLabel(
                tags_frame,
                text=favorite_text,
                font=self.get_font(10, "bold"),
                text_color=("#f44336", "#e57373"),
                justify="right"
            )
            favorite_label.pack(side="right", padx=(10, 0))
        
        # دکمه‌های action با طراحی بهتر
        action_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        action_frame.grid(row=0, column=0, sticky="w")
        
        # ایجاد دکمه‌های action
        buttons = [
            ("📄", self.open_pdf, "#2196F3", article, "open_pdf") if article.get('pdf_path') and os.path.exists(article['pdf_path']) else None,
            ("🌐", self.open_url, "#FF9800", article, "open_url") if article.get('url') else None,
            ("👁️", self.show_article_details, "#4CAF50", article, "view_details"),
            ("✏️", self.edit_article, "#9C27B0", article, "edit"),
            ("🗑️", self.delete_article, "#f44336", article, "delete")
        ]
        
        for i, btn_info in enumerate([b for b in buttons if b is not None]):
            text, command, color, art, tooltip = btn_info
            btn = ctk.CTkButton(
                action_frame,
                text=text,
                width=40,
                height=35,
                font=self.get_font(12),
                fg_color=color,
                hover_color=self.darken_color(color),
                command=lambda c=command, a=art: c(a),
                corner_radius=8
            )
            btn.grid(row=0, column=i, padx=3)
        
        self.article_widgets.append(card)
    
    def _add_hover_effect(self, widget):
        """افزودن effect hover به ویجت"""
        original_color = widget.cget("fg_color")
        
        def on_enter(event):
            widget.configure(fg_color=("#F5F5F5", "#363636"))
        
        def on_leave(event):
            widget.configure(fg_color=original_color)
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def show_add_dialog(self):
        """نمایش دیالوگ افزودن مقاله جدید"""
        dialog = AddArticleDialog(self, self.categories)
        self.wait_window(dialog)
        
        if dialog.result:
            self.save_article(dialog.result)
    
    def edit_article(self, article):
        """ویرایش مقاله"""
        dialog = AddArticleDialog(self, self.categories, article)
        self.wait_window(dialog)
        
        if dialog.result:
            self.update_article(article['id'], dialog.result)
    
    def _handle_pdf_file(self, file_path, article_title):
        """مدیریت فایل PDF با کپی به پوشه اختصاصی"""
        if not file_path or not os.path.exists(file_path):
            return ""
        
        try:
            # ایجاد نام فایل امن
            safe_title = "".join(c for c in article_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # محدودیت طول نام فایل
            file_extension = Path(file_path).suffix
            
            new_filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            new_file_path = self.pdf_storage_path / new_filename
            
            # کپی فایل به محل امن
            shutil.copy2(file_path, new_file_path)
            self.logger.info(f"فایل PDF ذخیره شد: {new_file_path}")
            
            return str(new_file_path)
            
        except Exception as e:
            self.logger.error(f"خطا در مدیریت فایل PDF: {e}")
            self._show_error("pdf_save_error", str(e))
            return ""
    
    def save_article(self, data):
        """ذخیره مقاله جدید در دیتابیس"""
        try:
            # مدیریت فایل PDF
            if data.get('pdf_path'):
                data['pdf_path'] = self._handle_pdf_file(data['pdf_path'], data['title'])
            
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO articles (
                        title, authors, abstract, journal, conference, year, 
                        volume, issue, pages, publisher, doi, url, pdf_path, 
                        citation, keywords, category, rating, read_status, favorite, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['title'], data['authors'], data['abstract'], data['journal'],
                    data['conference'], data['year'], data['volume'], data['issue'],
                    data['pages'], data['publisher'], data['doi'], data['url'],
                    data['pdf_path'], data['citation'], data['keywords'], data['category'],
                    data['rating'], data['read_status'], data['favorite'], data['notes']
                ))
                
            messagebox.showinfo(
                self.get_text("success"), 
                self.get_text("article_saved")
            )
            self.load_articles()
            
        except sqlite3.IntegrityError:
            self._show_error("duplicate_doi")
        except Exception as e:
            self.logger.error(f"❌ خطا در ذخیره مقاله: {e}")
            self._show_error("save_article_error", str(e))
    
    def update_article(self, article_id, data):
        """بروزرسانی مقاله"""
        try:
            # مدیریت فایل PDF
            if data.get('pdf_path') and data['pdf_path'] != self.articles[article_id]['pdf_path']:
                data['pdf_path'] = self._handle_pdf_file(data['pdf_path'], data['title'])
            
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE articles 
                    SET title=?, authors=?, abstract=?, journal=?, conference=?, year=?, 
                        volume=?, issue=?, pages=?, publisher=?, doi=?, url=?, pdf_path=?, 
                        citation=?, keywords=?, category=?, rating=?, read_status=?, favorite=?, notes=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (
                    data['title'], data['authors'], data['abstract'], data['journal'],
                    data['conference'], data['year'], data['volume'], data['issue'],
                    data['pages'], data['publisher'], data['doi'], data['url'],
                    data['pdf_path'], data['citation'], data['keywords'], data['category'],
                    data['rating'], data['read_status'], data['favorite'], data['notes'], article_id
                ))
                
            messagebox.showinfo(
                self.get_text("success"), 
                self.get_text("article_updated")
            )
            self.load_articles()
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بروزرسانی مقاله: {e}")
            self._show_error("update_article_error", str(e))
    
    def delete_article(self, article):
        """حذف مقاله"""
        confirm_message = self.get_text("confirm_delete_article").format(article['title'])
        if messagebox.askyesno(self.get_text("confirm"), confirm_message):
            try:
                with sqlite3.connect('data/research_assistant.db') as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('DELETE FROM articles WHERE id=?', (article['id'],))
                    
                messagebox.showinfo(
                    self.get_text("success"), 
                    self.get_text("article_deleted")
                )
                self.load_articles()
                
            except Exception as e:
                self.logger.error(f"❌ خطا در حذف مقاله: {e}")
                self._show_error("delete_article_error", str(e))
    
    def open_pdf(self, article):
        """باز کردن فایل PDF با مدیریت خطای بهتر"""
        pdf_path = article.get('pdf_path')
        
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showwarning(
                self.get_text("warning"), 
                self.get_text("pdf_not_found")
            )
            return
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(pdf_path)
            else:  # MacOS, Linux
                webbrowser.open(f"file://{pdf_path}")
                
            self.logger.info(f"فایل PDF باز شد: {pdf_path}")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در باز کردن فایل PDF: {e}")
            self._show_error("open_pdf_error", str(e))
    
    def open_url(self, article):
        """باز کردن لینک مقاله"""
        try:
            if article.get('url'):
                webbrowser.open(article['url'])
            else:
                messagebox.showwarning(
                    self.get_text("warning"), 
                    self.get_text("url_not_found")
                )
        except Exception as e:
            self.logger.error(f"❌ خطا در باز کردن لینک: {e}")
            self._show_error("open_url_error", str(e))
    
    def show_article_details(self, article):
        """نمایش جزئیات کامل مقاله"""
        dialog = ArticleDetailsDialog(self, article)
        self.wait_window(dialog)
    
    def load_articles(self):
        """بارگذاری مقالات از دیتابیس"""
        try:
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, authors, abstract, journal, conference, year, 
                           volume, issue, pages, publisher, doi, url, pdf_path, 
                           citation, keywords, category, rating, read_status, favorite, notes, created_at
                    FROM articles 
                    ORDER BY created_at DESC
                ''')
                
                rows = cursor.fetchall()
                self.articles = []
                
                for row in rows:
                    self.articles.append({
                        'id': row[0],
                        'title': row[1] or '',
                        'authors': row[2] or '',
                        'abstract': row[3] or '',
                        'journal': row[4] or '',
                        'conference': row[5] or '',
                        'year': row[6],
                        'volume': row[7] or '',
                        'issue': row[8] or '',
                        'pages': row[9] or '',
                        'publisher': row[10] or '',
                        'doi': row[11] or '',
                        'url': row[12] or '',
                        'pdf_path': row[13] or '',
                        'citation': row[14] or '',
                        'keywords': row[15] or '',
                        'category': row[16] or self.get_text("general"),
                        'rating': row[17] or 0,
                        'read_status': bool(row[18]),
                        'favorite': bool(row[19]),
                        'notes': row[20] or '',
                        'created_at': row[21] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
            self.logger.info(f"✅ {len(self.articles)} مقاله بارگذاری شد")
            self.refresh_articles_list()
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری مقالات: {e}")
            self._show_error("load_articles_error", str(e))
    
    def on_search(self, event=None):
        """جستجو با تاخیر و مدیریت ترد"""
        search_term = self.search_entry.get().strip()
        
        # لغو جستجوی قبلی اگر در حال اجراست
        if self._search_thread and self._search_thread.is_alive():
            return
        
        # استفاده از ترد برای جستجوی غیرهمزمان
        self._search_thread = threading.Thread(
            target=self._perform_search_async,
            args=(search_term,),
            daemon=True
        )
        self._search_thread.start()
    
    def _perform_search_async(self, search_term):
        """انجام جستجو در ترد جداگانه"""
        # تاخیر برای جلوگیری از جستجوهای مکرر
        threading.Event().wait(0.3)  # 300ms delay
        
        with self._search_lock:
            self.search_term = search_term
            self.after(0, self.refresh_articles_list)
    
    def perform_search(self):
        """انجام جستجو"""
        self.on_search()
    
    def show_advanced_search(self):
        """نمایش جستجوی پیشرفته"""
        messagebox.showinfo(
            self.get_text("coming_soon"),
            self.get_text("advanced_search_coming_soon")
        )
    
    def on_filter_changed(self, choice):
        """هنگام تغییر فیلتر"""
        self.current_filter = choice
        self.refresh_articles_list()
    
    def on_sort_changed(self, choice):
        """هنگام تغییر مرتب‌سازی"""
        sort_map = {
            self.get_text("newest"): "newest",
            self.get_text("oldest"): "oldest", 
            self.get_text("highest_rated"): "rating",
            self.get_text("alphabetical"): "alphabetical"
        }
        self.sort_by = sort_map.get(choice, "newest")
        self.refresh_articles_list()
    
    def manage_categories(self):
        """مدیریت دسته‌بندی‌ها"""
        dialog = ManageCategoriesDialog(self, self.categories)
        self.wait_window(dialog)
        
        if dialog.result:
            self.categories = dialog.result
            if self.save_categories():
                category_values = [self.get_text("all")] + self.categories
                self.filter_combo.configure(values=category_values)
                self.refresh_articles_list()
    
    def import_from_doi(self):
        """وارد کردن مقاله از DOI"""
        dialog = ImportFromDOIDialog(self, self.categories)
        self.wait_window(dialog)
        
        if dialog.result:
            self.save_article(dialog.result)
    
    def show_statistics(self):
        """نمایش آمار و گزارش"""
        dialog = ArticleStatisticsDialog(self, self.articles)
        self.wait_window(dialog)
    
    def export_bibtex(self):
        """خروجی BibTeX بهبود یافته"""
        try:
            if not self.articles:
                messagebox.showwarning(
                    self.get_text("warning"), 
                    self.get_text("no_articles_export")
                )
                return
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".bib",
                filetypes=[
                    ("BibTeX files", "*.bib"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                title=self.get_text("save_bibtex_file")
            )
            
            if not file_path:
                return
            
            bibtex_content = self._generate_bibtex_content()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bibtex_content)
            
            self.logger.info(f"خروجی BibTeX ذخیره شد: {file_path}")
            messagebox.showinfo(
                self.get_text("success"), 
                self.get_text("bibtex_exported")
            )
                
        except Exception as e:
            self.logger.error(f"❌ خطا در خروجی BibTeX: {e}")
            self._show_error("bibtex_export_error", str(e))
    
    def _generate_bibtex_content(self):
        """تولید محتوای BibTeX"""
        bibtex_entries = []
        
        for article in self.articles:
            try:
                entry = self._create_bibtex_entry(article)
                bibtex_entries.append(entry)
            except Exception as e:
                self.logger.warning(f"خطا در ایجاد ورودی BibTeX برای مقاله {article.get('title')}: {e}")
                continue
        
        return "\n\n".join(bibtex_entries)
    
    def _create_bibtex_entry(self, article):
        """ایجاد یک ورودی BibTeX"""
        # ایجاد کلید منحصر به فرد
        first_author = self._extract_first_author(article['authors'])
        year = article['year'] or '0000'
        key_base = f"{first_author}{year}"
        
        # اطمینان از منحصر به فرد بودن کلید
        key = self._make_unique_key(key_base, article['title'])
        
        # تعیین نوع منبع
        entry_type = self._determine_entry_type(article)
        
        # ایجاد ورودی
        fields = [
            ("title", article['title']),
            ("author", article['authors']),
            ("year", str(article['year'])) if article['year'] else None,
            ("journal", article['journal']) if article['journal'] else None,
            ("booktitle", article['conference']) if article['conference'] else None,
            ("volume", article['volume']) if article['volume'] else None,
            ("number", article['issue']) if article['issue'] else None,
            ("pages", article['pages']) if article['pages'] else None,
            ("publisher", article['publisher']) if article['publisher'] else None,
            ("doi", article['doi']) if article['doi'] else None,
            ("url", article['url']) if article['url'] else None,
        ]
        
        field_lines = []
        for field in fields:
            if field and field[1]:
                field_lines.append(f"  {field[0]} = {{{field[1]}}},")
        
        fields_str = "\n".join(field_lines).rstrip(',')
        
        return f"@{entry_type}{{{key},\n{fields_str}\n}}"
    
    def _extract_first_author(self, authors):
        """استخراج نام نویسنده اول"""
        if not authors:
            return "Unknown"
        
        first_author = authors.split(',')[0].strip()
        return first_author.split()[-1] if first_author else "Unknown"
    
    def _make_unique_key(self, base_key, title):
        """ایجاد کلید منحصر به فرد"""
        # پیاده‌سازی منطق برای اطمینان از منحصر به فرد بودن
        return base_key
    
    def _determine_entry_type(self, article):
        """تعیین نوع منبع BibTeX"""
        if article['journal']:
            return "article"
        elif article['conference']:
            return "inproceedings"
        else:
            return "misc"

    def export_excel(self):
        """خروجی Excel بهبود یافته"""
        try:
            if not self.articles:
                messagebox.showwarning(
                    self.get_text("warning"), 
                    self.get_text("no_articles_export")
                )
                return
            
            # تبدیل داده‌ها به DataFrame
            data = []
            for article in self.articles:
                data.append({
                    self.get_text("title"): article['title'],
                    self.get_text("authors"): article['authors'],
                    self.get_text("abstract"): article['abstract'],
                    self.get_text("journal"): article['journal'],
                    self.get_text("conference"): article['conference'],
                    self.get_text("year"): article['year'],
                    self.get_text("volume"): article['volume'],
                    self.get_text("issue"): article['issue'],
                    self.get_text("pages"): article['pages'],
                    self.get_text("publisher"): article['publisher'],
                    self.get_text("doi"): article['doi'],
                    self.get_text("url"): article['url'],
                    self.get_text("keywords"): article['keywords'],
                    self.get_text("category"): article['category'],
                    self.get_text("rating"): article['rating'],
                    self.get_text("read_status"): self.get_text("read") if article['read_status'] else self.get_text("unread"),
                    self.get_text("favorite"): self.get_text("yes") if article['favorite'] else self.get_text("no"),
                    self.get_text("notes"): article['notes'],
                    self.get_text("created_date"): article['created_at']
                })
            
            df = pd.DataFrame(data)
            
            # ذخیره فایل
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title=self.get_text("save_excel_file")
            )
            
            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                self.logger.info(f"خروجی Excel ذخیره شد: {file_path}")
                messagebox.showinfo(
                    self.get_text("success"), 
                    self.get_text("excel_exported")
                )
                
        except Exception as e:
            self.logger.error(f"❌ خطا در خروجی Excel: {e}")
            self._show_error("excel_export_error", str(e))

    def import_excel(self):
        """وارد کردن از Excel با قابلیت تشخیص تکراری"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
                title=self.get_text("select_excel_file")
            )
            
            if not file_path:
                return
            
            # خواندن فایل Excel
            df = pd.read_excel(file_path)
            
            # بررسی ستون‌های ضروری
            required_columns = [self.get_text("title"), self.get_text("authors")]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror(
                    self.get_text("error"), 
                    f"{self.get_text('missing_columns')}: {', '.join(missing_columns)}"
                )
                return
            
            # وارد کردن داده‌ها
            success_count = 0
            duplicate_count = 0
            error_count = 0
            duplicate_titles = []
            
            for _, row in df.iterrows():
                try:
                    title = str(row[self.get_text("title")]).strip()
                    authors = str(row[self.get_text("authors")]).strip()
                    
                    # بررسی تکراری بودن مقاله
                    if self.is_duplicate_article(title, authors):
                        duplicate_count += 1
                        duplicate_titles.append(title)
                        continue
                    
                    # تبدیل داده‌های Excel به فرمت مقاله
                    article_data = {
                        'title': title,
                        'authors': authors,
                        'abstract': str(row.get(self.get_text("abstract"), '')),
                        'journal': str(row.get(self.get_text("journal"), '')),
                        'conference': str(row.get(self.get_text("conference"), '')),
                        'year': int(row[self.get_text("year")]) if pd.notna(row.get(self.get_text("year"))) and str(row.get(self.get_text("year"))).strip() else None,
                        'volume': str(row.get(self.get_text("volume"), '')),
                        'issue': str(row.get(self.get_text("issue"), '')),
                        'pages': str(row.get(self.get_text("pages"), '')),
                        'publisher': str(row.get(self.get_text("publisher"), '')),
                        'doi': str(row.get(self.get_text("doi"), '')),
                        'url': str(row.get(self.get_text("url"), '')),
                        'pdf_path': '',
                        'citation': '',
                        'keywords': str(row.get(self.get_text("keywords"), '')),
                        'category': str(row.get(self.get_text("category"), self.get_text("general"))),
                        'rating': int(row.get(self.get_text("rating"), 0)),
                        'read_status': str(row.get(self.get_text("read_status"), '')).strip().lower() in [self.get_text("read"), 'read', 'true', '1', 'yes'],
                        'favorite': str(row.get(self.get_text("favorite"), '')).strip().lower() in [self.get_text("yes"), 'yes', 'true', '1'],
                        'notes': str(row.get(self.get_text("notes"), ''))
                    }
                    
                    # ذخیره مقاله
                    if self.save_article_direct(article_data):
                        success_count += 1
                    else:
                        error_count += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ خطا در وارد کردن مقاله: {e}")
                    error_count += 1
            
            # نمایش یک گزارش نهایی
            self.show_import_report(success_count, duplicate_count, error_count, duplicate_titles)
            self.load_articles()
                
        except Exception as e:
            self.logger.error(f"❌ خطا در وارد کردن Excel: {e}")
            self._show_error("excel_import_error", str(e))

    def is_duplicate_article(self, title, authors):
        """بررسی تکراری بودن مقاله بر اساس عنوان و نویسندگان"""
        try:
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    'SELECT COUNT(*) FROM articles WHERE title = ? AND authors = ?',
                    (title, authors)
                )
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"خطا در بررسی تکراری: {e}")
            return False

    def save_article_direct(self, article_data):
        """ذخیره مستقیم مقاله بدون نمایش دیالوگ"""
        try:
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO articles (
                        title, authors, abstract, journal, conference, year, 
                        volume, issue, pages, publisher, doi, url, pdf_path, 
                        citation, keywords, category, rating, read_status, favorite, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data['title'], article_data['authors'], article_data['abstract'],
                    article_data['journal'], article_data['conference'], article_data['year'],
                    article_data['volume'], article_data['issue'], article_data['pages'],
                    article_data['publisher'], article_data['doi'], article_data['url'],
                    article_data['pdf_path'], article_data['citation'], article_data['keywords'],
                    article_data['category'], article_data['rating'], article_data['read_status'],
                    article_data['favorite'], article_data['notes']
                ))
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطا در ذخیره مقاله: {e}")
            return False

    def show_import_report(self, success_count, duplicate_count, error_count, duplicate_titles):
        """نمایش گزارش نهایی وارد کردن"""
        report_message = f"{self.get_text('import_completed')}\n\n"
        report_message += f"✅ {self.get_text('successful_imports')}: {success_count}\n"
        
        if duplicate_count > 0:
            report_message += f"⚠️ {self.get_text('duplicate_articles')}: {duplicate_count}\n"
            
        if error_count > 0:
            report_message += f"❌ {self.get_text('failed_imports')}: {error_count}\n"
        
        # نمایش لیست مقالات تکراری اگر وجود دارد
        if duplicate_titles:
            report_message += f"\n{self.get_text('duplicate_list')}:\n"
            for i, title in enumerate(duplicate_titles[:10]):  # نمایش حداکثر 10 مورد
                short_title = title[:50] + "..." if len(title) > 50 else title
                report_message += f"  {i+1}. {short_title}\n"
            
            if len(duplicate_titles) > 10:
                report_message += f"  ... و {len(duplicate_titles) - 10} {self.get_text('more_items')}\n"
        
        messagebox.showinfo(
            self.get_text("import_report"), 
            report_message
        )

    def get_font(self, size=12, weight="normal"):
        """دریافت فونت از font_manager"""
        try:
            if hasattr(self.app, 'font_manager') and self.app.font_manager:
                return self.app.font_manager.get_font(size=size, weight=weight)
            else:
                # Fallback font با پشتیبانی از فارسی
                return ctk.CTkFont(family="Tahoma", size=size, weight=weight)
        except:
            return ctk.CTkFont(family="Tahoma", size=size, weight=weight)


class AddArticleDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories, article=None):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories
        self.article = article
        self.result = None
        self.selected_file_path = None
        
        self.title(self.parent.get_text("edit_article") if article else self.parent.get_text("new_article"))
        self.geometry("1000x900")
        self.minsize(900, 800)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # فعال کردن کپی پیست برای تمام ویجت‌ها
        self.setup_copy_paste()
        
        self.create_ui()
        self.center_window()
        
        if article:
            self.fill_form()
    
    def get_text(self, key):
        """دریافت متن ترجمه شده"""
        return self.parent.get_text(key) if hasattr(self.parent, 'get_text') else key
    
    def setup_copy_paste(self):
        """فعال کردن کپی پیست برای تمام ویجت‌ها"""
        # bind global copy/paste
        self.bind('<Control-c>', self.copy_text)
        self.bind('<Control-v>', self.paste_text)
        self.bind('<Control-x>', self.cut_text)
        
        # bind right-click context menu
        self.bind('<Button-3>', self.show_context_menu)
        
        # bind برای تمام ویجت‌های متنی
        self.bind_children(self)
    
    def bind_children(self, widget):
        """بایند کردن رویدادها برای تمام فرزندان"""
        for child in widget.winfo_children():
            if isinstance(child, (ctk.CTkEntry, ctk.CTkTextbox)):
                child.bind('<Control-c>', self.copy_text)
                child.bind('<Control-v>', self.paste_text)
                child.bind('<Control-x>', self.cut_text)
                child.bind('<Button-3>', self.show_context_menu)
            self.bind_children(child)
    
    def show_context_menu(self, event):
        """نمایش منوی راست کلیک"""
        try:
            # ایجاد منو
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label=self.get_text("copy"), command=self.copy_text)
            context_menu.add_command(label=self.get_text("paste"), command=self.paste_text)
            context_menu.add_command(label=self.get_text("cut"), command=self.cut_text)
            
            # نمایش منو در موقعیت کلیک
            context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"خطا در نمایش منو: {e}")
    
    def copy_text(self, event=None):
        """کپی متن"""
        try:
            widget = self.focus_get()
            if widget:
                if hasattr(widget, 'get') and hasattr(widget, 'selection_get'):
                    # برای Entry
                    selected_text = widget.selection_get()
                    self.clipboard_clear()
                    self.clipboard_append(selected_text)
                elif hasattr(widget, 'get') and hasattr(widget, 'tag_ranges'):
                    # برای Textbox
                    try:
                        selected_text = widget.get('sel.first', 'sel.last')
                        self.clipboard_clear()
                        self.clipboard_append(selected_text)
                    except:
                        pass
        except Exception as e:
            print(f"خطا در کپی: {e}")
    
    def paste_text(self, event=None):
        """پیست متن"""
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, 'insert'):
                clipboard_text = self.clipboard_get()
                if hasattr(widget, 'delete') and hasattr(widget, 'select_present') and widget.select_present():
                    # حذف متن انتخاب شده
                    widget.delete('sel.first', 'sel.last')
                widget.insert('insert', clipboard_text)
        except Exception as e:
            print(f"خطا در پیست: {e}")
    
    def cut_text(self, event=None):
        """کات متن"""
        self.copy_text()
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, 'delete') and hasattr(widget, 'select_present') and widget.select_present():
                widget.delete('sel.first', 'sel.last')
        except:
            pass
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        width = 1000
        height = 900
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری دیالوگ"""
        # فریم اصلی
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # عنوان
        title_text = self.get_text("edit_article") if self.article else self.get_text("new_article")
        title = ctk.CTkLabel(
            main_frame,
            text=title_text,
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        # استفاده از Tabview برای سازماندهی بهتر
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        # ایجاد تب‌ها
        self.basic_tab = self.tabview.add("📝 " + self.get_text("basic_info"))
        self.details_tab = self.tabview.add("📋 " + self.get_text("additional_info")) 
        self.extra_tab = self.tabview.add("⭐ " + self.get_text("status_notes"))
        
        # تنظیم grid برای تب‌ها
        for tab in [self.basic_tab, self.details_tab, self.extra_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_columnconfigure(1, weight=1)
            tab.grid_rowconfigure(0, weight=0)
        
        self.create_basic_tab()
        self.create_details_tab()
        self.create_extra_tab()
        
        # دکمه‌های action
        self.create_action_buttons(main_frame)
    
    def create_basic_tab(self):
        """ایجاد تب اطلاعات اصلی"""
        # عنوان مقاله
        ctk.CTkLabel(
            self.basic_tab,
            text=self.get_text("title") + " *",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        self.title_entry = ctk.CTkEntry(
            self.basic_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text=self.get_text("title_placeholder")
        )
        self.title_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # نویسندگان
        ctk.CTkLabel(
            self.basic_tab,
            text=self.get_text("authors") + " *",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 5), padx=5)
        
        self.authors_entry = ctk.CTkEntry(
            self.basic_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text=self.get_text("authors_placeholder")
        )
        self.authors_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # چکیده
        ctk.CTkLabel(
            self.basic_tab,
            text=self.get_text("abstract"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 5), padx=5)
        
        self.abstract_text = ctk.CTkTextbox(
            self.basic_tab,
            height=150,
            font=self.parent.get_font(12),
            corner_radius=8
        )
        self.abstract_text.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # دسته‌بندی
        ctk.CTkLabel(
            self.basic_tab,
            text=self.get_text("category") + " *",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=6, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.category_combo = ctk.CTkComboBox(
            self.basic_tab,
            values=self.categories,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            dropdown_font=self.parent.get_font(12)
        )
        if self.categories:
            self.category_combo.set(self.categories[0])
        self.category_combo.grid(row=6, column=1, sticky="ew", pady=(5, 5), padx=5)
    
    def create_details_tab(self):
        """ایجاد تب اطلاعات تکمیلی"""
        # ژورنال و کنفرانس
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("journal"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=5)
        
        self.journal_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text=self.get_text("journal_placeholder")
        )
        self.journal_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("conference"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=0, column=1, sticky="w", pady=(10, 5), padx=5)
        
        self.conference_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text=self.get_text("conference_placeholder")
        )
        self.conference_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # سال و ناشر
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("year"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=2, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.year_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8,
            placeholder_text="2024"
        )
        self.year_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("publisher"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=2, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.publisher_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text=self.get_text("publisher_placeholder")
        )
        self.publisher_entry.grid(row=3, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # جلد و شماره
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("volume"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=4, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.volume_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8,
            placeholder_text="5"
        )
        self.volume_entry.grid(row=5, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("issue"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=4, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.issue_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8,
            placeholder_text="2"
        )
        self.issue_entry.grid(row=5, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # صفحات و کلمات کلیدی
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("pages"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=6, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.pages_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8,
            placeholder_text="1-10"
        )
        self.pages_entry.grid(row=7, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("keywords"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=6, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.keywords_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text=self.get_text("keywords_placeholder")
        )
        self.keywords_entry.grid(row=7, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # DOI و URL
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("doi"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=8, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.doi_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8,
            placeholder_text="10.1234/example.doi"
        )
        self.doi_entry.grid(row=9, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("url"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=8, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.url_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8,
            placeholder_text="https://example.com"
        )
        self.url_entry.grid(row=9, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # فایل PDF
        ctk.CTkLabel(
            self.details_tab,
            text=self.get_text("pdf_file"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        file_frame = ctk.CTkFrame(self.details_tab, fg_color="transparent")
        file_frame.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=5)
        
        self.file_btn = ctk.CTkButton(
            file_frame,
            text="📁 " + self.get_text("select_file"),
            command=self.select_file,
            height=40,
            width=160,
            font=self.parent.get_font(12),
            corner_radius=8,
            fg_color="#2196F3"
        )
        self.file_btn.pack(side="left")
        
        self.file_label = ctk.CTkLabel(
            file_frame,
            text=self.get_text("no_file_selected"),
            text_color=("#666666", "#AAAAAA"),
            font=self.parent.get_font(11),
            justify="right"
        )
        self.file_label.pack(side="left", padx=10)
    
    def create_extra_tab(self):
        """ایجاد تب وضعیت و یادداشت"""
        # وضعیت مطالعه و مورد علاقه
        status_frame = ctk.CTkFrame(self.extra_tab, fg_color="transparent")
        status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10, 20), padx=5)
        
        self.read_status = ctk.BooleanVar()
        read_checkbox = ctk.CTkCheckBox(
            status_frame,
            text=self.get_text("read_status"),
            variable=self.read_status,
            font=self.parent.get_font(13),
            corner_radius=6
        )
        read_checkbox.pack(side="right", padx=15)
        
        self.favorite_status = ctk.BooleanVar()
        favorite_checkbox = ctk.CTkCheckBox(
            status_frame,
            text=self.get_text("favorite"),
            variable=self.favorite_status,
            font=self.parent.get_font(13),
            corner_radius=6
        )
        favorite_checkbox.pack(side="right", padx=15)
        
        # امتیاز
        rating_frame = ctk.CTkFrame(self.extra_tab, fg_color="transparent")
        rating_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20), padx=5)
        
        ctk.CTkLabel(
            rating_frame,
            text=self.get_text("rating") + ":",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).pack(side="right", padx=10)
        
        self.rating_slider = ctk.CTkSlider(
            rating_frame,
            from_=0,
            to=5,
            number_of_steps=5,
            width=250,
            height=20
        )
        self.rating_slider.set(0)
        self.rating_slider.pack(side="right", fill="x", expand=True, padx=10)
        
        self.rating_value = ctk.CTkLabel(
            rating_frame,
            text="0",
            font=self.parent.get_font(13, "bold"),
            width=30
        )
        self.rating_value.pack(side="right")
        
        # یادداشت‌ها
        ctk.CTkLabel(
            self.extra_tab,
            text=self.get_text("notes"),
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        self.notes_text = ctk.CTkTextbox(
            self.extra_tab,
            height=200,
            font=self.parent.get_font(12),
            corner_radius=8
        )
        self.notes_text.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 10), padx=5)
        
        # Bind events
        self.rating_slider.configure(command=self.on_rating_changed)
    
    def create_action_buttons(self, parent):
        """ایجاد دکمه‌های action"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text=self.get_text("cancel"),
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=0, column=0, padx=10, sticky="w")
        
        ctk.CTkButton(
            btn_frame,
            text=self.get_text("save_article"),
            command=self.save,
            fg_color="#4CAF50",
            width=150,
            height=45,
            font=self.parent.get_font(12, "bold"),
            corner_radius=8
        ).grid(row=0, column=1, padx=10, sticky="e")
    
    def on_rating_changed(self, value):
        """هنگام تغییر امتیاز"""
        self.rating_value.configure(text=str(int(float(value))))
    
    def fill_form(self):
        """پر کردن فرم با داده‌های موجود"""
        if self.article:
            self.title_entry.insert(0, self.article['title'])
            self.authors_entry.insert(0, self.article['authors'])
            
            if self.article['abstract']:
                self.abstract_text.insert("1.0", self.article['abstract'])
            
            self.journal_entry.insert(0, self.article['journal'] or '')
            self.conference_entry.insert(0, self.article['conference'] or '')
            
            if self.article['year']:
                self.year_entry.insert(0, str(self.article['year']))
            
            self.volume_entry.insert(0, self.article['volume'] or '')
            self.issue_entry.insert(0, self.article['issue'] or '')
            self.pages_entry.insert(0, self.article['pages'] or '')
            self.publisher_entry.insert(0, self.article['publisher'] or '')
            self.doi_entry.insert(0, self.article['doi'] or '')
            self.url_entry.insert(0, self.article['url'] or '')
            self.keywords_entry.insert(0, self.article['keywords'] or '')
            
            if self.article['category']:
                self.category_combo.set(self.article['category'])
            
            if self.article['pdf_path']:
                self.selected_file_path = self.article['pdf_path']
                self.file_label.configure(text=os.path.basename(self.article['pdf_path']))
            
            if self.article['read_status']:
                self.read_status.set(True)
            
            if self.article['favorite']:
                self.favorite_status.set(True)
            
            if self.article['rating']:
                self.rating_slider.set(self.article['rating'])
                self.rating_value.configure(text=str(self.article['rating']))
            
            if self.article['notes']:
                self.notes_text.insert("1.0", self.article['notes'])
    
    def select_file(self):
        """انتخاب فایل PDF"""
        file_path = filedialog.askopenfilename(
            title=self.get_text("select_pdf_file"),
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
    
    def save(self):
        """ذخیره مقاله"""
        title = self.title_entry.get().strip()
        authors = self.authors_entry.get().strip()
        category = self.category_combo.get()
        
        if not title:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("title_required")
            )
            return
        
        if not authors:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("authors_required")
            )
            return
        
        if not category:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("category_required")
            )
            return
        
        # پردازش سال
        year = None
        try:
            year_text = self.year_entry.get().strip()
            if year_text:
                year = int(year_text)
                if year < 1900 or year > datetime.now().year + 5:
                    messagebox.showerror(
                        self.get_text("error"), 
                        self.get_text("invalid_year_range")
                    )
                    return
        except:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("invalid_year")
            )
            return
        
        self.result = {
            'title': title,
            'authors': authors,
            'abstract': self.abstract_text.get("1.0", "end-1c").strip(),
            'journal': self.journal_entry.get().strip(),
            'conference': self.conference_entry.get().strip(),
            'year': year,
            'volume': self.volume_entry.get().strip(),
            'issue': self.issue_entry.get().strip(),
            'pages': self.pages_entry.get().strip(),
            'publisher': self.publisher_entry.get().strip(),
            'doi': self.doi_entry.get().strip(),
            'url': self.url_entry.get().strip(),
            'pdf_path': self.selected_file_path or '',
            'citation': '',
            'keywords': self.keywords_entry.get().strip(),
            'category': category,
            'rating': int(self.rating_slider.get()),
            'read_status': self.read_status.get(),
            'favorite': self.favorite_status.get(),
            'notes': self.notes_text.get("1.0", "end-1c").strip()
        }
        
        self.destroy()
    
    def cancel(self):
        """انصراف"""
        self.destroy()


class ImportFromDOIDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories
        self.result = None
        
        self.title(parent.get_text("import_from_doi"))
        self.geometry("600x700")
        self.minsize(500, 600)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        # فعال کردن کپی پیست
        self.setup_copy_paste()
        
        self.create_ui()
        self.center_window()
        
        # تنظیم برای تغییر اندازه خودکار
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def get_text(self, key):
        """دریافت متن ترجمه شده"""
        return self.parent.get_text(key) if hasattr(self.parent, 'get_text') else key

    def setup_copy_paste(self):
        """فعال کردن کپی پیست"""
        self.bind('<Control-c>', self.copy_text)
        self.bind('<Control-v>', self.paste_text)
        self.bind('<Control-x>', self.cut_text)
        self.bind('<Button-3>', self.show_context_menu)
        
        self.bind_children(self)
    
    def bind_children(self, widget):
        """بایند کردن رویدادها برای تمام فرزندان"""
        for child in widget.winfo_children():
            if isinstance(child, (ctk.CTkEntry, ctk.CTkTextbox)):
                child.bind('<Control-c>', self.copy_text)
                child.bind('<Control-v>', self.paste_text)
                child.bind('<Control-x>', self.cut_text)
                child.bind('<Button-3>', self.show_context_menu)
            self.bind_children(child)
    
    def show_context_menu(self, event):
        """نمایش منوی راست کلیک"""
        try:
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label=self.get_text("copy"), command=self.copy_text)
            context_menu.add_command(label=self.get_text("paste"), command=self.paste_text)
            context_menu.add_command(label=self.get_text("cut"), command=self.cut_text)
            
            context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"خطا در نمایش منو: {e}")
    
    def copy_text(self, event=None):
        """کپی متن"""
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, 'selection_get'):
                selected_text = widget.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except:
            pass
    
    def paste_text(self, event=None):
        """پیست متن"""
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, 'insert'):
                clipboard_text = self.clipboard_get()
                if hasattr(widget, 'delete') and hasattr(widget, 'select_present') and widget.select_present():
                    widget.delete('sel.first', 'sel.last')
                widget.insert('insert', clipboard_text)
        except:
            pass
    
    def cut_text(self, event=None):
        """کات متن"""
        self.copy_text()
        try:
            widget = self.focus_get()
            if widget and hasattr(widget, 'delete') and hasattr(widget, 'select_present') and widget.select_present():
                widget.delete('sel.first', 'sel.last')
        except:
            pass
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        width = 600
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری بهینه شده"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # عنوان
        title_text = "🌐 " + self.get_text("import_from_doi")
        title = ctk.CTkLabel(
            main_frame,
            text=title_text,
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        # محتوای اصلی با اسکرول
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        
        # توضیحات
        desc_text = self.get_text("enter_doi_description")
        desc = ctk.CTkLabel(
            content_frame,
            text=desc_text,
            font=self.parent.get_font(12),
            wraplength=500,
            justify="right"
        )
        desc.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        # فیلد DOI
        doi_label_text = self.get_text("doi") + " *"
        ctk.CTkLabel(
            content_frame,
            text=doi_label_text,
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))
        
        self.doi_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text=self.get_text("doi_example"),
            height=42,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8
        )
        self.doi_entry.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        self.doi_entry.bind('<Return>', lambda e: self.fetch_doi_info())
        
        # دکمه دریافت اطلاعات
        fetch_btn_text = "🔍 " + self.get_text("fetch_data")
        fetch_btn = ctk.CTkButton(
            content_frame,
            text=fetch_btn_text,
            command=self.fetch_doi_info,
            height=45,
            fg_color="#2196F3",
            font=self.parent.get_font(13, "bold"),
            corner_radius=8
        )
        fetch_btn.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        
        # وضعیت
        self.status_label = ctk.CTkLabel(
            content_frame,
            text="",
            font=self.parent.get_font(12),
            text_color=("#666666", "#AAAAAA"),
            justify="right"
        )
        self.status_label.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(content_frame)
        self.progress_bar.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()
        
        # فرم اطلاعات (در ابتدا مخفی)
        self.form_frame = ctk.CTkFrame(content_frame, corner_radius=12)
        self.form_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 20))
        self.form_frame.grid_columnconfigure(0, weight=1)
        self.form_frame.grid_remove()
        
        # عنوان فرم
        form_title = ctk.CTkLabel(
            self.form_frame,
            text="📋 " + self.get_text("article_information"),
            font=self.parent.get_font(16, "bold"),
            justify="right"
        )
        form_title.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        
        # فیلدهای فرم
        fields = [
            ("title", "title", True, "entry"),
            ("authors", "authors", True, "entry"),
            ("abstract", "abstract", False, "textbox"),
            ("journal", "journal", False, "entry"),
            ("year", "year", False, "entry"),
            ("publisher", "publisher", False, "entry"),
            ("category", "category", True, "combo")
        ]
        
        current_row = 1
        for field_key, label_key, required, field_type in fields:
            label_text = self.get_text(label_key) + (" *" if required else "")
            ctk.CTkLabel(
                self.form_frame,
                text=label_text,
                font=self.parent.get_font(12, "bold"),
                justify="right"
            ).grid(row=current_row, column=0, sticky="w", pady=(10, 5), padx=15)
            
            if field_type == "textbox":
                widget = ctk.CTkTextbox(
                    self.form_frame, 
                    height=100,
                    font=self.parent.get_font(12),
                    corner_radius=8
                )
            elif field_type == "combo":
                widget = ctk.CTkComboBox(
                    self.form_frame,
                    values=self.categories,
                    height=40,
                    font=self.parent.get_font(12),
                    justify="right",
                    corner_radius=8,
                    dropdown_font=self.parent.get_font(12)
                )
                if self.categories:
                    widget.set(self.categories[0])
            else:
                widget = ctk.CTkEntry(
                    self.form_frame, 
                    height=40,
                    font=self.parent.get_font(12),
                    justify="right" if field_type != "year" else "left",
                    corner_radius=8
                )
            
            widget.grid(row=current_row + 1, column=0, sticky="ew", pady=(0, 10), padx=15)
            setattr(self, f"{field_key}_widget", widget)
            current_row += 2
        
        # دکمه‌های action
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text=self.get_text("cancel"),
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=0, column=0, padx=5, sticky="w")
        
        ctk.CTkButton(
            btn_frame,
            text=self.get_text("save_article"),
            command=self.save,
            fg_color="#4CAF50",
            width=150,
            height=45,
            font=self.parent.get_font(12, "bold"),
            corner_radius=8
        ).grid(row=0, column=1, padx=5, sticky="e")

    def fetch_doi_info(self):
        """دریافت اطلاعات از DOI"""
        doi = self.doi_entry.get().strip()
        if not doi:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("doi_required")
            )
            return
        
        # پاک کردن فرم قبلی
        self.form_frame.grid_remove()
        
        # نمایش progress bar
        self.progress_bar.grid()
        self.progress_bar.start()
        
        self.status_label.configure(text=self.get_text("fetching_data"))
        
        threading.Thread(target=self._fetch_doi_info_thread, args=(doi,), daemon=True).start()
    
    def _fetch_doi_info_thread(self, doi):
        """تابع ترد برای دریافت اطلاعات DOI"""
        try:
            # استفاده از چندین سرویس برای دریافت اطلاعات کامل
            article_data = self._fetch_from_crossref(doi)
            if not article_data.get('title'):
                article_data = self._fetch_from_datacite(doi)
            
            self.after(0, self._handle_fetch_result, article_data)
                
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=self.get_text("connection_error")))
            self.after(0, lambda: self.progress_bar.grid_remove())
            self.after(0, lambda: messagebox.showerror(
                self.get_text("error"), 
                f"{self.get_text('server_connection_error')}: {str(e)}"
            ))
    
    def _fetch_from_crossref(self, doi):
        """دریافت اطلاعات از Crossref"""
        try:
            url = f"https://api.crossref.org/works/{doi}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})
                
                return {
                    'title': message.get('title', [''])[0] if message.get('title') else '',
                    'authors': self._format_authors(message.get('author', [])),
                    'abstract': self._extract_abstract(message),
                    'year': message.get('published-print', {}).get('date-parts', [[None]])[0][0] or 
                           message.get('published-online', {}).get('date-parts', [[None]])[0][0] or
                           message.get('created', {}).get('date-parts', [[None]])[0][0],
                    'journal': message.get('container-title', [''])[0] if message.get('container-title') else '',
                    'publisher': message.get('publisher', ''),
                    'volume': message.get('volume', ''),
                    'issue': message.get('issue', ''),
                    'pages': message.get('page', ''),
                    'url': message.get('URL', ''),
                    'doi': doi
                }
        except:
            pass
        
        return {}
    
    def _fetch_from_datacite(self, doi):
        """دریافت اطلاعات از DataCite"""
        try:
            url = f"https://api.datacite.org/dois/{doi}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get('data', {}).get('attributes', {})
                
                return {
                    'title': attributes.get('titles', [{}])[0].get('title', '') if attributes.get('titles') else '',
                    'authors': self._format_datacite_authors(attributes.get('creators', [])),
                    'abstract': attributes.get('descriptions', [{}])[0].get('description', '') if attributes.get('descriptions') else '',
                    'year': attributes.get('publicationYear'),
                    'publisher': attributes.get('publisher', ''),
                    'url': attributes.get('url', ''),
                    'doi': doi
                }
        except:
            pass
        
        return {}
    
    def _format_authors(self, authors):
        """فرمت‌دهی لیست نویسندگان از Crossref"""
        if not authors:
            return ""
        
        formatted_authors = []
        for author in authors:
            given = author.get('given', '')
            family = author.get('family', '')
            if given and family:
                formatted_authors.append(f"{given} {family}")
            elif family:
                formatted_authors.append(family)
            elif given:
                formatted_authors.append(given)
        
        return ", ".join(formatted_authors) if formatted_authors else ""
    
    def _format_datacite_authors(self, creators):
        """فرمت‌دهی لیست نویسندگان از DataCite"""
        if not creators:
            return ""
        
        formatted_authors = []
        for creator in creators:
            name = creator.get('name', '')
            given_name = creator.get('givenName', '')
            family_name = creator.get('familyName', '')
            
            if given_name and family_name:
                formatted_authors.append(f"{given_name} {family_name}")
            elif name:
                formatted_authors.append(name)
        
        return ", ".join(formatted_authors) if formatted_authors else ""
    
    def _extract_abstract(self, message):
        """استخراج چکیده از پیام"""
        if message.get('abstract'):
            import re
            clean_abstract = re.sub('<[^<]+?>', '', message['abstract'])
            return clean_abstract
        
        return ""
    
    def _handle_fetch_result(self, article_data):
        """پردازش نتیجه دریافت اطلاعات"""
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        
        if not article_data.get('title'):
            self.status_label.configure(text=self.get_text("error_fetching"))
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("fetch_error")
            )
            return
        
        self.status_label.configure(text=self.get_text("data_retrieved"))
        self.fill_form_with_data(article_data)
    
    def fill_form_with_data(self, data):
        """پر کردن فرم با داده‌های دریافتی"""
        # پر کردن فیلدها
        if data.get('title'):
            self.title_widget.delete(0, 'end')
            self.title_widget.insert(0, data['title'])
        
        if data.get('authors'):
            self.authors_widget.delete(0, 'end')
            self.authors_widget.insert(0, data['authors'])
        
        if data.get('abstract'):
            self.abstract_widget.delete("1.0", "end")
            self.abstract_widget.insert("1.0", data['abstract'])
        
        if data.get('journal'):
            self.journal_widget.delete(0, 'end')
            self.journal_widget.insert(0, data['journal'])
        
        if data.get('year'):
            self.year_widget.delete(0, 'end')
            self.year_widget.insert(0, str(data['year']))
        
        if data.get('publisher'):
            self.publisher_widget.delete(0, 'end')
            self.publisher_widget.insert(0, data['publisher'])
        
        # نمایش فرم
        self.form_frame.grid()
        self.title_widget.focus_set()

    def save(self):
        """ذخیره مقاله"""
        title = self.title_widget.get().strip()
        authors = self.authors_widget.get().strip()
        category = self.category_widget.get()
        
        if not title:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("title_required")
            )
            return
        
        if not authors:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("authors_required")
            )
            return
        
        # پردازش سال
        year = None
        try:
            year_text = self.year_widget.get().strip()
            if year_text:
                year = int(year_text)
        except:
            pass  # سال اختیاری است
        
        self.result = {
            'title': title,
            'authors': authors,
            'abstract': self.abstract_widget.get("1.0", "end-1c").strip(),
            'journal': self.journal_widget.get().strip(),
            'conference': '',
            'year': year,
            'volume': '',
            'issue': '',
            'pages': '',
            'publisher': self.publisher_widget.get().strip(),
            'doi': self.doi_entry.get().strip(),
            'url': '',
            'pdf_path': '',
            'citation': '',
            'keywords': '',
            'category': category,
            'rating': 0,
            'read_status': False,
            'favorite': False,
            'notes': ''
        }
        
        self.destroy()
    
    def cancel(self):
        """انصراف"""
        self.destroy()


# سایر کلاس‌ها (ArticleDetailsDialog, ArticleStatisticsDialog, ManageCategoriesDialog) 
# با بهبودهای مشابه باقی می‌مانند اما به دلیل محدودیت طول کد، تغییرات جزئی دارند.

class ArticleDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, article):
        super().__init__(parent)
        self.parent = parent
        self.article = article
        
        self.title("👁️ " + parent.get_text("article_details"))
        self.geometry("800x700")
        self.minsize(700, 600)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def get_text(self, key):
        """دریافت متن ترجمه شده"""
        return self.parent.get_text(key) if hasattr(self.parent, 'get_text') else key
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        width = 800
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            main_frame,
            text="📄 " + self.get_text("article_details"),
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        content_frame = ctk.CTkScrollableFrame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        
        self.display_article_info(content_frame)
        
        ctk.CTkButton(
            main_frame,
            text=self.get_text("close"),
            command=self.destroy,
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=2, column=0, pady=20)
    
    def display_article_info(self, parent):
        """نمایش اطلاعات مقاله"""
        # ایجاد کارت‌های اطلاعات
        self.create_info_card(parent, "📝", self.get_text("title"), self.article['title'], 0)
        self.create_info_card(parent, "👤", self.get_text("authors"), self.article['authors'], 1)
        
        if self.article['abstract']:
            self.create_info_card(parent, "📋", self.get_text("abstract"), self.article['abstract'], 2, is_textbox=True)
        
        # اطلاعات انتشار
        publication_info = []
        if self.article['journal']:
            publication_info.append(f"📰 {self.article['journal']}")
        if self.article['conference']:
            publication_info.append(f"🎤 {self.article['conference']}")
        if self.article['year']:
            publication_info.append(f"📅 {self.article['year']}")
        if self.article['volume']:
            publication_info.append(f"📚 {self.get_text('volume')}: {self.article['volume']}")
        if self.article['issue']:
            publication_info.append(f"🔢 {self.get_text('issue')}: {self.article['issue']}")
        if self.article['pages']:
            publication_info.append(f"📄 {self.get_text('pages')}: {self.article['pages']}")
        
        if publication_info:
            self.create_info_card(parent, "🏢", self.get_text("publication_info"), "\n".join(publication_info), 3)
        
        # اطلاعات اضافی
        additional_info = []
        if self.article['publisher']:
            additional_info.append(f"🏛️ {self.get_text('publisher')}: {self.article['publisher']}")
        if self.article['doi']:
            additional_info.append(f"🔗 {self.get_text('doi')}: {self.article['doi']}")
        if self.article['url']:
            additional_info.append(f"🌐 {self.get_text('url')}: {self.article['url']}")
        if self.article['category']:
            additional_info.append(f"🏷️ {self.get_text('category')}: {self.article['category']}")
        
        if additional_info:
            self.create_info_card(parent, "ℹ️", self.get_text("additional_info"), "\n".join(additional_info), 4)
        
        # وضعیت و امتیاز
        status_info = []
        status_info.append(f"⭐ {self.get_text('rating')}: {'★' * self.article['rating']}{'☆' * (5 - self.article['rating'])}")
        status_info.append(f"📖 {self.get_text('read_status')}: {self.get_text('read') if self.article['read_status'] else self.get_text('unread')}")
        status_info.append(f"❤️ {self.get_text('favorite')}: {self.get_text('yes') if self.article['favorite'] else self.get_text('no')}")
        
        self.create_info_card(parent, "📊", self.get_text("status"), "\n".join(status_info), 5)
        
        if self.article['notes']:
            self.create_info_card(parent, "💭", self.get_text("notes"), self.article['notes'], 6, is_textbox=True)
    
    def create_info_card(self, parent, icon, title, content, row, is_textbox=False):
        """ایجاد کارت اطلاعات"""
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", pady=8)
        card.grid_columnconfigure(0, weight=1)
        
        # هدر کارت
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 8))
        
        ctk.CTkLabel(
            header_frame,
            text=f"{icon} {title}",
            font=self.parent.get_font(14, "bold"),
            justify="right"
        ).grid(row=0, column=0, sticky="w")
        
        # محتوای کارت
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        content_frame.grid_columnconfigure(0, weight=1)
        
        if is_textbox:
            content_widget = ctk.CTkTextbox(
                content_frame,
                height=120,
                font=self.parent.get_font(12),
                wrap="word"
            )
            content_widget.insert("1.0", content)
            content_widget.configure(state="disabled")
        else:
            content_widget = ctk.CTkLabel(
                content_frame,
                text=content,
                font=self.parent.get_font(12),
                wraplength=700,
                justify="right"
            )
        
        content_widget.grid(row=0, column=0, sticky="ew")


# بقیه کلاس‌ها (ArticleStatisticsDialog, ManageCategoriesDialog) 
# با بهبودهای مشابه باقی می‌مانند...

class ArticleStatisticsDialog(ctk.CTkToplevel):
    def __init__(self, parent, articles):
        super().__init__(parent)
        self.articles = articles
        self.parent = parent
        
        self.title("📊 " + parent.get_text("statistics"))
        self.geometry("900x800")
        self.minsize(800, 700)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def get_text(self, key):
        return self.parent.get_text(key)
    
    def center_window(self):
        self.update_idletasks()
        width = 900
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            main_frame,
            text="📊 " + self.get_text("statistics"),
            font=self.parent.get_font(20, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        content_scroll = ctk.CTkScrollableFrame(main_frame)
        content_scroll.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        content_scroll.grid_columnconfigure(0, weight=1)
        
        stats = self.calculate_statistics()
        
        # کارت‌های آمار اصلی
        self.create_stat_card(content_scroll, "📚", self.get_text("total_articles"), 
                             str(stats['total_articles']), "#2196F3", 0)
        self.create_stat_card(content_scroll, "✅", self.get_text("read_articles"), 
                             f"{stats['read_articles']} ({stats['read_percentage']}%)", "#4CAF50", 1)
        self.create_stat_card(content_scroll, "❤️", self.get_text("favorite_articles"), 
                             str(stats['favorite_articles']), "#f44336", 2)
        self.create_stat_card(content_scroll, "⭐", self.get_text("average_rating"), 
                             f"{stats['avg_rating']:.1f}/5", "#FF9800", 3)
        
        # توزیع‌ها
        self.create_distribution_section(content_scroll, "📊", self.get_text("category_distribution"), 
                                       stats['category_distribution'], 4)
        self.create_distribution_section(content_scroll, "📅", self.get_text("year_distribution"), 
                                       stats['year_distribution'], 5)
        
        ctk.CTkButton(
            main_frame,
            text=self.get_text("close"),
            command=self.destroy,
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=2, column=0, pady=20)
    
    def calculate_statistics(self):
        total = len(self.articles)
        read = sum(1 for article in self.articles if article['read_status'])
        favorites = sum(1 for article in self.articles if article['favorite'])
        avg_rating = sum(article['rating'] for article in self.articles) / total if total > 0 else 0
        
        category_dist = {}
        year_dist = {}
        
        for article in self.articles:
            category = article['category']
            category_dist[category] = category_dist.get(category, 0) + 1
            
            if article['year']:
                year = article['year']
                year_dist[year] = year_dist.get(year, 0) + 1
        
        return {
            'total_articles': total,
            'read_articles': read,
            'read_percentage': round((read / total) * 100, 1) if total > 0 else 0,
            'favorite_articles': favorites,
            'avg_rating': avg_rating,
            'category_distribution': category_dist,
            'year_distribution': year_dist
        }
    
    def create_stat_card(self, parent, icon, title, value, color, row):
        card = ctk.CTkFrame(
            parent,
            border_width=2,
            border_color=("#E0E0E0", "#404040"),
            corner_radius=15
        )
        card.grid(row=row, column=0, sticky="ew", pady=8)
        
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            content_frame,
            text=f"{icon} {title}",
            font=self.parent.get_font(14),
            text_color=("#666666", "#AAAAAA"),
            justify="right"
        ).grid(row=0, column=0, sticky="w")
        
        ctk.CTkLabel(
            content_frame,
            text=value,
            font=self.parent.get_font(24, "bold"),
            text_color=color,
            justify="right"
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
    
    def create_distribution_section(self, parent, icon, title, distribution, start_row):
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.grid(row=start_row, column=0, sticky="ew", pady=15)
        section_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            section_frame,
            text=f"{icon} {title}",
            font=self.parent.get_font(16, "bold"),
            justify="right"
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        if not distribution:
            ctk.CTkLabel(
                section_frame,
                text=self.get_text("no_data"),
                font=self.parent.get_font(12),
                text_color=("#666666", "#AAAAAA"),
                justify="right"
            ).grid(row=1, column=0, sticky="w")
            return
        
        row_idx = 1
        for item, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True)[:10]:  # نمایش 10 مورد برتر
            item_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            item_frame.grid(row=row_idx, column=0, sticky="ew", pady=4)
            item_frame.grid_columnconfigure(0, weight=1)
            
            # نوار پیشرفت
            progress_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            progress_frame.grid(row=0, column=0, sticky="ew")
            progress_frame.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(
                progress_frame,
                text=str(item),
                font=self.parent.get_font(13),
                justify="right",
                width=200
            ).grid(row=0, column=0, sticky="w")
            
            # progress bar
            total = sum(distribution.values())
            percentage = (count / total) * 100 if total > 0 else 0
            
            progress = ctk.CTkProgressBar(progress_frame)
            progress.grid(row=0, column=1, sticky="ew", padx=10)
            progress.set(percentage / 100)
            
            ctk.CTkLabel(
                progress_frame,
                text=f"{count} ({percentage:.1f}%)",
                font=self.parent.get_font(13, "bold"),
                justify="right",
                width=80
            ).grid(row=0, column=2, sticky="e")
            
            row_idx += 1


class ManageCategoriesDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories.copy()
        self.result = None
        
        self.title("🗂️ " + parent.get_text("manage_categories"))
        self.geometry("600x700")
        self.minsize(500, 600)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def get_text(self, key):
        return self.parent.get_text(key)
    
    def center_window(self):
        self.update_idletasks()
        width = 600
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            main_frame,
            text="🗂️ " + self.get_text("manage_categories"),
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        self.list_frame = ctk.CTkScrollableFrame(main_frame)
        self.list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        self.category_widgets = []
        self.refresh_category_list()
        
        add_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        add_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        add_frame.grid_columnconfigure(0, weight=1)
        
        self.new_category_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text=self.get_text("new_category_placeholder"),
            height=45,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8
        )
        self.new_category_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.new_category_entry.bind('<Return>', lambda e: self.add_category())
        
        ctk.CTkButton(
            add_frame,
            text="➕ " + self.get_text("add"),
            command=self.add_category,
            width=100,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8,
            fg_color="#4CAF50"
        ).grid(row=0, column=1)
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text=self.get_text("cancel"),
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=0, column=0, padx=5, sticky="w")
        
        ctk.CTkButton(
            btn_frame,
            text=self.get_text("save_changes"),
            command=self.save,
            fg_color="#4CAF50",
            width=150,
            height=45,
            font=self.parent.get_font(12, "bold"),
            corner_radius=8
        ).grid(row=0, column=1, padx=5, sticky="e")
    
    def refresh_category_list(self):
        for widget in self.category_widgets:
            widget.destroy()
        
        self.category_widgets = []
        
        if not self.categories:
            empty_label = ctk.CTkLabel(
                self.list_frame,
                text=self.get_text("no_categories"),
                font=self.parent.get_font(14),
                text_color=("#666666", "#AAAAAA"),
                justify="center"
            )
            empty_label.grid(row=0, column=0, pady=40, sticky="nsew")
            self.category_widgets.append(empty_label)
            return
        
        for i, category in enumerate(self.categories):
            self.create_category_item(category, i)
    
    def create_category_item(self, category, index):
        item_frame = ctk.CTkFrame(self.list_frame, corner_radius=12)
        item_frame.grid(row=index, column=0, sticky="ew", pady=4)
        item_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            item_frame,
            text=category,
            font=self.parent.get_font(13),
            justify="right"
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        action_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        action_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        ctk.CTkButton(
            action_frame,
            text="✏️",
            width=45,
            height=35,
            fg_color="#2196F3",
            hover_color="#1976D2",
            command=lambda cat=category: self.edit_category(cat),
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=0, column=0, padx=3)
        
        ctk.CTkButton(
            action_frame,
            text="🗑️",
            width=45,
            height=35,
            fg_color="#f44336",
            hover_color="#d32f2f",
            command=lambda idx=index: self.delete_category(idx),
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=0, column=1, padx=3)
        
        self.category_widgets.append(item_frame)
    
    def add_category(self):
        new_category = self.new_category_entry.get().strip()
        if not new_category:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("category_name_required")
            )
            return
        
        if new_category in self.categories:
            messagebox.showerror(
                self.get_text("error"), 
                self.get_text("category_exists")
            )
            return
        
        self.categories.append(new_category)
        self.refresh_category_list()
        self.new_category_entry.delete(0, 'end')
    
    def delete_category(self, index):
        category_name = self.categories[index]
        confirm_message = self.get_text("confirm_delete_category").format(category_name)
        if messagebox.askyesno(self.get_text("confirm"), confirm_message):
            self.categories.pop(index)
            self.refresh_category_list()
    
    def edit_category(self, old_category):
        new_category = ctk.CTkInputDialog(
            text=f"{self.get_text('enter_new_category_name')} '{old_category}':",
            title=self.get_text("edit_category")
        ).get_input()
        
        if new_category and new_category.strip():
            index = self.categories.index(old_category)
            self.categories[index] = new_category.strip()
            self.refresh_category_list()
    
    def save(self):
        self.result = self.categories
        self.destroy()
    
    def cancel(self):
        self.destroy()