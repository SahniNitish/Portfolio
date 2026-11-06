"""Deep Time Academy whiteboard video: "Why School Sucks, According to Game Theory" (white paper, stick figures, 16:9).

Script by the user (topic: Prof. Jiang Xueqin's Predictive History lecture; credit him in the description). Voice: Kokoro draft (free), swap
audio/clean/l1..l58.wav for Fish WNBA VOICEOVER (about 7,200 credits) and rerun. Helpers come from wb01-fake-it (imported as a module) and stick.py.

    python deeptime/wb05-school-game/episode.py          # renders wb05_school_game.mp4 (about 10 min on 4 cores)
Scene timing uses SCRIPT LINE NUMBERS (lines.txt, 1-based): AT(n, frac), SG(t, n, m), LS(n), EN(n).
"""
import importlib.util, math, os, random, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import Timeline, finish_audio, place, FPS  # noqa: E402
from stick import *                                    # noqa: E402,F401,F403
import stick as S                                      # noqa: E402

_spec = importlib.util.spec_from_file_location("wb01", os.path.join(HERE, "..", "wb01-fake-it", "episode.py"))
wb = importlib.util.module_from_spec(_spec); sys.modules["wb01"] = wb; _spec.loader.exec_module(wb)
fig, tag, cap, hold, appear, pp, sparkle_burst, poof, glow_pulse = wb.fig, wb.tag, wb.cap, wb.hold, wb.appear, wb.pp, wb.sparkle_burst, wb.poof, wb.glow_pulse
p = lambda *a: os.path.join(HERE, *a)
random.seed(5)
WHITE = (255, 255, 255)

N = 58
GAPS = [0.5] * N
for n, g in {2: 0.8, 4: 0.9, 5: 1.0, 6: 1.1, 12: 0.8, 17: 0.9, 19: 1.1, 29: 0.8, 33: 0.8, 37: 1.0, 45: 0.9, 52: 1.0, 54: 0.9, 56: 0.9, 58: 3.0}.items():
    GAPS[n - 1] = g
TL = Timeline([p("audio", "clean", f"l{i}.wav") for i in range(1, N + 1)], GAPS, lead=0.7)
L, END, TOTAL = TL.L, TL.end, TL.total
def AT(n, frac): return L(n - 1) + frac * (END(n - 1) - L(n - 1))
def SG(t, n, m=None): m = n if m is None else m; return clamp01((t - L(n - 1)) / max(END(m - 1) - L(n - 1), 1e-6))
def LS(n): return L(n - 1)
def EN(n): return END(n - 1)


def base(t, u=0.0, zoom=0.035, cx=960, cy=540, shake=0.0, bg=PAPER):
    z = 1.0 + zoom * u
    sx, sy = (random.uniform(-shake, shake), random.uniform(-shake, shake)) if shake else (0, 0)
    return Canvas(t, cam=(cx + sx, cy + sy, z), bg=bg)


def G(cv, y=900): ground(cv, y, 60, 1860)


def sign(cv, t, t_in, text, x, y, w=420, h=110, col=NAVY, fill=CREAM, size=56, rot=0, post=True):
    s = pp(t, t_in, 0.4)
    if s <= 0.02:
        return
    with cv.at(x, y, s, rot):
        if post:
            cv.line((0, h / 2), (0, h / 2 + 150), w=9, col=BROWN)
        cv.rect(-w / 2, -h / 2, w / 2, h / 2, r=10, fill=fill, w=7, col=col)
        cv.text(text, 0, 2, size=size, font="marker", col=col)


def card(cv, t, t_in, text, x, y, w=520, h=130, fill=CREAM, col=NAVY, size=54, rot=0, sub=None):
    s = pp(t, t_in, 0.4)
    if s <= 0.02:
        return
    with cv.at(x, y, s, rot):
        cv.rect(-w / 2, -h / 2, w / 2, h / 2, r=18, fill=fill, w=7, col=col)
        cv.text(text, 0, -6 if sub else 0, size=size, font="marker", col=col)
        if sub:
            cv.text(sub, 0, h * 0.28, size=size * 0.55, font="hand", col=GREY)


def books(cv, x, y, n=5, w=150, h=34, seed=1, reveal=1.0):
    rnd = random.Random(seed)
    cols = [RED, BLUE, GREEN, PURPLE, ORANGE, BROWN, NAVY]
    yy = y
    for i in range(n):
        ww = w * rnd.uniform(0.75, 1.05)
        cv.rect(x - ww / 2 + rnd.uniform(-10, 10), yy - h, x + ww / 2, yy, fill=cols[(i + seed) % len(cols)], w=4, reveal=reveal, amp=0.5)
        yy -= h


def person(cv, x, y, h=300, pose="stand", face="neutral", label=None, t=None, t_in=0, outfit=(), col=INK, lab_col=NAVY, flip=False):
    J = fig(cv, x, y, h=h, pose=pose, face=face, outfit=outfit, col=col, flip=flip)
    if label and t is not None:
        tag(cv, t, t_in, label, x, y + 52, size=34, col=lab_col)
    return J


def bigtext(cv, t, t_in, text, x, y, size=100, col=NAVY, band=LGOLD, rot=0, dur=0.5):
    tag(cv, t, t_in, text, x, y, size=size, col=col, band=band, dur=dur, rot=rot)


def crowd(cv, t, x0, y0, cols, rows, dx, dy, h=58, col=INK, face_seed=0):
    k = 0
    for r in range(rows):
        for c in range(cols):
            mini(cv, x0 + c * dx, y0 + r * dy, h=h, phase=(t * 1.2 + k * 0.37), swing=0.05, col=col, seed=k + face_seed)
            k += 1


# ======================================================================= COLD OPEN
def sc_1(t):                                          # lines 1-2: three jobs of school
    cv = base(t, SG(t, 1, 2)); G(cv)
    rows = [(0, 8), (1, 7), (2, 6), (3, 5), (4, 4), (5, 3), (6, 2), (7, 1)]
    for r, c in rows:
        for i in range(c):
            x = 560 + (i - (c - 1) / 2) * 128
            y = 900 - r * 34
            rr = clamp01((t - (LS(1) - 0.1) - 0.04 * (r * 3 + i)) / 0.3)
            if rr > 0:
                cols = [RED, BLUE, GREEN, PURPLE, ORANGE, BROWN, NAVY]
                cv.rect(x - 60, y - 32, x + 60, y, fill=cols[(r + i) % 7], w=4, amp=0.4, reveal=rr)
    fig(cv, 250, 900, h=300, pose="fear", face="worry", w=7)
    sign(cv, t, AT(1, 0.55), "READ.", 1330, 330, 360)
    sign(cv, t, AT(2, 0.20), "THINK.", 1330, 560, 400, rot=2)
    sign(cv, t, AT(2, 0.62), "LOVE LEARNING.", 1330, 790, 640, rot=-2, size=52)
    return cv


def sc_2(t):                                          # line 3: memorisation instead of thinking, competition instead of collaboration
    cv = base(t, SG(t, 3))
    bigtext(cv, t, LS(3) + 0.1, "THINKING", 620, 330, 110, GREY, band=None)
    cv.line((330, 340), (910, 320), w=16, col=RED, reveal=appear(t, AT(3, 0.35), 0.3), amp=1.5)
    bigtext(cv, t, AT(3, 0.30), "MEMORIZING", 620, 500, 130, NAVY)
    bigtext(cv, t, AT(3, 0.55), "COLLABORATION", 1300, 700, 100, GREY, band=None)
    cv.line((900, 710), (1710, 690), w=16, col=RED, reveal=appear(t, AT(3, 0.82), 0.3), amp=1.5)
    bigtext(cv, t, AT(3, 0.78), "COMPETITION", 1300, 860, 120, NAVY)
    return cv


def sc_3(t):                                          # line 4: students celebrate the end of exams by never wanting to open a book
    u = SG(t, 4)
    cv = base(t, u); G(cv)
    fig(cv, 560, 900, h=480, pose="cheer", face="big", w=10)
    card(cv, t, LS(4) + 0.2, "A+", 560, 330, 260, 200, fill=PAPER, col=RED, size=140)
    thr = clamp01((t - AT(4, 0.5)) / 0.8)
    for k in range(5):
        a = clamp01(thr * 1.2 - k * 0.1)
        if a > 0:
            x = lerp(620, 1350, a); y = 640 - 330 * math.sin(a * math.pi) + k * 8
            with cv.at(x, y, 1.0, a * 420 + k * 40):
                cv.rect(-34, -24, 34, 24, fill=[RED, BLUE, GREEN, PURPLE, ORANGE][k], w=5)
    flame(cv, 1400, 890, 2.6, t, seed=1)
    flame(cv, 1520, 890, 2.0, t, seed=2)
    cap(cv, t, AT(4, 0.6), "NEVER AGAIN.", 1450, 520, size=64, col=RED, font="marker")
    return cv


