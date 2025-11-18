# modules/notes/notes_module.py
# NotesModule — ماژول یادداشت‌ها با طراحی مدرن و رابط کاربری بهینه

import os
import json
import sqlite3
import logging
from datetime import datetime
import tkinter as tk
from tkinter import ttk, colorchooser, simpledialog, messagebox, font as tkfont
import customtkinter as ctk

try:
    from core.base_module import BaseModule
except Exception:
    class BaseModule(ctk.CTkFrame):
        def __init__(self, parent, app=None, config=None, **kwargs):
            super().__init__(parent, **kwargs)
            self.app = app
            self.config = config or {}

# ایمپورت دیتابیس جداگانه
try:
    from .notes_database import NotesDatabase
except ImportError:
    from modules.notes.notes_database import NotesDatabase

logger = logging.getLogger("modules.notes.notes_module")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class ModernTextEditor(ctk.CTkFrame):
    """ویرایشگر متن مدرن با پشتیبانی کامل از راست‌چین و منوی راست کلیک"""
    
    def __init__(self, parent, default_family="Vazirmatn", default_size=12, *args, **kwargs):  # کاهش سایز فونت پایه
        super().__init__(parent, *args, **kwargs)
        
        self.default_family = default_family
        self.default_size = default_size
        self._modified_since_save = False
        self._autosave_after_id = None
        
        # تنظیم فونت پایه
        self.base_font = tkfont.Font(
            family=self.default_family, 
            size=self.default_size
        )
        
        self._create_widgets()
        self._configure_tags()
        self._bind_events()
        self._setup_initial_content()
        self._create_context_menu()  # ایجاد منوی راست کلیک

    def _create_context_menu(self):
        """ایجاد منوی راست کلیک برای عملیات کپی/پیست"""
        self.context_menu = tk.Menu(self.text, tearoff=0, font=("Vazirmatn", 10))
        self.context_menu.add_command(label="برش (Cut)", command=self.cut_text, accelerator="Ctrl+X")
        self.context_menu.add_command(label="کپی (Copy)", command=self.copy_text, accelerator="Ctrl+C")
        self.context_menu.add_command(label="چسباندن (Paste)", command=self.paste_text, accelerator="Ctrl+V")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="انتخاب همه", command=self.select_all, accelerator="Ctrl+A")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="حذف", command=self.delete_selection)

    def cut_text(self):
        """برش متن انتخاب شده"""
        try:
            self.text.event_generate("<<Cut>>")
        except Exception as e:
            logger.error(f"خطا در برش متن: {e}")

    def copy_text(self):
        """کپی متن انتخاب شده"""
        try:
            self.text.event_generate("<<Copy>>")
        except Exception as e:
            logger.error(f"خطا در کپی متن: {e}")

    def paste_text(self):
        """چسباندن متن"""
        try:
            self.text.event_generate("<<Paste>>")
        except Exception as e:
            logger.error(f"خطا در چسباندن متن: {e}")

    def select_all(self):
        """انتخاب تمام متن"""
        try:
            self.text.tag_add("sel", "1.0", "end")
        except Exception as e:
            logger.error(f"خطا در انتخاب همه متن: {e}")

    def delete_selection(self):
        """حذف متن انتخاب شده"""
        try:
            if self.text.tag_ranges("sel"):
                self.text.delete("sel.first", "sel.last")
        except Exception as e:
            logger.error(f"خطا در حذف متن: {e}")

    def _show_context_menu(self, event):
        """نمایش منوی راست کلیک"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _create_widgets(self):
        """ایجاد ویجت‌ها با طراحی مدرن"""
        self._create_modern_toolbar()
        self._create_text_area()

    def _create_modern_toolbar(self):
        """نوار ابزار مدرن با طراحی تمیز"""
        toolbar = ctk.CTkFrame(self, fg_color=("#ffffff", "#2b2b2b"), height=55)
        toolbar.pack(side="top", fill="x", padx=0, pady=(0, 1))
        toolbar.pack_propagate(False)

        toolbar_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_inner.pack(fill="both", expand=True, padx=12, pady=10)

        # استایل مشترک دکمه‌ها
        btn_style = {
            "width": 40, 
            "height": 36, 
            "corner_radius": 6,
            "font": ctk.CTkFont(size=11),  # کاهش سایز فونت
            "border_width": 1,
            "border_color": ("#e0e0e0", "#404040")
        }

        # گروه فرمت‌بندی متن - سمت راست
        format_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        format_frame.pack(side="right", padx=(8, 0))
        
        format_buttons = [
            ("B", self.toggle_bold, "پررنگ (Ctrl+B)"),
            ("I", self.toggle_italic, "مورب (Ctrl+I)"),
            ("U", self.toggle_underline, "زیرخط (Ctrl+U)"),
        ]
        
        for text, command, tooltip in format_buttons:
            btn = ctk.CTkButton(
                format_frame,
                text=text,
                command=command,
                fg_color="transparent",
                text_color=("#2c3e50", "#ecf0f1"),
                hover_color=("#3498db", "#2980b9"),
                **btn_style
            )
            btn.pack(side="right", padx=2)

        # جداکننده
        separator1 = ctk.CTkLabel(format_frame, text="|", text_color=("#cccccc", "#666666"))
        separator1.pack(side="right", padx=6)

        # گروه تراز متن
        align_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        align_frame.pack(side="right", padx=8)
        
        align_buttons = [
            ("⟪", lambda: self.set_alignment('right'), "راست‌چین"),
            ("⫯", lambda: self.set_alignment('center'), "وسط‌چین"), 
            ("⟫", lambda: self.set_alignment('left'), "چپ‌چین")
        ]
        
        for text, command, tooltip in align_buttons:
            btn = ctk.CTkButton(
                align_frame,
                text=text,
                command=command,
                fg_color="transparent",
                text_color=("#2c3e50", "#ecf0f1"),
                hover_color=("#3498db", "#2980b9"),
                **btn_style
            )
            btn.pack(side="right", padx=2)

        # جداکننده
        separator2 = ctk.CTkLabel(align_frame, text="|", text_color=("#cccccc", "#666666"))
        separator2.pack(side="right", padx=6)

        # گروه لیست‌ها
        list_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        list_frame.pack(side="right", padx=8)
        
        list_buttons = [
            ("•", self.insert_bullet, "لیست نقطه‌ای"),
            ("1.", self.insert_numbered, "لیست شماره‌ای")
        ]
        
        for text, command, tooltip in list_buttons:
            btn = ctk.CTkButton(
                list_frame,
                text=text,
                command=command,
                fg_color="transparent", 
                text_color=("#2c3e50", "#ecf0f1"),
                hover_color=("#3498db", "#2980b9"),
                **btn_style
            )
            btn.pack(side="right", padx=2)

        # کنترل‌های فونت در سمت چپ
        left_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        left_frame.pack(side="left")

        # کنترل سایز فونت
        size_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        size_frame.pack(side="left", padx=4)
        
        ctk.CTkLabel(size_frame, text="سایز:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))  # کاهش سایز فونت
        
        self.font_size_var = tk.StringVar(value=str(self.default_size))
        self.size_combo = ctk.CTkComboBox(
            size_frame,
            values=["10", "12", "14", "16", "18", "20", "22", "24", "28"],
            variable=self.font_size_var,
            width=65,
            height=34,
            dropdown_font=ctk.CTkFont(size=10),  # کاهش سایز فونت
            command=self._on_font_size_change
        )
        self.size_combo.pack(side="left")

        # پالت رنگ ساده با 15 رنگ
        self.color_palette = [
            "#FF5252", "#FF4081", "#E040FB", "#7C4DFF", "#536DFE",
            "#448AFF", "#40C4FF", "#18FFFF", "#64FFDA", "#69F0AE",
            "#B2FF59", "#EEFF41", "#FFFF00", "#FFD740", "#FFAB40"
        ]
        
        color_btn = ctk.CTkButton(
            left_frame,
            text="🎨", 
            command=self.show_color_palette,
            width=38,
            height=36,
            fg_color="transparent",
            text_color=("#2c3e50", "#ecf0f1"),
            hover_color=("#3498db", "#2980b9"),
            border_width=1,
            border_color=("#e0e0e0", "#404040")
        )
        color_btn.pack(side="left", padx=4)

        # دکمه فونت خانواده
        font_families = ["Vazirmatn", "Tahoma", "Arial", "Times New Roman", "Courier New"]
        self.font_family_var = tk.StringVar(value="Vazirmatn")
        self.font_combo = ctk.CTkComboBox(
            left_frame,
            values=font_families,
            variable=self.font_family_var,
            width=120,
            height=34,
            dropdown_font=ctk.CTkFont(size=10),  # کاهش سایز فونت
            command=self._on_font_family_change
        )
        self.font_combo.pack(side="left", padx=4)

    def show_color_palette(self):
        """نمایش پالت رنگ ساده"""
        try:
            palette_window = ctk.CTkToplevel(self)
            palette_window.title("انتخاب رنگ متن")
            palette_window.geometry("320x120")
            palette_window.resizable(False, False)
            palette_window.transient(self)
            palette_window.grab_set()
            
            # مرکز کردن پنجره
            palette_window.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() - 320) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 120) // 2
            palette_window.geometry(f"+{x}+{y}")
            
            # عنوان
            title_label = ctk.CTkLabel(
                palette_window, 
                text="رنگ متن را انتخاب کنید:",
                font=ctk.CTkFont("Vazirmatn", size=11)  # کاهش سایز فونت
            )
            title_label.pack(pady=(10, 5))
            
            # ایجاد شبکه رنگ‌ها
            color_frame = ctk.CTkFrame(palette_window, fg_color="transparent")
            color_frame.pack(expand=True, fill="both", padx=10, pady=5)
            
            # 3 ردیف و 5 ستون
            for i in range(3):
                color_frame.grid_rowconfigure(i, weight=1)
            for j in range(5):
                color_frame.grid_columnconfigure(j, weight=1)
            
            for idx, color in enumerate(self.color_palette):
                row = idx // 5
                col = idx % 5
                
                color_btn = ctk.CTkButton(
                    color_frame,
                    text="",
                    width=35,
                    height=35,
                    corner_radius=8,
                    fg_color=color,
                    hover_color=color,
                    command=lambda c=color: self._apply_color_and_close(c, palette_window)
                )
                color_btn.grid(row=row, column=col, padx=2, pady=2)
                
        except Exception as e:
            logger.error(f"خطا در نمایش پالت رنگ: {e}")

    def _apply_color_and_close(self, color, window):
        """اعمال رنگ و بستن پنجره"""
        try:
            self._apply_color_to_selection(color)
            window.destroy()
        except Exception as e:
            logger.error(f"خطا در بستن پالت رنگ: {e}")
            window.destroy()

    def _apply_color_to_selection(self, color):
        """اعمال رنگ به متن انتخاب شده"""
        try:
            # ایجاد تگ منحصر به فرد برای رنگ
            tag_name = f"color_{color.replace('#', '')}"
            
            # پیکربندی تگ اگر وجود ندارد
            current_fg = self.text.tag_cget(tag_name, "foreground")
            if not current_fg or current_fg == "":
                self.text.tag_configure(tag_name, foreground=color)
            
            # دریافت محدوده انتخاب
            start, end = self._get_selection_range()
            if not start:
                # اگر هیچ متنی انتخاب نشده، در موقعیت فعلی اعمال کن
                current_pos = self.text.index("insert")
                start = current_pos
                end = current_pos
            
            # اعمال تگ به محدوده انتخاب شده
            self.text.tag_add(tag_name, start, end)
            
            # اطمینان از نمایش تغییرات
            self.text.focus_set()
            
        except Exception as e:
            logger.error(f"خطا در اعمال رنگ: {e}")

    def _create_text_area(self):
        """ایجاد ناحیه متن با طراحی مدرن و فضای بیشتر"""
        # فریم اصلی متن
        text_container = ctk.CTkFrame(self, fg_color=("#fafafa", "#1a1a1a"), corner_radius=0)
        text_container.pack(fill="both", expand=True, padx=0, pady=0)
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)

        # فریم داخلی با فضای بیشتر
        inner_frame = ctk.CTkFrame(text_container, fg_color=("#ffffff", "#1e1e1e"), corner_radius=8)
        inner_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        inner_frame.grid_rowconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(0, weight=1)

        # اسکرول‌بارها
        self.v_scroll = ttk.Scrollbar(inner_frame)
        self.v_scroll.grid(row=0, column=1, sticky="ns", pady=2)

        self.h_scroll = ttk.Scrollbar(inner_frame, orient="horizontal")
        self.h_scroll.grid(row=1, column=0, sticky="ew", padx=2)

        # ویجت متن اصلی با راست‌چین اجباری و فضای بیشتر
        self.text = tk.Text(
            inner_frame,
            wrap="word",
            undo=True,
            font=self.base_font,
            padx=20,
            pady=20,
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
            borderwidth=0,
            relief="flat",
            bg='#ffffff' if ctk.get_appearance_mode() == "Light" else '#1e1e1e',
            fg='#2c3e50' if ctk.get_appearance_mode() == "Light" else '#ecf0f1',
            selectbackground='#3498db',
            insertbackground='#e74c3c',
            highlightthickness=1,
            highlightcolor="#bdc3c7",
            highlightbackground="#bdc3c7",
            spacing1=2,
            spacing2=1,
            spacing3=2
        )
        self.text.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        self.v_scroll.configure(command=self.text.yview)
        self.h_scroll.configure(command=self.text.xview)

    def _setup_initial_content(self):
        """تنظیم محتوای اولیه با راست‌چین"""
        if not self.text.get("1.0", "end-1c").strip():
            welcome_text = """✨ به ویرایشگر متن پیشرفته خوش آمدید!

