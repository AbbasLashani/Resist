import customtkinter as ctk
from core.base_module import BaseModule
from tkinter import ttk, Menu, Toplevel, simpledialog, messagebox, filedialog, scrolledtext
import sqlite3
from datetime import datetime

class NotesModule(BaseModule):
    def __init__(self, parent, app, config):
        super().__init__(parent, app, config)
        # مسیر دیتابیس (از config بخوان یا مقدار پیش‌فرض)
        self.db_path = config.get("notes_db", "notes.sqlite")
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

        # متغیرها
        self.current_note_id = None
        self.autosave_enabled = False
        self.autosave_interval_ms = 30_000  # 30 ثانیه
        self._autosave_after_id = None

        self.setup_ui()

        # شورتکات کلی (bind به کل ویندوز ماژول)
        # از bind_all استفاده نمی‌کنیم تا تداخل با بقیه برنامه کم باشه؛ bind روی خود فریم کافیست
        self.bind_all("<Control-s>", lambda e: self.save_note())
        self.bind_all("<Control-n>", lambda e: self.create_new_note())
        self.bind_all("<Control-f>", lambda e: self.open_find_replace())
        self.bind_all("<Control-a>", lambda e: self.select_all_in_text())
        # Undo/Redo (اگر ویجت پشتیبانی کنه)
        self.bind_all("<Control-z>", lambda e: self.try_undo())
        self.bind_all("<Control-y>", lambda e: self.try_redo())

    def create_table(self):
        """ایجاد جدول یادداشت‌ها در صورت نبود"""
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        self.conn.commit()

    def setup_ui(self):
        """ایجاد رابط کاربری مدیریت یادداشت‌ها"""
        # پاک کردن ویجت‌های موجود
        for widget in self.winfo_children():
            widget.destroy()

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        # ستون لیست یادداشت‌ها
        list_frame = ctk.CTkFrame(main_frame, width=320, fg_color=("#F0F0F0", "#2A2A2A"))
        list_frame.pack(side="right" if self.language.is_rtl() else "left", fill="y")
        list_frame.pack_propagate(False)

        list_header = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=10, pady=10)

        list_title = self.create_label(
            list_header,
            text="یادداشت‌ها" if self.language.is_rtl() else "Notes",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        list_title.pack(side="right" if self.language.is_rtl() else "left")

        add_btn = ctk.CTkButton(
            list_header,
            text="+",
            width=30,
            height=30,
            font=ctk.CTkFont(size=16),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=self.create_new_note
        )
        add_btn.pack(side="left" if self.language.is_rtl() else "right")

        search_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="جستجوی یادداشت..." if self.language.is_rtl() else "Search notes...",
            height=35
        )
        self.search_entry.pack(side="right" if self.language.is_rtl() else "left", fill="x", expand=True, padx=(10, 0))

        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=40,
            height=35,
            command=lambda: self.search_notes(self.search_entry.get())
        )
        search_btn.pack(side="right" if self.language.is_rtl() else "left")

        import_btn = ctk.CTkButton(
            search_frame,
            text="⬆️ وارد کن",
            width=70,
            height=35,
            command=self.import_note_from_file
        )
        import_btn.pack(side="right" if self.language.is_rtl() else "left", padx=(5,0))

        export_btn = ctk.CTkButton(
            search_frame,
            text="⬇️ خروجی",
            width=70,
            height=35,
            command=self.export_current_note
        )
        export_btn.pack(side="right" if self.language.is_rtl() else "left", padx=(5,0))

        self.notes_list = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.notes_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ستون ویرایشگر
        editor_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        editor_frame.pack(side="left" if self.language.is_rtl() else "right", fill="both", expand=True, padx=10, pady=10)

        editor_title = self.create_label(
            editor_frame,
            text="ویرایشگر یادداشت" if self.language.is_rtl() else "Note Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        editor_title.pack(pady=6)

        title_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=5)

        title_label = self.create_label(
            title_frame,
            text="عنوان:" if self.language.is_rtl() else "Title:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(anchor="w" if not self.language.is_rtl() else "e")

        self.title_entry = ctk.CTkEntry(
            title_frame,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.title_entry.pack(fill="x", pady=5)

        content_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=5)

        content_label = self.create_label(
            content_frame,
            text="محتوا:" if self.language.is_rtl() else "Content:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        content_label.pack(anchor="w" if not self.language.is_rtl() else "e")

        # CTkTextbox را با undo فعال می‌سازیم (در صورت پشتیبانی)
        try:
            self.content_text = ctk.CTkTextbox(
                content_frame,
                font=ctk.CTkFont(size=12),
                wrap="word",
                undo=True
            )
        except TypeError:
            # اگر CTkTextbox پارامتر undo را نمی‌پذیرد، بدون آن بساز
            self.content_text = ctk.CTkTextbox(
                content_frame,
                font=ctk.CTkFont(size=12),
                wrap="word"
            )

        self.content_text.pack(fill="both", expand=True, pady=5)

        # منوی راست‌کلیک برای کپی/پیست/کات/انتخاب همه
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="کپی", command=self.copy_text)
        self.context_menu.add_command(label="کات", command=self.cut_text)
        self.context_menu.add_command(label="پیست", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="انتخاب همه", command=self.select_all_in_text)

        # bind راست کلیک برای نمایش منو
        self.content_text.bind("<Button-3>", self._show_context_menu)

        # شورتکات های کپی پیست روی تکست با bind (Ctrl-*)
        self.content_text.bind("<Control-c>", lambda e: self.copy_text())
        self.content_text.bind("<Control-v>", lambda e: self.paste_text())
        self.content_text.bind("<Control-x>", lambda e: self.cut_text())
        self.content_text.bind("<Control-a>", lambda e: self.select_all_in_text())

        # بروزرسانی آمار (شمارش کلمات) هنگام تایپ
        self.content_text.bind("<KeyRelease>", lambda e: self.update_stats())

        # نوار ابزار قالب‌بندی
        toolbar_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        toolbar_frame.pack(fill="x", pady=8)

        # قالب‌بندی: اینجا ساده (مارک‌داون) انجام می‌دهیم تا وابستگی به فونت/تگ نداشته باشیم
        format_buttons = [
            {"text": "B", "tooltip": "پررنگ (Ctrl+B)", "cmd": self.toggle_bold},
            {"text": "I", "tooltip": "ایتالیک (Ctrl+I)", "cmd": self.toggle_italic},
            {"text": "U", "tooltip": "زیرخط (Ctrl+U)", "cmd": self.toggle_underline},
            {"text": "🔗", "tooltip": "لینک", "cmd": self.insert_link},
            {"text": "🔁", "tooltip": "Undo", "cmd": self.try_undo},
            {"text": "↻", "tooltip": "Redo", "cmd": self.try_redo},
            {"text": "🔍", "tooltip": "Find/Replace (Ctrl+F)", "cmd": self.open_find_replace},
            {"text": "👁 Preview", "tooltip": "پیش‌نمایش", "cmd": self.preview_note}
        ]

        for btn in format_buttons:
            format_btn = ctk.CTkButton(
                toolbar_frame,
                text=btn["text"],
                width=36,
                height=32,
                font=ctk.CTkFont(size=12),
                command=btn["cmd"]
            )
            format_btn.pack(side="right" if self.language.is_rtl() else "left", padx=4)

        # نوار عملگرها (ذخیره حذف و autosave)
        action_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=10)

        save_btn = self.create_button(
            action_frame,
            text="💾 ذخیره",
            command=self.save_note,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        save_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)

        delete_btn = self.create_button(
            action_frame,
            text="🗑️ حذف",
            command=self.delete_note,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#F44336",
            hover_color="#d32f2f"
        )
        delete_btn.pack(side="right" if self.language.is_rtl() else "left", padx=5)

        # autosave checkbox
        self.autosave_checkbox = ctk.CTkCheckBox(
            action_frame,
            text="Autosave",
            command=self.toggle_autosave
        )
        self.autosave_checkbox.pack(side="right" if self.language.is_rtl() else "left", padx=5)

        # آمار و وضعیت پایین ویرایشگر
        status_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0,5))

        self.stats_label = self.create_label(status_frame, text="Words: 0 | Chars: 0", font=ctk.CTkFont(size=12))
        self.stats_label.pack(side="left")

        # بارگذاری یادداشت‌ها
        self.load_notes_list()

    # --------------------------
    # لیست و دیتابیس
    # --------------------------
    def load_notes_list(self, query=None):
        """بارگذاری لیست یادداشت‌ها از دیتابیس"""
        for widget in self.notes_list.winfo_children():
            widget.destroy()

        cursor = self.conn.cursor()
        if query:
            cursor.execute("SELECT id, title, content, created_at, updated_at FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC", (f"%{query}%", f"%{query}%"))
        else:
            cursor.execute("SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC")
        rows = cursor.fetchall()

        # اگر خالیه یک placeholder نمایش بدیم
        if not rows:
            empty_label = self.create_label(self.notes_list, text="(هیچ یادداشتی یافت نشد)" if self.language.is_rtl() else "(No notes found)", font=ctk.CTkFont(size=12))
            empty_label.pack(pady=10)
            return

        for note in rows:
            note_dict = {
                "id": note[0],
                "title": note[1],
                "preview": (note[2][:60] + "...") if note[2] else "",
                "date": note[4] or note[3] or ""
            }
            self.create_note_item(note_dict)

    def create_note_item(self, note):
        """آیتم لیست یادداشت"""
        note_frame = ctk.CTkFrame(
            self.notes_list,
            fg_color=("#FFFFFF", "#333333"),
            corner_radius=8,
            height=80
        )
        note_frame.pack(fill="x", pady=6)
        note_frame.pack_propagate(False)

        content_frame = ctk.CTkFrame(note_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)

        title_lbl = self.create_label(content_frame, text=note["title"], font=ctk.CTkFont(size=13, weight="bold"))
        title_lbl.pack(anchor="w" if not self.language.is_rtl() else "e")

        preview_lbl = self.create_label(content_frame, text=note["preview"], font=ctk.CTkFont(size=11), text_color=("#666666", "#AAAAAA"))
        preview_lbl.pack(anchor="w" if not self.language.is_rtl() else "e")

        date_lbl = self.create_label(content_frame, text=note["date"], font=ctk.CTkFont(size=9), text_color=("#888888", "#888888"))
        date_lbl.pack(anchor="w" if not self.language.is_rtl() else "e")

        # bind روی فریم و روی لیبل‌ها تا کلیک کردن در هر نقطه آیتم کار کنه
        widgets_to_bind = (note_frame, content_frame, title_lbl, preview_lbl, date_lbl)
        for w in widgets_to_bind:
            w.bind("<Button-1>", lambda e, n=note: self.select_note(n))

    def select_note(self, note):
        """باز کردن یادداشت برای ویرایش (از دیتابیس بخوان)"""
        self.current_note_id = note["id"]
        cursor = self.conn.cursor()
        cursor.execute("SELECT title, content FROM notes WHERE id=?", (note["id"],))
        result = cursor.fetchone()
        if result:
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, result[0])
            self.content_text.delete("1.0", "end")
            self.content_text.insert("1.0", result[1])
            self.update_stats()

    # --------------------------
    # عملیات CRUD
    # --------------------------
    def create_new_note(self):
        """آماده‌سازی برای یادداشت جدید"""
        self.current_note_id = None
        self.title_entry.delete(0, "end")
        self.content_text.delete("1.0", "end")
        self.title_entry.insert(0, "یادداشت جدید" if self.language.is_rtl() else "New Note")
        self.content_text.insert("1.0", "محتوا را اینجا بنویسید..." if self.language.is_rtl() else "Write your content here...")
        self.update_stats()

    def save_note(self):
        """ذخیره یا آپدیت یادداشت"""
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not title or not content:
            messagebox.showwarning("Warning", "لطفا عنوان و محتوا را پر کنید" if self.language.is_rtl() else "Please provide title and content")
            return

        cursor = self.conn.cursor()
        if self.current_note_id:  # ویرایش
            cursor.execute("UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?", (title, content, now, self.current_note_id))
        else:  # ایجاد جدید
            cursor.execute("INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)", (title, content, now, now))
            self.current_note_id = cursor.lastrowid
        self.conn.commit()
        self.load_notes_list()
        messagebox.showinfo("Saved", "ذخیره شد ✔" if self.language.is_rtl() else "Saved ✔")

    def delete_note(self):
        """حذف یادداشت انتخاب‌شده"""
        if not self.current_note_id:
            messagebox.showwarning("Warning", "هیچ یادداشتی انتخاب نشده" if self.language.is_rtl() else "No note selected")
            return
        if not messagebox.askyesno("Confirm", "آیا از حذف مطمئنی؟" if self.language.is_rtl() else "Are you sure to delete?"):
            return
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id=?", (self.current_note_id,))
        self.conn.commit()
        self.current_note_id = None
        self.title_entry.delete(0, "end")
        self.content_text.delete("1.0", "end")
        self.load_notes_list()
        messagebox.showinfo("Deleted", "حذف شد" if self.language.is_rtl() else "Deleted")

    def search_notes(self, query):
        self.load_notes_list(query)

    # --------------------------
    # کپی پیست و منوی راست کلیک
    # --------------------------
    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_text(self):
        try:
            selected = self.content_text.selection_get()
            self.clipboard_clear()
            self.clipboard_append(selected)
        except Exception:
            pass

    def paste_text(self):
        try:
            text = self.clipboard_get()
            self.content_text.insert("insert", text)
        except Exception:
            pass

    def cut_text(self):
        try:
            selected = self.content_text.selection_get()
            self.clipboard_clear()
            self.clipboard_append(selected)
            self.content_text.delete("sel.first", "sel.last")
        except Exception:
            pass

    def select_all_in_text(self):
        try:
            self.content_text.tag_add("sel", "1.0", "end")
            return "break"
        except Exception:
            pass

    # --------------------------
    # قالب‌بندی سریع (مارک‌داون-محور)
    # --------------------------
    def _wrap_selection(self, prefix, suffix=None):
        """دور متن انتخابی را با prefix و suffix می‌بندد (اگر انتخابی نبود، متن نمونه قرار می‌دهد)"""
        if suffix is None:
            suffix = prefix
        try:
            start = self.content_text.index("sel.first")
            end = self.content_text.index("sel.last")
            selected = self.content_text.get(start, end)
            new = f"{prefix}{selected}{suffix}"
            self.content_text.delete(start, end)
            self.content_text.insert(start, new)
        except Exception:
            # هیچ انتخابی نیست؛ درج نمونه
            self.content_text.insert("insert", f"{prefix}متن{suffix}")

    def toggle_bold(self):
        self._wrap_selection("**", "**")

    def toggle_italic(self):
        self._wrap_selection("*", "*")

    def toggle_underline(self):
        # underline را با __ نشان می‌دهیم
        self._wrap_selection("__", "__")

    def insert_link(self):
        # ساده: از کاربر متن و لینک می‌گیریم و مارک‌داون قرار می‌دهیم
        text = simpledialog.askstring("Link text", "متن لینک:" if self.language.is_rtl() else "Link text:")
        url = simpledialog.askstring("URL", "آدرس لینک:" if self.language.is_rtl() else "URL:")
        if text and url:
            md = f"[{text}]({url})"
            self.content_text.insert("insert", md)

    # --------------------------
    # Undo/Redo (در صورت پشتیبانی ویجت)
    # --------------------------
    def try_undo(self, *args):
        try:
            self.content_text.edit_undo()
        except Exception:
            pass

    def try_redo(self, *args):
        try:
            self.content_text.edit_redo()
        except Exception:
            pass

    # --------------------------
    # Find & Replace
    # --------------------------
    def open_find_replace(self):
        dlg = Toplevel(self)
        dlg.title("Find & Replace" if not self.language.is_rtl() else "جستجو و جایگزینی")
        dlg.geometry("400x140")
        dlg.transient(self)

        find_lbl = ctk.CTkLabel(dlg, text="Find:" if not self.language.is_rtl() else "جستجو:")
        find_lbl.pack(anchor="w", padx=8, pady=(8,0))
        find_entry = ctk.CTkEntry(dlg)
        find_entry.pack(fill="x", padx=8)

        replace_lbl = ctk.CTkLabel(dlg, text="Replace:" if not self.language.is_rtl() else "جایگزینی:")
        replace_lbl.pack(anchor="w", padx=8, pady=(8,0))
        replace_entry = ctk.CTkEntry(dlg)
        replace_entry.pack(fill="x", padx=8)

        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(fill="x", pady=8, padx=8)

        def find_next():
            needle = find_entry.get()
            if not needle:
                return
            start_pos = self.content_text.index("insert")
            idx = self.content_text.search(needle, start_pos, nocase=1, stopindex="end")
            if not idx:
                messagebox.showinfo("Not found", "پایان متن" if self.language.is_rtl() else "Not found")
                return
            end_idx = f"{idx}+{len(needle)}c"
            self.content_text.tag_remove("search", "1.0", "end")
            self.content_text.tag_add("search", idx, end_idx)
            self.content_text.tag_config("search", background="#FFD54F")
            self.content_text.mark_set("insert", end_idx)
            self.content_text.see(idx)

        def replace_one():
            needle = find_entry.get()
            replacement = replace_entry.get()
            if not needle:
                return
            idx = self.content_text.search(needle, "1.0", nocase=1, stopindex="end")
            if not idx:
                messagebox.showinfo("Not found", "یافت نشد" if self.language.is_rtl() else "Not found")
                return
            end_idx = f"{idx}+{len(needle)}c"
            self.content_text.delete(idx, end_idx)
            self.content_text.insert(idx, replacement)

        def replace_all():
            needle = find_entry.get()
            replacement = replace_entry.get()
            if not needle:
                return
            count = 0
            start = "1.0"
            while True:
                idx = self.content_text.search(needle, start, nocase=1, stopindex="end")
                if not idx:
                    break
                end_idx = f"{idx}+{len(needle)}c"
                self.content_text.delete(idx, end_idx)
                self.content_text.insert(idx, replacement)
                start = f"{idx}+{len(replacement)}c"
                count += 1
            messagebox.showinfo("Done", f"Replaced {count} occurrences")

        find_btn = ctk.CTkButton(btn_frame, text="Find Next", command=find_next)
        find_btn.pack(side="left", padx=6)
        replace_btn = ctk.CTkButton(btn_frame, text="Replace", command=replace_one)
        replace_btn.pack(side="left", padx=6)
        replace_all_btn = ctk.CTkButton(btn_frame, text="Replace All", command=replace_all)
        replace_all_btn.pack(side="left", padx=6)

    # --------------------------
    # Preview
    # --------------------------
    def preview_note(self):
        """پنجره سادهٔ پیش‌نمایش (نمایش متن به صورت خام؛ در آینده می‌توان Markdown رندر اضافه کرد)"""
        dlg = Toplevel(self)
        dlg.title("Preview" if not self.language.is_rtl() else "پیش‌نمایش")
        dlg.geometry("700x500")
        txt = scrolledtext.ScrolledText(dlg, wrap="word")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", self.content_text.get("1.0", "end-1c"))
        txt.configure(state="disabled")

    # --------------------------
    # Export / Import
    # --------------------------
    def export_current_note(self):
        """صادرات یادداشت جاری به فایل txt"""
        if not self.current_note_id:
            messagebox.showwarning("No note", "هیچ یادداشتی انتخاب نشده" if self.language.is_rtl() else "No note selected")
            return
        title = self.title_entry.get().strip() or "note"
        default_name = f"{title}.txt"
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name, filetypes=[("Text files", "*.txt")])
        if not path:
            return
        content = self.content_text.get("1.0", "end-1c")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{content}")
        messagebox.showinfo("Exported", "ذخیره شد" if self.language.is_rtl() else "Exported")

    def import_note_from_file(self):
        """وارد کردن از فایل txt به عنوان یک یادداشت جدید"""
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        # جدا کردن عنوان و محتوا اگر ممکن بود (عنوان در خط اول)
        parts = data.splitlines()
        title = parts[0] if parts else "Imported Note"
        content = "\n".join(parts[2:]) if len(parts) > 2 else "\n".join(parts[1:]) if len(parts) > 1 else ""
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, title)
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", content)
        self.current_note_id = None  # به عنوان جدید ذخیره خواهد شد

    # --------------------------
    # Autosave
    # --------------------------
    def toggle_autosave(self):
        self.autosave_enabled = not self.autosave_enabled
        if self.autosave_enabled:
            # برنامه‌ریزی autosave
            self._schedule_autosave()
        else:
            if self._autosave_after_id:
                self.after_cancel(self._autosave_after_id)
                self._autosave_after_id = None

    def _schedule_autosave(self):
        if self.autosave_enabled:
            # فقط اگر عنوان و محتوا خالی نیستند autosave انجام بده
            title = self.title_entry.get().strip()
            content = self.content_text.get("1.0", "end-1c").strip()
            if title and content:
                # بدون پیغام ذخیره کن
                cursor = self.conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if self.current_note_id:
                    cursor.execute("UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?", (title, content, now, self.current_note_id))
                else:
                    cursor.execute("INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)", (title, content, now, now))
                    self.current_note_id = cursor.lastrowid
                self.conn.commit()
                self.load_notes_list()
            # schedule next
            self._autosave_after_id = self.after(self.autosave_interval_ms, self._schedule_autosave)

    # --------------------------
    # آمار
    # --------------------------
    def update_stats(self):
        text = self.content_text.get("1.0", "end-1c")
        words = len(text.split())
        chars = len(text)
        self.stats_label.configure(text=f"Words: {words} | Chars: {chars}")

    # --------------------------
    # بقیه
    # --------------------------
    def refresh_language(self):
        """تازه‌سازی متن‌ها بر اساس زبان جدید"""
        # ساده‌ترین کار بازسازی کامل UI است تا متن‌ها آپدیت شوند
        self.setup_ui()
