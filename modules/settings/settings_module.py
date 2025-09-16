import customtkinter as ctk
from tkinter import messagebox
import os
import json
from core.language_manager import LanguageManager

class SettingsModule(ctk.CTkFrame):
    def __init__(self, parent, app_instance, config, settings):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app_instance
        self.config = config
        self.settings = settings
        self.language_manager = LanguageManager(config)
        
        # ایجاد UI
        self.create_ui()
    
    def create_ui(self):
        """ایجاد رابط کاربری تنظیمات"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی با قابلیت اسکرول
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # عنوان تب تنظیمات
        title_label = ctk.CTkLabel(
            main_frame, 
            text=self.language_manager.get_text("settings_title"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # فریم اصلی برای محتوای تنظیمات
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ایجاد ویجت‌های تنظیمات
        self.create_settings_widgets(content_frame)
        
        # دکمه ذخیره تغییرات
        save_button = ctk.CTkButton(
            content_frame,
            text=self.language_manager.get_text("save_changes"),
            width=120,
            height=40,
            command=self.save_settings
        )
        save_button.grid(row=7, column=0, columnspan=2, pady=30)
    
    def create_settings_widgets(self, parent):
        """ایجاد ویجت‌های تنظیمات"""
        # پیکربندی شبکه برای چیدمان منظم
        parent.grid_columnconfigure(1, weight=1)
        
        # لیست تنظیمات و ویجت‌های مربوطه
        settings_config = [
            ("theme_mode", "combobox", {
                "label": "theme",
                "values": ["Light", "Dark", "System"],
                "row": 0
            }),
            ("font_size", "combobox", {
                "label": "font_size",
                "values": [12, 14, 16, 18],
                "row": 1
            }),
            ("sidebar_width", "combobox", {
                "label": "sidebar_width",
                "values": [200, 250, 300],
                "row": 2
            }),
            ("language", "combobox", {
                "label": "language",
                "values": ["fa", "en"],
                "row": 3
            }),
            ("auto_save", "switch", {
                "label": "auto_save",
                "row": 4
            }),
            ("notifications", "switch", {
                "label": "notifications",
                "row": 5
            }),
            ("backup_interval", "combobox", {
                "label": "backup_interval",
                "values": [6, 12, 24, 48],
                "row": 6
            })
        ]
        
        self.widget_vars = {}
        
        for key, widget_type, config in settings_config:
            # ایجاد برچسب
            label = ctk.CTkLabel(
                parent,
                text=self.language_manager.get_text(config["label"]),
                anchor="e"
            )
            label.grid(row=config["row"], column=0, padx=20, pady=10, sticky="e")
            
            # ایجاد ویجت بر اساس نوع
            if widget_type == "combobox":
                current_value = str(self.settings.get(key, config["values"][0]))
                var = ctk.StringVar(value=current_value)
                widget = ctk.CTkComboBox(
                    parent,
                    values=[str(v) for v in config["values"]],
                    variable=var,
                    state="readonly",
                    width=200
                )
            elif widget_type == "switch":
                current_value = self.settings.get(key, False)
                var = ctk.BooleanVar(value=current_value)
                widget = ctk.CTkSwitch(
                    parent,
                    text="",
                    variable=var
                )
            
            widget.grid(row=config["row"], column=1, padx=20, pady=10, sticky="w")
            self.widget_vars[key] = var
    
    def save_settings(self):
        """ذخیره تنظیمات"""
        new_settings = {}
        
        # جمع‌آوری مقادیر از ویجت‌ها
        for key, var in self.widget_vars.items():
            new_settings[key] = var.get()
        
        # تبدیل مقادیر به نوع مناسب
        if 'font_size' in new_settings:
            new_settings['font_size'] = int(new_settings['font_size'])
        if 'sidebar_width' in new_settings:
            new_settings['sidebar_width'] = int(new_settings['sidebar_width'])
        if 'backup_interval' in new_settings:
            new_settings['backup_interval'] = int(new_settings['backup_interval'])
        
        # اعمال تنظیمات جدید
        self.app.event_bus.publish("settings_changed", new_settings)
        
        # نمایش پیام موفقیت
        messagebox.showinfo(
            self.language_manager.get_text("success"),
            self.language_manager.get_text("changes_saved")
        )