from __future__ import annotations

import threading
import tkinter.messagebox as messagebox
import webbrowser
from typing import Any, Callable

import customtkinter as ctk

from core.devices import Device, device_manager
from core.log_store import LogStore
from core.runner import CommandResult, runner
from core.safety import build_confirmation, requires_confirmation
from core.scripts import ScriptStore
from core.settings import Settings
from core.tools import APP_NAME, APP_VERSION, SUPPORT_URL
from core.vendor_tools import VendorManager
from .ambient import AmbientBackground
from .widgets import ConfirmDialog, NavButton


class FlashBridgeApp(ctk.CTk):
    def __init__(self) -> None:
        self.settings = Settings()
        self.logs = LogStore(int(self.settings.get("log_limit", 5000)))
        self.scripts = ScriptStore()
        self.vendor = VendorManager(self.settings)
        self.current_device_key: str = ""
        self._cancel_event: threading.Event | None = None
        self._poll_stop = threading.Event()
        self._poll_thread: threading.Thread | None = None
        self._pages: dict[str, Any] = {}
        self._nav_buttons: dict[str, NavButton] = {}

        ctk.set_appearance_mode(str(self.settings.get("appearance", "dark")))
        ctk.set_default_color_theme(str(self.settings.get("color_theme", "blue")))

        super().__init__()
        self.configure(fg_color=("#e8f1ff", "#050914"))
        self.ambient = AmbientBackground(self, self.settings)
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1480x920")
        self.minsize(1120, 700)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_sidebar()
        self._build_topbar()
        self._build_content()
        self._build_pages()

        self.logs.log("FlashBridge PC started", source="system")
        device_manager.add_listener(self._on_devices_changed)
        self.show("dashboard")
        self.restart_polling()
        self.tk.call("lower", str(self.ambient))

    # ---------- layout ----------

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=236, corner_radius=0, fg_color=("#e2ebfb", "#081125"))
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)

        title = ctk.CTkFrame(sidebar, fg_color="transparent")
        title.grid(row=0, column=0, sticky="ew", padx=18, pady=(22, 18))
        ctk.CTkLabel(
            title,
            text="FlashBridge",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            title,
            text="PC Device Console",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
        ).pack(anchor="w")
        ctk.CTkFrame(title, height=3, corner_radius=2, fg_color="#22d3ee").pack(
            fill="x", pady=(12, 0)
        )

        self.nav_sections = [
            ("dashboard", "Dashboard"),
            ("devices", "Devices"),
            ("fastboot", "Fastboot"),
            ("shell", "ADB Shell"),
            ("apps", "Apps"),
            ("files", "Files"),
            ("sideload", "Sideload"),
            ("logs", "Logs"),
            ("scripts", "Scripts"),
            ("tools", "Vendor tools"),
            ("settings", "Settings"),
            ("about", "About"),
        ]
        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", padx=12)
        for index, (name, label) in enumerate(self.nav_sections):
            button = NavButton(nav, name, label, lambda n=name: self.show(n))
            button.grid(row=index, column=0, sticky="ew", pady=2)
            self._nav_buttons[name] = button

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=18, pady=18)
        ctk.CTkLabel(
            footer,
            text=f"v{APP_VERSION}  |  MIT License",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray65"),
        ).pack(anchor="w")

    def _build_topbar(self) -> None:
        top = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=("#e2ebfb", "#081125"))
        top.grid(row=0, column=1, sticky="new")
        top.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(top, text="●", text_color="gray", font=ctk.CTkFont(size=18))
        self.status_dot.grid(row=0, column=0, padx=(18, 6))
        self.status_label = ctk.CTkLabel(top, text="Starting", font=ctk.CTkFont(weight="bold"))
        self.status_label.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(top, text="Device", font=ctk.CTkFont(size=12)).grid(row=0, column=2, padx=(10, 4))
        self.device_combo = ctk.CTkComboBox(top, values=["No device"], width=360, command=self._on_device_selected)
        self.device_combo.set("No device")
        self.device_combo.grid(row=0, column=3, padx=4)

        ctk.CTkButton(top, text="Refresh", width=88, command=self.refresh_devices).grid(row=0, column=4, padx=6)
        ctk.CTkButton(top, text="Cancel", width=76, command=self.cancel_current, fg_color="transparent").grid(
            row=0, column=5, padx=6
        )
        ctk.CTkButton(
            top,
            text="Support",
            width=88,
            command=self.open_support,
            fg_color="#f59e0b",
            hover_color="#d97706",
            text_color="#0b1021",
        ).grid(row=0, column=6, padx=(0, 18))

    def _build_content(self) -> None:
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=1, column=1, sticky="nsew", padx=18, pady=(14, 18))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.page_title = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.page_title.grid(row=0, column=1, sticky="ne", padx=18, pady=(4, 0))

    def _build_pages(self) -> None:
        from .pages.apps import AppsPage
        from .pages.dashboard import DashboardPage
        from .pages.devices import DevicesPage
        from .pages.fastboot import FastbootPage
        from .pages.files import FilesPage
        from .pages.logs import LogsPage
        from .pages.scripts import ScriptsPage
        from .pages.shell import ShellPage
        from .pages.sideload import SideloadPage
        from .pages.tools import ToolsPage
        from .pages.about import AboutPage
        from .pages.settings import SettingsPage

        classes = {
            "dashboard": DashboardPage,
            "devices": DevicesPage,
            "fastboot": FastbootPage,
            "shell": ShellPage,
            "apps": AppsPage,
            "files": FilesPage,
            "sideload": SideloadPage,
            "logs": LogsPage,
            "scripts": ScriptsPage,
            "tools": ToolsPage,
            "settings": SettingsPage,
            "about": AboutPage,
        }
        for name, cls in classes.items():
            page = cls(self.content, self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[name] = page

    # ---------- navigation ----------

    def show(self, name: str) -> None:
        if name not in self._pages:
            return
        for page_name, page in self._pages.items():
            if page_name == name:
                page.tkraise()
            else:
                page.grid_remove()
        self._pages[name].grid()
        for nav_name, button in self._nav_buttons.items():
            button.set_active(nav_name == name)
        self.page_title.configure(text=self._pages[name].page_title)
        try:
            self._pages[name].on_show()
        except Exception as exc:
            self.logs.log(f"Page refresh failed: {exc}", "ERROR", "ui")

    # ---------- device handling ----------

    def refresh_devices(self) -> None:
        self.run_async(device_manager.refresh, on_done=lambda devices: self.logs.log(
            f"Device scan complete: {len(devices)} found", source="devices"
        ))

    def current_device(self) -> Device | None:
        return device_manager.find(self.current_device_key)

    def target(self) -> str:
        device = self.current_device()
        return device.label if device else "No device selected"

    def serial_for(self, kind: str) -> str | None:
        device = self.current_device()
        if device and device.kind == kind:
            return device.serial
        if kind == "adb":
            return device_manager.adb_serials()[0] if device_manager.adb_serials() else None
        return device_manager.fastboot_serials()[0] if device_manager.fastboot_serials() else None

    def require_serial(self, kind: str) -> str | None:
        serial = self.serial_for(kind)
        if not serial:
            kind_label = "ADB" if kind == "adb" else "Fastboot"
            messagebox.showwarning("No device", f"No connected {kind_label} device is available.")
        return serial

    def _on_device_selected(self, value: str) -> None:
        for device in device_manager.devices:
            if device.label == value:
                self.current_device_key = device.key
                self.set_status(f"{device.kind.upper()}: {device.state}", "ok")
                break

    def _on_devices_changed(self, devices: list[Device]) -> None:
        def update() -> None:
            labels = [device.label for device in devices]
            self.device_combo.configure(values=labels or ["No device"])
            still_present = any(device.key == self.current_device_key for device in devices)
            if not still_present:
                self.current_device_key = devices[0].key if devices else ""
                self.device_combo.set(devices[0].label if devices else "No device")
            else:
                current = self.current_device()
                if current:
                    self.device_combo.set(current.label)
            if not devices:
                self.set_status("No device", "idle")
            else:
                self.set_status(f"{len(devices)} device(s) detected", "ok")
            for page in self._pages.values():
                try:
                    page.on_devices_changed(devices)
                except Exception as exc:
                    self.logs.log(f"Device update failed: {exc}", "ERROR", "ui")

        self.after(0, update)

    def set_status(self, text: str, kind: str = "idle") -> None:
        colors = {"idle": "gray", "ok": "#16a34a", "run": "#2563eb", "warn": "#d97706", "error": "#dc2626"}
        self.status_label.configure(text=text)
        self.status_dot.configure(text_color=colors.get(kind, "gray"))

    def open_support(self) -> None:
        webbrowser.open(SUPPORT_URL)
        self.logs.log(f"Opened support link: {SUPPORT_URL}", "INFO", "system")
        self.set_status("Support link opened", "ok")

    # ---------- command execution ----------

    def run_async(self, function: Callable, on_done: Callable | None = None) -> None:
        def worker() -> None:
            try:
                result = function()
            except Exception as exc:
                self.logs.log(str(exc), "ERROR", "task")
                result = None
            if on_done:
                self.after(0, lambda: self._safe_callback(on_done, result))

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _safe_callback(callback: Callable, value: Any) -> None:
        try:
            callback(value)
        except Exception as exc:
            print(f"Callback error: {exc}")

    def run_command(
        self,
        args: list[str],
        description: str = "",
        on_line: Callable[[str], None] | None = None,
        on_done: Callable[[CommandResult], None] | None = None,
        confirm: bool = False,
        source: str = "command",
    ) -> None:
        def start() -> None:
            self._cancel_event = threading.Event()
            self.logs.log(f"$ {runner_display(args)}", "CMD", source)
            self.set_status("Command running", "run")

            def worker() -> None:
                def emit(line: str) -> None:
                    self.logs.log(line, "INFO", source)
                    if on_line:
                        self.after(0, lambda text=line: self._safe_callback(on_line, text))

                result = runner.run(args, on_line=emit, cancel_event=self._cancel_event)
                self.after(0, lambda: self._finish_command(result, on_done))

            threading.Thread(target=worker, daemon=True).start()

        if confirm and requires_confirmation(args):
            request = build_confirmation(args, self.target(), description)
            self.show_confirm(request, start)
        else:
            start()

    def _finish_command(self, result: CommandResult, on_done: Callable[[CommandResult], None] | None) -> None:
        level = "INFO" if result.ok else "ERROR"
        state = "ok" if result.ok else "error"
        label = "Command completed" if result.ok else "Command failed"
        if result.cancelled:
            level, state, label = "WARN", "warn", "Command cancelled"
        self.set_status(label, state)
        self.logs.log(f"{label} ({result.duration_ms} ms, exit {result.returncode})", level, "command")
        if on_done:
            self._safe_callback(on_done, result)

    def show_confirm(self, request, on_accept: Callable) -> None:
        if not bool(self.settings.get("confirm_destructive", True)):
            on_accept()
            return
        ConfirmDialog(self, request, on_accept)

    def cancel_current(self) -> None:
        if self._cancel_event:
            self._cancel_event.set()
            self.set_status("Cancelling", "warn")

    # ---------- polling ----------

    def restart_polling(self) -> None:
        self._poll_stop.set()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2)
        self._poll_stop = threading.Event()
        interval = max(500, int(self.settings.get("polling_ms", 2000))) / 1000

        def loop() -> None:
            while not self._poll_stop.wait(interval):
                try:
                    device_manager.refresh()
                except Exception as exc:
                    self.logs.log(f"Device scan failed: {exc}", "ERROR", "devices")

        self._poll_thread = threading.Thread(target=loop, daemon=True)
        self._poll_thread.start()

    def on_close(self) -> None:
        self._poll_stop.set()
        self.ambient.stop()
        runner.cancel_all()
        self.destroy()


def runner_display(args: list[str]) -> str:
    import subprocess

    return subprocess.list2cmdline([str(arg) for arg in args])