def sc_4(t):                                          # line 5: what if school isn't broken? (black card)
    cv = base(t, SG(t, 5), zoom=0.0, bg=(12, 12, 18))
    tag(cv, t, LS(5) + 0.25, "WHAT IF\nSCHOOL ISN'T BROKEN?", 960, 420, size=120, col=WHITE, band=None, dur=0.8)
    tag(cv, t, AT(5, 0.52), "IT'S WORKING EXACTLY\nAS THE SYSTEM REWARDS IT.", 960, 760, size=64, col=(240, 200, 80), band=None, font="hand", dur=0.8)
    return cv


def sc_5(t):                                          # line 6: the man who built the school everyone wants... then got fired
    u = SG(t, 6)
    cv = base(t, u); G(cv)
    x = lerp(240, 760, ease(clamp01(u / 0.45)))
    J = fig(cv, x, 900, h=420, pose=walk_pose(t * 6, 0.9) if u < 0.5 else "point", face="smile" if u < 0.78 else "worry", outfit=("glasses",), w=9)
    sign(cv, t, AT(6, 0.34), "YALE", 1100, 360, 280, 100, post=False)
    sign(cv, t, AT(6, 0.42), "WHARTON", 1400, 470, 360, 100, post=False, rot=2)
    sign(cv, t, AT(6, 0.5), "CORNELL", 1700, 360, 320, 100, post=False, rot=-3)
    stamp(cv, 960, 700, "FIRED", col=RED, size=210, rot=-9, s=pp(t, AT(6, 0.86), 0.3))
    return cv


