from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .tools import tool_path

ADB = "adb.exe"
FASTBOOT = "fastboot.exe"


def adb_args(serial: str | None, *args: Any) -> list[str]:
    command = [str(tool_path(ADB))]
    if serial:
        command += ["-s", serial]
    return command + [str(arg) for arg in args if arg is not None]


def fastboot_args(serial: str | None, *args: Any) -> list[str]:
    command = [str(tool_path(FASTBOOT))]
    if serial:
        command += ["-s", serial]
    return command + [str(arg) for arg in args if arg is not None]


def adb_shell(serial: str | None, command: str) -> list[str]:
    return adb_args(serial, "shell", command)


def adb_getprop(serial: str | None) -> list[str]:
    return adb_args(serial, "shell", "getprop")


def adb_packages(serial: str | None, third_party_only: bool = True) -> list[str]:
    return adb_args(serial, "shell", "pm", "list", "packages", "-3" if third_party_only else "")


def adb_install(serial: str | None, apk: str, reinstall: bool = False, grant: bool = False) -> list[str]:
    flags = []
    if reinstall:
        flags.append("-r")
    if grant:
        flags.append("-g")
    return adb_args(serial, "install", *flags, apk)


def adb_uninstall(serial: str | None, package: str, keep_data: bool = False) -> list[str]:
    flag = "-k" if keep_data else None
    return adb_args(serial, "uninstall", flag, package)


def adb_push(serial: str | None, local: str, remote: str) -> list[str]:
    return adb_args(serial, "push", local, remote)


def adb_pull(serial: str | None, remote: str, local: str) -> list[str]:
    return adb_args(serial, "pull", remote, local)


def adb_sideload(serial: str | None, image: str) -> list[str]:
    return adb_args(serial, "sideload", image)


def adb_reboot(serial: str | None, mode: str) -> list[str]:
    if mode == "system":
        return adb_args(serial, "reboot")
    return adb_args(serial, "reboot", mode)


def adb_connect(address: str) -> list[str]:
    return adb_args(None, "connect", address)


def adb_disconnect(address: str | None = None) -> list[str]:
    return adb_args(None, "disconnect", address)


def adb_screencap(serial: str | None) -> list[str]:
    return adb_args(serial, "exec-out", "screencap", "-p")


def adb_list_files(serial: str | None, path: str) -> list[str]:
    return adb_args(serial, "shell", "ls", "-la", path)


def adb_delete_file(serial: str | None, path: str) -> list[str]:
    return adb_args(serial, "shell", "rm", path)


def adb_force_stop(serial: str | None, package: str) -> list[str]:
    return adb_args(serial, "shell", "am", "force-stop", package)


def adb_clear_data(serial: str | None, package: str) -> list[str]:
    return adb_args(serial, "shell", "pm", "clear", package)


def fastboot_getvar_all(serial: str | None) -> list[str]:
    return fastboot_args(serial, "getvar", "all")


def fastboot_flash(serial: str | None, partition: str, image: str) -> list[str]:
    return fastboot_args(serial, "flash", partition, image)


def fastboot_flashall(serial: str | None, folder: str | None = None) -> list[str]:
    args = ["flashall"]
    if folder:
        args.append(folder)
    return fastboot_args(serial, *args)


def fastboot_boot(serial: str | None, image: str) -> list[str]:
    return fastboot_args(serial, "boot", image)


def fastboot_erase(serial: str | None, partition: str) -> list[str]:
    return fastboot_args(serial, "erase", partition)


def fastboot_format(serial: str | None, partition: str) -> list[str]:
    return fastboot_args(serial, "format", partition)


def fastboot_wipe(serial: str | None) -> list[str]:
    return fastboot_args(serial, "wipe")


def fastboot_flashing(serial: str | None, action: str) -> list[str]:
    return fastboot_args(serial, "flashing", action)


def fastboot_set_active(serial: str | None, slot: str) -> list[str]:
    return fastboot_args(serial, "set_active", slot)


def fastboot_oem(serial: str | None, command: str) -> list[str]:
    return fastboot_args(serial, "oem", command)


def fastboot_reboot(serial: str | None, mode: str | None = None) -> list[str]:
    if mode:
        return fastboot_args(serial, "reboot", mode)
    return fastboot_args(serial, "reboot")


def parse_getprop(output: str) -> dict[str, str]:
    props: dict[str, str] = {}
    for line in output.splitlines():
        match = re.match(r"^\[([^\]]+)\]:\s*\[(.*)\]$", line.strip())
        if match:
            props[match.group(1)] = match.group(2)
    return props


def parse_fastboot_vars(output: str) -> dict[str, str]:
    variables: dict[str, str] = {}
    for line in output.splitlines():
        text = line.strip()
        if text.startswith("(bootloader) "):
            text = text[len("(bootloader) ") :]
        if ":" in text:
            key, value = text.split(":", 1)
            variables[key.strip()] = value.strip()
    return variables


def parse_ls(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        text = line.strip()
        if not text or text.startswith("total "):
            continue
        parts = text.split()
        if len(parts) < 2:
            continue
        name = parts[-1]
        if name in (".", ".."):
            continue
        rows.append(
            {
                "permissions": parts[0],
                "size": parts[3] if len(parts) >= 5 else "-",
                "name": name,
                "raw": text,
            }
        )
    return rows


def save_screenshot(output: bytes, path: str | Path) -> None:
    data = output.replace(b"\r\n", b"\n")
    Path(path).write_bytes(data)
