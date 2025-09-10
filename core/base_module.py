import customtkinter as ctk
from .rtl_support import reshape_text, set_widget_rtl, set_widget_ltr

class BaseModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config = config
        self.language = app.language
        
    def setup_ui(self):
        """ایجاد رابط کاربری - باید در کلاس فرزند پیاده‌سازی شود"""
        pass
    
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        # این متد باید در کلاس فرزند پیاده‌سازی شود
        pass
    
    def apply_text_alignment(self, widget):
        """اعمال تراز متن بر اساس زبان"""
        if self.language.is_rtl():
            set_widget_rtl(widget)
        else:
            set_widget_ltr(widget)
    
    def create_label(self, parent, text, **kwargs):
        """ایجاد برچسب با تراز خودکار"""
        if self.language.is_rtl():
            text = reshape_text(text)
            
        label = ctk.CTkLabel(parent, text=text, **kwargs)
        self.apply_text_alignment(label)
        return label
    
    def create_button(self, parent, text, command, **kwargs):
        """ایجاد دکمه با تراز خودکار"""
        if self.language.is_rtl():
            text = reshape_text(text)
            
        btn = ctk.CTkButton(
            parent, 
            text=text, 
            command=command,
            anchor="e" if self.language.is_rtl() else "w",
            **kwargs
        )
        self.apply_text_alignment(btn)
        return btn