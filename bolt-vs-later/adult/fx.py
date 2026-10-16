"""Dark cinematic environments and effects. Static layers are cached as images for speed."""
import math
import random
from functools import lru_cache

import numpy as np
import skia

from engine.gfx import blurred, circle, col, draw_text, fill, mix, oval, poly, rrect, stroke, text_width

W, H = 1920, 1080
GROUND = 900          # ground line in world coords for most scenes
BAR = 64              # letterbox bar height


def _surface():
    return skia.Surface(W, H)


def _grad_v(c, y0, y1, colors, pos=None, x0=0, w=W):
    p = fill("#000000")
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [col(cc) for cc in colors], pos))
    c.drawRect(skia.Rect.MakeXYWH(x0, y0, w, y1 - y0), p)


# ----------------------------------------------------------------------------- cached backdrops
# Flat, minimal and dark: charcoal walls, thin light-grey line work, tiny warm windows, red horizon glow.

LINE = "#AEB3BF"


def _radial(c, cx, cy, r, inner, outer):
    p = fill("#000000")
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, [col(inner), col(outer)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def _stars(c, n, seed, ymax=700):
    rnd = random.Random(seed)
    for i in range(n):
        circle(c, rnd.uniform(0, W), rnd.uniform(BAR, ymax), rnd.uniform(0.8, 2.0), fill("#FFFFFF", rnd.randint(60, 200)))


def skyline(c, base_y, color, seed=1, lit=0.12, tall=1.0):
    rnd = random.Random(seed)
    x = -30
    while x < W + 30:
        bw = rnd.randint(60, 150)
        bh = rnd.randint(60, 230) * tall
        top = base_y - bh
        c.drawRect(skia.Rect.MakeXYWH(x, top, bw, base_y - top + 400), fill(color))
        for wy in range(int(top) + 12, int(base_y) - 6, 22):
            for wx in range(int(x) + 8, int(x + bw) - 10, 18):
                if rnd.random() < lit:
                    c.drawRect(skia.Rect.MakeXYWH(wx, wy, 8, 9), fill("#F2D492", rnd.randint(120, 230)))
        x += bw + rnd.randint(2, 18)


@lru_cache(maxsize=None)
def room(variant="night", seed=2, window=True, wall="#1C1E24"):
    s = _surface()
    c = s.getCanvas()
    _radial(c, W * 0.5, H * 0.45, 1100, mix(wall, "#FFFFFF", 0.05), mix(wall, "#000000", 0.35))
    c.drawRect(skia.Rect.MakeXYWH(0, GROUND, W, H - GROUND), fill(mix(wall, "#000000", 0.35)))
    c.drawLine(0, GROUND, W, GROUND, stroke("#2C2F38", 3))
    if window:
        wx, wy, ww, wh = 110, 170, 250, 290
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
        c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), fill("#0B0D14"))
        rnd = random.Random(seed)
        for i in range(30):
            circle(c, wx + rnd.uniform(0, ww), wy + rnd.uniform(0, wh), rnd.uniform(0.8, 1.8), fill("#FFFFFF", rnd.randint(80, 200)))
        circle(c, wx + 200, wy + 70, 14, fill("#F5F3EA"))
        circle(c, wx + 200, wy + 70, 30, blurred("#F5F3EA", 14, 60))
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), stroke(LINE, 4))
        c.drawLine(wx + ww / 2, wy, wx + ww / 2, wy + wh, stroke(LINE, 4))
        c.drawLine(wx, wy + wh / 2, wx + ww, wy + wh / 2, stroke(LINE, 4))
        # snow piled on the sill
        c.drawPath(poly([(wx + 6, wy + wh - 4), (wx + 120, wy + wh - 70), (wx + 190, wy + wh - 60), (wx + ww - 6, wy + wh - 4)]), fill("#E8ECF2"))
        rrect(c, wx - 20, wy + wh, ww + 40, 14, 4, fill("#2C2F38"))
    return s.makeImageSnapshot()


