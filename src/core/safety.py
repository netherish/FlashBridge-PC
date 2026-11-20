from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .runner import CommandResult, runner
from .tools import tool_path


@dataclass
class ConfirmationRequest:
    title: str
    target: str
    command: str
    details: str


DESTRUCTIVE_FASTBOOT = {
    "flash",
    "flashall",
    "erase",
    "format",
    "wipe",
    "flashing",
    "oem",
    "set_active",
}

DESTRUCTIVE_ADB = {"uninstall", "sideload"}


def _is_fastboot(args: list[str]) -> bool:
    return bool(args) and "fastboot" in args[0].lower()


def _is_adb(args: list[str]) -> bool:
    return bool(args) and "adb" in args[0].lower()


def requires_confirmation(args: list[str]) -> bool:
    if not args:
        return False
    lowered = [arg.lower() for arg in args]
    if _is_fastboot(args):
        return any(token in lowered for token in DESTRUCTIVE_FASTBOOT)
    if _is_adb(args):
        if "shell" in lowered:
            joined = " ".join(lowered)
            return any(
                token in joined
                for token in (
                    " rm ",
                    " dd ",
                    " fastboot ",
                    " wipe ",
                    " format ",
                    " pm clear ",
                )
            )
        return any(token in lowered for token in DESTRUCTIVE_ADB)
    return False


def build_confirmation(args: list[str], target: str, description: str = "") -> ConfirmationRequest:
    title = "Confirm operation"
    details = description or "This operation changes device state."
    if _is_fastboot(args):
        title = "Confirm fastboot operation"
        details = (
            "Fastboot operations write directly to device partitions. "
            "Verify the target device and image before continuing."
        )
    elif _is_adb(args):
        title = "Confirm ADB operation"
    return ConfirmationRequest(
        title=title,
        target=target or "Unknown device",
        command=subprocess.list2cmdline(args),
        details=details,
    )


def tool_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name, args in (
        ("adb", [str(tool_path("adb.exe")), "version"]),
        ("fastboot", [str(tool_path("fastboot.exe")), "--version"]),
    ):
        result: CommandResult = runner.run(args)
        lines = [line.strip() for line in result.output.splitlines() if line.strip()]
        versions[name] = lines[0] if lines else "Unknown"
    return versions
