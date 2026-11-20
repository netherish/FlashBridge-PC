from __future__ import annotations

import os
import tkinter.messagebox as messagebox
from tkinter import filedialog

import customtkinter as ctk

from .base import BasePage


class SettingsPage(BasePage):
    page_title = "Preferences"

    def __init__(self, master, app):
        super().__init__(master, app)
        scroll = ctk.CTkScrollableFrame(self, label_text="Application settings")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", pady=6)

        ctk.CTkLabel(row, text="Appearance", width=150, anchor="w").grid(row=0, column=0, padx=12, pady=8)
        self.appearance = ctk.CTkComboBox(row, values=["dark", "light", "system"], width=180)
        self.appearance.set(str(self.app.settings.get("appearance", "dark")))
        self.appearance.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(row, text="Color theme", width=150, anchor="w").grid(row=1, column=0, padx=12, pady=8)
        self.color = ctk.CTkComboBox(row, values=["blue", "green", "dark-blue"], width=180)
        self.color.set(str(self.app.settings.get("color_theme", "blue")))
        self.color.grid(row=1, column=1, padx=8, pady=8)

        ctk.CTkLabel(row, text="Polling interval (ms)", width=150, anchor="w").grid(row=2, column=0, padx=12, pady=8)
        self.polling = ctk.CTkEntry(row, width=180)
        self.polling.insert(0, str(self.app.settings.get("polling_ms", 2000)))
        self.polling.grid(row=2, column=1, padx=8, pady=8)

        ctk.CTkLabel(row, text="Log history limit", width=150, anchor="w").grid(row=3, column=0, padx=12, pady=8)
        self.log_limit = ctk.CTkEntry(row, width=180)
        self.log_limit.insert(0, str(self.app.settings.get("log_limit", 5000)))
        self.log_limit.grid(row=3, column=1, padx=8, pady=8)

        ctk.CTkLabel(row, text="Confirm destructive actions", width=150, anchor="w").grid(row=4, column=0, padx=12, pady=8)
        self.confirm = ctk.CTkSwitch(row, text="")
        if self.app.settings.get("confirm_destructive", True):
            self.confirm.select()
        self.confirm.grid(row=4, column=1, sticky="w", padx=8, pady=8)

        ctk.CTkLabel(row, text="Advanced operations", width=150, anchor="w").grid(row=5, column=0, padx=12, pady=8)
        self.advanced = ctk.CTkSwitch(row, text="")
        if self.app.settings.get("advanced_mode", True):
            self.advanced.select()
        self.advanced.grid(row=5, column=1, sticky="w", padx=8, pady=8)

        ctk.CTkLabel(row, text="Animated background", width=150, anchor="w").grid(row=6, column=0, padx=12, pady=8)
        self.ambient = ctk.CTkSwitch(row, text="")
        if self.app.settings.get("ambient_background", True):
            self.ambient.select()
        self.ambient.grid(row=6, column=1, sticky="w", padx=8, pady=8)

        ctk.CTkLabel(row, text="Motion blur trails", width=150, anchor="w").grid(row=7, column=0, padx=12, pady=8)
        self.motion = ctk.CTkSwitch(row, text="")
        if self.app.settings.get("motion_blur", True):
            self.motion.select()
        self.motion.grid(row=7, column=1, sticky="w", padx=8, pady=8)

        ctk.CTkLabel(row, text="Animation speed", width=150, anchor="w").grid(row=8, column=0, padx=12, pady=8)
        self.speed = ctk.CTkComboBox(row, values=["calm", "normal", "lively"], width=180)
        self.speed.set(str(self.app.settings.get("ambient_speed", "normal")))
        self.speed.grid(row=8, column=1, padx=8, pady=8)

        tools = ctk.CTkFrame(scroll)
        tools.grid(row=1, column=0, sticky="ew", pady=12)
        tools.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tools, text="Platform tools folder", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 4)
        )
        self.tools_path = ctk.CTkEntry(tools, placeholder_text="Uses bundled tools when empty")
        self.tools_path.insert(0, str(self.app.settings.get("tools_dir", "")))
        self.tools_path.grid(row=1, column=0, sticky="ew", padx=14, pady=4)
        ctk.CTkButton(tools, text="Browse", width=90, command=self.browse_tools).grid(row=1, column=1, padx=8)
        ctk.CTkLabel(
            tools,
            text="Changing this requires restarting FlashBridge PC.",
            text_color=("gray45", "gray65"),
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(2, 12))

        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=10)
        ctk.CTkButton(actions, text="Save settings", command=self.save).pack(side="left", padx=6)
        ctk.CTkButton(actions, text="Reset defaults", command=self.reset, fg_color="transparent").pack(side="left", padx=6)
        ctk.CTkButton(actions, text="Open config folder", command=self.open_config, fg_color="transparent").pack(side="left", padx=6)

    def on_show(self) -> None:
        pass

    def browse_tools(self) -> None:
        folder = filedialog.askdirectory(title="Select folder containing adb.exe and fastboot.exe")
        if folder:
            self.tools_path.delete(0, "end")
            self.tools_path.insert(0, folder)

    def save(self) -> None:
        try:
            polling = max(500, int(self.polling.get()))
            limit = max(100, int(self.log_limit.get()))
        except ValueError:
            messagebox.showerror("Invalid value", "Polling interval and log limit must be numbers.")
            return
        appearance = self.appearance.get()
        color = self.color.get()
        tools = self.tools_path.get().strip()
        self.app.settings.update(
            {
                "appearance": appearance,
                "color_theme": color,
                "ambient_background": bool(self.ambient.get()),
                "motion_blur": bool(self.motion.get()),
                "ambient_speed": self.speed.get(),
                "polling_ms": polling,
                "log_limit": limit,
                "confirm_destructive": bool(self.confirm.get()),
                "advanced_mode": bool(self.advanced.get()),
                "tools_dir": tools,
            }
        )
        if tools:
            os.environ["FLASHBRIDGE_TOOLS_DIR"] = tools
        ctk.set_appearance_mode(appearance)
        ctk.set_default_color_theme(color)
        self.app.ambient.apply_settings()
        self.app.logs.set_limit(limit)
        self.app.restart_polling()
        messagebox.showinfo("Saved", "Settings saved.")

    def reset(self) -> None:
        if messagebox.askyesno("Reset settings", "Restore all settings to defaults?"):
            self.app.settings.reset()
            self.app.ambient.apply_settings()
            messagebox.showinfo("Reset", "Defaults restored. Restart the application to apply all changes.")

    def open_config(self) -> None:
        os.startfile(str(self.app.settings.path.parent))
