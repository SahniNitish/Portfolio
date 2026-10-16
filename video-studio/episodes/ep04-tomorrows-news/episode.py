"""EP04: What If Your Phone Showed Tomorrow's News?   (about 2:45, 16:9)

    python tools/tts.py episodes/ep04-tomorrows-news      # voice (ElevenLabs / Kokoro / Piper)
    python episodes/ep04-tomorrows-news/episode.py        # clean audio + render + thumbnail
"""
import os, random, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import *  # noqa: E402,F401,F403
import engine as E    # noqa: E402

p = lambda *a: os.path.join(HERE, *a)
random.seed(4)

# ---------------------------------------------------------------- voice + timeline
N = len([l for l in open(p("lines.txt")) if l.strip()])
os.makedirs(p("audio", "clean"), exist_ok=True)
for i in range(1, N + 1):
    src, dst = p("audio", f"l{i}.wav"), p("audio", "clean", f"l{i}.wav")
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        clean_voice(src, dst)

GAPS = [0.45] * N
for i, g in {1: 0.5, 2: 0.5, 7: 0.6, 11: 0.6, 14: 0.5, 18: 0.5, 19: 0.6, 23: 0.6, 26: 0.6, 28: 0.9,
             30: 0.7, 33: 0.9, 35: 0.9, 36: 0.6, 37: 0.6, 38: 3.2}.items():
    GAPS[i] = g
TL = Timeline([p("audio", "clean", f"l{i}.wav") for i in range(1, N + 1)], GAPS)
L, END, TOTAL = TL.L, TL.end, TL.total


def seg(t, i, j=None):
    """0..1 progress through lines i..j (inclusive), measured start-of-i to start-of-(j+1)."""
    j = i if j is None else j
    return clamp01((t - L(i)) / (L(j + 1) - L(i)))


# ---------------------------------------------------------------- art
def bg_with_text(name, draws):
    im = Image.open(p("img", name)).convert("RGB")
    for xy, txt, size, fill, ang in draws:
        text_on(im, xy, txt, size, fill=fill, angle=ang)
    im.save(p("img", "_" + name), quality=95)
    return load_bg(p("img", "_" + name))


IMG = {n: load_bg(p("img", n + ".jpg")) for n in
       ["coldopen", "bedroom", "rain", "reporters", "bus", "fire", "stranger", "livingroom", "reveal"]}
IMG["lottery"] = bg_with_text("lottery.jpg", [((652, 172), "$48,000,000", 92, (20, 110, 40), 5)])
IMG["bridge"] = bg_with_text("bridge.jpg", [((410, 196), "BRIDGE RD", 52, (255, 255, 255), 0)])
HOST = key_green(os.path.join(E.ROOT, "assets", "characters", "host_glasses_green.png"))
HOST = HOST.resize((round(HOST.width * 900 / HOST.height), 900), Image.LANCZOS)
_blur_cache = {}


def host_bg(key, img, cx, cy, z):
    if key not in _blur_cache:
        _blur_cache[key] = blurred(cam(img, cx, cy, z))
    return _blur_cache[key].copy()


# ---------------------------------------------------------------- copy
CRASH = "Local man in fatal crash on Bridge Road"
DAY1 = ["Local team wins 4-1", "Heavy rain at 3 PM", "Corner bakery closes for good"]
RIPPLE = ["Fire on Bridge Road", "Bridge closed for repairs", "Power out on 5th Street", "Flood warning downtown",
          "Gas leak on Main St", "Train derails outside town", "Hospital at full capacity"]
RULES = ["PHONE SHOWS TOMORROW", "ONLY YOU CAN SEE IT", "CHANGE IT, IT CHANGES"]
MONTAGE = ["reveal", "livingroom", "stranger", "fire", "bus", "reporters", "lottery", "rain", "bedroom"]


