"""Flat, minimal props. Every prop is drawn with its bottom-centre at (x, y) unless noted."""
import math
import random

import skia

from engine.gfx import blurred, circle, col, draw_text, fill, oval, poly, rrect, stroke

LINE = "#AEB3BF"
DARK = "#24262E"


def _b(c, x, y, s, rot=0):
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(s, s)


def pizza_box(c, t=0, open_=True, **k):
    rrect(c, -100, -26, 200, 26, 6, fill("#C9A77C"))
    if open_:
        c.drawPath(poly([(-100, -26), (100, -26), (92, -170), (-92, -170)]), fill("#D8B98E"))
        rrect(c, -80, -150, 160, 110, 10, fill("#C9A77C", 120))
        oval(c, 0, -26, 86, 18, fill("#E9B44C"))
        oval(c, 0, -27, 76, 14, fill("#F4D27A"))
        for (px, py) in ((-40, -28), (10, -32), (40, -24), (-10, -22)):
            oval(c, px, py, 9, 4, fill("#C8423B"))
        c.drawLine(-60, -36, 60, -18, stroke("#C49A4F", 2))
    else:
        rrect(c, -100, -46, 200, 46, 8, fill("#D8B98E"))
        rrect(c, -46, -36, 92, 26, 13, fill("#C8423B"))
        draw_text(c, "PIZZA", 0, -16, "Inter-ExtraBold.otf", 18, color="#F5E9D6")


def can(c, t=0, color="#2FBF71", **k):
    rrect(c, -18, -62, 36, 62, 6, fill(color))
    c.drawRect(skia.Rect.MakeXYWH(-18, -62, 36, 8), fill("#C8CCD4"))
    c.drawRect(skia.Rect.MakeXYWH(-18, -8, 36, 8), fill("#C8CCD4"))
    c.drawPath(poly([(2, -50), (-8, -30), (0, -30), (-4, -14), (8, -36), (0, -36), (4, -50)]), fill("#F5F3EA"))


def cans(c, t=0, rows=4, **k):
    colors = ["#2FBF71", "#3A86FF", "#2FBF71", "#E63946"]
    for r in range(rows):
        n = rows - r
        for i in range(n):
            x = (i - (n - 1) / 2) * 40
            c.save()
            c.translate(x, -r * 62)
            can(c, t, colors[(i + r) % 4])
            c.restore()


def candy(c, t=0, **k):
    rnd = random.Random(4)
    colors = ["#F72585", "#FFD60A", "#3A86FF", "#06D6A0", "#FB5607", "#8338EC"]
    for i in range(26):
        x = rnd.uniform(-120, 120)
        y = -abs(rnd.gauss(0, 1)) * 30 - (1 - abs(x) / 130) * 50
        cc = rnd.choice(colors)
        oval(c, x, y, 14, 9, fill(cc))
        c.drawPath(poly([(x - 14, y), (x - 22, y - 7), (x - 22, y + 7)]), fill(cc))
        c.drawPath(poly([(x + 14, y), (x + 22, y - 7), (x + 22, y + 7)]), fill(cc))


def chips(c, t=0, **k):
    p = skia.Path()
    p.moveTo(-40, 0)
    p.lineTo(-46, -100)
    p.lineTo(46, -100)
    p.lineTo(40, 0)
    p.close()
    c.drawPath(p, fill("#E63946"))
    c.drawRect(skia.Rect.MakeXYWH(-46, -104, 92, 10), fill("#B71C2C"))
    oval(c, 0, -52, 22, 18, fill("#FFD166"))


def gaming_chair(c, t=0, **k):
    rrect(c, -60, -250, 120, 170, 30, fill("#2E2A3E"))
    rrect(c, -40, -230, 80, 120, 20, fill("#3A3550"))
    rrect(c, -80, -100, 160, 34, 14, fill("#2E2A3E"))
    c.drawRect(skia.Rect.MakeXYWH(-8, -66, 16, 46), fill("#1C1A26"))
    c.drawLine(-60, -12, 60, -12, stroke("#1C1A26", 10))
    for wx in (-56, 0, 56):
        circle(c, wx, -5, 7, fill("#111017"))
    circle(c, 0, -5, 4, fill("#E63946"))


def desk(c, t=0, w=420, **k):
    rrect(c, -w / 2, -150, w, 18, 4, fill("#3B3F4C"))
    c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 16, -132, 14, 132), fill("#2B2E38"))
    c.drawRect(skia.Rect.MakeXYWH(w / 2 - 30, -132, 14, 132), fill("#2B2E38"))


