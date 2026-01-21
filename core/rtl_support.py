import arabic_reshaper
from bidi.algorithm import get_display
import logging

# تنظیم لاگر برای این ماژول
logger = logging.getLogger(__name__)

# پیکربندی بهینه‌شده برای فارسی
reshaper_config = {
    'language': 'Farsi',
    'use_unshaped_instead_of_isolated': False,
    'delete_harakat': True,
    'support_ligatures': True,
    'digits': 'persian',
    'support_tashkeel': False
}

# ایجاد نمونه reshaper با پیکربندی بهینه
reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

def reshape_text(text):
    """
    تغییر شکل حروف فارسی و راست‌چین کردن متن
    Args:
        text (str): متن ورودی برای تغییر شکل
    Returns:
        str: متن تغییر شکل یافته و راست‌چین شده
    """
    try:
        # بررسی وجود متن و نوع آن
        if text is None:
            return ""
            
        if not isinstance(text, str):
            text = str(text)
            
        if not text.strip():
            return text
            
        # بررسی آیا متن حاوی حروف فارسی/عربی است
        has_arabic_chars = any('\u0600' <= char <= '\u06FF' for char in text)
        
        if not has_arabic_chars:
            return text
            
        # تغییر شکل متن
        reshaped_text = reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        
        return bidi_text
        
    except Exception as e:
        logger.error(f"خطا در reshape_text برای متن '{text}': {e}")
        return text

def set_widget_rtl(widget):
    """
    تنظیم ویجت و تمام فرزندانش برای راست به چپ
    Args:
        widget: ویجت اصلی برای تنظیم RTL
    """
    if widget is None:
        return
        
    try:
        # تنظیم خود ویجت
        _configure_single_widget_rtl(widget)
        
        # تنظیم بازگشتی تمام فرزندان
        children = widget.winfo_children()
        if children:
            for child in children:
                if child is not None:
                    set_widget_rtl(child)
                    
    except Exception as e:
        logger.error(f"خطا در set_widget_rtl: {e}")

def _configure_single_widget_rtl(widget):
    """
    تنظیمات RTL برای یک ویجت منفرد
    Args:
        widget: ویجت برای تنظیم
    """
    try:
        if hasattr(widget, 'configure'):
            config_options = widget.configure()
            
            # تنظیم anchor برای تراز راست
            if 'anchor' in config_options:
                widget.configure(anchor="e")
            
            # تنظیم justify برای متن‌های چندخطی
            if 'justify' in config_options:
                widget.configure(justify="right")
            
            # تنظیم compound برای ترکیب تصویر و متن
            if 'compound' in config_options:
                widget.configure(compound="right")
            
            # برای CustomTkinter widgets
            if hasattr(widget, 'text'):
                current_text = getattr(widget, 'text', '')
                if current_text:
                    widget.configure(text=reshape_text(current_text))
                    
    except Exception as e:
        logger.debug(f"خطا در پیکربندی ویجت RTL: {e}")

def set_widget_ltr(widget):
    """
    تنظیم ویجت و تمام فرزندانش برای چپ به راست
    Args:
        widget: ویجت اصلی برای تنظیم LTR
    """
    if widget is None:
        return
        
    try:
        # تنظیم خود ویجت
        _configure_single_widget_ltr(widget)
        
        # تنظیم بازگشتی تمام فرزندان
        children = widget.winfo_children()
        if children:
            for child in children:
                if child is not None:
                    set_widget_ltr(child)
                    
    except Exception as e:
        logger.error(f"خطا در set_widget_ltr: {e}")

def _configure_single_widget_ltr(widget):
    """
    تنظیمات LTR برای یک ویجت منفرد
    Args:
        widget: ویجت برای تنظیم
    """
    try:
        if hasattr(widget, 'configure'):
            config_options = widget.configure()
            
            # تنظیم anchor برای تراز چپ
            if 'anchor' in config_options:
                widget.configure(anchor="w")
            
            # تنظیم justify برای متن‌های چندخطی
            if 'justify' in config_options:
                widget.configure(justify="left")
            
            # تنظیم compound برای ترکیب تصویر و متن
            if 'compound' in config_options:
                widget.configure(compound="left")
                
    except Exception as e:
        logger.debug(f"خطا در پیکربندی ویجت LTR: {e}")

def create_rtl_label(parent, text, **kwargs):
    """
    ایجاد لیبل راست‌چین با متن فارسی
    Args:
        parent: والد ویجت
        text (str): متن لیبل
        **kwargs: آرگومان‌های اضافی برای لیبل
    Returns:
        ویجت لیبل ایجاد شده
    """
    try:
        from customtkinter import CTkLabel
        reshaped_text = reshape_text(text)
        label = CTkLabel(parent, text=reshaped_text, **kwargs)
        set_widget_rtl(label)
        return label
    except Exception as e:
        logger.error(f"خطا در ایجاد لیبل RTL: {e}")
        return None

def create_rtl_button(parent, text, command=None, **kwargs):
    """
    ایجاد دکمه راست‌چین با متن فارسی
    Args:
        parent: والد ویجت
        text (str): متن دکمه
        command: تابع callback
        **kwargs: آرگومان‌های اضافی برای دکمه
    Returns:
        ویجت دکمه ایجاد شده
    """
    try:
        from customtkinter import CTkButton
        reshaped_text = reshape_text(text)
        button = CTkButton(parent, text=reshaped_text, command=command, **kwargs)
        set_widget_rtl(button)
        return button
    except Exception as e:
        logger.error(f"خطا در ایجاد دکمه RTL: {e}")
        return None

# تست توابع در صورت اجرای مستقیم
if __name__ == "__main__":
    # تست توابع با متن فارسی
    test_text = "این یک متن تست فارسی است"
    print(f"متن اصلی: {test_text}")
    print(f"متن تغییر شکل یافته: {reshape_text(test_text)}")