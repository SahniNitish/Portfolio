"""20s 'What if' explainer: painted backgrounds, cut-out puppet characters, HUD, host + info card.

Pattern taken from the reference: cold-open hook -> rewind montage with a counter rolling back
-> premise -> host over blurred scene with a numbered rules card -> step 1 with HUD progress
-> ominous one-line cliffhanger.
"""
import math, os, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(HERE, *a)
W, H, FPS, SR = 1920, 1080, 30, 48000
FONT = p("..", "..", "assets", "fonts", "Anton.ttf")
F = lambda s: ImageFont.truetype(FONT, s)
YELLOW, RED = (255, 204, 0), (220, 40, 40)
random.seed(7)

# ---------------------------------------------------------------- timeline
GAPS = [0.30, 0.65, 0.50, 0.25, 0.30, 0.30, 0.50, 0.30, 1.30]
lines = [p("audio", f"l{i+1}.wav") for i in range(9)]


def read_wav(fn):
    with wave.open(fn) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return a, w.getframerate()


vo = [read_wav(f) for f in lines]
starts, t = [], 0.15
for (a, sr), g in zip(vo, GAPS):
    starts.append(t); t += len(a) / sr + g
TOTAL = t
L = lambda i: starts[i]          # start time of line i (0-based)
NF = int(round(TOTAL * FPS))

# ---------------------------------------------------------------- assets
def key_green(fn):
    a = np.asarray(Image.open(fn).convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    spill = g - np.maximum(r, b)
    alpha = np.clip(1 - (spill - 40) / 60, 0, 1)            # strong green -> transparent
    a[..., 1] = np.where(spill > 0, np.maximum(r, b), g)   # despill edges
    img = Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), "RGBA")
    img.putalpha(img.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8)))
    return img.crop(img.getbbox())


def bg(fn, w=2304):
    im = Image.open(fn).convert("RGB")
    return im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)


closeup, bed, street = bg(p("img", "closeup.jpg")), bg(p("img", "bed.jpg")), bg(p("img", "street.jpg"))
hero = key_green(p("img", "hero_g.png"))
host = key_green(p("img", "host_g.png"))
hero = hero.resize((round(hero.width * 560 / hero.height), 560), Image.LANCZOS)
host = host.resize((round(host.width * 900 / host.height), 900), Image.LANCZOS)
bed_blur = None  # built lazily from the bed framing


def ease_out_back(x):
    x = min(max(x, 0), 1); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def ease(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


def cam(img, cx, cy, zoom, shake=0.0):
    """Crop a 16:9 window of `img` centred on (cx, cy) in 0..1 units at `zoom` (1 = full width)."""
    vw = min(img.width, img.height * 16 / 9) / zoom; vh = vw * 9 / 16
    x0 = min(max(cx * img.width - vw / 2, 0), img.width - vw)
    y0 = min(max(cy * img.height - vh / 2, 0), img.height - vh)
    if shake:
        x0 += random.uniform(-shake, shake); y0 += random.uniform(-shake, shake)
        x0 = min(max(x0, 0), img.width - vw); y0 = min(max(y0, 0), img.height - vh)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + vw, y0 + vh))


def vignette():
    y, x = np.ogrid[-1:1:H * 1j, -1:1:W * 1j]
    v = np.clip(1 - 0.55 * (x ** 2 * 0.7 + y ** 2) ** 1.2, 0, 1)
    return v[..., None].astype(np.float32)


VIG = vignette()


def shadow(size):
    s = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((0, 0, *size), fill=(0, 0, 0, 90))
    return s.filter(ImageFilter.GaussianBlur(10))


HERO_SHADOW = shadow((300, 46))

# ---------------------------------------------------------------- HUD
def fmt(n):
    return f"{int(n):,}"


