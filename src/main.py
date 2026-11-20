from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def ensure_source_path() -> None:
    if getattr(sys, "frozen", False):
        return
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


def version_text() -> str:
    from core.tools import APP_NAME, APP_ID, APP_VERSION

    return f"{APP_NAME} {APP_VERSION} ({APP_ID})"


def doctor() -> int:
    from core.safety import tool_versions
    from core.tools import config_dir, tools_dir

    print(version_text())
    print(f"Python: {sys.version.split()[0]}")
    print(f"Config: {config_dir()}")
    print(f"Tools:  {tools_dir()}")
    ok = True
    try:
        versions = tool_versions()
    except Exception as exc:
        print(f"Tool check failed: {exc}")
        return 1
    for name, value in versions.items():
        print(f"{name:9} {value}")
        if not value or value == "Unknown":
            ok = False
    print("Status:", "OK" if ok else "TOOLS_MISSING")
    return 0 if ok else 1


def vendor_status() -> int:
    from core.settings import Settings
    from core.vendor_tools import VendorManager

    manager = VendorManager(Settings())
    print("Vendor tools")
    for tool, status in manager.statuses(prepare=False):
        detail = status.detail.replace("\n", " ")
        print(f"{tool.id:20} {status.state:10} {detail}")
    return 0


def list_devices() -> int:
    from core.devices import device_manager

    devices = device_manager.refresh()
    if not devices:
        print("No devices detected.")
        return 0
    for device in devices:
        print(f"{device.kind:8} {device.serial:24} {device.state:10} {device.label}")
    return 0


def launch_gui() -> int:
    from ui.app import FlashBridgeApp

    app = FlashBridgeApp()
    app.mainloop()
    return 0


def hide_console() -> None:
    """Hide the console window when the EXE is launched as a GUI app."""
    if not getattr(sys, "frozen", False):
        return
    try:
        import ctypes

        handle = ctypes.windll.kernel32.GetConsoleWindow()
        if handle:
            ctypes.windll.user32.ShowWindow(handle, 0)
    except Exception:
        return


def enable_console() -> None:
    """Attach to the launcher console for command-line diagnostics."""
    if not getattr(sys, "frozen", False):
        return
    try:
        import ctypes
        import io
        import msvcrt
        import os

        kernel32 = ctypes.windll.kernel32
        attached = kernel32.AttachConsole(-1)
        if not attached and kernel32.GetLastError() != 6:  # ERROR_INVALID_HANDLE
            return
        for handle_id, stream_name in ((-11, "stdout"), (-12, "stderr")):
            handle = kernel32.GetStdHandle(handle_id)
            if handle in (None, 0, -1):
                continue
            try:
                descriptor = msvcrt.open_osfhandle(handle, os.O_WRONLY)
                wrapper = io.TextIOWrapper(
                    os.fdopen(descriptor, "w", closefd=True), write_through=True
                )
                setattr(sys, stream_name, wrapper)
            except Exception:
                pass
    except Exception:
        return


def main() -> int:
    ensure_source_path()
    parser = argparse.ArgumentParser(
        prog="FlashBridgePC",
        description="Advanced ADB and fastboot console for Windows.",
    )
    parser.add_argument("--version", action="store_true", help="Print version information")
    parser.add_argument("--doctor", action="store_true", help="Check bundled platform tools")
    parser.add_argument("--list-devices", action="store_true", help="List connected devices and exit")
    parser.add_argument("--vendor-status", action="store_true", help="List bundled vendor tools and exit")
    args = parser.parse_args()

    if args.version or args.doctor or args.list_devices or args.vendor_status:
        enable_console()

    if args.version:
        print(version_text())
        return 0
    if args.doctor:
        return doctor()
    if args.list_devices:
        return list_devices()
    if args.vendor_status:
        return vendor_status()
    hide_console()
    return launch_gui()


if __name__ == "__main__":
    raise SystemExit(main())
