from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from .tools import config_dir

DEFAULTS: dict[str, Any] = {
    "appearance": "dark",
    "color_theme": "blue",
    "ambient_background": True,
    "motion_blur": True,
    "ambient_speed": "normal",
    "polling_ms": 2000,
    "confirm_destructive": True,
    "advanced_mode": True,
    "log_limit": 5000,
    "tools_dir": "",
    "vendor_paths": {},
    "last_fastboot_folder": "",
    "last_image_folder": "",
    "last_apk_folder": "",
    "last_script_folder": "",
}


class Settings:
    def __init__(self) -> None:
        self._path: Path = config_dir() / "settings.json"
        self._lock = threading.RLock()
        self._data = dict(DEFAULTS)
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> None:
        with self._lock:
            try:
                if self._path.is_file():
                    loaded = json.loads(self._path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        for key, value in loaded.items():
                            if key in DEFAULTS:
                                self._data[key] = value
            except Exception:
                self._data = dict(DEFAULTS)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self.save()

    def update(self, values: dict[str, Any]) -> None:
        with self._lock:
            for key, value in values.items():
                if key in DEFAULTS:
                    self._data[key] = value
            self.save()

    def all(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._data)

    def reset(self) -> None:
        with self._lock:
            self._data = dict(DEFAULTS)
            self.save()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2, sort_keys=True), encoding="utf-8"
        )
