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
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)
    
    def unsubscribe(self, event_type, callback):
        """لغو اشتراک رویداد"""
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)