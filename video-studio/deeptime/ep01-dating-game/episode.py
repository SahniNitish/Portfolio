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
def mgain(tm):        # pizzicato on/off by section
    if tm < L(2): return 0.0
    if tm < L(4): return 0.7
    if tm < L(5): return 0.0
    if L(10) <= tm < L(11): return 0.0
    return 1.0


def dgain(tm):        # overall bed level
    if STING - 0.2 < tm < L(5): return 0.35
    return 1.0


def build_audio():
    voice = TL.voice_track()
    fx = np.zeros_like(voice)
    mus = music(TOTAL, mgain, dgain)[:len(voice)]
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
    out = p("dating_game_v2.mp4")
    render(frame_at, TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
