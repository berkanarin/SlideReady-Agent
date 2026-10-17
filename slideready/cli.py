"""slideready komut satırı.

  slideready doctor                     ortamı kontrol eder
  slideready analyze  SUNUM.pptx        slaytları çözümler, plan.json yazar
  slideready preview  SUNUM.pptx        en zengin 1-2 slaydın hızlı önizlemesi (+ kontak sayfası)
  slideready export   SUNUM.pptx        tüm slaytları render eder ve videoları sunuma gömer
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .deck import inventory
from .doctor import main as doctor_main, node_env
from .embed import duration, embed
from . import pptrender
from .media import collect as collect_media
from .scene import build, default_plan, score

HERE = Path(__file__).resolve().parent
QUALITY = {
    "preview": dict(width=960, height=540, fps=30, crf=26, preset="veryfast"),
    "720": dict(width=1280, height=720, fps=30, crf=20, preset="medium"),
    "1080": dict(width=1920, height=1080, fps=60, crf=18, preset="medium"),
}
PLACEHOLDER = re.compile(r"buraya yaz|lorem ipsum|click to add|metin ekle", re.I)


def workdir(deck, opt):
    w = Path(opt) if opt else deck.with_name(deck.stem + ".slideready")
    w.mkdir(parents=True, exist_ok=True)
    return w


def missing_fonts(names):
    if not shutil.which("fc-match"):
        return []
    miss = []
    for n in names:
        got = subprocess.run(["fc-match", "-f", "%{family}", n], capture_output=True, text=True).stdout
        if n.lower() not in got.lower():
            miss.append(f"{n} → {got.split(',')[0] or '?'}")
    return miss


def analyze(deck, work, quiet=False):
    """PPTX -> analysis.json ve (kullanıcının düzenleyebileceği) plan.json. Çizim yapılmaz; PowerPoint gerekmez."""
    inv = inventory(deck)
    media = collect_media(deck, work)
    plan_path = work / "plan.json"
    old = {}
    if plan_path.exists():
        try:
            old = {p["no"]: p for p in json.loads(plan_path.read_text(encoding="utf-8"))["slides"]}
        except Exception:
            old = {}
    rows, plans = [], []
    for s in inv["slides"]:
        kinds = [d["kind"] for d in s["shapes"]]
        s["score"] = round(score(s), 1)
        s["placeholder"] = any(PLACEHOLDER.search(d.get("text", "")) for d in s["shapes"])
        s["media"] = media.get(s["no"], [])
        plan = {**default_plan(s), **old.get(s["no"], {})}
        plans.append(plan)
        rows.append(dict(no=s["no"], shapes=len(kinds), charts=kinds.count("chart"), tables=kinds.count("table"),
                         numbers=kinds.count("number"), score=s["score"], hidden=s["hidden"], placeholder=s["placeholder"], animate=plan["animate"],
                         media=", ".join(sorted({m["type"] for m in s["media"]})),
                         regions=sum(len(d["regions"]["blocks"]) for d in s["shapes"] if "regions" in d)))
    inv["missing_fonts"] = missing_fonts(inv["fonts"])
    (work / "analysis.json").write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    plan_path.write_text(json.dumps(dict(deck=str(deck), slides=plans), ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        print(f"{deck.name}: {len(rows)} slayt · çalışma klasörü {work}")
        print(f"{'no':>3} {'şekil':>5} {'grafik':>6} {'tablo':>5} {'sayı':>4} {'puan':>5}  not")
        for r in rows:
            notes = [n for n, c in (("gizli", r["hidden"]), ("yer tutucu metin", r["placeholder"]),
                                    ("sabit kalacak", not r["animate"]),
                                    (f"hareketli medya: {r['media']}", r["media"]),
                                    (f"resim içinde {r['regions']} blok", r["regions"])) if c]
            print(f"{r['no']:>3} {r['shapes']:>5} {r['charts']:>6} {r['tables']:>5} {r['numbers']:>4} {r['score']:>5}  {', '.join(notes)}")
        print("fontlar: " + ", ".join(inv["fonts"]))
        if inv["missing_fonts"]:
            print("⚠ eksik fontlar (yerine kullanılan): " + "; ".join(inv["missing_fonts"]))
        print(f"plan: {plan_path}  (animate/tempo/hold/static alanlarını düzenleyebilirsiniz)")
    return inv, plans, rows


def pick(spec, rows, n_auto=2):
    if spec in (None, "all"):
        return [r["no"] for r in rows if not r["hidden"]]
    if spec == "auto":
        cand = sorted((r for r in rows if not r["hidden"] and r["animate"]), key=lambda r: -r["score"])
        return sorted(r["no"] for r in cand[:n_auto])
    out = set()
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return sorted(out)


def render(jobs, work):
    if not shutil.which("node"):
        sys.exit("Node.js bulunamadı; `slideready doctor` çalıştırın.")
    jf = work / "jobs.json"
    jf.write_text(json.dumps(jobs), encoding="utf-8")
    r = subprocess.run(["node", str(HERE / "render.cjs"), str(jf)], env=node_env(), stdout=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit("render başarısız (yukarıdaki hataya bakın)")
    return json.loads(r.stdout or "[]")


def scenes(deck, work, spec, default, n_auto=2):
    """Çözümler, slayt seçimini uygular ve seçilen slaytların sahnelerini yazar."""
    inv, plans, rows = analyze(deck, work)
    plan = {p["no"]: p for p in plans}
    nos = []
    for no in pick(spec or default, rows, n_auto):
        if plan[no]["animate"]:
            nos.append(no)
        else:
            print(f"  slayt {no}: plan.json'da animate=false, atlandı")
    ok, why = pptrender.available()
    if not ok:
        sys.exit(f"PowerPoint ile çizilemiyor ({why}); `slideready doctor` çalıştırın.")
    print("PowerPoint katmanları:")
    layers = pptrender.render(deck, inv, work, nos)
    built = []
    for no in nos:
        dur, sc = build(inv["slides"][no - 1], layers.slide(no, plan[no].get("media", True)), layers, plan[no], work / "scenes" / f"{no:03d}")
        built.append((no, dur, sc))
    return built, rows


def sheet(scene_dir, out):
    """Dört anlık kareyi (%25, %50, %75, son) 2x2 kontak sayfasına dizer: ajanın ucuz görsel kontrolü."""
    stills = sorted(scene_dir.glob("still-*.png"), key=lambda p: float(p.stem.split("-", 1)[1]))
    args = sum((["-i", str(p)] for p in stills), [])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex",
                    "xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0", str(out)], check=True)


def inv_media(work, no):
    inv = json.loads((work / "analysis.json").read_text(encoding="utf-8"))
    plan = {p["no"]: p for p in json.loads((work / "plan.json").read_text(encoding="utf-8"))["slides"]}
    return inv["slides"][no - 1]["media"] if plan[no].get("media", True) else []


def add_audio(clip, media):
    """Slayttaki ilk sesli videonun sesini klibe ekler (orijinal video artık klibin altında kalıyor)."""
    src = next((m for m in media if m["type"] == "video" and m.get("audio")), None)
    if not src:
        return
    tmp = clip.with_name(clip.stem + "-a.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip), "-i", src["file"], "-map", "0:v", "-map",
                    "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", str(duration(clip)), "-movflags", "+faststart", str(tmp)],
                   check=True)
    tmp.replace(clip)


def cmd_preview(a):
    deck = Path(a.deck).resolve()
    work = workdir(deck, a.work)
    built, rows = scenes(deck, work, a.slides, "auto", a.count)
    q = QUALITY["preview"]
    pdir = work / "preview"
    pdir.mkdir(exist_ok=True)
    jobs = [dict(dir=str(work / "scenes" / f"{no:03d}"), out=str(pdir / f"{no:03d}.mp4"), **q) for no, _, _ in built]
    jobs += [dict(dir=str(work / "scenes" / f"{no:03d}"), at=[round(d * f, 2) for f in (0.25, 0.5, 0.75, 1.0)],
                  width=q["width"], height=q["height"], fps=q["fps"]) for no, d, _ in built]
    render(jobs, work)
    print("\nönizleme:")
    for no, d, sc in built:
        sheet(work / "scenes" / f"{no:03d}", pdir / f"{no:03d}-sheet.png")
        print(f"  slayt {no}: {d:.1f} sn, {len(sc)} hareketli öğe → {pdir / f'{no:03d}.mp4'}  (kontak: {no:03d}-sheet.png)")


def cmd_export(a):
    deck = Path(a.deck).resolve()
    work = workdir(deck, a.work)
    built, rows = scenes(deck, work, a.slides, "all")
    q = dict(QUALITY[a.quality])
    if a.fps:
        q["fps"] = a.fps
    cdir = work / "clips"
    cdir.mkdir(exist_ok=True)
    jobs = [dict(dir=str(work / "scenes" / f"{no:03d}"), out=str(cdir / f"{no:03d}.mp4"), **q) for no, _, _ in built]
    print(f"\n{len(jobs)} slayt render ediliyor ({q['width']}x{q['height']}, {q['fps']} fps)…")
    render(jobs, work)
    for no, _, _ in built:
        add_audio(cdir / f"{no:03d}.mp4", inv_media(work, no))
    dst = Path(a.output).resolve() if a.output else deck.with_name(deck.stem + "-SlideReady.pptx")
    done = embed(deck, {no: cdir / f"{no:03d}.mp4" for no, _, _ in built}, dst)
    size = dst.stat().st_size / 1e6
    print(f"\n✓ {dst}  ({size:.1f} MB)")
    print("  " + ", ".join(f"{no}: {d:.1f} sn" for no, d in done))
    skipped = [r["no"] for r in rows if r["no"] not in dict(done)]
    if skipped:
        print(f"  video eklenmeyen slaytlar: {', '.join(map(str, skipped))}")
    print("  Videolar otomatik başlar, döngü yoktur; poster karesi tamamlanmış slayttır.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="slideready", description="PPTX slaytlarını düzeni bozmadan canlandırır.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("doctor", help="ortamı kontrol et")
    d.add_argument("--json", action="store_true")
    for name, hlp in (("analyze", "slaytları çözümle, plan.json yaz"), ("preview", "hızlı önizleme"),
                      ("export", "render et ve PPTX'e göm")):
        s = sub.add_parser(name, help=hlp)
        s.add_argument("deck")
        s.add_argument("-w", "--work", help="çalışma klasörü (varsayılan: SUNUM.slideready/ sunumun yanında)")
        if name == "preview":
            s.add_argument("--slides", help="'auto' (varsayılan), '3' ya da '2,5-7'")
            s.add_argument("--count", type=int, default=2, help="auto modunda kaç slayt (varsayılan 2)")
        if name == "export":
            s.add_argument("--slides", help="'all' (varsayılan) ya da '2,5-7'")
            s.add_argument("-o", "--output", help="çıktı PPTX (varsayılan: SUNUM-SlideReady.pptx)")
            s.add_argument("--quality", choices=["1080", "720"], default="1080")
            s.add_argument("--fps", type=int)
    a = p.parse_args(argv)
    if a.cmd == "doctor":
        sys.exit(0 if doctor_main(a.json) else 1)
    if a.cmd == "analyze":
        deck = Path(a.deck).resolve()
        analyze(deck, workdir(deck, a.work))
    elif a.cmd == "preview":
        cmd_preview(a)
    else:
        cmd_export(a)
