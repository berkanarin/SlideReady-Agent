"""Hızlı testler: python3 -m unittest discover tests  (LibreOffice gerektirir)"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from slideready.deck import inventory, number_parts  # noqa: E402
from slideready.layers import SvgDeck, convert, match  # noqa: E402
from slideready.media import collect, strip_video  # noqa: E402
from slideready.regions import blocks  # noqa: E402

DEMO = ROOT / "examples" / "demo.pptx"


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


class ImageRegions(unittest.TestCase):
    """Metin/şekil resim olarak konmuşsa resim okuma sırasıyla bloklara ayrılır; fotoğraf bölünmez."""

    @staticmethod
    def png(im):
        import io
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return buf.getvalue()

    def test_screenshot_splits_in_reading_order(self):
        from PIL import Image, ImageDraw
        im = Image.new("RGB", (1600, 900), (245, 247, 250))
        d = ImageDraw.Draw(im)
        d.rectangle((80, 60, 700, 140), fill=(20, 30, 90))                 # başlık
        for i in range(3):                                                  # üç kart
            d.rectangle((80 + i * 500, 260, 500 + i * 500, 520), fill=(20, 60, 180))
        d.rectangle((80, 640, 1500, 820), fill=(240, 170, 0))               # alt şerit
        r = blocks(self.png(im))
        self.assertEqual(r["bg"], "#f5f7fa")
        self.assertEqual(len(r["blocks"]), 5)
        xs = [b[0] for b in r["blocks"][1:4]]
        self.assertEqual(xs, sorted(xs))
        self.assertLess(r["blocks"][0][1], r["blocks"][1][1])

    def test_transparent_background(self):
        from PIL import Image, ImageDraw
        im = Image.new("RGBA", (800, 400), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((40, 40, 300, 360), fill=(200, 0, 0, 255))
        d.rectangle((460, 40, 760, 360), fill=(0, 0, 200, 255))
        r = blocks(self.png(im))
        self.assertIsNone(r["bg"])
        self.assertEqual(len(r["blocks"]), 2)

    def test_photo_is_not_split(self):
        import random
        from PIL import Image
        rnd = random.Random(1)
        im = Image.new("RGB", (320, 180))
        im.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)) for _ in range(320 * 180)])
        self.assertIsNone(blocks(self.png(im)))


FAKE_SVG = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
 viewBox="0 0 33867 19050"><defs class="ClipPathGroup"/>
<g id="id20" class="Master_Slide"><g id="bg-id20" class="Background"/><g id="bo-id20" class="BackgroundObjects">
<g class="Graphic"><g><rect class="BoundingBox" stroke="none" fill="none" x="0" y="0" width="33867" height="19050"/>
<use xlink:href="#bitmap7"/></g></g></g></g>
<g class="DummySlide"></g>
<g id="ooo:meta_slide_0" ooo:slide="id1" ooo:master="id20" ooo:master-objects-visibility="visible"/>
<g visibility="hidden"><g id="container-id1"><g id="id1" class="Slide"><g class="Page">
<g class="TextShape"><g id="id5"><rect class="BoundingBox" stroke="none" fill="none" x="100" y="200" width="300" height="400"/>
<use xlink:href="#bitmap9" x="5"/></g></g></g></g></g></g>
<defs class="EmbeddedBitmaps"><image id="bitmap7" x="0" y="0" width="33867" height="19050" xlink:href="data:x"/>
<g id="bitmap9" visibility="hidden"><image width="1" height="1" style="fill:url(#grad3)"/></g>
<linearGradient id="grad3"><stop offset="0"/></linearGradient></defs>
</svg>"""


class SharedBitmaps(unittest.TestCase):
    """Yeni LibreOffice sürümleri tekrar eden görselleri bir kez tanımlayıp <use> ile çağırır; tanım slaytın ve
    asıl slaytın dışında kalsa da sahneye taşınmalı (aksi hâlde arka plan görselleri kaybolur)."""

    def test_definitions_outside_scene_are_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "x.svg"
            f.write_text(FAKE_SVG, encoding="utf-8")
            layer = SvgDeck(f).slide(1)
        for ref in ("bitmap7", "bitmap9", "grad3"):          # asıl slayttan, slayttan ve dolaylı referans
            self.assertIn(f'id="{ref}"', layer["body"], ref)
        self.assertNotIn('<g id="bitmap9" visibility="hidden"', layer["body"])
        self.assertEqual([g["id"] for g in layer["groups"]], ["id5"])
        self.assertEqual(layer["uses"], ["bg-id20", "bo-id20"])


