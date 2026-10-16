"""Cartoon props / icons. Each is drawn centred at (x, y); s=1 -> roughly 200px."""
import math

import skia

from .gfx import INK, circle, col, draw_text, fill, outlined, oval, poly, rrect, star_path, stroke


def _begin(c, x, y, s, rot=0):
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    c.scale(s, s)


def phone(c, t, screen="feed", **k):
    rrect(c, -58, -100, 116, 200, 22, fill("#2B2D42"))
    rrect(c, -58, -100, 116, 200, 22, stroke(INK, 7))
    scr = "#4CC9F0" if screen != "off" else "#11131F"
    rrect(c, -48, -84, 96, 160, 10, fill(scr))
    if screen == "feed":
        off = (t * 60) % 52
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(-48, -84, 96, 160))
        for i in range(-1, 5):
            yy = -84 + i * 52 - off
            rrect(c, -40, yy + 6, 80, 40, 6, fill("#FFFFFF", 230))
            circle(c, -28, yy + 18, 7, fill("#F72585"))
            rrect(c, -16, yy + 13, 46, 7, 3, fill("#B8C0FF"))
            rrect(c, -16, yy + 27, 30, 7, 3, fill("#B8C0FF"))
        c.restore()
        # notification badge
        circle(c, 46, -92, 18, fill("#F72585"))
        circle(c, 46, -92, 18, stroke(INK, 5))
        draw_text(c, "99", 46, -84, "Fredoka-Bold.ttf", 20)
    elif screen == "gray":
        rrect(c, -48, -84, 96, 160, 10, fill("#9A9A9A"))
        for i in range(3):
            for j in range(3):
                rrect(c, -38 + j * 28, -72 + i * 30, 20, 20, 5, fill("#6E6E6E"))
    rrect(c, -18, 82, 36, 6, 3, fill("#8D99AE"))


def clock(c, t, speed=1.0, **k):
    circle(c, 0, 0, 92, fill("#FFFFFF"))
    circle(c, 0, 0, 92, stroke(INK, 8))
    for i in range(12):
        a = math.radians(i * 30)
        circle(c, math.cos(a) * 72, math.sin(a) * 72, 5, fill(INK))
    m = t * speed * 6
    for (ang, L, w) in ((m / 12, 42, 10), (m, 64, 7)):
        a = math.radians(ang - 90)
        p = skia.Path()
        p.moveTo(0, 0)
        p.lineTo(math.cos(a) * L, math.sin(a) * L)
        c.drawPath(p, stroke(INK, w))
    circle(c, 0, 0, 9, fill("#E63946"))
    # bells
    for sx in (-1, 1):
        c.save()
        c.rotate(sx * 38)
        oval(c, 0, -104, 26, 16, fill("#E63946"))
        oval(c, 0, -104, 26, 16, stroke(INK, 6))
        c.restore()


def checklist(c, t, checked=3, items=3, **k):
    rrect(c, -80, -105, 160, 210, 14, fill("#FFFFFF"))
    rrect(c, -80, -105, 160, 210, 14, stroke(INK, 7))
    rrect(c, -34, -118, 68, 26, 8, fill("#8D99AE"))
    rrect(c, -34, -118, 68, 26, 8, stroke(INK, 5))
    for i in range(items):
        yy = -62 + i * 52
        rrect(c, -58, yy - 16, 32, 32, 7, fill("#FFFFFF"))
        rrect(c, -58, yy - 16, 32, 32, 7, stroke(INK, 5))
        rrect(c, -14, yy - 6, 70, 12, 6, fill("#CED4DA"))
        if i < checked:
            p = skia.Path()
            p.moveTo(-52, yy)
            p.lineTo(-42, yy + 10)
            p.lineTo(-22, yy - 16)
            c.drawPath(p, stroke("#2EC4B6", 9))


