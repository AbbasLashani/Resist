# core/config.py
import json
import os

class Config:
    def __init__(self):
        self.config_path = "config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """بارگذاری تنظیمات از فایل JSON"""
        default_config = {
            "app": {
                "name": "Research Assistant",
                "version": "1.0.0",
                "language": "fa",
                "default_module": "dashboard"
            },
            "database": {
                "path": "data/research_assistant.db",
                "backup_enabled": True,
                "backup_path": "backups/"
            },
            "theme": {
                "default_mode": "system",
                "default_color_theme": "blue",
                "animation_enabled": True,
                "font_family": "Vazirmatn",
                "font_size": 14
            }
        }
        
        # اگر فایل config وجود دارد، آن را بارگذاری کنید
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # ادغام config پیش‌فرض با config بارگذاری شده
                    return self.merge_configs(default_config, loaded_config)
            except Exception as e:
                print(f"خطا در بارگذاری config: {e}")
                return default_config
        else:
            # اگر فایل config وجود ندارد، آن را ایجاد کنید
            self.save_config(default_config)
            return default_config
    
    def merge_configs(self, default, loaded):
        """ادغام config پیش‌فرض با config بارگذاری شده"""
        # یک کپی از config پیش‌فرض ایجاد کنید
        merged = default.copy()
        
        # مقادیر از config بارگذاری شده را اضافه/به‌روزرسانی کنید
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # اگر هر دو مقدار دیکشنری هستند، به صورت بازگشتی ادغام کنید
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def save_config(self, config=None):
        """ذخیره تنظیمات در فایل JSON"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطا در ذخیره config: {e}")
    
    def get(self, key, default=None):
        """دریافت مقدار از config با کلید مشخص"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """تنظیم مقدار در config با کلید مشخص"""
        keys = key.split('.')
        config = self.config
        
        # به جز آخرین کلید، به دیکشنری داخلی بروید
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # مقدار را تنظیم کنید
        config[keys[-1]] = value
        
        # تغییرات را ذخیره کنید
        self.save_config()