from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class LogEntry:
    timestamp: str
    level: str
    source: str
    message: str

    def render(self) -> str:
        return f"[{self.timestamp}] [{self.level:<7}] [{self.source}] {self.message}"


class LogStore:
    def __init__(self, limit: int = 5000) -> None:
        self._limit = limit
        self._entries: deque[LogEntry] = deque(maxlen=limit)
        self._lock = threading.RLock()
        self._listeners: list = []

    def add_listener(self, callback) -> None:
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def log(self, message: str, level: str = "INFO", source: str = "app") -> LogEntry:
        entry = LogEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level=level.upper(),
            source=source,
            message=str(message).rstrip(),
        )
        with self._lock:
            self._entries.append(entry)
            listeners = list(self._listeners)
        for callback in listeners:
            try:
                callback(entry)
            except Exception:
                pass
        return entry

    def entries(self) -> list[LogEntry]:
        with self._lock:
            return list(self._entries)

    def render(self) -> str:
        return "\n".join(entry.render() for entry in self.entries())

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def export(self, path: str | Path) -> None:
        Path(path).write_text(self.render(), encoding="utf-8")

    def set_limit(self, limit: int) -> None:
        limit = max(100, int(limit))
        with self._lock:
            self._limit = limit
            resized = deque(self._entries, maxlen=limit)
            self._entries = resized
