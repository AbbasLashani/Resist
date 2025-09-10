import arabic_reshaper
from bidi.algorithm import get_display

# Create configuration for Arabic reshaper
reshaper_config = {
    'language': 'Arabic',
    'use_unshaped_instead_of_isolated': False,
    'delete_harakat': False,
    'support_ligatures': True,
    'digits': 'arabic'
}

# Initialize the reshaper with configuration
reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

def reshape_text(text):
    """تغییر شکل حروف فارسی و راست‌چین کردن متن"""
    try:
        reshaped_text = reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text

def set_widget_rtl(widget):
    """تنظیم جهت راست به چپ برای ویجت"""
    try:
        if hasattr(widget, 'configure'):
            widget.configure(anchor='e')
    except:
        pass

def set_widget_ltr(widget):
    """تنظیم جهت چپ به راست برای ویجت"""
    try:
        if hasattr(widget, 'configure'):
            widget.configure(anchor='w')
    except:
        pass