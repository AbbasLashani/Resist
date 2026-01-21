class ThemeManager:
    def __init__(self):
        self.themes = {
            "light": {
                "primary": "#3B8ED0",
                "secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "background": "#f8f9fa",
                "surface": "#ffffff",
                "text": "#212529"
            },
            "dark": {
                "primary": "#3B8ED0",
                "secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "background": "#121212",
                "surface": "#1e1e1e",
                "text": "#e0e0e0"
            }
        }
    
    def get_color(self, color_name, theme_mode=None):
        """دریافت رنگ بر اساس تم"""
        if theme_mode is None:
            theme_mode = "light"
        
        theme = self.themes.get(theme_mode.lower(), self.themes["light"])
        return theme.get(color_name, "#000000")
    
    def get_theme(self, theme_mode=None):
        """دریافت تم کامل"""
        if theme_mode is None:
            theme_mode = "light"
        
        return self.themes.get(theme_mode.lower(), self.themes["light"])