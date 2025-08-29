# research_assistant/core/app.py
import tkinter as tk
from tkinter import ttk
import importlib
from pathlib import Path
import logging

from .config import Config
from .event_bus import EventBus
from .database import Database

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("دستیار تحقیقات هوشمند")
        self.root.geometry("1200x700")
        
        # Initialize core components
        self.config = Config()
        self.event_bus = EventBus()
        self.db = Database(self.config)
        
        # Setup UI
        self.setup_ui()
        
        # Load modules
        self.modules = {}
        self.load_modules()
        
        # Show dashboard by default
        self.show_module("dashboard")
        
        # Subscribe to events
        self.event_bus.subscribe("module_change", self.show_module)
        self.event_bus.subscribe("file_opened", self.handle_file_opened)
        
        logger.info("برنامه با موفقیت راه‌اندازی شد")
    
    def setup_ui(self):
        """ایجاد رابط کاربری اصلی با نوار کناری"""
        # ایجاد فریم اصلی با دو بخش
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # نوار کناری (10% عرض)
        self.sidebar = ttk.Frame(main_frame, width=120, relief=tk.SUNKEN)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)  # جلوگیری از تغییر اندازه خودکار
        
        # بخش اصلی (90% عرض)
        self.main_content = ttk.Frame(main_frame)
        self.main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # ایجاد منوی کناری
        self.create_sidebar_menu()
        
        # نوار وضعیت
        self.status_bar = ttk.Label(self.root, text="آماده", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_sidebar_menu(self):
        """ایجاد منوی کناری با آیکون‌های ماژول‌ها"""
        # عنوان نوار کناری
        title_label = ttk.Label(
            self.sidebar,
            text="ماژول‌ها",
            font=("Tahoma", 12, "bold")
        )
        title_label.pack(pady=20)
        
        # دکمه‌های ماژول‌ها به صورت موزاییکی
        self.module_buttons = {}
        modules = [
            ("dashboard", "📊", "داشبورد"),
            ("datasheets", "📄", "مقالات"),
            ("research", "🔍", "تحقیق"),
            ("analysis", "📈", "تحلیل"),
            ("search", "🔎", "جستجو")
        ]
        
        for module_name, icon, text in modules:
            btn_frame = ttk.Frame(self.sidebar)
            btn_frame.pack(pady=5, padx=10, fill=tk.X)
            
            btn = ttk.Button(
                btn_frame,
                text=f"{icon} {text}",
                command=lambda m=module_name: self.event_bus.publish("module_change", m),
                width=15
            )
            btn.pack(fill=tk.X)
            self.module_buttons[module_name] = btn
    
    def load_modules(self):
        """بارگذاری ماژول‌ها از پوشه modules"""
        modules_dir = Path(__file__).parent.parent / "modules"
        for module_dir in modules_dir.iterdir():
            if module_dir.is_dir() and (module_dir / "__init__.py").exists():
                module_name = module_dir.name
                try:
                    # import module
                    module = importlib.import_module(f"modules.{module_name}.{module_name}_module")
                    module_class = getattr(module, f"{module_name.capitalize()}Module")
                    # create instance in main_content frame
                    module_instance = module_class(self.main_content, self)
                    self.modules[module_name] = module_instance
                    
                    logger.info(f"ماژول {module_name} با موفقیت بارگذاری شد")
                except ImportError as e:
                    logger.error(f"خطا در بارگذاری ماژول {module_name}: {e}")
                except Exception as e:
                    logger.error(f"خطای غیرمنتظره در بارگذاری ماژول {module_name}: {e}")
    
    def show_module(self, module_name):
        """نمایش ماژول درخواستی در بخش اصلی"""
        # پنهان کردن تمام ماژول‌ها
        for module in self.modules.values():
            module.pack_forget()
        
        # نمایش ماژول انتخاب شده
        if module_name in self.modules:
            self.modules[module_name].pack(fill=tk.BOTH, expand=True)
            self.status_bar.config(text=f"ماژول {module_name} فعال است")
            logger.info(f"ماژول {module_name} نمایش داده شد")
        else:
            self.status_bar.config(text=f"ماژول {module_name} یافت نشد")
            logger.warning(f"ماژول {module_name} یافت نشد")
    
    def open_file(self):
        """باز کردن فایل"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="باز کردن فایل",
            filetypes=[("PDF Files", "*.pdf"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.config.add_recent_file(file_path)
            self.event_bus.publish("file_opened", file_path)
            logger.info(f"فایل {file_path} باز شد")
    
    def handle_file_opened(self, file_path):
        """مدیریت فایل باز شده"""
        if file_path.endswith('.pdf'):
            self.event_bus.publish("module_change", "datasheets")
            self.event_bus.publish("pdf_file_opened", file_path)
        
        logger.info(f"فایل {file_path} پردازش شد")