@lru_cache(maxsize=None)
def gym(seed=3):
    s = _surface()
    c = s.getCanvas()
    _radial(c, W * 0.5, H * 0.5, 1100, "#1D2026", "#0D0E12")
    for x in range(0, W, 96):
        c.drawLine(x, 0, x, H, stroke("#262931", 1.5))
    for y in range(0, H, 96):
        c.drawLine(0, y, W, y, stroke("#262931", 1.5))
    c.drawRect(skia.Rect.MakeXYWH(0, GROUND, W, H - GROUND), fill("#0B0C10", 200))
    c.drawLine(0, GROUND, W, GROUND, stroke("#30343E", 3))
    return s.makeImageSnapshot()


@lru_cache(maxsize=None)
def hill(seed=4, dawn=0.0, slope=True):
    """Night slope with the city behind; the hill line rises left to right."""
    s = _surface()
    c = s.getCanvas()
    top = mix("#0A0B10", "#2A1E3A", dawn)
    low = mix("#1A0E12", "#F4A261", dawn)
    _grad_v(c, 0, H, [top, mix(top, low, 0.4), low], [0, 0.6, 1])
    if dawn > 0.2:
        circle(c, 1500, 760, 240, blurred("#FFD166", 90, int(200 * dawn)))
        circle(c, 1500, 780, 90, fill("#FFE8A3", int(255 * min(1, dawn * 1.4))))
    else:
        c.drawRect(skia.Rect.MakeXYWH(0, 640, W, 300), blurred("#7A1E25", 80, 120))
    _stars(c, int(140 * (1 - dawn)), seed)
    skyline(c, 860, mix("#0C0D12", "#3A2A3A", dawn), seed, lit=0.10 * (1 - dawn))
    hp = hill_path(slope)
    c.drawPath(hp, fill(mix("#101116", "#2A2026", dawn)))
    c.drawPath(hp, stroke("#E8ECF2", 3, a=200))
    return s.makeImageSnapshot()


def hill_y(x, slope=True):
    if not slope:
        return GROUND
    u = x / W
    return 1010 - 330 * (u ** 1.4) - 40 * math.sin(u * 3.1)


def hill_path(slope=True):
    p = skia.Path()
    p.moveTo(-10, H + 10)
    for i in range(0, 41):
        x = i * W / 40
        p.lineTo(x, hill_y(x, slope))
    p.lineTo(W + 10, H + 10)
    p.close()
    return p


@lru_cache(maxsize=None)
def street(seed=5, dawn=0.0):
    s = _surface()
    c = s.getCanvas()
    top = mix("#08090D", "#2A1E3A", dawn)
    _grad_v(c, 0, H, [top, mix("#16131C", "#E9A178", dawn)], None)
    _stars(c, int(90 * (1 - dawn)), seed, 400)
    skyline(c, 700, mix("#121319", "#4A3440", dawn), seed + 1, lit=0.08, tall=1.6)
    skyline(c, 860, mix("#0B0C10", "#2E2028", dawn), seed + 2, lit=0.14, tall=1.2)
    c.drawRect(skia.Rect.MakeXYWH(0, GROUND, W, H - GROUND), fill(mix("#0A0A0D", "#1E1618", dawn)))
    c.drawLine(0, GROUND, W, GROUND, stroke("#3A3E4A", 3))
    return s.makeImageSnapshot()


@lru_cache(maxsize=None)
def void(tint="#E63946"):
    s = _surface()
    c = s.getCanvas()
    _radial(c, W / 2, H * 0.62, 1000, mix(tint, "#000000", 0.82), "#050507")
    c.drawLine(0, GROUND, W, GROUND, stroke(tint, 2, a=70))
    return s.makeImageSnapshot()


def lamp_post(c, x, T, on=1.0):
    c.drawLine(x, GROUND, x, GROUND - 420, stroke("#2A2D36", 10))
    c.drawLine(x, GROUND - 420, x + 70, GROUND - 420, stroke("#2A2D36", 8))
    if on:
        c.drawPath(poly([(x + 50, GROUND - 410), (x + 90, GROUND - 410), (x + 260, GROUND), (x - 120, GROUND)]),
                   blurred("#FFE8A3", 30, int(40 * on)))
        circle(c, x + 70, GROUND - 410, 14, fill("#FFE8A3"))
        circle(c, x + 70, GROUND - 410, 40, blurred("#FFE8A3", 20, 120))


