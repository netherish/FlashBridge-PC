from __future__ import annotations

import customtkinter as ctk

from core.tools import APP_NAME, APP_VERSION, license_path
from .base import BasePage


class AboutPage(BasePage):
    page_title = "About"

    def __init__(self, master, app):
        super().__init__(master, app)
        card = ctk.CTkFrame(self, corner_radius=14)
        card.grid(row=0, column=0, sticky="ew", pady=10)
        ctk.CTkLabel(card, text=APP_NAME, font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(card, text=f"Version {APP_VERSION}", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=24)
        ctk.CTkLabel(
            card,
            text="A Windows desktop console for ADB and fastboot device work.",
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(12, 22))

        notices = ctk.CTkFrame(self)
        notices.grid(row=1, column=0, sticky="nsew")
        notices.grid_columnconfigure(0, weight=1)
        notices.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(notices, text="Third-party notices", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6)
        )
        box = ctk.CTkTextbox(notices, font=ctk.CTkFont("Consolas", 11))
        box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        try:
            text = license_path().read_text(encoding="utf-8")
        except Exception:
            text = "Third-party notices file is not available in this build."
        box.insert("end", text)
        box.configure(state="disabled")
