"""Deep Time Academy shared animation library (flat 2D "animated history" look).

Import it from an episode folder:
    sys.path.insert(0, os.path.join(HERE, ".."))           # deeptime/
    sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
    from engine import *
    import dta as D
    from dta import *

What is here (all drawing works on a 1920x1080 RGBA frame `f` at time `t` in seconds):
  fonts       cinzel(size, weight), sym(size)  (DejaVu symbols: ♥ ★ ♦ $; Anton has NO symbols)
  characters  load_cuts(img_dir, names), char(f, name, t, t_in, x, base, h, enter, flip, t_out, phase, walk)
  titles      gold_text(f, text, (cx, cy), size, a, shine, scale, weight, spacing)
  labels      label(f, t, t_in, text, (x, y), bg, fg, size, angle, t_out, face)
  icons       BADGE[k] for k in heart house hourglass coin sword land scroll players strategy payoff info,
              pop_img(f, t, t_in, img, (x, y)), heart_pts(cx, cy, s)
  long video  chapter_card(t, t0, num, title) -> frame, payoff_matrix(f, t, t_in, labels, cells, highlight),
              progress_bar(f, frac, mark=0.37, label_txt="37%")
  mood        motes(f, t), darken(f, k, color), spot(f, k), sepia(f, k)
  chalk       chalk_line(d, a, b, frac, color, width), person_glyph(d, x, y, color, s)
  props       medal_img(), arrow(d, x, y, up, color, s), reel_strip(order), SYMS, CELL
  channel     chrome(f, t) (series tag + watermark; set SERIES_TAG), sting_frame(u, end)
  audio       tone(freq, dur), nf(midi), fx_heartbeat(), fx_riser(dur), fx_shimmer(dur), fx_chalk(dur), fx_hit()
              music(total, mgain, dgain): curious A-minor pizzicato + low drone; mgain/dgain(t) -> 0..1
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "tools"))
from engine import *  # noqa: E402,F401,F403
import engine as E    # noqa: E402

FONTS = os.path.join(E.ROOT, "assets", "fonts")
SERIES_TAG = "GAME THEORY  ·  EP 1"

GOLD, GOLD_D, CREAM, NAVY = (232, 190, 96), (150, 98, 30), (250, 240, 215), (14, 20, 38)
BLOOD, TEAL, CHALK = (196, 32, 40), (40, 170, 150), (238, 238, 228)


# ---------------------------------------------------------------- fonts
_cf = {}


def cinzel(size, weight="Black"):
    k = (size, weight)
    if k not in _cf:
        f = ImageFont.truetype(os.path.join(FONTS, "Cinzel.ttf"), size)
        f.set_variation_by_name(weight)
        _cf[k] = f
    return _cf[k]


SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_sf = {}


def sym(size):
    if size not in _sf:
        _sf[size] = ImageFont.truetype(SYM, size)
    return _sf[size]



CUT = {}
_scaled = {}


def load_cuts(img_dir, names):
    """Key green-screen character PNGs (img_dir/<name>.png) into CUT[name]."""
    for n in names:
        CUT[n] = key_green(os.path.join(img_dir, n + ".png"))
    return CUT



def scaled(name, h, flip=False):
    k = (name, h, flip)
    if k not in _scaled:
        im = CUT[name]
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        _scaled[k] = im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im
    return _scaled[k]


def char(f, name, t, t_in, x, base, h, enter="pop", flip=False, t_out=None, phase=0.0, walk=False):
    """Cut-out character: enters (slide from left/right/bottom, or pop), lands with a squash, then breathes."""
    if t < t_in:
        return
    u = clamp01((t - t_in) / 0.6)
    im = scaled(name, h, flip)
    sx, sy, dx, dy, a = 1.0, 1.0, 0.0, 0.0, 1.0
    if enter in ("left", "right"):
        dist = (x + im.width) if enter == "left" else (W - x + im.width)
        dx = (-1 if enter == "left" else 1) * dist * (1 - ease(u))
        land = clamp01((t - t_in - 0.6) / 0.25)
        if 0 < land < 1:
            sy = 1 - 0.05 * math.sin(math.pi * land); sx = 1 + 0.03 * math.sin(math.pi * land)
        if u < 1:
            dy = -abs(math.sin(u * math.pi * 3)) * 22          # little hops while travelling
    elif enter == "bottom":
        dy = (1 - ease_out_back(u)) * (h * 0.9)
    else:                                                     # pop
        s = 0.6 + 0.4 * ease_out_back(clamp01((t - t_in) / 0.35))
        sx = sy = s; a = clamp01((t - t_in) / 0.15)
    if t_out is not None and t > t_out:
        a *= 1 - clamp01((t - t_out) / 0.3)
    br = math.sin(2 * math.pi * 0.45 * t + phase)
    sy *= 1 + 0.008 * br; dy += -3 * br
    if walk:
        dy += -abs(math.sin(t * 7 + phase)) * 14
    w2, h2 = max(1, round(im.width * sx)), max(1, round(im.height * sy))
    im2 = im if (w2, h2) == im.size else im.resize((w2, h2), Image.BILINEAR)
    if a < 1:
        im2 = im2.copy(); im2.putalpha(im2.getchannel("A").point(lambda v: int(v * a)))
    # ground shadow
    sh = Image.new("RGBA", (w2 + 60, 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((10, 14, w2 + 50, 46), fill=(0, 0, 0, int(95 * a)))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    f.alpha_composite(sh, (round(x + dx - sh.width / 2), round(base - 30)))
    f.alpha_composite(im2, (round(x + dx - w2 / 2), round(base + dy - h2)))


# ---------------------------------------------------------------- gold titles
_gold = {}


def gold_layer(text, size, weight="Black", spacing=0):
    k = (text, size, weight, spacing)
    if k in _gold:
        return _gold[k]
    fnt = cinzel(size, weight)
    d0 = ImageDraw.Draw(Image.new("L", (10, 10)))
    widths = [d0.textlength(ch, font=fnt) + spacing for ch in text]
    tw = int(sum(widths)) + 80; th = int(size * 1.5) + 60
    mask = Image.new("L", (tw, th), 0); d = ImageDraw.Draw(mask)
    x = 40
    for ch, w_ in zip(text, widths):
        d.text((x, 30), ch, font=fnt, fill=255); x += w_
    m = np.asarray(mask).astype(np.float32) / 255
    yy = np.linspace(0, 1, th)[:, None]
    grad = np.stack([np.interp(yy, [0, .38, .5, .62, 1], [255, 250, 205, 230, 150]),
                     np.interp(yy, [0, .38, .5, .62, 1], [244, 214, 140, 172, 92]),
                     np.interp(yy, [0, .38, .5, .62, 1], [196, 130, 50, 82, 22])], -1) * np.ones((1, tw, 1))
    out = np.zeros((th, tw, 4), np.float32)
    stroke = np.asarray(mask.filter(ImageFilter.MaxFilter(7))).astype(np.float32) / 255
    shadow = np.asarray(mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(10))).astype(np.float32) / 255
    shadow = np.roll(shadow, 8, 0)
    out[..., 3] = np.maximum(np.maximum(shadow * 0.75, stroke), m) * 255
    base = np.where(m[..., None] > 0, grad, np.array([45, 26, 8], np.float32))
    out[..., :3] = base * np.where(stroke[..., None] + m[..., None] > 0, 1, 0)
    lay = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
    _gold[k] = (lay, m)
    return _gold[k]


def gold_text(f, text, cxy, size, a=1.0, shine=None, scale=1.0, weight="Black", spacing=0):
    lay, m = gold_layer(text, size, weight, spacing)
    if shine is not None and 0 <= shine <= 1:
        arr = np.asarray(lay).astype(np.float32)
        hh, ww = m.shape
        X = np.arange(ww)[None, :] + 0.45 * np.arange(hh)[:, None]
        pos = -200 + shine * (ww + 400)
        band = np.exp(-((X - pos) / 60) ** 2) * m
        arr[..., :3] += band[..., None] * 200
        lay = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    if scale != 1.0:
        lay = lay.resize((max(1, round(lay.width * scale)), max(1, round(lay.height * scale))), Image.BICUBIC)
    if a < 1:
        lay = lay.copy(); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    f.alpha_composite(lay, (round(cxy[0] - lay.width / 2), round(cxy[1] - lay.height / 2)))


# ---------------------------------------------------------------- labels, icons, particles
_lab = {}


def label_img(text, size, bg, fg, pad=(28, 14), face="anton"):
    k = (text, size, bg, fg, face)
    if k not in _lab:
        fnt = font(size) if face == "anton" else cinzel(size, "Bold")
        d0 = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        l, t_, r, b = d0.textbbox((0, 0), text, font=fnt)
        w_, h_ = r - l + 2 * pad[0], b - t_ + 2 * pad[1]
        im = Image.new("RGBA", (w_ + 12, h_ + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((8, 10, w_ + 8, h_ + 10), 12, fill=(0, 0, 0, 120))            # drop shadow
        d.rounded_rectangle((2, 2, w_ + 2, h_ + 2), 12, fill=bg, outline=(30, 20, 10), width=4)
        d.text((2 + pad[0] - l, 2 + pad[1] - t_), text, font=fnt, fill=fg)
        _lab[k] = im
    return _lab[k]


def label(f, t, t_in, text, xy, bg=CREAM, fg=(40, 26, 12), size=54, angle=0, t_out=None, face="anton"):
    if t < t_in:
        return
    s = 0.2 + 0.8 * ease_out_back(clamp01((t - t_in) / 0.32), 2.2)
    a = 1.0 if t_out is None else 1 - clamp01((t - t_out) / 0.25)
    if a <= 0:
        return
    im = label_img(text, size, bg, fg, face=face)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.BICUBIC)
    if angle:
        im = im.rotate(angle, Image.BICUBIC, expand=True)
    if a < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    f.alpha_composite(im, (round(xy[0] - im.width / 2), round(xy[1] - im.height / 2)))


def heart_pts(cx, cy, s):
    pts = []
    for k in range(40):
        th = 2 * math.pi * k / 40
        x = 16 * math.sin(th) ** 3
        y = 13 * math.cos(th) - 5 * math.cos(2 * th) - 2 * math.cos(3 * th) - math.cos(4 * th)
        pts.append((cx + x * s / 16, cy - y * s / 16))
    return pts


def supersample(draw_fn, size, k=3):
    im = Image.new("RGBA", (size[0] * k, size[1] * k), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im), k)
    return im.resize(size, Image.LANCZOS)


def _badge(kind):
    def draw(d, k):
        R = 110 * k; c = (120 * k, 120 * k)
        d.ellipse((c[0] - R, c[1] - R, c[0] + R, c[1] + R), fill=(30, 22, 14), outline=GOLD, width=9 * k)
        if kind == "heart":
            d.polygon(heart_pts(c[0], c[1] + 6 * k, 62 * k), fill=BLOOD, outline=(255, 210, 200))
        elif kind == "house":
            d.polygon([(c[0] - 62 * k, c[1] - 2 * k), (c[0], c[1] - 64 * k), (c[0] + 62 * k, c[1] - 2 * k)], fill=GOLD)
            d.rectangle((c[0] - 46 * k, c[1] - 4 * k, c[0] + 46 * k, c[1] + 56 * k), fill=GOLD)
            d.rectangle((c[0] - 14 * k, c[1] + 16 * k, c[0] + 14 * k, c[1] + 56 * k), fill=(30, 22, 14))
        elif kind == "hourglass":
            d.rectangle((c[0] - 52 * k, c[1] - 70 * k, c[0] + 52 * k, c[1] - 58 * k), fill=GOLD)
            d.rectangle((c[0] - 52 * k, c[1] + 58 * k, c[0] + 52 * k, c[1] + 70 * k), fill=GOLD)
            d.polygon([(c[0] - 40 * k, c[1] - 58 * k), (c[0] + 40 * k, c[1] - 58 * k), (c[0] + 6 * k, c[1]),
                       (c[0] + 40 * k, c[1] + 58 * k), (c[0] - 40 * k, c[1] + 58 * k), (c[0] - 6 * k, c[1])],
                      fill=CREAM, outline=GOLD)
            d.polygon([(c[0] - 26 * k, c[1] + 54 * k), (c[0] + 26 * k, c[1] + 54 * k), (c[0], c[1] + 20 * k)], fill=GOLD)
        elif kind == "coin":                       # money
            for j, dy in enumerate((34, 10, -14)):
                d.ellipse((c[0] - 56 * k, c[1] + dy * k - 20 * k, c[0] + 56 * k, c[1] + dy * k + 20 * k),
                          fill=GOLD, outline=(120, 78, 20), width=4 * k)
            d.ellipse((c[0] - 56 * k, c[1] - 60 * k, c[0] + 56 * k, c[1] - 18 * k), fill=(250, 214, 120),
                      outline=(120, 78, 20), width=4 * k)
        elif kind == "sword":                      # armies / war
            d.polygon([(c[0], c[1] - 78 * k), (c[0] + 14 * k, c[1] - 56 * k), (c[0] + 14 * k, c[1] + 30 * k),
                       (c[0] - 14 * k, c[1] + 30 * k), (c[0] - 14 * k, c[1] - 56 * k)], fill=CREAM, outline=GOLD)
            d.rectangle((c[0] - 46 * k, c[1] + 30 * k, c[0] + 46 * k, c[1] + 42 * k), fill=GOLD)
            d.rectangle((c[0] - 9 * k, c[1] + 42 * k, c[0] + 9 * k, c[1] + 76 * k), fill=(150, 98, 30))
        elif kind == "land":                       # land / castle
            d.rectangle((c[0] - 60 * k, c[1] - 20 * k, c[0] + 60 * k, c[1] + 60 * k), fill=GOLD)
            for x0 in (-60, -24, 12, 48):
                d.rectangle((c[0] + x0 * k, c[1] - 44 * k, c[0] + (x0 + 14) * k, c[1] - 20 * k), fill=GOLD)
            d.pieslice((c[0] - 20 * k, c[1] + 14 * k, c[0] + 20 * k, c[1] + 60 * k), 180, 360, fill=(30, 22, 14))
            d.rectangle((c[0] - 20 * k, c[1] + 36 * k, c[0] + 20 * k, c[1] + 60 * k), fill=(30, 22, 14))
        elif kind == "scroll":                     # contract / deal
            d.rectangle((c[0] - 48 * k, c[1] - 56 * k, c[0] + 48 * k, c[1] + 56 * k), fill=CREAM, outline=GOLD, width=4 * k)
            for yy in (-30, -10, 10, 30):
                d.line((c[0] - 32 * k, c[1] + yy * k, c[0] + 32 * k, c[1] + yy * k), fill=(150, 120, 80), width=5 * k)
            d.ellipse((c[0] + 14 * k, c[1] + 30 * k, c[0] + 50 * k, c[1] + 66 * k), fill=BLOOD)
        elif kind == "players":                    # people
            for dx, s in ((-36, 0.8), (36, 0.8), (0, 1.0)):
                hx, hy = c[0] + dx * k, c[1] - 26 * k * s
                d.ellipse((hx - 18 * k * s, hy - 18 * k * s, hx + 18 * k * s, hy + 18 * k * s), fill=GOLD)
                d.pieslice((hx - 34 * k * s, hy + 22 * k * s, hx + 34 * k * s, hy + 92 * k * s), 180, 360, fill=GOLD)
        elif kind == "strategy":                   # chess pawn
            d.ellipse((c[0] - 22 * k, c[1] - 66 * k, c[0] + 22 * k, c[1] - 22 * k), fill=GOLD)
            d.polygon([(c[0] - 16 * k, c[1] - 26 * k), (c[0] + 16 * k, c[1] - 26 * k), (c[0] + 34 * k, c[1] + 40 * k),
                       (c[0] - 34 * k, c[1] + 40 * k)], fill=GOLD)
            d.rectangle((c[0] - 50 * k, c[1] + 40 * k, c[0] + 50 * k, c[1] + 62 * k), fill=GOLD)
        elif kind == "payoff":                     # trophy
            d.pieslice((c[0] - 50 * k, c[1] - 90 * k, c[0] + 50 * k, c[1] + 10 * k), 0, 180, fill=GOLD)
            d.rectangle((c[0] - 50 * k, c[1] - 60 * k, c[0] + 50 * k, c[1] - 40 * k), fill=GOLD)
            d.rectangle((c[0] - 10 * k, c[1] + 8 * k, c[0] + 10 * k, c[1] + 40 * k), fill=GOLD)
            d.rectangle((c[0] - 40 * k, c[1] + 40 * k, c[0] + 40 * k, c[1] + 60 * k), fill=GOLD)
        elif kind == "info":                       # eye
            d.chord((c[0] - 70 * k, c[1] - 44 * k, c[0] + 70 * k, c[1] + 44 * k), 0, 360, fill=CREAM, outline=GOLD, width=5 * k)
            d.ellipse((c[0] - 28 * k, c[1] - 28 * k, c[0] + 28 * k, c[1] + 28 * k), fill=(40, 110, 160))
            d.ellipse((c[0] - 12 * k, c[1] - 12 * k, c[0] + 12 * k, c[1] + 12 * k), fill=(10, 10, 10))
    return supersample(draw, (240, 240))


BADGE = {k: _badge(k) for k in ["heart", "house", "hourglass", "coin", "sword", "land", "scroll", "players",
                                "strategy", "payoff", "info"]}


def pop_img(f, t, t_in, im, xy, s0=0.2):
    if t < t_in:
        return
    s = s0 + (1 - s0) * ease_out_back(clamp01((t - t_in) / 0.35), 2.0)
    im2 = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.BICUBIC)
    f.alpha_composite(im2, (round(xy[0] - im2.width / 2), round(xy[1] - im2.height / 2)))


_rng = np.random.default_rng(3)
MOTES = _rng.uniform(0, 1, (46, 4))     # x, y, speed, size


def motes(f, t, color=(255, 214, 140), n=46, alpha=110):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, sp, sz in MOTES[:n]:
        px = (x * W + 40 * math.sin(t * 0.4 + y * 9)) % W
        py = (y * H - t * (14 + 30 * sp)) % H
        r = 1.5 + 3 * sz
        a = int(alpha * (0.5 + 0.5 * math.sin(t * 1.3 + x * 20)))
        d.ellipse((px - r, py - r, px + r, py + r), fill=color + (a,))
    f.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.2)))


def darken(f, k, color=(0, 0, 0)):
    if k <= 0:
        return f
    f.alpha_composite(Image.new("RGBA", (W, H), color + (int(255 * clamp01(k)),)))
    return f


def spotlight(f, k, cx=W / 2, cy=H * 0.55, r=520):
    if k <= 0:
        return
    y, x = np.ogrid[0:H, 0:W]
    m = np.clip(((x - cx) ** 2 / 1.6 + (y - cy) ** 2) ** 0.5 / r - 0.4, 0, 1)
    a = (m * 235 * clamp01(k)).astype(np.uint8)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.putalpha(Image.fromarray(a))
    f.alpha_composite(lay)


SPOT_CACHE = {}


def spot(f, k):
    kk = round(clamp01(k) * 20) / 20
    if kk <= 0:
        return
    if kk not in SPOT_CACHE:
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); spotlight(tmp, kk); SPOT_CACHE[kk] = tmp
    f.alpha_composite(SPOT_CACHE[kk])


def chrome(f, t):
    """Small series tag + watermark (the 'channel furniture')."""
    d = ImageDraw.Draw(f)
    d.rounded_rectangle((40, 36, 360, 86), 10, fill=(14, 12, 10, 170), outline=GOLD + (200,), width=2)
    d.text((200, 61), SERIES_TAG, font=cinzel(24, "Bold"), fill=GOLD, anchor="mm")
    d.text((W - 44, H - 40), "DEEP TIME ACADEMY", font=cinzel(26, "Bold"), fill=GOLD + (150,), anchor="rs")



# ---------------------------------------------------------------- channel sting
# channel sting: particles converge into the wordmark
_P = np.random.default_rng(11).uniform(-1, 1, (260, 3))


def sting_frame(u, end):
    """Channel logo sting. u = seconds since the sting started, end = its length (fades out at the end)."""
    f = Image.new("RGBA", (W, H), (8, 7, 6, 255))
    # warm radial glow
    g = clamp01(u / 0.8)
    if g > 0:
        y, x = np.ogrid[0:H:4, 0:W:4]
        m = np.exp(-(((x - W / 2) / 700) ** 2 + ((y - H / 2) / 330) ** 2)) * 70 * g
        glow = Image.fromarray(np.dstack([m * 1.0, m * 0.62, m * 0.25, m * 2.2]).clip(0, 255).astype(np.uint8), "RGBA")
        f.alpha_composite(glow.resize((W, H), Image.BILINEAR))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    c = ease(clamp01(u / 1.1))
    for px, py, sz in _P:
        x = W / 2 + px * 1100 * (1 - c) + px * 520 * c
        y = H / 2 - 10 + py * 650 * (1 - c) + py * 60 * c
        a = int(220 * (1 - clamp01((u - 1.0) / 0.5)) * clamp01(u / 0.2))
        r = 1.5 + 2.5 * (sz + 1)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 210, 120, a))
    f.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))
    if u > 0.9:
        v = clamp01((u - 0.9) / 0.35)
        gold_text(f, "DEEP TIME ACADEMY", (W / 2, H / 2 - 40), 128, a=v, scale=1.12 - 0.12 * ease(v),
                  shine=clamp01((u - 1.4) / 1.0), spacing=6)
        d = ImageDraw.Draw(f)
        w_ = 560 * ease(clamp01((u - 1.1) / 0.6))
        for sgn in (-1, 1):
            d.line((W / 2 + sgn * 60, H / 2 + 52, W / 2 + sgn * (60 + w_), H / 2 + 52), fill=(190, 30, 30), width=5)
        if u > 1.1:
            d.regular_polygon((W / 2, H / 2 + 52, 16), 4, rotation=45, fill=GOLD)
        if u > 1.5:
            a = int(255 * clamp01((u - 1.5) / 0.4))
            d.text((W / 2, H / 2 + 120), "HISTORY  •  GEOPOLITICS  •  GAME THEORY", font=cinzel(38, "Bold"),
                   fill=CREAM + (a,), anchor="mm")
    # fade out to next scene
    if u > end - 0.45:
        darken(f, (u - (end - 0.45)) / 0.45)
    return f



# ---------------------------------------------------------------- more helpers
def sepia(f, k=0.35):
    a = np.asarray(f.convert("RGB")).astype(np.float32)
    g = a @ np.array([0.30, 0.59, 0.11], np.float32)
    s = np.dstack([g * 1.07 + 12, g * 0.92 + 6, g * 0.72])
    return Image.fromarray(np.clip(a * (1 - k) + s * k, 0, 255).astype(np.uint8)).convert("RGBA")




def chalk_line(d, a, b, frac, color=CHALK, width=7):
    if frac <= 0:
        return
    x = a[0] + (b[0] - a[0]) * frac; y = a[1] + (b[1] - a[1]) * frac
    for off, al in [((0, 0), 230), ((2, -2), 110)]:
        d.line((a[0] + off[0], a[1] + off[1], x + off[0], y + off[1]), fill=color + (al,), width=width)


def person_glyph(d, x, y, color, s=1.0):
    d.ellipse((x - 46 * s, y - 46 * s, x + 46 * s, y + 46 * s), outline=color + (235,), width=6)
    d.ellipse((x - 13 * s, y - 30 * s, x + 13 * s, y - 4 * s), fill=color + (235,))
    d.pieslice((x - 28 * s, y - 2 * s, x + 28 * s, y + 52 * s), 180, 360, fill=color + (235,))




def medal_img():
    def draw(d, k):
        c = 260 * k; R = 200 * k
        d.ellipse((c - R - 14 * k, c - R - 14 * k, c + R + 14 * k, c + R + 14 * k), fill=(120, 78, 20))
        d.ellipse((c - R, c - R, c + R, c + R), fill=(226, 178, 70))
        d.ellipse((c - R + 26 * k, c - R + 26 * k, c + R - 26 * k, c + R - 26 * k), fill=(246, 206, 110),
                  outline=(170, 118, 36), width=6 * k)
        for j in range(24):                                # beaded ring
            ang = 2 * math.pi * j / 24
            bx, by = c + math.cos(ang) * 150 * k, c + math.sin(ang) * 150 * k
            d.ellipse((bx - 9 * k, by - 9 * k, bx + 9 * k, by + 9 * k), fill=(196, 146, 52))
        d.regular_polygon((c, c, 95 * k), 5, rotation=0, fill=(214, 160, 60), outline=(160, 108, 30))
        star = [(c + math.cos(math.radians(-90 + 36 * q)) * (100 if q % 2 == 0 else 42) * k,
                 c + math.sin(math.radians(-90 + 36 * q)) * (100 if q % 2 == 0 else 42) * k) for q in range(10)]
        d.ellipse((c - 105 * k, c - 105 * k, c + 105 * k, c + 105 * k), fill=(240, 196, 96))
        d.polygon(star, fill=(196, 140, 44), outline=(150, 100, 26))
    return supersample(draw, (520, 520), 2)




def arrow(d, x, y, up, color, s=1.0):
    if up:
        pts = [(x, y - 90 * s), (x + 80 * s, y), (x + 34 * s, y), (x + 34 * s, y + 90 * s), (x - 34 * s, y + 90 * s),
               (x - 34 * s, y), (x - 80 * s, y)]
    else:
        pts = [(x, y + 90 * s), (x + 80 * s, y), (x + 34 * s, y), (x + 34 * s, y - 90 * s), (x - 34 * s, y - 90 * s),
               (x - 34 * s, y), (x - 80 * s, y)]
    d.polygon(pts, fill=color, outline=(20, 14, 8))




SYMS = [("♥", (230, 40, 70)), ("$", (240, 200, 60)), ("♦", (230, 60, 200)), ("★", (255, 220, 60)), ("✗", (120, 200, 255))]
CELL = 170


def reel_strip(order):
    im = Image.new("RGBA", (CELL, CELL * len(order)), (250, 244, 230, 255)); d = ImageDraw.Draw(im)
    for n, k in enumerate(order):
        ch, col = SYMS[k]
        d.text((CELL / 2, n * CELL + CELL / 2), ch, font=sym(120), fill=col, anchor="mm", stroke_width=3,
               stroke_fill=(40, 20, 20))
        d.line((0, n * CELL, CELL, n * CELL), fill=(200, 190, 170), width=3)
    return im




# ---------------------------------------------------------------- audio
def tone(freq, dur, decay=3.0, harm=(1, .5, .25, .12), attack=0.004):
    n = int(dur * SR); tt = np.arange(n) / SR
    out = sum(a * np.sin(2 * np.pi * freq * (j + 1) * tt) * np.exp(-tt * decay * (1 + j * 0.8)) for j, a in enumerate(harm))
    return (out * E._env(n, attack, 0.05)).astype(np.float32)


def nf(note):   # midi -> Hz
    return 440 * 2 ** ((note - 69) / 12)




def music(total, mgain=lambda tm: 1.0, dgain=lambda tm: 1.0):
    n = int(total * SR); out = np.zeros(n, np.float32); tt = np.arange(n) / SR
    # low drone (A1 + E2) breathing
    drone = (np.sin(2 * np.pi * nf(33) * tt) + 0.6 * np.sin(2 * np.pi * nf(40) * tt) + 0.3 * np.sin(2 * np.pi * nf(45) * tt))
    drone *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.12 * tt)
    out += 0.18 * drone
    # curious pizzicato motif, A minor, 0.27 s per step
    motif = [57, 60, 64, 62, 60, 59, 60, None, 57, 60, 65, 64, 62, 60, 59, None]
    bass = [45, None, None, None, 41, None, None, None, 43, None, None, None, 40, None, None, None]
    step = 0.27
    k = 0
    while k * step < total:
        tm = k * step
        m = motif[k % 16]; b = bass[k % 16]
        gate = mgain(tm)
        if m and gate > 0.01:
            place(out, tone(nf(m + 12), 0.5, 7.0) * 0.30 * gate, tm)
        if b and gate > 0.01:
            place(out, tone(nf(b), 1.2, 2.2, (1, .4, .1)) * 0.38 * gate, tm)
        k += 1
    out = np.convolve(out, np.ones(6) / 6, "same")
    g = np.array([dgain(x) for x in np.arange(0, total, 0.05)], np.float32)
    g = np.interp(tt, np.arange(0, total, 0.05)[:len(g)], g)
    return out / (np.abs(out).max() + 1e-6) * 0.16 * g




def fx_heartbeat():
    out = np.zeros(int(0.9 * SR), np.float32)
    for st, a in [(0, 1.0), (0.22, 0.7)]:
        n = int(0.25 * SR); tt = np.arange(n) / SR
        out[int(st * SR):int(st * SR) + n] += np.sin(2 * np.pi * (60 - 30 * tt) * tt) * np.exp(-tt * 18) * a * 0.7
    return out


def fx_riser(dur=1.6):
    n = int(dur * SR); k = np.linspace(0, 1, n)
    noise = np.random.default_rng(2).normal(0, 1, n).astype(np.float32)
    hp = noise - np.convolve(noise, np.ones(30) / 30, "same")
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 900 * k ** 2) / SR)
    return ((hp * 0.25 + sweep * 0.2) * k ** 2.2 * 0.5).astype(np.float32)


def fx_shimmer(dur=2.2):
    n = int(dur * SR); tt = np.arange(n) / SR; out = np.zeros(n, np.float32)
    rng = np.random.default_rng(9)
    for f0 in [nf(81), nf(84), nf(88), nf(93), nf(96)]:
        st = rng.uniform(0, 0.4)
        out += np.sin(2 * np.pi * f0 * tt) * np.exp(-np.clip(tt - st, 0, None) * 2.0) * (tt > st)
    return (out * E._env(n, 0.05, 0.4) * 0.05).astype(np.float32)


def fx_chalk(dur=0.35):
    n = int(dur * SR)
    noise = np.random.default_rng(int(dur * 1000)).normal(0, 1, n).astype(np.float32)
    hp = noise - np.convolve(noise, np.ones(8) / 8, "same")
    grain = (np.random.default_rng(5).uniform(0, 1, n) > 0.6).astype(np.float32)
    return (hp * np.convolve(grain, np.ones(200) / 200, "same") * E._env(n, 0.02, 0.08) * 0.12).astype(np.float32)


def fx_hit():
    b = sfx("boom")
    n = int(0.4 * SR); noise = np.random.default_rng(4).normal(0, 1, n) * np.exp(-np.arange(n) / SR * 14) * 0.25
    b[:n] += noise.astype(np.float32)
    return b




# ---------------------------------------------------------------- long-video helpers (added for 10-12 min episodes)
def chapter_card(t, t0, num, title, dur=2.4):
    """Full-frame chapter card: black + gold motes, 'CHAPTER N' in gold, title in cream. Show it in a ~2.5 s gap.
    t0 = when the card starts. Returns a frame. Pair with sound: whoosh at t0-0.3, boom*0.5 + shimmer at t0+0.3."""
    u = t - t0
    f = Image.new("RGBA", (W, H), (8, 7, 6, 255))
    y, x = np.ogrid[0:H:4, 0:W:4]
    m = np.exp(-(((x - W / 2) / 760) ** 2 + ((y - H / 2) / 360) ** 2)) * 60
    f.alpha_composite(Image.fromarray(np.dstack([m, m * 0.62, m * 0.25, m * 2.2]).clip(0, 255).astype(np.uint8),
                                      "RGBA").resize((W, H), Image.BILINEAR))
    motes(f, t, alpha=150)
    v = clamp01(u / 0.35)
    gold_text(f, f"CHAPTER {num}", (W / 2, H / 2 - 70), 72, a=v, scale=1.1 - 0.1 * ease(v), weight="Bold", spacing=8)
    d = ImageDraw.Draw(f)
    w_ = 300 * ease(clamp01((u - 0.2) / 0.5))
    d.line((W / 2 - w_, H / 2 - 12, W / 2 + w_, H / 2 - 12), fill=(190, 30, 30), width=4)
    if u > 0.35:
        a = int(255 * clamp01((u - 0.35) / 0.4))
        d.text((W / 2, H / 2 + 60), title, font=cinzel(62, "Bold"), fill=CREAM + (a,), anchor="mm")
    if u > dur - 0.35:
        darken(f, (u - (dur - 0.35)) / 0.35)
    return f


def payoff_matrix(f, t, t_in, labels=("COOPERATE", "BETRAY"), cells=None, highlight=None, x=W / 2, y=560, size=640):
    """Animated 2x2 game board. cells = {(row, col): ("+3", "+3")} (row player first). highlight = (row, col) to
    glow gold. The board builds cell by cell from t_in (0.25 s apart)."""
    if t < t_in:
        return
    cells = cells or {(0, 0): ("WIN", "WIN"), (0, 1): ("LOSE", "BIG WIN"), (1, 0): ("BIG WIN", "LOSE"), (1, 1): ("LOSE", "LOSE")}
    d = ImageDraw.Draw(f)
    s = size / 2
    k = ease_out_back(clamp01((t - t_in) / 0.4))
    x0, y0 = x - s * k, y - s * k
    d.rounded_rectangle((x0 - 8, y0 - 8, x0 + size * k + 8, y0 + size * k + 8), 18, fill=(20, 14, 8, 230), outline=GOLD, width=5)
    if k < 0.98:
        return
    for (r, c), (a, b) in cells.items():
        ti = t_in + 0.4 + 0.25 * (r * 2 + c)
        if t < ti:
            continue
        cx0, cy0 = x0 + c * s, y0 + r * s
        glow = highlight == (r, c) and int(t * 4) % 2 == 0
        d.rounded_rectangle((cx0 + 10, cy0 + 10, cx0 + s - 10, cy0 + s - 10), 14,
                            fill=(90, 66, 20) if glow else (40, 30, 18), outline=GOLD if glow else (110, 80, 40), width=4)
        d.text((cx0 + s / 2, cy0 + s * 0.38), a, font=font(46), fill=(120, 190, 255), anchor="mm")
        d.text((cx0 + s / 2, cy0 + s * 0.64), b, font=font(46), fill=(255, 130, 150), anchor="mm")
    for i, lab in enumerate(labels):                     # row labels (left) and column labels (top)
        d.text((x0 - 24, y0 + s * (i + 0.5)), lab, font=font(40), fill=(120, 190, 255), anchor="rm")
        d.text((x0 + s * (i + 0.5), y0 - 30), lab, font=font(40), fill=(255, 130, 150), anchor="mm")


def progress_bar(f, frac, x=W / 2, y=930, w=1200, mark=None, label_txt=None):
    """Gold progress bar (0..1). mark = fraction to draw a red marker at (e.g. 0.37 for the 37% rule)."""
    d = ImageDraw.Draw(f)
    d.rounded_rectangle((x - w / 2, y - 26, x + w / 2, y + 26), 26, fill=(20, 14, 8, 220), outline=GOLD, width=4)
    if frac > 0:
        d.rounded_rectangle((x - w / 2 + 6, y - 20, x - w / 2 + 6 + (w - 12) * clamp01(frac), y + 20), 20, fill=GOLD)
    if mark is not None:
        mx = x - w / 2 + w * mark
        d.line((mx, y - 46, mx, y + 46), fill=(220, 40, 40), width=6)
        if label_txt:
            d.text((mx, y - 70), label_txt, font=font(48), fill=CREAM, anchor="mm", stroke_width=4, stroke_fill=(30, 20, 10))
