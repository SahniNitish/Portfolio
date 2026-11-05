"""Deep Time Academy map reel (9:16, 1080x1920): "Greg and the one problem money can't fix".

"Animated history" shorts look: real world map (Natural Earth, public domain) with coloured countries and tiny labels, camera zooming
to each place, cute round-headed cartoon puppets (drawn in code, no image AI), pop-up props, small bottom captions, a sound effect on every cut.
Original script (topic from a Prof. Jiang Xueqin Predictive History clip). Voice: Kokoro draft (swap audio/clean/l1..l10.wav for Fish later).

    python deeptime/wb04-map-reel/episode.py      # renders wb04_map_reel.mp4
"""
import importlib.util, json, math, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import shapefile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import Timeline, finish_audio, place, FPS  # noqa: E402

_spec = importlib.util.spec_from_file_location("wb01", os.path.join(HERE, "..", "wb01-fake-it", "episode.py"))   # reuse wb01 sfx + music
wb = importlib.util.module_from_spec(_spec); sys.modules["wb01"] = wb; _spec.loader.exec_module(wb)

p = lambda *a: os.path.join(HERE, *a)
W, H = 1080, 1920
FONTS = os.path.join(HERE, "..", "..", "assets", "fonts")
N = 10
WORDS = json.load(open(p("words.json")))
GAPS = [0.3] * N
GAPS[0], GAPS[1], GAPS[2], GAPS[4], GAPS[8], GAPS[9] = 0.25, 0.3, 0.4, 0.35, 0.45, 1.6
TL = Timeline([p("audio", "clean", f"l{k}.wav") for k in range(1, N + 1)], GAPS, lead=0.25)
LS = lambda k: TL.L(k - 1)
EN = lambda k: TL.end(k - 1)
AT = lambda k, f: LS(k) + f * (EN(k) - LS(k))
TOTAL = TL.total
clamp01 = lambda x: min(max(x, 0.0), 1.0)
lerp = lambda a, b, u: a + (b - a) * u
ease = lambda x: (lambda y: y * y * (3 - 2 * y))(clamp01(x))
def eob(x, c=1.7):
    x = clamp01(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
pop = lambda t, t0, d=0.35: eob((t - t0) / d)
mix = lambda a, b, u: tuple(int(lerp(x, y, u)) for x, y in zip(a, b))

_fc = {}
def font(name, px):
    k = (name, px)
    if k not in _fc:
        f = ImageFont.truetype(os.path.join(FONTS, name), px)
        if name == "Cinzel.ttf":
            f.set_variation_by_name("Bold")
        _fc[k] = f
    return _fc[k]
ANTON, HAND, MARK, CIN = "Anton.ttf", "PatrickHand-Regular.ttf", "PermanentMarker-Regular.ttf", "Cinzel.ttf"

INK, SKIN = (44, 30, 30), (247, 210, 176)
GOLD, RED, NAVY, CREAM = (240, 190, 60), (214, 52, 52), (24, 34, 70), (252, 244, 220)
SEA, LAND, BORDER = (92, 150, 168), (226, 210, 168), (150, 128, 90)

# ---------------------------------------------------------------- world map
_R = shapefile.Reader(os.path.join(HERE, "..", "assets", "map", "naturalearth_lowres.shp"))
COUNTRIES = {}
for sr in _R.shapeRecords():
    iso, name = sr.record[3], sr.record[2]
    if name == "Antarctica":
        continue
    pts = np.array(sr.shape.points, np.float64)
    parts = list(sr.shape.parts) + [len(pts)]
    rings = []
    for a, b in zip(parts[:-1], parts[1:]):
        r = pts[a:b]
        if len(r) < 3:
            continue
        lon, lat = r[:, 0], np.clip(r[:, 1], -75, 80)
        y = np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))
        rings.append(np.stack([lon, y], 1))
    COUNTRIES[name] = rings
def merc(lat): return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def draw_map(cam, fills, labels=(), jitter=0.0, ss=2):
    """cam=(lon, lat, px_per_degree). fills {country: rgb}. labels [(text, lon, lat, alpha, size)]."""
    lon0, lat0, z = cam
    cx, cy = lon0, merc(lat0)
    im = Image.new("RGB", (W * ss, H * ss), SEA)
    d = ImageDraw.Draw(im)
    for name, rings in COUNTRIES.items():
        col = fills.get(name, LAND)
        for r in rings:
            x = ((r[:, 0] - cx) * z + W / 2) * ss
            y = ((-(r[:, 1] - cy)) * z + H / 2) * ss
            if x.max() < -20 or x.min() > W * ss + 20 or y.max() < -20 or y.min() > H * ss + 20:
                continue
            pts = list(zip(x.tolist(), y.tolist()))
            d.polygon(pts, fill=col)
            d.line(pts + [pts[0]], fill=BORDER, width=max(2, int(z * ss * 0.05)), joint="curve")
    im = im.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    for text, lo, la, a, size in labels:
        if a <= 0.02:
            continue
        x = (lo - cx) * z + W / 2; y = -(merc(la) - cy) * z + H / 2
        d.text((x, y), text, font=font(CIN, size), fill=(70, 46, 24, int(255 * a)), anchor="mm")
    return im


# ---------------------------------------------------------------- puppets and props (flat vector sprites, drawn 2x then reduced)
SS = 2
def canvas(w, h):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)
def done(im, w, h): return im.resize((w, h), Image.LANCZOS)
def S(v): return v * SS
def el(d, cx, cy, rx, ry, fill, w=6, out=INK):
    d.ellipse([S(cx - rx), S(cy - ry), S(cx + rx), S(cy + ry)], fill=fill, outline=out if w else None, width=S(w))
