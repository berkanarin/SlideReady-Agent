"""LibreOffice SVG dışa aktarımından slayt katmanlarını çıkarır.

LibreOffice her şekli kendi <g id="idN"> grubunda, slayttaki yerinde yazar. Bu modül bir slaytın gövdesini,
arka planını ve şekil gruplarını (konum kutusuyla) ayıklar; kimliksiz gruplara (resim, tablo) kimlik verir.
"""
import io
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation

G = re.compile(r"<g\b[^>]*?(/?)>|</g>")


def soffice_bin():
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    for p in ("/Applications/LibreOffice.app/Contents/MacOS/soffice",
              r"C:\Program Files\LibreOffice\program\soffice.exe"):
        if Path(p).exists():
            return p
    return None


A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R_EMBED = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"


def bake_alpha(deck, dst):
    """Görsellerin ek opaklığını (a:alphaModFix) kendi alfa kanalına çarparak gömer; değiştiyse dst'ye yazar.

    LibreOffice bu opaklığı alfaya çarpmak yerine alfadan çıkarır (166 alfa, %70 -> 89; doğrusu 116), düşük alfalı
    kenarlar sıfıra iner: yumuşak gölgeler daralır ve silikleşir. Kırpma (a:srcRect) doğru işlendiği için
    dokunulmaz. Aynı görseli kullanan her nesneye kendi kopyası verilir. Düzeltilen nesne sayısını döndürür.
    """
    prs = Presentation(str(deck))
    parts = [s.part for s in prs.slides] + [l.part for l in prs.slide_layouts] + [m.part for m in prs.slide_masters]
    fixed = 0
    for part in parts:
        for fix in list(part._element.iter(A + "alphaModFix")):
            blip = fix.getparent()
            rid = blip.get(R_EMBED)
            try:
                im = Image.open(io.BytesIO(part.related_part(rid).blob)).convert("RGBA")
            except Exception:  # vektör ya da açılamayan görsel: LibreOffice'e bırak
                continue
            amt = max(0, min(100000, int(fix.get("amt", "100000"))))
            a = im.getchannel("A").point(lambda v: (v * amt + 50000) // 100000)
            im.putalpha(a)
            buf = io.BytesIO()
            im.save(buf, "PNG")
            buf.seek(0)
            _, new_rid = part.get_or_add_image_part(buf)
            blip.set(R_EMBED, new_rid)
            blip.remove(fix)
            fixed += 1
    if fixed:
        prs.save(str(dst))
    return fixed


def convert(deck, outdir, fmt="svg:impress_svg_Export"):
    """PPTX'i SVG'ye (veya PDF'e) çevirir. Ayrı profil kullanır; açık bir LibreOffice ile çakışmaz."""
    outdir.mkdir(parents=True, exist_ok=True)
    ext = fmt.split(":")[0]
    out = outdir / (Path(deck).stem + "." + ext)
    if out.exists() and out.stat().st_mtime >= Path(deck).stat().st_mtime:
        return out
    with tempfile.TemporaryDirectory() as prof, tempfile.TemporaryDirectory() as tmp:
        baked = Path(tmp) / Path(deck).name
        src = baked if bake_alpha(deck, baked) else Path(deck)
        subprocess.run([soffice_bin(), f"-env:UserInstallation={Path(prof).as_uri()}", "--headless",
                        "--convert-to", fmt, "--outdir", str(outdir), str(src)],
                       check=True, capture_output=True, timeout=600)
    if not out.exists():
        raise RuntimeError(f"LibreOffice çıktı üretmedi: {out}")
    return out


def _balanced(svg, start):
    depth = 0
    for m in G.finditer(svg, start):
        if m[0] == "</g>":
            depth -= 1
        elif not m[1]:
            depth += 1
        if depth == 0:
            return m.end()
    raise ValueError("SVG grubu kapanmıyor")


class SvgDeck:
    def __init__(self, path):
        self.svg = Path(path).read_text(encoding="utf-8")
        head_end = self.svg.index('<g class="DummySlide">')
        head = re.sub(r"<script.*?</script>", "", self.svg[:head_end], flags=re.S)
        self.defs = head[head.index("<svg"):].replace("</svg>", "")
        self.viewbox = [float(v) for v in re.search(r'viewBox="([^"]+)"', self.svg)[1].split()]
        self.meta = {int(m[1]): dict(slide=m[2], master=m[3], bo=m[4] != "hidden") for m in re.finditer(
            r'id="ooo:meta_slide_(\d+)" ooo:slide="(id\d+)" ooo:master="(id\d+)"[^>]*?'
            r'ooo:master-objects-visibility="(\w+)"', self.svg)}
        if not self.meta:  # eski sürümler: görünürlük özniteliği yok
            self.meta = {int(m[1]): dict(slide=m[2], master=m[3], bo=True) for m in re.finditer(
                r'id="ooo:meta_slide_(\d+)" ooo:slide="(id\d+)" ooo:master="(id\d+)"', self.svg)}

    def slide(self, no):
        """no: 1 tabanlı slayt numarası -> dict(body, background_uses, groups)"""
        meta = self.meta[no - 1]
        start = self.svg.index('<g id="container-%s">' % meta["slide"])
        body = self.svg[start:_balanced(self.svg, start)]
        seq = iter(range(10 ** 6))
        # kimliksiz şekil grupları: resimler ve tablolar
        body = re.sub(r'(<g class="(?:Graphic|com\.sun\.star\.drawing\.TableShape)">\s*(?:<desc>.*?</desc>\s*)?)<g>',
                      lambda m: m[1] + '<g id="sr%d">' % next(seq), body, flags=re.S)
        own_bg = re.search(r'<g id="(bg-%s)" class="Background">' % meta["slide"], body)
        uses = [own_bg[1]] if own_bg else ["bg-" + meta["master"]]
        if meta["bo"]:
            uses.append("bo-" + meta["master"])
        groups = [dict(id=m[1], x=float(m[2]), y=float(m[3]), w=float(m[4]), h=float(m[5])) for m in re.finditer(
            r'<g id="((?:id|sr)\d+)">\s*<rect class="BoundingBox" stroke="none" fill="none" '
            r'x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"', body)]
        return dict(body=body, uses=uses, groups=groups)


def match(shapes, groups, tol=600):
    """PPTX şekillerini SVG gruplarına konum kutusu üzerinden eşler (aynı sırayla gelmeleri gerekmez).

    LibreOffice otomatik boyutlanan metin kutularının yüksekliğini metne göre küçültür; bu yüzden merkezler ve
    sol kenar karşılaştırılır, boyut farkı yalnızca eşitliği bozmak için kullanılır.
    """
    free = list(groups)
    for d in sorted(shapes, key=lambda d: -d["w"] * d["h"]):
        cy = d["y"] + d["h"] / 2

        def ok(g):
            return abs(g["x"] - d["x"]) < tol and abs(g["y"] + g["h"] / 2 - cy) < max(tol, max(g["h"], d["h"]) / 2)

        def cost(g):
            return (abs(g["x"] - d["x"]) + abs(g["y"] + g["h"] / 2 - cy)
                    + 0.3 * (abs(g["w"] - d["w"]) + abs(g["h"] - d["h"])))

        best = min(filter(ok, free), key=cost, default=None)
        if best:
            d["id"] = best["id"]
            free.remove(best)
    return free  # eşlenmeyen SVG grupları: olduğu gibi (sabit) görünür
