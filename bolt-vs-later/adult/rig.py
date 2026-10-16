"""The two characters of the adult season, drawn from one 2D skeleton so they can run, punch and fall.

* YOU   - a plain cream-coloured everyman with determined brows.
* LATER - your shadow self: the same body in black with a red glow, red slit eyes and a smirk.

Angles are absolute directions in degrees: 0 = straight down, 90 = forward (+x), 180 = up, -90 = backward.
Characters face +x; pass flip=True to face left. The figure is auto-grounded: (x, ground) is where the
lowest foot/knee touches the floor, unless air > 0 lifts it.
"""
import math

import skia

from engine.gfx import circle, col, fill, oval, poly, stroke

L_TORSO, L_NECK, R_HEAD = 96, 34, 54
L_UA, L_FA = 50, 48
L_TH, L_SH = 56, 54
W_ARM, W_LEG = 23, 26

SKIN = "#E9E3D1"
SKIN_BACK = "#C9C2AE"
SKIN_SHADE = "#D6CFBB"
FACE_INK = "#26262B"
SHADOW_BODY = "#0A0A0D"
HOODIE = "#3B3E4A"
HOODIE_BACK = "#2B2E38"
SHADOW_GLOW = (235, 40, 50)
SHADOW_EYE = "#FF4D5A"

JOINTS = ("torso", "head", "ua_r", "fa_r", "ua_l", "fa_l", "th_r", "sh_r", "th_l", "sh_l")

