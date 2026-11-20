from __future__ import annotations

import customtkinter as ctk

from core.commands import adb_shell
from ui.widgets import OutputPanel
from .base import BasePage


class ShellPage(BasePage):
    page_title = "ADB shell"

    def __init__(self, master, app):
        super().__init__(master, app)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="ADB shell", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="Commands run directly through the connected ADB device.", text_color="gray").pack(
            side="left", padx=14
        )

        prompt = ctk.CTkFrame(self)
        prompt.grid(row=1, column=0, sticky="ew")
        prompt.grid_columnconfigure(0, weight=1)
        self.command = ctk.CTkEntry(prompt, placeholder_text="Example: getprop ro.product.model", height=36)
        self.command.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=12)
        self.command.bind("<Return>", lambda _: self.run())
        ctk.CTkButton(prompt, text="Run", width=90, command=self.run).grid(row=0, column=1, padx=4)
        ctk.CTkButton(prompt, text="Clear", width=70, command=lambda: self.output.clear(), fg_color="transparent").grid(
            row=0, column=2, padx=(4, 12)
        )

        quick = ctk.CTkFrame(self, fg_color="transparent")
        quick.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        commands = [
            ("getprop", "getprop"),
            ("Battery", "dumpsys battery"),
            ("Packages", "pm list packages -3"),
            ("Storage", "df -h"),
            ("IP address", "ip addr"),
            ("Logcat tail", "logcat -d -t 200"),
            ("Live logcat", "logcat"),
        ]
        for index, (label, value) in enumerate(commands):
            ctk.CTkButton(
                quick,
                text=label,
                width=100,
                fg_color="transparent",
                command=lambda v=value: self.run(v),
            ).grid(row=0, column=index, padx=3)

        self.output = OutputPanel(self, height=420)
        self.output.grid(row=3, column=0, sticky="nsew")

    def run(self, preset: str | None = None) -> None:
        serial = self.app.require_serial("adb")
        if not serial:
            return
        command = preset if preset is not None else self.command.get().strip()
        if not command:
            return
        self.output.append(f"$ adb -s {serial} shell {command}")
        self.app.run_command(
            adb_shell(serial, command),
            "Run ADB shell command",
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
        )
