from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from .base import BasePage


class LogsPage(BasePage):
    page_title = "Activity log"

    def __init__(self, master, app):
        super().__init__(master, app)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Activity log", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Export", command=self.export).pack(side="right", padx=4)
        ctk.CTkButton(header, text="Clear", command=self.clear, fg_color="transparent").pack(side="right", padx=4)

        filter_row = ctk.CTkFrame(self)
        filter_row.grid(row=1, column=0, sticky="ew")
        ctk.CTkLabel(filter_row, text="Filter").pack(side="left", padx=12)
        self.filter = ctk.CTkEntry(filter_row, placeholder_text="Text to match")
        self.filter.pack(side="left", fill="x", expand=True, padx=4, pady=10)
        self.filter.bind("<KeyRelease>", lambda _: self.render())

        self.textbox = ctk.CTkTextbox(self, font=ctk.CTkFont("Consolas", 12))
        self.textbox.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        self.textbox.configure(state="disabled")

    def on_show(self) -> None:
        self.render()

    def render(self) -> None:
        needle = self.filter.get().strip().lower()
        entries = self.app.logs.entries()
        if needle:
            entries = [entry for entry in entries if needle in entry.render().lower()]
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        for entry in entries:
            self.textbox.insert("end", entry.render() + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        self.app.logs.clear()
        self.render()

    def export(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export log",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt")],
        )
        if path:
            self.app.logs.export(path)
