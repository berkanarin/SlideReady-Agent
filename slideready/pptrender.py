"""Slayt katmanlarını kullanıcının kendi PowerPoint'iyle (COM) çizer: sahnedeki her şey PowerPoint'in çizdiğinin aynısıdır.

Her slayt için PowerPoint'e şunlar dışa aktarılır:
  full.png   slaytın kendisi (doğruluk karşılaştırması)
  bg.png     envanterdeki şekiller gizli: arka plan, arka plan görseli, düzen ve asıl slayt şekilleri
  her şekil  yalnızca o şekil görünürken bir kez düz beyaz, bir kez düz siyah zemin üzerinde. İki karenin farkından
             gölge, parlama ve yumuşak kenarlar dahil tam saydamlık çıkar (fark matlama):
             alfa = 1 - (beyaz - siyah), renk = siyah / alfa
  sayılar    sayaç için ara değerler: metin geçici olarak ara değerle değiştirilip aynı şekilde dışa aktarılır

Katmanlar kırpılmış RGBA PNG olarak yazılır ve sahnenin beklediği SVG gövdesine (1/100 mm birimli viewBox, her şekil
kendi <g id="p<şekil kimliği>"> grubunda) dönüştürülür. Şekil kimlikleri envanterle aynıdır; eşleme gerekmez.
"""
import json
import platform
import re
import shutil
import tempfile
import time
from pathlib import Path

FRAMES = 16          # sayaç kare sayısı (son kare şeklin kendisi)
ALPHA_MIN = 1 / 255  # bu kadar saydam pikseller kırpmada yok sayılır
VERSION = 2         # katman biçimi değişirse önbelleği geçersiz kılar


def available(close=False):
    """(çalışıyor mu, açıklama). PowerPoint yalnızca Windows'ta COM ile sürülebilir. close: boşta açılan PowerPoint
    kapatılır (doctor; render zaten kendisi kapatır)."""
    if platform.system() != "Windows":
        return False, "yalnızca Windows (PowerPoint COM)"
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return False, "pywin32 kurulu değil"
    pythoncom.CoInitialize()
    try:
        app = win32com.client.Dispatch("PowerPoint.Application")
        ver = app.Version
        if close and app.Presentations.Count == 0:
            app.Quit()
        return True, f"PowerPoint {ver}"
    except Exception as e:
        return False, f"PowerPoint açılamadı: {e}"


# --- sayaç değerleri (scene.html'deki eski numFmt'nin Python karşılığı) ---

def number_format(m):
    """'12,4' '1.250' '3.250,75' gibi bir sayının biçimini korur: k -> m'nin k katı aynı biçimde."""
    seps = re.findall(r"[.,]", m)
    ts = ds = ""
    if len(seps) > 1:
        ts = seps[0]
        if seps[-1] != ts:
            ds = seps[-1]
    elif len(seps) == 1:
        tail = m.split(seps[0])[1]
        if len(tail) == 3 and not m.startswith("0"):
            ts = seps[0]
        else:
            ds = seps[0]
    ip, fp = m.split(ds) if ds else (m, "")
    v = float((ip.replace(ts, "") if ts else ip) + "." + (fp or "0"))
    dec = len(fp)

    def fmt(k):
        a, _, b = f"{v * k:.{dec}f}".partition(".")
        if ts:
            a = re.sub(r"\B(?=(\d{3})+(?!\d))", ts, a)
        return a + ds + b if b else a
    return fmt


def count_frames(val, n=FRAMES):
    """Sayacın 0'dan değere ara metinleri (son değer hariç; o şeklin kendi katmanıdır)."""
    f = number_format(val)
    return [f(i / (n - 1)) for i in range(n - 1)]


# --- fark matlama ---

def matte(white, black):
    """Beyaz ve siyah zemin üzerindeki iki kareden RGBA görüntü ve kırpma kutusu (x0, y0, x1, y1); boşsa kutu None."""
    import numpy as np
    from PIL import Image
    wi, ki = np.asarray(white.convert("RGB")), np.asarray(black.convert("RGB"))
    out = np.zeros(wi.shape[:2] + (4,), np.uint8)
    # tamamen saydam pikselde beyaz - siyah = 255: hesap yalnızca şeklin dokunduğu dikdörtgende yapılır
    ys, xs = np.nonzero((wi[..., 1] < 255) | (ki[..., 1] > 0) | (wi[..., 0] < 255) | (ki[..., 0] > 0)
                        | (wi[..., 2] < 255) | (ki[..., 2] > 0))
    if not len(xs):
        return Image.fromarray(out, "RGBA"), None
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    w = wi[y0:y1, x0:x1].astype(np.float32) / 255
    k = ki[y0:y1, x0:x1].astype(np.float32) / 255
    a = np.clip(1 - (w - k).mean(axis=2), 0, 1)
    c = np.clip(k / np.maximum(a, 1e-4)[..., None], 0, 1)
    c[a < 1e-4] = 0
    out[y0:y1, x0:x1] = np.dstack([c, a]) * 255 + 0.5
    ys, xs = np.nonzero(out[y0:y1, x0:x1, 3] > ALPHA_MIN * 255)
    box = (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1) if len(xs) else None
    return Image.fromarray(out, "RGBA"), box


