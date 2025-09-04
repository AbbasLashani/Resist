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

logger = logging.getLogger(__name__)

class DatasheetsModule(ttk.Frame):
    def __init__(self, parent, app, config):
        super().__init__(parent)
        self.app = app
        self.config = config
        self.current_filters = {}
        self.setup_ui()
        
    def setup_ui(self):
        """ایجاد رابط کاربری مدیریت دیتاشیت‌ها"""
        self.pack(fill=tk.BOTH, expand=True)
        
        # عنوان اصلی
        title_label = ttk.Label(
            self,
            text="📄 " + self.config.t("articles_management"),
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # فریم برای دکمه‌های عملیاتی
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # دکمه افزودن دیتاشیت جدید
        add_btn = ttk.Button(
            buttons_frame,
            text="➕ " + self.config.t("add_article"),
            command=self.add_datasheet
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
            command=self.load_datasheets
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # فریم برای جستجو و فیلتر
        search_frame = ttk.Frame(self)
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
        
        # جدول نمایش دیتاشیت‌ها
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ایجاد Treeview با اسکرول بار
        self.create_table(table_frame)
        
        # بارگذاری داده‌های اولیه
        self.load_datasheets()
        
    def create_table(self, parent):
        """ایجاد جدول نمایش دیتاشیت‌ها"""
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
            columns=('id', 'title', 'category', 'tags', 'status', 'added_date', 'url', 'notes', 'file_path'),
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
            ('file_path', 'مسیر فایل', 150),
            ('notes', 'یادداشت‌ها', 200),
            ('url', 'لینک', 150),
            ('added_date', 'تاریخ افزودن', 100),
            ('status', 'وضعیت', 100),
            ('tags', 'برچسب‌ها', 150),
            ('category', 'دسته‌بندی', 100),
            ('title', 'عنوان', 200),
            ('id', 'ID', 50),
        ]
        
        for col_id, text, width in columns_config:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, minwidth=50)
            # راست‌چین کردن متن در ستون‌ها
            self.tree.column(col_id, anchor='e')
        
        # مخفی کردن ستون ID
        self.tree.column('id', width=0, stretch=False)
        
        # راست‌چین کردن کل جدول
        if self.config.current_language == "fa":
            self.tree["displaycolumns"] = ('file_path', 'notes', 'url', 'added_date', 'status', 'tags', 'category', 'title')
        
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
        self.tree.bind('<Button-3>', self.show_context_menu)
        
    def show_context_menu(self, event):
        """نمایش منوی راست‌کلیک"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def copy_selected(self):
        """کپی کردن محتوای سلول انتخاب شده"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
            column_index = int(column.replace('#', '')) - 1
            
            values = self.tree.item(item_id)['values']
            if column_index < len(values):
                cell_value = str(values[column_index])
                self.clipboard_clear()
                self.clipboard_append(cell_value)
        
    def load_datasheets(self):
        """بارگذاری دیتاشیت‌ها از پایگاه داده"""
        try:
            # پاک کردن داده‌های موجود
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # دریافت داده‌ها از دیتابیس
            datasheets = self.app.db.fetch_all("""
                SELECT id, title, category, tags, status, 
                       strftime('%Y-%m-%d', added_date) as added_date, 
                       url, notes, file_path 
                FROM datasheets 
                ORDER BY added_date DESC
            """)
            
            # افزودن به جدول
            for ds in datasheets:
                self.tree.insert('', 'end', values=ds, iid=ds[0])
                
            logger.info("دیتاشیت‌ها با موفقیت بارگذاری شدند")
            
        except Exception as e:
            logger.error(f"خطا در بارگذاری دیتاشیت‌ها: {e}")
            messagebox.showerror("خطا", "خطا در بارگذاری دیتاشیت‌ها")
    
    def on_item_double_click(self, event):
        """حالت باز کردن فایل/لینک هنگام دابل‌کلیک"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = self.tree.item(item_id)['values']
            
            # با ترتیب جدید: [id, title, category, tags, status, added_date, url, notes, file_path]
            file_path = values[8] if len(values) > 8 else ""  # file_path در ایندکس 8
            url = values[6] if len(values) > 6 else ""  # url در ایندکس 6
            
            # اولویت با باز کردن فایل است
            if file_path and os.path.exists(file_path):
                self.open_selected_file()
            elif url and url.startswith(('http://', 'https://')):
                self.open_selected_url()
            else:
                # اگر فایل یا لینک نداریم، ویرایش کنیم
                self.edit_datasheet(item_id)
    
    def add_datasheet(self):
        """افزودن دیتاشیت جدید"""
        self.dialog = tk.Toplevel(self)
        self.dialog.title("افزودن دیتاشیت جدید")
        self.dialog.geometry("500x700")
        self.dialog.transient(self)
        self.dialog.grab_set()
        
        # فیلدهای فرم
        fields = [
            ('title', 'عنوان', 'entry'),
            ('category', 'دسته‌بندی', 'combo'),
            ('tags', 'برچسب‌ها (با کاما جدا کنید)', 'entry'),
            ('status', 'وضعیت', 'combo'),
            ('file_path', 'مسیر فایل', 'file'),
            ('url', 'لینک (URL)', 'entry'),
            ('notes', 'یادداشت‌ها', 'text')
        ]
        
        self.entries = {}
        
        for field_name, label, field_type in fields:
            frame = ttk.Frame(self.dialog)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            ttk.Label(frame, text=label + ":").pack(side=tk.RIGHT, padx=5)
            
            if field_type == 'entry':
                entry = ttk.Entry(frame, width=40)
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                self.entries[field_name] = entry
                
            elif field_type == 'combo':
                if field_name == 'category':
                    options = ['مقاله', 'کتاب', 'گزارش', 'پایان‌نامه', 'دیتاشیت', 'سایر']
                else:  # status
                    options = ['خوانده شده', 'در حال مطالعه', 'برنامه‌ریزی شده', 'لغو شده']
                
                combo = ttk.Combobox(frame, values=options, width=37, state='readonly')
                combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                if field_name == 'status':
                    combo.set('برنامه‌ریزی شده')  # مقدار پیش‌فرض
                self.entries[field_name] = combo
                
            elif field_type == 'file':
                file_frame = ttk.Frame(frame)
                file_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                
                entry = ttk.Entry(file_frame, width=30)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                browse_btn = ttk.Button(file_frame, text="انتخاب فایل", 
                                      command=lambda e=entry: self.browse_file(e))
                browse_btn.pack(side=tk.LEFT, padx=5)
                
                self.entries[field_name] = entry
                
            elif field_type == 'text':
                text_widget = scrolledtext.ScrolledText(frame, height=5, width=40)
                text_widget.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                # اضافه کردن تشخیص خودکار جهت متن
                text_widget.bind('<KeyRelease>', self.auto_adjust_text_direction)
                self.entries[field_name] = text_widget
        
        # دکمه‌های ذخیره و انصراف
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="ذخیره", command=self.save_datasheet).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="انصراف", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    def auto_adjust_text_direction(self, event):
        """تنظیم خودکار جهت متن بر اساس محتوا"""
        text = event.widget.get('1.0', 'end-1c')
        if self.is_persian(text):
            event.widget.tag_configure('rtl', justify='right')
            event.widget.tag_add('rtl', '1.0', 'end')
        else:
            event.widget.tag_configure('ltr', justify='left')
            event.widget.tag_add('ltr', '1.0', 'end')
    
    def is_persian(self, text):
        """تشخیص اینکه آیا متن فارسی است یا نه"""
        # اگر بیش از 50% کاراکترها فارسی باشند، متن فارسی در نظر گرفته می‌شود
        if not text.strip():
            return False
            
        persian_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return False
            
        return (persian_chars / total_chars) > 0.5
    
    def browse_file(self, entry_widget):
        """انتخاب فایل"""
        file_path = filedialog.askopenfilename(
            title="انتخاب فایل",
            filetypes=[
                ("همه فایل‌ها", "*.*"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx;*.doc"),
                ("Excel Files", "*.xlsx;*.xls;*.csv"),
                ("PowerPoint Files", "*.pptx;*.ppt"),
                ("Text Files", "*.txt;*.rtf"),
                ("Images", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff"),
                ("Audio Files", "*.mp3;*.wav;*.ogg;*.flac"),
                ("Video Files", "*.mp4;*.avi;*.mov;*.wmv;*.mkv"),
                ("Archive Files", "*.zip;*.rar;*.7z;*.tar;*.gz"),
                ("Code Files", "*.py;*.java;*.cpp;*.c;*.html;*.css;*.js;*.php"),
                ("eBooks", "*.epub;*.mobi")
            ]
        )
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
    
    def save_datasheet(self):
        """ذخیره دیتاشیت جدید"""
        try:
            # جمع‌آوری داده‌ها
            data = {}
            for field_name, widget in self.entries.items():
                if field_name == 'notes':
                    data[field_name] = widget.get('1.0', tk.END).strip()
                else:
                    data[field_name] = widget.get().strip()
            
            # اعتبارسنجی
            if not data['title']:
                messagebox.showerror("خطا", "عنوان باید وارد شود")
                return
            
            # کپی فایل به پوشه داده‌ها اگر فایل جدید انتخاب شده
            if data['file_path'] and os.path.exists(data['file_path']):
                # فقط اگر فایل خارج از پوشه داده‌ها است، آن را کپی کن
                if not data['file_path'].startswith(self.app.data_dir):
                    new_path = self.copy_file_to_data_dir(data['file_path'])
                    data['file_path'] = new_path
            
            # ذخیره در دیتابیس
            self.app.db.execute_query("""
                INSERT INTO datasheets (title, category, tags, status, file_path, url, notes, added_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                data['title'],
                data['category'],
                data['tags'],
                data['status'],
                data['file_path'],
                data['url'],
                data['notes']
            ))
            
            self.dialog.destroy()
            self.load_datasheets()
            messagebox.showinfo("موفقیت", "دیتاشیت با موفقیت اضافه شد")
            
        except Exception as e:
            logger.error(f"خطا در ذخیره دیتاشیت: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره دیتاشیت: {e}")
    
    def copy_file_to_data_dir(self, original_path):
        """کپی کردن فایل به پوشه داده‌های برنامه"""
        try:
            # ایجاد پوشه داده‌ها اگر وجود ندارد
            os.makedirs(self.app.data_dir, exist_ok=True)
            
            # نام فایل
            filename = os.path.basename(original_path)
            counter = 1
            new_filename = filename
            
            # بررسی وجود فایل تکراری
            while os.path.exists(os.path.join(self.app.data_dir, new_filename)):
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}_{counter}{ext}"
                counter += 1
            
            # مسیر جدید
            new_path = os.path.join(self.app.data_dir, new_filename)
            
            # کپی فایل
            shutil.copy2(original_path, new_path)
            
            return new_path
        except Exception as e:
            logger.error(f"خطا در کپی فایل: {e}")
            return original_path  # در صورت خطا، مسیر اصلی را بازگردان
    
    def edit_selected(self):
        """ویرایش آیتم انتخاب شده"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            self.edit_datasheet(item_id)
    
    def delete_selected(self):
        """حذف آیتم انتخاب شده"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = self.tree.item(item_id)['values']
            title = values[1] if len(values) > 1 else ""  # عنوان در ایندکس 1
            
            if messagebox.askyesno("تأیید حذف", f"آیا از حذف '{title}' مطمئن هستید؟"):
                try:
                    self.app.db.execute_query("DELETE FROM datasheets WHERE id = ?", (item_id,))
                    self.load_datasheets()
                    messagebox.showinfo("موفقیت", "دیتاشیت با موفقیت حذف شد")
                except Exception as e:
                    logger.error(f"خطا در حذف دیتاشیت: {e}")
                    messagebox.showerror("خطا", f"خطا در حذف دیتاشیت: {e}")
    
    def add_note_to_selected(self):
        """افزودن یادداشت به آیتم انتخاب شده"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = self.tree.item(item_id)['values']
            current_notes = values[7] if len(values) > 7 else ""  # یادداشت در ایندکس 7
            
            dialog = tk.Toplevel(self)
            dialog.title("افزودن یادداشت")
            dialog.geometry("400x300")
            dialog.transient(self)
            dialog.grab_set()
            
            ttk.Label(dialog, text="یادداشت:").pack(pady=5)
            
            notes_text = scrolledtext.ScrolledText(dialog, height=10, width=50)
            notes_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            notes_text.insert('1.0', current_notes)
            # اضافه کردن تشخیص خودکار جهت متن
            notes_text.bind('<KeyRelease>', self.auto_adjust_text_direction)
            
            def save_note():
                new_note = notes_text.get('1.0', tk.END).strip()
                try:
                    self.app.db.execute_query(
                        "UPDATE datasheets SET notes = ? WHERE id = ?",
                        (new_note, item_id)
                    )
                    dialog.destroy()
                    self.load_datasheets()
                    messagebox.showinfo("موفقیت", "یادداشت با موفقیت ذخیره شد")
                except Exception as e:
                    logger.error(f"خطا در ذخیره یادداشت: {e}")
                    messagebox.showerror("خطا", f"خطا در ذخیره یادداشت: {e}")
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="ذخیره", command=save_note).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_frame, text="انصراف", command=dialog.destroy).pack(side=tk.LEFT)
    
    def open_selected_file(self):
        """باز کردن فایل انتخاب شده"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = self.tree.item(item_id)['values']
            file_path = values[8] if len(values) > 8 else ""  # file_path در ایندکس 8
            
            if file_path and os.path.exists(file_path):
                try:
                    self.app.open_file(file_path)
                except Exception as e:
                    logger.error(f"خطا در باز کردن فایل: {e}")
                    messagebox.showerror("خطا", f"خطا در باز کردن فایل: {e}")
            else:
                messagebox.showwarning("هشدار", "مسیر فایل معتبر نیست یا فایل وجود ندارد")
    
    def open_selected_url(self):
        """باز کردن لینک انتخاب شده"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            values = self.tree.item(item_id)['values']
            url = values[6] if len(values) > 6 else ""  # url در ایندکس 6
            
            if url and url.startswith(('http://', 'https://')):
                try:
                    self.app.open_url(url)
                except Exception as e:
                    logger.error(f"خطا در باز کردن لینک: {e}")
                    messagebox.showerror("خطا", f"خطا در باز کردن لینک: {e}")
            else:
                messagebox.showwarning("هشدار", "لینک معتبر نیست")
    
    def edit_datasheet(self, item_id):
        """ویرایش دیتاشیت"""
        values = self.tree.item(item_id)['values']
        
        # با ترتیب جدید: [id, title, category, tags, status, added_date, url, notes, file_path]
        
        dialog = tk.Toplevel(self)
        dialog.title("ویرایش دیتاشیت")
        dialog.geometry("500x700")
        dialog.transient(self)
        dialog.grab_set()
        
        # فیلدهای فرم
        fields = [
            ('title', 'عنوان', 'entry'),
            ('category', 'دسته‌بندی', 'combo'),
            ('tags', 'برچسب‌ها (با کاما جدا کنید)', 'entry'),
            ('status', 'وضعیت', 'combo'),
            ('file_path', 'مسیر فایل', 'file'),
            ('url', 'لینک (URL)', 'entry'),
            ('notes', 'یادداشت‌ها', 'text')
        ]
        
        entries = {}
        
        # نگاشت ایندکس‌ها با ترتیب جدید
        value_mapping = {
            'title': 1,      # عنوان در ایندکس 1
            'category': 2,   # دسته‌بندی در ایندکس 2
            'tags': 3,       # برچسب‌ها در ایندکس 3
            'status': 4,     # وضعیت در ایندکس 4
            'url': 6,        # لینک در ایندکس 6
            'notes': 7,      # یادداشت‌ها در ایندکس 7
            'file_path': 8   # مسیر فایل در ایندکس 8
        }
        
        for field_name, label, field_type in fields:
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.X, padx=20, pady=5)
            
            ttk.Label(frame, text=label + ":").pack(side=tk.RIGHT, padx=5)
            
            if field_type == 'entry':
                entry = ttk.Entry(frame, width=40)
                entry.insert(0, values[value_mapping[field_name]] if len(values) > value_mapping[field_name] else "")
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                entries[field_name] = entry
                
            elif field_type == 'combo':
                if field_name == 'category':
                    options = ['مقاله', 'کتاب', 'گزارش', 'پایان‌نامه', 'دیتاشیت', 'سایر']
                else:  # status
                    options = ['خوانده شده', 'در حال مطالعه', 'برنامه‌ریزی شده', 'لغو شده']
                
                combo = ttk.Combobox(frame, values=options, width=37, state='readonly')
                current_value = values[value_mapping[field_name]] if len(values) > value_mapping[field_name] else ""
                combo.set(current_value)
                combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                entries[field_name] = combo
                
            elif field_type == 'file':
                file_frame = ttk.Frame(frame)
                file_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                
                entry = ttk.Entry(file_frame, width=30)
                entry.insert(0, values[value_mapping[field_name]] if len(values) > value_mapping[field_name] else "")
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                browse_btn = ttk.Button(file_frame, text="انتخاب فایل", 
                                      command=lambda e=entry: self.browse_file(e))
                browse_btn.pack(side=tk.LEFT, padx=5)
                
                entries[field_name] = entry
                
            elif field_type == 'text':
                text_widget = scrolledtext.ScrolledText(frame, height=5, width=40)
                notes_value = values[value_mapping[field_name]] if len(values) > value_mapping[field_name] else ""
                text_widget.insert('1.0', notes_value)
                text_widget.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                # اضافه کردن تشخیص خودکار جهت متن
                text_widget.bind('<KeyRelease>', self.auto_adjust_text_direction)
                entries[field_name] = text_widget
        
        # دکمه‌های ذخیره و انصراف
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def save_changes():
            try:
                # جمع‌آوری داده‌ها
                data = {}
                for field_name, widget in entries.items():
                    if field_name == 'notes':
                        data[field_name] = widget.get('1.0', tk.END).strip()
                    else:
                        data[field_name] = widget.get().strip()
                
                # اعتبارسنجی
                if not data['title']:
                    messagebox.showerror("خطا", "عنوان باید وارد شود")
                    return
                
                # کپی فایل به پوشه داده‌ها اگر فایل جدید انتخاب شده
                if data['file_path'] and os.path.exists(data['file_path']):
                    # فقط اگر فایل خارج از پوشه داده‌ها است، آن را کپی کن
                    if not data['file_path'].startswith(self.app.data_dir):
                        new_path = self.copy_file_to_data_dir(data['file_path'])
                        data['file_path'] = new_path
                
                # به‌روزرسانی در دیتابیس
                self.app.db.execute_query("""
                    UPDATE datasheets 
                    SET title = ?, category = ?, tags = ?, status = ?, file_path = ?, url = ?, notes = ?
                    WHERE id = ?
                """, (
                    data['title'],
                    data['category'],
                    data['tags'],
                    data['status'],
                    data['file_path'],
                    data['url'],
                    data['notes'],
                    item_id
                ))
                
                dialog.destroy()
                self.load_datasheets()
                messagebox.showinfo("موفقیت", "دیتاشیت با موفقیت ویرایش شد")
                
            except Exception as e:
                logger.error(f"خطا در ویرایش دیتاشیت: {e}")
                messagebox.showerror("خطا", f"خطا در ویرایش دیتاشیت: {e}")
        
        ttk.Button(btn_frame, text="ذخیره تغییرات", command=save_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="انصراف", command=dialog.destroy).pack(side=tk.LEFT)
    
    def apply_filters(self, event=None):
        """اعمال فیلترهای جستجو"""
        search_text = self.search_var.get().lower()
        
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            # جستجو در عنوان، برچسب‌ها، یادداشت‌ها و لینک
            # با ترتیب جدید: [id, title, category, tags, status, added_date, url, notes, file_path]
            match = any([
                search_text in str(values[1]).lower(),  # title در ایندکس 1
                search_text in str(values[3]).lower(),  # tags در ایندکس 3
                search_text in str(values[7]).lower(),  # notes در ایندکس 7
                search_text in str(values[6]).lower()   # url در ایندکس 6
            ]) if search_text else True
            
            # اعمال فیلتر وضعیت
            if self.current_filters.get('status'):
                if self.current_filters['status'] != 'all':
                    status_match = str(values[4]).lower() == self.current_filters['status']  # status در ایندکس 4
                    match = match and status_match
            
            self.tree.item(item, tags=('hidden',) if not match else ())
        
        # مخفی کردن مواردی که تطابق ندارند
        self.tree.tag_configure('hidden', display='none')
    
    def set_filter(self, filter_type):
        """اعمال فیلتر بر اساس نوع"""
        status_map = {
            'all': None,
            'read': 'خوانده شده',
            'reading': 'در حال مطالعه',
            'planned': 'برنامه‌ریزی شده'
        }
        
        self.current_filters['status'] = status_map.get(filter_type)
        self.apply_filters()
    
    def export_to_excel(self):
        """خروجی اکسل از دیتاشیت‌ها"""
        try:
            # دریافت داده‌ها
            datasheets = self.app.db.fetch_all("""
                SELECT title, category, tags, status, 
                       strftime('%Y-%m-%d', added_date) as added_date, 
                       url, notes, file_path 
                FROM datasheets 
                ORDER BY added_date DESC
            """)
            
            # ایجاد DataFrame
            df = pd.DataFrame(datasheets, columns=[
                'عنوان', 'دسته‌بندی', 'برچسب‌ها', 'وضعیت', 'تاریخ افزودن', 'لینک', 'یادداشت‌ها', 'مسیر فایل'
            ])
            
            # ذخیره به صورت Excel
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
                title="ذخیره به عنوان فایل Excel"
            )
            
            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                messagebox.showinfo("موفقیت", f"داده‌ها با موفقیت در {file_path} ذخیره شدند")
                
        except Exception as e:
            logger.error(f"خطا در خروجی اکسل: {e}")
            messagebox.showerror("خطا", f"خطا در ایجاد خروجی اکسل: {e}")
    
    def on_activate(self):
        """هنگام فعال شدن ماژول فراخوانی می‌شود"""
        logger.info("ماژول دیتاشیت‌ها فعال شد")
        self.load_datasheets()