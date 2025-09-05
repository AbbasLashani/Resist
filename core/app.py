import customtkinter as ctk
from .database import Database
from .config import Config
from .event_bus import EventBus
from .theme_manager import ThemeManager
import importlib
import os

class ResearchAssistantApp(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.config = Config()
        self.db = Database(self.config)
        self.event_bus = EventBus()
        self.theme = ThemeManager()
        
        self.current_module = None
        self.modules = {}
        
        self.setup_ui()
        self.load_modules()
        self.setup_event_listeners()
        
    def setup_ui(self):
        """ایجاد رابط کاربری اصلی"""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # نوار کناری
        self.sidebar = self.create_sidebar()
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        # منطقه محتوا
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # نوار وضعیت
        self.status_bar = self.create_status_bar()
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
    
    def create_sidebar(self):
        """ایجاد نوار کناری"""
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=15)
        
        # هدر نوار کناری
        header = ctk.CTkLabel(
            sidebar,
            text="📚 دستیار تحقیقاتی",
            font=ctk.CTkFont(size=20, weight="bold"),
            height=60
        )
        header.pack(pady=(20, 10), padx=20, fill="x")
        
        # دکمه‌های ماژول‌ها
        modules = [
            ("🏠", "داشبورد", "dashboard"),
            ("📄", "مقالات", "papers"),
            ("📅", "برنامه‌ریزی", "planner"),
            ("📝", "یادداشت‌ها", "notes"),
            ("🔍", "تحقیق", "research"),
            ("✏️", "نوشتن", "writer"),
            ("⚙️", "تنظیمات", "settings")
        ]
        
        for icon, text, module_name in modules:
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon} {text}",
                font=ctk.CTkFont(size=14),
                height=45,
                corner_radius=10,
                anchor="w",
                fg_color="transparent",
                hover_color=self.theme.get_color("surface"),
                border_width=0,
                command=lambda mn=module_name: self.switch_module(mn)
            )
            btn.pack(pady=5, padx=15, fill="x")
        
        # سوئیچ تم
        theme_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        theme_frame.pack(side="bottom", pady=20, padx=15, fill="x")
        
        ctk.CTkLabel(theme_frame, text="تم:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        
        theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_switch = ctk.CTkSegmentedButton(
            theme_frame,
            values=["Light", "Dark", "System"],
            variable=theme_var,
            command=self.change_theme
        )
        theme_switch.pack(fill="x", pady=(5, 0))
        
        return sidebar
    
    def change_theme(self, theme_mode):
        """تغییر تم برنامه"""
        ctk.set_appearance_mode(theme_mode)
        self.event_bus.publish("theme_changed", {"theme": theme_mode})
    
    def create_status_bar(self):
        """ایجاد نوار وضعیت"""
        status_bar = ctk.CTkFrame(self, height=30, corner_radius=10)
        
        # وضعیت اتصال
        status_label = ctk.CTkLabel(
            status_bar,
            text="✅ آماده",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(side="left", padx=10)
        
        # اطلاعات پایگاه داده
        db_info = ctk.CTkLabel(
            status_bar,
            text="پایگاه داده: فعال",
            font=ctk.CTkFont(size=12)
        )
        db_info.pack(side="right", padx=10)
        
        return status_bar
    
    def load_modules(self):
        """بارگذاری ماژول‌ها"""
        module_paths = {
            "dashboard": "modules.dashboard.dashboard_module",
            "papers": "modules.papers.papers_module",
            "planner": "modules.planner.planner_module",
            "notes": "modules.notes.notes_module",
            "research": "modules.research.research_module",
            "writer": "modules.writer.writer_module"
        }
        
        for name, path in module_paths.items():
            try:
                module = importlib.import_module(path)
                module_class = getattr(module, f"{name.capitalize()}Module")
                self.modules[name] = module_class(self.content_frame, self, self.config)
            except Exception as e:
                print(f"خطا در بارگذاری ماژول {name}: {e}")
                # ایجاد ماژول جایگزین در صورت خطا
                self.modules[name] = self.create_fallback_module(name)
        
        # فعال کردن ماژول پیش‌فرض
        self.switch_module("dashboard")
    
    def create_fallback_module(self, name):
        """ایجاد ماژول جایگزین در صورت خطا"""
        fallback = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        label_text = f"ماژول {name} در حال توسعه است"
        if name == "notes":
            label_text = "ماژول یادداشت‌ها به زودی اضافه خواهد شد"
        
        label = ctk.CTkLabel(
            fallback,
            text=label_text,
            font=ctk.CTkFont(size=16)
        )
        label.pack(expand=True)
        
        return fallback
    
    def switch_module(self, module_name):
        """تعویض ماژول فعال"""
        if self.current_module:
            self.current_module.pack_forget()
        
        if module_name in self.modules:
            self.current_module = self.modules[module_name]
            self.current_module.pack(fill="both", expand=True)
            
            # ارسال رویداد تغییر ماژول
            self.event_bus.publish("module_changed", {"module": module_name})
    
    def setup_event_listeners(self):
        """تنظیم شنوندگان رویداد"""
        self.event_bus.subscribe("theme_changed", self.on_theme_changed)
        self.event_bus.subscribe("module_changed", self.on_module_changed)
    
    def on_theme_changed(self, data):
        """واکنش به تغییر تم"""
        print(f"تم تغییر کرد به: {data['theme']}")
    
    def on_module_changed(self, data):
        """واکنش به تغییر ماژول"""
        print(f"ماژول تغییر کرد به: {data['module']}")