def trophy(c, t, **k):
    cup = skia.Path()
    cup.moveTo(-70, -90)
    cup.lineTo(70, -90)
    cup.quadTo(70, 10, 0, 30)
    cup.quadTo(-70, 10, -70, -90)
    cup.close()
    for sx in (-1, 1):
        h = skia.Path()
        h.addCircle(sx * 72, -50, 30)
        c.drawPath(h, stroke(INK, 18))
        c.drawPath(h, stroke("#FFD23F", 9))
    outlined(c, cup, "#FFD23F", 7)
    oval(c, -30, -55, 12, 26, fill("#FFFFFF", 140))
    rrect(c, -14, 26, 28, 40, 4, fill("#F4A62A"))
    rrect(c, -14, 26, 28, 40, 4, stroke(INK, 6))
    rrect(c, -50, 62, 100, 32, 8, fill("#8D5A3B"))
    rrect(c, -50, 62, 100, 32, 8, stroke(INK, 6))
    c.drawPath(star_path(0, -42, 24, 11), fill("#FFFFFF"))


def laptop(c, t, **k):
    rrect(c, -110, -90, 220, 140, 14, fill("#2B2D42"))
    rrect(c, -110, -90, 220, 140, 14, stroke(INK, 7))
    rrect(c, -96, -76, 192, 112, 6, fill("#E9F5FF"))
    for i in range(4):
        w = 120 - (i * 23) % 50
        rrect(c, -80, -62 + i * 24, w, 10, 5, fill("#4361EE" if i == 0 else "#ADB5BD"))
    blink = int(t * 2) % 2
    if blink:
        rrect(c, -80 + 60, -62 + 3 * 24, 4, 14, 1, fill(INK))
    body = poly([(-140, 52), (140, 52), (120, 82), (-120, 82)])
    outlined(c, body, "#8D99AE", 7)


def calendar(c, t, mark=True, **k):
    rrect(c, -95, -90, 190, 185, 16, fill("#FFFFFF"))
    rrect(c, -95, -90, 190, 50, 16, fill("#E63946"))
    c.drawRect(skia.Rect.MakeXYWH(-95, -60, 190, 20), fill("#E63946"))
    rrect(c, -95, -90, 190, 185, 16, stroke(INK, 7))
    for sx in (-50, 50):
        rrect(c, sx - 7, -108, 14, 34, 7, fill("#8D99AE"))
        rrect(c, sx - 7, -108, 14, 34, 7, stroke(INK, 4))
    n = 0
    for i in range(4):
        for j in range(5):
            cx, cy = -72 + j * 36, -22 + i * 30
            n += 1
            if mark and n <= int((t * 4) % 21):
                p = skia.Path()
                p.moveTo(cx - 10, cy - 8)
                p.lineTo(cx + 10, cy + 8)
                p.moveTo(cx + 10, cy - 8)
                p.lineTo(cx - 10, cy + 8)
                c.drawPath(p, stroke("#2EC4B6", 5))
            else:
                circle(c, cx, cy, 5, fill("#CED4DA"))


def tomato(c, t, **k):
    """Pomodoro kitchen timer."""
    circle(c, 0, 10, 92, fill("#EF476F"))
    oval(c, -34, -26, 22, 14, fill("#FFFFFF", 120))
    circle(c, 0, 10, 92, stroke(INK, 7))
    leaf = poly([(0, -78), (-40, -100), (-14, -84), (0, -112), (14, -84), (40, -100)])
    outlined(c, leaf, "#06D6A0", 6)
    circle(c, 0, 20, 52, fill("#FFFFFF"))
    circle(c, 0, 20, 52, stroke(INK, 5))
    a = math.radians(-90 + (t * 40) % 360)
    p = skia.Path()
    p.moveTo(0, 20)
    p.lineTo(math.cos(a) * 40, 20 + math.sin(a) * 40)
    c.drawPath(p, stroke(INK, 7))
    draw_text(c, "25", 0, 64, "Fredoka-Bold.ttf", 22, color=INK)


def mountain(c, t, **k):
    m = poly([(-140, 90), (-30, -80), (20, -10), (60, -60), (150, 90)])
    outlined(c, m, "#6C757D", 7)
    snow = poly([(-30, -80), (-58, -36), (-38, -42), (-24, -30), (-8, -46)])
    c.drawPath(snow, fill("#FFFFFF"))
    p = skia.Path()
    p.moveTo(-30, -80)
    p.lineTo(-30, -150)
    c.drawPath(p, stroke(INK, 7))
    wave = math.sin(t * 6) * 6
    flag = poly([(-30, -150), (30, -138 + wave), (-30, -112)])
    outlined(c, flag, "#E63946", 5)


