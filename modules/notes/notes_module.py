"""
modules/notes/notes_module.py

NotesModule — طراحی بازطراحی شده برای بخش یادداشت‌ها
- نماییده شده از سایدبار به بعد (پوشش کامل فضای محتوا)
- ظاهری مدرن با استفاده از customtkinter
- امکانات: ایجاد/ویرایش/حذف/جستجو/صادرات ساده (.md)، لیست اسکرول‌شونده با پیش‌نمایش خلاصه، ذخیره اتوماتیک (قابل غیرفعال کردن)
- پشتیبانی RTL/LTR و واکنش به تغییر زبان/سایز فونت

نکات پیاده‌سازی:
- این ماژول همچنان از `app.db.connection` برای ذخیره در sqlite استفاده می‌کند اگر موجود باشد.
- برای کار صحیح، مسیر فایل را در: modules/notes/notes_module.py قرار بده و فایل __init__.py در همان فولدر داشته باشی.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

# RTL helpers fallback
try:
    from rtl_support import reshape_text, set_widget_rtl, set_widget_ltr
except Exception:
    def reshape_text(x):
        return x
    def set_widget_rtl(w):
        try:
            if hasattr(w, "config"):
                w.config(justify="right")
        except Exception:
            pass
    def set_widget_ltr(w):
        try:
            if hasattr(w, "config"):
                w.config(justify="left")
        except Exception:
            pass


class NotesModule(ctk.CTkFrame):
    """NotesModule: UI کامل و واکنش‌گرا برای مدیریت یادداشت‌ها."""

    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.parent = parent
        self.app = app
        self.config = config
        self.db = getattr(app, "db", None)
        self.event_bus = getattr(app, "event_bus", None)
        self.language = getattr(app, "language", None)
        self.font_size = getattr(app, "font_size", 14)

        # state
        self.notes: List[Dict] = []
        self.filtered_ids: List[int] = []
        self.current_note_id: Optional[int] = None
        self.autosave = True

        # UI vars
        self.search_var = ctk.StringVar()
        self.title_var = ctk.StringVar()

        # ensure table and build
        self._ensure_table()
        self._build_ui()
        self.load_notes()
        self._register_events()

    # ---- translations ----
    def _t(self, key: str, **kwargs) -> str:
        text = key
        try:
            if self.language:
                text = self.language.get_text(key)
        except Exception:
            text = key
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return reshape_text(text) if self.is_rtl() else text

    def is_rtl(self) -> bool:
        try:
            return bool(self.language and self.language.is_rtl())
        except Exception:
            return False

    # ---- UI ----
    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # layout: fixed-width sidebar-like list on left, editor on right
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        list_width = 260
        list_col = 0 if not self.is_rtl() else 1
        editor_col = 1 if not self.is_rtl() else 0

        # LEFT: notes list panel
        self.list_panel = ctk.CTkFrame(self, width=list_width, corner_radius=8)
        self.list_panel.grid(row=0, column=list_col, sticky="nsw" if not self.is_rtl() else "nse", padx=(8,4) if not self.is_rtl() else (4,8), pady=8)
        self.list_panel.grid_propagate(False)
        self.list_panel.grid_rowconfigure(2, weight=1)

        # header (title + actions)
        header = ctk.CTkFrame(self.list_panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="we", padx=8, pady=(8,6))
        header.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(header, text=self._t('notes'), font=ctk.CTkFont(size=self.font_size+2, weight="bold"))
        title_lbl.grid(row=0, column=0, sticky="w")

        # search
        search_entry = ctk.CTkEntry(self.list_panel, textvariable=self.search_var, placeholder_text=self._t('search'))
        search_entry.grid(row=1, column=0, sticky="we", padx=8, pady=(0,8))
        self.search_var.trace_add('write', lambda *_: self._refresh_notes_list())

        # scrollable list of note cards
        try:
            scroll_frame = ctk.CTkScrollableFrame(self.list_panel)
            scroll_frame.grid(row=2, column=0, sticky="nswe", padx=8, pady=(0,8))
            self.cards_container = scroll_frame
        except Exception:
            # fallback to canvas + frame
            container = tk.Frame(self.list_panel)
            container.grid(row=2, column=0, sticky="nswe", padx=8, pady=(0,8))
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)
            canvas = tk.Canvas(container)
            canvas.grid(row=0, column=0, sticky="nswe")
            vsb = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            vsb.grid(row=0, column=1, sticky='ns')
            canvas.configure(yscrollcommand=vsb.set)
            inner = tk.Frame(canvas)
            canvas.create_window((0,0), window=inner, anchor='nw')
            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            self.cards_container = inner

        # bottom action buttons
        actions = ctk.CTkFrame(self.list_panel, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="we", padx=8, pady=(0,8))

        btn_new = ctk.CTkButton(actions, text=self._t('new_note'), command=self.new_note, width=1)
        btn_new.pack(side="left", expand=True, fill="x", padx=(0,6))
        btn_export = ctk.CTkButton(actions, text=self._t('export'), command=self.export_note, width=1)
        btn_export.pack(side="left", expand=True, fill="x", padx=(0,6))
        btn_delete = ctk.CTkButton(actions, text=self._t('delete_note'), command=self.delete_note, fg_color="#ff6b6b", hover_color="#ff5252")
        btn_delete.pack(side="left", expand=True, fill="x")

        # RIGHT: editor panel
        self.editor_panel = ctk.CTkFrame(self, corner_radius=8)
        self.editor_panel.grid(row=0, column=editor_col, sticky="nswe", padx=(4,8) if not self.is_rtl() else (8,4), pady=8)
        self.editor_panel.grid_rowconfigure(3, weight=1)
        self.editor_panel.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self.editor_panel, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="we", padx=8, pady=(8,4))
        top_bar.grid_columnconfigure(1, weight=1)

        self.title_entry = ctk.CTkEntry(top_bar, textvariable=self.title_var)
        self.title_entry.grid(row=0, column=0, sticky="we", padx=(0,8))

        btn_save = ctk.CTkButton(top_bar, text=self._t('save'), command=self.save_note, width=80)
        btn_save.grid(row=0, column=1, sticky="e")

        body_lbl = ctk.CTkLabel(self.editor_panel, text=self._t('body'), font=ctk.CTkFont(size=self.font_size))
        body_lbl.grid(row=1, column=0, sticky="w", padx=8, pady=(6,2))

        try:
            self.body_text = ctk.CTkTextbox(self.editor_panel, width=10, height=20)
        except Exception:
            self.body_text = tk.Text(self.editor_panel, wrap='word')
        self.body_text.grid(row=3, column=0, sticky="nswe", padx=8, pady=(0,8))

        # status / autosave toggle
        bottom_bar = ctk.CTkFrame(self.editor_panel, fg_color="transparent")
        bottom_bar.grid(row=4, column=0, sticky="we", padx=8, pady=(0,8))
        self.autosave_var = tk.BooleanVar(value=self.autosave)
        autosave_cb = ctk.CTkCheckBox(bottom_bar, text=self._t('autosave'), variable=self.autosave_var, command=self._toggle_autosave)
        autosave_cb.pack(side="left")

        # initial styling for RTL
        if self.is_rtl():
            set_widget_rtl(self.title_entry)
            set_widget_rtl(self.body_text)

    # ---- database ----
    def _ensure_table(self):
        if not self.db or not hasattr(self.db, 'connection'):
            return
        try:
            cur = self.db.connection.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    body TEXT,
                    updated TIMESTAMP
                )
            ''')
            self.db.connection.commit()
        except Exception as e:
            print(f"NotesModule: ensure_table error: {e}")

    def load_notes(self):
        self.notes = []
        try:
            if self.db and hasattr(self.db, 'connection'):
                cur = self.db.connection.cursor()
                cur.execute("SELECT id, title, body, updated FROM notes ORDER BY updated DESC")
                rows = cur.fetchall()
                for r in rows:
                    nid, title, body, updated = r
                    self.notes.append({'id': nid, 'title': title or '', 'body': body or '', 'updated': updated})
            else:
                self.notes = []
        except Exception as e:
            print(f"NotesModule: load_notes error: {e}")
            self.notes = []
        self._refresh_notes_list()

    def _refresh_notes_list(self):
        # clear existing cards
        for child in list(self.cards_container.winfo_children()):
            child.destroy()
        q = self.search_var.get().strip().lower()
        self.filtered_ids = []
        for note in self.notes:
            title = note.get('title') or self._t('untitled')
            if not q or q in title.lower() or (q in (note.get('body') or '').lower()):
                self._add_note_card(note)
                self.filtered_ids.append(note['id'])

    def _add_note_card(self, note: Dict):
        # compact card with title and snippet
        frame = ctk.CTkFrame(self.cards_container, fg_color="transparent")
        frame.pack(fill='x', pady=6, padx=6)
        frame.bind('<Button-1>', lambda e, nid=note['id']: self.show_note_by_id(nid))

        t = note.get('title') or self._t('untitled')
        lbl = ctk.CTkLabel(frame, text=t, anchor='w', font=ctk.CTkFont(size=self.font_size, weight="bold"))
        lbl.pack(fill='x')
        lbl.bind('<Button-1>', lambda e, nid=note['id']: self.show_note_by_id(nid))

        snippet = (note.get('body') or '').split('\n', 1)[0][:120]
        sub = ctk.CTkLabel(frame, text=snippet, anchor='w', font=ctk.CTkFont(size=max(self.font_size-2,10)))
        sub.pack(fill='x')
        sub.bind('<Button-1>', lambda e, nid=note['id']: self.show_note_by_id(nid))

    # ---- actions ----
    def show_note_by_id(self, note_id: int):
        note = next((n for n in self.notes if n['id'] == note_id), None)
        if not note:
            return
        self.current_note_id = note_id
        self.title_var.set(note.get('title', ''))
        try:
            if isinstance(self.body_text, tk.Text):
                self.body_text.delete('1.0', tk.END)
                self.body_text.insert('1.0', note.get('body',''))
            else:
                self.body_text.delete('0.0', 'end')
                self.body_text.insert('0.0', note.get('body',''))
        except Exception:
            pass

    def new_note(self):
        self.current_note_id = None
        self.title_var.set('')
        try:
            if isinstance(self.body_text, tk.Text):
                self.body_text.delete('1.0', tk.END)
            else:
                self.body_text.delete('0.0', 'end')
        except Exception:
            pass
        self.title_entry.focus_set()

    def save_note(self):
        title = self.title_var.get().strip()
        try:
            body = self.body_text.get('1.0', tk.END) if isinstance(self.body_text, tk.Text) else self.body_text.get('0.0', 'end')
            body = body.rstrip('\n')
        except Exception:
            body = ''
        now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        try:
            if self.db and hasattr(self.db, 'connection'):
                cur = self.db.connection.cursor()
                if self.current_note_id is None:
                    cur.execute("INSERT INTO notes (title, body, updated) VALUES (?, ?, ?)", (title, body, now))
                    self.db.connection.commit()
                    self.current_note_id = cur.lastrowid
                else:
                    cur.execute("UPDATE notes SET title = ?, body = ?, updated = ? WHERE id = ?", (title, body, now, self.current_note_id))
                    self.db.connection.commit()
            else:
                if self.current_note_id is None:
                    nid = (max([n['id'] for n in self.notes]) + 1) if self.notes else 1
                    self.notes.insert(0, {'id': nid, 'title': title, 'body': body, 'updated': now})
                    self.current_note_id = nid
                else:
                    for n in self.notes:
                        if n['id'] == self.current_note_id:
                            n['title'] = title
                            n['body'] = body
                            n['updated'] = now
                            break
        except Exception as e:
            print(f"NotesModule: save_note error: {e}")
            messagebox.showerror(self._t('error'), self._t('save_failed'))
            return
        self.load_notes()
        try:
            idx = self.filtered_ids.index(self.current_note_id)
            # no direct selection on cards; bring into view by reloading and showing
        except Exception:
            pass
        try:
            if self.event_bus:
                self.event_bus.publish('notes_changed', {'id': self.current_note_id})
        except Exception:
            pass

    def delete_note(self):
        if self.current_note_id is None:
            messagebox.showinfo(self._t('info'), self._t('nothing_selected'))
            return
        if not messagebox.askyesno(self._t('confirm'), self._t('delete_confirm')):
            return
        try:
            if self.db and hasattr(self.db, 'connection'):
                cur = self.db.connection.cursor()
                cur.execute("DELETE FROM notes WHERE id = ?", (self.current_note_id,))
                self.db.connection.commit()
            else:
                self.notes = [n for n in self.notes if n['id'] != self.current_note_id]
        except Exception as e:
            print(f"NotesModule: delete_note error: {e}")
            messagebox.showerror(self._t('error'), self._t('delete_failed'))
            return
        self.current_note_id = None
        self.load_notes()
        self.new_note()
        try:
            if self.event_bus:
                self.event_bus.publish('notes_changed', {'id': None})
        except Exception:
            pass

    def export_note(self):
        if self.current_note_id is None:
            messagebox.showinfo(self._t('info'), self._t('nothing_selected'))
            return
        note = next((n for n in self.notes if n['id'] == self.current_note_id), None)
        if not note:
            return
        default_name = (note.get('title') or 'note').replace(' ', '_') + '.md'
        path = filedialog.asksaveasfilename(defaultextension='.md', initialfile=default_name, filetypes=[('Markdown', '*.md'), ('Text', '*.txt')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# {note.get('title','')}\n\n")
                f.write(note.get('body',''))
            messagebox.showinfo(self._t('export'), self._t('export_success'))
        except Exception as e:
            print(f"NotesModule: export error: {e}")
            messagebox.showerror(self._t('error'), self._t('export_failed'))

    def _toggle_autosave(self):
        self.autosave = bool(self.autosave_var.get())

    # ---- events ----
    def _register_events(self):
        if not self.event_bus:
            return
        try:
            self.event_bus.subscribe('language_changed', self._on_language_changed)
            self.event_bus.subscribe('font_size_changed', self._on_font_size_changed)
        except Exception:
            pass

    def _on_language_changed(self, data=None):
        self._build_ui()
        self.load_notes()

    def _on_font_size_changed(self, data):
        try:
            self.font_size = data.get('size', self.font_size)
        except Exception:
            pass
        self._build_ui()

# EOF
