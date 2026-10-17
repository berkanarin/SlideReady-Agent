"""Resim içindeki içerik blokları: metin, şekil ya da grafik slayta resim olarak konmuşsa (ekran görüntüsü, başka bir
araçtan yapıştırılmış tablo) resim tek parça yerine okuma sırasıyla blok blok açılabilsin.

OCR yapılmaz: düz renkli (ya da saydam) zemin bulunur, içerik bu zeminden ayrılan boşluklarla (XY-kesme) bloklara
bölünür. Fotoğraf gibi düz zemini olmayan resimler blok üretmez ve eskisi gibi tek parça açılır.
"""
import io

from PIL import Image

SIDE = 240          # çözümleme çözünürlüğü (uzun kenar, piksel)
MIN_GAP = 0.025     # blokları ayıran en küçük boşluk (resim boyutuna oranla)
MAX_BLOCKS = 24


def _mask(im):
    """Zemin rengi ve içerik maskesi (satır satır bool listesi); zemin düz değilse None."""
    w, h = im.size
    px = im.load()
    border = [px[x, y] for x in range(w) for y in (0, h - 1)] + [px[x, y] for y in range(h) for x in (0, w - 1)]
    transparent = sum(p[3] < 16 for p in border) > 0.85 * len(border)
    if transparent:
        bg = (0, 0, 0, 0)
        return bg, [[px[x, y][3] >= 48 for x in range(w)] for y in range(h)]
    q = {}
    for p in border:
        k = tuple(c // 8 for c in p[:3])
        q[k] = q.get(k, 0) + 1
    mode = max(q, key=q.get)
    near = [p for p in border if max(abs(c // 8 - m) for c, m in zip(p[:3], mode)) <= 2]
    if len(near) < 0.85 * len(border):
        return None
    bg = tuple(sum(p[i] for p in near) // len(near) for i in range(3)) + (255,)

    def ink(p):
        return p[3] >= 48 and max(abs(c - b) for c, b in zip(p[:3], bg[:3])) > 40

    return bg, [[ink(px[x, y]) for x in range(w)] for y in range(h)]


def _runs(flags, gap):
    """Dolu aralıklar [(a, b)]; gap'ten kısa boşluklar birleştirilir."""
    out, start, empty = [], None, 0
    for i, f in enumerate(flags + [False] * (gap + 1)):
        if f:
            if start is None:
                start = i
            empty = 0
        elif start is not None:
            empty += 1
            if empty > gap:
                out.append((start, i - empty + 1))
                start, empty = None, 0
    return out


def _cut(mask, x0, y0, x1, y1, gx, gy, depth):
    rows = [any(mask[y][x0:x1]) for y in range(y0, y1)]
    bands = [(y0 + a, y0 + b) for a, b in _runs(rows, gy)]
    out = []
    for a, b in bands:
        cols = [any(mask[y][x] for y in range(a, b)) for x in range(x0, x1)]
        parts = [(x0 + c, x0 + d) for c, d in _runs(cols, gx)]
        for c, d in parts:
            if depth and (len(bands) > 1 or len(parts) > 1):
                out += _cut(mask, c, a, d, b, gx, gy, depth - 1)
            else:
                out.append((c, a, d, b))
    return out


def blocks(blob):
    """Döner: dict(bg="#rrggbb" | None (saydam), blocks=[[x, y, w, h], ...] resim kutusuna oranla) ya da None."""
    try:
        im = Image.open(io.BytesIO(blob))
        im.seek(0)
        im = im.convert("RGBA")
    except Exception:
        return None
    im.thumbnail((SIDE, SIDE))
    w, h = im.size
    if w < 16 or h < 16:
        return None
    got = _mask(im)
    if not got:
        return None
    bg, mask = got
    gx, gy = max(2, int(w * MIN_GAP)), max(2, int(h * MIN_GAP))
    found = [b for b in _cut(mask, 0, 0, w, h, gx, gy, 3) if (b[2] - b[0]) * (b[3] - b[1]) >= 0.002 * w * h]
    if not 2 <= len(found) <= MAX_BLOCKS:
        return None
    pad = 1
    boxes = []
    for x0, y0, x1, y1 in sorted(found, key=lambda b: (round(b[1] / (h * 0.06)), b[0])):
        x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
        boxes.append([round(x0 / w, 4), round(y0 / h, 4), round((x1 - x0) / w, 4), round((y1 - y0) / h, 4)])
    return dict(bg=None if bg[3] == 0 else "#%02x%02x%02x" % bg[:3], blocks=boxes)
