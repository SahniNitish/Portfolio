"""Bolt (the hero) and Lord Later (the procrastination villain)."""
import math
from functools import lru_cache

import skia

from .gfx import (INK, blurred, circle, col, draw_text, fill, outlined, oval, poly,
                  stroke)
from . import props as P

# ----------------------------------------------------------------------------
# BOLT
# ----------------------------------------------------------------------------
BOLT_BODY = "#FFC93C"
BOLT_SHADE = "#F29E2E"
BOLT_LIGHT = "#FFE597"
CAPE = "#E63946"
CAPE_DARK = "#B8222F"
SHOE = "#3A86FF"
CHEEK = (255, 120, 140)

# hand target positions (right arm; left arm mirrored) in body space
POSES = {
    "down":   ((112, 88), (-112, 88)),
    "wave":   ((150, -75), (-112, 88)),
    "up":     ((140, -120), (-140, -120)),
    "point":  ((190, -5), (-112, 88)),
    "pointup": ((150, -110), (-112, 88)),
    "fist":   ((205, 5), (-118, 55)),
    "hips":   ((98, 60), (-98, 60)),
    "think":  ((28, 78), (-112, 88)),
    "shrug":  ((160, -25), (-160, -25)),
    "hold":   ((118, 25), (-112, 88)),
    "hold2":  ((70, 40), (-70, 40)),
    "scared": ((62, 0), (-62, 0)),
    "cheer":  ((140, -120), (-140, -120)),
    "flex":   ((150, -70), (-150, -70)),
}


def blink_amount(t, seed=0):
    """0 = open, 1 = closed. Deterministic blinks every ~3.3s."""
    period = 3.3 + (seed % 5) * 0.37
    ph = (t + seed * 0.71) % period
    if ph < 0.14:
        return math.sin(ph / 0.14 * math.pi)
    return 0.0


def _arm(c, sx, sy, hx, hy, bend, color, hand_r=17, fist=False):
    mx, my = (sx + hx) / 2, (sy + hy) / 2
    dx, dy = hx - sx, hy - sy
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    cx, cy = mx + nx * bend, my + ny * bend
    path = skia.Path()
    path.moveTo(sx, sy)
    path.quadTo(cx, cy, hx, hy)
    c.drawPath(path, stroke(INK, 23))
    c.drawPath(path, stroke(color, 12))
    r = hand_r * (1.25 if fist else 1.1)
    circle(c, hx, hy, r, fill(color))
    circle(c, hx, hy, r, stroke(INK, 5))


def _eye(c, ex, ey, rx, ry, blink, look, mood, side, pupil_r=14):
    ry_eff = max(2.5, ry * (1 - blink))
    oval(c, ex, ey, rx, ry_eff, fill("#FFFFFF"))
    if blink < 0.85:
        # pupil
        c.save()
        clip = skia.Path()
        clip.addOval(skia.Rect.MakeLTRB(ex - rx, ey - ry_eff, ex + rx, ey + ry_eff))
        c.clipPath(clip, doAntiAlias=True)
        pr = pupil_r
        if mood == "scared":
            pr = 8
        if mood in ("excited",):
            pr = 16
        px = ex + look[0] * 9
        py = ey + look[1] * 9 + (6 if mood == "sad" else 0)
        circle(c, px, py, pr, fill(INK))
        circle(c, px - 5, py - 6, pr * 0.36, fill("#FFFFFF"))
        circle(c, px + 4, py + 4, pr * 0.15, fill("#FFFFFF"))
        # lids
        lid = None
        if mood == "tired":
            lid = poly([(ex - rx - 2, ey - ry - 2), (ex + rx + 2, ey - ry - 2),
                        (ex + rx + 2, ey - ry * 0.05), (ex - rx - 2, ey - ry * 0.05)])
        elif mood == "determined":
            inner = 1 if side > 0 else -1
            # inner corner lower than outer
            pts = [(ex - rx - 2, ey - ry - 2), (ex + rx + 2, ey - ry - 2)]
            if side > 0:   # right eye: inner is left side
                pts += [(ex + rx + 2, ey - ry * 0.55), (ex - rx - 2, ey - ry * 0.05)]
            else:
                pts += [(ex + rx + 2, ey - ry * 0.05), (ex - rx - 2, ey - ry * 0.55)]
            lid = poly(pts)
        elif mood == "sad":
            pts = [(ex - rx - 2, ey - ry - 2), (ex + rx + 2, ey - ry - 2)]
            if side > 0:
                pts += [(ex + rx + 2, ey - ry * 0.25), (ex - rx - 2, ey - ry * 0.75)]
            else:
                pts += [(ex + rx + 2, ey - ry * 0.75), (ex - rx - 2, ey - ry * 0.25)]
            lid = poly(pts)
        if lid is not None:
            c.drawPath(lid, fill(BOLT_SHADE))
            c.drawPath(lid, stroke(INK, 4))
        c.restore()
    oval(c, ex, ey, rx, ry_eff, stroke(INK, 5))


