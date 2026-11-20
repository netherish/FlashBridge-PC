from __future__ import annotations

import customtkinter as ctk

from core.devices import device_manager
from core.safety import tool_versions
from .base import BasePage


class DashboardPage(BasePage):
    page_title = "Overview"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(3, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        ctk.CTkLabel(header, text="Dashboard", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Refresh devices", command=self.app.refresh_devices).pack(side="right")

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew")
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.cards = {}
        accent_colors = ("#22d3ee", "#818cf8", "#34d399", "#fbbf24")
        items = [
            ("devices", "Connected devices", "0"),
            ("adb", "ADB devices", "0"),
            ("fastboot", "Fastboot devices", "0"),
            ("tools", "Platform tools", "Checking"),
        ]
        for index, (key, title, value) in enumerate(items):
            card = ctk.CTkFrame(cards, corner_radius=12)
            card.grid(row=0, column=index, sticky="ew", padx=6)
            ctk.CTkFrame(card, height=3, corner_radius=2, fg_color=accent_colors[index]).pack(
                fill="x", padx=12, pady=(10, 0)
            )
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=("gray45", "gray65")).pack(
                anchor="w", padx=16, pady=(10, 2)
            )
            label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold"))
            label.pack(anchor="w", padx=16, pady=(0, 16))
            self.cards[key] = label

        quick = ctk.CTkFrame(self)
        quick.grid(row=2, column=0, sticky="ew", pady=14)
        ctk.CTkLabel(quick, text="Quick actions", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 8)
        )
        actions = ctk.CTkFrame(quick, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        action_colors = ("#0891b2", "#4f46e5", "#059669", "#2563eb", "#7c3aed")
        for index, (text, command) in enumerate(
            [
                ("Reboot to system", self.reboot_system),
                ("Reboot to fastboot", self.reboot_fastboot),
                ("Reboot to recovery", self.reboot_recovery),
                ("Open ADB shell", lambda: self.app.show("shell")),
                ("Fastboot console", lambda: self.app.show("fastboot")),
            ]
        ):
            ctk.CTkButton(
                actions,
                text=text,
                command=command,
                fg_color=action_colors[index],
            ).grid(row=0, column=index, padx=4)

        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=3, column=0, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(log_frame, text="Recent activity", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6)
        )
        self.activity = ctk.CTkTextbox(log_frame, font=ctk.CTkFont("Consolas", 12))
        self.activity.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.activity.configure(state="disabled")

    def on_show(self) -> None:
        self._update_counts()
        entries = self.app.logs.entries()[-30:]
        self.activity.configure(state="normal")
        self.activity.delete("1.0", "end")
        for entry in entries:
            self.activity.insert("end", entry.render() + "\n")
        self.activity.see("end")
        self.activity.configure(state="disabled")

    def on_devices_changed(self, devices) -> None:
        self._update_counts()

    def _update_counts(self) -> None:
        self.cards["devices"].configure(text=str(len(device_manager.devices)))
        self.cards["adb"].configure(text=str(len(device_manager.adb_serials())))
        self.cards["fastboot"].configure(text=str(len(device_manager.fastboot_serials())))

    def _tool_versions(self) -> None:
        try:
            versions = tool_versions()
            text = "Ready" if all(versions.values()) else "Missing"
        except Exception:
            text = "Missing"
        self.after(0, lambda: self.cards["tools"].configure(text=text))

    def reboot_system(self) -> None:
        from core.commands import adb_reboot

        serial = self.app.require_serial("adb")
        if serial:
            self.app.run_command(adb_reboot(serial, "system"), "Reboot to system", confirm=True)

    def reboot_fastboot(self) -> None:
        from core.commands import adb_reboot

        serial = self.app.require_serial("adb")
        if serial:
            self.app.run_command(adb_reboot(serial, "bootloader"), "Reboot to fastboot", confirm=True)

    def reboot_recovery(self) -> None:
        from core.commands import adb_reboot

        serial = self.app.require_serial("adb")
        if serial:
            self.app.run_command(adb_reboot(serial, "recovery"), "Reboot to recovery", confirm=True)