@lru_cache(maxsize=8)
def grain_frames(n=6, seed=5):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        g = rng.integers(0, 255, size=(270, 480), dtype=np.uint8)
        rgba = np.zeros((270, 480, 4), dtype=np.uint8)
        rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = g
        rgba[..., 3] = 11
        out.append(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType))
    return out


# ----------------------------------------------------------------------------- live effects

def grain(c, T):
    imgs = grain_frames()
    img = imgs[int(T * 24) % len(imgs)]
    c.drawImageRect(img, skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kNearest))


def vignette(c, strength=170):
    p = fill("#000000")
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1150,
                                               [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, strength)],
                                               [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def bars(c, k=1.0):
    h = BAR * k
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, h), fill("#000000"))
    c.drawRect(skia.Rect.MakeXYWH(0, H - h, W, h), fill("#000000"))


def rain(c, T, n=220, angle=12, alpha=70, seed=4, speed=1800):
    rnd = random.Random(seed)
    dx = math.tan(math.radians(angle))
    p = stroke("#9FB4D9", 2, a=alpha, cap="butt")
    for i in range(n):
        x0 = rnd.uniform(-200, W + 100)
        ph = rnd.random()
        L = rnd.uniform(30, 70)
        sp = speed * rnd.uniform(0.8, 1.2)
        y = ((T * sp + ph * (H + 200)) % (H + 200)) - 100
        x = x0 + y * dx
        c.drawLine(x, y, x + L * dx, y + L, p)


def snow(c, T, n=160, wind=1.0, seed=8, alpha=170):
    """Wind-driven snow: dots plus short streaks when it blows hard."""
    rnd = random.Random(seed)
    for i in range(n):
        sp = rnd.uniform(0.6, 1.4)
        x = (rnd.uniform(0, W * 1.5) - T * 420 * wind * sp) % (W + 300) - 150
        y = (rnd.uniform(0, H) + T * 160 * sp) % (H + 100) - 50
        if wind > 0.6:
            L = 26 * wind * sp
            c.drawLine(x, y, x + L, y - L * 0.25, stroke("#E8ECF2", 2, a=int(alpha * 0.6)))
        else:
            circle(c, x, y, rnd.uniform(1.2, 3), fill("#E8ECF2", alpha))


def fog(c, T, y=760, color="#3A4466", alpha=50, n=7, seed=6):
    rnd = random.Random(seed)
    for i in range(n):
        x = (rnd.uniform(0, W) + T * rnd.uniform(15, 40)) % (W + 800) - 400
        oval(c, x, y + rnd.uniform(-60, 120), rnd.uniform(300, 520), rnd.uniform(60, 120), blurred(color, 40, alpha))


def embers(c, T, n=60, color="#FFD60A", seed=7, alpha=200, area=(0, 0, W, H), rise=120):
    rnd = random.Random(seed)
    x0, y0, w, h = area
    for i in range(n):
        x = x0 + rnd.uniform(0, w)
        ph = (T * rnd.uniform(0.05, 0.2) + rnd.random()) % 1
        y = y0 + h - ph * (h + rise)
        x += math.sin(T * 1.3 + i) * 18
        circle(c, x, y, rnd.uniform(1.2, 3.5), fill(color, int(alpha * math.sin(ph * math.pi))))


def screen_glow(c, x, y, color="#4CC9F0", k=1.0, flicker=0.0, T=0.0):
    a = 0.85 + flicker * 0.15 * math.sin(T * 23) * math.sin(T * 7)
    c.drawPath(poly([(x - 20, y), (x + 20, y), (x + 520, y + 420), (x - 520, y + 420)]), blurred(color, 40, int(60 * k * a)))
    circle(c, x, y, 160, blurred(color, 60, int(90 * k * a)))