def _crop_save(im, box, path):
    im.crop(box).save(path, optimize=False, compress_level=3)
    return list(box)


# --- PowerPoint dışa aktarımı ---

class _PowerPoint:
    def __enter__(self):
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        self.app = win32com.client.Dispatch("PowerPoint.Application")
        self.had = self.app.Presentations.Count     # kullanıcının açık sunumları varsa PowerPoint kapatılmaz
        return self

    def open(self, deck):
        # Geçici kopya: kullanıcı aynı dosyayı PowerPoint'te açık tutuyorsa onun belgesine dokunulmaz. Salt okunur,
        # pencere yok; yapılan değişiklikler (gizleme, zemin, sayaç metni) kaydedilmez.
        self.tmp = tempfile.TemporaryDirectory(prefix="slideready-")
        copy = Path(self.tmp.name) / ("deck" + Path(deck).suffix)
        shutil.copyfile(deck, copy)
        self.pres = self.app.Presentations.Open(str(copy), True, False, False)
        return self.pres

    def __exit__(self, *exc):
        try:
            if getattr(self, "pres", None) is not None:
                self.pres.Saved = True
                self.pres.Close()
        finally:
            if self.had == 0 and self.app.Presentations.Count == 0:
                self.app.Quit()
            if getattr(self, "tmp", None):
                self.tmp.cleanup()


def _leaves(slide):
    """Slayttaki tüm yaprak şekiller {kimlik: şekil} (gruplar açılır)."""
    out = {}
    for s in slide.Shapes:
        if s.Type == 6:                                  # msoGroup
            for c in s.GroupItems:
                out[int(c.Id)] = c
        else:
            out[int(s.Id)] = s
    return out


PT = 12700 / 360    # 1 punto (COM) -> svg birimi (1/100 mm)


def _text_bounds(sh):
    """Metin şeklinin satır ve kelime kutuları (svg birimi, [sol, üst, sağ, alt]) ve şeklin dolgusuz/çizgisiz olup
    olmadığı. Sahne metni satır satır ya da kelime kelime açar; dolgulu kutuları bölmez. Döndürülmüş metinde None."""
    try:
        if not sh.HasTextFrame or not sh.TextFrame.HasText or sh.Rotation or sh.TextFrame.Orientation != 1:
            return None
        tr = sh.TextFrame.TextRange

        def boxes(get, limit):
            out = []
            for i in range(1, limit):
                r = get(i, 1)
                if r is None or r.Length == 0:
                    break
                if r.Text.strip() and r.BoundWidth > 0:
                    out.append([round(v * PT, 1) for v in (r.BoundLeft, r.BoundTop, r.BoundLeft + r.BoundWidth,
                                                           r.BoundTop + r.BoundHeight)])
            return out
        plain = not sh.Fill.Visible and not sh.Line.Visible
        return dict(plain=bool(plain), lines=boxes(tr.Lines, 80), words=boxes(tr.Words, 200))
    except Exception:
        return None


