from __future__ import annotations

import customtkinter as ctk
import tkinter.messagebox as messagebox

from core.commands import adb_connect, adb_disconnect, adb_getprop, fastboot_getvar_all
from core.devices import device_manager
from .base import BasePage


class DevicesPage(BasePage):
    page_title = "Device manager"

    def __init__(self, master, app):
        super().__init__(master, app)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(header, text="Detected devices", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Scan now", command=self.app.refresh_devices).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.list_frame = ctk.CTkScrollableFrame(body, label_text="Devices")
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.list_frame.grid_columnconfigure(0, weight=1)

        detail = ctk.CTkFrame(body)
        detail.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        detail.grid_columnconfigure(0, weight=1)
        detail.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(detail, text="Device details", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 6)
        )
        self.details = ctk.CTkTextbox(detail, font=ctk.CTkFont("Consolas", 12))
        self.details.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.details.configure(state="disabled")

        net = ctk.CTkFrame(self)
        net.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ctk.CTkLabel(net, text="ADB over network", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12)
        self.address = ctk.CTkEntry(net, placeholder_text="192.168.1.20:5555", width=220)
        self.address.pack(side="left", padx=4)
        ctk.CTkButton(net, text="Connect", command=self.connect).pack(side="left", padx=4)
        ctk.CTkButton(net, text="Disconnect all", command=self.disconnect).pack(side="left", padx=4)

    def on_show(self) -> None:
        self._render_list(device_manager.devices)

    def on_devices_changed(self, devices) -> None:
        self._render_list(devices)

    def _render_list(self, devices) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        if not devices:
            ctk.CTkLabel(self.list_frame, text="No devices detected.", text_color="gray").pack(pady=24)
            return
        for index, device in enumerate(devices):
            row = ctk.CTkFrame(self.list_frame)
            row.grid(row=index, column=0, sticky="ew", pady=4)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                row,
                text=f"{device.label}\nState: {device.state}  Serial: {device.serial}",
                justify="left",
            ).grid(row=0, column=0, sticky="w", padx=10, pady=8)
            ctk.CTkButton(row, text="Select", width=70, command=lambda d=device: self.select(d)).grid(
                row=0, column=1, padx=4
            )
            ctk.CTkButton(row, text="Info", width=60, command=lambda d=device: self.info(d)).grid(
                row=0, column=2, padx=4
            )

    def select(self, device) -> None:
        self.app.current_device_key = device.key
        self.app.device_combo.set(device.label)
        self.app.set_status(f"{device.kind.upper()}: {device.state}", "ok")

    def info(self, device) -> None:
        self.select(device)

        def finish(result) -> None:
            text = result.output or "No details returned."
            self.details.configure(state="normal")
            self.details.delete("1.0", "end")
            self.details.insert("end", text)
            self.details.configure(state="disabled")

        if device.kind == "adb":
            self.app.run_command(adb_getprop(device.serial), "Read ADB properties", on_done=finish)
        else:
            self.app.run_command(fastboot_getvar_all(device.serial), "Read fastboot variables", on_done=finish)

    def connect(self) -> None:
        address = self.address.get().strip()
        if not address:
            messagebox.showwarning("Missing address", "Enter a host:port address.")
            return
        self.app.run_command(adb_connect(address), "Connect ADB over network", on_done=lambda r: self.app.refresh_devices())

    def disconnect(self) -> None:
        self.app.run_command(adb_disconnect(), "Disconnect network ADB", on_done=lambda r: self.app.refresh_devices())
