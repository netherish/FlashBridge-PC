from __future__ import annotations

import math
import random
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.adb_auth import adb_public_key, open_adb_key_folder
from core.safety import ConfirmationRequest
from core.tools import SUPPORT_URL


class NavButton(ctk.CTkButton):
    def __init__(self, master, page_name: str, text: str, command, **kwargs):
        super().__init__(
            master,
            text=text,
            anchor="w",
            height=34,
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


def _mix_hex(first: str, second: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    left = first.lstrip("#")
    right = second.lstrip("#")
    channels = []
    for index in (0, 2, 4):
        a = int(left[index : index + 2], 16)
        b = int(right[index : index + 2], 16)
        channels.append(round(a + (b - a) * amount))
    return "#{:02x}{:02x}{:02x}".format(*channels)


class SupportSplash(ctk.CTkToplevel):
    """Self-contained animated thank-you card shown before the support redirect."""

    WIDTH = 640
    HEIGHT = 420
    BACKGROUND = "#070b17"
    ACCENTS = ("#FFB300", "#00E5FF", "#34D399", "#F472B6", "#A78BFA")

    def __init__(self, master, url: str, on_opened=None):
        super().__init__(master)
        self._url = url
        self._on_opened = on_opened
        self._duration = 3.2
        self._start = time.monotonic()
        self._last = self._start
        self._finished = False
        self._rng = random.Random()

        self.title("Thank you for supporting FlashBridge")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color=self.BACKGROUND)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        self.update_idletasks()
        x = master.winfo_rootx() + max(0, (master.winfo_width() - self.WIDTH) // 2)
        y = master.winfo_rooty() + max(0, (master.winfo_height() - self.HEIGHT) // 2)
        self.geometry(f"+{x}+{y}")

        self._canvas = tk.Canvas(
            self,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg=self.BACKGROUND,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

        self._particles = [
            {
                "x": self._rng.uniform(24, self.WIDTH - 24),
                "y": self._rng.uniform(24, self.HEIGHT - 24),
                "vx": self._rng.uniform(-18, 18),
                "vy": self._rng.uniform(-30, -8),
                "size": self._rng.choice((2, 3, 4, 5)),
                "color": self._rng.choice(self.ACCENTS),
            }
            for _ in range(46)
        ]

        self.bind("<Escape>", lambda _event: self._finish())
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self.lift()
        self.focus_force()
        self.after(30, self._tick)
        self.after(int(self._duration * 1000), self._finish)

    # ---------- animation ----------

    def _tick(self) -> None:
        if self._finished or not self.winfo_exists():
            return
        now = time.monotonic()
        delta = max(0.0, min(0.06, now - self._last))
        self._last = now
        elapsed = now - self._start
        progress = min(1.0, elapsed / self._duration)
        self._draw(progress, elapsed, delta)
        self.after(30, self._tick)

    def _draw(self, progress: float, elapsed: float, delta: float) -> None:
        canvas = self._canvas
        canvas.delete("all")

        top = "#0b1021"
        middle = "#172554"
        bands = 30
        for index in range(bands):
            ratio = index / max(1, bands - 1)
            color = _mix_hex(top, middle, ratio)
            y = index * (self.HEIGHT / bands)
            canvas.create_rectangle(
                0, y, self.WIDTH, y + self.HEIGHT / bands + 2,
                fill=color, outline="", tags="anim"
            )

        for offset in range(0, self.WIDTH + 120, 120):
            canvas.create_line(
                offset, 0, offset - 160, self.HEIGHT,
                fill=_mix_hex(top, "#93c5fd", 0.12),
                stipple="gray25", tags="anim"
            )

        for particle in self._particles:
            particle["x"] += particle["vx"] * delta
            particle["y"] += particle["vy"] * delta
            if particle["y"] < 18:
                particle["y"] = self.HEIGHT - 18
                particle["x"] = self._rng.uniform(24, self.WIDTH - 24)
            if particle["x"] < 12:
                particle["x"] = self.WIDTH - 12
            elif particle["x"] > self.WIDTH - 12:
                particle["x"] = 12
            radius = particle["size"]
            color = _mix_hex(self.BACKGROUND, particle["color"], 0.72)
            canvas.create_oval(
                particle["x"] - radius,
                particle["y"] - radius,
                particle["x"] + radius,
                particle["y"] + radius,
                fill=color, outline="", tags="anim"
            )

        center_x, center_y = self.WIDTH // 2, 118
        for index in range(5):
            cycle = (progress * 1.7 + index * 0.2) % 1.0
            radius = 42 + cycle * 200
            color = _mix_hex(self.BACKGROUND, self.ACCENTS[index % len(self.ACCENTS)], 0.30 * (1.0 - cycle))
            canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=color, width=2, tags="anim"
            )

        pulse = 0.5 + 0.5 * math.sin(elapsed * 4.2)
        heart_color = _mix_hex("#FFB300", "#00E5FF", 0.35 + pulse * 0.4)
        heart_size = 50 + pulse * 6
        canvas.create_polygon(
            self._heart_points(center_x, center_y, heart_size),
            fill=heart_color, outline="", tags="anim"
        )

        if elapsed < 0.9:
            title = "Thank you!"
            subtitle = "Your support means everything."
        elif elapsed < 1.8:
            title = "You are amazing!"
            subtitle = "It keeps FlashBridge fast, free, and independent."
        elif elapsed < 2.6:
            title = "We appreciate you!"
            subtitle = "Every coffee helps bring new tools and fixes."
        else:
            title = "Opening Buy me a coffee..."
            subtitle = "Redirecting now."

        title_color = _mix_hex("#0b1021", "#FFE9A8", min(1.0, elapsed / 0.5))
        subtitle_color = _mix_hex("#0b1021", "#BFEFFF", min(1.0, elapsed / 0.8))
        canvas.create_text(
            center_x, 202, text=title,
            font=("Segoe UI", 29, "bold"), fill=title_color, tags="anim"
        )
        canvas.create_text(
            center_x, 244, text=subtitle,
            font=("Segoe UI", 15), fill=subtitle_color, tags="anim"
        )
        canvas.create_text(
            center_x, 338, text="Thank you for backing independent tools.",
            font=("Segoe UI", 12), fill="#93a0bc", tags="anim"
        )

        track_x, track_y, track_w, track_h = 40, 380, self.WIDTH - 80, 8
        canvas.create_rectangle(
            track_x, track_y, track_x + track_w, track_y + track_h,
            fill="#1d2740", outline="", tags="anim"
        )
        canvas.create_rectangle(
            track_x, track_y, track_x + int(track_w * progress), track_y + track_h,
            fill="#FFB300", outline="", tags="anim"
        )

    @staticmethod
    def _heart_points(cx: int, cy: int, size: float) -> list[float]:
        points: list[float] = []
        scale = size / 32.0
        for step in range(80):
            angle = 2.0 * math.pi * step / 80
            x = 16.0 * math.sin(angle) ** 3
            y = (
                13.0 * math.cos(angle)
                - 5.0 * math.cos(2.0 * angle)
                - 2.0 * math.cos(3.0 * angle)
                - math.cos(4.0 * angle)
            )
            points.extend((cx + x * scale, cy - y * scale))
        return points

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        try:
            webbrowser.open(self._url)
        except Exception:
            pass
        try:
            if callable(self._on_opened):
                self._on_opened()
        except Exception:
            pass
        self.destroy()


class AdbAuthDialog(ctk.CTkToplevel):
    """Guided fix for ADB unauthorized errors, including recovery mode."""

    STEPS = (
        "Reboot the phone into Android, not recovery.",
        "Keep USB debugging enabled and connect this PC.",
        "On the phone, accept 'Allow USB debugging?' and check 'Always allow'.",
        "Reboot into recovery. Enter the decryption password if recovery asks for it.",
        "Retry the command. If it still fails, use 'Restart ADB server' below.",
        "Some recoveries also need ADB/root access enabled in their own menu.",
    )

    def __init__(self, master, detail: str = ""):
        super().__init__(master)
        self.app = master
        self.title("ADB authorization needed")
        self.geometry("780x560")
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color=("#f8fafc", "#0b1120"))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self,
            text="This PC is not trusted by the connected device",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 8))

        info = ctk.CTkFrame(self, corner_radius=12)
        info.grid(row=1, column=0, sticky="ew", padx=24)
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            info,
            text=(
                "Recovery has no Android 'Allow USB debugging?' prompt, so the PC must be "
                "trusted in Android first. Follow these steps, then retry."
            ),
            wraplength=710,
            justify="left",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))
        if detail:
            ctk.CTkLabel(
                info,
                text=f"ADB said: {detail}",
                wraplength=710,
                justify="left",
                text_color=("#b91c1c", "#fca5a5"),
                font=ctk.CTkFont("Consolas", 11),
            ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        steps = ctk.CTkFrame(self)
        steps.grid(row=2, column=0, sticky="nsew", padx=24, pady=14)
        steps.grid_columnconfigure(0, weight=1)
        for index, text in enumerate(self.STEPS):
            ctk.CTkLabel(
                steps,
                text=f"{index + 1}.  {text}",
                wraplength=690,
                justify="left",
                anchor="w",
            ).grid(row=index, column=0, sticky="w", padx=16, pady=6)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        ctk.CTkButton(
            actions,
            text="Restart ADB server",
            width=150,
            fg_color="#2563eb",
            command=self._restart_server,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions,
            text="Open key folder",
            width=130,
            command=self._open_keys,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            actions,
            text="Copy key path",
            width=120,
            command=self._copy_key_path,
            fg_color="transparent",
        ).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Close", width=90, command=self.destroy).pack(side="right")

        self.lift()
        self.focus_force()

    def _restart_server(self) -> None:
        try:
            self.app.restart_adb_server()
        except Exception as exc:
            messagebox.showerror("ADB restart failed", str(exc), parent=self)

    def _open_keys(self) -> None:
        open_adb_key_folder()

    def _copy_key_path(self) -> None:
        key = adb_public_key()
        self.clipboard_clear()
        self.clipboard_append(str(key))
        messagebox.showinfo("Copied", f"Copied:\n{key}", parent=self)
