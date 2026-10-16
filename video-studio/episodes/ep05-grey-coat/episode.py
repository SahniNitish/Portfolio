"""EP05: Tomorrow's News, Part 2: "The Man in the Grey Coat"   (about 3:45, 16:9)

    python tools/tts.py episodes/ep05-grey-coat           # voice
    python episodes/ep05-grey-coat/episode.py             # clean audio + render + thumbnail
    python tools/preview.py episodes/ep05-grey-coat       # (optional) contact sheet of key frames first

Images from Part 1 are reused from ../ep04-tomorrows-news/img. Any image missing from img/ renders as a
labelled placeholder, so timing can be checked before the art exists.
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

GAPS = [0.45] * N
for i, g in {6: 0.5, 7: 3.2, 11: 0.6, 15: 0.2, 16: 0.15, 17: 0.1, 18: 0.1, 19: 0.3, 20: 1.6, 23: 0.5, 24: 0.6,
             29: 0.4, 30: 1.0, 33: 0.6, 37: 0.6, 41: 0.5, 43: 0.8, 45: 0.6, 47: 0.7, 49: 0.5, 51: 0.8, 55: 1.2,
             56: 0.4, 58: 0.6, 59: 3.4}.items():
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


IMG = {n: img(n, part1=True) for n in ["coldopen", "bedroom", "lottery", "bus", "fire", "stranger", "livingroom"]}
_br = Image.open(P1("img", "bridge.jpg")).convert("RGB")
text_on(_br, (410, 196), "BRIDGE RD", 52, fill=(255, 255, 255))
IMG["bridge"] = _br.resize((2304, round(2304 * _br.height / _br.width)), Image.LANCZOS)
for n in ["bridge_6pm", "girl", "truck", "push", "aftermath", "hat_phone", "wall", "old_hero", "coat", "overlook",
          "two_coats"]:
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


# ---------------------------------------------------------------- copy
CRASH = "Local man in fatal crash on Bridge Road"
SENT = ["Local team wins 4-1", "Heavy rain at 3 PM", "Record $48M jackpot: one winner", "Who is the mystery winner?",
        "Bus crash on Bridge Road: 40 injured", "Fire on Bridge Road", "Local man in fatal crash on Bridge Road",
        "Go to Bridge Road. Trust me."]
RULES2 = ["SEND TOMORROW'S NEWS", "ONLY WHAT KEEPS HIM ALIVE", "MISS ONE DAY: IT ALL BREAKS"]
LAST_MSG = "Go to Bridge Road. Trust me. I've done this before."


def hud_state(t):
    if t < L(8) or L(20) <= t < L(21) or L(34) <= t < L(38) or t >= END(59) + 0.6:
        return None
    if t < L(21):
        return ("DAY", 147), ("TIME", "6:00 PM"), (6, -9)
    if t < L(31):
        return ("DAY", 147), ("TIME", "6:01 PM"), (6, -9)
    if t < L(34):
        return ("DAY", 148), ("MESSAGES SENT", 0), (7, L(31))
    if t < L(44):
        u = ease(seg(t, 38, 43))
        return ("DAY", round(148 + 260 * u)), ("MESSAGES SENT", round(260 * u)), (8, L(38))
    if t < L(46):
        u = ease(seg(t, 44, 45))
        return ("YEAR", max(1, round(20 * u))), ("MESSAGES SENT", round(260 + 7040 * u)), (10, L(44))
    if t < L(52):
        return ("YEAR", 20), ("MESSAGES SENT", 7305), (11, L(46))
    return ("YEAR", 20), ("TIME", "5:59 PM"), (12, L(52))


# ---------------------------------------------------------------- shots
def frame_at(t):
    if t < L(8):                                                        # recap
        shots = [("coldopen", 0.6), ("lottery", 0.6), ("bus", 0.5), ("fire", 0.5), ("stranger", 0.5),
                 ("coldopen", 0.6), ("livingroom", 0.4), ("bridge", 0.5)]
        k = next(i for i in range(8) if t < L(i + 1))
        name, cx = shots[k]
        f = cam(IMG[name], cx, 0.5, 1.05 + 0.1 * seg(t, k))
        if k < 7:
            f = grade(f, 0.55, 0.9)
        if k == 5:
            place_phone(f, news_phone("TOMORROW · 6:00 PM", [CRASH], 1, breaking=True), t, L(5) + 0.2)
        if k == 6:
            f = blurred(f, 10, 0.55)
            typed = clamp01((t - L(6) - 2.2) / 1.6)
            place_phone(f, message_phone("ME", "MY NUMBER", "Go to Bridge Road. Trust me.", typed, 1, t=t), t, L(6),
                        x=680, y=60)
        if t >= END(7) + 0.25:                                          # title card
            f = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            a = clamp01((t - END(7) - 0.4) / 0.5) * clamp01((L(8) - t) / 0.4)
            big_title(f, "PART 2", "THE MAN IN THE GREY COAT", a)
        else:
            previously(f)

    elif t < L(12):                                                     # 6 PM on Bridge Road
        u = seg(t, 8, 11)
        f = cam(IMG["bridge_6pm"], lerp(0.45, 0.58, u), 0.5, 1.0 + 0.25 * ease(u))
        if t >= L(10):
            place_phone(f, news_phone("TODAY · 6:00 PM", [CRASH], 1, breaking=True, highlight="date"), t, L(10) + 0.4,
                        x=140)                                          # hero stands on the right here

    elif t < L(13):                                                     # the girl
        f = cam(IMG["girl"], 0.5, 0.5, 1.0 + 0.12 * seg(t, 12))

    elif t < L(15):                                                     # the truck
        u = seg(t, 13, 14)
        f = cam(IMG["truck"], 0.5, 0.5, 1.0 + 0.35 * ease(u), shake=4 * u)

    elif t < L(16):                                                     # you run
        f = cam(IMG["girl"], lerp(0.45, 0.55, seg(t, 15)), 0.5, 1.25 + 0.2 * seg(t, 15), shake=10)

    elif t < L(17):                                                     # headlights
        u = seg(t, 16)
        f = grade(cam(IMG["truck"], 0.5, 0.45, 1.35 + 0.4 * ease(u), shake=8), 1.0, 1 + 1.2 * u ** 3)

    elif t < L(20):                                                     # the push
        u = seg(t, 17, 19)
        hit = L(19) + 0.9
        shake = 22 * max(0.0, 1 - abs(t - L(17) - 0.2) / 0.6) + (26 * max(0.0, 1 - (t - hit) / 0.7) if t > hit else 0)
        f = cam(IMG["push"], lerp(0.45, 0.55, u), 0.5, 1.1 + 0.15 * u, shake=shake)
        if hit < t < hit + 0.12:
            f = Image.new("RGBA", (W, H), (255, 255, 255, 255))

    elif t < L(21):                                                     # silence
        f = Image.new("RGBA", (W, H), (0, 0, 0, 255))

    elif t < L(24):                                                     # aftermath, the hat
        u = seg(t, 21, 23)
        z = 1.0 + 0.1 * ease(seg(t, 21, 22)) + 0.5 * ease(seg(t, 23))
        f = cam(IMG["aftermath"], 0.5, lerp(0.5, 0.7, ease(seg(t, 23))), z)

    elif t < L(25):                                                     # phone inside the hat
        f = cam(IMG["hat_phone"], 0.5, 0.5, 1.0 + 0.2 * seg(t, 24))

    elif t < L(31):                                                     # the sent messages
        f = blur_of("hat", IMG["hat_phone"])
        if t < L(26):
            shown = 0.6
        elif t < L(27):
            shown = 0.6 + 6.4 * ease(seg(t, 26))
        else:
            shown = 7
        draft = "Your turn." if t >= L(29) + 0.8 else ""
        ph = sent_phone("+1 (555) 014-2387  ·  ME", SENT[:7], shown, draft)
        place_phone(f, ph, t, L(25) - 0.2, x=260, y=40)
        if t >= L(30):
            float_text(f, t, L(30) + 0.1, "YOUR TURN.", (1340, 540), color=RED, size=170, rise=0, life=1.6)

    elif t < L(34):                                                     # the SEND button
        u = seg(t, 31, 33)
        f = cam(IMG["bedroom"], lerp(0.5, 0.62, ease(u)), lerp(0.5, 0.4, ease(u)), 1.0 + 0.4 * ease(u))
        if t >= L(32):
            place_phone(f, send_phone(t), t, L(32) + 0.3)

    elif t < L(38):                                                     # new rules (host)
        f = blur_of("bed", IMG["bedroom"], 0.62, 0.4, 1.4)
        host_in(f, HOST, t, L(34))
        card(f, t, L(34) + 0.5, RULES2, [L(35), L(36), L(37)], w=840)

    elif t < L(42):                                                     # the wall
        u = seg(t, 38, 41)
        f = cam(IMG["wall"], lerp(0.4, 0.6, u), 0.5, 1.05 + 0.25 * ease(u))
        for k, (hl, dt) in enumerate([("BRIDGE CLOSED", 0.2), ("FLOOD ON 5TH", 0.9), ("GAS LEAK", 1.6)]):
            float_text(f, t, L(40) + dt, hl, (500 + 450 * k, 820 - 60 * k), color=PAPER, size=64, life=1.4)

    elif t < L(44):                                                     # he was protecting you
        u = seg(t, 42, 43)
        f = grade(cam(IMG["stranger"], 0.5, lerp(0.5, 0.4, ease(u)), 1.0 + 0.8 * ease(u)), 0.6 + 0.6 * u, 1.0)

    elif t < L(46):                                                     # the years
        u = seg(t, 44, 45)
        name = "wall" if int(u * 6) % 2 == 0 else "old_hero"
        f = rgb_split(cam(IMG[name], 0.5, 0.5, 1.15), 6, scan=False) if int(u * 24) % 4 == 0 else cam(IMG[name], 0.5, 0.5, 1.15)
        for k, (lab, dt) in enumerate([("YEAR 1", 0.0), ("YEAR 5", 0.9), ("YEAR 20", 1.8)]):
            float_text(f, t, L(44) + dt, lab, (960, 560), color=YELLOW, size=140, rise=40, life=1.0)

    elif t < L(48):                                                     # the headline, 20 years later
        u = seg(t, 46, 47)
        f = cam(IMG["old_hero"], 0.6, 0.45, 1.0 + 0.3 * ease(u))
        place_phone(f, news_phone("TOMORROW · 6:00 PM", [CRASH], 1, breaking=True, highlight="date"), t, L(47) - 0.1)

    elif t < L(50):                                                     # the coat
        u = seg(t, 48, 49)
        f = cam(IMG["coat"], 0.5, 0.45, 1.0 + 0.2 * ease(u))

    elif t < L(52):                                                     # sending the last message
        f = blur_of("coat", IMG["coat"], 0.5, 0.45, 1.2)
        typing = clamp01((t - L(51)) / (END(51) - L(51)))
        if t < END(51) + 0.3:
            ph = sent_phone("ME (21 YEARS AGO)", SENT[:7], 7, LAST_MSG[: int(len(LAST_MSG) * typing)][-26:], cracked=False)
        else:
            ph = sent_phone("ME (21 YEARS AGO)", SENT, 7 + clamp01((t - END(51) - 0.3) / 0.3), cracked=False)
        place_phone(f, ph, t, L(50) + 0.6, x=680, y=40)

    elif t < L(56):                                                     # on the bridge, watching yourself
        u = seg(t, 52, 55)
        f = cam(IMG["overlook"], lerp(0.4, 0.55, u), 0.5, 1.0 + 0.3 * ease(u))

    elif t < END(59) + 0.6:                                             # two of us
        u = seg(t, 56, 59)
        f = cam(IMG["two_coats"], 0.5, 0.5, 1.0 + 0.15 * u)
        if t >= L(56) + 0.2:
            f = blurred(f, 6, 0.7) if t > L(57) else f
            typed = clamp01((t - L(59)) / 1.2)
            place_phone(f, message_phone("ME", "MY NUMBER", "There are two of us.", typed, 1, t=t), t, L(56) + 0.3,
                        x=680, y=60, wobble=2 * math.sin(t * 40) if t < L(56) + 1.2 else 0)

    else:                                                               # end card
        f = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        big_title(f, "TO BE CONTINUED", "PART 3 SOON", clamp01((t - END(59) - 1.2) / 0.5))

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
                              [196.0, 246.94, 293.66], [164.81, 207.65, 246.94]], 4.0, 0.06)
    gain = np.ones(n, np.float32)
    gain *= 1 - 0.85 * ((tt > END(7)) & (tt < L(8)))                                  # title card: near silence
    gain *= np.where((tt > L(13)) & (tt < L(21) + 1.0), 0.0, 1.0)                     # action: no music, only sfx
    gain *= np.clip(1 - (tt - L(56)) / 0.5, 0, 1) + np.clip((tt - END(59) - 0.8) / 1.0, 0, 0.9)
    music *= np.convolve(gain, np.ones(4800) / 4800, "same")
    fx = np.zeros(n, np.float32)
    ping, pop = sfx("ping"), sfx("pop")
    for at in [L(5) + 0.2, L(10) + 0.4, L(47) - 0.1]:
        place(fx, ping, at)
    place(fx, sfx("buzz"), L(6))
    place(fx, sfx("boom"), END(7) + 0.4)
    place(fx, sfx("screech"), L(13) + 0.5)
    place(fx, sfx("screech"), L(16))
    place(fx, sfx("whoosh"), L(17))
    place(fx, sfx("boom") * 1.3, L(19) + 0.9)
    for k in range(7):
        place(fx, ping * 0.3, L(26) + 0.3 * k)
    place(fx, sfx("boom"), L(30) + 0.1)
    for at in [L(34) + 0.5, L(35), L(36), L(37)]:
        place(fx, pop, at)
    for k in range(3):
        place(fx, sfx("pop"), L(40) + [0.2, 0.9, 1.6][k])
        place(fx, sfx("whoosh") * 0.5, L(44) + 0.9 * k)
    for k in range(int((END(51) - L(51)) / 0.12)):                                   # typing clicks
        place(fx, sfx("tick") * 0.6, L(51) + 0.12 * k)
    place(fx, sfx("ping") * 0.8, END(51) + 0.3)
    place(fx, sfx("buzz"), L(56) + 0.2)
    place(fx, sfx("boom") * 1.2, L(59) + 0.4)
    finish_audio(voice, music, fx, p("mix.wav"), HERE)


# ---------------------------------------------------------------- thumbnail
THUMB_TEXT = [("THERE ARE", "TWO OF ME", "thumbnail.jpg"), ("HE WAS", "ME ALL ALONG", "thumbnail_b.jpg")]


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
        d.text((1157, 670), "PART 2", font=font(44), fill=PAPER, anchor="mm")
        base.convert("RGB").save(p(name), quality=92)


if __name__ == "__main__":
    print(f"timeline {TOTAL:.1f}s, {N} lines")
    thumbnail()
    build_audio()
    render(frame_at, TOTAL, p("mix.wav"), p("grey_coat_part2.mp4"))
    os.remove(p("mix.wav"))
    print("done", p("grey_coat_part2.mp4"))