def laptop(c, t=0, glow=1.0, screen="#4CC9F0", **k):
    """Bottom-centre on the desk surface."""
    if glow > 0:
        c.drawPath(poly([(-60, -70), (60, -70), (260, 120), (-260, 120)]), blurred(screen, 40, int(45 * glow)))
    c.save()
    c.skew(-0.15, 0)
    rrect(c, -64, -92, 128, 86, 6, fill("#2B2E38"))
    rrect(c, -58, -86, 116, 74, 4, fill(screen if glow > 0 else "#15171C"))
    if glow > 0:
        for i in range(4):
            c.drawRect(skia.Rect.MakeXYWH(-48, -78 + i * 15, 70 - (i * 17) % 40, 6), fill("#FFFFFF", 110))
    c.restore()
    rrect(c, -84, -8, 168, 8, 3, fill("#3F4352"))


def phone(c, t=0, glow=1.0, **k):
    """Centred."""
    if glow > 0:
        circle(c, 0, 0, 90, blurred("#4CC9F0", 35, int(80 * glow)))
    rrect(c, -16, -30, 32, 60, 6, fill("#111217"))
    if glow > 0:
        rrect(c, -13, -26, 26, 52, 4, fill("#7FD8F5"))
        off = (t * 40) % 16
        for i in range(4):
            c.drawRect(skia.Rect.MakeXYWH(-10, -24 + i * 16 - off + 8, 20, 9), fill("#FFFFFF", 160))


def bed(c, t=0, **k):
    rrect(c, -230, -90, 460, 70, 12, fill("#2E3240"))
    rrect(c, -230, -110, 460, 34, 14, fill("#4A5068"))
    rrect(c, 140, -140, 80, 36, 14, fill("#C9CCD6"))
    c.drawRect(skia.Rect.MakeXYWH(-244, -180, 22, 180), fill("#2B2E38"))
    c.drawRect(skia.Rect.MakeXYWH(222, -120, 22, 120), fill("#2B2E38"))


def couch(c, t=0, **k):
    rrect(c, -240, -170, 480, 110, 26, fill("#3B3550"))
    rrect(c, -220, -90, 440, 60, 18, fill("#4A4466"))
    rrect(c, -270, -120, 60, 110, 22, fill("#332E46"))
    rrect(c, 210, -120, 60, 110, 22, fill("#332E46"))
    for x in (-230, 220):
        c.drawRect(skia.Rect.MakeXYWH(x, -12, 10, 12), fill("#1C1A26"))


def tv(c, t=0, glow=1.0, **k):
    if glow:
        circle(c, 0, -170, 220, blurred("#5E60CE", 70, int(60 * glow)))
    rrect(c, -150, -260, 300, 180, 8, fill("#111217"))
    rrect(c, -140, -250, 280, 160, 4, fill("#5E60CE" if glow else "#15171C"))
    c.drawRect(skia.Rect.MakeXYWH(-10, -80, 20, 40), fill("#2B2E38"))
    rrect(c, -90, -44, 180, 44, 6, fill("#2B2E38"))


def wall_clock(c, t=0, speed=1.0, **k):
    """Centred."""
    circle(c, 0, 0, 62, fill("#1A1C22"))
    circle(c, 0, 0, 62, stroke(LINE, 3))
    for i in range(12):
        a = math.radians(i * 30)
        c.drawLine(math.cos(a) * 50, math.sin(a) * 50, math.cos(a) * 56, math.sin(a) * 56, stroke(LINE, 3))
    m = t * speed * 360 / 60
    for (ang, L, w, cc) in ((m / 12, 30, 5, LINE), (m, 46, 3, LINE)):
        a = math.radians(ang - 90)
        c.drawLine(0, 0, math.cos(a) * L, math.sin(a) * L, stroke(cc, w))
    circle(c, 0, 0, 5, fill("#E63946"))


def alarm(c, t=0, ring=0.0, **k):
    """Centred."""
    sh = math.sin(t * 60) * 6 * ring
    c.save()
    c.rotate(sh)
    for sx in (-1, 1):
        circle(c, sx * 26, -38, 14, fill("#C8CCD4"))
    circle(c, 0, 0, 44, fill("#E63946"))
    circle(c, 0, 0, 34, fill("#F5F3EA"))
    c.drawLine(0, 0, 0, -22, stroke(DARK, 4))
    c.drawLine(0, 0, 14, 4, stroke(DARK, 4))
    c.restore()
    if ring > 0:
        for sx in (-1, 1):
            for r in (60, 78):
                p = skia.Path()
                p.addArc(skia.Rect.MakeXYWH(-r, -r, 2 * r, 2 * r), -40 if sx > 0 else 140, 80)
                c.drawPath(p, stroke("#F5F3EA", 4, a=int(200 * ring)))


