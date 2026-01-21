# event_bus.py
import logging
from typing import Dict, List, Callable, Any, Optional

class EventBus:
    """
    سیستم مدیریت رویدادها برای ارتباط بین ماژول‌های برنامه
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """تنظیمات لاگینگ"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def subscribe(self, event_type: str, callback: Callable) -> bool:
        """
        اشتراک در رویداد
        
        Args:
            event_type (str): نوع رویداد
            callback (Callable): تابع callback
            
        Returns:
            bool: موفقیت آمیز بودن عملیات
        """
        try:
            if not event_type or not callback:
                self.logger.warning("خطا در subscribe: event_type یا callback خالی است")
                return False
            
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            
            # جلوگیری از ثبت تکراری
            if callback not in self.subscribers[event_type]:
                self.subscribers[event_type].append(callback)
                self.logger.debug(f"اشتراک ثبت شد: {event_type} - {callback.__name__}")
                return True
            else:
                self.logger.debug(f"callback تکراری برای رویداد: {event_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"خطا در ثبت اشتراک برای {event_type}: {e}")
            return False
    
    def publish(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        انتشار رویداد
        
        Args:
            event_type (str): نوع رویداد
            data (Dict, optional): داده‌های رویداد
            
        Returns:
            bool: موفقیت آمیز بودن عملیات
        """
        try:
            if not event_type:
                self.logger.warning("خطا در publish: event_type خالی است")
                return False
            
            if data is None:
                data = {}
            
            self.logger.info(f"🎯 رویداد منتشر شد: {event_type} - {data}")
            
            if event_type in self.subscribers:
                # ایجاد کپی از لیست برای جلوگیری از تغییرات حین اجرا
                callbacks = self.subscribers[event_type].copy()
                
                for callback in callbacks:
                    try:
                        callback(data)
                        self.logger.debug(f"✅ callback اجرا شد: {callback.__name__} برای رویداد {event_type}")
                    except Exception as e:
                        self.logger.error(f"❌ خطا در اجرای callback {callback.__name__} برای رویداد {event_type}: {e}")
                        # ادامه اجرای بقیه callbackها حتی در صورت خطا
                        continue
            else:
                self.logger.debug(f"⚠️ هیچ اشتراکی برای رویداد {event_type} یافت نشد")
                
            return True
            
        except Exception as e:
            self.logger.error(f"خطا در انتشار رویداد {event_type}: {e}")
            return False
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        لغو اشتراک رویداد
        
        Args:
            event_type (str): نوع رویداد
            callback (Callable): تابع callback
            
        Returns:
            bool: موفقیت آمیز بودن عملیات
        """
        try:
            if not event_type or not callback:
                self.logger.warning("خطا در unsubscribe: event_type یا callback خالی است")
                return False
            
            if event_type in self.subscribers:
                if callback in self.subscribers[event_type]:
                    self.subscribers[event_type].remove(callback)
                    self.logger.debug(f"اشتراک لغو شد: {event_type} - {callback.__name__}")
                    
                    # حذف لیست خالی
                    if not self.subscribers[event_type]:
                        del self.subscribers[event_type]
                    return True
                else:
                    self.logger.warning(f"callback برای لغو اشتراک یافت نشد: {event_type}")
                    return False
            else:
                self.logger.warning(f"رویداد برای لغو اشتراک یافت نشد: {event_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"خطا در لغو اشتراک برای {event_type}: {e}")
            return False
    
    def unsubscribe_all(self, event_type: str) -> bool:
        """
        لغو تمام اشتراک‌های یک رویداد
        
        Args:
            event_type (str): نوع رویداد
            
        Returns:
            bool: موفقیت آمیز بودن عملیات
        """
        try:
            if event_type in self.subscribers:
                count = len(self.subscribers[event_type])
                del self.subscribers[event_type]
                self.logger.info(f"تمام {count} اشتراک برای رویداد {event_type} لغو شد")
                return True
            else:
                self.logger.debug(f"رویداد برای لغو اشتراک یافت نشد: {event_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"خطا در لغو تمام اشتراک‌های {event_type}: {e}")
            return False
    
    def get_subscriber_count(self, event_type: str) -> int:
        """
        دریافت تعداد اشتراک‌های یک رویداد
        
        Args:
            event_type (str): نوع رویداد
            
        Returns:
            int: تعداد اشتراک‌ها
        """
        return len(self.subscribers.get(event_type, []))
    
    def list_events(self) -> List[str]:
        """
        دریافت لیست تمام رویدادهای فعال
        
        Returns:
            List[str]: لیست رویدادها
        """
        return list(self.subscribers.keys())
    
    def clear_all(self):
        """پاک کردن تمام اشتراک‌ها"""
        try:
            event_count = len(self.subscribers)
            self.subscribers.clear()
            self.logger.info(f"تمام {event_count} رویداد پاک شدند")
        except Exception as e:
            self.logger.error(f"خطا در پاک کردن تمام اشتراک‌ها: {e}")

# نمونه گلوبال برای استفاده در سراسر برنامه
event_bus = EventBus()

# تست عملکرد در صورت اجرای مستقیم
if __name__ == "__main__":
    # تست توابع
    def test_callback1(data):
        print(f"Callback1 دریافت کرد: {data}")
    
    def test_callback2(data):
        print(f"Callback2 دریافت کرد: {data}")
    
    # تست اشتراک و انتشار
    event_bus.subscribe("test_event", test_callback1)
    event_bus.subscribe("test_event", test_callback2)
    
    # انتشار رویداد
    event_bus.publish("test_event", {"message": "تست رویداد"})
    
    # تست لغو اشتراک
    event_bus.unsubscribe("test_event", test_callback1)
    
    # انتشار مجدد
    event_bus.publish("test_event", {"message": "تست بعد از لغو اشتراک"})
    
    print(f"تعداد اشتراک‌ها: {event_bus.get_subscriber_count('test_event')}")
    print(f"رویدادهای فعال: {event_bus.list_events()}")