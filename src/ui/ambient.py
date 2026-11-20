from __future__ import annotations

import math
import tkinter as tk

import customtkinter as ctk

DARK_GRADIENT = ("#050914", "#0b1533", "#101d45")
LIGHT_GRADIENT = ("#e8f1ff", "#dfe9ff", "#f5f0ff")

ACCENTS = (
    "#22d3ee",
    "#818cf8",
    "#34d399",
    "#f472b6",
    "#fbbf24",
)

SPEEDS = {
    "calm": 0.55,
    "normal": 1.0,
    "lively": 1.65,
}

ORB_STATES = (
    {"sx": 0.31, "sy": 0.23, "px": 0.2, "py": 1.1, "r": 0.30, "accent": 0},
    {"sx": 0.19, "sy": 0.37, "px": 2.4, "py": 0.4, "r": 0.24, "accent": 1},
    {"sx": 0.43, "sy": 0.17, "px": 4.1, "py": 2.7, "r": 0.20, "accent": 2},
    {"sx": 0.27, "sy": 0.29, "px": 5.6, "py": 4.2, "r": 0.17, "accent": 3},
)


def _to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _to_hex(value: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*value)


def _mix(first: str, second: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    left = _to_rgb(first)
    right = _to_rgb(second)
    return _to_hex(
        tuple(round(left[index] + (right[index] - left[index]) * amount) for index in range(3))
    )


class AmbientBackground(tk.Canvas):
    """A low-cost animated canvas that sits behind every FlashBridge page."""

    def __init__(self, master, settings):
        super().__init__(master, highlightthickness=0, bd=0, takefocus=False)
        self.settings = settings
        self._phase = 0.0
        self._enabled = True
        self._motion = True
        self._speed = 1.0
        self._running = False
        self._loop_id: str | None = None
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._on_configure)
        self.apply_settings()
        self._draw_base()
        self._draw_orbs()

    # ---------- palette ----------

    def _gradient(self) -> tuple[str, str, str]:
        if ctk.get_appearance_mode().lower() == "light":
            return LIGHT_GRADIENT
        return DARK_GRADIENT

    def _base_color(self) -> str:
        return self._gradient()[0]

    # ---------- lifecycle ----------

    def apply_settings(self) -> None:
        self._enabled = bool(self.settings.get("ambient_background", True))
        self._motion = bool(self.settings.get("motion_blur", True))
        speed_key = str(self.settings.get("ambient_speed", "normal")).lower()
        self._speed = SPEEDS.get(speed_key, SPEEDS["normal"])
        self.configure(bg=self._base_color())

        if not self._enabled:
            self._stop()
            self.delete("orb")
            self._draw_base()
            return

        self._draw_base()
        self._start()

    def start(self) -> None:
        if self._enabled:
            self._start()

    def stop(self) -> None:
        self._stop()

    def _start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tick()

    def _stop(self) -> None:
        self._running = False
        if self._loop_id:
            try:
                self.after_cancel(self._loop_id)
            except tk.TclError:
                pass
            self._loop_id = None

    def _tick(self) -> None:
        if not self._running or not self._enabled:
            return
        self._phase += 0.010 * self._speed
        self._draw_orbs()
        self._loop_id = self.after(55, self._tick)

    def _on_configure(self, _event=None) -> None:
        self._draw_base()
        if self._enabled:
            self._draw_orbs()

    # ---------- drawing ----------

    def _draw_base(self) -> None:
        self.delete("base")
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 2 or height < 2:
            return
        top, middle, bottom = self._gradient()
        bands = 42
        band_height = height / bands + 2
        for index in range(bands):
            ratio = index / max(1, bands - 1)
            color = _mix(top, middle, ratio * 2) if ratio <= 0.5 else _mix(middle, bottom, (ratio - 0.5) * 2)
            y = index * band_height
            self.create_rectangle(0, y, width, y + band_height + 1, fill=color, outline="", tags="base")

        line_color = _mix(top, "#93c5fd", 0.16)
        for offset in range(0, width + 160, 160):
            self.create_line(offset, 0, offset - 160, height, fill=line_color, stipple="gray12", tags="base")

    @staticmethod
    def _orb_position(state: dict, phase: float, width: int, height: int) -> tuple[float, float]:
        x = width * (0.5 + 0.38 * math.sin(phase * state["sx"] + state["px"]))
        y = height * (0.5 + 0.34 * math.cos(phase * state["sy"] + state["py"]))
        return x, y

    def _draw_orbs(self) -> None:
        self.delete("orb")
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 2 or height < 2 or not self._enabled:
            return

        base = self._gradient()[0]
        trail_steps = 6 if self._motion else 0

        for ribbon_index, accent in enumerate(ACCENTS[:2]):
            points = []
            for step in range(13):
                x = width * step / 12
                y = height * (0.22 + ribbon_index * 0.52)
                y += height * 0.06 * math.sin(self._phase * 0.7 + step * 0.55 + ribbon_index * 2.1)
                points.extend((x, y))
            color = _mix(base, accent, 0.12)
            self.create_line(
                *points,
                fill=color,
                width=3,
                smooth=True,
                stipple="gray25",
                tags="orb",
            )

        for state in ORB_STATES:
            accent = ACCENTS[state["accent"]]
            radius = min(width, height) * state["r"]

            for step in range(trail_steps, 0, -1):
                trail_phase = self._phase - step * 0.026 * self._speed
                x, y = self._orb_position(state, trail_phase, width, height)
                strength = 0.055 + (trail_steps - step) * 0.012
                color = _mix(base, accent, strength)
                self.create_oval(
                    x - radius * 0.72,
                    y - radius * 0.72,
                    x + radius * 0.72,
                    y + radius * 0.72,
                    fill=color,
                    outline="",
                    stipple="gray50",
                    tags="orb",
                )

            x, y = self._orb_position(state, self._phase, width, height)
            for ring in range(6):
                factor = 1.0 - ring * 0.14
                strength = 0.10 + ring * 0.055
                color = _mix(base, accent, strength)
                self.create_oval(
                    x - radius * factor,
                    y - radius * factor,
                    x + radius * factor,
                    y + radius * factor,
                    fill=color,
                    outline="",
                    stipple="gray12" if ring < 3 else "gray25",
                    tags="orb",
                )
