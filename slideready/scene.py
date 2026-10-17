"""Koreografi ve sahne üretimi: slayt envanteri + SVG katmanları -> render(t) fonksiyonlu index.html."""
import json
import os
from pathlib import Path

from . import media as mediamod

TEMPLATE = Path(__file__).with_name("scene.html")
STAGGER, CLUSTER_GAP = 0.07, 0.16      # küme içi ve kümeler arası gecikme (sn)
MOTION_TAIL = 1.6                       # son başlayan hareketin bitmesi için pay
REGION_STAGGER = 0.14                   # resim içi bloklar arasındaki gecikme


def _contains(a, b):
    m = 50
    return (a is not b and a["kind"] == "panel" and a["x"] - m <= b["x"] and a["y"] - m <= b["y"]
            and b["x"] + b["w"] <= a["x"] + a["w"] + m and b["y"] + b["h"] <= a["y"] + a["h"] + m
            and a["w"] * a["h"] > b["w"] * b["h"])


def _overlap(a, b):
    return not (a["x"] + a["w"] < b["x"] or b["x"] + b["w"] < a["x"] or a["y"] + a["h"] < b["y"] or b["y"] + b["h"] < a["y"])


def _clusters(items, band):
    cl = []
    for d in sorted(items, key=lambda d: (d["y"], d["x"])):
        hit = [c for c in cl if any(_overlap(d, o) for o in c)]
        if hit:
            hit[0].append(d)
            for extra in hit[1:]:          # iki kümeyi birleştiren şekil
                hit[0].extend(extra)
                cl.remove(extra)
        else:
            cl.append([d])
    return sorted(cl, key=lambda c: (round(min(o["y"] for o in c) / band), min(o["x"] for o in c)))


def default_plan(slide):
    words = sum(d.get("words", 0) for d in slide["shapes"])
    return dict(no=slide["no"], animate=not slide["hidden"], tempo=1.0,
                hold=round(min(5.0, max(2.0, 1.5 + words / 12)), 1), static=[], media=True, note="")


def score(slide):
    k = [d["kind"] for d in slide["shapes"]]
    return 3 * k.count("chart") + 3 * k.count("table") + 2 * k.count("number") + min(len(k), 20) / 10


def choreograph(slide, plan, height):
    """Her şekle bir başlangıç zamanı (t0) verir; başlık önce, paneller ve içerikleri okuma sırasıyla."""
    static = set(plan.get("static") or [])
    live = [d for d in slide["shapes"] if "id" in d and d["kind"] not in ("static", "media") and d["name"] not in static]
    for d in live:
        parents = [p for p in live if _contains(p, d)]
        d["parent"] = min(parents, key=lambda p: p["w"] * p["h"])["name"] if parents else None
    timeline = []

    def schedule(parent, t):
        for c in _clusters([d for d in live if d["parent"] == parent and d["kind"] != "title"], height * 0.06):
            for i, d in enumerate(sorted(c, key=lambda d: (-d["w"] * d["h"]))):
                d["t0"] = round(t + i * STAGGER, 3)
                timeline.append(d)
                if d["kind"] == "panel":
                    end = schedule(d["name"], t + 0.25)
                    t = max(t, end - CLUSTER_GAP)
            t += CLUSTER_GAP
        return t

    t = 0.15
    for d in sorted((d for d in live if d["kind"] == "title"), key=lambda d: d["y"]):
        d["t0"] = t
        timeline.append(d)
        t += 0.2
    schedule(None, max(t + 0.15, 0.45))
    tempo = float(plan.get("tempo") or 1.0)
    for d in timeline:
        d["t0"] = round(d["t0"] / tempo, 3)
    last = max((d["t0"] for d in timeline), default=0)
    tail = MOTION_TAIL + (0.6 if any(d["kind"] in ("chart", "table") for d in timeline) else 0)
    for d in timeline:              # resim içi bloklar sırayla açılır: son bloğun da bitmesi beklenir
        if "regions" in d:
            d["bt"] = [round(d["t0"] + 0.2 / tempo + i * REGION_STAGGER / tempo, 3)
                       for i in range(len(d["regions"]["blocks"]))]
            last = max(last, d["bt"][-1])
    duration = round(last + tail / tempo + float(plan.get("hold", 2.0)), 2)
    keep = ("id", "name", "kind", "t0", "x", "y", "w", "h", "chart", "rows", "pre", "val", "suf", "regions", "bt")
    return [{k: d[k] for k in keep if k in d} for d in timeline], duration


def build(slide, layer, svgdeck, plan, outdir):
    """Slayt için index.html + scene.json yazar; süreyi döndürür."""
    scene, duration = choreograph(slide, plan, svgdeck.viewbox[3])
    outdir.mkdir(parents=True, exist_ok=True)
    media = []
    for m in (slide.get("media") or []) if plan.get("media", True) else []:
        d, n, ext = mediamod.frames(m, width=1920 * m["w"] / svgdeck.viewbox[2])
        rel = Path(os.path.relpath(d, outdir)).as_posix()
        media.append(dict(type=m["type"], x=m["x"], y=m["y"], w=m["w"], h=m["h"], n=n, fps=mediamod.FPS,
                          src=f"{rel}/f%05d.{ext}", loop=m["type"] == "gif"))
        if m["type"] == "video":            # arka plan videosu sonuna kadar oynasın, ardından okuma payı
            duration = max(duration, round(min(m["duration"], mediamod.MAX_SECONDS) + 0.5, 2))
    uses = "".join(f'<use href="#{u}"/>' for u in layer["uses"])
    html = (TEMPLATE.read_text(encoding="utf-8")
            .replace("/*SVG_DEFS*/", svgdeck.defs.strip())
            .replace("/*BG*/", uses).replace("/*SLIDE*/", layer["body"])
            .replace("/*SCENE*/", json.dumps(scene, ensure_ascii=False))
            .replace("/*MEDIA*/", json.dumps(media, ensure_ascii=False))
            .replace("/*DUR*/", str(duration)).replace("/*VBW*/", str(svgdeck.viewbox[2])))
    (outdir / "index.html").write_text(html, encoding="utf-8")
    (outdir / "scene.json").write_text(json.dumps(dict(duration=duration, shapes=scene, media=media),
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    return duration, scene
