"""Gösteri efektleri: hangi slaytta hangi efektin oynayacağı ve efektlerin ihtiyaç duyduğu veri.

Her efekt PowerPoint'in çizdiği katmandan beslenir ve iş bitince katmanın kendisine devreder; son kare değişmez.
Bir slaytta tek bir "kahraman" efekt olur (parçacık ya da mürekkep); diğerleri destekleyicidir:

  süreklilik  klip önceki slaytın son karesinden başlar, gölgelendirici geçişle bu slaydın açılışına akar; ortak
              öğeler (asıl slayttaki logo, başlık şeridi) yerinden kımıldamaz
  aurora      slaydın kendi renklerinden üretilmiş, akan bir ışık perdesi; okuma payından önce tamamen söner
  ışık sızması kapak/bölüm/kapanış slaytlarında kenardan sızan sıcak ışık
  parçacık    başlık (ya da kahraman öğe) kendi piksellerinden örneklenmiş binlerce parçacıktan toplanır
  mürekkep    büyük görseller gürültü eşiğiyle, parlayan bir yanık kenarla açılır
  odometre    sayının her rakamı kendi sütununda döner ve kendi gecikmesiyle durur
"""
import zlib
from pathlib import Path

PARTICLES_MIN, PARTICLES_MAX = 2500, 9000
PARTICLE_FLIGHT = 1.9          # parçacıkların uçuşu + toparlanma (sn)
CONTINUITY = 0.85              # slaytlar arası geçiş süresi (sn)


def palette(full_png, bg_png):
    """Slaydın renkleri: zemin (bg ortalaması), vurgu (en doygun, parlak renk), ışık (zeminin açık tonu); 0-1 RGB."""
    import colorsys
    import numpy as np
    from PIL import Image
    bg = np.asarray(Image.open(bg_png).convert("RGB").resize((64, 36)), dtype=np.float32).reshape(-1, 3) / 255
    full = np.asarray(Image.open(full_png).convert("RGB").resize((96, 54)), dtype=np.float32).reshape(-1, 3) / 255
    base = np.median(bg, axis=0)
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in full])
    vivid = full[(hsv[:, 1] > 0.45) & (hsv[:, 2] > 0.45)]
    if len(vivid) >= 8:
        hues = (np.array([colorsys.rgb_to_hsv(*p)[0] for p in vivid]) * 12).astype(int) % 12
        top = np.bincount(hues, minlength=12).argmax()
        accent = vivid[hues == top].mean(axis=0)
    else:
        accent = np.array([1.0, 0.72, 0.3])            # sıcak altın
    h, s, v = colorsys.rgb_to_hsv(*base)
    light = np.array(colorsys.hsv_to_rgb(h, min(1, s * 0.9 + 0.1), min(1, v * 2.6 + 0.25)))
    r = lambda a: [round(float(x), 3) for x in a]  # noqa: E731
    return dict(base=r(base), accent=r(accent), light=r(light))


def particles(layer_file, box, seed):
    """Katman piksellerinden parçacıklar: konum (svg birimi) ve renk. Opak alan büyüdükçe parçacık artar."""
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(layer_file).convert("RGBA"))
    ys, xs = np.nonzero(im[..., 3] > 110)
    if len(xs) < 50:
        return None
    n = int(min(PARTICLES_MAX, max(PARTICLES_MIN, len(xs) / 6)))
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(xs), size=min(n, len(xs)), replace=False)
    sx, sy = (box[2] - box[0]) / im.shape[1], (box[3] - box[1]) / im.shape[0]
    px = np.round(box[0] + (xs[pick] + 0.5) * sx).astype(int)
    py = np.round(box[1] + (ys[pick] + 0.5) * sy).astype(int)
    col = im[ys[pick], xs[pick], :3]
    area = len(xs) * sx * sy
    return dict(n=len(pick), area=round(float(area)), xy=np.column_stack([px, py]).ravel().tolist(),
                rgb=col.ravel().tolist())


def _shift(scene, dt):
    for d in scene:
        d["t0"] = round(d["t0"] + dt, 3)
        for key in ("bt",):
            if key in d:
                d[key] = [round(x + dt, 3) for x in d[key]]
        if "parts" in d:
            d["parts"] = [p[:4] + [round(p[4] + dt, 3)] for p in d["parts"]]


def apply(scene, st, plan, layer, groups, area):
    """Efekt kararlarını sahneye ve tarza yazar; efektlerin bitmesi için gereken en geç anı döndürür."""
    on = plan.get("effects", True) and st["name"] != "sakin"
    st["fx"] = on
    if not on:
        return 0.0
    last = 0.0
    hero_zoom = (st.get("zoom") or 1) >= 1.10
    try:
        st["palette"] = palette(layer["full"], layer["opening"])
    except Exception:
        st["palette"] = None
    st["aurora"] = 0.32 if hero_zoom else (0.16 if plan.get("lead") in ("number", "chart") else 0.24)
    if hero_zoom:
        st["leak"] = True
    if plan.get("continuity", True) and layer.get("prev"):
        st["cont"] = dict(prev=Path(layer["prev"]).as_uri(), to=Path(layer["opening"]).as_uri(), dur=CONTINUITY,
                          kind="zoom" if hero_zoom else "warp")
        _shift(scene, CONTINUITY * 0.55)
    # kahraman efekt: kapak/bölüm/kapanışta başlık parçacıklardan toplanır; yoksa en büyük görsel mürekkeple açılır
    hero = None
    if hero_zoom:
        cands = [d for d in scene if d["kind"] == "title"] or \
                sorted((d for d in scene if d["kind"] in ("text", "number")), key=lambda d: -d["w"] * d["h"])[:1]
        hero = cands[0] if cands else None
        g = groups.get(hero["id"]) if hero else None
        pts = particles(g["file"], g["box"], zlib.crc32(hero["id"].encode())) if g and g.get("file") else None
        if pts:
            hero.update(fx="particles", pts=pts)
            hero.pop("parts", None)
            last = max(last, hero["t0"] + PARTICLE_FLIGHT)
        else:
            hero = None
    if not hero:
        pics = sorted((d for d in scene if d["kind"] == "picture" and d["w"] * d["h"] > 0.12 * area),
                      key=lambda d: -d["w"] * d["h"])
        if pics:
            pics[0]["fx"] = "ink"
            last = max(last, pics[0]["t0"] + 1.4)
    for d in scene:                                          # odometre: her rakam kendi sütununda
        g = groups.get(d["id"])
        if d["kind"] == "number" and g and g.get("odo"):
            d["odo"] = g["odo"]
            last = max(last, d["t0"] + 2.2)
    return last
