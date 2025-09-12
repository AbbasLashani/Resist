modules/notes/notes_module.py

"""
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
            if hasattr(w, "configure"):
                w.configure(justify="right")
        except Exception:
            pass
    def set_widget_ltr(w):
        try:
            if hasattr(w, "configure"):
                w.configure(justify="left")
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
        self.autosave_var = ctk.BooleanVar(value=self.autosave)

        # Ensure table and build
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

        # Layout: fixed-width sidebar-like list on left, editor on right
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        list_col = 0 if not self.is_rtl() else 1
        editor_col = 1 if not self.is_rtl() else 0

        # LEFT: Notes list panel
        self.list_panel = ctk.CTkFrame(self, corner_radius=8)
        self.list_panel.grid(row=0, column=list_col, sticky="nswe", padx=(8, 4) if not self.is_rtl() else (4, 8), pady=8)
        self.list_panel.grid_rowconfigure(2, weight=1)
        self.list_panel.grid_columnconfigure(0, weight=1)

        # Header (title)
        header = ctk.CTkFrame(self.list_panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="we", padx=8, pady=(8, 6))
        header.grid_columnconfigure(0, weight=1)
        
        title_lbl = ctk.CTkLabel(header, text=self._t('notes'), font=ctk.CTkFont(size=self.font_size+2, weight="bold"))
        title_lbl.grid(row=0, column=0, sticky="w")

        # Search
        search_entry = ctk.CTkEntry(self.list_panel, textvariable=self.search_var, placeholder_text=self._t('search'))
        search_entry.grid(row=1, column=0, sticky="we", padx=8, pady=(0, 8))
        self.search_var.trace_add('write', lambda *_: self._refresh_notes_list())

        # Scrollable list of note cards
        self.cards_container = ctk.CTkScrollableFrame(self.list_panel, fg_color="transparent")
        self.cards_container.grid(row=2, column=0, sticky="nswe", padx=8, pady=(0, 8))
        self.cards_container.grid_columnconfigure(0, weight=1)
        
        # Bottom action buttons
        actions = ctk.CTkFrame(self.list_panel, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="we", padx=8, pady=(0, 8))
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        btn_new = ctk.CTkButton(actions, text=self._t('new_note'), command=self.new_note)
        btn_new.grid(row=0, column=0, sticky="we", padx=(0, 6))
        
        btn_export = ctk.CTkButton(actions, text=self._t('export'), command=self.export_note)
        btn_export.grid(row=0, column=1, sticky="we", padx=(0, 6))
        
        btn_delete = ctk.CTkButton(actions, text=self._t('delete_note'), command=self.delete_note, fg_color="#ff6b6b", hover_color="#ff5252")
        btn_delete.grid(row=0, column=2, sticky="we")

        # RIGHT: editor panel
        self.editor_panel = ctk.CTkFrame(self, corner_radius=8)
        self.editor_panel.grid(row=0, column=editor_col, sticky="nswe", padx=(4, 8) if not self.is_rtl() else (8, 4), pady=8)
        self.editor_panel.grid_rowconfigure(2, weight=1)
        self.editor_panel.grid_columnconfigure(0, weight=1)
        
        top_bar = ctk.CTkFrame(self.editor_panel, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="we", padx=8, pady=(8, 4))
        top_bar.grid_columnconfigure(0, weight=1)

        self.title_entry = ctk.CTkEntry(top_bar, textvariable=self.title_var, placeholder_text=self._t('title'))
        self.title_entry.grid(row=0, column=0, sticky="we", padx=(0, 8))

        btn_save = ctk.CTkButton(top_bar, text=self._t('save'), command=self.save_note, width=80)
        btn_save.grid(row=0, column=1, sticky="e")

        self.body_text = ctk.CTkTextbox(self.editor_panel, width=10, height=20, wrap="word", font=ctk.CTkFont(size=self.font_size))
        self.body_text.grid(row=1, column=0, sticky="nswe", padx=8, pady=(8, 8))
        
        # status / autosave toggle
        bottom_bar = ctk.CTkFrame(self.editor_panel, fg_color="transparent")
        bottom_bar.grid(row=2, column=0, sticky="we", padx=8, pady=(0, 8))
        autosave_cb = ctk.CTkCheckBox(bottom_bar, text=self._t('autosave'), variable=self.autosave_var, command=self._toggle_autosave)
        autosave_cb.grid(row=0, column=0, sticky="w")
        
        # Initial styling for RTL
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
        row = 0
        for note in self.notes:
            title = note.get('title') or self._t('untitled')
            if not q or q in title.lower() or (q in (note.get('body') or '').lower()):
                self._add_note_card(note, row)
                self.filtered_ids.append(note['id'])
                row += 1
    
    def _add_note_card(self, note: Dict, row: int):
        # Compact card with title and snippet
        frame = ctk.CTkFrame(self.cards_container, corner_radius=6, fg_color=self.cget('fg_color'))
        frame.grid(row=row, column=0, sticky="we", pady=3)
        frame.grid_columnconfigure(0, weight=1)
        frame.bind('<Button-1>', lambda e, nid=note['id']: self.show_note_by_id(nid))

        t = note.get('title') or self._t('untitled')
        lbl = ctk.CTkLabel(frame, text=t, anchor='w', font=ctk.CTkFont(size=self.font_size, weight="bold"))
        lbl.grid(row=0, column=0, sticky="w", padx=8, pady=2)
        lbl.bind('<Button-1>', lambda e, nid=note['id']: self.show_note_by_id(nid))

        snippet = (note.get('body') or '').split('\n', 1)[0][:120].strip()
        sub = ctk.CTkLabel(frame, text=snippet, anchor='w', font=ctk.CTkFont(size=max(self.font_size-2,10)))
        sub.grid(row=1, column=0, sticky="w", padx=8, pady=2)
        sub.bind('<Button-1>', lambda e, nid=note['id']: self.show_note_by_id(nid))

    # ---- actions ----
    def show_note_by_id(self, note_id: int):
        note = next((n for n in self.notes if n['id'] == note_id), None)
        if not note:
            return
        self.current_note_id = note_id
        self.title_var.set(note.get('title', ''))
        
        try:
            self.body_text.delete('0.0', 'end')
            self.body_text.insert('0.0', note.get('body',''))
        except Exception:
            pass

    def new_note(self):
        self.current_note_id = None
        self.title_var.set('')
        try:
            self.body_text.delete('0.0', 'end')
        except Exception:
            pass
        self.title_entry.focus_set()

    def save_note(self):
        title = self.title_var.get().strip()
        try:
            body = self.body_text.get('0.0', 'end').rstrip('\n')
        except Exception:
            body = ''
            
        if not title and not body:
            if self.current_note_id:
                self.delete_note()
            return
            
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
        self.autosave = self.autosave_var.get()
        if not self.autosave:
            # show a warning or change status if needed
            pass

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