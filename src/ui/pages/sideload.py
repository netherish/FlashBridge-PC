from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.commands import adb_reboot, adb_sideload
from core.utils import file_size, format_size
from ui.widgets import OutputPanel
from .base import BasePage


class SideloadPage(BasePage):
    page_title = "ADB sideload"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(3, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="ADB sideload", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        picker = ctk.CTkFrame(self)
        picker.grid(row=1, column=0, sticky="ew")
        picker.grid_columnconfigure(0, weight=1)
        self.image = ctk.CTkEntry(picker, placeholder_text="Select an OTA or ZIP package")
        self.image.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=12)
        ctk.CTkButton(picker, text="Browse", width=90, command=self.browse).grid(row=0, column=1, padx=4)
        self.size_label = ctk.CTkLabel(picker, text="No file selected")
        self.size_label.grid(row=0, column=2, padx=12)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(actions, text="Start sideload", fg_color="#2563eb", command=self.start).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Cancel", command=self.app.cancel_current, fg_color="transparent").pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Reboot to recovery", command=self.to_recovery).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Reboot to sideload", command=self.to_sideload).pack(side="left", padx=4)

        self.output = OutputPanel(self, height=420)
        self.output.grid(row=3, column=0, sticky="nsew")

    def browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Select sideload package",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
            initialdir=self.app.settings.get("last_image_folder") or None,
        )
        if path:
            self.image.delete(0, "end")
            self.image.insert(0, path)
            self.app.settings.set("last_image_folder", str(Path(path).parent))
            self.size_label.configure(text=format_size(file_size(path)))

    def start(self) -> None:
        serial = self.app.require_serial("adb")
        path = self.image.get().strip()
        if not serial or not path:
            return
        self.output.append(f"Starting sideload on {serial}: {path}")
        self.app.run_command(
            adb_sideload(serial, path),
            "ADB sideload",
            confirm=True,
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
        )

    def to_recovery(self) -> None:
        serial = self.app.require_serial("adb")
        if serial:
            self.app.run_command(adb_reboot(serial, "recovery"), "Reboot to recovery", confirm=True)

    def to_sideload(self) -> None:
        serial = self.app.require_serial("adb")
        if serial:
            self.app.run_command(adb_reboot(serial, "sideload"), "Reboot to sideload", confirm=True)
