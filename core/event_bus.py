# research_assistant/core/event_bus.py
class EventBus:
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, event_type, callback):
        """ثبت یک شنونده برای نوع رویداد مشخص"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type, callback):
        """حذف یک شنونده از نوع رویداد مشخص"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)
    
    def publish(self, event_type, data=None):
        """انتشار یک رویداد"""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"خطا در اجرای callback برای رویداد {event_type}: {e}")