import customtkinter as ctk
from core.rtl_support import reshape_text, set_widget_rtl

class SettingsModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config = config
        
        self.setup_ui()
    
    def setup_ui(self):
        """ایجاد رابط کاربری تنظیمات"""
        # عنوان
        title = ctk.CTkLabel(
            self,
            text=reshape_text("تنظیمات برنامه"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        set_widget_rtl(title)
        
        # فریم برای تنظیمات
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        # تنظیم اندازه فونت
        font_size_label = ctk.CTkLabel(
            settings_frame,
            text=reshape_text("اندازه فونت:"),
            font=ctk.CTkFont(size=16)
        )
        font_size_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        set_widget_rtl(font_size_label)
        
        font_size_var = ctk.StringVar(value=str(self.config.get("font_size", 14)))
        font_size_options = ["12", "14", "16", "18", "20"]
        font_size_menu = ctk.CTkOptionMenu(
            settings_frame,
            values=font_size_options,
            variable=font_size_var,
            command=self.change_font_size
        )
        font_size_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # تنظیمات اضافی می‌توانند اینجا اضافه شوند
        # ...
    
    def change_font_size(self, size):
        """تغییر اندازه فونت"""
        self.app.event_bus.publish("font_size_changed", {"size": int(size)})