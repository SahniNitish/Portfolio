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
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import *  # noqa: E402,F401,F403
import engine as E    # noqa: E402
import dta as D       # noqa: E402
from dta import *     # noqa: E402,F401,F403

p = lambda *a: os.path.join(HERE, *a)
random.seed(7)
D.SERIES_TAG = "GAME THEORY  ·  EP 1"


# ---------------------------------------------------------------- voice + timeline
import re
N = len([l for l in open(p("lines.txt")) if l.strip()])
LINES = [l.strip() for l in open(p("lines.txt")) if l.strip()]
os.makedirs(p("audio", "clean"), exist_ok=True)
os.makedirs(p("audio", "placeholder"), exist_ok=True)
PLACEHOLDERS = []     # lines with no real voice yet. Silent stand-ins are used ONLY for previews and layout checks.


def _voice_path(i):
    src, dst = p("audio", f"l{i}.wav"), p("audio", "clean", f"l{i}.wav")
    if os.path.exists(src):
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            clean_voice(src, dst)
        return dst
    ph = p("audio", "placeholder", f"l{i}.wav")
    if not os.path.exists(ph):
        words = len(re.sub(r"\[[^\]]*\]|<[^>]*>", "", LINES[i - 1]).split())
        write_wav(ph, np.zeros(int((0.4 + words / 2.35) * SR), np.float32))
    PLACEHOLDERS.append(i)
    return ph


# chapter cards: first script line (1-based) of each chapter -> (number, title)
CARDS = {15: (1, "FOR MOST OF HISTORY, YOU DIDN'T PLAY"), 24: (2, "WHAT IS A GAME?"), 38: (3, "THE ALGORITHM OF LOVE"),
         58: (4, "SIGNALS"), 73: (5, "THE TRUST TRAP"), 90: (6, "THE CASINO IN YOUR POCKET"),
         101: (7, "WHEN TO STOP SEARCHING"), 108: (8, "HOW TO WIN THE DATING GAME")}

GAPS = [0.45] * N                                   # pause after each line, by 0-based index (= script line - 1)
for i, g in {2: 0.5, 3: 0.6, 4: 4.6, 6: 0.4, 8: 0.6, 9: 0.7, 10: 0.5, 11: 0.6, 12: 0.5,
             47: 0.7, 46: 0.8, 49: 0.8, 53: 0.8, 67: 0.8, 77: 0.8, 86: 0.8, 98: 0.8, 105: 0.8, 115: 0.8,
             118: 3.8}.items():
    GAPS[i] = g
for first in CARDS:
    GAPS[first - 2] = 2.6                           # the pause before each chapter holds its card
TL = Timeline([_voice_path(i) for i in range(1, N + 1)], GAPS, lead=1.2)
L, END, TOTAL = TL.L, TL.end, TL.total
STING = END(4) + 0.9            # channel logo sting starts inside the long gap after the title line


def seg(t, i, j=None):
    j = i if j is None else j
    return clamp01((t - L(i)) / (END(j) - L(i)))


def at(i, frac):                # time at a fraction of line i's voice
    return L(i) + frac * (END(i) - L(i))


# ---------------------------------------------------------------- art
BG = {n: load_bg(p("img", n + ".png")) for n in ["bg_map", "bg_city", "bg_stage", "bg_office"]}
load_cuts(p("img"), ["man_curious", "man_shocked", "woman_confident", "woman_phone", "professors"])
_rng = D._rng
BADGE = D.BADGE


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


def sc_sting(t):
    return sting_frame(t - STING, L(5) - STING)


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


def sc_finale(t):         # line 14: "GAME THEORY" title (the chapter 1 card follows)
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
    return f


# ======================================================================= lines 15-119 (the full story)
# Helpers use 1-based SCRIPT LINE NUMBERS (the numbers in script.md), so the code reads like the script.
GREEN, AMBER, GREYL = (40, 150, 90), (232, 160, 40), (150, 150, 150)
WCOL = [(255, 120, 140), (255, 170, 60), (110, 200, 110), (190, 130, 230)]   # the four women in the matching demo
RED_L, GRN_L, NAVY_L = dict(bg=BLOOD, fg=CREAM), dict(bg=GREEN, fg=(255, 255, 255)), dict(bg=NAVY, fg=GOLD)

BG.update({n: load_bg(p("img", n + ".png")) for n in ["bg_rome", "bg_castle", "bg_china", "bg_india", "bg_market",
                                                       "bg_1973_office", "bg_skinner", "doors"]})
load_cuts(p("img"), ["nash_board", "families_deal", "peacock", "fox", "man_phone_car", "robots"])


def AT(n, frac): return at(n - 1, frac)
def SG(t, n, m=None): return seg(t, n - 1, (n if m is None else m) - 1)
def LS(n): return L(n - 1)
def EN(n): return END(n - 1)


def lab(f, t, n, frac, text, xy, **kw):
    label(f, t, AT(n, frac), text, xy, **kw)


def gtitle(f, t, t_in, text, y, size=120, x=W / 2):
    """Gold Cinzel title that pops in (big -> normal) and then shines. Shrinks itself to fit the screen."""
    if t < t_in:
        return
    while gold_layer(text, size)[0].width > 1800 and size > 40:
        size -= 8
    v = clamp01((t - t_in) / 0.35)
    gold_text(f, text, (x, y), size, a=v, scale=1.4 - 0.4 * ease(v), shine=clamp01((t - t_in - 0.5) / 1.0))


def qmarks(f, t, t_in, t_end=1e9, pts=((1240, 250, 1.0), (680, 330, 0.6), (1390, 470, 0.45))):
    if t < t_in or t > t_end:
        return
    v = ease_out_back(clamp01((t - t_in) / 0.4), 2.5)
    d = ImageDraw.Draw(f)
    for i, (x, y, s) in enumerate(pts):
        sz = int(170 * s * v)
        if sz > 4:
            d.text((x, y + 10 * math.sin(t * 3 + i)), "?", font=font(sz), fill=GOLD, anchor="mm",
                   stroke_width=6, stroke_fill=(40, 26, 10))


def cross(d, x, y, r=34, color=(220, 40, 40), w=12):
    d.line((x - r, y - r, x + r, y + r), fill=color, width=w)
    d.line((x - r, y + r, x + r, y - r), fill=color, width=w)


def arrowhead(d, a, b, color=(255, 236, 150), s=26):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p1 = (b[0] - s * math.cos(ang - 0.5), b[1] - s * math.sin(ang - 0.5))
    p2 = (b[0] - s * math.cos(ang + 0.5), b[1] - s * math.sin(ang + 0.5))
    d.polygon([b, p1, p2], fill=color + (255,))


def dashed(d, a, b, frac, color, width=7, seg_len=20):
    ln = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
    n = int(ln * clamp01(frac) / (seg_len * 2))
    for i in range(n + 1):
        s0 = i * seg_len * 2
        d.line((a[0] + ux * s0, a[1] + uy * s0, a[0] + ux * (s0 + seg_len), a[1] + uy * (s0 + seg_len)), fill=color, width=width)


def speech(f, x, y, text, size=80, tail=1):
    """White speech bubble centred on (x, y); the tail points down toward x - 60*tail."""
    d = ImageDraw.Draw(f)
    tw, th = d.textlength(text, font=font(size)) + 70, size + 50
    d.polygon([(x - 20 * tail, y + th / 2 - 6), (x - 80 * tail, y + th / 2 + 60), (x + 20 * tail, y + th / 2 - 6)],
              fill=(255, 255, 255), outline=(30, 20, 10))
    d.rounded_rectangle((x - tw / 2, y - th / 2, x + tw / 2, y + th / 2), 34, fill=(255, 255, 255), outline=(30, 20, 10), width=6)
    d.text((x, y + 2), text, font=font(size), fill=(30, 20, 10), anchor="mm")


def thought(f, x, y, text, size=40, w=None):
    """Thought bubble (cloud) above a character's head; the little circles lead down toward (x, y + 110)."""
    d = ImageDraw.Draw(f)
    tw = (w or d.textlength(text, font=font(size)) + 90); th = size + 80
    d.ellipse((x - tw / 2, y - th / 2, x + tw / 2, y + th / 2), fill=(255, 255, 255), outline=(30, 20, 10), width=6)
    for k, (dx, dy, r) in enumerate([(-14, th / 2 + 18, 16), (-30, th / 2 + 50, 11), (-42, th / 2 + 76, 7)]):
        d.ellipse((x + dx - r, y + dy - r, x + dx + r, y + dy + r), fill=(255, 255, 255), outline=(30, 20, 10), width=4)
    d.text((x, y + 2), text, font=font(size), fill=(30, 20, 10), anchor="mm")


def ring(f, x, y, t, r=100):
    pulse = 1 + 0.08 * math.sin(t * 8)
    ImageDraw.Draw(f).ellipse((x - r * pulse, y - r * pulse, x + r * pulse, y + r * pulse), outline=GOLD, width=9)


def card(f, x, y, w_, h_, title, sub=None, tcol=(40, 26, 12), size=52, k=1.0, dx=0):
    d = ImageDraw.Draw(f)
    w2, h2 = w_ * k / 2, h_ * k / 2
    if w2 < 4:
        return
    d.rounded_rectangle((x - w2 + 8, y - h2 + 10, x + w2 + 8, y + h2 + 10), 22, fill=(0, 0, 0, 110))
    d.rounded_rectangle((x - w2, y - h2, x + w2, y + h2), 22, fill=(250, 240, 215, 245), outline=(40, 26, 12), width=6)
    if k > 0.85:
        d.text((x + dx, y - (22 if sub else 0)), title, font=font(size), fill=tcol, anchor="mm")
        if sub:
            d.text((x + dx, y + 44), sub, font=font(34), fill=(120, 90, 50), anchor="mm")


# ---- CHAPTER 1: for most of history, you didn't play (lines 15-23)
def sc_hist(t):                                   # 15-16
    f = stage(t, 0.06 + 0.1 * SG(t, 15, 16), cy=0.6)
    darken(f, 0.1 + 0.3 * clamp01((t - LS(16)) / 1.0)); motes(f, t)
    char(f, "man_curious", t, LS(15) - 0.2, 960, 1030, 780, enter="bottom", t_out=AT(16, 0.45))
    qmarks(f, t, AT(15, 0.3), t_end=AT(16, 0.2))
    lab(f, t, 15, 0.05, "A QUICK HISTORY CHECK", (960, 150), size=58, **NAVY_L)
    lab(f, t, 16, 0.5, "IT WASN'T YOU", (960, 470), size=110, angle=-5, **RED_L)
    return f


PANELS = [((150, 150), "bg_rome", "ROME", .12), ((1050, 150), "bg_castle", "EUROPE", .38),
          ((150, 580), "bg_china", "CHINA", .62), ((1050, 580), "bg_india", "INDIA", .84)]


def sc_panels(t):                                 # 17: four civilisations
    f = stage(t, 0.1, cy=0.6)
    darken(f, 0.6)
    for (x0, y0), bgn, name, fr in PANELS:
        t_in = AT(17, fr)
        if t < t_in:
            continue
        k = ease_out_back(clamp01((t - t_in) / 0.45), 1.5)
        pw, ph = round(720 * k), round(405 * k)
        if pw < 8:
            continue
        im = cam(BG[bgn], 0.5, 0.5, 1.05 + 0.08 * clamp01((t - t_in) / 3)).resize((pw, ph), Image.BILINEAR)
        cx, cy = x0 + 360, y0 + 202
        ImageDraw.Draw(f).rounded_rectangle((cx - pw / 2 - 8, cy - ph / 2 - 8, cx + pw / 2 + 8, cy + ph / 2 + 8), 14, fill=GOLD)
        f.alpha_composite(im, (round(cx - pw / 2), round(cy - ph / 2)))
        label(f, t, t_in + 0.2, name, (x0 + 150, y0 + 365), size=46, **NAVY_L)
    lab(f, t, 17, 0.0, "MARRIAGE = A FAMILY MERGER", (1000, 72), size=46, **NAVY_L)
    return f