def media_deck(tmp):
    """Kurgusal deste: 1. slaytta tam ekran arka plan videosu + üstünde veri, düzende animasyonlu bir GIF."""
    from PIL import Image, ImageDraw
    from pptx import Presentation
    from pptx.util import Emu
    tmp = Path(tmp)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=3",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-pix_fmt", "yuv420p", "-shortest",
                    str(tmp / "bg.mp4")], check=True)
    frames = []
    for i in range(10):
        im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((i * 6, 20, i * 6 + 40, 60), fill=(255, 190, 0, 255))
        frames.append(im)
    frames[0].save(tmp / "spin.gif", save_all=True, append_images=frames[1:], duration=80, loop=0, disposal=2)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    layout = prs.slide_layouts[6]
    s1 = prs.slides.add_slide(layout)
    pic = s1.shapes.add_picture(str(tmp / "spin.gif"), 0, 0, Emu(900000), Emu(900000))
    _, rid = layout.part.get_or_add_image_part(str(tmp / "spin.gif"))
    pic._element.getparent().remove(pic._element)
    pic._element.xpath(".//a:blip")[0].set("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed", rid)
    pic._element.xpath(".//p:cNvPr")[0].set("id", "90")
    layout.shapes._spTree.append(pic._element)
    s1.shapes.add_movie(str(tmp / "bg.mp4"), 0, 0, prs.slide_width, prs.slide_height, mime_type="video/mp4")
    box = s1.shapes.add_shape(1, Emu(1500000), Emu(2500000), Emu(4000000), Emu(1500000))
    box.text_frame.text = "%42"
    s2 = prs.slides.add_slide(layout)
    s2.shapes.add_shape(1, Emu(1500000), Emu(2500000), Emu(4000000), Emu(1500000)).text_frame.text = "Merhaba"
    prs.save(str(tmp / "media.pptx"))
    return tmp / "media.pptx"


@unittest.skipUnless((shutil.which("soffice") or shutil.which("libreoffice")) and shutil.which("ffmpeg"),
                     "LibreOffice/ffmpeg yok")
class Media(unittest.TestCase):
    def test_collects_video_and_layout_gif(self):
        with tempfile.TemporaryDirectory() as tmp:
            deck = media_deck(tmp)
            media = collect(deck, Path(tmp))
            self.assertEqual(sorted((m["type"], m["layer"]) for m in media[1]), [("gif", "layout"), ("video", "slide")])
            self.assertEqual([(m["type"], m["layer"]) for m in media[2]], [("gif", "layout")])
            video = next(m for m in media[1] if m["type"] == "video")
            self.assertAlmostEqual(video["duration"], 3, delta=0.2)
            self.assertTrue(video["audio"])
            # video içeren sunum LibreOffice'te SVG'ye çevrilemeyebiliyor: poster görseline çevrilmiş kopya çevrilir
            self.assertTrue(strip_video(deck, Path(tmp) / "s.pptx"))
            svg = SvgDeck(convert(Path(tmp) / "s.pptx", Path(tmp) / "svg"))
            self.assertEqual(len(svg.meta), 2)

    @unittest.skipUnless(shutil.which("node"), "Node yok")
    def test_background_video_plays_in_scene(self):
        """Medya açıkken iki an arasındaki fark, medya kapalıyken olandan çok daha büyük olmalı."""
        from PIL import Image, ImageChops, ImageStat
        with tempfile.TemporaryDirectory() as tmp:
            deck, work = media_deck(tmp), Path(tmp) / "w"

            def change(media_on):
                subprocess.run([str(ROOT / "bin" / "slideready"), "analyze", str(deck), "-w", str(work)], check=True,
                               capture_output=True)
                plan = json.loads((work / "plan.json").read_text(encoding="utf-8"))
                plan["slides"][0]["media"] = media_on
                (work / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
                subprocess.run([str(ROOT / "bin" / "slideready"), "preview", str(deck), "-w", str(work), "--slides", "1"],
                               check=True, capture_output=True)
                stills = sorted((work / "scenes" / "001").glob("still-*.png"), key=lambda p: float(p.stem[6:]))
                a, b = (Image.open(p).convert("RGB") for p in (stills[0], stills[2]))
                for p in stills:
                    p.unlink()
                return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean)

            on, off = change(True), change(False)
            self.assertGreater(on, 4 * off + 5, (on, off))
            scene = json.loads((work / "scenes" / "001" / "scene.json").read_text(encoding="utf-8"))
            self.assertEqual(scene["media"], [])


if __name__ == "__main__":
    unittest.main()
