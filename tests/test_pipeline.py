"""Hızlı testler: python3 -m unittest discover tests  (LibreOffice gerektirir)"""
import base64
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lxml import etree  # noqa: E402
from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

from slideready.deck import inventory, number_parts  # noqa: E402
from slideready.layers import SvgDeck, convert, match  # noqa: E402

DEMO = ROOT / "examples" / "demo.pptx"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
CROP = dict(l=16928, t=7315, r=4237)  # 1/1000 % (OOXML a:srcRect)


def shadow_png(path, w=2047, h=114, peak=166):
    """Kurgusal yumuşak gölge: paletli (P + tRNS) PNG, alfa kenarlardan merkeze 0 -> peak."""
    im = Image.new("P", (w, h))
    im.putpalette([0, 0, 0] * 256)
    cx, cy, rx, ry = w / 2, h / 2, w / 2 - 30, h / 2 - 3
    im.putdata([int(peak * max(0.0, 1 - ((x - cx) / rx) ** 2 - ((y - cy) / ry) ** 2) ** 1.5)
                for y in range(h) for x in range(w)])
    im.save(path, transparency=bytes(range(256)))


def shadow_deck(path, png, slides=2, amt=70000):
    """Her slaytta aynı gölge görseli: ek opaklık (a:alphaModFix) + kırpma (a:srcRect)."""
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    for _ in range(slides):
        pic = prs.slides.add_slide(prs.slide_layouts[6]).shapes.add_picture(
            str(png), Emu(1000000), Emu(5000000), Emu(10000000), Emu(520000))
        blip = pic._element.find(f".//{A}blip")
        etree.SubElement(blip, A + "alphaModFix").set("amt", str(amt))
        rect = etree.Element(A + "srcRect", {k: str(v) for k, v in CROP.items()})
        blip.addnext(rect)
    prs.save(str(path))


def slide_bitmaps(svg, body):
    """Slayt gövdesindeki gömülü PNG'ler; <use> ile paylaşılan bitmap'ler de çözülür."""
    found = re.findall(r'<image\b[^>]*?href="data:image/png;base64,([^"]+)"', body)
    for ref in re.findall(r'<use\b[^>]*?href="#([^"]+)"', body):
        m = re.search(r'id="%s"' % re.escape(ref), svg)
        img = m and re.compile(r'<image\b[^>]*?href="data:image/png;base64,([^"]+)"').search(svg, m.start())
        if img:
            found.append(img[1])
    return [Image.open(io.BytesIO(base64.b64decode(b))).convert("RGBA") for b in found]


class Numbers(unittest.TestCase):
    def test_counters(self):
        self.assertEqual(number_parts("₺12,4M"), ("₺", "12,4", "M"))
        self.assertEqual(number_parts("%38"), ("%", "38", ""))
        self.assertEqual(number_parts("1.250"), ("", "1.250", ""))
        self.assertEqual(number_parts("+%31"), ("+%", "31", ""))
        self.assertEqual(number_parts("9 gün"), ("", "9", "gün"))

    def test_not_counters(self):
        for s in ("01", "2026", "2026 Yıl Sonu Özeti", "Başlık"):
            self.assertIsNone(number_parts(s), s)


@unittest.skipUnless(shutil.which("soffice") or shutil.which("libreoffice"), "LibreOffice yok")
class Layers(unittest.TestCase):
    def test_every_shape_matches_a_layer(self):
        inv = inventory(DEMO)
        with tempfile.TemporaryDirectory() as tmp:
            svg = SvgDeck(convert(DEMO, Path(tmp)))
            for s in inv["slides"]:
                free = match(s["shapes"], svg.slide(s["no"])["groups"])
                self.assertEqual([d["name"] for d in s["shapes"] if "id" not in d], [], f"slayt {s['no']}")
                self.assertEqual(free, [], f"slayt {s['no']}")

    def test_analyze_writes_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([str(ROOT / "bin" / "slideready"), "analyze", str(DEMO), "-w", tmp], check=True,
                           capture_output=True)
            plan = json.loads((Path(tmp) / "plan.json").read_text(encoding="utf-8"))
            self.assertEqual(len(plan["slides"]), 4)
            self.assertTrue(all(p["animate"] for p in plan["slides"]))


@unittest.skipUnless(shutil.which("soffice") or shutil.which("libreoffice"), "LibreOffice yok")
class TransparentPictures(unittest.TestCase):
    """Beklenen değer LibreOffice çıktısından değil, kaynak görselden hesaplanır: kırp, alfayı amt ile çarp."""

    def test_alpha_mod_and_crop_survive_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            shadow_png(tmp / "shadow.png")
            shadow_deck(tmp / "shadow.pptx", tmp / "shadow.png")
            src = Image.open(tmp / "shadow.png").convert("RGBA").getchannel("A")
            w, h = src.size
            box = (round(w * CROP["l"] / 1e5), round(h * CROP["t"] / 1e5), w - round(w * CROP["r"] / 1e5), h)
            want = src.crop(box).point(lambda v: round(v * 0.7))
            svg = SvgDeck(convert(tmp / "shadow.pptx", tmp / "svg"))
            for no in (1, 2):
                imgs = slide_bitmaps(svg.svg, svg.slide(no)["body"])
                self.assertEqual(len(imgs), 1, f"slayt {no}")
                got = imgs[0].getchannel("A")
                self.assertLessEqual(abs(got.size[0] - want.size[0]), 3, f"slayt {no}: kırpma genişliği")
                self.assertLessEqual(abs(got.size[1] - want.size[1]), 2, f"slayt {no}: kırpma yüksekliği")
                self.assertLessEqual(abs(got.getextrema()[1] - want.getextrema()[1]), 2, f"slayt {no}: tepe alfa")
                gb, wb = got.getbbox(), want.getbbox()
                self.assertGreaterEqual(gb[2] - gb[0], 0.97 * (wb[2] - wb[0]), f"slayt {no}: gölge daraldı")
                self.assertGreaterEqual(gb[3] - gb[1], 0.95 * (wb[3] - wb[1]), f"slayt {no}: gölge inceldi")

    def test_source_deck_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            shadow_png(tmp / "shadow.png")
            shadow_deck(tmp / "shadow.pptx", tmp / "shadow.png", slides=1)
            before = (tmp / "shadow.pptx").read_bytes()
            convert(tmp / "shadow.pptx", tmp / "svg")
            self.assertEqual((tmp / "shadow.pptx").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
