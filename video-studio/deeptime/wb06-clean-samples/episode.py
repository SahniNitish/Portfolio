"""Two 15-second clean samples (9:16, 1080x1920) of the same hook: "Why does school feel pointless?"
  A  FLAT CLEAN   warm white paper, flat colour shapes without outlines, round mascot "Pip", dark captions with a blue highlight
  B  NEON KINETIC deep navy, big kinetic words in the centre with neon glow, glowing line icons, thin progress bar
Original 29-word script, Gemini TTS voice Bodi (audio/voice.wav), wb01 music + sfx. No outlines/sketch look on purpose: "something new, clean".

    python deeptime/wb06-clean-samples/episode.py        # renders sample_a_flat.mp4 and sample_b_neon.mp4 (about 2 min)
"""
import importlib.util, json, math, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import Timeline, finish_audio, place, FPS  # noqa: E402

_spec = importlib.util.spec_from_file_location("wb04", os.path.join(HERE, "..", "wb04-map-reel", "episode.py"))   # reuse sprite helpers, fonts, sfx
w4 = importlib.util.module_from_spec(_spec); sys.modules["wb04"] = w4; _spec.loader.exec_module(w4)
font, canvas, done, el, rr, pg, ln, put, pop, ease, clamp01, lerp, mix = w4.font, w4.canvas, w4.done, w4.el, w4.rr, w4.pg, w4.ln, w4.put, w4.pop, w4.ease, w4.clamp01, w4.lerp, w4.mix
ANTON = w4.ANTON
wb = w4.wb
p = lambda *a: os.path.join(HERE, *a)
W, H = 1080, 1920
TOTAL = 15.0
LEAD = 0.5
WORDS = [(w, s + LEAD, e + LEAD) for w, s, e in json.load(open(p("words.json")))]

# ---- sentences (split at . and ?)
SENT, cur = [], []
for w in WORDS:
    cur.append(w)
    if w[0][-1] in ".?":
        SENT.append((cur[0][1], cur[-1][2], cur)); cur = []
if cur:
    SENT.append((cur[0][1], cur[-1][2], cur))
B = [0.0, SENT[1][0] - 0.2, SENT[2][0] - 0.2, SENT[3][0] - 0.2, TOTAL]       # scene boundaries (4 scenes, one per sentence)
SCN = lambda t: max(i for i in range(4) if t >= B[i])
LOC = lambda t: (t - B[SCN(t)])                                              # seconds into the scene


def chunks():
    out = []
    for s0, s1, ws in SENT:
        cur = []
        for i, wd in enumerate(ws):
            cur.append(wd)
            if len(cur) >= 3 or wd[0][-1] in ".,?!" or (i + 1 < len(ws) and ws[i + 1][1] - wd[2] > 0.3):
                out.append(cur); cur = []
        if cur:
            out.append(cur)
    return out
CH = chunks()
KEY = {"pointless?", "grades,", "learning.", "chase", "answer.", "reward", "changes."}


def chunk_at(t):
    for i, ch in enumerate(CH):
        t0 = ch[0][1] - 0.03
        nxt = CH[i + 1][0][1] - 0.03 if i + 1 < len(CH) else 1e9
        t1 = nxt if nxt - ch[-1][2] < 0.6 else ch[-1][2] + 0.3
        if t0 <= t < t1:
            return ch, t0
    return None, 0


# =============================================================== STYLE A: flat clean
PB, INKA, BLUE, CORAL, MINT, YEL, LIL, SKINA = (249, 246, 239), (38, 44, 64), (62, 116, 246), (255, 110, 92), (60, 200, 150), (255, 200, 70), (150, 120, 255), (255, 214, 170)


