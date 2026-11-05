"""Whiteboard stick-figure drawing engine (white paper, black marker, navy + gold accents).

Everything is drawn in code on a 2x supersampled canvas, with a hand-drawn look:
  * lines wobble and "boil" (re-jitter 8 times a second) like a real animated doodle
  * strokes can be revealed progressively (draw-on) with `reveal=0..1`
  * posable stick figures (`figure`), expressions, outfits, props, speech/thought bubbles, text in marker fonts

    cv = Canvas(t, cam=(cx, cy, zoom))     # logical size 1920x1080, y down
    cv.poly([...]); cv.ellipse(x, y, r); cv.text("HELLO", x, y, size=80, font="marker")
    with cv.at(x, y, s=1.2, rot=-5): ...   # local transform (pop-in scale, tilt)
    figure(cv, x, y, h=320, pose="think", face="worry")
    frame = cv.finish()                    # -> RGB PIL image 1920x1080

Colours: INK NAVY GOLD RED GREEN PURPLE BROWN GREY BLUE ORANGE PINK.  Fonts: marker, hand, brush, anton, cinzel.
"""
import math, os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(_HERE, "..", "assets", "fonts")
W, H, SS = 1920, 1080, 2

INK, NAVY, GOLD, RED = (26, 26, 34), (24, 48, 128), (240, 184, 28), (216, 52, 52)
GREEN, PURPLE, BROWN, GREY = (44, 164, 96), (128, 64, 176), (176, 124, 72), (150, 152, 160)
LGREY, PAPER, BLUE, SKY = (226, 228, 232), (255, 255, 255), (70, 140, 225), (214, 236, 255)
ORANGE, PINK, CREAM, LGOLD = (244, 140, 40), (240, 120, 150), (255, 244, 214), (255, 226, 130)
POTATO = (206, 158, 98)

_RNG = np.random.default_rng(2024)
NOISE = _RNG.normal(0, 1, (8192, 2)).astype(np.float32)


