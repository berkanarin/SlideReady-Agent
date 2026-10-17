"""LibreOffice SVG dışa aktarımından slayt katmanlarını çıkarır.

LibreOffice her şekli kendi <g id="idN"> grubunda, slayttaki yerinde yazar. Bu modül bir slaytın gövdesini,
arka planını ve şekil gruplarını (konum kutusuyla) ayıklar; kimliksiz gruplara (resim, tablo) kimlik verir.
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

G = re.compile(r"<g\b[^>]*?(/?)>|</g>")
REF = re.compile(r'href="#([^"]+)"|url\(#([^)]+)\)')


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


def convert(deck, outdir, fmt="svg:impress_svg_Export"):
    """PPTX'i SVG'ye (veya PDF'e) çevirir. Ayrı profil kullanır; açık bir LibreOffice ile çakışmaz."""
    outdir.mkdir(parents=True, exist_ok=True)
    ext = fmt.split(":")[0]
    out = outdir / (Path(deck).stem + "." + ext)
    if out.exists() and out.stat().st_mtime >= Path(deck).stat().st_mtime:
        return out
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([soffice_bin(), f"-env:UserInstallation={Path(prof).as_uri()}", "--headless",
                        "--convert-to", fmt, "--outdir", str(outdir), str(deck)],
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


def _element(svg, start):
    """svg[start] '<' ile başlayan öğenin bitişi (kendi kendini kapatan, <g> ya da aynı adlı iç içe öğe)."""
    tag = re.match(r"<([\w:.-]+)", svg[start:])[1]
    if tag == "g":
        return _balanced(svg, start)
    pat = re.compile(r"<%s\b[^>]*?(/?)>|</%s>" % (re.escape(tag), re.escape(tag)))
    depth = 0
    for m in pat.finditer(svg, start):
        if m[0].startswith("</"):
            depth -= 1
        elif not m[1]:
            depth += 1
        if depth == 0:
            return m.end()
    raise ValueError(f"SVG öğesi kapanmıyor: {tag}")


class SvgDeck:
    def __init__(self, path):
        self.svg = Path(path).read_text(encoding="utf-8")
        head_end = self.svg.index('<g class="DummySlide">')
        head = re.sub(r"<script.*?</script>", "", self.svg[:head_end], flags=re.S)
        self.defs = head[head.index("<svg"):].replace("</svg>", "")
        self.ids = {m[1]: m.start() for m in re.finditer(r'\sid="([^"]+)"', self.svg)}
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
        masters = [self.svg[self.ids[u]:_balanced(self.svg, self.svg.rindex("<", 0, self.ids[u]))]
                   for u in uses if u in self.ids]
        shared = self.shared(body + "".join(masters))
        if shared:
            body += '\n<defs class="SlideReadyShared">%s</defs>' % shared
        return dict(body=body, uses=uses, groups=groups)

    def shared(self, text):
        """Sahnede kullanılıp sahnenin dışında tanımlı öğeler (yeni LibreOffice sürümleri tekrar eden görselleri bir
        kez yazar, sonrakileri <use> ile çağırır; tanım başka bir slaytta ya da belgenin sonunda kalabilir)."""
        have = set(re.findall(r'\sid="([^"]+)"', self.defs + text))
        out, todo = [], [text]
        while todo:
            for m in REF.finditer(todo.pop()):
                ref = m[1] or m[2]
                if ref in have or ref not in self.ids:
                    continue
                start = self.svg.rindex("<", 0, self.ids[ref])
                el = self.svg[start:_element(self.svg, start)]
                el = re.sub(r'\svisibility="hidden"', "", el, count=1)
                have.update(re.findall(r'\sid="([^"]+)"', el))
                out.append(el)
                todo.append(el)
        return "\n".join(out)


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
