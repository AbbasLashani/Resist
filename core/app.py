import customtkinter as ctk
from .database import Database
from .config import Config
from .event_bus import EventBus
from .theme_manager import ThemeManager
from .language_manager import LanguageManager
from .rtl_support import reshape_text, set_widget_rtl, set_widget_ltr
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
        self.language = LanguageManager(self.config)
        
        # تنظیمات پیش‌فرض
        self.font_size = self.config.get("font_size", 14)
        self.theme_mode = self.config.get("theme_mode", "System")
        self.sidebar_width = self.config.get("sidebar_width", 200)
        
        self.current_module = None
        self.modules = {}
        self.current_module_name = "dashboard"
        
        # ایجاد فریم‌های اصلی
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.setup_ui()
        self.load_modules()
        self.setup_event_listeners()
        
        # اعمال تم اولیه
        ctk.set_appearance_mode(self.theme_mode)
        
    def setup_ui(self):
        """ایجاد رابط کاربری اصلی با پشتیبانی RTL/LTR"""
        # پاک کردن ویجت‌های موجود در main_container
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Configure grid برای main_container
        self.main_container.grid_rowconfigure(0, weight=1)
        
        if self.language.is_rtl():
            # برای فارسی: سایدبار در ستون 1، محتوا در ستون 0
            self.main_container.grid_columnconfigure(0, weight=1)  # محتوا
            self.main_container.grid_columnconfigure(1, weight=0)  # سایدبار
        else:
            # برای انگلیسی: سایدبار در ستون 0، محتوا در ستون 1
            self.main_container.grid_columnconfigure(0, weight=0)  # سایدبار
            self.main_container.grid_columnconfigure(1, weight=1)  # محتوا
        
        # ایجاد نوار کناری
        self.sidebar = self.create_sidebar()
        
        # ایجاد ناحیه محتوا
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # چیدمان بر اساس زبان
        if self.language.is_rtl():
            # برای فارسی: سایدبار در راست، محتوا در چپ
            self.sidebar.grid(row=0, column=1, sticky="ns", padx=(10, 0), pady=0)
            self.content_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        else:
            # برای انگلیسی: سایدبار در چپ، محتوا در راست
            self.sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 10), pady=0)
            self.content_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        
        # نوار وضعیت
        self.status_bar = self.create_status_bar()
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(10, 0))
    
    def create_sidebar(self):
        """ایجاد نوار کناری با پشتیبانی RTL/LTR"""
        sidebar = ctk.CTkFrame(self.main_container, width=self.sidebar_width, corner_radius=10)
        sidebar.grid_propagate(False)
        
        # هدر نوار کناری
        header_text = f"📚 {self.language.get_text('app_title')}"
        if self.language.is_rtl():
            header_text = reshape_text(header_text)
            
        header = ctk.CTkLabel(
            sidebar,
            text=header_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40
        )
        header.pack(pady=(15, 10), padx=15, fill="x")
        
        if self.language.is_rtl():
            set_widget_rtl(header)
        else:
            set_widget_ltr(header)
        
        # دکمه‌های ماژول‌ها
        modules = [
            ("🏠", "dashboard"),
            ("📄", "papers"),
            ("📅", "planner"),
            ("📝", "notes"),
            ("🔍", "research"),
            ("✏️", "writer"),
            ("⚙️", "settings")
        ]
        
        menu_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        menu_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        for icon, module_name in modules:
            btn_text = f"{icon} {self.language.get_text(module_name)}"
            if self.language.is_rtl():
                btn_text = reshape_text(btn_text)
                
            btn = ctk.CTkButton(
                menu_frame,
                text=btn_text,
                font=ctk.CTkFont(size=self.font_size - 1),
                height=35,
                corner_radius=8,
                anchor="e" if self.language.is_rtl() else "w",
                fg_color=("#F0F0F0", "#2B2B2B"),
                hover_color=("#E0E0E0", "#3C3C3C"),
                text_color=("#000000", "#FFFFFF"),
                border_width=0,
                command=lambda mn=module_name: self.switch_module(mn)
            )
            btn.pack(pady=3, fill="x")
            
            if self.language.is_rtl():
                set_widget_rtl(btn)
            else:
                set_widget_ltr(btn)
        
        return sidebar
    
    def create_status_bar(self):
        """ایجاد نوار وضعیت با پشتیبانی RTL/LTR"""
        status_bar = ctk.CTkFrame(self.main_container, height=25, corner_radius=8)
        
        # وضعیت اتصال
        status_text = f"✅ {self.language.get_text('status_ready')}"
        if self.language.is_rtl():
            status_text = reshape_text(status_text)
            
        status_label = ctk.CTkLabel(
            status_bar,
            text=status_text,
            font=ctk.CTkFont(size=self.font_size - 2)
        )
        
        # اطلاعات پایگاه داده
        db_text = self.language.get_text('db_status')
        if self.language.is_rtl():
            db_text = reshape_text(db_text)
            
        db_info = ctk.CTkLabel(
            status_bar,
            text=db_text,
            font=ctk.CTkFont(size=self.font_size - 2)
        )
        
        # چیدمان بر اساس زبان
        if self.language.is_rtl():
            status_label.pack(side="right", padx=8)
            db_info.pack(side="left", padx=8)
            set_widget_rtl(status_label)
            set_widget_rtl(db_info)
        else:
            status_label.pack(side="left", padx=8)
            db_info.pack(side="right", padx=8)
            set_widget_ltr(status_label)
            set_widget_ltr(db_info)
        
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
                print(f"Error loading module {name}: {e}")
                self.modules[name] = self.create_fallback_module(name)
        
        self.switch_module(self.current_module_name)
    
    def create_fallback_module(self, name):
        """ایجاد ماژول جایگزین در صورت خطا"""
        fallback = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        if name == "notes":
            label_text = self.language.get_text('notes_development')
        else:
            label_text = self.language.get_text('module_development').format(name)
            
        if self.language.is_rtl():
            label_text = reshape_text(label_text)
        
        label = ctk.CTkLabel(
            fallback,
            text=label_text,
            font=ctk.CTkFont(size=16)
        )
        label.pack(expand=True)
        
        if self.language.is_rtl():
            set_widget_rtl(label)
        else:
            set_widget_ltr(label)
        
        return fallback
    
    def switch_module(self, module_name):
        """تعویض ماژول فعال"""
        self.current_module_name = module_name
        
        if self.current_module:
            self.current_module.pack_forget()
        
        if module_name in self.modules:
            self.current_module = self.modules[module_name]
            self.current_module.pack(fill="both", expand=True)
            self.event_bus.publish("module_changed", {"module": module_name})
    
    def refresh_ui(self):
        """تازه‌سازی رابط کاربری"""
        # ذخیره ماژول فعلی
        current_module_name = self.current_module_name
        
        # پاک کردن ویجت‌های موجود
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # ساخت مجدد رابط کاربری
        self.setup_ui()
        
        # بارگذاری مجدد ماژول‌ها
        self.load_modules()
        
        # بازگرداندن به ماژول قبلی
        self.switch_module(current_module_name)
    
    def setup_event_listeners(self):
        """تنظیم شنوندگان رویداد"""
        self.event_bus.subscribe("theme_changed", self.on_theme_changed)
        self.event_bus.subscribe("module_changed", self.on_module_changed)
        self.event_bus.subscribe("font_size_changed", self.on_font_size_changed)
        self.event_bus.subscribe("sidebar_width_changed", self.on_sidebar_width_changed)
        self.event_bus.subscribe("language_changed", self.on_language_changed)
    
    def on_theme_changed(self, data):
        """واکنش به تغییر تم"""
        self.theme_mode = data["theme"]
        ctk.set_appearance_mode(self.theme_mode)
        self.config.set("theme_mode", self.theme_mode)
    
    def on_module_changed(self, data):
        """واکنش به تغییر ماژول"""
        print(f"Module changed to: {data['module']}")
    
    def on_font_size_changed(self, data):
        """واکنش به تغییر اندازه فونت"""
        self.font_size = data["size"]
        self.config.set("font_size", self.font_size)
        self.refresh_ui()
    
    def on_sidebar_width_changed(self, data):
        """واکنش به تغییر عرض سایدبار"""
        self.sidebar_width = data["width"]
        self.config.set("sidebar_width", self.sidebar_width)
        self.refresh_ui()
    
    def on_language_changed(self, data):
        """واکنش به تغییر زبان"""
        self.language.set_language(data["language"])
        self.config.set("language", data["language"])
        self.refresh_ui()