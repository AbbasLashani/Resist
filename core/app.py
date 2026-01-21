import customtkinter as ctk
from .database import Database
from .config import Config
from .event_bus import EventBus
from .theme_manager import ThemeManager
from .language_manager import LanguageManager
from .font_manager import FontManager
import os
import traceback
from typing import Dict, Any, Optional
import logging

class ResearchAssistantApp(ctk.CTkFrame):
    def __init__(self, parent, settings: Optional[Dict[str, Any]] = None):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        
        # Setup logging
        self._setup_logging()
        
        # Initialize core components
        self._initialize_core_components(settings)
        
        # Setup UI and modules
        self._setup_application()

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_core_components(self, settings: Optional[Dict[str, Any]]):
        """Initialize core application components"""
        try:
            self.config = Config()
            self.db = Database(self.config)
            self.event_bus = EventBus()
            self.theme = ThemeManager()
            
            # Language management
            self.language_manager = LanguageManager(self.config)
            self.language = self.language_manager  # For backward compatibility
            
            # Font management
            self.font_manager = FontManager(self.config)
            
            # Application settings
            self.settings = settings or {}
            self._load_application_settings()
            
            # Module management
            self.current_module = None
            self.modules = {}
            self.current_module_name = "dashboard"
            
            self.logger.info("✅ کامپوننت‌های اصلی برنامه با موفقیت راه‌اندازی شدند")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در راه‌اندازی کامپوننت‌های اصلی: {e}")
            raise

    def _load_application_settings(self):
        """Load and configure application settings"""
        try:
            self.font_size = self.settings.get("font_size", self.config.get("font_size", 14))
            self.theme_mode = self.settings.get("theme_mode", self.config.get("theme_mode", "System"))
            self.sidebar_width = self.settings.get("sidebar_width", self.config.get("sidebar_width", 200))
            self.language_code = self.settings.get("language", self.config.get("language", "fa"))
            
            # Set language
            self.language_manager.set_language(self.language_code)
            
            self.logger.info(f"✅ تنظیمات بارگذاری شد: زبان={self.language_code}, RTL={self.language_manager.is_rtl()}")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری تنظیمات: {e}")
            # Use default values
            self.font_size = 14
            self.theme_mode = "System"
            self.sidebar_width = 200
            self.language_code = "fa"

    def _setup_application(self):
        """Setup the main application"""
        try:
            self.setup_ui()
            self.load_modules()
            self.setup_event_listeners()
            
            # Apply initial theme
            ctk.set_appearance_mode(self.theme_mode)
            
            self.logger.info("✅ برنامه با موفقیت راه‌اندازی شد")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در راه‌اندازی برنامه: {e}")
            traceback.print_exc()

    def setup_ui(self):
        """Create main UI with RTL/LTR support"""
        self.logger.info(f"🔄 ایجاد رابط کاربری - زبان: {self.language_code}, RTL: {self.language_manager.is_rtl()}")
        
        # Clear existing widgets
        self._clear_existing_widgets()
        
        # Configure main grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup grid layout
        self._setup_grid_layout()
        
        # Create content area and sidebar
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.sidebar = self._create_sidebar()
        
        # Layout based on language direction
        self._apply_layout_direction()
        
        # Create status bar
        self.status_bar = self._create_status_bar()
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(10, 0))
        
        self.logger.info("✅ رابط کاربری با موفقیت ایجاد شد")

    def _clear_existing_widgets(self):
        """Clear all existing widgets"""
        for widget in self.winfo_children():
            try:
                if widget.winfo_exists():
                    widget.destroy()
            except Exception as e:
                self.logger.debug(f"خطا در حذف ویجت: {e}")

    def _setup_grid_layout(self):
        """Setup grid layout based on language direction"""
        self.main_container.grid_rowconfigure(0, weight=1)
        
        if self.language_manager.is_rtl():
            # RTL layout: content on left, sidebar on right
            self.main_container.grid_columnconfigure(0, weight=1)  # Content
            self.main_container.grid_columnconfigure(1, weight=0)  # Sidebar
            self.logger.info("   📐 استفاده از چیدمان RTL (فارسی)")
        else:
            # LTR layout: sidebar on left, content on right
            self.main_container.grid_columnconfigure(0, weight=0)  # Sidebar
            self.main_container.grid_columnconfigure(1, weight=1)  # Content
            self.logger.info("   📐 استفاده از چیدمان LTR (انگلیسی)")

    def _apply_layout_direction(self):
        """Apply layout direction based on language"""
        if self.language_manager.is_rtl():
            # RTL: sidebar on right, content on left
            self.sidebar.grid(row=0, column=1, sticky="ns", padx=(10, 0), pady=0)
            self.content_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        else:
            # LTR: sidebar on left, content on right
            self.sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 10), pady=0)
            self.content_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

    def _create_sidebar(self):
        """Create sidebar with proper RTL/LTR support"""
        self.logger.info(f"   🎨 ایجاد سایدبار - RTL: {self.language_manager.is_rtl()}")
        
        sidebar = ctk.CTkFrame(self.main_container, width=self.sidebar_width, corner_radius=10)
        sidebar.grid_propagate(False)
        
        # Create header
        self._create_sidebar_header(sidebar)
        
        # Create menu items
        self._create_sidebar_menu(sidebar)
        
        return sidebar

    def _create_sidebar_header(self, sidebar):
        """Create sidebar header"""
        header_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=50)
        header_frame.pack(pady=(10, 5), padx=10, fill="x")
        header_frame.pack_propagate(False)
        
        # Header text
        header_text = "📚 دستیار تحقیقاتی"
        reshaped_text = self.language_manager.reshape_text(header_text)
        
        self.logger.info(f"   📝 متن هدر: '{header_text}' -> '{reshaped_text}'")
        
        header = ctk.CTkLabel(
            header_frame,
            text=reshaped_text,
            font=self.font_manager.get_font(16, "bold"),
            height=40,
            anchor="e" if self.language_manager.is_rtl() else "w"
        )
        
        # Position based on language direction
        if self.language_manager.is_rtl():
            header.pack(side="right", padx=10, fill="x", expand=True)
            header.configure(anchor="e", justify="right")
        else:
            header.pack(side="left", padx=10, fill="x", expand=True)
            header.configure(anchor="w", justify="left")
        
        return header

    def _create_sidebar_menu(self, sidebar):
        """Create sidebar menu items"""
        modules = [
            ("🏠", "dashboard", "داشبورد"),
            ("📄", "papers", "مقالات"),
            ("📋", "datasheets", "دیتاشیت‌ها"),
            ("📅", "planner", "برنامه‌ریزی"),
            ("📝", "notes", "یادداشت‌ها"),
            ("🔍", "research", "تحقیق"),
            ("✏️", "writer", "نوشتن"),
            ("⚙️", "settings", "تنظیمات")
        ]
        
        menu_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        menu_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        for icon, module_name, persian_name in modules:
            self._create_menu_item(menu_frame, icon, module_name, persian_name)

    def _create_menu_item(self, parent, icon: str, module_name: str, persian_name: str):
        """Create a single menu item"""
        # Create menu item frame
        menu_item = ctk.CTkFrame(
            parent, 
            height=35, 
            corner_radius=8,
            fg_color=("#F0F0F0", "#2B2B2B")
        )
        menu_item.pack(pady=3, fill="x")
        menu_item.pack_propagate(False)
        
        # Create content frame
        content_frame = ctk.CTkFrame(menu_item, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15)
        
        # استفاده از متن فارسی مستقیم به جای ترجمه
        btn_text = persian_name
        reshaped_text = self.language_manager.reshape_text(btn_text)
        
        self.logger.info(f"     📍 {module_name}: '{btn_text}' -> '{reshaped_text}'")
        
        # Create icon and text labels
        icon_label, text_label = self._create_menu_labels(content_frame, icon, reshaped_text)
        
        # Apply layout based on language direction
        self._layout_menu_item(content_frame, icon_label, text_label)
        
        # Apply hover and click effects
        self._apply_menu_item_effects(menu_item, content_frame, icon_label, text_label, module_name)

    def _create_menu_labels(self, parent, icon: str, text: str):
        """Create icon and text labels for menu item"""
        icon_label = ctk.CTkLabel(
            parent,
            text=icon,
            font=self.font_manager.get_font(self.font_size),
            text_color=("#000000", "#FFFFFF"),
            width=25
        )
        
        text_label = ctk.CTkLabel(
            parent,
            text=text,
            font=self.font_manager.get_font(self.font_size - 1),
            text_color=("#000000", "#FFFFFF"),
            anchor="e" if self.language_manager.is_rtl() else "w"
        )
        
        return icon_label, text_label

    def _layout_menu_item(self, parent, icon_label, text_label):
        """Layout menu item based on language direction"""
        if self.language_manager.is_rtl():
            # RTL: text then icon
            text_label.pack(side="right", fill="y", expand=True)
            icon_label.pack(side="right", fill="y")
            text_label.configure(anchor="e", justify="right")
            icon_label.configure(anchor="e")
        else:
            # LTR: icon then text
            icon_label.pack(side="left", fill="y")
            text_label.pack(side="left", fill="y", expand=True, padx=(5, 0))
            text_label.configure(anchor="w", justify="left")
            icon_label.configure(anchor="w")

    def _apply_menu_item_effects(self, menu_item, content_frame, icon_label, text_label, module_name: str):
        """Apply hover and click effects to menu item"""
        def on_enter(e):
            if menu_item.winfo_exists():
                menu_item.configure(fg_color=("#E0E0E0", "#3C3C3C"))
                content_frame.configure(fg_color=("#E0E0E0", "#3C3C3C"))
        
        def on_leave(e):
            if menu_item.winfo_exists():
                menu_item.configure(fg_color=("#F0F0F0", "#2B2B2B"))
                content_frame.configure(fg_color="transparent")
        
        def on_click(e):
            if menu_item.winfo_exists():
                self.switch_module(module_name)
        
        # Bind events to all widgets
        for widget in [menu_item, content_frame, icon_label, text_label]:
            try:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)
                widget.configure(cursor="hand2")
            except Exception as e:
                self.logger.debug(f"خطا در bind کردن رویدادها: {e}")

    def _create_status_bar(self):
        """Create status bar with RTL/LTR support"""
        status_bar = ctk.CTkFrame(self.main_container, height=25, corner_radius=8)
        
        # Status text
        status_text = "✅ آماده به کار"
        status_reshaped = self.language_manager.reshape_text(status_text)
        
        status_label = ctk.CTkLabel(
            status_bar,
            text=status_reshaped,
            font=self.font_manager.get_font(self.font_size - 2),
            anchor="e" if self.language_manager.is_rtl() else "w"
        )
        
        # Database info
        db_text = "پایگاه داده: فعال"
        db_reshaped = self.language_manager.reshape_text(db_text)
        
        db_info = ctk.CTkLabel(
            status_bar,
            text=db_reshaped,
            font=self.font_manager.get_font(self.font_size - 2),
            anchor="e" if self.language_manager.is_rtl() else "w"
        )
        
        # Layout based on language direction
        if self.language_manager.is_rtl():
            status_label.pack(side="right", padx=8)
            db_info.pack(side="left", padx=8)
            status_label.configure(anchor="e", justify="right")
            db_info.configure(anchor="e", justify="right")
        else:
            status_label.pack(side="left", padx=8)
            db_info.pack(side="right", padx=8)
            status_label.configure(anchor="w", justify="left")
            db_info.configure(anchor="w", justify="left")
        
        return status_bar

    def load_modules(self):
        """Load all application modules"""
        self.logger.info("🔄 در حال بارگذاری ماژول‌ها...")
        
        module_configs = {
            "dashboard": ("modules.dashboard.dashboard_module", "DashboardModule"),
            "papers": ("modules.papers.papers_module", "PapersModule"),
            "planner": ("modules.planner.planner_module", "PlanningModule"),
            "notes": ("modules.notes.notes_module", "NotesModule"),
            "research": ("modules.research.research_module", "ResearchModule"),
            "writer": ("modules.writer.writer_module", "WriterModule"),
            "datasheets": ("modules.datasheets.datasheets_module", "DatasheetsModule"),
            "settings": ("modules.settings.settings_module", "SettingsModule")
        }
        
        for name, (path, class_name) in module_configs.items():
            self._load_single_module(name, path, class_name)
        
        # Display loaded modules
        self._display_loaded_modules()
        
        # Activate dashboard module
        self.switch_module("dashboard")

    def _load_single_module(self, name: str, path: str, class_name: str):
        """Load a single module"""
        try:
            self.logger.info(f"📦 بارگذاری ماژول: {name}")
            
            if name == "dashboard":
                from modules.dashboard.dashboard_module import DashboardModule
                self.modules[name] = DashboardModule(self.content_frame, self, self.config)
                
            elif name == "papers":
                if os.path.exists("modules/papers/papers_module.py"):
                    from modules.papers.papers_module import PapersModule
                    self.modules[name] = PapersModule(self.content_frame, self, self.config)
                else:
                    raise FileNotFoundError(f"ماژول {name} یافت نشد")
                    
            elif name == "planner":
                if os.path.exists("modules/planner/planner_module.py"):
                    from modules.planner.planner_module import PlanningModule
                    self.modules[name] = PlanningModule(self.content_frame, self, self.config)
                else:
                    raise FileNotFoundError(f"ماژول {name} یافت نشد")
                    
            elif name == "notes":
                if os.path.exists("modules/notes/notes_module.py"):
                    from modules.notes.notes_module import NotesModule
                    self.modules[name] = NotesModule(self.content_frame, self, self.config)
                else:
                    raise FileNotFoundError(f"ماژول {name} یافت نشد")
                    
            elif name == "research":
                if os.path.exists("modules/research/research_module.py"):
                    from modules.research.research_module import ResearchModule
                    self.modules[name] = ResearchModule(self.content_frame, self, self.config)
                else:
                    raise FileNotFoundError(f"ماژول {name} یافت نشد")
                    
            elif name == "writer":
                if os.path.exists("modules/writer/writer_module.py"):
                    from modules.writer.writer_module import WriterModule
                    self.modules[name] = WriterModule(self.content_frame, self, self.config)
                else:
                    raise FileNotFoundError(f"ماژول {name} یافت نشد")
                    
            elif name == "datasheets":
                if os.path.exists("modules/datasheets/datasheets_module.py"):
                    from modules.datasheets.datasheets_module import DatasheetsModule
                    self.modules[name] = DatasheetsModule(self.content_frame, self, self.config)
                else:
                    raise FileNotFoundError(f"ماژول {name} یافت نشد")
                    
            elif name == "settings":
                if os.path.exists("modules/settings/settings_module.py"):
                    from modules.settings.settings_module import SettingsModule
                    self.modules[name] = SettingsModule(self.content_frame, self, self.config, self.settings)
                else:
                    raise FileNotFoundError(f"ماژول {name} یافت نشد")
                    
            else:
                # Fallback for other modules
                self.modules[name] = self.create_fallback_module(name)
                
            self.logger.info(f"✅ ماژول {name} بارگذاری شد")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری ماژول {name}: {e}")
            traceback.print_exc()
            self.modules[name] = self.create_fallback_module(name)

    def _display_loaded_modules(self):
        """Display information about loaded modules"""
        loaded_modules = list(self.modules.keys())
        self.logger.info(f"📊 ماژول‌های بارگذاری شده: {loaded_modules}")
        
        for name, module in self.modules.items():
            module_type = type(module).__name__
            self.logger.info(f"   - {name}: {module_type}")

    def create_fallback_module(self, name: str):
        """Create fallback module when original fails to load"""
        fallback = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # استفاده از متن مستقیم فارسی
        if name == "notes":
            label_text = "ماژول یادداشت‌ها در حال توسعه است"
        else:
            label_text = f"ماژول {name} در حال توسعه است"
        
        # Reshape text for RTL if needed
        reshaped_text = self.language_manager.reshape_text(label_text)
        
        # Create label
        label = ctk.CTkLabel(
            fallback,
            text=reshaped_text,
            font=self.font_manager.get_font(16),
            text_color=("#2E2E2E", "#E0E0E0"),
            anchor="e" if self.language_manager.is_rtl() else "w"
        )
        label.pack(expand=True, padx=20, pady=20)
        
        # Add icon
        icon_label = ctk.CTkLabel(
            fallback,
            text="🚧" if name != "notes" else "📝",
            font=self.font_manager.get_font(48),
            text_color=("#FF9800", "#FFB74D")
        )
        icon_label.pack(pady=(0, 20))
        
        # Add back button
        back_text = "بازگشت به داشبورد"
        reshaped_back_text = self.language_manager.reshape_text(back_text)
        
        back_button = ctk.CTkButton(
            fallback,
            text=reshaped_back_text,
            command=lambda: self.switch_module("dashboard"),
            width=200,
            height=40,
            corner_radius=8,
            fg_color=("#2196F3", "#1976D2"),
            hover_color=("#1976D2", "#1565C0")
        )
        back_button.pack(pady=10)
        
        return fallback

    def switch_module(self, module_name: str):
        """Switch to a different module"""
        self.logger.info(f"🔄 تعویض ماژول به: {module_name}")
        self.current_module_name = module_name
        
        # Hide current module
        if self.current_module and self.current_module.winfo_exists():
            try:
                self.current_module.pack_forget()
            except Exception as e:
                self.logger.debug(f"خطا در مخفی کردن ماژول فعلی: {e}")
        
        # Show new module
        if module_name in self.modules and self.modules[module_name].winfo_exists():
            self.current_module = self.modules[module_name]
            try:
                self.current_module.pack(fill="both", expand=True)
                self.event_bus.publish("module_changed", {"module": module_name})
                self.logger.info(f"✅ ماژول {module_name} نمایش داده شد")
            except Exception as e:
                self.logger.error(f"❌ خطا در نمایش ماژول {module_name}: {e}")
        else:
            self.logger.warning(f"⚠️ ماژول {module_name} یافت نشد یا وجود ندارد")

    def setup_event_listeners(self):
        """Setup event listeners"""
        events = {
            "theme_changed": self.on_theme_changed,
            "module_changed": self.on_module_changed,
            "font_size_changed": self.on_font_size_changed,
            "sidebar_width_changed": self.on_sidebar_width_changed,
            "language_changed": self.on_language_changed,
            "settings_changed": self.on_settings_changed,
            "font_changed": self.on_font_changed
        }
        
        for event, handler in events.items():
            self.event_bus.subscribe(event, handler)
        
        self.logger.info("✅ Event listeners با موفقیت تنظیم شدند")

    def on_theme_changed(self, data):
        """Handle theme change"""
        if "theme" in data:
            self.theme_mode = data["theme"]
            ctk.set_appearance_mode(self.theme_mode)
            self.config.set("theme_mode", self.theme_mode)
            self.logger.info(f"🎨 تم تغییر کرد به: {self.theme_mode}")

    def on_module_changed(self, data):
        """Handle module change"""
        module_name = data.get('module', 'unknown')
        self.logger.info(f"🔄 ماژول تغییر کرد به: {module_name}")

    def on_font_size_changed(self, data):
        """Handle font size change"""
        if "size" in data:
            self.font_size = data["size"]
            self.config.set("font_size", self.font_size)
            self.font_manager.set_font_size(self.font_size)
            self.safe_refresh_ui()
            self.logger.info(f"🔤 سایز فونت تغییر کرد به: {self.font_size}")

    def on_sidebar_width_changed(self, data):
        """Handle sidebar width change"""
        if "width" in data:
            self.sidebar_width = data["width"]
            self.config.set("sidebar_width", self.sidebar_width)
            self.safe_refresh_ui()
            self.logger.info(f"📐 عرض سایدبار تغییر کرد به: {self.sidebar_width}")

    def on_language_changed(self, data):
        """Handle language change"""
        if "language" in data:
            new_language = data["language"]
            self.language_manager.set_language(new_language)
            self.config.set("language", new_language)
            self.language_code = new_language
            self.safe_refresh_ui()
            self.logger.info(f"🌍 زبان تغییر کرد به: {new_language}")

    def on_font_changed(self, data):
        """Handle font change"""
        try:
            self.logger.info("🔤 دریافت event تغییر فونت")
            self.update_all_fonts()
        except Exception as e:
            self.logger.error(f"❌ خطا در تغییر فونت: {e}")

    def on_settings_changed(self, data):
        """Handle settings change - safe version"""
        self.logger.info(f"⚙️ دریافت تنظیمات جدید: {list(data.keys())}")
        
        # Save settings to config
        for key, value in data.items():
            self.config.set(key, value)
        
        # Apply changes with proper order and management
        needs_full_refresh = False
        
        # First check language (requires full rebuild)
        if "language" in data and data["language"] != self.language_manager.current_language:
            self.logger.info(f"🌍 تغییر زبان به: {data['language']}")
            self.language_manager.set_language(data["language"])
            self.language_code = data["language"]
            needs_full_refresh = True
        
        # Then theme
        if "theme_mode" in data:
            self.logger.info(f"🎨 تغییر تم به: {data['theme_mode']}")
            self.theme_mode = data["theme_mode"]
            ctk.set_appearance_mode(self.theme_mode)
        
        # Then sidebar
        if "sidebar_width" in data:
            self.logger.info(f"📐 تغییر عرض سایدبار به: {data['sidebar_width']}")
            self.sidebar_width = data["sidebar_width"]
            needs_full_refresh = True
        
        # Finally font
        font_changed = False
        font_data = {}
        
        if "font_size" in data:
            self.logger.info(f"🔤 تغییر سایز فونت به: {data['font_size']}")
            self.font_size = data["font_size"]
            self.font_manager.set_font_size(self.font_size)
            font_changed = True
            font_data["font_size"] = data["font_size"]
        
        if "font_family" in data:
            self.logger.info(f"🔤 تغییر فونت به: {data['font_family']}")
            self.font_manager.set_font_family(data["font_family"])
            font_changed = True
            font_data["font_family"] = data["font_family"]
        
        # If full refresh needed
        if needs_full_refresh:
            self.logger.info("🔄 بازسازی کامل UI به دلیل تغییرات اساسی")
            self.safe_refresh_ui()
        elif font_changed:
            self.logger.info("🔤 انتشار event تغییر فونت")
            # Publish font event with delay to prevent race condition
            self.after(100, lambda: self.event_bus.publish("font_changed", font_data))
        
        # Publish event for other modules
        self.after(150, lambda: self.event_bus.publish("settings_updated", data))

    def safe_refresh_ui(self):
        """Safely refresh the UI"""
        try:
            current_module_name = self.current_module_name
            
            # Pause event processing
            self.update_idletasks()
            
            # Clear existing widgets with error management
            for widget in self.main_container.winfo_children():
                try:
                    if widget.winfo_exists():
                        widget.destroy()
                except Exception as e:
                    self.logger.debug(f"خطا در حذف ویجت: {e}")
            
            # Rebuild UI
            self.setup_ui()
            
            # Reload modules
            self.load_modules()
            
            # Restore previous module
            if current_module_name in self.modules:
                self.after(200, lambda: self.switch_module(current_module_name))
            else:
                self.after(200, lambda: self.switch_module("dashboard"))
                
            self.logger.info("✅ UI با موفقیت تازه‌سازی شد")
                
        except Exception as e:
            self.logger.error(f"❌ خطا در تازه‌سازی ایمن UI: {e}")
            traceback.print_exc()

    def update_all_fonts(self):
        """Update fonts for all widgets - completely safe version"""
        try:
            self.logger.info("🔤 شروع به روزرسانی فونت‌ها...")
            
            # Safe list of main widgets
            main_widgets = []
            
            # Only collect main widgets that exist
            if self.winfo_exists():
                main_widgets.append(self)
            
            if hasattr(self, 'sidebar') and self.sidebar.winfo_exists():
                main_widgets.append(self.sidebar)
            
            if hasattr(self, 'content_frame') and self.content_frame.winfo_exists():
                main_widgets.append(self.content_frame)
            
            if hasattr(self, 'status_bar') and self.status_bar.winfo_exists():
                main_widgets.append(self.status_bar)
            
            # Update each main widget
            for widget in main_widgets:
                self.safe_apply_font_to_widget(widget)
            
            self.logger.info("✅ فونت‌ها با موفقیت به روز شدند")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در به روزرسانی فونت‌ها: {e}")

    def safe_apply_font_to_widget(self, widget):
        """Safely apply font to a widget and its children"""
        try:
            if not widget.winfo_exists():
                return
                
            # If widget has font configuration
            if hasattr(widget, 'configure'):
                try:
                    current_font = widget.cget("font") if hasattr(widget, 'cget') else None
                    if current_font:
                        new_font = self.font_manager.get_font()
                        widget.configure(font=new_font)
                except Exception:
                    pass  # Continue if font setting fails
            
            # Apply to children - with limited depth to prevent infinite loop
            try:
                children = widget.winfo_children()
                for child in children:
                    if child.winfo_exists():
                        self.safe_apply_font_to_widget(child)
            except Exception:
                pass
                
        except Exception as e:
            self.logger.debug(f"خطا در اعمال فونت به ویجت: {e}")

    def update_ui_with_settings(self, settings):
        """Update UI with new settings"""
        self.settings = settings
        
        # Apply language changes
        if "language" in settings:
            self.language_manager.set_language(settings["language"])
            self.update_ui_texts()
        
        # Apply sidebar width changes
        if "sidebar_width" in settings:
            self.sidebar.configure(width=settings["sidebar_width"])
        
        # Apply font changes
        if "font_size" in settings:
            self.font_manager.set_font_size(settings["font_size"])
            self.font_size = settings["font_size"]
            self.update_all_fonts()
        
        if "font_family" in settings:
            self.font_manager.set_font_family(settings["font_family"])
            self.update_all_fonts()
        
        # Apply theme changes
        if "theme_mode" in settings:
            ctk.set_appearance_mode(settings["theme_mode"])

    def update_font_size(self, size):
        """Update font size"""
        self.font_manager.set_font_size(size)
        self.update_all_fonts()

    def update_ui_texts(self):
        """Update UI texts based on selected language"""
        # This method can be used to update static texts
        pass

    def create_settings_fallback(self):
        """Create fallback settings module"""
        fallback = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Title
        title_text = "تنظیمات"
        reshaped_title = self.language_manager.reshape_text(title_text)
        
        title = ctk.CTkLabel(
            fallback,
            text=reshaped_title,
            font=self.font_manager.get_font(20, "bold"),
            anchor="e" if self.language_manager.is_rtl() else "w"
        )
        title.pack(pady=20)
        
        # Error message
        error_text = "ماژول تنظیمات در حال توسعه است\nبه زودی در دسترس خواهد شد"
        reshaped_error = self.language_manager.reshape_text(error_text)
        
        error_label = ctk.CTkLabel(
            fallback,
            text=reshaped_error,
            font=self.font_manager.get_font(16),
            text_color=("#2E2E2E", "#E0E0E0"),
            anchor="e" if self.language_manager.is_rtl() else "w"
        )
        error_label.pack(pady=10)
        
        # Icon
        icon_label = ctk.CTkLabel(
            fallback,
            text="⚙️",
            font=self.font_manager.get_font(48),
            text_color=("#FF9800", "#FFB74D")
        )
        icon_label.pack(pady=20)
        
        # Back button
        back_text = "بازگشت به داشبورد"
        reshaped_back = self.language_manager.reshape_text(back_text)
        
        back_button = ctk.CTkButton(
            fallback,
            text=reshaped_back,
            command=lambda: self.switch_module("dashboard"),
            width=200,
            height=40
        )
        back_button.pack(pady=20)
        
        return fallback

    def get_current_module(self):
        """Get current active module"""
        return self.current_module

    def get_module(self, module_name):
        """Get specific module by name"""
        return self.modules.get(module_name)

    def refresh_current_module(self):
        """Refresh current module"""
        if self.current_module_name and self.current_module_name in self.modules:
            self.switch_module(self.current_module_name)

    def destroy(self):
        """Cleanup before destruction"""
        try:
            self.logger.info("🧹 در حال پاک‌سازی برنامه...")
            
            # Unsubscribe from all events
            self.event_bus.clear_all()
            
            # Destroy all modules
            for name, module in self.modules.items():
                try:
                    if hasattr(module, 'destroy'):
                        module.destroy()
                    elif module.winfo_exists():
                        module.destroy()
                    self.logger.info(f"✅ ماژول {name} پاک شد")
                except Exception as e:
                    self.logger.debug(f"خطا در پاک کردن ماژول {name}: {e}")
            
            # Call parent destroy
            super().destroy()
            self.logger.info("✅ برنامه با موفقیت بسته شد")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در تخریب برنامه: {e}")


def create_app(parent, settings=None):
    """Create and return the main application instance"""
    try:
        app = ResearchAssistantApp(parent, settings)
        return app
    except Exception as e:
        logging.error(f"❌ خطا در ایجاد برنامه: {e}")
        traceback.print_exc()
        return None