def battery(c, t, level=0.2, **k):
    rrect(c, -110, -55, 205, 110, 18, fill("#FFFFFF"))
    rrect(c, -110, -55, 205, 110, 18, stroke(INK, 8))
    rrect(c, 95, -22, 22, 44, 6, fill(INK))
    lv = max(0.05, min(1, level))
    colr = "#2EC4B6" if lv > 0.5 else ("#FFD23F" if lv > 0.25 else "#EF476F")
    rrect(c, -96, -41, 177 * lv, 82, 10, fill(colr))
    if lv > 0.5:
        b = poly([(-2, -36), (-24, 6), (-4, 6), (-12, 40), (20, -8), (0, -8), (8, -36)])
        outlined(c, b, "#FFFFFF", 4)


def heart(c, t, **k):
    beat = 1 + 0.06 * max(0, math.sin(t * 7))
    c.save()
    c.scale(beat, beat)
    p = skia.Path()
    p.moveTo(0, 85)
    p.cubicTo(-150, -10, -80, -120, 0, -45)
    p.cubicTo(80, -120, 150, -10, 0, 85)
    p.close()
    outlined(c, p, "#EF476F", 8)
    oval(c, -50, -40, 18, 12, fill("#FFFFFF", 150))
    c.restore()


def book(c, t, **k):
    for i, colr in enumerate(("#4361EE", "#2EC4B6", "#FFD23F")):
        yy = 50 - i * 46
        rrect(c, -100 + i * 8, yy - 22, 190, 44, 8, fill(colr))
        rrect(c, -100 + i * 8, yy - 22, 190, 44, 8, stroke(INK, 6))
        c.drawRect(skia.Rect.MakeXYWH(60 + i * 8, yy - 14, 18, 28), fill("#FFFFFF"))


def pillow(c, t, **k):
    p = skia.Path()
    p.moveTo(-100, -60)
    p.quadTo(0, -40, 100, -60)
    p.quadTo(80, 0, 100, 60)
    p.quadTo(0, 40, -100, 60)
    p.quadTo(-80, 0, -100, -60)
    p.close()
    outlined(c, p, "#F1E9FF", 7)
    draw_text(c, "zZ", 0, 14, "LuckiestGuy.ttf", 44, color="#8E74D0")


def bulb(c, t, on=True, **k):
    if on:
        circle(c, 0, -20, 120, fill("#FFE45C", 70))
        for i in range(8):
            a = math.radians(i * 45 + t * 20)
            p = skia.Path()
            p.moveTo(math.cos(a) * 95, -20 + math.sin(a) * 95)
            p.lineTo(math.cos(a) * 125, -20 + math.sin(a) * 125)
            c.drawPath(p, stroke("#FFB703", 9))
    circle(c, 0, -20, 70, fill("#FFE45C" if on else "#E9ECEF"))
    circle(c, 0, -20, 70, stroke(INK, 7))
    rrect(c, -32, 46, 64, 50, 10, fill("#8D99AE"))
    rrect(c, -32, 46, 64, 50, 10, stroke(INK, 6))
    oval(c, -24, -44, 14, 22, fill("#FFFFFF", 160))


def brain(c, t, **k):
    pts = [(-60, -30, 50), (-20, -60, 50), (35, -55, 48), (65, -10, 45), (40, 35, 45), (-15, 40, 48), (-62, 20, 42)]
    path = None
    for (x, y, r) in pts:
        p = skia.Path()
        p.addCircle(x, y, r)
        path = p if path is None else skia.Op(path, p, skia.PathOp.kUnion_PathOp)
    outlined(c, path, "#FFAFCC", 7)
    for (a, b, cc) in (((-40, -50), (-10, -10), (-50, 10)), ((20, -60), (10, -20), (50, 0)), ((0, 10), (30, 40), (-10, 50))):
        p = skia.Path()
        p.moveTo(*a)
        p.quadTo(*b, *cc)
        c.drawPath(p, stroke("#E07A9B", 6))