def _brows(c, mood, t):
    y = -72
    if mood == "determined":
        segs = [((-62, y - 8), (-20, y + 6)), ((20, y + 6), (62, y - 8))]
    elif mood == "sad":
        segs = [((-62, y + 4), (-22, y - 10)), ((22, y - 10), (62, y + 4))]
    elif mood == "scared":
        segs = [((-62, y - 6), (-22, y - 16)), ((22, y - 16), (62, y - 6))]
    elif mood == "tired":
        segs = [((-60, y + 8), (-22, y + 8)), ((22, y + 8), (60, y + 8))]
    elif mood == "excited":
        segs = [((-62, y - 4), (-22, y - 16)), ((22, y - 16), (62, y - 4))]
    else:  # happy / neutral
        segs = [((-60, y - 2), (-22, y - 9)), ((22, y - 9), (60, y - 2))]
    for (a, b) in segs:
        p = skia.Path()
        p.moveTo(*a)
        mx, my = (a[0] + b[0]) / 2, min(a[1], b[1]) - 5
        p.quadTo(mx, my, *b)
        c.drawPath(p, stroke(INK, 9))


def _mouth(c, mood, m, t):
    y = 34
    if m > 0.06 or mood in ("excited",):
        mm = max(m, 0.55 if mood == "excited" else 0)
        w = 30 + 10 * mm
        h = 8 + 30 * mm
        p = skia.Path()
        if mood in ("sad", "scared"):
            p.moveTo(-w * 0.8, y + 4)
            p.quadTo(0, y - 8, w * 0.8, y + 4)
            p.quadTo(w * 0.7, y + h, 0, y + h)
            p.quadTo(-w * 0.7, y + h, -w * 0.8, y + 4)
        else:
            p.moveTo(-w, y - 4)
            p.quadTo(0, y + 2, w, y - 4)
            p.quadTo(w * 0.85, y + h, 0, y + h + 2)
            p.quadTo(-w * 0.85, y + h, -w, y - 4)
        p.close()
        c.drawPath(p, fill("#7A1F2B"))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        oval(c, 0, y + h + 4, w * 0.6, h * 0.45, fill("#FF6B81"))
        if mood not in ("sad", "scared"):
            rr = skia.Rect.MakeLTRB(-w * 0.7, y - 10, w * 0.7, y + 4)
            c.drawRect(rr, fill("#FFFFFF"))
        c.restore()
        c.drawPath(p, stroke(INK, 5))
    else:
        p = skia.Path()
        if mood == "sad":
            p.moveTo(-22, y + 10)
            p.quadTo(0, y - 6, 22, y + 10)
        elif mood == "scared":
            p.moveTo(-24, y + 4)
            for i in range(4):
                p.quadTo(-18 + i * 12, y + (-6 if i % 2 == 0 else 10), -12 + i * 12, y + 4)
        elif mood == "tired":
            p.moveTo(-18, y + 6)
            p.quadTo(0, y + 9, 18, y + 4)
        elif mood == "determined":
            p.moveTo(-22, y + 2)
            p.quadTo(0, y + 14, 24, y - 2)
        else:
            p.moveTo(-28, y - 2)
            p.quadTo(0, y + 26, 28, y - 2)
        c.drawPath(p, stroke(INK, 7))


