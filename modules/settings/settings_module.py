import customtkinter as ctk
from core.base_module import BaseModule

class SettingsModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری تنظیمات"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # فریم اصلی با قابلیت اسکرول
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # عنوان
        title_text = self.language.get_text('settings_title')
        title = self.create_label(
            main_frame,
            text=title_text,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        
        # فریم برای تنظیمات
        settings_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        settings_frame.pack(fill="x", padx=50, pady=20)
        
        # تنظیمات در دو ستون
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # تنظیم زبان
        language_label_text = self.language.get_text('language')
        language_label = self.create_label(
            settings_frame,
            text=language_label_text,
            font=ctk.CTkFont(size=16)
        )
        language_label.grid(row=0, column=0, padx=10, pady=10, sticky="e" if self.language.is_rtl() else "w")
        
        language_var = ctk.StringVar(value=self.config.get("language", "fa"))
        language_options = ["fa", "en"]
        language_display = {
            "fa": self.language.get_text("persian"),
            "en": self.language.get_text("english")
        }
        
        language_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=[language_display[lang] for lang in language_options],
            variable=ctk.StringVar(value=language_display[language_var.get()]),
            command=lambda choice: self.change_language(
                next(key for key, value in language_display.items() if value == choice)
            ),
            width=150
        )
        language_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.apply_text_alignment(language_menu)
        
        # تنظیم تم
        theme_label_text = self.language.get_text('theme')
        theme_label = self.create_label(
            settings_frame,
            text=theme_label_text,
            font=ctk.CTkFont(size=16)
        )
        theme_label.grid(row=1, column=0, padx=10, pady=10, sticky="e" if self.language.is_rtl() else "w")
        
        theme_var = ctk.StringVar(value=self.config.get("theme_mode", "System"))
        theme_options = ["Light", "Dark", "System"]
        theme_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=theme_options,
            variable=theme_var,
            command=self.change_theme,
            width=150
        )
        theme_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.apply_text_alignment(theme_menu)
        
        # تنظیم اندازه فونت
        font_size_label_text = self.language.get_text('font_size')
        font_size_label = self.create_label(
            settings_frame,
            text=font_size_label_text,
            font=ctk.CTkFont(size=16)
        )
        font_size_label.grid(row=2, column=0, padx=10, pady=10, sticky="e" if self.language.is_rtl() else "w")
        
        font_size_var = ctk.StringVar(value=str(self.config.get("font_size", 14)))
        font_size_options = ["12", "14", "16", "18", "20"]
        font_size_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=font_size_options,
            variable=font_size_var,
            command=self.change_font_size,
            width=150
        )
        font_size_menu.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self.apply_text_alignment(font_size_menu)
        
        # تنظیم عرض سایدبار
        sidebar_label_text = self.language.get_text('sidebar_width')
        sidebar_label = self.create_label(
            settings_frame,
            text=sidebar_label_text,
            font=ctk.CTkFont(size=16)
        )
        sidebar_label.grid(row=3, column=0, padx=10, pady=10, sticky="e" if self.language.is_rtl() else "w")
        
        sidebar_var = ctk.StringVar(value=str(self.config.get("sidebar_width", 200)))
        sidebar_options = ["180", "200", "220", "240"]
        sidebar_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=sidebar_options,
            variable=sidebar_var,
            command=self.change_sidebar_width,
            width=150
        )
        sidebar_menu.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        self.apply_text_alignment(sidebar_menu)
        
        # دکمه ذخیره
        save_btn_text = self.language.get_text('save_changes')
        save_btn = self.create_button(
            settings_frame,
            text=save_btn_text,
            command=self.save_settings,
            font=ctk.CTkFont(size=16),
            height=40
        )
        save_btn.grid(row=4, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        self.setup_ui()
    
    def change_language(self, language):
        """تغییر زبان"""
        self.app.event_bus.publish("language_changed", {"language": language})
    
    def change_theme(self, theme):
        """تغییر تم"""
        self.app.theme_mode = theme
    
    def change_font_size(self, size):
        """تغییر اندازه فونت"""
        self.app.font_size = int(size)
    
    def change_sidebar_width(self, width):
        """تغییر عرض سایدبار"""
        self.app.sidebar_width = int(width)
    
    def save_settings(self):
        """ذخیره تنظیمات"""
        self.config.set("language", self.language.get_current_language())
        self.config.set("theme_mode", self.app.theme_mode)
        self.config.set("font_size", self.app.font_size)
        self.config.set("sidebar_width", self.app.sidebar_width)
        
        # نمایش پیام موفقیت
        success_text = self.language.get_text('changes_saved')
        success_label = self.create_label(
            self,
            text=success_text,
            font=ctk.CTkFont(size=14),
            text_color="green"
        )
        success_label.place(relx=0.5, rely=0.9, anchor="center")
        
        # حذف پیام پس از 3 ثانیه
        self.after(3000, success_label.destroy)