def sc_families(t):                               # 18-19
    f = blurred(cam(BG["bg_castle"], 0.5, 0.5, 1.0 + 0.06 * SG(t, 18, 19)), 6, 0.6)
    motes(f, t)
    char(f, "families_deal", t, LS(18) - 0.1, 960, 1050, 560, enter="bottom")
    if t < LS(19) + 0.1:
        for k, (kind, name, x) in enumerate([("land", "LAND", 520), ("coin", "MONEY", 960), ("sword", "ARMIES", 1400)]):
            tin = AT(18, 0.12 + 0.34 * k)
            pop_img(f, t, tin, BADGE[kind], (x, 270 + 8 * math.sin(t * 2 + k)))
            label(f, t, tin + 0.1, name, (x, 430), size=46, **NAVY_L)
    lab(f, t, 19, 0.05, "YOUR WEDDING = A BOARD MEETING", (960, 190), size=58)
    pop_img(f, t, AT(19, 0.6), BADGE["heart"], (860, 330))
    lab(f, t, 19, 0.65, "BONUS", (1110, 330), size=60, angle=6)
    lab(f, t, 19, 0.85, "NOT THE POINT", (960, 440), size=56, angle=-4, **RED_L)
    return f


def sc_pick(t):                                   # 20
    f = darken(cam(BG["bg_map"], 0.5, 0.5, 1.0 + 0.1 * SG(t, 20)), 0.15)
    char(f, "man_curious", t, AT(20, 0.35), 520, 1040, 700, enter="left")
    char(f, "woman_confident", t, AT(20, 0.5), 1400, 1040, 710, enter="right", phase=1.3)
    lab(f, t, 20, 0.04, "A WILD NEW IDEA", (960, 160), size=64, **NAVY_L)
    lab(f, t, 20, 0.40, "PICK YOUR OWN PARTNER", (960, 270), size=60, angle=-2)
    pop_img(f, t, AT(20, 0.86), BADGE["heart"], (960, 520))
    lab(f, t, 20, 0.88, "FOR LOVE", (960, 700), size=70, angle=3, **RED_L)
    return f


def sc_market(t):                                 # 21-22
    f = darken(cam(BG["bg_market"], 0.5, 0.55, 1.0 + 0.1 * SG(t, 21, 22)), 0.1)
    char(f, "man_curious", t, LS(21) - 0.2, 470, 1040, 720, enter="left")
    char(f, "woman_confident", t, LS(21), 1450, 1040, 730, enter="right", phase=1.3)
    t_x, t_g = AT(21, 0.68), AT(21, 0.84)
    lab(f, t, 21, 0.42, "A TREATY", (960, 300), bg=(205, 205, 205), fg=(60, 60, 60), size=84, angle=-3, t_out=t_g)
    if t_x < t < t_g + 0.25:
        d = ImageDraw.Draw(f); k1, k2 = clamp01((t - t_x) / 0.2), clamp01((t - t_x - 0.12) / 0.2)
        d.line((780, 235, 780 + 360 * k1, 235 + 130 * k1), fill=(220, 40, 40), width=14)
        d.line((780, 365, 780 + 360 * k2, 365 - 130 * k2), fill=(220, 40, 40), width=14)
    gtitle(f, t, t_g, "A MARKET", 300, 130)
    lab(f, t, 22, 0.12, "COMPETITION", (960, 480), size=60, angle=-2)
    lab(f, t, 22, 0.45, "BARGAINING", (960, 590), size=60, angle=2)
    lab(f, t, 22, 0.78, "STRATEGY", (960, 700), size=60, angle=-2, **RED_L)
    return f


def sc_gt(t):                                     # 23
    k = clamp01((t - LS(23)) / 0.8)
    f = stage(t, 0.14, cy=0.6)
    darken(f, 0.25 + 0.25 * k); spot(f, k); motes(f, t, alpha=150)
    char(f, "man_curious", t, -10, 470 + 120 * ease(k), 1030, 720)
    char(f, "woman_confident", t, -10, 1450 - 120 * ease(k), 1030, 730, phase=1.3)
    gtitle(f, t, AT(23, 0.35), "GAME THEORY", 320, 170)
    return f


# ---- CHAPTER 2: what is a game? (lines 24-37)
def sc_decide(t):                                 # 24
    f = board(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, col, fr in [(620, (120, 190, 255), 0.2), (1300, (255, 130, 150), 0.3)]:
        if t > AT(24, fr):
            person_glyph(d, x, 580, col, max(0.05, 2.0 * ease_out_back(clamp01((t - AT(24, fr)) / 0.35))))
    for a, b, fr in [((730, 540), (1190, 540), 0.5), ((1190, 620), (730, 620), 0.72)]:
        k = clamp01((t - AT(24, fr)) / 0.4)
        chalk_line(d, a, b, k, (255, 236, 150), 8)
        if k >= 1:
            arrowhead(d, a, b)
    f.alpha_composite(lay)
    lab(f, t, 24, 0.05, "DECISIONS THAT DEPEND ON OTHERS", (960, 170), size=56)
    return f


def book_img():
    im = Image.new("RGBA", (380, 500), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 379, 499), 14, fill=(26, 70, 52), outline=GOLD, width=8)
    d.rounded_rectangle((26, 26, 353, 473), 8, outline=GOLD, width=3)
    for k, s in enumerate(["THEORY", "OF GAMES", "AND", "ECONOMIC", "BEHAVIOR"]):
        d.text((190, 110 + k * 62), s, font=cinzel(40 if k != 2 else 28, "Bold"), fill=GOLD, anchor="mm")
    d.line((60, 440, 320, 440), fill=GOLD, width=3)
    return im


BOOK = book_img()


def sc_book(t):                                   # 25
    f = darken(sepia(cam(BG["bg_office"], 0.5, 0.5, 1.05), 0.3), 0.3)
    u = ease(clamp01((t - LS(25) + 0.1) / 0.7))
    bk = BOOK.rotate(lerp(-25, -6, u), Image.BICUBIC, expand=True)
    f.alpha_composite(bk, (round(1230 - bk.width / 2), round(lerp(1400, 560, u) - bk.height / 2)))
    v = ease(clamp01((SG(t, 25) - 0.1) / 0.5))
    gold_text(f, str(round(1900 + 44 * v)), (500, 250), 150)
    lab(f, t, 25, 0.60, "VON NEUMANN", (500, 440), size=52)
    lab(f, t, 25, 0.78, "MORGENSTERN", (500, 550), size=52)
    return f


