"""Shared building blocks for What If…? episodes: camera moves, cut-out characters, HUD, host card,
phone/news UI, message UI, sound effects and a clean broadcast-loudness audio mix.

An episode script imports this, defines SHOTS keyed to narration lines, and calls render().
"""
import math, os, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS, SR = 1920, 1080, 30, 48000
ANTON = os.path.join(ROOT, "assets", "fonts", "Anton.ttf")
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
YELLOW, RED, INK, PAPER = (255, 204, 0), (220, 40, 40), (20, 20, 20), (255, 255, 255)
_fonts = {}


def font(size, face="anton"):
    key = (size, face)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(ANTON if face == "anton" else INTER.format(face), size)
    return _fonts[key]


# ------------------------------------------------------------------ easing
def clamp01(x):
    return min(max(x, 0.0), 1.0)


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, c=1.7):
    x = clamp01(x)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


# ------------------------------------------------------------------ images
def load_bg(path, w=2304):
    im = Image.open(path).convert("RGB")
    return im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)


def key_green(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    spill = g - np.maximum(r, b)
    alpha = np.clip(1 - (spill - 40) / 60, 0, 1)
    a[..., 1] = np.where(spill > 0, np.maximum(r, b), g)
    img = Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), "RGBA")
    img.putalpha(img.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8)))
    return img.crop(img.getbbox())


def cam(img, cx, cy, zoom, shake=0.0):
    """16:9 window of img centred on (cx, cy) in 0..1 units; zoom 1 = widest framing."""
    vw = min(img.width, img.height * 16 / 9) / zoom
    vh = vw * 9 / 16
    x0 = min(max(cx * img.width - vw / 2, 0), img.width - vw)
    y0 = min(max(cy * img.height - vh / 2, 0), img.height - vh)
    if shake:
        x0 = min(max(x0 + random.uniform(-shake, shake), 0), img.width - vw)
        y0 = min(max(y0 + random.uniform(-shake, shake), 0), img.height - vh)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + vw, y0 + vh)).convert("RGBA")


def blurred(frame, radius=14, dim=0.5):
    return ImageEnhance.Brightness(frame.convert("RGB").filter(ImageFilter.GaussianBlur(radius))).enhance(dim).convert("RGBA")


def grade(frame, sat=1.0, bright=1.0):
    f = frame.convert("RGB")
    if sat != 1.0:
        f = ImageEnhance.Color(f).enhance(sat)
    if bright != 1.0:
        f = ImageEnhance.Brightness(f).enhance(bright)
    return f.convert("RGBA")


def rgb_split(frame, off=14, scan=True):
    arr = np.asarray(frame.convert("RGB")).astype(np.int16)
    arr = np.dstack([np.roll(arr[..., 0], off, 1), arr[..., 1], np.roll(arr[..., 2], -off, 1)])
    if scan:
        arr[::4] = arr[::4] * 0.7
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


def vignette_mask():
    y, x = np.ogrid[-1:1:H * 1j, -1:1:W * 1j]
    return np.clip(1 - 0.5 * (x ** 2 * 0.7 + y ** 2) ** 1.2, 0, 1)[..., None].astype(np.float32)


VIG = vignette_mask()


def text_on(img, xy, text, size, fill=INK, anchor="mm", angle=0, face="anton"):
    """Draw text onto a background image (e.g. a blank sign or cheque), optionally rotated."""
    f = font(size, face)
    if not angle:
        ImageDraw.Draw(img).text(xy, text, font=f, fill=fill, anchor=anchor)
        return
    l, t, r, b = ImageDraw.Draw(img).textbbox((0, 0), text, font=f)
    layer = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((10 - l, 10 - t), text, font=f, fill=fill)
    layer = layer.rotate(angle, Image.BICUBIC, expand=True)
    img.paste(layer, (round(xy[0] - layer.width / 2), round(xy[1] - layer.height / 2)), layer)


