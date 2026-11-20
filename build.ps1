$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$src = Join-Path $root "src"
$dist = Join-Path $root "dist"
$payloadDir = Join-Path $root "vendor\payload"
$exeName = "FlashBridgePC-v1.0.0"
$requiredTools = @("adb.exe", "fastboot.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll")

$vendorPayloads = @(
    @{ Name = "SP_Flash_Tool_V5.2404_Win.zip"; Sha = "F4C16FCF557647A1FA21FC3992171B59392D2AFA0AEE76C5EE2876EC3E148B4B" },
    @{ Name = "SP_Flash_Tool_V6.2404_Win.zip"; Sha = "706E390479B7EA12B8A289A11E4BBA599B8067016CBE0144658D493CDAB724F2" },
    @{ Name = "MTK-Driver-v5.1632.zip"; Sha = "9BF1A12BE76D07DAAE42A127D171A075B3CCBF3757059F8F5F202B8F0DCFEF55" },
    @{ Name = "Qualcomm_USB_Driver_v1.0.10065.1.zip"; Sha = "BF875901977D9BE3DDDD1374E9D45873644EBDB27446945C39C1C3108655B4A2" },
    @{ Name = "QPST_2.7.496.zip"; Sha = "B0EECB317851FBFF1A450FE0EE18BE1FAF59BC7744FF0E4383ED4C3F6F86A977" },
    @{ Name = "heimdall-suite-1.4.0-win32.zip"; Sha = "5A117709470CA5B54B53142FEE0B29708AB84174EEE226FE90B1184A5787173A" },
    @{ Name = "MiFlash20220507.zip"; Sha = "4880D3395154254A729F57A488BE44CA68EF6E19EDFBA5425A0AF25F19C5FF52" },
    @{ Name = "MiUnlock-7.6.727.43-en.zip"; Sha = "6BB390BDDAAFF3E75A6A2B1ECAFA3F49BF6E4D93747302A6870698FB26285A32" }
)

foreach ($tool in $requiredTools) {
    $path = Join-Path $root "tools\$tool"
    if (-not (Test-Path $path)) {
        throw "Missing bundled tool: $path"
    }
}

New-Item -ItemType Directory -Force -Path $payloadDir | Out-Null

$pyinstallerArgs = @(
    "--clean",
    "--noconfirm",
    "--onefile",
    "--console",
    "--name", $exeName,
    "--paths", $src,
    "--hidden-import", "customtkinter",
    "--hidden-import", "darkdetect",
    "--add-data", "$root\LICENSE;.",
    "--add-data", "$root\THIRD_PARTY_NOTICES.md;.",
    "--add-data", "$root\licenses\Apache-2.0.txt;licenses",
    "--add-binary", "$root\tools\adb.exe;tools",
    "--add-binary", "$root\tools\fastboot.exe;tools",
    "--add-binary", "$root\tools\AdbWinApi.dll;tools",
    "--add-binary", "$root\tools\AdbWinUsbApi.dll;tools"
)

Write-Host "Building $exeName with platform-tools and verified vendor payloads..."
foreach ($entry in $vendorPayloads) {
    $source = Join-Path $root "vendor\downloads\$($entry.Name)"
    $destination = Join-Path $payloadDir $entry.Name
    if (-not (Test-Path $source)) {
        throw "Missing vendor payload: $source"
    }
    Copy-Item -LiteralPath $source -Destination $destination -Force
    $actual = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
    if ($actual -ne $entry.Sha) {
        throw "Hash mismatch for $($entry.Name): expected $($entry.Sha), got $actual"
    }
    $pyinstallerArgs += @("--add-data", "$destination;vendor/payload")
}

$pyinstallerArgs += "$src\main.py"

Push-Location $root
try {
    pyinstaller @pyinstallerArgs
} finally {
    Pop-Location
}

$built = Join-Path $dist "$exeName.exe"
if (-not (Test-Path $built)) {
    throw "Build finished without producing $built"
}

$hash = Get-FileHash $built -Algorithm SHA256
Write-Host "Built: $built"
Write-Host "SHA-256: $($hash.Hash)"