def rr(d, x0, y0, x1, y1, r, fill, w=6, out=INK):
    d.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(r), fill=fill, outline=out if w else None, width=S(w))
def pg(d, pts, fill, w=6, out=INK):
    d.polygon([(S(x), S(y)) for x, y in pts], fill=fill, outline=None)
    if w:
        d.line([(S(x), S(y)) for x, y in pts + [pts[0]]], fill=out, width=S(w), joint="curve")
def ln(d, pts, w=8, col=INK):
    q = [(S(x), S(y)) for x, y in pts]
    d.line(q, fill=col, width=S(w), joint="curve")
    for x, y in (q[0], q[-1]):
        d.ellipse([x - S(w) / 2, y - S(w) / 2, x + S(w) / 2, y + S(w) / 2], fill=col)
def arc(d, cx, cy, rx, ry, a0, a1, w=8, col=INK):
    d.arc([S(cx - rx), S(cy - ry), S(cx + rx), S(cy + ry)], a0, a1, fill=col, width=S(w))


def face(d, eyes, mouth, tears=False, ex=(235, 365), ey=285, big=1.0, pupil=1.0):
    for x in ex:
        if eyes == "shut":
            arc(d, x, ey + 10, 38, 30, 200, 340, 8)
        elif eyes == "dead":
            ln(d, [(x - 28, ey - 28), (x + 28, ey + 28)], 9); ln(d, [(x + 28, ey - 28), (x - 28, ey + 28)], 9)
        else:
            rx, ry = (50, 60) if eyes == "wide" else (42, 48)
            el(d, x, ey, rx * big, ry * big, (255, 255, 255), 6)
            pr = (9 if eyes == "wide" else 17) * pupil
            el(d, x + (6 if x < 300 else -6), ey + 6, pr, pr * 1.1, INK, 0)
            el(d, x + (6 if x < 300 else -6) - 5, ey, 5, 5, (255, 255, 255), 0)
    if eyes == "sad":
        ln(d, [(190, 215), (265, 238)], 9); ln(d, [(410, 215), (335, 238)], 9)
    if eyes == "wide":
        ln(d, [(190, 205), (270, 195)], 9); ln(d, [(410, 205), (330, 195)], 9)
    el(d, 185, 350, 28, 18, (255, 140, 130), 0); el(d, 415, 350, 28, 18, (255, 140, 130), 0)
    m = (300, 392)
    if mouth == "smile":
        arc(d, m[0], m[1] - 20, 55, 42, 20, 160, 9)
    elif mouth == "grin":
        pg(d, [(235, 375), (365, 375), (345, 425), (255, 425)], (255, 255, 255), 6)
    elif mouth == "o":
        el(d, m[0], m[1] + 14, 52, 66, (92, 24, 36), 7); el(d, m[0], m[1] + 48, 34, 20, (232, 110, 120), 0)
    elif mouth == "flat":
        ln(d, [(255, 400), (345, 400)], 9)
    elif mouth == "frown":
        arc(d, m[0], m[1] + 38, 50, 36, 200, 340, 9)
    elif mouth == "cry":
        pg(d, [(235, 400), (365, 400), (350, 440), (250, 440)], (92, 24, 36), 7)
    if tears:
        for x in ex:
            pg(d, [(x - 8, ey + 50), (x + 8, ey + 50), (x + 26, ey + 150), (x - 26, ey + 150)], (120, 190, 255), 0)
            el(d, x, ey + 156, 28, 18, (120, 190, 255), 0)


