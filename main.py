# research_assistant/main.py
import tkinter as tk
from core.app import ResearchAssistantApp

def main():
    """نقطه ورود اصلی برنامه"""
    root = tk.Tk()
    app = ResearchAssistantApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()