# ------------------------------------------------------------------ small maths helpers
def clamp01(x): return min(max(x, 0.0), 1.0)
def lerp(a, b, u): return a + (b - a) * u
def ease(x): x = clamp01(x); return x * x * (3 - 2 * x)
def ease_out_back(x, c=1.7): x = clamp01(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def rad(d): return math.radians(d)


FONT_FILES = {"marker": "PermanentMarker-Regular.ttf", "hand": "PatrickHand-Regular.ttf", "brush": "CaveatBrush-Regular.ttf",
              "anton": "Anton.ttf", "cinzel": "Cinzel.ttf"}
_fonts, _layers = {}, {}


def get_font(name, px):
    k = (name, px)
    if k not in _fonts:
        f = ImageFont.truetype(os.path.join(FONT_DIR, FONT_FILES[name]), px)
        if name == "cinzel":
            f.set_variation_by_name("Bold")
        _fonts[k] = f
    return _fonts[k]


class Canvas:
    def __init__(self, t, cam=(W / 2, H / 2, 1.0), bg=PAPER):
        self.t = t
        self.img = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.img)
        self.boil = int(t * 8)
        cx, cy, z = cam
        self.M = (z, 0.0, 0.0, z, W / 2 - cx * z, H / 2 - cy * z)       # x' = a x + b y + e ; y' = c x + d y + f
        self.fade = 1.0
        self.stack = []

    # -------------------------------------------------------------- transforms
    @property
    def sc(self):
        a, b, c, d, _, _ = self.M
        return math.sqrt(abs(a * d - b * c))

    @contextmanager
    def at(self, x=0, y=0, s=1.0, rot=0.0):
        a, b, c, d, e, f = self.M
        self.stack.append(self.M)
        cs, sn = math.cos(rad(rot)) * s, math.sin(rad(rot)) * s
        self.M = (a * cs + b * sn, -a * sn + b * cs, c * cs + d * sn, -c * sn + d * cs, a * x + b * y + e, c * x + d * y + f)
        try:
            yield self
        finally:
            self.M = self.stack.pop()

    @contextmanager
    def fading(self, a):
        old = self.fade
        self.fade = old * clamp01(a)
        try:
            yield self
        finally:
            self.fade = old

    def P(self, pts):
        a, b, c, d, e, f = self.M
        p = np.asarray(pts, np.float32).reshape(-1, 2)
        return np.stack([a * p[:, 0] + b * p[:, 1] + e, c * p[:, 0] + d * p[:, 1] + f], 1) * SS

    def xy(self, x, y):
        a, b, c, d, e, f = self.M
        return (a * x + b * y + e, c * x + d * y + f)

    def _col(self, col):
        if self.fade >= 0.999:
            return tuple(int(v) for v in col)
        return tuple(int(PAPER[i] + (col[i] - PAPER[i]) * self.fade) for i in range(3))

    # -------------------------------------------------------------- strokes
    @staticmethod
    def _subdiv(pts, step):
        out = [pts[0]]
        for i in range(1, len(pts)):
            a, b = pts[i - 1], pts[i]
            n = int(np.hypot(*(b - a)) // step)
            for k in range(1, n + 1):
                out.append(a + (b - a) * (k / (n + 1)))
            out.append(b)
        return np.array(out, np.float32)

    @staticmethod
    def _cut(pts, r):
        seglen = np.hypot(*(pts[1:] - pts[:-1]).T)
        cum = np.concatenate([[0], np.cumsum(seglen)])
        target = cum[-1] * clamp01(r)
        k = int(np.searchsorted(cum, target))
        if k <= 0:
            return pts[:1]
        k = min(k, len(pts) - 1)
        u = (target - cum[k - 1]) / max(seglen[k - 1], 1e-6)
        return np.vstack([pts[:k], pts[k - 1] + (pts[k] - pts[k - 1]) * u])

    def poly(self, pts, w=6, col=INK, closed=False, fill=None, reveal=1.0, amp=1.4, seed=0, cap=True, step=36):
        if reveal <= 0.001:
            return
        pts = np.asarray(pts, np.float32)
        if closed:
            pts = np.vstack([pts, pts[:1]])
        pts = self._subdiv(pts, step)
        if amp:
            idx = (seed * 131 + self.boil * 977 + np.arange(len(pts))) % 8192
            pts = pts + NOISE[idx] * (amp / max(self.sc, 0.05))
        if reveal < 1:
            pts = self._cut(pts, reveal)
        P = self.P(pts)
        if fill is not None and closed and reveal >= 0.999:
            self.d.polygon([tuple(p) for p in P], fill=self._col(fill))
        if len(P) < 2:
            return
        wpx = max(1, int(round(w * min(self.sc, 1.6) * SS)))
        c = self._col(col)
        self.d.line([tuple(p) for p in P], fill=c, width=wpx, joint="curve")
        if cap:
            r = wpx / 2
            for q in (P[0], P[-1]):
                self.d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=c)

    def line(self, p0, p1, **kw): self.poly([p0, p1], **kw)

    def curve(self, p0, pc, p1, n=14, **kw):
        t = np.linspace(0, 1, n)[:, None]
        p0, pc, p1 = (np.asarray(v, np.float32) for v in (p0, pc, p1))
        self.poly((1 - t) ** 2 * p0 + 2 * (1 - t) * t * pc + t ** 2 * p1, **kw)

    def ellipse(self, x, y, rx, ry=None, fill=None, seed=0, closed=None, **kw):
        ry = rx if ry is None else ry
        n = max(14, int((rx + ry) / 3.2))
        a0 = (seed * 0.9) % 6.28
        over = 1.0 if (fill is not None or closed) else 1.05
        th = np.linspace(a0, a0 + 2 * math.pi * over, n)
        pts = np.stack([x + rx * np.cos(th), y + ry * np.sin(th)], 1)
        self.poly(pts, closed=bool(fill is not None or closed), fill=fill, seed=seed, **kw)

    def rect(self, x0, y0, x1, y1, r=0, fill=None, **kw):
        if r <= 0:
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        else:
            pts = []
            for cx, cy, a0 in [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]:
                for k in range(6):
                    a = rad(a0 + 90 * k / 5)
                    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.poly(pts, closed=True, fill=fill, **kw)

    def arrow(self, p0, p1, head=26, **kw):
        reveal = kw.get("reveal", 1.0)
        self.line(p0, p1, **kw)
        if reveal >= 0.98:
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            k = {k: v for k, v in kw.items() if k != "reveal"}
            for s in (-0.5, 0.5):
                self.line(p1, (p1[0] - head * math.cos(ang + s), p1[1] - head * math.sin(ang + s)), **k)

    def zig(self, p0, p1, n=6, jag=26, **kw):
        pts = [np.array(p0, np.float32)]
        d = np.array(p1, np.float32) - np.array(p0, np.float32)
        nrm = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-6)
        for k in range(1, n):
            pts.append(np.array(p0) + d * (k / n) + nrm * jag * (1 if k % 2 else -1))
        pts.append(np.array(p1, np.float32))
        self.poly(pts, **kw)

    def band(self, x0, y0, x1, y1, col=LGOLD, alpha=0.75, reveal=1.0):
        """Marker highlight behind text (axis-aligned in screen space)."""
        if reveal <= 0.001:
            return
        (ax, ay), (bx, by) = self.xy(x0, y0), self.xy(x1, y1)
        ax, bx = sorted((ax, bx)); ay, by = sorted((ay, by))
        bx = ax + (bx - ax) * clamp01(reveal)
        w, h = int((bx - ax) * SS), int((by - ay) * SS)
        if w < 2 or h < 2:
            return
        mask = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, h * 0.12, w, h * 0.92), radius=int(h * 0.3), fill=int(255 * alpha * self.fade))
        self.img.paste(Image.new("RGB", (w, h), col), (int(ax * SS), int(ay * SS)), mask)

    # -------------------------------------------------------------- text
    def text(self, s, x, y, size=48, col=INK, font="hand", anchor="mm", reveal=1.0, rot=0, line_gap=1.12, stroke=0):
        if reveal <= 0.001 or not s:
            return
        px = max(6, int(size * self.sc * SS))
        c = self._col(col)
        rot = rot - math.degrees(math.atan2(self.M[2], self.M[0]))        # follow the current transform's tilt
        key = (s, px, c, font, stroke, round(rot))
        lay = _layers.get(key)
        if lay is None:
            f = get_font(font, px)
            lines = s.split("\n")
            tmp = ImageDraw.Draw(Image.new("L", (4, 4)))
            ws = [tmp.textlength(ln, font=f) for ln in lines]
            lh = int(px * line_gap)
            pad = px // 3 + stroke * 2
            lay = Image.new("RGBA", (int(max(ws)) + pad * 2, lh * len(lines) + pad * 2), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            for i, ln in enumerate(lines):
                ld.text((lay.width / 2, pad + lh * i + lh / 2), ln, font=f, fill=c + (255,), anchor="mm",
                        stroke_width=stroke * SS, stroke_fill=c + (255,))
            if rot:
                lay = lay.rotate(rot, Image.BICUBIC, expand=True)
            if len(_layers) > 500:
                _layers.clear()
            _layers[key] = lay
        sx, sy = self.xy(x, y)
        lw, lh_ = lay.size
        ox = {"l": 0, "m": -lw / 2, "r": -lw}[anchor[0]]
        oy = {"t": 0, "m": -lh_ / 2, "b": -lh_}[anchor[1]]
        pos = (int(sx * SS + ox), int(sy * SS + oy))
        if reveal < 1:
            lay = lay.crop((0, 0, max(2, int(lw * clamp01(reveal))), lh_))
        self.img.paste(lay, pos, lay)

    def text_w(self, s, size=48, font="hand"):
        f = get_font(font, int(size * SS))
        return ImageDraw.Draw(Image.new("L", (4, 4))).textlength(s, font=f) / SS

    def finish(self):
        return self.img.reduce(SS)


# ------------------------------------------------------------------ stick figure
POSE = {
    "stand": dict(A=(10, 5), B=(-10, -5), C=(5, 0), D=(-5, 0)),
    "sit": dict(A=(40, 60), B=(30, 70), C=(90, -90), D=(82, -85)),
    "type": dict(A=(58, 40), B=(48, 48), C=(90, -90), D=(82, -85), lean=5),
    "cheer": dict(A=(160, 10), B=(-160, -10), C=(8, 0), D=(-8, 0)),
    "shrug": dict(A=(40, 110), B=(-40, -110), C=(5, 0), D=(-5, 0)),
    "point": dict(A=(92, 0), B=(-10, -5), C=(5, 0), D=(-5, 0)),
    "point_up": dict(A=(170, 0), B=(-10, -5), C=(5, 0), D=(-5, 0)),
    "think": dict(A=(30, 128), B=(-10, -5), C=(5, 0), D=(-5, 0)),
    "slump": dict(A=(-4, 8), B=(4, -8), C=(4, 0), D=(-4, 0), lean=14, hd=14),
    "lift": dict(A=(150, 30), B=(-150, -30), C=(10, -10), D=(-10, 10)),
    "flex": dict(A=(90, 90), B=(-90, -90), C=(14, 0), D=(-14, 0)),
    "hips": dict(A=(50, -110), B=(-50, 110), C=(8, 0), D=(-8, 0)),
    "juggle": dict(A=(125, 55), B=(-125, -55), C=(8, 0), D=(-8, 0)),
    "arms_out": dict(A=(75, 0), B=(-75, 0), C=(8, 0), D=(-8, 0)),
    "hold": dict(A=(70, 40), B=(-20, 30), C=(5, 0), D=(-5, 0)),
    "fear": dict(A=(120, 70), B=(-120, -70), C=(14, -6), D=(-14, 6)),
    "sneak": dict(A=(30, 50), B=(-20, 40), C=(24, -26), D=(-24, 22), lean=12),
}


def pose_mix(p, q, u):
    p, q = (POSE[p] if isinstance(p, str) else p), (POSE[q] if isinstance(q, str) else q)
    out = {}
    for k in ("A", "B", "C", "D"):
        out[k] = (lerp(p[k][0], q[k][0], u), lerp(p[k][1], q[k][1], u))
    out["lean"] = lerp(p.get("lean", 0), q.get("lean", 0), u)
    out["hd"] = lerp(p.get("hd", 0), q.get("hd", 0), u)
    return out


def walk_pose(phase, amp=1.0, arms=True):
    s, c = math.sin(phase), math.cos(phase)
    return dict(A=(-32 * s * amp if arms else 10, 18), B=(32 * s * amp if arms else -10, 18),
                C=(34 * s * amp, -max(0.0, c) * 50 * amp), D=(-34 * s * amp, -max(0.0, -c) * 50 * amp), lean=5)


def run_pose(phase):
    s, c = math.sin(phase), math.cos(phase)
    return dict(A=(-60 * s, 80), B=(60 * s, 80), C=(55 * s, -max(0.0, c) * 85), D=(-55 * s, -max(0.0, -c) * 85), lean=16)


def draw_face(cv, c, r, face, dirn, t, ink=INK, w=5):
    ex, ey = r * 0.34, r * 0.06
    gaze = dirn * r * 0.14
    blink = (t % 3.6) < 0.12
    def eye(sx, big=1.0):
        if blink or face == "sleepy":
            cv.line((c[0] + sx * ex + gaze - r * 0.14, c[1] - ey), (c[0] + sx * ex + gaze + r * 0.14, c[1] - ey), w=w * 0.8, col=ink, amp=0)
        elif face == "dead":
            x, y, k = c[0] + sx * ex + gaze, c[1] - ey, r * 0.15
            cv.line((x - k, y - k), (x + k, y + k), w=w * 0.8, col=ink, amp=0); cv.line((x - k, y + k), (x + k, y - k), w=w * 0.8, col=ink, amp=0)
        else:
            rr = r * 0.12 * big
            cv.d.ellipse([(v) for v in (*[q * SS for q in cv.xy(c[0] + sx * ex + gaze - rr, c[1] - ey - rr)],
                                         *[q * SS for q in cv.xy(c[0] + sx * ex + gaze + rr, c[1] - ey + rr)])], fill=cv._col(ink))
    if face == "cool":
        cv.rect(c[0] - r * 0.78, c[1] - r * 0.3, c[0] + r * 0.78, c[1] + r * 0.06, r=r * 0.1, fill=INK, w=3, amp=0)
        cv.line((c[0] - r * 0.78, c[1] - r * 0.2), (c[0] - r * 1.0, c[1] - r * 0.28), w=4, amp=0)
        cv.curve((c[0] - r * 0.3, c[1] + r * 0.42), (c[0], c[1] + r * 0.55), (c[0] + r * 0.4, c[1] + r * 0.36), w=w, col=ink, amp=0.6)
        return
    big = 1.5 if face in ("shock", "scared") else 1.0
    eye(-1, big); eye(1, big)
    my = c[1] + r * 0.46
    if face in ("neutral", "worry", "sweat", "blank"):
        if face in ("worry", "sweat"):
            cv.poly([(c[0] - r * 0.34 + k * r * 0.17, my + (r * 0.07 if k % 2 else -r * 0.04)) for k in range(5)], w=w, col=ink, amp=0.4)
        else:
            cv.line((c[0] - r * 0.28 + gaze * .4, my), (c[0] + r * 0.28 + gaze * .4, my), w=w, col=ink, amp=0.4)
    elif face in ("smile", "happy"):
        cv.curve((c[0] - r * 0.4, my - r * 0.1), (c[0], my + r * 0.5), (c[0] + r * 0.4, my - r * 0.1), w=w, col=ink, amp=0.4)
    elif face == "big":
        cv.rect(c[0] - r * 0.4, my - r * 0.12, c[0] + r * 0.4, my + r * 0.3, r=r * 0.15, fill=WHITE_FILL, w=w * .8, col=ink, amp=0.4)
    elif face in ("sad", "cry"):
        cv.curve((c[0] - r * 0.34, my + r * 0.2), (c[0], my - r * 0.18), (c[0] + r * 0.34, my + r * 0.2), w=w, col=ink, amp=0.4)
        cv.line((c[0] - ex - r * .2, c[1] - r * 0.45), (c[0] - ex + r * .2, c[1] - r * 0.3), w=w * .7, amp=0)
        cv.line((c[0] + ex + r * .2, c[1] - r * 0.45), (c[0] + ex - r * .2, c[1] - r * 0.3), w=w * .7, amp=0)
    elif face in ("shock", "scared"):
        cv.ellipse(c[0], my + r * 0.05, r * 0.2, r * 0.27, w=w * .8, col=ink, amp=0.3, fill=WHITE_FILL)
    elif face == "smirk":
        cv.curve((c[0] - r * 0.3, my + r * 0.02), (c[0] + r * 0.1, my + r * 0.12), (c[0] + r * 0.45, my - r * 0.22), w=w, col=ink, amp=0.4)
    elif face == "angry":
        cv.line((c[0] - ex - r * .25, c[1] - r * 0.5), (c[0] - ex + r * .2, c[1] - r * 0.3), w=w, amp=0)
        cv.line((c[0] + ex + r * .25, c[1] - r * 0.5), (c[0] + ex - r * .2, c[1] - r * 0.3), w=w, amp=0)
        cv.line((c[0] - r * 0.3, my + r * 0.05), (c[0] + r * 0.3, my + r * 0.05), w=w, amp=0.3)
    elif face == "dead":
        cv.line((c[0] - r * 0.3, my), (c[0] + r * 0.3, my), w=w, amp=0.3)
    if face in ("sweat", "scared"):                       # animated sweat drops
        for k in range(2):
            ph = (t * 1.6 + k * 0.5) % 1.0
            sx, sy = c[0] + (1 if k else -1) * r * (1.15 + 0.25 * ph), c[1] - r * 0.6 + ph * r * 1.3
            cv.poly([(sx, sy - r * 0.28), (sx - r * 0.13, sy), (sx, sy + r * 0.12), (sx + r * 0.13, sy)], closed=True, fill=SKY,
                    w=3, col=BLUE, amp=0.2)
    if face == "cry":
        for k in (-1, 1):
            for j in range(2):
                ph = (t * 1.4 + j * 0.5) % 1.0
                cv.line((c[0] + k * ex, c[1] + r * 0.1 + ph * r * 1.0), (c[0] + k * ex, c[1] + r * 0.28 + ph * r * 1.0), w=4, col=BLUE, amp=0)


WHITE_FILL = (255, 255, 255)


def figure(cv, x, y, h=300, pose="stand", face="neutral", flip=False, reveal=1.0, seed=3, outfit=(), col=INK, w=7, bob=0.0, t=None):
    """Draw a stick figure standing with its feet at (x, y). Returns a dict of joint positions."""
    t = cv.t if t is None else t
    p = POSE[pose] if isinstance(pose, str) else pose
    dirn = -1 if flip else 1
    L1 = L2 = 0.23 * h
    def leg(k):
        a1, a2 = p[k]
        k1 = (math.sin(rad(a1)) * L1 * dirn, math.cos(rad(a1)) * L1)
        ft = (k1[0] + math.sin(rad(a1 + a2)) * L2 * dirn, k1[1] + math.cos(rad(a1 + a2)) * L2)
        return k1, ft
    (ck, cf), (dk, df) = leg("C"), leg("D")
    hip_h = max(cf[1], df[1])
    hip = (x, y - hip_h + bob)
    lean = rad(p.get("lean", 0))
    tor = 0.31 * h
    neck = (hip[0] + math.sin(lean) * tor * dirn, hip[1] - math.cos(lean) * tor)
    hr = 0.095 * h
    hl = lean + rad(p.get("hd", 0))
    hc = (neck[0] + math.sin(hl) * (hr + 0.012 * h) * dirn, neck[1] - math.cos(hl) * (hr + 0.012 * h))
    sh = (hip[0] + math.sin(lean) * tor * 0.9 * dirn, hip[1] - math.cos(lean) * tor * 0.9)
    def arm(k):
        a1, a2 = p[k]
        e = (sh[0] + math.sin(rad(a1)) * 0.16 * h * dirn, sh[1] + math.cos(rad(a1)) * 0.16 * h)
        hd = (e[0] + math.sin(rad(a1 + a2)) * 0.16 * h * dirn, e[1] + math.cos(rad(a1 + a2)) * 0.16 * h)
        return e, hd
    (ae, ah), (be, bh) = arm("A"), arm("B")
    J = dict(hip=hip, neck=neck, head=hc, hr=hr, hA=ah, hB=bh, eA=ae, eB=be, fC=(hip[0] + cf[0], hip[1] + cf[1]),
             fD=(hip[0] + df[0], hip[1] + df[1]), sh=sh, dir=dirn, h=h)
    kw = dict(w=w, col=col, seed=seed, reveal=1.0)
    rv = reveal
    # reveal order: legs, torso, arms, head
    def seg(a, b): return clamp01((rv - a) / max(b - a, 1e-6))
    pj = "pajamas" in outfit
    legs = [(hip, (hip[0] + ck[0], hip[1] + ck[1]), (hip[0] + cf[0], hip[1] + cf[1])), (hip, (hip[0] + dk[0], hip[1] + dk[1]), (hip[0] + df[0], hip[1] + df[1]))]
    if "cape" in outfit:
        cv.poly([sh, (sh[0] - dirn * 0.20 * h, sh[1] + 0.55 * h), (sh[0] - dirn * 0.02 * h, sh[1] + 0.58 * h), (sh[0] + dirn * 0.02 * h, sh[1] + 0.05 * h)],
                closed=True, fill=RED, w=4, amp=0.8, seed=seed + 9, reveal=seg(0.3, 0.7))
    for i, (a, b, c_) in enumerate(legs):
        if pj:
            cv.poly([a, b, c_], w=w + 12, col=(168, 200, 240), amp=0.6, seed=seed + i, reveal=seg(0.0, 0.3))
        cv.poly([a, b, c_], reveal=seg(0.0, 0.3), **{k: v for k, v in kw.items() if k != "reveal"})
    cv.line(hip, neck, reveal=seg(0.25, 0.5), **{k: v for k, v in kw.items() if k != "reveal"})
    for (e, hnd) in ((be, bh), (ae, ah)):
        cv.poly([sh, e, hnd], reveal=seg(0.45, 0.75), **{k: v for k, v in kw.items() if k != "reveal"})
    if "tank" in outfit:
        u = np.array(neck) - np.array(hip); u = u / (np.hypot(*u) + 1e-6); n_ = np.array([-u[1], u[0]])
        pts = [np.array(hip) + n_ * 0.075 * h, np.array(hip) - n_ * 0.075 * h, np.array(sh) - n_ * 0.085 * h, np.array(sh) + n_ * 0.085 * h]
        cv.poly(pts, closed=True, fill=RED, w=4, amp=0.6, seed=seed + 4, reveal=seg(0.5, 0.8))
    if "suit" in outfit:
        u = np.array(neck) - np.array(hip); u = u / (np.hypot(*u) + 1e-6); n_ = np.array([-u[1], u[0]])
        top = np.array(sh) + u * 0.02 * h
        pts = [np.array(hip) + n_ * 0.1 * h - u * 0.05 * h, np.array(hip) - n_ * 0.1 * h - u * 0.05 * h, top - n_ * 0.11 * h, top + n_ * 0.11 * h]
        cv.poly(pts, closed=True, fill=NAVY, w=4, amp=0.6, seed=seed + 5, reveal=seg(0.5, 0.8))
        cv.poly([top - n_ * 0.035 * h, top - u * 0.18 * h, top + n_ * 0.035 * h], closed=True, fill=PAPER, w=3, amp=0.3)
        cv.poly([top, top - u * 0.05 * h - n_ * 0.02 * h, top - u * 0.2 * h, top - u * 0.05 * h + n_ * 0.02 * h], closed=True, fill=GOLD, w=3, amp=0.3)
    if "labcoat" in outfit:
        u = np.array(neck) - np.array(hip); u = u / (np.hypot(*u) + 1e-6); n_ = np.array([-u[1], u[0]])
        top = np.array(sh) + u * 0.02 * h
        pts = [np.array(hip) + n_ * 0.12 * h - u * 0.15 * h, np.array(hip) - n_ * 0.12 * h - u * 0.15 * h, top - n_ * 0.1 * h, top + n_ * 0.1 * h]
        cv.poly(pts, closed=True, fill=PAPER, w=4, amp=0.6, seed=seed + 6, reveal=seg(0.5, 0.8))
        cv.line(top - u * 0.02 * h, np.array(hip) - u * 0.15 * h, w=3, amp=0.3)
    # head
    cv.ellipse(hc[0], hc[1], hr, hr, fill=PAPER, w=w, col=col, seed=seed + 11, reveal=seg(0.7, 1.0))
    if rv >= 0.98:
        draw_face(cv, hc, hr, face, dirn, t, ink=col, w=max(3, w * 0.7))
        draw_headgear(cv, hc, hr, outfit, dirn, seed, t)
    return J


def draw_headgear(cv, c, r, outfit, dirn, seed, t):
    if "crown" in outfit:
        b = c[1] - r * 0.92
        cv.poly([(c[0] - r * 0.6, b), (c[0] - r * 0.7, b - r * 0.7), (c[0] - r * 0.28, b - r * 0.32), (c[0], b - r * 0.8),
                 (c[0] + r * 0.28, b - r * 0.32), (c[0] + r * 0.7, b - r * 0.7), (c[0] + r * 0.6, b)], closed=True, fill=GOLD, w=4, amp=0.5)
    if "helmet" in outfit:
        cv.poly([(c[0] - r * 1.08, c[1] - r * 0.1), (c[0] - r * 0.9, c[1] - r * 0.95), (c[0], c[1] - r * 1.3), (c[0] + r * 0.9, c[1] - r * 0.95),
                 (c[0] + r * 1.08, c[1] - r * 0.1)], closed=True, fill=(150, 156, 170), w=5, amp=0.6)
        cv.curve((c[0], c[1] - r * 1.3), (c[0] + dirn * r * 0.2, c[1] - r * 2.0), (c[0] + dirn * r * 0.9, c[1] - r * 1.75), w=7, col=RED, amp=0.5)
    if "hat" in outfit:                                   # conquistador morion
        cv.poly([(c[0] - r * 1.3, c[1] - r * 0.78), (c[0] - r * 0.7, c[1] - r * 0.95), (c[0] - r * 0.4, c[1] - r * 1.5), (c[0], c[1] - r * 1.15),
                 (c[0] + r * 0.4, c[1] - r * 1.5), (c[0] + r * 0.7, c[1] - r * 0.95), (c[0] + r * 1.3, c[1] - r * 0.78)], closed=True, fill=(190, 192, 200), w=5, amp=0.6)
    if "tricorn" in outfit:
        cv.poly([(c[0] - r * 1.4, c[1] - r * 0.7), (c[0], c[1] - r * 1.7), (c[0] + r * 1.4, c[1] - r * 0.7), (c[0], c[1] - r * 0.95)],
                closed=True, fill=(60, 60, 80), w=5, amp=0.6)
    if "glasses" in outfit:
        for s in (-1, 1):
            cv.ellipse(c[0] + s * r * 0.4, c[1] - r * 0.02, r * 0.3, r * 0.3, w=3.5, amp=0.3)
        cv.line((c[0] - r * 0.1, c[1] - r * 0.02), (c[0] + r * 0.1, c[1] - r * 0.02), w=3.5, amp=0)
    if "goggles" in outfit:
        for s in (-1, 1):
            cv.ellipse(c[0] + s * r * 0.4, c[1] - r * 0.02, r * 0.34, r * 0.34, w=5, col=NAVY, fill=SKY, amp=0.3)
        cv.line((c[0] - r * 1.05, c[1] - r * 0.02), (c[0] + r * 1.05, c[1] - r * 0.02), w=4, col=NAVY, amp=0)
    if "wild" in outfit:
        for k in range(9):
            a = rad(-150 + k * 37.5)
            cv.line((c[0] + math.cos(a) * r * 0.95, c[1] + math.sin(a) * r * 0.95), (c[0] + math.cos(a) * r * 1.9, c[1] + math.sin(a) * r * 1.9 + (k % 2) * 6),
                    w=5, amp=1.2, seed=seed + k)
    if "longhair" in outfit:
        for s in (-1, 1):
            cv.poly([(c[0] + s * r * 0.95, c[1] - r * 0.4), (c[0] + s * r * 1.15, c[1] + r * 0.8), (c[0] + s * r * 0.9, c[1] + r * 1.5)], w=5, amp=0.8)
    if "horns" in outfit:
        for s_ in (-1, 1):
            cv.poly([(c[0] + s_ * r * 0.55, c[1] - r * 0.85), (c[0] + s_ * r * 0.9, c[1] - r * 1.7), (c[0] + s_ * r * 0.15, c[1] - r * 0.98)], closed=True,
                    fill=(150, 214, 150), w=4, amp=0.4)
    if "hardhat" in outfit:
        cv.poly([(c[0] - r * 1.15, c[1] - r * 0.45), (c[0] - r * 0.95, c[1] - r * 1.1), (c[0], c[1] - r * 1.35), (c[0] + r * 0.95, c[1] - r * 1.1),
                 (c[0] + r * 1.15, c[1] - r * 0.45)], closed=True, fill=GOLD, w=5, amp=0.5)


# ------------------------------------------------------------------ bubbles
def bubble(cv, x, y, text, size=40, font="hand", tail=None, pad=26, reveal=1.0, fill=PAPER, col=INK, w=5, lines=None):
    """Speech bubble centred at (x, y). tail=(tx, ty) points at the speaker."""
    ls = text.split("\n")
    tw = max(cv.text_w(s, size, font) for s in ls)
    bw, bh = tw + pad * 2, len(ls) * size * 1.12 + pad * 1.4
    x0, y0, x1, y1 = x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2
    r = min(30, bh / 2)
    if tail is not None and reveal > 0.2:
        tx, ty = tail
        bx = min(max(tx, x0 + r + 20), x1 - r - 40)
        by = y1 if ty > y else y0
        cv.poly([(bx - 22, by), (tx, ty), (bx + 22, by)], closed=True, fill=fill, w=w, col=col, amp=0.8)
    cv.rect(x0, y0, x1, y1, r=r, fill=fill, w=w, col=col, reveal=clamp01(reveal * 1.3), seed=3)
    if tail is not None and reveal > 0.2:
        by = y1 if tail[1] > y else y0
        bx = min(max(tail[0], x0 + r + 20), x1 - r - 40)
        cv.line((bx - 17, by), (bx + 17, by), w=w + 2, col=fill, amp=0, cap=False)
    cv.text(text, x, y + 3, size=size, font=font, col=col, reveal=clamp01((reveal - 0.3) / 0.7))
    return (x0, y0, x1, y1)


def thought(cv, x, y, text, size=40, font="hand", tail_to=None, pad=34, reveal=1.0, w=5):
    ls = text.split("\n")
    tw = max(cv.text_w(s, size, font) for s in ls)
    rx, ry = tw / 2 + pad * 1.2, len(ls) * size * 0.62 + pad
    pts = []
    n = 9
    for k in range(n):
        a = 2 * math.pi * k / n
        pts.append((x + rx * math.cos(a) * 0.86, y + ry * math.sin(a) * 0.86, 0.42 * min(rx, ry)))
    for (px, py, rr) in pts:
        cv.ellipse(px, py, rr, rr, fill=PAPER, w=w, amp=0.6)
    for (px, py, rr) in pts:
        cv.ellipse(px, py, rr - w * 0.45, rr - w * 0.45, fill=PAPER, w=0.01, col=PAPER, amp=0)
    cv.ellipse(x, y, rx * 0.86, ry * 0.86, fill=PAPER, w=0.01, col=PAPER, amp=0)
    if tail_to:
        tx, ty = tail_to
        for k, rr in enumerate((16, 11, 7)):
            u = (k + 1) / 4
            cv.ellipse(lerp(x, tx, 0.55 + 0.4 * u), lerp(y + ry * 0.8, ty, 0.2 + 0.7 * u), rr, rr, fill=PAPER, w=4, amp=0.3)
    cv.text(text, x, y + 2, size=size, font=font, reveal=clamp01(reveal))


# ------------------------------------------------------------------ props & doodles
def flame(cv, x, y, s=1.0, t=0.0, seed=0):
    f = 1 + 0.12 * math.sin(t * 17 + seed) + 0.06 * math.sin(t * 29 + seed * 2)
    h = 70 * s * f
    cv.poly([(x - 22 * s, y), (x - 26 * s, y - h * 0.5), (x - 6 * s, y - h * 0.55), (x - 2 * s, y - h), (x + 12 * s, y - h * 0.55), (x + 26 * s, y - h * 0.5), (x + 22 * s, y)],
            closed=True, fill=ORANGE, w=4, col=RED, amp=1.0, seed=seed)
    cv.poly([(x - 11 * s, y), (x - 12 * s, y - h * 0.32), (x, y - h * 0.62), (x + 12 * s, y - h * 0.32), (x + 11 * s, y)], closed=True, fill=GOLD, w=2, col=GOLD, amp=0.8, seed=seed + 3)


def cookie(cv, x, y, r=26):
    cv.ellipse(x, y, r, r, fill=(214, 160, 90), w=4, seed=2)
    for dx, dy in ((-8, -8), (9, -3), (-2, 10), (10, 11), (-12, 6)):
        cv.ellipse(x + dx * r / 26, y + dy * r / 26, 3.5 * r / 26, 3.5 * r / 26, fill=(90, 56, 30), w=1, col=(90, 56, 30), amp=0)


def crown(cv, x, y, s=1.0, rot=0):
    with cv.at(x, y, s, rot):
        cv.poly([(-34, 0), (-40, -42), (-16, -20), (0, -50), (16, -20), (40, -42), (34, 0)], closed=True, fill=GOLD, w=5, amp=0.6)
        for dx, dy in ((-40, -42), (0, -50), (40, -42)):
            cv.ellipse(dx, dy, 6, 6, fill=RED, w=2, amp=0)


def potato(cv, x, y, s=1.0, face="neutral", reveal=1.0, arms="down", wobble=0.0, crowned=False, t=0.0):
    """Lumpy potato character, centred on (x, y) = its feet."""
    with cv.at(x, y - 95 * s, s, wobble):
        cv.poly([(-60, 20), (-72, -20), (-54, -64), (-10, -88), (40, -80), (72, -34), (76, 14), (50, 62), (0, 80), (-44, 66)], closed=True,
                fill=POTATO, w=6, amp=1.6, seed=7, reveal=reveal, step=24)
        for dx, dy in ((-30, -30), (24, -50), (40, 20), (-16, 40), (-44, 10)):
            cv.ellipse(dx, dy, 5, 4, fill=(150, 108, 64), w=1, col=(150, 108, 64), amp=0)
        if reveal >= 0.98:
            draw_face(cv, (0, -6), 46, face, 1, t, w=5)
            lift = arms == "up"
            cv.poly([(-62, 10), (-80, -118 if lift else 40)], w=6, amp=1)
            cv.poly([(62, 10), (80, -118 if lift else 40)], w=6, amp=1)
            cv.line((-24, 74), (-30, 96), w=6, amp=0.6); cv.line((24, 74), (30, 96), w=6, amp=0.6)
            if crowned:
                crown(cv, 0, -78, 0.9)


def barbell(cv, x, y, plates=0, w_bar=300, s=1.0, tilt=0):
    with cv.at(x, y, s, tilt):
        cv.line((-w_bar / 2, 0), (w_bar / 2, 0), w=9, amp=0.6)
        for sgn in (-1, 1):
            for k in range(plates):
                px = sgn * (w_bar / 2 - 18 - k * 20)
                cv.rect(px - 7, -34 + k * 6, px + 7, 34 - k * 6, fill=(70, 70, 80), w=4, amp=0.5)
            cv.line((sgn * (w_bar / 2 + 4), -9), (sgn * (w_bar / 2 + 4), 9), w=6, amp=0)


def desk(cv, x, y, w=620, reveal=1.0, legh=190):
    cv.line((x - w / 2, y), (x + w / 2, y), w=9, reveal=reveal, amp=1)
    cv.rect(x - w / 2 + 20, y, x - w / 2 + 70, y + legh, w=7, reveal=reveal)
    cv.rect(x + w / 2 - 70, y, x + w / 2 - 20, y + legh, w=7, reveal=reveal)


def laptop(cv, x, y, s=1.0, screen=None):
    with cv.at(x, y, s):
        cv.poly([(-70, 0), (70, 0), (60, -12), (-60, -12)], closed=True, fill=LGREY, w=5)
        cv.rect(-62, -118, 62, -12, fill=PAPER if screen is None else screen, w=6, r=6)


def mug(cv, x, y, s=1.0, t=0.0):
    with cv.at(x, y, s):
        cv.poly([(-22, -50), (22, -50), (18, 0), (-18, 0)], closed=True, fill=CREAM, w=5)
        cv.curve((22, -38), (46, -34), (20, -14), w=5)
        for k in range(2):
            ph = (t * 0.8 + k * 0.5) % 1
            cv.curve((-6 + k * 12, -56), (0 + k * 12, -70 - ph * 8), (-6 + k * 12, -86 - ph * 8), w=3, col=GREY, amp=0.5)


def paper(cv, x, y, w=70, h=90, rot=0, text=None, size=18, fill=PAPER):
    with cv.at(x, y, 1, rot):
        cv.rect(-w / 2, -h / 2, w / 2, h / 2, fill=fill, w=4, amp=0.8)
        if text:
            cv.text(text, 0, 0, size=size, font="hand")
        else:
            for k in range(4):
                cv.line((-w / 2 + 10, -h / 2 + 16 + k * 16), (w / 2 - 10 - (k % 2) * 14, -h / 2 + 16 + k * 16), w=2.5, col=GREY, amp=0.4)


def cloud(cv, x, y, s=1.0, fill=(214, 226, 240), reveal=1.0):
    with cv.at(x, y, s):
        puffs = [(-90, 10, 50), (-40, -30, 62), (30, -34, 66), (88, 4, 52), (0, 24, 70)]
        for px, py, r in puffs:
            cv.ellipse(px, py, r, r, fill=fill, w=6, amp=0.8)
        for px, py, r in puffs:
            cv.ellipse(px, py, r - 3, r - 3, fill=fill, w=0.01, col=fill, amp=0)


def gear(cv, x, y, r, teeth=10, ang=0.0, fill=LGREY, w=6, hole=True):
    pts = []
    n = teeth * 4
    for k in range(n):
        a = rad(ang + k * 360 / n)
        rr = r if (k // 2) % 2 == 0 else r * 0.8
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    cv.poly(pts, closed=True, fill=fill, w=w, amp=0.6, step=200)
    if hole:
        cv.ellipse(x, y, r * 0.28, r * 0.28, fill=PAPER, w=w * 0.8, amp=0.4)


def flask(cv, x, y, col, s=1.0, fill_amt=0.65, t=0.0, smoke=False, sparkle=False, label=None):
    with cv.at(x, y, s):
        out = [(-26, -150), (26, -150), (26, -88), (84, -10), (70, 4), (-70, 4), (-84, -10), (-26, -88)]
        liq_y = -88 + (1 - fill_amt) * 70
        cv.poly([(-76 + 0.0, liq_y + 14), (76, liq_y + 14), (80, -6), (68, 2), (-68, 2), (-80, -6)], closed=True, fill=col, w=0.01, col=col, amp=0)
        cv.poly(out, closed=True, w=6, amp=0.7)
        cv.line((-32, -150), (32, -150), w=8)
        if smoke:
            for k in range(4):
                ph = (t * 0.9 + k * 0.27) % 1
                cv.ellipse(-20 + k * 14 + 10 * math.sin(t * 3 + k), -168 - ph * 120, 14 + ph * 22, 14 + ph * 22, w=4, col=(110, 70, 140), amp=0.5)
        if sparkle:
            for k in range(3):
                ph = (t * 1.5 + k * 0.33) % 1
                sx, sy = -24 + k * 24, -170 - ph * 60
                cv.line((sx - 10, sy), (sx + 10, sy), w=4, col=GOLD, amp=0); cv.line((sx, sy - 10), (sx, sy + 10), w=4, col=GOLD, amp=0)
        if label:
            cv.text(label, 0, -34, size=30, font="marker", col=NAVY)


def chair(cv, x, y, s=1.0, wobble=0.0, rot=0.0):
    with cv.at(x, y, s, rot + wobble):
        cv.line((-50, -60), (-50, 0), w=8); cv.line((50, -60), (50, 0), w=8)
        cv.line((-56, -60), (56, -60), w=9)
        cv.line((-50, -60), (-58, -170), w=8); cv.line((50, -60), (58, -170), w=8)
        cv.line((-58, -140), (58, -140), w=6); cv.line((-56, -110), (56, -110), w=6)


def rocket(cv, x, y, s=1.0, flame_t=None, rot=0):
    with cv.at(x, y, s, rot):
        cv.poly([(0, -140), (34, -80), (34, 20), (-34, 20), (-34, -80)], closed=True, fill=PAPER, w=7, amp=0.7)
        cv.poly([(0, -140), (34, -80), (-34, -80)], closed=True, fill=RED, w=6, amp=0.5)
        cv.ellipse(0, -46, 15, 15, fill=SKY, w=5, amp=0.3)
        cv.poly([(-34, -10), (-62, 40), (-34, 20)], closed=True, fill=RED, w=5, amp=0.4)
        cv.poly([(34, -10), (62, 40), (34, 20)], closed=True, fill=RED, w=5, amp=0.4)
        if flame_t is not None:
            flame(cv, 0, 70, 1.1, flame_t)


def anchor(cv, x, y, s=1.0):
    with cv.at(x, y, s):
        cv.ellipse(0, -52, 14, 14, w=7)
        cv.line((0, -38), (0, 50), w=9)
        cv.line((-26, -14), (26, -14), w=8)
        cv.curve((-56, 14), (-50, 62), (0, 56), w=9); cv.curve((56, 14), (50, 62), (0, 56), w=9)


def boat(cv, x, y, s=1.0, rot=0.0, sink=0.0, col=BROWN):
    with cv.at(x, y + sink * 90, s, rot):
        cv.poly([(-120, -34), (120, -34), (86, 26), (-86, 26)], closed=True, fill=col, w=7, amp=1.0)
        cv.line((-92, -10), (92, -10), w=4, col=(120, 80, 40), amp=0.5)


def waves(cv, y, x0=0, x1=W, t=0.0, col=BLUE, amp=14, n=3, gap=24):
    for k in range(n):
        pts = []
        for xx in range(int(x0), int(x1) + 40, 40):
            pts.append((xx, y + k * gap + amp * math.sin(xx * 0.012 + t * 2 + k * 1.3)))
        cv.poly(pts, w=5, col=col, amp=0.6, seed=k, step=60)


def ground(cv, y, x0=60, x1=W - 60, col=GREY, reveal=1.0, ticks=True):
    cv.line((x0, y), (x1, y), w=5, col=col, reveal=reveal, amp=1.2)


def tree(cv, x, y, s=1.0):
    with cv.at(x, y, s):
        cv.line((0, 0), (0, -70), w=7, col=BROWN)
        cv.ellipse(0, -100, 42, 42, fill=(170, 220, 160), w=5, seed=4)


def tally(cv, x, y, n, s=1.0, col=INK):
    for g in range(n // 5 + 1):
        m = min(5, n - g * 5)
        gx = x + g * 70 * s
        for k in range(min(m, 4)):
            cv.line((gx + k * 14 * s, y), (gx + k * 14 * s, y + 46 * s), w=5, col=col, amp=0.8, seed=g * 5 + k)
        if m == 5:
            cv.line((gx - 8 * s, y + 38 * s), (gx + 56 * s, y + 8 * s), w=5, col=col, amp=0.8)


def mini(cv, x, y, h=64, phase=0.0, col=INK, swing=0.0, weapon=False, w=4, flip=False, seed=1):
    """Tiny stick person for crowds (cheap)."""
    pose = walk_pose(phase, 0.9)
    if swing:
        pose = dict(pose, A=(150 - 110 * swing, 20), B=(-20, 20))
    return figure(cv, x, y, h=h, pose=pose, face="blank", w=w, col=col, flip=flip, seed=seed, t=0.0)


def stamp(cv, x, y, text, col=RED, size=64, rot=-8, s=1.0, font="marker", reveal=1.0):
    ls = text.split("\n")
    wd = max(cv.text_w(q, size, font) for q in ls)
    hh = size * 0.62 * len(ls) + (size * 0.1 if len(ls) > 1 else 0)
    with cv.at(x, y, s, rot):
        cv.rect(-wd / 2 - 24, -hh, wd / 2 + 24, hh, r=10, w=7, col=col, reveal=reveal, amp=1.0)
        cv.text(text, 0, 2, size=size, col=col, font=font, reveal=clamp01(reveal * 1.2))


def check(cv, x, y, s=1.0, col=GREEN, reveal=1.0):
    with cv.at(x, y, s):
        cv.poly([(-22, 2), (-6, 22), (26, -22)], w=9, col=col, reveal=reveal, amp=0.6)


def xmark(cv, x, y, s=1.0, col=RED, reveal=1.0):
    with cv.at(x, y, s):
        cv.line((-20, -20), (20, 20), w=9, col=col, reveal=clamp01(reveal * 2), amp=0.6)
        cv.line((-20, 20), (20, -20), w=9, col=col, reveal=clamp01(reveal * 2 - 1), amp=0.6)


def sparkles(cv, x, y, t, n=4, r=60, col=GOLD):
    for k in range(n):
        ph = (t * 1.2 + k / n) % 1
        a = k * 2.4 + t
        sx, sy = x + math.cos(a) * r * (0.5 + ph * 0.6), y + math.sin(a) * r * (0.5 + ph * 0.6)
        s = 12 * math.sin(ph * math.pi)
        cv.line((sx - s, sy), (sx + s, sy), w=4, col=col, amp=0); cv.line((sx, sy - s), (sx, sy + s), w=4, col=col, amp=0)


def burst_lines(cv, x, y, r0, r1, n=12, col=GOLD, w=6, a0=0.0):
    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        cv.line((x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a)), w=w, col=col, amp=0.6)
