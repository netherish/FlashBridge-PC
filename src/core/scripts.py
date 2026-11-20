from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Any

from .tools import config_dir


class ScriptStore:
    def __init__(self) -> None:
        self._path: Path = config_dir() / "scripts.json"
        self._lock = threading.RLock()
        self._scripts: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        with self._lock:
            try:
                data = json.loads(self._path.read_text(encoding="utf-8")) if self._path.is_file() else []
                self._scripts = data if isinstance(data, list) else []
            except Exception:
                self._scripts = []

    def save(self) -> None:
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._scripts, indent=2, sort_keys=True), encoding="utf-8"
            )

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(script) for script in self._scripts]

    def add(self, script: dict[str, Any]) -> dict[str, Any]:
        record = dict(script)
        record["id"] = uuid.uuid4().hex
        with self._lock:
            self._scripts.append(record)
            self.save()
        return dict(record)

    def update(self, script_id: str, values: dict[str, Any]) -> None:
        with self._lock:
            for script in self._scripts:
                if script.get("id") == script_id:
                    script.update(values)
                    break
            self.save()

    def delete(self, script_id: str) -> None:
        with self._lock:
            self._scripts = [script for script in self._scripts if script.get("id") != script_id]
            self.save()
