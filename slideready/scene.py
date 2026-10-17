"""Koreografi ve sahne üretimi: slayt envanteri + SVG katmanları -> render(t) fonksiyonlu index.html."""
import json
import os
import re
from pathlib import Path

from . import fx as fxmod
from . import media as mediamod

TEMPLATE = Path(__file__).with_name("scene.html")
FXJS = Path(__file__).with_name("fx.js")
STAGGER, CLUSTER_GAP = 0.07, 0.16      # küme içi ve kümeler arası gecikme (sn)
MOTION_TAIL = 1.6                       # son başlayan hareketin bitmesi için pay
REGION_STAGGER = 0.14                   # resim içi bloklar arasındaki gecikme
TEXT_SPREAD = 1.6                       # bir metnin satır/kelime açılışı en fazla bu kadar sürer

# Hareket tarzları (plan.json "style"). Hepsi aynı son kareye varır; fark yol boyunca.
#   zoom      kamera açılışta bu kadar yakından başlar ve geri çekilir (1 = kamera yok)
#   parallax  arka plan, paneller ve içerik farklı derinlikte: kamera hareketinde farklı hızda kayar
#   blur      odak çekme: öğeler bulanıktan netleşir (1920 genişlikte piksel)
#   sweep     panellerin üstünden geçen ışık süzmesi;  glow: sayaç sayımı bitince kısa parıltı
#   words     başlık ve kısa metinler kelime kelime, uzun metin satır satır açılır
#   rise      metin ve içeriğin yükselme mesafesi (piksel);  pop: ikon ve sayılarda yaylanma
STYLES = {
    "sinematik": dict(tempo=1.0, zoom=1.07, parallax=True, blur=9, sweep=True, glow=True, words=True, rise=26,
                      pop=0.6, line=0.12, word=0.055),
    "sakin": dict(tempo=0.85, zoom=1.0, parallax=False, blur=4, sweep=False, glow=False, words=False, rise=12,
                  pop=0.0, line=0.15, word=0.07),
    "enerjik": dict(tempo=1.25, zoom=1.13, parallax=True, blur=6, sweep=True, glow=True, words=True, rise=42,
                    pop=1.0, line=0.08, word=0.04),
}
DEFAULT_STYLE = "auto"      # ajan slayt başına kendisi seçer (auto_style); kullanıcıya sorulmaz


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
    return dict(no=slide["no"], animate=not slide["hidden"], style=DEFAULT_STYLE, tempo=1.0,
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
    if plan.get("lead") in ("number", "chart"):     # veri önde: serbest açıklama metinleri verilerden sonra gelir
        data = [d["t0"] for d in timeline if d["kind"] in ("number", "chart", "table")]
        after = max(data, default=0) + 0.3
        for d in sorted(timeline, key=lambda d: d["t0"]):
            if data and d["kind"] == "text" and d["parent"] is None and d["t0"] < after:
                d["t0"], after = round(after, 3), after + STAGGER
    tempo =float(plan.get("tempo") or 1.0)
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


CLOSING = re.compile(r"teşekkür|tesekkur|thank|sorular|questions|iletişim|contact", re.I)


def _features(slide, W, H):
    sh = [d for d in slide["shapes"] if d["kind"] != "static"]
    k = [d["kind"] for d in sh]
    words = sum(d.get("words", 0) for d in sh)
    visual = sum(d["w"] * d["h"] for d in sh if d["kind"] in ("picture", "media")) / (W * H)
    text = " ".join(d.get("text", "") for d in sh)
    return dict(n=len(sh), words=words, longest=max((d.get("words", 0) for d in sh), default=0),
                numbers=k.count("number"), data=k.count("chart") + k.count("table"), visual=visual,
                closing=bool(CLOSING.search(text)))


def _decide(f, no, last):
    """(tarz, kamera yakınlığı, öne çıkan, gerekçe). Okuma her şeyden önce gelir; kamera veriyi gölgelemez.
    Kısa etiketli kart ızgaraları metin yoğun sayılmaz; yoğunluk en uzun paragrafa ve toplam kelimeye bakar."""
    dense_data = f["data"] or f["numbers"] >= 3
    if f["words"] > 180:
        return None, None, None, f"uzun başvuru metni ({f['words']} kelime): sabit kalır"
    if f["longest"] >= 35 or f["words"] > 90:
        return "sakin", None, "title", f"paragraf ağırlıklı metin ({f['longest']} kelimelik blok): hareket okumanın önüne geçmesin"
    if no == last and (f["closing"] or f["n"] <= 6):
        return "sinematik", 1.10, "title", "kapanış slaytı: yavaş, geniş bir geri çekilme"
    if dense_data:
        lead = "chart" if f["data"] else "number"
        return "sinematik", 1.04, lead, ("grafik/tablo" if f["data"] else f"{f['numbers']} sayı") + \
            ": sakin kamera, veri öne çıkar ve sayar, açıklama sonra gelir"
    if no == 1:
        return "sinematik", 1.12, "title", "kapak: en güçlü kamera hareketi"
    if f["n"] <= 7 and f["words"] <= 25:
        if f["visual"] > 0.25:
            return "enerjik", None, "picture", "görsel ağırlıklı vurgu slaytı: canlı giriş"
        return "sinematik", 1.12, "title", "az öğeli bölüm/vurgu slaytı: güçlü kamera"
    if f["visual"] > 0.35 and f["words"] <= 15:
        return "enerjik", None, "picture", "görsel ağırlıklı, az metin: canlı giriş"
    return "sinematik", None, "title", "kartlı/karma düzen: okuma sırasıyla, derinlikli giriş"

def auto_plan(slides, W, H):
    """Destenin her slaytı için ajan kararı: tarz, kamera yakınlığı, öne çıkan öğe ve kısa gerekçe.
    Deste tek bir aile içinde kalır: sakin ile enerjik art arda gelmez (enerjik sinematiğe iner)."""
    last = max((s["no"] for s in slides if not s["hidden"]), default=0)
    out = {s["no"]: _decide(_features(s, W, H), s["no"], last) for s in slides}
    nos = sorted(out)
    for a, b in zip(nos, nos[1:]):
        for x, y in ((a, b), (b, a)):
            if out[x][0] == "enerjik" and out[y][0] == "sakin":
                st, z, lead, why = out[x]
                out[x] = ("sinematik", z, lead, why + " (komşu slayt sakin: uyum için sinematik)")
    return out


def apply_auto(plan, decision):
    """'auto' plana kararı yazar (chosen, zoom, lead, note). Kullanıcı tarzı elle seçtiyse karar yalnızca nottur."""
    style, zoom, lead, why = decision
    note = plan.get("note") or ""
    if not note or note.startswith("otomatik:"):
        plan["note"] = "otomatik: " + why
    if plan.get("style", DEFAULT_STYLE) != "auto":
        return plan
    if style is None:
        plan["animate"] = False
        plan.pop("chosen", None)
        return plan
    plan.update(chosen=style, lead=lead)
    if zoom:
        plan["zoom"] = zoom
    else:
        plan.pop("zoom", None)
    # açılış anı: ilk slaytın (ve kapak/bölüm/kapanışın) başlığı parçacıklardan toplanır
    if plan.get("no") == 1 or (zoom or 1) >= 1.10:
        plan["hero"] = "title"
        if plan.get("no") == 1 and (zoom or 1) < 1.10 and plan["note"].startswith("otomatik:"):
            plan["note"] += "; açılış slaytı: başlık parçacıklardan toplanır"
    else:
        plan.pop("hero", None)
    return plan


def style_of(plan, slide=None):
    """plan.json'daki tarz ve tempo ile birleşmiş hâli. "auto": analyze'ın seçtiği (chosen, zoom)."""
    name = plan.get("style")
    auto = name not in STYLES
    if auto:
        name = plan.get("chosen") if plan.get("chosen") in STYLES else "sinematik"
    st = dict(STYLES[name], name=name, auto=auto)
    if auto and plan.get("zoom") and st["zoom"] > 1:
        st["zoom"] = float(plan["zoom"])
    st["tempo"] = round(st["tempo"] * float(plan.get("tempo") or 1.0), 3)
    return st

def text_parts(g, words):
    """Metin katmanını satır (words=True ise kelime) bantlarına böler: [x, y, w, h, satır no] (svg birimi).

    Bantlar katman kutusunu boşluksuz kaplar; hepsi açılınca katmanın tamamı görünür (son kare değişmez). Dolgulu ya da
    çizgili kutular, döndürülmüş metin ve satırları üst üste binen metin (sütunlar) bölünmez: None."""
    t, B = g.get("text"), g.get("box")
    if not t or not B or not t.get("plain") or not t.get("lines"):
        return None
    lines = sorted(t["lines"], key=lambda b: b[1])
    if any(b[1] < a[1] + 0.5 * (a[3] - a[1]) for a, b in zip(lines, lines[1:])):
        return None
    ys = [B[1]] + [(a[3] + b[1]) / 2 for a, b in zip(lines, lines[1:])] + [B[3]]
    parts = []
    for i, ln in enumerate(lines):
        y0, y1 = ys[i], ys[i + 1]
        ws = sorted((w for w in t.get("words") or [] if ln[1] - 1 <= (w[1] + w[3]) / 2 <= ln[3] + 1),
                    key=lambda w: w[0]) if words else []
        if len(ws) > 1:
            xs = [B[0]] + [max((a[2] + b[0]) / 2, B[0]) for a, b in zip(ws, ws[1:])] + [B[2]]
            xs = [min(max(x, xs[max(j - 1, 0)]), B[2]) for j, x in enumerate(xs)]   # sıralı kalsın
            parts += [[xs[j], y0, xs[j + 1] - xs[j], y1 - y0, i] for j in range(len(ws)) if xs[j + 1] > xs[j]]
        else:
            parts.append([B[0], y0, B[2] - B[0], y1 - y0, i])
    return parts if len(parts) > 1 else None


def _schedule_text(d, parts, st):
    """Bantların açılış zamanları: satırlar arası 'line', kelimeler arası 'word' gecikmesi; toplam TEXT_SPREAD'i aşmaz."""
    wordmode = len(parts) > len({p[4] for p in parts})
    raw, t, prev = [], 0.0, parts[0][4]
    for p in parts:
        if wordmode and p[4] != prev:          # yeni satıra geçerken kısa nefes
            t += st["line"] * 0.5
            prev = p[4]
        raw.append(t)
        t += st["word"] if wordmode else st["line"]
    k = min(1.0, TEXT_SPREAD / max(raw[-1], 1e-6))
    return [round(d["t0"] + (0.05 + r * k) / st["tempo"], 3) for r in raw]


def build(slide, layer, svgdeck, plan, outdir):
    """Slayt için index.html + scene.json yazar; süreyi döndürür."""
    st = style_of(plan, slide)
    scene, duration = choreograph(slide, {**plan, "tempo": st["tempo"]}, svgdeck.viewbox[3])
    hold = float(plan.get("hold", 2.0))
    groups = {g["id"]: g for g in layer.get("groups") or []}
    last = 0.0
    for d in scene:
        g = groups.get(d["id"])
        if g and g.get("box"):
            d["box"] = g["box"]
        if g and d["kind"] in ("title", "text"):
            words = st["words"] and (d["kind"] == "title" or len((g.get("text") or {}).get("words") or []) <= 12)
            parts = text_parts(g, words)
            if parts:
                times = _schedule_text(d, parts, st)
                d["parts"] = [p[:4] + [tt] for p, tt in zip(parts, times)]
                last = max(last, times[-1])
    before = scene[0]["t0"] if scene else 0.0
    fx_last = fxmod.apply(scene, st, plan, layer, groups, svgdeck.viewbox[2] * svgdeck.viewbox[3])
    shift = (scene[0]["t0"] - before) if scene else 0.0      # süreklilik geçişi sahneyi ileri kaydırır
    duration = round(duration + shift, 2)
    last = max(last + shift, fx_last)
    duration = max(duration, round(last + 0.9 / st["tempo"] + hold, 2))
    st["still"] = round(duration - hold, 3)                  # bundan sonra (medya dışında) hiçbir şey kımıldamaz
    # kamera: başlığın (yoksa ilk öğenin) üstünden geri çekilir; son öğe yerine oturunca durur
    first = next((d for d in scene if d["kind"] == "title"), scene[0] if scene else None)
    settle = max((d["t0"] for d in scene), default=0) + 1.1 / st["tempo"]
    st["camera"] = dict(zoom=st["zoom"], end=round(min(settle, duration - hold), 3),
                        focus=[first["x"] + first["w"] / 2, first["y"] + first["h"] / 2] if first else None)
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
            .replace("/*FX_JS*/", FXJS.read_text(encoding="utf-8"))
            .replace("/*STYLE*/", json.dumps(st, ensure_ascii=False))
            .replace("/*DUR*/", str(duration)).replace("/*VBW*/", str(svgdeck.viewbox[2]))
            .replace("/*VBH*/", str(svgdeck.viewbox[3])))
    (outdir / "index.html").write_text(html, encoding="utf-8")
    (outdir / "scene.json").write_text(json.dumps(dict(duration=duration, style=st, shapes=scene, media=media),
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    return duration, scene