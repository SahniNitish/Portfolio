"""Deep Time Academy, Game Theory #1: "The Dating Game" (first-minute draft, 16:9).

    KOKORO_VOICE=am_michael KOKORO_SPEED=0.95 python tools/tts.py deeptime/ep01-dating-game   # draft voice
    FISH_AUDIO_API_KEY=... FISH_VOICE_ID=... python tools/tts.py deeptime/ep01-dating-game     # final voice
    python tools/preview.py deeptime/ep01-dating-game        # contact sheet
    python deeptime/ep01-dating-game/episode.py              # render -> dating_game_v1.mp4

Look: flat 2D cartoon "animated history" style. Characters are green-screen cut-outs that slide in, land,
breathe and react over separate backgrounds; maps, chalk diagrams, counters, medal and slot machine are
drawn in code. Gold Cinzel titles match the channel banner.
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import *  # noqa: E402,F401,F403
import engine as E    # noqa: E402

p = lambda *a: os.path.join(HERE, *a)
FONTS = os.path.join(E.ROOT, "assets", "fonts")
random.seed(7)

GOLD, GOLD_D, CREAM, NAVY = (232, 190, 96), (150, 98, 30), (250, 240, 215), (14, 20, 38)
BLOOD, TEAL, CHALK = (196, 32, 40), (40, 170, 150), (238, 238, 228)

# ---------------------------------------------------------------- voice + timeline
N = len([l for l in open(p("lines.txt")) if l.strip()])
os.makedirs(p("audio", "clean"), exist_ok=True)
for i in range(1, N + 1):
    src, dst = p("audio", f"l{i}.wav"), p("audio", "clean", f"l{i}.wav")
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        clean_voice(src, dst)

GAPS = [0.45] * N
for i, g in {2: 0.5, 3: 0.6, 4: 4.6, 6: 0.4, 8: 0.6, 9: 0.7, 10: 0.5, 11: 0.6, 12: 0.5, 13: 3.6}.items():
    GAPS[i] = g
TL = Timeline([p("audio", "clean", f"l{i}.wav") for i in range(1, N + 1)], GAPS, lead=1.2)
L, END, TOTAL = TL.L, TL.end, TL.total
STING = END(4) + 0.9            # channel logo sting starts inside the long gap after the title line


def seg(t, i, j=None):
    j = i if j is None else j
    return clamp01((t - L(i)) / (END(j) - L(i)))


def at(i, frac):                # time at a fraction of line i's voice
    return L(i) + frac * (END(i) - L(i))


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


# ---------------------------------------------------------------- art
BG = {n: load_bg(p("img", n + ".png")) for n in ["bg_map", "bg_city", "bg_stage", "bg_office"]}
CUT = {n: key_green(p("img", n + ".png")) for n in ["man_curious", "man_shocked", "woman_confident",
                                                     "woman_phone", "professors"]}
_scaled = {}


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
    return supersample(draw, (240, 240))


BADGE = {k: _badge(k) for k in ["heart", "house", "hourglass"]}


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
    d.text((200, 61), "GAME THEORY  ·  EP 1", font=cinzel(24, "Bold"), fill=GOLD, anchor="mm")
    d.text((W - 44, H - 40), "DEEP TIME ACADEMY", font=cinzel(26, "Bold"), fill=GOLD + (150,), anchor="rs")


# ---------------------------------------------------------------- scenes
LAND = [(0.20, 0.33), (0.25, 0.40), (0.16, 0.28), (0.30, 0.62), (0.33, 0.72), (0.49, 0.30), (0.53, 0.26),
        (0.52, 0.52), (0.56, 0.62), (0.62, 0.30), (0.70, 0.34), (0.78, 0.38), (0.66, 0.46), (0.74, 0.50),
        (0.86, 0.72), (0.82, 0.30), (0.46, 0.40), (0.58, 0.44), (0.22, 0.48), (0.37, 0.68)]
HEART_T = sorted(_rng.uniform(0, 1, len(LAND)) ** 0.8)


def sc_map(t):            # line 1
    u = clamp01((t - 0.0) / (END(0) + 0.4))
    f = cam(BG["bg_map"], 0.5 + 0.03 * u, 0.48, 1.0 + 0.12 * ease(u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    z = 1.0 + 0.12 * ease(u)
    for (x, y), ht in zip(LAND, HEART_T):
        t_in = at(0, 0.05 + 0.85 * ht)
        if t < t_in:
            continue
        s = ease_out_back(clamp01((t - t_in) / 0.3), 2.5)
        px = (x - 0.5 - 0.03 * u) * W * z + W / 2; py = (y - 0.48) * H * z + H / 2
        pulse = 1 + 0.1 * math.sin(t * 6 + x * 30)
        ring = clamp01((t - t_in) / 1.2)
        if ring < 1:
            rr = 20 + 70 * ring
            d.ellipse((px - rr, py - rr, px + rr, py + rr), outline=BLOOD + (int(200 * (1 - ring)),), width=4)
        d.polygon(heart_pts(px, py, 22 * s * pulse), fill=BLOOD, outline=(255, 235, 220))
    f.alpha_composite(lay)
    label(f, t, at(0, 0.12), "EVERY NIGHT", (W / 2, 140), bg=NAVY, fg=GOLD, size=64)
    return f


def sc_city(t):           # line 2
    u = seg(t, 1)
    f = cam(BG["bg_city"], 0.42 + 0.16 * u, 0.5, 1.15)
    motes(f, t, (255, 240, 180), 30, 80)
    char(f, "man_curious", t, L(1) - 0.1, lerp(260, 620, ease(u)), 1060, 640, walk=u < 0.8)
    label(f, t, at(1, 0.35), "NOBODY SIGNED UP FOR THIS", (1260, 170), bg=CREAM, size=52, angle=3)
    return f


def stage(t, push=0.0, cx=0.5, cy=0.55):
    return cam(BG["bg_stage"], cx, cy, 1.0 + push)


def sc_rules(t):          # line 3
    u = seg(t, 2)
    f = stage(t, 0.06 * u)
    motes(f, t)
    char(f, "man_curious", t, L(2) - 0.3, 470, 1020, 720, enter="left")
    char(f, "woman_confident", t, L(2) + 0.2, 1450, 1020, 730, enter="right", phase=1.3)
    label(f, t, at(2, 0.05), "NO RULEBOOK", (960, 260), bg=CREAM, size=56, angle=-4)
    label(f, t, at(2, 0.28), "NO REFEREE", (960, 400), bg=CREAM, size=56, angle=3)
    if t > at(2, 0.55):                                     # scoreboard drops in
        k = ease_out_back(clamp01((t - at(2, 0.55)) / 0.4))
        d = ImageDraw.Draw(f)
        y = -120 + 220 * k
        d.rounded_rectangle((760, y - 70, 1160, y + 70), 16, fill=(18, 14, 10), outline=GOLD, width=5)
        d.text((960, y - 38), "SCORE", font=cinzel(28, "Bold"), fill=GOLD, anchor="mm")
        q = "?" if int(t * 8) % 2 else "¿"
        d.text((960, y + 18), f"{'?'}  :  {'?'}", font=font(70), fill=(255, 80, 70), anchor="mm")
    return f


def sc_stakes(t):         # line 4
    u = seg(t, 3)
    f = stage(t, 0.06 + 0.1 * ease(u), cy=0.6)
    darken(f, 0.25 * u)
    motes(f, t)
    char(f, "man_curious", t, -10, 470, 1020, 720, phase=0.0)
    char(f, "woman_confident", t, -10, 1450, 1020, 730, phase=1.3)
    for kind, xf, name, x in [("heart", 0.22, "HAPPINESS", 600), ("house", 0.48, "FAMILY", 960),
                              ("hourglass", 0.72, "FUTURE", 1320)]:
        pop_img(f, t, at(3, xf), BADGE[kind], (x, 360 + 8 * math.sin(t * 2 + x)))
        label(f, t, at(3, xf) + 0.1, name, (x, 520), bg=(30, 22, 14), fg=GOLD, size=44)
    return f


def sc_title(t):          # line 5 + title hold
    k = clamp01((t - L(4)) / 0.8)
    f = stage(t, 0.16 + 0.05 * clamp01((t - L(4)) / 4), cy=0.6)
    darken(f, 0.25 + 0.25 * k)
    spot(f, k)
    char(f, "man_curious", t, -10, 470 + 120 * ease(k), 1020, 720)
    char(f, "woman_confident", t, -10, 1450 - 120 * ease(k), 1020, 730, phase=1.3)
    motes(f, t, alpha=150)
    t0 = at(4, 0.45)
    if t > t0:
        v = clamp01((t - t0) / 0.35)
        s = 1.6 - 0.6 * ease(v)
        gold_text(f, "THE DATING GAME", (W / 2, 330), 150, a=v, scale=s, shine=clamp01((t - t0 - 0.5) / 1.1))
        if t > t0 + 0.5:
            a = clamp01((t - t0 - 0.5) / 0.5)
            ImageDraw.Draw(f).text((W / 2, 455), "A  GAME  THEORY  STORY", font=cinzel(40, "Bold"),
                                   fill=CREAM + (int(255 * a),), anchor="mm")
    return f


# channel sting: particles converge into the wordmark
_P = np.random.default_rng(11).uniform(-1, 1, (260, 3))


def sc_sting(t):
    u = t - STING
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
    end = L(5) - STING
    if u > end - 0.45:
        darken(f, (u - (end - 0.45)) / 0.45)
    return f


def sc_strange(t):        # line 6
    u = seg(t, 5)
    f = stage(t, 0.1 + 0.08 * u)
    darken(f, 0.15)
    motes(f, t)
    char(f, "man_curious", t, L(5) - 0.2, 960, 1030, 780, enter="bottom")
    if t > at(5, 0.35):
        v = ease_out_back(clamp01((t - at(5, 0.35)) / 0.4), 2.5)
        d = ImageDraw.Draw(f)
        for i, (x, y, s) in enumerate([(1240, 250, 1.0), (680, 330, 0.6), (1390, 470, 0.45)]):
            sz = int(170 * s * v)
            if sz > 4:
                yy = y + 10 * math.sin(t * 3 + i)
                d.text((x, yy), "?", font=font(sz), fill=GOLD, anchor="mm", stroke_width=6, stroke_fill=(40, 26, 10))
    return f


def sepia(f, k=0.35):
    a = np.asarray(f.convert("RGB")).astype(np.float32)
    g = a @ np.array([0.30, 0.59, 0.11], np.float32)
    s = np.dstack([g * 1.07 + 12, g * 0.92 + 6, g * 0.72])
    return Image.fromarray(np.clip(a * (1 - k) + s * k, 0, 255).astype(np.uint8)).convert("RGBA")


def sc_years(t):          # line 7: the year counter rolls back
    u = seg(t, 6)
    f = sepia(cam(BG["bg_office"], 0.5, 0.5, 1.0 + 0.08 * u), 0.25 + 0.35 * u)
    darken(f, 0.35)
    v = ease(clamp01((u - 0.15) / 0.65))
    year = round(2026 - 64 * v)
    d = ImageDraw.Draw(f)
    d.rounded_rectangle((W / 2 - 330, H / 2 - 150, W / 2 + 330, H / 2 + 120), 26, fill=(20, 14, 8, 215),
                        outline=GOLD, width=6)
    jitter = 0 if v >= 1 or v <= 0 else random.uniform(-3, 3)
    gold_text(f, str(year), (W / 2 + jitter, H / 2 - 20), 190)
    if u > 0.85:
        label(f, t, at(6, 0.85), "60+ YEARS AGO", (W / 2, H / 2 + 180), bg=BLOOD, fg=CREAM, size=54)
    return f


def sc_profs(t):          # line 8
    u = seg(t, 7)
    f = sepia(cam(BG["bg_office"], 0.45 + 0.05 * u, 0.55, 1.12), 0.2)
    motes(f, t, (255, 230, 170), 20, 60)
    char(f, "professors", t, L(7) - 0.2, 760, 1060, 900, enter="right")
    label(f, t, at(7, 0.0), "1962", (1470, 200), bg=(30, 22, 14), fg=GOLD, size=86, face="cinzel")
    label(f, t, at(7, 0.5), "DAVID GALE", (250, 520), bg=CREAM, size=46, angle=-3)
    label(f, t, at(7, 0.62), "LLOYD SHAPLEY", (1330, 600), bg=CREAM, size=46, angle=3)
    return f


MEN_Y = [300, 460, 620, 780]
PAIRS = [(0, 2), (1, 0), (2, 3), (3, 1)]
TRIES = [(0, 0), (1, 0), (2, 1), (3, 2)]       # first, unstable attempts (crossed out)


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


def board(t, zoom_extra=0.0):
    return cam(BG["bg_office"], 0.598, 0.282, 2.45 + zoom_extra)


def sc_chalk(t):          # line 9: stable matching on the chalkboard
    u = seg(t, 8)
    f = board(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    LX, RX = 560, 1360
    for i, y in enumerate(MEN_Y):
        if u > 0.02 + 0.04 * i:
            person_glyph(d, LX, y, (120, 190, 255))
        if u > 0.1 + 0.04 * i:
            person_glyph(d, RX, y, (255, 130, 150))
    for n, (a, b) in enumerate(TRIES):               # messy first attempts, then crossed out
        st = 0.25 + 0.06 * n
        fr = clamp01((u - st) / 0.07)
        if u < 0.62:
            chalk_line(d, (LX + 55, MEN_Y[a]), (RX - 55, MEN_Y[b]), fr, (230, 230, 210), 5)
        if u > 0.5 and u < 0.62:
            mx, my = (LX + RX) / 2, (MEN_Y[a] + MEN_Y[b]) / 2
            d.line((mx - 26, my - 26, mx + 26, my + 26), fill=(255, 90, 80, 255), width=8)
            d.line((mx - 26, my + 26, mx + 26, my - 26), fill=(255, 90, 80, 255), width=8)
    for n, (a, b) in enumerate(PAIRS):               # the stable pairing
        st = 0.64 + 0.07 * n
        chalk_line(d, (LX + 55, MEN_Y[a]), (RX - 55, MEN_Y[b]), clamp01((u - st) / 0.08), (255, 236, 150), 8)
    f.alpha_composite(lay)
    label(f, t, at(8, 0.02), "EVERYONE RANKS EVERYONE", (W / 2, 150), bg=CREAM, size=46)
    return f


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


MEDAL = medal_img()


def sc_nobel(t):          # line 10
    u = seg(t, 9)
    t_med = at(9, 0.3)
    if t < t_med:
        f = board(t)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for a, b in PAIRS:
            chalk_line(d, (615, MEN_Y[a]), (1305, MEN_Y[b]), 1, (255, 236, 150), 8)
        for y in MEN_Y:
            person_glyph(d, 560, y, (120, 190, 255)); person_glyph(d, 1360, y, (255, 130, 150))
        f.alpha_composite(lay)
        label(f, t, L(9) + 0.2, "STABLE!", (W / 2, 540), bg=(40, 150, 90), fg=(255, 255, 255), size=96, angle=-6)
        return f
    v = clamp01((t - t_med) / 0.7)
    f = Image.new("RGBA", (W, H), (16, 12, 30, 255))
    y_, x_ = np.ogrid[0:H:4, 0:W:4]
    m = np.exp(-(((x_ - W / 2) / 650) ** 2 + ((y_ - 470) / 420) ** 2)) * 120
    f.alpha_composite(Image.fromarray(np.dstack([m * 0.9, m * 0.62, m * 0.3, m * 1.8]).clip(0, 255).astype(np.uint8),
                                      "RGBA").resize((W, H), Image.BILINEAR))
    # rays
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for r in range(14):
        ang = r * math.pi / 7 + t * 0.15
        d.polygon([(W / 2, 450), (W / 2 + 1400 * math.cos(ang - 0.05), 450 + 1400 * math.sin(ang - 0.05)),
                   (W / 2 + 1400 * math.cos(ang + 0.05), 450 + 1400 * math.sin(ang + 0.05))],
                  fill=(255, 220, 140, int(28 * v)))
    f.alpha_composite(lay)
    flip = abs(math.cos((1 - ease(v)) * math.pi * 1.5))   # coin-flip spin in
    s = 0.4 + 0.6 * ease_out_back(v)
    med = MEDAL.resize((max(2, round(520 * s * max(flip, 0.04))), round(520 * s)), Image.BICUBIC)
    # ribbon
    d = ImageDraw.Draw(f)
    d.polygon([(W / 2 - 120, -10), (W / 2 - 10, 260), (W / 2 + 10, 260), (W / 2 + 120, -10)], fill=(30, 60, 150))
    d.polygon([(W / 2 - 40, -10), (W / 2, 240), (W / 2 + 40, -10)], fill=(200, 40, 50))
    f.alpha_composite(med, (round(W / 2 - med.width / 2), round(450 - med.height / 2)))
    motes(f, t, (255, 220, 150), 46, 160)
    if t > t_med + 0.6:
        gold_text(f, "NOBEL PRIZE", (W / 2, 820), 96, a=clamp01((t - t_med - 0.6) / 0.4),
                  shine=clamp01((t - t_med - 0.9) / 1.0))
        label(f, t, t_med + 1.0, "ECONOMICS  ·  2012", (W / 2, 930), bg=(30, 22, 14), fg=GOLD, size=44)
    return f


def sc_twist(t):          # line 11
    u = seg(t, 10)
    hit = at(10, 0.72)
    sh = 14 * (1 - clamp01((t - hit) / 0.4)) if t > hit else 0
    f = stage(t, 0.2 + 0.1 * u, cy=0.62)
    f = darken(f, 0.35, (60, 0, 0))
    spot(f, 0.7)
    if sh:
        f = cam(f, 0.5, 0.5, 1.0, sh)
    char(f, "man_shocked", t, L(10) - 0.2, 960, 1050, 800, enter="pop")
    if t > hit:
        label(f, t, hit, "THE TWIST", (W / 2, 220), bg=BLOOD, fg=CREAM, size=110, angle=-5)
    return f


def arrow(d, x, y, up, color, s=1.0):
    if up:
        pts = [(x, y - 90 * s), (x + 80 * s, y), (x + 34 * s, y), (x + 34 * s, y + 90 * s), (x - 34 * s, y + 90 * s),
               (x - 34 * s, y), (x - 80 * s, y)]
    else:
        pts = [(x, y + 90 * s), (x + 80 * s, y), (x + 34 * s, y), (x + 34 * s, y - 90 * s), (x - 34 * s, y - 90 * s),
               (x - 34 * s, y), (x - 80 * s, y)]
    d.polygon(pts, fill=color, outline=(20, 14, 8))


def sc_firstmove(t):      # line 12
    u = seg(t, 11)
    f = blurred(stage(t, 0.1), 10, 0.55)
    char(f, "man_curious", t, L(11) - 0.3, 330, 1060, 700, enter="left")
    char(f, "woman_confident", t, at(11, 0.48), 1590, 1060, 710, enter="right", phase=1.1)
    d = ImageDraw.Draw(f)
    for side, t_in, title, res, col, up in [(-1, at(11, 0.02), "MAKES THE FIRST MOVE", "BEST MATCH", (60, 180, 100), True),
                                            (1, at(11, 0.55), "WAITS", "WORST MATCH", (210, 50, 50), False)]:
        if t < t_in:
            continue
        x = W / 2 + side * 260
        k = ease_out_back(clamp01((t - t_in) / 0.4))
        y0 = 260 + (1 - k) * 600
        d.rounded_rectangle((x - 240, y0, x + 240, y0 + 520), 22, fill=(250, 240, 215, 235), outline=(40, 26, 12), width=6)
        d.text((x, y0 + 60), title, font=font(42 if len(title) > 10 else 60), fill=(40, 26, 12), anchor="mm")
        if t > t_in + 0.9:
            kk = ease_out_back(clamp01((t - t_in - 0.9) / 0.35))
            arrow(d, x, y0 + 250, up, col, kk)
            d.text((x, y0 + 440), res, font=font(64), fill=col, anchor="mm")
    return f


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


STRIPS = [reel_strip([0, 1, 2, 3, 4, 1, 3, 2] * 3), reel_strip([2, 3, 0, 4, 1, 2, 4, 3] * 3),
          reel_strip([4, 2, 3, 1, 0, 3, 2, 4] * 3)]
STOP_IDX = [8, 10, 12]          # final symbols: heart, heart, $ (cells at those indices)


def sc_casino(t):         # line 13
    u = seg(t, 12)
    f = cam(BG["bg_city"], 0.55, 0.45, 1.35)
    f = darken(f, 0.45, (20, 0, 30))
    char(f, "woman_phone", t, L(12) - 0.2, 430, 1060, 760, enter="left")
    # phone glow
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse((330, 330, 530, 530), fill=(255, 60, 160, 70))
    f.alpha_composite(gl.filter(ImageFilter.GaussianBlur(40)))
    t_in = at(12, 0.05)
    if t > t_in:
        k = ease_out_back(clamp01((t - t_in) / 0.45))
        x0, y0 = 860 + (1 - k) * 900, 250
        wbox, hbox = 820, 470
        d = ImageDraw.Draw(f)
        neon = (255, 60, 170) if int(t * 6) % 7 else (255, 150, 220)
        d.rounded_rectangle((x0, y0, x0 + wbox, y0 + hbox), 40, fill=(60, 10, 40), outline=neon, width=10)
        for b in range(18):                               # chasing bulbs
            bx = x0 + 40 + b * (wbox - 80) / 17
            on = (b + int(t * 10)) % 3 == 0
            for by in (y0 + 22, y0 + hbox - 22):
                d.ellipse((bx - 9, by - 9, bx + 9, by + 9), fill=(255, 230, 120) if on else (120, 80, 40))
        for r in range(3):
            stop_t = at(12, 0.5 + 0.12 * r)
            if t < stop_t:
                off = ((t - t_in) * 2600 + r * 400) % (CELL * 16)
            else:
                bounce = math.sin(clamp01((t - stop_t) / 0.25) * math.pi) * 18
                off = (STOP_IDX[r] - 1) * CELL - bounce
            strip = STRIPS[r].crop((0, int(off), CELL, int(off) + CELL * 2))
            strip = strip.resize((210, 340))
            rx = x0 + 70 + r * 235
            f.alpha_composite(strip, (int(rx), y0 + 65))
            d.rectangle((rx, y0 + 65, rx + 210, y0 + 405), outline=(40, 10, 30), width=6)
        d.line((x0 + 50, y0 + 235, x0 + wbox - 50, y0 + 235), fill=(255, 60, 60, 160), width=3)
    label(f, t, at(12, 0.45), "LOVE STORY?", (1270, 820), bg=CREAM, size=60, angle=-3, t_out=at(12, 0.78))
    if t > at(12, 0.8):
        a = 1.0 if int(t * 12) % 5 else 0.5
        d = ImageDraw.Draw(f)
        d.text((1270, 820), "CASINO", font=font(130), fill=(255, 90, 200, int(255 * a)), anchor="mm",
               stroke_width=6, stroke_fill=(90, 0, 60))
    return f


def sc_finale(t):         # line 14 + end card
    u = seg(t, 13)
    f = stage(t, 0.05 + 0.15 * ease(u), cy=0.6)
    motes(f, t)
    char(f, "man_curious", t, L(13) - 0.3, 470, 1030, 720, enter="left")
    char(f, "woman_confident", t, L(13) + 0.1, 1450, 1030, 730, enter="right", phase=1.3)
    t0 = at(13, 0.6)
    if t > t0:
        v = clamp01((t - t0) / 0.4)
        darken(f, 0.35 * v)
        gold_text(f, "GAME THEORY", (W / 2, 300), 170, a=v, scale=1.4 - 0.4 * ease(v), shine=clamp01((t - t0 - 0.5) / 1.0))
    if t > END(13) + 0.5:
        a = clamp01((t - END(13) - 0.5) / 0.5)
        ImageDraw.Draw(f).text((W / 2, 440), "EPISODE 1  ·  THE DATING GAME", font=cinzel(46, "Bold"),
                               fill=CREAM + (int(255 * a),), anchor="mm")
    if t > TOTAL - 1.0:
        darken(f, (t - (TOTAL - 1.0)) / 1.0)
    return f


SCENES = [(0.0, sc_map, True), (L(1) - 0.15, sc_city, True), (L(2) - 0.3, sc_rules, True),
          (L(3) - 0.1, sc_stakes, True), (L(4) - 0.2, sc_title, False), (STING, sc_sting, False),
          (L(5) - 0.05, sc_strange, True), (L(6) - 0.1, sc_years, True), (L(7) - 0.2, sc_profs, True),
          (L(8) - 0.2, sc_chalk, True), (L(9) - 0.1, sc_nobel, True), (L(10) - 0.15, sc_twist, True),
          (L(11) - 0.3, sc_firstmove, True), (L(12) - 0.2, sc_casino, True), (L(13) - 0.3, sc_finale, True)]
XF = 0.3   # crossfade length


def frame_at(t):
    k = max(i for i, (s, _, _) in enumerate(SCENES) if s <= t) if t >= 0 else 0
    s, fn, ch = SCENES[k]
    f = fn(t)
    if k > 0 and t - s < XF and fn is not sc_sting:
        prev = SCENES[k - 1][1](t)
        f = Image.blend(prev.convert("RGB"), f.convert("RGB"), ease((t - s) / XF)).convert("RGBA")
    if ch:
        chrome(f, t)
    return f


# ---------------------------------------------------------------- audio
def tone(freq, dur, decay=3.0, harm=(1, .5, .25, .12), attack=0.004):
    n = int(dur * SR); tt = np.arange(n) / SR
    out = sum(a * np.sin(2 * np.pi * freq * (j + 1) * tt) * np.exp(-tt * decay * (1 + j * 0.8)) for j, a in enumerate(harm))
    return (out * E._env(n, attack, 0.05)).astype(np.float32)


def nf(note):   # midi -> Hz
    return 440 * 2 ** ((note - 69) / 12)


def music(total):
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


def mgain(tm):        # pizzicato on/off by section
    if tm < L(2): return 0.0
    if tm < L(4): return 0.7
    if tm < L(5): return 0.0
    if L(10) <= tm < L(11): return 0.0
    return 1.0


def dgain(tm):        # overall bed level
    if STING - 0.2 < tm < L(5): return 0.35
    return 1.0


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


def build_audio():
    voice = TL.voice_track()
    fx = np.zeros_like(voice)
    mus = music(TOTAL)[:len(voice)]
    # scene whooshes
    for s, fn, _ in SCENES[1:]:
        if fn not in (sc_sting,):
            place(fx, sfx("whoosh") * 0.35, s - 0.35)
    # map hearts
    for ht in HEART_T:
        place(fx, sfx("pop") * 0.35, at(0, 0.05 + 0.85 * ht))
    place(fx, sfx("pop"), at(0, 0.12))
    place(fx, sfx("pop"), at(1, 0.35))
    for fr in (0.05, 0.28):
        place(fx, sfx("pop"), at(2, fr))
    place(fx, sfx("tick") * 2, at(2, 0.55)); place(fx, sfx("coin"), at(2, 0.6))
    for fr in (0.22, 0.48, 0.72):
        place(fx, fx_heartbeat(), at(3, fr)); place(fx, sfx("pop") * 0.6, at(3, fr))
    place(fx, fx_riser(1.4), at(4, 0.45) - 1.4)
    place(fx, fx_hit() * 1.2, at(4, 0.45)); place(fx, fx_shimmer(), at(4, 0.45) + 0.4)
    # sting
    place(fx, fx_riser(1.0) * 0.8, STING); place(fx, sfx("boom") * 1.1, STING + 0.9); place(fx, fx_shimmer(2.6) * 1.5, STING + 1.1)
    place(fx, sfx("pop"), at(5, 0.35))
    # year counter ticks
    for k in range(26):
        place(fx, sfx("tick") * 1.4, at(6, 0.15 + 0.65 * (k / 25) ** 0.6))
    place(fx, sfx("boom") * 0.5, at(6, 0.82)); place(fx, sfx("pop"), at(6, 0.85))
    place(fx, sfx("pop"), at(7, 0.0)); place(fx, sfx("pop"), at(7, 0.5)); place(fx, sfx("pop"), at(7, 0.62))
    # chalk
    for n_ in range(4):
        place(fx, fx_chalk(0.2), at(8, 0.25 + 0.06 * n_)); place(fx, fx_chalk(0.3), at(8, 0.64 + 0.07 * n_))
    place(fx, sfx("screech") * 0.4, at(8, 0.5))
    place(fx, sfx("coin") * 1.5, L(9) + 0.2); place(fx, sfx("pop"), L(9) + 0.2)
    place(fx, sfx("whoosh") * 0.5, at(9, 0.3)); place(fx, fx_shimmer(2.6) * 1.8, at(9, 0.3) + 0.3)
    place(fx, sfx("boom") * 0.6, at(9, 0.3) + 0.6)
    place(fx, fx_hit() * 1.2, at(10, 0.72))
    place(fx, sfx("pop"), at(11, 0.02)); place(fx, sfx("coin"), at(11, 0.02) + 0.9)
    place(fx, sfx("pop"), at(11, 0.55)); place(fx, sfx("boom") * 0.4, at(11, 0.55) + 0.9)
    # casino reels
    for k in range(40):
        tk = at(12, 0.05) + k * 0.09
        if tk < at(12, 0.74):
            place(fx, sfx("tick") * 0.9, tk)
    for r in range(3):
        place(fx, sfx("pop") * 0.8, at(12, 0.5 + 0.12 * r))
    for k in range(6):
        place(fx, sfx("coin") * 0.9, at(12, 0.8) + k * 0.08)
    place(fx, fx_riser(1.2) * 0.6, at(13, 0.6) - 1.2); place(fx, fx_hit(), at(13, 0.6)); place(fx, fx_shimmer(3.0) * 1.4, at(13, 0.6) + 0.3)
    out = p("_mix.wav")
    finish_audio(voice, mus, fx, out, HERE)
    return out


if __name__ == "__main__":
    wav = build_audio()
    out = p("dating_game_v1.mp4")
    render(frame_at, TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
