# Third-party notices

FlashBridge PC is MIT licensed. The released EXE includes the third-party
components listed below. Vendor payload archives are bundled inside the EXE and
unpacked to `%APPDATA%\FlashBridgePC\vendor` on first use.

## Android platform-tools (bundled)

`adb.exe`, `fastboot.exe`, `AdbWinApi.dll` and `AdbWinUsbApi.dll` are part of
the Android SDK platform-tools package and are licensed under the Apache
License, Version 2.0.

Source: https://android.googlesource.com/platform/system/core/

Copyright 2026 The Android Open Source Project

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use these files except in compliance with the License. You may obtain a copy
of the License at:

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.

## CustomTkinter (bundled at build time)

MIT License. Copyright (c) 2023 Tom Schimansky.

Source: https://github.com/TomSchimansky/CustomTkinter

## PyInstaller (build tool only)

PyInstaller is licensed under the GNU General Public License v2 with the
PyInstaller bootloader exception. It is used only to produce the executable
and is not a runtime dependency of the distributed application.

Source: https://github.com/pyinstaller/pyinstaller

## Python and Tkinter (runtime)

Python is licensed under the Python Software Foundation License. Tkinter is
distributed under the Tcl/Tk license. The executable is produced with Python
3.12 on Windows.

## Third-party mirror disclosure

Some vendor packages were obtained from public third-party mirrors because the
vendors do not provide the same packages through stable public direct download
URLs. These mirrors are independent sites. Their use of vendor names is for
identification only and does not imply endorsement by the trademark owner.

- `spflashtools.com` states that SP Flash Tool is not endorsed by, owned by, or
  affiliated with MediaTek, Inc.
- `mtkdriver.com` states that MTK Driver is not endorsed by, owned by, or
  affiliated with MediaTek, Inc.
- `qpsttool.com` states that QPST Tool is not endorsed by, owned by, or
  affiliated with Qualcomm Technologies, Inc.
- `qcomdriver.com` states that Qualcomm Driver is not endorsed by, owned by, or
  affiliated with Qualcomm Technologies, Inc.
- `xiaomiflash.com` states that it is not affiliated with the official Xiaomi
  website.
- `xiaomifirmware.com` states that it is not affiliated with Xiaomi Inc.

FlashBridge PC does not claim that these mirrors are official vendor
distribution channels. Payload SHA-256 values are published below so the exact
files inside the release can be verified.

## Vendor payloads (bundled)

### SP Flash Tool v5 5.2404 Win

Source: https://spflashtools.com/windows/sp-flash-tool-v5-2404

Archive: `SP_Flash_Tool_V5.2404_Win.zip`

SHA-256: `F4C16FCF557647A1FA21FC3992171B59392D2AFA0AEE76C5EE2876EC3E148B4B`

Launcher: `flash_tool.exe`

### SP Flash Tool v6 6.2404 Win

Source: https://spflashtools.com/windows/sp-flash-tool-v6-2404

Archive: `SP_Flash_Tool_V6.2404_Win.zip`

SHA-256: `706E390479B7EA12B8A289A11E4BBA599B8067016CBE0144658D493CDAB724F2`

Launcher: `SPFlashToolV6.exe`

### MTK USB VCOM driver 5.1632

Source: https://mtkdriver.com/mtk-driver-v5-1632/

Archive: `MTK-Driver-v5.1632.zip`

SHA-256: `9BF1A12BE76D07DAAE42A127D171A075B3CCBF3757059F8F5F202B8F0DCFEF55`

Installer: `MTK Driver Setup.exe`

The official URL `http://online.mediatek.com/Public%20Documents/MTK_Android_USB_Driver.zip`
returned HTTP 404 when checked, so the public mirror above was used.

### Qualcomm USB driver 1.0.10065.1

Source: https://qcomdriver.com/qualcomm-usb-driver-v1-0-10065-1/

Also referenced by Quectel public download documentation.

Archive: `Qualcomm_USB_Driver_v1.0.10065.1.zip`

SHA-256: `BF875901977D9BE3DDDD1374E9D45873644EBDB27446945C39C1C3108655B4A2`

Installer: `Qualcomm USB Driver v1.0.10065.1.exe`

Qualcomm open-source USB driver repositories are available at
https://github.com/qualcomm/qcom-usb-kernel-drivers and
https://github.com/qualcomm/qcom-usb-userspace-drivers under BSD-3-Clause. The
bundled executable driver package is a separate binary distribution.

### QPST / QFIL 2.7.496

Source: https://qpsttool.com/qpst-tool-v2-7-496/

Archive: `QPST_2.7.496.zip`

SHA-256: `B0EECB317851FBFF1A450FE0EE18BE1FAF59BC7744FF0E4383ED4C3F6F86A977`

Installer: `QPST.2.7.496.1.exe`

QFIL is installed as part of the QPST package. Official QFIL and QUD downloads
require a Qualcomm account, so this public QPST mirror was used.

### Heimdall 1.4.0

Source: https://bitbucket.org/extremes/heimdall/downloads/heimdall-suite-1.4.0-win32.zip

Maintained fork: https://git.sr.ht/~grimler/Heimdall

License: MIT

Archive: `heimdall-suite-1.4.0-win32.zip`

SHA-256: `5A117709470CA5B54B53142FEE0B29708AB84174EEE226FE90B1184A5787173A`

Launchers: `heimdall.exe`, `heimdall-frontend.exe`

The archive also includes `Drivers/zadig.exe`.

### Mi Flash Tool 20220507

Source: https://www.xiaomiflash.com/download

Archive: `MiFlash20220507.zip`

SHA-256: `4880D3395154254A729F57A488BE44CA68EF6E19EDFBA5425A0AF25F19C5FF52`

Launcher: `XiaoMiFlash.exe`

This is a third-party mirror of the Xiaomi flashing utility. It requires the
exact Fastboot ROM for the target device and may require account authorization
depending on device and region.

### Mi Unlock Tool 7.6.727.43

Source: https://xiaomifirmware.com/downloads/download-mi-unlock-3-5-1108-44/

Official Xiaomi CDN package name: `miflash_unlock_7.6.727.43.zip`

Bundled archive: `MiUnlock-7.6.727.43-en.zip`

SHA-256: `6BB390BDDAAFF3E75A6A2B1ECAFA3F49BF6E4D93747302A6870698FB26285A32`

Launcher: `miflash_unlock.exe`

The bundled file is the English package and matches the published SHA-256 for
Mi Unlock 7.6.727.43. It requires an authorized Xiaomi account, OEM unlocking,
and a compatible device. China-region devices are not supported by the global
unlock service.

## Not bundled

### Samsung Odin

No official public Windows distribution of Odin was found. Odin is not bundled.
The Vendor tools page can detect common installed Odin paths or use a path set
by the user. Heimdall is provided as the bundled Samsung flashing tool.

### MTK auth bypass

Security-control bypass utilities are not bundled or launched by FlashBridge
PC. Use authorized vendor service tools for protected devices.

## User responsibility

Vendor tools can permanently change or erase device software. FlashBridge PC
does not bundle firmware images and does not decide whether a firmware file is
correct for a device. Back up data, verify model and region, verify hashes,
keep the device charged, and follow the vendor tool instructions.
