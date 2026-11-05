"""Deep Time Academy reel (9:16, 1080x1920): "Feeling Like a Fraud? Good. Fake It Anyway."

Built entirely from OLD assets: the Fish Audio WNBA VOICEOVER lines already voiced for wb01-fake-it (9 of the 43 lines), the stick-figure engine
(deeptime/stick.py), wb01's sound effects and music. Only new things: portrait scene layouts and word-by-word captions (the spoken word is red).

    python deeptime/wb02-reel/episode.py        # renders wb02_reel.mp4 (about 1.5 min on 4 cores)
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
WANT = [1, 2, 3, 14, 29, 30, 36, 41, 43]                     # which wb01 narration lines the reel uses
WORDS = json.load(open(p("words.json")))
GAPS = [0.3] * len(WANT)
GAPS[0], GAPS[5], GAPS[7], GAPS[8] = 0.4, 1.0, 0.45, 1.6
TL = Timeline([os.path.join(WB01, "audio", "clean", f"l{n}.wav") for n in WANT], GAPS, lead=0.3)
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
def role(cv, t, t_in, x, kind, name, face, h=450):
    s = pp(t, t_in)
    if s <= 0.02:
        return
    with cv.at(x, GY, s):
        J = fig(cv, 0, 0, h=h, pose="flex" if kind == "fit" else "stand", face=face, w=6,
                outfit={"founder": ("suit",), "creator": (), "fit": ("tank",)}[kind])
        hold(cv, J, {"founder": "brief", "creator": "cam", "fit": "dumb"}[kind], hand="hA", s=1.5)
    tag(cv, t, t_in + 0.15, name, x, GY + 76, size=40, col=NAVY)


ROLES = [(190, "founder", "FOUNDER", 0.26), (540, "creator", "CREATOR", 0.42), (890, "fit", "FIT PERSON", 0.60)]


def sc_r1(t):                                     # line 1: what do founders, creators and fit people have in common?
    cv = RC(t, SG(t, 1))
    ground(cv, GY, 60, 1020)
    for x, kind, name, fr in ROLES:
        role(cv, t, AT(1, fr), x, kind, name, "neutral")
        if t > AT(1, fr) + 0.3:
            cv.text("?", x, GY - 560 + 12 * math.sin(t * 4 + x), size=120, font="marker", col=GOLD)
    return cv


def sc_r2(t):                                     # line 2: every one of them had no idea what they were doing
    cv = RC(t, SG(t, 2))
    ground(cv, GY, 60, 1020)
    for (x, kind, name, fr), txt, tf in zip(ROLES, ("no idea", "winging it", "send help"), (0.36, 0.52, 0.68)):
        role(cv, t, -5, x, kind, name, "sweat")
        if t > AT(2, tf):
            thought(cv, x, GY - 640, txt, size=44, tail_to=(x, GY - 520), reveal=appear(t, AT(2, tf), 0.4))
    return cv


def sc_r3(t):                                     # line 3: act confident first, let reality catch up
    cv = RC(t, SG(t, 3))
    ground(cv, GY, 60, 1020)
    flip = AT(3, 0.40)
    conf = t > flip
    pz = pose_mix("slump", "hips", ease(clamp01((t - flip) / 0.4)))
    fig(cv, 540, GY, h=620, pose=pz, face="cool" if conf else "sweat", outfit=("suit", "crown") if conf else ("suit",), w=12)
    wb.sparkle_burst(cv, 540, GY - 600, t, flip, r=260, n=12)
    cap(cv, t, LS(3) + 0.3, "reality loading...", 540, GY + 78, size=44, col=GREY)
    cv.rect(190, GY + 110, 890, GY + 150, r=16, w=5, reveal=appear(t, LS(3) + 0.3, 0.4))
    fr = 0.37 * appear(t, AT(3, 0.45), EN(3) - AT(3, 0.45))
    if fr > 0.01:
        cv.rect(196, GY + 116, 196 + 688 * fr, GY + 144, r=12, fill=GOLD, w=0.01, col=GOLD, amp=0)
    return cv


def sc_r4(t):                                     # line 14: you don't think your way into a new identity, you act your way in
    u = SG(t, 14)
    cv = RC(t, u)
    ground(cv, GY, 60, 1020)
    cx = lerp(250, 760, ease(clamp01((u - 0.5) / 0.4)))
    walking = 0.5 < u < 0.92
    with cv.fading(1 - ease((u - 0.9) / 0.1)):
        fig(cv, cx, GY, h=520, pose=walk_pose(t * 7, 0.9) if walking else ("think" if u < 0.5 else "stand"), face="worry" if u < 0.5 else "smile", w=10)
    thought(cv, 330, 960, "think my way\ninto a new me...", size=50, tail_to=(280, 1130), reveal=appear(t, LS(14) + 0.3, 0.5))
    xmark(cv, 330, 960, 3.4, reveal=appear(t, AT(14, 0.42), 0.4)) if t > AT(14, 0.42) else None
    r = appear(t, AT(14, 0.45), 0.5)
    with cv.at(860, GY):
        cv.rect(-150, -640, 150, 0, w=9, fill=CREAM, reveal=r)
        cv.ellipse(105, -300, 11, 11, fill=GOLD, w=2, reveal=r)
        tag(cv, t, AT(14, 0.55), "NEW\nIDENTITY", 0, -470, size=46, col=NAVY, band=None)
    return cv


def sc_r5(t):                                     # line 29: every backup plan is a boat, every boat is a permission slip to quit
    cv = RC(t, SG(t, 29))
    wb.waves(cv, GY - 40, 0, RW, t, n=3, gap=44) if hasattr(wb, "waves") else waves(cv, GY - 40, 0, RW, t, n=3, gap=44)
    for k, x in enumerate((190, 540, 890)):
        r = pp(t, AT(29, 0.15 + 0.10 * k), 0.4)
        if r > 0.02:
            with cv.at(x, GY - 60, r * 1.3, 3 * math.sin(t * 2 + k)):
                boat(cv, 0, 0, 1.0)
                cv.text("PLAN B", 0, -6, size=44, font="marker", col=PAPER)
    r = pp(t, AT(29, 0.62), 0.45)
    with cv.at(540, 930, r * 1.35, 3):
        cv.rect(-210, -150, 210, 150, r=12, fill=CREAM, w=7)
        cv.text("PERMISSION SLIP", 0, -86, size=44, font="marker", col=NAVY)
        cv.text("[   ]  I QUIT", 0, 0, size=60, font="hand")
        cv.line((-150, 96), (150, 96), w=4, col=GREY)
        if t > AT(29, 0.9):
            check(cv, -150, 0, 1.2)
    fig(cv, 160, 1060, h=330, pose="point", face="worry", w=6) if False else None
    return cv


def sc_r6(t):                                     # line 30: your Plan B is the reason your Plan A fails
    cut = AT(30, 0.82)
    cv = RC(t, SG(t, 30))
    ground(cv, GY + 40, 60, 1020)
    shake = 5 * math.sin(t * 30) if t < cut else 0
    k = t - cut
    ry = 1060 + shake if t < cut else 1060 - 1700 * ease(clamp01(k / 1.1))
    rocket(cv, 540 + shake, ry, 2.3, flame_t=t, rot=shake * 0.3)
    anchor(cv, 540, GY - 20, 2.2)
    if t < cut:
        cv.poly([(540, ry + 130), (505, 1230), (575, 1330), (540, GY - 120)], w=11, col=BROWN, amp=1.6)
    cap(cv, t, LS(30) + 0.3, "PLAN A", 800, 1000, size=64, col=NAVY, font="marker")
    cap(cv, t, LS(30) + 0.5, "PLAN B", 800, GY - 20, size=64, col=RED, font="marker")
    if AT(30, 0.68) < t < cut + 0.25:
        snip = abs(math.sin(t * 24)) if t < cut else 0
        with cv.at(540, 1270, 1.8):
            cv.poly([(-34, -26), (14 + snip * 6, 10), (34, 44)], w=9); cv.poly([(34, -26), (-14 - snip * 6, 10), (-34, 44)], w=9)
            cv.ellipse(-38, 56, 16, 16, w=7); cv.ellipse(38, 56, 16, 16, w=7)
    return cv


def sc_r7(t):                                     # line 36: failure isn't the opposite of success, it's the tuition
    cv = RC(t, SG(t, 36))
    ground(cv, GY, 60, 1020)
    r = appear(t, LS(36), 0.7)
    with cv.at(540, GY):
        cv.poly([(-380, -520), (0, -680), (380, -520)], closed=True, fill=CREAM, w=9, reveal=r)
        cv.rect(-380, -520, 380, -470, w=8, fill=PAPER, reveal=r)
        for k in range(5):
            cv.rect(-330 + k * 165 - 28, -470, -330 + k * 165 + 28, -24, w=7, fill=PAPER, reveal=r)
        cv.rect(-380, -24, 380, 0, w=8, fill=PAPER, reveal=r)
        cv.text("UNIVERSITY OF\nHARD KNOCKS", 0, -585, size=40, font="marker", col=NAVY, reveal=r)
    if t > AT(36, 0.3):
        with cv.at(300, GY + 80, pp(t, AT(36, 0.3), 0.4), -5):
            cv.rect(-140, -70, 140, 70, r=10, fill=CREAM, w=6)
            cv.text("TUITION DUE", 0, 0, size=44, font="marker", col=RED)
    if t > AT(36, 0.45):
        with cv.at(850, GY + 70, 1.0):
            cv.poly([(-50, 40), (-58, -70), (58, -70), (50, 40)], closed=True, fill=SKY, w=6)
            cv.text("FAILURES", 0, -14, size=24, font="marker")
            for q in range(5):
                if t > AT(36, 0.5 + 0.06 * q):
                    cv.ellipse(-30 + (q % 3) * 30, 20 - (q // 3) * 22, 12, 12, fill=GOLD, w=3, amp=0.3)
    if t > AT(36, 0.78):
        with cv.at(540, 1090, pp(t, AT(36, 0.78), 0.4), 3):
            cv.rect(-200, -56, 200, 56, r=10, fill=PAPER, w=6)
            cv.text("DEGREE IN EXPERIENCE", 0, 0, size=30, font="marker", col=NAVY)
    return cv


def sc_r8(t):                                     # line 41: a fraud and a founder differ by about three years of showing up
    cv = RC(t, SG(t, 41))
    ground(cv, GY, 60, 1020)
    drop = clamp01((t - AT(41, 0.78)) / 0.4)
    potato(cv, 540, GY, 3.2, face="big" if drop >= 1 else "smile", arms="down", wobble=2 * math.sin(t * 3), t=t)
    if drop > 0:
        crown(cv, 540, lerp(500, GY - 440, ease_out_back(drop, 2.0)), 2.2, rot=(1 - drop) * 25)
    if drop >= 1:
        sparkles(cv, 540, GY - 380, t, n=7, r=240)
    tag(cv, t, AT(41, 0.28), "FRAUD", 540, 700, size=110, col=GREY, band=None)
    cv.line((300, 700), (780, 700), w=14, col=RED, reveal=appear(t, AT(41, 0.34), 0.3), amp=1.5)
    tag(cv, t, AT(41, 0.40), "FOUNDER", 540, 840, size=130, col=NAVY)
    return cv


def sc_r9(t):                                     # line 43: subscribe + sign-off
    cv = RC(t, SG(t, 43))
    ground(cv, GY, 60, 1020)
    fig(cv, 540, GY, h=560, pose="cheer" if int(t * 3) % 2 else S_POSE_UP, face="big", outfit=("crown",), w=11)
    r = pp(t, AT(43, 0.12), 0.45)
    clicked = t > AT(43, 0.55)
    with cv.at(540, 800, r):
        cv.rect(-290, -70, 290, 70, r=70, fill=GREY if clicked else RED, w=8)
        cv.text("SUBSCRIBED" if clicked else "SUBSCRIBE", 0, 4, size=66, font="marker", col=PAPER)
    if clicked:
        with cv.at(790, 700, 1.2, 14 * math.sin(t * 22)):
            cv.poly([(-34, 30), (-28, -20), (0, -46), (28, -20), (34, 30)], closed=True, fill=GOLD, w=6, amp=0.4)
            cv.line((-40, 30), (40, 30), w=7); cv.ellipse(0, 44, 9, 9, fill=GOLD, w=3)
    u = ease(clamp01((t - AT(43, 0.25)) / 0.3))
    if t > AT(43, 0.2):
        with cv.at(lerp(760, 600, u), lerp(1050, 850, u), 1.4):
            cv.poly([(0, 0), (0, 54), (14, 42), (26, 66), (38, 60), (26, 38), (44, 36)], closed=True, fill=PAPER, w=5, amp=0.3)
    tag(cv, t, AT(43, 0.7), "FAKE IT. WING IT. WIN IT.", 540, 1150, size=62, col=NAVY)
    return cv


S_POSE_UP = POSE["point_up"]
SCENES = [(0.0, sc_r1), (LS(2) - 0.1, sc_r2), (LS(3) - 0.1, sc_r3), (LS(4) - 0.1, sc_r4), (LS(5) - 0.1, sc_r5), (LS(6) - 0.1, sc_r6),
          (LS(7) - 0.1, sc_r7), (LS(8) - 0.1, sc_r8), (LS(9) - 0.1, sc_r9)]
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
FXT = [(1, .26, "pop"), (1, .42, "pop"), (1, .60, "pop"), (2, .36, "pop"), (2, .52, "pop"), (2, .68, "pop"), (3, .40, "ding"), (3, .40, "poof"),
       (4, .15, "pop"), (4, .42, "scribble"), (4, .50, "whoosh"), (5, .15, "pop"), (5, .25, "pop"), (5, .35, "pop"), (5, .62, "stamp"), (5, .90, "ding"),
       (6, .20, "pop"), (6, .68, "tick"), (6, .82, "click"), (6, .84, "whoosh"), (6, .86, "boom"),
       (7, .30, "pop"), (7, .45, "coin"), (7, .78, "ding"), (8, .28, "scribble"), (8, .40, "pop"), (8, .78, "ding"), (8, .85, "shimmer"),
       (9, .12, "pop"), (9, .55, "click"), (9, .56, "ding"), (9, .70, "pop")]


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
                    "-af", "alimiter=limit=0.74:level=disabled", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    wav = build_audio()
    out = p("wb02_reel.mp4")
    render_parallel(TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
