from __future__ import annotations

import shlex
import tkinter.messagebox as messagebox

import customtkinter as ctk

from core.commands import adb_args, fastboot_args
from ui.widgets import OutputPanel
from .base import BasePage


class ScriptEditor(ctk.CTkToplevel):
    def __init__(self, master, script: dict | None, on_save):
        super().__init__(master)
        self.title("Script" if script else "New script")
        self.geometry("620x360")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.on_save = on_save
        self.script = script or {}

        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="Name", anchor="w").grid(row=0, column=0, sticky="w", padx=20, pady=(18, 2))
        self.name = ctk.CTkEntry(self)
        self.name.grid(row=1, column=0, sticky="ew", padx=20)
        self.name.insert(0, self.script.get("name", ""))

        ctk.CTkLabel(self, text="Engine", anchor="w").grid(row=2, column=0, sticky="w", padx=20, pady=(10, 2))
        self.engine = ctk.CTkComboBox(self, values=["adb", "fastboot"], width=180)
        self.engine.set(self.script.get("engine", "adb"))
        self.engine.grid(row=3, column=0, sticky="w", padx=20)

        ctk.CTkLabel(self, text="Arguments", anchor="w").grid(row=4, column=0, sticky="w", padx=20, pady=(10, 2))
        self.command = ctk.CTkEntry(self, placeholder_text="Example: shell getprop ro.product.model")
        self.command.grid(row=5, column=0, sticky="ew", padx=20)
        self.command.insert(0, self.script.get("command", ""))

        ctk.CTkLabel(self, text="Description", anchor="w").grid(row=6, column=0, sticky="w", padx=20, pady=(10, 2))
        self.description = ctk.CTkEntry(self)
        self.description.grid(row=7, column=0, sticky="ew", padx=20)
        self.description.insert(0, self.script.get("description", ""))

        self.destructive = ctk.CTkSwitch(self, text="Treat as destructive")
        if self.script.get("destructive"):
            self.destructive.select()
        self.destructive.grid(row=8, column=0, sticky="w", padx=20, pady=10)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=9, column=0, sticky="e", padx=20, pady=12)
        ctk.CTkButton(actions, text="Cancel", command=self.destroy, fg_color="transparent").pack(side="right", padx=6)
        ctk.CTkButton(actions, text="Save", command=self.save).pack(side="right", padx=6)

    def save(self) -> None:
        name = self.name.get().strip()
        command = self.command.get().strip()
        if not name or not command:
            messagebox.showwarning("Missing fields", "Name and arguments are required.")
            return
        values = {
            "name": name,
            "engine": self.engine.get(),
            "command": command,
            "description": self.description.get().strip(),
            "destructive": bool(self.destructive.get()),
        }
        self.on_save(values, self.script)
        self.destroy()


class ScriptsPage(BasePage):
    page_title = "Command scripts"

    def __init__(self, master, app):
        super().__init__(master, app)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Saved scripts", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        for text, command in [
            ("New", self.new_script),
            ("Edit", self.edit_script),
            ("Delete", self.delete_script),
            ("Run", self.run_script),
        ]:
            ctk.CTkButton(header, text=text, width=80, command=command, fg_color="transparent" if text != "Run" else None).pack(
                side="right", padx=3
            )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self.list_frame = ctk.CTkScrollableFrame(body, label_text="Scripts")
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.selected = ctk.StringVar(value="")
        self.output = OutputPanel(body, height=380)
        self.output.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def on_show(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        scripts = self.app.scripts.all()
        if not scripts:
            ctk.CTkLabel(self.list_frame, text="No saved scripts.", text_color="gray").pack(pady=20)
            return
        for index, script in enumerate(scripts):
            radio = ctk.CTkRadioButton(
                self.list_frame,
                text=f"{script.get('name', 'Unnamed')}  [{script.get('engine', 'adb')}]",
                variable=self.selected,
                value=script.get("id", ""),
            )
            radio.grid(row=index, column=0, sticky="w", padx=10, pady=4)

    def _script(self) -> dict | None:
        script_id = self.selected.get()
        for script in self.app.scripts.all():
            if script.get("id") == script_id:
                return script
        return None

    def new_script(self) -> None:
        ScriptEditor(self, None, self._save)

    def edit_script(self) -> None:
        script = self._script()
        if script:
            ScriptEditor(self, script, self._save)
        else:
            messagebox.showinfo("No selection", "Select a script first.")

    def _save(self, values: dict, existing: dict | None) -> None:
        if existing:
            self.app.scripts.update(existing["id"], values)
        else:
            self.app.scripts.add(values)
        self.refresh()

    def delete_script(self) -> None:
        script = self._script()
        if script and messagebox.askyesno("Delete script", f"Delete '{script.get('name')}'?"):
            self.app.scripts.delete(script["id"])
            self.refresh()

    def run_script(self) -> None:
        script = self._script()
        if not script:
            messagebox.showinfo("No selection", "Select a script first.")
            return
        engine = script.get("engine", "adb")
        serial = self.app.require_serial(engine)
        if not serial:
            return
        try:
            parts = shlex.split(script.get("command", ""), posix=False)
        except ValueError as exc:
            messagebox.showerror("Invalid script", str(exc))
            return
        args = adb_args(serial, *parts) if engine == "adb" else fastboot_args(serial, *parts)
        self.output.append(f"$ {' '.join(args)}")
        self.app.run_command(
            args,
            script.get("description") or script.get("name", "Run script"),
            confirm=bool(script.get("destructive")),
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
        )
