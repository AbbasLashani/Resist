import arabic_reshaper
from bidi.algorithm import get_display

# تنظیمات arabic_reshaper
arabic_reshaper.config_for_arabic_reshaper(
    language='farsi',
    use_unshaped_instead_of_isolated=False,
    delete_harakat=True,
    support_ligatures=True,
    digits='arabic'
)

def reshape_text(text):
    """تغییر شکل حروف فارسی و راست‌چین کردن متن"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    except:
        return text

def set_widget_rtl(widget):
    """تنظیم جهت راست به چپ برای ویجت"""
    try:
        # برای ویجت‌های CTk می‌توانیم از anchor استفاده کنیم
        if hasattr(widget, 'configure'):
            widget.configure(anchor='e')  # تراز به راست
    except:
        pass