def draw_bolt(c, x, y, s=1.0, t=0.0, mood="happy", pose="down", mouth=0.0,
              look=(0.25, 0.0), hold=None, flip=False, jump=0.0, squash=0.0,
              seed=0, rot=0.0, shadow=True, alpha=255):
    """Draw Bolt with body centre at (x, y). s=1 -> ~260px tall."""
    if shadow:
        sh = max(0.4, 1 - jump / 300)
        oval(c, x, y + 142 * s, 95 * s * sh, 15 * s * sh, fill(INK, 55))
    c.save()
    c.translate(x, y - jump * s)
    c.rotate(rot)
    c.scale(s * (-1 if flip else 1), s)
    sq = 1 + squash
    c.scale(1 / math.sqrt(sq), sq)

    idle = math.sin(t * 2 * math.pi * 0.9 + seed)
    # ---- cape (behind)
    fl = math.sin(t * 6 + seed) * 10
    cape = skia.Path()
    cape.moveTo(-70, -40)
    cape.quadTo(-128 - fl * 0.4, 50, -118 - fl, 128)
    cape.quadTo(-70, 112 + fl * 0.5, -30, 130)
    cape.quadTo(10, 116 - fl * 0.5, 40, 132)
    cape.quadTo(84, 114, 120 + fl, 124)
    cape.quadTo(128 + fl * 0.4, 50, 70, -40)
    cape.close()
    outlined(c, cape, CAPE, 7)

    # ---- feet
    for fx in (-42, 42):
        oval(c, fx, 124, 30, 17, fill(SHOE))
        oval(c, fx, 124, 30, 17, stroke(INK, 6))
        oval(c, fx - 6, 118, 12, 5, fill("#FFFFFF", 160))

    # ---- antenna bolt (behind body top)
    c.save()
    c.translate(0, -100)
    c.rotate(math.sin(t * 3.1 + seed) * 7)
    bolt = poly([(-6, 8), (-20, -42), (-2, -40), (-14, -82), (26, -30), (6, -32), (16, 8)])
    outlined(c, bolt, "#FFE45C", 6)
    c.restore()

    # ---- body
    body = skia.Path()
    body.addOval(skia.Rect.MakeLTRB(-108, -112, 108, 118))
    paint = fill(BOLT_BODY)
    paint.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(0, -112), skia.Point(0, 118)], [col(BOLT_LIGHT), col(BOLT_BODY), col(BOLT_SHADE)],
        [0.0, 0.45, 1.0]))
    c.drawPath(body, paint)
    # belly badge with bolt
    oval(c, 0, 97, 19, 13, fill("#FFF3C4"))
    oval(c, 0, 97, 19, 13, stroke(INK, 3.5))
    badge = poly([(-2, 87), (-7, 98), (0, 98), (-3, 107), (8, 95), (1, 95), (4, 87)])
    c.drawPath(badge, fill(CAPE))
    c.drawPath(body, stroke(INK, 7))
    # cheek blush
    circle(c, -68, 22, 15, fill(CHEEK, 130))
    circle(c, 68, 22, 15, fill(CHEEK, 130))
    # shine
    oval(c, -52, -70, 20, 11, fill("#FFFFFF", 150))

    # ---- face
    b = blink_amount(t, seed)
    if mood == "tired":
        b = max(b, 0.0)
    _brows(c, mood, t)
    for side, ex in ((-1, -40), (1, 40)):
        _eye(c, ex, -22, 27, 33, b, look, mood, side)
    _mouth(c, mood, mouth, t)

    # ---- arms
    (rh, lh) = POSES.get(pose, POSES["down"])
    rhx, rhy = rh
    lhx, lhy = lh
    if pose == "wave":
        rhx += math.sin(t * 9) * 18
        rhy += math.cos(t * 9) * 8
    if pose == "cheer":
        k = math.sin(t * 7)
        rhy += k * 22
        lhy -= k * 22
    if pose in ("down", "hips", "hold", "point", "think"):
        rhy += idle * 3
        lhy += idle * 3
    if pose == "point":
        rhx += math.sin(t * 4) * 4
    if pose == "scared":
        rhx += math.sin(t * 40) * 2
        lhx += math.sin(t * 40 + 1) * 2
    bend_r = -20 if rhy < 0 else 22
    bend_l = 20 if lhy < 0 else -22
    if pose == "hips":
        bend_r, bend_l = 40, -40
    if pose == "think":
        bend_r = 50
    _arm(c, -92, 18, lhx, lhy, bend_l, BOLT_BODY)
    _arm(c, 92, 18, rhx, rhy, bend_r, BOLT_BODY, fist=(pose == "fist"))
    c.restore()

    hx = x + rhx * s * (-1 if flip else 1)
    hy = y - jump * s + rhy * s
    if hold:
        P.draw(c, hold, hx, hy - 40 * s, s * 0.55, t)
        # thumb over the prop so it looks held
        circle(c, hx, hy, 17 * s, fill(BOLT_BODY))
        circle(c, hx, hy, 17 * s, stroke(INK, 5 * s))
    return (hx, hy)


# ----------------------------------------------------------------------------
# LORD LATER
# ----------------------------------------------------------------------------
LATER_TOP = "#B4A0E5"
LATER_MID = "#8E74D0"
LATER_BOT = "#5E4A9E"
LATER_LID = "#6A55B0"

