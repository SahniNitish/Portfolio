"""Adult-season thumbnails: hooded close-up, intense eyes, red shadow self, huge rounded text."""
import math
import os
import random

import skia
from PIL import Image

from engine.gfx import blurred, circle, col, draw_text, fill, mix, oval, poly, stroke, text_width
from . import fx
from . import things as Th
from .rig import HOODIE, HOODIE_BACK, SKIN, SKIN_SHADE, SHADOW_EYE

W, H = 1920, 1080
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "adult", "thumbnails")
FONT = "Baloo2-ExtraBold.ttf"
RED = "#FF3B4A"

THUMBS = {
    1: dict(text=["NOT *LAZY.*"], expr="angry", prop=("pizza_box", 330, 960, 1.6, {}), sky="#0B1426", shadow=True),
    2: dict(text=["*2* MINUTES."], expr="angry", prop=("wall_clock", 330, 700, 2.2, {"speed": 0}), sky="#101826", shadow=True),
    3: dict(text=["PUT IT *DOWN.*"], expr="tired", prop=("phone", 360, 720, 3.2, {"glow": 1.0}), sky="#06101C", shadow=True, glow="#4CC9F0"),
    4: dict(text=["PERFECT", "IS *FEAR.*"], expr="sad", prop=("laptop", 340, 900, 2.0, {"glow": 1.0}), sky="#14101E", shadow=True, small=True),
    5: dict(text=["TOO *MUCH.*"], expr="shocked", prop=("bills", 340, 960, 2.0, {}), sky="#0E1420", shadow=True),
    6: dict(text=["NO", "*MOTIVATION?*"], expr="tired", prop=("alarm", 330, 700, 2.2, {"ring": 1.0}), sky="#0B1426", shadow=False, small=True),
    7: dict(text=["FUTURE *YOU.*"], expr="determined", prop=("calendar", 330, 720, 1.8, {"marks": 12}), sky="#101826", shadow=True),
    8: dict(text=["ALWAYS *TIRED.*"], expr="tired", prop=("mug", 330, 960, 3.0, {}), sky="#0D1018", shadow=True, bags=1.0),
    9: dict(text=["THEM vs *YOU.*"], expr="sad", prop=("phone", 360, 720, 3.2, {"glow": 1.0}), sky="#0B1426", shadow=True, glow="#4CC9F0"),
    10: dict(text=["FAILED", "*AGAIN?*"], expr="angry", prop=("calendar", 330, 720, 1.8, {"marks": 6}), sky="#101826", shadow=True, small=True),
}


