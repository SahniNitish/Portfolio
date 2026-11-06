"""15-second sample (16:9, 1920x1080) in the "illustrated business-history explainer" look (reference: CEOzoned, "The ENTIRE History of Coca-Cola"):
full-colour cartoon scenes (classroom, hallway), meme-faced stick characters with thin limbs and big expressive eyes, floating "?" marks,
slow camera push-ins, bold white captions with outline. Same 29-word school hook and Gemini Bodi voice as wb06. All drawn in code.

    python deeptime/wb07-cartoon-sample/episode.py     # renders sample_cartoon.mp4
"""
import importlib.util, math, os, random, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("wb06", os.path.join(HERE, "..", "wb06-clean-samples", "episode.py"))
w6 = importlib.util.module_from_spec(_s); sys.modules["wb06"] = w6; _s.loader.exec_module(w6)
w4 = w6.w4
font, canvas, done, el, rr, pg, ln, put, pop, ease, clamp01, lerp, mix = w6.font, w6.canvas, w6.done, w6.el, w6.rr, w6.pg, w6.ln, w6.put, w6.pop, w6.ease, w6.clamp01, w6.lerp, w6.mix
ANTON = w6.ANTON
FPS = w6.FPS
p = lambda *a: os.path.join(HERE, *a)
W, H, TOTAL = 1920, 1080, 15.0
B = w6.B
INK = (34, 28, 30)
GOLD, RED, BLUE, GREEN, WHITE = (250, 196, 60), (222, 62, 58), (66, 120, 220), (70, 170, 100), (255, 255, 255)


# ------------------------------------------------------------- characters: white round head, brows, big eyes, thin limbs
def kid(mood="meh", look=0.0, arms="down", legs=0.0, shirt=BLUE, hat=None, glasses=False, tie=False, stache=False, backpack=False, key=None):
    k = (mood, round(look, 1), arms, round(legs * 4) / 4, shirt, hat, glasses, tie, stache, backpack)
    if k in _kc:
        return _kc[k]
    cw, ch = 520, 900
    im, d = canvas(cw, ch)
    # legs
    for j, hx in enumerate((230, 290)):
        sw = math.sin(legs * 2 * math.pi + j * math.pi) * 55 if legs else 0
        ln(d, [(hx, 640), (hx + sw * 0.6, 740), (hx + sw, 840)], 12, INK)
        el(d, hx + sw + 16, 850, 34, 16, INK, 0)
    # body
    if backpack:
        rr(d, 150, 400, 235, 600, 24, (220, 140, 60), 6)
    pg(d, [(205, 400), (315, 400), (330, 650), (190, 650)], shirt, 6)
    if tie:
        pg(d, [(260, 405), (245, 440), (260, 540), (275, 440)], RED, 3)
    sh = ((205, 430), (315, 430))
    hands = {"down": ((150, 600), (370, 600)), "shrug": ((90, 470), (430, 470)), "up": ((120, 190), (400, 190)), "hold": ((190, 560), (330, 520)),
             "point": ((140, 590), (470, 420)), "run": ((150, 520), (380, 400)), "bored": ((250, 420), (330, 560))}[arms]
    for s_, h_ in zip(sh, hands):
        ln(d, [s_, ((s_[0] + h_[0]) / 2 + (6 if s_[0] > 260 else -6), (s_[1] + h_[1]) / 2 + 20), h_], 11, INK)
        el(d, h_[0], h_[1], 17, 17, WHITE, 5)
    # head
    el(d, 260, 250, 130, 126, WHITE, 8)
    ex = (215, 305); lk = look * 12
    wide = mood in ("shock", "wow")
    for x in ex:
        if mood == "shut":
            ln(d, [(x - 24, 255), (x + 24, 250)], 8, INK)
        elif mood == "hap":
            d.arc([S(x - 26), S(235), S(x + 26), S(285)], 190, 350, fill=INK, width=S(8))
        else:
            el(d, x, 252, 33 if not wide else 38, 38 if not wide else 46, WHITE, 6)
            el(d, x + lk, 258, 12 if not wide else 7, 13 if not wide else 8, INK, 0)
    if mood in ("meh", "sad", "worry"):
        ln(d, [(180, 220), (240, 202)], 9, INK); ln(d, [(340, 220), (280, 202)], 9, INK)
    elif mood == "mad":
        ln(d, [(180, 200), (240, 220)], 10, INK); ln(d, [(340, 200), (280, 220)], 10, INK)
    elif mood in ("shock", "wow", "hap"):
        ln(d, [(185, 198), (240, 188)], 9, INK); ln(d, [(335, 198), (280, 188)], 9, INK)
    if glasses:
        for x in ex:
            el(d, x, 252, 44, 44, None, 6)
        ln(d, [(255, 252), (265, 252)], 6, INK)
    if mood == "hap":
        pg(d, [(215, 305), (305, 305), (290, 350), (230, 350)], WHITE, 6)
    elif mood in ("shock", "wow"):
        el(d, 260, 330, 26, 34, (110, 30, 40), 6)
    elif mood in ("sad", "worry"):
        d.arc([S(225), S(318), S(295), S(362)], 200, 340, fill=INK, width=S(8))
    elif mood == "mad":
        pg(d, [(225, 335), (295, 335), (285, 352), (235, 352)], WHITE, 6)
    else:
        ln(d, [(228, 335), (292, 338)], 8, INK)
    if stache:
        pg(d, [(260, 318), (205, 312), (180, 338), (225, 330), (260, 326), (295, 330), (340, 338), (315, 312)], INK, 3)
    if hat == "bowler":
        el(d, 260, 150, 130, 20, (30, 30, 36), 6); pg(d, [(180, 150), (200, 90), (260, 72), (320, 90), (340, 150)], (30, 30, 36), 6)
    elif hat == "cap":
        pg(d, [(140, 175), (170, 110), (260, 90), (350, 110), (385, 175), (300, 160), (200, 160)], RED, 6)
    for dx in ((-50, -10, 30) if hat is None else ()):
        ln(d, [(260 + dx, 128), (260 + dx + 10, 100)], 9, INK)
    _kc[k] = done(im, cw, ch)
    return _kc[k]
