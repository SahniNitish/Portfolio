"""Deep Time Academy reel 2 (9:16, 1080x1920): "Why Billionaires Are Terrified of One Thing" (original script, topic from a Prof. Jiang clip).

Voice: Kokoro (free draft; swap audio/clean/l1..l10.wav for Fish WNBA VOICEOVER when credits allow). Stick engine, music and sfx come from wb01.

    python deeptime/wb03-reel-wealth/episode.py        # renders wb03_reel.mp4 (about 1.5 min on 4 cores)
"""
import importlib.util, json, math, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WB01 = os.path.join(HERE, "..", "wb01-fake-it")
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from stick import *  # noqa: E402,F401,F403
from engine import Timeline, finish_audio, place, FPS  # noqa: E402

_spec = importlib.util.spec_from_file_location("wb01", os.path.join(WB01, "episode.py"))   # reuse wb01's helpers, sfx and music
wb = importlib.util.module_from_spec(_spec); sys.modules["wb01"] = wb; _spec.loader.exec_module(wb)

p = lambda *a: os.path.join(HERE, *a)
RW, RH = 1080, 1920
GY = 1480                                                    # ground line (keeps clear of the reel UI at the bottom)
WANT = list(range(1, 11))
WORDS = json.load(open(p("words.json")))
GAPS = [0.35] * len(WANT)
GAPS[1], GAPS[3], GAPS[8], GAPS[9] = 0.6, 0.5, 0.5, 1.6
TL = Timeline([p("audio", "clean", f"l{n}.wav") for n in WANT], GAPS, lead=0.3)
L, END, TOTAL = TL.L, TL.end, TL.total


def _ix(k): return WANT.index(k) if k in WANT else k - 1     # accepts a wb01 line number (14, 29...) or a reel index 1..9
def AT(k, frac): return L(_ix(k)) + frac * (END(_ix(k)) - L(_ix(k)))
def LS(k): return L(_ix(k))
def EN(k): return END(_ix(k))
def SG(t, k): return clamp01((t - LS(k)) / max(EN(k) - LS(k), 1e-6))


def RC(t, u=0.0, shake=0.0):
    z = 1.0 + 0.03 * u
    return Canvas(t, cam=(RW / 2 + (np.random.uniform(-shake, shake) if shake else 0), RH / 2, z), size=(RW, RH))


fig, tag, cap, pp, appear, hold = wb.fig, wb.tag, wb.cap, wb.pp, wb.appear, wb.hold


# ---------------------------------------------------------------- word-by-word captions (the spoken word turns red)
def make_chunks():
    chunks = []
    for k, n in enumerate(WANT, 1):
        ws = [(w, LS(k) + s, LS(k) + e) for w, s, e in WORDS[str(n)]]
        cur = []
        for i, wd in enumerate(ws):
            cur.append(wd)
            if len(cur) >= 3 or wd[0][-1] in ".,?!:;" or (i + 1 < len(ws) and ws[i + 1][1] - wd[2] > 0.35):
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
    return chunks


CHUNKS = make_chunks()


def draw_caption(cv, t):
    for i, ch in enumerate(CHUNKS):
        t0 = ch[0][1] - 0.04
        nxt = CHUNKS[i + 1][0][1] - 0.04 if i + 1 < len(CHUNKS) else 1e9
        t1 = nxt if nxt - ch[-1][2] < 0.6 else ch[-1][2] + 0.35
        if t0 <= t < t1:
            break
    else:
        return
    words = [w.upper() for w, _, _ in ch]
    size = 134
    gap = lambda sz: 0.26 * sz
    width = lambda sz: sum(cv.text_w(w, sz, "anton") for w in words) + gap(sz) * (len(words) - 1)
    while width(size) > 900 and size > 60:
        size -= 6
    total = width(size)
    sc = 0.78 + 0.22 * ease_out_back(clamp01((t - t0) / 0.12))
    with cv.at(540, 520, sc):
        cv.band(-total / 2 - 26, -size * 0.58, total / 2 + 26, size * 0.58, col=LGOLD, alpha=0.8)
        x = -total / 2
        for (w, ws, we), word in zip(ch, words):
            cv.text(word, x, 0, size=size, font="anton", col=RED if ws - 0.02 <= t < we + 0.05 else INK, anchor="lm")
            x += cv.text_w(word, size, "anton") + gap(size)


