# research_assistant/core/app.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import importlib.util
import sys
import logging
import traceback

# اضافه کردن مسیر اصلی پروژه به sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.config import Config
from core.database import Database
from core.event_bus import EventBus

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchAssistantApp:
    def __init__(self, root):
        self.root = root
        self.config = Config()
        self.event_bus = EventBus()
        self.db = Database(self.config)
        self.setup_app()
        self.setup_ui()
        self.load_modules()
        
    def setup_app(self):
        """تنظیمات اولیه برنامه"""
        self.root.title(self.config.t("app_title"))
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # تنظیم راست به چپ برای فارسی
        if self.config.current_language == "fa":
            try:
                self.root.tk.call('tk', 'scaling', 1.2)
            except:
                pass
            self.root.option_add('*justify', 'right')
            self.root.option_add('*direction', 'rtl')
            self.root.option_add('*font', 'Tahoma 10')
        
        # مسیرهای مهم
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.modules_dir = os.path.join(self.base_dir, "modules")
        
        # ایجاد پوشه‌های لازم
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.modules_dir, exist_ok=True)
        
        # سیستم ماژول‌ها
        self.modules = {}
        self.current_module = "dashboard"
        self.current_module_instance = None
        
    def setup_ui(self):
        """ایجاد رابط کاربری اصلی با نوار کناری"""
        # فریم اصلی که شامل نوار کناری و محتوای اصلی است
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # نوار کناری (سمت راست - 20% عرض)
        self.sidebar = ttk.Frame(main_container, width=200, relief=tk.SUNKEN)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)  # جلوگیری از تغییر سایز خودکار
        
        # بخش محتوای اصلی (سمت چپ - 80% عرض)
        self.main_content = ttk.Frame(main_container)
        self.main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # ایجاد منوی کناری
        self.create_sidebar()
        
        # ایجاد منوی اصلی
        self.setup_main_menu()
        
        # ناحیه محتوای ماژول‌ها
        self.content_frame = ttk.Frame(self.main_content)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # نوار وضعیت
        self.setup_status_bar()
        
    def create_sidebar(self):
        """ایجاد نوار کناری با دکمه‌های ماژول‌ها"""
        # عنوان نوار کناری
        title_label = ttk.Label(
            self.sidebar,
            text="🧪 " + self.config.t("modules"),
            font=("Tahoma", 12, "bold")
        )
        title_label.pack(pady=20)
        
        # جداکننده
        separator = ttk.Separator(self.sidebar, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=10, pady=10)
        
        # فریم برای دکمه‌های ماژول‌ها
        self.buttons_frame = ttk.Frame(self.sidebar)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_main_menu(self):
        """ایجاد منوی اصلی"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # منوی فایل
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.config.t("file"), menu=file_menu)
        file_menu.add_command(label=self.config.t("settings"), command=self.show_settings)
        
        # انتخاب زبان
        lang_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="زبان / Language", menu=lang_menu)
        lang_menu.add_command(label="فارسی", command=lambda: self.change_language("fa"))
        lang_menu.add_command(label="English", command=lambda: self.change_language("en"))
        
        file_menu.add_separator()
        file_menu.add_command(label=self.config.t("exit"), command=self.root.quit)
        
        # منوی کمک
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.config.t("help"), menu=help_menu)
        help_menu.add_command(label=self.config.t("about"), command=self.show_about)
        
    def setup_status_bar(self):
        """ایجاد نوار وضعیت"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value=self.config.t("status_ready"))
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # نمایش زبان جاری
        lang_text = "فارسی" if self.config.current_language == "fa" else "English"
        ttk.Label(self.status_frame, text=f"🌐 {lang_text}").pack(side=tk.RIGHT, padx=5)
        
    def clear_content(self):
        """پاک کردن محتوای فعلی"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        if self.current_module_instance:
            try:
                self.current_module_instance.destroy()
            except:
                pass
            self.current_module_instance = None
        
    def load_modules(self):
        """بارگذاری ماژول‌ها"""
        logger.info("بارگذاری ماژول‌ها شروع شد")
        
        # ماژول‌های داخلی
        self.register_builtin_modules()
        
        # ماژول‌های خارجی (از پوشه modules)
        self.load_external_modules()
        
        # اضافه کردن دکمه‌های ماژول‌ها به نوار کناری
        self.add_module_buttons_to_sidebar()
        
        # نمایش داشبورد به عنوان صفحه اصلی
        self.activate_module("dashboard")
        
    def add_module_buttons_to_sidebar(self):
        """اضافه کردن دکمه‌های ماژول‌ها به نوار کناری"""
        # پاک کردن دکمه‌های قبلی
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # اضافه کردن دکمه‌های ماژول‌ها
        modules_info = [
            ("dashboard", "📊", self.config.t("dashboard")),
            ("articles", "📄", self.config.t("articles_management")),
            ("research", "🔍", self.config.t("research")),
            ("analysis", "📈", self.config.t("analysis")),
            ("search", "🔎", self.config.t("search"))
        ]
        
        for module_name, icon, text in modules_info:
            if module_name in self.modules:
                # ایجاد دکمه با آیکون و متن
                btn = ttk.Button(
                    self.buttons_frame,
                    text=f"{icon} {text}",
                    command=lambda m=module_name: self.activate_module(m),
                    width=20
                )
                btn.pack(pady=5, padx=10, fill=tk.X)
        
    def register_builtin_modules(self):
        """ثبت ماژول‌های داخلی"""
        try:
            # مسیر ماژول داشبورد
            dashboard_path = os.path.join(self.modules_dir, "dashboard", "dashboard_module.py")
            
            if not os.path.exists(dashboard_path):
                logger.error(f"فایل ماژول داشبورد یافت نشد: {dashboard_path}")
                return
                
            # بارگذاری ماژول با importlib
            spec = importlib.util.spec_from_file_location("dashboard_module", dashboard_path)
            dashboard_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dashboard_module)
            
            # پیدا کردن کلاس DashboardModule
            if hasattr(dashboard_module, 'DashboardModule'):
                self.modules["dashboard"] = dashboard_module.DashboardModule
                logger.info("ماژول داشبورد با موفقیت بارگذاری شد")
            else:
                logger.error("کلاس DashboardModule در ماژول داشبورد یافت نشد")
                
        except Exception as e:
            logger.error(f"خطا در بارگذاری ماژول داشبورد: {e}")
            self.show_error_screen()
            
    def load_external_modules(self):
        """بارگذاری خودکار ماژول‌ها از پوشه modules"""
        if not os.path.exists(self.modules_dir):
            return
            
        for module_name in os.listdir(self.modules_dir):
            module_path = os.path.join(self.modules_dir, module_name)
            if os.path.isdir(module_path) and module_name != "__pycache__" and module_name != "dashboard":
                self.load_single_module(module_name, module_path)
                
    def load_single_module(self, module_name, module_path):
        """بارگذاری یک ماژول از پوشه"""
        try:
            # جستجوی فایل ماژول
            module_file = None
            possible_files = [
                os.path.join(module_path, "module.py"),
                os.path.join(module_path, f"{module_name}_module.py"),
                os.path.join(module_path, f"{module_name}.py")
            ]
            
            for file_path in possible_files:
                if os.path.exists(file_path):
                    module_file = file_path
                    break
            
            if not module_file:
                logger.warning(f"فایل ماژول برای {module_name} یافت نشد")
                return
                
            # بارگذاری ماژول
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # پیدا کردن کلاس ماژول
            module_class = None
            possible_classes = [
                getattr(module, "Module", None),
                getattr(module, f"{module_name.capitalize()}Module", None),
                getattr(module, module_name.capitalize(), None)
            ]
            
            for class_obj in possible_classes:
                if class_obj and hasattr(class_obj, '__call__'):
                    module_class = class_obj
                    break
            
            if not module_class:
                logger.warning(f"کلاس ماژول برای {module_name} یافت نشد")
                return
                
            # ثبت ماژول
            self.modules[module_name] = module_class
            logger.info(f"ماژول {module_name} با موفقیت بارگذاری شد")
                    
        except Exception as e:
            logger.error(f"خطا در بارگذاری ماژول {module_name}: {e}")
            
    def activate_module(self, module_name):
        """فعال کردن یک ماژول"""
        logger.info(f"تلاش برای فعال‌سازی ماژول: {module_name}")
        
        if module_name in self.modules:
            try:
                self.clear_content()
                self.status_var.set(f"{self.config.t('loading_module')} {module_name}...")
                self.root.update()
                
                # ایجاد نمونه ماژول
                self.current_module = module_name
                self.current_module_instance = self.modules[module_name](
                    self.content_frame, 
                    self,
                    self.config
                )
                
                # نمایش فریم ماژول
                self.current_module_instance.pack(fill=tk.BOTH, expand=True)
                
                # اگر ماژول متد on_activate دارد، آن را فراخوانی کن
                if hasattr(self.current_module_instance, 'on_activate'):
                    self.current_module_instance.on_activate()
                
                logger.info(f"ماژول {module_name} با موفقیت فعال شد")
                self.status_var.set(self.config.t("status_ready"))
                
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"خطا در فعال‌سازی ماژول {module_name}: {error_details}")
                self.status_var.set(self.config.t("module_load_error"))
                messagebox.showerror(
                    self.config.t("error"), 
                    f"{self.config.t('module_load_error')} {module_name}:\n{str(e)}"
                )
                self.show_error_screen()
        else:
            logger.warning(f"ماژول {module_name} یافت نشد")
            messagebox.showwarning(
                self.config.t("warning"), 
                f"{self.config.t('module_not_found')}: {module_name}"
            )
            
    def change_language(self, language):
        """تغییر زبان برنامه"""
        if language in ["fa", "en"]:
            if self.config.set_language(language):
                messagebox.showinfo(
                    self.config.t("info"), 
                    self.config.t("restart_required")
                )
            
    def show_settings(self):
        """نمایش تنظیمات"""
        messagebox.showinfo(
            self.config.t("settings"), 
            self.config.t("settings_under_development")
        )
        
    def show_about(self):
        """نمایش اطلاعات درباره برنامه"""
        about_text = f"""
        {self.config.t("app_title")}
        {self.config.t("version")} 0.1
        
        {self.config.t("about_description")}
        
        {self.config.t("developed_with")} Python & Tkinter
        """
        messagebox.showinfo(self.config.t("about"), about_text)
        
    def show_error_screen(self):
        """نمایش صفحه خطا"""
        self.clear_content()
        
        error_frame = ttk.Frame(self.content_frame)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)
        
        ttk.Label(
            error_frame, 
            text="❌ " + self.config.t("module_load_error"),
            font=("Tahoma", 16, "bold")
        ).pack(pady=20)
        
        ttk.Label(
            error_frame, 
            text=self.config.t("check_module_installation"),
            font=("Tahoma", 12)
        ).pack(pady=10)
        
    def __del__(self):
        """تمیزکاری هنگام بسته شدن"""
        # بستن اتصال به پایگاه داده
        if hasattr(self, 'db'):
            self.db.close()