_kc = {}
S = lambda v: v * w4.SS


def sweat(img, x, y):
    d = ImageDraw.Draw(img)
    d.polygon([(x, y - 30), (x - 14, y + 4), (x + 14, y + 4)], fill=(120, 190, 255)); d.ellipse([x - 14, y - 10, x + 14, y + 18], fill=(120, 190, 255))


# ------------------------------------------------------------- backgrounds (full colour)
def classroom(bright, t=0.0):
    wall = mix((120, 150, 160), (255, 214, 130), bright); floor = mix((140, 120, 104), (214, 160, 96), bright)
    im = Image.new("RGB", (W, H), wall); d = ImageDraw.Draw(im)
    d.rectangle([0, 760, W, H], fill=floor)
    for x in range(-200, W + 200, 140):
        d.line([(x, 760), (x - 120, H)], fill=mix(floor, (0, 0, 0), 0.12), width=4)
    d.rectangle([0, 740, W, 770], fill=mix(wall, (0, 0, 0), 0.2))
    sky = mix((150, 165, 180), (130, 200, 255), bright)
    for x0 in (120, 1500):
        d.rectangle([x0, 150, x0 + 300, 520], fill=(250, 250, 250)); d.rectangle([x0 + 14, 164, x0 + 286, 506], fill=sky)
        d.line([(x0 + 150, 164), (x0 + 150, 506)], fill=(250, 250, 250), width=10); d.line([(x0 + 14, 335), (x0 + 286, 335)], fill=(250, 250, 250), width=10)
        d.ellipse([x0 + 40, 220, x0 + 150, 280], fill=(255, 255, 255)); d.ellipse([x0 + 110, 200, x0 + 230, 270], fill=(255, 255, 255))
    d.rectangle([560, 130, 1360, 560], fill=(122, 82, 50)); d.rectangle([580, 150, 1340, 540], fill=mix((50, 70, 64), (30, 110, 84), bright))
    for k, (a, b, c, e) in enumerate(((620, 220, 900, 200), (620, 300, 1100, 320), (620, 380, 980, 390))):
        d.line([(a, b), (c, e)], fill=(235, 235, 225), width=7)
    d.rectangle([600, 548, 1320, 560], fill=(236, 230, 214))
    d.ellipse([1390, 150, 1480, 240], fill=(250, 250, 250), outline=INK, width=6)
    d.line([(1435, 195), (1435, 165)], fill=INK, width=6); ang = t * 2.0; d.line([(1435, 195), (1435 + 28 * math.sin(ang), 195 - 28 * math.cos(ang))], fill=RED, width=5)
    for row, (y, s) in enumerate(((820, 1.25), (940, 1.5))):
        for i in range(4):
            x = 260 + i * 460 - (row * 90)
            d.rectangle([x, y, x + 240 * s * 0.8, y + 24], fill=(150, 98, 56)); d.rectangle([x + 20, y + 24, x + 36, y + 120], fill=(110, 70, 40)); d.rectangle([x + 170, y + 24, x + 186, y + 120], fill=(110, 70, 40))
    return im


