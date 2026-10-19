"""EP05: Tomorrow's News, Part 2 (FINAL): "The Man in the Grey Coat"   (slow, explanatory cut, about 7:30, 16:9)

    KOKORO_SPEED=0.92 python tools/tts.py episodes/ep05-grey-coat   # voice (slower than default on purpose)
    python tools/preview.py episodes/ep05-grey-coat                 # contact sheet of key frames first
    python episodes/ep05-grey-coat/episode.py                       # clean audio + render + thumbnail

Structure: 20 s hook → recap (PREVIOUSLY) → title card → story → host explains the twist twice → reveal
→ he saves the driver instead → no crash, no loop → sleep → normal morning → comment question + THE END. Part 1 images are reused from ../ep04-tomorrows-news/img.
"""
import os, random, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import *  # noqa: E402,F401,F403
import engine as E    # noqa: E402

p = lambda *a: os.path.join(HERE, *a)
P1 = lambda *a: os.path.join(HERE, "..", "ep04-tomorrows-news", *a)
random.seed(5)

# ---------------------------------------------------------------- voice + timeline
N = len([l for l in open(p("lines.txt")) if l.strip()])
os.makedirs(p("audio", "clean"), exist_ok=True)
for i in range(1, N + 1):
    src, dst = p("audio", f"l{i}.wav"), p("audio", "clean", f"l{i}.wav")
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        clean_voice(src, dst)

# 0-based line index -> pause after it. Default is slow (0.6 s); action lines are tight, reveals linger.
GAPS = [0.6] * N
for i, g in {0: 0.5, 3: 0.7, 4: 1.3, 14: 3.2, 19: 0.9, 22: 0.5, 23: 0.3, 24: 0.3, 25: 0.15, 26: 0.15, 27: 0.1,
             28: 0.1, 29: 0.1, 30: 0.5, 31: 1.8, 34: 0.8, 35: 0.8, 36: 0.9, 39: 0.9, 41: 0.7, 42: 0.8, 44: 0.9,
             46: 1.2, 50: 0.9, 55: 1.0, 59: 0.7, 62: 1.0, 64: 0.8, 67: 1.0, 70: 1.0, 72: 1.4, 73: 0.7, 74: 0.9,
             76: 0.6, 77: 1.2, 79: 0.7, 80: 0.9, 82: 0.6, 83: 0.4, 84: 0.6, 86: 1.0, 87: 0.7, 90: 0.9, 92: 0.7,
             93: 1.4, 95: 1.6, 98: 0.8, 99: 1.0, 100: 3.5}.items():
    GAPS[i] = g
TL = Timeline([p("audio", "clean", f"l{i}.wav") for i in range(1, N + 1)], GAPS)
L, END, TOTAL = TL.L, TL.end, TL.total


def seg(t, i, j=None):
    j = i if j is None else j
    return clamp01((t - L(i)) / (L(j + 1) - L(i)))


# ---------------------------------------------------------------- art
def img(name, part1=False):
    path = P1("img", name + ".jpg") if part1 else p("img", name + ".jpg")
    if os.path.exists(path):
        return load_bg(path)
    ph = Image.new("RGB", (2304, 1296), (30, 34, 48))                 # placeholder until the art exists
    ImageDraw.Draw(ph).text((1152, 648), f"[{name}]", font=font(120), fill=(120, 130, 160), anchor="mm")
    return ph


IMG = {n: img(n, part1=True) for n in ["coldopen", "bedroom", "rain", "lottery", "bus", "fire", "stranger",
                                       "livingroom", "reveal"]}
_br = Image.open(P1("img", "bridge.jpg")).convert("RGB")
text_on(_br, (410, 196), "BRIDGE RD", 52, fill=(255, 255, 255))
IMG["bridge"] = _br.resize((2304, round(2304 * _br.height / _br.width)), Image.LANCZOS)
for n in ["bridge_6pm", "girl", "truck", "push", "aftermath", "hat_phone", "wall", "old_hero", "coat", "overlook",
          "diner", "knock", "truck_stops", "sleep", "morning"]:
    IMG[n] = img(n)