def hud_state(t):
    """(left, right, step) for the HUD, or None when the HUD is hidden."""
    if t < L(2):
        return ("DAY", 147), ("HEADLINES CHANGED", 23), (6, -9)
    if t < L(3):
        u = ease(seg(t, 2))
        return ("DAY", round(147 - 146 * u)), ("HEADLINES CHANGED", round(23 * (1 - u))), None
    if t < L(8):
        return ("DAY", 1), ("HEADLINES CHANGED", 0), None
    if t < L(12) or L(19) <= t < L(20):
        return None
    if t < L(15):
        return ("DAY", 3), ("HEADLINES CHANGED", 0), (1, L(12))
    if t < L(19):
        return ("DAY", 30), ("HEADLINES CHANGED", 1 if t > L(17) else 0), (2, L(15))
    if t < L(24):
        return ("DAY", 90), ("HEADLINES CHANGED", 2 if t > L(23) else 1), (3, L(20))
    if t < L(27):
        return ("DAY", 91), ("HEADLINES CHANGED", round(2 + 20 * ease(seg(t, 25)))), (4, L(24))
    if t < L(29):
        return ("DAY", 120), ("HEADLINES CHANGED", 22), (5, L(27))
    if t < L(32):
        return ("DAY", 147), ("HEADLINES CHANGED", 23), (6, L(29))
    if t < L(33):
        return ("DAY", 147), ("TIME", f"{3 + min(int(seg(t, 32) * 3), 2)}:00 PM"), (6, -9)
    if t < L(38):
        return ("DAY", 147), ("TIME", "5:59 PM"), (6, -9)
    return None


