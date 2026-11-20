from __future__ import annotations

import customtkinter as ctk

from core.devices import device_manager
from .base import BasePage


class StartPage(BasePage):
    page_title = "Quick start"

    def __init__(self, master, app):
        super().__init__(master, app)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(
            header,
            text="Welcome to FlashBridge PC",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Follow three simple steps, then choose what you want to do.",
            font=ctk.CTkFont(size=14),
            text_color=("gray45", "gray65"),
        ).pack(anchor="w", pady=(4, 0))

        self.banner = ctk.CTkFrame(self, corner_radius=14, fg_color=("#dbeafe", "#12213f"))
        self.banner.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self.banner.grid_columnconfigure(0, weight=1)
        self.banner_dot = ctk.CTkLabel(self.banner, text="●", font=ctk.CTkFont(size=18))
        self.banner_dot.grid(row=0, column=0, padx=(18, 6), pady=14)
        self.banner_text = ctk.CTkLabel(
            self.banner,
            text="Checking devices...",
            anchor="w",
            justify="left",
            wraplength=900,
        )
        self.banner_text.grid(row=0, column=1, sticky="w", pady=14)
        ctk.CTkButton(
            self.banner,
            text="Scan again",
            width=110,
            command=self.app.refresh_devices,
        ).grid(row=0, column=2, padx=(8, 8), pady=14)
        ctk.CTkButton(
            self.banner,
            text="ADB help",
            width=100,
            command=lambda: self.app.show_adb_auth_help(),
            fg_color="transparent",
            border_width=1,
            border_color="#38bdf8",
        ).grid(row=0, column=3, padx=(0, 18), pady=14)

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="ew")
        cards.grid_columnconfigure((0, 1, 2), weight=1)
        self.cards = cards

        self._make_card(
            0,
            "1",
            "Connect your phone",
            "Use a working data cable. Unlock the phone and allow USB debugging if it asks.",
            ("Scan for devices", self.app.refresh_devices),
            "#22d3ee",
        )
        self._make_card(
            1,
            "2",
            "Trust this PC",
            "For recovery use, trust this PC in Android first. The helper explains every step.",
            ("ADB authorization help", lambda: self.app.show_adb_auth_help()),
            "#f59e0b",
        )
        self._make_card(
            2,
            "3",
            "Pick a task",
            "Check device details, run ADB shell commands, or launch bundled vendor tools.",
            ("Open vendor tools", lambda: self.app.show("tools")),
            "#818cf8",
        )

        shortcuts = ctk.CTkFrame(self, fg_color="transparent")
        shortcuts.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        ctk.CTkLabel(
            shortcuts,
            text="Common next steps:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(2, 10))
        for label, page in (
            ("Device details", "devices"),
            ("ADB shell", "shell"),
            ("Fastboot", "fastboot"),
            ("Overview", "dashboard"),
        ):
            ctk.CTkButton(
                shortcuts,
                text=label,
                width=120,
                command=lambda p=page: self.app.show(p),
                fg_color="transparent",
            ).pack(side="left", padx=4)

        tip = ctk.CTkFrame(self, corner_radius=12)
        tip.grid(row=4, column=0, sticky="ew", pady=(16, 0))
        ctk.CTkLabel(
            tip,
            text=(
                "Recovery tip: if ADB says 'device unauthorized', reboot to Android, accept "
                "the USB debugging prompt, then return to recovery and enter your decryption "
                "password if asked."
            ),
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", padx=16, pady=14)

    def _make_card(self, column: int, number: str, title: str, body: str, action, color: str) -> None:
        card = ctk.CTkFrame(self.cards, corner_radius=14)
        card.grid(row=0, column=column, sticky="nsew", padx=6)
        ctk.CTkFrame(card, height=4, corner_radius=2, fg_color=color).pack(fill="x", padx=14, pady=(14, 8))
        ctk.CTkLabel(
            card,
            text=f"STEP {number}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=color,
        ).pack(anchor="w", padx=18)
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(4, 6))
        ctk.CTkLabel(
            card,
            text=body,
            wraplength=300,
            justify="left",
            text_color=("gray45", "gray65"),
        ).pack(anchor="w", padx=18, pady=(0, 14))
        ctk.CTkButton(card, text=action[0], command=action[1], width=180).pack(
            anchor="w", padx=18, pady=(0, 18)
        )

    # ---------- live status ----------

    def on_show(self) -> None:
        self._refresh_banner()

    def on_devices_changed(self, devices) -> None:
        self._refresh_banner(devices)

    def _refresh_banner(self, devices=None) -> None:
        devices = list(devices if devices is not None else device_manager.devices)
        if not devices:
            text = "No device detected yet. Connect your phone, enable USB debugging, then scan again."
            color = "#f59e0b"
        elif any(device.state == "unauthorized" for device in devices):
            text = "Device found but not authorized. Open ADB help and follow the trust steps."
            color = "#ef4444"
        else:
            selected = self.app.current_device()
            name = selected.label if selected else devices[0].label
            text = f"Connected: {len(devices)} device(s). Currently using {name}."
            color = "#22c55e"
        self.banner_text.configure(text=text)
        self.banner_dot.configure(text_color=color)