def sc_nash(t):                                   # 26
    f = board(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k, (a, b) in enumerate([((560, 520), (1060, 520)), ((560, 700), (1060, 700)), ((680, 380), (680, 840)), ((940, 380), (940, 840))]):
        chalk_line(d, a, b, clamp01((t - AT(26, 0.18 + 0.07 * k)) / 0.3), CHALK, 8)
    f.alpha_composite(lay)
    char(f, "nash_board", t, LS(26) - 0.2, 1500, 1110, 960, enter="right")
    lab(f, t, 26, 0.22, "JOHN NASH", (700, 190), size=70)
    lab(f, t, 26, 0.50, "YES, THE 'BEAUTIFUL MIND' GUY", (760, 940), size=50, **RED_L)
    return f


BIG = {k: BADGE[k].resize((340, 340), Image.LANCZOS) for k in ["players", "strategy", "payoff", "info"]}
SMALL = {k: BADGE[k].resize((170, 170), Image.LANCZOS) for k in ["players", "strategy", "payoff", "info"]}


def sc_four(t):                                   # 27-31: the four parts
    f = blurred(stage(t, 0.1), 10, 0.5)
    gtitle(f, t, AT(27, 0.3), "4 PARTS", 190, 130)
    for k, (n, kind, name) in enumerate([(28, "players", "PLAYERS"), (29, "strategy", "STRATEGIES"),
                                         (30, "payoff", "PAYOFFS"), (31, "info", "INFORMATION")]):
        x, tin = 360 + k * 400, AT(n, 0.06)
        pop_img(f, t, tin, BIG[kind], (x, 560 + 8 * math.sin(t * 2 + k)))
        label(f, t, tin + 0.12, name, (x, 790), size=50, **NAVY_L)
    return f


def sc_lenses(t):                                 # 32-37: your love life through the four lenses
    push = 0.06 + 0.08 * SG(t, 32, 37) + 0.1 * ease(clamp01((t - LS(37)) / 1.5))
    f = stage(t, push, cy=0.6); darken(f, 0.25); motes(f, t)
    if AT(35, 0.78) < t < LS(37):
        char(f, "man_shocked", t, AT(35, 0.78), 470, 1030, 730, enter="pop")
    else:
        char(f, "man_curious", t, LS(32) - 0.2, 470, 1030, 720, enter="left")
    char(f, "woman_confident", t, LS(32), 1450, 1030, 730, enter="right", phase=1.3)
    active = "players" if LS(33) <= t < LS(34) else "strategy" if LS(34) <= t < LS(35) else \
             "payoff" if LS(35) <= t < LS(36) else "info" if LS(36) <= t < LS(37) else None
    for k, kind in enumerate(["players", "strategy", "payoff", "info"]):
        x, tin = 640 + k * 213, AT(32, 0.15 + 0.2 * k)
        pop_img(f, t, tin, SMALL[kind], (x, 150))
        if kind == active and t > tin:
            ring(f, x, 150, t, 98)
    lab(f, t, 33, 0.25, "YOU", (470, 240), size=56, t_out=LS(34))
    lab(f, t, 33, 0.60, "EVERYONE ELSE", (1450, 240), size=56, **NAVY_L, t_out=LS(34))
    for fr, txt, y in [(0.05, "APPROACH OR WAIT", 400), (0.38, "COMMIT OR KEEP OPTIONS", 510), (0.70, "TRUTH OR HIGHLIGHT REEL", 620)]:
        lab(f, t, 34, fr, txt, (960, y), size=52, angle=-2 if y != 510 else 2, t_out=LS(35))
    for k, (kind, x) in enumerate([("heart", 760), ("house", 960), ("coin", 1160)]):
        if t < LS(36):
            pop_img(f, t, AT(35, 0.1 + 0.2 * k), BADGE[kind], (x, 470 + 6 * math.sin(t * 2 + k)))
    lab(f, t, 35, 0.80, "HEARTBREAK", (960, 640), size=70, angle=-4, **RED_L, t_out=LS(36))
    qmarks(f, t, LS(36) + 0.1, t_end=LS(37), pts=((470, 200, 0.5), (1450, 200, 0.5)))
    lab(f, t, 36, 0.24, "CATASTROPHIC", (960, 470), size=100, angle=-6, **RED_L, t_out=LS(37))
    gtitle(f, t, AT(37, 0.55), "BUILT FOR THIS", 400, 110)
    return f


# ---- CHAPTER 3: the algorithm of love (lines 38-57)
def sc_gs(t):                                     # 38
    f = sepia(cam(BG["bg_office"], 0.45 + 0.03 * SG(t, 38), 0.55, 1.12), 0.2)
    motes(f, t, (255, 230, 170), 20, 60)
    char(f, "professors", t, LS(38) - 0.2, 760, 1060, 900, enter="right")
    lab(f, t, 38, 0.30, "DAVID GALE", (250, 520), size=48, angle=-3)
    lab(f, t, 38, 0.50, "LLOYD SHAPLEY", (1330, 600), size=48, angle=3)
    return f


LX, RX = 560, 1360
MPREF = [[0, 1, 2, 3], [0, 2, 1, 3], [1, 0, 3, 2], [0, 1, 3, 2]]       # each man's ranking of the four women
# (man, woman, (line, frac) proposed, 'keep'|'rej', (line, frac) woman answers, (line, frac) later dumped or None)
EV = [(0, 0, (40, .25), 'rej', (41, .30), None), (1, 0, (40, .35), 'keep', (41, .30), None),
      (2, 1, (40, .45), 'keep', (41, .36), (43, .30)), (3, 0, (40, .55), 'rej', (41, .42), None),
      (0, 1, (42, .30), 'keep', (43, .30), None), (3, 1, (42, .45), 'rej', (43, .38), None),
      (2, 0, (44, .12), 'rej', (44, .20), None), (3, 3, (44, .18), 'keep', (44, .26), (44, .46)),
      (2, 3, (44, .36), 'keep', (44, .42), None), (3, 2, (44, .62), 'keep', (44, .70), None)]


def sc_algo(t):                                   # 39-46: Gale-Shapley, round by round
    f = board(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    t_gold = AT(45, 0.35)
    for i, y in enumerate(MEN_Y):
        tm, tw = AT(39, 0.06 + 0.1 * i), AT(39, 0.40 + 0.1 * i)
        if t > tm:
            person_glyph(d, LX, y, (120, 190, 255), max(0.05, ease_out_back(clamp01((t - tm) / 0.3))))
            for r, w in enumerate(MPREF[i]):                       # his ranking, as coloured dots
                if t > tm + 0.15 + 0.06 * r:
                    d.ellipse((LX - 190 + 30 * r - 11, y - 11, LX - 190 + 30 * r + 11, y + 11), fill=WCOL[w] + (255,))
        if t > tw:
            person_glyph(d, RX, y, WCOL[i], max(0.05, ease_out_back(clamp01((t - tw) / 0.3))))
    for m, w, tin, kind, tres, tdump in EV:
        t0, tr = AT(*tin), AT(*tres)
        if t < t0:
            continue
        a, b = (LX + 58, MEN_Y[m]), (RX - 58, MEN_Y[w])
        td = AT(*tdump) if tdump else None
        dead = tr if kind == 'rej' and t > tr else (td if td and t > td else None)
        k = clamp01((t - t0) / 0.4)
        if dead is not None:                                          # red flash, then the line retracts
            r = clamp01((t - dead - 0.25) / 0.6)
            if r < 1:
                chalk_line(d, a, b, 1 - r, (235, 70, 60), 8)
            if t - dead < 0.7:
                cross(d, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        elif t > t_gold and kind == 'keep' and td is None:
            chalk_line(d, a, b, 1, (255, 206, 70), 13)
        elif kind == 'keep' and t > tr:
            chalk_line(d, a, b, 1, (255, 226, 100), 9)
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            d.rounded_rectangle((mx - 62, my - 22, mx + 62, my + 22), 10, fill=(255, 220, 90, 255))
            d.text((mx, my + 1), "MAYBE", font=font(30), fill=(40, 26, 12), anchor="mm")
        else:
            chalk_line(d, a, b, k, (245, 245, 235), 7)
    if t > AT(46, 0.15):                                              # a "runaway" pair is blocked
        a, b = (LX + 58, MEN_Y[0]), (RX - 58, MEN_Y[0])
        k = clamp01((t - AT(46, 0.15)) / (0.55 * (EN(46) - LS(46))))
        dashed(d, a, b, k, (255, 255, 255, 255))
        if t > AT(46, 0.62):
            cross(d, W / 2, MEN_Y[0], 44, (235, 70, 60), 14)
    f.alpha_composite(lay)
    for n, txt in [(40, "STEP 1"), (41, "STEP 2"), (42, "STEP 3")]:
        lab(f, t, n, 0.02, txt, (960, 150), size=70, **NAVY_L, t_out=LS(n + 1) + 0.1)
    lab(f, t, 43, 0.45, "TRADES UP", (960, 440), size=76, angle=-4, **RED_L, t_out=LS(44))
    for fr, nxt, txt in [(0.06, 0.32, "ROUND 3"), (0.30, 0.56, "ROUND 4"), (0.56, 1.3, "ROUND 5")]:
        lab(f, t, 44, fr, txt, (960, 150), size=70, **NAVY_L, t_out=AT(44, nxt) if nxt < 1 else AT(45, 0.1))
    lab(f, t, 45, 0.45, "STABLE MATCH", (960, 940), size=90, angle=-3, **GRN_L)
    lab(f, t, 46, 0.62, "NOBODY RUNS OFF", (960, 940), size=80, angle=2, **GRN_L)
    return f


def sc_proved(t):                                 # 47
    f = stage(t, 0.12, cy=0.62); darken(f, 0.3); spot(f, 0.5); motes(f, t)
    char(f, "professors", t, LS(47) - 0.2, 960, 1040, 640, enter="bottom")
    gtitle(f, t, AT(47, 0.45), "ALWAYS WORKS", 190, 130)
    lab(f, t, 47, 0.78, "ANY NUMBER OF PEOPLE", (960, 320), size=52, **NAVY_L)
    return f


def sc_twist2(t):                                 # 48
    hit = AT(48, 0.62)
    f = stage(t, 0.2 + 0.1 * SG(t, 48), cy=0.62)
    f = darken(f, 0.35, (60, 0, 0)); spot(f, 0.7)
    if t > hit:
        f = cam(f, 0.5, 0.5, 1.0, 14 * (1 - clamp01((t - hit) / 0.4)))
    char(f, "man_shocked", t, LS(48) - 0.2, 960, 1050, 800, enter="pop")
    if t > hit:
        label(f, t, hit, "THE TWIST", (W / 2, 220), bg=BLOOD, fg=CREAM, size=110, angle=-5)
    return f


def sc_moves(t):                                  # 49-51: proposers win, waiters lose, it isn't about gender
    f = blurred(stage(t, 0.1), 10, 0.55)
    sw = ease(clamp01((t - AT(51, 0.3)) / 0.9))
    char(f, "man_curious", t, LS(49) - 0.3, lerp(330, 1590, sw), 1060, 700, enter="left")
    char(f, "woman_confident", t, LS(49), lerp(1590, 330, sw), 1060, 710, enter="right", phase=1.1)
    for n, fr, side, title, res, col, up in [(49, 0.05, -1, "PROPOSES FIRST", "BEST MATCH", GREEN, True),
                                             (50, 0.0, 1, "WAITS", "WORST MATCH", (210, 50, 50), False)]:
        t_in = AT(n, fr)
        if t < t_in:
            continue
        x = W / 2 + side * 260
        k = ease_out_back(clamp01((t - t_in) / 0.4)); y0 = 260 + (1 - k) * 600
        d = ImageDraw.Draw(f)
        d.rounded_rectangle((x - 240, y0, x + 240, y0 + 520), 22, fill=(250, 240, 215, 235), outline=(40, 26, 12), width=6)
        d.text((x, y0 + 60), title, font=font(52), fill=(40, 26, 12), anchor="mm")
        if t > t_in + 1.1:
            kk = ease_out_back(clamp01((t - t_in - 1.1) / 0.35))
            arrow(d, x, y0 + 250, up, col, kk)
            d.text((x, y0 + 440), res, font=font(64), fill=col, anchor="mm")
    lab(f, t, 51, 0.10, "NOT ABOUT GENDER", (960, 170), size=60, **NAVY_L, t_out=AT(51, 0.58))
    lab(f, t, 51, 0.62, "ONLY WHO MOVES FIRST", (960, 170), size=60, **RED_L)
    return f


def sc_lying(t):                                  # 52-53
    f = stage(t, 0.1, cy=0.6); darken(f, 0.2); motes(f, t)
    char(f, "man_curious", t, LS(52) - 0.2, 470, 1030, 720, enter="left")
    lab(f, t, 52, 0.40, "PROPOSERS: NO REASON TO LIE", (960, 200), size=54, **NAVY_L, t_out=AT(53, 0.4))
    char(f, "woman_confident", t, LS(53) - 0.2, 1450, 1030, 730, enter="right", phase=1.3)
    if t > AT(53, 0.28):
        speech(f, 1250, 330, "NO...", 90, tail=-1)
    lab(f, t, 53, 0.58, "WAITERS CAN BLUFF", (960, 450), size=64, angle=-3, **RED_L)
    return f


def sc_hard(t):                                   # 54
    f = stage(t, 0.14, cy=0.6); darken(f, 0.35); spot(f, 0.6); motes(f, t, alpha=150)
    char(f, "woman_confident", t, LS(54) - 0.2, 960, 1040, 760, enter="bottom")
    lab(f, t, 54, 0.08, "1962", (300, 340), size=84, face="cinzel", **NAVY_L)
    gtitle(f, t, AT(54, 0.40), "PLAYING HARD TO GET", 200, 100)
    lab(f, t, 54, 0.78, "GRANDMA WAS RIGHT", (1060, 340), size=84, angle=-4, **RED_L)
    return f


def hospital_icon(d, x, y, s=1.0):
    d.rounded_rectangle((x - 70 * s, y - 70 * s, x + 70 * s, y + 70 * s), 14, fill=(250, 250, 250), outline=(30, 20, 10), width=5)
    d.rectangle((x - 14 * s, y - 44 * s, x + 14 * s, y + 44 * s), fill=(220, 40, 40))
    d.rectangle((x - 44 * s, y - 14 * s, x + 44 * s, y + 14 * s), fill=(220, 40, 40))


def sc_doctors(t):                                # 55
    f = darken(cam(BG["bg_city"], 0.5, 0.5, 1.1), 0.55, (10, 10, 30))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    rows = [250, 410, 570, 730]
    for i, y in enumerate(rows):
        tin = AT(55, 0.08 + 0.07 * i)
        if t > tin:
            s = max(0.05, ease_out_back(clamp01((t - tin) / 0.3)))
            person_glyph(d, 520, y, (250, 250, 250), 1.3 * s)
            hospital_icon(d, 1400, y, 0.8 * s)
    for k, (i, j) in enumerate([(0, 1), (1, 0), (2, 3), (3, 2), (0, 0), (2, 2), (1, 3), (3, 1)]):
        chalk_line(d, (600, rows[i]), (1320, rows[j]), clamp01((t - AT(55, 0.30 + 0.05 * k)) / 0.3),
                   (255, 236, 150) if k < 4 else (255, 255, 255), 6)
    f.alpha_composite(lay)
    lab(f, t, 55, 0.05, "NEW DOCTORS TO HOSPITALS", (960, 120), size=60, **NAVY_L)
    lab(f, t, 55, 0.70, "TENS OF THOUSANDS A YEAR", (960, 900), size=66, angle=-2)
    return f


def school_icon(d, x, y, s=1.0):
    d.polygon([(x - 90 * s, y - 20 * s), (x, y - 90 * s), (x + 90 * s, y - 20 * s)], fill=(190, 60, 50), outline=(30, 20, 10))
    d.rectangle((x - 76 * s, y - 20 * s, x + 76 * s, y + 70 * s), fill=(240, 210, 150), outline=(30, 20, 10), width=4)
    d.rectangle((x - 16 * s, y + 20 * s, x + 16 * s, y + 70 * s), fill=(110, 70, 40))
    d.line((x, y - 90 * s, x, y - 140 * s), fill=(30, 20, 10), width=5)
    d.polygon([(x, y - 140 * s), (x + 44 * s, y - 126 * s), (x, y - 112 * s)], fill=(40, 90, 200))


def sc_schools(t):                                # 56
    f = blurred(cam(BG["bg_city"], 0.5, 0.5, 1.05), 8, 0.5)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(4):
        x = 360 + k * 400
        tin = AT(56, 0.18 + 0.14 * k)
        if t > tin:
            school_icon(d, x, 560, 1.7 * max(0.05, ease_out_back(clamp01((t - tin) / 0.3))))
        for q in range(3):                                        # students walking in
            tw = AT(56, 0.55 + 0.1 * k + 0.05 * q)
            if t > tw:
                u = clamp01((t - tw) / 0.7)
                person_glyph(d, x - 220 * (1 - u) + 6 * q, 780 - 10 * q, (250, 250, 250), 0.6 * (1 - 0.6 * u))
    f.alpha_composite(lay)
    lab(f, t, 56, 0.08, "NEW YORK CITY HIGH SCHOOLS", (960, 160), size=64, **NAVY_L)
    return f


def sc_nobel2(t):                                 # 57: medal
    t_med = AT(57, 0.12)
    v = clamp01((t - t_med) / 0.7)
    f = Image.new("RGBA", (W, H), (16, 12, 30, 255))
    y_, x_ = np.ogrid[0:H:4, 0:W:4]
    m = np.exp(-(((x_ - W / 2) / 650) ** 2 + ((y_ - 470) / 420) ** 2)) * 120
    f.alpha_composite(Image.fromarray(np.dstack([m * 0.9, m * 0.62, m * 0.3, m * 1.8]).clip(0, 255).astype(np.uint8),
                                      "RGBA").resize((W, H), Image.BILINEAR))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for r in range(14):
        ang = r * math.pi / 7 + t * 0.15
        d.polygon([(W / 2, 450), (W / 2 + 1400 * math.cos(ang - 0.05), 450 + 1400 * math.sin(ang - 0.05)),
                   (W / 2 + 1400 * math.cos(ang + 0.05), 450 + 1400 * math.sin(ang + 0.05))], fill=(255, 220, 140, int(28 * v)))
    f.alpha_composite(lay)
    flip = abs(math.cos((1 - ease(v)) * math.pi * 1.5)); s = 0.4 + 0.6 * ease_out_back(v)
    med = MEDAL.resize((max(2, round(520 * s * max(flip, 0.04))), round(520 * s)), Image.BICUBIC)
    d = ImageDraw.Draw(f)
    d.polygon([(W / 2 - 120, -10), (W / 2 - 10, 260), (W / 2 + 10, 260), (W / 2 + 120, -10)], fill=(30, 60, 150))
    d.polygon([(W / 2 - 40, -10), (W / 2, 240), (W / 2 + 40, -10)], fill=(200, 40, 50))
    f.alpha_composite(med, (round(W / 2 - med.width / 2), round(450 - med.height / 2)))
    motes(f, t, (255, 220, 150), 46, 160)
    gtitle(f, t, t_med + 0.6, "NOBEL PRIZE", 820, 96)
    lab(f, t, 57, 0.55, "SHAPLEY & ROTH  ·  2012", (W / 2, 930), size=46, **NAVY_L)
    return f


# ---- CHAPTER 4: signals (lines 58-72)
def sc_crack(t):                                  # 58-59: the neat diagram meets real life
    f = board(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i, y in enumerate(MEN_Y):
        person_glyph(d, LX, y, (120, 190, 255)); person_glyph(d, RX, y, WCOL[i])
        for r, w in enumerate(MPREF[i]):
            d.ellipse((LX - 190 + 30 * r - 11, y - 11, LX - 190 + 30 * r + 11, y + 11), fill=WCOL[w] + (255,))
    for m, w in [(1, 0), (0, 1), (2, 3), (3, 2)]:
        chalk_line(d, (LX + 58, MEN_Y[m]), (RX - 58, MEN_Y[w]), 1, (255, 206, 70), 12)
    k = clamp01((t - AT(58, 0.55)) / 0.5)
    if k > 0:
        pts = [(960, 150), (900, 330), (1010, 470), (890, 620), (1000, 760), (940, 900)]
        for a, b in zip(pts, pts[1:]):
            chalk_line(d, a, (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k), 1, (235, 70, 60), 12)
    f.alpha_composite(lay)
    lab(f, t, 58, 0.70, "THE PROBLEM", (960, 940), size=84, angle=-3, **RED_L, t_out=LS(59))
    lab(f, t, 59, 0.08, "EVERYONE KNOWS WHAT THEY WANT", (960, 940), size=64, **GRN_L)
    return f


def sc_hidden(t):                                 # 60-61
    f = stage(t, 0.1, cy=0.6); darken(f, 0.2); motes(f, t)
    char(f, "man_curious", t, LS(60) - 0.2, 470, 1030, 720, enter="left")
    char(f, "woman_confident", t, LS(60), 1450, 1030, 730, enter="right", phase=1.3)
    lab(f, t, 60, 0.30, "HIDDEN INFORMATION", (960, 200), size=66, **NAVY_L, t_out=LS(61))
    if t > AT(60, 0.4):
        thought(f, 470, 190, "?", 80, w=180)
        thought(f, 1450, 190, "?", 80, w=180)
    for fr, txt, x in [(0.10, "SERIOUS?", 470), (0.30, "JUST PASSING TIME?", 470), (0.50, "INTERESTED?", 1450), (0.66, "JUST POLITE?", 1450)]:
        t_in = AT(61, fr)
        nxt = {0.10: 0.30, 0.30: 1.0, 0.50: 0.66, 0.66: 1.0}[fr]
        if t_in < t < (AT(61, nxt) if nxt < 1.0 else LS(62) + 0.3):
            thought(f, x, 190, txt, 38)
    lab(f, t, 61, 0.83, "OVER THEIR EX?", (960, 560), size=84, angle=-4, **RED_L)
    return f


def sc_signal(t):                                 # 62
    f = blurred(stage(t, 0.1), 10, 0.5)
    gtitle(f, t, AT(62, 0.30), "SIGNALING GAME", 330, 140)
    if t > AT(62, 0.78):
        speech(f, 960, 640, "CHEAP TALK", 100, tail=1)
    return f


def glow_rect(f, rect, t, t_in):
    if t < t_in:
        return
    x0, y0, x1, y1 = rect
    a = int(160 + 80 * math.sin(t * 6))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0 - 14, y0 - 14, x1 + 14, y1 + 14), 16, outline=GOLD + (a,), width=14)
    f.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(f).rounded_rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), 12, outline=GOLD, width=5)


