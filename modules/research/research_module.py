# research_assistant/modules/research/research_module.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from tkinter import scrolledtext
import pandas as pd
from datetime import datetime
import os
import sqlite3
import subprocess
import platform
import webbrowser
import shutil
import re
import requests
from bs4 import BeautifulSoup
import threading
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

logger = logging.getLogger(__name__)

# دانلود داده‌های لازم برای nltk (فقط یک بار لازم است)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ResearchModule(ttk.Frame):
    def __init__(self, parent, app, config):
        super().__init__(parent)
        self.app = app
        self.config = config
        self.current_filters = {}
        self.search_results = []
        self.analysis_combo = None  # اضافه کردن reference برای combobox
        self.setup_ui()
        
    def setup_ui(self):
        """ایجاد رابط کاربری مدیریت مقالات تحقیقاتی"""
        self.pack(fill=tk.BOTH, expand=True)
        
        # نوت‌بوک برای تب‌های مختلف
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تب مدیریت مقالات
        self.articles_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.articles_tab, text="📚 مدیریت مقالات")
        
        # تب جستجوی خودکار
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="🔍 جستجوی خودکار")
        
        # تب آنالیز متن
        self.analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_tab, text="📊 آنالیز متن")
        
        # تب مدیریت پروژه‌ها
        self.projects_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.projects_tab, text="📂 مدیریت پروژه‌ها")
        
        # راه‌اندازی هر تب
        self.setup_articles_tab()
        self.setup_search_tab()
        self.setup_analysis_tab()
        self.setup_projects_tab()
        
    def setup_articles_tab(self):
        """ایجاد تب مدیریت مقالات"""
        # عنوان اصلی
        title_label = ttk.Label(
            self.articles_tab,
            text="📚 مدیریت مقالات تحقیقاتی",
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # فریم برای دکمه‌های عملیاتی
        buttons_frame = ttk.Frame(self.articles_tab)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # دکمه افزودن مقاله جدید
        add_btn = ttk.Button(
            buttons_frame,
            text="➕ افزودن مقاله",
            command=self.add_article
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # دکمه خروجی اکسل
        export_btn = ttk.Button(
            buttons_frame,
            text="💾 خروجی Excel",
            command=self.export_to_excel
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # دکمه بروزرسانی
        refresh_btn = ttk.Button(
            buttons_frame,
            text="🔄 بروزرسانی",
            command=self.load_research
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # دکمه تولید استناد
        citation_btn = ttk.Button(
            buttons_frame,
            text="📝 تولید استناد",
            command=self.generate_citation
        )
        citation_btn.pack(side=tk.LEFT, padx=5)
        
        # فریم برای جستجو و فیلتر
        search_frame = ttk.Frame(self.articles_tab)
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # فیلد جستجو
        ttk.Label(search_frame, text="جستجو:").pack(side=tk.RIGHT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.RIGHT, padx=5)
        search_entry.bind('<KeyRelease>', self.apply_filters)
        
        # دکمه‌های فیلتر
        filter_buttons = ttk.Frame(search_frame)
        filter_buttons.pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(filter_buttons, text="همه", command=lambda: self.set_filter('all')).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_buttons, text="خوانده شده", command=lambda: self.set_filter('read')).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_buttons, text="در حال مطالعه", command=lambda: self.set_filter('reading')).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_buttons, text="برنامه‌ریزی شده", command=lambda: self.set_filter('planned')).pack(side=tk.LEFT, padx=2)
        
        # جدول نمایش مقالات
        table_frame = ttk.Frame(self.articles_tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ایجاد Treeview با اسکرول بار
        self.create_table(table_frame)
        
        # بارگذاری داده‌های اولیه
        self.load_research()
    
    def create_table(self, parent):
        """ایجاد جدول نمایش مقالات تحقیقاتی"""
        # فریم برای جدول و اسکرول بار
        table_container = ttk.Frame(parent)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # اسکرول بار عمودی
        v_scrollbar = ttk.Scrollbar(table_container)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # اسکرول بار افقی
        h_scrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ایجاد Treeview
        self.tree = ttk.Treeview(
            table_container,
            columns=('id', 'title', 'authors', 'publication_date', 'journal', 'status', 'rating', 'doi', 'url', 'file_path', 'notes', 'project_id'),
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            selectmode='browse'
        )
        
        # تنظیم اسکرول بارها
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # تعریف ستون‌ها با ترتیب راست به چپ
        columns_config = [
            ('notes', 'یادداشت‌ها', 200),
            ('file_path', 'مسیر فایل', 150),
            ('url', 'لینک', 150),
            ('doi', 'DOI', 100),
            ('rating', 'امتیاز', 80),
            ('status', 'وضعیت', 100),
            ('journal', 'ژورنال/کنفرانس', 150),
            ('publication_date', 'تاریخ انتشار', 100),
            ('authors', 'نویسندگان', 200),
            ('title', 'عنوان', 250),
            ('id', 'ID', 50),
            ('project_id', 'پروژه', 0)
        ]
        
        for col_id, text, width in columns_config:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, minwidth=50)
            # راست‌چین کردن متن در ستون‌ها
            self.tree.column(col_id, anchor='e')
        
        # مخفی کردن ستون‌های ID و project_id
        self.tree.column('id', width=0, stretch=False)
        self.tree.column('project_id', width=0, stretch=False)
        
        # راست‌چین کردن کل جدول
        if self.config.current_language == "fa":
            self.tree["displaycolumns"] = ('notes', 'file_path', 'url', 'doi', 'rating', 'status', 'journal', 'publication_date', 'authors', 'title')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # رویداد دابل‌کلیک برای باز کردن فایل/لینک
        self.tree.bind('<Double-1>', self.on_item_double_click)
        
        # منوی راست‌کلیک
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="ویرایش", command=self.edit_selected)
        self.context_menu.add_command(label="حذف", command=self.delete_selected)
        self.context_menu.add_command(label="افزودن یادداشت", command=self.add_note_to_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="باز کردن فایل", command=self.open_selected_file)
        self.context_menu.add_command(label="باز کردن لینک", command=self.open_selected_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="کپی", command=self.copy_selected)
        self.context_menu.add_command(label="خلاصه‌سازی", command=self.summarize_selected)
        self.tree.bind('<Button-3>', self.show_context_menu)
    
    def add_article(self):
        """افزودن مقاله جدید"""
        # ایجاد پنجره dialog برای افزودن مقاله
        dialog = tk.Toplevel(self)
        dialog.title("افزودن مقاله جدید")
        dialog.geometry("600x500")
        
        # ایجاد فرم ورود اطلاعات
        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # فیلدهای فرم
        fields = [
            ("title", "عنوان مقاله", True),
            ("authors", "نویسندگان", True),
            ("publication_date", "تاریخ انتشار", False),
            ("journal", "ژورنال/کنفرانس", False),
            ("status", "وضعیت", False),
            ("rating", "امتیاز (1-5)", False),
            ("doi", "DOI", False),
            ("url", "لینک مقاله", False),
            ("file_path", "مسیر فایل", False),
            ("notes", "یادداشت‌ها", False)
        ]
        
        entries = {}
        for field, label, required in fields:
            row = ttk.Frame(form_frame)
            row.pack(fill=tk.X, pady=5)
            
            ttk.Label(row, text=f"{label}:", width=15).pack(side=tk.RIGHT)
            
            if field == "notes":
                entry = scrolledtext.ScrolledText(row, height=5, width=40)
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            else:
                entry = ttk.Entry(row, width=40)
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            if required:
                ttk.Label(row, text="*", foreground="red").pack(side=tk.RIGHT)
            
            entries[field] = entry
        
        # دکمه‌های ثبت/انصراف
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def submit():
            # جمع‌آوری داده‌ها از فرم
            data = {}
            for field, entry in entries.items():
                if field == "notes":
                    data[field] = entry.get("1.0", tk.END).strip()
                else:
                    data[field] = entry.get().strip()
            
            # اعتبارسنجی داده‌های ضروری
            if not data["title"] or not data["authors"]:
                messagebox.showwarning("هشدار", "عنوان و نویسندگان مقاله ضروری هستند")
                return
            
            try:
                # ذخیره در دیتابیس
                self.app.db.execute_query("""
                    INSERT INTO papers (title, authors, publication_date, journal, status, rating, doi, url, file_path, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["title"], data["authors"], data["publication_date"], data["journal"],
                    data["status"], data["rating"], data["doi"], data["url"], data["file_path"], data["notes"]
                ))
                
                messagebox.showinfo("موفقیت", "مقاله با موفقیت افزوده شد")
                dialog.destroy()
                self.load_research()
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در افزودن مقاله: {str(e)}")
        
        ttk.Button(button_frame, text="ثبت", command=submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="انصراف", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_research(self):
        """بارگذاری مقالات از دیتابیس"""
        try:
            # پاک کردن داده‌های قبلی
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # ساخت کوئری بر اساس فیلترها
            query = "SELECT * FROM papers WHERE 1=1"
            params = []
            
            if self.current_filters.get('status'):
                query += " AND status = ?"
                params.append(self.current_filters['status'])
            
            if self.current_filters.get('search'):
                query += " AND (title LIKE ? OR authors LIKE ? OR journal LIKE ? OR notes LIKE ?)"
                search_term = f"%{self.current_filters['search']}%"
                params.extend([search_term, search_term, search_term, search_term])
            
            query += " ORDER BY id DESC"
            
            # اجرای کوئری
            papers = self.app.db.fetch_all(query, params)
            
            # افزودن به Treeview
            for paper in papers:
                self.tree.insert('', 'end', values=paper)
                
        except Exception as e:
            logger.error(f"خطا در بارگذاری مقالات: {e}")
            messagebox.showerror("خطا", "خطا در بارگذاری مقالات")
    
    def apply_filters(self, event=None):
        """اعمال فیلترها بر روی مقالات"""
        search_text = self.search_var.get().strip()
        if search_text:
            self.current_filters['search'] = search_text
        else:
            self.current_filters.pop('search', None)
        
        self.load_research()
    
    def set_filter(self, filter_type):
        """تنظیم فیلتر وضعیت"""
        status_map = {
            'all': None,
            'read': 'خوانده شده',
            'reading': 'در حال مطالعه',
            'planned': 'برنامه‌ریزی شده'
        }
        
        if filter_type == 'all':
            self.current_filters.pop('status', None)
        else:
            self.current_filters['status'] = status_map[filter_type]
        
        self.load_research()
    
    def export_to_excel(self):
        """خروجی اکسل از مقالات"""
        try:
            # دریافت تمام مقالات
            papers = self.app.db.fetch_all("SELECT * FROM papers")
            
            if not papers:
                messagebox.showwarning("هشدار", "هیچ مقاله‌ای برای خروجی وجود ندارد")
                return
            
            # ایجاد DataFrame
            df = pd.DataFrame(papers, columns=[
                'ID', 'Title', 'Authors', 'Publication Date', 'Journal', 
                'Status', 'Rating', 'DOI', 'URL', 'File Path', 'Notes', 'Project ID'
            ])
            
            # انتخاب مسیر ذخیره
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="ذخیره فایل اکسل"
            )
            
            if file_path:
                # ذخیره به اکسل
                df.to_excel(file_path, index=False)
                messagebox.showinfo("موفقیت", "خروجی اکسل با موفقیت ایجاد شد")
                
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ایجاد خروجی اکسل: {str(e)}")
    
    def edit_selected(self):
        """ویرایش مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        
        # ایجاد پنجره ویرایش
        self.show_edit_dialog(values)
    
    def show_edit_dialog(self, values):
        """نمایش دیالوگ ویرایش مقاله"""
        dialog = tk.Toplevel(self)
        dialog.title("ویرایش مقاله")
        dialog.geometry("600x500")
        
        # ایجاد فرم ویرایش
        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # فیلدهای فرم
        fields = [
            ("title", "عنوان مقاله", True),
            ("authors", "نویسندگان", True),
            ("publication_date", "تاریخ انتشار", False),
            ("journal", 'ژورنال/کنفرانس', False),
            ("status", "وضعیت", False),
            ("rating", "امتیاز (1-5)", False),
            ("doi", "DOI", False),
            ("url", "لینک مقاله", False),
            ("file_path", "مسیر فایل", False),
            ("notes", "یادداشت‌ها", False)
        ]
        
        entries = {}
        for i, (field, label, required) in enumerate(fields):
            row = ttk.Frame(form_frame)
            row.pack(fill=tk.X, pady=5)
            
            ttk.Label(row, text=f"{label}:", width=15).pack(side=tk.RIGHT)
            
            if field == "notes":
                entry = scrolledtext.ScrolledText(row, height=5, width=40)
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                if i < len(values):
                    entry.insert("1.0", values[i] or "")
            else:
                entry = ttk.Entry(row, width=40)
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                if i < len(values):
                    entry.insert(0, values[i] or "")
            
            if required:
                ttk.Label(row, text="*", foreground="red").pack(side=tk.RIGHT)
            
            entries[field] = entry
        
        # دکمه‌های ثبت/انصراف
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def submit():
            # جمع‌آوری داده‌ها از فرم
            data = {}
            for field, entry in entries.items():
                if field == "notes":
                    data[field] = entry.get("1.0", tk.END).strip()
                else:
                    data[field] = entry.get().strip()
            
            # اعتبارسنجی داده‌های ضروری
            if not data["title"] or not data["authors"]:
                messagebox.showwarning("هشدار", "عنوان و نویسندگان مقاله ضروری هستند")
                return
            
            try:
                # به روزرسانی در دیتابیس
                self.app.db.execute_query("""
                    UPDATE papers 
                    SET title=?, authors=?, publication_date=?, journal=?, status=?, 
                        rating=?, doi=?, url=?, file_path=?, notes=?
                    WHERE id=?
                """, (
                    data["title"], data["authors"], data["publication_date"], data["journal"],
                    data["status"], data["rating"], data["doi"], data["url"], 
                    data["file_path"], data["notes"], values[0]  # ID مقاله
                ))
                
                messagebox.showinfo("موفقیت", "مقاله با موفقیت ویرایش شد")
                dialog.destroy()
                self.load_research()
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در ویرایش مقاله: {str(e)}")
        
        ttk.Button(button_frame, text="ثبت تغییرات", command=submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="انصراف", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def delete_selected(self):
        """حذف مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        
        if messagebox.askyesno("تأیید حذف", f"آیا از حذف مقاله '{values[1]}' مطمئن هستید؟"):
            try:
                # حذف از دیتابیس
                self.app.db.execute_query("DELETE FROM papers WHERE id=?", (values[0],))
                
                messagebox.showinfo("موفقیت", "مقاله با موفقیت حذف شد")
                self.load_research()
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در حذف مقاله: {str(e)}")
    
    def add_note_to_selected(self):
        """افزودن یادداشت به مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        
        # ایجاد پنجره افزودن یادداشت
        dialog = tk.Toplevel(self)
        dialog.title("افزودن یادداشت")
        dialog.geometry("500x300")
        
        ttk.Label(dialog, text="یادداشت جدید:", font=("Tahoma", 12)).pack(pady=10)
        
        note_text = scrolledtext.ScrolledText(dialog, height=10, width=50, wrap=tk.WORD)
        note_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        if len(values) > 10 and values[10]:  # اگر یادداشت قبلی وجود دارد
            note_text.insert("1.0", values[10])
        
        def save_note():
            new_note = note_text.get("1.0", tk.END).strip()
            
            try:
                # به روزرسانی یادداشت در دیتابیس
                self.app.db.execute_query("UPDATE papers SET notes=? WHERE id=?", (new_note, values[0]))
                
                messagebox.showinfo("موفقیت", "یادداشت با موفقیت افزوده شد")
                dialog.destroy()
                self.load_research()
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در افزودن یادداشت: {str(e)}")
        
        ttk.Button(dialog, text="ذخیره", command=save_note).pack(pady=10)
    
    def open_selected_file(self):
        """باز کردن فایل مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        
        if len(values) > 9 and values[9]:  # file_path
            file_path = values[9]
            if os.path.exists(file_path):
                try:
                    if platform.system() == "Windows":
                        os.startfile(file_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", file_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    messagebox.showerror("خطا", f"خطا در باز کردن فایل: {str(e)}")
            else:
                messagebox.showwarning("هشدار", "فایل یافت نشد")
        else:
            messagebox.showwarning("هشدار", "مسیر فایل مشخص نشده است")
    
    def open_selected_url(self):
        """باز کردن لینک مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        
        if len(values) > 8 and values[8]:  # url
            url = values[8]
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            try:
                webbrowser.open(url)
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در باز کردن لینک: {str(e)}")
        else:
            messagebox.showwarning("هشدار", "لینک مقاله مشخص نشده است")
    
    def copy_selected(self):
        """کپی اطلاعات مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        
        # ایجاد متن قابل کپی
        copy_text = f"عنوان: {values[1]}\nنویسندگان: {values[2]}\nتاریخ انتشار: {values[3]}\nژورنال: {values[4]}"
        
        if len(values) > 8 and values[8]:  # url
            copy_text += f"\nلینک: {values[8]}"
        
        # کپی به کلیپ‌بورد
        self.clipboard_clear()
        self.clipboard_append(copy_text)
        messagebox.showinfo("موفقیت", "اطلاعات مقاله کپی شد")
    
    def summarize_selected(self):
        """خلاصه‌سازی مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        notes = values[10] if len(values) > 10 else ""  # یادداشت‌ها در ایندکس 10
        
        if not notes:
            messagebox.showwarning("هشدار", "مقاله انتخاب شده یادداشتی ندارد")
            return
        
        try:
            # خلاصه‌سازی متن با sumy
            parser = PlaintextParser.from_string(notes, Tokenizer("english"))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, 3)  # 3 جمله خلاصه
            
            summary_text = "\n".join([str(sentence) for sentence in summary])
            
            # نمایش خلاصه
            self.notebook.select(self.analysis_tab)
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, f"خلاصه مقاله:\n{summary_text}")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در خلاصه‌سازی: {str(e)}")
    
    def show_context_menu(self, event):
        """نمایش منوی راست‌کلیک"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def on_item_double_click(self, event):
        """رویداد دابل‌کلیک روی آیتم"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.selection()[0]
            values = self.tree.item(item)['values']
            
            if column == "#9":  # ستون file_path
                self.open_selected_file()
            elif column == "#8":  # ستون url
                self.open_selected_url()
            else:
                self.edit_selected()
    
    def setup_search_tab(self):
        """ایجاد تب جستجوی خودکار"""
        title_label = ttk.Label(
            self.search_tab,
            text="🔍 جستجوی خودکار در پایگاه‌های داده علمی",
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # فریم جستجو
        search_frame = ttk.Frame(self.search_tab)
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(search_frame, text="کلیدواژه:").pack(side=tk.RIGHT, padx=5)
        self.search_keyword = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_keyword, width=30)
        search_entry.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(search_frame, text="تعداد نتایج:").pack(side=tk.RIGHT, padx=5)
        self.result_count = tk.IntVar(value=10)
        count_spinbox = ttk.Spinbox(search_frame, from_=5, to=50, textvariable=self.result_count, width=5)
        count_spinbox.pack(side=tk.RIGHT, padx=5)
        
        # دکمه‌های جستجو
        search_buttons = ttk.Frame(search_frame)
        search_buttons.pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(search_buttons, text="جستجو در Google Scholar", 
                  command=lambda: self.search_online('scholar')).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_buttons, text="جستجو در PubMed", 
                  command=lambda: self.search_online('pubmed')).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_buttons, text="جستجو در arXiv", 
                  command=lambda: self.search_online('arxiv')).pack(side=tk.LEFT, padx=2)
        
        # نتایج جستجو
        results_frame = ttk.Frame(self.search_tab)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.search_tree = ttk.Treeview(
            results_frame,
            columns=('title', 'authors', 'year', 'source', 'url'),
            show='headings',
            height=15
        )
        
        # تعریف ستون‌ها
        columns_config = [
            ('title', 'عنوان', 300),
            ('authors', 'نویسندگان', 200),
            ('year', 'سال', 80),
            ('source', 'منبع', 100),
            ('url', 'لینک', 150)
        ]
        
        for col_id, text, width in columns_config:
            self.search_tree.heading(col_id, text=text)
            self.search_tree.column(col_id, width=width)
        
        # اسکرول بار
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # دکمه افزودن انتخاب شده‌ها
        add_selected_btn = ttk.Button(
            self.search_tab,
            text="➕ افزودن مقالات انتخاب شده",
            command=self.add_selected_results
        )
        add_selected_btn.pack(pady=10)
        
        # رویداد دابل‌کلیک برای باز کردن لینک
        self.search_tree.bind('<Double-1>', self.open_search_result)
    
    def search_online(self, source):
        """جستجوی خودکار در پایگاه‌های داده علمی"""
        keyword = self.search_keyword.get().strip()
        if not keyword:
            messagebox.showwarning("هشدار", "لطفاً کلیدواژه جستجو را وارد کنید")
            return
        
        # نمایش وضعیت جستجو
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, f"در حال جستجوی '{keyword}' در {source}...\n")
        
        # اجرای جستجو در thread جداگانه
        thread = threading.Thread(target=self.perform_search, args=(source, keyword))
        thread.daemon = True
        thread.start()
    
    def perform_search(self, source, keyword):
        """انجام جستجو در پایگاه داده انتخاب شده"""
        try:
            if source == 'scholar':
                results = self.search_google_scholar(keyword)
            elif source == 'pubmed':
                results = self.search_pubmed(keyword)
            elif source == 'arxiv':
                results = self.search_arxiv(keyword)
            else:
                results = []
            
            # نمایش نتایج در GUI
            self.app.root.after(0, self.display_search_results, results, source)
            
        except Exception as e:
            self.app.root.after(0, lambda: messagebox.showerror("خطا", f"خطا در جستجو: {str(e)}"))
    
    def search_google_scholar(self, keyword):
        """جستجو در Google Scholar (شبیه‌سازی)"""
        # این یک شبیه‌سازی است - در عمل نیاز به استفاده از API دارد
        results = []
        for i in range(self.result_count.get()):
            results.append({
                'title': f'مقاله نمونه {i+1} درباره {keyword}',
                'authors': 'نویسنده یک, نویسنده دو',
                'year': str(2023 - i),
                'source': 'Google Scholar',
                'url': f'https://scholar.google.com/scholar?q={keyword}'
            })
        return results
    
    def search_pubmed(self, keyword):
        """جستجو در PubMed (شبیه‌سازی)"""
        results = []
        for i in range(self.result_count.get()):
            results.append({
                'title': f'مطالعه تحقیقاتی {i+1} درباره {keyword}',
                'authors': 'پژوهشگر الف, پژوهشگر ب',
                'year': str(2023 - i),
                'source': 'PubMed',
                'url': f'https://pubmed.ncbi.nlm.nih.gov/?term={keyword}'
            })
        return results
    
    def search_arxiv(self, keyword):
        """جستجو در arXiv (شبیه‌سازی)"""
        results = []
        for i in range(self.result_count.get()):
            results.append({
                'title': f'پیش‌چاپ {i+1} درباره {keyword}',
                'authors': 'دانشمند X, دانشمند Y',
                'year': str(2023 - i),
                'source': 'arXiv',
                'url': f'https://arxiv.org/search/?query={keyword}'
            })
        return results
    
    def display_search_results(self, results, source):
        """نمایش نتایج جستجو در Treeview"""
        # پاک کردن نتایج قبلی
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        # افزودن نتایج جدید
        for result in results:
            self.search_tree.insert('', 'end', values=(
                result['title'],
                result['authors'],
                result['year'],
                result['source'],
                result['url']
            ))
        
        self.search_results = results
        self.analysis_text.insert(tk.END, f"یافت {len(results)} نتیجه از {source}\n")
    
    def open_search_result(self, event):
        """باز کردن لینک نتیجه جستجو"""
        selection = self.search_tree.selection()
        if selection:
            item = self.search_tree.item(selection[0])
            url = item['values'][4]  # لینک در ستون پنجم
            if url:
                webbrowser.open(url)
    
    def add_selected_results(self):
        """افزودن نتایج انتخاب شده به پایگاه داده"""
        selected_items = self.search_tree.selection()
        if not selected_items:
            messagebox.showwarning("هشدار", "لطفاً حداقل یک مقاله را انتخاب کنید")
            return
        
        added_count = 0
        for item in selected_items:
            values = self.search_tree.item(item)['values']
            # یافتن نتیجه کامل در لیست نتایج
            for result in self.search_results:
                if result['title'] == values[0] and result['authors'] == values[1]:
                    try:
                        # افزودن به پایگاه داده
                        self.app.db.execute_query("""
                            INSERT INTO papers (title, authors, publication_date, journal, source)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            result['title'],
                            result['authors'],
                            result['year'],
                            result.get('journal', ''),
                            result['source']
                        ))
                        added_count += 1
                    except Exception as e:
                        logger.error(f"خطا در افزودن مقاله: {e}")
        
        if added_count > 0:
            messagebox.showinfo("موفقیت", f"{added_count} مقاله با موفقیت افزوده شد")
            self.load_research()
        else:
            messagebox.showwarning("هشدار", "هیچ مقاله‌ای افزوده نشد")
    
    def setup_analysis_tab(self):
        """ایجاد تب آنالیز متن"""
        title_label = ttk.Label(
            self.analysis_tab,
            text="📊 آنالیز متن و تجسم داده‌ها",
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # فریم انتخاب مقاله برای آنالیز
        selection_frame = ttk.Frame(self.analysis_tab)
        selection_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(selection_frame, text="انتخاب مقاله برای آنالیز:").pack(side=tk.RIGHT, padx=5)
        self.analysis_var = tk.StringVar()
        self.analysis_combo = ttk.Combobox(selection_frame, textvariable=self.analysis_var, width=40, state='readonly')
        self.analysis_combo.pack(side=tk.RIGHT, padx=5)
        
        # پر کردن combobox با عناوین مقالات
        self.load_analysis_titles()
        
        # دکمه‌های آنالیز
        analysis_buttons = ttk.Frame(self.analysis_tab)
        analysis_buttons.pack(pady=10)
        
        ttk.Button(analysis_buttons, text="خلاصه‌سازی متن", 
                  command=self.summarize_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_buttons, text="استخراج کلیدواژه", 
                  command=self.extract_keywords).pack(side=tk.LEFT, padx=5)
        ttk.Button(analysis_buttons, text="تجزیه و تحلیل آماری", 
                  command=self.statistical_analysis).pack(side=tk.LEFT, padx=5)
        
        # فریم نتایج آنالیز
        results_frame = ttk.Frame(self.analysis_tab)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.analysis_text = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
        
        # فریم برای نمودارها
        self.chart_frame = ttk.Frame(self.analysis_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    def load_analysis_titles(self):
        """بارگذاری عناوین مقالات برای combobox آنالیز"""
        try:
            papers = self.app.db.fetch_all("SELECT id, title FROM papers ORDER BY title")
            paper_options = [f"{paper[0]}: {paper[1]}" for paper in papers]
            
            # به روزرسانی combobox
            if self.analysis_combo:
                self.analysis_combo['values'] = paper_options
                
                if paper_options:
                    self.analysis_combo.current(0)
                
        except Exception as e:
            logger.error(f"خطا در بارگذاری عناوین: {e}")
    
    def summarize_text(self):
        """خلاصه‌سازی متن مقاله انتخاب شده"""
        selected_value = self.analysis_var.get()
        if not selected_value:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        paper_id = selected_value.split(":")[0]  # استخراج ID از combobox
        
        # دریافت یادداشت‌های مقاله از دیتابیس
        result = self.app.db.fetch_one("SELECT notes FROM papers WHERE id = ?", (paper_id,))
        if not result or not result[0]:
            messagebox.showwarning("هشدار", "مقاله انتخاب شده یادداشتی ندارد")
            return
        
        notes = result[0]
        try:
            # خلاصه‌سازی متن با sumy
            parser = PlaintextParser.from_string(notes, Tokenizer("english"))
            summarizer = LsaSummarizer()
            summary = summarizer(parser.document, 3)  # 3 جمله خلاصه
            
            summary_text = "\n".join([str(sentence) for sentence in summary])
            
            # نمایش خلاصه
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, f"خلاصه مقاله:\n{summary_text}")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در خلاصه‌سازی: {str(e)}")
    
    def extract_keywords(self):
        """استخراج کلیدواژه‌های مقاله انتخاب شده"""
        selected_value = self.analysis_var.get()
        if not selected_value:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        paper_id = selected_value.split(":")[0]  # استخراج ID از combobox
        
        # دریافت یادداشت‌های مقاله از دیتابیس
        result = self.app.db.fetch_one("SELECT notes FROM papers WHERE id = ?", (paper_id,))
        if not result or not result[0]:
            messagebox.showwarning("هشدار", "مقاله انتخاب شده یادداشتی ندارد")
            return
        
        notes = result[0]
        try:
            # استخراج کلیدواژه‌ها
            words = word_tokenize(notes)
            stop_words = set(stopwords.words('english'))
            filtered_words = [word for word in words if word.isalnum() and word.lower() not in stop_words]
            
            # شمارش تکرار کلمات
            from collections import Counter
            word_freq = Counter(filtered_words)
            top_keywords = word_freq.most_common(10)  # 10 کلیدواژه برتر
            
            # نمایش کلیدواژه‌ها
            keywords_text = "\n".join([f"{word}: {count}" for word, count in top_keywords])
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, f"کلیدواژه‌های برتر:\n{keywords_text}")
            
            # ایجاد نمودار
            self.create_keyword_chart(top_keywords)
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در استخراج کلیدواژه: {str(e)}")
    
    def create_keyword_chart(self, keywords):
        """ایجاد نمودار برای کلیدواژه‌ها"""
        # پاک کردن فریم نمودار
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # ایجاد نمودار
        words = [item[0] for item in keywords]
        counts = [item[1] for item in keywords]
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.barh(words, counts)
        ax.set_xlabel('تعداد تکرار')
        ax.set_title('توزیع کلیدواژه‌ها')
        
        # نمایش نمودار در Tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def statistical_analysis(self):
        """تجزیه و تحلیل آماری مقالات"""
        try:
            # دریافت تمام مقالات از دیتابیس
            papers = self.app.db.fetch_all("SELECT publication_date, journal, status FROM papers")
            
            if not papers:
                messagebox.showwarning("هشدار", "هیچ مقاله‌ای برای تحلیل وجود ندارد")
                return
            
            # تحلیل داده‌ها
            year_counts = {}
            journal_counts = {}
            status_counts = {}
            
            for paper in papers:
                # شمارش بر اساس سال
                year = paper[0][:4] if paper[0] and len(paper[0]) >= 4 else 'نامشخص'
                year_counts[year] = year_counts.get(year, 0) + 1
                
                # شمارش بر اساس ژورنال
                journal = paper[1] or 'نامشخص'
                journal_counts[journal] = journal_counts.get(journal, 0) + 1
                
                # شمارش بر اساس وضعیت
                status = paper[2] or 'نامشخص'
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # نمایش نتایج
            analysis_text = "تحلیل آماری مقالات:\n\n"
            analysis_text += f"تعداد کل مقالات: {len(papers)}\n\n"
            
            analysis_text += "توزیع بر اساس سال:\n"
            for year, count in sorted(year_counts.items()):
                analysis_text += f"  {year}: {count} مقاله\n"
            
            analysis_text += "\nتوزیع بر اساس ژورنال:\n"
            for journal, count in sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:5]:  # 5 ژورنال برتر
                analysis_text += f"  {journal}: {count} مقاله\n"
            
            analysis_text += "\nتوزیع بر اساس وضعیت:\n"
            for status, count in status_counts.items():
                analysis_text += f"  {status}: {count} مقاله\n"
            
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, analysis_text)
            
            # ایجاد نمودار وضعیت
            self.create_status_chart(status_counts)
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در تحلیل آماری: {str(e)}")
    
    def create_status_chart(self, status_counts):
        """ایجاد نمودار وضعیت مقالات"""
        # پاک کردن فریم نمودار
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # ایجاد نمودار
        labels = list(status_counts.keys())
        sizes = list(status_counts.values())
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title('توزیع مقالات بر اساس وضعیت')
        
        # نمایش نمودار در Tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_projects_tab(self):
        """ایجاد تب مدیریت پروژه‌ها"""
        title_label = ttk.Label(
            self.projects_tab,
            text="📂 مدیریت پروژه‌های تحقیقاتی",
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # فریم ایجاد پروژه جدید
        create_frame = ttk.Frame(self.projects_tab)
        create_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(create_frame, text="نام پروژه:").pack(side=tk.RIGHT, padx=5)
        self.project_name = tk.StringVar()
        project_entry = ttk.Entry(create_frame, textvariable=self.project_name, width=30)
        project_entry.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(create_frame, text="ایجاد پروژه جدید", 
                  command=self.create_project).pack(side=tk.RIGHT, padx=5)
        
        # لیست پروژه‌ها
        projects_frame = ttk.Frame(self.projects_tab)
        projects_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.projects_tree = ttk.Treeview(  # اصلاح: ttk به جای ttk
            projects_frame,
            columns=('id', 'name', 'created_date', 'paper_count'),
            show='headings',
            height=15
        )
        
        # تعریف ستون‌ها
        columns_config = [
            ('name', 'نام پروژه', 200),
            ('created_date', 'تاریخ ایجاد', 100),
            ('paper_count', 'تعداد مقالات', 100),
            ('id', 'ID', 0)
        ]
        
        for col_id, text, width in columns_config:
            self.projects_tree.heading(col_id, text=text)
            self.projects_tree.column(col_id, width=width)
        
        # اسکرول بار
        scrollbar = ttk.Scrollbar(projects_frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=scrollbar.set)
        
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # دکمه‌های مدیریت پروژه
        project_buttons = ttk.Frame(self.projects_tab)
        project_buttons.pack(pady=10)
        
        ttk.Button(project_buttons, text="مدیریت مقالات پروژه", 
                  command=self.manage_project_papers).pack(side=tk.LEFT, padx=5)
        ttk.Button(project_buttons, text="حذف پروژه", 
                  command=self.delete_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(project_buttons, text="گزارش پروژه", 
                  command=self.generate_project_report).pack(side=tk.LEFT, padx=5)
        
        # بارگذاری پروژه‌ها
        self.load_projects()
    
    def create_project(self):
        """ایجاد پروژه تحقیقاتی جدید"""
        project_name = self.project_name.get().strip()
        if not project_name:
            messagebox.showwarning("هشدار", "لطفاً نام پروژه را وارد کنید")
            return
        
        try:
            # ایجاد پروژه در دیتابیس
            self.app.db.execute_query("""
                INSERT INTO research_projects (name, created_date)
                VALUES (?, datetime('now'))
            """, (project_name,))
            
            messagebox.showinfo("موفقیت", "پروژه با موفقیت ایجاد شد")
            self.project_name.set("")
            self.load_projects()
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ایجاد پروژه: {str(e)}")
    
    def load_projects(self):
        """بارگذاری پروژه‌ها از دیتابیس"""
        try:
            # پاک کردن لیست قبلی
            for item in self.projects_tree.get_children():
                self.projects_tree.delete(item)
            
            # دریافت پروژه‌ها از دیتابیس
            projects = self.app.db.fetch_all("""
                SELECT rp.id, rp.name, rp.created_date, COUNT(rpm.paper_id) as paper_count
                FROM research_projects rp
                LEFT JOIN research_project_mapers rpm ON rp.id = rpm.project_id
                GROUP BY rp.id, rp.name, rp.created_date
                ORDER BY rp.created_date DESC
            """)
            
            # افزودن به Treeview
            for project in projects:
                self.projects_tree.insert('', 'end', values=project)
                
        except Exception as e:
            logger.error(f"خطا در بارگذاری پروژه‌ها: {e}")
    
    def manage_project_papers(self):
        """مدیریت مقالات پروژه انتخاب شده"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک پروژه را انتخاب کنید")
            return
        
        project_id = self.projects_tree.item(selection[0])['values'][3]  # ID در ستون چهارم
        
        # ایجاد پنجره مدیریت مقالات پروژه
        self.show_project_papers_window(project_id)
    
    def show_project_papers_window(self, project_id):
        """نمایش پنجره مدیریت مقالات پروژه"""
        window = tk.Toplevel(self)
        window.title("مدیریت مقالات پروژه")
        window.geometry("800x600")
        
        # دریافت اطلاعات پروژه
        project = self.app.db.fetch_one("SELECT name FROM research_projects WHERE id = ?", (project_id,))
        project_name = project[0] if project else "نامشخص"
        
        ttk.Label(window, text=f"مقالات پروژه: {project_name}", font=("Tahoma", 14, "bold")).pack(pady=10)
        
        # فریم برای لیست مقالات
        list_frame = ttk.Frame(window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview برای نمایش مقالات
        columns = ('id', 'title', 'authors', 'journal')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # تعریف ستون‌ها
        tree.heading('id', text='ID')
        tree.heading('title', text='عنوان')
        tree.heading('authors', text='نویسندگان')
        tree.heading('journal', text='ژورنال')
        
        tree.column('id', width=50)
        tree.column('title', width=300)
        tree.column('authors', width=200)
        tree.column('journal', width=150)
        
        # اسکرول بار
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # بارگذاری مقالات پروژه
        papers = self.app.db.fetch_all("""
            SELECT p.id, p.title, p.authors, p.journal
            FROM papers p
            JOIN research_project_mapers rpm ON p.id = rpm.paper_id
            WHERE rpm.project_id = ?
            ORDER BY p.title
        """, (project_id,))
        
        for paper in papers:
            tree.insert('', 'end', values=paper)
        
        # فریم برای دکمه‌ها
        button_frame = ttk.Frame(window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="افزودن مقاله به پروژه", 
                  command=lambda: self.add_paper_to_project(project_id, tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="حذف مقاله از پروژه", 
                  command=lambda: self.remove_paper_from_project(project_id, tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="بستن", command=window.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_paper_to_project(self, project_id, tree):
        """افزودن مقاله به پروژه"""
        # نمایش دیالوگ انتخاب مقاله
        papers = self.app.db.fetch_all("""
            SELECT id, title, authors FROM papers 
            WHERE id NOT IN (
                SELECT paper_id FROM research_project_mapers WHERE project_id = ?
            )
            ORDER BY title
        """, (project_id,))
        
        if not papers:
            messagebox.showinfo("اطلاع", "هیچ مقاله‌ای برای افزودن وجود ندارد")
            return
        
        # ایجاد پنجره انتخاب مقاله
        select_window = tk.Toplevel(self)
        select_window.title("انتخاب مقاله برای افزودن به پروژه")
        select_window.geometry("600x400")
        
        ttk.Label(select_window, text="مقاله مورد نظر را انتخاب کنید:", font=("Tahoma", 12)).pack(pady=10)
        
        # Treeview برای نمایش مقالات available
        columns = ('id', 'title', 'authors')
        select_tree = ttk.Treeview(select_window, columns=columns, show='headings', height=15)
        
        select_tree.heading('id', text='ID')
        select_tree.heading('title', text='عنوان')
        select_tree.heading('authors', text='نویسندگان')
        
        select_tree.column('id', width=50)
        select_tree.column('title', width=300)
        select_tree.column('authors', width=200)
        
        scrollbar = ttk.Scrollbar(select_window, orient=tk.VERTICAL, command=select_tree.yview)
        select_tree.configure(yscrollcommand=scrollbar.set)
        
        select_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        for paper in papers:
            select_tree.insert('', 'end', values=paper)
        
        def add_selected():
            selection = select_tree.selection()
            if not selection:
                messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
                return
            
            paper_id = select_tree.item(selection[0])['values'][0]
            
            try:
                # افزودن رابطه مقاله-پروژه
                self.app.db.execute_query("""
                    INSERT INTO research_project_mapers (project_id, paper_id)
                    VALUES (?, ?)
                """, (project_id, paper_id))
                
                messagebox.showinfo("موفقیت", "مقاله با موفقیت به پروژه افزوده شد")
                select_window.destroy()
                
                # به روزرسانی Treeview اصلی
                paper_info = self.app.db.fetch_one("SELECT id, title, authors, journal FROM papers WHERE id = ?", (paper_id,))
                if paper_info:
                    tree.insert('', 'end', values=paper_info)
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در افزودن مقاله: {str(e)}")
        
        ttk.Button(select_window, text="افزودن انتخاب شده", command=add_selected).pack(pady=10)
    
    def remove_paper_from_project(self, project_id, tree):
        """حذف مقاله از پروژه"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        paper_id = tree.item(selection[0])['values'][0]
        paper_title = tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("تأیید", f"آیا از حذف مقاله '{paper_title}' از پروژه مطمئن هستید؟"):
            try:
                # حذف رابطه مقاله-پروژه
                self.app.db.execute_query("""
                    DELETE FROM research_project_mapers 
                    WHERE project_id = ? AND paper_id = ?
                """, (project_id, paper_id))
                
                messagebox.showinfo("موفقیت", "مقاله با موفقیت از پروژه حذف شد")
                tree.delete(selection[0])
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در حذف مقاله: {str(e)}")
    
    def delete_project(self):
        """حذف پروژه انتخاب شده"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک پروژه را انتخاب کنید")
            return
        
        project_id = self.projects_tree.item(selection[0])['values'][3]  # ID در ستون چهارم
        project_name = self.projects_tree.item(selection[0])['values'][0]  # نام در ستون اول
        
        if messagebox.askyesno("تأیید", f"آیا از حذف پروژه '{project_name}' مطمئن هستید؟"):
            try:
                # حذف روابط مقاله-پروژه
                self.app.db.execute_query("DELETE FROM research_project_mapers WHERE project_id = ?", (project_id,))
                
                # حذف پروژه
                self.app.db.execute_query("DELETE FROM research_projects WHERE id = ?", (project_id,))
                
                messagebox.showinfo("موفقیت", "پروژه با موفقیت حذف شد")
                self.load_projects()
                
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در حذف پروژه: {str(e)}")
    
    def generate_project_report(self):
        """تولید گزارش برای پروژه انتخاب شده"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک پروژه را انتخاب کنید")
            return
        
        project_id = self.projects_tree.item(selection[0])['values'][3]  # ID در ستون چهارم
        project_name = self.projects_tree.item(selection[0])['values'][0]  # نام در ستون اول
        
        try:
            # دریافت اطلاعات پروژه
            project_info = self.app.db.fetch_one("""
                SELECT name, created_date, description FROM research_projects WHERE id = ?
            """, (project_id,))
            
            # دریافت مقالات پروژه
            papers = self.app.db.fetch_all("""
                SELECT p.title, p.authors, p.publication_date, p.journal, p.status
                FROM papers p
                JOIN research_project_mapers rpm ON p.id = rpm.paper_id
                WHERE rpm.project_id = ?
                ORDER BY p.publication_date DESC
            """, (project_id,))
            
            if not papers:
                messagebox.showwarning("هشدار", "پروژه انتخاب شده هیچ مقاله‌ای ندارد")
                return
            
            # ایجاد گزارش
            report_text = f"گزارش پروژه: {project_name}\n"
            report_text += f"تاریخ ایجاد: {project_info[1]}\n"
            if project_info[2]:
                report_text += f"توضیحات: {project_info[2]}\n"
            report_text += f"\nتعداد مقالات: {len(papers)}\n\n"
            
            report_text += "لیست مقالات:\n"
            for i, paper in enumerate(papers, 1):
                report_text += f"{i}. {paper[0]}\n"
                report_text += f"   نویسندگان: {paper[1]}\n"
                report_text += f"   تاریخ انتشار: {paper[2] or 'نامشخص'}\n"
                report_text += f"   ژورنال: {paper[3] or 'نامشخص'}\n"
                report_text += f"   وضعیت: {paper[4] or 'نامشخص'}\n\n"
            
            # تحلیل وضعیت مقالات
            status_counts = {}
            for paper in papers:
                status = paper[4] or 'نامشخص'
                status_counts[status] = status_counts.get(status, 0) + 1
            
            report_text += "توزیع وضعیت مقالات:\n"
            for status, count in status_counts.items():
                report_text += f"  {status}: {count} مقاله\n"
            
            # نمایش گزارش
            self.notebook.select(self.analysis_tab)
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, report_text)
            
            # ایجاد نمودار وضعیت
            self.create_status_chart(status_counts)
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در تولید گزارش: {str(e)}")
    
    def generate_citation(self):
        """تولید استناد برای مقاله انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("هشدار", "لطفاً یک مقاله را انتخاب کنید")
            return
        
        item_id = selection[0]
        values = self.tree.item(item_id)['values']
        
        # استخراج اطلاعات مقاله
        title = values[1] if len(values) > 1 else ""  # عنوان در ایندکس 1
        authors = values[2] if len(values) > 2 else ""  # نویسندگان در ایندکس 2
        year = values[3] if len(values) > 3 else ""  # تاریخ انتشار در ایندکس 3
        journal = values[4] if len(values) > 4 else ""  # ژورنال در ایندکس 4
        doi = values[7] if len(values) > 7 else ""  # DOI در ایندکس 7
        
        if not title or not authors:
            messagebox.showwarning("هشدار", "اطلاعات مقاله برای تولید استناد کافی نیست")
            return
        
        # ایجاد استناد به فرمت APA
        citation = self.generate_apa_citation(authors, year, title, journal, doi)
        
        # نمایش استناد
        citation_window = tk.Toplevel(self)
        citation_window.title("استناد مقاله")
        citation_window.geometry("500x300")
        
        ttk.Label(citation_window, text="استناد به فرمت APA:", font=("Tahoma", 12, "bold")).pack(pady=10)
        
        citation_text = scrolledtext.ScrolledText(citation_window, height=10, width=60, wrap=tk.WORD)
        citation_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        citation_text.insert(tk.END, citation)
        
        # دکمه کپی
        ttk.Button(citation_window, text="کپی به کلیپ‌بورد", 
                  command=lambda: self.copy_to_clipboard(citation)).pack(pady=10)
    
    def generate_apa_citation(self, authors, year, title, journal, doi):
        """تولید استناد به فرمت APA"""
        # پردازش نویسندگان
        author_list = authors.split(',')
        if len(author_list) == 1:
            authors_formatted = author_list[0].strip()
        elif len(author_list) == 2:
            authors_formatted = f"{author_list[0].strip()} & {author_list[1].strip()}"
        else:
            authors_formatted = f"{author_list[0].strip()}, et al."
        
        # ساخت استناد
        citation = f"{authors_formatted} ({year}). {title}. "
        if journal:
            citation += f"{journal}. "
        if doi:
            citation += f"https://doi.org/{doi}"
        
        return citation
    
    def copy_to_clipboard(self, text):
        """کپی متن به کلیپ‌بورد"""
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("موفقیت", "متن با موفقیت کپی شد")
    
    def on_activate(self):
        """هنگام فعال شدن ماژول فراخوانی می‌شود"""
        logger.info("ماژول مقالات تحقیقاتی فعال شد")
        self.load_research()
        self.load_projects()
        self.load_analysis_titles()