def hud(frame, t, hours, step, energy):
    d = ImageDraw.Draw(frame)
    d.text((48, 34), "HOURS AWAKE", font=F(26), fill=(255, 255, 255))
    d.text((48, 64), fmt(hours), font=F(54), fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    if step is not None:
        x0, y = W / 2 - 12 * 38 / 2, 52
        for k in range(12):
            lit = k < step[0]
            col = YELLOW if lit else (90, 90, 90)
            if lit and k == step[0] - 1 and t - step[1] < 0.5:     # flash the newly lit dash
                col = (255, 255, 255) if int((t - step[1]) * 12) % 2 == 0 else YELLOW
            d.rounded_rectangle((x0 + k * 38, y, x0 + k * 38 + 28, y + 9), 3, fill=col)
    d.text((W - 48, 34), "ENERGY", font=F(26), fill=(255, 255, 255), anchor="ra")
    d.text((W - 48, 64), f"{energy}%", font=F(54), fill=(255, 255, 255), anchor="ra", stroke_width=3, stroke_fill=(0, 0, 0))


# ---------------------------------------------------------------- rules card
RULES = ["YOU NEVER GET TIRED", "YOU NEVER DREAM", "YOU CAN'T SWITCH IT OFF"]


def card(frame, t):
    t_card = L(3) + 0.35
    if t < t_card:
        return
    s = 0.6 + 0.4 * ease_out_back((t - t_card) / 0.35)
    cw, ch = 760, 330
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((4, 4, cw - 4, ch - 4), 26, fill=(255, 255, 255), outline=(0, 0, 0), width=6)
    for k, txt in enumerate(RULES):
        tk = L(4 + k)
        if t >= tk:
            a = ease_out_back((t - tk) / 0.25)
            y = 48 + k * 92 + (1 - a) * 18
            d.text((48, y), str(k + 1), font=F(62), fill=RED)
            d.text((104, y), txt, font=F(62), fill=(20, 20, 20))
    c = c.resize((round(cw * s), round(ch * s)), Image.BICUBIC)
    frame.alpha_composite(c, (round(1080 + (cw - c.width) / 2), round(330 + (ch - c.height) / 2)))


# ---------------------------------------------------------------- scenes
def frame_at(t):
    global bed_blur
    hours, step, energy = 87600, None, 3

    if t < L(1):                                                 # 1. cold open close-up
        u = t / L(1)
        f = cam(closeup, 0.5, 0.48, 1.0 + 0.10 * ease(u))
        flick = 1 + 0.06 * math.sin(t * 37) * (random.random() > 0.6)
        f = ImageEnhance.Brightness(f).enhance(flick)

    elif t < L(2):                                               # 2. rewind montage
        u = (t - L(1)) / (L(2) - L(1))
        shots = [(street, .5, .5), (bed, .35, .45), (closeup, .5, .48), (street, .3, .55), (bed, .5, .5)]
        img, cx, cy = shots[min(int(u * len(shots)), len(shots) - 1)]
        f = cam(img, cx, cy, 1.25)
        arr = np.asarray(f).astype(np.int16)
        off = 14
        arr = np.dstack([np.roll(arr[..., 0], off, 1), arr[..., 1], np.roll(arr[..., 2], -off, 1)])
        arr[::4] = arr[::4] * 0.7                                # scanlines
        f = Image.fromarray(np.clip(arr * 0.85 + 20, 0, 255).astype(np.uint8))
        hours = int(87600 * (1 - ease(u)) ** 2)
        energy = int(3 + 97 * ease(u))

    elif t < L(3):                                               # 3. premise: awake in bed
        u = (t - L(2)) / (L(3) - L(2))
        f = cam(bed, 0.42, 0.50, 1.0 + 0.45 * ease(u))
        hours, energy = int(7 * u), 100

    elif t < L(7):                                               # 4. host + rules over blurred bg
        if bed_blur is None:
            b = cam(bed, 0.42, 0.50, 1.45).filter(ImageFilter.GaussianBlur(14))
            bed_blur = ImageEnhance.Brightness(b).enhance(0.5).convert("RGBA")
        f = bed_blur.copy()
        u = (t - L(3)) / 0.45
        x = -host.width + (host.width + 120) * ease_out_back(u)
        bob = 6 * math.sin(t * 3.2)
        f.alpha_composite(host, (round(x), round(H - host.height + 60 + bob)))
        card(f, t)
        hours, energy = 8, 100
        f = f.convert("RGB")

    else:                                                        # 5. day one: walking down the street
        u = (t - L(7)) / (TOTAL - L(7))
        pan = 0.30 + 0.25 * u
        dark = ease((t - L(8)) / 0.8)                              # mood turns on the last line
        f = cam(street, pan, 0.55, 1.0 + 0.05 * u + 0.25 * dark).convert("RGBA")
        walk_end = L(8) + 0.4
        wu = min((t - L(7)) / (walk_end - L(7)), 1)
        hx = 260 + 700 * ease(wu)
        moving = wu < 1
        bob = abs(math.sin(t * 9)) * 22 if moving else 0
        ang = 4 * math.sin(t * 9) if moving else 0
        spr = hero.rotate(ang, Image.BICUBIC, expand=True)
        gy = 1000
        f.alpha_composite(HERO_SHADOW, (round(hx + spr.width / 2 - 150), gy - 26))
        f.alpha_composite(spr, (round(hx), round(gy - spr.height - bob)))
        f = f.convert("RGB")
        if dark > 0:
            f = ImageEnhance.Color(f).enhance(1 - 0.85 * dark)
            f = ImageEnhance.Brightness(f).enhance(1 - 0.45 * dark)
        hours = int(8 + 16 * min((t - L(7)) / 1.6, 1))
        energy = 100
        step = (1, L(7) + 0.2)

    f = f.convert("RGBA")
    hud(f, t, hours, step, energy)
    arr = np.asarray(f.convert("RGB")).astype(np.float32) * VIG
    if t > TOTAL - 0.45:                                          # hard out to black
        arr *= 0
    if t < 0.3:
        arr *= t / 0.3
    return arr.astype(np.uint8)


# ---------------------------------------------------------------- audio
def build_audio():
    n = int(TOTAL * SR)
    mix = np.zeros(n, np.float32)
    for (a, sr), st in zip(vo, starts):
        if sr != SR:
            a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a).astype(np.float32)
        i = int(st * SR); mix[i:i + len(a)] += a[: n - i] * 1.0
    tt = np.arange(n) / SR
    # soft pad: Am - F - C - G, one chord per ~2.5s
    chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [196, 261.6, 329.6], [196, 246.9, 293.7]]
    pad = np.zeros(n, np.float32)
    for k, ch in enumerate(chords * 3):
        s, e = int(k * 2.5 * SR), int((k + 1) * 2.5 * SR)
        if s >= n: break
        e = min(e, n); seg = tt[s:e]
        env = np.minimum(1, np.minimum((seg - seg[0]) / 0.6, (seg[-1] - seg + 1e-3) / 0.6))
        pad[s:e] = sum(np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(4 * np.pi * f * seg) for f in ch) * env
    pad *= 0.022
    duck = np.ones(n, np.float32)                                 # dark turn: drop the pad
    duck[int(L(8) * SR):] = np.linspace(1, 0, n - int(L(8) * SR)) ** 2
    mix += pad * duck
    # rewind whoosh
    s, e = int(L(1) * SR), int(L(2) * SR)
    noise = np.random.default_rng(1).normal(0, 1, e - s).astype(np.float32)
    k = np.linspace(0, 1, e - s)
    mix[s:e] += np.convolve(noise, np.ones(12) / 12, "same") * np.sin(np.pi * k) * 0.25
    mix[s:e] += np.sin(2 * np.pi * np.cumsum(900 - 700 * k) / SR) * np.sin(np.pi * k) * 0.05
    # pops on card + each rule
    for st in [L(3) + 0.35] + [L(4 + j) for j in range(3)]:
        i = int(st * SR); m = int(0.09 * SR); seg = np.arange(m) / SR
        mix[i:i + m] += np.sin(2 * np.pi * (700 + 900 * seg / 0.09) * seg) * np.exp(-seg * 40) * 0.22
    # low boom on the cliffhanger + cut to black
    for st, amp in [(L(8), 0.5), (TOTAL - 0.45, 0.35)]:
        i = int(st * SR); m = min(int(1.4 * SR), n - i); seg = np.arange(m) / SR
        mix[i:i + m] += np.sin(2 * np.pi * (55 - 20 * seg) * seg) * np.exp(-seg * 3) * amp
    mix /= max(1.0, np.abs(mix).max() / 0.92)
    with wave.open(p("mix.wav"), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


build_audio()
out = p("never_sleep_20s.mp4")
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", p("mix.wav"),
                       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                      stdin=subprocess.PIPE)
for k in range(NF):
    ff.stdin.write(frame_at(k / FPS).tobytes())
ff.stdin.close(); ff.wait()
print(out, round(TOTAL, 2), "s")
