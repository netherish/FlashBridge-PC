# FlashBridge PC

A Windows desktop console for ADB, fastboot, and vendor service tools.

FlashBridge PC is a single-file Windows EXE. It bundles Google platform-tools
and the accepted vendor tool payloads. No runtime download is required for the
tools listed below. Vendor payloads unpack on first use to
`%APPDATA%\FlashBridgePC\vendor`, and every accepted tool is visible and
launchable from the **Vendor tools** page inside FlashBridge PC.

The Android phone app is a separate project. FlashBridge PC is not submitted
to F-Droid.

## Download

Download `FlashBridgePC-v1.0.0.exe` from the GitHub Releases page and run it.
There is no installer and no separate platform-tools download.

## Features

- Multi-device dashboard with ADB and fastboot detection
- Fastboot flash queue with partition picker, SHA-256, file size and exact-command confirmation
- Boot, erase, format, wipe, unlock, lock, set-active, OEM and getvar operations
- ADB shell with quick commands and live logcat support
- Application manager with install, uninstall, force-stop and clear-data actions
- Device file browser with push, pull and delete
- ADB sideload controller
- Saved command scripts
- Searchable activity log with export
- Dark, light and system themes
- Animated ambient background with soft aurora orbs, optional motion-blur trails, and three speed presets
- Accent-colored dashboard cards and quick actions
- Vendor tools page with grouped cards, search, status, launch, folder access, and user-supplied launcher paths

## Bundled vendor tools

| Tool | Version | Notes |
| --- | --- | --- |
| Android platform-tools | Bundled Google release | ADB and fastboot used by FlashBridge operations |
| SP Flash Tool v5 | 5.2404 Win | MediaTek scatter flashing |
| SP Flash Tool v6 | 6.2404 Win | Newer MediaTek device support |
| MTK USB VCOM driver | 5.1632 | Driver installer, requires administrator approval |
| Qualcomm USB driver | 1.0.10065.1 | Driver installer, requires administrator approval |
| QPST / QFIL | 2.7.496 | Qualcomm flashing tools, QFIL installs with QPST |
| Heimdall CLI | 1.4.0 | Samsung Odin-protocol command-line tool |
| Heimdall frontend | 1.4.0 | Graphical interface for Heimdall |
| Mi Flash Tool | 20220507 | Xiaomi Fastboot ROM flashing |
| Mi Unlock Tool | 7.6.727.43 | Xiaomi bootloader unlock, account permission required |

Samsung Odin has no official public Windows distribution, so it is not bundled.
The Vendor tools page can detect common installed Odin paths or use a launcher
path that you supply. MTK auth bypass utilities are not included or launched.

Mi Unlock requires an authorized Xiaomi account, OEM unlocking, and a compatible
device. Xiaomi China-region devices are not supported by the global unlock
service. Mi Flash requires the exact Fastboot ROM for the connected device.

The **Vendor tools** page shows each tool as ready, bundled, setup, missing, or
excluded. **Launch** unpacks a bundled payload when needed and starts the tool.
**Unpack all** prepares every bundled payload at once. **Open folder** opens the
unpacked payload directory. **Set path** and **Clear** manage a user-supplied
launcher for tools that are not bundled, such as Odin. **Notices** opens the
third-party notices.

The **Settings** page includes controls for the animated background, motion-blur
trails, and animation speed. All three are enabled by default and can be turned
off for a static interface or slower machines.

Third-party mirror sources and payload hashes are documented in
`THIRD_PARTY_NOTICES.md`.

## Diagnostics

```powershell
FlashBridgePC-v1.0.0.exe --version
FlashBridgePC-v1.0.0.exe --doctor
FlashBridgePC-v1.0.0.exe --list-devices
FlashBridgePC-v1.0.0.exe --vendor-status
```

When building from source, the same commands are available through
`.\dist\FlashBridgePC-v1.0.0.exe`.

## Build from source

Requirements:

- Python 3.12
- `customtkinter`
- `pyinstaller`

The repository contains the required platform-tools files in `tools/`. Vendor
payload archives are not committed because of their size and redistribution
terms. To build the full self-contained EXE, place these exact files in
`vendor/downloads/`:

```text
SP_Flash_Tool_V5.2404_Win.zip
SP_Flash_Tool_V6.2404_Win.zip
MTK-Driver-v5.1632.zip
Qualcomm_USB_Driver_v1.0.10065.1.zip
QPST_2.7.496.zip
heimdall-suite-1.4.0-win32.zip
MiFlash20220507.zip
MiUnlock-7.6.727.43-en.zip
```

`build.ps1` verifies every SHA-256 before packaging.

```powershell
python -m pip install -r requirements.txt
.\build.ps1
```

## Safety

Destructive operations display a confirmation dialog containing the exact
target device and exact command. There is no typed-token confirmation. The app
never bundles firmware images and does not impose an image size limit. Vendor
tools have their own confirmation dialogs and remain user-controlled. Back up
devices before flashing and use only firmware intended for the exact model.

## License

FlashBridge PC is MIT licensed. Bundled platform-tools are Apache-2.0 licensed.
See `LICENSE` and `THIRD_PARTY_NOTICES.md` for third-party terms, sources,
hashes, and mirror disclaimers.
