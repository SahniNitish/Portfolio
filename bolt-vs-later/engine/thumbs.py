"""YouTube thumbnails (1280x720). Rendered at 1920x1080 and downscaled for smooth edges."""
import math
import os

import skia
from PIL import Image

from . import props as P
from .characters import draw_bolt, draw_later
from .gfx import INK, blurred, circle, col, draw_text, fill, mix, poly, stroke, text_width
from .scenes import H, TITLE_FONT, W, _vignette

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "thumbnails")

THUMBS = {
    1: dict(bg=("#FF006E", "#5C0029"), text=["YOU'RE NOT", "LAZY!"], hl=1, side="left",
            bolt=dict(x=1480, y=640, s=2.0, mood="scared", pose="scared"),
            later=dict(x=1760, y=250, s=0.85, mood="laugh"),
            prop=dict(name="brain", x=1040, y=830, s=1.2), arrow=None),
    2: dict(bg=("#FB5607", "#5E1F00"), text=["JUST 2", "MINUTES"], hl=0, side="left",
            bolt=dict(x=1500, y=660, s=1.9, mood="excited", pose="cheer"),
            later=dict(x=1780, y=260, s=0.8, mood="shocked"),
            prop=dict(name="clock", x=1060, y=800, s=1.35), arrow=True),
    3: dict(bg=("#0077B6", "#03045E"), text=["PHONE", "TRAP!"], hl=1, side="left",
            bolt=dict(x=1560, y=690, s=1.75, mood="scared", pose="scared"),
            later=dict(x=1330, y=300, s=1.0, mood="laugh"),
            prop=dict(name="phone", x=1000, y=760, s=1.75, rot=-10), arrow=True),
    4: dict(bg=("#8338EC", "#2A0B5C"), text=["PERFECT", "= STUCK"], hl=1, side="left",
            bolt=dict(x=1500, y=660, s=1.95, mood="sad", pose="think"),
            later=dict(x=1790, y=240, s=0.8, mood="smug"),
            prop=dict(name="target", x=1040, y=820, s=1.1), arrow=None),
    5: dict(bg=("#118AB2", "#073B4C"), text=["TOO MUCH", "TO DO?"], hl=1, side="left",
            bolt=dict(x=1480, y=680, s=1.8, mood="scared", pose="scared"),
            later=dict(x=1800, y=230, s=0.75, mood="laugh"),
            props=[dict(name="checklist", x=1130, y=360, s=1.0, rot=-12), dict(name="clock", x=1820, y=640, s=0.8, rot=10),
                   dict(name="laptop", x=560, y=840, s=1.25, rot=-6), dict(name="calendar", x=1060, y=680, s=0.85, rot=8),
                   dict(name="phone", x=220, y=860, s=0.9, rot=14)], arrow=None),
    6: dict(bg=("#2A9D8F", "#0B3B36"), text=["MOTIVATION", "IS A LIE"], hl=1, side="left", size=168,
            bolt=dict(x=1520, y=650, s=1.9, mood="determined", pose="flex"),
            later=dict(x=1800, y=250, s=0.8, mood="shocked"),
            prop=dict(name="calendar", x=1030, y=820, s=1.0, rot=-8), arrow=None),
    7: dict(bg=("#FF7B00", "#6B2A00"), text=["FUTURE YOU", "NEEDS YOU"], hl=0, side="left", size=172,
            bolt=dict(x=1520, y=660, s=1.9, mood="excited", pose="point", flip=True),
            later=dict(x=1810, y=250, s=0.75, mood="angry"),
            prop=dict(name="letter", x=1020, y=820, s=1.15, rot=-8), arrow=None),
    8: dict(bg=("#3A86FF", "#0B1F5C"), text=["ALWAYS", "TIRED?"], hl=1, side="left",
            bolt=dict(x=1520, y=680, s=1.9, mood="tired", pose="down"),
            later=dict(x=1800, y=250, s=0.8, mood="smug", hold="pillow"),
            prop=dict(name="battery", x=1000, y=820, s=1.25, kw=dict(level=0.12)), arrow=True),
    9: dict(bg=("#F15BB5", "#4F0E37"), text=["THEM", "vs YOU"], hl=1, side="left",
            bolt=dict(x=1520, y=680, s=1.85, mood="sad", pose="hold", hold="phone"),
            later=dict(x=1800, y=250, s=0.8, mood="laugh"),
            prop=dict(name="chart", x=1020, y=820, s=1.1, rot=-6), arrow=None),
    10: dict(bg=("#06A77D", "#023D2C"), text=["FAILED", "AGAIN?"], hl=0, side="left",
             bolt=dict(x=1500, y=660, s=1.95, mood="determined", pose="fist"),
             later=dict(x=1800, y=250, s=0.8, mood="shocked"),
             prop=dict(name="mountain", x=1040, y=820, s=1.1), arrow=None),
}


