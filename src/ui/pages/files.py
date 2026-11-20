from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.commands import adb_delete_file, adb_list_files, adb_pull, adb_push
from ui.widgets import OutputPanel
from .base import BasePage


class FilesPage(BasePage):
    page_title = "File manager"

    def __init__(self, master, app):
        super().__init__(master, app)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Device files", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        nav = ctk.CTkFrame(self)
        nav.grid(row=1, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(nav, text="Path").pack(side="left", padx=(12, 6))
        self.path = ctk.CTkEntry(nav)
        self.path.insert(0, "/sdcard/")
        self.path.pack(side="left", fill="x", expand=True, padx=4, pady=10)
        self.path.bind("<Return>", lambda _: self.list_directory())
        ctk.CTkButton(nav, text="Open", width=80, command=self.list_directory).pack(side="left", padx=4)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.list_frame = ctk.CTkScrollableFrame(body, label_text="Directory contents")
        self.list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.selected = ctk.StringVar(value="")
        self.output = OutputPanel(body, height=360)
        self.output.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        transfer = ctk.CTkFrame(self)
        transfer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        transfer.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(transfer, text="Push file", command=self.push).grid(row=0, column=0, padx=(12, 6), pady=10)
        self.local_file = ctk.CTkEntry(transfer, placeholder_text="Local file to push")
        self.local_file.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkButton(transfer, text="Browse", width=80, command=self.browse_push).grid(row=0, column=2, padx=4)
        ctk.CTkButton(transfer, text="Pull selected", command=self.pull).grid(row=1, column=0, padx=(12, 6), pady=(0, 10))
        self.local_dir = ctk.CTkEntry(transfer, placeholder_text="Local folder for pulled files")
        self.local_dir.grid(row=1, column=1, sticky="ew", padx=4, pady=(0, 10))
        ctk.CTkButton(transfer, text="Browse", width=80, command=self.browse_pull).grid(row=1, column=2, padx=4, pady=(0, 10))
        ctk.CTkButton(transfer, text="Delete selected", fg_color="#dc2626", command=self.delete).grid(row=2, column=0, pady=(0, 10))

    def on_show(self) -> None:
        if not self.list_frame.winfo_children():
            self.list_directory()

    def list_directory(self) -> None:
        serial = self.app.require_serial("adb")
        if not serial:
            return
        from core.commands import parse_ls

        remote = self.path.get().strip() or "/sdcard/"

        def finish(result) -> None:
            rows = parse_ls(result.output)
            self._render(rows)
            self.output.append(f"{remote}: {len(rows)} entry/entries")

        self.app.run_command(adb_list_files(serial, remote), "List directory", on_done=finish)

    def _render(self, rows: list[dict[str, str]]) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        if not rows:
            ctk.CTkLabel(self.list_frame, text="Directory is empty.", text_color="gray").pack(pady=20)
            return
        for index, row in enumerate(rows):
            name = row["name"]
            ctk.CTkRadioButton(
                self.list_frame,
                text=f"{name}    {row['size']}",
                variable=self.selected,
                value=name,
            ).grid(row=index, column=0, sticky="w", padx=10, pady=2)

    def browse_push(self) -> None:
        path = filedialog.askopenfilename(title="Select file to push")
        if path:
            self.local_file.delete(0, "end")
            self.local_file.insert(0, path)

    def browse_pull(self) -> None:
        path = filedialog.askdirectory(title="Select destination folder")
        if path:
            self.local_dir.delete(0, "end")
            self.local_dir.insert(0, path)

    def _remote_selected(self) -> str:
        base = self.path.get().strip().rstrip("/")
        name = self.selected.get().strip()
        return f"{base}/{name}" if base and name else name

    def push(self) -> None:
        serial = self.app.require_serial("adb")
        local = self.local_file.get().strip()
        remote = self.path.get().strip() or "/sdcard/"
        if serial and local:
            self.app.run_command(
                adb_push(serial, local, remote),
                "Push file",
                on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
                on_done=lambda r: self.list_directory() if r.ok else None,
            )

    def pull(self) -> None:
        serial = self.app.require_serial("adb")
        remote = self._remote_selected()
        local = self.local_dir.get().strip()
        if not serial or not remote or not local:
            return
        destination = str(Path(local) / Path(remote).name)
        self.app.run_command(
            adb_pull(serial, remote, destination),
            "Pull file",
            on_line=lambda line: self.after(0, lambda t=line: self.output.append(t)),
        )

    def delete(self) -> None:
        serial = self.app.require_serial("adb")
        remote = self._remote_selected()
        if serial and remote:
            self.app.run_command(
                adb_delete_file(serial, remote),
                f"Delete {remote}",
                confirm=True,
                on_done=lambda r: self.list_directory() if r.ok else None,
            )
