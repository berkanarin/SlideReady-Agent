# SlideReady kurulumu (Windows PowerShell). Repo kökünden: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
function Need($c) { $null -ne (Get-Command $c -ErrorAction SilentlyContinue) }

if (-not (Need soffice) -and -not (Test-Path "C:\Program Files\LibreOffice\program\soffice.exe")) {
  winget install --silent TheDocumentFoundation.LibreOffice }
if (-not (Need ffmpeg)) { winget install --silent Gyan.FFmpeg }
if (-not (Need node))   { winget install --silent OpenJS.NodeJS.LTS }

python -m pip install -q -r requirements.txt
npm install --no-audit --no-fund
npx --yes playwright install chromium
bin\slideready.cmd doctor
