# modules/writer/writer_module.py
import customtkinter as ctk

class WriterModule(ctk.CTkFrame):
    def __init__(self, parent, app, config):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config = config
        
        label = ctk.CTkLabel(
            self,
            text="ماژول نوشتن به زودی اضافه خواهد شد",
            font=ctk.CTkFont(size=16)
        )
        label.pack(expand=True)