_CLOUD = [(0, -5, 98), (-82, 22, 70), (82, 22, 70), (-52, -62, 62), (50, -66, 64),
          (0, -92, 58), (-38, 72, 58), (40, 72, 58), (0, 60, 66)]


@lru_cache(maxsize=1)
def _cloud_path():
    path = None
    for (x, y, r) in _CLOUD:
        p = skia.Path()
        p.addCircle(x, y, r)
        path = p if path is None else skia.Op(path, p, skia.PathOp.kUnion_PathOp)
    # little tail curl
    tail = skia.Path()
    tail.moveTo(-20, 110)
    tail.quadTo(0, 175, 40, 160)
    tail.quadTo(70, 150, 52, 128)
    tail.quadTo(40, 150, 20, 140)
    tail.quadTo(10, 128, 22, 112)
    tail.close()
    path = skia.Op(path, tail, skia.PathOp.kUnion_PathOp)
    return path


def _later_eye(c, ex, ey, mood, look, b, side):
    rx, ry = 25, 23
    if mood in ("shocked",):
        rx, ry = 28, 30
    ry_eff = max(2.5, ry * (1 - b))
    if mood == "laugh":
        p = skia.Path()
        p.moveTo(ex - 20, ey + 4)
        p.quadTo(ex, ey - 18, ex + 20, ey + 4)
        c.drawPath(p, stroke(INK, 7))
        return
    if mood == "defeated":
        for d in (-1, 1):
            p = skia.Path()
            p.moveTo(ex - 14, ey - 14 * d)
            p.lineTo(ex + 14, ey + 14 * d)
            c.drawPath(p, stroke(INK, 7))
        return
    oval(c, ex, ey, rx, ry_eff, fill("#FFFFFF"))
    c.save()
    clip = skia.Path()
    clip.addOval(skia.Rect.MakeLTRB(ex - rx, ey - ry_eff, ex + rx, ey + ry_eff))
    c.clipPath(clip, doAntiAlias=True)
    pr = 7 if mood == "shocked" else 11
    px, py = ex + look[0] * 9, ey + 7 + look[1] * 5
    if mood == "shocked":
        py = ey
    circle(c, px, py, pr, fill(INK))
    circle(c, px - 3, py - 4, 3.5, fill("#FFFFFF"))
    if mood not in ("shocked",):
        if mood == "angry":
            if side > 0:
                lid = poly([(ex - rx - 2, ey - ry - 2), (ex + rx + 2, ey - ry - 2), (ex + rx + 2, ey - ry * 0.5), (ex - rx - 2, ey + ry * 0.15)])
            else:
                lid = poly([(ex - rx - 2, ey - ry - 2), (ex + rx + 2, ey - ry - 2), (ex + rx + 2, ey + ry * 0.15), (ex - rx - 2, ey - ry * 0.5)])
        else:  # sleepy smug lids
            lid = poly([(ex - rx - 2, ey - ry - 2), (ex + rx + 2, ey - ry - 2), (ex + rx + 2, ey - 1), (ex - rx - 2, ey - 1)])
        c.drawPath(lid, fill(LATER_LID))
        p = skia.Path()
        p.moveTo(ex - rx, ey - 1 if mood != "angry" else ey)
        c.drawPath(lid, stroke(INK, 4))
    c.restore()
    oval(c, ex, ey, rx, ry_eff, stroke(INK, 5))
    # eye bags
    p = skia.Path()
    p.moveTo(ex - 15, ey + ry + 7)
    p.quadTo(ex, ey + ry + 14, ex + 15, ey + ry + 7)
    c.drawPath(p, stroke(LATER_BOT, 4))


