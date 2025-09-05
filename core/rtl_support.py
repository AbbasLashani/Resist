# core/rtl_support.py
import arabic_reshaper
from bidi.algorithm import get_display

class RTLSupport:
    @staticmethod
    def reshape_text(text):
        """تغییر شکل حروف فارسی و راست‌چین کردن متن"""
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except:
            return text
    
    @staticmethod
    def setup_widget_rtl(widget):
        """تنظیم جهت راست به چپ برای ویجت"""
        try:
            # برای ویجت‌های CTk می‌توانیم از anchor استفاده کنیم
            if hasattr(widget, 'configure'):
                widget.configure(anchor='e')  # تراز به راست
        except:
            pass