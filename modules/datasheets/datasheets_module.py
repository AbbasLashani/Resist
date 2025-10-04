import customtkinter as ctk
import os
import json
import sqlite3
from tkinter import filedialog, messagebox
import webbrowser
from datetime import datetime
import pandas as pd
import openpyxl

class DatasheetsModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app
        self.config = config
        
        # پیدا کردن language_manager و font_manager
        if hasattr(app, 'language_manager'):
            self.language_manager = app.language_manager
        elif hasattr(app, 'language'):
            self.language_manager = app.language
            
        if hasattr(app, 'font_manager'):
            self.font_manager = app.font_manager
        else:
            from core.font_manager import FontManager
            self.font_manager = FontManager(config)
        
        # داده‌ها
        self.datasheets = []
        self.categories = self.load_categories()
        self.current_filter = "همه"
        self.search_term = ""
        self.font_widgets = []
        
        # ایجاد جدول در دیتابیس
        self.init_database()
        
        # ثبت event listeners
        self.setup_event_listeners()
        
        # ایجاد UI
        self.setup_ui()
        
        # بارگذاری داده‌ها
        self.load_datasheets()
    
    def load_categories(self):
        """بارگذاری دسته‌بندی‌ها از فایل"""
        categories_file = "categories.json"
        default_categories = ["الکترونیکی", "مکانیکی", "نرم‌افزاری", "سخت‌افزاری", "متفرقه"]
        
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
            categories_file = "categories.json"
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"❌ خطا در ذخیره دسته‌بندی‌ها: {e}")
            return False
    
    def init_database(self):
        """ایجاد جدول دیتاشیت‌ها در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ جدول دیتاشیت‌ها ایجاد شد")
        except Exception as e:
            print(f"❌ خطا در ایجاد جدول دیتاشیت‌ها: {e}")
    
    def setup_event_listeners(self):
        """تنظیم شنوندگان رویداد"""
        try:
            self.app.event_bus.unsubscribe("font_changed", self.on_font_changed)
            self.app.event_bus.subscribe("font_changed", self.on_font_changed)
            print("✅ Event listeners برای دیتاشیت‌ها ثبت شدند")
        except Exception as e:
            print(f"⚠️ خطا در ثبت event listeners دیتاشیت‌ها: {e}")
    
    def on_font_changed(self, data):
        """واکنش به تغییر فونت"""
        try:
            if not self.winfo_exists():
                return
            self.after(50, self.update_all_fonts)
        except Exception as e:
            print(f"⚠️ خطا در مدیریت تغییر فونت دیتاشیت‌ها: {e}")
    
    def update_all_fonts(self):
        """به روزرسانی تمام فونت‌ها"""
        try:
            if not self.winfo_exists():
                return
            
            for widget_info in self.font_widgets:
                try:
                    widget = widget_info['widget']
                    font_type = widget_info['font_type']
                    
                    if widget.winfo_exists():
                        if font_type == "title":
                            new_font = self.font_manager.get_font(weight="bold")
                        elif font_type == "heading":
                            new_font = self.font_manager.get_font(weight="bold")
                        elif font_type == "small":
                            new_font = self.font_manager.get_font()
                        else:
                            new_font = self.font_manager.get_font()
                        
                        widget.configure(font=new_font)
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"⚠️ خطا در آپدیت فونت دیتاشیت‌ها: {e}")
    
    def register_font_widget(self, widget, font_type="normal"):
        """ثبت ویجت برای مدیریت فونت"""
        self.font_widgets.append({
            'widget': widget,
            'font_type': font_type
        })
    
    def setup_ui(self):
        """ایجاد رابط کاربری"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except:
                pass
        
        self.font_widgets = []
        
        # چیدمان اصلی
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # نوار ابزار بالا
        self.create_toolbar()
        
        # بخش اصلی
        self.create_main_section()
        
        print("✅ UI دیتاشیت‌ها با موفقیت ایجاد شد")
    
    def create_toolbar(self):
        """ایجاد نوار ابزار"""
        toolbar = ctk.CTkFrame(self, height=60)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        toolbar.grid_propagate(False)
        
        # عنوان
        title_text = "مدیریت دیتاشیت‌ها و مستندات" if self.language_manager.is_rtl() else "Datasheets & Documents Manager"
        title = ctk.CTkLabel(
            toolbar,
            text=title_text,
            font=self.font_manager.get_font(weight="bold")
        )
        title.pack(side="right" if self.language_manager.is_rtl() else "left", padx=15, pady=10)
        self.register_font_widget(title, "title")
        
        # دکمه‌های action
        button_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_frame.pack(side="left" if self.language_manager.is_rtl() else "right", padx=10, pady=10)
        
        # دکمه مدیریت دسته‌بندی‌ها
        category_text = "🗂️ مدیریت دسته‌بندی‌ها" if self.language_manager.is_rtl() else "🗂️ Manage Categories"
        category_btn = ctk.CTkButton(
            button_frame,
            text=category_text,
            command=self.manage_categories,
            width=150,
            height=35,
            font=self.font_manager.get_font(),
            fg_color="#FF9800",
            hover_color="#F57C00"
        )
        category_btn.pack(side="right" if self.language_manager.is_rtl() else "left", padx=5)
        self.register_font_widget(category_btn, "normal")
        
        # دکمه خروجی اکسل
        export_text = "📊 خروجی اکسل" if self.language_manager.is_rtl() else "📊 Export Excel"
        export_btn = ctk.CTkButton(
            button_frame,
            text=export_text,
            command=self.export_to_excel,
            width=120,
            height=35,
            font=self.font_manager.get_font(),
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        export_btn.pack(side="right" if self.language_manager.is_rtl() else "left", padx=5)
        self.register_font_widget(export_btn, "normal")
        
        # دکمه افزودن جدید
        add_text = "➕ افزودن جدید" if self.language_manager.is_rtl() else "➕ Add New"
        add_btn = ctk.CTkButton(
            button_frame,
            text=add_text,
            command=self.show_add_dialog,
            width=120,
            height=35,
            font=self.font_manager.get_font(),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        add_btn.pack(side="right" if self.language_manager.is_rtl() else "left", padx=5)
        self.register_font_widget(add_btn, "normal")
    
    def create_main_section(self):
        """ایجاد بخش اصلی"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # تنظیم grid
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # نوار فیلتر و جستجو
        self.create_filter_bar(main_frame)
        
        # لیست دیتاشیت‌ها
        self.create_datasheets_list(main_frame)
    
    def create_filter_bar(self, parent):
        """ایجاد نوار فیلتر و جستجو"""
        filter_frame = ctk.CTkFrame(parent, height=50)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_propagate(False)
        
        # جستجو
        search_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        search_frame.pack(side="right" if self.language_manager.is_rtl() else "left", padx=10, pady=5)
        
        search_text = "جستجو..." if self.language_manager.is_rtl() else "Search..."
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=search_text,
            width=200,
            height=35,
            font=self.font_manager.get_font()
        )
        self.search_entry.pack(side="right" if self.language_manager.is_rtl() else "left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)
        self.register_font_widget(self.search_entry, "normal")
        
        # فعال کردن کپی-پیست برای فیلد جستجو
        self.search_entry.bind("<Control-c>", lambda e: self.copy_text(e))
        self.search_entry.bind("<Control-v>", lambda e: self.paste_text(e))
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=40,
            height=35,
            command=self.perform_search,
            font=self.font_manager.get_font()
        )
        search_btn.pack(side="right" if self.language_manager.is_rtl() else "left", padx=5)
        self.register_font_widget(search_btn, "normal")
        
        # فیلتر دسته‌بندی
        filter_btn_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filter_btn_frame.pack(side="left" if self.language_manager.is_rtl() else "right", padx=10, pady=5)
        
        filter_text = "فیلتر دسته‌بندی" if self.language_manager.is_rtl() else "Category Filter"
        self.filter_combo = ctk.CTkComboBox(
            filter_btn_frame,
            values=["همه"] + self.categories if self.language_manager.is_rtl() else ["All"] + self.categories,
            width=150,
            height=35,
            font=self.font_manager.get_font(),
            command=self.on_filter_changed
        )
        self.filter_combo.set("همه" if self.language_manager.is_rtl() else "All")
        self.filter_combo.pack(side="right" if self.language_manager.is_rtl() else "left", padx=5)
        self.register_font_widget(self.filter_combo, "normal")
    
    def create_datasheets_list(self, parent):
        """ایجاد لیست دیتاشیت‌ها"""
        # فریم لیست
        self.list_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew")
        
        # برچسب خالی
        self.empty_label = ctk.CTkLabel(
            self.list_frame,
            text="هیچ دیتاشیتی یافت نشد" if self.language_manager.is_rtl() else "No datasheets found",
            font=self.font_manager.get_font(),
            text_color=("#666666", "#AAAAAA")
        )
        self.empty_label.pack(pady=50)
        self.register_font_widget(self.empty_label, "normal")
        
        self.datasheet_widgets = []
    
    def refresh_datasheets_list(self):
        """تازه‌سازی لیست دیتاشیت‌ها"""
        # پاک کردن ویجت‌های قبلی
        for widget in self.datasheet_widgets:
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except:
                pass
        self.datasheet_widgets = []
        
        # فیلتر کردن داده‌ها
        filtered_data = self.datasheets
        
        if self.current_filter != "همه" and self.current_filter != "All":
            filtered_data = [item for item in filtered_data if item['category'] == self.current_filter]
        
        if self.search_term:
            filtered_data = [item for item in filtered_data if 
                           self.search_term.lower() in item['name'].lower() or 
                           self.search_term.lower() in item['description'].lower() or 
                           self.search_term.lower() in item['tags'].lower()]
        
        # نمایش برچسب خالی اگر داده‌ای نیست
        if not filtered_data:
            self.empty_label.pack(pady=50)
            return
        else:
            self.empty_label.pack_forget()
        
        # ایجاد کارت برای هر دیتاشیت
        for i, item in enumerate(filtered_data):
            self.create_datasheet_card(item, i)
    
    def create_datasheet_card(self, item, index):
        """ایجاد کارت دیتاشیت - نسخه بهبود یافته"""
        card = ctk.CTkFrame(
            self.list_frame,
            corner_radius=12,
            border_width=1,
            border_color=("#E0E0E0", "#404040"),
            height=130
        )
        card.pack(fill="x", padx=8, pady=6)
        card.pack_propagate(False)
        
        # محتوای کارت
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        # سمت راست: اطلاعات اصلی
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="right" if self.language_manager.is_rtl() else "left", fill="both", expand=True)
        
        # نام و دسته‌بندی در یک خط
        header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 8))
        
        name_label = ctk.CTkLabel(
            header_frame,
            text=item['name'],
            font=self.font_manager.get_font(size=14, weight="bold"),
            anchor="w" if not self.language_manager.is_rtl() else "e"
        )
        name_label.pack(side="left" if not self.language_manager.is_rtl() else "right", fill="x", expand=True)
        
        category_badge = ctk.CTkLabel(
            header_frame,
            text=f"📁 {item['category']}",
            font=self.font_manager.get_font(size=11),
            text_color=("#666666", "#AAAAAA"),
            anchor="e" if not self.language_manager.is_rtl() else "w"
        )
        category_badge.pack(side="right" if not self.language_manager.is_rtl() else "left", padx=(10, 0))
        
        # توضیحات
        if item['description']:
            desc_text = item['description'][:120] + "..." if len(item['description']) > 120 else item['description']
            desc_label = ctk.CTkLabel(
                info_frame,
                text=desc_text,
                font=self.font_manager.get_font(size=11),
                wraplength=400,
                anchor="w" if not self.language_manager.is_rtl() else "e",
                justify="left"
            )
            desc_label.pack(fill="x", pady=(0, 8))
        
        # هشتگ‌ها
        if item['tags']:
            tags_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            tags_frame.pack(fill="x")
            
            tags = [tag.strip() for tag in item['tags'].split(',') if tag.strip()]
            for tag in tags[:4]:  # حداکثر 4 هشتگ
                tag_label = ctk.CTkLabel(
                    tags_frame,
                    text=f"#{tag}",
                    font=self.font_manager.get_font(size=10),
                    text_color=("#2196F3", "#64B5F6"),
                    padx=8,
                    pady=2,
                    corner_radius=10
                )
                if self.language_manager.is_rtl():
                    tag_label.pack(side="right", padx=(5, 0))
                else:
                    tag_label.pack(side="left", padx=(0, 5))
        
        # سمت چپ: دکمه‌های action - بهبود ترازبندی
        action_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=180)
        action_frame.pack(side="left" if self.language_manager.is_rtl() else "right", padx=(0, 10) if self.language_manager.is_rtl() else (10, 0))
        action_frame.pack_propagate(False)
        
        # دکمه‌های action در یک خط
        btn_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_frame.pack(expand=True)
        
        # ایجاد دکمه‌های هم‌اندازه
        button_config = {
            "width": 36,
            "height": 36,
            "font": self.font_manager.get_font(size=12),
            "corner_radius": 8
        }
        
        # دکمه باز کردن فایل
        if item['file_path'] and os.path.exists(item['file_path']):
            file_icon = "📄" if item['file_type'] == 'pdf' else "📂"
            file_btn = ctk.CTkButton(
                btn_frame,
                text=file_icon,
                command=lambda i=item: self.open_file(i),
                fg_color="#2196F3",
                hover_color="#1976D2",
                **button_config
            )
            file_btn.pack(side="left" if not self.language_manager.is_rtl() else "right", padx=2)
        
        # دکمه لینک آنلاین
        if item['online_link']:
            link_btn = ctk.CTkButton(
                btn_frame,
                text="🌐",
                command=lambda i=item: self.open_link(i),
                fg_color="#FF9800",
                hover_color="#F57C00",
                **button_config
            )
            link_btn.pack(side="left" if not self.language_manager.is_rtl() else "right", padx=2)
        
        # دکمه ویرایش
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            command=lambda i=item: self.edit_datasheet(i),
            fg_color="#4CAF50",
            hover_color="#45a049",
            **button_config
        )
        edit_btn.pack(side="left" if not self.language_manager.is_rtl() else "right", padx=2)
        
        # دکمه حذف
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️",
            command=lambda i=item: self.delete_datasheet(i),
            fg_color="#f44336",
            hover_color="#da190b",
            **button_config
        )
        delete_btn.pack(side="left" if not self.language_manager.is_rtl() else "right", padx=2)
        
        self.datasheet_widgets.append(card)
    
    def manage_categories(self):
        """مدیریت دسته‌بندی‌ها"""
        dialog = ManageCategoriesDialog(self, self.language_manager, self.font_manager, self.categories)
        self.wait_window(dialog)
        
        if dialog.result:
            self.categories = dialog.result
            self.save_categories()
            self.filter_combo.configure(values=["همه"] + self.categories if self.language_manager.is_rtl() else ["All"] + self.categories)
            self.refresh_datasheets_list()
    
    def export_to_excel(self):
        """خروجی به اکسل"""
        try:
            if not self.datasheets:
                messagebox.showwarning("هشدار", "هیچ داده‌ای برای خروجی وجود ندارد")
                return
            
            # ایجاد DataFrame
            data = []
            for item in self.datasheets:
                data.append({
                    'نام': item['name'],
                    'دسته‌بندی': item['category'],
                    'لینک آنلاین': item['online_link'] or '',
                    'مسیر فایل': item['file_path'] or '',
                    'نوع فایل': item['file_type'] or '',
                    'هشتگ‌ها': item['tags'],
                    'توضیحات': item['description'],
                    'تاریخ ایجاد': item['created_at']
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
                messagebox.showinfo("موفقیت", f"داده‌ها با موفقیت در {file_path} ذخیره شد")
                
        except Exception as e:
            print(f"❌ خطا در خروجی اکسل: {e}")
            messagebox.showerror("خطا", f"خطا در خروجی اکسل: {e}")
    
    def copy_text(self, event):
        """کپی متن"""
        try:
            widget = event.widget
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except Exception as e:
            print(f"❌ خطا در کپی متن: {e}")
    
    def paste_text(self, event):
        """پیست متن"""
        try:
            widget = event.widget
            if isinstance(widget, ctk.CTkEntry):
                clipboard_text = self.clipboard_get()
                widget.insert(ctk.INSERT, clipboard_text)
        except Exception as e:
            print(f"❌ خطا در پیست متن: {e}")
    
    def show_add_dialog(self):
        """نمایش دیالوگ افزودن دیتاشیت جدید"""
        dialog = AddDatasheetDialog(self, self.language_manager, self.font_manager, self.categories)
        self.wait_window(dialog)
        
        if dialog.result:
            self.save_datasheet(dialog.result)
    
    def edit_datasheet(self, item):
        """ویرایش دیتاشیت"""
        dialog = AddDatasheetDialog(self, self.language_manager, self.font_manager, self.categories, item)
        self.wait_window(dialog)
        
        if dialog.result:
            self.update_datasheet(item['id'], dialog.result)
    
    def save_datasheet(self, data):
        """ذخیره دیتاشیت جدید در دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO datasheets (name, category, online_link, file_path, file_type, tags, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data['name'], data['category'], data['online_link'], data['file_path'], 
                  data['file_type'], data['tags'], data['description']))
            
            conn.commit()
            conn.close()
            
            print("✅ دیتاشیت جدید ذخیره شد")
            self.load_datasheets()
            
            # انتشار رویداد برای به روزرسانی داشبورد
            self.app.event_bus.publish("datasheet_added", {
                "name": data['name'],
                "category": data['category'],
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ خطا در ذخیره دیتاشیت: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره دیتاشیت: {e}")
    
    def update_datasheet(self, item_id, data):
        """بروزرسانی دیتاشیت"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE datasheets 
                SET name=?, category=?, online_link=?, file_path=?, file_type=?, tags=?, description=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (data['name'], data['category'], data['online_link'], data['file_path'], 
                  data['file_type'], data['tags'], data['description'], item_id))
            
            conn.commit()
            conn.close()
            
            print("✅ دیتاشیت بروزرسانی شد")
            self.load_datasheets()
            
            # انتشار رویداد برای به روزرسانی داشبورد
            self.app.event_bus.publish("datasheet_updated", {
                "name": data['name'],
                "category": data['category'],
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ خطا در بروزرسانی دیتاشیت: {e}")
            messagebox.showerror("خطا", f"خطا در بروزرسانی دیتاشیت: {e}")
    
    def delete_datasheet(self, item):
        """حذف دیتاشیت"""
        if messagebox.askyesno("تأیید حذف", f"آیا از حذف '{item['name']}' اطمینان دارید؟"):
            try:
                conn = sqlite3.connect('research_assistant.db')
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM datasheets WHERE id=?', (item['id'],))
                
                conn.commit()
                conn.close()
                
                print("✅ دیتاشیت حذف شد")
                self.load_datasheets()
                
                # انتشار رویداد برای به روزرسانی داشبورد
                self.app.event_bus.publish("datasheet_deleted", {
                    "name": item['name'],
                    "category": item['category'],
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ خطا در حذف دیتاشیت: {e}")
                messagebox.showerror("خطا", f"خطا در حذف دیتاشیت: {e}")
    
    def open_file(self, item):
        """باز کردن فایل"""
        try:
            if item['file_path'] and os.path.exists(item['file_path']):
                os.startfile(item['file_path']) if os.name == 'nt' else webbrowser.open(item['file_path'])
            else:
                messagebox.showwarning("هشدار", "فایل یافت نشد")
                
        except Exception as e:
            print(f"❌ خطا در باز کردن فایل: {e}")
            messagebox.showerror("خطا", f"خطا در باز کردن فایل: {e}")
    
    def open_link(self, item):
        """باز کردن لینک آنلاین"""
        try:
            if item['online_link']:
                webbrowser.open(item['online_link'])
            else:
                messagebox.showwarning("هشدار", "لینک موجود نیست")
        except Exception as e:
            print(f"❌ خطا در باز کردن لینک: {e}")
            messagebox.showerror("خطا", f"خطا در باز کردن لینک: {e}")
    
    def load_datasheets(self):
        """بارگذاری دیتاشیت‌ها از دیتابیس"""
        try:
            conn = sqlite3.connect('research_assistant.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, category, online_link, file_path, file_type, tags, description, created_at
                FROM datasheets 
                ORDER BY created_at DESC
            ''')
            
            self.datasheets = []
            for row in cursor.fetchall():
                self.datasheets.append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'online_link': row[3],
                    'file_path': row[4],
                    'file_type': row[5],
                    'tags': row[6] or '',
                    'description': row[7] or '',
                    'created_at': row[8]
                })
            
            conn.close()
            print(f"✅ {len(self.datasheets)} دیتاشیت بارگذاری شد")
            self.refresh_datasheets_list()
            
        except Exception as e:
            print(f"❌ خطا در بارگذاری دیتاشیت‌ها: {e}")
    
    def on_search(self, event=None):
        """هنگام جستجو"""
        self.search_term = self.search_entry.get().strip()
        self.refresh_datasheets_list()
    
    def perform_search(self):
        """انجام جستجو"""
        self.on_search()
    
    def on_filter_changed(self, choice):
        """هنگام تغییر فیلتر"""
        self.current_filter = choice
        self.refresh_datasheets_list()
    
    def __del__(self):
        """تمیزکاری"""
        try:
            self.app.event_bus.unsubscribe("font_changed", self.on_font_changed)
        except:
            pass


class AddDatasheetDialog(ctk.CTkToplevel):
    def __init__(self, parent, language_manager, font_manager, categories, item=None):
        super().__init__(parent)
        self.parent = parent
        self.language_manager = language_manager
        self.font_manager = font_manager
        self.categories = categories
        self.item = item
        self.result = None
        
        self.title("افزودن دیتاشیت جدید" if language_manager.is_rtl() else "Add New Datasheet")
        self.geometry("600x750")  # افزایش سایز
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.create_ui()
        self.center_window()
        
        # فعال کردن کلیدهای میانبر
        self.bind("<Control-s>", lambda e: self.save())
        self.bind("<Control-S>", lambda e: self.save())
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری دیالوگ - نسخه بهبود یافته"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # عنوان
        title_text = "ویرایش دیتاشیت" if self.item else "افزودن دیتاشیت جدید"
        if not self.language_manager.is_rtl():
            title_text = "Edit Datasheet" if self.item else "Add New Datasheet"
            
        title = ctk.CTkLabel(
            main_frame,
            text=title_text,
            font=self.font_manager.get_font(size=18, weight="bold")
        )
        title.pack(pady=(0, 25))
        
        # فرم اصلی با اسکرول
        form_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_container.pack(fill="both", expand=True)
        
        # اسکرول برای فرم
        form_scroll = ctk.CTkScrollableFrame(form_container, fg_color="transparent", height=550)
        form_scroll.pack(fill="both", expand=True)
        
        # Configure grid برای چیدمان بهتر
        form_scroll.grid_columnconfigure(0, weight=1)
        
        row = 0
        
        # نام قطعه
        name_label = ctk.CTkLabel(
            form_scroll,
            text="نام قطعه *:",
            font=self.font_manager.get_font(size=12, weight="bold"),
            anchor="w"
        )
        name_label.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        
        self.name_entry = ctk.CTkEntry(
            form_scroll,
            font=self.font_manager.get_font(size=12),
            height=40,
            placeholder_text="نام قطعه را وارد کنید..."
        )
        self.name_entry.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        row += 1
        
        # دسته‌بندی
        category_label = ctk.CTkLabel(
            form_scroll,
            text="دسته‌بندی *:",
            font=self.font_manager.get_font(size=12, weight="bold"),
            anchor="w"
        )
        category_label.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        
        self.category_combo = ctk.CTkComboBox(
            form_scroll,
            values=self.categories,
            font=self.font_manager.get_font(size=12),
            height=40,
            state="readonly"
        )
        if self.categories:
            self.category_combo.set(self.categories[0])
        self.category_combo.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        row += 1
        
        # لینک آنلاین
        link_label = ctk.CTkLabel(
            form_scroll,
            text="لینک آنلاین (اختیاری):",
            font=self.font_manager.get_font(size=12, weight="bold"),
            anchor="w"
        )
        link_label.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        
        self.link_entry = ctk.CTkEntry(
            form_scroll,
            font=self.font_manager.get_font(size=12),
            height=40,
            placeholder_text="https://..."
        )
        self.link_entry.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        row += 1
        
        # فایل پیوست
        file_label = ctk.CTkLabel(
            form_scroll,
            text="فایل پیوست (اختیاری):",
            font=self.font_manager.get_font(size=12, weight="bold"),
            anchor="w"
        )
        file_label.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        
        file_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        file_frame.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        file_frame.grid_columnconfigure(1, weight=1)
        
        self.file_btn = ctk.CTkButton(
            file_frame,
            text="📁 انتخاب فایل",
            command=self.select_file,
            font=self.font_manager.get_font(size=12),
            height=40,
            width=120,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.file_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.file_label = ctk.CTkLabel(
            file_frame,
            text="هیچ فایلی انتخاب نشده",
            font=self.font_manager.get_font(size=11),
            text_color=("#666666", "#AAAAAA"),
            anchor="w"
        )
        self.file_label.grid(row=0, column=1, sticky="ew")
        row += 1
        
        # هشتگ‌ها
        tags_label = ctk.CTkLabel(
            form_scroll,
            text="هشتگ‌ها (با کاما جدا کنید):",
            font=self.font_manager.get_font(size=12, weight="bold"),
            anchor="w"
        )
        tags_label.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        
        self.tags_entry = ctk.CTkEntry(
            form_scroll,
            font=self.font_manager.get_font(size=12),
            height=40,
            placeholder_text="مثال: الکترونیک,آردوینو,سنسور"
        )
        self.tags_entry.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        row += 1
        
        # توضیحات
        desc_label = ctk.CTkLabel(
            form_scroll,
            text="توضیحات (اختیاری):",
            font=self.font_manager.get_font(size=12, weight="bold"),
            anchor="w"
        )
        desc_label.grid(row=row, column=0, sticky="w", pady=(0, 8))
        row += 1
        
        self.desc_text = ctk.CTkTextbox(
            form_scroll,
            font=self.font_manager.get_font(size=12),
            height=120
        )
        self.desc_text.grid(row=row, column=0, sticky="ew", pady=(0, 30))
        row += 1
        
        # دکمه‌های action
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ انصراف",
            command=self.cancel,
            font=self.font_manager.get_font(size=12),
            height=45,
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=120
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 ذخیره (Ctrl+S)",
            command=self.save,
            font=self.font_manager.get_font(size=12, weight="bold"),
            height=45,
            fg_color="#4CAF50",
            hover_color="#45a049",
            width=150
        )
        save_btn.pack(side="right")
        
        # پر کردن فرم در حالت ویرایش
        if self.item:
            self.fill_form()
        
        # فوکوس روی فیلد نام
        self.after(100, lambda: self.name_entry.focus())
    
    def copy_text(self, event):
        """کپی متن"""
        try:
            widget = event.widget
            if hasattr(widget, 'selection_get') and widget.selection_present():
                selected_text = widget.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except Exception as e:
            print(f"❌ خطا در کپی متن: {e}")
    
    def paste_text(self, event):
        """پیست متن"""
        try:
            widget = event.widget
            clipboard_text = self.clipboard_get()
            if isinstance(widget, ctk.CTkEntry):
                widget.insert(ctk.INSERT, clipboard_text)
            elif isinstance(widget, ctk.CTkTextbox):
                widget.insert(ctk.INSERT, clipboard_text)
        except Exception as e:
            print(f"❌ خطا در پیست متن: {e}")
    
    def fill_form(self):
        """پر کردن فرم با داده‌های موجود"""
        self.name_entry.insert(0, self.item['name'])
        self.category_combo.set(self.item['category'])
        if self.item['online_link']:
            self.link_entry.insert(0, self.item['online_link'])
        if self.item['file_path']:
            self.file_label.configure(text=os.path.basename(self.item['file_path']))
            self.selected_file_path = self.item['file_path']
        if self.item['tags']:
            self.tags_entry.insert(0, self.item['tags'])
        if self.item['description']:
            self.desc_text.insert("1.0", self.item['description'])
    
    def select_file(self):
        """انتخاب فایل"""
        file_path = filedialog.askopenfilename(
            title="انتخاب فایل",
            filetypes=[
                ("همه فایل‌ها", "*.*"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx *.doc"),
                ("Excel files", "*.xlsx *.xls"),
                ("Text files", "*.txt")
            ]
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
    
    def save(self):
        """ذخیره دیتاشیت"""
        name = self.name_entry.get().strip()
        category = self.category_combo.get()
        
        if not name:
            messagebox.showerror("خطا", "لطفاً نام قطعه را وارد کنید")
            return
        
        if not category:
            messagebox.showerror("خطا", "لطفاً دسته‌بندی را انتخاب کنید")
            return
        
        # تعیین نوع فایل
        file_type = None
        if self.selected_file_path:
            ext = os.path.splitext(self.selected_file_path)[1].lower()
            if ext == '.pdf':
                file_type = 'pdf'
            elif ext in ['.docx', '.doc']:
                file_type = 'word'
            elif ext in ['.xlsx', '.xls']:
                file_type = 'excel'
            else:
                file_type = 'other'
        
        self.result = {
            'name': name,
            'category': category,
            'online_link': self.link_entry.get().strip(),
            'file_path': self.selected_file_path,
            'file_type': file_type,
            'tags': self.tags_entry.get().strip(),
            'description': self.desc_text.get("1.0", "end-1c").strip()
        }
        
        self.destroy()
    
    def cancel(self):
        """انصراف"""
        self.destroy()


class ManageCategoriesDialog(ctk.CTkToplevel):
    def __init__(self, parent, language_manager, font_manager, categories):
        super().__init__(parent)
        self.parent = parent
        self.language_manager = language_manager
        self.font_manager = font_manager
        self.categories = categories.copy()
        self.result = None
        
        self.title("مدیریت دسته‌بندی‌ها" if language_manager.is_rtl() else "Manage Categories")
        self.geometry("500x550")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # ایجاد رفرنس مستقیم به فریم‌ها
        self.main_frame = None
        self.list_frame = None
        self.category_entries = []
        
        self.create_ui()
        self.center_window()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_ui(self):
        """ایجاد رابط کاربری بهبود یافته"""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # عنوان
        title_text = "مدیریت دسته‌بندی‌ها" if self.language_manager.is_rtl() else "Manage Categories"
        title = ctk.CTkLabel(
            self.main_frame,
            text=title_text,
            font=self.font_manager.get_font(size=16, weight="bold")
        )
        title.pack(pady=(0, 20))
        
        # فریم لیست دسته‌بندی‌ها
        list_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        list_container.pack(fill="both", expand=True, pady=(0, 20))
        
        # برچسب لیست
        list_label = ctk.CTkLabel(
            list_container,
            text="دسته‌بندی‌های موجود:",
            font=self.font_manager.get_font(size=12, weight="bold"),
            anchor="w"
        )
        list_label.pack(fill="x", pady=(0, 10))
        
        # لیست دسته‌بندی‌ها با اسکرول
        self.list_frame = ctk.CTkScrollableFrame(
            list_container, 
            fg_color="transparent", 
            height=300
        )
        self.list_frame.pack(fill="both", expand=True)
        
        self.category_entries = []
        
        # ایجاد آیتم‌های دسته‌بندی موجود
        for i, category in enumerate(self.categories):
            self.create_category_item(category, i)
        
        # دکمه افزودن دسته‌بندی جدید
        add_btn = ctk.CTkButton(
            self.main_frame,
            text="➕ افزودن دسته‌بندی جدید",
            command=self.add_new_category,
            font=self.font_manager.get_font(),
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        add_btn.pack(fill="x", pady=(0, 15))
        
        # دکمه‌های action
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        cancel_text = "❌ انصراف" if self.language_manager.is_rtl() else "❌ Cancel"
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            command=self.cancel,
            font=self.font_manager.get_font(),
            height=40,
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=120
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        save_text = "💾 ذخیره تغییرات" if self.language_manager.is_rtl() else "💾 Save Changes"
        save_btn = ctk.CTkButton(
            btn_frame,
            text=save_text,
            command=self.save,
            font=self.font_manager.get_font(weight="bold"),
            height=40,
            fg_color="#2196F3",
            hover_color="#1976D2",
            width=150
        )
        save_btn.pack(side="right")
    
    def create_category_item(self, category, index):
        """ایجاد آیتم دسته‌بندی"""
        item_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        item_frame.pack(fill="x", pady=3)
        
        entry = ctk.CTkEntry(
            item_frame,
            font=self.font_manager.get_font(),
            height=38,
            placeholder_text="نام دسته‌بندی..."
        )
        entry.insert(0, category)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # فعال کردن کپی-پیست
        entry.bind("<Control-c>", lambda e: self.copy_text(e))
        entry.bind("<Control-v>", lambda e: self.paste_text(e))
        
        delete_btn = ctk.CTkButton(
            item_frame,
            text="🗑️",
            width=45,
            height=38,
            command=lambda idx=index: self.delete_category(idx),
            font=self.font_manager.get_font(),
            fg_color="#f44336",
            hover_color="#da190b"
        )
        delete_btn.pack(side="right")
        
        self.category_entries.append(entry)
    
    def copy_text(self, event):
        """کپی متن"""
        try:
            widget = event.widget
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except Exception as e:
            print(f"❌ خطا در کپی متن: {e}")
    
    def paste_text(self, event):
        """پیست متن"""
        try:
            widget = event.widget
            if isinstance(widget, ctk.CTkEntry):
                clipboard_text = self.clipboard_get()
                widget.insert(ctk.INSERT, clipboard_text)
        except Exception as e:
            print(f"❌ خطا در پیست متن: {e}")
    
    def add_new_category(self):
        """افزودن دسته‌بندی جدید"""
        new_category_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        new_category_frame.pack(fill="x", pady=3)
        
        entry = ctk.CTkEntry(
            new_category_frame,
            font=self.font_manager.get_font(),
            height=38,
            placeholder_text="نام دسته‌بندی جدید را وارد کنید..."
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # فعال کردن کپی-پیست
        entry.bind("<Control-c>", lambda e: self.copy_text(e))
        entry.bind("<Control-v>", lambda e: self.paste_text(e))
        
        delete_btn = ctk.CTkButton(
            new_category_frame,
            text="🗑️",
            width=45,
            height=38,
            command=lambda: self.delete_category_entry(new_category_frame, entry),
            font=self.font_manager.get_font(),
            fg_color="#f44336",
            hover_color="#da190b"
        )
        delete_btn.pack(side="right")
        
        self.category_entries.append(entry)
        
        # فوکوس روی فیلد جدید
        self.after(100, lambda: entry.focus())
        
        print("✅ دسته‌بندی جدید اضافه شد")
    
    def delete_category(self, index):
        """حذف دسته‌بندی موجود"""
        if len(self.category_entries) > 1:
            # پیدا کردن فریم والد این entry
            entry = self.category_entries[index]
            parent_frame = entry.master
            
            # حذف از لیست و از رابط
            self.category_entries.pop(index)
            parent_frame.destroy()
            
            print(f"✅ دسته‌بندی در ایندکس {index} حذف شد")
        else:
            messagebox.showwarning(
                "هشدار", 
                "حداقل یک دسته‌بندی باید وجود داشته باشد"
            )
    
    def delete_category_entry(self, frame, entry):
        """حذف آیتم دسته‌بندی جدید"""
        if len(self.category_entries) > 1:
            if entry in self.category_entries:
                self.category_entries.remove(entry)
            frame.destroy()
            print("✅ دسته‌بندی جدید حذف شد")
        else:
            messagebox.showwarning(
                "هشدار", 
                "حداقل یک دسته‌بندی باید وجود داشته باشد"
            )
    
    def save(self):
        """ذخیره تغییرات"""
        new_categories = []
        
        # جمع‌آوری دسته‌بندی‌های معتبر
        for entry in self.category_entries:
            category = entry.get().strip()
            if category:  # فقط دسته‌بندی‌های غیر خالی
                if category not in new_categories:  # جلوگیری از تکراری
                    new_categories.append(category)
                else:
                    messagebox.showwarning(
                        "هشدار", 
                        f"دسته‌بندی '{category}' تکراری است و فقط یک بار ذخیره می‌شود"
                    )
        
        # بررسی حداقل یک دسته‌بندی
        if not new_categories:
            messagebox.showerror(
                "خطا", 
                "حداقل یک دسته‌بندی باید وجود داشته باشد"
            )
            return
        
        self.result = new_categories
        print(f"✅ {len(new_categories)} دسته‌بندی ذخیره شد")
        self.destroy()
    
    def cancel(self):
        """انصراف"""
        print("❌ مدیریت دسته‌بندی‌ها لغو شد")
        self.destroy()