POSES = {
    "stand":   dict(torso=180, head=180, ua_r=10, fa_r=6, ua_l=-10, fa_l=-6, th_r=6, sh_r=0, th_l=-6, sh_l=0),
    "idle":    dict(torso=178, head=177, ua_r=14, fa_r=24, ua_l=-8, fa_l=8, th_r=8, sh_r=0, th_l=-8, sh_l=-2),
    "fists":   dict(torso=178, head=178, ua_r=20, fa_r=40, ua_l=-20, fa_l=-40, th_r=14, sh_r=0, th_l=-14, sh_l=0),
    "guard":   dict(torso=172, head=172, ua_r=45, fa_r=150, ua_l=25, fa_l=160, th_r=30, sh_r=-8, th_l=-25, sh_l=-10),
    "punch":   dict(torso=160, head=165, ua_r=92, fa_r=92, ua_l=10, fa_l=150, th_r=42, sh_r=0, th_l=-32, sh_l=-14),
    "punch2":  dict(torso=163, head=168, ua_r=30, fa_r=150, ua_l=95, fa_l=95, th_r=38, sh_r=-4, th_l=-30, sh_l=-12),
    "uppercut": dict(torso=172, head=174, ua_r=150, fa_r=178, ua_l=-20, fa_l=40, th_r=22, sh_r=-10, th_l=-30, sh_l=-6),
    "kick":    dict(torso=205, head=198, ua_r=-40, fa_r=-20, ua_l=60, fa_l=120, th_r=95, sh_r=92, th_l=-4, sh_l=-6),
    "hit":     dict(torso=205, head=215, ua_r=-60, fa_r=-30, ua_l=-80, fa_l=-50, th_r=20, sh_r=10, th_l=-20, sh_l=-30),
    "charge":  dict(torso=180, head=182, ua_r=45, fa_r=20, ua_l=-45, fa_l=-20, th_r=26, sh_r=-8, th_l=-26, sh_l=8),
    "power":   dict(torso=184, head=188, ua_r=125, fa_r=145, ua_l=-125, fa_l=-145, th_r=24, sh_r=-6, th_l=-24, sh_l=6),
    "push":    dict(torso=150, head=158, ua_r=92, fa_r=96, ua_l=86, fa_l=92, th_r=60, sh_r=-10, th_l=-45, sh_l=-35),
    "crouch":  dict(torso=150, head=164, ua_r=60, fa_r=110, ua_l=-20, fa_l=40, th_r=60, sh_r=-15, th_l=-50, sh_l=-25),
    "kneel":   dict(torso=172, head=150, ua_r=25, fa_r=15, ua_l=0, fa_l=-5, th_r=92, sh_r=0, th_l=-8, sh_l=-92),
    "crawl":   dict(torso=120, head=140, ua_r=40, fa_r=10, ua_l=20, fa_l=-10, th_r=60, sh_r=-60, th_l=20, sh_l=-80),
    "sit":     dict(torso=182, head=170, ua_r=50, fa_r=95, ua_l=40, fa_l=90, th_r=90, sh_r=0, th_l=86, sh_l=-4),
    "slump":   dict(torso=198, head=152, ua_r=22, fa_r=60, ua_l=12, fa_l=40, th_r=88, sh_r=6, th_l=84, sh_l=2),
    "phone":   dict(torso=188, head=142, ua_r=40, fa_r=140, ua_l=30, fa_l=130, th_r=88, sh_r=6, th_l=84, sh_l=2),
    "type":    dict(torso=172, head=170, ua_r=70, fa_r=95, ua_l=60, fa_l=92, th_r=90, sh_r=0, th_l=86, sh_l=-4),
    "victory": dict(torso=180, head=188, ua_r=168, fa_r=176, ua_l=-30, fa_l=-10, th_r=12, sh_r=0, th_l=-12, sh_l=0),
    "point":   dict(torso=178, head=176, ua_r=88, fa_r=92, ua_l=-14, fa_l=-6, th_r=10, sh_r=0, th_l=-10, sh_l=0),
    "offer":   dict(torso=176, head=170, ua_r=70, fa_r=110, ua_l=-12, fa_l=-6, th_r=8, sh_r=0, th_l=-8, sh_l=0),
    "lookup":  dict(torso=184, head=202, ua_r=10, fa_r=6, ua_l=-10, fa_l=-6, th_r=6, sh_r=0, th_l=-6, sh_l=0),
    "head_down": dict(torso=172, head=140, ua_r=8, fa_r=4, ua_l=-6, fa_l=-2, th_r=6, sh_r=0, th_l=-6, sh_l=0),
    "lift":    dict(torso=180, head=180, ua_r=150, fa_r=178, ua_l=-150, fa_l=-178, th_r=24, sh_r=-4, th_l=-24, sh_l=4),
    "curl":    dict(torso=180, head=176, ua_r=10, fa_r=160, ua_l=-10, fa_l=-160, th_r=10, sh_r=0, th_l=-10, sh_l=0),
    "jump":    dict(torso=172, head=174, ua_r=150, fa_r=165, ua_l=-60, fa_l=-30, th_r=100, sh_r=-40, th_l=40, sh_l=-60),
    "dash":    dict(torso=130, head=140, ua_r=-60, fa_r=-50, ua_l=-50, fa_l=-40, th_r=62, sh_r=-40, th_l=-50, sh_l=-80),
    "arms_cross": dict(torso=178, head=172, ua_r=30, fa_r=-80, ua_l=20, fa_l=-75, th_r=8, sh_r=0, th_l=-8, sh_l=0),
    "lean_back": dict(torso=196, head=186, ua_r=-30, fa_r=-40, ua_l=-40, fa_l=-50, th_r=20, sh_r=0, th_l=-10, sh_l=0),
}


def run_pose(p):
    a = math.sin(p * 2 * math.pi)
    b = math.cos(p * 2 * math.pi)
    return dict(torso=164, head=168, ua_r=-50 * a + 15, fa_r=-50 * a + 90, ua_l=50 * a + 15, fa_l=50 * a + 90,
                th_r=48 * a + 18, sh_r=48 * a - 30 + 30 * max(0, -b), th_l=-48 * a + 18, sh_l=-48 * a - 30 + 30 * max(0, b))


def walk_pose(p, tired=0.0):
    a = math.sin(p * 2 * math.pi)
    b = math.cos(p * 2 * math.pi)
    return dict(torso=176 - 18 * tired, head=176 - 25 * tired, ua_r=-20 * a + 6, fa_r=-20 * a + 20,
                ua_l=20 * a + 6, fa_l=20 * a + 20, th_r=24 * a + 4, sh_r=24 * a - 12 * max(0, -b),
                th_l=-24 * a + 4, sh_l=-24 * a - 12 * max(0, b))


