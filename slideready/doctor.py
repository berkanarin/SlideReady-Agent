"""Ortam kontrolü: SlideReady'nin ihtiyaç duyduğu her aracı dener, eksikse nasıl kurulacağını söyler."""
import importlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .layers import soffice_bin

ROOT = Path(__file__).resolve().parent.parent


def node_env():
    """Playwright'ı önce repo node_modules'ta, sonra global npm kökünde arar."""
    import os
    paths = [str(ROOT / "node_modules")]
    npm = shutil.which("npm")
    if npm:
        try:
            paths.append(subprocess.run([npm, "root", "-g"], capture_output=True, text=True, timeout=30).stdout.strip())
        except Exception:
            pass
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(p for p in paths + [env.get("NODE_PATH", "")] if p)
    return env


def _hint(tool):
    sysname = platform.system()
    hints = {
        "libreoffice": {"Linux": "sudo apt-get install -y libreoffice-impress", "Darwin": "brew install --cask libreoffice",
                        "Windows": "winget install TheDocumentFoundation.LibreOffice"},
        "ffmpeg": {"Linux": "sudo apt-get install -y ffmpeg", "Darwin": "brew install ffmpeg", "Windows": "winget install Gyan.FFmpeg"},
        "node": {"Linux": "https://nodejs.org (18+)", "Darwin": "brew install node", "Windows": "winget install OpenJS.NodeJS.LTS"},
    }
    if tool in hints:
        return hints[tool].get(sysname, hints[tool]["Linux"])
    return {"python": "python3 -m pip install -r requirements.txt",
            "playwright": "npm install && npx playwright install chromium"}[tool]


def checks():
    res = []

    def add(name, ok, detail, fix=None):
        res.append(dict(name=name, ok=bool(ok), detail=detail, fix=None if ok else fix))

    add("Python 3.9+", sys.version_info >= (3, 9), platform.python_version(), "Python 3.9 veya üstünü kurun")
    for mod in ("pptx", "lxml"):
        try:
            importlib.import_module(mod)
            add(f"python: {mod}", True, "kurulu")
        except ImportError:
            add(f"python: {mod}", False, "yok", _hint("python"))
    so = soffice_bin()
    add("LibreOffice", so, so or "bulunamadı", _hint("libreoffice"))
    for tool in ("ffmpeg", "ffprobe"):
        add(tool, shutil.which(tool), shutil.which(tool) or "bulunamadı", _hint("ffmpeg"))
    node = shutil.which("node")
    ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
    add("Node.js 18+", node and int(ver.lstrip("v").split(".")[0] or 0) >= 18, ver or "bulunamadı", _hint("node"))
    if node:
        js = "const {chromium}=require('playwright');chromium.launch().then(b=>b.close()).then(()=>console.log('ok'))"
        try:
            r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=120, env=node_env())
            add("Playwright + Chromium", r.stdout.strip() == "ok", "çalışıyor" if r.stdout.strip() == "ok" else
                (r.stderr.strip().splitlines() or ["hata"])[-1][:120], _hint("playwright"))
        except subprocess.TimeoutExpired:
            add("Playwright + Chromium", False, "zaman aşımı", _hint("playwright"))
    return res


def main(as_json=False):
    res = checks()
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for r in res:
            print(("✓ " if r["ok"] else "✗ ") + f"{r['name']}: {r['detail']}" + ("" if r["ok"] else f"\n    kurulum: {r['fix']}"))
        print("\nHazır." if all(r["ok"] for r in res) else "\nEksikler var; yukarıdaki kurulum komutlarını çalıştırın ya da scripts/setup.sh kullanın.")
    return all(r["ok"] for r in res)