# ---------------------------------------------------------------- shots
def frame_at(t):
    if t < L(2):                                                     # cold open
        u = seg(t, 0, 1)
        f = cam(IMG["coldopen"], 0.6, 0.5, 1.0 + 0.25 * ease(u))
        place_phone(f, news_phone("TOMORROW · 6:00 PM", [CRASH], 1, breaking=True), t, L(1) + 0.25)

    elif t < L(3):                                                   # rewind montage
        u = seg(t, 2)
        f = rgb_split(cam(IMG[MONTAGE[min(int(u * len(MONTAGE)), len(MONTAGE) - 1)]], 0.5, 0.5, 1.2))

    elif t < L(8):                                                   # day 1: the glitch
        u = seg(t, 3, 7)
        f = cam(IMG["bedroom"], lerp(0.5, 0.62, ease(u)), lerp(0.5, 0.4, ease(u)), 1.0 + 0.45 * ease(u))
        if t >= L(4):
            shown = 0 if t < L(5) else 3 * clamp01((t - L(5)) / (END(5) - L(5)) * 1.05) + 0.2
            place_phone(f, news_phone("TUESDAY · TOMORROW", DAY1, shown, highlight="date"), t, L(4) + 0.1)
        if L(6) + 1.0 < t < L(6) + 1.35:
            f = rgb_split(f, 22)
        if t >= L(7):
            stamp(f, t, L(7) + 1.6, "IT ALL CAME TRUE", (560, 760))

    elif t < L(12):                                                  # rules (host)
        f = host_bg("bed", IMG["bedroom"], 0.47, 0.4, 1.45)
        host_in(f, HOST, t, L(8))
        card(f, t, L(8) + 0.5, RULES, [L(9), L(10), L(11)])

    elif t < L(15):                                                  # day 3: umbrella + bets
        u = seg(t, 12, 14)
        f = cam(IMG["rain"], 0.5, lerp(0.5, 0.42, ease(u)), 1.0 + 0.35 * ease(u))
        for k in range(3):
            float_text(f, t, L(14) + 0.15 + 0.4 * k, "+$10", (1250 + 170 * k, 560 - 70 * k))

    elif t < L(16):                                                  # day 30: jackpot headline
        f = grade(cam(IMG["lottery"], 0.62, 0.5, 1.1), 0.6, 0.55)
        shown = 1 if t < L(15) + 2.9 else 2
        place_phone(f, news_phone("SATURDAY · TOMORROW", ["Record $48M jackpot: one winner",
                                                          "Winning numbers: 7 · 12 · 19 · 23 · 41"], shown,
                                  breaking=True), t, L(15) + 0.9)

    elif t < L(18):                                                  # winning, then the winner story
        u = seg(t, 16, 17)
        f = cam(IMG["lottery"], 0.6, 0.38, 1.0 + 0.2 * ease(u))
        place_phone(f, news_phone("SUNDAY · TOMORROW", ["Who is the mystery jackpot winner?"], 1,
                                  breaking=True), t, L(17) + 1.0)

    elif t < L(19):                                                  # reporters
        u = seg(t, 18)
        f = cam(IMG["reporters"], 0.52, 0.45, 1.0 + 0.2 * ease(u))
        if random.random() < 0.18:
            f = grade(f, 1.0, 1.6)

    elif t < L(20):                                                  # lesson one (host)
        f = host_bg("rep", IMG["reporters"], 0.52, 0.45, 1.2)
        host_in(f, HOST, t, L(19))
        card(f, t, L(19) + 0.4, ["EVERY CHANGE MAKES NEWS"], [L(19) + 1.1], w=820)

    elif t < L(22):                                                  # day 90: bus headline
        u = seg(t, 20, 21)
        f = cam(IMG["bridge"], lerp(0.45, 0.6, u), 0.5, 1.1)
        place_phone(f, news_phone("FRIDAY · TOMORROW", ["Bus crash on Bridge Road: 40 injured"], 1, breaking=True),
                    t, L(20) + 1.3)

    elif t < L(24):                                                  # stopping the bus
        u = seg(t, 22, 23)
        z = 1.0 + 0.3 * ease(seg(t, 22)) - 0.3 * ease(seg(t, 23))
        stop = L(22) + 2.6
        shake = 18 * max(0.0, 1 - (t - stop) / 0.6) if t > stop else 0
        f = cam(IMG["bus"], 0.5, 0.52, z, shake)
        if t > L(23):
            float_text(f, t, L(23) + 1.2, "NOBODY HURT", (960, 300), color=(120, 230, 120), size=90, life=1.6)

    elif t < L(27):                                                  # the ripple
        u = seg(t, 24, 26)
        f = cam(IMG["fire"], 0.5, 0.48, 1.0 + 0.2 * ease(u))
        if L(26) <= t:
            f = grade(f, 1 - 0.7 * ease(seg(t, 26)), 1 - 0.3 * ease(seg(t, 26)))
        if t < L(25):
            place_phone(f, news_phone("SATURDAY · TOMORROW", [RIPPLE[0]], 1, breaking=True), t, L(24) + 1.6)
        elif t < L(26):
            k = min(int((t - L(25)) / 0.42), len(RIPPLE) - 1)
            place_phone(f, news_phone("TOMORROW", [RIPPLE[k]], 1, breaking=True), t, L(24) + 1.6)
        else:
            place_phone(f, news_phone("TOMORROW", [RIPPLE[-1]], 1, breaking=True), t, L(24) + 1.6, out_at=L(26) + 0.6)

    elif t < L(29):                                                  # the man in the grey coat
        u = seg(t, 27, 28)
        f = grade(cam(IMG["stranger"], 0.5, lerp(0.5, 0.4, ease(u)), 1.0 + 0.7 * ease(u) ** 1.5), 0.8)

    elif t < L(31):                                                  # the headline is you
        u = seg(t, 29, 30)
        f = cam(IMG["coldopen"], 0.6, 0.5, 1.0 + 0.3 * ease(u))
        date_line = "TOMORROW" if t < L(30) + 2.6 else "TOMORROW · 6:00 PM"
        place_phone(f, news_phone(date_line, [CRASH], 1, breaking=True, highlight="date" if t > L(30) + 2.6 else None),
                    t, L(29) + 2.0)

    elif t < L(33):                                                  # staying home
        u = seg(t, 31, 32)
        f = cam(IMG["livingroom"], 0.45, 0.5, 1.0 + 0.15 * ease(u))
        if t >= L(32):
            hr = 3 + min(int(seg(t, 32) * 3), 2)
            place_phone(f, news_phone(f"UPDATED {hr}:00 PM", [CRASH, "Police: 'a matter of hours'"], 1 + (hr > 3),
                                      breaking=True), t, L(32) + 0.2, x=1300, y=170, scale=0.8)

    elif t < L(36):                                                  # 5:59, the message
        u = seg(t, 33, 35)
        shake = 6 if L(33) + 1.5 < t < L(33) + 2.8 else 0
        f = cam(IMG["livingroom"], 0.4, 0.5, 1.0 + 0.5 * ease(seg(t, 33)), shake)
        if t >= L(34):
            f = blurred(f, 10, 0.55)
            mine = t >= L(35)
            ph = message_phone("ME" if mine else "(555) 014-2387", "MY NUMBER" if mine else "MOBILE", "", 0,
                               header_glow=clamp01((t - L(35)) / 0.3) if mine else 0, t=t)
            place_phone(f, ph, t, L(34) + 0.3, x=680, y=60)

    elif t < L(38):                                                  # the message types out, Bridge Road at dusk
        u = seg(t, 36, 37)
        f = cam(IMG["bridge"], lerp(0.35, 0.55, u), 0.5, 1.15 - 0.1 * u)
        typed = clamp01((t - L(36)) / (END(36) - L(36)))
        ph = message_phone("ME", "MY NUMBER", "Go to Bridge Road. Trust me. I've done this before.", typed, 1)
        place_phone(f, ph, t, L(36) - 0.3, out_at=L(37) + 0.3)

    else:                                                            # reveal, then black
        if t < END(38) + 0.9:
            u = clamp01((t - L(38)) / (END(38) + 0.9 - L(38)))
            f = cam(IMG["reveal"], 0.48, 0.38, 1.0 + 0.3 * ease(u))
        else:
            f = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            a = clamp01((t - END(38) - 1.2) / 0.5)
            big_title(f, "TO BE CONTINUED", "PART 2 SOON", a)

    st = hud_state(t)
    if st:
        hud(f, t, *st)
    return f