def mascot(mood="smile", arms="down", legs=0.0, w=1, tilt=0):
    key = (mood, arms, round(legs * 4) / 4)
    if key in _mc:
        return _mc[key]
    cw, ch = 520, 700
    im, d = canvas(cw, ch)
    hip = [(215, 590), (305, 590)]
    for k, (hx, hy) in enumerate(hip):
        sw = math.sin(legs * math.pi * 2 + k * math.pi) * 60 if legs else 0
        ln(d, [(hx, hy), (hx + sw, 660)], 38, INKA)
        el(d, hx + sw + (14 if sw >= 0 else -14) * 0 + 12, 668, 36, 20, INKA, 0)
    rr(d, 160, 380, 360, 610, 80, BLUE, 0)
    rr(d, 190, 405, 330, 440, 17, (255, 255, 255), 0) if False else None
    sh = ((176, 440), (344, 440))
    hands = {"down": ((150, 580), (370, 580)), "shrug": ((70, 400), (450, 400)), "run": ((120, 500), (400, 380)), "cheer": ((90, 190), (430, 190)),
             "point": ((110, 560), (470, 430))}[arms]
    for s_, h_ in zip(sh, hands):
        ln(d, [s_, h_], 46, BLUE); el(d, h_[0], h_[1], 30, 30, SKINA, 0)
    el(d, 260, 240, 150, 146, SKINA, 0)
    for dx in (-60, -10, 40):                                           # hair tufts
        ln(d, [(260 + dx, 112), (260 + dx + 14, 78)], 22, INKA)
    for ex in (205, 315):
        if mood == "shut":
            ln(d, [(ex - 22, 245), (ex + 22, 245)], 10, INKA)
        else:
            el(d, ex, 240, 17 if mood != "wow" else 22, 19 if mood != "wow" else 26, INKA, 0)
    el(d, 168, 290, 26, 16, (255, 160, 140), 0); el(d, 352, 290, 26, 16, (255, 160, 140), 0)
    if mood in ("smile", "shut"):
        d.arc([S2(215), S2(262), S2(305), S2(330)], 20, 160, fill=INKA, width=S2(10))
    elif mood == "wow":
        el(d, 260, 305, 24, 30, INKA, 0)
    elif mood == "sad":
        d.arc([S2(225), S2(300), S2(295), S2(345)], 200, 340, fill=INKA, width=S2(10))
    elif mood == "big":
        pg(d, [(215, 280), (305, 280), (290, 335), (230, 335)], (255, 255, 255), 0)
    _mc[key] = done(im, cw, ch)
    return _mc[key]
_mc = {}
S2 = lambda v: v * w4.SS


