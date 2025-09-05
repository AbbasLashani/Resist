import customtkinter as ctk
import json
import os

class ThemeManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_self()
        return cls._instance
    
    def _init_self(self):
        """مقداردهی اولیه تم‌ها"""
        self.themes = {
            "light": {
                "bg": "#FFFFFF",
                "fg": "#000000",
                "primary": "#1976D2",
                "secondary": "#424242",
                "accent": "#FF4081",
                "surface": "#F5F5F5",
                "error": "#F44336",
                "warning": "#FFC107",
                "success": "#4CAF50",
                "on_primary": "#FFFFFF",
                "on_secondary": "#FFFFFF",
                "on_surface": "#000000",
                "border": "#E0E0E0"
            },
            "dark": {
                "bg": "#121212",
                "fg": "#FFFFFF",
                "primary": "#2196F3",
                "secondary": "#BDBDBD",
                "accent": "#FF4081",
                "surface": "#1E1E1E",
                "error": "#F44336",
                "warning": "#FFC107",
                "success": "#4CAF50",
                "on_primary": "#000000",
                "on_secondary": "#000000",
                "on_surface": "#FFFFFF",
                "border": "#424242"
            }
        }
        
        self.current_theme = "light"
    
    def get_color(self, color_name):
        """دریافت رنگ بر اساس تم فعال"""
        return self.themes[self.current_theme].get(color_name, "#000000")
    
    def get_current_theme(self):
        """دریافت تم فعلی"""
        return self.current_theme