from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "FlashBridge PC"
APP_VERSION = "1.0.1"
APP_ID = "com.netherish.flashbridgepc"
SUPPORT_URL = "https://buymeacoffee.com/netherish"


def resource_root() -> Path:
    """Return the directory that contains bundled resources."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parents[2]


def tools_dir() -> Path:
    override = os.environ.get("FLASHBRIDGE_TOOLS_DIR", "").strip()
    if override:
        candidate = Path(override)
        if candidate.is_dir():
            return candidate
    return resource_root() / "tools"


def tool_path(name: str) -> Path:
    path = tools_dir() / name
    if not path.is_file():
        raise FileNotFoundError(
            f"Required tool is missing: {path}\n"
            f"Set FLASHBRIDGE_TOOLS_DIR to a folder containing platform-tools."
        )
    return path


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    path = Path(base) / "FlashBridgePC"
    path.mkdir(parents=True, exist_ok=True)
    return path


def license_path() -> Path:
    return resource_root() / "THIRD_PARTY_NOTICES.md"