def sc_spence(t):                                 # 63-64
    f = darken(sepia(cam(BG["bg_1973_office"], 0.5, 0.5, 1.0 + 0.06 * SG(t, 63, 64)), 0.25), 0.15)
    char(f, "man_curious", t, LS(63) - 0.2, 420, 1060, 760, enter="left")
    lab(f, t, 63, 0.10, "1973", (1560, 170), size=90, face="cinzel", **NAVY_L)
    lab(f, t, 63, 0.45, "MICHAEL SPENCE", (1500, 290), size=56)
    glow_rect(f, (1013, 90, 1424, 335), t, AT(64, 0.1))
    lab(f, t, 64, 0.22, "HARD TO GET", (1220, 440), size=58, **NAVY_L)
    lab(f, t, 64, 0.62, "COSTLY TO FAKE", (1220, 540), size=58, **RED_L)
    return f


def sc_peacock(t):                                # 65-68
    f = blurred(cam(BG["bg_rome"], 0.5, 0.5, 1.0 + 0.06 * SG(t, 65, 68)), 5, 0.75)
    if t > AT(67, 0.1):                                           # golden glow behind the proud bird
        g = ease(clamp01((t - AT(67, 0.1)) / 0.8))
        yy, xx = np.ogrid[0:H:6, 0:W:6]
        m = np.exp(-(((xx - 640) / 520) ** 2 + ((yy - 640) / 420) ** 2)) * 150 * g
        f.alpha_composite(Image.fromarray(np.dstack([m * 1.0, m * 0.8, m * 0.3, m * 1.4]).clip(0, 255).astype(np.uint8),
                                          "RGBA").resize((W, H), Image.BILINEAR))
    char(f, "peacock", t, LS(65) - 0.2, 640, 1040, 640, enter="left")
    char(f, "fox", t, AT(66, 0.35), 1500, 1040, 330, enter="right", t_out=AT(67, 0.35))
    lab(f, t, 65, 0.20, "NATURE FIGURED IT OUT", (960, 170), size=60, **NAVY_L, t_out=LS(66))
    lab(f, t, 66, 0.15, "HEAVY. SLOW. RISKY.", (960, 170), size=64, **RED_L, t_out=LS(67))
    lab(f, t, 67, 0.72, "A FLEX YOU CAN'T FAKE", (960, 170), size=64)
    gtitle(f, t, AT(68, 0.30), "HANDICAP PRINCIPLE", 330, 110)
    return f