HOST = key_green(os.path.join(E.ROOT, "assets", "characters", "host_glasses_green.png"))
HOST = HOST.resize((round(HOST.width * 900 / HOST.height), 900), Image.LANCZOS)
_blur = {}


def blur_of(key, im, cx=0.5, cy=0.5, z=1.2):
    if key not in _blur:
        _blur[key] = blurred(cam(im, cx, cy, z))
    return _blur[key].copy()


def previously(f):
    d = ImageDraw.Draw(f)
    d.rounded_rectangle((40, 36, 330, 96), 12, fill=(0, 0, 0, 170))
    d.text((185, 66), "PREVIOUSLY", font=font(40), fill=YELLOW, anchor="mm")


def black():
    return Image.new("RGBA", (W, H), (0, 0, 0, 255))


# ---------------------------------------------------------------- copy
CRASH = "Local man in fatal crash on Bridge Road"
DAY1 = ["Local team wins 4-1", "Heavy rain at 3 PM", "Corner bakery closes for good"]
SENT = ["Local team wins 4-1", "Heavy rain at 3 PM", "Record $48M jackpot: one winner", "Who is the mystery winner?",
        "Bus crash on Bridge Road: 40 injured", "Fire on Bridge Road", "Local man in fatal crash on Bridge Road",
        "Go to Bridge Road. Trust me."]
RULES2 = ["SEND TOMORROW'S NEWS", "ONLY WHAT KEEPS HIM ALIVE", "NEVER MISS A SINGLE DAY"]
LAST_MSG = "Go to Bridge Road. Trust me. I've done this before."
RECAP = [("coldopen", 0.6), ("bedroom", 0.62), ("rain", 0.5), ("lottery", 0.6), ("bus", 0.5), ("fire", 0.5),
         ("stranger", 0.5), ("coldopen", 0.6), ("livingroom", 0.4), ("bridge", 0.5)]          # lines 5..14


def hud_state(t):
    hidden = [(0, 15), (31, 32), (42, 45), (51, 56), (73, 74), (94, N + 1)]
    if any(L(a) <= t < L(b) for a, b in hidden):
        return None
    if t < L(31):
        return ("DAY", 147), ("TIME", "6:00 PM"), (6, -9)
    if t < L(47):
        return ("DAY", 147), ("TIME", "6:01 PM"), (6, -9)
    if t < L(51):
        return ("DAY", 148), ("MESSAGES SENT", 0), (7, L(47))
    if t < L(63):
        u = ease(seg(t, 56, 62))
        return ("DAY", round(148 + 260 * u)), ("MESSAGES SENT", round(260 * u)), (8, L(56))
    if t < L(65):
        u = ease(seg(t, 63, 64))
        return ("YEAR", max(1, round(20 * u))), ("MESSAGES SENT", round(260 + 7040 * u)), (10, L(63))
    if t < L(74):
        return ("YEAR", 20), ("MESSAGES SENT", 7306), (11, L(65))
    if t < L(81):
        return ("YEAR", 20), ("TIME", "5:40 PM"), (12, L(74))
    if t < L(87):
        return ("YEAR", 20), ("TIME", "5:51 PM"), (12, -9)
    return ("YEAR", 20), ("TIME", "6:00 PM"), (12, -9)