def _bg(c, sky, seed):
    p = fill(sky)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W * 0.5, H * 0.45), 1300,
                                               [col(mix(sky, "#FFFFFF", 0.12)), col(sky), col("#020306")], [0, 0.5, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    rnd = random.Random(seed)
    # pine silhouettes like a snowy forest at night
    for layer, (colr, base, sc) in enumerate((("#0E1830", 980, 1.0), ("#08101F", 1060, 1.4))):
        x = -60
        while x < W + 60:
            h = rnd.uniform(260, 520) * sc
            w = h * 0.36
            c.drawPath(poly([(x, base - h), (x - w / 2, base), (x + w / 2, base)]), fill(colr))
            c.drawPath(poly([(x, base - h), (x - w * 0.18, base - h * 0.55), (x + w * 0.18, base - h * 0.55)]), fill("#DDE6F5", 40))
            x += rnd.uniform(110, 210) * sc
    # bokeh snow
    for i in range(70):
        r = rnd.uniform(3, 18)
        circle(c, rnd.uniform(0, W), rnd.uniform(0, H), r, blurred("#E8F0FF", r * 0.6, rnd.randint(60, 170)))
    fx.snow(c, 2.3, n=120, wind=0.9, alpha=150, seed=seed)


def _closeup(c, cx, cy, s, expr, bags=0.6, snow_on=True, breath=True):
    c.save()
    c.translate(cx, cy)
    c.scale(s, s)
    # hoodie body / shoulders
    body = skia.Path()
    body.moveTo(-260, 420)
    body.cubicTo(-250, 160, -150, 90, 0, 90)
    body.cubicTo(150, 90, 250, 160, 260, 420)
    body.close()
    bp = fill(HOODIE)
    bp.setShader(skia.GradientShader.MakeLinear([skia.Point(-260, 0), skia.Point(260, 0)],
                                                [col(HOODIE_BACK), col(HOODIE), col("#4A4E5C")]))
    c.drawPath(body, bp)
    c.drawLine(-30, 120, -40, 300, stroke("#1A1C22", 8))
    c.drawLine(30, 120, 40, 300, stroke("#1A1C22", 8))
    # hood back
    oval(c, 0, -10, 175, 170, fill(HOODIE_BACK))
    # head
    hp = fill(SKIN)
    hp.setShader(skia.GradientShader.MakeRadial(skia.Point(-40, -50), 200, [col("#F7F3E8"), col(SKIN), col(SKIN_SHADE)], [0, 0.6, 1]))
    oval(c, 0, 10, 128, 132, hp)
    # hood rim
    rim = skia.Path()
    rim.addArc(skia.Rect.MakeLTRB(-150, -150, 150, 160), 160, 220)
    c.drawPath(rim, stroke(HOODIE, 34))
    if snow_on:
        rnd = random.Random(3)
        cap = skia.Path()
        for i in range(34):
            a = math.radians(rnd.uniform(195, 345))
            r = rnd.uniform(150, 172)
            q = skia.Path()
            q.addCircle(math.cos(a) * r, math.sin(a) * r + 4, rnd.uniform(16, 30))
            cap = q if i == 0 else skia.Op(cap, q, skia.PathOp.kUnion_PathOp)
        c.drawPath(cap, fill("#EEF3FA"))
        c.drawPath(cap, stroke("#C9D4E4", 3))
        for (x0, y0) in ((-200, 150), (190, 150)):
            sh = skia.Path()
            for i in range(7):
                q = skia.Path()
                q.addCircle(x0 + rnd.uniform(-50, 50), y0 + rnd.uniform(-12, 12), rnd.uniform(14, 24))
                sh = q if i == 0 else skia.Op(sh, q, skia.PathOp.kUnion_PathOp)
            c.drawPath(sh, fill("#EEF3FA"))
        for i in range(6):
            x, y = rnd.uniform(-150, 150), rnd.uniform(-150, -120)
            c.drawPath(poly([(x - 5, y), (x + 5, y), (x, y + rnd.uniform(18, 34))]), fill("#DCE8F5", 220))
    # face
    ink = "#1E1E24"
    for sx in (-1, 1):
        ex = sx * 52
        # eye bags
        if bags > 0:
            oval(c, ex, 22, 44, 30, fill("#8E6E7A", int(150 * bags)))
        oval(c, ex, 4, 40, 36 if expr != "tired" else 22, fill("#FFFFFF"))
        oval(c, ex, 4, 40, 36 if expr != "tired" else 22, stroke("#C9B9B0", 3))
        pr = 15 if expr != "shocked" else 10
        circle(c, ex + 6, 8, pr, fill(ink))
        circle(c, ex + 1, 2, 4, fill("#FFFFFF"))
        # brows
        if expr in ("angry", "determined"):
            c.drawLine(ex - sx * 40, -18, ex + sx * 42, -52, stroke(ink, 16))
        elif expr == "sad":
            c.drawLine(ex - sx * 40, -56, ex + sx * 40, -32, stroke(ink, 13))
        elif expr == "tired":
            c.drawLine(ex - 40, -26, ex + 38, -26, stroke(ink, 13))
            oval(c, ex, -6, 42, 14, fill(SKIN_SHADE))
        else:
            c.drawLine(ex - 38, -60, ex + 34, -66, stroke(ink, 12))
    # mouth
    if expr == "shocked":
        oval(c, 0, 82, 16, 20, fill(ink))
    elif expr == "sad":
        m = skia.Path()
        m.moveTo(-26, 90)
        m.quadTo(0, 74, 26, 90)
        c.drawPath(m, stroke(ink, 8))
    else:
        c.drawLine(-22, 84, 22, 82, stroke(ink, 8))
    c.drawLine(-8, -18, 8, -12, stroke("#C8B9A6", 4))  # brow crease
    # fists gripping the drawstrings
    for sx in (-1, 1):
        circle(c, sx * 70, 250, 54, fill(SKIN))
        circle(c, sx * 70, 250, 54, stroke(SKIN_SHADE, 4))
        for k in range(3):
            c.drawLine(sx * 70 - 30, 228 + k * 18, sx * 70 + 30, 228 + k * 18, stroke(SKIN_SHADE, 3))
    if breath:
        for i in range(3):
            oval(c, 120 + i * 50, 70 - i * 14, 40 + i * 20, 26 + i * 10, blurred("#DDE6F0", 18, 120 - i * 30))
    c.restore()


def _shadow_self(c, x, y, s):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = skia.Paint(ImageFilter=skia.ImageFilters.DropShadow(0, 0, 18, 18, skia.Color(235, 40, 50, 255), None))
    c.saveLayer(None, p)
    oval(c, 0, 0, 150, 154, fill("#07070A"))
    body = skia.Path()
    body.moveTo(-230, 520)
    body.cubicTo(-220, 230, -120, 130, 0, 130)
    body.cubicTo(120, 130, 220, 230, 230, 520)
    body.close()
    c.drawPath(body, fill("#07070A"))
    c.restore()
    for sx in (-1, 1):
        e = skia.Path()
        e.moveTo(sx * 40 - 36, -10 + (6 if sx > 0 else 0))
        e.quadTo(sx * 40, -34, sx * 40 + 36, -10)
        c.drawPath(e, stroke(SHADOW_EYE, 13))
        c.drawPath(e, blurred(SHADOW_EYE, 10, 160))
    m = skia.Path()
    m.moveTo(-40, 50)
    m.quadTo(10, 80, 50, 40)
    c.drawPath(m, stroke(SHADOW_EYE, 9))
    c.restore()


def _headline(c, lines, small=False):
    size = 210 if not small else 172
    y = 40 + size * 0.86
    for ln in lines:
        parts = [(seg, i % 2 == 1) for i, seg in enumerate(ln.split("*")) if seg]
        total = sum(text_width(s_, FONT, size) for s_, _ in parts)
        while total > 1780:
            size -= 6
            total = sum(text_width(s_, FONT, size) for s_, _ in parts)
        x = W / 2 - total / 2
        for s_, em in parts:
            draw_text(c, s_, x, y + size * 0.05, FONT, size, color="#000000", outline="#000000", ow=size * 0.24, align="left")
            draw_text(c, s_, x, y, FONT, size, color=RED if em else "#FFFFFF", outline="#000000", ow=size * 0.16, align="left")
            x += text_width(s_, FONT, size)
        y += size * 0.92


def render_thumb(n, path):
    cfg = THUMBS[n]
    s = skia.Surface(W, H)
    c = s.getCanvas()
    _bg(c, cfg["sky"], n)
    if cfg.get("shadow"):
        _shadow_self(c, 1500, 640, 1.25)
    name, px, py, ps, kw = cfg["prop"]
    if cfg.get("glow"):
        circle(c, px, py, 260, blurred(cfg["glow"], 90, 120))
    Th.draw(c, name, px, py, ps, 1.3, rot=-8, **kw)
    _closeup(c, 960, 640 if not cfg.get("small") else 690, 1.75, cfg["expr"], bags=cfg.get("bags", 0.7))
    vg = fill("#000000")
    vg.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1150,
                                                [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 170)], [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), vg)
    _headline(c, cfg["text"], cfg.get("small", False))
    img = s.makeImageSnapshot().toarray()
    im = Image.fromarray(img[:, :, [2, 1, 0]]).resize((1280, 720), Image.LANCZOS)
    im.save(path, quality=92, optimize=True)
    return path


def make_all(nums):
    os.makedirs(OUT, exist_ok=True)
    for n in nums:
        print("thumbnail", render_thumb(n, os.path.join(OUT, f"ep{n:02d}_thumbnail.jpg")), flush=True)
    ims = [Image.open(os.path.join(OUT, f"ep{n:02d}_thumbnail.jpg")).resize((640, 360)) for n in nums]
    sheet = Image.new("RGB", (1280, 360 * ((len(ims) + 1) // 2)))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 2) * 640, (i // 2) * 360))
    sheet.save(os.path.join(OUT, "ALL_THUMBNAILS.jpg"), quality=90)