def puppet(kind, eyes="open", mouth="smile", arms="down", sweat=False, tears=False, grey=False, items=()):
    w, h = 600, 820
    im, d = canvas(w, h)
    robe = {"greg": (34, 34, 52), "reaper": (30, 26, 44), "emperor": (190, 38, 42)}[kind]
    skin = SKIN if kind != "reaper" else (236, 236, 244)
    if grey:
        robe = mix(robe, (150, 150, 156), 0.8); skin = (176, 178, 184)
    if kind == "reaper":
        pg(d, [(95, 120), (300, -10 + 20), (505, 120), (560, 360), (40, 360)], robe, 6)
        el(d, 300, 255, 235, 235, robe, 6)
    # legs and shoes
    for x in (255, 345):
        rr(d, x - 24, 680, x + 24, 780, 18, robe if kind != "reaper" else (20, 18, 30), 6)
        el(d, x + (-12 if x < 300 else 12), 790, 42, 22, (20, 18, 30), 6)
    if kind == "reaper":
        pg(d, [(190, 430), (410, 430), (490, 790), (110, 790)], robe, 6)
    else:
        rr(d, 190, 430, 410, 700, 70, robe, 6)
    shoulders = ((205, 485), (395, 485))
    hands = {"down": ((150, 640), (450, 640)), "up": ((85, 300), (515, 300)), "point": ((40, 520), (440, 650)),
             "hug": ((275, 600), (325, 600)), "wave": ((150, 640), (520, 330)), "hold": ((250, 585), (350, 585)),
             "shrug": ((95, 520), (505, 520)), "sip": ((150, 640), (330, 380))}[arms]
    armcol = robe if kind != "emperor" else (170, 30, 36)
    aw = 56 if kind != "emperor" else 84
    for s_, hnd in zip(shoulders, hands):
        ln(d, [s_, hnd], aw + 12, INK); ln(d, [s_, hnd], aw, armcol)
        if kind != "emperor":
            el(d, hnd[0], hnd[1], 34, 34, skin, 6)
        else:
            el(d, hnd[0], hnd[1], 30, 30, skin, 6)
    # outfit details on body
    if kind == "greg":
        pg(d, [(300, 436), (262, 470), (300, 510), (338, 470)], (255, 255, 255), 0)
        pg(d, [(300, 460), (255, 440), (255, 482)], RED, 5); pg(d, [(300, 460), (345, 440), (345, 482)], RED, 5); el(d, 300, 461, 12, 12, RED, 5)
        for i in range(11):
            a = i / 10
            x = lerp(225, 375, a); y = 500 + 90 * math.sin(a * math.pi)
            el(d, x, y, 12, 12, GOLD, 4)
        el(d, 300, 604, 24, 24, GOLD, 5)
    if kind == "emperor":
        rr(d, 255, 430, 345, 700, 10, (240, 190, 60), 5)
        el(d, 300, 560, 46, 46, (240, 190, 60), 5); el(d, 300, 560, 22, 22, (190, 38, 42), 0)
    if kind == "reaper":
        rr(d, 218, 520, 382, 700, 10, CREAM, 6)
        for i in range(5):
            ln(d, [(240, 550 + i * 28), (360 if i % 2 else 330, 550 + i * 28)], 5, (120, 110, 100))
    # head
    el(d, 300, 290, 168, 160, skin, 7)
    if kind == "greg":
        el(d, 142, 300, 26, 40, skin, 6); el(d, 458, 300, 26, 40, skin, 6)
    face(d, eyes, mouth, tears, big=1.08 if kind == "reaper" else 1.0, pupil=1.4 if kind == "reaper" else 1.0)
    if kind == "greg":
        for sx in (-1, 1):
            pg(d, [(300 + sx * 8, 352), (300 + sx * 110, 340), (300 + sx * 170, 395), (300 + sx * 120, 372), (300 + sx * 8, 384)], (250, 250, 250), 6)
        el(d, 365, 285, 62, 62, None, 0)
        d.ellipse([S(365 - 62), S(285 - 62), S(365 + 62), S(285 + 62)], outline=GOLD, width=S(9))
        ln(d, [(420, 300), (470, 470)], 3, GOLD)
        el(d, 300, 130, 150, 26, (20, 20, 30), 6)
        rr(d, 205, 10, 395, 135, 16, (24, 24, 34), 6); rr(d, 205, 96, 395, 128, 4, RED, 0)
        ln(d, [(205, 96), (395, 96)], 4, INK); ln(d, [(205, 128), (395, 128)], 4, INK)
    if kind == "emperor":
        ln(d, [(265, 380), (225, 480)], 8); ln(d, [(335, 380), (375, 480)], 8)
        rr(d, 150, 118, 450, 150, 10, (24, 24, 34), 6); ln(d, [(150, 134), (450, 134)], 5, GOLD)
        for bx in (172, 428):
            for i in range(7):
                el(d, bx, 168 + i * 17, 9, 9, (255, 255, 255), 3)
        rr(d, 190, 100, 410, 122, 6, (40, 40, 52), 5)
    if kind == "reaper":
        pg(d, [(110, 215), (300, 70), (490, 215), (470, 160), (300, 20), (130, 160)], robe, 6)
        pg(d, [(125, 250), (180, 150), (300, 120), (420, 150), (475, 250)], robe, 0)
        el(d, 300, 290, 168, 160, None, 0)
    if sweat:
        pg(d, [(480, 150), (462, 200), (498, 200)], (140, 205, 255), 4); el(d, 480, 204, 20, 18, (140, 205, 255), 4)
    return done(im, w, h)


_pc = {}
def PUP(kind, **kw):
    k = (kind, tuple(sorted(kw.items())))
    if k not in _pc:
        _pc[k] = puppet(kind, **kw)
    return _pc[k]


