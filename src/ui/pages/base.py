from __future__ import annotations

import customtkinter as ctk


class BasePage(ctk.CTkFrame):
    page_title = "Page"

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

    def on_show(self) -> None:
        pass

    def on_devices_changed(self, devices) -> None:
        pass
