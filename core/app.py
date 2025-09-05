import customtkinter as ctk
from .database import Database
from .config import Config
from .event_bus import EventBus
from .theme_manager import ThemeManager
from .rtl_support import reshape_text, set_widget_rtl
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
        
        # تنظیمات پیش‌فرض
        self.font_size = self.config.get("font_size", 14)
        self.theme_mode = self.config.get("theme_mode", "System")
        
        self.current_module = None
        self.modules = {}
        
        self.setup_ui()
        self.load_modules()
        self.setup_event_listeners()
        
        # اعمال تم اولیه
        self.apply_theme_settings()
        
    def setup_ui(self):
        """ایجاد رابط کاربری اصلی با پشتیبانی RTL"""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=4)  # محتوا 4 واحد فضای بیشتر بگیرد
        self.grid_columnconfigure(1, weight=1)  # سایدبار 1 واحد فضا بگیرد
        
        # منطقه محتوا (در سمت چپ)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # نوار کناری (در سمت راست)
        self.sidebar = self.create_sidebar()
        self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        
        # نوار وضعیت
        self.status_bar = self.create_status_bar()
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
    
    def create_sidebar(self):
        """ایجاد نوار کناری با پشتیبانی RTL"""
        sidebar = ctk.CTkFrame(self, width=250, corner_radius=15)
        sidebar.pack_propagate(False)  # جلوگیری از تغییر اندازه توسط فرزندان

        # هدر نوار کناری با متن فارسی
        header_text = reshape_text("📚 دستیار تحقیقاتی")
        header = ctk.CTkLabel(
            sidebar,
            text=header_text,
            font=ctk.CTkFont(size=20, weight="bold"),
            height=60
        )
        header.pack(pady=(20, 10), padx=20, fill="x")
        set_widget_rtl(header)
        
        # دکمه‌های ماژول‌ها با متن فارسی
        modules = [
            ("🏠", "داشبورد", "dashboard"),
            ("📄", "مقالات", "papers"),
            ("📅", "برنامه‌ریزی", "planner"),
            ("📝", "یادداشت‌ها", "notes"),
            ("🔍", "تحقیق", "research"),
            ("✏️", "نوشتن", "writer"),
            ("⚙️", "تنظیمات", "settings")
        ]
        
        # فریم برای دکمه‌های منو با اسکرول اگر نیاز باشد
        menu_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        menu_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for icon, text, module_name in modules:
            btn_text = reshape_text(f"{icon} {text}")
            btn = ctk.CTkButton(
                menu_frame,
                text=btn_text,
                font=ctk.CTkFont(size=self.font_size),
                height=45,
                corner_radius=10,
                anchor="e",  # تراز به راست
                fg_color=("#F0F0F0", "#2B2B2B"),  # رنگ پس‌زمینه متفاوت برای حالت عادی
                hover_color=("#E0E0E0", "#3C3C3C"),  # رنگ متفاوت برای حالت هاور
                text_color=("#000000", "#FFFFFF"),  # رنگ متن برای تم روشن و تاریک
                border_width=0,
                command=lambda mn=module_name: self.switch_module(mn)
            )
            btn.pack(pady=5, fill="x")
            set_widget_rtl(btn)
        
        # سوئیچ تم با متن فارسی
        theme_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        theme_frame.pack(side="bottom", pady=20, padx=15, fill="x")
        
        theme_label_text = reshape_text("تم:")
        theme_label = ctk.CTkLabel(
            theme_frame, 
            text=theme_label_text, 
            font=ctk.CTkFont(size=self.font_size)
        )
        theme_label.pack(anchor="e")
        set_widget_rtl(theme_label)
        
        theme_var = ctk.StringVar(value=self.theme_mode)
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
        self.theme_mode = theme_mode
        self.config.set("theme_mode", theme_mode)
        ctk.set_appearance_mode(theme_mode)
        self.event_bus.publish("theme_changed", {"theme": theme_mode})
        
        # اعمال مجدد تنظیمات تم
        self.apply_theme_settings()
    
    def apply_theme_settings(self):
        """اعمال تنظیمات تم روی تمام ویجت‌ها"""
        # این متد می‌تواند برای به روزرسانی رنگ‌ها پس از تغییر تم استفاده شود
        # در اینجا می‌توانید رنگ‌های خاص تم را روی ویجت‌ها اعمال کنید
        pass
    
    def create_status_bar(self):
        """ایجاد نوار وضعیت با پشتیبانی RTL"""
        status_bar = ctk.CTkFrame(self, height=30, corner_radius=10)
        
        # وضعیت اتصال با متن فارسی
        status_text = reshape_text("✅ آماده")
        status_label = ctk.CTkLabel(
            status_bar,
            text=status_text,
            font=ctk.CTkFont(size=self.font_size)
        )
        status_label.pack(side="right", padx=10)
        set_widget_rtl(status_label)
        
        # اطلاعات پایگاه داده با متن فارسی
        db_text = reshape_text("پایگاه داده: فعال")
        db_info = ctk.CTkLabel(
            status_bar,
            text=db_text,
            font=ctk.CTkFont(size=self.font_size)
        )
        db_info.pack(side="left", padx=10)
        set_widget_rtl(db_info)
        
        return status_bar
    
    def load_modules(self):
        """بارگذاری ماژول‌ها"""
        module_paths = {
            "dashboard": "modules.dashboard.dashboard_module",
            "papers": "modules.papers.papers_module",
            "planner": "modules.planner.planner_module",
            "notes": "modules.notes.notes_module",
            "research": "modules.research.research_module",
            "writer": "modules.writer.writer_module",
            "settings": "modules.settings.settings_module"
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
        from .rtl_support import reshape_text
        
        fallback = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        label_text = f"ماژول {name} در حال توسعه است"
        if name == "notes":
            label_text = "ماژول یادداشت‌ها به زودی اضافه خواهد شد"
        
        label = ctk.CTkLabel(
            fallback,
            text=reshape_text(label_text),
            font=ctk.CTkFont(size=16)
        )
        label.pack(expand=True)
        set_widget_rtl(label)
        
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
        self.event_bus.subscribe("font_size_changed", self.on_font_size_changed)
    
    def on_theme_changed(self, data):
        """واکنش به تغییر تم"""
        print(f"تم تغییر کرد به: {data['theme']}")
    
    def on_module_changed(self, data):
        """واکنش به تغییر ماژول"""
        print(f"ماژول تغییر کرد به: {data['module']}")
    
    def on_font_size_changed(self, data):
        """واکنش به تغییر اندازه فونت"""
        self.font_size = data["size"]
        self.config.set("font_size", self.font_size)
        print(f"اندازه فونت تغییر کرد به: {self.font_size}")
        
        # بازسازی رابط کاربری با اندازه فونت جدید
        self.setup_ui()
        self.load_modules()