"""LATER: a smoky shadow entity with violet eyes, a grin of light and grasping tendrils."""
import math
import random

import skia

from engine.gfx import blurred, circle, col, fill, oval, poly, stroke

CORE = "#07040D"
SMOKE = "#140A22"
RIM = "#9D4EDD"
EYE = "#E0AAFF"

_rnd = random.Random(11)
PUFFS = [(_rnd.uniform(-1, 1), _rnd.uniform(-1, 0.9), _rnd.uniform(0.35, 0.6), _rnd.uniform(0, 6.28), _rnd.uniform(0.6, 1.4))
         for _ in range(16)]
TENDRILS = [(-150, 60, 200), (-110, 120, 230), (120, 110, -40), (150, 40, -10), (-60, 150, 160), (70, 150, 20)]


def _tendril(c, x0, y0, ang, L, t, k, width=58, reach=0.0, target=None):
    """A tapering tentacle from (x0,y0) heading at angle ang (deg, 0=right)."""
    pts = []
    n = 14
    for i in range(n + 1):
        u = i / n
        a = math.radians(ang + math.sin(t * 1.7 + k * 1.3 + u * 3.5) * 28 * u)
        if i == 0:
            x, y = x0, y0
        else:
            seg = L / n * (1 + reach)
            x, y = pts[-1][0] + math.cos(a) * seg, pts[-1][1] + math.sin(a) * seg
        pts.append((x, y))
    if target is not None and reach > 0:
        tx, ty = target
        for i in range(len(pts)):
            u = (i / n) ** 2 * min(1, reach)
            pts[i] = (pts[i][0] + (tx - pts[-1][0]) * u, pts[i][1] + (ty - pts[-1][1]) * u)
    left, right = [], []
    for i in range(len(pts)):
        x, y = pts[i]
        x2, y2 = pts[min(i + 1, n)] if i < n else pts[i - 1]
        dx, dy = (x2 - x, y2 - y) if i < n else (x - x2, y - y2)
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = width * (1 - i / (n + 1)) ** 1.3 / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    path = poly(left + right[::-1])
    c.drawPath(path, blurred(RIM, 12, 120))
    c.drawPath(path, fill(SMOKE))
    c.drawPath(path, stroke(RIM, 2.5, a=170))
    return pts[-1]


def draw_shadow(c, x, y, s=1.0, t=0.0, mood="grin", hp=1.0, dissolve=0.0, reach=0.0, target=None,
                eye=1.0, alpha=255):
    """mood: grin | angry | hurt | laugh. reach 0..1 extends tendrils towards target (world coords)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if alpha < 255:
        c.saveLayerAlpha(None, alpha)
    flick = 1.0
    if hp < 0.4:
        flick = 0.75 + 0.25 * math.sin(t * 37) * math.sin(t * 13)
    breathe = 1 + 0.03 * math.sin(t * 1.4)
    R = 190 * breathe
    tgt = None
    if target is not None:
        tgt = ((target[0] - x) / s, (target[1] - y) / s)
    # tendrils behind
    for k, (tx0, ty0, ang) in enumerate(TENDRILS):
        if dissolve > 0.5:
            break
        rr = reach if k in (0, 1) else 0
        _tendril(c, tx0 * breathe, ty0, ang, 230 + 40 * math.sin(k), t, k, reach=rr, target=tgt)
    # outer glow
    circle(c, 0, -10, R * 1.15, blurred(RIM, 60, int(110 * flick * (1 - dissolve))))
    # smoke puffs: glow pass first, then the dark smoke on top so no bubble outlines show
    puffs = []
    for i, (px, py, pr, ph, sp) in enumerate(PUFFS):
        wob = math.sin(t * sp + ph)
        dx = px * R * 0.85 + wob * 10
        dy = py * R * 0.8 + math.cos(t * sp * 0.8 + ph) * 8
        if dissolve > 0:
            dx += px * dissolve * 600
            dy += (py - 0.6) * dissolve * 500
        puffs.append((dx, dy, pr * R * (1 + 0.08 * wob) * (1 - dissolve * 0.6)))
    a = int(255 * (1 - dissolve))
    for (dx, dy, rr) in puffs:
        circle(c, dx, dy, rr + 9, blurred(RIM, 16, int(a * 0.5 * flick)))
    for (dx, dy, rr) in puffs:
        circle(c, dx, dy, rr, blurred(SMOKE, 7, a))
    oval(c, 0, -10, R * 0.75, R * 0.7, blurred(CORE, 30, int(255 * (1 - dissolve))))
    # face
    if dissolve < 0.6:
        fa = int(255 * eye * flick * (1 - dissolve / 0.6))
        ey = -40
        for sx in (-1, 1):
            c.save()
            c.translate(sx * 58, ey)
            tilt = {"grin": 14, "angry": 26, "hurt": -10, "laugh": 8}.get(mood, 14)
            c.rotate(sx * tilt)
            h = 15 if mood != "hurt" else 22
            if mood == "laugh":
                h = 6
            oval(c, 0, 0, 44, h * 2.2, blurred(RIM, 16, fa))
            oval(c, 0, 0, 34, h, fill(EYE, fa))
            oval(c, 0, 0, 20, h * 0.5, fill("#FFFFFF", fa))
            c.restore()
        # grin of light
        gw = 105 if mood in ("grin", "laugh") else 70
        gh = 44 if mood == "laugh" else 26
        if mood == "hurt":
            gw, gh = 50, -16
        m = skia.Path()
        m.moveTo(-gw, 30)
        m.quadTo(0, 30 + gh * 2.6, gw, 30)
        m.quadTo(0, 30 + gh * 1.1, -gw, 30)
        m.close()
        c.drawPath(m, blurred(RIM, 14, fa))
        c.drawPath(m, fill(EYE, fa))
        # teeth
        if mood in ("grin", "laugh", "angry"):
            for i in range(9):
                u = -1 + i / 4
                tx = u * gw * 0.85
                ty = 30 + gh * 1.1 * (1 - u * u) + 2
                c.drawPath(poly([(tx - 9, ty), (tx + 9, ty), (tx, ty + 16)]), fill(CORE, fa))
    if alpha < 255:
        c.restore()
    c.restore()


def particles(c, x, y, t, n=60, spread=420, color=RIM, seed=3, alpha=200):
    """Drifting embers around the shadow."""
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, 6.283)
        r0 = rnd.uniform(0.2, 1.0) * spread
        sp = rnd.uniform(20, 70)
        ph = (t * sp / 200 + rnd.random()) % 1.0
        px = x + math.cos(a) * r0 + math.sin(t + i) * 12
        py = y + math.sin(a) * r0 * 0.6 - ph * 220
        circle(c, px, py, rnd.uniform(1.5, 4), fill(color, int(alpha * math.sin(ph * math.pi))))