# ---------------------------------------------------------------- sound
def build_audio():
    n = int(TOTAL * SR)
    voice = TL.voice_track()
    music = music_bed(TOTAL, [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63],
                              [196.0, 246.94, 293.66], [164.81, 207.65, 246.94]], 4.0, 0.06)
    gain = np.ones(n, np.float32)
    tt = np.arange(n) / SR
    gain *= np.clip(1 - (tt - L(33)) / 0.8, 0, 1) + np.clip((tt - L(37)) / 1.5, 0, 0.8)   # silence for the climax
    gain *= np.clip((END(38) + 0.9 - tt) / 0.05, 0, 1)                                    # hard cut to black
    music *= gain
    fx = np.zeros(n, np.float32)
    ping, pop, coin = sfx("ping"), sfx("pop"), sfx("coin")
    for at in [L(1) + 0.25, L(4) + 0.1, L(15) + 0.9, L(15) + 2.9, L(17) + 1.0, L(20) + 1.3, L(24) + 1.6,
               L(29) + 2.0, L(32) + 0.2]:
        place(fx, ping, at)
    for k in range(3):
        place(fx, ping * 0.6, L(5) + (END(5) - L(5)) * k / 3 / 1.05 + 0.05)
        place(fx, coin, L(14) + 0.15 + 0.4 * k)
    for at in [L(8) + 0.5, L(9), L(10), L(11), L(19) + 0.4, L(19) + 1.1]:
        place(fx, pop, at)
    place(fx, sfx("pop") * 1.4, L(7) + 1.6)
    for k in range(int((L(26) - L(25)) / 0.42)):
        place(fx, ping * 0.35, L(25) + 0.42 * k)
    place(fx, sfx("whoosh"), L(2) - 0.1)
    place(fx, sfx("flash"), L(18) + 0.1)
    place(fx, sfx("screech"), L(22) + 1.5)
    place(fx, sfx("boom") * 0.6, L(22) + 2.6)
    for at in [END(1) + 0.05, L(28) + 2.5, L(30) + 0.2, L(35) + 0.1]:
        place(fx, sfx("boom"), at)
    for k in range(int(L(34) - L(31))):                                                  # the clock
        place(fx, sfx("tick"), L(31) + k)
    place(fx, sfx("buzz"), L(33) + 1.5)
    place(fx, sfx("boom") * 1.2, END(38) + 0.9)
    finish_audio(voice, music, fx, p("mix.wav"), HERE)


# ---------------------------------------------------------------- thumbnail
THUMB_TEXT = [("IF YOU KNEW", "THE FUTURE...", "thumbnail.jpg"),
              ("I CAN SEE", "THE FUTURE", "thumbnail_b.jpg"),
              ("I SAW", "TOMORROW", "thumbnail_c.jpg")]


def thumbnail():
    for small, big, name in THUMB_TEXT:
        _thumb(small, big, name)


def _thumb(small, big, name):
    base = Image.open(p("img", "thumb_base.png")).convert("RGB").resize((1280, 720), Image.LANCZOS).convert("RGBA")
    ph = news_phone("TOMORROW · 6:00 PM", ["Local man in fatal crash"], 1, breaking=True, highlight="date")
    ph = ph.resize((round(PW * 0.44), round(PH * 0.44)), Image.LANCZOS).rotate(-8, Image.BICUBIC, expand=True)
    base.alpha_composite(ph, (900, 268))
    d = ImageDraw.Draw(base)
    size = 120
    while d.textlength(big, font=font(size)) > 600:
        size -= 4
    d.text((1255, 34), small, font=font(76), fill=PAPER, anchor="ra", stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((1255, 112), big, font=font(size), fill=YELLOW, anchor="ra", stroke_width=7, stroke_fill=(0, 0, 0))
    base.convert("RGB").save(p(name), quality=92)


if __name__ == "__main__":
    print(f"timeline {TOTAL:.1f}s, {N} lines")
    thumbnail()
    build_audio()
    render(frame_at, TOTAL, p("mix.wav"), p("tomorrows_news.mp4"))
    os.remove(p("mix.wav"))
    print("done", p("tomorrows_news.mp4"))
