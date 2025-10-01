import customtkinter as ctk
from tkinter import messagebox
import os
import json

class SettingsModule(ctk.CTkFrame):
    def __init__(self, parent, app_instance, config, settings):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app_instance
        self.config = config
        self.settings = settings
        
        # پیدا کردن language_manager
        if hasattr(app_instance, 'language_manager'):
            self.language_manager = app_instance.language_manager
        elif hasattr(app_instance, 'language'):
            self.language_manager = app_instance.language
        else:
            from core.language_manager import LanguageManager
            self.language_manager = LanguageManager(config)
        
        # ثبت event listener
        try:
            self.app.event_bus.subscribe("language_changed", self.on_language_changed)
            self.app.event_bus.subscribe("settings_updated", self.on_settings_updated)
            self.app.event_bus.subscribe("font_changed", self.on_font_changed)
            print("✅ event listeners ثبت شدند")
        except Exception as e:
            print(f"⚠️ خطا در ثبت event listeners: {e}")
        
        # ایجاد UI
        self.create_ui()
    
    def on_language_changed(self, data):
        """واکنش به تغییر زبان"""
        try:
            self.language_manager.set_language(data["language"])
            self.refresh_ui()
        except Exception as e:
            print(f"❌ خطا در on_language_changed: {e}")
    
    def on_settings_updated(self, data):
        """واکنش به تغییر تنظیمات"""
        if "language" in data:
            try:
                self.language_manager.set_language(data["language"])
                self.refresh_ui()
            except Exception as e:
                print(f"❌ خطا در on_settings_updated: {e}")
    
    def on_font_changed(self, data):
        """واکنش به تغییر فونت"""
        try:
            print("🔄 تغییر فونت در ماژول تنظیمات")
            self.update_fonts()
        except Exception as e:
            print(f"❌ خطا در تغییر فونت تنظیمات: {e}")
    
    def refresh_ui(self):
        """تازه‌سازی رابط کاربری"""
        print("🔄 تازه‌سازی UI تنظیمات")
        try:
            self.create_ui()
        except Exception as e:
            print(f"❌ خطا در refresh_ui: {e}")
    
    def create_ui(self):
        """ایجاد رابط کاربری تنظیمات"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فقط از GRID استفاده می‌کنیم
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # فریم اصلی با قابلیت اسکرول
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure grid برای فریم اصلی
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # عنوان
        title_text = self.language_manager.get_text("settings_title")
        if self.language_manager.is_rtl():
            title_text = self.language_manager.reshape_text(title_text)
            
        title_label = ctk.CTkLabel(
            self.main_frame, 
            text=title_text,
            font=self.app.font_manager.get_font(20, "bold")
        )
        title_label.grid(row=0, column=0, pady=20, sticky="ew")
        
        # فریم محتوا
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=10)
        self.content_frame.grid_columnconfigure(1, weight=1)
        
        # ایجاد ویجت‌های تنظیمات
        self.create_settings_widgets()
        
        # دکمه ذخیره
        save_text = self.language_manager.get_text("save_changes")
        if self.language_manager.is_rtl():
            save_text = self.language_manager.reshape_text(save_text)
            
        self.save_button = ctk.CTkButton(
            self.main_frame,
            text=save_text,
            width=120,
            height=40,
            command=self.save_settings,
            font=self.app.font_manager.get_font()
        )
        self.save_button.grid(row=2, column=0, pady=30)
        
        # اعمال فونت‌ها
        self.update_fonts()
        
        print("✅ UI تنظیمات با موفقیت ایجاد شد")
    
    def create_settings_widgets(self):
        """ایجاد ویجت‌های تنظیمات"""
        self.widget_vars = {}
        
        # لیست کامل تنظیمات
        settings_config = [
            ("font_family", "combobox", {
                "label": "font_family",
                "values": ["Tahoma", "Arial", "Vazirmatn", "Segoe UI", "Microsoft Sans Serif"],
                "default": "Tahoma"
            }),
            ("font_size", "combobox", {
                "label": "font_size", 
                "values": ["10", "12", "14", "16", "18", "20"],
                "default": "14"
            }),
            ("theme_mode", "combobox", {
                "label": "theme",
                "values": ["light", "dark", "system"],
                "default": "system"
            }),
            ("sidebar_width", "combobox", {
                "label": "sidebar_width",
                "values": ["200", "250", "300", "350"],
                "default": "300"
            }),
            ("language", "combobox", {
                "label": "language",
                "values": ["fa", "en"],
                "default": "fa"
            }),
            ("auto_save", "switch", {
                "label": "auto_save",
                "default": True
            }),
            ("notifications", "switch", {
                "label": "notifications", 
                "default": True
            }),
            ("backup_interval", "combobox", {
                "label": "backup_interval",
                "values": ["6", "12", "24", "48"],
                "default": "24"
            })
        ]
        
        for i, (key, widget_type, config) in enumerate(settings_config):
            # دریافت مقدار فعلی
            current_value = self.settings.get(key, config["default"])
            
            # ایجاد برچسب
            label_text = self.language_manager.get_text(config["label"])
            if self.language_manager.is_rtl():
                label_text = self.language_manager.reshape_text(label_text)
                
            label = ctk.CTkLabel(
                self.content_frame,
                text=label_text,
                anchor="e" if self.language_manager.is_rtl() else "w",
                font=self.app.font_manager.get_font()
            )
            
            # ایجاد ویجت
            if widget_type == "combobox":
                var = ctk.StringVar(value=str(current_value))
                
                # تنظیم مقادیر نمایشی
                display_values = []
                actual_values = []
                
                if key == "language":
                    for value in config["values"]:
                        if value == "fa":
                            display_values.append(self.language_manager.get_text("persian"))
                            actual_values.append("fa")
                        elif value == "en":
                            display_values.append(self.language_manager.get_text("english"))
                            actual_values.append("en")
                        else:
                            display_values.append(value)
                            actual_values.append(value)
                    
                    current_display = self.language_manager.get_text("persian") if current_value == "fa" else self.language_manager.get_text("english")
                
                elif key == "theme_mode":
                    for value in config["values"]:
                        if value == "light":
                            display_values.append(self.language_manager.get_text("light"))
                            actual_values.append("light")
                        elif value == "dark":
                            display_values.append(self.language_manager.get_text("dark"))
                            actual_values.append("dark")
                        elif value == "system":
                            display_values.append(self.language_manager.get_text("system"))
                            actual_values.append("system")
                        else:
                            display_values.append(value)
                            actual_values.append(value)
                    
                    current_display = self.language_manager.get_text(current_value)
                
                else:
                    display_values = config["values"]
                    actual_values = config["values"]
                    current_display = str(current_value)
                
                widget = ctk.CTkComboBox(
                    self.content_frame,
                    values=display_values,
                    variable=var,
                    state="readonly",
                    width=200,
                    font=self.app.font_manager.get_font()
                )
                widget.set(current_display)
                widget.actual_values = actual_values
                widget.display_values = display_values
                
            elif widget_type == "switch":
                var = ctk.BooleanVar(value=bool(current_value))
                widget = ctk.CTkSwitch(
                    self.content_frame,
                    text="",
                    variable=var,
                    width=50
                )
            
            # موقعیت‌گذاری در grid
            if self.language_manager.is_rtl():
                # برای RTL: برچسب در راست، ویجت در چپ
                label.grid(row=i, column=1, padx=20, pady=10, sticky="e")
                widget.grid(row=i, column=0, padx=20, pady=10, sticky="w")
                self.language_manager.set_widget_rtl(label)
                if hasattr(widget, 'configure'):
                    self.language_manager.set_widget_rtl(widget)
            else:
                # برای LTR: برچسب در چپ، ویجت در راست
                label.grid(row=i, column=0, padx=20, pady=10, sticky="w")
                widget.grid(row=i, column=1, padx=20, pady=10, sticky="w")
                self.language_manager.set_widget_ltr(label)
                if hasattr(widget, 'configure'):
                    self.language_manager.set_widget_ltr(widget)
            
            self.widget_vars[key] = {
                'var': var,
                'widget': widget,
                'type': widget_type
            }
    
    def save_settings(self):
        """ذخیره تنظیمات"""
        try:
            new_settings = {}
            
            # جمع‌آوری مقادیر از ویجت‌ها
            for key, widget_info in self.widget_vars.items():
                var = widget_info['var']
                widget = widget_info['widget']
                widget_type = widget_info['type']
                
                value = var.get()
                
                # تبدیل مقادیر نمایشی به مقادیر واقعی
                if widget_type == "combobox" and hasattr(widget, 'actual_values'):
                    try:
                        index = widget.display_values.index(value)
                        value = widget.actual_values[index]
                    except (ValueError, IndexError):
                        pass
                
                new_settings[key] = value
            
            # تبدیل انواع داده
            if 'font_size' in new_settings:
                new_settings['font_size'] = int(new_settings['font_size'])
            if 'sidebar_width' in new_settings:
                new_settings['sidebar_width'] = int(new_settings['sidebar_width'])
            if 'backup_interval' in new_settings:
                new_settings['backup_interval'] = int(new_settings['backup_interval'])
            
            print(f"💾 ذخیره تنظیمات: {new_settings}")
            
            # ذخیره در فایل
            self.save_settings_to_file(new_settings)
            
            # انتشار رویداد
            self.app.event_bus.publish("settings_changed", new_settings)
            
            # نمایش پیام موفقیت با ترازبندی صحیح
            success_text = self.language_manager.get_text("success")
            saved_text = self.language_manager.get_text("changes_saved")
            
            # ایجاد پنجره پیغام سفارشی برای کنترل ترازبندی
            message_window = ctk.CTkToplevel(self)
            message_window.title(success_text)
            message_window.geometry("300x150")
            message_window.transient(self)
            message_window.grab_set()
            
            # مرکز پنجره
            message_window.grid_rowconfigure(0, weight=1)
            message_window.grid_columnconfigure(0, weight=1)
            
            # متن پیغام
            message_label = ctk.CTkLabel(
                message_window,
                text=saved_text,
                font=self.app.font_manager.get_font(14),
                wraplength=250
            )
            
            # دکمه OK
            ok_button = ctk.CTkButton(
                message_window,
                text="OK",
                command=message_window.destroy,
                width=80,
                font=self.app.font_manager.get_font()
            )
            
            # تنظیم ترازبندی بر اساس زبان
            if self.language_manager.is_rtl():
                message_label.grid(row=0, column=0, padx=20, pady=10)
                ok_button.grid(row=1, column=0, pady=10)
                message_label.configure(anchor="e", justify="right")
                self.language_manager.set_widget_rtl(message_label)
                self.language_manager.set_widget_rtl(ok_button)
            else:
                message_label.grid(row=0, column=0, padx=20, pady=10)
                ok_button.grid(row=1, column=0, pady=10)
                message_label.configure(anchor="w", justify="left")
                self.language_manager.set_widget_ltr(message_label)
                self.language_manager.set_widget_ltr(ok_button)
            
            # موقعیت دهی در مرکز
            message_window.update_idletasks()
            x = (message_window.winfo_screenwidth() // 2) - (message_window.winfo_width() // 2)
            y = (message_window.winfo_screenheight() // 2) - (message_window.winfo_height() // 2)
            message_window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            print(f"❌ خطا در ذخیره تنظیمات: {e}")
            
            # نمایش پیغام خطا
            error_window = ctk.CTkToplevel(self)
            error_window.title("خطا")
            error_window.geometry("350x150")
            error_window.transient(self)
            error_window.grab_set()
            
            error_label = ctk.CTkLabel(
                error_window,
                text=f"خطا در ذخیره تنظیمات:\n{e}",
                text_color="red",
                wraplength=300,
                font=self.app.font_manager.get_font()
            )
            error_label.pack(expand=True, padx=20, pady=20)
            
            ok_button = ctk.CTkButton(
                error_window,
                text="OK",
                command=error_window.destroy,
                font=self.app.font_manager.get_font()
            )
            ok_button.pack(pady=10)
    
    def save_settings_to_file(self, settings):
        """ذخیره تنظیمات در فایل JSON"""
        try:
            config_path = "config.json"
            
            # ذخیره با فرمت JSON
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            print(f"✅ تنظیمات در {config_path} ذخیره شد")
            
        except Exception as e:
            print(f"❌ خطا در ذخیره فایل: {e}")
            raise
    
    def update_fonts(self):
        """به روزرسانی فونت در ماژول تنظیمات"""
        try:
            print("🔄 به روزرسانی فونت در ماژول تنظیمات")
            self.apply_font_to_widgets(self)
        except Exception as e:
            print(f"❌ خطا در به روزرسانی فونت تنظیمات: {e}")
    
    def apply_font_to_widgets(self, parent_widget):
        """اعمال فونت به تمام ویجت‌های فرزند"""
        try:
            for widget in parent_widget.winfo_children():
                # اگر ویجت دارای ویژگی font است
                if hasattr(widget, 'configure'):
                    try:
                        # دریافت فونت جدید
                        new_font = self.app.font_manager.get_font()
                        widget.configure(font=new_font)
                    except Exception as e:
                        # اگر خطا در اعمال فونت بود، ادامه بده
                        pass
                
                # اعمال بازگشتی به فرزندان
                if widget.winfo_children():
                    self.apply_font_to_widgets(widget)
                    
        except Exception as e:
            print(f"⚠️ خطا در اعمال فونت به ویجت تنظیمات: {e}")
    
    def __del__(self):
        """تمیزکاری"""
        try:
            self.app.event_bus.unsubscribe("language_changed", self.on_language_changed)
            self.app.event_bus.unsubscribe("settings_updated", self.on_settings_updated)
            self.app.event_bus.unsubscribe("font_changed", self.on_font_changed)
        except:
            pass