# ---------------------------------------------------------------- shots
def frame_at(t):
    if t < L(5):                                                        # HOOK
        shots = [("overlook", 0.3, 0.45), ("push", 0.45, 0.5), ("stranger", 0.5, 0.42), ("old_hero", 0.5, 0.42),
                 ("reveal", 0.48, 0.38)]
        k = next(i for i in range(5) if t < L(i + 1))
        name, cx, cy = shots[k]
        f = cam(IMG[name], cx, cy, 1.05 + 0.25 * ease(seg(t, k)))
        if k == 1:
            f = grade(f, 0.75, 0.95)
        if t > END(4) + 0.5:
            f = black()

    elif t < L(15):                                                     # RECAP + title card
        k = next(i for i in range(5, 15) if t < L(i + 1))
        name, cx = RECAP[k - 5]
        f = cam(IMG[name], cx, 0.5, 1.05 + 0.1 * seg(t, k))
        if k < 14:
            f = grade(f, 0.55, 0.9)
        if k == 6:
            place_phone(f, news_phone("TOMORROW", DAY1, 3, highlight="date"), t, L(6) + 0.3)
        if k == 12:
            place_phone(f, news_phone("TOMORROW · 6:00 PM", [CRASH], 1, breaking=True), t, L(12) + 0.3)
        if k == 13:
            f = blurred(f, 10, 0.55)
            typed = clamp01((t - L(13) - 3.6) / 1.6)
            place_phone(f, message_phone("ME", "MY NUMBER", "Go to Bridge Road. Trust me.", typed, 1, t=t), t, L(13),
                        x=680, y=60)
        if t >= END(14) + 0.25:
            f = black()
            a = clamp01((t - END(14) - 0.4) / 0.5) * clamp01((L(15) - t) / 0.4)
            big_title(f, "PART 2", "THE MAN IN THE GREY COAT", a)
        else:
            previously(f)

    elif t < L(20):                                                     # 6 PM on Bridge Road
        u = seg(t, 15, 19)
        f = cam(IMG["bridge_6pm"], lerp(0.45, 0.58, u), 0.5, 1.0 + 0.25 * ease(u))
        if t >= L(17):
            place_phone(f, news_phone("TODAY · 6:00 PM", [CRASH], 1, breaking=True, highlight="date"), t, L(17) + 0.4,
                        x=140)

    elif t < L(23):                                                     # the girl
        f = cam(IMG["girl"], 0.5, 0.5, 1.0 + 0.2 * ease(seg(t, 20, 22)))

    elif t < L(25):                                                     # the truck
        u = seg(t, 23, 24)
        f = cam(IMG["truck"], 0.5, 0.5, 1.0 + 0.35 * ease(u), shake=4 * u)

    elif t < L(27):                                                     # you run
        f = cam(IMG["girl"], lerp(0.45, 0.55, seg(t, 25, 26)), 0.5, 1.25 + 0.2 * seg(t, 25, 26), shake=10)

    elif t < L(28):                                                     # headlights
        u = seg(t, 27)
        f = grade(cam(IMG["truck"], 0.5, 0.45, 1.35 + 0.4 * ease(u), shake=8), 1.0, 1 + 1.2 * u ** 3)

    elif t < L(31):                                                     # the push
        u = seg(t, 28, 30)
        hit = L(30) + 1.3
        shake = 22 * max(0.0, 1 - abs(t - L(28) - 0.3) / 0.6) + (26 * max(0.0, 1 - (t - hit) / 0.7) if t > hit else 0)
        f = cam(IMG["push"], lerp(0.45, 0.55, u), 0.5, 1.1 + 0.15 * u, shake=shake)
        if hit < t < hit + 0.12:
            f = Image.new("RGBA", (W, H), (255, 255, 255, 255))

    elif t < L(32):                                                     # silence
        f = black()

    elif t < L(36):                                                     # aftermath, the hat
        hz = ease(clamp01(seg(t, 35) * 1.6))
        z = 1.0 + 0.1 * ease(seg(t, 32, 34)) + 0.6 * hz
        f = cam(IMG["aftermath"], lerp(0.5, 0.32, hz), lerp(0.5, 0.85, hz), z)

    elif t < L(37):                                                     # phone inside the hat
        f = cam(IMG["hat_phone"], 0.5, 0.5, 1.0 + 0.25 * seg(t, 36))

    elif t < L(42):                                                     # the sent messages
        f = blur_of("hat", IMG["hat_phone"])
        shown = 0.6 if t < L(38) else 0.6 + 6.4 * ease(seg(t, 38))
        place_phone(f, sent_phone("+1 (555) 014-2387  ·  ME", SENT[:7], shown), t, L(37) - 0.2, x=260, y=40)
        if L(39) <= t:
            float_text(f, t, L(39) + 0.1, "YOUR NUMBER.", (1340, 540), color=YELLOW, size=130, rise=0, life=2.0)

    elif t < L(45):                                                     # host explains the twist
        f = blur_of("hat", IMG["hat_phone"])
        host_in(f, HOST, t, L(42))
        card(f, t, L(42) + 0.5, ["NOT MAGIC", "IT CAME FROM THIS PHONE"], [L(43) + 0.4, L(44) + 1.0], w=860)

    elif t < L(47):                                                     # the unsent draft
        f = blur_of("hat", IMG["hat_phone"])
        draft = "Your turn." if t >= L(45) + 1.6 else ""
        place_phone(f, sent_phone("+1 (555) 014-2387  ·  ME", SENT[:7], 7, draft), t, L(45) - 0.2, x=260, y=40)
        if t >= L(46):
            float_text(f, t, L(46) + 0.6, "YOUR TURN.", (1340, 540), color=RED, size=170, rise=0, life=2.4)

    elif t < L(51):                                                     # the SEND button
        u = seg(t, 47, 50)
        f = cam(IMG["bedroom"], lerp(0.5, 0.62, ease(u)), lerp(0.5, 0.4, ease(u)), 1.0 + 0.4 * ease(u))
        if t >= L(48):
            place_phone(f, send_phone(t), t, L(48) + 0.3)

    elif t < L(56):                                                     # new rules (host)
        f = blur_of("bed", IMG["bedroom"], 0.62, 0.4, 1.4)
        host_in(f, HOST, t, L(51))
        card(f, t, L(51) + 0.6, RULES2, [L(52), L(53), L(54)], w=860)
        if t >= L(55):
            float_text(f, t, L(55) + 1.8, "NO WARNINGS = NO YOU", (1480, 800), color=RED, size=80, rise=0, life=4.0)

    elif t < L(60):                                                     # the wall
        u = seg(t, 56, 59)
        f = cam(IMG["wall"], lerp(0.4, 0.6, u), 0.5, 1.05 + 0.25 * ease(u))
        for k, (hl, dt) in enumerate([("BRIDGE CLOSED", 0.3), ("FLOOD ON 5TH", 1.3), ("GAS LEAK", 2.3)]):
            float_text(f, t, L(58) + dt, hl, (500 + 450 * k, 820 - 60 * k), color=PAPER, size=64, life=1.6)

    elif t < L(63):                                                     # he was protecting you
        u = seg(t, 60, 62)
        f = grade(cam(IMG["stranger"], 0.5, lerp(0.5, 0.4, ease(u)), 1.0 + 0.8 * ease(u)), 0.6 + 0.6 * u, 1.0)

    elif t < L(65):                                                     # the years
        u = seg(t, 63, 64)
        name = "wall" if int(u * 6) % 2 == 0 else "old_hero"
        f = cam(IMG[name], 0.5, 0.5, 1.15)
        for k, (lab, dt) in enumerate([("YEAR 1", 0.0), ("YEAR 5", 1.0), ("YEAR 20", 2.0)]):
            float_text(f, t, L(63) + dt, lab, (1480, 880), color=YELLOW, size=140, rise=40, life=1.1)

    elif t < L(68):                                                     # the headline, 20 years later
        u = seg(t, 65, 67)
        f = cam(IMG["old_hero"], 0.6, 0.45, 1.0 + 0.3 * ease(u))
        place_phone(f, news_phone("TOMORROW · 6:00 PM", [CRASH], 1, breaking=True, highlight="date"), t, L(66) - 0.1)

    elif t < L(69):                                                     # the coat
        f = cam(IMG["coat"], 0.5, 0.45, 1.0 + 0.2 * ease(seg(t, 68)))

    elif t < L(71):                                                     # sending the last message
        f = blur_of("coat", IMG["coat"], 0.5, 0.45, 1.2)
        typing = clamp01((t - L(70)) / (END(70) - L(70)))
        if t < END(70) + 0.3:
            ph = sent_phone("ME (21 YEARS AGO)", SENT[:7], 7, LAST_MSG[: int(len(LAST_MSG) * typing)][-26:], cracked=False)
        else:
            ph = sent_phone("ME (21 YEARS AGO)", SENT, 7 + clamp01((t - END(70) - 0.3) / 0.3), cracked=False)
        place_phone(f, ph, t, L(69) + 0.6, x=680, y=40)

    elif t < L(73):                                                     # the reveal, said out loud
        u = seg(t, 71, 72)
        f = cam(IMG["reveal"], 0.48, 0.38, 1.0 + 0.35 * ease(u))
        if t >= L(72):
            float_text(f, t, L(72) + 0.2, "IT WAS YOU.", (1400, 760), color=YELLOW, size=150, rise=0, life=3.2)

    elif t < L(74):                                                     # younger self gets the message
        f = blur_of("living", IMG["livingroom"], 0.4, 0.5, 1.2)
        place_phone(f, message_phone("ME", "MY NUMBER", LAST_MSG, 1, 1, t=t), t, L(73) - 0.2, x=680, y=60)

    elif t < L(75):                                                     # how it always ends
        f = grade(cam(IMG["push"], 0.5, 0.5, 1.15 + 0.1 * seg(t, 74)), 0.3, 0.7)

    elif t < L(78):                                                     # the wall: nobody saved the driver
        u = seg(t, 75, 77)
        f = cam(IMG["wall"], lerp(0.45, 0.6, u), lerp(0.5, 0.45, u), 1.05 + 0.3 * ease(u))
        if t >= L(77):
            float_text(f, t, L(77) + 0.9, "THE DRIVER.", (1300, 820), color=RED, size=150, rise=0, life=3.0)

    elif t < L(79):                                                     # the diner
        f = cam(IMG["diner"], 0.45, 0.5, 1.0 + 0.1 * seg(t, 78))

    elif t < L(80):                                                     # where he falls asleep
        f = cam(IMG["truck"], 0.62, 0.32, 1.4 + 0.3 * ease(seg(t, 79)))

    elif t < L(81):                                                     # you go to the diner
        f = cam(IMG["coat"], lerp(0.45, 0.55, seg(t, 80)), 0.45, 1.15)

    elif t < L(83):                                                     # 5:51 at the diner
        u = seg(t, 81, 82)
        f = cam(IMG["diner"], lerp(0.5, 0.62, u), lerp(0.5, 0.56, u), 1.0 + 0.5 * ease(u))

    elif t < L(87):                                                     # the knock
        knock = L(83) + 0.5
        shake = 14 * max(0.0, 1 - (t - knock) / 0.4) if t > knock else 0
        u = seg(t, 83, 86)
        f = cam(IMG["knock"], lerp(0.5, 0.6, u), 0.45, 1.05 + 0.2 * ease(u), shake=shake)

    elif t < L(94):                                                     # 6 PM: the truck stops
        u = seg(t, 87, 93)
        if t < L(92):
            f = cam(IMG["truck_stops"], 0.55, 0.5, 1.0 + 0.15 * ease(seg(t, 87, 91)))
        else:
            f = cam(IMG["truck_stops"], lerp(0.55, 0.25, ease(seg(t, 92))), 0.5, 1.15 + 0.35 * ease(seg(t, 92)))
        if t >= L(93):
            stamp(f, t, L(93) + 2.0, "LOOP CLOSED", (1340, 540), color=(40, 170, 80))

    elif t < L(96):                                                     # you sleep
        f = cam(IMG["sleep"], 0.55, 0.5, 1.0 + 0.2 * ease(seg(t, 94, 95)))

    elif t < L(100):                                                    # a normal morning
        u = seg(t, 96, 99)
        f = cam(IMG["morning"], lerp(0.5, 0.62, u), 0.45, 1.0 + 0.2 * ease(u))
        if t >= L(96) + 1.0:
            place_phone(f, news_phone("TODAY", ["Sunny all day", "Corner bakery reopens"], 2, highlight="date"), t,
                        L(96) + 1.4, x=140, out_at=L(98) + 0.4)

    else:                                                               # comment question + end card
        f = black()
        big_title(f, "THE END", "WHAT WOULD YOU DO WITH TOMORROW'S NEWS?", clamp01((t - L(100)) / 0.5))

    st = hud_state(t)
    if st:
        hud(f, t, *st)
    return f


