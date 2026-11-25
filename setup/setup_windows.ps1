<#
 One-shot environment setup for the drill-noise study (Windows 10/11, no admin rights needed).
 Everything is downloaded from the official sources and installed under %LOCALAPPDATA% (venv, CalculiX) or C:\OpenRadioss.

 usage (PowerShell, from the repository root):
     powershell -ExecutionPolicy Bypass -File setup\setup_windows.ps1            # Python venv + CalculiX
     powershell -ExecutionPolicy Bypass -File setup\setup_windows.ps1 -WithOpenRadioss   # also OpenRadioss (cross-check only)

 Needs: Python 3.12 on PATH (python.org installer or Windows Store), internet access.
 MS Word is needed only for the PDF export of the report (src\export_pdf.py).
#>
param([switch]$WithOpenRadioss)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $env:LOCALAPPDATA 'drill-lsdyna-venv'
$ccxDir = Join-Path $env:LOCALAPPDATA 'CalculiX'
$dl = Join-Path $env:LOCALAPPDATA 'drill-dl'
New-Item -ItemType Directory -Force $dl | Out-Null

# 1. Python venv (kept out of OneDrive on purpose)
if (-not (Test-Path "$venv\Scripts\python.exe")) { python -m venv $venv }
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install -r (Join-Path $root 'requirements.txt')

# 2. CalculiX 2.22 (official build from the author's site, dhondt.de); SHA-256 of the file used in the study
$zip = Join-Path $dl 'ccx_win.zip'
$sha = 'a1f91281944c96d6cd914cc020421e8ae65973b3e15d055dc63a3e3e3066d281'
if (-not (Test-Path "$ccxDir\ccx_static.exe")) {
    Invoke-WebRequest 'https://www.dhondt.de/calculix_2.22_4win.zip' -OutFile $zip
    $got = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
    if ($got -ne $sha) { Write-Warning "SHA-256 differs from the one used in the study ($got). Check the download before using it." }
    $tmp = Join-Path $dl 'ccx_extract'
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    Expand-Archive $zip $tmp
    $exe = Get-ChildItem $tmp -Recurse -Filter ccx_static.exe | Select-Object -First 1
    New-Item -ItemType Directory -Force $ccxDir | Out-Null
    Copy-Item (Join-Path $exe.DirectoryName '*') $ccxDir -Recurse -Force
}

# 3. OpenRadioss (optional, official GitHub release) -> C:\OpenRadioss\OpenRadioss
if ($WithOpenRadioss -and -not (Test-Path 'C:\OpenRadioss\OpenRadioss\exec\starter_win64.exe')) {
    $rel = Invoke-RestMethod 'https://api.github.com/repos/OpenRadioss/OpenRadioss/releases/latest'
    $asset = $rel.assets | Where-Object { $_.name -match 'win64.*\.zip$' } | Select-Object -First 1
    if (-not $asset) { throw 'No win64 zip asset found in the latest OpenRadioss release; download it manually from github.com/OpenRadioss/OpenRadioss/releases' }
    $z = Join-Path $dl $asset.name
    Invoke-WebRequest $asset.browser_download_url -OutFile $z
    New-Item -ItemType Directory -Force 'C:\OpenRadioss' | Out-Null
    Expand-Archive $z 'C:\OpenRadioss' -Force
}

Write-Host "`nDone. venv python : $venv\Scripts\python.exe"
Write-Host "CalculiX        : $ccxDir\ccx_static.exe"
Write-Host "Quick test      : cd src ; & '$venv\Scripts\python.exe' verify_e_dsp.py"