def climb_pose(p):
    """Leaning into a slope / wind."""
    a = math.sin(p * 2 * math.pi)
    b = math.cos(p * 2 * math.pi)
    return dict(torso=146, head=150, ua_r=-25 * a + 40, fa_r=-25 * a + 70, ua_l=25 * a + 40, fa_l=25 * a + 70,
                th_r=30 * a + 35, sh_r=30 * a - 5 * max(0, -b), th_l=-30 * a + 35, sh_l=-30 * a - 5 * max(0, b))


def lift_pose(p):
    """Overhead press rep: p in cycles."""
    k = 0.5 - 0.5 * math.cos(p * 2 * math.pi)
    return blend(dict(POSES["lift"], ua_r=110, fa_r=200, ua_l=-110, fa_l=-200), POSES["lift"], k)


def blend(p1, p2, k):
    return {j: p1.get(j, 0) + (p2.get(j, 0) - p1.get(j, 0)) * k for j in JOINTS}


def _v(a, L):
    r = math.radians(a)
    return math.sin(r) * L, math.cos(r) * L


def skeleton(pose):
    tx, ty = _v(pose["torso"], L_TORSO)
    neck = (tx, ty)
    hx, hy = _v(pose["head"], L_NECK)
    head = (neck[0] + hx, neck[1] + hy)
    sh = (tx * 0.82, ty * 0.82)
    j = dict(pelvis=(0.0, 0.0), neck=neck, head=head, shoulder=sh)
    for s in ("r", "l"):
        ex, ey = _v(pose["ua_" + s], L_UA)
        e = (sh[0] + ex, sh[1] + ey)
        wx, wy = _v(pose["fa_" + s], L_FA)
        j["elbow_" + s], j["hand_" + s] = e, (e[0] + wx, e[1] + wy)
        kx, ky = _v(pose["th_" + s], L_TH)
        k = (kx, ky)
        ax, ay = _v(pose["sh_" + s], L_SH)
        j["knee_" + s], j["foot_" + s] = k, (k[0] + ax, k[1] + ay)
    return j


def lowest(j):
    return max(j["foot_l"][1] + 12, j["foot_r"][1] + 12, j["knee_l"][1] + 13, j["knee_r"][1] + 13)


def _limb(c, pts, w, color):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    c.drawPath(p, stroke(color, w))


def _body_path(j):
    px, py = j["pelvis"]
    nx, ny = j["neck"]
    L = math.hypot(nx - px, ny - py) or 1
    up = ((nx - px) / L, (ny - py) / L)
    perp = (-up[1], up[0])

    def P(a, s_):
        return (px + up[0] * a * L + perp[0] * s_, py + up[1] * a * L + perp[1] * s_)
    b = skia.Path()
    b.moveTo(*P(-0.22, 0))
    b.cubicTo(*P(-0.22, 52), *P(0.35, 56), *P(0.7, 44))
    b.cubicTo(*P(1.0, 36), *P(1.12, 18), *P(1.12, 0))
    b.cubicTo(*P(1.12, -18), *P(1.0, -36), *P(0.7, -44))
    b.cubicTo(*P(0.35, -56), *P(-0.22, -52), *P(-0.22, 0))
    b.close()
    return b


