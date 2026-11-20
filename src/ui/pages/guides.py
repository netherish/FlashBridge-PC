from __future__ import annotations

import threading
import tkinter.messagebox as messagebox
from dataclasses import dataclass
from tkinter import filedialog

import customtkinter as ctk

from core.commands import adb_reboot
from core.devices import device_manager
from core.vendor_tools import TOOL_BY_ID, VendorTool

from .base import BasePage


@dataclass(frozen=True)
class Guide:
    id: str
    name: str
    blurb: str
    accent: str
    steps: tuple[str, ...]
    warning: str = ""


GUIDES: tuple[Guide, ...] = (
    Guide(
        id="adb-recovery",
        name="ADB in recovery",
        blurb="Fix unauthorized ADB and use ADB shell from a custom recovery.",
        accent="#22d3ee",
        steps=(
            "In Android, enable USB debugging and accept 'Allow USB debugging?' for this PC.",
            "Keep the cable connected and reboot to recovery. Recovery does not show the Android trust prompt.",
            "Enter your decryption password in recovery if it asks. Some recoveries also need ADB enabled in their own menu.",
            "Use the buttons below to check the device or open the guided ADB authorization helper.",
        ),
        warning="If ADB says 'device unauthorized', trust this PC in Android first, then return to recovery.",
    ),
    Guide(
        id="xiaomi-unlock",
        name="Xiaomi unlock",
        blurb="Prepare bootloader unlock with the official Mi Unlock tool.",
        accent="#f59e0b",
        steps=(
            "On the phone, open Settings > About phone and tap MIUI version seven times to enable Developer options.",
            "In Developer options, turn on USB debugging and OEM unlocking, then link your Xiaomi account in 'Device unlocking status'.",
            "Sign in to Mi Unlock with the same authorized Xiaomi account. Wait for any account timer to finish.",
            "Power off, hold Volume Down + Power to enter Fastboot, and connect the USB cable.",
            "Confirm the device below, then open Mi Unlock and click Unlock in that tool.",
        ),
        warning="Unlocking erases all data and may affect warranty. Only unlock devices you are authorized to modify.",
    ),
    Guide(
        id="xiaomi-flash",
        name="Xiaomi stock ROM",
        blurb="Select the exact Fastboot ROM and prepare Mi Flash Tool.",
        accent="#818cf8",
        steps=(
            "Download the exact Fastboot ROM for the device model and region.",
            "Extract the ROM and choose the extracted folder below. It should contain the fastboot images and flash scripts.",
            "Boot the phone to Fastboot with Volume Down + Power, then connect the USB cable.",
            "Choose the wipe option and confirm the device below.",
            "Open Mi Flash Tool, select the same ROM folder and device, then start the flash in that tool.",
        ),
        warning="Using the wrong ROM or wipe option can permanently damage the device. Verify the model and region first.",
    ),
    Guide(
        id="mediatek-flash",
        name="MediaTek / SP Flash",
        blurb="Prepare scatter flashing and MTK drivers for authorized service use.",
        accent="#34d399",
        steps=(
            "Install the bundled MTK USB VCOM driver if the device does not appear as a MediaTek port.",
            "Download the firmware that matches the exact model and select its scatter file below.",
            "Power off the phone. Hold Volume Up or Volume Down with Power while connecting the cable until the MTK port appears.",
            "Choose SP Flash Tool v5 or v6, then open it and load the same scatter file.",
            "In SP Flash Tool, confirm the operation and click Download. The auth bypass button is for authorized service only.",
        ),
        warning="MediaTek auth bypass can override device protections. Use it only on devices you own or have written authorization to service.",
    ),
    Guide(
        id="qualcomm-flash",
        name="Qualcomm / QFIL",
        blurb="Prepare Qualcomm drivers and QFIL firmware files.",
        accent="#60a5fa",
        steps=(
            "Install the bundled Qualcomm USB driver, then install QPST if QFIL is not available yet.",
            "Download the Qualcomm firmware for the exact model. Select rawprogram and patch XML files below.",
            "Put the device into the service mode required by your model, commonly EDL or Fastboot.",
            "Open QFIL, select the correct COM port and the XML files, then start the download in QFIL.",
        ),
        warning="EDL service access may require authorized credentials. Do not attempt to bypass manufacturer security.",
    ),
    Guide(
        id="samsung-flash",
        name="Samsung / Odin",
        blurb="Use bundled Heimdall or an Odin executable you already have.",
        accent="#f472b6",
        steps=(
            "Download the exact Samsung firmware for the model and CSC region.",
            "Power off the phone. Hold Volume Down + Power, then press Volume Up to enter Download Mode.",
            "Use bundled Heimdall for supported operations, or set a path to an Odin executable you already have.",
            "In Odin, select BL, AP, CP and CSC files, confirm the model, then click Start.",
        ),
        warning="Odin is not bundled because no official public Windows package was found. Heimdall is the bundled alternative.",
    ),
)