def draw_later(c, x, y, s=1.0, t=0.0, mood="smug", mouth=0.0, look=(-0.6, 0.0), hold=None,
               zzz=True, alpha=255, seed=3, rot=None, glow=True):
    """Lord Later, a sleepy purple procrastination cloud wearing a crown."""
    fy = math.sin(t * 1.6 + seed) * 12
    r = math.sin(t * 0.9 + seed) * 3 if rot is None else rot
    if glow:
        oval(c, x, y + 210 * s, 100 * s, 16 * s, fill(INK, 45))
    c.save()
    c.translate(x, y + fy * s)
    c.rotate(r)
    c.scale(s, s)
    if alpha < 255:
        c.saveLayerAlpha(None, alpha)
    path = _cloud_path()
    if glow:
        c.drawPath(path, blurred(LATER_MID, 22, 90))
    paint = fill(LATER_MID)
    paint.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(0, -150), skia.Point(0, 170)], [col(LATER_TOP), col(LATER_MID), col(LATER_BOT)],
        [0.0, 0.5, 1.0]))
    c.drawPath(path, paint)
    c.drawPath(path, stroke(INK, 7))
    # highlight puffs
    oval(c, -55, -80, 22, 12, fill("#FFFFFF", 110))
    oval(c, 40, -100, 14, 8, fill("#FFFFFF", 90))

    # crown
    c.save()
    c.translate(18, -140)
    c.rotate(14 + math.sin(t * 1.3) * 3)
    crown = poly([(-42, 18), (-46, -26), (-22, -4), (0, -36), (22, -4), (46, -26), (42, 18)])
    outlined(c, crown, "#FFD23F", 6)
    circle(c, 0, 4, 8, fill("#E63946"))
    circle(c, 0, 4, 8, stroke(INK, 3))
    for gx in (-46, 0, 46):
        gy = -26 if gx else -36
        circle(c, gx, gy, 6, fill("#FFD23F"))
        circle(c, gx, gy, 6, stroke(INK, 3))
    c.restore()

    # face
    b = blink_amount(t, seed) if mood not in ("defeated", "laugh") else 0
    for side, ex in ((-1, -38), (1, 38)):
        _later_eye(c, ex, -8, mood, look, b, side)
    if mood == "angry":
        for (a, bb) in (((-62, -44), (-18, -32)), ((18, -32), (62, -44))):
            p = skia.Path()
            p.moveTo(*a)
            p.lineTo(*bb)
            c.drawPath(p, stroke(INK, 8))
    my = 46
    if mood == "shocked":
        oval(c, 0, my + 6, 16, 20 + mouth * 6, fill("#3B1F4F"))
        oval(c, 0, my + 6, 16, 20 + mouth * 6, stroke(INK, 5))
    elif mood == "defeated":
        p = skia.Path()
        p.moveTo(-30, my + 6)
        for i in range(5):
            p.quadTo(-24 + i * 12, my + (-4 if i % 2 == 0 else 14), -18 + i * 12, my + 6)
        c.drawPath(p, stroke(INK, 6))
    elif mouth > 0.06 or mood == "laugh":
        mm = max(mouth, 0.6 if mood == "laugh" else 0)
        w, h = 30, 8 + 30 * mm
        p = skia.Path()
        p.moveTo(-w, my - 2)
        p.quadTo(4, my + 4, w + 6, my - 8)
        p.quadTo(w, my + h, 0, my + h)
        p.quadTo(-w, my + h, -w, my - 2)
        p.close()
        c.drawPath(p, fill("#3B1F4F"))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        oval(c, 0, my + h + 2, 18, h * 0.4, fill("#E77FA8"))
        c.restore()
        c.drawPath(p, stroke(INK, 5))
    else:
        p = skia.Path()
        if mood == "angry":
            p.moveTo(-26, my + 10)
            p.quadTo(0, my - 4, 26, my + 10)
        else:  # smug smirk
            p.moveTo(-28, my + 2)
            p.quadTo(0, my + 16, 34, my - 10)
        c.drawPath(p, stroke(INK, 7))
        if mood == "smug":
            # drool-less sleepy dimple
            circle(c, 38, my - 12, 3, fill(INK))

    # stubby arms
    arm_y = 62 + math.sin(t * 2.2) * 6
    for ax in (-140, 140):
        circle(c, ax, arm_y, 24, fill(LATER_MID))
        circle(c, ax, arm_y, 24, stroke(INK, 6))
        for k in (-1, 1):
            circle(c, ax + k * 11, arm_y + 17, 8, fill(LATER_MID))
            circle(c, ax + k * 11, arm_y + 17, 8, stroke(INK, 4))
    if alpha < 255:
        c.restore()
    c.restore()

    if hold:
        P.draw(c, hold, x - 140 * s, y + (fy + arm_y - 60) * s, s * 0.6, t)
        circle(c, x - 140 * s, y + (fy + arm_y) * s, 24 * s, fill(LATER_MID))
        circle(c, x - 140 * s, y + (fy + arm_y) * s, 24 * s, stroke(INK, 6 * s))
    if zzz and mood in ("smug", "laugh"):
        for i in range(3):
            ph = (t * 0.45 + i / 3) % 1.0
            zx = x + (110 + ph * 60 + math.sin(ph * 6 + i) * 12) * s
            zy = y + (-150 - ph * 140) * s
            a = int(255 * math.sin(ph * math.pi))
            draw_text(c, "z", zx, zy, "LuckiestGuy.ttf", (34 + ph * 30) * s, color="#FFFFFF",
                      outline=INK, ow=6 * s, alpha=a)
