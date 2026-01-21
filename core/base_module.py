# core/base_module.py
import customtkinter as ctk
from .language_manager import LanguageManager
from .rtl_support import reshape_text, set_widget_rtl, set_widget_ltr

class BaseModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app
        self.config = config
        self.language = LanguageManager(config)
        
    def create_label(self, parent, text, **kwargs):
        """ایجاد لیبل با پشتیبانی RTL"""
        if self.language.is_rtl():
            text = reshape_text(text)
            
        label = ctk.CTkLabel(parent, text=text, **kwargs)
        
        if self.language.is_rtl():
            set_widget_rtl(label)
        else:
            set_widget_ltr(label)
            
        return label
    
    def create_button(self, parent, text, **kwargs):
        """ایجاد دکمه با پشتیبانی RTL"""
        if self.language.is_rtl():
            text = reshape_text(text)
            
        button = ctk.CTkButton(parent, text=text, **kwargs)
        
        if self.language.is_rtl():
            set_widget_rtl(button)
        else:
            set_widget_ltr(button)
            
        return button
    
    def refresh_language(self):
        """تازه‌سازی زبان - باید در کلاس فرزند پیاده‌سازی شود"""
        pass