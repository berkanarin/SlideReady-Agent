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


if __name__ == "__main__":
    unittest.main()
