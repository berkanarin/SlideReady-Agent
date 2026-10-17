"""Örnek deste üretir: examples/demo.pptx

SlideReady'nin desteklediği öğe türlerini tek yerde toplar: başlık, KPI sayıları, sütun / çubuk / çizgi /
halka grafikler, tablo, gruplanmış süreç şekilleri. İçerik tamamen kurgusaldır.

Kullanım: python3 examples/make_demo.py [cikti.pptx]
"""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Pt

BG1, BG2, CARD = RGBColor(0x1C, 0x21, 0x33), RGBColor(0x0F, 0x12, 0x1C), RGBColor(0x26, 0x2C, 0x44)
WHITE, MUTED, CORAL, SKY, MINT = (RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xB4, 0xBA, 0xCC), RGBColor(0xFF, 0x7A, 0x59),
                                  RGBColor(0x4C, 0xC9, 0xF0), RGBColor(0x8A, 0xE6, 0xB0))
EDGE, GRID = RGBColor(0x3A, 0x42, 0x63), RGBColor(0x2C, 0x33, 0x4E)
FONT = "Liberation Sans"
pt = lambda v: Pt(v * 0.75)          # yazı boyutları da tasarım ölçeğinde
px = lambda v: Emu(int(v * 6350))   # 1920x1080 tasarım pikseli -> EMU (16:9 slayt, 12192000 EMU geniş)