def letter(c, t, **k):
    rrect(c, -110, -70, 220, 140, 12, fill("#FFFFFF"))
    rrect(c, -110, -70, 220, 140, 12, stroke(INK, 7))
    p = skia.Path()
    p.moveTo(-108, -66)
    p.lineTo(0, 10)
    p.lineTo(108, -66)
    c.drawPath(p, stroke(INK, 6))
    heartp = skia.Path()
    heartp.moveTo(0, 30)
    heartp.cubicTo(-40, 5, -20, -25, 0, -6)
    heartp.cubicTo(20, -25, 40, 5, 0, 30)
    outlined(c, heartp, "#EF476F", 4)


def target(c, t, **k):
    for i, colr in enumerate(("#EF476F", "#FFFFFF", "#EF476F", "#FFFFFF", "#EF476F")):
        r = 100 - i * 20
        circle(c, 0, 0, r, fill(colr))
        circle(c, 0, 0, r, stroke(INK, 5))
    p = skia.Path()
    p.moveTo(0, 0)
    p.lineTo(110, -90)
    c.drawPath(p, stroke(INK, 9))
    fl = poly([(110, -90), (130, -120), (140, -86), (124, -78)])
    outlined(c, fl, "#4361EE", 4)


def frog(c, t, **k):
    oval(c, 0, 20, 100, 72, fill("#06D6A0"))
    oval(c, 0, 20, 100, 72, stroke(INK, 7))
    for sx in (-1, 1):
        circle(c, sx * 45, -45, 30, fill("#06D6A0"))
        circle(c, sx * 45, -45, 30, stroke(INK, 6))
        circle(c, sx * 45, -45, 17, fill("#FFFFFF"))
        circle(c, sx * 45 + 3, -43, 9, fill(INK))
    p = skia.Path()
    p.moveTo(-50, 20)
    p.quadTo(0, 60, 50, 20)
    c.drawPath(p, stroke(INK, 7))
    circle(c, -60, 10, 10, fill("#FF8FA3", 140))
    circle(c, 60, 10, 10, fill("#FF8FA3", 140))


def coffee(c, t, **k):
    for i in range(3):
        ph = (t * 0.8 + i / 3) % 1
        p = skia.Path()
        x0 = -30 + i * 30
        p.moveTo(x0, -60)
        p.quadTo(x0 + 18 * math.sin(ph * 6), -90, x0, -120)
        c.drawPath(p, stroke("#FFFFFF", 7, a=int(200 * (1 - ph))))
    h = skia.Path()
    h.addCircle(78, 10, 32)
    c.drawPath(h, stroke(INK, 18))
    c.drawPath(h, stroke("#FFFFFF", 9))
    cup = poly([(-75, -50), (75, -50), (60, 80), (-60, 80)])
    outlined(c, cup, "#FFFFFF", 7)
    rrect(c, -64, -8, 128, 34, 4, fill("#E63946"))
    c.drawRect(skia.Rect.MakeXYWH(-70, -50, 140, 14), fill("#6F4E37"))
    c.drawPath(cup, stroke(INK, 7))


def stairs(c, t, **k):
    for i in range(5):
        x0 = -130 + i * 52
        h = 40 + i * 40
        rrect(c, x0, 90 - h, 52, h, 4, fill("#4361EE" if i % 2 else "#4CC9F0"))
        rrect(c, x0, 90 - h, 52, h, 4, stroke(INK, 6))
    c.drawPath(star_path(118, -128, 26, 12), fill("#FFD23F"))
    c.drawPath(star_path(118, -128, 26, 12), stroke(INK, 4))


def shield(c, t, **k):
    p = skia.Path()
    p.moveTo(0, -110)
    p.quadTo(60, -80, 95, -85)
    p.quadTo(100, 40, 0, 110)
    p.quadTo(-100, 40, -95, -85)
    p.quadTo(-60, -80, 0, -110)
    p.close()
    outlined(c, p, "#4361EE", 8)
    b = poly([(-6, -60), (-34, 10), (-6, 10), (-16, 70), (30, -6), (4, -6), (16, -60)])
    outlined(c, b, "#FFD23F", 5)


def mirror(c, t, **k):
    oval(c, 0, -10, 80, 105, fill("#CDEFFF"))
    oval(c, 0, -10, 80, 105, stroke("#C9A227", 16))
    oval(c, 0, -10, 80, 105, stroke(INK, 5))
    p = skia.Path()
    p.moveTo(-40, -70)
    p.lineTo(10, -100)
    p.moveTo(-50, -30)
    p.lineTo(30, -80)
    c.drawPath(p, stroke("#FFFFFF", 8))
    rrect(c, -12, 92, 24, 40, 6, fill("#C9A227"))
    rrect(c, -12, 92, 24, 40, 6, stroke(INK, 5))