class GuidesPage(BasePage):
    page_title = "Guided tools"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._guide_buttons: dict[str, ctk.CTkButton] = {}
        self._fields: dict[str, ctk.CTkEntry] = {}
        self.current_guide = GUIDES[0].id

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Guided tools",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text="Simple steps for common tasks. FlashBridge checks files and devices; official tools open only when needed.",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
        ).grid(row=1, column=0, sticky="w")
        ctk.CTkButton(
            header,
            text="Vendor tools list",
            width=140,
            fg_color="transparent",
            command=lambda: self.app.show("tools"),
        ).grid(row=0, column=1, rowspan=2, padx=6)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        chooser = ctk.CTkScrollableFrame(body, width=230, fg_color="transparent")
        chooser.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ctk.CTkLabel(
            chooser,
            text="Choose a task",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(6, 10))
        for index, guide in enumerate(GUIDES):
            button = ctk.CTkButton(
                chooser,
                text=guide.name,
                anchor="w",
                fg_color="transparent",
                command=lambda guide_id=guide.id: self.select(guide_id),
            )
            button.grid(row=index + 1, column=0, sticky="ew", pady=2)
            self._guide_buttons[guide.id] = button

        panel = ctk.CTkFrame(body, corner_radius=14)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        self.banner = ctk.CTkFrame(panel, corner_radius=12, fg_color=("#dbeafe", "#12213f"))
        self.banner.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        self.banner.grid_columnconfigure(1, weight=1)
        self.banner_dot = ctk.CTkLabel(self.banner, text="●", font=ctk.CTkFont(size=18))
        self.banner_dot.grid(row=0, column=0, padx=(14, 6), pady=10)
        self.banner_text = ctk.CTkLabel(
            self.banner,
            text="Checking devices...",
            anchor="w",
            justify="left",
            wraplength=760,
        )
        self.banner_text.grid(row=0, column=1, sticky="w", pady=10)
        ctk.CTkButton(
            self.banner,
            text="Scan devices",
            width=110,
            command=self.app.refresh_devices,
        ).grid(row=0, column=2, padx=4, pady=10)
        ctk.CTkButton(
            self.banner,
            text="ADB help",
            width=90,
            fg_color="transparent",
            border_width=1,
            border_color="#38bdf8",
            command=lambda: self.app.show_adb_auth_help(),
        ).grid(row=0, column=3, padx=(4, 14), pady=10)

        self.detail = ctk.CTkScrollableFrame(panel, label_text="")
        self.detail.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.detail.grid_columnconfigure(0, weight=1)

        self.select(self.current_guide)

    # ---------- navigation and live status ----------

    def on_show(self) -> None:
        self._refresh_banner()

    def on_devices_changed(self, devices) -> None:
        self._refresh_banner(devices)
        if self.winfo_exists() and self._fields:
            self._update_preview()

    def select(self, guide_id: str) -> None:
        guide = next((item for item in GUIDES if item.id == guide_id), None)
        if guide is None:
            return
        self.current_guide = guide_id
        self._fields.clear()
        for child in self.detail.winfo_children():
            child.destroy()
        for key, button in self._guide_buttons.items():
            button.configure(fg_color=("#2563eb", "#1d4ed8") if key == guide_id else "transparent")

        ctk.CTkLabel(
            self.detail,
            text=guide.name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=guide.accent,
        ).grid(row=0, column=0, sticky="w", pady=(4, 2))
        ctk.CTkLabel(
            self.detail,
            text=guide.blurb,
            wraplength=820,
            justify="left",
            text_color=("gray45", "gray65"),
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        row = 2
        if guide.warning:
            warning = ctk.CTkFrame(self.detail, corner_radius=10, fg_color=("#fff1d6", "#3b2a11"))
            warning.grid(row=row, column=0, sticky="ew", pady=(0, 12))
            ctk.CTkLabel(
                warning,
                text=guide.warning,
                wraplength=820,
                justify="left",
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=14, pady=10)
            row += 1

        row = self._build_steps(guide, row)
        row = self._build_options(guide, row)
        row = self._build_device_actions(guide, row)
        row = self._build_preview(row)
        self._build_actions(guide, row)
        self._refresh_banner()
        self._update_preview()

    # ---------- panel builders ----------

    def _build_steps(self, guide: Guide, row: int) -> int:
        card = ctk.CTkFrame(self.detail, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            card,
            text="Steps",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 6))
        for index, step in enumerate(guide.steps, start=1):
            ctk.CTkLabel(
                card,
                text=str(index),
                width=26,
                height=26,
                corner_radius=13,
                fg_color=guide.accent,
                text_color="#081125",
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=index, column=0, padx=(14, 8), pady=3, sticky="nw")
            ctk.CTkLabel(
                card,
                text=step,
                wraplength=780,
                justify="left",
            ).grid(row=index, column=1, sticky="w", pady=3)
        ctk.CTkLabel(card, text="", height=4).grid(row=len(guide.steps) + 1, column=0)
        return row + 1

    def _build_options(self, guide: Guide, row: int) -> int:
        card = ctk.CTkFrame(self.detail, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            card,
            text="Files and options",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(12, 6))

        fields: list[tuple[str, str, str, str]] = []
        if guide.id == "xiaomi-flash":
            fields.append(("rom", "Extracted ROM folder", "dir", "Select the folder containing the Fastboot images"))
        elif guide.id == "mediatek-flash":
            fields.append(("scatter", "Scatter file", "file", "Select the firmware .txt scatter file"))
        elif guide.id == "qualcomm-flash":
            fields.append(("rawprogram", "Raw program XML", "file", "rawprogram0.xml"))
            fields.append(("patch", "Patch XML", "file", "patch0.xml"))
        elif guide.id == "samsung-flash":
            fields.append(("odin", "Odin executable (optional)", "file", "Only if you already have Odin"))

        option_row = 1
        for key, label, kind, placeholder in fields:
            ctk.CTkLabel(card, text=label, width=150, anchor="w").grid(
                row=option_row, column=0, sticky="w", padx=(14, 6), pady=4
            )
            entry = ctk.CTkEntry(card, placeholder_text=placeholder)
            entry.grid(row=option_row, column=1, sticky="ew", pady=4)
            if key == "odin":
                entry.insert(0, self.app.vendor.user_path("odin"))
            entry.bind("<KeyRelease>", lambda _event: self._update_preview())
            self._fields[key] = entry
            ctk.CTkButton(
                card,
                text="Browse",
                width=80,
                fg_color="transparent",
                command=lambda k=key, t=kind: self._browse(k, t),
            ).grid(row=option_row, column=2, padx=(6, 14), pady=4)
            option_row += 1

        if guide.id == "xiaomi-flash":
            ctk.CTkLabel(card, text="Wipe option", width=150, anchor="w").grid(
                row=option_row, column=0, sticky="w", padx=(14, 6), pady=4
            )
            self.clean_combo = ctk.CTkComboBox(
                card,
                values=("clean", "clean and lock", "save user data"),
                command=lambda _value: self._update_preview(),
                width=220,
            )
            self.clean_combo.set("clean")
            self.clean_combo.grid(row=option_row, column=1, sticky="w", pady=4)
            option_row += 1
        elif guide.id == "mediatek-flash":
            ctk.CTkLabel(card, text="SP Flash Tool", width=150, anchor="w").grid(
                row=option_row, column=0, sticky="w", padx=(14, 6), pady=4
            )
            self.sp_version_combo = ctk.CTkComboBox(
                card,
                values=("v5", "v6"),
                command=lambda _value: self._update_preview(),
                width=220,
            )
            self.sp_version_combo.set("v6")
            self.sp_version_combo.grid(row=option_row, column=1, sticky="w", pady=4)
            option_row += 1

        if option_row == 1:
            ctk.CTkLabel(
                card,
                text="No files are required for this task.",
                text_color=("gray45", "gray65"),
            ).grid(row=1, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 12))
        else:
            ctk.CTkLabel(card, text="", height=4).grid(row=option_row, column=0)
        return row + 1

    def _build_device_actions(self, guide: Guide, row: int) -> int:
        card = ctk.CTkFrame(self.detail, fg_color="transparent")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkButton(card, text="Check device", width=120, command=self.app.refresh_devices).pack(
            side="left", padx=(2, 6)
        )
        if guide.id in {"adb-recovery", "xiaomi-unlock"}:
            ctk.CTkButton(card, text="Reboot to fastboot", width=150, command=self._reboot_fastboot).pack(
                side="left", padx=6
            )
        if guide.id == "adb-recovery":
            ctk.CTkButton(
                card,
                text="Open ADB shell",
                width=130,
                fg_color="transparent",
                command=lambda: self.app.show("shell"),
            ).pack(side="left", padx=6)
        else:
            ctk.CTkButton(
                card,
                text="Fastboot console",
                width=130,
                fg_color="transparent",
                command=lambda: self.app.show("fastboot"),
            ).pack(side="left", padx=6)
        return row + 1

    def _build_preview(self, row: int) -> int:
        card = ctk.CTkFrame(self.detail, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card,
            text="Ready summary",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        self.preview = ctk.CTkTextbox(card, height=90, font=ctk.CTkFont("Consolas", 11))
        self.preview.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.preview.configure(state="disabled")
        return row + 1

    def _build_actions(self, guide: Guide, row: int) -> None:
        card = ctk.CTkFrame(self.detail, fg_color="transparent")
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))

        if guide.id == "adb-recovery":
            ctk.CTkButton(
                card,
                text="ADB authorization help",
                width=200,
                command=lambda: self.app.show_adb_auth_help(),
            ).pack(side="left", padx=(2, 8))
        elif guide.id == "mediatek-flash":
            ctk.CTkButton(
                card,
                text="Open SP Flash Tool",
                width=190,
                command=self._open_sp_flash,
            ).pack(side="left", padx=(2, 8))
            ctk.CTkButton(
                card,
                text="Install MTK driver",
                width=150,
                fg_color="transparent",
                command=lambda: self._launch_tool("mtk-vcom-driver"),
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                card,
                text="MTK auth bypass (authorized use)",
                width=240,
                fg_color="#b45309",
                hover_color="#92400e",
                command=lambda: self._launch_tool("mtk-auth-bypass"),
            ).pack(side="left", padx=6)
        elif guide.id == "qualcomm-flash":
            ctk.CTkButton(
                card,
                text="Install Qualcomm driver",
                width=180,
                fg_color="transparent",
                command=lambda: self._launch_tool("qualcomm-usb-driver"),
            ).pack(side="left", padx=(2, 6))
            ctk.CTkButton(
                card,
                text="Install QPST / QFIL",
                width=170,
                command=lambda: self._launch_tool("qpst-qfil"),
            ).pack(side="left", padx=6)
        elif guide.id == "samsung-flash":
            ctk.CTkButton(
                card,
                text="Open Heimdall frontend",
                width=190,
                command=lambda: self._launch_tool("heimdall-frontend"),
            ).pack(side="left", padx=(2, 6))
            ctk.CTkButton(
                card,
                text="Open Odin",
                width=120,
                fg_color="transparent",
                command=lambda: self._launch_tool("odin"),
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                card,
                text="Save Odin path",
                width=130,
                fg_color="transparent",
                command=self._save_odin_path,
            ).pack(side="left", padx=6)
        elif guide.id == "xiaomi-unlock":
            ctk.CTkButton(
                card,
                text="Open Mi Unlock",
                width=180,
                command=lambda: self._launch_tool("mi-unlock"),
            ).pack(side="left", padx=(2, 8))
            ctk.CTkButton(
                card,
                text="Open vendor tools list",
                width=180,
                fg_color="transparent",
                command=lambda: self.app.show("tools"),
            ).pack(side="left", padx=6)
        else:
            ctk.CTkButton(
                card,
                text="Open Mi Flash Tool",
                width=190,
                command=lambda: self._launch_tool("mi-flash"),
            ).pack(side="left", padx=(2, 8))
            ctk.CTkButton(
                card,
                text="Open vendor tools list",
                width=180,
                fg_color="transparent",
                command=lambda: self.app.show("tools"),
            ).pack(side="left", padx=6)

    # ---------- actions ----------

    def _browse(self, key: str, kind: str) -> None:
        if kind == "dir":
            path = filedialog.askdirectory(title="Choose folder")
        else:
            path = filedialog.askopenfilename(title="Choose file", filetypes=[("All supported", "*.*")])
        if not path:
            return
        entry = self._fields.get(key)
        if entry is not None:
            entry.delete(0, "end")
            entry.insert(0, path)
        if key == "odin":
            self.app.vendor.set_user_path("odin", path)
        self._update_preview()

    def _save_odin_path(self) -> None:
        entry = self._fields.get("odin")
        path = entry.get().strip() if entry else ""
        if not path:
            self._browse("odin", "file")
            return
        self.app.vendor.set_user_path("odin", path)
        messagebox.showinfo("Guided tools", "Odin path saved.")

    def _open_sp_flash(self) -> None:
        combo = getattr(self, "sp_version_combo", None)
        tool_id = "sp-flash-v6" if combo is None or combo.get() == "v6" else "sp-flash-v5"
        self._launch_tool(tool_id)

    def _reboot_fastboot(self) -> None:
        serial = self.app.require_serial("adb")
        if serial:
            self.app.run_command(
                adb_reboot(serial, "bootloader"),
                "Reboot to fastboot",
                confirm=True,
                source="guides",
            )

    def _launch_tool(self, tool_id: str) -> None:
        tool = TOOL_BY_ID.get(tool_id)
        if tool is None:
            return
        self.app.set_status(f"Preparing {tool.name}", "run")

        def worker() -> None:
            try:
                self.app.vendor.launch(tool)
                message = f"{tool.name} started. Follow the steps shown in FlashBridge while using that tool."
                error = False
            except Exception as exc:
                message = f"Could not start {tool.name}: {exc}"
                error = True
            try:
                self.app.after(0, lambda: self._launch_done(message, error))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _launch_done(self, message: str, error: bool) -> None:
        self.app.set_status("Vendor tool failed" if error else "Vendor tool started", "error" if error else "ok")
        self.app.logs.log(message, "ERROR" if error else "INFO", "vendor")
        (messagebox.showerror if error else messagebox.showinfo)("Guided tools", message)

    # ---------- previews ----------

    def _value(self, key: str) -> str:
        entry = self._fields.get(key)
        return entry.get().strip() if entry is not None else ""

    def _update_preview(self) -> None:
        if not hasattr(self, "preview"):
            return
        lines: list[str] = []
        devices = list(device_manager.devices)
        selected = self.app.current_device()
        lines.append(f"Device: {selected.label if selected else (devices[0].label if devices else 'not connected')}")
        guide_id = self.current_guide

        if guide_id == "adb-recovery":
            lines.append("Next: use ADB shell only after the device is trusted and recovery ADB is enabled.")
            if any(device.state == "unauthorized" for device in devices):
                lines.append("Status: unauthorized. Open ADB help and trust this PC in Android first.")
        elif guide_id == "xiaomi-unlock":
            lines.append("Account: use the authorized Xiaomi account linked on the device.")
            lines.append("Mode required: Fastboot. Official tool: Mi Unlock.")
        elif guide_id == "xiaomi-flash":
            lines.append(f"ROM folder: {self._value('rom') or 'not selected'}")
            combo = getattr(self, "clean_combo", None)
            lines.append(f"Wipe option: {combo.get() if combo else 'clean'}")
            lines.append("Official tool: Mi Flash Tool. Verify model and region before flashing.")
        elif guide_id == "mediatek-flash":
            lines.append(f"Scatter file: {self._value('scatter') or 'not selected'}")
            combo = getattr(self, "sp_version_combo", None)
            lines.append(f"Official tool: SP Flash Tool {combo.get() if combo else 'v6'}.")
            lines.append("Auth bypass is shown only for authorized service use.")
        elif guide_id == "qualcomm-flash":
            lines.append(f"Raw program: {self._value('rawprogram') or 'not selected'}")
            lines.append(f"Patch file: {self._value('patch') or 'not selected'}")
            lines.append("Official tool: QFIL. Select the correct COM port in QFIL.")
        elif guide_id == "samsung-flash":
            odin = self._value("odin") or self.app.vendor.user_path("odin")
            lines.append(f"Odin: {odin or 'not set'}")
            lines.append("Mode required: Download Mode. Bundled alternative: Heimdall frontend.")

        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("end", "\n".join(lines))
        self.preview.configure(state="disabled")

    def _refresh_banner(self, devices=None) -> None:
        devices = list(devices if devices is not None else device_manager.devices)
        if not devices:
            text = "No device detected. Connect the phone with a data cable, then click Scan devices."
            color = "#f59e0b"
        elif any(device.state == "unauthorized" for device in devices):
            text = "Device found but not authorized. Open ADB help and trust this PC in Android first."
            color = "#ef4444"
        else:
            selected = self.app.current_device()
            name = selected.label if selected else devices[0].label
            text = f"Connected: {len(devices)} device(s). Currently using {name}."
            color = "#22c55e"
        self.banner_text.configure(text=text)
        self.banner_dot.configure(text_color=color)
