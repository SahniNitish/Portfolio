"""Deep Time Academy whiteboard video: "Why Faking It Is Actually a Superpower" (white paper, stick figures).

    python deeptime/wb01-fake-it/episode.py          # renders dating... no: wb01_fake_it.mp4 (parallel, 4 cores)
    python tools/preview.py deeptime/wb01-fake-it    # contact sheet, one frame per narration line

One function per scene (`sc_*`); scene timing uses SCRIPT LINE NUMBERS (the numbers in lines.txt, 1-based):
AT(n, frac) = time at a fraction of line n's voice, SG(t, n, m) = progress through lines n..m, LS(n)/EN(n) = start/end of line n.
All drawing is done with deeptime/stick.py (hand-drawn look, boiling lines, draw-on reveals).
"""
import math, os, random, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import Timeline, clean_voice, finish_audio, place, sfx, write_wav, SR, FPS  # noqa: E402
from dta import fx_riser, fx_shimmer, fx_hit                                              # noqa: E402
from stick import *                                                                       # noqa: E402,F401,F403
import stick as S                                                                         # noqa: E402

p = lambda *a: os.path.join(HERE, *a)
random.seed(11)
SERIES = "DEEP TIME ACADEMY"

# ---------------------------------------------------------------- voice + timeline
LINES = [l.strip() for l in open(p("lines.txt")) if l.strip()]
N = len(LINES)
os.makedirs(p("audio", "clean"), exist_ok=True)


def _voice(i):
    src, dst = p("audio", f"l{i}.wav"), p("audio", "clean", f"l{i}.wav")
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        clean_voice(src, dst)
    return dst


GAPS = [0.55] * N                                   # pause after each line, by 0-based index (= script line - 1)
for n, g in {4: 0.7, 5: 2.6, 12: 0.9, 15: 1.0, 21: 1.0, 28: 0.9, 30: 0.9, 31: 1.0, 37: 1.0, 36: 0.9, 41: 0.8, 43: 3.0}.items():
    GAPS[n - 1] = g                                 # n is the script line the pause FOLLOWS
TL = Timeline([_voice(i) for i in range(1, N + 1)], GAPS, lead=0.7)
L, END, TOTAL = TL.L, TL.end, TL.total


def AT(n, frac): return L(n - 1) + frac * (END(n - 1) - L(n - 1))
def SG(t, n, m=None): m = n if m is None else m; return clamp01((t - L(n - 1)) / max(END(m - 1) - L(n - 1), 1e-6))
def LS(n): return L(n - 1)
def EN(n): return END(n - 1)


def appear(t, t_in, dur=0.5): return clamp01((t - t_in) / dur)
def pp(t, t_in, dur=0.4): return ease_out_back(clamp01((t - t_in) / dur))


def base(t, u=0.0, zoom=0.035, cx=960, cy=540, shake=0.0):
    z = 1.0 + zoom * u
    sx, sy = (random.uniform(-shake, shake), random.uniform(-shake, shake)) if shake else (0, 0)
    return Canvas(t, cam=(cx + sx, cy + sy, z))


def fig(cv, x, y, h=360, pose="stand", face="neutral", **kw):
    kw.setdefault("w", max(5, h * 0.021))
    return figure(cv, x, y, h=h, pose=pose, face=face, **kw)


def tag(cv, t, t_in, text, x, y, size=56, col=NAVY, font="marker", band=LGOLD, dur=0.5, rot=0, t_out=None):
    """Marker text with a highlighter band, wiped on from the left."""
    r = appear(t, t_in, dur)
    if r <= 0:
        return
    a = 1.0 if t_out is None else 1 - clamp01((t - t_out) / 0.25)
    if a <= 0:
        return
    wd = cv.text_w(text.split("\n")[0] if "\n" not in text else max(text.split("\n"), key=len), size, font)
    nl = text.count("\n") + 1
    with cv.fading(a), cv.at(x, y, 1, rot):
        if band:
            cv.band(-wd / 2 - 16, -size * 0.62 * nl, wd / 2 + 16, size * 0.62 * nl, col=band, reveal=r)
        cv.text(text, 0, 0, size=size, col=col, font=font, reveal=r)


def cap(cv, t, t_in, text, x, y, size=44, col=INK, font="hand", **kw):
    tag(cv, t, t_in, text, x, y, size=size, col=col, font=font, band=None, **kw)


def hold(cv, J, what, hand="hA", s=1.0):
    x, y = J[hand]
    with cv.at(x, y, s):
        if what == "cookie": cookie(cv, 0, 0, 24)
        elif what == "bar":
            cv.line((-150, 0), (150, 0), w=9)
        elif what == "mug": cv.rect(-16, -34, 16, 0, fill=CREAM, w=4)
        elif what == "phone": cv.rect(-18, -50, 18, 6, r=5, fill=SKY, w=5)
        elif what == "brief": cv.rect(-40, -6, 40, 44, r=6, fill=BROWN, w=5)
        elif what == "cam": cv.rect(-34, -26, 34, 22, r=6, fill=LGREY, w=5); cv.ellipse(0, -2, 13, 13, fill=SKY, w=4)
        elif what == "dumb":
            cv.line((-30, 0), (30, 0), w=6); cv.rect(-42, -18, -26, 18, fill=GREY, w=4); cv.rect(26, -18, 42, 18, fill=GREY, w=4)
        elif what == "torch":
            cv.line((0, 40), (0, -8), w=8, col=BROWN); flame(cv, 0, -6, 0.55, cv.t, seed=int(x) % 7)


def label_small(cv, t, t_in, text, x, y, size=32): cap(cv, t, t_in, text, x, y, size=size, col=NAVY)


def sun(cv, x, y, r, rays=True, t=0.0, reveal=1.0):
    cv.ellipse(x, y, r, r, fill=LGOLD, w=6, col=GOLD, reveal=reveal)
    if rays:
        burst_lines(cv, x, y, r * 1.25, r * 1.75, n=14, col=GOLD, w=6, a0=t * 0.2)


def sparkle_burst(cv, x, y, t, t0, r=120, n=10, col=GOLD):
    u = clamp01((t - t0) / 0.6)
    if 0 < u < 1:
        for k in range(n):
            a = 2 * math.pi * k / n
            cv.line((x + math.cos(a) * r * u * 0.6, y + math.sin(a) * r * u * 0.6), (x + math.cos(a) * r * (0.5 + u * 0.7), y + math.sin(a) * r * (0.5 + u * 0.7)),
                    w=6 * (1 - u) + 2, col=col, amp=0.6)


def poof(cv, x, y, t, t0, r=80):
    u = clamp01((t - t0) / 0.7)
    if 0 < u < 1:
        for k in range(6):
            a = 2 * math.pi * k / 6 + 0.4
            cv.ellipse(x + math.cos(a) * r * u, y + math.sin(a) * r * u * 0.8, 24 * (1 - u * 0.5) + 6, w=5, col=GREY, amp=0.6)


def glow_pulse(t, f=3.0): return 0.5 + 0.5 * math.sin(t * f * 2 * math.pi)


# ======================================================================= COLD OPEN (lines 1-5)
S.POSE["sit_cheer"] = dict(A=(160, 10), B=(-160, -10), C=(90, -90), D=(82, -85), lean=-6)
S.POSE["deadlift"] = dict(A=(8, 0), B=(-8, 0), C=(50, -70), D=(42, -62), lean=58)
S.POSE["squat_press"] = dict(A=(14, 0), B=(-14, 0), C=(30, -40), D=(-30, 40))


def chair_side(cv, x, y_seat, ground=900):
    cv.line((x - 70, y_seat), (x + 52, y_seat), w=8)
    cv.line((x - 70, y_seat), (x - 82, y_seat - 190), w=8)
    cv.line((x - 56, y_seat), (x - 56, ground), w=7)
    cv.line((x + 44, y_seat), (x + 44, ground), w=7)


def role_fig(cv, t, t_in, x, role, name, face, gy=560, h=190):
    s = pp(t, t_in)
    if s <= 0.02:
        return
    with cv.at(x, gy, s):
        J = fig(cv, 0, 0, h=h, pose="flex" if role == "fit" else "stand", face=face, w=4.5,
                outfit={"founder": ("suit",), "creator": (), "fit": ("tank",)}[role])
        hold(cv, J, {"founder": "brief", "creator": "cam", "fit": "dumb"}[role], hand="hA", s=0.8)
    label_small(cv, t, t_in + 0.2, name, x, gy + 44)


def sc_open(t):                                   # 1-3: the fraud at the messy desk
    u = SG(t, 1, 3)
    cv = base(t, u, cy=545)
    ground(cv, 900, 80, 1840, reveal=appear(t, 0.0, 0.9))
    desk(cv, 830, 750, 560, reveal=appear(t, 0.1, 0.8), legh=150)
    laptop(cv, 820, 750, 1.5)
    if int(t * 2) % 2 == 0:
        cv.line((812, 668), (812, 696), w=4, amp=0)                    # blinking cursor on the blank screen
    mug(cv, 1040, 750, 1.2, t)
    paper(cv, 650, 738, rot=-14, w=60, h=76); paper(cv, 1110, 878, rot=22, w=64, h=80); paper(cv, 330, 888, rot=-30, w=56, h=70)
    for bx, by in ((260, 880), (1230, 890), (1195, 862), (560, 884)):
        cv.ellipse(bx, by, 16, 14, w=4, fill=PAPER, seed=bx)
    chair_side(cv, 470, 817)
    conf = t > AT(3, 0.12)
    pz = S.POSE["sit_cheer"] if t > AT(3, 0.55) else "type"
    face = "sweat" if not conf else ("big" if t > AT(3, 0.55) else "smirk")
    fig(cv, 450, 900, h=360, pose=pz, face=face)
    if not conf:
        bubble(cv, 400, 390, "I have zero experience.\nI'm a fraud.", size=42, tail=(455, 600), reveal=appear(t, 0.5, 0.6))
    else:
        bubble(cv, 400, 390, "I'm totally confident.*", size=42, tail=(455, 600), reveal=appear(t, AT(3, 0.14), 0.4))
    for x, role, name, n in ((1330, "founder", "FOUNDER", 0.42), (1530, "creator", "CREATOR", 0.58), (1730, "fit", "FIT PERSON", 0.76)):
        role_fig(cv, t, AT(1, n), x, role, name, "sweat" if t < AT(3, 0.15) else "cool")
    for x, txt, n in ((1330, "no idea", 0.22), (1530, "winging it", 0.38), (1730, "send help", 0.54)):
        if AT(2, n) < t < AT(3, 0.1):
            thought(cv, x, 300, txt, size=30, tail_to=(x, 372), reveal=appear(t, AT(2, n), 0.4))
    if t > AT(3, 0.1):                                                     # "reality loading..." bar
        cap(cv, t, AT(3, 0.2), "*reality loading...", 1500, 790, size=38, col=GREY)
        cv.rect(1290, 830, 1710, 872, r=16, w=5)
        fr = 0.27 * appear(t, AT(3, 0.25), EN(3) - AT(3, 0.25))
        if fr > 0.01:
            cv.rect(1296, 836, 1296 + 408 * fr, 866, r=12, fill=GOLD, w=0.01, col=GOLD, amp=0)
        cap(cv, t, AT(3, 0.6), f"{int(fr * 100)}%", 1500, 910, size=34, col=NAVY)
    return cv


def sc_quote(t):                                  # 4: "fake it till you make it" ... with receipts
    cv = base(t, SG(t, 4))
    tag(cv, t, LS(4) + 0.05, '"FAKE IT TILL\nYOU MAKE IT"', 780, 290, size=112, col=NAVY)
    if t > AT(4, 0.2):                                                    # laughing "just a joke" face
        k = pp(t, AT(4, 0.2))
        with cv.at(1480, 250, k * 1.2):
            cv.ellipse(0, 0, 62, 62, fill=LGOLD, w=6)
            cv.curve((-34, -12), (-24, -28), (-12, -12), w=5); cv.curve((12, -12), (24, -28), (36, -12), w=5)
            cv.rect(-30, 8, 30, 38, r=14, fill=PAPER, w=5)
            for sx in (-70, 70):
                cv.line((sx * 0.7, -2), (sx, 14 + 6 * math.sin(t * 8)), w=4, col=BLUE, amp=0)
        cap(cv, t, AT(4, 0.25), "just a joke...", 1480, 360, size=40, col=GREY)
    if t > AT(4, 0.42):
        x = AT(4, 0.42)
        sc = lerp(3.0, 1.0, ease(clamp01((t - x) / 0.2)))
        with cv.fading(clamp01((t - x) / 0.08)):
            stamp(cv, 700, 600, "300 YEARS OLD", col=RED, size=84, rot=-5, s=sc)
    if t > AT(4, 0.7):                                                    # receipt unrolling
        r = ease(clamp01((t - AT(4, 0.7)) / 0.9))
        top, hh = 460, 470 * r
        cv.poly([(1380, top), (1740, top), (1740, top + hh), (1710, top + hh + 14), (1680, top + hh), (1650, top + hh + 14), (1620, top + hh),
                 (1590, top + hh + 14), (1560, top + hh), (1530, top + hh + 14), (1500, top + hh), (1470, top + hh + 14), (1440, top + hh),
                 (1410, top + hh + 14), (1380, top + hh)], closed=True, fill=CREAM, w=5, amp=0.8)
        rows = ["RECEIPTS", "FRANKLIN ..... OK", "XIANG YU ..... OK", "CORTES ....... OK", "TOTAL: IT WORKS"]
        for i, s in enumerate(rows):
            if hh > 70 + i * 80:
                cv.text(s, 1560, top + 46 + i * 80, size=40 if i in (0, 4) else 32, font="marker" if i in (0, 4) else "hand", col=NAVY if i in (0, 4) else INK)
        for i in range(1, 4):
            if hh > 70 + i * 80:
                check(cv, 1710, top + 50 + i * 80, 0.7)
    return cv