def text(sl, x, y, w, h, s, size, color=WHITE, bold=False, align=PP_ALIGN.LEFT, name=None):
    tb = sl.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, line in enumerate(s.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size, r.font.bold, r.font.color.rgb, r.font.name = pt(size), bold, color, FONT
    if name:
        tb.name = name
    return tb


def box(sl, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=None):
    b = sl.shapes.add_shape(shape, px(x), px(y), px(w), px(h))
    b.fill.solid()
    b.fill.fore_color.rgb = fill
    if line:
        b.line.color.rgb = line
        b.line.width = Pt(1.25)
    else:
        b.line.fill.background()
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        b.adjustments[0] = 0.08
    return b


def chart(sl, kind, x, y, w, h, cats, series, colors, legend=True):
    data = CategoryChartData()
    data.categories = cats
    for name, vals in series:
        data.add_series(name, vals)
    gf = sl.shapes.add_chart(kind, px(x), px(y), px(w), px(h), data)
    c = gf.chart
    c.has_title = False
    c.font.size, c.font.color.rgb, c.font.name = pt(14), MUTED, FONT
    c.has_legend = legend and len(series) > 1
    if c.has_legend:
        c.legend.position, c.legend.include_in_layout = XL_LEGEND_POSITION.TOP, False
        c.legend.font.color.rgb = WHITE
    plot = c.plots[0]
    for s, col in zip(plot.series, colors):
        if kind in (XL_CHART_TYPE.LINE_MARKERS, XL_CHART_TYPE.LINE):
            s.format.line.color.rgb, s.format.line.width, s.smooth = col, Pt(3), False
        else:
            s.format.fill.solid()
            s.format.fill.fore_color.rgb = col
    if kind in (XL_CHART_TYPE.COLUMN_CLUSTERED, XL_CHART_TYPE.BAR_CLUSTERED):
        plot.gap_width = 60
    if kind not in (XL_CHART_TYPE.DOUGHNUT, XL_CHART_TYPE.PIE):
        for ax in (c.category_axis, c.value_axis):
            ax.tick_labels.font.color.rgb = MUTED
            ax.format.line.color.rgb = EDGE
        c.value_axis.has_major_gridlines = True
        c.value_axis.major_gridlines.format.line.color.rgb = GRID
    return gf


def slide(prs, title, sub=None):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    sl.background.fill.gradient()
    sl.background.fill.gradient_angle = 90
    st = sl.background.fill.gradient_stops
    st[0].color.rgb, st[1].color.rgb = BG1, BG2
    text(sl, 96, 56, 1400, 90, title, 40, bold=True, name="Başlık")
    if sub:
        text(sl, 96, 140, 1400, 50, sub, 20, MUTED, name="Alt başlık")
    return sl


def main(out):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)

    # 1. KPI kartları + halka
    sl = slide(prs, "2026 Yıl Sonu Özeti", "Örnek A.Ş. · kurgusal veriler")
    for i, (val, lbl) in enumerate([("₺12,4M", "Toplam gelir"), ("%38", "Büyüme"), ("1.250", "Yeni müşteri")]):
        x = 96 + i * 440
        box(sl, x, 260, 400, 260, CARD, line=EDGE)
        box(sl, x + 32, 300, 64, 8, CORAL, MSO_SHAPE.RECTANGLE)
        text(sl, x + 32, 330, 340, 110, val, 54, CORAL, True)
        text(sl, x + 32, 440, 340, 50, lbl, 20, MUTED)
    box(sl, 1424, 260, 400, 560, CARD, line=EDGE)
    chart(sl, XL_CHART_TYPE.DOUGHNUT, 1484, 300, 280, 280, ["Hedefe ulaşan", "Kalan"], [("Hedef", (72, 28))], [CORAL])
    dn = sl.shapes[-1].chart.plots[0]
    for idx, col in enumerate([CORAL, EDGE]):
        point = dn.series[0].points[idx]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = col
    text(sl, 1544, 400, 160, 80, "%72", 36, WHITE, True, PP_ALIGN.CENTER)
    text(sl, 1460, 600, 330, 120, "Hedeflerin %72'si yıl sonunda tamamlandı.", 20, MUTED, align=PP_ALIGN.CENTER)
    text(sl, 96, 580, 1240, 240, "Gelirdeki artışın büyük kısmı ikinci yarıda geldi.\nYeni müşterilerin üçte biri kurumsal segmentte.", 24, WHITE)

    # 2. Sütun grafik + açıklama
    sl = slide(prs, "Çeyreklere göre gelir", "Milyon ₺, 2025 ve 2026")
    chart(sl, XL_CHART_TYPE.COLUMN_CLUSTERED, 96, 220, 1120, 760, ["Ç1", "Ç2", "Ç3", "Ç4"],
          [("2025", (2.1, 2.4, 2.2, 2.9)), ("2026", (2.5, 2.8, 3.3, 3.8))], [SKY, CORAL])
    box(sl, 1290, 260, 534, 640, CARD)
    text(sl, 1330, 300, 460, 100, "+%31", 64, CORAL, True)
    text(sl, 1330, 410, 460, 60, "Ç4 yıllık artış", 22, MUTED)
    text(sl, 1330, 500, 460, 360, "• En güçlü çeyrek Ç4\n• Ç3'te kampanya etkisi\n• 2026 her çeyrekte 2025'in üzerinde", 22, WHITE)

    # 3. Tablo + çizgi grafik
    sl = slide(prs, "Bölge performansı", "Hedef ve gerçekleşen")
    rows = [("Bölge", "Hedef", "Gerçekleşen", "Oran"), ("Marmara", "4.200", "4.650", "%111"), ("Ege", "2.100", "2.050", "%98"),
            ("İç Anadolu", "1.800", "1.920", "%107"), ("Akdeniz", "1.500", "1.610", "%107"), ("Karadeniz", "900", "870", "%97")]
    tbl = sl.shapes.add_table(len(rows), 4, px(96), px(240), px(860), px(520)).table
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = EDGE if r == 0 else (CARD if r % 2 else BG1)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
            run = p.add_run()
            run.text = v
            run.font.size, run.font.bold, run.font.name = pt(18), r == 0, FONT
            run.font.color.rgb = WHITE
    chart(sl, XL_CHART_TYPE.LINE_MARKERS, 1010, 220, 820, 560, ["Oca", "Şub", "Mar", "Nis", "May", "Haz"],
          [("Gerçekleşen", (62, 70, 68, 81, 88, 95)), ("Hedef", (65, 68, 72, 76, 80, 84))], [CORAL, MINT])
    text(sl, 1010, 820, 820, 100, "Haziran itibarıyla hedefin %13 üzerinde.", 22, WHITE)

    # 4. Gruplanmış süreç + yatay çubuk
    sl = slide(prs, "Yeni müşteri süreci", "Dört adım, ortalama 9 gün")
    grp = sl.shapes.add_group_shape()
    grp.name = "Süreç grubu"
    steps = [("01", "Başvuru"), ("02", "Değerlendirme"), ("03", "Teklif"), ("04", "Aktivasyon")]
    for i, (n, lbl) in enumerate(steps):
        x = 96 + i * 440
        b = grp.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(x), px(250), px(380), px(180))
        b.fill.solid(); b.fill.fore_color.rgb = CARD; b.line.color.rgb = SKY
        tf = b.text_frame
        tf.text = f"{n}\n{lbl}"
        for j, p in enumerate(tf.paragraphs):
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size, r.font.bold, r.font.name = pt(32 if j == 0 else 22), True, FONT
                r.font.color.rgb = CORAL if j == 0 else WHITE
        if i < 3:
            a = grp.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, px(x + 388), px(320), px(44), px(40))
            a.fill.solid(); a.fill.fore_color.rgb = CORAL; a.line.fill.background()
    chart(sl, XL_CHART_TYPE.BAR_CLUSTERED, 96, 500, 1100, 480, ["Aktivasyon", "Teklif", "Değerlendirme", "Başvuru"],
          [("Gün", (1.5, 2, 4, 1.5))], [MINT], legend=False)
    box(sl, 1290, 520, 534, 420, CARD)
    text(sl, 1330, 560, 460, 120, "9 gün", 64, CORAL, True)
    text(sl, 1330, 690, 460, 200, "Değerlendirme adımı sürenin yarısından fazlasını alıyor.", 22, WHITE)

    prs.save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("demo.pptx")))