# ------------------------------------------------------------------ HUD
def hud(frame, t, left, right, step=None):
    """left/right = (label, value). step = (n_lit, t_lit) for the 12-dash progress bar."""
    d = ImageDraw.Draw(frame)
    for (label, val), x, anc in [(left, 48, "la"), (right, W - 48, "ra")]:
        d.text((x, 34), label, font=font(26), fill=PAPER, anchor=anc, stroke_width=2, stroke_fill=(0, 0, 0))
        d.text((x, 64), val if isinstance(val, str) else f"{int(val):,}", font=font(54), fill=PAPER,
               anchor=anc, stroke_width=3, stroke_fill=(0, 0, 0))
    if step:
        x0, y = W / 2 - 12 * 38 / 2, 52
        for k in range(12):
            lit = k < step[0]
            col = YELLOW if lit else (90, 90, 90)
            if lit and k == step[0] - 1 and 0 <= t - step[1] < 0.5:
                col = PAPER if int((t - step[1]) * 12) % 2 == 0 else YELLOW
            d.rounded_rectangle((x0 + k * 38, y, x0 + k * 38 + 28, y + 9), 3, fill=col, outline=(0, 0, 0), width=1)


# ------------------------------------------------------------------ host + card
def host_in(frame, host, t, t_in):
    x = -host.width + (host.width + 120) * ease_out_back((t - t_in) / 0.45)
    frame.alpha_composite(host, (round(x), round(H - host.height + 60 + 6 * math.sin(t * 3.2))))


def card(frame, t, t_card, items, item_times, x=1060, y=300, w=780):
    if t < t_card:
        return
    s = 0.6 + 0.4 * ease_out_back((t - t_card) / 0.35)
    h = 70 + 92 * max(len(items), 1)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((4, 4, w - 4, h - 4), 26, fill=PAPER, outline=(0, 0, 0), width=6)
    for k, (txt, tk) in enumerate(zip(items, item_times)):
        if t >= tk:
            a = ease_out_back((t - tk) / 0.25)
            yy = 40 + k * 92 + (1 - a) * 18
            if len(items) > 1:
                d.text((44, yy), str(k + 1), font=font(58), fill=RED)
            d.text((100 if len(items) > 1 else 44, yy), txt, font=font(58), fill=INK)
    c = c.resize((round(w * s), round(h * s)), Image.BICUBIC)
    frame.alpha_composite(c, (round(x + (w - c.width) / 2), round(y + (h - c.height) / 2)))


# ------------------------------------------------------------------ phone UI
PW, PH = 560, 1000


def _phone_shell():
    p = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((0, 0, PW - 1, PH - 1), 70, fill=(18, 18, 22), outline=(70, 70, 80), width=4)
    d.rounded_rectangle((22, 22, PW - 23, PH - 23), 52, fill=(250, 250, 248))
    d.rounded_rectangle((PW / 2 - 70, 36, PW / 2 + 70, 66), 15, fill=(18, 18, 22))   # notch
    return p


_SHELL = None


def _wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if d.textlength(test, font=f) <= maxw:
            cur = test
        else:
            lines.append(cur); cur = w_
    return lines + [cur] if cur else lines


def news_phone(date_line, headlines, shown, breaking=False, highlight=None):
    """headlines: list of str; shown: how many are visible (float allows a fade-in on the last)."""
    global _SHELL
    if _SHELL is None:
        _SHELL = _phone_shell()
    p = _SHELL.copy()
    d = ImageDraw.Draw(p)
    d.rectangle((22, 90, PW - 23, 190), fill=RED)
    d.text((PW / 2, 140), "NEWSFLASH", font=font(52), fill=PAPER, anchor="mm")
    d.text((54, 215), date_line, font=font(24, "Bold"), fill=RED if highlight == "date" else (110, 110, 110))
    y = 262
    if breaking:
        d.rounded_rectangle((54, y, 230, y + 40), 8, fill=RED)
        d.text((142, y + 20), "BREAKING", font=font(26), fill=PAPER, anchor="mm")
        y += 60
    big = len(headlines) == 1
    for k, hl in enumerate(headlines):
        a = clamp01(shown - k)
        if a <= 0:
            break
        f = font(64 if big else 48)
        col = tuple(round(lerp(250, c, a)) for c in INK)
        for ln in _wrap(d, hl.upper(), f, PW - 110):
            d.text((54, y), ln, font=f, fill=col)
            y += f.size + 10
        grey = tuple(round(lerp(250, 205, a)) for _ in range(3))
        if big:                                                 # article photo placeholder
            y += 14
            d.rounded_rectangle((54, y, PW - 56, y + 230), 18, fill=tuple(round(lerp(250, 222, a)) for _ in range(3)))
            mx, my = PW / 2, y + 115
            d.polygon([(mx - 90, my + 60), (mx - 25, my - 20), (mx + 20, my + 30), (mx + 50, my), (mx + 100, my + 60)], fill=grey)
            d.ellipse((mx + 40, my - 70, mx + 80, my - 30), fill=grey)
            y += 250
        for bw in ((0.92, 0.86, 0.9, 0.6) if big else (0.86, 0.7)):   # grey "article body" lines
            d.rounded_rectangle((54, y + 8, 54 + (PW - 110) * bw, y + 22), 6, fill=grey)
            y += 28
        y += 30
        if k < len(headlines) - 1:
            d.line((54, y - 16, PW - 56, y - 16), fill=(225, 225, 225), width=2)
    return p