def sc_promises(t):                               # 5: three promises
    cv = base(t, SG(t, 5))
    specs = [(0.10, 370, "1", "\"READY\"\nIS A LIE"), (0.40, 960, "2", "OPTIONS ARE\nQUIETLY\nDESTROYING YOU"), (0.72, 1550, "3", "THE FOUR-WORD RULE\nTURNS FAILURE\nINTO FUEL")]
    for n_, (fr, x, num, txt) in enumerate(specs):
        t_in = AT(5, fr)
        r = appear(t, t_in, 0.5)
        if r <= 0:
            continue
        cv.rect(x - 240, 190, x + 240, 800, r=26, w=6, fill=PAPER, reveal=r)
        with cv.fading(r):
            cv.ellipse(x - 190, 250, 34, 34, fill=GOLD, w=5)
            cv.text(num, x - 190, 253, size=44, font="marker")
            cv.text(txt, x + 14, 330, size=46, font="marker", col=NAVY)
        if n_ == 0 and r > 0.6:                                           # waiting for "ready"
            fig(cv, x - 90, 770, h=230, pose="stand", face="worry", w=5)
            with cv.at(x + 120, 640, 1.0):
                cv.ellipse(0, 0, 54, 54, fill=PAPER, w=6)
                cv.line((0, 0), (0, -34), w=5); cv.line((0, 0), (math.cos(t * 3) * 24, math.sin(t * 3) * 24), w=5)
            if t > t_in + 0.8:
                stamp(cv, x + 10, 560, "LIE", size=76, rot=-12, s=pp(t, t_in + 0.8, 0.3))
        if n_ == 1 and r > 0.6:                                           # five exits pulling in different directions
            fig(cv, x, 770, h=230, pose="arms_out", face="worry", w=5)
            for k, (dx, dy) in enumerate(((-150, -120), (150, -120), (-170, 40), (170, 40), (0, -190))):
                cv.arrow((x + dx * 0.35, 640 + dy * 0.35), (x + dx, 640 + dy), w=5, col=RED, amp=1.0, seed=k, head=20)
        if n_ == 2 and r > 0.6:                                           # four blanks + fuel can
            for k in range(4):
                cv.line((x - 205 + k * 100, 560), (x - 135 + k * 100, 560), w=7, col=NAVY)
            cv.text("?", x, 480, size=80, font="marker", col=GOLD)
            with cv.at(x, 760, 1.0):
                cv.rect(-60, -100, 60, 0, r=10, fill=RED, w=6)
                cv.poly([(-20, -100), (-20, -126), (40, -126), (40, -100)], w=6)
                cv.text("FUEL", 0, -48, size=42, font="marker", col=PAPER)
            flame(cv, x + 90, 740, 0.9, t)
    return cv


def sc_title(t):                                  # title slam
    t0 = EN(5) + 0.25
    k = clamp01((t - t0) / 0.3)
    cv = base(t, 0, shake=16 * (1 - k) if t > t0 else 0)
    if t > t0:
        s = lerp(3.4, 1.0, ease(clamp01((t - t0) / 0.2)))
        with cv.fading(clamp01((t - t0) / 0.08)), cv.at(960, 400, s):
            cv.band(-760, -220, 760, -50, col=LGOLD, alpha=0.0)
            cv.text("WHY FAKING IT", 0, -130, size=170, font="marker", col=NAVY)
            cv.band(-720, 10, 720, 160, col=LGOLD, alpha=0.85, reveal=clamp01((t - t0 - 0.25) / 0.5))
            cv.text("IS A SUPERPOWER", 0, 90, size=170, font="marker", col=NAVY)
        if 0 < t - t0 < 0.5:
            burst_lines(cv, 960, 420, 560, 560 + 220 * clamp01((t - t0) / 0.3), n=18, col=GOLD, w=7)
    if t > t0 + 0.6:
        s = pp(t, t0 + 0.6, 0.45)
        with cv.at(960, 1000, s):
            fig(cv, 0, 0, h=320, pose="hips", face="cool", outfit=("cape", "crown"))
        sparkles(cv, 960, 760, t, n=6, r=150)
    return cv


# ======================================================================= ACT I (lines 6-15)
def sc_split(t):                                  # 6: born good or made good
    cv = base(t, SG(t, 6))
    cv.line((960, 150), (960, 990), w=6, col=GREY, reveal=appear(t, LS(6), 0.8))
    r1 = pp(t, AT(6, 0.2))
    if r1 > 0.02:
        with cv.at(470, 540, r1 * 1.6):
            cloud(cv, 0, 0, 1.0)
            draw_face(cv, (0, 8), 52, "cry", 1, t, w=5)
        for k in range(5):
            ph = (t * 1.1 + k * 0.21) % 1
            cv.line((380 + k * 45, 640 + ph * 220), (376 + k * 45, 664 + ph * 220), w=5, col=BLUE, amp=0)
        tag(cv, t, AT(6, 0.3), "ROUSSEAU", 470, 880, size=58)
    r2 = pp(t, AT(6, 0.5))
    if r2 > 0.02:
        with cv.at(1440, 520, r2):
            gear(cv, 0, 0, 150, 12, ang=t * 30)
            gear(cv, 185, 120, 90, 9, ang=-t * 30 * 1.65 + 13)
            gear(cv, -150, 150, 70, 8, ang=-t * 30 * 2.1 + 5)
            for sx in (-1, 1):
                cv.ellipse(sx * 44, -8, 32, 32, w=5)
            cv.line((-12, -8), (12, -8), w=5)
        tag(cv, t, AT(6, 0.6), "FRANKLIN", 1440, 880, size=58)
    tag(cv, t, LS(6) + 0.2, "BORN GOOD...  or  MADE GOOD?", 960, 140, size=70, col=NAVY)
    return cv


def sc_pure(t):                                   # 7: pure heart -> cookie thief -> zap
    sw = ease((t - AT(7, 0.44)) / 0.1)
    cv = base(t, SG(t, 7))
    with cv.fading(1 - sw):
        if sw < 1:
            r = pp(t, LS(7))
            with cv.at(380, 450, r * 1.2):
                cloud(cv, 0, 0, 0.8)
                draw_face(cv, (0, 8), 46, "happy", 1, t, w=5)
            cap(cv, t, LS(7) + 0.3, "\"humans are born pure\"", 380, 580, size=40, col=NAVY)
            fall = ease((t - AT(7, 0.22)) / 0.3)
            fig(cv, 960, 900, h=340, pose="stand", face="happy" if fall < 0.3 else "sad")
            with cv.at(960, 900 - 0.95 * 340 - 34 + fall * 120, 1.0, fall * 25):
                cv.ellipse(0, 0, 40, 12, w=6, col=GOLD)
            if t > AT(7, 0.2):
                for k in range(7):
                    q = clamp01((t - AT(7, 0.2) - k * 0.1) / 0.5)
                    cv.zig((1560 - q * 380, 600 + 50 * math.sin(k)), (1560 - q * 380 + 90, 640 + 60 * math.cos(k)), n=4, jag=14, w=7, col=INK, seed=k, reveal=q)
                tag(cv, t, AT(7, 0.25), "THE WORLD", 1500, 440, size=60, col=RED, band=None)
    with cv.fading(sw):
        if sw > 0:
            desk(cv, 1360, 640, 400, legh=260)
            with cv.at(1190, 640):
                cv.poly([(-50, 0), (-56, -90), (-36, -122), (36, -122), (56, -90), (50, 0)], closed=True, fill=SKY, w=6)
                cv.rect(-40, -146, 40, -122, r=6, fill=GOLD, w=5)
                cookie(cv, -8, -64, 20); cookie(cv, 18, -44, 18)
                cv.text("COOKIES", 0, -102, size=22, font="marker")
            zapped = t > AT(7, 0.93)
            x0 = 940
            pz = "sneak" if t < AT(7, 0.5) else ("shrug" if not zapped else "fear")
            if not zapped and AT(7, 0.5) < t < AT(7, 0.62):
                pz = pose_mix("sneak", "point", 0.5)
            J = fig(cv, x0, 900, h=380, pose=pz, face="smirk" if not zapped else "dead", outfit=("wild",) if zapped else ())
            if AT(7, 0.6) < t and not zapped:
                hold(cv, J, "cookie", hand="hA", s=1.0)
            if not zapped and t > AT(7, 0.75):
                bubble(cv, 700, 380, "My intentions\nwere good!", size=44, tail=(x0, 560), reveal=appear(t, AT(7, 0.75), 0.4))
            if zapped:
                for k in range(3):
                    cv.curve((x0 - 30 + k * 30, 520), (x0 - 40 + k * 30, 470 - ((t * 60) % 40), ), (x0 - 28 + k * 30, 420 - ((t * 60) % 40)), w=4, col=GREY, amp=0.5)
                cap(cv, t, AT(7, 0.93) + 0.1, "BZZZT!", 640, 520, size=80, col=RED, font="marker")
    z0 = AT(7, 0.93)
    if z0 < t < z0 + 0.45:                                                  # the lightning bolt itself
        for w_, c_ in ((26, GOLD), (10, PAPER)):
            cv.zig((960 if False else 940, -20), (940, 560), n=8, jag=70, w=w_, col=c_, seed=int(t * 30) % 5, amp=2.5)
        burst_lines(cv, 940, 560, 60, 130, n=12, col=GOLD, w=6)
    return cv


def sc_franklin(t):                               # 8: Franklin says nope; no good person inside, only actions
    cv = base(t, SG(t, 8))
    fig(cv, 1480, 900, h=400, pose="point", face="smirk", flip=True, outfit=("tricorn", "glasses", "longhair"))
    bubble(cv, 1180, 330, "NOPE.", size=76, font="marker", tail=(1440, 540), reveal=appear(t, LS(8) + 0.1, 0.4))
    r = appear(t, AT(8, 0.3), 0.5)
    J = fig(cv, 620, 900, h=420, pose="stand", face="neutral")
    if r > 0:
        cv.rect(J["hip"][0] - 44, J["neck"][1] + 30, J["hip"][0] + 44, J["hip"][1] - 8, fill=PAPER, w=5, reveal=r)
        if r > 0.9:
            cv.text("?", J["hip"][0], (J["hip"][1] + J["neck"][1]) / 2 + 20, size=64, font="marker", col=GREY)
            tx = ((t * 120) % 140) - 20
            cv.ellipse(J["hip"][0] - 40 + tx, J["hip"][1] - 26, 12, 12, w=4, col=BROWN, amp=0.6)
        cap(cv, t, AT(8, 0.34), "no \"good person\" inside", 330, 520, size=40, col=RED, rot=-4)
    if t > AT(8, 0.62):
        tag(cv, t, AT(8, 0.62), "ONLY ACTIONS:", 960, 150, size=64)
        for k, (x, ok, txt) in enumerate(((820, True, "good"), (960, True, "good"), (1100, False, "bad"))):
            t_k = AT(8, 0.74 + 0.07 * k)
            if t > t_k:
                (check if ok else xmark)(cv, x, 250, 0.9)
                cap(cv, t, t_k, txt, x, 305, size=36, col=GREEN if ok else RED)
    return cv


def sc_habit(t):                                  # 9: character is a habit
    cv = base(t, SG(t, 9))
    tag(cv, t, LS(9) + 0.05, "CHARACTER", 960, 250, size=150, col=NAVY)
    cap(cv, t, AT(9, 0.3), "isn't a feeling", 960, 440, size=76, col=GREY, font="marker")
    if t > AT(9, 0.4):
        cv.line((700, 440), (1220, 440), w=9, col=RED, reveal=appear(t, AT(9, 0.4), 0.3), amp=1.2)
    tag(cv, t, AT(9, 0.62), "it's a HABIT", 960, 680, size=130, col=NAVY)
    if t > AT(9, 0.7):                                                     # habit loop arrow
        r = appear(t, AT(9, 0.7), 0.7)
        pts = [(960 + 480 * math.cos(a), 680 + 150 * math.sin(a)) for a in np.linspace(math.pi * 0.15, math.pi * 1.85, 30)]
        cv.poly(pts, w=7, col=GOLD, reveal=r, amp=1.0, step=80)
        if r > 0.95:
            cv.arrow((pts[-3][0], pts[-3][1]), pts[-1], w=7, col=GOLD, head=34)
    return cv


FRANKLIN_VIRTUES = ["Temperance", "Silence", "Order", "Resolution", "Frugality", "Industry", "Sincerity", "Justice", "Moderation", "Cleanliness",
                    "Tranquillity", "Chastity", "Humility"]
_rg = random.Random(5)
FAULT_CELLS = sorted(_rg.sample([(r, c) for r in range(13) for c in range(7)], 24), key=lambda rc: rc[1] * 20 + rc[0])


def sc_notebook(t):                               # 10: Franklin's 13-virtue notebook, graded weekly
    cv = base(t, SG(t, 10), cx=900)
    r = pp(t, LS(10) + 0.05, 0.5)
    with cv.at(680, 560, r, -2):
        cv.rect(-390, -360, 390, 360, r=14, fill=CREAM, w=7)
        for k in range(9):
            cv.ellipse(-390, -310 + k * 78, 11, 11, fill=PAPER, w=4, amp=0.4)
        cv.text("13 VIRTUES", -20, -318, size=54, font="marker", col=NAVY)
        for j, d in enumerate("SMTWTFS"):
            cv.text(d, 40 + j * 62, -262, size=28, font="marker", col=GREY)
        for i, name in enumerate(FRANKLIN_VIRTUES):
            y = -222 + i * 40
            cv.text(name, -360, y, size=25, anchor="lm")
            cv.line((-370, y + 18), (330, y + 18), w=2, col=LGREY, amp=0.3)
        for j in range(8):
            cv.line((10 + j * 62, -246), (10 + j * 62, 298), w=2, col=LGREY, amp=0.3)
        for k, (ri, ci) in enumerate(FAULT_CELLS):
            if t > AT(10, 0.3 + 0.017 * k):
                cv.ellipse(41 + ci * 62, -222 + ri * 40, 8, 8, fill=RED, w=1, col=RED, amp=0)
    fig(cv, 1480, 900, h=400, pose="point", face="smile", flip=True, outfit=("tricorn", "glasses", "longhair"))
    cap(cv, t, AT(10, 0.2), "thirteen virtues", 1450, 330, size=44, col=NAVY)
    cap(cv, t, AT(10, 0.5), "graded every week", 1450, 395, size=44, col=NAVY)
    if t > AT(10, 0.82):
        stamp(cv, 1450, 520, "HOMEWORK\nFOR HIS SOUL", col=RED, size=48, rot=-6, s=lerp(2.5, 1.0, ease(clamp01((t - AT(10, 0.82)) / 0.2))))
    return cv