def _export_slide(slide, d, shapes, bgmedia, W, H):
    """Ham kareleri d/raw altına yazar; bulunamayan şekil kimliklerini döndürür.

    bgmedia: düzen/asıl slayttaki hareketli medya [(katman, kimlik)]; varsa onlarsız bir arka plan (bgm.png) da yazılır,
    sahne medyanın karelerini bunun üstüne koyar (aksi hâlde ilk kare animasyonun altında görünürdü)."""
    raw = d / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    ex = lambda name: slide.Export(str(raw / name), "PNG", W, H)  # noqa: E731
    leaves = _leaves(slide)
    ex("full.png")
    items, missing, texts = [], [], {}
    for s in shapes:
        sh = leaves.get(s["sid"])
        if sh is None:
            missing.append(s["sid"])
            continue
        if sh.Visible:                                   # PowerPoint'te gizli şeklin katmanı yok
            items.append((s, sh))
            if s["kind"] in ("text", "title"):
                texts[str(s["sid"])] = _text_bounds(sh)
        sh.Visible = 0
    ex("bg.png")
    if bgmedia:
        owners = {"layout": _leaves(slide.CustomLayout), "master": _leaves(slide.Master)}
        hidden = [owners[layer][sid] for layer, sid in bgmedia if sid in owners.get(layer, {})]
        vis = [sh.Visible for sh in hidden]
        for sh in hidden:
            sh.Visible = 0
        ex("bgm.png")
        for sh, v in zip(hidden, vis):
            sh.Visible = v
    for sh in leaves.values():                           # envanter dışı şekiller arka planda kaldı
        sh.Visible = 0
    slide.FollowMasterBackground = 0
    slide.DisplayMasterShapes = 0
    slide.Background.Fill.Solid()
    for tag, rgb in (("w", 0xFFFFFF), ("k", 0)):
        slide.Background.Fill.ForeColor.RGB = rgb
        for s, sh in items:
            sh.Visible = -1
            ex(f"{s['sid']}-{tag}.png")
            if s.get("frames"):
                tr, cur = sh.TextFrame.TextRange, s["val"]
                for i, f in enumerate(s["frames"]):
                    hit = tr.Find(cur)
                    if hit is None:
                        break
                    hit.Text, cur = f, f
                    ex(f"{s['sid']}-n{i}-{tag}.png")
                hit = tr.Find(cur)
                if hit is not None:
                    hit.Text = s["val"]
            sh.Visible = 0
    return missing, texts


def _stamp(deck, width, shapes, bgmedia):
    st = Path(deck).stat()
    return dict(v=VERSION, size=st.st_size, mtime=int(st.st_mtime), width=width,
                shapes=[[s["sid"], s.get("frames") or []] for s in shapes], bgmedia=bgmedia)


def _bgmedia(slide):
    return [[m["layer"], m["sid"]] for m in slide.get("media") or [] if m["layer"] != "slide"]


def _jobs(slide):
    """Envanter şekillerinden dışa aktarım işi: kimlik, sayaç kareleri, medya kutusu."""
    out = []
    for d in slide["shapes"]:
        j = dict(sid=d["sid"], id=d["id"], kind=d["kind"], box=[d["x"], d["y"], d["w"], d["h"]], media=d["kind"] == "media")
        if d["kind"] == "number":
            j.update(val=d["val"], frames=count_frames(d["val"]))
        out.append(j)
    return out


def render(deck, inv, work, nos, width=1920, log=print):
    """Seçilen slaytların katmanlarını work/layers/NNN altına üretir (önbellekli) ve PptDeck döndürür."""
    from PIL import Image
    W, H = width, round(width * inv["height"] / inv["width"])
    k = inv["width"] / W                                 # 1 piksel = k svg birimi
    root = work / "layers"
    todo = []
    for no in nos:
        shapes, bgmedia = _jobs(inv["slides"][no - 1]), _bgmedia(inv["slides"][no - 1])
        d = root / f"{no:03d}"
        meta = d / "layers.json"
        stamp = _stamp(deck, width, shapes, bgmedia)
        try:
            if json.loads(meta.read_text(encoding="utf-8"))["stamp"] == stamp:
                continue
        except Exception:
            pass
        todo.append((no, shapes, bgmedia, d, stamp))
    if todo:
        with _PowerPoint() as pp:
            pres = pp.open(deck)
            for no, shapes, bgmedia, d, stamp in todo:
                t0 = time.time()
                for old in d.glob("*.png"):
                    old.unlink()
                missing, texts = _export_slide(pres.Slides(no), d, shapes, bgmedia, W, H)
                t1 = time.time()
                raw = d / "raw"
                layers = {}
                for s in shapes:
                    if not (raw / f"{s['sid']}-w.png").exists():
                        continue
                    pair = lambda n: (Image.open(raw / f"{n}-w.png"), Image.open(raw / f"{n}-k.png"))  # noqa: E731
                    im, box = matte(*pair(s["sid"]))
                    if s["media"]:                       # medya kareleri şeklin kendi kutusuna oturur
                        x, y, w, h = s["box"]
                        box = (round(x / k), round(y / k), round((x + w) / k), round((y + h) / k))
                    if not box:
                        continue
                    L = dict(file=f"{s['sid']}.png", box=_crop_save(im, box, d / f"{s['sid']}.png"))
                    if s.get("frames"):
                        L["frames"] = []
                        for i in range(len(s["frames"])):
                            if not (raw / f"{s['sid']}-n{i}-w.png").exists():
                                break
                            fim, fbox = matte(*pair(f"{s['sid']}-n{i}"))
                            if fbox:
                                L["frames"].append(dict(file=f"{s['sid']}-n{i}.png",
                                                        box=_crop_save(fim, fbox, d / f"{s['sid']}-n{i}.png")))
                    if texts.get(str(s["sid"])):
                        L["text"] = texts[str(s["sid"])]
                    layers[str(s["sid"])] = L
                for name in ("full.png", "bg.png", "bgm.png"):
                    if (raw / name).exists():
                        (raw / name).replace(d / name)
                for f in raw.glob("*.png"):
                    f.unlink()
                raw.rmdir()
                info = dict(stamp=stamp, layers=layers, missing=missing, export_s=round(t1 - t0, 2),
                            matte_s=round(time.time() - t1, 2))
                info["fidelity"] = fidelity(d, layers)
                (d / "layers.json").write_text(json.dumps(info), encoding="utf-8")
                log(f"  slayt {no}: PowerPoint {info['export_s']} sn, katmanlar {info['matte_s']} sn, "
                    f"PowerPoint karesinden fark {info['fidelity']['mean']:.2f}/255")
    return PptDeck(inv, root, nos, k)