def message_phone(contact, number, text, typed, header_glow=0.0, t=0.0):
    global _SHELL
    if _SHELL is None:
        _SHELL = _phone_shell()
    p = _SHELL.copy()
    d = ImageDraw.Draw(p)
    d.rectangle((22, 90, PW - 23, 330), fill=(240, 240, 244))
    d.ellipse((PW / 2 - 62, 104, PW / 2 + 62, 228), fill=(70, 120, 220))
    d.text((PW / 2, 166), contact[:1] if contact[0].isalpha() else "?", font=font(72), fill=PAPER, anchor="mm")
    glow = tuple(round(lerp(30, c, header_glow)) for c in RED)
    d.text((PW / 2, 268), contact, font=font(48), fill=glow, anchor="mm")
    d.text((PW / 2, 308), number, font=font(24, "SemiBold"), fill=(120, 120, 120), anchor="mm")
    shown = text[: int(len(text) * clamp01(typed))]
    f = font(44, "SemiBold")
    if shown:
        lines = _wrap(d, shown, f, PW - 180)
        bh = 36 + 58 * len(lines)
        d.rounded_rectangle((50, 380, PW - 60, 380 + bh), 34, fill=(229, 229, 234))
        for k, ln in enumerate(lines):
            d.text((80, 398 + k * 58), ln, font=f, fill=INK)
    else:                                                       # "typing…" bubble
        d.rounded_rectangle((50, 380, 210, 460), 34, fill=(229, 229, 234))
        for k in range(3):
            v = 150 + 60 * math.sin(t * 8 - k * 0.9)
            d.ellipse((84 + k * 34, 408, 108 + k * 34, 432), fill=(round(v),) * 3)
    d.text((PW / 2, PH - 70), "Text Message · 5:59 PM", font=font(24, "SemiBold"), fill=(150, 150, 150), anchor="mm")
    return p


