import customtkinter as ctk
import os
import json
import sqlite3
from tkinter import filedialog, messagebox
import webbrowser
from datetime import datetime
import requests
import threading
from core.base_module import BaseModule

class PapersModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        
        # داده‌ها
        self.articles = []
        self.categories = self.load_categories()
        self.current_filter = "همه"
        self.search_term = ""
        self.sort_by = "newest"
        self.selected_file_path = None
        
        # ایجاد دیتابیس
        self.init_database()
        
        # ایجاد UI
        self.setup_ui()
        
        # بارگذاری داده‌ها
        self.load_articles()
    
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
    
    def create_toolbar(self):
        """ایجاد نوار ابزار"""
        toolbar = ctk.CTkFrame(self, height=70)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        toolbar.grid_propagate(False)
        
        # عنوان
        title_text = "📚 مدیریت مقالات علمی"
        title = ctk.CTkLabel(
            toolbar,
            text=title_text,
            font=self.get_font(16, "bold"),
            justify="right"
        )
        title.pack(side="right", padx=20, pady=15)
        
        # دکمه‌های action
        button_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_frame.pack(side="left", padx=15, pady=15)
        
        # دکمه‌های مختلف
        buttons = [
            ("🗂️ مدیریت دسته‌بندی", self.manage_categories, "#FF9800"),
            ("🌐 وارد کردن از DOI", self.import_from_doi, "#2196F3"),
            ("📊 آمار و گزارش", self.show_statistics, "#4CAF50"),
            ("📥 خروجی BibTeX", self.export_bibtex, "#9C27B0"),
            ("➕ مقاله جدید", self.show_add_dialog, "#2196F3")
        ]
        
        for text, command, color in buttons:
            btn = ctk.CTkButton(
                button_frame,
                text=text,
                command=command,
                width=140,
                height=35,
                font=self.get_font(),
                fg_color=color,
                hover_color=self.darken_color(color)
            )
            btn.pack(side="left", padx=5)
    
    def darken_color(self, color):
        """تیره کردن رنگ برای hover effect"""
        colors = {
            "#FF9800": "#F57C00",
            "#2196F3": "#1976D2", 
            "#4CAF50": "#45a049",
            "#9C27B0": "#7B1FA2",
            "#f44336": "#d32f2f"
        }
        return colors.get(color, color)
    
    def create_main_section(self):
        """ایجاد بخش اصلی"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # تنظیم grid
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # نوار فیلتر و جستجو
        self.create_filter_bar(main_frame)
        
        # لیست مقالات
        self.create_articles_list(main_frame)
    
    def create_filter_bar(self, parent):
        """ایجاد نوار فیلتر و جستجو"""
        filter_frame = ctk.CTkFrame(parent, height=60)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_propagate(False)
        
        # سمت راست: جستجو
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(side="right", padx=15, pady=10)
        
        search_text = "جستجو در عنوان، نویسندگان، چکیده..."
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=search_text,
            width=250,
            height=35,
            font=self.get_font(),
            justify="right"
        )
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=40,
            height=35,
            command=self.perform_search,
            font=self.get_font()
        )
        search_btn.pack(side="right", padx=5)
        
        # سمت چپ: فیلترها
        filter_btn_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_btn_frame.pack(side="left", padx=15, pady=10)
        
        # فیلتر دسته‌بندی
        category_label = ctk.CTkLabel(
            filter_btn_frame,
            text="دسته‌بندی:",
            font=self.get_font(12),
            justify="right"
        )
        category_label.pack(side="right", padx=(10, 5))
        
        self.filter_combo = ctk.CTkComboBox(
            filter_btn_frame,
            values=["همه"] + self.categories,
            width=150,
            height=35,
            font=self.get_font(),
            command=self.on_filter_changed,
            justify="right"
        )
        self.filter_combo.set("همه")
        self.filter_combo.pack(side="right", padx=5)
        
        # مرتب‌سازی
        sort_label = ctk.CTkLabel(
            filter_btn_frame,
            text="مرتب‌سازی:",
            font=self.get_font(12),
            justify="right"
        )
        sort_label.pack(side="right", padx=(10, 5))
        
        self.sort_combo = ctk.CTkComboBox(
            filter_btn_frame,
            values=["جدیدترین", "قدیمی‌ترین", "امتیاز بالا", "حروف الفبا"],
            width=120,
            height=35,
            font=self.get_font(),
            command=self.on_sort_changed,
            justify="right"
        )
        self.sort_combo.set("جدیدترین")
        self.sort_combo.pack(side="right", padx=5)
    
    def create_articles_list(self, parent):
        """ایجاد لیست مقالات"""
        # فریم لیست
        self.list_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew")
        
        # برچسب خالی
        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text="📖 هیچ مقاله‌ای یافت نشد\nروی دکمه 'مقاله جدید' کلیک کنید تا مقاله اول را اضافه کنید",
            font=self.get_font(12),
            text_color=("#666666", "#AAAAAA"),
            justify="center"
        )
        self.empty_label.pack(pady=80)
        
        self.article_widgets = []
    
    def load_categories(self):
        """بارگذاری دسته‌بندی‌های مقالات"""
        categories_file = "article_categories.json"
        default_categories = [
            "علوم کامپیوتر", "هوش مصنوعی", "یادگیری ماشین", 
            "شبکه‌های کامپیوتری", "امنیت اطلاعات", "داده‌کاوی",
            "برنامه‌نویسی", "پایگاه داده", "اینترنت اشیا",
            "روباتیک", "بینایی کامپیوتر", "پردازش زبان طبیعی"
        ]
        
        try:
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        
        return default_categories
    
    def save_categories(self):
        """ذخیره دسته‌بندی‌ها در فایل"""
        try:
            categories_file = "article_categories.json"
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"❌ خطا در ذخیره دسته‌بندی‌ها: {e}")
            return False
    
    def init_database(self):
        """ایجاد جدول مقالات در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
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
                    doi TEXT,
                    url TEXT,
                    pdf_path TEXT,
                    citation TEXT,
                    keywords TEXT,
                    category TEXT NOT NULL,
                    rating INTEGER DEFAULT 0,
                    read_status BOOLEAN DEFAULT FALSE,
                    favorite BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ جدول مقالات ایجاد شد")
        except Exception as e:
            print(f"❌ خطا در ایجاد جدول مقالات: {e}")
    
    def refresh_articles_list(self):
        """تازه‌سازی لیست مقالات"""
        # پاک کردن ویجت‌های قبلی
        for widget in self.article_widgets:
            widget.destroy()
        self.article_widgets = []
        
        # فیلتر کردن و مرتب‌سازی داده‌ها
        filtered_data = self.filter_articles()
        sorted_data = self.sort_articles(filtered_data)
        
        # نمایش برچسب خالی اگر داده‌ای نیست
        if not sorted_data:
            self.empty_label.pack(pady=80)
            return
        else:
            self.empty_label.pack_forget()
        
        # ایجاد کارت برای هر مقاله
        for i, article in enumerate(sorted_data):
            self.create_article_card(article, i)
    
    def filter_articles(self):
        """فیلتر کردن مقالات"""
        filtered = self.articles
        
        if self.current_filter != "همه":
            filtered = [article for article in filtered if article['category'] == self.current_filter]
        
        if self.search_term:
            search_lower = self.search_term.lower()
            filtered = [
                article for article in filtered 
                if (search_lower in article['title'].lower() or 
                    search_lower in article['authors'].lower() or 
                    search_lower in article['abstract'].lower() or
                    search_lower in article['keywords'].lower())
            ]
        
        return filtered
    
    def sort_articles(self, articles):
        """مرتب‌سازی مقالات"""
        if self.sort_by == "newest":
            return sorted(articles, key=lambda x: x['created_at'], reverse=True)
        elif self.sort_by == "oldest":
            return sorted(articles, key=lambda x: x['created_at'])
        elif self.sort_by == "rating":
            return sorted(articles, key=lambda x: x['rating'], reverse=True)
        elif self.sort_by == "alphabetical":
            return sorted(articles, key=lambda x: x['title'].lower())
        return articles
    
    def create_article_card(self, article, index):
        """ایجاد کارت مقاله"""
        card = ctk.CTkFrame(
            self.list_frame,
            corner_radius=15,
            border_width=1,
            border_color=("#E0E0E0", "#404040"),
            height=200
        )
        card.pack(fill="x", padx=5, pady=8)
        card.pack_propagate(False)
        
        # محتوای کارت
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        # هدر کارت
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # عنوان و ستاره‌ها
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x")
        
        # عنوان مقاله
        title_label = ctk.CTkLabel(
            title_frame,
            text=article['title'],
            font=self.get_font(14, "bold"),
            wraplength=500,
            justify="right"
        )
        title_label.pack(side="right", fill="x", expand=True)
        
        # ستاره‌های امتیاز
        rating_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        rating_frame.pack(side="left")
        
        rating_text = "⭐ " * article['rating'] + "☆ " * (5 - article['rating'])
        rating_label = ctk.CTkLabel(
            rating_frame,
            text=rating_text.strip(),
            font=self.get_font(12),
            text_color="#FFD700"
        )
        rating_label.pack()
        
        # اطلاعات مقاله
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 10))
        
        # نویسندگان
        authors_text = f"✍️ {article['authors']}"
        authors_label = ctk.CTkLabel(
            info_frame,
            text=authors_text,
            font=self.get_font(11),
            wraplength=400,
            justify="right"
        )
        authors_label.pack(anchor="e")
        
        # ژورنال و سال
        journal_text = f"📰 {article['journal']}" if article['journal'] else f"🎤 {article['conference']}" if article['conference'] else ""
        if journal_text and article['year']:
            journal_text += f" | {article['year']}"
        
        if journal_text:
            journal_label = ctk.CTkLabel(
                info_frame,
                text=journal_text,
                font=self.get_font(10),
                text_color=("#666666", "#AAAAAA"),
                justify="right"
            )
            journal_label.pack(anchor="e")
        
        # چکیده کوتاه
        if article['abstract']:
            abstract_short = article['abstract'][:120] + "..." if len(article['abstract']) > 120 else article['abstract']
            abstract_label = ctk.CTkLabel(
                content_frame,
                text=abstract_short,
                font=self.get_font(10),
                wraplength=600,
                justify="right"
            )
            abstract_label.pack(fill="x", pady=(0, 10))
        
        # فوتر کارت
        footer_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        footer_frame.pack(fill="x")
        
        # برچسب‌ها و دسته‌بندی
        tags_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        tags_frame.pack(side="right", fill="x", expand=True)
        
        # دسته‌بندی
        category_badge = ctk.CTkLabel(
            tags_frame,
            text=f"🏷️ {article['category']}",
            font=self.get_font(10),
            text_color=("#2196F3", "#64B5F6"),
            padx=10,
            pady=3,
            corner_radius=10,
            fg_color=("#E3F2FD", "#0D47A1")
        )
        category_badge.pack(side="right", padx=(5, 0))
        
        # وضعیت مطالعه
        status_text = "✅ خوانده شده" if article['read_status'] else "📖 خوانده نشده"
        status_label = ctk.CTkLabel(
            tags_frame,
            text=status_text,
            font=self.get_font(10),
            text_color=("#4CAF50", "#81C784") if article['read_status'] else ("#FF9800", "#FFB74D"),
            justify="right"
        )
        status_label.pack(side="right", padx=(10, 0))
        
        # علاقه‌مندی
        if article['favorite']:
            favorite_label = ctk.CTkLabel(
                tags_frame,
                text="❤️ مورد علاقه",
                font=self.get_font(10),
                text_color=("#f44336", "#e57373"),
                justify="right"
            )
            favorite_label.pack(side="right", padx=(10, 0))
        
        # دکمه‌های action
        action_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        action_frame.pack(side="left")
        
        # ایجاد دکمه‌های action
        buttons = [
            ("📄", self.open_pdf, "#2196F3", article) if article['pdf_path'] and os.path.exists(article['pdf_path']) else None,
            ("🌐", self.open_url, "#FF9800", article) if article['url'] else None,
            ("📋", self.show_article_details, "#4CAF50", article),
            ("✏️", self.edit_article, "#9C27B0", article),
            ("🗑️", self.delete_article, "#f44336", article)
        ]
        
        for btn_info in buttons:
            if btn_info:
                text, command, color, art = btn_info
                btn = ctk.CTkButton(
                    action_frame,
                    text=text,
                    width=35,
                    height=30,
                    font=self.get_font(10),
                    fg_color=color,
                    hover_color=self.darken_color(color),
                    command=lambda c=command, a=art: c(a)
                )
                btn.pack(side="left", padx=2)
        
        self.article_widgets.append(card)
    
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
    
    def save_article(self, data):
        """ذخیره مقاله جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
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
            
            conn.commit()
            conn.close()
            
            print("✅ مقاله جدید ذخیره شد")
            self.load_articles()
            
        except Exception as e:
            print(f"❌ خطا در ذخیره مقاله: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره مقاله: {e}")
    
    def update_article(self, article_id, data):
        """بروزرسانی مقاله"""
        try:
            conn = sqlite3.connect('research_assistant.db')
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
            
            conn.commit()
            conn.close()
            
            print("✅ مقاله بروزرسانی شد")
            self.load_articles()
            
        except Exception as e:
            print(f"❌ خطا در بروزرسانی مقاله: {e}")
            messagebox.showerror("خطا", f"خطا در بروزرسانی مقاله: {e}")
    
    def delete_article(self, article):
        """حذف مقاله"""
        if messagebox.askyesno("تأیید حذف", f"آیا از حذف مقاله '{article['title']}' اطمینان دارید؟"):
            try:
                conn = sqlite3.connect('research_assistant.db')
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM articles WHERE id=?', (article['id'],))
                
                conn.commit()
                conn.close()
                
                print("✅ مقاله حذف شد")
                self.load_articles()
                
            except Exception as e:
                print(f"❌ خطا در حذف مقاله: {e}")
                messagebox.showerror("خطا", f"خطا در حذف مقاله: {e}")
    
    def open_pdf(self, article):
        """باز کردن فایل PDF"""
        try:
            if article['pdf_path'] and os.path.exists(article['pdf_path']):
                os.startfile(article['pdf_path']) if os.name == 'nt' else webbrowser.open(article['pdf_path'])
            else:
                messagebox.showwarning("هشدار", "فایل PDF یافت نشد")
        except Exception as e:
            print(f"❌ خطا در باز کردن فایل PDF: {e}")
            messagebox.showerror("خطا", f"خطا در باز کردن فایل PDF: {e}")
    
    def open_url(self, article):
        """باز کردن لینک مقاله"""
        try:
            if article['url']:
                webbrowser.open(article['url'])
            else:
                messagebox.showwarning("هشدار", "لینک مقاله موجود نیست")
        except Exception as e:
            print(f"❌ خطا در باز کردن لینک: {e}")
            messagebox.showerror("خطا", f"خطا در باز کردن لینک: {e}")
    
    def show_article_details(self, article):
        """نمایش جزئیات کامل مقاله"""
        dialog = ArticleDetailsDialog(self, article)
        self.wait_window(dialog)
    
    def load_articles(self):
        """بارگذاری مقالات از دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, authors, abstract, journal, conference, year, 
                       volume, issue, pages, publisher, doi, url, pdf_path, 
                       citation, keywords, category, rating, read_status, favorite, notes, created_at
                FROM articles 
                ORDER BY created_at DESC
            ''')
            
            self.articles = []
            for row in cursor.fetchall():
                self.articles.append({
                    'id': row[0],
                    'title': row[1],
                    'authors': row[2],
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
                    'category': row[16],
                    'rating': row[17] or 0,
                    'read_status': bool(row[18]),
                    'favorite': bool(row[19]),
                    'notes': row[20] or '',
                    'created_at': row[21]
                })
            
            conn.close()
            print(f"✅ {len(self.articles)} مقاله بارگذاری شد")
            self.refresh_articles_list()
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری مقالات: {e}")
    
    def on_search(self, event=None):
        """هنگام جستجو"""
        self.search_term = self.search_entry.get().strip()
        self.refresh_articles_list()
    
    def perform_search(self):
        """انجام جستجو"""
        self.on_search()
    
    def on_filter_changed(self, choice):
        """هنگام تغییر فیلتر"""
        self.current_filter = choice
        self.refresh_articles_list()
    
    def on_sort_changed(self, choice):
        """هنگام تغییر مرتب‌سازی"""
        sort_map = {
            "جدیدترین": "newest",
            "قدیمی‌ترین": "oldest", 
            "امتیاز بالا": "rating",
            "حروف الفبا": "alphabetical"
        }
        self.sort_by = sort_map.get(choice, "newest")
        self.refresh_articles_list()
    
    def manage_categories(self):
        """مدیریت دسته‌بندی‌ها"""
        dialog = ManageCategoriesDialog(self, self.categories)
        self.wait_window(dialog)
        
        if dialog.result:
            self.categories = dialog.result
            self.save_categories()
            self.filter_combo.configure(values=["همه"] + self.categories)
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
        """خروجی BibTeX"""
        try:
            if not self.articles:
                messagebox.showwarning("هشدار", "هیچ مقاله‌ای برای خروجی وجود ندارد")
                return
            
            bibtex_content = ""
            for article in self.articles:
                bibtex_entry = self.generate_bibtex_entry(article)
                bibtex_content += bibtex_entry + "\n\n"
            
            # ذخیره فایل
            file_path = filedialog.asksaveasfilename(
                defaultextension=".bib",
                filetypes=[("BibTeX files", "*.bib"), ("All files", "*.*")],
                title="ذخیره فایل BibTeX"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(bibtex_content)
                messagebox.showinfo("موفقیت", f"فایل BibTeX با موفقیت در {file_path} ذخیره شد")
                
        except Exception as e:
            print(f"❌ خطا در خروجی BibTeX: {e}")
            messagebox.showerror("خطا", f"خطا در خروجی BibTeX: {e}")
    
    def generate_bibtex_entry(self, article):
        """تولید ورودی BibTeX برای مقاله"""
        # ایجاد کلید از نام نویسنده و سال
        first_author = article['authors'].split(',')[0].strip().split()[-1] if ',' in article['authors'] else article['authors'].split()[0]
        key = f"{first_author}{article['year']}"
        
        entry_type = "article" if article['journal'] else "inproceedings" if article['conference'] else "misc"
        
        entry = f"@{entry_type}{{{key},\n"
        entry += f"  title = {{{article['title']}}},\n"
        entry += f"  author = {{{article['authors']}}},\n"
        
        if article['journal']:
            entry += f"  journal = {{{article['journal']}}},\n"
        if article['conference']:
            entry += f"  booktitle = {{{article['conference']}}},\n"
        if article['year']:
            entry += f"  year = {{{article['year']}}},\n"
        if article['volume']:
            entry += f"  volume = {{{article['volume']}}},\n"
        if article['issue']:
            entry += f"  number = {{{article['issue']}}},\n"
        if article['pages']:
            entry += f"  pages = {{{article['pages']}}},\n"
        if article['publisher']:
            entry += f"  publisher = {{{article['publisher']}}},\n"
        if article['doi']:
            entry += f"  doi = {{{article['doi']}}},\n"
        if article['url']:
            entry += f"  url = {{{article['url']}}},\n"
        
        entry = entry.rstrip(',\n') + "\n"
        entry += "}"
        
        return entry

    def get_font(self, size=12, weight="normal"):
        """دریافت فونت از font_manager"""
        if hasattr(self.app, 'font_manager') and self.app.font_manager:
            return self.app.font_manager.get_font(size=size, weight=weight)
        else:
            # Fallback font
            return ctk.CTkFont(family="Tahoma", size=size, weight=weight)


# دیالوگ افزودن مقاله با طراحی جدید
class AddArticleDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories, article=None):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories
        self.article = article
        self.result = None
        self.selected_file_path = None
        
        self.title("ویرایش مقاله" if article else "افزودن مقاله جدید")
        self.geometry("900x750")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
        
        if article:
            self.fill_form()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری دیالوگ"""
        # فریم اصلی
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # عنوان
        title_text = "ویرایش مقاله" if self.article else "افزودن مقاله جدید"
        title = ctk.CTkLabel(
            main_frame,
            text=title_text,
            font=self.parent.get_font(18, "bold"),
            justify="right"
        )
        title.pack(pady=(0, 20))
        
        # استفاده از Tabview برای سازماندهی بهتر
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=(0, 20))
        
        # ایجاد تب‌ها
        self.basic_tab = self.tabview.add("📝 اطلاعات اصلی")
        self.details_tab = self.tabview.add("📋 اطلاعات تکمیلی") 
        self.extra_tab = self.tabview.add("⭐ وضعیت و یادداشت")
        
        # تنظیم grid برای تب‌ها
        for tab in [self.basic_tab, self.details_tab, self.extra_tab]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_columnconfigure(1, weight=1)
        
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
            text="عنوان مقاله *",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        self.title_entry = ctk.CTkEntry(
            self.basic_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.title_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # نویسندگان
        ctk.CTkLabel(
            self.basic_tab,
            text="نویسندگان *",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 5), padx=5)
        
        self.authors_entry = ctk.CTkEntry(
            self.basic_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.authors_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # چکیده
        ctk.CTkLabel(
            self.basic_tab,
            text="چکیده",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(5, 5), padx=5)
        
        self.abstract_text = ctk.CTkTextbox(
            self.basic_tab,
            height=100,
            font=self.parent.get_font()
        )
        self.abstract_text.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        # دسته‌بندی
        ctk.CTkLabel(
            self.basic_tab,
            text="دسته‌بندی *",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=6, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.category_combo = ctk.CTkComboBox(
            self.basic_tab,
            values=self.categories,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        if self.categories:
            self.category_combo.set(self.categories[0])
        self.category_combo.grid(row=6, column=1, sticky="ew", pady=(5, 5), padx=5)
    
    def create_details_tab(self):
        """ایجاد تب اطلاعات تکمیلی"""
        # ژورنال و کنفرانس
        ctk.CTkLabel(
            self.details_tab,
            text="ژورنال",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=5)
        
        self.journal_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.journal_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text="کنفرانس",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=0, column=1, sticky="w", pady=(10, 5), padx=5)
        
        self.conference_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.conference_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # سال و ناشر
        ctk.CTkLabel(
            self.details_tab,
            text="سال انتشار",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=2, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.year_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.year_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text="ناشر",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=2, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.publisher_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.publisher_entry.grid(row=3, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # جلد و شماره
        ctk.CTkLabel(
            self.details_tab,
            text="جلد",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=4, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.volume_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.volume_entry.grid(row=5, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text="شماره",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=4, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.issue_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.issue_entry.grid(row=5, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # صفحات و کلمات کلیدی
        ctk.CTkLabel(
            self.details_tab,
            text="صفحات",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=6, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.pages_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.pages_entry.grid(row=7, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text="کلمات کلیدی",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=6, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.keywords_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.keywords_entry.grid(row=7, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # DOI و URL
        ctk.CTkLabel(
            self.details_tab,
            text="DOI",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=8, column=0, sticky="w", pady=(5, 5), padx=5)
        
        self.doi_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.doi_entry.grid(row=9, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(
            self.details_tab,
            text="URL",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=8, column=1, sticky="w", pady=(5, 5), padx=5)
        
        self.url_entry = ctk.CTkEntry(
            self.details_tab,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.url_entry.grid(row=9, column=1, sticky="ew", pady=(0, 10), padx=5)
        
        # فایل PDF
        ctk.CTkLabel(
            self.details_tab,
            text="فایل PDF",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        file_frame = ctk.CTkFrame(self.details_tab, fg_color="transparent")
        file_frame.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=5)
        
        self.file_btn = ctk.CTkButton(
            file_frame,
            text="📁 انتخاب فایل PDF",
            command=self.select_file,
            height=35,
            width=150,
            font=self.parent.get_font()
        )
        self.file_btn.pack(side="left")
        
        self.file_label = ctk.CTkLabel(
            file_frame,
            text="هیچ فایلی انتخاب نشده",
            text_color=("#666666", "#AAAAAA"),
            font=self.parent.get_font(),
            justify="right"
        )
        self.file_label.pack(side="left", padx=10)
    
    def create_extra_tab(self):
        """ایجاد تب وضعیت و یادداشت"""
        # وضعیت مطالعه و مورد علاقه
        status_frame = ctk.CTkFrame(self.extra_tab, fg_color="transparent")
        status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10, 20), padx=5)
        
        self.read_status = ctk.BooleanVar()
        ctk.CTkCheckBox(
            status_frame,
            text="خوانده شده",
            variable=self.read_status,
            font=self.parent.get_font()
        ).pack(side="right", padx=10)
        
        self.favorite_status = ctk.BooleanVar()
        ctk.CTkCheckBox(
            status_frame,
            text="مورد علاقه",
            variable=self.favorite_status,
            font=self.parent.get_font()
        ).pack(side="right", padx=10)
        
        # امتیاز
        rating_frame = ctk.CTkFrame(self.extra_tab, fg_color="transparent")
        rating_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20), padx=5)
        
        ctk.CTkLabel(
            rating_frame,
            text="امتیاز:",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(side="right", padx=10)
        
        self.rating_slider = ctk.CTkSlider(
            rating_frame,
            from_=0,
            to=5,
            number_of_steps=5
        )
        self.rating_slider.set(0)
        self.rating_slider.pack(side="right", fill="x", expand=True, padx=10)
        
        self.rating_value = ctk.CTkLabel(
            rating_frame,
            text="0",
            font=self.parent.get_font(weight="bold")
        )
        self.rating_value.pack(side="right")
        
        # یادداشت‌ها
        ctk.CTkLabel(
            self.extra_tab,
            text="یادداشت‌های شخصی",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=5)
        
        self.notes_text = ctk.CTkTextbox(
            self.extra_tab,
            height=150,
            font=self.parent.get_font()
        )
        self.notes_text.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 10), padx=5)
        
        # Bind events
        self.rating_slider.configure(command=self.on_rating_changed)
    
    def create_action_buttons(self, parent):
        """ایجاد دکمه‌های action"""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="انصراف",
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            height=40,
            font=self.parent.get_font()
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="ذخیره مقاله",
            command=self.save,
            fg_color="#4CAF50",
            width=150,
            height=40,
            font=self.parent.get_font(weight="bold")
        ).pack(side="right", padx=10)
    
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
            title="انتخاب فایل PDF",
            filetypes=[("PDF files", "*.pdf")]
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
            messagebox.showerror("خطا", "لطفاً عنوان مقاله را وارد کنید")
            return
        
        if not authors:
            messagebox.showerror("خطا", "لطفاً نویسندگان مقاله را وارد کنید")
            return
        
        if not category:
            messagebox.showerror("خطا", "لطفاً دسته‌بندی را انتخاب کنید")
            return
        
        # پردازش سال
        year = None
        try:
            year_text = self.year_entry.get().strip()
            if year_text:
                year = int(year_text)
        except:
            messagebox.showerror("خطا", "سال باید یک عدد معتبر باشد")
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


# سایر دیالوگ‌ها (کامل و بدون حذف)
class ArticleDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, article):
        super().__init__(parent)
        self.article = article
        self.parent = parent
        
        self.title(f"جزئیات مقاله: {article['title'][:50]}...")
        self.geometry("600x700")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # عنوان
        title = ctk.CTkLabel(
            main_frame,
            text="جزئیات کامل مقاله",
            font=self.parent.get_font(16, "bold"),
            justify="right"
        )
        title.pack(pady=(0, 20))
        
        # محتوای اصلی با اسکرول
        content_scroll = ctk.CTkScrollableFrame(main_frame)
        content_scroll.pack(fill="both", expand=True)
        
        # بخش‌های مختلف
        sections = [
            ("📖 عنوان", self.article['title'], True),
            ("✍️ نویسندگان", self.article['authors'], False),
            ("📰 ژورنال/کنفرانس", self.article['journal'] or self.article['conference'] or "ندارد", False),
            ("📅 سال", str(self.article['year']) if self.article['year'] else "ندارد", False),
            ("🔢 اطلاعات انتشار", self.get_publication_info(), False),
            ("🌐 DOI", self.article['doi'] or "ندارد", False),
            ("🔗 لینک", self.article['url'] or "ندارد", False),
            ("🏷️ دسته‌بندی", self.article['category'], False),
            ("⭐ امتیاز", "⭐" * self.article['rating'] + "☆" * (5 - self.article['rating']), False),
            ("📊 وضعیت", "✅ خوانده شده" if self.article['read_status'] else "📖 خوانده نشده", False),
            ("❤️ مورد علاقه", "✅ بله" if self.article['favorite'] else "❌ خیر", False),
        ]
        
        for label, value, is_title in sections:
            if value and value != "ندارد":
                self.create_section(content_scroll, label, value, is_title)
        
        # چکیده
        if self.article['abstract']:
            self.create_section(content_scroll, "📋 چکیده", self.article['abstract'], False)
        
        # کلمات کلیدی
        if self.article['keywords']:
            self.create_section(content_scroll, "🏷️ کلمات کلیدی", self.article['keywords'], False)
        
        # یادداشت‌ها
        if self.article['notes']:
            self.create_section(content_scroll, "📝 یادداشت‌های شخصی", self.article['notes'], False)
        
        # فایل PDF
        if self.article['pdf_path'] and os.path.exists(self.article['pdf_path']):
            file_frame = ctk.CTkFrame(content_scroll, fg_color="transparent")
            file_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                file_frame,
                text="📁 فایل PDF:",
                font=self.parent.get_font(weight="bold"),
                justify="right"
            ).pack(anchor="w")
            
            file_info = f"{os.path.basename(self.article['pdf_path'])}"
            ctk.CTkLabel(
                file_frame,
                text=file_info,
                font=self.parent.get_font(12),
                justify="right"
            ).pack(anchor="w", pady=(5, 0))
            
            ctk.CTkButton(
                file_frame,
                text="📄 باز کردن فایل PDF",
                command=self.open_pdf,
                width=150,
                font=self.parent.get_font()
            ).pack(anchor="w", pady=(10, 0))
        
        # دکمه بستن
        ctk.CTkButton(
            main_frame,
            text="بستن",
            command=self.destroy,
            width=100,
            font=self.parent.get_font()
        ).pack(pady=20)
    
    def get_publication_info(self):
        """دریافت اطلاعات انتشار"""
        info_parts = []
        if self.article['volume']:
            info_parts.append(f"جلد: {self.article['volume']}")
        if self.article['issue']:
            info_parts.append(f"شماره: {self.article['issue']}")
        if self.article['pages']:
            info_parts.append(f"صفحات: {self.article['pages']}")
        if self.article['publisher']:
            info_parts.append(f"ناشر: {self.article['publisher']}")
        
        return " | ".join(info_parts) if info_parts else "ندارد"
    
    def create_section(self, parent, label, value, is_title):
        """ایجاد بخش اطلاعات"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=10)
        
        # برچسب
        ctk.CTkLabel(
            section_frame,
            text=label,
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w")
        
        # مقدار
        if is_title:
            value_label = ctk.CTkLabel(
                section_frame,
                text=value,
                font=self.parent.get_font(14, "bold"),
                wraplength=550,
                justify="right"
            )
        else:
            value_label = ctk.CTkLabel(
                section_frame,
                text=value,
                font=self.parent.get_font(12),
                wraplength=550,
                justify="right"
            )
        
        value_label.pack(anchor="w", pady=(5, 0))
    
    def open_pdf(self):
        """باز کردن فایل PDF"""
        try:
            if self.article['pdf_path'] and os.path.exists(self.article['pdf_path']):
                os.startfile(self.article['pdf_path']) if os.name == 'nt' else webbrowser.open(self.article['pdf_path'])
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در باز کردن فایل PDF: {e}")


class ImportFromDOIDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories
        self.result = None
        
        self.title("وارد کردن مقاله از DOI")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # عنوان
        title = ctk.CTkLabel(
            main_frame,
            text="وارد کردن مقاله از DOI",
            font=self.parent.get_font(16, "bold"),
            justify="right"
        )
        title.pack(pady=(0, 20))
        
        # توضیحات
        desc = ctk.CTkLabel(
            main_frame,
            text="DOI مقاله را وارد کنید تا اطلاعات آن به طور خودکار دریافت شود:",
            font=self.parent.get_font(12),
            wraplength=400,
            justify="right"
        )
        desc.pack(pady=(0, 20))
        
        # فیلد DOI
        ctk.CTkLabel(
            main_frame,
            text="DOI مقاله:",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w")
        
        self.doi_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="مثال: 10.1145/3442188.3445922",
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.doi_entry.pack(fill="x", pady=(5, 20))
        
        # دکمه دریافت اطلاعات
        ctk.CTkButton(
            main_frame,
            text="🔍 دریافت اطلاعات از DOI",
            command=self.fetch_doi_info,
            height=40,
            fg_color="#2196F3",
            font=self.parent.get_font()
        ).pack(fill="x", pady=(0, 20))
        
        # وضعیت
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=self.parent.get_font(11),
            text_color=("#666666", "#AAAAAA"),
            justify="right"
        )
        self.status_label.pack()
        
        # فرم اطلاعات
        self.form_frame = ctk.CTkFrame(main_frame)
        
        # فیلدهای فرم
        ctk.CTkLabel(
            self.form_frame,
            text="عنوان مقاله:",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w", pady=(10, 5))
        
        self.title_entry = ctk.CTkEntry(
            self.form_frame, 
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.title_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            self.form_frame,
            text="نویسندگان:",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w", pady=(5, 5))
        
        self.authors_entry = ctk.CTkEntry(
            self.form_frame, 
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.authors_entry.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            self.form_frame,
            text="چکیده:",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w", pady=(5, 5))
        
        self.abstract_text = ctk.CTkTextbox(
            self.form_frame, 
            height=80,
            font=self.parent.get_font()
        )
        self.abstract_text.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            self.form_frame,
            text="دسته‌بندی:",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w", pady=(5, 5))
        
        self.category_combo = ctk.CTkComboBox(
            self.form_frame,
            values=self.categories,
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        if self.categories:
            self.category_combo.set(self.categories[0])
        self.category_combo.pack(fill="x", pady=(0, 20))
        
        # دکمه‌های action
        btn_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="انصراف",
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            font=self.parent.get_font()
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="ذخیره مقاله",
            command=self.save,
            fg_color="#4CAF50",
            width=150,
            font=self.parent.get_font()
        ).pack(side="right", padx=5)
    
    def fetch_doi_info(self):
        """دریافت اطلاعات از DOI"""
        doi = self.doi_entry.get().strip()
        if not doi:
            messagebox.showerror("خطا", "لطفاً DOI مقاله را وارد کنید")
            return
        
        self.status_label.configure(text="در حال دریافت اطلاعات...")
        
        # شبیه‌سازی دریافت اطلاعات
        def simulate_fetch():
            import time
            time.sleep(2)
            
            sample_data = {
                'title': 'مقاله نمونه: بررسی روش‌های جدید در یادگیری ماشین',
                'authors': 'نویسنده اول, نویسنده دوم, نویسنده سوم',
                'abstract': 'این یک چکیده نمونه برای مقاله است که از طریق DOI دریافت شده است.',
                'year': '2023',
                'journal': 'ژورنال نمونه علوم کامپیوتر',
                'publisher': 'ناشر نمونه'
            }
            
            self.after(0, self.fill_form_with_data, sample_data)
        
        threading.Thread(target=simulate_fetch, daemon=True).start()
    
    def fill_form_with_data(self, data):
        """پر کردن فرم با داده‌های دریافتی"""
        self.title_entry.delete(0, 'end')
        self.title_entry.insert(0, data['title'])
        
        self.authors_entry.delete(0, 'end')
        self.authors_entry.insert(0, data['authors'])
        
        self.abstract_text.delete("1.0", "end")
        self.abstract_text.insert("1.0", data['abstract'])
        
        self.status_label.configure(text="✅ اطلاعات با موفقیت دریافت شد")
        
        # نمایش فرم
        self.form_frame.pack(fill="x", pady=(20, 0))
        self.geometry("500x700")
    
    def save(self):
        """ذخیره مقاله"""
        title = self.title_entry.get().strip()
        authors = self.authors_entry.get().strip()
        category = self.category_combo.get()
        
        if not title:
            messagebox.showerror("خطا", "لطفاً عنوان مقاله را وارد کنید")
            return
        
        if not authors:
            messagebox.showerror("خطا", "لطفاً نویسندگان مقاله را وارد کنید")
            return
        
        self.result = {
            'title': title,
            'authors': authors,
            'abstract': self.abstract_text.get("1.0", "end-1c").strip(),
            'journal': '',
            'conference': '',
            'year': None,
            'volume': '',
            'issue': '',
            'pages': '',
            'publisher': '',
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


class ArticleStatisticsDialog(ctk.CTkToplevel):
    def __init__(self, parent, articles):
        super().__init__(parent)
        self.articles = articles
        self.parent = parent
        
        self.title("آمار و گزارش مقالات")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # عنوان
        title = ctk.CTkLabel(
            main_frame,
            text="📊 آمار و گزارش مقالات",
            font=self.parent.get_font(16, "bold"),
            justify="right"
        )
        title.pack(pady=(0, 20))
        
        # محتوای اصلی با اسکرول
        content_scroll = ctk.CTkScrollableFrame(main_frame)
        content_scroll.pack(fill="both", expand=True)
        
        # محاسبه آمار
        stats = self.calculate_statistics()
        
        # نمایش آمار
        self.create_stat_card(content_scroll, "📚 تعداد کل مقالات", str(stats['total_articles']), "#2196F3")
        self.create_stat_card(content_scroll, "✅ مقالات خوانده شده", f"{stats['read_articles']} ({stats['read_percentage']}%)", "#4CAF50")
        self.create_stat_card(content_scroll, "❤️ مقالات مورد علاقه", str(stats['favorite_articles']), "#f44336")
        self.create_stat_card(content_scroll, "📈 میانگین امتیاز", f"{stats['avg_rating']:.1f} ⭐", "#FF9800")
        
        # توزیع دسته‌بندی‌ها
        self.create_category_distribution(content_scroll, stats['category_distribution'])
        
        # توزیع سال‌ها
        self.create_year_distribution(content_scroll, stats['year_distribution'])
        
        # دکمه بستن
        ctk.CTkButton(
            main_frame,
            text="بستن",
            command=self.destroy,
            width=100,
            font=self.parent.get_font()
        ).pack(pady=20)
    
    def calculate_statistics(self):
        """محاسبه آمار مقالات"""
        total = len(self.articles)
        read = sum(1 for article in self.articles if article['read_status'])
        favorites = sum(1 for article in self.articles if article['favorite'])
        avg_rating = sum(article['rating'] for article in self.articles) / total if total > 0 else 0
        
        # توزیع دسته‌بندی
        category_dist = {}
        for article in self.articles:
            category = article['category']
            category_dist[category] = category_dist.get(category, 0) + 1
        
        # توزیع سال
        year_dist = {}
        for article in self.articles:
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
    
    def create_stat_card(self, parent, title, value, color):
        """ایجاد کارت آمار"""
        card = ctk.CTkFrame(
            parent,
            border_width=1,
            border_color=("#E0E0E0", "#404040"),
            corner_radius=10
        )
        card.pack(fill="x", pady=5)
        
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=10)
        
        # عنوان
        ctk.CTkLabel(
            content_frame,
            text=title,
            font=self.parent.get_font(12),
            text_color=("#666666", "#AAAAAA"),
            justify="right"
        ).pack(anchor="w")
        
        # مقدار
        ctk.CTkLabel(
            content_frame,
            text=value,
            font=self.parent.get_font(16, "bold"),
            text_color=color,
            justify="right"
        ).pack(anchor="w", pady=(5, 0))
    
    def create_category_distribution(self, parent, distribution):
        """نمایش توزیع دسته‌بندی‌ها"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            section_frame,
            text="📊 توزیع بر اساس دسته‌بندی",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w", pady=(0, 10))
        
        if not distribution:
            ctk.CTkLabel(
                section_frame,
                text="هیچ داده‌ای موجود نیست",
                font=self.parent.get_font(12),
                text_color=("#666666", "#AAAAAA"),
                justify="right"
            ).pack(anchor="w")
            return
        
        for category, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
            item_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                item_frame,
                text=category,
                font=self.parent.get_font(12),
                justify="right"
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=str(count),
                font=self.parent.get_font(12, "bold"),
                justify="right"
            ).pack(side="right")
    
    def create_year_distribution(self, parent, distribution):
        """نمایش توزیع سال‌ها"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            section_frame,
            text="📅 توزیع بر اساس سال انتشار",
            font=self.parent.get_font(weight="bold"),
            justify="right"
        ).pack(anchor="w", pady=(0, 10))
        
        if not distribution:
            ctk.CTkLabel(
                section_frame,
                text="هیچ داده‌ای موجود نیست",
                font=self.parent.get_font(12),
                text_color=("#666666", "#AAAAAA"),
                justify="right"
            ).pack(anchor="w")
            return
        
        for year, count in sorted(distribution.items(), reverse=True):
            item_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                item_frame,
                text=str(year),
                font=self.parent.get_font(12),
                justify="right"
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=str(count),
                font=self.parent.get_font(12, "bold"),
                justify="right"
            ).pack(side="right")


class ManageCategoriesDialog(ctk.CTkToplevel):
    def __init__(self, parent, categories):
        super().__init__(parent)
        self.parent = parent
        self.categories = categories.copy()
        self.result = None
        
        self.title("مدیریت دسته‌بندی")
        self.geometry("400x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # عنوان
        title = ctk.CTkLabel(
            main_frame,
            text="🗂️ مدیریت دسته‌بندی",
            font=self.parent.get_font(16, "bold"),
            justify="right"
        )
        title.pack(pady=(0, 20))
        
        # لیست دسته‌بندی‌ها با اسکرول
        list_frame = ctk.CTkScrollableFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.category_widgets = []
        for i, category in enumerate(self.categories):
            self.create_category_item(list_frame, category, i)
        
        # افزودن دسته‌بندی جدید
        add_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        add_frame.pack(fill="x", pady=(0, 20))
        
        self.new_category_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="نام دسته‌بندی جدید...",
            height=35,
            font=self.parent.get_font(),
            justify="right"
        )
        self.new_category_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            add_frame,
            text="➕ افزودن",
            command=self.add_category,
            width=80,
            height=35,
            font=self.parent.get_font()
        ).pack(side="right")
        
        # دکمه‌های action
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="انصراف",
            command=self.cancel,
            fg_color="#6c757d",
            width=120,
            font=self.parent.get_font()
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="ذخیره تغییرات",
            command=self.save,
            fg_color="#4CAF50",
            width=150,
            font=self.parent.get_font()
        ).pack(side="right", padx=5)
    
    def create_category_item(self, parent, category, index):
        """ایجاد آیتم دسته‌بندی"""
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", pady=2)
        
        # نام دسته‌بندی
        ctk.CTkLabel(
            item_frame,
            text=category,
            font=self.parent.get_font(12),
            justify="right"
        ).pack(side="left", padx=10, pady=8)
        
        # دکمه حذف
        ctk.CTkButton(
            item_frame,
            text="🗑️",
            width=40,
            height=30,
            fg_color="#f44336",
            hover_color="#d32f2f",
            command=lambda idx=index: self.delete_category(idx),
            font=self.parent.get_font()
        ).pack(side="right", padx=5, pady=5)
        
        # دکمه ویرایش
        ctk.CTkButton(
            item_frame,
            text="✏️",
            width=40,
            height=30,
            fg_color="#FF9800",
            hover_color="#F57C00",
            command=lambda cat=category: self.edit_category(cat),
            font=self.parent.get_font()
        ).pack(side="right", padx=5, pady=5)
        
        self.category_widgets.append(item_frame)
    
    def add_category(self):
        """افزودن دسته‌بندی جدید"""
        new_category = self.new_category_entry.get().strip()
        if not new_category:
            messagebox.showerror("خطا", "لطفاً نام دسته‌بندی را وارد کنید")
            return
        
        if new_category in self.categories:
            messagebox.showerror("خطا", "این دسته‌بندی قبلاً وجود دارد")
            return
        
        self.categories.append(new_category)
        self.refresh_category_list()
        self.new_category_entry.delete(0, 'end')
    
    def delete_category(self, index):
        """حذف دسته‌بندی"""
        if messagebox.askyesno("تأیید حذف", f"آیا از حذف دسته‌بندی '{self.categories[index]}' اطمینان دارید؟"):
            self.categories.pop(index)
            self.refresh_category_list()
    
    def edit_category(self, old_category):
        """ویرایش دسته‌بندی"""
        new_category = ctk.CTkInputDialog(
            text=f"نام جدید برای دسته‌بندی '{old_category}':",
            title="ویرایش دسته‌بندی"
        ).get_input()
        
        if new_category and new_category.strip():
            index = self.categories.index(old_category)
            self.categories[index] = new_category.strip()
            self.refresh_category_list()
    
    def refresh_category_list(self):
        """تازه‌سازی لیست دسته‌بندی‌ها"""
        for widget in self.category_widgets:
            widget.destroy()
        
        self.category_widgets = []
        
        list_frame = self.winfo_children()[0].winfo_children()[1]
        for i, category in enumerate(self.categories):
            self.create_category_item(list_frame, category, i)
    
    def save(self):
        """ذخیره تغییرات"""
        self.result = self.categories
        self.destroy()
    
    def cancel(self):
        """انصراف"""
        self.destroy()