def fidelity(d, layers):
    """Katmanlar arka planın üstüne dizilince PowerPoint'in kendi karesine ne kadar yakın: ortalama ve en büyük fark
    (0-255) ile 8'den büyük farkın piksel oranı."""
    import numpy as np
    from PIL import Image
    acc = np.asarray(Image.open(d / "bg.png").convert("RGB"), dtype=np.float32)
    for L in layers.values():
        x0, y0, x1, y1 = L["box"]
        im = np.asarray(Image.open(d / L["file"]), dtype=np.float32)
        a = im[..., 3:] / 255
        acc[y0:y1, x0:x1] = im[..., :3] * a + acc[y0:y1, x0:x1] * (1 - a)
    diff = np.abs(acc - np.asarray(Image.open(d / "full.png").convert("RGB"), dtype=np.float32)).max(axis=2)
    return dict(mean=round(float(diff.mean()), 3), max=round(float(diff.max()), 1), over8=round(float((diff > 8).mean()), 5))


class PptDeck:
    """scene.build'in beklediği arayüz: viewbox, defs ve slide(no) -> dict(body, uses, groups)."""

    def __init__(self, inv, root, nos, k):
        self.inv, self.root, self.k = inv, root, k
        self.viewbox = [0, 0, inv["width"], inv["height"]]
        vb = " ".join(f"{v:g}" for v in self.viewbox)
        self.defs = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                     f'viewBox="{vb}" preserveAspectRatio="xMidYMid meet">')
        self.info = {no: json.loads((root / f"{no:03d}" / "layers.json").read_text(encoding="utf-8")) for no in nos}

    def _image(self, d, L, extra=""):
        x0, y0, x1, y1 = L["box"]
        k = self.k
        return (f'<image x="{x0 * k:.1f}" y="{y0 * k:.1f}" width="{(x1 - x0) * k:.1f}" height="{(y1 - y0) * k:.1f}" '
                f'preserveAspectRatio="none" href="{(d / L["file"]).as_uri()}"{extra}/>')

    def slide(self, no, media=True):
        """media: düzen/asıl slayttaki hareketli medya sahnede oynayacaksa arka plan onsuz çizilmiş olandır."""
        d, info = self.root / f"{no:03d}", self.info[no]
        W, H = self.viewbox[2:]
        bg = d / ("bgm.png" if media and (d / "bgm.png").exists() else "bg.png")
        out = [f'<defs><image id="srbg" x="0" y="0" width="{W:g}" height="{H:g}" preserveAspectRatio="none" '
               f'href="{bg.as_uri()}"/></defs>']
        groups = []
        for s in self.inv["slides"][no - 1]["shapes"]:
            L = info["layers"].get(str(s["sid"]))
            out.append(f'<g id="{s["id"]}" data-k="{s["kind"]}"><rect class="BoundingBox" stroke="none" fill="none" x="{s["x"]:.0f}" '
                       f'y="{s["y"]:.0f}" width="{s["w"]:.0f}" height="{s["h"]:.0f}"/>')
            if L:
                for i, f in enumerate(L.get("frames") or []):        # sayaç kareleri: sahne birini gösterir
                    out.append(self._image(d, f, f' data-n="{i}" display="none"'))
                n = len(L.get("frames") or [])
                out.append(self._image(d, L, f' data-n="{n}"' if n else ' data-media=""' if s["kind"] == "media" else ""))
            out.append("</g>")
            g = dict(id=s["id"], x=s["x"], y=s["y"], w=s["w"], h=s["h"])
            if L:                                       # katman kutusu ve metin satırları (svg birimi)
                x0, y0, x1, y1 = L["box"]
                g["box"] = [x0 * self.k, y0 * self.k, x1 * self.k, y1 * self.k]
                if L.get("text"):
                    g["text"] = L["text"]
            groups.append(g)
        return dict(body="\n".join(out), uses=["srbg"], groups=groups)
