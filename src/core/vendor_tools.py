from __future__ import annotations

import ctypes
import hashlib
import os
import shutil
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .tools import config_dir, resource_root, tools_dir

MARKER_NAME = ".flashbridge-payload"


@dataclass(frozen=True)
class VendorTool:
    id: str
    name: str
    group: str
    version: str
    summary: str
    source: str
    payload: str = ""
    sha256: str = ""
    candidates: tuple[str, ...] = ()
    installer: bool = False
    console: bool = False
    excluded: bool = False
    note: str = ""


TOOLS: tuple[VendorTool, ...] = (
    VendorTool(
        id="platform-tools",
        name="Android platform-tools",
        group="Core",
        version="Bundled with Google release",
        summary="ADB and fastboot used by every FlashBridge operation.",
        source="https://android.googlesource.com/platform/system/core/",
        candidates=("adb.exe",),
        console=True,
    ),
    VendorTool(
        id="sp-flash-v5",
        name="SP Flash Tool v5",
        group="MediaTek",
        version="5.2404 Win",
        summary="MediaTek scatter-based flashing tool.",
        source="https://spflashtools.com/windows/sp-flash-tool-v5-2404",
        payload="SP_Flash_Tool_V5.2404_Win.zip",
        sha256="F4C16FCF557647A1FA21FC3992171B59392D2AFA0AEE76C5EE2876EC3E148B4B",
        candidates=("flash_tool.exe",),
    ),
    VendorTool(
        id="sp-flash-v6",
        name="SP Flash Tool v6",
        group="MediaTek",
        version="6.2404 Win",
        summary="Newer MediaTek flashing tool with updated device support.",
        source="https://spflashtools.com/windows/sp-flash-tool-v6-2404",
        payload="SP_Flash_Tool_V6.2404_Win.zip",
        sha256="706E390479B7EA12B8A289A11E4BBA599B8067016CBE0144658D493CDAB724F2",
        candidates=("SPFlashToolV6.exe",),
    ),
    VendorTool(
        id="mtk-vcom-driver",
        name="MTK USB VCOM driver",
        group="Drivers",
        version="5.1632",
        summary="USB serial driver for MediaTek preloader and VCOM modes.",
        source="https://mtkdriver.com/mtk-driver-v5-1632/",
        payload="MTK-Driver-v5.1632.zip",
        sha256="9BF1A12BE76D07DAAE42A127D171A075B3CCBF3757059F8F5F202B8F0DCFEF55",
        candidates=("MTK Driver Setup.exe",),
        installer=True,
        note="Driver installation requires administrator approval.",
    ),
    VendorTool(
        id="qualcomm-usb-driver",
        name="Qualcomm USB driver",
        group="Drivers",
        version="1.0.10065.1",
        summary="Qualcomm HS-USB driver package for fastboot, ADB and EDL ports.",
        source="https://qcomdriver.com/qualcomm-usb-driver-v1-0-10065-1/",
        payload="Qualcomm_USB_Driver_v1.0.10065.1.zip",
        sha256="BF875901977D9BE3DDDD1374E9D45873644EBDB27446945C39C1C3108655B4A2",
        candidates=("Qualcomm USB Driver v1.0.10065.1.exe",),
        installer=True,
        note="Driver installation requires administrator approval.",
    ),
    VendorTool(
        id="qpst-qfil",
        name="QPST / QFIL",
        group="Qualcomm",
        version="2.7.496",
        summary="Qualcomm download tools. QFIL is installed with the QPST package.",
        source="https://qpsttool.com/qpst-tool-v2-7-496/",
        payload="QPST_2.7.496.zip",
        sha256="B0EECB317851FBFF1A450FE0EE18BE1FAF59BC7744FF0E4383ED4C3F6F86A977",
        candidates=("QPST.2.7.496.1.exe",),
        installer=True,
        note="Third-party mirror package. Install QPST first, then launch QFIL from the installed QPST folder.",
    ),
    VendorTool(
        id="heimdall-cli",
        name="Heimdall CLI",
        group="Samsung",
        version="1.4.0",
        summary="Command-line Samsung Odin protocol flashing tool.",
        source="https://bitbucket.org/extremes/heimdall/downloads/heimdall-suite-1.4.0-win32.zip",
        payload="heimdall-suite-1.4.0-win32.zip",
        sha256="5A117709470CA5B54B53142FEE0B29708AB84174EEE226FE90B1184A5787173A",
        candidates=("heimdall.exe",),
        console=True,
    ),
    VendorTool(
        id="heimdall-frontend",
        name="Heimdall frontend",
        group="Samsung",
        version="1.4.0",
        summary="Graphical interface for the Heimdall flashing suite.",
        source="https://bitbucket.org/extremes/heimdall/downloads/heimdall-suite-1.4.0-win32.zip",
        payload="heimdall-suite-1.4.0-win32.zip",
        sha256="5A117709470CA5B54B53142FEE0B29708AB84174EEE226FE90B1184A5787173A",
        candidates=("heimdall-frontend.exe",),
    ),
    VendorTool(
        id="mi-flash",
        name="Mi Flash Tool",
        group="Xiaomi",
        version="20220507",
        summary="Xiaomi stock Fastboot ROM flashing tool.",
        source="https://www.xiaomiflash.com/download",
        payload="MiFlash20220507.zip",
        sha256="4880D3395154254A729F57A488BE44CA68EF6E19EDFBA5425A0AF25F19C5FF52",
        candidates=("XiaoMiFlash.exe",),
        note="A bootloader unlock permission and the exact Fastboot ROM for the device are required.",
    ),
    VendorTool(
        id="mi-unlock",
        name="Mi Unlock Tool",
        group="Xiaomi",
        version="7.6.727.43",
        summary="Xiaomi official bootloader unlock tool.",
        source="https://xiaomifirmware.com/downloads/download-mi-unlock-3-5-1108-44/",
        payload="MiUnlock-7.6.727.43-en.zip",
        sha256="6BB390BDDAAFF3E75A6A2B1ECAFA3F49BF6E4D93747302A6870698FB26285A32",
        candidates=("miflash_unlock.exe",),
        note="Requires an authorized Xiaomi account, OEM unlocking and a compatible device.",
    ),
    VendorTool(
        id="odin",
        name="Samsung Odin",
        group="Samsung",
        version="User supplied",
        summary="No official public Odin distribution is available, so Odin is not bundled.",
        source="https://developer.samsung.com/",
        note="Use Heimdall, or set a path to an Odin executable you already have.",
    ),
    VendorTool(
        id="mtk-auth-bypass",
        name="MTK auth bypass",
        group="Excluded",
        version="Not included",
        summary="Security-control bypass utilities are not bundled or launched by FlashBridge PC.",
        source="",
        excluded=True,
        note="Use authorized vendor service tools for protected devices.",
    ),
)