def prop(kind, **kw):
    if kind == "pile":
        w, h = 560, 300; im, d = canvas(w, h)
        rows = [(6, 250), (5, 200), (4, 150), (3, 100), (2, 52), (1, 6)]
        for c, y in rows:
            for i in range(c):
                x = w / 2 + (i - (c - 1) / 2) * 90
                el(d, x, y + 40, 56, 30, GOLD, 5)
                d.text((S(x), S(y + 38)), "$", font=font(MARK, S(42)), fill=(130, 84, 10), anchor="mm")
        return done(im, w, h)
    if kind == "jet":
        w, h = 520, 200; im, d = canvas(w, h)
        pg(d, [(20, 100), (120, 70), (400, 70), (500, 100), (400, 130), (120, 130)], (250, 250, 255), 6)
        pg(d, [(200, 100), (320, 20), (360, 20), (320, 100)], (190, 205, 235), 6); pg(d, [(200, 100), (320, 180), (360, 180), (320, 100)], (190, 205, 235), 6)
        pg(d, [(40, 96), (50, 20), (90, 20), (110, 96)], RED, 6)
        for i in range(6):
            el(d, 160 + i * 36, 90, 9, 9, (110, 160, 220), 3)
        return done(im, w, h)
    if kind == "yacht":
        w, h = 560, 300; im, d = canvas(w, h)
        pg(d, [(20, 170), (540, 170), (470, 260), (90, 260)], (250, 250, 255), 6)
        pg(d, [(40, 190), (520, 190), (508, 208), (52, 208)], (60, 110, 190), 0)
        rr(d, 120, 100, 400, 170, 14, (250, 250, 255), 6); rr(d, 190, 50, 340, 100, 12, (250, 250, 255), 6)
        for i in range(5):
            rr(d, 140 + i * 50, 120, 170 + i * 50, 145, 5, (120, 175, 230), 3)
        ln(d, [(440, 170), (440, 30)], 6); pg(d, [(440, 30), (500, 48), (440, 66)], RED, 4)
        return done(im, w, h)
    if kind == "toilet":
        w, h = 360, 400; im, d = canvas(w, h)
        G2 = (255, 224, 110)
        rr(d, 90, 30, 270, 190, 24, GOLD, 6); rr(d, 110, 18, 250, 50, 12, G2, 5)
        el(d, 180, 250, 130, 52, G2, 6); rr(d, 130, 240, 230, 360, 30, GOLD, 6); rr(d, 110, 345, 250, 385, 14, GOLD, 6)
        ln(d, [(110, 70), (110, 160)], 8, (255, 250, 200))
        for pos in ((60, 70), (300, 120), (250, 20)):
            ln(d, [(pos[0] - 18, pos[1]), (pos[0] + 18, pos[1])], 5, (255, 250, 200)); ln(d, [(pos[0], pos[1] - 18), (pos[0], pos[1] + 18)], 5, (255, 250, 200))
        return done(im, w, h)
    if kind == "junk":
        w, h = 560, 460; im, d = canvas(w, h)
        pg(d, [(40, 340), (520, 340), (450, 420), (110, 420)], (140, 80, 40), 6)
        ln(d, [(280, 340), (280, 30)], 10)
        pg(d, [(290, 50), (500, 80), (470, 320), (290, 330)], (200, 40, 40), 6)
        for i in range(1, 5):
            ln(d, [(290, 50 + i * 56), (500 - i * 6, 80 + i * 56)], 5, (120, 20, 20))
        pg(d, [(268, 50), (268, 20), (200, 36)], GOLD, 4)
        return done(im, w, h)
    if kind == "flask":
        col = kw.get("col", (150, 156, 170))
        w, h = 320, 420; im, d = canvas(w, h)
        pg(d, [(125, 30), (195, 30), (200, 150), (290, 330), (250, 395), (70, 395), (30, 330), (120, 150)], (230, 240, 250), 6)
        pg(d, [(60, 270), (260, 270), (290, 330), (250, 395), (70, 395), (30, 330)], col, 0)
        pg(d, [(125, 30), (195, 30), (200, 150), (290, 330), (250, 395), (70, 395), (30, 330), (120, 150)], None, 6) if False else None
        ln(d, [(125, 30), (120, 150), (30, 330), (70, 395), (250, 395), (290, 330), (200, 150), (195, 30)], 7)
        rr(d, 108, 14, 212, 44, 10, (120, 80, 50), 6)
        for x, y, r in ((130, 320, 14), (180, 345, 10), (215, 310, 12)):
            el(d, x, y, r, r, (255, 255, 255), 0)
        if kw.get("skull"):
            el(d, 160, 330, 26, 24, (250, 250, 250), 4); el(d, 150, 326, 6, 7, INK, 0); el(d, 172, 326, 6, 7, INK, 0)
        return done(im, w, h)
    if kind == "mouse":
        w, h = 260, 240; im, d = canvas(w, h)
        ln(d, [(225, 150), (255, 110), (240, 70)], 8, (240, 150, 170))
        el(d, 150, 140, 82, 60, (186, 190, 200), 6)
        pg(d, [(95, 110), (125, 100), (135, 190), (90, 195)], (34, 34, 52), 5)
        pg(d, [(112, 110), (96, 134), (128, 134)], RED, 4)
        el(d, 70, 100, 46, 40, (196, 200, 210), 6); el(d, 70, 54, 24, 24, (255, 170, 190), 6)
        el(d, 58, 94, 8, 9, INK, 0); el(d, 28, 108, 8, 7, (255, 120, 140), 0)
        ln(d, [(36, 120), (18, 130)], 3); ln(d, [(36, 126), (14, 142)], 3)
        return done(im, w, h)
    if kind == "coffin":
        w, h = 380, 580; im, d = canvas(w, h)
        pg(d, [(120, 20), (260, 20), (350, 180), (280, 560), (100, 560), (30, 180)], (126, 78, 44), 7)
        ln(d, [(190, 100), (190, 300)], 12, GOLD); ln(d, [(130, 170), (250, 170)], 12, GOLD)
        return done(im, w, h)
    if kind == "bell":
        w, h = 140, 150; im, d = canvas(w, h)
        pg(d, [(30, 110), (36, 60), (70, 20), (104, 60), (110, 110)], GOLD, 6); ln(d, [(18, 112), (122, 112)], 9); el(d, 70, 128, 12, 12, GOLD, 5)
        return done(im, w, h)
    raise KeyError(kind)


_prc = {}
def PROP(kind, **kw):
    k = (kind, tuple(sorted(kw.items())))
    if k not in _prc:
        _prc[k] = prop(kind, **kw)
    return _prc[k]


def put(img, spr, x, y, s=1.0, rot=0.0, a=1.0, flip=False, anchor="bm"):
    """paste sprite with anchor 'bm' (bottom centre) or 'c' at (x, y)."""
    if s <= 0.01 or a <= 0.01:
        return
    if flip:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
    w, h = spr.size
    sp = spr.resize((max(1, int(w * s)), max(1, int(h * s))), Image.BILINEAR) if abs(s - 1) > 0.005 else spr
    if abs(rot) > 0.1:
        sp = sp.rotate(rot, resample=Image.BILINEAR, expand=True)
    if a < 0.99:
        al = sp.getchannel("A").point(lambda v: int(v * a)); sp = sp.copy(); sp.putalpha(al)
    px = int(x - sp.width / 2)
    py = int(y - sp.height) if anchor == "bm" else int(y - sp.height / 2)
    img.paste(sp, (px, py), sp)


