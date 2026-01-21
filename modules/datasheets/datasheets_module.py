import customtkinter as ctk
import os
import json
import sqlite3
from tkinter import filedialog, messagebox
import webbrowser
from datetime import datetime
import pandas as pd
from pathlib import Path
import shutil
import logging
import threading
import tkinter as tk
from core.base_module import BaseModule

class DatasheetsModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        
        # ابتدا language_manager را تنظیم کنید
        self.language_manager = app.language_manager if hasattr(app, 'language_manager') else None
        
        # داده‌ها
        self.datasheets = []
        self.categories = self.load_categories()
        self.current_filter = self.get_text("all")
        self.search_term = ""
        self.selected_file_path = None
        self.datasheet_widgets = []
        
        # تنظیمات جدید
        self.file_storage_path = Path("data/datasheets")
        self.file_storage_path.mkdir(parents=True, exist_ok=True)
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
        self.load_datasheets()
    
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
        title_text = self.get_text("datasheets_module_title")
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
            ("statistics", self.show_statistics, "#4CAF50", "📊"),
            ("export_excel", self.export_excel, "#4CAF50", "📤"),
            ("import_excel", self.import_excel, "#2196F3", "📥"),
            ("new_datasheet", self.show_add_dialog, "#2196F3", "➕")
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
        
        # لیست دیتاشیت‌ها
        self.create_datasheets_list(main_frame)
    
    def create_filter_bar(self, parent):
        """ایجاد نوار فیلتر و جستجوی پیشرفته"""
        filter_frame = ctk.CTkFrame(parent, height=70, corner_radius=12)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_propagate(False)
        filter_frame.grid_columnconfigure(0, weight=1)
        
        # سمت راست: جستجوی پیشرفته
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.grid(row=0, column=1, padx=20, pady=15, sticky="e")
        
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
        category_label.grid(row=0, column=1, padx=(10, 5), pady=5, sticky="e")
        
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
        self.filter_combo.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    def create_datasheets_list(self, parent):
        """ایجاد لیست دیتاشیت‌ها با طراحی بهتر"""
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
        empty_text = self.get_text("no_datasheets_found")
        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text=f"📋 {empty_text}",
            font=self.get_font(16),
            text_color=("#666666", "#AAAAAA"),
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=100, sticky="nsew")
        
        self.datasheet_widgets = []
    
    def load_categories(self):
        """بارگذاری دسته‌بندی‌های دیتاشیت‌ها"""
        categories_file = "data/datasheet_categories.json"
        
        # استفاده از مقادیر ترجمه شده برای دسته‌بندی‌های پیش‌فرض
        default_categories = [
            "الکترونیک", "مکانیک", "نرم‌افزار", "سخت‌افزار", 
            "برق", "دیتاشیت", "کاتالوگ", "مشخصات فنی",
            "گواهی", "گزارش", "آموزش", "استاندارد"
        ]
        
        try:
            os.makedirs('data', exist_ok=True)
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    loaded_categories = json.load(f)
                    return loaded_categories
            else:
                # اگر فایل وجود ندارد، دسته‌بندی‌های پیش‌فرض را ذخیره کن
                with open(categories_file, 'w', encoding='utf-8') as f:
                    json.dump(default_categories, f, ensure_ascii=False, indent=4)
                return default_categories
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری دسته‌بندی‌ها: {e}")
            return default_categories
    
    def save_categories(self):
        """ذخیره دسته‌بندی‌ها در فایل"""
        try:
            categories_file = "data/datasheet_categories.json"
            os.makedirs('data', exist_ok=True)
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"❌ خطا در ذخیره دسته‌بندی‌ها: {e}")
            self._show_error("save_categories_error", str(e))
            return False

    def manage_categories(self):
        """مدیریت دسته‌بندی‌ها - نسخه اصلاح شده"""
        try:
            dialog = ManageCategoriesDialog(self, self.categories)
            self.wait_window(dialog)
            
            if dialog.result is not None:
                self.categories = dialog.result
                if self.save_categories():
                    # به‌روزرسانی مقادیر combo box
                    category_values = [self.get_text("all")] + self.categories
                    self.filter_combo.configure(values=category_values)
                    self.refresh_datasheets_list()
                    messagebox.showinfo(
                        self.get_text("success"),
                        "دسته‌بندی‌ها با موفقیت به‌روزرسانی شدند"
                    )
        except Exception as e:
            self.logger.error(f"خطا در مدیریت دسته‌بندی‌ها: {e}")
            self._show_error("خطا در مدیریت دسته‌بندی‌ها", str(e))

    def init_database(self):
        """ایجاد جدول دیتاشیت‌ها در دیتابیس با مدیریت خطای بهتر"""
        try:
            # اطمینان از وجود پوشه دیتابیس
            os.makedirs('data', exist_ok=True)
            
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS datasheets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        online_link TEXT,
                        file_path TEXT,
                        file_type TEXT,
                        tags TEXT,
                        description TEXT,
                        file_size INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_access TIMESTAMP
                    )
                ''')
                
                # ایجاد ایندکس برای بهبود عملکرد
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasheets_name ON datasheets(name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasheets_category ON datasheets(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasheets_file_type ON datasheets(file_type)')
                
            self.logger.info("✅ جدول دیتاشیت‌ها ایجاد شد")
        except sqlite3.Error as e:
            self.logger.error(f"❌ خطای دیتابیس: {e}")
            self._show_error("خطای دیتابیس", str(e))
        except Exception as e:
            self.logger.error(f"❌ خطای غیرمنتظره در ایجاد دیتابیس: {e}")
            self._show_error("خطای دیتابیس", str(e))
    
    def refresh_datasheets_list(self):
        """تازه‌سازی لیست دیتاشیت‌ها با کشینگ"""
        # پاک کردن ویجت‌های قبلی
        for widget in self.datasheet_widgets:
            try:
                widget.destroy()
            except:
                pass
        self.datasheet_widgets = []
        
        # فیلتر کردن داده‌ها
        filtered_data = self.filter_datasheets()
        
        # نمایش برچسب خالی اگر داده‌ای نیست
        if not filtered_data:
            self.empty_label.grid(row=0, column=0, pady=80, sticky="nsew")
            return
        else:
            self.empty_label.grid_forget()
        
        # ایجاد کارت برای هر دیتاشیت
        for i, item in enumerate(filtered_data):
            self.create_datasheet_card(item, i)
    
    def filter_datasheets(self):
        """فیلتر کردن دیتاشیت‌ها بر اساس دسته‌بندی و جستجو"""
        filtered = self.datasheets
        
        # فیلتر بر اساس دسته‌بندی
        if self.current_filter != self.get_text("all"):
            filtered = [item for item in filtered if item['category'] == self.current_filter]
        
        # فیلتر بر اساس جستجو
        if self.search_term:
            search_lower = self.search_term.lower()
            filtered = [
                item for item in filtered 
                if (search_lower in item['name'].lower() or 
                    search_lower in item['description'].lower() or 
                    search_lower in item['tags'].lower() or
                    search_lower in item['file_type'].lower())
            ]
        
        return filtered
    
    def create_datasheet_card(self, item, index):
        """ایجاد کارت دیتاشیت با طراحی مدرن"""
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
        
        # نام و نوع فایل
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        
        # نام دیتاشیت با قابلیت کلیک
        name_label = ctk.CTkLabel(
            title_frame,
            text=item['name'],
            font=self.get_font(15, "bold"),
            wraplength=600,
            justify="right",
            anchor="e",
            cursor="hand2"
        )
        name_label.grid(row=0, column=0, sticky="ew", padx=(0, 15))
        name_label.bind("<Button-1>", lambda e: self.show_datasheet_details(item))
        
        # نوع فایل و سایز
        file_info_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        file_info_frame.grid(row=0, column=1, sticky="e")
        
        file_type_text = self._get_file_type_icon(item['file_type'])
        if item.get('file_size'):
            size_text = self._format_file_size(item['file_size'])
            file_type_text += f" • {size_text}"
        
        file_type_label = ctk.CTkLabel(
            file_info_frame,
            text=file_type_text,
            font=self.get_font(12),
            text_color=("#666666", "#AAAAAA")
        )
        file_type_label.pack()
        
        # اطلاعات دیتاشیت
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # توضیحات
        if item['description']:
            desc_short = item['description'][:150] + "..." if len(item['description']) > 150 else item['description']
            desc_label = ctk.CTkLabel(
                info_frame,
                text=desc_short,
                font=self.get_font(12),
                wraplength=600,
                justify="right",
                anchor="e"
            )
            desc_label.grid(row=0, column=0, sticky="ew")
        
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
            text=f"🏷️ {item['category']}",
            font=self.get_font(10, "bold"),
            text_color=("#2196F3", "#64B5F6"),
            padx=12,
            pady=6,
            corner_radius=15,
            fg_color=("#E3F2FD", "#0D47A1")
        )
        category_badge.pack(side="right", padx=(5, 0))
        
        # هشتگ‌ها
        if item['tags']:
            tags = [tag.strip() for tag in item['tags'].split(',') if tag.strip()]
            for tag in tags[:3]:  # حداکثر 3 هشتگ
                tag_badge = ctk.CTkLabel(
                    tags_frame,
                    text=f"#{tag}",
                    font=self.get_font(9, "bold"),
                    text_color=("#9C27B0", "#CE93D8"),
                    padx=8,
                    pady=4,
                    corner_radius=12,
                    fg_color=("#F3E5F5", "#4A148C")
                )
                tag_badge.pack(side="right", padx=(5, 0))
        
        # دکمه‌های action با طراحی بهتر
        action_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        action_frame.grid(row=0, column=0, sticky="w")
        
        # ایجاد دکمه‌های action
        buttons = [
            ("📄", self.open_file, "#2196F3", item, "open_file") if item.get('file_path') and os.path.exists(item['file_path']) else None,
            ("🌐", self.open_link, "#FF9800", item, "open_link") if item.get('online_link') else None,
            ("👁️", self.show_datasheet_details, "#4CAF50", item, "view_details"),
            ("✏️", self.edit_datasheet, "#9C27B0", item, "edit"),
            ("🗑️", self.delete_datasheet, "#f44336", item, "delete")
        ]
        
        for i, btn_info in enumerate([b for b in buttons if b is not None]):
            text, command, color, itm, tooltip = btn_info
            btn = ctk.CTkButton(
                action_frame,
                text=text,
                width=40,
                height=35,
                font=self.get_font(12),
                fg_color=color,
                hover_color=self.darken_color(color),
                command=lambda c=command, it=itm: c(it),
                corner_radius=8
            )
            btn.grid(row=0, column=i, padx=3)
        
        self.datasheet_widgets.append(card)
    
    def _add_hover_effect(self, widget):
        """افزودن effect hover به ویجت"""
        original_color = widget.cget("fg_color")
        
        def on_enter(event):
            widget.configure(fg_color=("#F5F5F5", "#363636"))
        
        def on_leave(event):
            widget.configure(fg_color=original_color)
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _get_file_type_icon(self, file_type):
        """دریافت آیکون بر اساس نوع فایل"""
        icons = {
            'pdf': '📄 PDF',
            'word': '📝 Word',
            'excel': '📊 Excel',
            'image': '🖼️ Image',
            'video': '🎥 Video',
            'archive': '📦 Archive',
            'code': '💻 Code',
            'text': '📃 Text'
        }
        return icons.get(file_type, '📁 File')
    
    def _format_file_size(self, size_bytes):
        """فرمت‌دهی سایز فایل"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def show_add_dialog(self):
        """نمایش دیالوگ افزودن دیتاشیت جدید"""
        dialog = AddDatasheetDialog(self, self.categories)
        self.wait_window(dialog)
        
        if dialog.result:
            self.save_datasheet(dialog.result)
    
    def edit_datasheet(self, item):
        """ویرایش دیتاشیت"""
        dialog = AddDatasheetDialog(self, self.categories, item)
        self.wait_window(dialog)
        
        if dialog.result:
            self.update_datasheet(item['id'], dialog.result)
    
    def _handle_file_upload(self, file_path, item_name):
        """مدیریت فایل آپلود شده با کپی به پوشه اختصاصی"""
        if not file_path or not os.path.exists(file_path):
            return "", 0, None
        
        try:
            # ایجاد نام فایل امن
            safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name[:50]  # محدودیت طول نام فایل
            file_extension = Path(file_path).suffix
            
            new_filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            new_file_path = self.file_storage_path / new_filename
            
            # کپی فایل به محل امن
            shutil.copy2(file_path, new_file_path)
            
            # محاسبه سایز فایل
            file_size = os.path.getsize(new_file_path)
            
            # تعیین نوع فایل
            file_type = self._determine_file_type(file_extension)
            
            self.logger.info(f"فایل ذخیره شد: {new_file_path} ({file_size} bytes)")
            
            return str(new_file_path), file_size, file_type
            
        except Exception as e:
            self.logger.error(f"خطا در مدیریت فایل: {e}")
            self._show_error("خطا در آپلود فایل", str(e))
            return "", 0, None
    
    def _determine_file_type(self, file_extension):
        """تعیین نوع فایل بر اساس پسوند"""
        file_types = {
            '.pdf': 'pdf',
            '.doc': 'word', '.docx': 'word',
            '.xls': 'excel', '.xlsx': 'excel',
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image', '.bmp': 'image',
            '.mp4': 'video', '.avi': 'video', '.mov': 'video', '.wmv': 'video',
            '.zip': 'archive', '.rar': 'archive', '.7z': 'archive', '.tar': 'archive',
            '.py': 'code', '.java': 'code', '.cpp': 'code', '.c': 'code', '.js': 'code', '.html': 'code', '.css': 'code',
            '.txt': 'text', '.md': 'text', '.rtf': 'text'
        }
        return file_types.get(file_extension.lower(), 'other')
    
    def save_datasheet(self, data):
        """ذخیره دیتاشیت جدید در دیتابیس"""
        try:
            # مدیریت فایل آپلود شده
            file_path, file_size, file_type = self._handle_file_upload(
                data.get('file_path'), data['name']
            )
            
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO datasheets (
                        name, category, online_link, file_path, file_type, 
                        tags, description, file_size
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['name'], data['category'], data['online_link'], file_path,
                    file_type, data['tags'], data['description'], file_size
                ))
                
            messagebox.showinfo(
                "موفقیت", 
                "دیتاشیت با موفقیت ذخیره شد"
            )
            self.load_datasheets()
            
        except sqlite3.IntegrityError:
            self._show_error("ورودی تکراری")
        except Exception as e:
            self.logger.error(f"❌ خطا در ذخیره دیتاشیت: {e}")
            self._show_error("خطا در ذخیره دیتاشیت", str(e))
    
    def update_datasheet(self, item_id, data):
        """بروزرسانی دیتاشیت"""
        try:
            # مدیریت فایل آپلود شده
            file_path, file_size, file_type = self._handle_file_upload(
                data.get('file_path'), data['name']
            )
            
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE datasheets 
                    SET name=?, category=?, online_link=?, file_path=?, file_type=?, 
                        tags=?, description=?, file_size=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (
                    data['name'], data['category'], data['online_link'], file_path,
                    file_type, data['tags'], data['description'], file_size, item_id
                ))
                
            messagebox.showinfo(
                "موفقیت", 
                "دیتاشیت با موفقیت به‌روزرسانی شد"
            )
            self.load_datasheets()
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بروزرسانی دیتاشیت: {e}")
            self._show_error("خطا در بروزرسانی دیتاشیت", str(e))
    
    def delete_datasheet(self, item):
        """حذف دیتاشیت"""
        confirm_message = f"آیا از حذف '{item['name']}' اطمینان دارید؟"
        if messagebox.askyesno("تأیید حذف", confirm_message):
            try:
                with sqlite3.connect('data/research_assistant.db') as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('DELETE FROM datasheets WHERE id=?', (item['id'],))
                    
                messagebox.showinfo(
                    "موفقیت", 
                    "دیتاشیت با موفقیت حذف شد"
                )
                self.load_datasheets()
                
            except Exception as e:
                self.logger.error(f"❌ خطا در حذف دیتاشیت: {e}")
                self._show_error("خطا در حذف دیتاشیت", str(e))
    
    def open_file(self, item):
        """باز کردن فایل با مدیریت خطای بهتر"""
        file_path = item.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning(
                "هشدار", 
                "فایل یافت نشد"
            )
            return
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            else:  # MacOS, Linux
                webbrowser.open(f"file://{file_path}")
                
            # به روزرسانی زمان آخرین دسترسی
            self._update_last_access(item['id'])
            
            self.logger.info(f"فایل باز شد: {file_path}")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در باز کردن فایل: {e}")
            self._show_error("خطا در باز کردن فایل", str(e))
    
    def open_link(self, item):
        """باز کردن لینک آنلاین"""
        try:
            if item.get('online_link'):
                webbrowser.open(item['online_link'])
                
                # به روزرسانی زمان آخرین دسترسی
                self._update_last_access(item['id'])
            else:
                messagebox.showwarning(
                    "هشدار", 
                    "لینک موجود نیست"
                )
        except Exception as e:
            self.logger.error(f"❌ خطا در باز کردن لینک: {e}")
            self._show_error("خطا در باز کردن لینک", str(e))
    
    def _update_last_access(self, item_id):
        """به روزرسانی زمان آخرین دسترسی"""
        try:
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE datasheets SET last_access=CURRENT_TIMESTAMP WHERE id=?',
                    (item_id,)
                )
        except Exception as e:
            self.logger.error(f"خطا در به روزرسانی زمان دسترسی: {e}")
    
    def show_datasheet_details(self, item):
        """نمایش جزئیات کامل دیتاشیت"""
        dialog = DatasheetDetailsDialog(self, item)
        self.wait_window(dialog)
    
    def load_datasheets(self):
        """بارگذاری دیتاشیت‌ها از دیتابیس"""
        try:
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, name, category, online_link, file_path, file_type, 
                           tags, description, file_size, created_at, last_access
                    FROM datasheets 
                    ORDER BY created_at DESC
                ''')
                
                rows = cursor.fetchall()
                self.datasheets = []
                
                for row in rows:
                    self.datasheets.append({
                        'id': row[0],
                        'name': row[1] or '',
                        'category': row[2] or 'عمومی',
                        'online_link': row[3] or '',
                        'file_path': row[4] or '',
                        'file_type': row[5] or 'other',
                        'tags': row[6] or '',
                        'description': row[7] or '',
                        'file_size': row[8],
                        'created_at': row[9] or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'last_access': row[10]
                    })
                
            self.logger.info(f"✅ {len(self.datasheets)} دیتاشیت بارگذاری شد")
            self.refresh_datasheets_list()
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری دیتاشیت‌ها: {e}")
            self._show_error("خطا در بارگذاری دیتاشیت‌ها", str(e))
    
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
            self.after(0, self.refresh_datasheets_list)
    
    def perform_search(self):
        """انجام جستجو"""
        self.on_search()
    
    def on_filter_changed(self, choice):
        """هنگام تغییر فیلتر - نمایش دیتاشیت‌های دسته‌بندی انتخاب شده"""
        self.current_filter = choice
        self.logger.info(f"فیلتر دسته‌بندی تغییر کرد به: {choice}")
        self.refresh_datasheets_list()
    
    def show_statistics(self):
        """نمایش آمار و گزارش"""
        dialog = DatasheetStatisticsDialog(self, self.datasheets)
        self.wait_window(dialog)
    
    def export_excel(self):
        """خروجی Excel بهبود یافته"""
        try:
            if not self.datasheets:
                messagebox.showwarning(
                    "هشدار", 
                    "هیچ دیتاشیتی برای خروجی وجود ندارد"
                )
                return
            
            # تبدیل داده‌ها به DataFrame
            data = []
            for item in self.datasheets:
                data.append({
                    "نام": item['name'],
                    "دسته‌بندی": item['category'],
                    "لینک آنلاین": item['online_link'],
                    "مسیر فایل": item['file_path'],
                    "نوع فایل": item['file_type'],
                    "سایز فایل": self._format_file_size(item['file_size']) if item['file_size'] else '',
                    "هشتگ‌ها": item['tags'],
                    "توضیحات": item['description'],
                    "تاریخ ایجاد": item['created_at'],
                    "آخرین دسترسی": item['last_access'] or "هرگز"
                })
            
            df = pd.DataFrame(data)
            
            # ذخیره فایل
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="ذخیره فایل اکسل"
            )
            
            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                self.logger.info(f"خروجی Excel ذخیره شد: {file_path}")
                messagebox.showinfo(
                    "موفقیت", 
                    "داده‌ها با موفقیت به اکسل export شدند"
                )
                
        except Exception as e:
            self.logger.error(f"❌ خطا در خروجی Excel: {e}")
            self._show_error("خطا در خروجی Excel", str(e))

    def import_excel(self):
        """وارد کردن از Excel با قابلیت تشخیص تکراری"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
                title="انتخاب فایل اکسل"
            )
            
            if not file_path:
                return
            
            # خواندن فایل Excel
            df = pd.read_excel(file_path)
            
            # بررسی ستون‌های ضروری
            required_columns = ["نام"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror(
                    "خطا", 
                    f"ستون‌های ضروری وجود ندارد: {', '.join(missing_columns)}"
                )
                return
            
            # وارد کردن داده‌ها
            success_count = 0
            duplicate_count = 0
            error_count = 0
            duplicate_names = []
            
            for _, row in df.iterrows():
                try:
                    name = str(row["نام"]).strip()
                    
                    # بررسی تکراری بودن دیتاشیت
                    if self.is_duplicate_datasheet(name):
                        duplicate_count += 1
                        duplicate_names.append(name)
                        continue
                    
                    # تبدیل داده‌های Excel به فرمت دیتاشیت
                    datasheet_data = {
                        'name': name,
                        'category': str(row.get("دسته‌بندی", "عمومی")),
                        'online_link': str(row.get("لینک آنلاین", '')),
                        'file_path': '',
                        'file_type': str(row.get("نوع فایل", 'other')),
                        'tags': str(row.get("هشتگ‌ها", '')),
                        'description': str(row.get("توضیحات", ''))
                    }
                    
                    # ذخیره دیتاشیت
                    if self.save_datasheet_direct(datasheet_data):
                        success_count += 1
                    else:
                        error_count += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ خطا در وارد کردن دیتاشیت: {e}")
                    error_count += 1
            
            # نمایش یک گزارش نهایی
            self.show_import_report(success_count, duplicate_count, error_count, duplicate_names)
            self.load_datasheets()
                
        except Exception as e:
            self.logger.error(f"❌ خطا در وارد کردن Excel: {e}")
            self._show_error("خطا در وارد کردن Excel", str(e))

    def is_duplicate_datasheet(self, name):
        """بررسی تکراری بودن دیتاشیت بر اساس نام"""
        try:
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    'SELECT COUNT(*) FROM datasheets WHERE name = ?',
                    (name,)
                )
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"خطا در بررسی تکراری: {e}")
            return False

    def save_datasheet_direct(self, datasheet_data):
        """ذخیره مستقیم دیتاشیت بدون نمایش دیالوگ"""
        try:
            with sqlite3.connect('data/research_assistant.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO datasheets (
                        name, category, online_link, file_path, file_type, tags, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datasheet_data['name'], datasheet_data['category'], datasheet_data['online_link'],
                    datasheet_data['file_path'], datasheet_data['file_type'], datasheet_data['tags'],
                    datasheet_data['description']
                ))
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطا در ذخیره دیتاشیت: {e}")
            return False

    def show_import_report(self, success_count, duplicate_count, error_count, duplicate_names):
        """نمایش گزارش نهایی وارد کردن"""
        report_message = f"وارد کردن داده‌ها تکمیل شد\n\n"
        report_message += f"✅ وارد کردن موفق: {success_count}\n"
        
        if duplicate_count > 0:
            report_message += f"⚠️ دیتاشیت‌های تکراری: {duplicate_count}\n"
            
        if error_count > 0:
            report_message += f"❌ خطا در وارد کردن: {error_count}\n"
        
        # نمایش لیست دیتاشیت‌های تکراری اگر وجود دارد
        if duplicate_names:
            report_message += f"\nلیست موارد تکراری:\n"
            for i, name in enumerate(duplicate_names[:10]):  # نمایش حداکثر 10 مورد
                short_name = name[:50] + "..." if len(name) > 50 else name
                report_message += f"  {i+1}. {short_name}\n"
            
            if len(duplicate_names) > 10:
                report_message += f"  ... و {len(duplicate_names) - 10} مورد دیگر\n"
        
        messagebox.showinfo(
            "گزارش وارد کردن", 
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


class ManageCategoriesDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories.copy()
        self.result = None
        
        self.title("🗂️ مدیریت دسته‌بندی‌ها")
        self.geometry("500x600")
        self.minsize(450, 500)
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
        width = 500
        height = 600
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # عنوان
        title = ctk.CTkLabel(
            main_frame,
            text="🗂️ مدیریت دسته‌بندی‌ها",
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        # توضیحات
        desc = ctk.CTkLabel(
            main_frame,
            text="مدیریت دسته‌بندی‌های دیتاشیت‌ها. می‌توانید دسته‌بندی‌ها را اضافه، ویرایش یا حذف کنید.",
            font=self.parent.get_font(12),
            wraplength=460,
            justify="right",
            text_color=("#666666", "#AAAAAA")
        )
        desc.grid(row=1, column=0, pady=(0, 20), sticky="ew")
        
        # لیست دسته‌بندی‌ها
        list_frame = ctk.CTkScrollableFrame(main_frame, height=300)
        list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.category_entries = []
        
        # ایجاد آیتم‌های دسته‌بندی
        for i, category in enumerate(self.categories):
            self.create_category_item(list_frame, category, i)
        
        # دکمه افزودن دسته‌بندی جدید
        add_btn = ctk.CTkButton(
            main_frame,
            text="➕ افزودن دسته‌بندی جدید",
            command=lambda: self.create_category_item(list_frame, "", len(self.category_entries)),
            height=40,
            font=self.parent.get_font(12),
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        add_btn.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        
        # دکمه‌های action
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text="انصراف",
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=0, column=0, padx=5, sticky="w")
        
        ctk.CTkButton(
            btn_frame,
            text="ذخیره تغییرات",
            command=self.save,
            fg_color="#2196F3",
            width=120,
            height=45,
            font=self.parent.get_font(12, "bold"),
            corner_radius=8
        ).grid(row=0, column=1, padx=5, sticky="e")
    
    def create_category_item(self, parent, category, index):
        """ایجاد آیتم دسته‌بندی"""
        item_frame = ctk.CTkFrame(parent, fg_color="transparent")
        item_frame.pack(fill="x", pady=5)
        item_frame.grid_columnconfigure(0, weight=1)
        
        entry = ctk.CTkEntry(
            item_frame,
            placeholder_text="نام دسته‌بندی",
            height=40,
            font=self.parent.get_font(12)
        )
        if category:
            entry.insert(0, category)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # دکمه حذف
        delete_btn = ctk.CTkButton(
            item_frame,
            text="🗑️",
            width=50,
            height=40,
            command=lambda idx=index: self.delete_category(idx),
            fg_color="#f44336",
            hover_color="#d32f2f",
            font=self.parent.get_font(12)
        )
        delete_btn.grid(row=0, column=1)
        
        # ذخیره reference
        if index < len(self.category_entries):
            self.category_entries[index] = entry
        else:
            self.category_entries.append(entry)
    
    def delete_category(self, index):
        """حذف دسته‌بندی"""
        if len(self.category_entries) <= 1:
            messagebox.showwarning(
                "هشدار",
                "حداقل یک دسته‌بندی باید وجود داشته باشد"
            )
            return
        
        # حذف از لیست
        self.category_entries.pop(index)
        
        # بازسازی لیست
        self.rebuild_categories_list()
    
    def rebuild_categories_list(self):
        """بازسازی لیست دسته‌بندی‌ها"""
        # پاک کردن فریم والد
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and hasattr(widget, 'category_item'):
                widget.destroy()
        
        # ایجاد مجدد آیتم‌ها
        list_frame = self.winfo_children()[0].winfo_children()[2]  # پیدا کردن فریم لیست
        for i, entry in enumerate(self.category_entries):
            self.create_category_item(list_frame, entry.get(), i)
    
    def save(self):
        """ذخیره تغییرات"""
        new_categories = []
        
        for entry in self.category_entries:
            category_name = entry.get().strip()
            if category_name:
                if category_name not in new_categories:
                    new_categories.append(category_name)
                else:
                    messagebox.showwarning(
                        "هشدار",
                        f"دسته‌بندی '{category_name}' تکراری است"
                    )
                    return
        
        if not new_categories:
            messagebox.showerror(
                "خطا",
                "حداقل یک دسته‌بندی باید وجود داشته باشد"
            )
            return
        
        self.result = new_categories
        self.destroy()
    
    def cancel(self):
        """انصراف"""
        self.result = None
        self.destroy()


class AddDatasheetDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories, item=None):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories
        self.item = item
        self.result = None
        self.selected_file_path = None
        
        self.title("ویرایش دیتاشیت" if item else "افزودن دیتاشیت جدید")
        self.geometry("800x750")
        self.minsize(700, 650)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
        
        if item:
            self.fill_form()
    
    def get_text(self, key):
        return self.parent.get_text(key)
    
    def center_window(self):
        self.update_idletasks()
        width = 800
        height = 750
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        title_text = "ویرایش دیتاشیت" if self.item else "افزودن دیتاشیت جدید"
        title = ctk.CTkLabel(
            main_frame,
            text=title_text,
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        # استفاده از Tabview
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        
        # ایجاد تب‌ها
        self.basic_tab = self.tabview.add("📝 اطلاعات اصلی")
        self.details_tab = self.tabview.add("🔗 لینک‌ها و فایل‌ها")
        
        # تنظیم grid برای تب‌ها
        for tab in [self.basic_tab, self.details_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_columnconfigure(1, weight=1)
        
        self.create_basic_tab()
        self.create_details_tab()
        
        # دکمه‌های action
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text="انصراف",
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=0, column=0, padx=10, sticky="w")
        
        ctk.CTkButton(
            btn_frame,
            text="ذخیره دیتاشیت",
            command=self.save,
            fg_color="#4CAF50",
            width=150,
            height=45,
            font=self.parent.get_font(12, "bold"),
            corner_radius=8
        ).grid(row=0, column=1, padx=10, sticky="e")
    
    def create_basic_tab(self):
        """ایجاد تب اطلاعات اصلی"""
        # نام دیتاشیت
        ctk.CTkLabel(
            self.basic_tab,
            text="نام دیتاشیت *",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        self.name_entry = ctk.CTkEntry(
            self.basic_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text="نام دیتاشیت را وارد کنید..."
        )
        self.name_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # دسته‌بندی
        ctk.CTkLabel(
            self.basic_tab,
            text="دسته‌بندی *",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=2, column=0, sticky="w", pady=(5, 5), padx=5)
        
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
        self.category_combo.grid(row=2, column=1, sticky="ew", pady=(5, 15), padx=5)
        
        # هشتگ‌ها
        ctk.CTkLabel(
            self.basic_tab,
            text="هشتگ‌ها (با کاما جدا کنید)",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 5), padx=5)
        
        self.tags_entry = ctk.CTkEntry(
            self.basic_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="right",
            corner_radius=8,
            placeholder_text="مثال: الکترونیک, آردوینو, سنسور"
        )
        self.tags_entry.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # توضیحات
        ctk.CTkLabel(
            self.basic_tab,
            text="توضیحات",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(5, 5), padx=5)
        
        self.desc_text = ctk.CTkTextbox(
            self.basic_tab,
            height=150,
            font=self.parent.get_font(12),
            corner_radius=8
        )
        self.desc_text.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=5)
    
    def create_details_tab(self):
        """ایجاد تب لینک‌ها و فایل‌ها"""
        # لینک آنلاین
        ctk.CTkLabel(
            self.details_tab,
            text="لینک آنلاین",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        self.link_entry = ctk.CTkEntry(
            self.details_tab,
            height=40,
            font=self.parent.get_font(12),
            justify="left",
            corner_radius=8,
            placeholder_text="https://example.com"
        )
        self.link_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20), padx=5)
        
        # فایل پیوست
        ctk.CTkLabel(
            self.details_tab,
            text="فایل پیوست",
            font=self.parent.get_font(13, "bold"),
            justify="right"
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        file_frame = ctk.CTkFrame(self.details_tab, fg_color="transparent")
        file_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20), padx=5)
        
        self.file_btn = ctk.CTkButton(
            file_frame,
            text="📁 انتخاب فایل",
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
            text="هیچ فایلی انتخاب نشده",
            text_color=("#666666", "#AAAAAA"),
            font=self.parent.get_font(11),
            justify="right"
        )
        self.file_label.pack(side="left", padx=10)
        
        # اطلاعات فایل
        self.file_info_label = ctk.CTkLabel(
            self.details_tab,
            text="",
            font=self.parent.get_font(10),
            text_color=("#666666", "#AAAAAA"),
            justify="right"
        )
        self.file_info_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 0), padx=5)
    
    def fill_form(self):
        """پر کردن فرم با داده‌های موجود"""
        if self.item:
            self.name_entry.insert(0, self.item['name'])
            
            if self.item['category']:
                self.category_combo.set(self.item['category'])
            
            if self.item['online_link']:
                self.link_entry.insert(0, self.item['online_link'])
            
            if self.item['tags']:
                self.tags_entry.insert(0, self.item['tags'])
            
            if self.item['description']:
                self.desc_text.insert("1.0", self.item['description'])
            
            if self.item['file_path']:
                self.selected_file_path = self.item['file_path']
                filename = os.path.basename(self.item['file_path'])
                self.file_label.configure(text=filename)
                
                # نمایش اطلاعات فایل
                if self.item.get('file_size'):
                    size_text = self.parent._format_file_size(self.item['file_size'])
                    file_type = self.item.get('file_type', 'unknown')
                    self.file_info_label.configure(
                        text=f"{filename} • {size_text} • {file_type.upper()}"
                    )
    
    def select_file(self):
        """انتخاب فایل"""
        file_path = filedialog.askopenfilename(
            title="انتخاب فایل",
            filetypes=[
                ("همه فایل‌ها", "*.*"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx *.doc"),
                ("Excel files", "*.xlsx *.xls"),
                ("Images", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("Videos", "*.mp4 *.avi *.mov *.wmv"),
                ("Archives", "*.zip *.rar *.7z *.tar"),
                ("Code files", "*.py *.java *.cpp *.c *.js *.html *.css"),
                ("Text files", "*.txt *.md *.rtf")
            ]
        )
        
        if file_path:
            self.selected_file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.configure(text=filename)
            
            # نمایش اطلاعات فایل
            try:
                file_size = os.path.getsize(file_path)
                size_text = self.parent._format_file_size(file_size)
                file_extension = Path(file_path).suffix
                file_type = self.parent._determine_file_type(file_extension)
                
                self.file_info_label.configure(
                    text=f"{filename} • {size_text} • {file_type.upper()}"
                )
            except Exception as e:
                self.file_info_label.configure(text=f"{filename}")
    
    def save(self):
        """ذخیره دیتاشیت"""
        name = self.name_entry.get().strip()
        category = self.category_combo.get()
        
        if not name:
            messagebox.showerror("خطا", "لطفاً نام دیتاشیت را وارد کنید")
            return
        
        if not category:
            messagebox.showerror("خطا", "لطفاً دسته‌بندی را انتخاب کنید")
            return
        
        self.result = {
            'name': name,
            'category': category,
            'online_link': self.link_entry.get().strip(),
            'file_path': self.selected_file_path,
            'tags': self.tags_entry.get().strip(),
            'description': self.desc_text.get("1.0", "end-1c").strip()
        }
        
        self.destroy()
    
    def cancel(self):
        """انصراف"""
        self.destroy()


class DatasheetDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, item):
        super().__init__(parent)
        self.parent = parent
        self.item = item
        
        self.title("👁️ جزئیات دیتاشیت")
        self.geometry("700x600")
        self.minsize(600, 500)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        width = 700
        height = 600
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
            text="📋 جزئیات دیتاشیت",
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        content_frame = ctk.CTkScrollableFrame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1)
        
        self.display_datasheet_info(content_frame)
        
        ctk.CTkButton(
            main_frame,
            text="بستن",
            command=self.destroy,
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=2, column=0, pady=20)
    
    def display_datasheet_info(self, parent):
        """نمایش اطلاعات دیتاشیت"""
        # ایجاد کارت‌های اطلاعات
        self.create_info_card(parent, "📝", "نام", self.item['name'], 0)
        
        if self.item['description']:
            self.create_info_card(parent, "📋", "توضیحات", self.item['description'], 1, is_textbox=True)
        
        # اطلاعات دسته‌بندی و فایل
        basic_info = []
        basic_info.append(f"🏷️ دسته‌بندی: {self.item['category']}")
        
        if self.item['file_type'] and self.item['file_type'] != 'other':
            basic_info.append(f"📄 نوع فایل: {self.item['file_type'].upper()}")
        
        if self.item.get('file_size'):
            size_text = self.parent._format_file_size(self.item['file_size'])
            basic_info.append(f"💾 سایز فایل: {size_text}")
        
        if basic_info:
            self.create_info_card(parent, "ℹ️", "اطلاعات پایه", "\n".join(basic_info), 2)
        
        # لینک‌ها و مسیرها
        link_info = []
        if self.item['online_link']:
            link_info.append(f"🌐 لینک آنلاین: {self.item['online_link']}")
        
        if self.item['file_path']:
            link_info.append(f"📁 مسیر فایل: {self.item['file_path']}")
        
        if link_info:
            self.create_info_card(parent, "🔗", "لینک‌ها و فایل‌ها", "\n".join(link_info), 3)
        
        # هشتگ‌ها
        if self.item['tags']:
            tags = [tag.strip() for tag in self.item['tags'].split(',') if tag.strip()]
            if tags:
                tags_text = " ".join([f"#{tag}" for tag in tags])
                self.create_info_card(parent, "🏷️", "هشتگ‌ها", tags_text, 4)
        
        # اطلاعات زمانی
        time_info = []
        time_info.append(f"📅 تاریخ ایجاد: {self.item['created_at']}")
        
        if self.item['last_access']:
            time_info.append(f"🕒 آخرین دسترسی: {self.item['last_access']}")
        else:
            time_info.append(f"🕒 آخرین دسترسی: هرگز")
        
        self.create_info_card(parent, "⏰", "اطلاعات زمانی", "\n".join(time_info), 5)
    
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
                wraplength=650,
                justify="right"
            )
        
        content_widget.grid(row=0, column=0, sticky="ew")


class DatasheetStatisticsDialog(ctk.CTkToplevel):
    def __init__(self, parent, datasheets):
        super().__init__(parent)
        self.datasheets = datasheets
        self.parent = parent
        
        self.title("📊 آمار دیتاشیت‌ها")
        self.geometry("800x700")
        self.minsize(700, 600)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        width = 800
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
            text="📊 آمار دیتاشیت‌ها",
            font=self.parent.get_font(20, "bold"),
            justify="right"
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        
        content_scroll = ctk.CTkScrollableFrame(main_frame)
        content_scroll.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        content_scroll.grid_columnconfigure(0, weight=1)
        
        stats = self.calculate_statistics()
        
        # کارت‌های آمار اصلی
        self.create_stat_card(content_scroll, "📚", "کل دیتاشیت‌ها", 
                             str(stats['total_datasheets']), "#2196F3", 0)
        self.create_stat_card(content_scroll, "📄", "دیتاشیت‌های دارای فایل", 
                             str(stats['total_files']), "#4CAF50", 1)
        self.create_stat_card(content_scroll, "💾", "حجم کل فایل‌ها", 
                             stats['total_size'], "#FF9800", 2)
        self.create_stat_card(content_scroll, "🔗", "دیتاشیت‌های دارای لینک", 
                             str(stats['total_links']), "#9C27B0", 3)
        
        # توزیع‌ها
        self.create_distribution_section(content_scroll, "📊", "توزیع دسته‌بندی‌ها", 
                                       stats['category_distribution'], 4)
        self.create_distribution_section(content_scroll, "📄", "توزیع نوع فایل", 
                                       stats['file_type_distribution'], 5)
        
        ctk.CTkButton(
            main_frame,
            text="بستن",
            command=self.destroy,
            width=120,
            height=45,
            font=self.parent.get_font(12),
            corner_radius=8
        ).grid(row=2, column=0, pady=20)
    
    def calculate_statistics(self):
        total = len(self.datasheets)
        total_files = sum(1 for item in self.datasheets if item['file_path'])
        total_links = sum(1 for item in self.datasheets if item['online_link'])
        total_size = sum(item.get('file_size', 0) for item in self.datasheets)
        
        category_dist = {}
        file_type_dist = {}
        
        for item in self.datasheets:
            category = item['category']
            category_dist[category] = category_dist.get(category, 0) + 1
            
            file_type = item.get('file_type', 'other')
            file_type_dist[file_type] = file_type_dist.get(file_type, 0) + 1
        
        return {
            'total_datasheets': total,
            'total_files': total_files,
            'total_links': total_links,
            'total_size': self.parent._format_file_size(total_size),
            'category_distribution': category_dist,
            'file_type_distribution': file_type_dist
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
                text="داده‌ای موجود نیست",
                font=self.parent.get_font(12),
                text_color=("#666666", "#AAAAAA"),
                justify="right"
            ).grid(row=1, column=0, sticky="w")
            return
        
        row_idx = 1
        for item, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
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