def _face(c, hx, hy, expr, facing_shift, t, shadow=False, ink=FACE_INK):
    fx = hx + facing_shift
    fy = hy + 4
    blink = 1.0
    ph = (t + 0.7) % 3.7
    if ph < 0.11 and expr not in ("smirk", "ko"):
        blink = 0.12
    if shadow:
        # glowing red slit eyes and a smug smile
        for sx in (-1, 1):
            e = skia.Path()
            ex = fx + sx * 17
            if expr == "angry":
                e.moveTo(ex - 11, fy - 9 - sx * 3)
                e.lineTo(ex + 11, fy - 9 + sx * 3)
            else:
                e.moveTo(ex - 11, fy - 6)
                e.quadTo(ex, fy - 13, ex + 11, fy - 6)
            c.drawPath(e, stroke(SHADOW_EYE, 6))
        m = skia.Path()
        if expr == "hurt":
            m.moveTo(fx - 10, fy + 20)
            m.quadTo(fx, fy + 12, fx + 10, fy + 20)
        else:
            m.moveTo(fx - 14, fy + 14)
            m.quadTo(fx + 2, fy + 24, fx + 16, fy + 11)
        c.drawPath(m, stroke(SHADOW_EYE, 4))
        return
    br = {
        "determined": ((-26, -18, -8, -10), (8, -10, 26, -18)),
        "angry": ((-27, -21, -7, -9), (7, -9, 27, -21)),
        "neutral": ((-26, -14, -9, -14), (9, -14, 26, -14)),
        "tired": ((-26, -10, -9, -12), (9, -12, 26, -10)),
        "sad": ((-26, -10, -8, -18), (8, -18, 26, -10)),
        "shocked": ((-26, -24, -9, -27), (9, -27, 26, -24)),
        "happy": ((-26, -18, -9, -21), (9, -21, 26, -18)),
        "ko": ((-26, -12, -9, -12), (9, -12, 26, -12)),
    }.get(expr, ((-26, -18, -8, -10), (8, -10, 26, -18)))
    for (x0, y0, x1, y1) in br:
        c.drawLine(fx + x0, fy + y0, fx + x1, fy + y1, stroke(ink, 6.5))
    for sx in (-1, 1):
        ex, ey = fx + sx * 15, fy - 2
        if expr == "ko":
            c.drawLine(ex - 5, ey - 5, ex + 5, ey + 5, stroke(ink, 4))
            c.drawLine(ex + 5, ey - 5, ex - 5, ey + 5, stroke(ink, 4))
        elif expr == "tired":
            c.drawLine(ex - 6, ey + 1, ex + 6, ey + 1, stroke(ink, 4))
        elif expr == "shocked":
            circle(c, ex, ey, 5, fill(ink))
        else:
            oval(c, ex, ey, 4, 4.5 * blink, fill(ink))
    my = fy + 17
    if expr in ("happy",):
        m = skia.Path()
        m.moveTo(fx - 10, my - 2)
        m.quadTo(fx, my + 7, fx + 10, my - 2)
        c.drawPath(m, stroke(ink, 4))
    elif expr == "shocked":
        oval(c, fx, my + 2, 5, 6, fill(ink))
    elif expr == "sad":
        m = skia.Path()
        m.moveTo(fx - 9, my + 3)
        m.quadTo(fx, my - 3, fx + 9, my + 3)
        c.drawPath(m, stroke(ink, 4))
    elif expr == "angry":
        c.drawLine(fx - 9, my + 1, fx + 9, my - 1, stroke(ink, 4.5))
    else:
        c.drawLine(fx - 8, my, fx + 8, my, stroke(ink, 4))