def sc_costless(t):                               # 69: "I love you" costs nothing
    f = darken(cam(BG["bg_city"], 0.55, 0.45, 1.3), 0.3, (20, 0, 30))
    char(f, "woman_phone", t, LS(69) - 0.2, 430, 1060, 760, enter="left")
    lab(f, t, 69, 0.25, "COST: ZERO", (1300, 150), size=80, angle=-3, **RED_L)
    for k in range(9):
        tin = AT(69, 0.45 + 0.055 * k)
        if t > tin:
            u = ease(clamp01((t - tin) / 0.5))
            x = 640 + (330 + 190 * (k % 3)) * u; y = 560 + ((k // 3) * 150 - 190) * u
            label(f, t, tin, "I LOVE YOU", (x, y), bg=(255, 255, 255), fg=(30, 20, 10), size=34, angle=(-6, 4, -2)[k % 3])
    return f


def sc_drive(t):                                  # 70: a three-hour drive
    u = SG(t, 70)
    f = cam(BG["bg_city"], 0.35 + 0.3 * u, 0.55, 1.15)
    f = darken(f, 0.1)
    char(f, "man_phone_car", t, -10, lerp(-300, 2250, ease(clamp01((u - 0.02) / 0.96))), 1020, 330, walk=True)
    lab(f, t, 70, 0.10, "3 HOURS", (480, 170), size=70, **NAVY_L)
    lab(f, t, 70, 0.45, "REMEMBERED", (960, 290), size=70)
    lab(f, t, 70, 0.78, "MEET THE FAMILY", (1400, 170), size=70, **RED_L)
    return f


def sc_costly(t):                                 # 71
    f = stage(t, 0.12, cy=0.6); darken(f, 0.35); spot(f, 0.5); motes(f, t, alpha=150)
    pop_img(f, t, AT(71, 0.2), BADGE["coin"], (560, 560))
    pop_img(f, t, AT(71, 0.3), BADGE["heart"], (1360, 560))
    gtitle(f, t, AT(71, 0.45), "COSTLY SIGNALS", 330, 120)
    lab(f, t, 71, 0.75, "= TRUST", (960, 560), size=110, angle=-3, **GRN_L)
    return f


def sc_hey(t):                                    # 72
    f = darken(cam(BG["bg_city"], 0.55, 0.45, 1.3), 0.3, (20, 0, 30))
    char(f, "woman_phone", t, -10, 430, 1060, 760)
    for k in range(7):
        tin = AT(72, 0.06 + 0.075 * k)
        if t > tin:
            fall = ease(clamp01((t - AT(72, 0.60) - 0.04 * k) / 0.6)) if t > AT(72, 0.60) else 0
            label(f, t, tin, "HEY", (1150 + 60 * (k % 2) - 70 * (k % 3), 880 - 105 * k + 900 * fall), bg=(255, 255, 255),
                  fg=(30, 20, 10), size=44, angle=(-4, 3, -2)[k % 3])
    lab(f, t, 72, 0.64, "WORTH NOTHING", (1350, 380), size=96, angle=-5, **RED_L)
    return f


# ---- CHAPTER 5: the trust trap (lines 73-89)
def sc_trap1(t):                                  # 73-74
    f = stage(t, 0.08 + 0.1 * SG(t, 73, 74), cy=0.6); darken(f, 0.15 + 0.3 * clamp01((t - LS(74)) / 0.8)); motes(f, t)
    char(f, "man_curious", t, LS(73) - 0.2, 470, 1030, 720, enter="left", t_out=AT(74, 0.52))
    char(f, "woman_confident", t, LS(73), 1450, 1030, 730, enter="right", phase=1.3, t_out=AT(74, 0.52))
    lab(f, t, 73, 0.45, "ANOTHER TRAP", (960, 260), size=84, angle=3, **RED_L, t_out=LS(74))
    lab(f, t, 74, 0.05, "1950", (500, 160), size=90, face="cinzel", **NAVY_L)
    lab(f, t, 74, 0.28, "RAND CORPORATION", (1400, 160), size=56)
    gtitle(f, t, AT(74, 0.62), "THE PRISONER'S DILEMMA", 520, 96)
    return f


def sc_matrix(t):                                 # 75-78
    f = blurred(stage(t, 0.1), 10, 0.5)
    char(f, "man_curious", t, LS(75) - 0.2, 230, 1050, 560, enter="left")
    char(f, "woman_confident", t, LS(75), 1690, 1050, 570, enter="right", phase=1.3)
    hl = None
    if AT(76, 0.1) < t < AT(76, 0.55): hl = (0, 0)
    elif AT(76, 0.55) < t < LS(77): hl = (0, 1)
    elif t > AT(78, 0.12): hl = (1, 1)
    payoff_matrix(f, t, AT(75, 0.12), highlight=hl, x=W / 2, y=590, size=560)
    if t > AT(77, 0.3):
        qmarks(f, t, AT(77, 0.3), t_end=LS(78), pts=((230, 330, 0.5), (1690, 330, 0.5)))
    lab(f, t, 77, 0.55, "PROTECT MYSELF?", (960, 150), size=70, **NAVY_L, t_out=LS(78))
    lab(f, t, 78, 0.35, "BOTH LOSE", (960, 150), size=84, angle=-3, **RED_L)
    return f


def sc_openup(t):                                 # 79-81
    k = ease(clamp01((t - LS(81)) / (EN(81) - LS(81))))
    f = stage(t, 0.1, cy=0.6); darken(f, 0.15 + 0.3 * clamp01((t - LS(81)) / 1.0)); motes(f, t)
    char(f, "man_curious", t, LS(79) - 0.2, lerp(470, 250, k), 1030, 720, enter="left")
    char(f, "woman_confident", t, LS(79), lerp(1450, 1670, k), 1030, 730, enter="right", phase=1.3)
    for fr, txt, x in [(0.12, "OPEN UP", 560), (0.42, "INVEST", 960), (0.72, "COMMIT", 1360)]:
        lab(f, t, 79, fr, txt, (x, 200), size=62, **GRN_L, t_out=LS(80))
    lab(f, t, 80, 0.30, "ONE FOOT OUT THE DOOR", (960, 330), size=60, angle=-2, **RED_L, t_out=LS(81))
    lab(f, t, 80, 0.70, "THE OTHER ON THE APPS", (960, 450), size=60, angle=2, **RED_L, t_out=LS(81))
    lab(f, t, 81, 0.55, "NEVER STARTS", (960, 560), size=96, angle=-4, **RED_L)
    return f


def sc_escape(t):                                 # 82
    f = stage(t, 0.12, cy=0.6); darken(f, 0.15); motes(f, t)
    char(f, "man_curious", t, LS(82) - 0.2, 960, 1030, 780, enter="bottom")
    qmarks(f, t, AT(82, 0.2))
    lab(f, t, 82, 0.30, "HOW DO WE ESCAPE?", (960, 150), size=66, **NAVY_L)
    return f


def blobs(name):
    """x-ranges (x0, x1, top_y) of the separate objects in a cut-out, in cut-out pixels."""
    a = np.asarray(CUT[name].getchannel("A")) > 40
    cols, out, start = a.any(0), [], None
    for x, v in enumerate(cols):
        if v and start is None:
            start = x
        if (not v or x == len(cols) - 1) and start is not None:
            if x - start > 20:
                out.append((start, x, int(np.argmax(a[:, start:x].any(1)))))
            start = None
    return out


ROBOTS = blobs("robots")


def crown(d, x, y, s=1.0):
    d.polygon([(x - 46 * s, y), (x - 52 * s, y - 56 * s), (x - 24 * s, y - 28 * s), (x, y - 70 * s),
               (x + 24 * s, y - 28 * s), (x + 52 * s, y - 56 * s), (x + 46 * s, y)], fill=(255, 206, 70), outline=(120, 78, 20))
    for dx in (-52, 0, 52):
        d.ellipse((x + (dx - 8) * s, y - (70 if dx == 0 else 56) * s - 8 * s, x + (dx + 8) * s, y - (70 if dx == 0 else 56) * s + 8 * s),
                  fill=(255, 245, 190))


def sc_axelrod(t):                                # 83-84
    f = sepia(cam(BG["bg_office"], 0.5, 0.5, 1.0 + 0.06 * SG(t, 83, 84)), 0.3); darken(f, 0.25)
    hh = 620
    char(f, "robots", t, LS(83) - 0.1, 960, 1040, hh, enter="bottom")
    lab(f, t, 83, 0.04, "1980", (480, 160), size=90, face="cinzel", **NAVY_L)
    lab(f, t, 83, 0.30, "AXELROD'S TOURNAMENT", (1250, 160), size=56)
    if t > AT(84, 0.5) and ROBOTS:
        cw = CUT["robots"].width; sc = hh / CUT["robots"].height
        x0, x1, top = ROBOTS[0]
        cx = 960 - cw * sc / 2 + (x0 + x1) / 2 * sc; cy = 1040 - hh + top * sc - 8
        k = ease_out_back(clamp01((t - AT(84, 0.5)) / 0.4), 2.0)
        crown(ImageDraw.Draw(f), cx, cy - 60 * (1 - k), 1.3 * max(k, 0.05))
    gtitle(f, t, AT(84, 0.62), "TIT FOR TAT", 305, 140)
    return f


def sc_tft(t):                                    # 85-86
    f = blurred(stage(t, 0.1), 10, 0.5)
    if t < LS(86) - 0.1:
        card(f, 620, 540, 640, 300, "START NICE", "ROUND ONE", k=ease_out_back(clamp01((t - AT(85, 0.08)) / 0.4)), size=64)
        card(f, 1300, 540, 640, 300, "THEN COPY THEM", "WHAT THEY DID LAST", k=ease_out_back(clamp01((t - AT(85, 0.50)) / 0.4)), size=56)
    for fr, txt, y in [(0.10, "BE NICE", 300), (0.30, "RESPOND QUICKLY", 420), (0.50, "FORGIVE QUICKLY", 540)]:
        lab(f, t, 86, fr, txt, (960, y), size=66, angle=-2 if y != 420 else 2, **GRN_L)
    gtitle(f, t, AT(86, 0.80), "A GOOD MEMORY", 760, 100)
    return f


def sc_repeat(t):                                 # 87
    f = blurred(stage(t, 0.1), 10, 0.5)
    k1, k2 = ease_out_back(clamp01((t - AT(87, 0.08)) / 0.4)), ease_out_back(clamp01((t - AT(87, 0.52)) / 0.4))
    card(f, 560, 520, 700, 380, "ONE ROUND", "BETRAYAL PAYS", tcol=(190, 40, 40), k=k1, size=84)
    card(f, 1360, 520, 700, 380, "REPEATED GAME", "TRUST WINS", tcol=(40, 130, 80), k=k2, size=76)
    return f


def sc_shadow(t):                                 # 88-89
    k = ease(clamp01((t - LS(89)) / (EN(89) - LS(89))))
    f = stage(t, 0.1, cy=0.6); darken(f, 0.35); motes(f, t, alpha=140)
    g = ease(clamp01((t - LS(88)) / 1.2))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(560, 1040), (1360, 1040), (1040, 470), (880, 470)], fill=(255, 200, 80, int(90 * g)))
    d.polygon([(760, 1040), (1160, 1040), (1000, 470), (920, 470)], fill=(255, 220, 120, int(120 * g)))
    f.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
    char(f, "man_curious", t, -10, lerp(700, 800, k), 1040, 720)
    char(f, "woman_confident", t, -10, lerp(1220, 1120, k), 1040, 730, phase=1.3)
    if t < LS(89):
        gtitle(f, t, AT(88, 0.45), "THE SHADOW OF THE FUTURE", 250, 100)
    lab(f, t, 89, 0.30, "THE ULTIMATE REPEATED GAME", (960, 200), size=66, **NAVY_L)
    pop_img(f, t, AT(89, 0.82), BADGE["heart"], (960, 520))
    return f


# ---- CHAPTER 6: the casino in your pocket (lines 90-100)
def profile_card(d, x, y, s=1.0, hot=False):
    w_, h_ = 90 * s, 120 * s
    d.rounded_rectangle((x - w_ / 2, y - h_ / 2, x + w_ / 2, y + h_ / 2), 8 * s, fill=(250, 240, 215),
                        outline=GOLD if hot else (40, 26, 12), width=4 if hot else 3)
    d.ellipse((x - 18 * s, y - 38 * s, x + 18 * s, y - 2 * s), fill=(190, 150, 110))
    d.pieslice((x - 30 * s, y, x + 30 * s, y + 56 * s), 180, 360, fill=(110, 130, 170))


