import tkinter as tk
from tkinter import ttk

class ArticlesModule:
    def __init__(self, parent, app, config):
        self.parent = parent
        self.app = app
        self.config = config
        self.setup_ui()
        
    def setup_ui(self):
        """ایجاد رابط کاربری مدیریت مقالات"""
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # عنوان ماژول
        title_label = ttk.Label(
            main_frame,
            text="📄 " + self.config.t("articles_management"),
            font=("Tahoma", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # محتوای ماژول
        ttk.Label(main_frame, text="این بخش مدیریت مقالات است").pack(pady=10)
        
    def destroy(self):
        """تمیزکاری"""
        pass