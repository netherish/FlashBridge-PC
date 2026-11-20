from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Callable

from .runner import runner
from .tools import tool_path


@dataclass
class Device:
    kind: str
    serial: str
    state: str
    model: str = ""
    product: str = ""
    details: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.serial}"

    @property
    def label(self) -> str:
        name = self.model or self.product or self.serial
        return f"{name} [{self.serial}] ({self.kind})"


class DeviceManager:
    def __init__(self) -> None:
        self.devices: list[Device] = []
        self._listeners: list[Callable[[list[Device]], None]] = []
        self._lock = threading.RLock()

    def add_listener(self, callback: Callable[[list[Device]], None]) -> None:
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[list[Device]], None]) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _notify(self) -> None:
        with self._lock:
            listeners = list(self._listeners)
            devices = list(self.devices)
        for callback in listeners:
            try:
                callback(devices)
            except Exception:
                pass

    def refresh(self) -> list[Device]:
        found: list[Device] = []
        found.extend(self._scan_adb())
        found.extend(self._scan_fastboot())
        with self._lock:
            self.devices = found
        self._notify()
        return found

    def _scan_adb(self) -> list[Device]:
        result = runner.run([str(tool_path("adb.exe")), "devices", "-l"])
        devices: list[Device] = []
        for line in result.output.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            serial, state = parts[0], parts[1]
            if serial.lower() in {"daemon", "list", "of", "*"}:
                continue
            extra: dict[str, str] = {}
            for token in parts[2:]:
                if ":" in token:
                    key, value = token.split(":", 1)
                    extra[key] = value
            devices.append(
                Device(
                    kind="adb",
                    serial=serial,
                    state=state,
                    model=extra.get("model", ""),
                    product=extra.get("product", ""),
                    details=" ".join(parts[2:]),
                    extra=extra,
                )
            )
        return devices

    def _scan_fastboot(self) -> list[Device]:
        result = runner.run([str(tool_path("fastboot.exe")), "devices", "-l"])
        devices: list[Device] = []
        for line in result.output.splitlines():
            parts = line.split()
            if len(parts) < 2 or parts[1].lower() != "fastboot":
                continue
            serial = parts[0]
            extra: dict[str, str] = {}
            for token in parts[2:]:
                if ":" in token:
                    key, value = token.split(":", 1)
                    extra[key] = value
            devices.append(
                Device(
                    kind="fastboot",
                    serial=serial,
                    state="fastboot",
                    model=extra.get("model", ""),
                    product=extra.get("product", ""),
                    details=" ".join(parts[2:]),
                    extra=extra,
                )
            )
        return devices

    def find(self, key: str) -> Device | None:
        with self._lock:
            for device in self.devices:
                if device.key == key:
                    return device
        return None

    def keys(self) -> list[str]:
        with self._lock:
            return [device.key for device in self.devices]

    def adb_serials(self) -> list[str]:
        with self._lock:
            return [d.serial for d in self.devices if d.kind == "adb" and d.state == "device"]

    def fastboot_serials(self) -> list[str]:
        with self._lock:
            return [d.serial for d in self.devices if d.kind == "fastboot"]


device_manager = DeviceManager()
