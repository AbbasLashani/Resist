import arabic_reshaper
from bidi.algorithm import get_display

# پیکربندی جدید برای arabic-reshaper
reshaper_config = {
    'language': 'Arabic',
    'use_unshaped_instead_of_isolated': False,
    'delete_harakat': True,
    'support_ligatures': True,
    'digits': 'arabic'
}

# ایجاد نمونه reshaper با پیکربندی
reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

def reshape_text(text):
    """تغییر شکل حروف فارسی و راست‌چین کردن متن"""
    try:
        if isinstance(text, str) and any('\u0600' <= c <= '\u06FF' for c in text):
            reshaped_text = reshaper.reshape(text)
            return get_display(reshaped_text)
        return text
    except:
        return text

def set_widget_rtl(widget):
    """تنظیم ویجت برای راست به چپ"""
    try:
        if hasattr(widget, 'configure'):
            if 'anchor' in widget.configure():
                widget.configure(anchor="e")
            if 'justify' in widget.configure():
                widget.configure(justify="right")
    except:
        pass

def set_widget_ltr(widget):
    """تنظیم ویجت برای چپ به راست"""
    try:
        if hasattr(widget, 'configure'):
            if 'anchor' in widget.configure():
                widget.configure(anchor="w")
            if 'justify' in widget.configure():
                widget.configure(justify="left")
    except:
        pass