def barbell(c, t=0, w=380, **k):
    """Centred (held)."""
    c.drawLine(-w / 2, 0, w / 2, 0, stroke("#9AA0AC", 9))
    for sx in (-1, 1):
        for i, (pw, ph) in enumerate(((18, 120), (14, 92))):
            x = sx * (w / 2 - 40 + i * 24 * (1 if sx > 0 else -1))
            rrect(c, x - pw / 2, -ph / 2, pw, ph, 5, fill("#2B2E38"))
            rrect(c, x - pw / 2, -ph / 2, pw, ph, 5, stroke("#5C6170", 2))
        c.drawRect(skia.Rect.MakeXYWH(sx * (w / 2 - 70) - 5, -10, 10, 20), fill("#C8CCD4"))


def rack(c, t=0, **k):
    for sx in (-1, 1):
        c.drawRect(skia.Rect.MakeXYWH(sx * 210 - 7, -470, 14, 470), fill("#3B3F4C"))
        c.drawRect(skia.Rect.MakeXYWH(sx * 210 - 26, -300, 30 if sx < 0 else 30, 10), fill("#5C6170"))
    c.drawRect(skia.Rect.MakeXYWH(-230, -478, 460, 14), fill("#3B3F4C"))


def bench(c, t=0, **k):
    rrect(c, -150, -86, 300, 26, 10, fill("#2B2E38"))
    c.drawRect(skia.Rect.MakeXYWH(-110, -60, 14, 60), fill("#3B3F4C"))
    c.drawRect(skia.Rect.MakeXYWH(96, -60, 14, 60), fill("#3B3F4C"))


def plate(c, t=0, r=56, **k):
    """Centred."""
    circle(c, 0, 0, r, fill("#1C1E25"))
    circle(c, 0, 0, r, stroke("#5C6170", 3))
    circle(c, 0, 0, r * 0.55, stroke("#3B3F4C", 3))
    circle(c, 0, 0, 8, fill("#9AA0AC"))


def dumbbell(c, t=0, **k):
    """Centred."""
    c.drawLine(-36, 0, 36, 0, stroke("#9AA0AC", 8))
    for sx in (-1, 1):
        c.drawPath(poly([(sx * 30, -24), (sx * 52, -24), (sx * 60, 0), (sx * 52, 24), (sx * 30, 24), (sx * 24, 0)]), fill("#2B2E38"))


def gym_bag(c, t=0, **k):
    rrect(c, -70, -56, 140, 56, 22, fill("#274C77"))
    p = skia.Path()
    p.addArc(skia.Rect.MakeXYWH(-36, -86, 72, 64), 180, 180)
    c.drawPath(p, stroke("#1B3557", 7))
    c.drawLine(-60, -30, 60, -30, stroke("#1B3557", 3))


def books(c, t=0, **k):
    for i, (w, cc) in enumerate(((150, "#8D5A3B"), (130, "#3A5A80"), (160, "#5E4B6E"))):
        rrect(c, -w / 2 + i * 6, -(i + 1) * 26, w, 24, 3, fill(cc))
        c.drawRect(skia.Rect.MakeXYWH(w / 2 - 22 + i * 6, -(i + 1) * 26 + 4, 14, 16), fill("#E9E3D1", 200))


def notebook(c, t=0, ticks=3, **k):
    """Centred."""
    rrect(c, -70, -90, 140, 180, 8, fill("#E9E3D1"))
    for i in range(5):
        y = -60 + i * 30
        c.drawRect(skia.Rect.MakeXYWH(-50, y - 8, 16, 16), stroke("#3B3F4C", 3))
        c.drawLine(-24, y, 50, y, stroke("#B5AE9C", 4))
        if i < ticks:
            p = skia.Path()
            p.moveTo(-50, y - 2)
            p.lineTo(-43, y + 6)
            p.lineTo(-30, y - 12)
            c.drawPath(p, stroke("#2FBF71", 5))


def bills(c, t=0, **k):
    rnd = random.Random(2)
    for i in range(7):
        c.save()
        c.translate(rnd.uniform(-60, 60), -i * 8)
        c.rotate(rnd.uniform(-14, 14))
        rrect(c, -55, -36, 110, 72, 3, fill("#E9E3D1" if i % 2 else "#D9D2BE"))
        c.drawLine(-40, -16, 30, -16, stroke("#B5AE9C", 4))
        c.drawLine(-40, 0, 20, 0, stroke("#B5AE9C", 4))
        draw_text(c, "DUE", 30, 26, "Inter-ExtraBold.otf", 18, color="#E63946")
        c.restore()