def place_phone(frame, phone, t, t_in, x=1240, y=70, scale=0.95, wobble=0.0, out_at=None):
    u = ease_out_back((t - t_in) / 0.45)
    if out_at is not None and t > out_at:
        u = 1 - ease((t - out_at) / 0.3)
    if u <= 0:
        return
    ph = phone.resize((round(PW * scale), round(PH * scale)), Image.BICUBIC)
    if wobble:
        ph = ph.rotate(wobble, Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", ph.size, (0, 0, 0, 0))
    sh.putalpha(ph.getchannel("A").point(lambda v: v * 0.45))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    yy = round(lerp(H + 40, y, u))
    frame.alpha_composite(sh, (x + 14, yy + 22))
    frame.alpha_composite(ph, (x, yy))


def stamp(frame, t, t_in, text, xy, color=RED, angle=-12):
    if t < t_in:
        return
    u = clamp01((t - t_in) / 0.18)
    s = lerp(2.2, 1.0, ease(u))
    f = font(110)
    l, tp, r, b = ImageDraw.Draw(frame).textbbox((0, 0), text, font=f)
    layer = Image.new("RGBA", (r - l + 70, b - tp + 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((6, 6, layer.width - 6, layer.height - 6), 18, outline=color, width=10)
    d.text((35 - l, 25 - tp), text, font=f, fill=color)
    layer = layer.resize((round(layer.width * s), round(layer.height * s)), Image.BICUBIC).rotate(angle, Image.BICUBIC, expand=True)
    layer.putalpha(layer.getchannel("A").point(lambda v: v * clamp01(u * 1.5)))
    frame.alpha_composite(layer, (round(xy[0] - layer.width / 2), round(xy[1] - layer.height / 2)))


def float_text(frame, t, t_in, text, xy, color=YELLOW, size=80, rise=120, life=1.0):
    u = (t - t_in) / life
    if not 0 <= u <= 1:
        return
    a = 1 - u ** 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((xy[0], xy[1] - rise * ease(u)), text, font=font(size), fill=color + (round(255 * a),),
                               anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, round(255 * a)))
    frame.alpha_composite(layer)


def big_title(frame, text, sub=None, a=1.0):
    d = ImageDraw.Draw(frame)
    fill = tuple(round(c * a) for c in PAPER)
    d.text((W / 2, H / 2 - 30), text, font=font(130), fill=fill, anchor="mm")
    if sub:
        d.text((W / 2, H / 2 + 80), sub, font=font(48), fill=tuple(round(c * a) for c in YELLOW), anchor="mm")


# ------------------------------------------------------------------ audio
def read_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(1)
        sr = w.getframerate()
    if sr != SR:
        a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a).astype(np.float32)
    return a


def write_wav(path, a):
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def _env(n, attack, release):
    e = np.ones(n, np.float32)
    a, r = min(int(attack * SR), n), min(int(release * SR), n)
    if a: e[:a] = np.linspace(0, 1, a)
    if r: e[-r:] *= np.linspace(1, 0, r)
    return e


def sfx(kind):
    """Small, clean synthesized sound effects (mono float32 at SR)."""
    rng = np.random.default_rng(len(kind))
    if kind == "ping":                      # phone notification: two soft bell tones
        out = np.zeros(int(0.55 * SR), np.float32)
        for st, f in [(0.0, 1318.5), (0.11, 1760.0)]:
            n = int(0.42 * SR); s = int(st * SR); tt = np.arange(n) / SR
            tone = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 9)
            out[s:s + n] += tone * _env(n, 0.003, 0.05)
        return out * 0.22
    if kind == "pop":
        n = int(0.09 * SR); tt = np.arange(n) / SR
        return (np.sin(2 * np.pi * (600 + 900 * tt / 0.09) * tt) * np.exp(-tt * 40) * 0.28).astype(np.float32)
    if kind == "whoosh":
        n = int(1.0 * SR); k = np.linspace(0, 1, n)
        noise = rng.normal(0, 1, n).astype(np.float32)
        lo = np.convolve(noise, np.ones(24) / 24, "same")
        return (lo * np.sin(np.pi * k) ** 2 * 0.5).astype(np.float32)
    if kind == "boom":
        n = int(1.8 * SR); tt = np.arange(n) / SR
        return ((np.sin(2 * np.pi * (58 - 22 * tt) * tt) + 0.3 * np.sin(2 * np.pi * 2 * (58 - 22 * tt) * tt))
                * np.exp(-tt * 2.6) * _env(n, 0.004, 0.2) * 0.55).astype(np.float32)
    if kind == "tick":
        n = int(0.05 * SR); tt = np.arange(n) / SR
        return (np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 160) * 0.18).astype(np.float32)
    if kind == "buzz":                      # phone vibrating on a table: 3 pulses
        out = np.zeros(int(1.3 * SR), np.float32)
        for s in (0.0, 0.45, 0.9):
            n = int(0.3 * SR); tt = np.arange(n) / SR
            v = np.sign(np.sin(2 * np.pi * 165 * tt)) * 0.6 + np.sin(2 * np.pi * 330 * tt) * 0.4
            v = np.convolve(v, np.ones(6) / 6, "same")
            out[int(s * SR):int(s * SR) + n] += v * _env(n, 0.01, 0.04) * 0.2
        return out
    if kind == "screech":
        n = int(1.1 * SR); k = np.linspace(0, 1, n); tt = np.arange(n) / SR
        tone = np.sin(2 * np.pi * np.cumsum(2300 - 600 * k) / SR) * 0.5 + rng.normal(0, 0.25, n)
        return (np.convolve(tone, np.ones(3) / 3, "same") * np.sin(np.pi * k) ** 0.5 * (1 - k) * 0.18).astype(np.float32)
    if kind == "flash":                     # camera shutter clicks
        out = np.zeros(int(0.9 * SR), np.float32)
        for s in rng.uniform(0, 0.75, 6):
            n = int(0.04 * SR)
            out[int(s * SR):int(s * SR) + n] += rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 120) * 0.15
        return out
    if kind == "coin":
        n = int(0.35 * SR); tt = np.arange(n) / SR
        f = np.where(tt < 0.07, 1975.5, 2637.0)
        return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 10) * _env(n, 0.002, 0.05) * 0.16).astype(np.float32)
    raise ValueError(kind)