def hallway(t, speed=420):
    im = Image.new("RGB", (W, H), (236, 224, 190)); d = ImageDraw.Draw(im)
    d.rectangle([0, 800, W, H], fill=(196, 170, 140))
    off = (t * speed) % 260
    cols = [(220, 80, 70), (70, 130, 220), (80, 170, 110), (240, 190, 60)]
    for i in range(-1, 9):
        x = i * 260 - off; c = cols[(i + int(t * speed // 260)) % 4]
        d.rectangle([x, 260, x + 220, 800], fill=c, outline=INK, width=5)
        for j in range(5):
            d.line([(x + 40, 320 + j * 14), (x + 180, 320 + j * 14)], fill=mix(c, (0, 0, 0), 0.3), width=4)
        d.rectangle([x + 150, 520, x + 175, 580], fill=(235, 235, 235))
    d.rectangle([0, 190, W, 250], fill=(120, 90, 70))
    for i in range(-1, 12):
        x = i * 200 - (off * 0.7) % 200
        d.polygon([(x, 190), (x + 70, 190), (x + 35, 130)], fill=[RED, GOLD, BLUE][i % 3])
    d.rectangle([0, 790, W, 810], fill=(150, 120, 96))
    return im


# ------------------------------------------------------------- scenes
def cam(im, u, z0=1.0, z1=1.1, cx=0.5, cy=0.5):
    z = lerp(z0, z1, ease(clamp01(u)))
    w, h = W / z, H / z
    x0 = (W - w) * cx; y0 = (H - h) * cy
    return im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BICUBIC)


def coinimg():
    sp = Image.new("RGBA", (80, 80), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    d.ellipse([3, 3, 76, 76], fill=GOLD, outline=(160, 110, 20), width=5); d.text((40, 41), "$", font=font(ANTON, 42), fill=(160, 100, 10), anchor="mm"); return sp


def scene(t):
    k = w6.SCN(t); u = (t - B[k]) / (B[k + 1] - B[k])
    if k == 0:
        im = classroom(0.0, t); 
        put(im, kid("meh", 0.5, "bored", shirt=(90, 110, 200), backpack=True), 520, 1040, 0.85, 1.5 * math.sin(t * 2))
        for j, (x, y, s) in enumerate(((330, 480, 1.0), (560, 380, 1.4), (760, 520, 0.9))):
            a = pop(t, 0.5 + 0.35 * j, 0.4)
            d = ImageDraw.Draw(im); d.text((x + 8 * math.sin(t * 2 + j), y + 10 * math.sin(t * 3 + j)), "?", font=font(ANTON, int(150 * s * max(0.01, a))), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=INK)
        sweat(im, 590, 690)
        return cam(im, u, 1.0, 1.12, 0.4, 0.55)
    if k == 1:
        im = classroom(0.25, t)
        d = ImageDraw.Draw(im)
        put(im, kid("hap", 0.6, "up", shirt=GREEN, backpack=True), 520, 1040, 0.85, 3 * math.sin(t * 6))
        s1 = pop(t, B[1] + 0.2, 0.45)
        card = Image.new("RGBA", (360, 420), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, 359, 419], radius=24, fill=(255, 255, 255), outline=INK, width=8); cd.text((180, 200), "A+", font=font(ANTON, 230), fill=RED, anchor="mm")
        put(im, card, 520, 200, 0.75 * s1, -6, anchor="c")
        for j in range(12):
            tt = t - (B[1] + 0.6) - j * 0.25
            if tt > 0:
                put(im, coinimg(), 380 + (j % 5) * 70, min(960, 480 + 900 * tt * tt), 1.0, 40 * tt, anchor="c")
        put(im, kid("meh", -0.4, "hold", shirt=(130, 130, 150), glasses=True, tie=True, stache=True, hat="bowler"), 1450, 1040, 0.85)
        bk = Image.new("RGBA", (260, 200), (0, 0, 0, 0)); bd = ImageDraw.Draw(bk)
        bd.rounded_rectangle([6, 20, 254, 190], radius=14, fill=(120, 130, 160), outline=INK, width=6); bd.rectangle([124, 20, 136, 190], fill=(90, 100, 130))
        for q in range(4):
            bd.line([(20, 30 + q * 10), (120 - q * 14, 60 + q * 22)], fill=(235, 235, 240), width=3)
        put(im, bk, 1450, 700, pop(t, B[1] + 1.2, 0.4), anchor="c")
        d.text((1730, 640), "0", font=font(ANTON, 160), fill=(120, 120, 140), anchor="mm", stroke_width=5, stroke_fill=WHITE) if t > B[1] + 1.6 else None
        return cam(im, u, 1.0, 1.1, 0.5, 0.55)
    if k == 2:
        im = hallway(t)
        ph = (t * 1.8) % 1.0
        put(im, kid("hap", 0.9, "run", legs=ph, shirt=(230, 100, 80), backpack=True), 640, 1060, 0.95, 5 * math.sin(t * 16))
        bx = 1180 + 70 * math.sin(t * 2); by = 470 + 40 * math.sin(t * 3)
        d = ImageDraw.Draw(im)
        d.line([(bx, by + 110), (bx - 90, 760)], fill=INK, width=5)
        d.ellipse([bx - 130, by - 130, bx + 130, by + 130], fill=GREEN, outline=INK, width=8); d.text((bx, by + 4), "A+", font=font(ANTON, 150), fill=WHITE, anchor="mm", stroke_width=5, stroke_fill=INK)
        a = clamp01((t - B[2]) / 2.0)
        bk = Image.new("RGBA", (260, 200), (0, 0, 0, 0)); bd = ImageDraw.Draw(bk)
        bd.rounded_rectangle([6, 20, 254, 190], radius=14, fill=BLUE, outline=INK, width=6); bd.rectangle([124, 20, 136, 190], fill=(40, 80, 170))
        put(im, bk, lerp(520, -200, a), 930, lerp(1.0, 0.6, a), -25 * a, 1 - 0.5 * a, anchor="c")
        for j in range(5):
            put(im, kid("hap", 0.9, "run", legs=(ph + j * 0.2) % 1.0, shirt=[(70, 130, 220), (80, 170, 110), (240, 190, 60), (180, 90, 200), (230, 100, 80)][j]), 160 + j * 110 - 320 * clamp01(u * 0.4), 880, 0.38, 3 * math.sin(t * 14 + j))
        return cam(im, u, 1.0, 1.08, 0.5, 0.6)
    im = classroom(clamp01(u * 3.0), t)
    bright = clamp01(u * 3.0)
    d = ImageDraw.Draw(im, "RGBA")
    if bright > 0.2:
        for j in range(14):
            a = j / 14 * 2 * math.pi; r0 = 80 + 900 * ease(bright)
            d.polygon([(960, 520), (960 + math.cos(a) * 1600, 520 + math.sin(a) * 1600), (960 + math.cos(a + 0.12) * 1600, 520 + math.sin(a + 0.12) * 1600)], fill=(255, 240, 160, int(60 * bright))) if j % 2 == 0 else None
    for j, (x, sh) in enumerate(((330, GREEN), (700, BLUE), (1250, (240, 190, 60)), (1600, (230, 100, 80)))):
        put(im, kid("hap" if bright > 0.4 else "meh", 0, "up" if bright > 0.4 else "bored", shirt=sh, backpack=j % 2 == 0), x, 1050, 0.8, (6 * math.sin(t * 8 + j)) if bright > 0.4 else 0)
    rw = pop(t, B[3] + 0.9, 0.5)
    if rw > 0.02:
        bn = Image.new("RGBA", (900, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(bn)
        bd.rounded_rectangle([0, 0, 899, 149], radius=26, fill=GREEN, outline=INK, width=8); bd.text((450, 78), "NEW REWARD: LEARNING", font=font(ANTON, 78), fill=WHITE, anchor="mm", stroke_width=4, stroke_fill=INK)
        put(im, bn, 960, 90, rw, anchor="c")
    return cam(im, u, 1.0, 1.1, 0.5, 0.55)


def caption(im, t):
    ch, t0 = w6.chunk_at(t)
    if not ch:
        return im
    d = ImageDraw.Draw(im)
    size = 92; f = font(ANTON, size)
    words = [w.upper() for w, _, _ in ch]
    sp = d.textlength(" ", font=f) * 1.1; wd = [d.textlength(x, font=f) for x in words]
    x = 960 - (sum(wd) + sp * (len(words) - 1)) / 2; y = 985 - 6 * (1 - w4.eob((t - t0) / 0.14))
    for (w, s, e), word, ww in zip(ch, words, wd):
        on = s - 0.02 <= t < e + 0.05
        d.text((x, y), word, font=f, fill=(255, 226, 90) if on else WHITE, anchor="lm", stroke_width=10, stroke_fill=(20, 16, 18))
        x += ww + sp
    return im


def frame(t):
    im = scene(t).convert("RGB")
    d = ImageDraw.Draw(im)
    d.text((1830, 1040), "DEEP TIME ACADEMY", font=font("Cinzel.ttf", 22), fill=(255, 255, 255), anchor="rm", stroke_width=3, stroke_fill=(30, 20, 20))
    return caption(im, t)


def _chunk(job):
    k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        ff.stdin.write(np.asarray(frame(k / FPS)).tobytes())
    ff.stdin.close(); ff.wait()


if __name__ == "__main__":
    import multiprocessing as mp
    wav = w6.build_audio()
    nf = int(TOTAL * FPS); parts = 8
    tmp = tempfile.mkdtemp(prefix="cartoon_parts_", dir=HERE)
    bounds = [round(nf * i / parts) for i in range(parts + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(tmp, f"part{i}.mp4")) for i in range(parts)]
    with mp.get_context("fork").Pool(4) as pool:
        pool.map(_chunk, jobs)
    open(os.path.join(tmp, "l.txt"), "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    out = p("sample_cartoon.mp4")
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "l.txt"), "-i", wav, "-c:v", "copy",
                    "-af", "alimiter=limit=0.70:level=disabled", "-c:a", "aac", "-ac", "2", "-ar", "44100", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp); print("done", out)