def calendar(c, t=0, marks=0, **k):
    """Centred."""
    rrect(c, -80, -80, 160, 160, 8, fill("#E9E3D1"))
    c.drawRect(skia.Rect.MakeXYWH(-80, -80, 160, 34), fill("#C8423B"))
    for i in range(4):
        for j in range(5):
            cx, cy = -60 + j * 30, -26 + i * 28
            if i * 5 + j < marks:
                c.drawLine(cx - 8, cy - 8, cx + 8, cy + 8, stroke("#2FBF71", 4))
                c.drawLine(cx + 8, cy - 8, cx - 8, cy + 8, stroke("#2FBF71", 4))
            else:
                circle(c, cx, cy, 3, fill("#B5AE9C"))


def mug(c, t=0, **k):
    rrect(c, -26, -56, 52, 56, 8, fill("#E9E3D1"))
    p = skia.Path()
    p.addCircle(32, -30, 14)
    c.drawPath(p, stroke("#E9E3D1", 7))
    for i in range(2):
        ph = (t * 0.6 + i * 0.5) % 1
        oval(c, -6 + i * 12, -70 - ph * 50, 6 + ph * 6, 10, blurred("#E9E3D1", 4, int(120 * (1 - ph))))


def door(c, t=0, open_=0.0, **k):
    c.drawRect(skia.Rect.MakeXYWH(-80, -330, 160, 330), fill("#0E0F13"))
    if open_ > 0:
        c.drawRect(skia.Rect.MakeXYWH(-80, -330, 160, 330), blurred("#FFE8A3", 30, int(200 * open_)))
    w = 160 * (1 - open_ * 0.8)
    c.drawRect(skia.Rect.MakeXYWH(-80, -330, w, 330), fill("#3B3F4C"))
    circle(c, -80 + w - 18, -160, 6, fill("#C8CCD4"))


def mirror(c, t=0, **k):
    rrect(c, -70, -300, 140, 220, 70, fill("#2B3242"))
    rrect(c, -70, -300, 140, 220, 70, stroke(LINE, 4))
    c.drawLine(-30, -250, 10, -280, stroke("#FFFFFF", 4, a=80))


def trophy(c, t=0, **k):
    c.drawPath(poly([(-50, -150), (50, -150), (30, -80), (-30, -80)]), fill("#FFD166"))
    c.drawRect(skia.Rect.MakeXYWH(-8, -80, 16, 40), fill("#E9B44C"))
    rrect(c, -40, -40, 80, 40, 6, fill("#3B3F4C"))


def flag(c, t=0, color="#E9E3D1", **k):
    c.drawLine(0, 0, 0, -220, stroke("#C8CCD4", 6))
    wv = math.sin(t * 5) * 8
    c.drawPath(poly([(0, -220), (100, -200 + wv), (0, -170)]), fill(color))


def lamp(c, t=0, on=1.0, **k):
    c.drawLine(0, 0, 0, -160, stroke("#3B3F4C", 6))
    c.drawPath(poly([(-40, -150), (40, -150), (24, -200), (-24, -200)]), fill("#5C6170"))
    if on:
        c.drawPath(poly([(-40, -150), (40, -150), (160, 0), (-160, 0)]), blurred("#FFE8A3", 30, int(50 * on)))


def plant(c, t=0, **k):
    c.drawPath(poly([(-30, 0), (30, 0), (38, -50), (-38, -50)]), fill("#5C4033"))
    for i, a in enumerate((-40, -15, 10, 35, 60)):
        r = math.radians(a - 90)
        x1, y1 = math.cos(r) * 90, -50 + math.sin(r) * 90
        c.drawLine(0, -50, x1, y1, stroke("#2D6A4F", 12))


def shoes(c, t=0, **k):
    for x in (-34, 34):
        oval(c, x, -14, 30, 14, fill("#E9E3D1"))
        c.drawRect(skia.Rect.MakeXYWH(x - 30, -6, 60, 6), fill("#3B3F4C"))


def headphones(c, t=0, **k):
    p = skia.Path()
    p.addArc(skia.Rect.MakeXYWH(-40, -40, 80, 80), 180, 180)
    c.drawPath(p, stroke("#2B2E38", 9))
    for sx in (-1, 1):
        rrect(c, sx * 40 - 10, -10, 20, 34, 8, fill("#2B2E38"))


def weight_scale(c, t=0, **k):
    rrect(c, -70, -18, 140, 18, 6, fill("#C8CCD4"))


_REG = {k: v for k, v in globals().items() if callable(v) and not k.startswith("_") and k not in (
    "blurred", "circle", "col", "draw_text", "fill", "oval", "poly", "rrect", "stroke")}


def draw(c, name, x, y, s=1.0, t=0.0, rot=0, **kw):
    fn = _REG[name]
    _b(c, x, y, s, rot)
    fn(c, t, **kw)
    c.restore()


def names():
    return sorted(_REG)
