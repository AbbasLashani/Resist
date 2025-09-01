# research_assistant/main.py
import tkinter as tk
from core.app import ResearchAssistantApp

def main():
    """نقطه ورود اصلی برنامه"""
    root = tk.Tk()
    root.tk_setPalette(background='white')
    
    # تنظیمات راست‌چین برای فارسی
    root.option_add('*Font', 'Tahoma 10')
    root.option_add('*Label.anchor', 'e')
    root.option_add('*Button.anchor', 'center')
    
    app = ResearchAssistantApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()