def lightning(c, x0, y0, x1, y1, T, color="#FFE45C", width=6, seed=0, branches=2):
    rnd = random.Random(seed + int(T * 30))
    pts = [(x0, y0)]
    n = 12
    for i in range(1, n):
        u = i / n
        pts.append((x0 + (x1 - x0) * u + rnd.uniform(-40, 40), y0 + (y1 - y0) * u + rnd.uniform(-40, 40)))
    pts.append((x1, y1))
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    c.drawPath(path, blurred(color, 14, 200) if False else stroke(color, width * 4, a=60))
    c.drawPath(path, stroke(color, width, a=230))
    c.drawPath(path, stroke("#FFFFFF", width * 0.4))
    for b in range(branches):
        i = rnd.randint(2, n - 3)
        bx, by = pts[i]
        q = skia.Path()
        q.moveTo(bx, by)
        for k in range(4):
            bx += rnd.uniform(-60, 60)
            by += rnd.uniform(10, 50)
            q.lineTo(bx, by)
        c.drawPath(q, stroke(color, width * 0.5, a=180))


def beam(c, x0, y0, x1, y1, T, k=1.0, color="#FFD60A"):
    """Energy beam from (x0,y0) to (x1,y1)."""
    w = 70 * k * (1 + 0.08 * math.sin(T * 40))
    c.drawLine(x0, y0, x1, y1, stroke(color, w * 2.2, a=60, cap="round"))
    c.drawLine(x0, y0, x1, y1, stroke(color, w, a=200, cap="round"))
    c.drawLine(x0, y0, x1, y1, stroke("#FFFFFF", w * 0.4, cap="round"))
    circle(c, x0, y0, w * 1.1, blurred(color, 30, 220))
    circle(c, x1, y1, w * 1.6, blurred("#FFFFFF", 40, 200))


def sparks(c, x, y, t, n=26, seed=1, color="#FFD60A", power=1.0):
    """Burst of sparks, t = seconds since impact."""
    if t < 0 or t > 0.9:
        return
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, 6.283)
        sp = rnd.uniform(400, 1300) * power
        d = sp * t * (1 - t * 0.6)
        px, py = x + math.cos(a) * d, y + math.sin(a) * d + 400 * t * t
        L = 30 * (1 - t)
        c.drawLine(px, py, px - math.cos(a) * L, py - math.sin(a) * L, stroke(color, 4 * (1 - t) + 1, a=int(255 * (1 - t))))
    if t < 0.25:
        k = 1 - t / 0.25
        circle(c, x, y, 46 * power, blurred("#FFFFFF", 12, int(240 * k)))
        circle(c, x, y, 18 * power, fill("#FFFFFF", int(255 * k)))
        circle(c, x, y, (60 + 200 * (1 - k)) * power, stroke(color, 8 * k + 1, a=int(220 * k)))


def speed_lines(c, T, k=1.0, cx=W / 2, cy=H / 2, n=60, seed=9, color="#FFFFFF"):
    rnd = random.Random(seed + int(T * 20))
    for i in range(n):
        a = rnd.uniform(0, 6.283)
        r0 = rnd.uniform(380, 700)
        r1 = r0 + rnd.uniform(200, 600)
        c.drawLine(cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * r1, cy + math.sin(a) * r1,
                   stroke(color, rnd.uniform(1.5, 4), a=int(90 * k)))


def flash(c, k, color="#FFFFFF"):
    if k > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(color, int(255 * min(1, k))))


def hp_bar(c, x, y, w, hp, label="LATER", color="#9D4EDD"):
    draw_text(c, label, x, y - 12, "BebasNeue.ttf", 42, color="#E0AAFF", align="left")
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, 16), fill("#000000", 200))
    c.drawRect(skia.Rect.MakeXYWH(x + 3, y + 3, (w - 6) * max(0, hp), 10), fill(color))
    c.drawRect(skia.Rect.MakeXYWH(x + 3, y + 3, (w - 6) * max(0, hp), 10), blurred(color, 6, 160))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, 16), stroke("#E0AAFF", 1.5, a=120))