def sc_gym1(t):                                   # 11: day one, can't lift the bar; shows up daily
    cv = base(t, SG(t, 11))
    ground(cv, 900, 80, 1840)
    shake = 5 * math.sin(t * 28) if t < AT(11, 0.3) or True else 0
    J = fig(cv, 760, 900, h=380, pose="deadlift", face="sweat" if t < AT(11, 0.8) else "smirk", outfit=("tank", "pajamas"), bob=abs(shake) * 0.6)
    bar_y = 872
    cv.line((560, bar_y), (900, bar_y), w=9)
    cv.ellipse(556, bar_y, 6, 6, fill=INK); cv.ellipse(904, bar_y, 6, 6, fill=INK)
    cap(cv, t, LS(11) + 0.2, "DAY ONE: can't lift the empty bar", 960, 190, size=50, col=NAVY)
    if t > AT(11, 0.3):                                                      # calendar flipping through the days
        n_ = min(6, 1 + int((t - AT(11, 0.3)) / 0.55))
        fl = (t - AT(11, 0.3)) % 0.55
        with cv.at(1560, 360, 1.0):
            cv.rect(-130, -130, 130, 150, r=12, fill=PAPER, w=6)
            cv.rect(-130, -130, 130, -70, r=12, fill=RED, w=6)
            sx = max(0.05, abs(math.cos(fl / 0.55 * math.pi)) if fl < 0.2 else 1.0)
            with cv.at(0, 10, 1.0):
                cv.text(f"DAY {n_}", 0, 10, size=64 * sx if sx < 1 else 64, font="marker", col=NAVY)
            check(cv, 70, 100, 0.9)
        cap(cv, t, AT(11, 0.34), "shows up daily", 1560, 560, size=44, col=GREEN)
    if t > AT(11, 0.55):
        bubble(cv, 1100, 400, "bro. leg day.\nprotein.", size=44, tail=(820, 560), reveal=appear(t, AT(11, 0.55), 0.4))
    if t > AT(11, 0.78):
        cap(cv, t, AT(11, 0.78), "tank top (over pajamas)", 520, 560, size=42, col=RED, rot=-4)
        cv.arrow((560, 590), (700, 690), w=5, col=RED, reveal=appear(t, AT(11, 0.8), 0.3), head=22)
    return cv


def sc_potato(t):                                 # 12: a slightly stronger potato
    cv = base(t, SG(t, 12))
    ground(cv, 900, 300, 1620)
    tag(cv, t, LS(12) + 0.05, "YEAR ONE", 960, 160, size=88, col=NAVY)
    wob = 2.5 * math.sin(t * 9)
    potato(cv, 960, 900, 2.0, face="sweat" if t < AT(12, 0.55) else "smile", arms="up", wobble=wob, t=t)
    barbell(cv, 960, 478 - abs(wob) * 3, plates=1, w_bar=420)
    if t > AT(12, 0.45):
        cv.arrow((1450, 360), (1220, 560), w=6, col=RED, reveal=appear(t, AT(12, 0.45), 0.4), head=26)
        cap(cv, t, AT(12, 0.45), "a slightly stronger\npotato", 1560, 330, size=48, col=RED, rot=-3)
    return cv


def sc_year3(t):                                  # 13: year three, that guy; the body followed the behaviour
    cv = base(t, SG(t, 13))
    ground(cv, 900, 80, 1840)
    tag(cv, t, LS(13) + 0.05, "YEAR THREE", 700, 160, size=88, col=NAVY)
    pz = pose_mix("flex", "lift", ease(clamp01((t - AT(13, 0.25)) / 0.4)))
    J = fig(cv, 700, 900, h=430, pose=pz, face="cool" if t > AT(13, 0.1) else "smirk", w=16, outfit=("tank",))
    if t > AT(13, 0.25):
        barbell(cv, 700, J["hA"][1] - 34, plates=3, w_bar=420)
    cap(cv, t, AT(13, 0.12), "THAT GUY.", 1180, 300, size=76, col=RED, font="marker", rot=-4)
    if t > AT(13, 0.55):
        for x, txt, tin in ((1350, "BEHAVIOR", 0.55), (1700, "BODY", 0.75)):
            r = appear(t, AT(13, tin), 0.4)
            cv.rect(x - 130, 590, x + 130, 690, r=18, w=6, reveal=r)
            cv.text(txt, x, 642, size=44, font="marker", col=NAVY, reveal=r)
        cv.arrow((1490, 640), (1560, 640), w=7, col=GOLD, reveal=appear(t, AT(13, 0.68), 0.3), head=24)
        cap(cv, t, AT(13, 0.8), "the body just followed", 1520, 750, size=40, col=GREY)
    return cv


def sc_identity(t):                               # 14: you act your way into a new identity
    cv = base(t, SG(t, 14))
    ground(cv, 900, 80, 1840)
    with cv.at(400, 520, pp(t, LS(14) + 0.1)):
        cv.ellipse(0, 0, 120, 120, fill=PAPER, w=7)
        draw_face(cv, (0, 10), 120, "worry", 1, t, w=7)
    thought(cv, 420, 250, "I'll think my way\ninto a new me...", size=40, tail_to=(400, 380), reveal=appear(t, LS(14) + 0.3, 0.5))
    if t > AT(14, 0.3):
        xmark(cv, 400, 250, 4.2, reveal=appear(t, AT(14, 0.3), 0.4))
    r = appear(t, AT(14, 0.35), 0.5)
    with cv.at(1460, 900):
        cv.rect(-110, -440, 110, 0, w=8, fill=CREAM, reveal=r)
        cv.ellipse(70, -200, 9, 9, fill=GOLD, w=2, reveal=r)
        tag(cv, t, AT(14, 0.45), "NEW\nIDENTITY", 0, -330, size=44, col=NAVY, band=None)
    ph = t * 7
    xx = lerp(760, 1360, ease(clamp01((t - AT(14, 0.4)) / (EN(14) - AT(14, 0.4)) * 1.1)))
    if xx < 1370:
        fig(cv, xx, 900, h=340, pose=walk_pose(ph, 0.9), face="smile")
    tag(cv, t, AT(14, 0.7), "ACT YOUR WAY IN", 1000, 190, size=70, col=NAVY)
    return cv


def sc_dragon(t):                                 # 15: faking confidence vs faking a dragon
    cv = base(t, SG(t, 15))
    ground(cv, 920, 80, 1840)
    cv.line((960, 150), (960, 900), w=5, col=GREY, reveal=appear(t, LS(15), 0.6))
    fig(cv, 500, 920, h=400, pose="hips", face="cool", outfit=("crown", "suit"))
    tag(cv, t, LS(15) + 0.15, "faking confidence", 500, 190, size=58, col=GREEN)
    check(cv, 760, 250, 1.4, reveal=appear(t, AT(15, 0.35), 0.4))
    r = pp(t, AT(15, 0.4))
    if r > 0.02:
        with cv.at(1400, 920, r):
            J = fig(cv, 0, 0, h=400, pose="arms_out", face="angry", outfit=("horns",))
            sh = J["sh"]
            for s_ in (-1, 1):
                cv.poly([sh, (sh[0] + s_ * 190, sh[1] - 150), (sh[0] + s_ * 120, sh[1] - 30), (sh[0] + s_ * 210, sh[1] - 20), (sh[0] + s_ * 90, sh[1] + 50)],
                        closed=True, fill=(150, 214, 150), w=5, amp=0.8)
            cv.curve(J["hip"], (J["hip"][0] - 120, J["hip"][1] + 40), (J["hip"][0] - 190, J["hip"][1] - 50), w=7, col=GREEN)
            if t > AT(15, 0.5):
                flame(cv, J["head"][0] + 90 + 10 * math.sin(t * 9), J["head"][1] + 20, 1.0, t)
        tag(cv, t, AT(15, 0.42), "faking a dragon", 1400, 190, size=58, col=RED)
    if t > AT(15, 0.7):
        r = pp(t, AT(15, 0.7), 0.4)
        with cv.at(960, 980, r):
            cv.rect(-210, -70, 210, 40, r=12, fill=PAPER, w=6)
            cv.rect(-210, -70, 210, -34, r=12, fill=RED, w=6)
            cv.text("HELLO, MY NAME IS", 0, -52, size=24, font="marker", col=PAPER)
            cv.text("________", 0, 10, size=40, font="hand", col=GREY)
        cap(cv, t, AT(15, 0.76), "...it has a name.", 960, 880, size=50, col=NAVY)
    return cv


# ======================================================================= ACT II (lines 16-21)
def sc_lab(t):                                    # 16: two potions
    cv = base(t, SG(t, 16))
    ground(cv, 900, 80, 1840)
    cv.line((520, 740), (1800, 740), w=9, reveal=appear(t, LS(16), 0.6))
    for x in (640, 1500):
        cv.line((x, 740), (x, 900), w=9, reveal=appear(t, LS(16) + 0.1, 0.5))
    fig(cv, 470, 900, h=420, pose="hips" if t < AT(16, 0.4) else "arms_out", face="angry" if t < AT(16, 0.4) else "big", outfit=("labcoat", "goggles", "wild"))
    cap(cv, t, LS(16) + 0.2, "VARUN MAYYA, entrepreneur", 560, 190, size=44, col=NAVY)
    r1 = pp(t, AT(16, 0.45), 0.45)
    if r1 > 0.02:
        flask(cv, 1020, 740, GREEN, s=1.5 * r1, fill_amt=0.7, t=t, sparkle=True)
        tag(cv, t, AT(16, 0.5), "TYPE 1", 1020, 860 + 70, size=60, col=GREEN, band=None) if False else None
        tag(cv, t, AT(16, 0.5), "TYPE 1", 1020, 330, size=64, col=GREEN)
    r2 = pp(t, AT(16, 0.78), 0.45)
    if r2 > 0.02:
        flask(cv, 1560, 740, PURPLE, s=1.5 * r2, fill_amt=0.75, t=t, smoke=True)
        tag(cv, t, AT(16, 0.82), "TYPE 2", 1560, 330, size=64, col=PURPLE)
    return cv