def sofa(c, t, **k):
    rrect(c, -170, -70, 340, 110, 30, fill("#4361EE"))
    rrect(c, -170, -70, 340, 110, 30, stroke(INK, 7))
    rrect(c, -200, -20, 60, 110, 24, fill("#3A56D4"))
    rrect(c, -200, -20, 60, 110, 24, stroke(INK, 7))
    rrect(c, 140, -20, 60, 110, 24, fill("#3A56D4"))
    rrect(c, 140, -20, 60, 110, 24, stroke(INK, 7))
    rrect(c, -150, 10, 300, 70, 18, fill("#4CC9F0"))
    rrect(c, -150, 10, 300, 70, 18, stroke(INK, 7))
    for sx in (-170, 160):
        rrect(c, sx, 88, 14, 26, 4, fill(INK))


def dumbbell(c, t, **k):
    rrect(c, -90, -10, 180, 20, 8, fill("#8D99AE"))
    rrect(c, -90, -10, 180, 20, 8, stroke(INK, 5))
    for sx in (-1, 1):
        rrect(c, sx * 80 - 22, -55, 44, 110, 12, fill("#2B2D42"))
        rrect(c, sx * 80 - 22, -55, 44, 110, 12, stroke(INK, 5))


def gift(c, t, **k):
    rrect(c, -85, -40, 170, 130, 10, fill("#F72585"))
    rrect(c, -85, -40, 170, 130, 10, stroke(INK, 7))
    rrect(c, -95, -70, 190, 40, 10, fill("#FF4D9D"))
    rrect(c, -95, -70, 190, 40, 10, stroke(INK, 7))
    c.drawRect(skia.Rect.MakeXYWH(-14, -70, 28, 160), fill("#FFD23F"))
    for sx in (-1, 1):
        oval(c, sx * 30, -88, 30, 18, fill("#FFD23F"))
        oval(c, sx * 30, -88, 30, 18, stroke(INK, 5))


def bed(c, t, **k):
    rrect(c, -200, -20, 400, 90, 16, fill("#FFFFFF"))
    rrect(c, -200, -20, 400, 90, 16, stroke(INK, 7))
    rrect(c, -230, -110, 40, 220, 12, fill("#8D5A3B"))
    rrect(c, -230, -110, 40, 220, 12, stroke(INK, 7))
    rrect(c, 190, -40, 40, 150, 12, fill("#8D5A3B"))
    rrect(c, 190, -40, 40, 150, 12, stroke(INK, 7))
    rrect(c, -40, -40, 230, 100, 20, fill("#4CC9F0"))
    rrect(c, -40, -40, 230, 100, 20, stroke(INK, 7))


def fire(c, t, **k):
    w = math.sin(t * 9) * 8
    p = skia.Path()
    p.moveTo(0, 90)
    p.cubicTo(-110, 80, -80, -20, -30 + w, -60)
    p.cubicTo(-30, -20, 0, -10, 10, -110 - w)
    p.cubicTo(70, -40, 120, 60, 0, 90)
    p.close()
    outlined(c, p, "#FF7B00", 7)
    q = skia.Path()
    q.moveTo(0, 82)
    q.cubicTo(-60, 70, -40, 0, -6 - w, -20)
    q.cubicTo(10, 10, 40, 0, 30, -40 + w)
    q.cubicTo(70, 30, 50, 80, 0, 82)
    c.drawPath(q, fill("#FFD23F"))


def sword(c, t, **k):
    blade = poly([(-10, 40), (-10, -120), (0, -145), (10, -120), (10, 40)])
    outlined(c, blade, "#E9ECEF", 6)
    rrect(c, -50, 36, 100, 18, 8, fill("#FFD23F"))
    rrect(c, -50, 36, 100, 18, 8, stroke(INK, 5))
    rrect(c, -10, 54, 20, 60, 6, fill("#8D5A3B"))
    rrect(c, -10, 54, 20, 60, 6, stroke(INK, 5))