# ---------------------------------------------------------------- sound
def build_audio():
    n = int(TOTAL * SR)
    tt = np.arange(n) / SR
    voice = TL.voice_track()
    music = music_bed(TOTAL, [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63],
                              [196.0, 246.94, 293.66], [164.81, 207.65, 246.94]], 4.5, 0.06)
    gain = np.ones(n, np.float32)
    gain *= 1 - 0.85 * ((tt > END(14)) & (tt < L(15)))                                # title card: near silence
    gain *= np.where((tt > L(23)) & (tt < L(32) + 1.0), 0.0, 1.0)                     # action: only sfx
    gain *= np.where((tt > L(87)) & (tt < L(91)), 0.15, 1.0)                        # 6 PM: hold your breath
    gain *= np.clip((END(100) + 2.5 - tt) / 1.5, 0, 1)                                 # fade out under THE END
    music *= np.convolve(gain, np.ones(4800) / 4800, "same")
    fx = np.zeros(n, np.float32)
    ping, pop = sfx("ping"), sfx("pop")
    place(fx, sfx("whoosh"), END(4) + 0.3)
    for at in [L(6) + 0.3, L(12) + 0.3, L(17) + 0.4, L(66) - 0.1]:
        place(fx, ping, at)
    place(fx, sfx("buzz"), L(13))
    place(fx, sfx("boom"), END(14) + 0.4)
    place(fx, sfx("screech"), L(23) + 0.5)
    place(fx, sfx("screech"), L(27))
    place(fx, sfx("whoosh"), L(28))
    place(fx, sfx("boom") * 1.3, L(30) + 1.3)
    for k in range(7):
        place(fx, ping * 0.3, L(38) + 0.35 * k)
    place(fx, sfx("boom") * 0.7, L(39) + 0.1)
    for at in [L(42) + 0.5, L(43) + 0.4, L(44) + 1.0, L(51) + 0.6, L(52), L(53), L(54)]:
        place(fx, pop, at)
    place(fx, sfx("boom"), L(46) + 0.6)
    for k in range(3):
        place(fx, sfx("pop"), L(58) + [0.3, 1.3, 2.3][k])
        place(fx, sfx("whoosh") * 0.5, L(63) + 1.0 * k)
    for k in range(int((END(70) - L(70)) / 0.12)):                                   # typing clicks
        place(fx, sfx("tick") * 0.6, L(70) + 0.12 * k)
    place(fx, sfx("ping") * 0.8, END(70) + 0.3)
    place(fx, sfx("boom"), L(72) + 0.2)
    place(fx, ping, L(73) - 0.2)
    place(fx, sfx("boom") * 0.6, L(77) + 0.9)
    for k in range(2):                                                                # knock knock
        place(fx, sfx("boom")[: int(0.25 * SR)] * 0.6, L(83) + 0.5 + 0.22 * k)
    for k in range(int(L(91) - L(87))):                                               # the clock at 6 PM
        place(fx, sfx("tick"), L(87) + k)
    place(fx, sfx("pop") * 1.4, L(93) + 2.0)
    place(fx, ping, L(96) + 1.4)
    finish_audio(voice, music, fx, p("mix.wav"), HERE)