def draw_guy(c, x, ground, pose, s=1.0, t=0.0, flip=False, shadow=False, expr="determined", air=0.0,
             hold=None, glow=1.0, alpha=255, sweat=0.0, breath=0.0, rot=0.0, seat=None, hoodie=False):
    """Draw a character standing on `ground` (y) at x. Returns joint positions in world coords."""
    j = skeleton(pose)
    base = lowest(j)
    sx = -s if flip else s
    oy = ground - (base + air) * s if seat is None else seat
    c.save()
    c.translate(x, oy)
    if rot:
        c.rotate(rot)
    c.scale(sx, s)
    layer = False
    if shadow:
        r, g, b = SHADOW_GLOW
        p = skia.Paint(ImageFilter=skia.ImageFilters.DropShadow(0, 0, 9 / s, 9 / s,
                                                                 skia.Color(r, g, b, int(255 * glow)), None))
        if alpha < 255:
            p.setAlphaf(alpha / 255)
        c.saveLayer(None, p)
        layer = True
    elif alpha < 255:
        c.saveLayerAlpha(None, alpha)
        layer = True
    body_c = SHADOW_BODY if shadow else (HOODIE if hoodie else SKIN)
    back_c = SHADOW_BODY if shadow else (HOODIE_BACK if hoodie else SKIN_BACK)
    hand_c = body_c if (shadow or not hoodie) else SKIN
    hand_back = back_c if (shadow or not hoodie) else SKIN_BACK
    _limb(c, [j["shoulder"], j["elbow_l"], j["hand_l"]], W_ARM, back_c)
    circle(c, *j["hand_l"], 13, fill(hand_back))
    _limb(c, [j["pelvis"], j["knee_l"], j["foot_l"]], W_LEG, back_c)
    _foot(c, j["foot_l"], back_c)
    body = _body_path(j)
    bp = fill(body_c)
    if not shadow and not hoodie:
        nx, ny = j["neck"]
        bp.setShader(skia.GradientShader.MakeLinear([skia.Point(nx - 50, ny - 20), skia.Point(nx + 40, ny + 120)],
                                                    [col("#F3EEDF"), col(SKIN), col(SKIN_SHADE)], [0, 0.5, 1]))
    c.drawPath(body, bp)
    _limb(c, [j["pelvis"], j["knee_r"], j["foot_r"]], W_LEG, body_c)
    _foot(c, j["foot_r"], body_c)
    raised = j["hand_r"][1] < j["neck"][1] + 10
    if raised and not hoodie:
        _limb(c, [j["shoulder"], j["elbow_r"], j["hand_r"]], W_ARM, body_c)
        circle(c, *j["hand_r"], 14, fill(hand_c))
    hx, hy = j["head"]
    if hoodie and not shadow:
        oval(c, hx - 4, hy - 4, R_HEAD * 1.24, R_HEAD * 1.22, fill(HOODIE_BACK))
    hp = fill(SKIN if (hoodie and not shadow) else body_c)
    if not shadow:
        hp.setShader(skia.GradientShader.MakeRadial(skia.Point(hx - 18, hy - 22), 80,
                                                    [col("#F6F2E6"), col(SKIN), col(SKIN_SHADE)], [0, 0.6, 1]))
    if hoodie and not shadow:
        oval(c, hx + 4, hy + 4, R_HEAD * 0.86, R_HEAD * 0.9, hp)
        rim = skia.Path()
        rim.addArc(skia.Rect.MakeLTRB(hx - R_HEAD * 1.02, hy - R_HEAD * 1.06, hx + R_HEAD * 1.06, hy + R_HEAD * 1.1), 150, 240)
        c.drawPath(rim, stroke(HOODIE, 16))
    else:
        oval(c, hx, hy, R_HEAD * 0.98, R_HEAD, hp)
    _face(c, hx + (4 if hoodie else 0), hy + (4 if hoodie else 0), expr, 7, t, shadow=shadow)
    if sweat > 0 and not shadow:
        for k in range(2):
            ph = (t * 0.9 + k * 0.5) % 1
            dx, dy = hx - 40 + k * 70, hy - 20 + ph * 40
            drop = poly([(dx, dy - 8), (dx + 5, dy + 3), (dx, dy + 7), (dx - 5, dy + 3)])
            c.drawPath(drop, fill("#9AD1FF", int(200 * sweat * (1 - ph))))
    if not raised or hoodie:
        _limb(c, [j["shoulder"], j["elbow_r"], j["hand_r"]], W_ARM, body_c)
        circle(c, *j["hand_r"], 14, fill(hand_c))
    if layer:
        c.restore()
    c.restore()
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = {k: (x + (v[0] * sx) * cr - (v[1] * s) * sr, oy + (v[0] * sx) * sr + (v[1] * s) * cr) for k, v in j.items()}
    if breath > 0 and not shadow:
        bx, by = out["head"]
        for k in range(3):
            ph = (t * 0.7 + k / 3) % 1
            oval(c, bx + (60 + ph * 90) * (sx / abs(sx)) * s, by + 14 * s - ph * 20 * s, (12 + ph * 30) * s, (8 + ph * 16) * s,
                 _soft("#DDE6F0", int(110 * breath * (1 - ph))))
    return out


def _soft(color, a):
    p = fill(color, a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8))
    return p


def _foot(c, foot, color):
    fx, fy = foot
    oval(c, fx + 9, fy + 2, 19, 11, fill(color))