# ======================================================================= THE EXPERIMENT
def sc_6(t):                                          # line 7: arrives in Shenzhen in 2008
    u = SG(t, 7)
    cv = base(t, u)
    for i, (bx, bh) in enumerate([(120, 420), (300, 640), (470, 520), (640, 760), (800, 480), (1500, 560), (1680, 700), (1830, 440)]):
        r = appear(t, LS(7) + 0.05 * i, 0.5)
        cv.rect(bx - 60, 900 - bh * r, bx + 60, 900, fill=(238, 242, 248), w=5, col=GREY, amp=0.6)
        for k in range(int(bh * r // 80)):
            cv.rect(bx - 30, 900 - bh * r + 30 + k * 80, bx + 30, 900 - bh * r + 56 + k * 80, fill=SKY, w=2, col=GREY, amp=0.2)
    G(cv)
    bx = 1180
    cv.rect(bx - 190, 640, bx + 190, 900, fill=CREAM, w=8, amp=0.6, reveal=appear(t, AT(7, 0.55), 0.5))
    cv.poly([(bx - 230, 640), (bx, 540), (bx + 230, 640)], closed=True, fill=LGOLD, w=8, reveal=appear(t, AT(7, 0.55), 0.5))
    tag(cv, t, AT(7, 0.6), "SHENZHEN\nMIDDLE SCHOOL", bx, 760, size=36, col=NAVY, band=None)
    x = lerp(160, 700, ease(clamp01((t - LS(7) - 0.2) / 3.5)))
    J = fig(cv, x, 900, h=420, pose=walk_pose(t * 6, 0.9), face="smile", outfit=("glasses",), w=9)
    with cv.at(J["hA"][0], J["hA"][1], 1.0):
        cv.rect(-60, -2, 60, 70, r=8, fill=BROWN, w=6)
        cv.text("2008", 0, 34, size=38, font="marker", col=CREAM)
    tag(cv, t, LS(7) + 0.2, "YALE ENGLISH MAJOR", 520, 340, size=44, col=NAVY)
    tag(cv, t, AT(7, 0.35), "SHENZHEN, CHINA", 1000, 230, size=52, col=RED, band=None)
    return cv


def sc_7(t):                                          # lines 8-9: impressive on paper... fifty silent students
    u = SG(t, 8, 9)
    cv = base(t, u); G(cv, 940)
    if t < AT(9, 0.0):                                # line 8: pretty brochure
        card(cv, t, LS(8) + 0.1, "IMPRESSIVE\nON PAPER", 960, 450, 900, 420, fill=PAPER, size=90)
        check(cv, 1450, 350, 2.4, reveal=appear(t, LS(8) + 0.5, 0.4))
        cap(cv, t, AT(8, 0.55), "but inside the classroom?", 960, 800, size=70, col=RED, font="marker")
        return cv
    crowd(cv, t, 480, 640, 10, 4, 105, 82, h=56)
    for k, (bx, by) in enumerate([(520, 600), (830, 560), (1100, 600), (1370, 560), (700, 700), (1250, 700)]):
        if t > AT(9, 0.08 + 0.02 * k):
            cv.ellipse(bx + 40, by - 70, 38, 28, w=4, col=GREY, amp=0.4)
    fig(cv, 220, 940, h=460, pose="point", face="neutral", outfit=("glasses",), w=9)
    bubble(cv, 360, 320, "blah blah blah", size=44, tail=(260, 470), reveal=appear(t, LS(9) + 0.1, 0.3))
    tag(cv, t, LS(9) + 0.2, "50 STUDENTS. ONE ROOM.", 1100, 340, size=60, col=NAVY)
    for k, txt in enumerate(("NO DISCUSSION.", "NO DEBATE.", "NO REAL IDEAS.")):
        tt = AT(9, 0.4 + 0.2 * k)
        if t > tt:
            xmark(cv, 1160 - 330 + 80, 440 + k * 82, 0.9, reveal=appear(t, tt, 0.25))
            cap(cv, t, tt, txt, 1160, 440 + k * 82, size=54, col=INK, font="marker")
    return cv


def sc_8(t):                                          # line 10: SAT prep = memorising vocabulary lists
    u = SG(t, 10)
    cv = base(t, u); G(cv)
    pr = appear(t, LS(10) + 0.1, 0.5)
    with cv.at(520, 560, pr):
        cv.rect(-210, -330, 210, 330, fill=PAPER, w=7)
        for k, wd in enumerate(("ubiquitous", "ephemeral", "obfuscate", "pernicious", "magnanimous", "capricious", "laconic", "ostentatious")):
            if t > LS(10) + 0.3 + 0.12 * k:
                cv.text(wd, 0, -280 + k * 76, size=42, font="hand")
        cv.text("SAT WORDS", 0, -360, size=40, font="marker", col=RED)
    fig(cv, 960, 900, h=420, pose="think", face="sweat", w=9)
    cap(cv, t, AT(10, 0.4), "memorize 3,000 words", 960, 380, size=48, col=NAVY, font="marker")
    card(cv, t, AT(10, 0.6), "BETTER READER?", 1530, 400, 560, 110, size=50)
    xmark(cv, 1530, 400, 2.4, reveal=appear(t, AT(10, 0.72), 0.3))
    card(cv, t, AT(10, 0.72), "BETTER WRITER?", 1530, 580, 560, 110, size=50)
    xmark(cv, 1530, 580, 2.4, reveal=appear(t, AT(10, 0.85), 0.3))
    return cv


def sc_9(t):                                          # line 11: everyone joined Model UN to look involved
    u = SG(t, 11)
    cv = base(t, u); G(cv)
    n = 0
    for r in range(3):
        for c in range(11):
            x, y = 330 + c * 125 + (r % 2) * 60, 640 + r * 90
            mini(cv, x, y, h=64, phase=t * 1.4 + n * 0.5, swing=0.05, seed=n)
            cv.rect(x - 14, y - 36, x + 14, y - 22, fill=SKY, w=2, amp=0.1)
            n += 1
    tag(cv, t, LS(11) + 0.3, "MODEL UN", 960, 300, size=110, col=NAVY)
    fig(cv, 270, 900, h=300, pose="shrug", face="worry", w=7)
    bubble(cv, 380, 480, "What are we\nmodeling?", size=40, tail=(300, 620), reveal=appear(t, AT(11, 0.45), 0.3))
    tag(cv, t, AT(11, 0.7), "LOOKING INVOLVED  >  BEING INVOLVED", 1280, 880, size=44, col=RED, band=None)
    return cv


def sc_10(t):                                         # line 12: so the new teacher changed the game
    u = SG(t, 12)
    cv = base(t, u); G(cv)
    cv.rect(980, 220, 1760, 700, r=10, fill=PAPER, w=8, reveal=appear(t, LS(12), 0.4))
    tag(cv, t, AT(12, 0.30), "NEW GAME", 1370, 400, size=140, col=NAVY)
    for k in range(3):
        a = appear(t, AT(12, 0.5 + 0.12 * k), 0.3)
        with cv.at(1100 + k * 270, 590, a):
            cv.rect(-50, -50, 50, 50, r=12, fill=PAPER, w=6)
            for dx, dy in [(-20, -20), (20, 20), (0, 0)][: k + 1] + ([(20, -20), (-20, 20)] if k == 2 else []):
                cv.ellipse(dx, dy, 7, 7, fill=INK, w=2, amp=0)
    fig(cv, 560, 900, h=480, pose="point", face="smirk", outfit=("glasses",), w=10)
    return cv


# ======================================================================= THE SCHOOL EVERYONE SAYS THEY WANT
def sc_11(t):                                         # line 13: seminars + 5,000-book library
    u = SG(t, 13)
    cv = base(t, u); G(cv)
    card(cv, t, LS(13) + 0.1, "GIANT LECTURES", 480, 250, 640, 120, fill=PAPER, col=GREY, size=60)
    cv.line((180, 262), (780, 240), w=16, col=RED, reveal=appear(t, AT(13, 0.22), 0.3), amp=1.5)
    card(cv, t, AT(13, 0.2), "SMALL SEMINARS", 480, 420, 640, 130, size=64)
    for k in range(7):
        a = 2 * math.pi * k / 7
        if t > AT(13, 0.26 + 0.03 * k):
            fig(cv, 480 + math.cos(a) * 190, 790 + math.sin(a) * 40, h=170, pose="stand", face="smile", w=4) if False else mini(cv, 480 + math.cos(a) * 200, 800 + math.sin(a) * 50, h=90, phase=t + k, swing=0.05, seed=k)
    card(cv, t, AT(13, 0.55), "5,000-BOOK LIBRARY", 1360, 250, 760, 130, size=60)
    for r in range(4):
        y = 860 - r * 150
        if t > AT(13, 0.58 + 0.06 * r):
            cv.line((980, y), (1760, y), w=8, col=BROWN, reveal=appear(t, AT(13, 0.58 + 0.06 * r), 0.3))
            for k in range(14):
                cv.rect(990 + k * 55, y - 100 + (k * 13 % 22), 990 + k * 55 + 40, y - 8, fill=[RED, BLUE, GREEN, PURPLE, ORANGE, BROWN, NAVY][(k + r) % 7], w=3, amp=0.3, reveal=appear(t, AT(13, 0.6 + 0.06 * r) + k * 0.02, 0.2))
    return cv


def sc_12(t):                                         # line 14: student-run coffee house
    u = SG(t, 14)
    cv = base(t, u); G(cv)
    cv.rect(520, 640, 1400, 700, fill=BROWN, w=8)
    cv.rect(560, 700, 1360, 900, fill=CREAM, w=8)
    cv.poly([(480, 380), (960, 250), (1440, 380)], closed=True, fill=LGOLD, w=8)
    tag(cv, t, LS(14) + 0.2, "STUDENT-RUN COFFEE HOUSE", 960, 190, size=62, col=NAVY)
    fig(cv, 640, 700, h=280, pose="stand", face="scared", w=6)
    wb.hold(cv, {"hA": (700, 560)}, "mug")
    smoke = appear(t, AT(14, 0.3), 0.5)
    for k in range(3):
        cv.curve((694 + k * 8, 520), (680 + k * 14, 470 - 30 * smoke), (700 + k * 8, 420 - 50 * smoke), w=5, col=GREY, reveal=smoke)
    cap(cv, t, AT(14, 0.35), "oops, burnt", 650, 360, size=40, col=RED, font="marker")
    fig(cv, 960, 700, h=280, pose="think", face="worry", w=6)
    paper(cv, 1000, 540, 120, 150, rot=-6, text="-$40", size=34) if t > AT(14, 0.5) else None
    fig(cv, 1280, 700, h=280, pose="point", face="smile", w=6)
    sign(cv, t, AT(14, 0.72), "REAL BUSINESS", 1560, 520, 460, 110, size=48, rot=3)
    for k, w_ in enumerate(("MANAGEMENT", "FINANCE", "TEAMWORK")):
        tag(cv, t, AT(14, 0.45 + 0.17 * k), w_, 420 + k * 540, 980, size=44, col=NAVY)
    return cv


def sc_13(t):                                         # line 15: daily student newspaper
    u = SG(t, 15)
    cv = base(t, u); G(cv)
    stages = ["REPORT", "EDIT", "PRINT", "DELIVER"]
    for k, st in enumerate(stages):
        x = 300 + k * 440
        tt = AT(15, 0.05 + 0.12 * k)
        if t > tt:
            fig(cv, x, 760, h=250, pose=["point", "think", "stand", "cheer"][k], face="smile", w=6)
            tag(cv, t, tt, st, x, 860, size=40, col=NAVY)
            if k < 3:
                cv.arrow((x + 120, 640), (x + 320, 640), w=7, col=GREY, reveal=appear(t, tt + 0.2, 0.3))
    card(cv, t, LS(15) + 0.2, "THE DAILY STUDENT NEWS", 960, 220, 920, 130, fill=PAPER, size=62)
    for k, (txt, c_) in enumerate((("REAL READING.", BLUE), ("REAL WRITING.", GREEN), ("REAL RESPONSIBILITY.", RED))):
        tag(cv, t, AT(15, 0.62 + 0.12 * k), txt, 960, 420 + k * 90, size=62, col=c_, band=None)
    return cv


def sc_14(t):                                         # line 16: record admissions, the program worked
    u = SG(t, 16)
    cv = base(t, u); G(cv)
    fig(cv, 960, 900, h=460, pose="cheer", face="big", w=10)
    for k, nm in enumerate(("YALE", "WHARTON", "CORNELL", "YALE", "WHARTON", "CORNELL", "YALE", "CORNELL")):
        a = clamp01((t - AT(16, 0.05) - 0.18 * k) / 1.6)
        if 0 < a < 1.3:
            x = 260 + k * 200 + 30 * math.sin(a * 6 + k)
            y = lerp(-80, 880, clamp01(a))
            with cv.at(x, y, 1.0, 14 * math.sin(a * 5 + k)):
                cv.rect(-70, -46, 70, 46, r=6, fill=PAPER, w=5)
                cv.poly([(-70, -46), (0, 8), (70, -46)], w=4)
                cv.text(nm, 0, 22, size=22, font="marker", col=NAVY)
    tag(cv, t, AT(16, 0.34), "RECORD ADMISSIONS", 960, 220, size=96, col=NAVY)
    check(cv, 1540, 460, 3.0, reveal=appear(t, AT(16, 0.74), 0.4))
    cap(cv, t, AT(16, 0.74), "THE PROGRAM WORKED", 1500, 640, size=48, col=GREEN, font="marker")
    return cv


def sc_15(t):                                         # lines 17-18: everyone celebrates... nope, angry mob, fired
    u = SG(t, 17, 18)
    cv = base(t, u, shake=3 if AT(18, 0.0) < t < AT(18, 0.25) else 0); G(cv)
    nope = AT(17, 0.62)
    if t < nope:
        for k in range(18):
            x = (k * 211 + t * 90) % 1900; y = (k * 97 + t * 300) % 760
            cv.rect(x, y, x + 14, y + 22, fill=[RED, BLUE, GOLD, GREEN][k % 4], w=1, amp=0, col=[RED, BLUE, GOLD, GREEN][k % 4])
        for x in (500, 960, 1420):
            fig(cv, x, 900, h=360, pose="cheer", face="big", w=8)
        cap(cv, t, LS(17) + 0.2, "everyone celebrated, right?", 960, 200, size=70, col=NAVY, font="marker")
        return cv
    people = [(380, "PARENTS", "angry"), (760, "TEACHERS", "angry"), (1140, "ADMINS", "angry")]
    for k, (x, lab, face) in enumerate(people):
        ta = AT(18, 0.04 + 0.2 * k)
        if t > ta - 0.1:
            fig(cv, x, 900, h=380, pose="arms_out", face=face, w=8)
            tag(cv, t, ta, lab, x, 960, size=36, col=RED)
            for j in range(3):
                cv.zig((x - 40 + j * 40, 440), (x - 30 + j * 40, 400 - 20 * (j % 2)), n=3, jag=10, w=4, col=RED, reveal=appear(t, ta, 0.3)) if False else None
    fx = lerp(1500, 1750, ease(clamp01((t - AT(18, 0.55)) / 0.5)))
    fig(cv, fx, 900, h=380, pose="shrug", face="sad", outfit=("glasses",), w=8)
    with cv.at(fx - 90, 640, 1.0, -8):
        cv.rect(-60, -40, 60, 40, fill=BROWN, w=5); cv.text("FIRED", 0, 0, size=34, font="marker", col=CREAM)
    tag(cv, t, AT(18, 0.7), "GREAT RESULTS.\nTERRIBLE OUTCOME.", 960, 260, size=84, col=RED, band=LGOLD)
    return cv


def sc_16(t):                                         # line 19: changed the classes without changing the game
    u = SG(t, 19)
    cv = base(t, u); G(cv)
    card(cv, t, LS(19) + 0.2, "CHANGED THE CLASSES", 560, 300, 800, 130, size=62)
    check(cv, 1060, 300, 1.6, reveal=appear(t, AT(19, 0.3), 0.3))
    card(cv, t, AT(19, 0.46), "DID NOT CHANGE\nTHE GAME", 1260, 600, 800, 200, fill=(255, 226, 226), col=RED, size=64)
    stamp(cv, 1260, 760, "SAME RULES", col=RED, size=70, rot=-6, s=pp(t, AT(19, 0.7), 0.3))
    fig(cv, 360, 900, h=420, pose="shrug", face="worry", outfit=("glasses",), w=9)
    tag(cv, t, AT(19, 0.16), "strategic mistake", 560, 440, size=48, col=NAVY, band=None, font="hand")
    return cv


# ======================================================================= MEET THE PLAYERS
PLAYERS = [("PARENTS", 330, 380), ("TEACHERS", 960, 330), ("ADMINS", 1590, 380), ("GOVERNMENT", 330, 700), ("COLLEGES", 960, 740), ("STUDENTS", 1590, 700)]


def sc_17(t):                                         # line 20: players, incentives, power
    u = SG(t, 20)
    cv = base(t, u); G(cv)
    cv.rect(300, 220, 1620, 900, r=20, w=7, col=GREY, fill=(250, 250, 244), reveal=appear(t, LS(20), 0.5))
    for k, (nm, x, y) in enumerate(PLAYERS):
        ta = AT(20, 0.12 + 0.05 * k)
        if t > ta:
            s = pp(t, ta, 0.4)
            with cv.at(x, y + 60, s):
                fig(cv, 0, 0, h=190, pose="stand", face="neutral", w=5)
                cv.text(nm, 0, 40, size=30, font="marker", col=NAVY)
    for k, w_ in enumerate(("PLAYERS", "INCENTIVES", "POWER")):
        tag(cv, t, AT(20, 0.5 + 0.17 * k), w_, 560 + k * 400, 130, size=70, col=[NAVY, GREEN, RED][k])
    return cv


def sc_18(t):                                         # line 21: biggest perceived reward for the least effort
    u = SG(t, 21)
    cv = base(t, u); G(cv)
    tag(cv, t, LS(21) + 0.2, "BIGGEST PERCEIVED REWARD", 960, 260, size=90, col=GREEN)
    tag(cv, t, AT(21, 0.55), "LEAST POSSIBLE EFFORT", 960, 430, size=90, col=RED)
    fig(cv, 560, 900, h=420, pose="hips", face="smirk", w=9)
    with cv.at(1300, 800, pp(t, AT(21, 0.3), 0.4)):
        cv.poly([(-140, 80), (140, 80), (0, 0)], closed=True, fill=LGREY, w=6)
        tilt = -12 * ease(clamp01((t - AT(21, 0.6)) / 0.5))
        with cv.at(0, 0, 1.0, tilt):
            cv.line((-220, 0), (220, 0), w=10)
            cv.ellipse(-190, -46, 40, 40, fill=GOLD, w=5); cv.text("$", -190, -46, size=44, font="marker")
            cv.ellipse(190, -40, 24, 24, fill=SKY, w=5)
    return cv


def sc_19(t):                                         # line 22: not selfish or lazy, watch what they reward
    u = SG(t, 22)
    cv = base(t, u); G(cv)
    card(cv, t, LS(22) + 0.2, "WHAT THEY SAY", 560, 280, 600, 120, size=56)
    card(cv, t, AT(22, 0.45), "WHAT THEY REWARD", 1360, 280, 700, 120, fill=LGOLD, size=56)
    fig(cv, 560, 900, h=380, pose="arms_out", face="smile", w=8)
    bubble(cv, 560, 520, "I want\nreal learning!", size=42, tail=(560, 680), reveal=appear(t, LS(22) + 0.4, 0.3))
    with cv.at(1360, 640, pp(t, AT(22, 0.5), 0.4)):                      # an eye
        cv.curve((-190, 0), (0, -150), (190, 0), w=9)
        cv.curve((-190, 0), (0, 150), (190, 0), w=9)
        cv.ellipse(0, 0, 70, 70, fill=SKY, w=8); cv.ellipse(0, 0, 30, 30, fill=INK, w=2, amp=0)
    cap(cv, t, AT(22, 0.65), "don't design around words", 1360, 880, size=48, col=RED, font="marker")
    return cv


def sc_20(t):                                         # line 23: parents
    u = SG(t, 23)
    cv = base(t, u); G(cv)
    fig(cv, 420, 900, h=440, pose="arms_out", face="smile", w=10)
    tag(cv, t, LS(23) + 0.1, "PARENTS", 420, 970, size=40, col=NAVY)
    bubble(cv, 440, 330, "I want an independent,\nsuccessful child!", size=40, tail=(420, 460), reveal=appear(t, LS(23) + 0.4, 0.3))
    for k, w_ in enumerate(("PRESTIGE", "HIGH GRADES", "CONTROL")):
        card(cv, t, AT(23, 0.35 + 0.1 * k), w_, 1100, 250 + k * 150, 520, 100, size=50, fill=LGOLD, rot=(-2, 2, -1)[k])
    cv.rect(1360, 600, 1860, 900, w=0, col=PAPER) if False else None
    cv.line((1480, 900), (1480, 640), w=9, col=GREY, reveal=appear(t, AT(23, 0.7), 0.3)); cv.line((1760, 900), (1760, 640), w=9, col=GREY, reveal=appear(t, AT(23, 0.7), 0.3))
    cv.poly([(1460, 640), (1620, 560), (1780, 640)], w=8, reveal=appear(t, AT(23, 0.7), 0.3))
    tag(cv, t, AT(23, 0.72), "SCHOOL GATE", 1620, 520, size=34, col=GREY, band=None)
    fig(cv, 1620, 900, h=340, pose="point", face="smile", outfit=("glasses",), w=7)
    sign(cv, t, AT(23, 0.84), "FOREIGN TEACHERS!", 1420, 380, 460, 90, size=38, post=False, rot=-3)
    return cv


def sc_21(t):                                         # line 24: teachers
    u = SG(t, 24)
    cv = base(t, u); G(cv)
    fig(cv, 560, 900, h=440, pose="stand", face="worry", w=10)
    tag(cv, t, LS(24) + 0.1, "TEACHERS", 560, 970, size=40, col=NAVY)
    for k in range(7):
        r = appear(t, AT(24, 0.35 + 0.05 * k), 0.3)
        if r > 0:
            paper(cv, 560 + (k % 3 - 1) * 70, 440 - k * 44, 110, 150, rot=(k * 17) % 20 - 10, text="" if k else "MORE\nWORK", size=26)
    card(cv, t, LS(24) + 0.3, "I CARE.", 1260, 280, 400, 110, fill=(226, 255, 232), col=GREEN, size=60)
    card(cv, t, AT(24, 0.4), "SEMINARS + NEWSPAPER\n+ PROJECTS", 1360, 520, 700, 200, size=50)
    card(cv, t, AT(24, 0.7), "SAME SALARY", 1360, 800, 500, 120, fill=(255, 226, 226), col=RED, size=62)
    return cv


def sc_22(t):                                         # line 25: administrators balance on a chair
    u = SG(t, 25)
    cv = base(t, u); G(cv)
    cv.line((520, 900), (520, 640), w=9, col=GREY); cv.line((1400, 900), (1400, 640), w=9, col=GREY)
    for x, lab in ((520, "ANGRY\nPARENTS"), (1400, "ANGRY\nSTAFF")):
        for k in range(3):
            mini(cv, x - 80 + k * 80, 900, h=90, phase=t * 3 + k, swing=0.12, seed=k + x)
        tag(cv, t, LS(25) + 0.4, lab, x, 790, size=36, col=RED, band=None)
    sway = 5 * math.sin(t * 2.2)
    with cv.at(960, 900, 1.0, sway):
        chair(cv, 0, 0, 1.4)
        fig(cv, 0, -120, h=300, pose="shrug", face="scared", w=8)
    tag(cv, t, LS(25) + 0.1, "ADMINISTRATORS", 960, 250, size=60, col=NAVY)
    bubble(cv, 1050, 380, "bold reform?", size=40, tail=(980, 540), reveal=appear(t, AT(25, 0.45), 0.3))
    if t > AT(25, 0.7):
        cv.line((850, 380), (1250, 380), w=12, col=RED, reveal=appear(t, AT(25, 0.72), 0.2))
        tag(cv, t, AT(25, 0.75), "DON'T CAUSE TROUBLE", 960, 480, size=76, col=RED)
    return cv


def sc_23(t):                                         # line 26: government prioritises stability
    u = SG(t, 26)
    cv = base(t, u); G(cv)
    fig(cv, 600, 900, h=460, pose="point", face="neutral", outfit=("glasses",), w=10)
    tag(cv, t, LS(26) + 0.1, "GOVERNMENT", 600, 970, size=40, col=NAVY)
    bubble(cv, 620, 300, "creativity! innovation!", size=44, tail=(600, 440), reveal=appear(t, LS(26) + 0.3, 0.3))
    sign(cv, t, AT(26, 0.45), "STABILITY", 1370, 450, 640, 150, size=88, fill=LGOLD)
    for k, w_ in enumerate(("COMPLIANCE", "NO DISRUPTION")):
        card(cv, t, AT(26, 0.65 + 0.14 * k), w_, 1370, 740 + k * 110, 520, 90, size=44)
    return cv


def sc_24(t):                                         # line 27: colleges and tuition
    u = SG(t, 27)
    cv = base(t, u); G(cv)
    cv.rect(380, 300, 1000, 900, fill=CREAM, w=8)
    cv.poly([(330, 300), (690, 170), (1050, 300)], closed=True, fill=LGOLD, w=8)
    for k in range(4):
        cv.rect(430 + k * 140, 360, 500 + k * 140, 880, fill=PAPER, w=6)
    tag(cv, t, LS(27) + 0.1, "COLLEGE", 690, 100, size=70, col=NAVY)
    g_ = ease(clamp01((t - AT(27, 0.3)) / 0.8))
    cv.rect(560, 700, 820, 900, fill=BROWN, w=8)
    cv.rect(560 - 130 * g_, 700, 560, 900, fill=(200, 160, 110), w=6) if g_ > 0 else None
    cv.rect(1250, 640, 1700, 900, r=10, fill=LGREY, w=8)
    cv.rect(1290, 560, 1660, 640, r=8, fill=SKY, w=6)
    tag(cv, t, AT(27, 0.4), "FULL TUITION", 1475, 520, size=52, col=GREEN)
    for k in range(6):
        a = clamp01((t - AT(27, 0.5) - 0.12 * k) / 0.7)
        if 0 < a < 1:
            cv.ellipse(lerp(1000, 1440, a), lerp(820, 640, a) - 80 * math.sin(a * math.pi), 24, w=5, fill=GOLD)
    cap(cv, t, AT(27, 0.2), "curious, passionate students...", 690, 960, size=44, col=NAVY, font="marker")
    return cv


def sc_25(t):                                         # lines 28-29: students pick EASY A
    u = SG(t, 28, 29)
    cv = base(t, u); G(cv)
    fig(cv, 560, 900, h=440, pose="point" if t < AT(28, 0.55) else "hips", face="smirk", w=10)
    tag(cv, t, LS(28) + 0.1, "STUDENTS", 560, 970, size=40, col=NAVY)
    card(cv, t, AT(28, 0.2), "HARD LEARNING", 1300, 330, 560, 130, size=56, fill=PAPER, col=GREY)
    card(cv, t, AT(28, 0.4), "EASY A", 1300, 600, 560, 190, size=96, fill=LGOLD, col=RED)
    n = int(max(0, (t - AT(28, 0.6)) * 6))
    if n > 0 and t < EN(28) + 0.3:
        with cv.at(1300, 600, 1.0 + 0.06 * (n % 2)):
            cv.rect(-280, -95, 280, 95, r=18, w=9, col=RED)
        tag(cv, t, AT(28, 0.62), "SLAP! SLAP! SLAP!", 1300, 800, size=48, col=RED, band=None)
    if t > LS(29) - 0.1:
        tag(cv, t, LS(29) + 0.2, "NOT EVERYONE. NOT ALWAYS.", 960, 200, size=70, col=NAVY)
        tag(cv, t, AT(29, 0.5), "BUT ENOUGH, OFTEN ENOUGH.", 960, 330, size=70, col=RED)
    return cv


# ======================================================================= WHO HAS THE POWER?
def sc_26(t):                                         # lines 30-31: power meters
    u = SG(t, 30, 31)
    cv = base(t, u); G(cv)
    xs = [(330, "PARENTS", 0.95, GREEN), (810, "TEACHERS", 0.6, BLUE), (1290, "ADMINS", 0.42, ORANGE), (1690, "STUDENTS", 0.1, RED)]
    for k, (x, nm, v, c_) in enumerate(xs):
        start = [LS(30) + 0.2, AT(31, 0.05), AT(31, 0.5), AT(31, 0.85)][k]
        r = appear(t, start, 0.8)
        if t > start - 0.1:
            fig(cv, x, 900, h=300, pose="stand", face="neutral", w=7)
            tag(cv, t, start, nm, x, 970, size=34, col=NAVY)
            cv.rect(x - 40, 300, x + 40, 560, r=8, w=6)
            cv.rect(x - 34, 556 - 250 * v * ease(r), x + 34, 556, r=6, fill=c_, w=2, amp=0)
            tag(cv, t, start + 0.4, ["FUNDS IT", "RUNS THE DAY", "NEGOTIATES", "?"][k], x, 240, size=36, col=c_, band=None)
    return cv


def sc_27(t):                                         # line 32: students have the least power
    u = SG(t, 32)
    cv = base(t, u); G(cv)
    fig(cv, 560, 900, h=420, pose="point_up", face="sad", w=9)
    cv.rect(250, 420, 330, 780, r=8, w=6, reveal=appear(t, LS(32), 0.4))
    cv.rect(256, 760, 324, 774, r=4, fill=RED, w=2, amp=0, reveal=appear(t, LS(32) + 0.4, 0.4))
    tag(cv, t, LS(32) + 0.2, "POWER", 290, 370, size=40, col=RED, band=None)
    tag(cv, t, LS(32) + 0.2, "THE PURPOSE OF SCHOOL", 560, 190, size=44, col=NAVY)
    for k in range(4):
        fig(cv, 960 + k * 250, 900, h=300, pose="stand", face="neutral", flip=False, w=7) if False else mini(cv, 960 + k * 250, 900, h=300, phase=0, swing=0, seed=k + 3)
    for k in range(4):
        x = 960 + k * 250
        with cv.at(x, 900):
            cv.curve((-40, -330), (0, -380), (40, -330), w=6, col=GREY)
    bubble(cv, 480, 650, "hello?", size=44, tail=(480, 760), reveal=appear(t, AT(32, 0.6), 0.3)) if False else None
    cap(cv, t, AT(32, 0.55), "nobody looks", 1450, 520, size=60, col=RED, font="marker")
    return cv


def sc_28(t):                                         # line 33: tug of war -> glowing knot -> the school everyone can tolerate
    u = SG(t, 33)
    cv = base(t, u); G(cv)
    pull = 1 if u < 0.42 else 0
    kk = glow_pulse(t, 1.4)
    fig(cv, 360 - (20 * math.sin(t * 8) if pull else 0), 900, h=380, pose="lift", face="angry", w=9)
    fig(cv, 1560 + (20 * math.sin(t * 8) if pull else 0), 900, h=380, pose="lift", face="angry", flip=True, w=9)
    tag(cv, t, LS(33) + 0.1, "PARENTS", 360, 970, size=36, col=NAVY); tag(cv, t, LS(33) + 0.1, "TEACHERS", 1560, 970, size=36, col=NAVY)
    if u < 0.42:
        cv.line((470, 600), (1450, 600), w=10, col=BROWN)
    else:
        cv.line((470, 600), (880, 600), w=10, col=BROWN); cv.line((1040, 600), (1450, 600), w=10, col=BROWN)
        r = 70 + 14 * kk
        cv.ellipse(960, 600, r, r, fill=LGOLD, w=7, col=GOLD)
        wb.sunburst(cv, 960, 600, r, t) if hasattr(wb, "sunburst") else burst_lines(cv, 960, 600, r * 1.2, r * 1.8, n=14, col=GOLD, w=6, a0=t * 0.3)
        tag(cv, t, AT(33, 0.45), "CONVERGENCE", 960, 380, size=80, col=NAVY)
        tag(cv, t, AT(33, 0.7), "THE SCHOOL EVERYONE CAN TOLERATE", 960, 220, size=60, col=RED)
    return cv


def sc_29(t):                                         # line 34: everyone gets what they want
    u = SG(t, 34)
    cv = base(t, u); G(cv)
    rows = [("PARENTS", "IMPRESSIVE GRADES"), ("TEACHERS", "NO IMPOSSIBLE WORKLOAD"), ("ADMINS", "NO CONFLICT"), ("STUDENTS", "NO PAINFUL STRUGGLE")]
    for k, (who, what) in enumerate(rows):
        ta = AT(34, 0.02 + 0.24 * k)
        y = 240 + k * 190
        if t > ta:
            card(cv, t, ta, who, 480, y, 420, 110, size=48)
            cv.arrow((720, y), (860, y), w=8, col=GREY, reveal=appear(t, ta + 0.2, 0.25))
            card(cv, t, ta + 0.15, what, 1300, y, 800, 110, size=48, fill=(226, 255, 232), col=GREEN)
            check(cv, 1760, y, 1.4, reveal=appear(t, ta + 0.4, 0.3))
    return cv


def sc_30(t):                                         # line 35: real learning in the brochure
    u = SG(t, 35)
    cv = base(t, u); G(cv)
    cv.rect(560, 160, 1560, 700, r=14, fill=PAPER, w=9, reveal=appear(t, LS(35), 0.4))
    cv.line((600, 700), (600, 900), w=10, col=BROWN); cv.line((1520, 700), (1520, 900), w=10, col=BROWN)
    tag(cv, t, LS(35) + 0.2, "SUPER SCHOOL!", 1060, 300, size=110, col=NAVY)
    tag(cv, t, AT(35, 0.3), "HIGH GRADES • AWARDS • GLITTER", 1060, 470, size=44, col=GOLD, band=None)
    fig(cv, 380, 900, h=150, pose="point_up", face="smile", w=4) if False else None
    s_ = pp(t, AT(35, 0.55), 0.5)
    with cv.at(1700, 880, s_):
        fig(cv, 0, 0, h=130, pose="point_up", face="sad", w=4)
        cv.text("LEARNING", 0, 40, size=26, font="marker", col=RED)
    bubble(cv, 1700, 640, "hi... I'm in\nthe brochure", size=32, tail=(1700, 770), reveal=appear(t, AT(35, 0.7), 0.3))
    return cv


def sc_31(t):                                         # line 36: symptoms
    u = SG(t, 36)
    cv = base(t, u); G(cv)
    words = ["GRADE INFLATION", "COSMETIC INNOVATION", "CHEATING", "HIGH TEACHER TURNOVER"]
    for k, w_ in enumerate(words):
        card(cv, t, AT(36, 0.04 + 0.2 * k), w_, 560 + (k % 2) * 800, 280 + (k // 2) * 220, 700, 120, size=46, fill=(255, 226, 226), col=RED, rot=(-2, 2, 1, -2)[k])
    tag(cv, t, AT(36, 0.62), "LOOKS SUCCESSFUL.", 960, 760, size=88, col=GREEN, band=None)
    tag(cv, t, AT(36, 0.82), "QUIETLY FAILING.", 960, 900, size=88, col=RED, band=None)
    return cv


def sc_32(t):                                         # line 37: decent people + bad incentives = bad system
    u = SG(t, 37)
    cv = base(t, u); G(cv)
    fig(cv, 380, 900, h=420, pose="stand", face="smile", w=9)
    tag(cv, t, LS(37) + 0.2, "DECENT PEOPLE", 380, 970, size=40, col=GREEN)
    cap(cv, t, AT(37, 0.25), "+", 700, 600, size=140, col=NAVY, font="marker")
    card(cv, t, AT(37, 0.3), "BAD\nINCENTIVES", 1010, 600, 420, 220, size=54, fill=(255, 226, 226), col=RED)
    cap(cv, t, AT(37, 0.55), "=", 1350, 600, size=140, col=NAVY, font="marker")
    card(cv, t, AT(37, 0.6), "BAD\nSYSTEMS", 1640, 600, 360, 220, size=54, fill=RED, col=INK)
    cap(cv, t, AT(37, 0.8), "not because they're evil", 960, 220, size=60, col=NAVY, font="marker")
    return cv


# ======================================================================= WHY SOME SCHOOLS ESCAPE
LEVERS = [("COHESION", 420, BLUE), ("OPENNESS", 960, GREEN), ("ENERGY", 1500, ORANGE)]


def levers(cv, t, hi=None, dim=0.0, t0=0):
    for k, (nm, x, c_) in enumerate(LEVERS):
        a = pp(t, t0 + 0.2 * k, 0.4)
        if a > 0.02:
            with cv.at(x, 800, a):
                cv.rect(-30, -420, 30, 0, r=10, fill=LGREY, w=6)
                cv.ellipse(0, -300 if hi == k else -140, 52, 52, fill=c_, w=7)
                cv.text(nm, 0, 70, size=48, font="marker", col=c_)


def sc_33(t):                                         # line 38: three forces
    cv = base(t, SG(t, 38)); G(cv)
    levers(cv, t, t0=AT(38, 0.55))
    tag(cv, t, LS(38) + 0.2, "SOCIETY SITS AROUND THE SCHOOL", 960, 180, size=62, col=NAVY)
    tag(cv, t, AT(38, 0.5), "3 FORCES", 960, 340, size=100, col=RED)
    return cv


def sc_34(t):                                         # line 39: cohesion
    cv = base(t, SG(t, 39)); G(cv)
    levers(cv, t, hi=0, t0=-5)
    bubble(cv, 420, 220, "Every child's future\nmatters?", size=44, tail=(420, 330), reveal=appear(t, LS(39) + 0.2, 0.3))
    bubble(cv, 1100, 300, "...or only my kid's\nranking?", size=44, tail=(560, 420), reveal=appear(t, AT(39, 0.6), 0.3), fill=(255, 226, 226))
    return cv


def sc_35(t):                                         # line 40: openness
    cv = base(t, SG(t, 40)); G(cv)
    levers(cv, t, hi=1, t0=-5)
    bubble(cv, 960, 200, "Admit mistakes\nand adapt?", size=44, tail=(960, 310), reveal=appear(t, LS(40) + 0.2, 0.3))
    bubble(cv, 1500, 340, "...or punish whoever\nexposes the problem?", size=40, tail=(1000, 440), reveal=appear(t, AT(40, 0.6), 0.3), fill=(255, 226, 226))
    return cv


def sc_36(t):                                         # line 41: energy
    cv = base(t, SG(t, 41)); G(cv)
    levers(cv, t, hi=2, t0=-5)
    bubble(cv, 1500, 190, "Build excellent\ninstitutions?", size=44, tail=(1500, 300), reveal=appear(t, LS(41) + 0.2, 0.3))
    bubble(cv, 960, 340, "...or just protect\nwhat we have?", size=44, tail=(1400, 440), reveal=appear(t, AT(41, 0.6), 0.3), fill=(255, 226, 226))
    return cv


def sc_37(t):                                         # line 42: Finland, China in the 1980s
    u = SG(t, 42)
    cv = base(t, u); G(cv)
    levers(cv, t, hi=None, t0=-5)
    for k in range(3):
        cv.ellipse(LEVERS[k][1], -140 + 800 - 0, 0.1) if False else None
    tag(cv, t, LS(42) + 0.2, "ALL THREE STRONG = SCHOOLS THRIVE", 960, 150, size=64, col=GREEN)
    card(cv, t, AT(42, 0.3), "FINLAND", 560, 300, 420, 110, size=60)
    card(cv, t, AT(42, 0.5), "CHINA, 1980s", 1360, 300, 520, 110, size=60)
    cap(cv, t, AT(42, 0.65), "education = path out of poverty", 1360, 410, size=40, col=NAVY, font="marker")
    cap(cv, t, AT(42, 0.82), "limited resources, huge respect + drive", 960, 500, size=44, col=GREEN, font="marker")
    for k in range(3):
        a = appear(t, AT(42, 0.2 + 0.08 * k), 0.5)
        with cv.at(LEVERS[k][1], 800):
            cv.ellipse(0, -300 * a - 20, 52, 52, fill=LEVERS[k][2], w=7)
    return cv


def sc_38(t):                                         # line 43: zero-sum contest
    u = SG(t, 43)
    cv = base(t, u); G(cv)
    tilt = 14 * ease(clamp01((t - AT(43, 0.55)) / 0.5))
    cv.poly([(840, 900), (1080, 900), (960, 800)], closed=True, fill=LGREY, w=7)
    with cv.at(960, 800, 1.0, -tilt):
        cv.line((-520, 0), (520, 0), w=12)
        fig(cv, -400, 0, h=200, pose="cheer", face="big", w=6)
        fig(cv, 400, 0, h=200, pose="fear", face="sad", w=6)
    tag(cv, t, LS(43) + 0.3, "ZERO-SUM", 960, 200, size=120, col=RED)
    card(cv, t, AT(43, 0.55), "YOUR CHILD'S SUCCESS", 560, 420, 600, 100, size=44, fill=(226, 255, 232), col=GREEN)
    card(cv, t, AT(43, 0.72), "= MY CHILD'S FAILURE", 1380, 420, 640, 100, size=44, fill=(255, 226, 226), col=RED)
    return cv


def sc_39(t):                                         # lines 44-45: risk-averse admins, comfy wealthy families, marketplace for advantage
    u = SG(t, 44, 45)
    cv = base(t, u); G(cv)
    if t < LS(45):
        fig(cv, 480, 900, h=380, pose="fear", face="scared", w=9)
        tag(cv, t, LS(44) + 0.2, "ADMINISTRATORS STOP TAKING RISKS", 600, 200, size=54, col=RED)
        fig(cv, 1380, 900, h=380, pose="hips", face="cool", outfit=("crown",), w=9)
        tag(cv, t, AT(44, 0.55), "WEALTHY FAMILIES NEED GRADES LESS", 1300, 330, size=44, col=NAVY)
        return cv
    cv.poly([(380, 520), (960, 380), (1540, 520)], closed=True, fill=LGOLD, w=8, reveal=appear(t, LS(45), 0.5))
    cv.rect(420, 520, 1500, 780, w=8, fill=CREAM, reveal=appear(t, LS(45), 0.5))
    tag(cv, t, AT(45, 0.3), "MARKETPLACE FOR ADVANTAGE", 960, 640, size=62, col=NAVY)
    for k, w_ in enumerate(("TUTORS", "CONNECTIONS", "BRAND NAMES")):
        card(cv, t, AT(45, 0.5 + 0.14 * k), w_ + " - $$$", 480 + k * 480, 880, 440, 80, size=36, fill=PAPER)
    tag(cv, t, LS(45) + 0.1, "SCHOOL = A SHARED PROJECT?", 960, 230, size=60, col=GREY, band=None)
    cv.line((420, 240), (1500, 220), w=14, col=RED, reveal=appear(t, AT(45, 0.15), 0.3), amp=1.5)
    return cv


# ======================================================================= THE REAL LESSON
def sc_40(t):                                         # lines 46-48: reformer pushed offscreen
    u = SG(t, 46, 48)
    cv = base(t, u); G(cv)
    push = ease(clamp01((t - AT(46, 0.5)) / 1.2))
    rx = lerp(960, 1900, push) if t > AT(46, 0.5) else 960
    fig(cv, rx, 900, h=400, pose="arms_out", face="big" if push < 0.05 else "scared", outfit=("glasses",), w=9)
    sign(cv, t, LS(46) + 0.2, "I HAVE FIXED EVERYTHING!", 960 - 40 + (rx - 960), 360, 760, 120, size=46, post=False)
    for k, x in enumerate((140, 420, 700)):
        if t > AT(46, 0.45):
            fig(cv, x + 170 * push * 0 + (rx - 960) * 0.2 * 0, 900, h=360, pose="point", face="angry", w=8, flip=False)
    if t > LS(47) - 0.1:
        cv.rect(0, 0, 1920, 1080, fill=PAPER, w=0, col=PAPER)
        G(cv)
        for k, (w_, sub) in enumerate((("STRICT FAIRNESS", "threatened hidden privileges"), ("HARDER LEARNING", "created more work"), ("NEW RESPONSIBILITIES", "disrupted hierarchies"))):
            card(cv, t, AT(47, 0.05 + 0.3 * k), w_, 620, 260 + k * 190, 700, 130, size=52, sub=sub)
            xmark(cv, 1060, 260 + k * 190, 1.4, reveal=appear(t, AT(47, 0.2 + 0.3 * k), 0.3))
        if t > LS(48):
            tag(cv, t, LS(48) + 0.2, "RECORD ADMISSIONS\nCOULDN'T SAVE HIM", 1480, 560, size=56, col=RED)
            fig(cv, 1480, 900, h=300, pose="shrug", face="sad", outfit=("glasses",), w=7)
    return cv


def sc_41(t):                                         # lines 49-52: sustainable reform = overlap of interests, small steps
    u = SG(t, 49, 52)
    cv = base(t, u); G(cv)
    cols = [(400, "PARENTS", RED), (760, "TEACHERS", BLUE), (1120, "ADMINS", GREEN), (1480, "STUDENTS", ORANGE)]
    if t < LS(50):
        for k, (x, nm, c_) in enumerate(cols):
            a = appear(t, LS(49) + 0.2 + 0.1 * k, 0.6)
            cv.ellipse(x + (k - 1.5) * 60 * (1 - a * 0) + 0, 520, 190, 190, w=7, col=c_, reveal=a)
        tag(cv, t, AT(49, 0.45), "THE OVERLAP", 960, 520, size=70, col=NAVY)
        tag(cv, t, LS(49) + 0.1, "NOT A HEROIC OUTSIDER", 960, 180, size=62, col=GREY, band=None)
        return cv
    steps = [(LS(50) + 0.1, "PARENTS", "visible growth", RED), (AT(50, 0.5), "TEACHERS", "sustainable reforms", BLUE),
             (LS(51) + 0.1, "ADMINS", "safe wins", GREEN), (AT(51, 0.5), "STUDENTS", "real challenges", ORANGE)]
    for k, (ts, nm, what, c_) in enumerate(steps):
        a = pp(t, ts, 0.4)
        if a > 0.02:
            x = 300 + k * 420; y = 800 - k * 120
            with cv.at(x, y, a):
                cv.rect(-190, 0, 190, 130 + k * 120, fill=CREAM, w=7, col=c_)
                cv.text("GIVE " + nm, 0, 30, size=36, font="marker", col=c_)
                cv.text(what, 0, 80, size=34, font="hand", col=INK)
    if t > LS(52):
        fig(cv, 1560, 440, h=260, pose="cheer", face="big", w=7)
        tag(cv, t, LS(52) + 0.2, "MOVE THE EQUILIBRIUM, ONE STEP AT A TIME", 960, 160, size=60, col=NAVY)
    return cv


def sc_42(t):                                         # lines 53-54: ask a better question
    u = SG(t, 53, 54)
    cv = base(t, u); G(cv)
    fig(cv, 360, 900, h=420, pose="think", face="worry", w=9)
    flame(cv, 360, 905, 1.2, 0.0, seed=1) if False else None
    tag(cv, t, LS(53) + 0.2, "ASK A BETTER QUESTION", 1100, 190, size=76, col=RED)
    qs = ["WHO GETS REWARDED\nWHEN STUDENTS TRULY LEARN?", "WHO PAYS THE PRICE?", "WHO HAS THE POWER\nTO STOP IT?"]
    for k, q in enumerate(qs):
        ta = LS(54) + 0.1 + 0.9 * k if k else AT(54, 0.05)
        ta = [AT(54, 0.02), AT(54, 0.38), AT(54, 0.62)][k]
        card(cv, t, ta, q, 1180, 420 + k * 210, 1000, 150 if k != 1 else 110, size=48, fill=LGOLD if k != 1 else CREAM)
    return cv


def sc_43(t):                                         # lines 55-56: it's a game; system may be working as designed
    u = SG(t, 55, 56)
    cv = base(t, u)
    crack = ease(clamp01((t - AT(55, 0.55)) / 0.8))
    if t < LS(56):
        G(cv)
        fig(cv, 300, 900, h=380, pose="fear", face="worry", w=9)
        tag(cv, t, LS(55) + 0.2, "SCHOOL IS BROKEN", 1100, 380, size=110, col=NAVY) if crack < 0.3 else None
        if crack >= 0.3:
            tag(cv, t, LS(55), "SCHOOL IS BROKEN", 1100, 380, size=110, col=GREY, band=None)
            cv.zig((760, 250), (1440, 520), n=9, jag=30, w=10, col=RED)
        tag(cv, t, AT(55, 0.25), "IT'S A GAME.", 1100, 650, size=100, col=RED)
        return cv
    G(cv)
    tag(cv, t, LS(56) + 0.1, "THE SYSTEM MAY BE WORKING\nEXACTLY AS DESIGNED.", 960, 300, size=96, col=NAVY)
    fig(cv, 960, 900, h=360, pose="shrug", face="sad", w=8)
    cap(cv, t, AT(56, 0.4), "...blaming students for a game they never designed", 960, 720, size=44, col=RED, font="marker")
    return cv


def sc_44(t):                                         # lines 57-58: comments + subscribe + final text
    u = SG(t, 57, 58)
    cv = base(t, u); G(cv)
    fig(cv, 960, 900, h=420, pose="stand" if t < LS(58) else "cheer", face="smile", w=9)
    if t < LS(58):
        bubble(cv, 520, 380, "LEARNING", size=64, tail=(800, 560), reveal=appear(t, LS(57) + 0.5, 0.3), fill=(226, 255, 232))
        bubble(cv, 1400, 380, "LOOKING\nSUCCESSFUL", size=56, tail=(1120, 560), reveal=appear(t, AT(57, 0.45), 0.3), fill=(255, 226, 226))
        tag(cv, t, AT(57, 0.7), "TELL ME IN THE COMMENTS", 960, 160, size=70, col=NAVY)
        return cv
    r = pp(t, LS(58) + 0.2, 0.4)
    clicked = t > AT(58, 0.45)
    with cv.at(960, 300, r):
        cv.rect(-300, -70, 300, 70, r=70, fill=GREY if clicked else RED, w=8)
        cv.text("SUBSCRIBED" if clicked else "SUBSCRIBE", 0, 4, size=70, font="marker", col=PAPER)
    if t > AT(58, 0.8):
        tag(cv, t, AT(58, 0.8), "DON'T JUST CHANGE THE SCHOOL.\nCHANGE THE GAME.", 960, 600, size=84, col=NAVY)
    return cv


# ======================================================================= table, chapter cards, audio, render
SCENES = [(1, sc_1), (3, sc_2), (4, sc_3), (5, sc_4), (6, sc_5), (7, sc_6), (8, sc_7), (10, sc_8), (11, sc_9), (12, sc_10),
          (13, sc_11), (14, sc_12), (15, sc_13), (16, sc_14), (17, sc_15), (19, sc_16),
          (20, sc_17), (21, sc_18), (22, sc_19), (23, sc_20), (24, sc_21), (25, sc_22), (26, sc_23), (27, sc_24), (28, sc_25),
          (30, sc_26), (32, sc_27), (33, sc_28), (34, sc_29), (35, sc_30), (36, sc_31), (37, sc_32),
          (38, sc_33), (39, sc_34), (40, sc_35), (41, sc_36), (42, sc_37), (43, sc_38), (44, sc_39),
          (46, sc_40), (49, sc_41), (53, sc_42), (55, sc_43), (57, sc_44)]
ST = [0.0] + [LS(n) - 0.1 for n, _ in SCENES[1:]]
CHAPTERS = [(1, "COLD OPEN"), (7, "THE EXPERIMENT"), (13, "THE SCHOOL EVERYONE SAYS THEY WANT"), (20, "MEET THE PLAYERS"),
            (30, "WHO HAS THE POWER?"), (38, "WHY SOME SCHOOLS ESCAPE"), (46, "THE REAL LESSON"), (53, "THE ENDING")]
XF = 0.14


def decorate(cv, t):
    cv.text("DEEP TIME ACADEMY", 1690, 1046, size=26, font="cinzel", col=(176, 178, 188))
    for n, title in CHAPTERS:
        a = appear(t, LS(n) - 0.05, 0.3) * (1 - appear(t, LS(n) + 2.8, 0.4))
        if a > 0:
            with cv.fading(a):
                cv.band(60, 36, 60 + cv.text_w(title, 34, "marker") + 50, 94, col=LGOLD, alpha=0.9)
                cv.text(title, 85, 66, size=34, font="marker", col=NAVY, anchor="lm")


def frame_at(t):
    k = max(i for i, s in enumerate(ST) if s <= t)
    cv = SCENES[k][1](t); decorate(cv, t); img = cv.finish()
    if k > 0 and t - ST[k] < XF:
        pv = SCENES[k - 1][1](t); decorate(pv, t)
        img = Image.blend(pv.finish(), img, ease((t - ST[k]) / XF))
    return img


FXT = []
def _fx(n, fr, name): FXT.append((n, fr, name))
for n, fr, name in [(1, .1, "pop"), (1, .55, "pop"), (2, .2, "pop"), (2, .62, "ding"), (3, .1, "pop"), (3, .35, "stamp"), (3, .78, "stamp"), (4, .5, "thud"), (4, .62, "fire"),
                    (5, .3, "boom"), (5, .6, "riser"), (6, .34, "pop"), (6, .42, "pop"), (6, .5, "pop"), (6, .86, "stamp"), (7, .2, "whoosh"), (7, .55, "pop"), (7, .3, "pop"),
                    (9, .08, "pop"), (9, .4, "pop"), (9, .6, "pop"), (10, .3, "scribble"), (11, .3, "pop"), (11, .7, "buzzer"), (12, .1, "pop"), (12, .5, "pop"), (12, .8, "ding"),
                    (13, .2, "pop"), (13, .55, "pop"), (14, .3, "pop"), (14, .72, "stamp"), (15, .05, "pop"), (15, .62, "pop"), (16, .05, "whoosh"), (16, .34, "ding"), (16, .74, "ding"),
                    (17, .62, "buzzer"), (17, .7, "thud"), (18, .04, "pop"), (18, .24, "pop"), (18, .44, "pop"), (18, .7, "boom"), (19, .2, "pop"), (19, .46, "stamp"),
                    (20, .12, "pop"), (20, .5, "pop"), (20, .67, "pop"), (20, .84, "pop"), (21, .3, "pop"), (21, .55, "ding"), (22, .2, "pop"), (22, .45, "pop"),
                    (23, .35, "pop"), (23, .45, "pop"), (23, .55, "pop"), (23, .84, "pop"), (24, .35, "pop"), (24, .4, "pop"), (24, .7, "stamp"), (25, .2, "pop"), (25, .75, "stamp"),
                    (26, .45, "pop"), (26, .65, "ding"), (27, .3, "coin"), (27, .5, "coin"), (28, .2, "pop"), (28, .4, "pop"), (28, .6, "stamp"), (28, .62, "stamp"), (28, .64, "stamp"),
                    (30, .2, "pop"), (30, .5, "pop"), (31, .05, "pop"), (31, .5, "pop"), (31, .85, "pop"), (32, .6, "buzzer"), (33, .45, "boom"), (33, .5, "shimmer"),
                    (34, .1, "pop"), (34, .34, "pop"), (34, .58, "pop"), (34, .82, "pop"), (35, .55, "pop"), (36, .04, "pop"), (36, .24, "pop"), (36, .44, "pop"), (36, .62, "thud"),
                    (37, .3, "pop"), (37, .55, "pop"), (38, .2, "pop"), (38, .5, "ding"), (39, .2, "pop"), (39, .6, "pop"), (40, .2, "pop"), (40, .6, "pop"),
                    (41, .2, "pop"), (41, .6, "pop"), (42, .3, "pop"), (42, .5, "pop"), (43, .55, "thud"), (43, .72, "stamp"), (44, .2, "pop"), (44, .55, "pop"),
                    (46, .5, "whoosh"), (46, .56, "boing"), (47, .05, "stamp"), (47, .35, "stamp"), (47, .65, "stamp"), (48, .2, "buzzer"), (49, .3, "pop"), (50, .1, "pop"),
                    (50, .5, "pop"), (51, .1, "pop"), (51, .5, "pop"), (52, .2, "shimmer"), (53, .2, "pop"), (54, .02, "pop"), (54, .38, "pop"), (54, .62, "pop"),
                    (55, .55, "smash"), (55, .25, "pop"), (56, .1, "boom"), (57, .45, "pop"), (57, .7, "pop"), (58, .2, "pop"), (58, .45, "click"), (58, .46, "ding"), (58, .8, "ding")]:
    _fx(n, fr, name)


def build_audio():
    voice = TL.voice_track()
    fx = np.zeros_like(voice)
    mus = wb.music_fun(TOTAL, level=0.2)[:len(voice)]
    for s in ST[1:]:
        place(fx, wb.SFXF["whoosh"](), s - 0.2)
    for n, fr, name in FXT:
        place(fx, wb.SFXF[name](), AT(n, fr))
    out = p("_mix.wav")
    finish_audio(voice, mus, fx, out, HERE)
    return out


def _render_chunk(job):
    k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        ff.stdin.write(np.asarray(frame_at(k / FPS).convert("RGB")).tobytes())
    ff.stdin.close(); ff.wait()
    return path


def render_parallel(total, audio_wav, out_mp4, procs=4, parts=24):
    import multiprocessing as mp
    nf = int(round(total * FPS))
    tmp = tempfile.mkdtemp(prefix="wb_parts_", dir=HERE)
    bounds = [round(nf * i / parts) for i in range(parts + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(tmp, f"part{i:02d}.mp4")) for i in range(parts)]
    with mp.get_context("fork").Pool(procs) as pool:
        for n, _ in enumerate(pool.imap_unordered(_render_chunk, jobs), 1):
            print(f"chunk {n}/{parts} done", flush=True)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio_wav, "-c:v", "copy",
                    "-af", "alimiter=limit=0.70:level=disabled", "-c:a", "aac", "-ac", "2", "-ar", "44100", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    wav = build_audio()
    out = p("wb05_school_game.mp4")
    render_parallel(TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
