"""Low-level drawing helpers on top of skia-python."""
import math
import os
from functools import lru_cache

import skia

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

INK = (34, 36, 58)          # cartoon outline colour
WHITE = (255, 255, 255)


def col(c, a=255):
    if isinstance(c, str):
        c = c.lstrip("#")
        c = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    if len(c) == 4:
        return skia.Color(*c)
    return skia.Color(c[0], c[1], c[2], int(a))


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    c1 = hexrgb(c1) if isinstance(c1, str) else c1
    c2 = hexrgb(c2) if isinstance(c2, str) else c2
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def fill(c, a=255):
    return skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kFill_Style)


def stroke(c, w, a=255, cap="round"):
    p = skia.Paint(AntiAlias=True, Color=col(c, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def blurred(c, sigma, a=255):
    p = fill(c, a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    return p


@lru_cache(maxsize=None)
def typeface(name):
    return skia.Typeface.MakeFromFile(os.path.join(ASSETS, name))


@lru_cache(maxsize=4096)
def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def text_width(txt, fname, size):
    return font(fname, size).measureText(txt)


def draw_text(c, txt, x, y, fname, size, color=WHITE, outline=None, ow=0, align="center",
              shadow=None, alpha=255):
    """Draw text with optional outline. y is the baseline."""
    f = font(fname, size)
    w = f.measureText(txt)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    blob = skia.TextBlob.MakeFromString(txt, f)
    if blob is None:
        return w
    if shadow:
        c.drawTextBlob(blob, x + shadow[0], y + shadow[1], fill(shadow[2], min(alpha, shadow[3] if len(shadow) > 3 else 120)))
    if outline and ow:
        c.drawTextBlob(blob, x, y, stroke(outline, ow, alpha))
    c.drawTextBlob(blob, x, y, fill(color, alpha))
    return w


def wrap(txt, fname, size, maxw):
    words = txt.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t, fname, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(txt, fname, size, maxw, maxlines, minsize=20):
    """Shrink font size until text wraps into maxlines lines."""
    s = size
    while s > minsize:
        lines = wrap(txt, fname, s, maxw)
        if len(lines) <= maxlines and all(text_width(l, fname, s) <= maxw for l in lines):
            return lines, s
        s -= 2
    return wrap(txt, fname, s, maxw), s


def rrect(c, x, y, w, h, r, paint):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint)


def circle(c, x, y, r, paint):
    c.drawCircle(x, y, r, paint)


def oval(c, cx, cy, rx, ry, paint):
    c.drawOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), paint)


def poly(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    if close:
        p.close()
    return p


def star_path(cx, cy, r1, r2, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


def outlined(c, path, color, ow=7, ink=INK, alpha=255):
    c.drawPath(path, fill(color, alpha))
    c.drawPath(path, stroke(ink, ow, alpha))


# ---------- easing ----------

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_cubic(t):
    t = clamp(t) - 1
    return t * t * t + 1


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_elastic(t):
    t = clamp(t)
    if t in (0, 1):
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def pop(t, dur=0.45):
    """Scale-in factor for pop animations."""
    return ease_out_back(t / dur) if t < dur else 1.0


def lerp(a, b, t):
    return a + (b - a) * t
