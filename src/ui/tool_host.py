from __future__ import annotations

import ctypes
import subprocess
import threading
import time
import tkinter as tk
from ctypes import wintypes
from typing import Callable

user32 = ctypes.WinDLL("user32", use_last_error=True)

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
LONG_PTR = ctypes.c_ssize_t

GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MAXIMIZEBOX = 0x00010000
WS_MINIMIZEBOX = 0x00020000
WM_CLOSE = 0x0010
SW_SHOW = 5
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040

user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
user32.SetParent.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL

try:
    _get_window_long = user32.GetWindowLongPtrW
    _set_window_long = user32.SetWindowLongPtrW
except AttributeError:
    _get_window_long = user32.GetWindowLongW
    _set_window_long = user32.SetWindowLongW
_get_window_long.argtypes = [wintypes.HWND, ctypes.c_int]
_get_window_long.restype = LONG_PTR
_set_window_long.argtypes = [wintypes.HWND, ctypes.c_int, LONG_PTR]
_set_window_long.restype = LONG_PTR


def _window_title(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


class EmbeddedToolHost:
    """Launches a vendor GUI and reparents its window into FlashBridge PC."""

    def __init__(self, app, container, on_state: Callable | None = None):
        self.app = app
        self.container = container
        self.on_state = on_state
        self._process: subprocess.Popen | None = None
        self._hwnd: int | None = None
        self._tool = None
        self._lock = threading.RLock()
        self._closed = False
        self.container.bind("<Configure>", lambda _event: self.resize())

    # ---------- public ----------

    def launch(self, tool) -> None:
        self.close()
        self._closed = False
        self._tool = tool
        self._emit("preparing", tool.name)

        def worker() -> None:
            try:
                path = self.app.vendor.resolve(tool, prepare=True)
                if not path or not path.is_file():
                    raise FileNotFoundError(f"No launcher is available for {tool.name}.")

                if tool.installer or tool.console:
                    self.app.vendor.launch(tool)
                    self.app.after(
                        0,
                        lambda: self._emit(
                            "external",
                            tool.name,
                            "Installers and command-line tools must open in their own window.",
                        ),
                    )
                    return

                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                process = subprocess.Popen(
                    [str(path)],
                    cwd=str(path.parent),
                    close_fds=True,
                    creationflags=creationflags,
                )
                with self._lock:
                    self._process = process

                found = self._find_window(process.pid, timeout=22.0)
                if found:
                    hwnd, title = found
                    self.app.after(0, lambda h=hwnd, t=title: self._embed(h, tool, t))
                else:
                    self.app.after(
                        0,
                        lambda: self._emit(
                            "external",
                            tool.name,
                            "The tool opened in its own window because no embeddable window was found.",
                        ),
                    )

                while not self._closed:
                    with self._lock:
                        current_hwnd = self._hwnd
                        current_process = self._process
                    if current_hwnd and not user32.IsWindow(current_hwnd):
                        break
                    if current_process is not None and current_process.poll() is not None and not current_hwnd:
                        break
                    time.sleep(0.5)
            except Exception as exc:
                self.app.after(0, lambda error=exc: self._emit("error", tool.name, str(error)))
            finally:
                self.app.after(0, self._on_process_exit)

        threading.Thread(target=worker, daemon=True).start()

    def close(self) -> None:
        self._closed = True
        with self._lock:
            hwnd, process = self._hwnd, self._process
            self._hwnd, self._process, self._tool = None, None, None
        if hwnd and user32.IsWindow(hwnd):
            try:
                user32.SetParent(hwnd, 0)
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            except Exception:
                pass
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass

    close_all = close

    def resize(self) -> None:
        with self._lock:
            hwnd = self._hwnd
        if not hwnd or not user32.IsWindow(hwnd):
            return
        width = max(200, self.container.winfo_width())
        height = max(160, self.container.winfo_height())
        flags = SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW
        user32.SetWindowPos(hwnd, 0, 0, 0, width, height, flags)

    # ---------- internals ----------

    @staticmethod
    def _find_window(pid: int, timeout: float) -> tuple[int, str] | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found: list[tuple[int, str]] = []

            @WNDENUMPROC
            def callback(hwnd, _lparam):
                process_id = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                if process_id.value == pid and user32.IsWindowVisible(hwnd):
                    title = _window_title(hwnd)
                    if title:
                        found.append((hwnd, title))
                return True

            user32.EnumWindows(callback, 0)
            if found:
                return found[0]
            time.sleep(0.2)
        return None

    def _embed(self, hwnd: int, tool, title: str) -> None:
        if not user32.IsWindow(hwnd):
            self._emit("error", tool.name, "The tool window closed before it could be embedded.")
            return
        try:
            parent = int(self.container.winfo_id())
            style = _get_window_long(hwnd, GWL_STYLE)
            style &= ~(WS_CAPTION | WS_THICKFRAME | WS_SYSMENU | WS_MAXIMIZEBOX | WS_MINIMIZEBOX)
            style |= WS_CHILD
            user32.SetParent(hwnd, parent)
            _set_window_long(hwnd, GWL_STYLE, style)
            with self._lock:
                self._hwnd = hwnd
            user32.ShowWindow(hwnd, SW_SHOW)
            self.resize()
            self._emit("embedded", tool.name, title)
        except Exception as exc:
            self._emit("error", tool.name, f"Could not embed the tool window: {exc}")

    def _on_process_exit(self) -> None:
        with self._lock:
            hwnd = self._hwnd
        if hwnd and user32.IsWindow(hwnd):
            return
        with self._lock:
            self._hwnd, self._process, self._tool = None, None, None
        self._emit("closed", "")

    def _emit(self, event: str, tool_name: str, detail: str = "") -> None:
        if self.on_state is None:
            return
        try:
            if not self.app.winfo_exists():
                return
        except tk.TclError:
            return
        try:
            self.on_state(event, tool_name, detail)
        except Exception:
            pass