ویژگی‌ها:
• فرمت‌بندی متن (پررنگ، مورب، زیرخط)
• ترازبندی متن (راست، وسط، چپ)
• لیست‌های نقطه‌ای و شماره‌ای
• تغییر رنگ متن و فونت
• جستجو در متن
• منوی راست کلیک برای کپی/پیست

برای شروع تایپ کنید..."""
            
            self.text.insert("1.0", welcome_text)
        
        # اعمال تگ راست‌چین به کل متن
        self.text.tag_add("right", "1.0", "end")

    def _configure_tags(self):
        """پیکربندی تگ‌های فرمت‌بندی"""
        # فونت‌های تگ‌ها
        self.tag_fonts = {
            "bold": tkfont.Font(family=self.default_family, size=self.default_size, weight="bold"),
            "italic": tkfont.Font(family=self.default_family, size=self.default_size, slant="italic"), 
            "underline": tkfont.Font(family=self.default_family, size=self.default_size, underline=1),
            "bold_italic": tkfont.Font(family=self.default_family, size=self.default_size, weight="bold", slant="italic"),
        }
        
        # تگ‌های استایل
        self.text.tag_configure("bold", font=self.tag_fonts["bold"])
        self.text.tag_configure("italic", font=self.tag_fonts["italic"])
        self.text.tag_configure("underline", font=self.tag_fonts["underline"])
        self.text.tag_configure("bold_italic", font=self.tag_fonts["bold_italic"])
        
        # تگ‌های تراز - برای ویجت Text باید از تگ‌های justify استفاده کرد
        self.text.tag_configure("right", justify="right")
        self.text.tag_configure("center", justify="center")
        self.text.tag_configure("left", justify="left")
        
        # تگ‌های لیست
        self.text.tag_configure("bullet", lmargin1=30, lmargin2=30, foreground="#e74c3c")
        self.text.tag_configure("numbered", lmargin1=30, lmargin2=30, foreground="#27ae60")

    def _bind_events(self):
        """اتصال رویدادها برای مدیریت راست‌چین و منوی راست کلیک"""
        self.text.bind("<<Modified>>", self._on_text_modified)
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<Return>", self._on_return_pressed)
        self.text.bind("<KeyPress>", self._ensure_rtl_typing)
        
        # رویداد راست کلیک برای نمایش منو
        self.text.bind("<Button-3>", self._show_context_menu)  # راست کلیک
        
        # میانبرهای صفحه کلید
        self.text.bind("<Control-b>", lambda e: (self.toggle_bold(), "break"))
        self.text.bind("<Control-i>", lambda e: (self.toggle_italic(), "break"))
        self.text.bind("<Control-u>", lambda e: (self.toggle_underline(), "break"))
        self.text.bind("<Control-f>", lambda e: (self.find_text(), "break"))
        
        # میانبرهای کپی/پیست
        self.text.bind("<Control-c>", lambda e: (self.copy_text(), "break"))
        self.text.bind("<Control-x>", lambda e: (self.cut_text(), "break"))
        self.text.bind("<Control-v>", lambda e: (self.paste_text(), "break"))
        self.text.bind("<Control-a>", lambda e: (self.select_all(), "break"))

    def _ensure_rtl_typing(self, event=None):
        """اطمینان از راست‌چین بودن در حین تایپ"""
        if event and event.keysym not in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R']:
            current_pos = self.text.index("insert")
            line_start = self.text.index(f"{current_pos} linestart")
            line_end = self.text.index(f"{current_pos} lineend")
            
            # حذف تمام تگ‌های تراز و اعمال راست‌چین
            for tag in ["right", "center", "left"]:
                self.text.tag_remove(tag, line_start, line_end)
            self.text.tag_add("right", line_start, line_end)

    def _on_text_modified(self, event=None):
        """مدیریت تغییرات متن"""
        try:
            if self.text.edit_modified():
                self._modified_since_save = True
                self.text.edit_modified(False)
        except Exception:
            pass

    def _on_key_release(self, event=None):
        """مدیریت رها کردن کلید"""
        self._ensure_alignment_tags()

    def _on_return_pressed(self, event):
        """مدیریت کلید اینتر با حفظ راست‌چین"""
        current_pos = self.text.index("insert")
        self.text.insert(current_pos, "\n")
        
        # پیدا کردن تراز خط قبلی و اعمال آن به خط جدید
        line_num = int(current_pos.split('.')[0])
        if line_num > 1:
            prev_line_start = f"{line_num - 1}.0"
            prev_line_end = f"{line_num - 1}.end"
            
            # همیشه راست‌چین اعمال کن
            new_line_start = f"{line_num}.0"
            new_line_end = f"{line_num}.end"
            self.text.tag_add("right", new_line_start, new_line_end)
        
        return "break"

    def _ensure_alignment_tags(self):
        """اطمینان از اعمال تگ‌های تراز راست‌چین"""
        try:
            line_count = int(self.text.index('end-1c').split('.')[0])
            for line_num in range(1, line_count + 1):
                line_start = f"{line_num}.0"
                line_end = f"{line_num}.end"
                
                # حذف تمام تگ‌های تراز و اعمال راست‌چین
                for tag in ["right", "center", "left"]:
                    self.text.tag_remove(tag, line_start, line_end)
                self.text.tag_add("right", line_start, line_end)
        except Exception:
            pass

    def _get_selection_range(self):
        """دریافت محدوده انتخاب شده"""
        try:
            return (self.text.index("sel.first"), self.text.index("sel.last"))
        except tk.TclError:
            return (None, None)

    # --- عملیات فرمت‌بندی ---
    def toggle_bold(self):
        self._toggle_tag("bold")

    def toggle_italic(self):
        self._toggle_tag("italic")

    def toggle_underline(self):
        self._toggle_tag("underline")

    def _toggle_tag(self, tag):
        start, end = self._get_selection_range()
        if not start:
            return
        
        if self.text.tag_nextrange(tag, start, end):
            self.text.tag_remove(tag, start, end)
        else:
            self.text.tag_add(tag, start, end)

    def set_alignment(self, align):
        start, end = self._get_selection_range()
        if not start:
            start = self.text.index("insert linestart")
            end = self.text.index("insert lineend")
        
        for t in ("right", "center", "left"):
            self.text.tag_remove(t, start, end)
        
        self.text.tag_add(align, start, end)

    def insert_bullet(self):
        idx = self.text.index("insert linestart")
        self.text.insert(idx, "• ")
        self.text.tag_add("bullet", idx, f"{idx} lineend")

    def insert_numbered(self):
        cur_line = int(self.text.index("insert").split('.')[0])
        self.text.insert(f"{cur_line}.0", f"{cur_line}. ")
        self.text.tag_add("numbered", f"{cur_line}.0", f"{cur_line}.0 lineend")

    def pick_color(self):
        color = colorchooser.askcolor(parent=self, title="انتخاب رنگ متن")
        if color and color[1]:
            self._apply_color_to_selection(color[1])

    def find_text(self):
        """جستجوی متن در ویرایشگر"""
        search_term = simpledialog.askstring("جستجو", "عبارت مورد نظر را وارد کنید:")
        if not search_term:
            return
        
        # حذف هایلایت‌های قبلی
        self.text.tag_remove("search_match", "1.0", "end")
        
        # جستجو و هایلایت کردن
        start_pos = "1.0"
        found_count = 0
        
        while True:
            start_pos = self.text.search(search_term, start_pos, stopindex="end")
            if not start_pos:
                break
                
            end_pos = f"{start_pos}+{len(search_term)}c"
            self.text.tag_add("search_match", start_pos, end_pos)
            found_count += 1
            start_pos = end_pos
        
        # پیکربندی تگ جستجو
        self.text.tag_configure("search_match", background="#fff9c4")
        
        if found_count > 0:
            messagebox.showinfo("جستجو", f"تعداد {found_count} مورد یافت شد")
            # رفتن به اولین مورد
            first_match = self.text.search(search_term, "1.0")
            if first_match:
                self.text.see(first_match)
        else:
            messagebox.showinfo("جستجو", "موردی یافت نشد")

    def _on_font_size_change(self, choice):
        try:
            new_size = int(choice)
            self.base_font.configure(size=new_size)
            for font_obj in self.tag_fonts.values():
                font_obj.configure(size=new_size)
        except Exception as e:
            logger.error(f"خطا در تغییر سایز فونت: {e}")

    def _on_font_family_change(self, choice):
        try:
            self.base_font.configure(family=choice)
            for font_obj in self.tag_fonts.values():
                font_obj.configure(family=choice)
        except Exception as e:
            logger.error(f"خطا در تغییر خانواده فونت: {e}")

    # --- متدهای عمومی ---
    def get_serialized_format(self):
        data = {
            "content": self.text.get("1.0", "end-1c"),
            "tags": []
        }
        
        for tag in self.text.tag_names():
            if tag in ("sel", "current", "insert"):
                continue
                
            ranges = self.text.tag_ranges(tag)
            if not ranges:
                continue
                
            pairs = []
            for i in range(0, len(ranges), 2):
                pairs.append([str(ranges[i]), str(ranges[i + 1])])
                
            data["tags"].append({"name": tag, "ranges": pairs})
            
        return data

    def set_content_from_serialized(self, data):
        content = data.get("content", "")
        self.text.delete("1.0", "end")
        
        if content:
            self.text.insert("1.0", content)
        
        for tag in list(self.text.tag_names()):
            if tag not in ("sel", "current", "insert"):
                try:
                    self.text.tag_remove(tag, "1.0", "end")
                except Exception:
                    pass
        
        for tagobj in data.get("tags", []):
            name = tagobj.get("name")
            
            if name.startswith("color_") and not self.text.tag_cget(name, "foreground"):
                try:
                    col = "#" + name.split("_", 1)[1]
                    self.text.tag_configure(name, foreground=col)
                except Exception:
                    pass
            
            for (start, end) in tagobj.get("ranges", []):
                try:
                    self.text.tag_add(name, start, end)
                except Exception:
                    pass
        
        self._ensure_alignment_tags()
        self._modified_since_save = False

    def get_content_text(self):
        return self.text.get("1.0", "end-1c")

    def set_plain_text(self, txt):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", txt)
        self._ensure_alignment_tags()
        self._modified_since_save = False

    def start_autosave(self, callback, interval_ms=5000):
        self.stop_autosave()
        
        def _tick():
            try:
                if self._modified_since_save:
                    callback()
                    self._modified_since_save = False
                self._autosave_after_id = self.after(interval_ms, _tick)
            except Exception as e:
                logger.error(f"Autosave error: {e}")
                self._autosave_after_id = self.after(interval_ms, _tick)
                
        self._autosave_after_id = self.after(interval_ms, _tick)

    def stop_autosave(self):
        if self._autosave_after_id:
            try:
                self.after_cancel(self._autosave_after_id)
            except Exception:
                pass
            self._autosave_after_id = None


class ModernCategoryManager(ctk.CTkToplevel):
    """مدیریت دسته‌بندی‌ها با قابلیت کامل ویرایش و حذف"""
    
    def __init__(self, parent, categories, on_update_callback, language_manager=None):
        super().__init__(parent)
        
        self.categories = categories.copy()
        self.on_update_callback = on_update_callback
        
        self.title("مدیریت دسته‌بندی‌ها")
        self.geometry("550x650")
        self.minsize(550, 650)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self._center_window()
        self._create_ui()

    def _center_window(self):
        """مرکز کردن پنجره"""
        self.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        x = parent_x + (parent_width - 550) // 2
        y = parent_y + (parent_height - 650) // 2
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """ایجاد رابط کاربری"""
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # هدر
        header_frame = ctk.CTkFrame(self, fg_color=("#3498db", "#2980b9"), height=70)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=20, pady=12)
        
        ctk.CTkLabel(
            header_content,
            text="🗂️ مدیریت دسته‌بندی‌ها",
            font=ctk.CTkFont("Vazirmatn", size=16, weight="bold"),  # کاهش سایز فونت
            text_color="white"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_content,
            text="مدیریت کامل دسته‌بندی‌های یادداشت‌ها",
            font=ctk.CTkFont("Vazirmatn", size=12),  # کاهش سایز فونت
            text_color="white"
        ).pack(anchor="w", pady=(3, 0))

        # بخش افزودن دسته‌بندی جدید
        self._create_add_section()
        
        # لیست دسته‌بندی‌ها
        self._create_list_section()
        
        # دکمه‌های عمل
        self._create_action_buttons()
        
        # دکمه‌های پایین
        self._create_bottom_buttons()

    def _create_add_section(self):
        """بخش افزودن دسته‌بندی جدید"""
        add_frame = ctk.CTkFrame(self, fg_color=("#f8f9fa", "#2d2d2d"), height=90)
        add_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(15, 10))
        add_frame.grid_propagate(False)
        
        add_content = ctk.CTkFrame(add_frame, fg_color="transparent")
        add_content.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            add_content,
            text="افزودن دسته‌بندی جدید:",
            font=ctk.CTkFont("Vazirmatn", size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 6))
        
        input_frame = ctk.CTkFrame(add_content, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.new_category_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="نام دسته‌بندی جدید را وارد کنید...",
            height=36,
            font=ctk.CTkFont("Vazirmatn", size=12)
        )
        self.new_category_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.new_category_entry.bind("<Return>", lambda e: self._add_category())
        
        add_btn = ctk.CTkButton(
            input_frame,
            text="➕ افزودن",
            command=self._add_category,
            height=36,
            width=90,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=ctk.CTkFont("Vazirmatn", size=11, weight="bold")
        )
        add_btn.pack(side="right")

    def _create_list_section(self):
        """بخش لیست دسته‌بندی‌ها"""
        list_container = ctk.CTkFrame(self, fg_color="transparent")
        list_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        list_container.grid_rowconfigure(1, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        # هدر لیست
        list_header = ctk.CTkFrame(list_container, fg_color="transparent", height=40)
        list_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        list_header.grid_propagate(False)
        
        ctk.CTkLabel(
            list_header,
            text="لیست دسته‌بندی‌ها:",
            font=ctk.CTkFont("Vazirmatn", size=13, weight="bold")
        ).pack(side="left")

        self.count_label = ctk.CTkLabel(
            list_header,
            text=f"({len(self.categories)} مورد)",
            font=ctk.CTkFont("Vazirmatn", size=11),
            text_color=("#666666", "#aaaaaa")
        )
        self.count_label.pack(side="left", padx=(8, 0))

        # فریم لیست با اسکرول
        list_frame = ctk.CTkFrame(list_container)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # ایجاد فریم اسکرول‌شونده برای دسته‌بندی‌ها
        self.categories_scrollable = ctk.CTkScrollableFrame(
            list_frame,
            fg_color=("#ffffff", "#2d2d2d"),
            scrollbar_button_color=("#3498db", "#2980b9"),
            height=300
        )
        self.categories_scrollable.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # پر کردن لیست دسته‌بندی‌ها
        self._refresh_categories_list()

    def _refresh_categories_list(self):
        """بارگذاری مجدد لیست دسته‌بندی‌ها با دکمه‌های ویرایش و حذف"""
        # حذف ویجت‌های قدیمی
        for widget in self.categories_scrollable.winfo_children():
            widget.destroy()

        if not self.categories:
            # نمایش پیام وقتی دسته‌بندی‌ای وجود ندارد
            no_cat_label = ctk.CTkLabel(
                self.categories_scrollable,
                text="⚠️ هیچ دسته‌بندی‌ای وجود ندارد",
                font=ctk.CTkFont("Vazirmatn", size=13),
                text_color=("#95a5a6", "#7f8c8d")
            )
            no_cat_label.pack(pady=20)
        else:
            for idx, category in enumerate(self.categories):
                self._create_category_item(category, idx)

    def _create_category_item(self, category, index):
        """ایجاد آیتم دسته‌بندی با دکمه‌های ویرایش و حذف"""
        # فریم اصلی هر دسته‌بندی
        item_frame = ctk.CTkFrame(
            self.categories_scrollable,
            corner_radius=8,
            fg_color=("#ffffff", "#2d2d2d"),
            border_width=1,
            border_color=("#e0e0e0", "#404040")
        )
        item_frame.pack(fill="x", pady=3, padx=2)

        # محتوای داخلی
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=8)

        # سطر اول: نام دسته‌بندی و دکمه‌ها
        top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_frame.pack(fill="x")

        # نام دسته‌بندی
        name_label = ctk.CTkLabel(
            top_frame,
            text=category,
            font=ctk.CTkFont("Vazirmatn", size=13, weight="bold"),
            text_color=("#2c3e50", "#ecf0f1"),
            anchor="w"
        )
        name_label.pack(side="right", fill="x", expand=True)

        # دکمه‌های عمل
        button_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        button_frame.pack(side="left")

        # دکمه ویرایش
        edit_btn = ctk.CTkButton(
            button_frame,
            text="✏️",
            width=35,
            height=28,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=ctk.CTkFont(size=11),
            command=lambda c=category, i=index: self._edit_category(c, i)
        )
        edit_btn.pack(side="left", padx=(4, 2))

        # دکمه حذف
        delete_btn = ctk.CTkButton(
            button_frame,
            text="🗑️",
            width=35,
            height=28,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=ctk.CTkFont(size=11),
            command=lambda c=category, i=index: self._delete_category(c, i)
        )
        delete_btn.pack(side="left", padx=(2, 4))

        # افکت هاور
        def on_enter(e):
            item_frame.configure(fg_color=("#f0f0f0", "#3d3d3d"))
            
        def on_leave(e):
            item_frame.configure(fg_color=("#ffffff", "#2d2d2d"))
            
        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)
        
        # هاور برای تمام ویجت‌های داخلی
        for widget in [item_frame, content_frame, top_frame, name_label, button_frame, edit_btn, delete_btn]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def _create_action_buttons(self):
        """دکمه‌های عمل"""
        button_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=8)
        button_frame.grid_propagate(False)

        action_buttons = [
            ("📊 نمایش آمار", self._show_stats, "#9b59b6"),
            ("🔄 بارگذاری مجدد", self._refresh_categories_list, "#95a5a6")
        ]

        for i, (text, command, color) in enumerate(action_buttons):
            btn = ctk.CTkButton(
                button_frame,
                text=text,
                command=command,
                height=34,
                fg_color=color,
                font=ctk.CTkFont("Vazirmatn", size=11, weight="bold"),
                corner_radius=6
            )
            btn.grid(row=0, column=i, padx=3, sticky="ew")
            button_frame.grid_columnconfigure(i, weight=1)

    def _create_bottom_buttons(self):
        """دکمه‌های پایین"""
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        bottom_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=15)
        bottom_frame.grid_propagate(False)
        
        # استفاده از pack برای centering
        inner_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        inner_frame.pack(expand=True)
        
        ctk.CTkButton(
            inner_frame,
            text="💾 ذخیره تغییرات",
            command=self._save_and_close,
            height=38,
            width=130,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=ctk.CTkFont("Vazirmatn", size=12, weight="bold")
        ).pack(side="left", padx=8)
        
        ctk.CTkButton(
            inner_frame,
            text="❌ انصراف",
            command=self.destroy,
            height=38,
            width=130,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            font=ctk.CTkFont("Vazirmatn", size=12)
        ).pack(side="left", padx=8)

    def _update_count_label(self):
        """به‌روزرسانی برچسب تعداد"""
        count = len(self.categories)
        self.count_label.configure(text=f"({count} مورد)")

    def _add_category(self):
        """افزودن دسته‌بندی جدید"""
        name = self.new_category_entry.get().strip()
        
        if not name:
            messagebox.showwarning("هشدار", "لطفاً نام دسته‌بندی را وارد کنید")
            self.new_category_entry.focus()
            return
            
        if name in self.categories:
            messagebox.showwarning("هشدار", "این دسته‌بندی قبلاً وجود دارد")
            self.new_category_entry.select_range(0, tk.END)
            self.new_category_entry.focus()
            return
        
        # افزودن به لیست
        self.categories.append(name)
        
        # به‌روزرسانی UI
        self._refresh_categories_list()
        self._update_count_label()
        self.new_category_entry.delete(0, tk.END)
        
        messagebox.showinfo("موفقیت", f"دسته‌بندی '{name}' با موفقیت افزوده شد")

    def _edit_category(self, category, index):
        """ویرایش دسته‌بندی"""
        new_name = simpledialog.askstring(
            "ویرایش دسته‌بندی", 
            f"نام جدید برای دسته‌بندی '{category}':",
            initialvalue=category,
            parent=self
        )
        
        if not new_name or not new_name.strip():
            return
            
        new_name = new_name.strip()
        
        if new_name == category:
            return
            
        if new_name in self.categories:
            messagebox.showwarning("هشدار", "این دسته‌بندی قبلاً وجود دارد")
            return

        # به‌روزرسانی در لیست
        self.categories[index] = new_name
        
        # به‌روزرسانی UI
        self._refresh_categories_list()
        self._update_count_label()
        
        messagebox.showinfo("موفقیت", f"دسته‌بندی به '{new_name}' تغییر یافت")

    def _delete_category(self, category, index):
        """حذف دسته‌بندی"""
        # تأیید حذف
        result = messagebox.askyesno(
            "تأیید حذف", 
            f"آیا از حذف دسته‌بندی '{category}' اطمینان دارید؟\n\nاین عمل غیرقابل بازگشت است.",
            icon='warning',
            parent=self
        )
        
        if not result:
            return
        
        # حذف از لیست
        deleted_category = self.categories.pop(index)
        
        # به‌روزرسانی UI
        self._refresh_categories_list()
        self._update_count_label()
        
        messagebox.showinfo("موفقیت", f"دسته‌بندی '{deleted_category}' حذف شد")

    def _show_stats(self):
        """نمایش آمار دسته‌بندی‌ها"""
        if not self.categories:
            messagebox.showinfo("آمار", "هیچ دسته‌بندی‌ای وجود ندارد")
            return
        
        stats_text = f"📊 آمار دسته‌بندی‌ها\n\n"
        stats_text += f"• تعداد کل: {len(self.categories)} دسته‌بندی\n\n"
        stats_text += f"• لیست دسته‌بندی‌ها:\n"
        
        for i, category in enumerate(self.categories, 1):
            stats_text += f"  {i}. {category}\n"
        
        messagebox.showinfo("آمار دسته‌بندی‌ها", stats_text)

    def _save_and_close(self):
        """ذخیره تغییرات و بستن پنجره"""
        try:
            # اعتبارسنجی نام‌های تکراری
            if len(self.categories) != len(set(self.categories)):
                messagebox.showerror("خطا", "نام‌های تکراری در لیست دسته‌بندی‌ها وجود دارد")
                return
            
            # فراخوانی کالبک برای به‌روزرسانی
            self.on_update_callback(self.categories)
            
            messagebox.showinfo("موفقیت", "تغییرات با موفقیت ذخیره شد")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ذخیره تغییرات: {str(e)}")


class NotesModule(BaseModule):
    """ماژول مدیریت یادداشت‌ها با UI فشرده و بهینه"""
    
    def __init__(self, parent, app, config):
        try:
            super().__init__(parent, app=app, config=config, fg_color="transparent")
        except TypeError:
            BaseModule.__init__(self, parent, app=app, config=config)

        self.parent = parent
        self.app = app
        self.config = config or {}
        self.logger = logger
        self.language_manager = getattr(app, 'language_manager', None)

        # وضعیت
        self.notes = []
        self.categories = []
        self.current_filter = "همه"
        self.search_term = ""
        self.note_widgets = []
        self.selected_note = None
        self.selected_note_id = None  # ID یادداشت انتخاب شده
        self.is_editor_visible = False  # وضعیت نمایش ادیتور

        # استفاده از دیتابیس جداگانه برای یادداشت‌ها
        self.db = NotesDatabase()
        
        # مقداردهی اولیه
        self._load_categories()
        self._build_optimized_ui()
        self.load_notes()
        # autosave فقط وقتی فعال می‌شود که ادیتور نمایش داده شود

        self.logger.info("✅ NotesModule initialized با دیتابیس جداگانه و UI بهبود یافته")

    def _load_categories(self):
        """بارگذاری دسته‌بندی‌ها از دیتابیس جداگانه"""
        try:
            results = self.db.fetch_all("SELECT name FROM categories ORDER BY name")
            self.categories = [row[0] for row in results] if results else ["عمومی", "شخصی", "کار"]
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری دسته‌بندی‌ها: {e}")
            self.categories = ["عمومی", "شخصی", "کار"]

    def _save_categories(self):
        """ذخیره دسته‌بندی‌ها در دیتابیس جداگانه"""
        try:
            # حذف دسته‌بندی‌های قدیمی
            self.db.execute_query("DELETE FROM categories")
            
            # درج دسته‌بندی‌های جدید
            for category in self.categories:
                self.db.execute_query(
                    "INSERT INTO categories (name) VALUES (?)",
                    (category,)
                )
        except Exception as e:
            self.logger.error(f"خطا در ذخیرهٔ دسته‌بندی‌ها: {e}")

    def _build_optimized_ui(self):
        """ساخت رابط کاربری بهینه و فشرده"""
        self._clear_existing_widgets()
        self._setup_main_layout()
        self._create_compact_sidebar()
        self._create_compact_editor()

    def _clear_existing_widgets(self):
        for w in self.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def _setup_main_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _create_compact_sidebar(self):
        """ایجاد نوار کناری فشرده با عرض بیشتر"""
        sidebar = ctk.CTkFrame(self, width=480, corner_radius=0,
                              fg_color=("#f8f9fa", "#252525"))
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1), pady=0)
        sidebar.grid_propagate(False)
        
        # ساخت layout شبکه‌ای برای کنترل بهتر فاصله‌ها
        sidebar.grid_rowconfigure(0, weight=0)  # هدر
        sidebar.grid_rowconfigure(1, weight=0)  # فیلترها
        sidebar.grid_rowconfigure(2, weight=1)  # لیست یادداشت‌ها

        # هدر - ارتفاع بیشتر
        header_frame = ctk.CTkFrame(sidebar, fg_color=("#3498db", "#2980b9"), height=80)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=18, pady=15)

        # عنوان و دکمه در یک خط
        top_row = ctk.CTkFrame(header_content, fg_color="transparent")
        top_row.pack(fill="x", pady=0)
        
        ctk.CTkLabel(
            top_row, 
            text="📝 یادداشت‌ها", 
            font=ctk.CTkFont("Vazirmatn", size=18, weight="bold"),  # کاهش سایز فونت
            text_color="white"
        ).pack(side="left", pady=0)
        
        # دکمه با متن کامل
        ctk.CTkButton(
            top_row,
            text="➕ یادداشت جدید",
            command=self.create_new_note,
            height=38,
            width=130,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            corner_radius=8,
            font=ctk.CTkFont("Vazirmatn", size=13, weight="bold")  # کاهش سایز فونت
        ).pack(side="right", pady=0)

        # بخش فیلترها
        filter_container = ctk.CTkFrame(sidebar, fg_color="transparent", height=150)
        filter_container.grid(row=1, column=0, sticky="ew", padx=15, pady=(12, 8))
        filter_container.grid_propagate(False)

        # جستجو
        self.search_entry = ctk.CTkEntry(
            filter_container,
            placeholder_text="🔍 جستجو در یادداشت‌ها...",
            height=42,
            corner_radius=8,
            font=ctk.CTkFont("Vazirmatn", size=13)  # کاهش سایز فونت
        )
        self.search_entry.pack(fill="x", pady=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        # سطر آمار و مدیریت
        stats_manage_row = ctk.CTkFrame(filter_container, fg_color="transparent")
        stats_manage_row.pack(fill="x", pady=(0, 12))
        
        self.stats_label = ctk.CTkLabel(
            stats_manage_row,
            text="",
            font=ctk.CTkFont("Vazirmatn", size=12),  # کاهش سایز فونت
            text_color=("#666666", "#aaaaaa")
        )
        self.stats_label.pack(side="left")
        
        # دکمه مدیریت
        manage_btn = ctk.CTkButton(
            stats_manage_row,
            text="⚙️ مدیریت دسته‌بندی‌ها",
            command=self._manage_categories,
            height=35,
            width=150,
            fg_color="transparent",
            hover_color=("#e74c3c", "#c0392b"),
            font=ctk.CTkFont("Vazirmatn", size=11),  # کاهش سایز فونت
            text_color=("#e74c3c", "#e74c3c"),
            border_width=1,
            border_color=("#e74c3c", "#c0392b")
        )
        manage_btn.pack(side="right")

        # دسته‌بندی
        category_frame = ctk.CTkFrame(filter_container, fg_color="transparent")
        category_frame.pack(fill="x", pady=(0, 0))

        ctk.CTkLabel(
            category_frame,
            text="دسته‌بندی:",
            font=ctk.CTkFont("Vazirmatn", size=13, weight="bold"),  # کاهش سایز فونت
            text_color=("#2c3e50", "#ecf0f1")
        ).pack(anchor="w", pady=(0, 8))
        
        category_values = ["همه"] + self.categories
        self.filter_combo = ctk.CTkComboBox(
            category_frame,
            values=category_values,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont("Vazirmatn", size=12),  # کاهش سایز فونت
            dropdown_font=ctk.CTkFont("Vazirmatn", size=12)  # کاهش سایز فونت
        )
        self.filter_combo.set("همه")
        self.filter_combo.pack(fill="x")
        self.filter_combo.configure(command=self._on_filter_changed)

        # لیست یادداشت‌ها
        self.notes_list_frame = ctk.CTkScrollableFrame(
            sidebar, 
            fg_color=("#ffffff", "#1e1e1e"),
            scrollbar_button_color=("#3498db", "#2980b9"),
            border_width=0
        )
        self.notes_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.empty_label = ctk.CTkLabel(
            self.notes_list_frame,
            text="📝\nهیچ یادداشتی وجود ندارد\n\nبرای شروع روی دکمه 'یادداشت جدید' کلیک کنید",
            font=ctk.CTkFont("Vazirmatn", size=13),  # کاهش سایز فونت
            text_color=("#95a5a6", "#7f8c8d"),
            justify="center"
        )
        self.empty_label.pack(pady=30)

    def _create_compact_editor(self):
        """ایجاد بخش ویرایشگر با قابلیت نمایش/پنهان‌سازی"""
        self.editor_main = ctk.CTkFrame(self, fg_color="transparent")
        self.editor_main.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        self.editor_main.grid_rowconfigure(1, weight=1)
        self.editor_main.grid_columnconfigure(0, weight=1)

        # ایجاد پلیس‌هولدر برای زمانی که هیچ یادداشتی انتخاب نشده
        self._create_editor_placeholder()
        
        self._create_compact_editor_header()
        self._create_compact_text_editor()
        
        # در ابتدا ادیتور رو پنهان می‌کنیم
        self._hide_editor()

    def _create_editor_placeholder(self):
        """ایجاد پلیس‌هولدر برای زمانی که ادیتور نمایش داده نمی‌شود"""
        self.placeholder_frame = ctk.CTkFrame(
            self.editor_main, 
            fg_color=("#f8f9fa", "#252525"),
            corner_radius=12
        )
        self.placeholder_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        
        placeholder_content = ctk.CTkFrame(self.placeholder_frame, fg_color="transparent")
        placeholder_content.pack(expand=True, fill="both", padx=20, pady=40)
        
        # آیکون و متن پلیس‌هولدر
        ctk.CTkLabel(
            placeholder_content,
            text="📝",
            font=ctk.CTkFont(size=64),
            text_color=("#bdc3c7", "#7f8c8d")
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            placeholder_content,
            text="یادداشت‌های شما اینجا نمایش داده می‌شوند",
            font=ctk.CTkFont("Vazirmatn", size=16, weight="bold"),  # کاهش سایز فونت
            text_color=("#95a5a6", "#7f8c8d")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            placeholder_content,
            text="برای شروع، یک یادداشت جدید ایجاد کنید یا از لیست سمت راست یک یادداشت را انتخاب نمایید.",
            font=ctk.CTkFont("Vazirmatn", size=13),  # کاهش سایز فونت
            text_color=("#bdc3c7", "#7f8c8d"),
            wraplength=400,
            justify="center"
        ).pack(pady=(0, 30))
        
        ctk.CTkButton(
            placeholder_content,
            text="➕ ایجاد یادداشت جدید",
            command=self.create_new_note,
            height=45,
            width=200,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=ctk.CTkFont("Vazirmatn", size=13, weight="bold"),  # کاهش سایز فونت
            corner_radius=8
        ).pack()

    def _hide_editor(self):
        """پنهان کردن ادیتور و نمایش پلیس‌هولدر"""
        self.is_editor_visible = False
        # پنهان کردن بخش‌های ادیتور
        for widget in self.editor_main.winfo_children():
            if widget != self.placeholder_frame:
                widget.grid_remove()
        
        # نمایش پلیس‌هولدر
        self.placeholder_frame.grid()
        
        # توقف autosave
        if hasattr(self, 'editor') and hasattr(self.editor, 'stop_autosave'):
            self.editor.stop_autosave()

    def _show_editor(self):
        """نمایش ادیتور و پنهان کردن پلیس‌هولدر"""
        self.is_editor_visible = True
        # پنهان کردن پلیس‌هولدر
        self.placeholder_frame.grid_remove()
        
        # نمایش بخش‌های ادیتور
        for widget in self.editor_main.winfo_children():
            if widget != self.placeholder_frame:
                widget.grid()
        
        # راه‌اندازی autosave
        self._setup_autosave()

    def _create_compact_editor_header(self):
        """ایجاد هدر ویرایشگر با ارتفاع بیشتر"""
        self.editor_header = ctk.CTkFrame(self.editor_main, height=85, fg_color=("#ffffff", "#2b2b2b"))
        self.editor_header.grid(row=0, column=0, sticky="ew", pady=(0, 1))
        self.editor_header.grid_propagate(False)
        
        header_content = ctk.CTkFrame(self.editor_header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=15, pady=12)

        # بخش چپ - دکمه‌های عمل
        left_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        left_frame.pack(side="left")
        
        action_buttons = [
            ("💾 ذخیره", self.save_current_note, "#27ae60"),
            ("🗑️ حذف", self.delete_current_note, "#e74c3c"),
        ]

        for text, command, color in action_buttons:
            btn = ctk.CTkButton(
                left_frame,
                text=text,
                command=command,
                width=100,
                height=40,
                fg_color=color,
                font=ctk.CTkFont("Vazirmatn", size=12, weight="bold"),  # کاهش سایز فونت
                corner_radius=8
            )
            btn.pack(side="left", padx=5)

        # بخش وسط - عنوان
        middle_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        middle_frame.pack(side="left", fill="x", expand=True, padx=15)
        
        self.title_entry = ctk.CTkEntry(
            middle_frame,
            placeholder_text="عنوان یادداشت...",
            height=42,
            corner_radius=8,
            font=ctk.CTkFont("Vazirmatn", size=14),  # کاهش سایز فونت
            border_width=1
        )
        self.title_entry.pack(fill="x", expand=True)

        # بخش راست - دسته‌بندی
        right_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        right_frame.pack(side="right")
        
        self.category_combo = ctk.CTkComboBox(
            right_frame,
            values=self.categories,
            width=160,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont("Vazirmatn", size=12)  # کاهش سایز فونت
        )
        if self.categories:
            self.category_combo.set(self.categories[0])
        self.category_combo.pack(side="left")

    def _create_compact_text_editor(self):
        """ایجاد ویرایشگر متن با فضای بیشتر"""
        try:
            editor_container = ctk.CTkFrame(self.editor_main, fg_color=("#ffffff", "#1a1a1a"))
            editor_container.grid(row=1, column=0, sticky="nsew")
            editor_container.grid_rowconfigure(0, weight=1)
            editor_container.grid_columnconfigure(0, weight=1)

            self.editor = ModernTextEditor(
                editor_container,
                default_family=self.config.get("font_family", "Vazirmatn"),
                default_size=self.config.get("font_size", 12)  # کاهش سایز فونت پایه
            )
            self.editor.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
        except Exception as e:
            logger.error(f"خطا در ایجاد ویرایشگر: {e}")
            self._create_fallback_editor(editor_container)

    def _create_fallback_editor(self, parent):
        """ویرایشگر ساده جایگزین در صورت بروز خطا"""
        fallback_frame = ctk.CTkFrame(parent, fg_color="transparent")
        fallback_frame.grid(row=0, column=0, sticky="nsew")
        
        # فریم اصلی برای ویرایشگر ساده
        editor_frame = ctk.CTkFrame(fallback_frame, fg_color=("#ffffff", "#1e1e1e"))
        editor_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        # اسکرول‌بار عمودی
        v_scroll = ttk.Scrollbar(editor_frame)
        v_scroll.pack(side="right", fill="y")
        
        # ویرایشگر ساده
        simple_editor = tk.Text(
            editor_frame,
            wrap="word",
            font=("Vazirmatn", self.config.get("font_size", 12)),  # کاهش سایز فونت
            padx=20,
            pady=20,
            yscrollcommand=v_scroll.set,
            borderwidth=0,
            relief="flat",
            bg='#ffffff' if ctk.get_appearance_mode() == "Light" else '#1e1e1e',
            fg='#2c3e50' if ctk.get_appearance_mode() == "Light" else '#ecf0f1',
            selectbackground='#3498db',
            insertbackground='#e74c3c'
        )
        simple_editor.pack(fill="both", expand=True)
        
        v_scroll.configure(command=simple_editor.yview)
        
        # تنظیم تگ راست‌چین برای ویرایشگر ساده
        simple_editor.tag_configure("right", justify="right")
        simple_editor.tag_add("right", "1.0", "end")
        
        self.editor = simple_editor
        self.editor.get_content_text = lambda: self.editor.get("1.0", "end-1c")
        self.editor.set_plain_text = lambda txt: self.editor.delete("1.0", "end") or self.editor.insert("1.0", txt)
        self.editor.get_serialized_format = lambda: {"content": self.editor.get("1.0", "end-1c")}
        self.editor.set_content_from_serialized = lambda data: self.editor.set_plain_text(data.get("content", ""))
        self.editor.start_autosave = lambda *args, **kwargs: None
        self.editor.stop_autosave = lambda: None

    def _manage_categories(self):
        """مدیریت دسته‌بندی‌ها با قابلیت ویرایش و حذف"""
        try:
            # ایجاد کپی از دسته‌بندی‌ها برای مدیریت
            current_categories = self.categories.copy()
            
            # ایجاد پنجره مدیریت دسته‌بندی
            dialog = ModernCategoryManager(
                self, 
                current_categories, 
                self._on_categories_updated
            )
            
            # منتظر بسته شدن پنجره بمان
            self.wait_window(dialog)
            
        except Exception as e:
            self.logger.error(f"خطا در باز کردن مدیریت دسته‌بندی: {e}")
            messagebox.showerror("خطا", f"خطا در باز کردن مدیریت دسته‌بندی: {e}")
    
    def _on_categories_updated(self, new_categories):
        """به‌روزرسانی دسته‌بندی‌ها پس از مدیریت"""
        try:
            self.categories = new_categories
            self._save_categories()
            self._update_category_combos()
            self._refresh_notes_list()
            messagebox.showinfo("موفقیت", "دسته‌بندی‌ها با موفقیت به‌روزرسانی شدند")
        except Exception as e:
            self.logger.error(f"خطا در به‌روزرسانی دسته‌بندی‌ها: {e}")
            messagebox.showerror("خطا", f"خطا در به‌روزرسانی دسته‌بندی‌ها: {e}")

    def _update_category_combos(self):
        """به‌روزرسانی کامبوباکس‌های دسته‌بندی"""
        try:
            # به‌روزرسانی فیلتر دسته‌بندی
            category_values = ["همه"] + self.categories
            self.filter_combo.configure(values=category_values)
            
            # به‌روزرسانی کامبوباکس دسته‌بندی در ویرایشگر
            self.category_combo.configure(values=self.categories)
            
            # اگر دسته‌بندی انتخاب شده حذف شده باشد، به اولین دسته‌بندی تغییر می‌دهیم
            current_category = self.category_combo.get()
            if current_category not in self.categories and self.categories:
                self.category_combo.set(self.categories[0])
                
        except Exception as e:
            self.logger.error(f"خطا در به‌روزرسانی کامبوباکس‌ها: {e}")

    def load_notes(self):
        """بارگذاری یادداشت‌ها از دیتابیس جداگانه"""
        try:
            query = '''
                SELECT id, title, content, category, tags, created_at, updated_at, format_json, is_pinned
                FROM notes 
                ORDER BY is_pinned DESC, updated_at DESC
            '''
            rows = self.db.fetch_all(query)
            self.notes = []
            
            for row in rows:
                fmt = None
                try:
                    fmt = json.loads(row[7]) if row[7] else None
                except Exception:
                    fmt = None
                
                self.notes.append({
                    'id': row[0],
                    'title': row[1] or "بدون عنوان",
                    'content': row[2] or '',
                    'category': row[3] or 'عمومی',
                    'tags': row[4] or '',
                    'created_at': row[5] or '',
                    'updated_at': row[6] or '',
                    'format': fmt,
                    'is_pinned': bool(row[8])
                })
                
            self._refresh_notes_list()
            self.logger.info(f"✅ {len(self.notes)} یادداشت از دیتابیس جداگانه بارگذاری شد")
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری یادداشت‌ها: {e}")
            messagebox.showerror("خطا", f"خطا در بارگذاری یادداشت‌ها: {e}")

    def _refresh_notes_list(self):
        """بارگذاری مجدد لیست یادداشت‌ها"""
        try:
            # حذف ویجت‌های قدیمی
            for w in self.note_widgets:
                try:
                    w.destroy()
                except Exception:
                    pass
            self.note_widgets = []

            # فیلتر کردن یادداشت‌ها
            filtered = self._get_filtered_notes()
            
            # نمایش پیام خالی یا لیست یادداشت‌ها
            if not filtered:
                self.empty_label.pack(pady=40)
            else:
                self.empty_label.pack_forget()
                for i, note in enumerate(filtered):
                    self._create_compact_note_card(note, i)
            
            # به‌روزرسانی آمار
            self._update_stats()
        except Exception as e:
            self.logger.error(f"خطا در بارگذاری مجدد لیست: {e}")

    def _get_filtered_notes(self):
        """دریافت یادداشت‌های فیلتر شده"""
        filtered = self.notes
        
        if self.current_filter != "همه":
            filtered = [n for n in filtered if n.get('category') == self.current_filter]
        
        if self.search_term:
            s = self.search_term.lower()
            filtered = [
                n for n in filtered 
                if s in (n.get('title', '').lower() + " " + (n.get('content', '') or '').lower())
            ]
        
        return filtered

    def _create_compact_note_card(self, note, index):
        """ایجاد کارت نمایش یادداشت با افکت هاور و highlight انتخاب شده"""
        try:
            # بررسی آیا این یادداشت انتخاب شده است
            is_selected = self.selected_note_id == note['id']
            
            # رنگ‌های متفاوت برای حالت‌های مختلف
            if is_selected:
                # حالت انتخاب شده - highlight ویژه
                bg_color = ("#e3f2fd", "#1e3a5f")
                border_color = ("#3498db", "#2980b9")
                text_color = ("#2c3e50", "#ecf0f1")
            elif note.get('is_pinned'):
                # حالت سنجاق شده
                bg_color = ("#fff3cd", "#856404")
                border_color = ("#ffeaa7", "#f39c12")
                text_color = ("#2c3e50", "#ecf0f1")
            else:
                # حالت عادی
                bg_color = ("#ffffff", "#2d2d2d") if index % 2 == 0 else ("#f8f9fa", "#252525")
                border_color = ("#e0e0e0", "#404040")
                text_color = ("#2c3e50", "#ecf0f1")
            
            hover_color = ("#e3f2fd", "#3d3d3d") if not is_selected else ("#d4e6f1", "#2a4d6e")
            hover_border_color = ("#3498db", "#2980b9")

            item_frame = ctk.CTkFrame(
                self.notes_list_frame,
                corner_radius=8,
                fg_color=bg_color[0] if ctk.get_appearance_mode() == "Light" else bg_color[1],
                border_width=2 if is_selected else 1,
                border_color=border_color[0] if ctk.get_appearance_mode() == "Light" else border_color[1]
            )
            item_frame.pack(fill="x", pady=6, padx=8)
            item_frame.note_id = note['id']

            def on_enter(e):
                if not is_selected:  # فقط اگر انتخاب شده نیست، هاور اعمال شود
                    item_frame.configure(
                        fg_color=hover_color[0] if ctk.get_appearance_mode() == "Light" else hover_color[1],
                        border_color=hover_border_color[0] if ctk.get_appearance_mode() == "Light" else hover_border_color[1]
                    )
                
            def on_leave(e):
                if not is_selected:  # فقط اگر انتخاب شده نیست، به حالت عادی برگردد
                    item_frame.configure(
                        fg_color=bg_color[0] if ctk.get_appearance_mode() == "Light" else bg_color[1],
                        border_color=border_color[0] if ctk.get_appearance_mode() == "Light" else border_color[1]
                    )

            # افکت هاور برای فریم اصلی
            item_frame.bind("<Enter>", on_enter)
            item_frame.bind("<Leave>", on_leave)

            content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            content_frame.pack(fill="x", padx=15, pady=12)

            # هدر کارت
            header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            header_frame.pack(fill="x", pady=(0, 10))

            # عنوان
            title_label = ctk.CTkLabel(
                header_frame,
                text=note['title'],
                font=ctk.CTkFont("Vazirmatn", size=15, weight="bold"),  # کاهش سایز فونت
                text_color=text_color[0] if ctk.get_appearance_mode() == "Light" else text_color[1],
                anchor="w",
                justify="right"
            )
            title_label.pack(side="right", fill="x", expand=True)

            # آیکون سنجاق
            if note.get('is_pinned'):
                pin_label = ctk.CTkLabel(
                    header_frame,
                    text="📌",
                    font=ctk.CTkFont(size=13),  # کاهش سایز فونت
                    text_color=("#f39c12", "#f39c12")
                )
                pin_label.pack(side="left", padx=(0, 10))

            # دسته‌بندی
            category_label = ctk.CTkLabel(
                header_frame,
                text=note['category'],
                font=ctk.CTkFont("Vazirmatn", size=11),  # کاهش سایز فونت
                text_color=("#ffffff", "#ffffff"),
                corner_radius=10,
                fg_color=("#3498db", "#2980b9"),
                padx=10,
                pady=5
            )
            category_label.pack(side="left", padx=(4, 0))

            # پیش‌نمایش محتوا
            if note['content']:
                content_preview = note['content'].strip()
                if len(content_preview) > 120:
                    content_preview = content_preview[:120] + "..."
                    
                content_label = ctk.CTkLabel(
                    content_frame,
                    text=content_preview,
                    font=ctk.CTkFont("Vazirmatn", size=12),  # کاهش سایز فونت
                    text_color=("#7f8c8d", "#bdc3c7"),
                    anchor="w",
                    justify="right",
                    wraplength=400
                )
                content_label.pack(fill="x", pady=(0, 10))

            # فوتر - تاریخ
            footer_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            footer_frame.pack(fill="x")

            date_text = ""
            if note['updated_at']:
                try:
                    date_obj = datetime.strptime(note['updated_at'], '%Y-%m-%d %H:%M:%S')
                    date_text = date_obj.strftime('%Y/%m/%d %H:%M')
                except Exception:
                    date_text = note['updated_at'].split(' ')[0]

            date_label = ctk.CTkLabel(
                footer_frame,
                text=date_text,
                font=ctk.CTkFont("Vazirmatn", size=11),  # کاهش سایز فونت
                text_color=("#95a5a6", "#7f8c8d")
            )
            date_label.pack(side="left")

            # آیکون انتخاب شده (فقط اگر انتخاب شده باشد)
            if is_selected:
                selected_indicator = ctk.CTkLabel(
                    footer_frame,
                    text="✓ در حال ویرایش",
                    font=ctk.CTkFont("Vazirmatn", size=11, weight="bold"),  # کاهش سایز فونت
                    text_color=("#27ae60", "#2ecc71")
                )
                selected_indicator.pack(side="right", padx=(0, 5))

            # رویداد کلیک
            def on_click(event, n=note):
                self.select_note(n)
            
            # اعمال افکت هاور و کلیک برای تمام ویجت‌های داخلی
            widgets_to_bind = [item_frame, content_frame, header_frame, title_label, 
                              category_label, pin_label if note.get('is_pinned') else None,
                              content_label if note['content'] else None, footer_frame, date_label,
                              selected_indicator if is_selected else None]
            
            for widget in widgets_to_bind:
                if widget:
                    if not is_selected:  # فقط برای آیتم‌های غیر انتخاب شده هاور اعمال شود
                        widget.bind("<Enter>", on_enter)
                        widget.bind("<Leave>", on_leave)
                    widget.bind("<Button-1>", on_click)

            self.note_widgets.append(item_frame)
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد کارت یادداشت: {e}")

    def select_note(self, note):
        """انتخاب یک یادداشت برای نمایش و ویرایش"""
        try:
            # ذخیره ID یادداشت انتخاب شده
            self.selected_note_id = note['id']
            self.selected_note = note
            
            # نمایش ادیتور
            self._show_editor()
            
            # به‌روزرسانی عنوان
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, note.get('title', "بدون عنوان"))
            
            # به‌روزرسانی دسته‌بندی
            if note.get('category'):
                try:
                    self.category_combo.set(note['category'])
                except Exception:
                    if self.categories:
                        self.category_combo.set(self.categories[0])

            # به‌روزرسانی محتوا
            if hasattr(self.editor, 'set_content_from_serialized'):
                if note.get('format'):
                    try:
                        self.editor.set_content_from_serialized(note['format'])
                    except Exception:
                        self.editor.set_plain_text(note.get('content', ''))
                else:
                    self.editor.set_plain_text(note.get('content', ''))
            else:
                self.editor.set_plain_text(note.get('content', ''))

            # بارگذاری مجدد لیست برای highlight کردن آیتم انتخاب شده
            self._refresh_notes_list()

            # فوکوس روی ویرایشگر
            try:
                if hasattr(self.editor, 'text'):
                    self.editor.text.focus_set()
                else:
                    self.editor.focus_set()
            except Exception:
                pass

        except Exception as e:
            self.logger.error(f"خطا در انتخاب یادداشت: {e}")
            messagebox.showerror("خطا", f"خطا در انتخاب یادداشت: {e}")

    def create_new_note(self):
        """ایجاد یک یادداشت جدید"""
        try:
            new_note = {
                'id': None,
                'title': "یادداشت جدید",
                'content': '',
                'category': self.categories[0] if self.categories else 'عمومی',
                'tags': '',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'format': None,
                'is_pinned': False
            }
            
            self.notes.insert(0, new_note)
            self._refresh_notes_list()
            self.select_note(new_note)
            
            # فوکوس روی عنوان و انتخاب متن
            self.title_entry.focus()
            self.title_entry.select_range(0, "end")
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد یادداشت جدید: {e}")
            messagebox.showerror("خطا", f"خطا در ایجاد یادداشت جدید: {e}")

    def save_current_note(self):
        """ذخیره یادداشت جاری"""
        try:
            if not self.selected_note:
                messagebox.showwarning("هشدار", "هیچ یادداشتی انتخاب نشده است")
                return
                
            title = self.title_entry.get().strip()
            if not title:
                messagebox.showerror("خطا", "لطفاً عنوان یادداشت را وارد کنید")
                self.title_entry.focus()
                return
            
            category = self.category_combo.get() or (self.categories[0] if self.categories else "عمومی")
            tags = ""
            
            # دریافت محتوای فرمت‌بندی شده یا ساده
            if hasattr(self.editor, 'get_serialized_format'):
                serialized = self.editor.get_serialized_format()
                content_plain = serialized.get("content", "")
                format_json = json.dumps(serialized, ensure_ascii=False, indent=2)
            else:
                content_plain = self.editor.get_content_text()
                format_json = json.dumps({"content": content_plain}, ensure_ascii=False, indent=2)
            
            # ذخیره در دیتابیس
            if self.selected_note.get('id'):
                # به‌روزرسانی یادداشت موجود
                self.db.execute_query('''
                    UPDATE notes 
                    SET title=?, content=?, category=?, tags=?, updated_at=CURRENT_TIMESTAMP, format_json=?
                    WHERE id=?
                ''', (title, content_plain, category, tags, format_json, self.selected_note['id']))
                self.logger.info(f"یادداشت با ID {self.selected_note['id']} به‌روزرسانی شد")
            else:
                # درج یادداشت جدید
                cursor = self.db.execute_query('''
                    INSERT INTO notes (title, content, category, tags, format_json)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, content_plain, category, tags, format_json))
                self.selected_note['id'] = cursor.lastrowid
                self.logger.info(f"یادداشت جدید با ID {self.selected_note['id']} ایجاد شد")

            # پارس کردن فرمت JSON
            try:
                serialized_data = json.loads(format_json) if format_json else {"content": content_plain}
            except json.JSONDecodeError:
                serialized_data = {"content": content_plain}

            # به‌روزرسانی یادداشت در حافظه
            self.selected_note.update({
                'title': title,
                'content': content_plain,
                'category': category,
                'tags': tags,
                'format': serialized_data,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            # اگر دسته‌بندی جدیدی اضافه شده، ذخیره شود
            if category not in self.categories:
                self.categories.append(category)
                self._save_categories()
                self._update_category_combos()

            # بارگذاری مجدد لیست
            self._refresh_notes_list()
            messagebox.showinfo("موفقیت", "یادداشت با موفقیت ذخیره شد")
            
        except Exception as e:
            self.logger.error(f"خطا در ذخیره یادداشت: {e}")
            messagebox.showerror("خطا", f"خطا در ذخیره یادداشت: {e}")

    def delete_current_note(self):
        """حذف یادداشت جاری"""
        try:
            if not self.selected_note or not self.selected_note.get('id'):
                messagebox.showwarning("هشدار", "هیچ یادداشتی انتخاب نشده است")
                return
            
            confirm = messagebox.askyesno(
                "تأیید حذف", 
                "آیا از حذف این یادداشت اطمینان دارید؟",
                icon='warning'
            )
            
            if not confirm:
                return
            
            # حذف از دیتابیس
            self.db.execute_query("DELETE FROM notes WHERE id=?", (self.selected_note['id'],))

            # حذف از حافظه
            self.notes = [n for n in self.notes if n.get('id') != self.selected_note.get('id')]
            self.selected_note = None
            self.selected_note_id = None
            
            # بارگذاری مجدد لیست
            self._refresh_notes_list()
            
            # پاک کردن ویرایشگر و پنهان کردن آن
            if hasattr(self.editor, 'set_plain_text'):
                self.editor.set_plain_text("")
            elif hasattr(self.editor, 'delete'):
                self.editor.delete("1.0", "end")
                
            # پاک کردن عنوان
            self.title_entry.delete(0, "end")
            
            # پنهان کردن ادیتور
            self._hide_editor()
            
            messagebox.showinfo("موفقیت", "یادداشت با موفقیت حذف شد")
            
        except Exception as e:
            self.logger.error(f"خطا در حذف یادداشت: {e}")
            messagebox.showerror("خطا", f"خطا در حذف یادداشت: {e}")

    def _on_search(self):
        """مدیریت جستجو"""
        self.search_term = self.search_entry.get().strip()
        self._refresh_notes_list()

    def _on_filter_changed(self, val):
        """مدیریت تغییر فیلتر دسته‌بندی"""
        self.current_filter = val
        self._refresh_notes_list()

    def _update_stats(self):
        """به‌روزرسانی آمار"""
        try:
            total = len(self.notes)
            filtered = len(self._get_filtered_notes())
            
            if total == 0:
                txt = "📝 هیچ یادداشتی وجود ندارد"
            elif filtered == total:
                txt = f"📊 {total} یادداشت"
            else:
                txt = f"🔍 {filtered} از {total}"
                
            self.stats_label.configure(text=txt)
        except Exception as e:
            self.logger.error(f"خطا در به‌روزرسانی آمار: {e}")

    def _setup_autosave(self):
        """راه‌اندازی ذخیره‌سازی خودکار"""
        try:
            if hasattr(self.editor, 'start_autosave'):
                self.editor.start_autosave(self._autosave_current_note, interval_ms=10000)
        except Exception as e:
            self.logger.error(f"خطا در راه‌اندازی autosave: {e}")

    def _autosave_current_note(self):
        """ذخیره‌سازی خودکار یادداشت جاری"""
        try:
            if self.selected_note and self.title_entry.get().strip():
                title = self.title_entry.get().strip() or "بدون عنوان"
                category = self.category_combo.get() or (self.categories[0] if self.categories else "عمومی")
                
                # دریافت محتوا
                if hasattr(self.editor, 'get_serialized_format'):
                    serialized = self.editor.get_serialized_format()
                    content_plain = serialized.get("content", "")
                    fmt = json.dumps(serialized, ensure_ascii=False, indent=2)
                else:
                    content_plain = self.editor.get_content_text()
                    fmt = json.dumps({"content": content_plain}, ensure_ascii=False, indent=2)
                
                # ذخیره در دیتابیس
                if self.selected_note.get('id'):
                    self.db.execute_query(
                        '''UPDATE notes 
                           SET title=?, content=?, category=?, tags=?, updated_at=CURRENT_TIMESTAMP, format_json=? 
                           WHERE id=?''',
                        (title, content_plain, category, "", fmt, self.selected_note['id'])
                    )
                else:
                    cursor = self.db.execute_query(
                        'INSERT INTO notes (title, content, category, tags, format_json) VALUES (?, ?, ?, ?, ?)',
                        (title, content_plain, category, "", fmt)
                    )
                    self.selected_note['id'] = cursor.lastrowid

                # به‌روزرسانی در حافظه
                try:
                    serialized_data = json.loads(fmt) if fmt else {"content": content_plain}
                except json.JSONDecodeError:
                    serialized_data = {"content": content_plain}
                
                self.selected_note.update({
                    'title': title,
                    'content': content_plain,
                    'category': category,
                    'format': serialized_data,
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # بارگذاری مجدد لیست
                self._refresh_notes_list()
                
        except Exception as e:
            self.logger.error(f"خطا در autosave: {e}")

    def destroy(self):
        """تخریب ماژول و توقف autosave"""
        try:
            if hasattr(self.editor, 'stop_autosave'):
                self.editor.stop_autosave()
        except Exception:
            pass
            
        try:
            super().destroy()
        except Exception:
            pass