# research_assistant/modules/research/research_module.py
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class ResearchModule(tk.Frame):
    module_name = "تحقیق"
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()
        
    def setup_ui(self):
        """ایجاد رابط کاربری ابزارهای تحقیقاتی"""
        title_label = ttk.Label(
            self,
            text="🔍 ابزارهای تحقیقاتی",
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # پیام موقت
        message = ttk.Label(
            self,
            text="این بخش در حال توسعه است. به زودی ویژگی‌های تحقیقاتی اضافه خواهد شد.",
            font=("Tahoma", 10)
        )
        message.pack(pady=50)