# research_assistant/modules/search/search_module.py
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class SearchModule(tk.Frame):
    module_name = "جستجو"
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()
        
    def setup_ui(self):
        """ایجاد رابط کاربری جستجوی علمی"""
        title_label = ttk.Label(
            self,
            text="🔎 جستجوی علمی",
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # پیام موقت
        message = ttk.Label(
            self,
            text="این بخش در حال توسعه است. به زودی ویژگی‌های جستجوی علمی اضافه خواهد شد.",
            font=("Tahoma", 10)
        )
        message.pack(pady=50)