# ---------------------------------------------------------------- thumbnail
THUMB_TEXT = [("HE WAS", "ME ALL ALONG", "thumbnail.jpg"), ("THIS IS", "HOW IT ENDS", "thumbnail_b.jpg")]


def thumbnail():
    src = p("img", "thumb_base.png") if os.path.exists(p("img", "thumb_base.png")) else P1("img", "thumb_base.png")
    for small, big, name in THUMB_TEXT:
        base = Image.open(src).convert("RGB").resize((1280, 720), Image.LANCZOS).convert("RGBA")
        d = ImageDraw.Draw(base)
        size = 120
        while d.textlength(big, font=font(size)) > 600:
            size -= 4
        d.text((1255, 34), small, font=font(76), fill=PAPER, anchor="ra", stroke_width=6, stroke_fill=(0, 0, 0))
        d.text((1255, 112), big, font=font(size), fill=YELLOW, anchor="ra", stroke_width=7, stroke_fill=(0, 0, 0))
        d.rounded_rectangle((1060, 640, 1255, 700), 10, fill=RED)
        d.text((1157, 670), "FINALE", font=font(44), fill=PAPER, anchor="mm")
        base.convert("RGB").save(p(name), quality=92)


if __name__ == "__main__":
    print(f"timeline {TOTAL:.1f}s, {N} lines")
    thumbnail()
    build_audio()
    render(frame_at, TOTAL, p("mix.wav"), p("grey_coat_part2.mp4"))
    os.remove(p("mix.wav"))
    print("done", p("grey_coat_part2.mp4"))
