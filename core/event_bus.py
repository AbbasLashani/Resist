# event_bus.py
class EventBus:
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, event_type, callback):
        """اشتراک در رویداد"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def publish(self, event_type, data):
        """انتشار رویداد"""
        print(f"🎯 Event Published: {event_type} - {data}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in event callback: {e}")
    
    def unsubscribe(self, event_type, callback):
        """لغو اشتراک رویداد"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)