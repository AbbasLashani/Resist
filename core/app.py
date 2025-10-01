import customtkinter as ctk
from .database import Database
from .config import Config
from .event_bus import EventBus
from .theme_manager import ThemeManager
from .language_manager import LanguageManager
from .rtl_support import reshape_text, set_widget_rtl, set_widget_ltr
from .font_manager import FontManager
import importlib
import os

class ResearchAssistantApp(ctk.CTkFrame):
    def __init__(self, parent, settings=None):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.config = Config()
        self.db = Database(self.config)
        self.event_bus = EventBus()
        self.theme = ThemeManager()
        
        # ایجاد language_manager - و حفظ compatibility با ماژول‌های موجود
        self.language_manager = LanguageManager(self.config)
        self.language = self.language_manager  # برای compatibility با ماژول‌های قدیمی
        
        self.font_manager = FontManager(self.config)
        
        # استفاده از تنظیمات ارسال شده یا بارگذاری از config
        self.settings = settings if settings else {}
        
        # تنظیمات پیش‌فرض
        self.font_size = self.settings.get("font_size", self.config.get("font_size", 14))
        self.theme_mode = self.settings.get("theme_mode", self.config.get("theme_mode", "System"))
        self.sidebar_width = self.settings.get("sidebar_width", self.config.get("sidebar_width", 200))
        self.language_code = self.settings.get("language", self.config.get("language", "fa"))
        
        # دیباگ: چک کردن مقادیر زبان
        print(f"🔍 دیباگ زبان:")
        print(f"   - زبان از settings: {self.settings.get('language', 'Not found')}")
        print(f"   - زبان از config: {self.config.get('language', 'Not found')}")
        print(f"   - زبان نهایی: {self.language_code}")
        
        # تنظیم زبان
        self.language_manager.set_language(self.language_code)
        
        # دیباگ بعد از تنظیم زبان
        print(f"   - زبان تنظیم شده: {self.language_manager.current_language}")
        print(f"   - آیا RTL است: {self.language_manager.is_rtl()}")
        print(f"   - متن تست: {self.language_manager.get_text('app_title')}")
        
        self.current_module = None
        self.modules = {}
        self.current_module_name = "dashboard"
        
        self.setup_ui()
        self.load_modules()
        self.setup_event_listeners()
        
        # اعمال تم اولیه
        ctk.set_appearance_mode(self.theme_mode)
        
    def setup_ui(self):
        """ایجاد رابط کاربری اصلی با پشتیبانی RTL/LTR"""
        print(f"🔧 ایجاد UI - زبان: {self.language_code}, RTL: {self.language_manager.is_rtl()}")
        
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # ایجاد فریم اصلی برای محتوا و سایدبار
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # تنظیم grid برای فریم اصلی
        self.main_container.grid_rowconfigure(0, weight=1)
        
        if self.language_manager.is_rtl():
            print("   - استفاده از چیدمان RTL (فارسی)")
            self.main_container.grid_columnconfigure(0, weight=1)  # محتوا
            self.main_container.grid_columnconfigure(1, weight=0)  # سایدبار
        else:
            print("   - استفاده از چیدمان LTR (انگلیسی)")
            self.main_container.grid_columnconfigure(0, weight=0)  # سایدبار
            self.main_container.grid_columnconfigure(1, weight=1)  # محتوا
        
        # ایجاد ناحیه محتوا
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # ایجاد نوار کناری
        self.sidebar = self.create_sidebar()
        
        # چیدمان بر اساس زبان
        if self.language_manager.is_rtl():
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
        print(f"   - ایجاد سایدبار - RTL: {self.language_manager.is_rtl()}")
        
        sidebar = ctk.CTkFrame(self.main_container, width=self.sidebar_width, corner_radius=10)
        sidebar.grid_propagate(False)
        
        # ایجاد فریم برای هدر برای کنترل بهتر
        header_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=50)
        header_frame.pack(pady=(10, 5), padx=10, fill="x")
        header_frame.pack_propagate(False)
        
        # هدر نوار کناری
        header_text = f"📚 {self.language_manager.get_text('app_title')}"
        if self.language_manager.is_rtl():
            header_text = self.language_manager.reshape_text(header_text)
            
        header = ctk.CTkLabel(
            header_frame,
            text=header_text,
            font=self.font_manager.get_font(16, "bold"),
            height=40
        )
        
        # موقعیت‌گذاری بر اساس زبان
        if self.language_manager.is_rtl():
            header.pack(side="right", padx=10, fill="x", expand=True)
            header.configure(anchor="e", justify="right")
            self.language_manager.set_widget_rtl(header)
        else:
            header.pack(side="left", padx=10, fill="x", expand=True)
            header.configure(anchor="w", justify="left")
            self.language_manager.set_widget_ltr(header)
        
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
            # ایجاد یک تابع برای مدیریت hover و کلیک
            def create_menu_item(icon=icon, module_name=module_name):
                # ایجاد فریم اصلی برای آیتم منو
                menu_item = ctk.CTkFrame(
                    menu_frame, 
                    height=35, 
                    corner_radius=8,
                    fg_color=("#F0F0F0", "#2B2B2B")
                )
                menu_item.pack(pady=3, fill="x")
                menu_item.pack_propagate(False)
                
                # ایجاد فریم داخلی برای محتوا
                content_frame = ctk.CTkFrame(menu_item, fg_color="transparent")
                content_frame.pack(fill="both", expand=True, padx=15)
                
                # متن ماژول
                btn_text = self.language_manager.get_text(module_name)
                if self.language_manager.is_rtl():
                    btn_text = self.language_manager.reshape_text(btn_text)
                
                print(f"     * {module_name}: {btn_text}")
                
                # لیبل آیکون
                icon_label = ctk.CTkLabel(
                    content_frame,
                    text=icon,
                    font=self.font_manager.get_font(self.font_size),
                    text_color=("#000000", "#FFFFFF"),
                    width=25
                )
                
                # لیبل متن
                text_label = ctk.CTkLabel(
                    content_frame,
                    text=btn_text,
                    font=self.font_manager.get_font(self.font_size - 1),
                    text_color=("#000000", "#FFFFFF")
                )
                
                # چیدمان بر اساس RTL/LTR
                if self.language_manager.is_rtl():
                    # برای فارسی: متن سپس آیکون
                    text_label.pack(side="right", fill="y", expand=True)
                    icon_label.pack(side="right", fill="y")
                    text_label.configure(anchor="e")
                    icon_label.configure(anchor="e")
                    self.language_manager.set_widget_rtl(text_label)
                    self.language_manager.set_widget_rtl(icon_label)
                else:
                    # برای انگلیسی: آیکون سپس متن
                    icon_label.pack(side="left", fill="y")
                    text_label.pack(side="left", fill="y", expand=True, padx=(5, 0))
                    text_label.configure(anchor="w")
                    icon_label.configure(anchor="w")
                    self.language_manager.set_widget_ltr(text_label)
                    self.language_manager.set_widget_ltr(icon_label)
                
                # مدیریت hover effects
                def on_enter(e):
                    menu_item.configure(fg_color=("#E0E0E0", "#3C3C3C"))
                    content_frame.configure(fg_color=("#E0E0E0", "#3C3C3C"))
                
                def on_leave(e):
                    menu_item.configure(fg_color=("#F0F0F0", "#2B2B2B"))
                    content_frame.configure(fg_color="transparent")
                
                def on_click(e):
                    self.switch_module(module_name)
                
                # bind events به کل فریم‌ها
                for widget in [menu_item, content_frame, icon_label, text_label]:
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)
                    widget.bind("<Button-1>", on_click)
                    # فعال کردن cursor pointer
                    widget.configure(cursor="hand2")
                
                return menu_item
            
            create_menu_item()
        
        return sidebar
    
    def create_status_bar(self):
        """ایجاد نوار وضعیت با پشتیبانی RTL/LTR"""
        status_bar = ctk.CTkFrame(self.main_container, height=25, corner_radius=8)
        
        # وضعیت اتصال
        status_text = f"✅ {self.language_manager.get_text('status_ready')}"
        if self.language_manager.is_rtl():
            status_text = self.language_manager.reshape_text(status_text)
            
        status_label = ctk.CTkLabel(
            status_bar,
            text=status_text,
            font=self.font_manager.get_font(self.font_size - 2)
        )
        
        # اطلاعات پایگاه داده
        db_text = self.language_manager.get_text('db_status')
        if self.language_manager.is_rtl():
            db_text = self.language_manager.reshape_text(db_text)
            
        db_info = ctk.CTkLabel(
            status_bar,
            text=db_text,
            font=self.font_manager.get_font(self.font_size - 2)
        )
        
        # چیدمان بر اساس زبان
        if self.language_manager.is_rtl():
            status_label.pack(side="right", padx=8)
            db_info.pack(side="left", padx=8)
            self.language_manager.set_widget_rtl(status_label)
            self.language_manager.set_widget_rtl(db_info)
        else:
            status_label.pack(side="left", padx=8)
            db_info.pack(side="right", padx=8)
            self.language_manager.set_widget_ltr(status_label)
            self.language_manager.set_widget_ltr(db_info)
        
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
                print(f"🔍 در حال بارگذاری ماژول: {name}")
                
                if name == "research":
                    from modules.research.research_module import ResearchModule
                    self.modules[name] = ResearchModule(self.content_frame, self, self.config)
                    print(f"✅ ماژول {name} بارگذاری شد")
                    
                elif name == "writer":
                    from modules.writer.writer_module import WriterModule
                    self.modules[name] = WriterModule(self.content_frame, self, self.config)
                    print(f"✅ ماژول {name} بارگذاری شد")
                    
                elif name == "settings":
                    # ماژول تنظیمات با پارامترهای اضافی
                    try:
                        from modules.settings.settings_module import SettingsModule
                        self.modules[name] = SettingsModule(self.content_frame, self, self.config, self.settings)
                        print(f"✅ ماژول {name} بارگذاری شد")
                    except Exception as e:
                        print(f"❌ خطا در بارگذاری ماژول {name}: {e}")
                        import traceback
                        traceback.print_exc()
                        # ایجاد ماژول ساده برای تنظیمات
                        self.modules[name] = self.create_settings_fallback()
                        
                elif name == "dashboard":
                    # ماژول داشبورد - import مستقیم
                    try:
                        from modules.dashboard.dashboard_module import DashboardModule
                        self.modules[name] = DashboardModule(self.content_frame, self, self.config)
                        print(f"✅ ماژول {name} بارگذاری شد")
                    except Exception as e:
                        print(f"❌ خطا در بارگذاری ماژول {name}: {e}")
                        import traceback
                        traceback.print_exc()
                        self.modules[name] = self.create_fallback_module(name)
                        
                else:
                    # برای ماژول‌های دیگر از روش معمول استفاده می‌کنیم
                    try:
                        module = importlib.import_module(path)
                        module_class = getattr(module, f"{name.capitalize()}Module")
                        self.modules[name] = module_class(self.content_frame, self, self.config)
                        print(f"✅ ماژول {name} بارگذاری شد")
                    except Exception as e:
                        print(f"❌ خطا در بارگذاری ماژول {name}: {e}")
                        import traceback
                        traceback.print_exc()
                        self.modules[name] = self.create_fallback_module(name)
                        
            except Exception as e:
                print(f"❌ خطای کلی در بارگذاری ماژول {name}: {e}")
                import traceback
                traceback.print_exc()
                self.modules[name] = self.create_fallback_module(name)
        
        # نمایش ماژول‌های بارگذاری شده
        print(f"📦 ماژول‌های بارگذاری شده: {list(self.modules.keys())}")
        
        # بررسی اینکه هر ماژول چه نوعی است
        for name, module in self.modules.items():
            module_type = type(module).__name__
            print(f"   - {name}: {module_type}")
        
        self.switch_module(self.current_module_name)
    
    def create_settings_fallback(self):
        """ایجاد ماژول تنظیمات جایگزین"""
        fallback = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # عنوان
        title_text = self.language_manager.get_text('settings_title')
        if self.language_manager.is_rtl():
            title_text = self.language_manager.reshape_text(title_text)
            
        title = ctk.CTkLabel(
            fallback,
            text=title_text,
            font=self.font_manager.get_font(20, "bold")
        )
        title.pack(pady=20)
        
        # پیام خطا
        error_text = "ماژول تنظیمات در حال توسعه است\nبه زودی در دسترس خواهد شد"
        if self.language_manager.is_rtl():
            error_text = self.language_manager.reshape_text(error_text)
            
        error_label = ctk.CTkLabel(
            fallback,
            text=error_text,
            font=self.font_manager.get_font(16),
            text_color=("#2E2E2E", "#E0E0E0")
        )
        error_label.pack(pady=10)
        
        # آیکون
        icon_label = ctk.CTkLabel(
            fallback,
            text="⚙️",
            font=self.font_manager.get_font(48),
            text_color=("#FF9800", "#FFB74D")
        )
        icon_label.pack(pady=20)
        
        # دکمه بازگشت
        back_button = ctk.CTkButton(
            fallback,
            text=self.language_manager.get_text('back_to_dashboard'),
            command=lambda: self.switch_module("dashboard"),
            width=200,
            height=40
        )
        back_button.pack(pady=20)
        
        # اعمال ترازبندی RTL/LTR
        if self.language_manager.is_rtl():
            self.language_manager.set_widget_rtl(title)
            self.language_manager.set_widget_rtl(error_label)
            self.language_manager.set_widget_rtl(icon_label)
            self.language_manager.set_widget_rtl(back_button)
        else:
            self.language_manager.set_widget_ltr(title)
            self.language_manager.set_widget_ltr(error_label)
            self.language_manager.set_widget_ltr(icon_label)
            self.language_manager.set_widget_ltr(back_button)
        
        return fallback
    
    def create_fallback_module(self, name):
        """ایجاد ماژول جایگزین در صورت خطا"""
        fallback = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # تعیین متن بر اساس نوع ماژول
        if name == "notes":
            label_text = self.language_manager.get_text('notes_development')
        else:
            label_text = self.language_manager.get_text('module_development').format(
                self.language_manager.get_text(name)
            )
        
        # تغییر شکل متن برای RTL اگر لازم باشد
        if self.language_manager.is_rtl():
            label_text = self.language_manager.reshape_text(label_text)
        
        # ایجاد برچسب
        label = ctk.CTkLabel(
            fallback,
            text=label_text,
            font=self.font_manager.get_font(16),
            text_color=("#2E2E2E", "#E0E0E0")
        )
        label.pack(expand=True, padx=20, pady=20)
        
        # اضافه کردن آیکون برای زیبایی
        icon_label = ctk.CTkLabel(
            fallback,
            text="🚧" if name != "notes" else "📝",
            font=self.font_manager.get_font(48),
            text_color=("#FF9800", "#FFB74D")
        )
        icon_label.pack(pady=(0, 20))
        
        # اضافه کردن دکمه برای بازگشت یا اقدام دیگر
        back_button = ctk.CTkButton(
            fallback,
            text=self.language_manager.get_text('back_to_dashboard'),
            command=lambda: self.switch_module("dashboard"),
            width=200,
            height=40,
            corner_radius=8,
            fg_color=("#2196F3", "#1976D2"),
            hover_color=("#1976D2", "#1565C0")
        )
        back_button.pack(pady=10)
        
        # اعمال ترازبندی RTL/LTR
        if self.language_manager.is_rtl():
            self.language_manager.set_widget_rtl(label)
            self.language_manager.set_widget_rtl(icon_label)
            self.language_manager.set_widget_rtl(back_button)
        else:
            self.language_manager.set_widget_ltr(label)
            self.language_manager.set_widget_ltr(icon_label)
            self.language_manager.set_widget_ltr(back_button)
        
        # اضافه کردن اطلاعات دیباگ برای توسعه دهندگان
        if self.config.get("debug_mode", False):
            debug_label = ctk.CTkLabel(
                fallback,
                text=f"Module: {name}\nError: Failed to load module",
                font=self.font_manager.get_font(12),
                text_color=("#666666", "#AAAAAA")
            )
            debug_label.pack(side="bottom", pady=10)
            
            if self.language_manager.is_rtl():
                debug_label.configure(anchor="e")
            else:
                debug_label.configure(anchor="w")
        
        return fallback
    
    def switch_module(self, module_name):
        """تعویض ماژول فعال"""
        print(f"🔄 تعویض ماژول به: {module_name}")
        self.current_module_name = module_name
        
        if self.current_module:
            self.current_module.pack_forget()
        
        if module_name in self.modules:
            self.current_module = self.modules[module_name]
            self.current_module.pack(fill="both", expand=True)
            self.event_bus.publish("module_changed", {"module": module_name})
            print(f"✅ ماژول {module_name} نمایش داده شد")
        else:
            print(f"❌ ماژول {module_name} یافت نشد")
    
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
        self.event_bus.subscribe("settings_changed", self.on_settings_changed)
        self.event_bus.subscribe("font_changed", self.on_font_changed)
    
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
        self.language_manager.set_language(data["language"])
        self.config.set("language", data["language"])
        self.refresh_ui()
    
    def on_font_changed(self, data):
        """واکنش به تغییر فونت"""
        if "font_family" in data:
            self.font_manager.set_font_family(data["font_family"])
        
        if "font_size" in data:
            self.font_manager.set_font_size(data["font_size"])
            self.font_size = data["font_size"]
        
        # به روزرسانی فونت‌ها در کل UI
        self.update_all_fonts()
        
        # انتشار رویداد برای ماژول‌ها
        self.event_bus.publish("font_changed", data)
    
    def on_settings_changed(self, data):
        """واکنش به تغییر تنظیمات"""
        # به روزرسانی تنظیمات
        self.settings.update(data)
        
        # اعمال تغییرات
        if "theme_mode" in data:
            self.on_theme_changed({"theme": data["theme_mode"]})
        
        if "font_size" in data:
            self.on_font_size_changed({"size": data["font_size"]})
        
        if "sidebar_width" in data:
            self.on_sidebar_width_changed({"width": data["sidebar_width"]})
        
        if "language" in data:
            self.on_language_changed({"language": data["language"]})
        
        if "font_family" in data or "font_size" in data:
            self.on_font_changed(data)
        
        # ذخیره تنظیمات در config
        for key, value in data.items():
            self.config.set(key, value)
        
        # انتشار رویداد برای سایر ماژول‌ها
        self.event_bus.publish("settings_updated", data)
    
    def update_all_fonts(self):
        """به روزرسانی فونت تمام ویجت‌ها در برنامه"""
        try:
            # به روزرسانی فونت در ویجت‌های اصلی
            self.apply_font_to_widgets(self)
            
            # به روزرسانی فونت در سایدبار
            self.apply_font_to_widgets(self.sidebar)
            
            # به روزرسانی فونت در status bar
            self.apply_font_to_widgets(self.status_bar)
            
            # به روزرسانی فونت در content frame
            self.apply_font_to_widgets(self.content_frame)
            
            # به روزرسانی فونت در ماژول فعال
            if self.current_module:
                self.apply_font_to_widgets(self.current_module)
            
            print("✅ فونت‌ها در کل برنامه به روز شدند")
            
        except Exception as e:
            print(f"❌ خطا در به روزرسانی فونت‌ها: {e}")
    
    def apply_font_to_widgets(self, parent_widget):
        """اعمال فونت به تمام ویجت‌های فرزند"""
        try:
            for widget in parent_widget.winfo_children():
                # اگر ویجت دارای ویژگی font است
                if hasattr(widget, 'configure'):
                    try:
                        # سعی کن فونت جدید اعمال کنی
                        new_font = self.font_manager.get_font()
                        widget.configure(font=new_font)
                    except:
                        # اگر خطا داد، ادامه بده
                        pass
                
                # اعمال بازگشتی به فرزندان
                if widget.winfo_children():
                    self.apply_font_to_widgets(widget)
                    
        except Exception as e:
            print(f"⚠️ خطا در اعمال فونت به ویجت: {e}")
    
    def update_ui_with_settings(self, settings):
        """به روزرسانی UI با تنظیمات جدید"""
        self.settings = settings
        
        # اعمال تغییرات زبان
        if "language" in settings:
            self.language_manager.set_language(settings["language"])
            self.update_ui_texts()
        
        # اعمال تغییرات عرض نوار کناری
        if "sidebar_width" in settings:
            self.sidebar.configure(width=settings["sidebar_width"])
        
        # اعمال تغییرات فونت
        if "font_size" in settings:
            self.font_manager.set_font_size(settings["font_size"])
            self.font_size = settings["font_size"]
            self.update_all_fonts()
        
        if "font_family" in settings:
            self.font_manager.set_font_family(settings["font_family"])
            self.update_all_fonts()
        
        # اعمال تغییرات تم
        if "theme_mode" in settings:
            ctk.set_appearance_mode(settings["theme_mode"])
    
    def update_font_size(self, size):
        """به روزرسانی اندازه فونت"""
        self.font_manager.set_font_size(size)
        self.update_all_fonts()
    
    def update_ui_texts(self):
        """به روزرسانی متون UI بر اساس زبان انتخاب شده"""
        # این متد می‌تواند برای به روزرسانی متون استاتیک استفاده شود
        pass