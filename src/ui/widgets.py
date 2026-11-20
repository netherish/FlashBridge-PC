from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.safety import ConfirmationRequest


class NavButton(ctk.CTkButton):
    def __init__(self, master, page_name: str, text: str, command, **kwargs):
        super().__init__(
            master,
            text=text,
            anchor="w",
            height=38,
            corner_radius=8,
            fg_color="transparent",
            hover_color=("gray75", "gray25"),
            command=command,
            **kwargs,
        )
        self.page_name = page_name
        self._base_fg = self.cget("fg_color")

    def set_active(self, active: bool) -> None:
        self.configure(fg_color=("#2563eb", "#1e40af") if active else "transparent")


class OutputPanel(ctk.CTkFrame):
    def __init__(self, master, height: int = 260):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 2))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Output", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(header, text="Copy", width=64, command=self.copy).grid(row=0, column=1, padx=3)
        ctk.CTkButton(header, text="Save", width=64, command=self.save).grid(row=0, column=2, padx=3)
        ctk.CTkButton(header, text="Clear", width=64, command=self.clear).grid(row=0, column=3, padx=3)

        self.textbox = ctk.CTkTextbox(self, height=height, wrap="word", font=ctk.CTkFont("Consolas", 12))
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self.textbox.configure(state="disabled")

    def append(self, text: str) -> None:
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text.rstrip() + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def set_text(self, text: str) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("end", text)
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        self.set_text("")

    def get_text(self) -> str:
        return self.textbox.get("1.0", "end-1c")

    def copy(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.get_text())
        messagebox.showinfo("Copied", "Output copied to the clipboard.")

    def save(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save output",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            Path(path).write_text(self.get_text(), encoding="utf-8")


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, request: ConfirmationRequest, on_accept):
        super().__init__(master)
        self.title(request.title)
        self.geometry("680x360")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(fg_color=("#f8fafc", "#0b1120"))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self,
            text=request.title,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 8))

        card = ctk.CTkFrame(self, corner_radius=12)
        card.grid(row=1, column=0, sticky="ew", padx=22, pady=4)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Target", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="nw", padx=14, pady=(12, 4)
        )
        ctk.CTkLabel(card, text=request.target, wraplength=520, justify="left").grid(
            row=0, column=1, sticky="w", padx=4, pady=(12, 4)
        )

        ctk.CTkLabel(card, text="Command", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="nw", padx=14, pady=4
        )
        ctk.CTkLabel(
            card,
            text=request.command,
            wraplength=520,
            justify="left",
            font=ctk.CTkFont("Consolas", 12),
        ).grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ctk.CTkLabel(card, text="Details", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, sticky="nw", padx=14, pady=(4, 14)
        )
        ctk.CTkLabel(card, text=request.details, wraplength=520, justify="left").grid(
            row=2, column=1, sticky="w", padx=4, pady=(4, 14)
        )

        ctk.CTkLabel(
            self,
            text="Verify the device and operation before continuing.",
            text_color=("#b91c1c", "#fca5a5"),
            wraplength=620,
            justify="left",
        ).grid(row=2, column=0, sticky="w", padx=22, pady=(10, 0))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="e", padx=22, pady=16)
        ctk.CTkButton(actions, text="Cancel", width=110, command=self.destroy).pack(side="right", padx=6)
        ctk.CTkButton(
            actions,
            text="Continue",
            width=110,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=self._accept,
        ).pack(side="right", padx=6)
        self._on_accept = on_accept

    def _accept(self) -> None:
        self.destroy()
        self._on_accept()


class KeyValueTable(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self._row = 0

    def set_rows(self, rows: dict[str, str] | list[tuple[str, str]]) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._row = 0
        items = rows.items() if isinstance(rows, dict) else rows
        for key, value in items:
            ctk.CTkLabel(self, text=str(key), font=ctk.CTkFont(weight="bold"), anchor="w").grid(
                row=self._row, column=0, sticky="nw", padx=(8, 12), pady=3
            )
            ctk.CTkLabel(self, text=str(value), wraplength=520, justify="left", anchor="w").grid(
                row=self._row, column=1, sticky="nw", padx=(0, 8), pady=3
            )
            self._row += 1