TOOL_BY_ID = {tool.id: tool for tool in TOOLS}


@dataclass(frozen=True)
class ToolStatus:
    state: str
    path: Path | None
    detail: str


def payload_root() -> Path:
    """Return the directory containing bundled vendor payload archives."""
    bundled = resource_root() / "vendor" / "payload"
    if bundled.is_dir():
        return bundled
    staged = resource_root() / "vendor" / "downloads"
    return staged if staged.is_dir() else bundled


def vendor_root() -> Path:
    root = config_dir() / "vendor"
    root.mkdir(parents=True, exist_ok=True)
    return root


def find_executable(root: Path, names: tuple[str, ...]) -> Path | None:
    if not root.is_dir():
        return None
    lowered = {name.lower() for name in names}
    for path in root.rglob("*"):
        if path.is_file() and path.name.lower() in lowered:
            return path
    return None


class VendorManager:
    def __init__(self, settings) -> None:
        self.settings = settings
        stored = settings.get("vendor_paths", {})
        self._paths: dict[str, str] = dict(stored) if isinstance(stored, dict) else {}

    # ---------- paths ----------

    def user_path(self, tool_id: str) -> str:
        return str(self._paths.get(tool_id, ""))

    def set_user_path(self, tool_id: str, path: str | Path) -> None:
        candidate = Path(path).expanduser()
        if not candidate.is_file():
            raise FileNotFoundError(f"Selected launcher does not exist: {candidate}")
        self._paths[tool_id] = str(candidate.resolve())
        self.settings.set("vendor_paths", dict(self._paths))

    def clear_user_path(self, tool_id: str) -> None:
        self._paths.pop(tool_id, None)
        self.settings.set("vendor_paths", dict(self._paths))

    def extraction_dir(self, tool: VendorTool) -> Path:
        return vendor_root() / tool.id

    def payload_path(self, tool: VendorTool) -> Path:
        return payload_root() / tool.payload

    # ---------- payload handling ----------

    @staticmethod
    def verify_payload(path: Path, expected_sha: str) -> None:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest().upper()
        if actual != expected_sha.upper():
            raise ValueError(
                f"Vendor payload integrity check failed: {path.name}\n"
                f"Expected: {expected_sha.upper()}\nActual:   {actual}"
            )

    @staticmethod
    def safe_extract(archive: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        root = target.resolve()
        with zipfile.ZipFile(archive) as zipped:
            for info in zipped.infolist():
                if info.is_dir():
                    continue
                destination = (target / info.filename).resolve()
                if root not in destination.parents:
                    raise ValueError(f"Unsafe path in vendor archive: {info.filename}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(info) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)

    def marker_valid(self, tool: VendorTool) -> bool:
        marker = self.extraction_dir(tool) / MARKER_NAME
        if not marker.is_file():
            return False
        try:
            return marker.read_text(encoding="utf-8").strip() == f"{tool.version}\n{tool.sha256.upper()}"
        except OSError:
            return False

    def ensure(self, tool: VendorTool) -> Path:
        """Unpack a bundled payload once and return its launcher path."""
        target = self.extraction_dir(tool)
        existing = find_executable(target, tool.candidates)
        if self.marker_valid(tool) and existing:
            return existing

        archive = self.payload_path(tool)
        if not tool.payload or not archive.is_file():
            raise FileNotFoundError(f"Bundled payload is missing: {archive}")

        self.verify_payload(archive, tool.sha256)
        stage = target.parent / f".{tool.id}-extract-{os.getpid()}"
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir(parents=True, exist_ok=True)
        self.safe_extract(archive, stage)

        executable = find_executable(stage, tool.candidates)
        if not executable:
            raise FileNotFoundError(
                f"Unpacked payload does not contain {', '.join(tool.candidates)}: {archive.name}"
            )
        (stage / MARKER_NAME).write_text(
            f"{tool.version}\n{tool.sha256.upper()}", encoding="utf-8"
        )

        backup: Path | None = None
        if target.exists():
            backup = target.parent / f".{tool.id}-old-{int(time.time())}"
            try:
                target.rename(backup)
            except OSError:
                shutil.rmtree(target, ignore_errors=True)
        try:
            stage.rename(target)
        except OSError as exc:
            if backup and backup.exists() and not target.exists():
                backup.rename(target)
            raise OSError(f"Could not install unpacked tool into {target}: {exc}") from exc
        if backup and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        return find_executable(target, tool.candidates) or executable

    def ensure_all(self) -> dict[str, str]:
        results: dict[str, str] = {}
        errors: list[str] = []
        for tool in TOOLS:
            if not tool.payload or tool.excluded:
                continue
            try:
                results[tool.id] = str(self.ensure(tool))
            except Exception as exc:
                errors.append(f"{tool.name}: {exc}")
        if errors:
            raise RuntimeError("\n".join(errors))
        return results

    # ---------- resolution and status ----------

    @staticmethod
    def find_installed(tool: VendorTool) -> Path | None:
        if tool.id != "odin":
            return None
        roots = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", r"C:\Users")),
        ]
        relative_paths = (
            r"Odin\Odin.exe",
            r"Odin3\Odin3.exe",
            r"Odin3-v3.14.1\Odin3.exe",
            r"Samsung\Odin\Odin.exe",
        )
        for root in roots:
            for relative in relative_paths:
                candidate = root / relative
                if candidate.is_file():
                    return candidate
        return None

    def resolve(self, tool: VendorTool, prepare: bool = True) -> Path | None:
        override = self.user_path(tool.id)
        if override:
            candidate = Path(override)
            return candidate if candidate.is_file() else None

        if tool.id == "platform-tools":
            candidate = tools_dir() / "adb.exe"
            return candidate if candidate.is_file() else None

        if tool.excluded or not tool.payload:
            return self.find_installed(tool)

        target = self.extraction_dir(tool)
        unpacked = find_executable(target, tool.candidates)
        if unpacked and self.marker_valid(tool):
            return unpacked
        return self.ensure(tool) if prepare else None

    def status(self, tool: VendorTool, prepare: bool = False) -> ToolStatus:
        if tool.excluded:
            return ToolStatus("excluded", None, tool.note or "Not included.")
        try:
            path = self.resolve(tool, prepare=prepare)
        except Exception as exc:
            return ToolStatus("error", None, str(exc))
        if path:
            origin = "User supplied" if self.user_path(tool.id) else "Ready"
            return ToolStatus("ready", path, f"{origin}: {path}")
        if tool.payload and self.payload_path(tool).is_file():
            return ToolStatus("bundled", None, "Bundled payload present; launch to unpack.")
        if tool.id == "odin":
            return ToolStatus("setup", None, tool.note or "Set a launcher path to use Odin.")
        if tool.payload:
            return ToolStatus("missing", None, f"Bundled payload missing: {tool.payload}")
        return ToolStatus("setup", None, tool.note or "Set a launcher path.")

    def statuses(self, prepare: bool = False) -> list[tuple[VendorTool, ToolStatus]]:
        return [(tool, self.status(tool, prepare=prepare)) for tool in TOOLS]

    # ---------- actions ----------

    @staticmethod
    def run_as_admin(path: Path, parameters: str = "") -> None:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", str(path), parameters, str(path.parent), 1
        )
        if int(result) <= 32:
            raise OSError(f"Windows did not start the installer (code {result}): {path}")

    @staticmethod
    def run_console(path: Path) -> None:
        command = f'cd /d "{path.parent}" && "{path.name}" --help'
        subprocess.Popen(
            ["cmd.exe", "/k", command],
            creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        )

    def launch(self, tool: VendorTool) -> None:
        if tool.excluded:
            raise RuntimeError(f"{tool.name} is not included in FlashBridge PC.")
        path = self.resolve(tool, prepare=True)
        if not path or not path.is_file():
            raise FileNotFoundError(f"No launcher is available for {tool.name}.")
        if tool.installer:
            self.run_as_admin(path)
        elif tool.console:
            self.run_console(path)
        else:
            subprocess.Popen([str(path)], cwd=str(path.parent), close_fds=True)

    def open_folder(self, tool: VendorTool) -> None:
        if tool.id == "platform-tools":
            folder = tools_dir()
        else:
            override = self.user_path(tool.id)
            if override and Path(override).is_file():
                folder = Path(override).parent
            else:
                folder = self.extraction_dir(tool)
                if not folder.is_dir():
                    folder = vendor_root()
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))
