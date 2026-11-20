from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog

from core.commands import (
    adb_clear_data,
    adb_force_stop,
    adb_install,
    adb_packages,
    adb_uninstall,
)
from ui.widgets import OutputPanel
from .base import BasePage


class AppsPage(BasePage):
    page_title = "Application manager"

    def __init__(self, master, app):
        super().__init__(master, app)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Applications", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Refresh", command=self.refresh).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.list_frame = ctk.CTkScrollableFrame(body, label_text="Third-party packages")
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.selected = ctk.StringVar(value="")

        self.output = OutputPanel(body, height=360)
        self.output.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        install = ctk.CTkFrame(self)
        install.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        install.grid_columnconfigure(0, weight=1)
        self.apk_path = ctk.CTkEntry(install, placeholder_text="Select an APK file")
        self.apk_path.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=10)
        ctk.CTkButton(install, text="Browse", width=80, command=self.browse_apk).grid(row=0, column=1, padx=4)
        self.reinstall = ctk.CTkSwitch(install, text="Reinstall")
        self.reinstall.grid(row=0, column=2, padx=6)
        self.grant = ctk.CTkSwitch(install, text="Grant permissions")
        self.grant.grid(row=0, column=3, padx=6)
        ctk.CTkButton(install, text="Install", command=self.install).grid(row=0, column=4, padx=(6, 12))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=8)
        ctk.CTkButton(actions, text="Uninstall", fg_color="#dc2626", command=self.uninstall).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Force stop", command=self.force_stop).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Clear data", fg_color="#b45309", command=self.clear_data).pack(side="left", padx=4)

    def on_show(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        serial = self.app.require_serial("adb")
        if not serial:
            return
        self.output.append(f"$ adb -s {serial} shell pm list packages -3")

        def finish(result) -> None:
            packages = []
            for line in result.output.splitlines():
                if line.startswith("package:"):
                    packages.append(line.split(":", 1)[1].strip())
            self._render(packages)
            self.output.append(f"Found {len(packages)} package(s)")

        self.app.run_command(adb_packages(serial), "List packages", on_done=finish)

    def _render(self, packages: list[str]) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        if not packages:
            ctk.CTkLabel(self.list_frame, text="No third-party packages found.", text_color="gray").pack(pady=20)
            return
        for index, package in enumerate(packages):
            ctk.CTkRadioButton(
                self.list_frame,
                text=package,
                variable=self.selected,
                value=package,
            ).grid(row=index, column=0, sticky="w", padx=10, pady=3)

    def browse_apk(self) -> None:
        path = filedialog.askopenfilename(
            title="Select APK",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")],
            initialdir=self.app.settings.get("last_apk_folder") or None,
        )
        if path:
            from pathlib import Path

            self.apk_path.delete(0, "end")
            self.apk_path.insert(0, path)
            self.app.settings.set("last_apk_folder", str(Path(path).parent))

    def install(self) -> None:
        serial = self.app.require_serial("adb")
        path = self.apk_path.get().strip()
        if not serial or not path:
            return
        self.app.run_command(
            adb_install(
                serial,
                path,
                reinstall=bool(self.reinstall.get()),
                grant=bool(self.grant.get()),
            ),
            "Install APK",
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
        )

    def _package(self) -> str | None:
        package = self.selected.get().strip()
        if not package:
            return None
        return package

    def uninstall(self) -> None:
        serial = self.app.require_serial("adb")
        package = self._package()
        if serial and package:
            self.app.run_command(
                adb_uninstall(serial, package),
                f"Uninstall {package}",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
                on_done=lambda r: self.refresh() if r.ok else None,
            )

    def force_stop(self) -> None:
        serial = self.app.require_serial("adb")
        package = self._package()
        if serial and package:
            self.app.run_command(
                adb_force_stop(serial, package),
                f"Force stop {package}",
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )

    def clear_data(self) -> None:
        serial = self.app.require_serial("adb")
        package = self._package()
        if serial and package:
            self.app.run_command(
                adb_clear_data(serial, package),
                f"Clear data for {package}",
                confirm=True,
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
            )