def sc_type1(t):                                  # 17: the biggest company in my city
    cv = base(t, SG(t, 17))
    ground(cv, 900, 80, 1840)
    r = appear(t, LS(17), 0.8)
    for k, (x, hh, w_) in enumerate(((700, 220, 120), (840, 330, 130), (1000, 520, 170), (1170, 280, 120), (1290, 190, 100), (560, 160, 110))):
        cv.rect(x - w_ / 2, 900 - hh * r, x + w_ / 2, 900, w=7, fill=PAPER if k != 2 else LGOLD, reveal=r)
        for q in range(int(hh // 90)):
            cv.rect(x - 26, 900 - hh * r + 24 + q * 80, x + 26, 900 - hh * r + 50 + q * 80, w=3, col=GREY) if r > 0.95 else None
    if r > 0.95:
        cv.line((1000, 380), (1000, 300), w=6)
        cv.poly([(1000, 300), (1070, 322), (1000, 346)], closed=True, fill=RED, w=4, amp=0.5)
    fig(cv, 360, 900, h=330, pose="hips", face="smirk", outfit=("suit",))
    bubble(cv, 420, 360, "I'll build the biggest\ncompany in my city.", size=40, tail=(360, 560), reveal=appear(t, LS(17) + 0.2, 0.5))
    if t > AT(17, 0.34):
        cap(cv, t, AT(17, 0.34), "sounds insane...", 1500, 240, size=50, col=RED, rot=-3)
    if t > AT(17, 0.5):                                                         # normal humans have done it thousands of times
        cap(cv, t, AT(17, 0.5), "done by normal humans:", 1520, 400, size=44, col=NAVY)
        n_ = int(clamp01((t - AT(17, 0.5)) / (0.3 * (EN(17) - LS(17)))) * 24)
        tally(cv, 1380, 450, n_, 1.0)
        cap(cv, t, AT(17, 0.58), "thousands of times", 1520, 580, size=44, col=GREY)
    tag(cv, t, AT(17, 0.78), "CRAZY... WITH MATH BEHIND IT", 960, 120, size=60, col=GREEN)
    return cv


def tapered(cv, p0, pc, p1, w0, w1, fill, n=16, **kw):
    """Filled, tapering ribbon along a quadratic curve (tails, necks)."""
    ts = np.linspace(0, 1, n)[:, None]
    p0, pc, p1 = (np.asarray(v, np.float32) for v in (p0, pc, p1))
    c = (1 - ts) ** 2 * p0 + 2 * (1 - ts) * ts * pc + ts ** 2 * p1
    d = np.gradient(c, axis=0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1) / (np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-6)
    w = (w0 + (w1 - w0) * ts) / 2
    cv.poly(np.vstack([c + nrm * w, (c - nrm * w)[::-1]]), closed=True, fill=fill, **kw)


def dragon_doodle(cv, x, y, s=1.0, t=0.0, breath=False):
    G, D = (150, 214, 150), (104, 176, 120)
    with cv.at(x, y, s):
        cv.poly([(-10, -150), (-150, -340), (-90, -260), (-30, -350), (20, -262), (120, -320), (90, -150)], closed=True, fill=D, w=7, amp=1.0, seed=3)   # wings
        for q in range(3):
            cv.line((0, -150), (-100 + q * 60, -300 + abs(q - 1) * 30), w=3, col=GREEN, amp=0.5)
        tapered(cv, (-120, -100), (-260, -10), (-330, -150), 70, 8, G, w=7, amp=1.0, seed=2)                            # tail
        cv.poly([(-340, -150), (-380, -190), (-322, -178)], closed=True, fill=GOLD, w=4, amp=0.3)
        cv.line((-70, -30), (-80, 50), w=10); cv.line((70, -30), (80, 50), w=10)                                        # legs
        cv.line((-80, 50), (-40, 50), w=8); cv.line((80, 50), (120, 50), w=8)
        cv.ellipse(0, -100, 150, 88, fill=G, w=8, seed=4)                                                              # body
        cv.ellipse(10, -70, 100, 46, fill=(214, 240, 200), w=2, col=GREEN, amp=0.6)                                    # belly
        tapered(cv, (110, -140), (210, -190), (200, -260), 64, 44, G, w=7, amp=0.8, seed=6)                             # neck
        cv.poly([(150, -300), (250, -300), (310, -262), (258, -236), (170, -232)], closed=True, fill=G, w=7, amp=0.8, seed=8)   # head
        cv.ellipse(228, -276, 7, 7, fill=INK, w=1); cv.ellipse(292, -262, 4, 4, fill=INK, w=1)
        for q in range(2):
            cv.poly([(170 + q * 40, -300), (166 + q * 40, -352), (200 + q * 40, -304)], closed=True, fill=GOLD, w=4, amp=0.3)
        for q in range(7):
            bx = -110 + q * 36
            cv.poly([(bx, -184 + abs(q - 3) * 9), (bx + 10, -214 + abs(q - 3) * 9), (bx + 24, -184 + abs(q - 3) * 9)], closed=True, fill=GOLD, w=3, amp=0.3)
        if breath:
            with cv.at(318 + 8 * math.sin(t * 9), -250, 1.0, 90):
                flame(cv, 0, 0, 1.5, t)


def sc_type2(t):                                  # 18: "I'll become an actual dragon"
    cv = base(t, SG(t, 18))
    ground(cv, 900, 80, 1840)
    fig(cv, 330, 900, h=330, pose="arms_out", face="big", outfit=("horns",))
    bubble(cv, 380, 360, "I'll become an\nactual dragon.", size=42, tail=(330, 560), reveal=appear(t, LS(18) + 0.1, 0.5))
    dragon_doodle(cv, 900, 880, 1.2 * pp(t, AT(18, 0.45)), t, breath=t > AT(18, 0.55))
    if t > AT(18, 0.55):
        x = 1650
        cv.rect(x - 230, 430, x + 230, 840, r=20, w=6, fill=PAPER, reveal=appear(t, AT(18, 0.55), 0.5))
        with cv.fading(appear(t, AT(18, 0.6), 0.4)):
            cv.text("DOCUMENTED CASES", x, 490, size=34, font="marker", col=NAVY)
            cv.text("0", x, 580, size=120, font="marker", col=RED)
            cv.text("ROI: ", x - 70, 700, size=44, font="marker", col=NAVY)
            cv.poly([(x - 10, 670), (x + 40, 700), (x + 80, 690), (x + 130, 735)], w=7, col=RED, amp=0.8)
    if t > AT(18, 0.82):
        stamp(cv, 960, 300, "AVOID", col=RED, size=100, rot=-8, s=lerp(2.6, 1.0, ease(clamp01((t - AT(18, 0.82)) / 0.2))))
    return cv


def sc_diary(t):                                  # 19: diary entry vision, then nothing
    cv = base(t, SG(t, 19))
    ground(cv, 900, 80, 1840)
    desk(cv, 760, 700, 520, legh=200)
    chair_side(cv, 360, 817)
    J = fig(cv, 345, 900, h=360, pose="type", face="happy" if t < AT(19, 0.5) else "blank")
    cv.rect(640, 640, 780, 700, r=6, fill=PAPER, w=6)                          # the diary
    cv.line((710, 640), (710, 700), w=4)
    for k in range(2):
        cv.line((652, 658 + k * 20), (700, 658 + k * 20), w=3, col=GREY, amp=0.5)
    sparkles(cv, 700, 600, t, n=4, r=70)
    bubble(cv, 500, 330, "My vision is pure!", size=46, tail=(350, 530), reveal=appear(t, LS(19) + 0.5, 0.5))
    if t > AT(19, 0.55):
        cap(cv, t, AT(19, 0.55), "...and then they do nothing.", 1340, 250, size=50, col=RED, rot=-2)
        with cv.at(1520, 520, pp(t, AT(19, 0.6))):                                  # wall clock
            cv.ellipse(0, 0, 90, 90, fill=PAPER, w=7)
            cv.line((0, 0), (0, -52), w=6); cv.line((0, 0), (math.cos(t * 6) * 70, math.sin(t * 6) * 70), w=5)
        cap(cv, t, AT(19, 0.7), "TODAY'S ACTION:  ______", 1500, 740, size=44, col=NAVY)
        tx = ((t * 160) % 700) - 100
        if t > AT(19, 0.75):
            cv.ellipse(1000 + tx * 0.9, 880, 20, 20, w=5, col=BROWN, amp=1.5)
    return cv


def sc_winners(t):                                # 20: look wildly unqualified, act it out anyway
    cv = base(t, SG(t, 20))
    ground(cv, 900, 80, 1840)
    r = pp(t, LS(20) + 0.1)
    xx = lerp(500, 1000, ease(clamp01((t - AT(20, 0.4)) / 0.4)))
    pz = "stand" if t < AT(20, 0.4) else pose_mix("stand", "hips", ease(clamp01((t - AT(20, 0.7)) / 0.3)))
    J = fig(cv, xx, 900, h=400, pose=pz, face="worry" if t < AT(20, 0.55) else "smirk", outfit=("suit", "glasses"))
    with cv.at(xx, 820, 1.0):                                                        # suit that's too big: sleeves hanging over the hands
        pass
    cap(cv, t, AT(20, 0.3), "wildly unqualified", 480, 330, size=50, col=RED, rot=-4)
    if t > AT(20, 0.3):
        cv.arrow((560, 360), (xx - 20, 440), w=5, col=RED, reveal=appear(t, AT(20, 0.32), 0.3), head=22)
    with cv.at(1480, 900, appear(t, AT(20, 0.5), 0.4)):                              # CEO podium
        cv.poly([(-120, 0), (-100, -300), (100, -300), (120, 0)], closed=True, fill=CREAM, w=8)
        cv.text("CEO", 0, -190, size=84, font="marker", col=NAVY)
    if t > AT(20, 0.62):
        bubble(cv, 1100, 260, "Hello. I am\nvery qualified.", size=40, tail=(xx + 40, 480), reveal=appear(t, AT(20, 0.62), 0.4))
    tag(cv, t, AT(20, 0.82), "ACTING IT OUT ANYWAY", 960, 130, size=64, col=GREEN)
    return cv


def sc_exits(t):                                  # 21: remove your exits
    cv = base(t, SG(t, 21))
    ground(cv, 900, 80, 1840)
    for k, x in enumerate((420, 800, 1180, 1560)):
        r = pp(t, LS(21) + 0.05 + 0.1 * k, 0.35)
        if r > 0.02:
            with cv.at(x, 330, r):
                cv.rect(-110, -50, 110, 50, r=8, fill=GREEN, w=6)
                cv.text("EXIT", 0, 2, size=60, font="marker", col=PAPER)
        if t > AT(21, 0.18 + 0.1 * k):
            cv.line((x - 130, 270), (x + 130, 392), w=14, col=RED, reveal=appear(t, AT(21, 0.18 + 0.1 * k), 0.25), amp=1.5)
            cv.line((x + 130, 270), (x - 130, 392), w=14, col=RED, reveal=appear(t, AT(21, 0.22 + 0.1 * k), 0.25), amp=1.5)
    fig(cv, 640, 900, h=360, pose="stand", face="worry" if t < AT(21, 0.55) else "smirk")
    tag(cv, t, AT(21, 0.3), "REMOVE YOUR EXITS", 1130, 650, size=72, col=NAVY)
    if t > AT(21, 0.66):                                                           # the order, rolled scroll with a seal
        r = pp(t, AT(21, 0.66), 0.45)
        with cv.at(1300, 810, r):
            cv.rect(-300, -60, 300, 60, r=22, fill=CREAM, w=7)
            cv.ellipse(-300, 0, 20, 60, fill=LGOLD, w=6); cv.ellipse(300, 0, 20, 60, fill=LGOLD, w=6)
            cv.text("THE MOST BRUTAL ORDER\nIN MILITARY HISTORY", 0, 0, size=34, font="marker", col=RED)
            cv.ellipse(220, 70, 24, 24, fill=RED, w=4)
    return cv


# ======================================================================= ACT III (lines 22-31)
def mini_row(cv, x0, y, n, gap, h=70, t=0.0, col=INK, phase0=0.0, flip=False, **kw):
    for k in range(n):
        mini(cv, x0 + k * gap, y, h=h, phase=phase0 + k * 0.9 + t * 6, col=col, flip=flip, seed=k + 1, **kw)


def sc_river(t):                                  # 22: 207 BC, Xiang Yu crosses a river at dawn
    u = SG(t, 22)
    cv = base(t, u)
    rise = ease(clamp01((t - LS(22)) / 2.0))
    sun(cv, 1420, 470 - 70 * rise, 110, t=t, reveal=appear(t, LS(22), 0.8))
    cv.line((0, 560), (W, 560), w=5, col=GREY, amp=1.5)
    cv.poly([(1200, 560), (1330, 470), (1450, 540), (1560, 440), (1760, 560)], w=6, col=GREY, amp=1.2)           # far hills
    waves(cv, 640, 0, W, t, n=4, gap=70)
    bx = lerp(320, 1180, ease(u))
    with cv.at(bx, 720, 1.0, 2 * math.sin(t * 2)):
        boat(cv, 0, 0, 1.25)
        J = fig(cv, -40, -26, h=250, pose="point", face="angry", outfit=("helmet", "cape"), w=5)
        for k in range(3):
            mini(cv, 40 + k * 46, -30, h=120, phase=k, w=3.5, face="blank") if False else None
    for k, (dx, dy) in enumerate(((-300, 60), (-440, -20), (320, 80))):
        with cv.at(bx + dx, 790 + dy, 0.7, 2 * math.sin(t * 2 + k)):
            boat(cv, 0, 0, 1.0)
            for q in range(3):
                fig(cv, -60 + q * 56, -26, h=110, pose="stand", face="blank", w=3.5)
    tag(cv, t, LS(22) + 0.2, "207 BC", 400, 140, size=84, col=NAVY)
    tag(cv, t, AT(22, 0.3), "XIANG YU", 400, 270, size=64, col=RED, band=None)
    cap(cv, t, AT(22, 0.5), "dawn. enemy territory ahead.", 1200, 140, size=46, col=GREY)
    return cv


def pot(cv, x, y, s=1.0, broken=0.0):
    with cv.at(x, y, s):
        if broken < 0.05:
            cv.poly([(-60, -70), (60, -70), (80, -20), (60, 0), (-60, 0), (-80, -20)], closed=True, fill=(120, 120, 130), w=7, amp=0.8)
            cv.line((-70, -70), (70, -70), w=8)
            cv.line((-100, -50), (-80, -50), w=6); cv.line((80, -50), (100, -50), w=6)
        else:
            for k, (dx, dy, rot) in enumerate(((-70, -30, -40), (0, -60, 20), (70, -20, 60), (-30, 10, 10))):
                with cv.at(dx * (1 + broken * 1.4), dy - 30 * math.sin(broken * 3) + broken * 40, 1, rot * broken):
                    cv.poly([(-30, -20), (30, -30), (10, 20)], closed=True, fill=(120, 120, 130), w=6, amp=0.5)
            if broken < 0.6:
                burst_lines(cv, 0, -40, 60, 110, n=8, col=GOLD, w=5)


def sc_pots(t):                                   # 23: smash the cooking pots, sink the boats
    cv = base(t, SG(t, 23))
    ground(cv, 900, 60, 960)
    waves(cv, 700, 1020, W, t, n=3, gap=70)
    cap(cv, t, LS(23) + 0.3, "ORDER #1", 480, 150, size=50, col=GREY)
    for k, x in enumerate((220, 480, 740)):
        b = clamp01((t - AT(23, 0.42 + 0.06 * k)) / 0.7)
        pot(cv, x, 880, 1.15, broken=b if b > 0 else 0.0)
    stamp(cv, 480, 280, "SMASH THE POTS", col=RED, size=58, rot=-4, s=pp(t, AT(23, 0.35), 0.35)) if t > AT(23, 0.35) else None
    for k, x in enumerate((1230, 1480, 1730)):
        sink = clamp01((t - AT(23, 0.76 + 0.05 * k)) / 1.2)
        with cv.at(0, 0):
            boat(cv, x, 640, 0.9, rot=-18 * sink, sink=sink * 0.9)
        if 0 < sink < 1:
            for q in range(3):
                cv.ellipse(x + 20 * q - 20, 600 - sink * 80 - q * 30, 8 + q * 3, w=4, col=BLUE, amp=0.5)
    if t > AT(23, 0.7):
        stamp(cv, 1480, 280, "SINK THE BOATS", col=NAVY, size=58, rot=3, s=pp(t, AT(23, 0.7), 0.35))
    waves(cv, 690, 1020, W, t + 0.4, n=1, gap=1)
    return cv


def sc_days(t):                                   # 24: three days of food, no retreat, win fast or disappear
    cv = base(t, SG(t, 24))
    for k in range(3):
        x = 420 + k * 280
        r = pp(t, LS(24) + 0.1 + 0.2 * k, 0.4)
        gone = clamp01((t - AT(24, 0.28 + 0.1 * k)) / 0.4)
        if r > 0.02 and gone < 1:
            with cv.at(x, 450, r * (1 - gone), 0):
                cv.poly([(-70, -20), (70, -20), (50, 60), (-50, 60)], closed=True, fill=CREAM, w=7)
                cv.ellipse(0, -20, 70, 20, fill=PAPER, w=6)
                for q in range(5):
                    cv.ellipse(-36 + q * 18, -26, 6, 4, fill=LGOLD, w=2, col=GOLD, amp=0)
            cap(cv, t, LS(24) + 0.3, f"day {k + 1}", x, 570, size=44, col=NAVY)
    if t > AT(24, 0.28):
        cap(cv, t, AT(24, 0.28), "...food runs out", 700, 700, size=48, col=RED)
    if t > AT(24, 0.45):                                                            # no retreat: one-way sign
        r = pp(t, AT(24, 0.45), 0.4)
        with cv.at(1560, 450, r):
            cv.ellipse(0, 0, 120, 120, fill=RED, w=8)
            cv.rect(-80, -18, 80, 18, fill=PAPER, w=4)
        cv.arrow((1700, 640), (1450, 640), w=8, col=GREY, amp=1.0, head=30)
        xmark(cv, 1575, 640, 1.6, reveal=appear(t, AT(24, 0.52), 0.4))
        tag(cv, t, AT(24, 0.5), "NO RETREAT", 1560, 780, size=64, col=RED)
    if t > AT(24, 0.72):
        k = clamp01((t - AT(24, 0.72)) / 1.4)
        fig(cv, 960, 960, h=280 * (1 - 0.2 * k), pose="fear", face="scared", w=5)
        for q in range(int(14 * k)):
            a = q * 2.4
            cv.ellipse(960 + math.cos(a) * 60 * k * (1 + q * 0.08), 820 - q * 12 * k, 4, w=3, col=GREY, amp=0)
        tag(cv, t, AT(24, 0.74), "WIN FAST... or DISAPPEAR", 960, 160, size=64, col=NAVY)
    return cv


def sc_battle(t):                                 # 25: the cornered army fights like it has nothing to lose
    u = SG(t, 25)
    cv = base(t, u, shake=3 if 0.15 < u < 0.75 else 0)
    ground(cv, 900, 60, 1860)
    adv = ease(clamp01(u / 0.45))
    for k in range(9):                                                             # our army charges
        mini(cv, lerp(100, 700, adv) + (k % 3) * 125 + (k // 3) * 40, 880 + (k // 3) * 22, h=210, phase=k * 0.7 + t * 9, col=NAVY,
             swing=0.5 + 0.5 * math.sin(t * 10 + k), w=5, seed=k)
    for k in range(12):                                                            # a much bigger enemy force
        fall = clamp01((u - 0.35 - 0.04 * k) / 0.2)
        if fall < 1:
            ex = 1100 + (k % 4) * 120 + (k // 4) * 40
            ey = 880 + (k // 4) * 22
            mini(cv, ex + fall * 100, ey, h=210 * (1 - fall * 0.2), phase=k, col=RED, flip=True, w=5, seed=k + 30)
    if u > 0.2:
        cap(cv, t, AT(25, 0.2), "nothing to lose", 460, 440, size=54, col=NAVY, rot=-3)
    if u > 0.8:
        k = pp(t, AT(25, 0.8), 0.4)
        burst_lines(cv, 960, 360, 190, 290, n=16, col=GOLD, w=8, a0=t * 0.3)
        with cv.at(960, 360, k):
            cv.text("AND THEY WON.", 0, 0, size=110, font="marker", col=NAVY)
    return cv


def sc_cortes(t):                                 # 26: Cortes scuttles his ships; commitment device; a different gear
    u = SG(t, 26)
    cv = base(t, u)
    cv.line((0, 700), (W, 700), w=5, col=GREY, amp=1.5)
    cv.poly([(0, 900), (300, 760), (700, 760), (1000, 900)], closed=True, fill=(244, 232, 196), w=5, amp=1.2)             # beach
    waves(cv, 760, 700, W, t, n=3, gap=60)
    fig(cv, 300, 800, h=300, pose="hips", face="smirk", outfit=("hat", "cape"), w=6)
    for k, x in enumerate((1100, 1380, 1660)):
        sink = clamp01((t - AT(26, 0.05 + 0.04 * k)) / 1.6)
        boat(cv, x, 760, 1.0, rot=-24 * sink, sink=sink * 0.85)
    tag(cv, t, LS(26) + 0.1, "1519 · CORTES SCUTTLES HIS SHIPS", 1000, 150, size=54, col=NAVY)
    if t > AT(26, 0.38):
        tag(cv, t, AT(26, 0.38), "COMMITMENT DEVICE", 960, 330, size=96, col=RED)
        cap(cv, t, AT(26, 0.46), "quitting becomes impossible", 960, 430, size=48, col=GREY)
    if t > AT(26, 0.68):                                                            # a different gear: gauge needle jumps
        r = pp(t, AT(26, 0.68), 0.4)
        with cv.at(1500, 700, r):
            pts = [(120 * math.cos(math.pi + a), 120 * math.sin(math.pi + a)) for a in np.linspace(0, math.pi, 20)]
            cv.poly(pts, w=8, col=GREY, amp=0.6)
            ang = math.pi + lerp(0.15, 2.9, ease(clamp01((t - AT(26, 0.74)) / 0.35)))
            cv.line((0, 0), (100 * math.cos(ang), 100 * math.sin(ang)), w=8, col=RED)
            cv.ellipse(0, 0, 12, 12, fill=INK, w=2)
            cv.text("TURBO", 0, 50, size=40, font="marker", col=RED)
        cap(cv, t, AT(26, 0.78), "a different gear", 1500, 560, size=44, col=NAVY)
    return cv


TORCH_LABELS = ["STARTUP", "FREELANCE", "CODING", "GYM", "CRYPTO"]


def torch_pos(k, t):
    ph = (t * 0.9 + k / 5) % 1.0
    x = 960 + (k - 2) * 190 + 130 * math.sin(ph * 2 * math.pi)
    y = 560 - 330 * math.sin(ph * math.pi) ** 1.0
    return x, y


def sc_juggle(t):                                 # 27: five backup plans, five half-finished projects
    cv = base(t, SG(t, 27))
    ground(cv, 900, 80, 1840)
    fig(cv, 960, 900, h=400, pose="juggle", face="worry", w=8)
    for k in range(5):
        r = appear(t, LS(27) + 0.15 + 0.15 * k, 0.4)
        if r <= 0:
            continue
        x, y = torch_pos(k, t)
        with cv.at(x, y, 1.0, 20 * math.sin(t * 4 + k)):
            cv.line((0, 40), (0, -10), w=9, col=BROWN)
            flame(cv, 0, -10, 0.7, t, seed=k)
        cv.text(TORCH_LABELS[k], x, y - 118, size=30, font="marker", col=NAVY, reveal=r)
    cap(cv, t, AT(27, 0.45), "5 backup plans · 5 half-finished projects", 960, 130, size=52, col=RED)
    return cv


def sc_fire(t):                                   # 28: that's not ambition, that's a fire hazard
    cv = base(t, SG(t, 28))
    ground(cv, 900, 80, 1840)
    drop = clamp01((t - AT(28, 0.2)) / 0.5)
    fig(cv, 760, 900, h=400, pose="fear" if drop > 0 else "juggle", face="scared" if drop > 0 else "worry", w=8, outfit=("wild",) if drop > 0.9 else ())
    for k in range(5):
        x = 760 - 320 + k * 160
        yy = lerp(420 + 30 * math.sin(k), 880, ease(drop))
        if drop < 1:
            with cv.at(x, yy, 1.0, 40 * drop):
                cv.line((0, 40), (0, -10), w=9, col=BROWN); flame(cv, 0, -10, 0.7, t, seed=k)
        else:
            flame(cv, x, 890, 1.0 + 0.2 * (k % 2), t, seed=k + 3)
    if t > AT(28, 0.5):
        r = pp(t, AT(28, 0.5), 0.4)
        with cv.at(1480, 560, r):
            cv.poly([(0, -210), (190, 100), (-190, 100)], closed=True, fill=GOLD, w=10, amp=1.0)
            flame(cv, 0, 60, 1.2, t)
            cv.text("!", 0, -50, size=130, font="marker")
        tag(cv, t, AT(28, 0.62), "FIRE HAZARD", 1480, 760, size=80, col=RED)
    cap(cv, t, LS(28) + 0.2, "not ambition...", 640, 200, size=60, col=NAVY)
    return cv


def sc_boats(t):                                  # 29: every backup plan is a boat = a permission slip to quit
    cv = base(t, SG(t, 29))
    ground(cv, 780, 80, 1840, col=GREY)
    waves(cv, 840, 0, W, t, n=3, gap=50)
    for k in range(5):
        x = 330 + k * 300
        r = pp(t, AT(29, 0.12 + 0.07 * k), 0.4)
        if r > 0.02:
            with cv.at(x, 790, r, 3 * math.sin(t * 2 + k)):
                boat(cv, 0, 0, 0.9)
                cv.text("PLAN B", 0, -6, size=40, font="marker", col=PAPER)
    fig(cv, 900, 770, h=300, pose="hold", face="smirk")
    if t > AT(29, 0.55):
        r = pp(t, AT(29, 0.55), 0.4)
        with cv.at(1400, 360, r, 4):
            cv.rect(-210, -120, 210, 120, r=10, fill=CREAM, w=7)
            cv.text("PERMISSION SLIP", 0, -66, size=44, font="marker", col=NAVY)
            cv.text("☐ I QUIT" if False else "[ ]  I QUIT", 0, 4, size=54, font="hand", col=INK)
            cv.line((-150, 80), (150, 80), w=4, col=GREY)
            if t > AT(29, 0.85):
                check(cv, -140, 4, 1.0)
    cap(cv, t, LS(29) + 0.2, "every backup plan is a boat", 960, 150, size=62, col=NAVY)
    return cv


def sc_planb(t):                                  # 30: your Plan B is the reason your Plan A fails
    u = SG(t, 30)
    cut = AT(30, 0.78)
    cv = base(t, u)
    ground(cv, 940, 80, 1840)
    if t < cut:
        shake = 5 * math.sin(t * 30)
        rocket(cv, 760 + shake, 830, 1.5, flame_t=t, rot=shake * 0.3)
        anchor(cv, 1260, 880, 1.8)
        cv.poly([(760, 860), (900, 900), (1050, 870), (1180, 880), (1250, 860)], w=8, col=BROWN, amp=1.5)
        cv.text("PLAN A", 760, 1035, size=54, font="marker", col=NAVY)
        cv.text("PLAN B", 1260, 1035, size=54, font="marker", col=RED)
    else:
        k = t - cut
        rocket(cv, 760, 830 - 700 * ease(clamp01(k / 1.2)) - 800 * clamp01(k - 1.2), 1.5, flame_t=t)
        anchor(cv, 1260, 880, 1.8)
        sc_ = clamp01(k / 0.3)
        with cv.at(1000, 880, 1.0, 20 * sc_):
            cv.line((-30, -30), (30, 30), w=8); cv.line((-30, 30), (30, -30), w=8)
    tag(cv, t, LS(30) + 0.15, "YOUR PLAN B IS THE REASON\nYOUR PLAN A FAILS", 960, 190, size=66, col=NAVY)
    if t > AT(30, 0.65) and t < cut + 0.2:
        with cv.at(1000 + 60 * math.sin(t * 6), 860, 1.0):
            cv.poly([(-30, -24), (14, 10), (30, 40)], w=8); cv.poly([(30, -24), (-14, 10), (-30, 40)], w=8)
            cv.ellipse(-34, 52, 14, 14, w=6); cv.ellipse(34, 52, 14, 14, w=6)
    return cv


def sc_bad(t):                                    # 31: you're about to be bad at it, on purpose
    cv = base(t, SG(t, 31))
    cv.poly([(80, 940), (700, 760), (1240, 760), (1840, 940)], w=6, col=GREY, amp=1.2)
    cv.line((960, 760), (960, 940), w=6, col=GOLD, amp=1.0)
    for k, x in enumerate((420, 760, 1160, 1500)):
        with cv.at(x, 840 + (k % 2) * 40, appear(t, LS(31) + 0.1 * k, 0.4)):
            cv.poly([(-26, 0), (0, -64), (26, 0)], closed=True, fill=ORANGE, w=5, amp=0.5)
    J = fig(cv, 800, 900, h=380, pose="hold", face="worry", outfit=("glasses",))
    hx, hy = J["hA"]
    cv.line((hx, hy + 20), (hx + 10, hy - 150), w=7)
    with cv.at(hx + 150, hy - 190, pp(t, AT(31, 0.3)), -4):
        cv.rect(-165, -50, 165, 50, r=8, fill=GOLD, w=7)
        cv.text("BEGINNER", 0, 2, size=56, font="marker", col=INK)
    tag(cv, t, AT(31, 0.55), "BAD AT IT.  ON PURPOSE.", 960, 160, size=84, col=NAVY)
    return cv


# ======================================================================= ACT IV (lines 32-37)
FOG = dict(cols=8, rows=4, tw=200, th=150, x0=160, y0=250)
PATH = [(0, 3), (1, 3), (2, 2), (3, 2), (4, 1), (5, 1), (6, 0), (7, 0)]


def tile_icon(cv, k, x, y):
    if k == 0:
        tree(cv, x, y + 36, 0.55)
    elif k == 1:
        cv.poly([(x - 34, y + 30), (x - 16, y - 8), (x + 10, y - 20), (x + 36, y + 30)], closed=True, fill=LGREY, w=4, amp=0.5)
    elif k == 2:
        cv.rect(x - 30, y - 6, x + 30, y + 30, r=5, fill=BROWN, w=4); cv.rect(x - 30, y - 22, x + 30, y - 6, r=8, fill=GOLD, w=4)
    else:
        cv.line((x, y + 34), (x, y - 26), w=5); cv.poly([(x, y - 26), (x + 40, y - 12), (x, y + 2)], closed=True, fill=RED, w=4, amp=0.4)


def fog_grid(cv, t, clear):
    F = FOG
    for r in range(F["rows"]):
        for c in range(F["cols"]):
            x, y = F["x0"] + c * F["tw"], F["y0"] + r * F["th"]
            tc = clear.get((c, r))
            a = 1.0 if tc is None else 1 - ease((t - tc) / 0.6)
            cx, cy = x + F["tw"] / 2, y + F["th"] / 2
            if a < 0.99:
                cv.rect(x + 3, y + 3, x + F["tw"] - 3, y + F["th"] - 3, r=10, w=2, col=LGREY, amp=0.4)
                with cv.fading(1 - a):
                    tile_icon(cv, (c * 3 + r) % 4, cx, cy)
            if a > 0.01:
                col = tuple(int(255 - (255 - v) * a) for v in (198, 202, 210))
                cv.rect(x + 3, y + 3, x + F["tw"] - 3, y + F["th"] - 3, r=10, fill=col, w=0.01, col=col, amp=0)
                with cv.fading(a):
                    cv.text("?", cx, cy, size=64, font="marker", col=(150, 154, 164))


def tile_xy(c, r):
    return FOG["x0"] + c * FOG["tw"] + FOG["tw"] / 2, FOG["y0"] + r * FOG["th"] + FOG["th"] - 14


def clear_around(clear, tile, t0):
    c0, r0 = tile
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            k = (c0 + dc, r0 + dr)
            if 0 <= k[0] < FOG["cols"] and 0 <= k[1] < FOG["rows"] and k not in clear:
                clear[k] = t0


def sc_fog(t):                                    # 32: Brian Armstrong's rule: action produces information
    cv = base(t, SG(t, 32))
    clear = {}
    steps = [AT(32, 0.55), AT(32, 0.7), AT(32, 0.85)]
    clear_around(clear, PATH[0], -5)
    for k, ts in enumerate(steps):
        clear_around(clear, PATH[k + 1], ts)
    fog_grid(cv, t, clear)
    pos = 0
    for ts in steps:
        if t > ts:
            pos += 1
    frac = clamp01((t - (steps[pos - 1] if pos else -9)) / 0.5) if pos else 1
    a, b = tile_xy(*PATH[max(pos - 1, 0)]), tile_xy(*PATH[pos])
    x, y = (lerp(a[0], b[0], ease(frac)), lerp(a[1], b[1], ease(frac))) if pos else tile_xy(*PATH[0])
    fig(cv, x, y, h=150, pose=walk_pose(t * 8, 0.8) if frac < 1 else "stand", face="smile", w=4)
    cap(cv, t, LS(32) + 0.1, "BRIAN ARMSTRONG'S FAVORITE RULE:", 960, 90, size=40, col=GREY)
    for k, wd in enumerate(("ACTION", "PRODUCES", "INFORMATION.")):
        tag(cv, t, AT(32, 0.28 + 0.12 * k), wd, 420 + k * 540 if k < 2 else 1480, 190, size=68, col=NAVY)
    return cv


def sc_think(t):                                  # 33: thinking produces nothing
    cv = base(t, SG(t, 33))
    ground(cv, 900, 80, 1840)
    desk(cv, 700, 700, 520, legh=200)
    chair_side(cv, 300, 817)
    fig(cv, 285, 900, h=360, pose="think" if t > AT(33, 0.1) else "sit", face="worry")
    thought(cv, 560, 250, "the PERFECT plan...", size=44, tail_to=(300, 560), reveal=appear(t, LS(33) + 0.2, 0.5))
    r = appear(t, AT(33, 0.2), 0.6)
    if r > 0:
        with cv.at(1480, 560, 1.0):                                                     # output tray: empty
            cv.rect(-190, 0, 190, 110, r=10, w=7, reveal=r)
            cv.text("OUTPUT", 0, 52, size=50, font="marker", col=NAVY, reveal=r)
            cv.text("0", 0, -90, size=140, font="marker", col=RED, reveal=r)
        cap(cv, t, AT(33, 0.3), "that produces nothing.", 1480, 340, size=48, col=RED)
    if t > AT(33, 0.62):                                                                # lamp lights up a guess
        r = appear(t, AT(33, 0.62), 0.5)
        with cv.at(1100, 330, 1.0):
            cv.line((0, 0), (0, -120), w=8); cv.curve((0, -120), (-40, -170), (-90, -130), w=8)
            cv.poly([(-130, -130), (-50, -130), (-30, -90), (-150, -90)], closed=True, fill=GOLD, w=6, amp=0.5)
            cv.poly([(-150, -90), (-30, -90), (30, 100), (-210, 100)], closed=True, fill=(255, 244, 190), w=0.01, col=(255, 244, 190), amp=0)
            cv.text("?", -90, 40, size=90, font="marker", col=NAVY)
        tag(cv, t, AT(33, 0.68), "thinking = guessing\n(with better lighting)", 1340, 830, size=44, col=NAVY)
    return cv


def sc_ugly(t):                                   # 34: build the ugly app, film the bad video, write the messy draft
    cv = base(t, SG(t, 34))
    items = [(0.05, 400, "UGLY APP"), (0.38, 960, "BAD VIDEO"), (0.70, 1520, "MESSY DRAFT")]
    for k, (fr, x, name) in enumerate(items):
        r = pp(t, AT(34, fr), 0.45)
        if r > 0.02:
            with cv.at(x, 520, r):
                if k == 0:
                    cv.rect(-110, -200, 110, 200, r=22, fill=SKY, w=8)
                    for q, (dx, dy, c_) in enumerate(((-40, -120, RED), (30, -60, GREEN), (-20, 10, GOLD), (50, 90, PURPLE))):
                        cv.ellipse(dx, dy, 30 - q * 3, 24, fill=c_, w=3, amp=1.5, seed=q)
                    cv.rect(-60, 130, 40, 160, r=4, fill=PAPER, w=4, amp=2.0)
                elif k == 1:
                    cv.rect(-150, -110, 150, 110, r=10, fill=LGREY, w=8)
                    jit = 4 * math.sin(t * 25)
                    cv.rect(-130 + jit, -90, 100 + jit, 60, w=4, col=GREY)
                    cv.ellipse(100, 70, 44, 54, fill=(255, 220, 190), w=4, amp=1)
                    cv.text("REC", -90, -70, size=28, font="marker", col=RED)
                else:
                    paper(cv, 0, 0, w=240, h=330, rot=-3)
                    for q in range(6):
                        cv.zig((-90, -110 + q * 36), (80, -110 + q * 36 + (q % 2) * 18), n=7, jag=9, w=3, col=GREY, seed=q)
                    cv.line((-80, -40), (60, 20), w=5, col=RED); cv.line((60, -40), (-70, 40), w=5, col=RED)
        tag(cv, t, AT(34, fr + 0.06), name, x, 800, size=52, col=NAVY)
        if t > AT(34, fr + 0.17):
            stamp(cv, x + 90, 270, "SHIPPED", col=GREEN, size=38, rot=-10, s=lerp(2.2, 1.0, ease(clamp01((t - AT(34, fr + 0.17)) / 0.18))))
    return cv


CHAIR_SEG = [((-50, -60), (-50, 0)), ((50, -60), (50, 0)), ((-56, -60), (56, -60)), ((-50, -60), (-58, -170)), ((50, -60), (58, -170)),
             ((-58, -140), (58, -140)), ((-56, -110), (56, -110))]
CHAIR_VEL = [(-230, -120, 70), (260, -160, -50), (90, -300, 120), (-170, -260, -90), (230, -220, 60), (-60, -330, 40), (300, -60, -110)]


def chair_exploded(cv, x, y, k, s=1.0):
    for (a, b), (vx, vy, rot) in zip(CHAIR_SEG, CHAIR_VEL):
        g = 900 * k * k * 0.5
        with cv.at(x + vx * k * s, y + (vy * k + g * 0.2) * s, s, rot * k * 2):
            cv.line(((a[0] + b[0]) / 2 * 0 + a[0] - (a[0] + b[0]) / 2, a[1] - (a[1] + b[1]) / 2), (b[0] - (a[0] + b[0]) / 2, b[1] - (a[1] + b[1]) / 2), w=8)


def sc_chair1(t):                                 # 35: first version collapses; that crash is information
    cv = base(t, SG(t, 35))
    ground(cv, 900, 80, 1840)
    boom = AT(35, 0.38)
    if t < boom:
        k = appear(t, LS(35) + 0.1, 0.8)
        chair(cv, 1050, 900 - 0 + 6 * math.sin(t * 20), 1.5, wobble=3 * math.sin(t * 14) * k)
    else:
        kk = clamp01((t - boom) / 1.1)
        chair_exploded(cv, 1050, 800, kk, 1.5)
        burst_lines(cv, 1050, 760, 80, 80 + 260 * clamp01((t - boom) / 0.3), n=14, col=ORANGE, w=7) if t - boom < 0.35 else None
        if kk < 1:
            cap(cv, t, boom, "CRASH!", 1050, 380, size=110, col=RED, font="marker", rot=-6)
    pz = "hold" if t < boom else ("fear" if t < AT(35, 0.55) else "think")
    fig(cv, 560, 900, h=380, pose=pz, face="worry" if t < boom else ("scared" if t < AT(35, 0.55) else "smirk"), outfit=("hardhat",))
    if t < boom:
        cap(cv, t, LS(35) + 0.2, "no instructions...", 560, 250, size=48, col=GREY)
    if t > AT(35, 0.58):
        tag(cv, t, AT(35, 0.58), "CRASH = DATA", 1400, 230, size=84, col=GREEN)
    if t > AT(35, 0.78):
        cap(cv, t, AT(35, 0.78), "no course could teach this", 1400, 330, size=50, col=NAVY)
        with cv.at(1400, 430, 1.0):
            cv.text("COURSE $499", 0, 0, size=50, font="marker", col=GREY)
            cv.line((-170, 0), (170, 0), w=8, col=RED, reveal=appear(t, AT(35, 0.84), 0.3), amp=1)
    return cv


def sc_tuition(t):                                # 36: failure is the tuition
    cv = base(t, SG(t, 36))
    ground(cv, 900, 80, 1840)
    r = appear(t, LS(36), 0.8)
    with cv.at(1330, 900, 1.0):                                                       # university building
        cv.poly([(-300, -420), (0, -560), (300, -420)], closed=True, fill=CREAM, w=8, reveal=r)
        cv.rect(-300, -420, 300, -380, w=7, fill=PAPER, reveal=r)
        for k in range(5):
            cv.rect(-250 + k * 125 - 22, -380, -250 + k * 125 + 22, 0, w=6, fill=PAPER, reveal=r)
        cv.rect(-300, -20, 300, 0, w=7, fill=PAPER, reveal=r)
        cv.text("UNIVERSITY OF HARD KNOCKS", 0, -470, size=34, font="marker", col=NAVY, reveal=r)
    fig(cv, 640, 900, h=360, pose="hold", face="sad" if t < AT(36, 0.55) else "smile")
    tag(cv, t, LS(36) + 0.2, "FAILURE  =  TUITION", 700, 170, size=76, col=NAVY)
    if t > AT(36, 0.3):
        with cv.at(960, 600, pp(t, AT(36, 0.3), 0.4), -4):
            cv.rect(-120, -80, 120, 80, r=8, fill=CREAM, w=6)
            cv.text("TUITION\nDUE", 0, -10, size=44, font="marker", col=RED)
        with cv.at(430, 700, 1.0):                                                    # jar of failures
            cv.poly([(-50, 0), (-60, -130), (60, -130), (50, 0)], closed=True, fill=SKY, w=6)
            cv.text("FAILURES", 0, -64, size=26, font="marker")
            for q in range(6):
                if t > AT(36, 0.4 + 0.05 * q):
                    cv.ellipse(-30 + (q % 3) * 30, -20 - (q // 3) * 22, 13, 13, fill=GOLD, w=3, amp=0.3)
    if t > AT(36, 0.72):
        with cv.at(960, 840, pp(t, AT(36, 0.72), 0.4), 3):
            cv.rect(-150, -42, 150, 42, r=8, fill=PAPER, w=6)
            cv.text("DEGREE IN EXPERIENCE", 0, 0, size=26, font="marker", col=NAVY)
    return cv


def sc_map2(t):                                   # 37 (first half): you get the map by walking
    cv = base(t, SG(t, 37))
    clear = {}
    clear_around(clear, PATH[0], -5)
    t_walk = AT(37, 0.0)
    for k in range(1, len(PATH)):
        clear_around(clear, PATH[k], t_walk + 0.35 * k)
    fog_grid(cv, t, clear)
    k = (t - t_walk) / 0.35
    i = min(int(max(k, 0)), len(PATH) - 1)
    a, b = tile_xy(*PATH[i]), tile_xy(*PATH[min(i + 1, len(PATH) - 1)])
    u = ease(k - int(max(k, 0))) if k < len(PATH) - 1 else 1
    fig(cv, lerp(a[0], b[0], u), lerp(a[1], b[1], u), h=150, pose=walk_pose(t * 9, 0.8) if k < len(PATH) - 1 else "cheer", face="smile", w=4)
    cap(cv, t, LS(37) + 0.1, "you don't get the map by staring at the fog...", 960, 120, size=54, col=GREY)
    tag(cv, t, AT(37, 0.32), "you get it by WALKING.", 960, 190, size=70, col=NAVY)
    return cv


def sc_chairs(t):                                 # 37 (second half): chair two wobbles, chair three sells
    cv = base(t, 0.0)
    ground(cv, 900, 80, 1840)
    t0 = AT(37, 0.55)
    for k, (fr, x, name) in enumerate(((0.0, 340, "#1"), (0.1, 760, "#2"), (0.22, 1180, "#3"))):
        r = pp(t, lerp(t0, EN(37), fr), 0.4)
        if r > 0.02:
            if k == 0:
                for q, (dx, ang) in enumerate(((-90, 12), (-30, -40), (30, 80), (90, 20), (0, 0))):
                    with cv.at(x + dx, 880, r, ang):
                        cv.line((-50, 0), (50, 0), w=8)
            elif k == 1:
                chair(cv, x, 900, 1.5 * r, wobble=6 * math.sin(t * 6))
            else:
                chair(cv, x, 900, 1.5 * r)
                sparkles(cv, x, 700, t, n=5, r=110)
            cap(cv, t, lerp(t0, EN(37), fr) + 0.1, name, x, 960, size=50, col=NAVY)
    fig(cv, 1430, 900, h=330, pose="hips", face="smirk", outfit=("hardhat",))
    if t > lerp(t0, EN(37), 0.45):
        fig(cv, 1720, 900, h=300, pose="shrug", face="shock", flip=True)
        bubble(cv, 1480, 330, "Where did you\nbuy this?!", size=42, tail=(1700, 620), reveal=appear(t, lerp(t0, EN(37), 0.45), 0.4))
    return cv


# ======================================================================= OUTRO (lines 38-43)
def sc_belief1(t):                                # 38: belief doesn't download at 100%
    cv = base(t, SG(t, 38))
    ground(cv, 900, 80, 1840)
    sun(cv, 560, 800, 190, t=t, reveal=appear(t, LS(38), 0.8))
    cv.rect(0, 900, W, H, w=0.01, fill=PAPER, col=PAPER, amp=0)
    fig(cv, 560, 900, h=400, pose="hips", face="cool", outfit=("suit",))
    r = pp(t, LS(38) + 0.3, 0.4)
    with cv.at(1380, 470, r):
        cv.rect(-330, -170, 330, 170, r=16, fill=PAPER, w=7)
        cv.rect(-330, -170, 330, -110, r=16, fill=NAVY, w=7)
        cv.text("SELF-BELIEF.exe", -20, -140, size=36, font="marker", col=PAPER)
        cv.rect(-280, 10, 280, 70, r=18, w=6)
        fr = 0.64 * appear(t, AT(38, 0.3), AT(38, 0.55) - AT(38, 0.3))
        if t > AT(38, 0.55):
            fr = 0.64
        if fr > 0.01:
            cv.rect(-274, 16, -274 + 548 * fr, 64, r=14, fill=GOLD, w=0.01, col=GOLD, amp=0)
        cv.text(f"downloading... {int(fr * 100)}%" if t < AT(38, 0.62) else "ERROR: can't download belief", 0, -62, size=34,
                font="hand", col=INK if t < AT(38, 0.62) else RED)
        if t > AT(38, 0.62):
            xmark(cv, 0, 120, 1.2, reveal=appear(t, AT(38, 0.62), 0.3))
    tag(cv, t, AT(38, 0.7), "not at 100%.", 1380, 790, size=64, col=RED)
    return cv


def sc_belief2(t):                                # 39: it's a meter you fill, one awkward action at a time
    u = SG(t, 39)
    cv = base(t, u)
    ground(cv, 900, 80, 1840)
    tag(cv, t, LS(39) + 0.05, "BELIEF METER", 960, 130, size=70, col=NAVY)
    cv.rect(260, 190, 1660, 270, r=30, w=8, reveal=appear(t, LS(39), 0.5))
    reps = [AT(39, 0.40), AT(39, 0.58), AT(39, 0.76)]
    n_ = sum(1 for r_ in reps if t > r_)
    fillv = 0.0
    for r_ in reps:
        fillv += 0.01 * ease(clamp01((t - r_) / 0.3))
    if fillv > 0.002:
        cv.rect(270, 200, 270 + max(1380 * fillv, 26), 260, r=22, fill=GOLD, w=0.01, col=GOLD, amp=0)
    for q, lbl in enumerate(("0%", "25%", "50%", "75%", "100%")):
        cv.line((270 + 1380 * q / 4, 276), (270 + 1380 * q / 4, 292), w=4, col=GREY, amp=0)
        cv.text(lbl, 270 + 1380 * q / 4, 318, size=30, font="hand", col=GREY)
    cap(cv, t, LS(39) + 0.4, f"{int(fillv * 100 + 0.5)}%", 960, 380, size=64, col=NAVY, font="marker")
    poses = ["stand", S.POSE["point_up"], "fear", "stand"]
    k = min(n_, 3)
    pz = ["stand", "cheer", "fear", "shrug"][k]
    fig(cv, 960, 900, h=420, pose=pz, face=["smile", "smile", "scared", "smirk"][k])
    for i, r_ in enumerate(reps):
        if r_ - 0.2 < t < r_ + 1.0:
            up = clamp01((t - r_) / 1.0)
            cv.text("+1%", 760 + i * 200, 620 - 120 * up, size=64, font="marker", col=GREEN, reveal=1.0) if t > r_ else None
    for i, (fr, txt) in enumerate(((0.4, "um... hi?"), (0.58, "*trips*"), (0.76, "*bad speech*"))):
        if AT(39, fr) - 0.1 < t < AT(39, fr) + 1.4:
            bubble(cv, 1350, 480, txt, size=44, tail=(1040, 560), reveal=appear(t, AT(39, fr) - 0.1, 0.3))
    return cv


def sc_burn(t):                                   # 40: stop waiting for permission, burn your boats, collect failures
    cv = base(t, SG(t, 40))
    ground(cv, 900, 80, 1840)
    waves(cv, 840, 0, 800, t, n=2, gap=50)
    boat(cv, 380, 800, 1.3, rot=2 * math.sin(t * 2))
    if t > AT(40, 0.5):
        for k, dx in enumerate((-70, 0, 70)):
            flame(cv, 380 + dx, 740, 1.3, t, seed=k)
    fig(cv, 960, 900, h=400, pose="hips" if t < AT(40, 0.25) else "point", face="smirk", outfit=("crown",) if t > AT(40, 0.3) else ())
    k = clamp01((t - AT(40, 0.0)) / 0.5)
    if t < AT(40, 0.22):                                                                # the permission slip rips in two
        with cv.at(1250, 480, 1.0):
            paper(cv, 0, 0, w=190, h=140, text="PERMISSION\nSLIP", size=28)
    else:
        rp = clamp01((t - AT(40, 0.22)) / 0.7)
        for sgn in (-1, 1):
            with cv.at(1250 + sgn * (20 + 150 * rp), 480 + 220 * rp * rp, 1.0, sgn * 35 * rp):
                cv.poly([(-95 * (1 if sgn < 0 else 0), -70), (95 * (0 if sgn < 0 else 1), -70), (95 * (0 if sgn < 0 else 1), 70), (-95 * (1 if sgn < 0 else 0), 70)],
                        closed=True, fill=PAPER, w=5, amp=1.2)
    cap(cv, t, AT(40, 0.0) + 0.2, "stop waiting for permission.", 1180, 200, size=54, col=NAVY)
    if t > AT(40, 0.45):
        tag(cv, t, AT(40, 0.45), "BURN YOUR BOATS", 540, 270, size=70, col=RED)
    if t > AT(40, 0.7):
        tag(cv, t, AT(40, 0.7), "collect quality failures:", 1380, 700, size=46, col=NAVY)
        for q in range(3):
            if t > AT(40, 0.76 + 0.07 * q):
                with cv.at(1230 + q * 150, 830, pp(t, AT(40, 0.76 + 0.07 * q), 0.35)):
                    cv.ellipse(0, 0, 52, 52, fill=LGOLD, w=6)
                    cv.text(f"#{q + 1}", 0, 4, size=44, font="marker", col=NAVY)
                    cv.poly([(-26, 40), (-36, 100), (0, 76), (36, 100), (26, 40)], closed=True, fill=RED, w=4, amp=0.4)
    return cv


def sc_crown(t):                                  # 41: the potato callback; fraud -> founder in three years
    cv = base(t, SG(t, 41))
    ground(cv, 900, 80, 1840)
    drop = clamp01((t - AT(41, 0.7)) / 0.45)
    potato(cv, 1000, 900, 2.0, face="big" if drop >= 1 else "smile", arms="down", wobble=2 * math.sin(t * 3), t=t)
    if drop > 0:
        crown(cv, 1000, lerp(-100, 440, ease_out_back(drop, 2.0)), 1.6, rot=(1 - drop) * 25)
    if drop >= 1:
        sparkles(cv, 1000, 520, t, n=7, r=200)
    tag(cv, t, LS(41) + 0.1, "FRAUD", 440, 230, size=100, col=GREY, band=None)
    cv.line((250, 230), (630, 230), w=12, col=RED, reveal=appear(t, AT(41, 0.3), 0.3), amp=1.5)
    tag(cv, t, AT(41, 0.4), "FOUNDER", 440, 360, size=120, col=NAVY)
    if t > AT(41, 0.55):
        for q in range(3):
            tin = AT(41, 0.55 + 0.12 * q)
            if t > tin:
                with cv.at(330 + q * 190, 600, pp(t, tin, 0.35)):
                    cv.rect(-80, -90, 80, 100, r=10, fill=PAPER, w=6)
                    cv.rect(-80, -90, 80, -40, r=10, fill=RED, w=6)
                    cv.text(f"YEAR\n{q + 1}", 0, 20, size=46, font="marker", col=NAVY)
        cap(cv, t, AT(41, 0.62), "about three years of showing up", 560, 790, size=46, col=GREY)
    return cv


def sc_comment(t):                                # 42: what's YOUR Type 1 crazy belief?
    cv = base(t, SG(t, 42))
    fig(cv, 300, 900, h=420, pose="point", face="smile", outfit=("crown",))
    tag(cv, t, LS(42) + 0.1, "WHAT'S YOUR  TYPE 1  CRAZY BELIEF?", 1000, 150, size=76, col=NAVY)
    r = pp(t, LS(42) + 0.8, 0.45)
    with cv.at(1100, 520, r):
        cv.rect(-520, -140, 520, 140, r=26, fill=PAPER, w=8)
        cv.ellipse(-460, -70, 30, 30, fill=LGOLD, w=5)
        cv.text("Add a comment...", -400, -70, size=36, font="hand", col=GREY, anchor="lm")
        msg = "My Type 1 crazy belief is: I will ..."
        n_ = int(len(msg) * clamp01((t - AT(42, 0.35)) / (AT(42, 0.75) - AT(42, 0.35))))
        cv.text(msg[:n_] + ("|" if int(t * 3) % 2 == 0 else ""), -480, 30, size=44, font="hand", col=INK, anchor="lm")
        cv.rect(300, 80, 500, 128, r=14, fill=BLUE, w=4)
        cv.text("COMMENT", 400, 106, size=30, font="marker", col=PAPER)
    if t > AT(42, 0.8):
        cap(cv, t, AT(42, 0.8), "(yes, the pun was intentional)", 1100, 760, size=44, col=GREY)
    return cv


def sc_end(t):                                    # 43: subscribe + sign-off
    cv = base(t, SG(t, 43))
    fig(cv, 500, 900, h=420, pose="cheer" if int(t * 3) % 2 else S.POSE["point_up"], face="big", outfit=("crown",))
    tag(cv, t, LS(43) + 0.2, "SEE YOU THERE!", 1200, 220, size=96, col=NAVY)
    r = pp(t, AT(43, 0.15), 0.45)
    clicked = t > AT(43, 0.6)
    with cv.at(1200, 520, r):
        cv.rect(-230, -60, 230, 60, r=60, fill=GREY if clicked else RED, w=7)
        cv.text("SUBSCRIBED" if clicked else "SUBSCRIBE", 0, 4, size=56, font="marker", col=PAPER)
    if clicked:
        with cv.at(1430, 540, 1.0, 14 * math.sin(t * 22)):                              # bell ringing
            cv.poly([(-34, 30), (-28, -20), (0, -46), (28, -20), (34, 30)], closed=True, fill=GOLD, w=6, amp=0.4)
            cv.line((-40, 30), (40, 30), w=7); cv.ellipse(0, 44, 9, 9, fill=GOLD, w=3)
    cx, cy = lerp(1500, 1330, ease(clamp01((t - AT(43, 0.3)) / 0.3))), lerp(720, 560, ease(clamp01((t - AT(43, 0.3)) / 0.3)))
    if AT(43, 0.3) - 0.2 < t:
        with cv.at(cx, cy, 1.0 - 0.15 * (1 if clicked and (t - AT(43, 0.6)) < 0.15 else 0)):
            cv.poly([(0, 0), (0, 54), (14, 42), (26, 66), (38, 60), (26, 38), (44, 36)], closed=True, fill=PAPER, w=5, amp=0.3)
    cap(cv, t, AT(43, 0.7), "deep time academy", 1200, 760, size=60, col=NAVY, font="marker")
    if t > TOTAL - 1.4:
        cv.fade = 1.0
        a = clamp01((t - (TOTAL - 1.4)) / 1.2)
        cv.d.rectangle((0, 0, W * SS, H * SS), fill=(255, 255, 255)) if a > 0.98 else None
    return cv


# ======================================================================= wiring: scenes, banners, crossfades
SCENES = [(1, sc_open), (4, sc_quote), (5, sc_promises), ("title", sc_title), (6, sc_split), (7, sc_pure), (8, sc_franklin), (9, sc_habit),
          (10, sc_notebook), (11, sc_gym1), (12, sc_potato), (13, sc_year3), (14, sc_identity), (15, sc_dragon), (16, sc_lab), (17, sc_type1),
          (18, sc_type2), (19, sc_diary), (20, sc_winners), (21, sc_exits), (22, sc_river), (23, sc_pots), (24, sc_days), (25, sc_battle),
          (26, sc_cortes), (27, sc_juggle), (28, sc_fire), (29, sc_boats), (30, sc_planb), (31, sc_bad), (32, sc_fog), (33, sc_think),
          (34, sc_ugly), (35, sc_chair1), (36, sc_tuition), (37, sc_map2), ("chairs", sc_chairs), (38, sc_belief1), (39, sc_belief2),
          (40, sc_burn), (41, sc_crown), (42, sc_comment), (43, sc_end)]
ACT_STARTS = (6, 16, 22, 32, 38)


def _start(key):
    if key == "title": return EN(5) + 0.2
    if key == "chairs": return AT(37, 0.55) - 0.05
    return LS(key) - (0.05 if key in ACT_STARTS else 0.15)


SCENE_T = [(_start(k), fn) for k, fn in SCENES]
XF = 0.25
ACTS = [(6, "ACT I", "FRANKLIN vs. YOUR INNER CHILD"), (16, "ACT II", "TYPE 1 vs. TYPE 2 CRAZY"), (22, "ACT III", "BURN THE BOATS"),
        (32, "ACT IV", "ACTION PRODUCES INFORMATION"), (38, "OUTRO", "THE BELIEF METER")]


def decorate(cv, t):
    for n, a, b in ACTS:                                                       # act banner slides in for a few seconds
        t0 = LS(n)
        if t0 - 0.05 <= t < t0 + 3.7:
            kin, kout = ease((t - t0) / 0.4), ease((t - (t0 + 3.2)) / 0.45)
            wd = cv.text_w(a + "   " + b, 34, "marker") + 70
            with cv.at(lerp(-wd - 40, 36, kin) - lerp(0, wd + 80, kout), 20):
                cv.rect(0, 0, wd, 64, r=14, fill=NAVY, w=5, amp=0.8, col=NAVY)
                cv.text(a, 22, 34, size=34, font="marker", col=GOLD, anchor="lm")
                cv.text(b, 22 + cv.text_w(a + "   ", 34, "marker"), 34, size=34, font="marker", col=PAPER, anchor="lm")
    cv.text(SERIES, 1884, 1046, size=26, font="cinzel", col=(176, 178, 188), anchor="rm")


def frame_at(t):
    k = max([i for i, (s, _) in enumerate(SCENE_T) if s <= t] or [0])
    s0, fn = SCENE_T[k]
    cv = fn(t)
    decorate(cv, t)
    img = cv.finish()
    if k > 0 and t - s0 < XF:
        pv = SCENE_T[k - 1][1](t)
        decorate(pv, t)
        img = Image.blend(pv.finish(), img, ease((t - s0) / XF))
    if t > TOTAL - 1.2:
        img = Image.blend(img, Image.new("RGB", img.size, (255, 255, 255)), clamp01((t - (TOTAL - 1.2)) / 1.0))
    return img


# ======================================================================= sound effects (synthesised) + music
def _env(n, a=0.004, r=0.05):
    e = np.ones(n, np.float32)
    na, nr = min(int(a * SR), n), min(int(r * SR), n)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def _noise(n, seed=1): return np.random.default_rng(seed).normal(0, 1, n).astype(np.float32)


def _lp(x, k): return np.convolve(x, np.ones(k) / k, "same").astype(np.float32)


def sfx_zap():
    n = int(0.75 * SR); tt = np.arange(n) / SR
    saw = (2 * ((tt * (110 + 40 * np.sin(tt * 60))) % 1) - 1)
    crackle = _noise(n, 3) * (np.random.default_rng(4).random(n) > 0.82)
    sig = (saw * 0.55 + crackle * 0.8) * np.exp(-tt * 3.2) * (0.6 + 0.4 * np.sign(np.sin(tt * 90)))
    return (sig * _env(n, 0.003, 0.15) * 0.55).astype(np.float32)


def sfx_boing():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    f = 180 + 520 * np.exp(-tt * 7) * (1 + 0.5 * np.sin(tt * 40))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6) * _env(n, 0.002, 0.08) * 0.35).astype(np.float32)


def sfx_scribble(dur=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR
    hp = _noise(n, 7) - _lp(_noise(n, 7), 14)
    return (hp * (0.6 + 0.4 * np.sign(np.sin(tt * 55))) * _env(n, 0.01, 0.08) * 0.12).astype(np.float32)


def sfx_smash():
    n = int(0.6 * SR); tt = np.arange(n) / SR
    out = _noise(n, 9) * np.exp(-tt * 14) * 0.5
    for k, f in enumerate((2300, 3100, 1800)):
        s = int((0.02 + 0.07 * k) * SR)
        m = min(int(0.2 * SR), n - s)
        out[s:s + m] += np.sin(2 * np.pi * f * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 22) * 0.3
    return (out * _env(n, 0.001, 0.1)).astype(np.float32)


def sfx_splash():
    n = int(0.8 * SR); tt = np.arange(n) / SR
    return (_lp(_noise(n, 11), 6) * np.exp(-tt * 4.5) * (1 + 0.6 * np.sin(tt * 30)) * _env(n, 0.01, 0.2) * 0.45).astype(np.float32)


def sfx_ding():
    n = int(0.9 * SR); tt = np.arange(n) / SR
    return ((np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 1976 * tt) + 0.2 * np.sin(2 * np.pi * 2637 * tt)) * np.exp(-tt * 5.5)
            * _env(n, 0.002, 0.1) * 0.22).astype(np.float32)


def sfx_poof():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    return (_lp(_noise(n, 13), 10) * np.exp(-tt * 7) * _env(n, 0.004, 0.1) * 0.5).astype(np.float32)


def sfx_stamp():
    n = int(0.45 * SR); tt = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (95 - 40 * tt) * tt) * np.exp(-tt * 14)
    click = _noise(n, 15) * np.exp(-tt * 120) * 0.5
    return ((thud + click) * _env(n, 0.001, 0.08) * 0.7).astype(np.float32)


def sfx_buzzer():
    n = int(0.55 * SR); tt = np.arange(n) / SR
    sq = np.sign(np.sin(2 * np.pi * 120 * tt)) * 0.5 + np.sign(np.sin(2 * np.pi * 151 * tt)) * 0.3
    return (_lp(sq.astype(np.float32), 5) * _env(n, 0.005, 0.1) * 0.25).astype(np.float32)


def sfx_click():
    n = int(0.12 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 90) * 0.4 + _noise(n, 5) * np.exp(-tt * 200) * 0.2).astype(np.float32)


def sfx_fire(dur=0.9):
    n = int(dur * SR); tt = np.arange(n) / SR
    hp = _noise(n, 21) - _lp(_noise(n, 21), 30)
    crack = _noise(n, 22) * (np.random.default_rng(23).random(n) > 0.994) * 3
    return ((_lp(hp, 3) * 0.25 + crack * 0.4) * _env(n, 0.1, 0.3) * (0.7 + 0.3 * np.sin(tt * 17))).astype(np.float32)


def sfx_thud():
    n = int(0.25 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * (70 - 25 * tt) * tt) * np.exp(-tt * 20) * _env(n, 0.001, 0.05) * 0.6).astype(np.float32)


def pluck(freq, dur=0.4, bright=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * tt) + 0.5 * np.sin(4 * np.pi * freq * tt) * bright + 0.2 * np.sin(6 * np.pi * freq * tt) * bright
    return (s * np.exp(-tt * 9) * _env(n, 0.002, 0.05)).astype(np.float32)


def nf(m): return 440 * 2 ** ((m - 69) / 12)


def music_fun(total, level=0.22):
    """Bouncy ukulele-style loop: C - G - Am - F at 120 bpm (pluck arpeggio, bass on 1 and 3, shaker on the off-beats)."""
    n = int(total * SR); out = np.zeros(n, np.float32)
    chords = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]
    bass = [36, 43, 45, 41]
    hat = (_noise(int(0.05 * SR), 31) - _lp(_noise(int(0.05 * SR), 31), 8)) * np.exp(-np.arange(int(0.05 * SR)) / SR * 70) * 0.25
    k = 0
    while k * 0.25 < total + 1:
        tm = k * 0.25
        bar, step = (k // 8) % 4, k % 8
        place(out, pluck(nf(chords[bar][(0, 1, 2, 1, 0, 1, 2, 1)[step]] + 12), 0.35), tm)
        if step in (0, 4):
            place(out, pluck(nf(bass[bar]), 0.5, 0.3) * 1.5, tm)
        if step % 2 == 1:
            place(out, hat.astype(np.float32), tm)
        k += 1
    t_ = np.arange(n) / SR
    out *= np.clip(t_ / 1.5, 0, 1) * np.clip((total - t_) / 2.0, 0, 1)
    return out / (np.abs(out).max() + 1e-6) * level


SFXF = {"pop": lambda: sfx("pop"), "tick": lambda: sfx("tick") * 1.4, "coin": lambda: sfx("coin"), "boom": lambda: sfx("boom") * 0.7,
        "whoosh": lambda: sfx("whoosh") * 0.3, "hit": fx_hit, "shimmer": fx_shimmer, "zap": sfx_zap, "boing": sfx_boing, "scribble": sfx_scribble,
        "smash": sfx_smash, "splash": sfx_splash, "ding": sfx_ding, "poof": sfx_poof, "stamp": sfx_stamp, "buzzer": sfx_buzzer,
        "click": sfx_click, "fire": sfx_fire, "thud": sfx_thud, "riser": lambda: fx_riser(1.3) * 0.7}

# (script line, fraction of that line, sound)
FXT = (
    [(1, .05, "scribble"), (1, .42, "pop"), (1, .58, "pop"), (1, .76, "pop"), (2, .22, "pop"), (2, .38, "pop"), (2, .54, "pop"),
     (3, .14, "pop"), (3, .30, "tick"), (3, .55, "ding"), (4, .05, "scribble"), (4, .20, "boing"), (4, .42, "stamp"), (4, .70, "scribble"),
     (5, .10, "pop"), (5, .22, "stamp"), (5, .40, "pop"), (5, .72, "pop"), (6, .20, "pop"), (6, .50, "pop")]
    + [(7, 0.0, "pop"), (7, .25, "scribble"), (7, .44, "whoosh"), (7, .62, "pop"), (7, .75, "pop"), (7, .93, "zap"), (7, .94, "hit")]
    + [(8, .10, "pop"), (8, .30, "pop"), (8, .62, "pop"), (8, .74, "ding"), (8, .81, "ding"), (8, .88, "buzzer")]
    + [(9, .05, "scribble"), (9, .30, "scribble"), (9, .40, "scribble"), (9, .62, "stamp"), (9, .70, "scribble")]
    + [(10, .05, "pop")] + [(10, .30 + .017 * k, "tick") for k in range(24)] + [(10, .82, "stamp")]
    + [(11, .20, "pop"), (11, .30, "pop"), (11, .55, "pop"), (11, .78, "pop")] + [(11, .3 + .12 * k, "tick") for k in range(5)]
    + [(12, .05, "scribble"), (12, .45, "boing"), (13, .10, "pop"), (13, .25, "boing"), (13, .55, "pop"), (13, .75, "pop"),
       (14, .10, "pop"), (14, .30, "buzzer"), (14, .35, "pop"), (14, .70, "scribble"), (15, .15, "pop"), (15, .35, "ding"), (15, .42, "pop"), (15, .50, "fire"),
       (15, .70, "pop")]
    + [(16, .45, "pop"), (16, .50, "poof"), (16, .78, "pop"), (16, .80, "poof"), (17, .20, "pop"), (17, .34, "pop"), (17, .78, "scribble")]
    + [(17, .5 + .012 * k, "tick") for k in range(18)]
    + [(18, .10, "pop"), (18, .45, "thud"), (18, .55, "fire"), (18, .82, "stamp"), (19, .5, "pop"), (19, .55, "pop"), (19, .70, "pop"),
       (20, .10, "pop"), (20, .30, "pop"), (20, .50, "pop"), (20, .62, "pop"), (20, .82, "ding")]
    + [(21, .05 + .1 * k, "pop") for k in range(4)] + [(21, .18 + .1 * k, "scribble") for k in range(4)] + [(21, .66, "pop")]
    + [(22, .10, "scribble"), (22, .30, "pop"), (22, .50, "pop"), (23, .35, "stamp"), (23, .70, "stamp")]
    + [(23, .42 + .06 * k, "smash") for k in range(3)] + [(23, .76 + .05 * k, "splash") for k in range(3)]
    + [(24, .10 + .2 * k, "pop") for k in range(3)] + [(24, .28 + .1 * k, "poof") for k in range(3)] + [(24, .45, "pop"), (24, .50, "stamp"), (24, .72, "poof")]
    + [(25, .10, "whoosh"), (25, .80, "boom")] + [(25, .35 + .06 * k, "thud") for k in range(8)]
    + [(26, .05 + .04 * k, "splash") for k in range(3)] + [(26, .38, "stamp"), (26, .68, "pop"), (26, .74, "ding")]
    + [(27, .15 + .15 * k, "pop") for k in range(5)]
    + [(28, .2, "boom"), (28, .5, "pop"), (28, .5, "fire"), (28, .62, "stamp")]
    + [(29, .12 + .07 * k, "pop") for k in range(5)] + [(29, .55, "pop"), (29, .85, "ding")]
    + [(30, .15, "pop"), (30, .65, "tick"), (30, .78, "click"), (30, .80, "whoosh"), (30, .82, "boom")]
    + [(31, .0, "pop"), (31, .3, "pop"), (31, .55, "stamp")]
    + [(32, .28, "pop"), (32, .40, "pop"), (32, .52, "pop"), (32, .55, "tick"), (32, .70, "tick"), (32, .85, "tick")]
    + [(33, .2, "pop"), (33, .3, "buzzer"), (33, .62, "click"), (33, .68, "pop")]
    + [(34, .05, "pop"), (34, .22, "stamp"), (34, .38, "pop"), (34, .55, "stamp"), (34, .70, "pop"), (34, .87, "stamp")]
    + [(35, .38, "smash"), (35, .38, "boom"), (35, .58, "ding"), (35, .78, "scribble")]
    + [(36, .3, "pop")] + [(36, .4 + .05 * k, "coin") for k in range(6)] + [(36, .72, "ding")]
    + [(37, .32, "pop"), (37, .55, "pop"), (37, .60, "pop"), (37, .70, "boing"), (37, .85, "ding")] + [(37, .02 + .06 * k, "tick") for k in range(8)]
    + [(38, .3, "tick"), (38, .62, "buzzer"), (38, .7, "pop"), (39, .4, "ding"), (39, .4, "boing"), (39, .58, "ding"), (39, .76, "ding")]
    + [(40, .22, "scribble"), (40, .45, "pop"), (40, .5, "fire")] + [(40, .76 + .07 * k, "pop") for k in range(3)]
    + [(41, .3, "scribble"), (41, .4, "pop"), (41, .7, "ding"), (41, .85, "shimmer")] + [(41, .55 + .12 * k, "pop") for k in range(3)]
    + [(42, .35 + .015 * k, "tick") for k in range(26)] + [(42, .8, "pop")]
    + [(43, .15, "pop"), (43, .6, "click"), (43, .6, "ding"), (43, .7, "pop")]
)


def build_audio():
    voice = TL.voice_track()
    fx = np.zeros_like(voice)
    mus = music_fun(TOTAL)[:len(voice)]
    for key, fn in SCENES[1:]:
        if key != "title":
            place(fx, SFXF["whoosh"](), _start(key) - 0.3)
    for n in ACT_STARTS:
        place(fx, SFXF["whoosh"](), LS(n) - 0.05)
    t0 = EN(5) + 0.25                                                          # the title slam
    place(fx, fx_riser(1.3) * 0.7, t0 - 1.3); place(fx, sfx("boom"), t0); place(fx, fx_hit(), t0); place(fx, fx_shimmer(), t0 + 0.4)
    for n, fr, name in FXT:
        place(fx, SFXF[name](), AT(n, fr))
    out = p("_mix.wav")
    finish_audio(voice, mus, fx, out, HERE)
    return out


# ======================================================================= rendering (parallel chunks on 4 cores)
def _render_chunk(job):
    k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        t = k / FPS
        img = frame_at(t)
        if t < 0.3:
            img = Image.blend(Image.new("RGB", img.size, (255, 255, 255)), img, t / 0.3)
        ff.stdin.write(np.asarray(img.convert("RGB")).tobytes())
    ff.stdin.close(); ff.wait()
    return path


def render_parallel(total, audio_wav, out_mp4, procs=4, parts=16):
    import multiprocessing as mp
    nf_ = int(round(total * FPS))
    tmp = tempfile.mkdtemp(prefix="wb_parts_", dir=HERE)
    bounds = [round(nf_ * i / parts) for i in range(parts + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(tmp, f"part{i:02d}.mp4")) for i in range(parts)]
    with mp.get_context("fork").Pool(procs) as pool:
        for n, _ in enumerate(pool.imap_unordered(_render_chunk, jobs), 1):
            print(f"chunk {n}/{parts} done", flush=True)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio_wav, "-c:v", "copy",
                    "-af", "alimiter=limit=0.70:level=disabled", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    wav = build_audio()
    out = p("wb01_fake_it.mp4")
    render_parallel(TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