def pill(img, text, x, y, t, t0, size=70, bg=GOLD, fg=NAVY, rot=-3, font_=ANTON):
    s = pop(t, t0, 0.4)
    if s <= 0.02:
        return
    f = font(font_, size)
    d0 = ImageDraw.Draw(img); tw = d0.textlength(text, font=f)
    w, h = int(tw + 70), int(size * 1.5)
    sp = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    d.rounded_rectangle([6, 6, w + 6, h + 6], radius=h // 2, fill=bg, outline=INK, width=6)
    d.text(((w + 12) / 2, (h + 12) / 2 + 2), text, font=f, fill=fg, anchor="mm")
    put(img, sp, x, y, s, rot, anchor="c")


def bubble(img, text, x, y, t, t0, tail=(0, 80), size=46, flip=False):
    s = pop(t, t0, 0.3)
    if s <= 0.02:
        return
    f = font(HAND, size); d0 = ImageDraw.Draw(img)
    lines = text.split("\n"); tw = max(d0.textlength(l, font=f) for l in lines)
    w, h = int(tw + 60), int(size * 1.3 * len(lines) + 36)
    sp = Image.new("RGBA", (w + 80, h + 140), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
    ox, oy = 40, 20
    d.rounded_rectangle([ox, oy, ox + w, oy + h], radius=34, fill=(255, 255, 255), outline=INK, width=6)
    tx = ox + w / 2 + tail[0] * 0.3
    d.polygon([(ox + w / 2 - 30 + tail[0] * .2, oy + h - 3), (ox + w / 2 + 30 + tail[0] * .2, oy + h - 3), (tx + tail[0] * .3, oy + h + 90)], fill=(255, 255, 255), outline=INK)
    d.polygon([(ox + w / 2 - 26 + tail[0] * .2, oy + h - 8), (ox + w / 2 + 26 + tail[0] * .2, oy + h - 8), (tx + tail[0] * .3, oy + h + 82)], fill=(255, 255, 255))
    for i, l in enumerate(lines):
        d.text((ox + w / 2, oy + 18 + size * 1.3 * (i + 0.5)), l, font=f, fill=INK, anchor="mm")
    put(img, sp, x, y, s, anchor="c")


# ---------------------------------------------------------------- captions (small, bottom, current word yellow)
def make_chunks():
    ch = []
    for k in range(1, N + 1):
        ws = [(w, LS(k) + s, LS(k) + e) for w, s, e in WORDS[str(k)]]
        cur = []
        for i, wd in enumerate(ws):
            cur.append(wd)
            if len(cur) >= 4 or wd[0][-1] in ".,?!:;" or (i + 1 < len(ws) and ws[i + 1][1] - wd[2] > 0.35):
                ch.append(cur); cur = []
        if cur:
            ch.append(cur)
    return ch
CHUNKS = make_chunks()


def draw_caption(img, t):
    for i, ch in enumerate(CHUNKS):
        t0 = ch[0][1] - 0.03
        nxt = CHUNKS[i + 1][0][1] - 0.03 if i + 1 < len(CHUNKS) else 1e9
        t1 = nxt if nxt - ch[-1][2] < 0.6 else ch[-1][2] + 0.3
        if t0 <= t < t1:
            break
    else:
        return
    d = ImageDraw.Draw(img)
    size = 76
    f = font(ANTON, size)
    words = [w.upper() for w, _, _ in ch]
    sp = d.textlength(" ", font=f) * 1.1
    widths = [d.textlength(w, font=f) for w in words]
    total = sum(widths) + sp * (len(words) - 1)
    while total > 940 and size > 40:
        size -= 4; f = font(ANTON, size); widths = [d.textlength(w, font=f) for w in words]; sp = d.textlength(" ", font=f) * 1.1
        total = sum(widths) + sp * (len(words) - 1)
    x = 540 - total / 2; y = 1560 - 6 * (1 - eob((t - t0) / 0.12))
    for (w, ws, we), word, wd in zip(ch, words, widths):
        on = ws - 0.02 <= t < we + 0.05
        d.text((x, y), word, font=f, fill=GOLD if on else (255, 255, 255), anchor="lm", stroke_width=9, stroke_fill=(20, 20, 30))
        x += wd + sp


def vignette(img):
    v = _VIG
    return Image.composite(Image.new("RGB", (W, H), (10, 20, 30)), img, v)


def _mk_vig():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    a = np.clip((r - 0.55) / 0.6, 0, 1) ** 1.6 * 0.55
    return Image.fromarray((a * 255).astype(np.uint8))
_VIG = _mk_vig()

# ---------------------------------------------------------------- scenes
USA = {"United States of America": (74, 112, 196), "Canada": (212, 68, 70), "Mexico": (232, 150, 70)}
CHINA = {"China": (212, 68, 70), "Mongolia": (232, 150, 70), "Japan": (90, 160, 130), "South Korea": (74, 112, 196)}


def bob(t, a=8, f=3.0, ph=0.0): return a * math.sin(t * f + ph)


def sc1(t):
    u = (t - LS(1)) / (EN(1) - LS(1) + 0.4)
    cam = (-98 - 4 * u, 41, lerp(15, 18, ease(u)))
    labels = [("UNITED STATES", -99, 39, pop(t, LS(1) + 0.3, 0.4), 40), ("CANADA", -100, 57, 1, 36), ("MEXICO", -102, 24, 1, 34)]
    im = draw_map(cam, USA, labels)
    s = pop(t, LS(1) + 0.15, 0.45)
    put(im, PROP("pile"), 540, 1330, 1.55 * s)
    put(im, PUP("greg", eyes="open", mouth="grin", arms="up"), 540, 1330 - 120, 1.05 * s, bob(t, 3, 4))
    pill(im, "$10,000,000,000", 540, 560, t, AT(1, 0.55), 72)
    for k in range(10):
        tt = (t - AT(1, 0.5) + k * 0.12)
        if tt > 0:
            fy = 700 + (tt * 520) % 760
            put(im, PROP("pile").resize((60, 32)), 120 + (k * 97) % 840, fy, 1.0, 14 * math.sin(tt * 5 + k), anchor="c")
    return im


def sc2(t):
    u = (t - LS(2)) / (EN(2) - LS(2))
    im = draw_map((-98, 38, lerp(18, 20, u)), USA, [("UNITED STATES", -99, 39, 1, 40)])
    put(im, PUP("greg", eyes="wide", mouth="o", arms="shrug", sweat=u > 0.7), 540, 1450, 1.0, bob(t, 3, 5))
    jx = lerp(1300, -300, ease(clamp01((t - AT(2, 0.05)) / 0.9)))
    put(im, PROP("jet"), jx, 700 + 30 * math.sin(t * 6), 1.3, -6, anchor="c")
    pill(im, "JET", 250, 1040, t, AT(2, 0.18), 64, rot=-6)
    put(im, PROP("yacht"), 780, 1210, pop(t, AT(2, 0.33), 0.35) * 1.0, 2 * math.sin(t * 3))
    pill(im, "YACHT", 780, 1040, t, AT(2, 0.42), 64, rot=5)
    put(im, PROP("toilet"), 190, 1250, pop(t, AT(2, 0.6), 0.35) * 0.9)
    pill(im, "GOLDEN TOILET", 330, 880, t, AT(2, 0.66), 56, rot=-4)
    if t > AT(2, 0.82):
        pill(im, "ONE PROBLEM", 540, 480, t, AT(2, 0.82), 90, bg=RED, fg=(255, 255, 255), rot=3)
    return im


def sc3(t):
    u = (t - LS(3)) / (EN(3) - LS(3))
    im = draw_map((-90 + 6 * u, 38, 16), USA, [])
    im = Image.blend(im, Image.new("RGB", (W, H), (20, 24, 40)), 0.35)
    rx = lerp(1350, 800, ease(clamp01((t - LS(3) - 0.1) / 0.5)))
    put(im, PUP("reaper", eyes="open", mouth="flat", arms="hold"), rx, 1450, 1.0, bob(t, 4, 3))
    sweaty = t > AT(3, 0.1)
    put(im, PUP("greg", eyes="wide" if sweaty else "open", mouth="o" if t > AT(3, 0.5) else "frown", arms="shrug", sweat=sweaty), 300, 1450, 1.0, bob(t, 3, 5))
    bubble(im, "Can I pay\nextra?", 300, 780, t, AT(3, 0.40), tail=(10, 80), size=56)
    bubble(im, "Sir, this is\nnot Uber.", 790, 780, t, AT(3, 0.70), tail=(-10, 80), size=56)
    pill(im, "DEATH", 800, 560, t, AT(3, 0.1), 60, bg=(30, 26, 44), fg=(255, 255, 255), rot=4)
    return im


def sc4(t):
    u = (t - LS(4)) / (EN(4) - LS(4))
    cam = (lerp(112, 128, ease(u)), 34, lerp(13, 11, u))
    labels = [("CHINA", 104, 35, 1, 44), ("JAPAN", 138, 37, 1, 30), ("~ 220 BC", 106, 24, pop(t, LS(4) + 0.2, 0.4), 36)]
    im = draw_map(cam, CHINA, labels)
    # dotted route from the coast to the east
    d = ImageDraw.Draw(im, "RGBA")
    x0, y0 = (121 - cam[0]) * cam[2] + W / 2, -(merc(31) - merc(cam[1])) * cam[2] + H / 2
    x1, y1 = (150 - cam[0]) * cam[2] + W / 2, -(merc(34) - merc(cam[1])) * cam[2] + H / 2
    prog = ease(clamp01((t - AT(4, 0.35)) / 0.55))
    for i in range(24):
        a = i / 23
        if a <= prog:
            d.ellipse([lerp(x0, x1, a) - 8, lerp(y0, y1, a) - 8 - 60 * math.sin(a * math.pi), lerp(x0, x1, a) + 8, lerp(y0, y1, a) + 8 - 60 * math.sin(a * math.pi)], fill=(190, 40, 40, 255))
    sx, sy = lerp(x0, x1, prog), lerp(y0, y1, prog) - 60 * math.sin(prog * math.pi)
    put(im, PROP("junk"), sx, sy + 90, 0.75 * pop(t, AT(4, 0.3), 0.4), 4 * math.sin(t * 3))
    put(im, PUP("emperor", eyes="open", mouth="grin", arms="point"), 280, 1480, 0.95 * pop(t, LS(4) + 0.1, 0.5), bob(t, 3, 4))
    pill(im, "FIRST EMPEROR", 300, 1160, t, AT(4, 0.15), 50, rot=-3)
    pill(im, "FIND ME ETERNAL LIFE!", 540, 400, t, AT(4, 0.55), 56, bg=(255, 255, 255), rot=2)
    return im


def sc5(t):
    u = (t - LS(5)) / (EN(5) - LS(5))
    im = draw_map((108, 33, 15 + 3 * u), CHINA, [("CHINA", 104, 35, 1, 50)])
    im = Image.blend(im, Image.new("RGB", (W, H), (40, 30, 50)), 0.25 + 0.3 * u)
    drank = t > AT(5, 0.5)
    grey = t > AT(5, 0.62)
    arms = "sip" if 0.2 < u < 0.55 else "down"
    em = PUP("emperor", eyes="dead" if grey else ("wide" if drank else "open"), mouth="o" if drank else "smile", arms=arms, grey=grey, sweat=drank)
    put(im, em, 540, 1480, 1.05, bob(t, 3, 4) if not grey else 8 * math.sin(t * 20))
    if t > AT(5, 0.66):
        gu = clamp01((t - AT(5, 0.66)) / 0.9)
        put(im, em, 540, 1480 - 500 * ease(gu), 1.0, 0, a=0.5 * (1 - gu))   # ghost floats up
    if t < AT(5, 0.5):
        put(im, PROP("flask", col=(150, 156, 170), skull=True), lerp(160, 700, 0.5) + 150 * math.sin(u * 3) * 0, 1000, 0.9 * pop(t, LS(5) + 0.1, 0.4), bob(t, 8, 2) * 1)
    pill(im, "MERCURY", 340, 520, t, AT(5, 0.3), 80, bg=(190, 195, 205), rot=-6)
    pill(im, "NOT A VITAMIN", 700, 420, t, AT(5, 0.8), 62, bg=RED, fg=(255, 255, 255), rot=4)
    return im


def sc6(t):
    u = (t - LS(6)) / (EN(6) - LS(6))
    cam = (lerp(-100, -121, ease(u * 1.2)), lerp(40, 37.5, ease(u * 1.2)), lerp(15, 30, ease(u * 1.2)))
    im = draw_map(cam, USA, [("CALIFORNIA", -119.5, 37, clamp01((u - 0.4) * 3), 38)])
    cxp, cyp = (-122 - cam[0]) * cam[2] + W / 2, -(merc(37.4) - merc(cam[1])) * cam[2] + H / 2
    pin = pop(t, AT(6, 0.45), 0.4)
    d = ImageDraw.Draw(im, "RGBA")
    if pin > 0.02:
        d.polygon([(cxp, cyp), (cxp - 34 * pin, cyp - 70 * pin), (cxp + 34 * pin, cyp - 70 * pin)], fill=RED, outline=INK)
        d.ellipse([cxp - 40 * pin, cyp - 112 * pin, cxp + 40 * pin, cyp - 36 * pin], fill=RED, outline=INK, width=6)
        d.ellipse([cxp - 14 * pin, cyp - 88 * pin, cxp + 14 * pin, cyp - 60 * pin], fill=(255, 255, 255))
    pill(im, "ALTOS LABS", 540, 470, t, AT(6, 0.5), 76)
    pill(im, "2021 • $3 BILLION", 540, 620, t, AT(6, 0.78), 64, bg=(255, 255, 255), rot=2)
    put(im, PROP("flask", col=(90, 200, 120)), 220, 1450, 1.0 * pop(t, LS(6) + 0.2, 0.4), bob(t, 4, 3))
    put(im, PROP("flask", col=(110, 170, 240)), 860, 1450, 1.0 * pop(t, LS(6) + 0.35, 0.4), bob(t, 4, 3, 1))
    put(im, PROP("mouse"), 540, 1450, 1.9 * pop(t, AT(6, 0.55), 0.4), bob(t, 4, 6))
    return im


def sc7(t):
    u = (t - LS(7)) / (EN(7) - LS(7))
    im = draw_map((-98, 38, 17), USA, [])
    im = Image.blend(im, Image.new("RGB", (W, H), (20, 24, 40)), 0.25)
    put(im, PROP("pile"), 380, 1450, 1.2)
    put(im, PUP("greg", eyes="wide", mouth="cry", arms="hug", sweat=True), 400, 1330, 0.95, bob(t, 3, 8))
    put(im, PUP("reaper", eyes="open", mouth="flat", arms="point"), 880, 1480, 0.8, bob(t, 3, 3))
    pill(im, "SUNK COST", 540, 400, t, LS(7) + 0.1, 90, bg=RED, fg=(255, 255, 255), rot=-4)
    ky = lerp(1900, 1300, ease(clamp01((t - AT(7, 0.45)) / 0.4)))
    yx = lerp(180, 760, ease(clamp01((t - AT(7, 0.6)) / 0.35)))
    put(im, PROP("coffin"), 760, 1480, 0.7 * pop(t, AT(7, 0.4), 0.4))
    if t > AT(7, 0.55):
        put(im, PROP("yacht"), yx, 1060 + 40 * (1 - clamp01((t - AT(7, 0.6)) / 0.35)), 0.55, 20 * ease(clamp01((t - AT(7, 0.6)) / 0.35)), anchor="c")
    return im


EMP = [("Italy", (84, 160, 96), "ROME", 12.5, 42.5, 0.08), ("Mongolia", (232, 150, 70), "MONGOLS", 103, 46.5, 0.26), ("United Kingdom", (212, 68, 70), "BRITAIN", -2, 54, 0.44)]


def sc8(t):
    u = (t - LS(8)) / (EN(8) - LS(8))
    z = lerp(7.2, 5.2, ease(u))
    cam = (lerp(30, 40, u), 42, z)
    fills, labels = {}, []
    crumble = clamp01((u - 0.7) / 0.3)
    for name, col, lab, lo, la, f0 in EMP:
        if u >= f0:
            k = ease((u - f0) / 0.05)
            c = mix(LAND, col, k)
            if crumble > 0:
                c = mix(c, (170, 170, 170), crumble)
            fills[name] = c
            labels.append((lab, lo, la, k * (1 - crumble * 0.6), 34))
    im = draw_map(cam, fills, labels)
    pill(im, "EMPIRES RISE", 540, 420, t, AT(8, 0.1), 80, bg=(84, 170, 100), fg=(255, 255, 255), rot=-3)
    if crumble > 0:
        pill(im, "EMPIRES CRUMBLE", 540, 560, t, AT(8, 0.72), 80, bg=RED, fg=(255, 255, 255), rot=3)
        put(im, PUP("greg", eyes="wide", mouth="o", arms="up", sweat=True), 540, 1500, 0.75 * pop(t, AT(8, 0.72), 0.4), 6 * math.sin(t * 16))
    return im


def sc9(t):
    u = (t - LS(9)) / (EN(9) - LS(9))
    im = draw_map((-98, 38, 16), {"United States of America": (140, 140, 150), "Canada": (150, 150, 160), "Mexico": (150, 150, 160)}, [])
    im = Image.blend(im, Image.new("RGB", (W, H), (14, 16, 28)), 0.55)
    put(im, PUP("greg", eyes="sad", mouth="cry", arms="down", tears=True, sweat=True), 540, 1480, 1.05, bob(t, 3, 5))
    sp = pop(t, AT(9, 0.45), 0.4)
    if sp > 0.02:
        scr = Image.new("RGBA", (720, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(scr)
        d.rounded_rectangle([0, 0, 719, 359], radius=26, fill=(8, 10, 16), outline=(90, 255, 140), width=8)
        d.text((360, 90), "GAME OVER", font=font(ANTON, 96), fill=(90, 255, 140), anchor="mm")
        d.text((360, 190), "WEALTH: $0", font=font(ANTON, 60), fill=(90, 255, 140), anchor="mm")
        d.text((360, 275), "RESTART?" + ("  _" if int(t * 3) % 2 else ""), font=font(ANTON, 60), fill=(255, 255, 255), anchor="mm")
        put(im, scr, 540, 540, sp, anchor="c")
    pill(im, "THEY FEAR STARTING OVER", 540, 270, t, AT(9, 0.1), 54, bg=RED, fg=(255, 255, 255), rot=-2)
    return im


def sc10(t):
    u = (t - LS(10)) / (EN(10) - LS(10) + 1.6)
    im = draw_map((lerp(-60, -30, u), 30, lerp(5, 3.4, ease(u))), {"United States of America": (74, 112, 196), "China": (212, 68, 70)}, [])
    put(im, PUP("greg", eyes="open", mouth="grin", arms="wave"), 330, 1480, 0.95, bob(t, 3, 5))
    put(im, PUP("reaper", eyes="open", mouth="smile", arms="wave"), 790, 1480, 0.85, bob(t, 3, 5, 1))
    clicked = t > AT(10, 0.55)
    s = pop(t, LS(10) + 0.1, 0.45)
    pill(im, "FOLLOWING" if clicked else "FOLLOW", 500, 470, t, LS(10) + 0.1, 100, bg=(130, 130, 140) if clicked else RED, fg=(255, 255, 255), rot=0)
    if clicked:
        put(im, PROP("bell"), 930, 400, 1.4 * pop(t, AT(10, 0.55), 0.3), 14 * math.sin(t * 22), anchor="c")
    pill(im, "PART 2 SOON", 540, 590, t, AT(10, 0.7), 60, bg=(255, 255, 255), rot=2)
    return im


SCENES = [(0.0, sc1)] + [(LS(i) - 0.08, f) for i, f in zip(range(2, 11), (sc2, sc3, sc4, sc5, sc6, sc7, sc8, sc9, sc10))]
XF = 0.1


def decorate(im, t):
    im = vignette(im)
    d = ImageDraw.Draw(im)
    d.text((540, 92), "DEEP TIME ACADEMY", font=font(CIN, 30), fill=(235, 235, 240), anchor="mm", stroke_width=4, stroke_fill=(20, 30, 40))
    draw_caption(im, t)
    return im


def frame_at(t):
    k = max(i for i, (s, _) in enumerate(SCENES) if s <= t)
    s0, fn = SCENES[k]
    im = fn(t).convert("RGB")
    if k > 0 and t - s0 < XF:
        pv = SCENES[k - 1][1](t).convert("RGB")
        im = Image.blend(pv, im, ease((t - s0) / XF))
    return decorate(im, t)


# ---------------------------------------------------------------- audio
FXT = [(1, .15, "pop"), (1, .30, "boing"), (1, .55, "ding"), (2, .05, "whoosh"), (2, .18, "pop"), (2, .42, "pop"), (2, .66, "pop"), (2, .82, "stamp"),
       (3, .10, "boing"), (3, .40, "pop"), (3, .70, "pop"), (3, .93, "buzzer"), (4, .15, "pop"), (4, .35, "whoosh"), (4, .55, "ding"),
       (5, .30, "pop"), (5, .50, "thud"), (5, .62, "boom"), (5, .80, "stamp"), (6, .20, "pop"), (6, .45, "ding"), (6, .55, "pop"), (6, .78, "ding"),
       (7, .10, "stamp"), (7, .40, "pop"), (7, .60, "boing"), (7, .90, "thud"), (8, .10, "ding"), (8, .38, "ding"), (8, .60, "ding"), (8, .72, "smash"),
       (9, .10, "pop"), (9, .45, "buzzer"), (10, .10, "pop"), (10, .55, "click"), (10, .56, "ding"), (10, .70, "pop")]


def build_audio():
    voice = TL.voice_track()
    fx = np.zeros_like(voice)
    mus = wb.music_fun(TOTAL, level=0.2)[:len(voice)]
    for s, _ in SCENES[1:]:
        place(fx, wb.SFXF["whoosh"](), s - 0.2)
    for ch in CHUNKS:
        place(fx, wb.SFXF["tick"]() * 0.3, ch[0][1] - 0.03)
    for k, fr, name in FXT:
        place(fx, wb.SFXF[name](), AT(k, fr))
    out = p("_mix.wav")
    finish_audio(voice, mus, fx, out, HERE)
    return out


def _render_chunk(job):
    k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        ff.stdin.write(np.asarray(frame_at(k / FPS)).tobytes())
    ff.stdin.close(); ff.wait()
    return path


def render_parallel(total, audio_wav, out_mp4, procs=4, parts=12):
    import multiprocessing as mp
    nf = int(round(total * FPS))
    tmp = tempfile.mkdtemp(prefix="map_parts_", dir=HERE)
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
    out = p("wb04_map_reel.mp4")
    render_parallel(TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