def pill(img, text, x, y, fill=INKA, fg=(255, 255, 255), size=54, s=1.0, rot=0):
    if s <= 0.02:
        return
    f = font(ANTON, size); tw = ImageDraw.Draw(img).textlength(text, font=f)
    w_, h_ = int(tw + 70), int(size * 1.6)
    sp = Image.new("RGBA", (w_, h_), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    d.rounded_rectangle([0, 0, w_ - 1, h_ - 1], radius=h_ // 2, fill=fill)
    d.text((w_ / 2, h_ / 2 + 2), text, font=f, fill=fg, anchor="mm")
    put(img, sp, x, y, s, rot, anchor="c")


def card(img, x, y, w_, h_, fill, s=1.0, rot=0):
    if s <= 0.02:
        return
    sp = Image.new("RGBA", (w_ + 60, h_ + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    d.rounded_rectangle([34, 40, w_ + 34, h_ + 40], radius=52, fill=(0, 0, 0, 36))
    sp = sp.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(sp)
    d.rounded_rectangle([30, 30, w_ + 29, h_ + 29], radius=52, fill=fill)
    put(img, sp, x, y, s, rot, anchor="c")


def coin(img, x, y, s=1.0, rot=0):
    sp = Image.new("RGBA", (90, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    d.ellipse([4, 4, 85, 85], fill=YEL); d.ellipse([16, 16, 73, 73], outline=(235, 160, 30), width=5)
    d.text((45, 46), "$", font=font(ANTON, 46), fill=(200, 120, 20), anchor="mm")
    put(img, sp, x, y, s, rot, anchor="c")


def bgA(t):
    im = Image.new("RGBA", (W, H), PB + (255,))
    d = ImageDraw.Draw(im, "RGBA")
    for k, (cx, cy, r, col) in enumerate(((140, 260, 260, LIL), (960, 520, 200, MINT), (200, 1500, 300, YEL), (980, 1300, 180, CORAL))):
        dx, dy = 28 * math.sin(t * 0.7 + k), 22 * math.cos(t * 0.6 + k * 2)
        d.ellipse([cx - r + dx, cy - r + dy, cx + r + dx, cy + r + dy], fill=col + (34,))
    return im


def captionA(img, t):
    ch, t0 = chunk_at(t)
    if not ch:
        return
    d = ImageDraw.Draw(img)
    size = 84; f = font(ANTON, size)
    words = [w.upper().rstrip(".,?") + ("?" if w.endswith("?") else "") for w, _, _ in ch]
    sp = d.textlength(" ", font=f) * 1.15
    wd = [d.textlength(x, font=f) for x in words]; total = sum(wd) + sp * (len(words) - 1)
    while total > 900 and size > 44:
        size -= 4; f = font(ANTON, size); wd = [d.textlength(x, font=f) for x in words]; sp = d.textlength(" ", font=f) * 1.15; total = sum(wd) + sp * (len(words) - 1)
    pad = 36; y = 1600 + 8 * (1 - w4.eob((t - t0) / 0.14))
    d.rounded_rectangle([540 - total / 2 - pad, y - size * 0.78, 540 + total / 2 + pad, y + size * 0.78], radius=int(size * 0.8), fill=(255, 255, 255, 235))
    x = 540 - total / 2
    for (w, s, e), word, ww in zip(ch, words, wd):
        on = s - 0.02 <= t < e + 0.05
        d.text((x, y), word, font=f, fill=BLUE if (on or w in KEY) and on else INKA, anchor="lm")
        x += ww + sp


def frameA(t):
    im = bgA(t); k = SCN(t); u = LOC(t)
    if k == 0:
        s = pop(t, 0.15, 0.5)
        d = ImageDraw.Draw(im, "RGBA")
        r = int(300 * s); d.ellipse([540 - r, 700 - r, 540 + r, 700 + r], fill=LIL + (255,))
        d.text((540, 720 + 10 * math.sin(t * 3)), "?", font=font(ANTON, max(8, int(560 * s))), fill=(255, 255, 255), anchor="mm")
        put(im, mascot("wow" if u > 1.4 else "smile", "shrug"), 540, 1560, 0.78, 3 * math.sin(t * 5))
    elif k == 1:
        s1 = pop(t, B[1] + 0.1, 0.45); s2 = pop(t, B[1] + 0.3, 0.45)
        card(im, 300, 960, 440, 640, (255, 255, 255), s1); card(im, 790, 960, 440, 640, (255, 255, 255), s2)
        pill(im, "GRADES", 300, 560, MINT, s=s1); pill(im, "LEARNING", 790, 560, (150, 150, 165), s=s2)
        d = ImageDraw.Draw(im, "RGBA")
        d.text((300, 860), "A+", font=font(ANTON, max(8, int(260 * s1))), fill=MINT, anchor="mm")
        for j in range(9):                                              # coins rain onto the grades card
            tt = (t - (B[1] + 0.6) - j * 0.28)
            if tt > 0:
                y = min(1100, 700 + 700 * tt * tt * 0.9)
                coin(im, 220 + (j % 3) * 80, y + (j // 3) * -0, 0.9)
        bk = Image.new("RGBA", (180, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(bk)
        bd.rounded_rectangle([10, 20, 170, 140], radius=18, fill=BLUE); bd.rectangle([84, 20, 96, 140], fill=(40, 80, 190))
        put(im, bk, 790, 880, 1.6 * s2)
        d.text((790, 1110), "0", font=font(ANTON, max(8, int(210 * s2))), fill=(170, 170, 185), anchor="mm")
        d.text((790, 1220), "coins", font=font(ANTON, 50), fill=(170, 170, 185), anchor="mm") if s2 > 0.5 else None
    elif k == 2:
        sx = (t * 420) % 180
        d = ImageDraw.Draw(im, "RGBA")
        for j in range(-1, 8):
            d.rounded_rectangle([j * 180 - sx, 1478, j * 180 - sx + 100, 1496], radius=9, fill=INKA + (60,))
        ph = (t * 1.7) % 1.0
        put(im, mascot("big", "run", legs=ph), 360, 1470, 0.92, 4 * math.sin(t * 14))
        bx = 780 + 60 * math.sin(t * 2.0); by = 760 + 40 * math.sin(t * 3.0)
        d.line([(bx, by + 150), (bx - 120, 1130)], fill=INKA + (120,), width=6)
        d.ellipse([bx - 170, by - 170, bx + 170, by + 170], fill=MINT + (255,))
        d.text((bx, by + 4), "A+", font=font(ANTON, 190), fill=(255, 255, 255), anchor="mm")
        bk = Image.new("RGBA", (180, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(bk)
        bd.rounded_rectangle([10, 20, 170, 140], radius=18, fill=BLUE); bd.rectangle([84, 20, 96, 140], fill=(40, 80, 190))
        a = clamp01(u / 2.4)
        put(im, bk, lerp(300, -140, a), 1480, lerp(1.0, 0.5, a), -20 * a, 1 - 0.6 * a)
        pill(im, "THE ANSWER?", lerp(300, -140, a), 1280, CORAL, s=clamp01(1 - a * 1.2))
    else:
        flip = clamp01((u - 0.7) / 0.35)
        d = ImageDraw.Draw(im, "RGBA")
        ease_f = ease(flip)
        col_t = mix((170, 172, 184), MINT, ease_f)
        d.rounded_rectangle([140, 540, 940, 740], radius=100, fill=col_t + (255,))
        kx = lerp(240, 840, ease_f)
        d.ellipse([kx - 80, 560, kx + 80, 720], fill=(255, 255, 255, 255))
        pill(im, "GRADES", 280, 450, (150, 150, 165) if flip > 0.5 else INKA)
        pill(im, "LEARNING", 790, 450, MINT if flip > 0.5 else (150, 150, 165))
        d.text((540, 880), "REWARD", font=font(ANTON, 120), fill=INKA, anchor="mm")
        bld = Image.new("RGBA", (560, 460), (0, 0, 0, 0)); bd = ImageDraw.Draw(bld)
        c1 = mix((190, 192, 204), BLUE, ease_f); c2 = mix((210, 212, 222), YEL, ease_f)
        bd.polygon([(30, 150), (280, 20), (530, 150)], fill=c1); bd.rectangle([60, 150, 500, 430], fill=c2)
        for i in range(4):
            bd.rectangle([100 + i * 100, 200, 140 + i * 100, 430], fill=mix((225, 226, 234), (255, 255, 255), ease_f))
        put(im, bld, 540, 1480, 1.0 + 0.04 * ease_f)
        if flip > 0:
            for j in range(16):
                a = j / 16 * 2 * math.pi; rr_ = 120 + 460 * ease_f
                d.ellipse([540 + math.cos(a) * rr_ - 10, 640 + math.sin(a) * rr_ * 0.9 - 10, 540 + math.cos(a) * rr_ + 10, 640 + math.sin(a) * rr_ * 0.9 + 10],
                          fill=[YEL, CORAL, MINT, LIL][j % 4] + (int(255 * (1 - ease_f * 0.85)),))
        if flip > 0.6:
            put(im, mascot("big", "cheer"), 150, 1300, 0.6, 4 * math.sin(t * 9))
    captionA(im, t)
    d = ImageDraw.Draw(im)
    d.text((540, 96), "DEEP TIME ACADEMY", font=font("Cinzel.ttf", 28), fill=(150, 152, 164), anchor="mm")
    return im.convert("RGB")


# =============================================================== STYLE B: neon kinetic
BG1, BG2 = (8, 10, 26), (24, 12, 52)
CY, PK, LM, WH = (60, 240, 255), (255, 70, 170), (170, 255, 80), (240, 244, 255)
_bgB = None


def bgB():
    global _bgB
    if _bgB is None:
        yy = np.linspace(0, 1, H)[:, None, None]
        arr = (np.array(BG1) * (1 - yy) + np.array(BG2) * yy) * np.ones((H, W, 3))
        im = Image.fromarray(arr.astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        for x in range(0, W, 60):
            for y in range(0, H, 60):
                d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(120, 140, 220, 46))
        _bgB = im
    return _bgB.copy()


def glow(base, layer, rad=16, k=1.4):
    g = layer.filter(ImageFilter.GaussianBlur(rad))
    base.paste(Image.new("RGB", base.size, (0, 0, 0)), (0, 0), None) if False else None
    b = np.asarray(base).astype(np.float32); gg = np.asarray(g.convert("RGBA")).astype(np.float32)
    al = gg[..., 3:4] / 255.0 * k
    b = np.clip(b + gg[..., :3] * al, 0, 255)
    out = Image.fromarray(b.astype(np.uint8))
    out.paste(layer.convert("RGB"), (0, 0), layer.getchannel("A"))
    return out


def iconB(kind, t, u, col):
    """line icons drawn on a transparent layer"""
    L_ = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L_)
    c = col + (255,)
    if kind == "q":
        cx, cy = 540, 1280
        d.arc([cx - 150, cy - 220, cx + 150, cy + 20], 160, 400, fill=c, width=26)
        d.line([(cx + 80, cy - 50), (cx, cy + 60), (cx, cy + 90)], fill=c, width=26)
        d.ellipse([cx - 22, cy + 140, cx + 22, cy + 184], fill=c)
    elif kind == "money":
        for k, (cx, label, cc) in enumerate(((310, "A+", LM), (770, "0", (150, 160, 190)))):
            cy = 1250
            d.rounded_rectangle([cx - 190, cy - 230, cx + 190, cy + 230], radius=44, outline=cc + (255,), width=12)
            d.text((cx, cy - 20), label, font=font(ANTON, 230), fill=cc + (255,), anchor="mm")
            d.text((cx, cy + 150), "COINS" if k == 0 else "NOTHING", font=font(ANTON, 54), fill=cc + (255,), anchor="mm")
        for j in range(int(u * 7)):
            tt = u - j / 7.0
            d.ellipse([240 + (j % 3) * 70, 960 + (j * 45) % 120 - 40, 296 + (j % 3) * 70, 1016 + (j * 45) % 120 - 40], outline=YEL + (255,), width=8)
    elif kind == "chase":
        ax = lerp(250, 780, ease(u)); ay = 1250
        d.ellipse([ax - 140, ay - 140, ax + 140, ay + 140], outline=CY + (255,), width=14)
        d.text((ax, ay), "A", font=font(ANTON, 200), fill=CY + (255,), anchor="mm")
        for j in range(4):
            xx = ax - 330 - j * 70
            d.line([(xx, ay - 20), (xx + 120, ay - 20)], fill=PK + (255 - j * 55,), width=14)
        d.polygon([(ax - 200, ay - 20), (ax - 160, ay - 60), (ax - 160, ay + 20)], fill=PK + (255,))
        bx = lerp(250, -100, clamp01(u * 1.2))
        d.rounded_rectangle([bx - 70, 1500, bx + 70, 1580], radius=10, outline=(160, 170, 210, int(255 * (1 - clamp01(u * 1.2)))), width=8)
    else:
        f_ = ease(clamp01((u - 0.25) / 0.4))
        d.rounded_rectangle([190, 1160, 890, 1340], radius=90, outline=mix(PK, LM, f_) + (255,), width=14)
        kx = lerp(290, 790, f_)
        d.ellipse([kx - 70, 1180, kx + 70, 1320], fill=mix(PK, LM, f_) + (255,))
        d.text((290, 1090), "GRADES", font=font(ANTON, 54), fill=PK + (255,) if f_ < 0.5 else (110, 110, 150, 255), anchor="mm")
        d.text((790, 1090), "LEARNING", font=font(ANTON, 54), fill=LM + (255,) if f_ >= 0.5 else (110, 110, 150, 255), anchor="mm")
    return L_


def frameB(t):
    im = bgB(); k = SCN(t); u = LOC(t)
    icon = ["q", "money", "chase", "switch"][k]
    col = [CY, LM, PK, LM][k]
    im = glow(im, iconB(icon, t, clamp01(u / 2.6) if k != 1 else u, col), 14, 1.3)
    ch, t0 = chunk_at(t)
    if ch:
        L_ = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L_)
        size = 190; f = font(ANTON, size)
        words = [w.upper() for w, _, _ in ch]
        wd = [d.textlength(x, font=f) for x in words]; sp = d.textlength(" ", font=f)
        while max(wd) > 940 or (len(words) <= 2 and sum(wd) + sp * (len(words) - 1) > 940):
            size -= 8; f = font(ANTON, size); wd = [d.textlength(x, font=f) for x in words]; sp = d.textlength(" ", font=f)
        y0 = 600 - (len(words) - 1) * size * 0.5
        for j, ((w, s, e), word) in enumerate(zip(ch, words)):
            if t < s - 0.03:
                continue
            sc = 0.7 + 0.3 * w4.eob((t - s) / 0.16)
            colw = (CY if w.strip(".,?") not in ("", ) and w in KEY else WH)
            if w in KEY:
                colw = [PK, CY, LM, PK][k]
            tl = Image.new("RGBA", (int(wd[j] + 80), int(size * 1.5)), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
            td.text((tl.width / 2, tl.height / 2), word, font=f, fill=colw + (255,), anchor="mm")
            put(L_, tl, 540, y0 + j * size * 1.0 + size * 0.5, sc, anchor="c")
        im = glow(im, L_, 12, 1.1)
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([60, 80, W - 60, 90], radius=5, fill=(255, 255, 255, 40))
    d.rounded_rectangle([60, 80, 60 + (W - 120) * clamp01(t / TOTAL), 90], radius=5, fill=CY + (255,))
    d.text((540, 150), "DEEP TIME ACADEMY", font=font("Cinzel.ttf", 28), fill=(150, 160, 200), anchor="mm")
    return im


# =============================================================== audio + render
CUES = [(0.5 + 0.1, "pop"), (SENT[0][1] - 0.4, "boing"), (B[1] + 0.1, "whoosh"), (B[1] + 0.12, "pop"), (B[1] + 0.3, "pop"), (B[1] + 0.6, "coin"), (B[1] + 0.9, "coin"),
        (B[1] + 1.3, "coin"), (B[1] + 1.7, "buzzer"), (B[2], "whoosh"), (B[2] + 1.0, "tick"), (B[2] + 2.4, "thud"), (B[3], "whoosh"),
        (B[3] + 0.7, "click"), (B[3] + 1.0, "ding"), (B[3] + 1.02, "shimmer"), (B[3] + 1.4, "pop"), (TOTAL - 1.6, "ding")]


def build_audio():
    tl = Timeline([p("audio", "voice.wav")], [TOTAL - LEAD - 11.72 if False else 0.0], lead=LEAD)
    voice = tl.voice_track()
    n = int(TOTAL * 48000)
    v = np.zeros(n, np.float32); v[:min(n, len(voice))] = voice[:n]
    fx = np.zeros(n, np.float32)
    for tt, name in CUES:
        place(fx, wb.SFXF[name](), tt)
    mus = wb.music_fun(TOTAL, level=0.2)[:n]
    out = p("_mix.wav")
    finish_audio(v, mus, fx, out, HERE)
    return out


def render(fn, out_mp4, audio_wav, procs=4, parts=8):
    import multiprocessing as mp
    nf = int(round(TOTAL * FPS))
    tmp = tempfile.mkdtemp(prefix="clean_parts_", dir=HERE)
    bounds = [round(nf * i / parts) for i in range(parts + 1)]
    jobs = [(fn, bounds[i], bounds[i + 1], os.path.join(tmp, f"part{i:02d}.mp4")) for i in range(parts)]
    with mp.get_context("fork").Pool(procs) as pool:
        pool.map(_chunk, jobs)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{j[3]}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio_wav, "-c:v", "copy",
                    "-af", "alimiter=limit=0.70:level=disabled", "-c:a", "aac", "-ac", "2", "-ar", "44100", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(tmp)


def _chunk(job):
    fn, k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        ff.stdin.write(np.asarray(fn(k / FPS).convert("RGB")).tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == "__main__":
    wav = build_audio()
    render(frameA, p("sample_a_flat.mp4"), wav)
    render(frameB, p("sample_b_neon.mp4"), wav)
    print("done")