def decorate(cv, t):
    cv.text("DEEP TIME ACADEMY", 540, 96, size=30, font="cinzel", col=(176, 178, 188))
    draw_caption(cv, t)


# ---------------------------------------------------------------- scenes (portrait)
def pile(cv, x, y, s=1.0, n=14, reveal=1.0):
    rows = [(0, 6), (1, 5), (2, 3), (3, 1)]
    k = 0
    for r, c in rows:
        for i in range(c):
            if k / n > reveal:
                return
            cv.ellipse(x + (i - (c - 1) / 2) * 62 * s, y - 20 * s - r * 34 * s, 36 * s, 17 * s, fill=GOLD, w=4)
            cv.text("$", x + (i - (c - 1) / 2) * 62 * s, y - 20 * s - r * 34 * s, size=int(26 * s), font="marker", col=NAVY)
            k += 1


def hourglass(cv, x, y, f, s=1.0, rot=0.0):
    with cv.at(x, y, s, rot):
        cv.poly([(-130, -560), (130, -560), (0, -330)], closed=True, fill=CREAM, w=7)
        cv.poly([(0, -330), (-130, -100), (130, -100)], closed=True, fill=CREAM, w=7)
        if f < 0.99:
            q = 1 - f
            cv.poly([(-120 * q, -552), (120 * q, -552), (0, -552 + 210 * q)], closed=True, fill=GOLD, w=2, amp=0)
        if f > 0.01:
            cv.poly([(-124 * f, -106), (124 * f, -106), (0, -106 - 220 * f)], closed=True, fill=GOLD, w=2, amp=0)
        cv.line((0, -330), (0, -106), w=4, col=GOLD) if 0.02 < f < 0.98 else None
        cv.rect(-160, -590, 160, -560, w=8, fill=BROWN)
        cv.rect(-160, -100, 160, -70, w=8, fill=BROWN)


def skull(cv, x, y, s=1.0):
    with cv.at(x, y, s):
        cv.ellipse(0, 0, 60, 54, fill=PAPER, w=6)
        cv.rect(-30, 36, 30, 80, r=8, fill=PAPER, w=6)
        cv.ellipse(-22, 2, 14, 16, fill=INK, w=2, amp=0); cv.ellipse(22, 2, 14, 16, fill=INK, w=2, amp=0)
        cv.poly([(0, 24), (-7, 38), (7, 38)], closed=True, fill=INK, w=2, amp=0)


