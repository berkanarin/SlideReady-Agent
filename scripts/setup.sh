#!/usr/bin/env bash
# SlideReady kurulumu (Linux / macOS). Repo kökünden: bash scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

need() { command -v "$1" >/dev/null 2>&1; }
OS=$(uname -s)

echo "→ Sistem araçları (ffmpeg, Node.js)"
echo "  Not: slaytları kullanıcının PowerPoint'i çizer (Windows, COM); bu makinede yalnızca analyze çalışır."
missing=()
need ffmpeg || missing+=(ffmpeg)
need node || missing+=(node)
if [ ${#missing[@]} -gt 0 ]; then
  echo "  eksik: ${missing[*]}"
  if [ "$OS" = Darwin ] && need brew; then
    for m in "${missing[@]}"; do
      brew install "$m"
    done
  elif need apt-get; then
    pk=(); for m in "${missing[@]}"; do case $m in node) pk+=(nodejs npm) ;; *) pk+=("$m") ;; esac; done
    SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO=sudo
    $SUDO apt-get update -y && $SUDO apt-get install -y "${pk[@]}"
  else
    echo "  Lütfen bunları kendiniz kurun: ${missing[*]} (README > Kurulum)"; exit 1
  fi
fi

echo "→ Python paketleri"
python3 -m pip install -q -r requirements.txt

echo "→ Playwright + Chromium"
if node -e "require('playwright')" 2>/dev/null; then
  echo "  playwright zaten erişilebilir"
else
  npm install --no-audit --no-fund
fi
if [ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]; then
  npx --yes playwright install chromium
fi

echo "→ Kontrol"
bin/slideready doctor