def _burst(c, c1, c2):
    paint = fill(c1)
    paint.setShader(skia.GradientShader.MakeRadial(skia.Point(1300, 500), 1400,
                                                   [col(mix(c1, "#FFFFFF", 0.3)), col(c1), col(c2)], [0, 0.4, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), paint)
    c.save()
    c.translate(1350, 520)
    for i in range(16):
        a0 = math.radians(i * 22.5)
        a1 = math.radians(i * 22.5 + 11.25)
        c.drawPath(poly([(0, 0), (math.cos(a0) * 2600, math.sin(a0) * 2600), (math.cos(a1) * 2600, math.sin(a1) * 2600)]),
                   fill("#FFFFFF", 30))
    c.restore()
    _vignette(c, 130)


def _arrow(c, x0, y0, x1, y1):
    ang = math.atan2(y1 - y0, x1 - x0)
    L = math.hypot(x1 - x0, y1 - y0)
    c.save()
    c.translate(x0, y0)
    c.rotate(math.degrees(ang))
    p = poly([(0, -22), (L - 60, -22), (L - 60, -55), (L + 10, 0), (L - 60, 55), (L - 60, 22), (0, 22)])
    c.drawPath(p, stroke(INK, 22))
    c.drawPath(p, fill("#FF1F3D"))
    c.restore()


def render_thumb(num, path):
    cfg = THUMBS[num]
    s = skia.Surface(W, H)
    c = s.getCanvas()
    _burst(c, *cfg["bg"])
    T = 1.7
    lt = cfg["later"]
    draw_later(c, lt["x"] - 30, lt["y"] + 10, lt["s"] * 1.25, T, mood=lt["mood"], look=(-0.8, 0.4), zzz=False,
               hold=lt.get("hold"), rot=-8)
    for pr in cfg.get("props", [cfg.get("prop")]):
        if pr:
            if "props" not in cfg:
                pr = dict(pr, x=pr.get("tx", 700), y=pr.get("ty", 820), s=pr["s"] * 1.3)
                circle(c, pr["x"], pr["y"], 190 * pr["s"] / 1.3, blurred("#FFFFFF", 40, 70))
            P.draw(c, pr["name"], pr["x"], pr["y"], pr["s"], T, rot=pr.get("rot", 0), **pr.get("kw", {}))
            if cfg.get("arrow") and "props" not in cfg:
                _arrow(c, pr["x"] - 420, pr["y"] + 150, pr["x"] - 170 * pr["s"] / 1.3, pr["y"] + 40)
    b = cfg["bolt"]
    circle(c, b["x"], b["y"] - 20, 330 * b["s"] / 1.9, blurred("#FFFFFF", 60, 120))
    draw_bolt(c, b["x"], b["y"] + 20, b["s"] * 1.12, T, mood=b["mood"], pose=b["pose"], mouth=0.0 if b["mood"] in ("sad", "tired") else 0.75,
              look=(-0.5, 0.0), flip=b.get("flip", False), hold=b.get("hold"), seed=1)
    # headline
    size = cfg.get("size", 215)
    c.save()
    c.translate(70, 120)
    c.rotate(-4)
    y = size * 0.9
    for i, line in enumerate(cfg["text"]):
        sz = size
        while text_width(line, TITLE_FONT, sz) > 960 and sz > 90:
            sz -= 4
        colr = "#FFD60A" if i == cfg["hl"] else "#FFFFFF"
        draw_text(c, line, 0, y + 14, TITLE_FONT, sz, color=INK, align="left", outline=INK, ow=sz * 0.2)
        draw_text(c, line, 0, y, TITLE_FONT, sz, color=colr, outline=INK, ow=sz * 0.16, align="left")
        y += sz * 1.02
    c.restore()
    img = s.makeImageSnapshot().toarray()
    im = Image.fromarray(img[:, :, [2, 1, 0]]).resize((1280, 720), Image.LANCZOS)
    im.save(path.replace(".png", ".jpg"), quality=92, optimize=True)
    im.save(path)
    return path


def make_all(nums):
    os.makedirs(OUT, exist_ok=True)
    for n in nums:
        p = render_thumb(n, os.path.join(OUT, f"ep{n:02d}_thumbnail.png"))
        print("thumbnail", p, flush=True)