def building(cv, x, y, w, h, label, t, t_in, col=CREAM, size=34):
    r = appear(t, t_in, 0.5)
    if r <= 0.01:
        return
    with cv.at(x, y):
        cv.rect(-w / 2, -h, w / 2, 0, w=8, fill=col, reveal=r)
        for i in range(3):
            for j in range(max(2, int(h // 150))):
                cv.rect(-w / 2 + 26 + i * (w - 52) / 3, -h + 30 + j * 100, -w / 2 + 26 + i * (w - 52) / 3 + 40, -h + 70 + j * 100, w=4, fill=SKY, reveal=r)
        cv.text(label, 0, -h - 40, size=size, font="marker", col=NAVY, reveal=r)


def sc_w1(t):                                     # imagine $10 billion, still can't fix one problem
    cv = RC(t, SG(t, 1))
    ground(cv, GY, 60, 1020)
    pile(cv, 540, GY, 2.0, reveal=appear(t, LS(1) + 0.2, 1.0))
    s = pp(t, AT(1, 0.15), 0.5)
    if s > 0.02:
        with cv.at(540, GY - 215, s):
            fig(cv, 0, 0, h=470, pose="arms_out", face="smile" if t < AT(1, 0.6) else "worry", outfit=("suit", "crown"), w=9)
    tag(cv, t, AT(1, 0.3), "$10,000,000,000", 540, 760, size=76, col=NAVY)
    if t > AT(1, 0.68):
        cv.text("?", 800, 860 + 14 * math.sin(t * 5), size=190, font="marker", col=RED)
    return cv


def sc_w2(t):                                     # you can't buy more time
    u = SG(t, 2)
    cv = RC(t, u)
    ground(cv, GY, 60, 1020)
    hourglass(cv, 640, GY, ease(u * 0.9), s=1.0)
    fig(cv, 220, GY, h=470, pose="shrug", face="worry", outfit=("suit",), w=9)
    for k in range(5):
        tt = (t * 0.9 + k / 5) % 1
        if u > 0.25:
            cv.ellipse(300 + 120 * tt, 1000 - 220 * tt + 30 * math.sin(tt * 9), 30, 15, fill=GOLD, w=3, amp=0.3)
    stamp(cv, 540, 780, "SOLD OUT", col=RED, size=90, rot=-6, s=pp(t, AT(2, 0.55), 0.4))
    return cv


def sc_w3(t):                                     # first emperor sent expeditions for an elixir
    u = SG(t, 3)
    cv = RC(t, u)
    waves(cv, GY - 40, 0, 560, t, n=3, gap=40)
    ground(cv, GY, 560, 1020)
    bx = lerp(-100, 400, ease(clamp01((u - 0.1) / 0.8)))
    with cv.at(bx, GY - 70, 1.5, 3 * math.sin(t * 2)):
        boat(cv, 0, 0, 1.0)
    cap(cv, t, AT(3, 0.35), "EXPEDITION", 300, 1000, size=52, col=NAVY, font="marker")
    fig(cv, 800, GY, h=520, pose="point", face="smile", outfit=("crown",), w=10, flip=True)
    tag(cv, t, AT(3, 0.2), "QIN SHI HUANG", 800, 810, size=46, col=NAVY)
    flask(cv, 560, GY - 120, GOLD, s=2.0, t=t, sparkle=True, label="ELIXIR") if t > AT(3, 0.6) else None
    cap(cv, t, AT(3, 0.75), "~ 220 BC", 540, 1620, size=52, col=GREY)
    return cv


def sc_w4(t):                                     # pills contained mercury, probably did him in
    u = SG(t, 4)
    cv = RC(t, u)
    ground(cv, GY, 60, 1020)
    flask(cv, 330, GY - 80, GREY, s=2.4, t=t, smoke=True, label="MERCURY")
    k = ease(clamp01((u - 0.45) / 0.35))
    with cv.at(740 + 30 * k, GY, 1.0, 30 * k):
        fig(cv, 0, 0, h=500, pose="slump" if u > 0.45 else "stand", face="sweat" if u > 0.3 else "smile", outfit=("crown",), w=10)
    if u > 0.8:
        skull(cv, 540, 900, pp(t, AT(4, 0.8), 0.4) * 1.5)
    stamp(cv, 540, 760, "OOPS", col=RED, size=120, rot=-8, s=pp(t, AT(4, 0.55), 0.4))
    return cv


def sc_w5(t):                                     # today: longevity labs, Altos Labs, $3 billion
    u = SG(t, 5)
    cv = RC(t, u)
    ground(cv, GY, 60, 1020)
    building(cv, 540, GY, 520, 560, "ALTOS LABS", t, LS(5) + 0.2, size=56)
    gear(cv, 190, GY - 430, 70, ang=t * 1.2)
    gear(cv, 880, GY - 330, 56, ang=-t * 1.5)
    flask(cv, 190, GY - 130, GREEN, s=1.8, t=t, sparkle=True)
    flask(cv, 880, GY - 100, SKY, s=1.8, t=t, sparkle=True)
    tag(cv, t, AT(5, 0.5), "2021 • $3 BILLION", 540, 820, size=64, col=NAVY)
    return cv


def sc_w6(t):                                     # sunk cost: I built all this, can't lose it
    u = SG(t, 6)
    cv = RC(t, u)
    waves(cv, GY - 20, 0, RW, t, n=3, gap=44)
    anchor(cv, 540, GY - 20, 2.6)
    pile(cv, 220, GY - 20, 1.3, reveal=1.0)
    fig(cv, 820, GY - 40, h=470, pose="fear", face="sweat", outfit=("suit",), w=9)
    thought(cv, 600, 860, "I built all this.\nI can't lose it!", size=48, tail_to=(780, 1020), reveal=appear(t, AT(6, 0.4), 0.5))
    stamp(cv, 400, 1090, "SUNK COST", col=RED, size=96, rot=-5, s=pp(t, AT(6, 0.18), 0.4))
    return cv


def sc_w7(t):                                     # wealth never stays in one place
    u = SG(t, 7)
    cv = RC(t, u)
    ground(cv, GY, 60, 1020)
    building(cv, 210, GY, 260, 420, "BANK A", t, LS(7) + 0.1, size=34)
    building(cv, 540, GY, 260, 560, "BANK B", t, LS(7) + 0.3, size=34)
    building(cv, 870, GY, 260, 360, "BANK C", t, LS(7) + 0.5, size=34)
    m = ease(clamp01((u - 0.3) / 0.6))
    bx = lerp(210, 870, m)
    by = GY - 560 - 110 * math.sin(m * math.pi) - 40
    with cv.at(bx, by, 1.2, 12 * math.sin(t * 9)):
        cv.ellipse(0, 0, 48, 56, fill=CREAM, w=6)
        cv.text("$", 0, 4, size=62, font="marker", col=GREEN)
    cv.line((210, 720), (860, 720), w=6, col=GREY, reveal=appear(t, AT(7, 0.5), 0.5))
    cap(cv, t, AT(7, 0.55), "MONEY MOVES", 540, 800, size=70, col=NAVY, font="marker")
    return cv


def sc_w8(t):                                     # empires rise, fortunes crumble
    u = SG(t, 8)
    cv = RC(t, u)
    ground(cv, GY, 60, 1020)
    pts = [(80 + i * 22, GY - 300 - 360 * math.sin(i / 43 * math.pi * 2.0) * (1 - i / 80) + 0 * i) for i in range(0, 41)]
    cv.poly(pts, w=12, col=NAVY, reveal=appear(t, LS(8) + 0.2, 3.0))
    sx = int(40 * clamp01((t - LS(8) - 0.2) / 3.0))
    px, py = pts[sx]
    with cv.at(px, py - 70, 1.5):
        crown(cv, 0, 0, 1.0)
    cap(cv, t, AT(8, 0.2), "RISE", 230, 1040, size=90, col=GREEN, font="marker")
    cap(cv, t, AT(8, 0.55), "CRUMBLE", 760, 1590, size=90, col=RED, font="marker")
    if t > AT(8, 0.85):
        stamp(cv, 540, 800, "NOTHING LASTS", col=NAVY, size=80, rot=-4, s=pp(t, AT(8, 0.85), 0.4))
    return cv


def sc_w9(t):                                     # rich don't fear dying, they fear starting over
    u = SG(t, 9)
    cv = RC(t, u)
    ground(cv, GY, 60, 1020)
    pile(cv, 300, GY, 1.6, reveal=1.0 - 0.9 * ease(clamp01((u - 0.5) / 0.4)))
    fig(cv, 760, GY, h=520, pose="fear", face="sweat", outfit=("suit", "crown"), w=10)
    tag(cv, t, AT(9, 0.1), "DYING?", 300, 780, size=84, col=GREY, band=None)
    cv.line((120, 780), (480, 780), w=14, col=RED, reveal=appear(t, AT(9, 0.3), 0.3), amp=1.5)
    if t > AT(9, 0.55):
        stamp(cv, 540, 940, "START OVER", col=RED, size=110, rot=-6, s=pp(t, AT(9, 0.55), 0.4))
    return cv


def sc_w10(t):                                    # follow
    cv = RC(t, SG(t, 10))
    ground(cv, GY, 60, 1020)
    fig(cv, 540, GY, h=560, pose="cheer" if int(t * 3) % 2 else POSE["point_up"], face="big", outfit=("crown",), w=11)
    r = pp(t, AT(10, 0.1), 0.45)
    clicked = t > AT(10, 0.5)
    with cv.at(540, 800, r):
        cv.rect(-260, -70, 260, 70, r=70, fill=GREY if clicked else RED, w=8)
        cv.text("FOLLOWING" if clicked else "FOLLOW", 0, 4, size=70, font="marker", col=PAPER)
    if clicked:
        with cv.at(790, 700, 1.2, 14 * math.sin(t * 22)):
            cv.poly([(-34, 30), (-28, -20), (0, -46), (28, -20), (34, 30)], closed=True, fill=GOLD, w=6, amp=0.4)
            cv.line((-40, 30), (40, 30), w=7); cv.ellipse(0, 44, 9, 9, fill=GOLD, w=3)
    tag(cv, t, AT(10, 0.6), "FOLLOW FOR PART 2", 540, 1130, size=54, col=NAVY)
    return cv


SCENES = [(0.0, sc_w1)] + [(LS(i) - 0.1, fn) for i, fn in zip(range(2, 11), (sc_w2, sc_w3, sc_w4, sc_w5, sc_w6, sc_w7, sc_w8, sc_w9, sc_w10))]
XF = 0.12


def frame_at(t):
    k = max(i for i, (s, _) in enumerate(SCENES) if s <= t)
    s0, fn = SCENES[k]
    cv = fn(t); decorate(cv, t); img = cv.finish()
    if k > 0 and t - s0 < XF:
        pv = SCENES[k - 1][1](t); decorate(pv, t)
        img = Image.blend(pv.finish(), img, ease((t - s0) / XF))
    return img


# ---------------------------------------------------------------- audio: wb01's music and sound effects
FXT = [(1, .15, "pop"), (1, .30, "pop"), (1, .68, "buzzer"), (2, .55, "stamp"), (3, .20, "pop"), (3, .35, "whoosh"), (3, .60, "ding"), (3, .75, "pop"),
       (4, .30, "pop"), (4, .55, "stamp"), (4, .80, "thud"), (5, .20, "pop"), (5, .50, "pop"), (5, .60, "ding"), (6, .18, "stamp"), (6, .40, "pop"),
       (7, .30, "pop"), (7, .60, "whoosh"), (8, .20, "pop"), (8, .55, "boom"), (8, .85, "stamp"), (9, .10, "pop"), (9, .30, "scribble"), (9, .55, "stamp"),
       (10, .10, "pop"), (10, .50, "click"), (10, .51, "ding"), (10, .60, "pop")]


def build_audio():
    voice = TL.voice_track()
    fx = np.zeros_like(voice)
    mus = wb.music_fun(TOTAL, level=0.2)[:len(voice)]
    for s, _ in SCENES[1:]:
        place(fx, wb.SFXF["whoosh"](), s - 0.2)
    for ch in CHUNKS:                                                     # a soft tick as each caption pops in
        place(fx, wb.SFXF["tick"]() * 0.35, ch[0][1] - 0.04)
    for k, fr, name in FXT:
        place(fx, wb.SFXF[name](), AT(k, fr))
    out = p("_mix.wav")
    finish_audio(voice, mus, fx, out, HERE)
    return out


def _render_chunk(job):
    k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        ff.stdin.write(np.asarray(frame_at(k / FPS).convert("RGB")).tobytes())
    ff.stdin.close(); ff.wait()
    return path


def render_parallel(total, audio_wav, out_mp4, procs=4, parts=8):
    import multiprocessing as mp
    nf = int(round(total * FPS))
    tmp = tempfile.mkdtemp(prefix="reel_parts_", dir=HERE)
    bounds = [round(nf * i / parts) for i in range(parts + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(tmp, f"part{i:02d}.mp4")) for i in range(parts)]
    with mp.get_context("fork").Pool(procs) as pool:
        for n, _ in enumerate(pool.imap_unordered(_render_chunk, jobs), 1):
            print(f"chunk {n}/{parts} done", flush=True)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio_wav, "-c:v", "copy",
                    "-af", "alimiter=limit=0.74:level=disabled", "-c:a", "aac", "-ac", "2", "-ar", "44100", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    wav = build_audio()
    out = p("wb03_reel.mp4")
    render_parallel(TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