def magnet(c, t, **k):
    p = skia.Path()
    p.addArc(skia.Rect.MakeLTRB(-80, -80, 80, 80), 180, 180)
    c.drawPath(p, stroke(INK, 54, cap="butt"))
    c.drawPath(p, stroke("#E63946", 40, cap="butt"))
    for sx in (-1, 1):
        rrect(c, sx * 80 - 27, 0, 54, 70, 4, fill("#E63946"))
        rrect(c, sx * 80 - 27, 50, 54, 30, 4, fill("#E9ECEF"))
        rrect(c, sx * 80 - 27, 0, 54, 80, 4, stroke(INK, 6))


def chart(c, t, **k):
    rrect(c, -120, -100, 240, 200, 16, fill("#FFFFFF"))
    rrect(c, -120, -100, 240, 200, 16, stroke(INK, 7))
    pts = [(-90, 60), (-50, 40), (-10, 45), (30, 0), (60, 10), (95, -60)]
    p = skia.Path()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p, stroke("#2EC4B6", 10))
    arr = poly([(95, -60), (70, -55), (92, -35)])
    outlined(c, arr, "#2EC4B6", 4)


def lock(c, t, **k):
    p = skia.Path()
    p.addArc(skia.Rect.MakeLTRB(-50, -100, 50, 0), 180, 180)
    p.lineTo(50, -30)
    p.moveTo(-50, -50)
    p.lineTo(-50, -30)
    c.drawPath(p, stroke(INK, 26))
    c.drawPath(p, stroke("#8D99AE", 14))
    rrect(c, -80, -30, 160, 120, 18, fill("#FFD23F"))
    rrect(c, -80, -30, 160, 120, 18, stroke(INK, 7))
    circle(c, 0, 20, 14, fill(INK))
    rrect(c, -6, 20, 12, 36, 4, fill(INK))


def moon(c, t, **k):
    p = skia.Path()
    p.addCircle(0, 0, 90)
    q = skia.Path()
    q.addCircle(45, -30, 80)
    m = skia.Op(p, q, skia.PathOp.kDifference_PathOp)
    outlined(c, m, "#FFE45C", 7)
    draw_text(c, "Z", 60, 40, "LuckiestGuy.ttf", 60, color="#FFFFFF", outline=INK, ow=7)


def plant(c, t, grow=1.0, **k):
    pot = poly([(-60, 40), (60, 40), (45, 120), (-45, 120)])
    outlined(c, pot, "#E07A5F", 7)
    h = 40 + 110 * grow
    p = skia.Path()
    p.moveTo(0, 40)
    p.quadTo(10, 40 - h / 2, 0, 40 - h)
    c.drawPath(p, stroke(INK, 14))
    c.drawPath(p, stroke("#06D6A0", 7))
    for i in range(int(1 + grow * 3)):
        yy = 20 - i * 34
        sx = -1 if i % 2 else 1
        leaf = skia.Path()
        leaf.moveTo(0, yy)
        leaf.quadTo(sx * 40, yy - 40, sx * 70, yy - 16)
        leaf.quadTo(sx * 40, yy + 4, 0, yy)
        outlined(c, leaf, "#06D6A0", 5)


def door(c, t, **k):
    rrect(c, -70, -120, 140, 240, 10, fill("#8D5A3B"))
    rrect(c, -70, -120, 140, 240, 10, stroke(INK, 7))
    rrect(c, -50, -100, 100, 80, 6, stroke("#6B4226", 6))
    rrect(c, -50, 0, 100, 100, 6, stroke("#6B4226", 6))
    circle(c, 45, 10, 10, fill("#FFD23F"))
    circle(c, 45, 10, 10, stroke(INK, 4))


_PROPS = {k: v for k, v in globals().items() if callable(v) and not k.startswith("_") and k not in (
    "col", "fill", "stroke", "circle", "oval", "poly", "rrect", "outlined", "draw_text", "star_path")}


def draw(c, name, x, y, s=1.0, t=0.0, rot=0, **kw):
    fn = _PROPS.get(name)
    if fn is None:
        return
    _begin(c, x, y, s, rot)
    fn(c, t, **kw)
    c.restore()


def names():
    return sorted(_PROPS)