def sc_phone(t):                                  # 90-92
    f = darken(cam(BG["bg_city"], 0.55, 0.45, 1.3), 0.45, (20, 0, 30))
    char(f, "woman_phone", t, LS(90) - 0.2, 430, 1060, 760, enter="left")
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse((330, 330, 530, 530), fill=(255, 60, 160, 80))
    f.alpha_composite(gl.filter(ImageFilter.GaussianBlur(40)))
    lab(f, t, 90, 0.40, "THE DATING APP", (820, 95), size=70, **NAVY_L)
    d = ImageDraw.Draw(f)
    for k in range(36):
        tk = AT(91, 0.05 + 0.85 * k / 36)
        if t > tk:
            u = ease(clamp01((t - tk) / 0.7)); a = math.radians(-40 + 80 * ((k // 3) / 11))
            r = 120 + ((400, 560, 720)[k % 3] - 120) * u            # three rings of cards fanning out to the right
            profile_card(d, 640 + r * math.cos(a), 600 + r * math.sin(a) * 0.95, 0.5 + 0.5 * u, hot=(k % 9 == 0))
    lab(f, t, 91, 0.30, "THOUSANDS OF OPTIONS", (1250, 960), size=60, **NAVY_L, t_out=LS(92))
    lab(f, t, 92, 0.05, "A DREAM?", (1250, 960), size=80, bg=(255, 150, 220), fg=(60, 10, 40))
    lab(f, t, 92, 0.62, "A TRAP", (1560, 150), size=110, angle=-5, **RED_L)
    return f


def sc_oneswipe(t):                               # 93
    u = SG(t, 93)
    f = stage(t, 0.1, cy=0.6); darken(f, 0.3); motes(f, t)
    g = 1 - ease(clamp01((u - 0.1) / 0.7))                       # the shadow of the future shrinks away
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(560, 1040), (1360, 1040), (1040, 470), (880, 470)], fill=(255, 200, 80, int(90 * g)))
    f.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
    char(f, "man_curious", t, LS(93) - 0.2, 960, 1040, 720, enter="bottom")
    d = ImageDraw.Draw(f)
    for k, tin in enumerate([AT(93, 0.30), AT(93, 0.52), AT(93, 0.74)]):
        if t > tin:
            x = lerp(1500, -200, ease(clamp01((t - tin) / 0.9)))
            profile_card(d, x, 300 + 40 * k, 1.5)
    lab(f, t, 93, 0.25, "ONE SWIPE AWAY", (960, 170), size=84, angle=-2, **NAVY_L)
    return f


def sc_pyramid(t):                                # 94
    f = blurred(stage(t, 0.1), 10, 0.5)
    d = ImageDraw.Draw(f)
    rows = [1, 2, 3, 4, 5]
    for r, n in enumerate(rows):
        for c in range(n):
            x = 960 + (c - (n - 1) / 2) * 165; y = 300 + r * 150
            tin = AT(94, 0.08 + 0.05 * (r * 2 + c % 2))
            if t > tin:
                s = max(0.05, ease_out_back(clamp01((t - tin) / 0.3)))
                profile_card(d, x, y, 1.2 * s, hot=(r < 2))
                if r < 2:
                    for q in range(5 - r * 2):
                        tq = AT(94, 0.30 + 0.06 * q + 0.04 * c)
                        if t > tq:
                            pop = ease_out_back(clamp01((t - tq) / 0.35))
                            hx, hy = x - 60 + 30 * q, y - 105 - 10 * math.sin(t * 3 + q)
                            d.polygon(heart_pts(hx, hy, 22 * pop), fill=BLOOD)
    lab(f, t, 94, 0.10, "ATTENTION PILES UP AT THE TOP", (960, 105), size=60, **NAVY_L)
    lab(f, t, 94, 0.72, "MOST PEOPLE HEAR SILENCE", (960, 1028), size=52, bg=(200, 200, 200), fg=(60, 60, 60))
    return f


def sc_swipe(t):                                  # 95-96
    f = darken(cam(BG["bg_city"], 0.55, 0.45, 1.3), 0.45, (20, 0, 30))
    char(f, "woman_phone", t, LS(95) - 0.2, 520, 1480, 1350, enter="left")
    lab(f, t, 95, 0.30, "LOOK HOW IT FEELS", (1250, 200), size=72, **NAVY_L, t_out=LS(96))
    seq = [(0.04, "SWIPE", None), (0.13, "NOTHING", "g"), (0.25, "SWIPE", None), (0.33, "NOTHING", "g"), (0.45, "SWIPE", None),
           (0.56, "IT'S A MATCH!", "m"), (0.72, "AGAIN", "r"), (0.82, "AGAIN", "r"), (0.92, "AGAIN", "r")]
    for k, (fr, txt, kind) in enumerate(seq):
        nxt = AT(96, seq[k + 1][0]) if k + 1 < len(seq) and kind != "r" and seq[k + 1][2] != "r" else None
        if kind == "m":
            nxt = AT(96, 0.70)
        pos = (1300, 330) if kind != "r" else (1100 + 200 * (k - 6), 560 + 130 * (k - 6))
        style = dict(bg=(200, 200, 200), fg=(60, 60, 60)) if kind == "g" else \
                dict(bg=(255, 150, 220), fg=(60, 10, 40)) if kind == "m" else \
                dict(bg=BLOOD, fg=CREAM) if kind == "r" else dict(bg=CREAM, fg=(40, 26, 12))
        lab(f, t, 96, fr, txt, pos, size=110 if kind == "m" else 84, angle=-3 + 2 * (k % 3), t_out=nxt, **style)
    return f


def sc_skinner(t):                                # 97
    f = darken(sepia(cam(BG["bg_skinner"], 0.5, 0.5, 1.0 + 0.05 * SG(t, 97)), 0.25), 0.1)
    lab(f, t, 97, 0.05, "1950s", (440, 150), size=84, face="cinzel", **NAVY_L)
    lab(f, t, 97, 0.18, "B. F. SKINNER", (1450, 150), size=56)
    lab(f, t, 97, 0.40, "RANDOM REWARDS", (440, 260), size=56, **RED_L)
    if t > AT(97, 0.25):                                         # lever-press counter: irregular, keeps climbing
        n = int((t - AT(97, 0.25)) * 9 + 4 * math.sin((t - AT(97, 0.25)) * 3) ** 2)
        d = ImageDraw.Draw(f)
        d.rounded_rectangle((1330, 780, 1790, 960), 20, fill=(20, 14, 8, 235), outline=GOLD, width=6)
        d.text((1560, 815), "PRESSES", font=cinzel(30, "Bold"), fill=GOLD, anchor="mm")
        d.text((1560, 905), str(n), font=font(100), fill=(255, 240, 200), anchor="mm")
    lab(f, t, 97, 0.80, "KEEPS PRESSING", (440, 370), size=56)
    return f


def sc_slot(t):                                   # 98: the slot machine inside your phone
    f = cam(BG["bg_city"], 0.55, 0.45, 1.35)
    f = darken(f, 0.45, (20, 0, 30))
    char(f, "woman_phone", t, LS(98) - 0.2, 430, 1060, 760, enter="left")
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse((330, 330, 530, 530), fill=(255, 60, 160, 70))
    f.alpha_composite(gl.filter(ImageFilter.GaussianBlur(40)))
    t_in = AT(98, 0.05)
    if t > t_in:
        k = ease_out_back(clamp01((t - t_in) / 0.45))
        x0, y0, wbox, hbox = 860 + (1 - k) * 900, 250, 820, 470
        d = ImageDraw.Draw(f)
        neon = (255, 60, 170) if int(t * 6) % 7 else (255, 150, 220)
        d.rounded_rectangle((x0, y0, x0 + wbox, y0 + hbox), 40, fill=(60, 10, 40), outline=neon, width=10)
        for b in range(18):
            bx = x0 + 40 + b * (wbox - 80) / 17; on = (b + int(t * 10)) % 3 == 0
            for by in (y0 + 22, y0 + hbox - 22):
                d.ellipse((bx - 9, by - 9, bx + 9, by + 9), fill=(255, 230, 120) if on else (120, 80, 40))
        for r in range(3):
            stop_t = AT(98, 0.45 + 0.1 * r)
            if t < stop_t:
                off = ((t - t_in) * 2600 + r * 400) % (CELL * 16)
            else:
                off = (STOP_IDX[r] - 1) * CELL - math.sin(clamp01((t - stop_t) / 0.25) * math.pi) * 18
            strip = STRIPS[r].crop((0, int(off), CELL, int(off) + CELL * 2)).resize((210, 340))
            rx = x0 + 70 + r * 235
            f.alpha_composite(strip, (int(rx), y0 + 65))
            d.rectangle((rx, y0 + 65, rx + 210, y0 + 405), outline=(40, 10, 30), width=6)
        d.line((x0 + 50, y0 + 235, x0 + wbox - 50, y0 + 235), fill=(255, 60, 60, 160), width=3)
    lab(f, t, 98, 0.08, "SLOT MACHINE", (1270, 820), size=64, angle=-3, t_out=AT(98, 0.66))
    if t > AT(98, 0.68):
        a = 1.0 if int(t * 12) % 5 else 0.5
        ImageDraw.Draw(f).text((1270, 820), "YOUR PHONE", font=font(120), fill=(255, 90, 200, int(255 * a)), anchor="mm",
                               stroke_width=6, stroke_fill=(90, 0, 60))
    return f


def sc_games(t):                                  # 99-100
    f = darken(cam(BG["bg_city"], 0.5, 0.5, 1.2), 0.5, (20, 0, 30))
    char(f, "woman_phone", t, LS(99) - 0.2, 400, 1060, 760, enter="left")
    pop_img(f, t, AT(99, 0.5), BADGE["coin"].resize((420, 420), Image.LANCZOS), (1500, 640))
    lab(f, t, 99, 0.10, "YOUR GAME: FIND SOMEONE", (700, 190), size=56, **GRN_L)
    lab(f, t, 99, 0.55, "THE APP'S GAME: KEEP PLAYING", (1350, 330), size=52, **RED_L)
    lab(f, t, 100, 0.30, "THE APP WINS WHEN YOU STAY", (960, 850), size=60, angle=-2, **RED_L, t_out=AT(100, 0.58))
    lab(f, t, 100, 0.60, "THE HOUSE ALWAYS WINS", (960, 850), size=70, angle=2, **NAVY_L, t_out=AT(100, 0.84))
    lab(f, t, 100, 0.86, "UNLESS YOU KNOW THE RULES", (960, 850), size=64, **GRN_L)
    return f


# ---- CHAPTER 7: when to stop searching (lines 101-107)
def sc_search(t):                                 # 101
    f = stage(t, 0.12, cy=0.6); darken(f, 0.15); motes(f, t)
    char(f, "man_curious", t, LS(101) - 0.2, 960, 1030, 780, enter="bottom")
    qmarks(f, t, AT(101, 0.2))
    lab(f, t, 101, 0.40, "HOW MUCH SEARCHING IS ENOUGH?", (960, 140), size=62, **NAVY_L)
    return f


DOOR_Q = [0.40, 0.55, 0.35, 0.80, 0.50, 0.60, 0.70]
DOOR_OPEN = {0: AT(103, 0.25), 1: AT(103, 0.45), 2: AT(103, 0.65), 3: AT(105, 0.45)}


def draw_door(f, k, t):
    x, y, w_, h_ = 185 + k * 230, 300, 170, 400
    d = ImageDraw.Draw(f)
    tin = AT(102, 0.35 + 0.07 * k)
    if t < tin:
        return
    pop = ease_out_back(clamp01((t - tin) / 0.35)); dy = (1 - pop) * 200
    y += dy
    d.rounded_rectangle((x - 12, y - 12, x + w_ + 12, y + h_ + 12), 16, fill=(50, 30, 16))
    op = ease(clamp01((t - DOOR_OPEN[k]) / 0.5)) if k in DOOR_OPEN else 0.0
    star = k == 3 and t > DOOR_OPEN[3] + 0.4
    if op > 0.02:
        d.rectangle((x, y, x + w_, y + h_), fill=(255, 226, 150) if star else (60, 44, 30))
        person_glyph(d, x + w_ / 2, y + 170, (250, 250, 250) if not star else (255, 200, 60), 1.2)
        q = DOOR_Q[k]
        d.rectangle((x + 20, y + h_ - 56, x + w_ - 20, y + h_ - 30), outline=(250, 240, 215), width=4)
        d.rectangle((x + 22, y + h_ - 54, x + 22 + (w_ - 44) * q, y + h_ - 32), fill=GOLD)
    leaf = w_ * (1 - op)
    if leaf > 4:
        d.rectangle((x, y, x + leaf, y + h_), fill=(130, 84, 46), outline=(40, 24, 12), width=4)
        d.rectangle((x + 16, y + 28, x + max(18, leaf - 16), y + 150), outline=(90, 56, 28), width=4)
        d.rectangle((x + 16, y + 190, x + max(18, leaf - 16), y + 360), outline=(90, 56, 28), width=4)
        d.ellipse((x + leaf - 34, y + 200, x + leaf - 14, y + 220), fill=GOLD)
    if star:
        glow_rect(f, (x, y, x + w_, y + h_), t, DOOR_OPEN[3] + 0.4)
        d.polygon([(x + w_ / 2 + 70 * math.cos(math.radians(-90 + 36 * q)) * (1 if q % 2 == 0 else 0.42),
                    y - 60 + 70 * math.sin(math.radians(-90 + 36 * q)) * (1 if q % 2 == 0 else 0.42)) for q in range(10)],
                  fill=(255, 220, 70), outline=(150, 100, 26))


def sc_doors(t):                                  # 102-106
    f = blurred(cam(BG["doors"], 0.5, 0.5, 1.0 + 0.05 * SG(t, 102, 106)), 8, 0.45)
    for k in range(7):
        draw_door(f, k, t)
    lab(f, t, 102, 0.20, "1960", (1650, 150), size=84, face="cinzel", **NAVY_L)
    lab(f, t, 102, 0.50, "THE SECRETARY PROBLEM", (800, 150), size=60, t_out=LS(103))
    lab(f, t, 103, 0.82, "NO GOING BACK", (960, 800), size=84, angle=-3, **RED_L, t_out=LS(104))
    frac = 0.0
    if t > AT(104, 0.2):
        frac = 0.37 * ease(clamp01((t - AT(104, 0.2)) / (0.6 * (EN(104) - LS(104)))))
    if t > AT(105, 0.0):
        frac = 0.37 + 0.18 * ease(clamp01((t - LS(105)) / (EN(105) - LS(105)))) if t > LS(105) else frac
    if t > AT(104, 0.2):
        progress_bar(f, frac, y=930, mark=0.37, label_txt="37%")
    lab(f, t, 104, 0.30, "JUST LOOK. DON'T COMMIT.", (960, 765), size=64, **NAVY_L, t_out=LS(105))
    lab(f, t, 105, 0.62, "BETTER THAN ALL SO FAR", (960, 765), size=64, **GRN_L, t_out=LS(106))
    lab(f, t, 106, 0.45, "NOT PERFECT. BEST ODDS.", (960, 765), size=64)
    return f


def sc_enough(t):                                 # 107
    f = stage(t, 0.12, cy=0.6); darken(f, 0.3); spot(f, 0.5); motes(f, t, alpha=150)
    char(f, "man_curious", t, LS(107) - 0.2, 470, 1030, 720, enter="left")
    char(f, "woman_confident", t, LS(107), 1450, 1030, 730, enter="right", phase=1.3)
    lab(f, t, 107, 0.32, "SEARCH FOREVER = LOSE", (960, 250), size=66, angle=-3, **RED_L)
    gtitle(f, t, AT(107, 0.78), "GOOD ENOUGH IS THE WIN", 420, 100)
    return f


# ---- CHAPTER 8: how to win (lines 108-119)
def sc_four2(t):                                  # 108
    k = clamp01((t - LS(108)) / 0.8)
    f = stage(t, 0.14, cy=0.6)
    darken(f, 0.25 + 0.25 * k); spot(f, k); motes(f, t, alpha=150)
    char(f, "man_curious", t, LS(108) - 0.2, 470 + 120 * ease(k), 1030, 720, enter="left")
    char(f, "woman_confident", t, LS(108), 1450 - 120 * ease(k), 1030, 730, enter="right", phase=1.3)
    gtitle(f, t, AT(108, 0.40), "4 LESSONS", 320, 170)
    return f


LESSONS = [(109, "MAKE THE FIRST MOVE", "GALE & SHAPLEY", "strategy"), (110, "SEND COSTLY SIGNALS", "THE PEACOCK", "peacock"),
           (111, "TRUST. FORGIVE. PLAY LONG.", "AXELROD", "payoff"), (112, "EXPLORE... THEN STOP", "THE 37% RULE", "bar")]


def sc_lessons(t):                                # 109-112
    f = blurred(stage(t, 0.1), 10, 0.5)
    for k, (n, title, sub, icon) in enumerate(LESSONS):
        x, y = (500 if k % 2 == 0 else 1420), (330 if k < 2 else 700)
        tin = AT(n, 0.10)
        if t < tin:
            continue
        flip = clamp01((t - tin) / 0.45)
        kk = abs(math.cos((1 - ease(flip)) * math.pi / 2)) if flip < 1 else 1.0
        card(f, x, y, 820, 300, title, sub, k=kk, size=46, dx=-50)
        if kk > 0.9:
            d = ImageDraw.Draw(f)
            d.ellipse((x - 380, y - 130, x - 310, y - 60), fill=GOLD, outline=(40, 26, 12), width=4)
            d.text((x - 345, y - 95), str(k + 1), font=font(48), fill=(40, 26, 12), anchor="mm")
            if icon == "peacock":
                im = scaled("peacock", 140); f.alpha_composite(im, (round(x + 325 - im.width / 2), round(y + 100 - im.height)))
            elif icon == "bar":
                progress_bar(f, 0.37, x=x + 325, y=y + 90, w=110, mark=0.37)
            else:
                f.alpha_composite(SMALL[icon].resize((110, 110), Image.LANCZOS), (x + 270, y - 55))
    return f


def sc_dinner(t):                                 # 113
    f = darken(sepia(blurred(cam(BG["bg_castle"], 0.5, 0.5, 1.05 + 0.04 * SG(t, 113)), 4, 0.7), 0.3), 0.15)
    motes(f, t, (255, 230, 170), 24, 80)
    char(f, "families_deal", t, LS(113) - 0.1, 960, 1050, 560, enter="bottom")
    lab(f, t, 113, 0.18, "FOR THOUSANDS OF YEARS", (960, 190), size=60, **NAVY_L)
    lab(f, t, 113, 0.48, "AT DINNER TABLES YOU WERE NEVER INVITED TO", (960, 330), size=54, **RED_L)
    return f


def sc_every(t):                                  # 114-115: pull back from the city to the whole world
    pull = ease(clamp01((t - LS(114)) / (0.6 * (EN(114) - LS(114)))))
    city = darken(cam(BG["bg_city"], 0.5, 0.5, 1.7 - 0.7 * pull), 0.25, (20, 0, 30))
    k = ease(clamp01((t - AT(114, 0.55)) / 0.7))
    if k <= 0:
        f = city
    else:
        mp = cam(BG["bg_map"], 0.5, 0.48, 1.0)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        t0, t1 = AT(114, 0.62), AT(115, 0.30)
        for (x, y), ht in zip(LAND, HEART_T):
            ti = lerp(t0, t1, ht)
            if t < ti:
                continue
            s = ease_out_back(clamp01((t - ti) / 0.3), 2.5)
            px, py = x * W, y * H
            d.polygon(heart_pts(px, py, 24 * s * (1 + 0.1 * math.sin(t * 6 + x * 30))), fill=BLOOD, outline=(255, 235, 220))
        mp.alpha_composite(lay)
        f = Image.blend(city.convert("RGB"), mp.convert("RGB"), k).convert("RGBA")
    lab(f, t, 114, 0.55, "MILLIONS OF US", (960, 150), size=70, **NAVY_L, t_out=LS(115))
    lab(f, t, 114, 0.82, "EVERY SINGLE NIGHT", (960, 280), size=70, **RED_L, t_out=LS(115))
    lab(f, t, 115, 0.20, "THE RULES WERE NEVER WRITTEN DOWN", (960, 150), size=62)
    return f


def sc_nowknow(t):                                # 116
    f = stage(t, 0.14, cy=0.6)
    darken(f, 0.4); spot(f, 0.8); motes(f, t, alpha=170)
    char(f, "man_curious", t, -10, 600, 1030, 720)
    char(f, "woman_confident", t, -10, 1320, 1030, 730, phase=1.3)
    gtitle(f, t, AT(116, 0.35), "NOW YOU KNOW", 300, 170)
    return f


def sc_comment(t):                                # 117
    f = stage(t, 0.1, cy=0.6); darken(f, 0.2); motes(f, t)
    char(f, "man_curious", t, LS(117) - 0.2, 470, 1030, 720, enter="left")
    char(f, "woman_confident", t, LS(117), 1450, 1030, 730, enter="right", phase=1.3)
    lab(f, t, 117, 0.28, "MOVE FIRST?", (470, 250), size=66, **GRN_L)
    lab(f, t, 117, 0.45, "WAIT AND SEE?", (1450, 250), size=66, bg=AMBER, fg=(40, 26, 12))
    lab(f, t, 117, 0.76, "FIGHT IT OUT BELOW", (960, 560), size=78, angle=-3, **NAVY_L)
    return f


FLAGS = [(0.22, 0.34, (200, 40, 40)), (0.30, 0.55, (40, 100, 200)), (0.50, 0.28, (240, 200, 40)), (0.55, 0.50, (40, 150, 90)),
         (0.66, 0.34, (220, 120, 40)), (0.76, 0.44, (160, 60, 180)), (0.84, 0.66, (40, 160, 200)), (0.42, 0.66, (230, 230, 230))]


def sc_next(t):                                   # 118
    f = darken(cam(BG["bg_map"], 0.5, 0.48, 1.0 + 0.06 * SG(t, 118)), 0.35)
    d = ImageDraw.Draw(f)
    for k, (x, y, col) in enumerate(FLAGS):
        tin = AT(118, 0.30 + 0.07 * k)
        if t > tin:
            s = ease_out_back(clamp01((t - tin) / 0.35)); px, py = x * W, y * H
            d.line((px, py, px, py - 110 * s), fill=(30, 20, 10), width=6)
            wave = 6 * math.sin(t * 5 + k)
            d.polygon([(px, py - 110 * s), (px + 70 * s, py - 96 * s + wave), (px, py - 70 * s)], fill=col, outline=(30, 20, 10))
    lab(f, t, 118, 0.45, "NEXT: A GAME PLAYED BY NATIONS", (960, 150), size=66, **NAVY_L)
    return f


def sc_end(t):                                    # 119: end card
    f = Image.new("RGBA", (W, H), (8, 7, 6, 255))
    y_, x_ = np.ogrid[0:H:4, 0:W:4]
    m = np.exp(-(((x_ - W / 2) / 760) ** 2 + ((y_ - H / 2) / 360) ** 2)) * 60
    f.alpha_composite(Image.fromarray(np.dstack([m, m * 0.62, m * 0.25, m * 2.2]).clip(0, 255).astype(np.uint8),
                                      "RGBA").resize((W, H), Image.BILINEAR))
    motes(f, t, alpha=150)
    gtitle(f, t, LS(119) + 0.1, "DEEP TIME ACADEMY", 360, 120)
    d = ImageDraw.Draw(f)
    w_ = 520 * ease(clamp01((t - LS(119) - 0.4) / 0.6))
    d.line((W / 2 - w_, 450, W / 2 + w_, 450), fill=(190, 30, 30), width=5)
    k = ease_out_back(clamp01((t - AT(119, 0.42)) / 0.4))
    if k > 0.02:
        pw, ph = 460 * k, 120 * k
        d.rounded_rectangle((W / 2 - pw / 2, 600 - ph / 2, W / 2 + pw / 2, 600 + ph / 2), 60, fill=(210, 30, 30), outline=(255, 255, 255), width=5)
        if k > 0.9:
            d.text((W / 2, 603), "SUBSCRIBE", font=font(70), fill=(255, 255, 255), anchor="mm")
    if t > AT(119, 0.70):
        a = int(255 * clamp01((t - AT(119, 0.70)) / 0.5))
        d.text((W / 2, 780), "GAME THEORY  ·  EPISODE 2  ·  COMING SOON", font=cinzel(40, "Bold"), fill=CREAM + (a,), anchor="mm")
    if t > TOTAL - 1.2:
        darken(f, (t - (TOTAL - 1.2)) / 1.2)
    return f


# ======================================================================= wiring: scenes, crossfades, chapter cards
import shutil, subprocess, tempfile

OPEN_SCENES = [(0.0, sc_map, True), (L(1) - 0.15, sc_city, True), (L(2) - 0.3, sc_rules, True),
               (L(3) - 0.1, sc_stakes, True), (L(4) - 0.2, sc_title, False), (STING, sc_sting, False),
               (L(5) - 0.05, sc_strange, True), (L(6) - 0.1, sc_years, True), (L(7) - 0.2, sc_profs, True),
               (L(8) - 0.2, sc_chalk, True), (L(9) - 0.1, sc_nobel, True), (L(10) - 0.15, sc_twist, True),
               (L(11) - 0.3, sc_firstmove, True), (L(12) - 0.2, sc_casino, True), (L(13) - 0.3, sc_finale, True)]

STORY_SCENES = [(15, sc_hist), (17, sc_panels), (18, sc_families), (20, sc_pick), (21, sc_market), (23, sc_gt),
                (24, sc_decide), (25, sc_book), (26, sc_nash), (27, sc_four), (32, sc_lenses),
                (38, sc_gs), (39, sc_algo), (47, sc_proved), (48, sc_twist2), (49, sc_moves), (52, sc_lying), (54, sc_hard),
                (55, sc_doctors), (56, sc_schools), (57, sc_nobel2),
                (58, sc_crack), (60, sc_hidden), (62, sc_signal), (63, sc_spence), (65, sc_peacock), (69, sc_costless),
                (70, sc_drive), (71, sc_costly), (72, sc_hey),
                (73, sc_trap1), (75, sc_matrix), (79, sc_openup), (82, sc_escape), (83, sc_axelrod), (85, sc_tft),
                (87, sc_repeat), (88, sc_shadow),
                (90, sc_phone), (93, sc_oneswipe), (94, sc_pyramid), (95, sc_swipe), (97, sc_skinner), (98, sc_slot),
                (99, sc_games),
                (101, sc_search), (102, sc_doors), (107, sc_enough),
                (108, sc_four2), (109, sc_lessons), (113, sc_dinner), (114, sc_every), (116, sc_nowknow),
                (117, sc_comment), (118, sc_next), (119, sc_end)]


def _card_fn(num, title, t0):
    return lambda t: chapter_card(t, t0, num, title, 2.3)


CARD_START = {first: END(first - 2) + 0.3 for first in CARDS}
SCENES = list(OPEN_SCENES)
for first, (num, title) in CARDS.items():
    SCENES.append((CARD_START[first], _card_fn(num, title, CARD_START[first]), False))
for first, fn in STORY_SCENES:
    SCENES.append((LS(first) - (0.1 if first in CARDS else 0.2), fn, fn is not sc_end))
SCENES.sort(key=lambda s: s[0])
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


# ======================================================================= audio: music rules + sound-effect cues
CARD_WINDOWS = [(CARD_START[f] - 0.2, CARD_START[f] + 2.4) for f in CARDS]
SERIOUS_LINES = [11, 16, 21, 36, 48, 78, 81, 100, 113, 114, 115, 116]     # music pizzicato drops out under these


def mgain(tm):        # pizzicato on/off by section
    if tm < L(2): return 0.0
    if tm < L(4): return 0.7
    if tm < L(5): return 0.0
    for n in SERIOUS_LINES:
        if L(n - 1) <= tm < END(n - 1) + 0.3: return 0.0
    for a, b in CARD_WINDOWS:
        if a <= tm < b: return 0.0
    return 1.0


def dgain(tm):        # overall bed level
    if STING - 0.2 < tm < L(5): return 0.35
    for a, b in CARD_WINDOWS:
        if a <= tm < b: return 0.45
    if tm > TOTAL - 5: return 0.8
    return 1.0


# (script line, fraction of that line, sound). Fractions match the on-screen events above.
FXT = (
    [(15, .05, "pop"), (15, .30, "pop"), (16, .50, "hit")]
    + [(17, f, "pop") for f in (.0, .12, .38, .62, .84)]
    + [(18, .12, "coin"), (18, .46, "coin"), (18, .80, "boom"), (19, .05, "pop"), (19, .60, "pop"), (19, .65, "pop"), (19, .85, "hit")]
    + [(20, .04, "pop"), (20, .40, "pop"), (20, .86, "pop"), (20, .88, "pop")]
    + [(21, .42, "pop"), (21, .68, "screech"), (21, .84, "hit"), (22, .12, "pop"), (22, .45, "pop"), (22, .78, "pop"), (23, .35, "riser_hit")]
    # chapter 2
    + [(24, .05, "pop"), (24, .20, "pop"), (24, .30, "pop"), (24, .50, "chalk"), (24, .72, "chalk")]
    + [(25, .10 + .5 * (k / 22) ** .6, "tick") for k in range(23)] + [(25, .60, "pop"), (25, .78, "pop")]
    + [(26, .18, "chalk"), (26, .25, "chalk"), (26, .32, "chalk"), (26, .39, "chalk"), (26, .22, "pop"), (26, .50, "hit")]
    + [(27, .30, "riser_hit")] + [(n, f, "pop") for n in (28, 29, 30, 31) for f in (.06, .18)]
    + [(32, f, "pop") for f in (.15, .35, .55, .75)] + [(33, .25, "pop"), (33, .60, "pop")]
    + [(34, .05, "pop"), (34, .38, "pop"), (34, .70, "pop"), (35, .10, "pop"), (35, .30, "pop"), (35, .50, "pop"), (35, .78, "screech"),
       (35, .80, "hit"), (36, .10, "pop"), (36, .24, "hit"), (37, .55, "riser_hit")]
    # chapter 3
    + [(38, .30, "pop"), (38, .50, "pop")]
    + [(39, .06 + .1 * i, "pop") for i in range(4)] + [(39, .40 + .1 * i, "pop") for i in range(4)]
    + [(40, f, "chalk") for f in (.25, .35, .45, .55)] + [(41, .30, "pop"), (41, .30, "screech"), (41, .36, "screech"), (41, .42, "screech")]
    + [(42, .30, "chalk"), (42, .45, "chalk"), (43, .30, "screech"), (43, .38, "screech"), (43, .45, "hit")]
    + [(44, f, "chalk") for f in (.12, .18, .36, .62)] + [(44, f, "screech") for f in (.20, .46)] + [(44, f, "pop") for f in (.06, .30, .56)]
    + [(45, .35, "shimmer"), (45, .45, "coin"), (46, .15, "chalk"), (46, .62, "screech"), (46, .64, "pop")]
    + [(47, .45, "riser_hit"), (47, .78, "pop"), (48, .62, "hit")]
    + [(49, .05, "pop"), (49, .30, "coin"), (50, .00, "pop"), (50, .32, "boom"), (51, .10, "pop"), (51, .30, "swish"), (51, .62, "pop")]
    + [(52, .40, "pop"), (53, .28, "pop"), (53, .58, "hit"), (54, .08, "pop"), (54, .40, "riser_hit"), (54, .78, "coin")]
    + [(55, .08 + .07 * i, "pop") for i in range(4)] + [(55, .30 + .05 * k, "tick") for k in range(8)] + [(55, .70, "pop")]
    + [(56, .08, "pop")] + [(56, .18 + .14 * k, "pop") for k in range(4)] + [(57, .12, "boom"), (57, .12, "swish"), (57, .22, "shimmer"), (57, .55, "pop")]
    # chapter 4
    + [(58, .55, "screech"), (58, .70, "hit"), (59, .08, "pop"), (60, .30, "pop"), (60, .40, "pop")]
    + [(61, f, "pop") for f in (.10, .30, .50, .66)] + [(61, .83, "hit"), (62, .30, "riser_hit"), (62, .78, "pop")]
    + [(63, .10, "pop"), (63, .45, "pop"), (64, .10, "shimmer"), (64, .22, "pop"), (64, .62, "pop")]
    + [(65, .20, "pop"), (66, .15, "pop"), (66, .35, "hit"), (67, .35, "swish"), (67, .72, "pop"), (68, .30, "riser_hit")]
    + [(69, .25, "hit")] + [(69, .45 + .055 * k, "tick") for k in range(9)]
    + [(70, .10, "pop"), (70, .45, "pop"), (70, .78, "pop"), (70, .05, "swish"), (71, .20, "coin"), (71, .30, "pop"), (71, .45, "riser_hit"), (71, .75, "pop")]
    + [(72, .06 + .075 * k, "tick") for k in range(7)] + [(72, .64, "hit")]
    # chapter 5
    + [(73, .45, "pop"), (74, .05, "pop"), (74, .28, "pop"), (74, .62, "riser_hit")]
    + [(75, .12, "swish")] + [(75, .20 + .06 * k, "pop") for k in range(4)] + [(76, .10, "pop"), (76, .55, "pop"), (77, .55, "pop"), (78, .12, "pop"), (78, .35, "hit")]
    + [(79, f, "pop") for f in (.12, .42, .72)] + [(80, .30, "pop"), (80, .70, "pop"), (81, .55, "hit"), (82, .30, "pop"), (82, .2, "pop")]
    + [(83, .04, "pop"), (83, .30, "pop")] + [(83, .05 + .04 * k, "tick") for k in range(15)] + [(84, .50, "coin"), (84, .62, "riser_hit")]
    + [(85, .08, "pop"), (85, .50, "pop"), (86, .10, "pop"), (86, .30, "pop"), (86, .50, "pop"), (86, .80, "riser_hit")]
    + [(87, .08, "pop"), (87, .52, "coin"), (88, .45, "riser_hit"), (89, .30, "pop"), (89, .82, "heart")]
    # chapter 6
    + [(90, .40, "pop")] + [(91, .05 + .85 * k / 36, "tick") for k in range(0, 36, 2)] + [(91, .30, "pop"), (92, .05, "pop"), (92, .62, "hit")]
    + [(93, .25, "pop")] + [(93, f, "swish") for f in (.30, .52, .74)] + [(94, .10, "pop"), (94, .72, "pop")]
    + [(94, .08 + .05 * k, "pop") for k in range(6)]
    + [(95, .30, "pop"), (96, .04, "tick"), (96, .13, "tick"), (96, .25, "tick"), (96, .33, "tick"), (96, .45, "tick"), (96, .56, "coin"),
       (96, .72, "tick"), (96, .82, "tick"), (96, .92, "tick")]
    + [(97, .05, "pop"), (97, .18, "pop"), (97, .40, "pop"), (97, .80, "pop")] + [(97, .25 + .04 * k, "tick") for k in range(16)]
    + [(98, .08, "pop"), (98, .68, "hit")] + [(98, .05 + .018 * k, "tick") for k in range(30)] + [(98, .45 + .1 * r, "pop") for r in range(3)]
    + [(98, .68 + .02 * k, "coin") for k in range(5)]
    + [(99, .10, "pop"), (99, .50, "coin"), (99, .55, "pop"), (100, .30, "hit"), (100, .60, "pop"), (100, .86, "pop")]
    # chapter 7
    + [(101, .20, "pop"), (101, .40, "pop"), (102, .20, "pop"), (102, .50, "pop")] + [(102, .35 + .07 * k, "pop") for k in range(7)]
    + [(103, .25, "swish"), (103, .45, "swish"), (103, .65, "swish"), (103, .82, "hit"), (104, .20, "pop"), (104, .30, "pop"), (105, .45, "swish"),
       (105, .50, "shimmer"), (105, .62, "coin"), (106, .45, "pop"), (107, .32, "hit"), (107, .78, "riser_hit")]
    # chapter 8
    + [(108, .40, "riser_hit")] + [(n, .10, "swish") for n in (109, 110, 111, 112)] + [(n, .20, "pop") for n in (109, 110, 111, 112)]
    + [(113, .18, "pop"), (113, .48, "hit"), (114, .55, "pop"), (114, .82, "pop"), (115, .20, "pop")]
    + [(114, .62 + .02 * k, "tick") for k in range(18)]
    + [(116, .35, "riser_hit"), (117, .28, "pop"), (117, .45, "pop"), (117, .76, "pop"), (118, .45, "pop")]
    + [(118, .30 + .07 * k, "pop") for k in range(8)] + [(119, .10, "shimmer"), (119, .42, "pop")]
)


def fx_play(fx, name, tm):
    if name == "pop": place(fx, sfx("pop"), tm)
    elif name == "tick": place(fx, sfx("tick") * 1.2, tm)
    elif name == "coin": place(fx, sfx("coin"), tm)
    elif name == "boom": place(fx, sfx("boom") * 0.5, tm)
    elif name == "hit": place(fx, fx_hit(), tm)
    elif name == "shimmer": place(fx, fx_shimmer(), tm)
    elif name == "chalk": place(fx, fx_chalk(0.25), tm)
    elif name == "screech": place(fx, sfx("screech") * 0.35, tm)
    elif name == "heart": place(fx, fx_heartbeat(), tm)
    elif name == "swish": place(fx, sfx("whoosh") * 0.3, tm)
    elif name == "riser_hit":
        place(fx, fx_riser(1.3) * 0.7, tm - 1.3); place(fx, fx_hit(), tm); place(fx, fx_shimmer(), tm + 0.3)
    else:
        raise ValueError(name)


def build_audio():
    voice = TL.voice_track()
    fx = np.zeros_like(voice)
    mus = music(TOTAL, mgain, dgain)[:len(voice)]
    # ---- opening (lines 1-14), unchanged
    for s, fn, _ in OPEN_SCENES[1:]:
        if fn not in (sc_sting,):
            place(fx, sfx("whoosh") * 0.35, s - 0.35)
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
    place(fx, fx_riser(1.0) * 0.8, STING); place(fx, sfx("boom") * 1.1, STING + 0.9); place(fx, fx_shimmer(2.6) * 1.5, STING + 1.1)
    place(fx, sfx("pop"), at(5, 0.35))
    for k in range(26):
        place(fx, sfx("tick") * 1.4, at(6, 0.15 + 0.65 * (k / 25) ** 0.6))
    place(fx, sfx("boom") * 0.5, at(6, 0.82)); place(fx, sfx("pop"), at(6, 0.85))
    place(fx, sfx("pop"), at(7, 0.0)); place(fx, sfx("pop"), at(7, 0.5)); place(fx, sfx("pop"), at(7, 0.62))
    for n_ in range(4):
        place(fx, fx_chalk(0.2), at(8, 0.25 + 0.06 * n_)); place(fx, fx_chalk(0.3), at(8, 0.64 + 0.07 * n_))
    place(fx, sfx("screech") * 0.4, at(8, 0.5))
    place(fx, sfx("coin") * 1.5, L(9) + 0.2); place(fx, sfx("pop"), L(9) + 0.2)
    place(fx, sfx("whoosh") * 0.5, at(9, 0.3)); place(fx, fx_shimmer(2.6) * 1.8, at(9, 0.3) + 0.3)
    place(fx, sfx("boom") * 0.6, at(9, 0.3) + 0.6)
    place(fx, fx_hit() * 1.2, at(10, 0.72))
    place(fx, sfx("pop"), at(11, 0.02)); place(fx, sfx("coin"), at(11, 0.02) + 0.9)
    place(fx, sfx("pop"), at(11, 0.55)); place(fx, sfx("boom") * 0.4, at(11, 0.55) + 0.9)
    for k in range(40):
        tk = at(12, 0.05) + k * 0.09
        if tk < at(12, 0.74):
            place(fx, sfx("tick") * 0.9, tk)
    for r in range(3):
        place(fx, sfx("pop") * 0.8, at(12, 0.5 + 0.12 * r))
    for k in range(6):
        place(fx, sfx("coin") * 0.9, at(12, 0.8) + k * 0.08)
    place(fx, fx_riser(1.2) * 0.6, at(13, 0.6) - 1.2); place(fx, fx_hit(), at(13, 0.6)); place(fx, fx_shimmer(3.0) * 1.4, at(13, 0.6) + 0.3)
    # ---- the story (lines 15-119)
    for first, fn in STORY_SCENES:
        place(fx, sfx("whoosh") * 0.3, LS(first) - (0.1 if first in CARDS else 0.2) - 0.3)
    for first in CARDS:                                           # chapter cards
        t0 = CARD_START[first]
        place(fx, sfx("whoosh") * 0.4, t0 - 0.3); place(fx, sfx("boom") * 0.5, t0 + 0.3); place(fx, fx_shimmer(), t0 + 0.3)
    for n, fr, name in FXT:
        fx_play(fx, name, AT(n, fr))
    out = p("_mix.wav")
    finish_audio(voice, mus, fx, out, HERE)
    return out


# ======================================================================= rendering (parallel chunks, 4 cores)
def _render_chunk(job):
    k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        t = k / FPS
        arr = np.asarray(frame_at(t).convert("RGB")).astype(np.float32) * VIG
        if t < 0.3:
            arr *= t / 0.3
        ff.stdin.write(arr.astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    return path


def render_parallel(total, audio_wav, out_mp4, procs=4, parts=16):
    import multiprocessing as mp
    nf = int(round(total * FPS))
    tmp = tempfile.mkdtemp(prefix="dta_parts_", dir=HERE)
    bounds = [round(nf * i / parts) for i in range(parts + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(tmp, f"part{i:02d}.mp4")) for i in range(parts)]
    with mp.get_context("fork").Pool(procs) as pool:
        for n, path in enumerate(pool.imap_unordered(_render_chunk, jobs), 1):
            print(f"chunk {n}/{parts} done", flush=True)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio_wav,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    if PLACEHOLDERS and not os.environ.get("ALLOW_PLACEHOLDER"):
        sys.exit(f"STOP: {len(PLACEHOLDERS)} lines have no real voice yet (e.g. {PLACEHOLDERS[:6]}). "
                 f"Voice them (see PRODUCTION_PLAN.md) and re-run. Set ALLOW_PLACEHOLDER=1 only for a silent layout test.")
    wav = build_audio()
    out = p("dating_game_full_v1.mp4")
    render_parallel(TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