def music_bed(total, chords, sec_per_chord=4.0, level=0.05):
    """Warm, soft pad: pure sines with slow attack/release and a gentle low-pass, no buzz."""
    n = int(total * SR); out = np.zeros(n, np.float32)
    k = 0
    while True:
        ch = chords[k % len(chords)]
        s = int(k * sec_per_chord * SR)
        if s >= n:
            break
        m = min(int((sec_per_chord + 1.5) * SR), n - s)    # overlap for smooth crossfade
        tt = np.arange(m) / SR
        tone = sum(np.sin(2 * np.pi * f * tt + j) * (0.6 if j else 1.0) for j, f in enumerate(ch))
        tone += 0.5 * np.sin(2 * np.pi * ch[0] / 2 * tt)                # sub octave
        out[s:s + m] += tone * _env(m, 1.2, 1.6) * (1 + 0.15 * np.sin(2 * np.pi * 0.2 * tt))
        k += 1
    out = np.convolve(out, np.ones(8) / 8, "same")                     # soften highs
    return out / (np.abs(out).max() + 1e-6) * level


def clean_voice(src_wav, dst_wav):
    """High-pass rumble, tame sibilance, gentle compression, normalise each line consistently."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src_wav, "-af",
                    "highpass=f=75,deesser=i=0.4,acompressor=threshold=-21dB:ratio=2.5:attack=8:release=120:makeup=2,"
                    "loudnorm=I=-18:TP=-2:LRA=7,aresample=48000",
                    "-ac", "1", "-ar", "48000", dst_wav], check=True)


def finish_audio(voice, music, fx, out_wav, tmp_dir):
    """Duck the music under the voice, sum, then master to YouTube loudness (-14 LUFS, -1.5 dBTP)."""
    env = np.abs(voice)
    win = int(0.25 * SR)
    env = np.convolve(env, np.ones(win) / win, "same")
    duck = 1 - 0.55 * np.clip(env / (env.max() * 0.25 + 1e-6), 0, 1)
    mix = voice + music * duck + fx
    raw = os.path.join(tmp_dir, "_premaster.wav")
    write_wav(raw, mix / max(1.0, np.abs(mix).max() / 0.95))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000", "-ar", "48000", out_wav], check=True)
    os.remove(raw)


# ------------------------------------------------------------------ timeline + render
class Timeline:
    def __init__(self, line_wavs, gaps, lead=0.4):
        self.voice_clips = [read_wav(p) for p in line_wavs]
        self.starts, t = [], lead
        for a, g in zip(self.voice_clips, gaps):
            self.starts.append(t); t += len(a) / SR + g
        self.total = t

    def L(self, i):
        return self.starts[i] if i < len(self.starts) else self.total

    def end(self, i):
        return self.starts[i] + len(self.voice_clips[i]) / SR

    def voice_track(self):
        n = int(self.total * SR); v = np.zeros(n, np.float32)
        for a, st in zip(self.voice_clips, self.starts):
            i = int(st * SR); v[i:i + len(a)] += a[: n - i]
        return v


def place(track, clip, t):
    i = int(t * SR)
    if 0 <= i < len(track):
        track[i:i + len(clip)] += clip[: len(track) - i]


def render(frame_at, total, audio_wav, out_mp4, fade_in=0.3):
    nf = int(round(total * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio_wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4],
                          stdin=subprocess.PIPE)
    for k in range(nf):
        t = k / FPS
        arr = np.asarray(frame_at(t).convert("RGB")).astype(np.float32) * VIG
        if t < fade_in:
            arr *= t / fade_in
        ff.stdin.write(arr.astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
