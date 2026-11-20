from __future__ import annotations

import os
from pathlib import Path

UNAUTHORIZED_MARKERS = (
    "device unauthorized",
    "adb vendor keys is not set",
    "$adb_vendor_keys is not set",
    "device still unauthorized",
)


def adb_key_dir() -> Path:
    return Path.home() / ".android"


def adb_public_key() -> Path:
    return adb_key_dir() / "adbkey.pub"


def is_unauthorized(output: str) -> bool:
    lowered = output.lower()
    return any(marker in lowered for marker in UNAUTHORIZED_MARKERS)


def open_adb_key_folder() -> Path:
    path = adb_key_dir()
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception:
        pass
    return path
