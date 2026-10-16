"""Shot library for the adult season. Each shot draws one frame from its local time.

ctx keys: t (local s), d (duration s), T (global s), p (params), beat (s per beat), ep (episode dict)
"""
import math
import random

import skia

from engine.gfx import blurred, circle, clamp, col, draw_text, ease_in_out, ease_out_back, ease_out_cubic, fill, \
    fit_lines, lerp, mix, oval, poly, rrect, stroke, text_width, wrap
from . import fx
from . import things as Th
from .rig import POSES, blend, climb_pose, draw_guy, lift_pose, run_pose, walk_pose

W, H, G = fx.W, fx.H, fx.GROUND
BIG = "Fredoka-Bold.ttf"
UI = "Inter-Bold.otf"
RED = "#FF4D5A"
WARM = "#F2D492"
TXT = "#EDEFF3"


# ----------------------------------------------------------------------------- shared helpers

def camera(c, t, d, p):
    z0, z1 = p.get("zoom", (1.0, 1.06))
    k = ease_in_out(t / max(d, 0.01))
    z = lerp(z0, z1, k)
    px, py = p.get("pan", (0, 0))
    cx, cy = p.get("focus", (W / 2, H * 0.55))
    c.translate(cx, cy)
    c.scale(z, z)
    c.translate(-cx - px * k, -cy - py * k)


def shake(c, amt, T):
    if amt > 0:
        c.translate(math.sin(T * 91) * amt, math.cos(T * 77) * amt)


def day_label(c, p, t, d):
    day = p.get("day")
    if day is None:
        return
    if isinstance(day, (tuple, list)):
        d0, d1 = day
        v = int(round(lerp(d0, d1, ease_in_out(clamp(t / max(0.1, d * 0.85))))))
        txt = f"DAY {v}"
    else:
        txt = day if isinstance(day, str) else f"DAY {day}"
    a = int(255 * clamp(t / 0.4))
    draw_text(c, txt, 70, fx.BAR + 62, BIG, 44, color="#C8CCD4", align="left", alpha=a)


def rich_line(c, line, cx, y, size, accent=RED, alpha=255, font=BIG, shadow=True):
    """Draw a line where *words* are accented."""
    parts = []
    for i, seg in enumerate(line.split("*")):
        if seg:
            parts.append((seg, i % 2 == 1))
    total = sum(text_width(s_, font, size) for s_, _ in parts)
    x = cx - total / 2
    for s_, em in parts:
        if shadow:
            draw_text(c, s_, x, y + size * 0.06, font, size, color="#000000", align="left", alpha=int(alpha * 0.7))
        draw_text(c, s_, x, y, font, size, color=accent if em else TXT, align="left", alpha=alpha)
        x += text_width(s_, font, size)


def statement(c, p, t, beat, y=300, size=96):
    """Big on-screen lines that appear one per `every` beats."""
    lines = p.get("text") or []
    if isinstance(lines, str):
        lines = [lines]
    every = p.get("every", 4) * beat
    start = p.get("text_at", 0.6) * beat
    yy = p.get("text_y", y)
    sz = p.get("text_size", size)
    for i, ln in enumerate(lines):
        tt = t - start - i * every
        if tt < 0:
            continue
        a = int(255 * clamp(tt / 0.35))
        k = 1 + 0.12 * (1 - ease_out_cubic(clamp(tt / 0.35)))
        c.save()
        c.translate(W / 2, yy + i * sz * 1.15)
        c.scale(k, k)
        rich_line(c, ln, 0, 0, sz, p.get("accent", RED), a)
        c.restore()


def glow_spot(c, x, y, r, color, a):
    circle(c, x, y, r, blurred(color, r * 0.4, a))


# ----------------------------------------------------------------------------- shots

def shot_title(c, ctx):
    t, d, T, p, ep = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["ep"]
    c.clear(col("#050507"))
    fx.snow(c, T, n=90, wind=0.3, alpha=110)
    # the shadow's eyes open in the dark
    if t > 0.4:
        a = clamp((t - 0.4) / 0.6)
        blink = 0.15 if 1.9 < t < 2.0 else 1
        for sx in (-1, 1):
            e = skia.Path()
            ex = W / 2 + sx * 120
            e.moveTo(ex - 60, 640)
            e.quadTo(ex, 640 - 34 * blink, ex + 60, 640)
            c.drawPath(e, stroke(RED, 14, a=int(160 * a)))
            c.drawPath(e, blurred(RED, 18, int(90 * a)))
    k = ease_out_cubic(clamp((t - 1.0) / 0.6))
    if k > 0:
        draw_text(c, f"EPISODE {ep['num']:02d}", W / 2, 300, UI, 34, color="#8A8F9C", alpha=int(255 * k))
        size = ep.get("title_size", 132)
        for i, ln in enumerate(ep["title_lines"]):
            c.save()
            c.translate(W / 2, 430 + i * size * 1.02)
            sc = 1 + 0.25 * (1 - k)
            c.scale(sc, sc)
            rich_line(c, ln, 0, 0, size, RED, int(255 * k))
            c.restore()


def shot_end(c, ctx):
    t, d, T, p, ep = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["ep"]
    c.clear(col("#050507"))
    fx.snow(c, T, n=80, wind=0.25, alpha=90)
    a = int(255 * clamp(t / 0.6))
    rich_line(c, "VS *LATER*", W / 2, 360, 120, RED, a)
    draw_text(c, "a new fight every week", W / 2, 430, UI, 34, color="#8A8F9C", alpha=a)
    if p.get("next"):
        b = int(255 * clamp((t - 1.0) / 0.6))
        draw_text(c, "NEXT EPISODE", W / 2, 600, UI, 30, color="#8A8F9C", alpha=b)
        rich_line(c, p["next"], W / 2, 680, 64, RED, b)
    draw_guy(c, 420, G + 40, POSES["arms_cross"], 0.9, T, expr="determined", alpha=a)
    draw_guy(c, 1500, G + 40, POSES["arms_cross"], 0.9, T, shadow=True, expr="smirk", flip=True, alpha=a)


def shot_text(c, ctx):
    t, d, T, p = ctx["t"], ctx["d"], ctx["T"], ctx["p"]
    c.clear(col("#060608"))
    env = p.get("env")
    if env == "void":
        c.drawImage(fx.void(), 0, 0)
    fx.snow(c, T, n=110, wind=p.get("wind", 0.4), alpha=120)
    if p.get("walker"):
        x = lerp(-100, W + 100, t / d)
        draw_guy(c, x, G, walk_pose(T * 0.9, p.get("tired", 0.0)), 0.7, T, expr=p.get("expr", "determined"),
                 alpha=150, breath=0.6, hoodie=True)
    if p.get("eyes"):
        a = clamp(t / 1.0)
        for sx in (-1, 1):
            e = skia.Path()
            ex = W / 2 + sx * 90
            e.moveTo(ex - 45, 780)
            e.quadTo(ex, 760, ex + 45, 780)
            c.drawPath(e, stroke(RED, 10, a=int(120 * a)))
    statement(c, p, t, ctx["beat"], y=p.get("text_y", 420), size=p.get("text_size", 104))


def shot_stat(c, ctx):
    t, d, T, p = ctx["t"], ctx["d"], ctx["T"], ctx["p"]
    c.clear(col("#060608"))
    c.drawImage(fx.void(p.get("tint", "#E63946")), 0, 0)
    fx.snow(c, T, n=80, wind=0.3, alpha=90)
    k = ease_out_cubic(clamp((t - 0.3) / 1.6))
    num = p["num"]
    val = num * k
    s = (f"{val:.1f}" if isinstance(num, float) and not float(num).is_integer() else f"{int(round(val)):,}")
    s = p.get("prefix", "") + s + p.get("suffix", "")
    a = int(255 * clamp(t / 0.4))
    draw_text(c, s, W / 2, 520, BIG, 250, color=p.get("color", RED), alpha=a)
    for i, ln in enumerate(wrap(p.get("label", ""), BIG, 58, 1300)):
        draw_text(c, ln, W / 2, 640 + i * 68, BIG, 58, color=TXT, alpha=a)
    if p.get("source"):
        draw_text(c, p["source"], W / 2, 640 + 68 * len(wrap(p.get("label", ""), BIG, 58, 1300)) + 30, UI, 26,
                  color="#7E8494", alpha=a)


def _room_bg(c, p, T):
    c.drawImage(fx.room(window=p.get("window", True)), 0, 0)
    if p.get("clock", True):
        Th.draw(c, "wall_clock", 1700, 300, 0.9, T, speed=p.get("clock_speed", 60))


def shot_room(c, ctx):
    t, d, T, p = ctx["t"], ctx["d"], ctx["T"], ctx["p"]
    c.save()
    camera(c, t, d, p)
    _room_bg(c, p, T)
    for (name, x, kw) in p.get("props", []):
        kw = dict(kw)
        y = kw.pop("y", G)
        sc = kw.pop("s", 1.0)
        Th.draw(c, name, x, y, sc, T, **kw)
    act = p.get("act", "chair_phone")
    expr = p.get("expr", "tired")
    hx = p.get("x", 900)
    shadow = p.get("shadow")
    if act == "chair_phone":
        Th.draw(c, "gaming_chair", hx, G, 1.0, T)
        j = draw_guy(c, hx + 6, G, POSES["phone"], 1.0, T, expr=expr, seat=G - 92)
        mx = (j["hand_r"][0] + j["hand_l"][0]) / 2
        my = (j["hand_r"][1] + j["hand_l"][1]) / 2 - 18
        Th.draw(c, "phone", mx, my, 1.0, T, glow=1.0)
    elif act == "desk":
        Th.draw(c, "desk", hx + 170, G, 1.0, T)
        Th.draw(c, "laptop", hx + 210, G - 150, 1.0, T, glow=p.get("glow", 1.0))
        Th.draw(c, "gaming_chair", hx - 10, G, 0.9, T)
        pose = POSES["type"] if p.get("typing", True) else POSES["slump"]
        if p.get("typing", True):
            pose = dict(pose, fa_r=pose["fa_r"] + math.sin(T * 30) * 6, fa_l=pose["fa_l"] + math.cos(T * 27) * 6)
        draw_guy(c, hx, G, pose, 1.0, T, expr=expr, seat=G - 90)
    elif act == "bed_phone":
        Th.draw(c, "bed", hx, G, 1.0, T)
        pose = dict(POSES["stand"], ua_r=165, fa_r=200, ua_l=160, fa_l=195, head=186)
        j = draw_guy(c, hx - 80, G - 120, pose, 0.95, T, expr=expr, rot=-90, seat=G - 128)
        Th.draw(c, "phone", j["hand_r"][0] + 10, j["hand_r"][1], 1.0, T, glow=1.0, rot=90)
    elif act == "bed_wake":
        Th.draw(c, "bed", hx, G, 1.0, T)
        k = ease_in_out(clamp((t - p.get("wake_at", 1.5)) / 0.8))
        rot = lerp(-90, 0, k)
        pose = blend(POSES["stand"], POSES["sit"], k)
        draw_guy(c, hx - 80 + 40 * k, G - 120, pose, 0.95, T, expr="shocked" if k > 0.3 else "tired", rot=rot, seat=G - 128 + 10 * k)
        ring = 1.0 if t < p.get("wake_at", 1.5) + 0.6 else 0.0
        Th.draw(c, "alarm", hx + 300, G - 160, 1.0, T, ring=ring)
    elif act == "stand":
        draw_guy(c, hx, G, POSES[p.get("pose", "idle")], 1.0, T, expr=expr, flip=p.get("flip", False))
    elif act == "walk_out":
        k = clamp(t / d)
        x = lerp(hx, hx + 700, k)
        draw_guy(c, x, G, walk_pose(T * 1.1), 1.0, T, expr="determined")
    if shadow:
        sx = p.get("sx", hx - 260)
        if shadow == "behind":
            draw_guy(c, sx, G, dict(POSES["offer"], ua_r=60, fa_r=80), 1.05, T, shadow=True, expr="smirk")
        elif shadow == "offer":
            k = ease_out_cubic(clamp(t / 1.2))
            x = lerp(sx - 300, sx, k)
            j = draw_guy(c, x, G, POSES["offer"], 1.05, T, shadow=True, expr="smirk")
            Th.draw(c, p.get("offer", "pizza_box"), j["hand_r"][0] + 30, j["hand_r"][1] + 20, 0.6, T, open_=False)
        elif shadow == "lean":
            draw_guy(c, sx, G, POSES["arms_cross"], 1.05, T, shadow=True, expr="smirk", flip=True)
        elif shadow == "chair":
            Th.draw(c, "gaming_chair", sx, G, 1.0, T)
            j = draw_guy(c, sx + 6, G, POSES["phone"], 1.0, T, shadow=True, expr="smirk", seat=G - 92)
            Th.draw(c, "phone", (j["hand_r"][0] + j["hand_l"][0]) / 2, (j["hand_r"][1] + j["hand_l"][1]) / 2 - 18, 1.0, T)
        elif shadow == "loom":
            draw_guy(c, sx, G, POSES["arms_cross"], 1.6, T, shadow=True, expr="smirk", flip=True)
    c.restore()
    statement(c, p, t, ctx["beat"], y=p.get("text_y", 230), size=p.get("text_size", 84))
    day_label(c, p, t, d)


def shot_gym(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    c.save()
    camera(c, t, d, p)
    c.drawImage(fx.gym(), 0, 0)
    Th.draw(c, "plate", 300, 560, 1.4, T)
    Th.draw(c, "plate", 1640, 240, 1.0, T)
    Th.draw(c, "dumbbell", 1640, 820, 1.2, T)
    act = p.get("act", "lift")
    rep = T / (beat * p.get("beats_per_rep", 2))
    hx = p.get("x", 960)
    sweat = p.get("sweat", 0.6)
    if act == "lift":
        Th.draw(c, "rack", hx, G, 1.0, T)
        j = draw_guy(c, hx, G, lift_pose(rep), 1.2, T, expr="angry", sweat=sweat)
        Th.draw(c, "barbell", (j["hand_r"][0] + j["hand_l"][0]) / 2, (j["hand_r"][1] + j["hand_l"][1]) / 2, 1.15, T)
    elif act == "curl":
        k = 0.5 - 0.5 * math.cos(rep * 2 * math.pi)
        pose = dict(POSES["curl"], fa_r=lerp(10, 165, k), fa_l=lerp(-10, -165, k))
        j = draw_guy(c, hx, G, pose, 1.0, T, expr="angry", sweat=sweat)
        for hnd in ("hand_r", "hand_l"):
            Th.draw(c, "dumbbell", j[hnd][0], j[hnd][1], 0.55, T, rot=90)
    elif act == "squat":
        k = 0.5 - 0.5 * math.cos(rep * 2 * math.pi)
        pose = blend(POSES["fists"], dict(POSES["crouch"], torso=165, head=170, th_r=80, sh_r=-10, th_l=-60, sh_l=-10), k)
        pose = dict(pose, ua_r=150, fa_r=60, ua_l=-150, fa_l=-60)
        j = draw_guy(c, hx, G, pose, 1.0, T, expr="angry", sweat=sweat)
        Th.draw(c, "barbell", j["neck"][0], j["neck"][1] + 10, 1.0, T)
    elif act == "pushup":
        k = 0.5 - 0.5 * math.cos(rep * 2 * math.pi)
        pose = dict(POSES["stand"], ua_r=180 + 0, fa_r=180, ua_l=180, fa_l=180)
        draw_guy(c, hx, G - 40 - 30 * k, POSES["stand"], 0.95, T, expr="angry", rot=-78, sweat=sweat, seat=G - 70 + 26 * k)
    if p.get("shadow") == "bench":
        Th.draw(c, "bench", 1450, G, 1.0, T)
        j = draw_guy(c, 1450, G, POSES["sit"], 1.0, T, shadow=True, expr="smirk", flip=True, seat=G - 92)
        Th.draw(c, "pizza_box", 1300, G, 0.6, T)
    elif p.get("shadow") == "lean":
        draw_guy(c, 1500, G, POSES["arms_cross"], 1.0, T, shadow=True, expr="angry", flip=True)
    if p.get("reps"):
        n = int(t / (beat * p.get("beats_per_rep", 2))) + 1
        draw_text(c, f"x{n}", hx + 260, 330, BIG, 64, color="#C8CCD4", alpha=200)
    c.restore()
    statement(c, p, t, beat, y=p.get("text_y", 220), size=p.get("text_size", 84))
    day_label(c, p, t, d)


def _scrolling(c, img, offset):
    off = offset % W
    c.drawImage(img, -off, 0)
    c.drawImage(img, W - off, 0)


def shot_run(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    dawn = p.get("dawn", 0.0)
    speed = p.get("speed", 520)
    c.save()
    camera(c, t, d, dict(p, zoom=p.get("zoom", (1.0, 1.0))))
    _scrolling(c, fx.street(dawn=round(dawn, 2)), T * speed * 0.35)
    for i in range(4):
        x = (i * 640 - T * speed) % (W + 640) - 320
        fx.lamp_post(c, x, T, on=1 - dawn)
    phase = T * p.get("cadence", 1.6)
    hx = p.get("x", 900)
    draw_guy(c, hx, G, run_pose(phase), 1.0, T, expr=p.get("expr", "determined"), breath=0.8, sweat=p.get("sweat", 0.3),
             hoodie=p.get("hoodie", True))
    ch = p.get("shadow")
    if ch == "chase":
        gap = 380 + 60 * math.sin(T * 0.8) - p.get("gain", 0.0) * 260 * (t / d)
        draw_guy(c, hx - gap, G, run_pose(phase + 0.5), 1.05, T, shadow=True, expr="angry")
    elif ch == "behind_far":
        k = t / d
        draw_guy(c, hx - 500 - 900 * k, G, run_pose(phase + 0.3), 1.0, T, shadow=True, expr="hurt", alpha=int(255 * (1 - k)))
    fx.snow(c, T, n=140, wind=1.4, alpha=150)
    c.restore()
    statement(c, p, t, beat, y=p.get("text_y", 230), size=p.get("text_size", 84))
    day_label(c, p, t, d)


def shot_climb(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    c.save()
    camera(c, t, d, p)
    c.drawImage(fx.hill(), 0, 0)
    k = t / d
    x0, x1 = p.get("from", 300), p.get("to", 1100)
    # progress with stalls and a push-back
    prog = ease_in_out(k)
    push_at = p.get("push_at")
    slide = 0.0
    if push_at is not None and t > push_at * beat:
        u = t - push_at * beat
        slide = 140 * math.exp(-u * 1.5) * min(1, u * 6)
    x = lerp(x0, x1, prog) - slide
    y = fx.hill_y(x)
    slope = math.degrees(math.atan2(fx.hill_y(x + 10) - fx.hill_y(x - 10), 20))
    pose = climb_pose(T * 0.9) if slide < 40 else POSES["crouch"]
    draw_guy(c, x, y, pose, 0.95, T, expr="angry", rot=slope * 0.6, breath=1.0, sweat=0.4, hoodie=p.get("hoodie", True))
    if p.get("shadow", True):
        sx = p.get("sx", 1500)
        push = push_at is not None and abs(t - push_at * beat) < 0.5
        draw_guy(c, sx, fx.hill_y(sx), POSES["push"] if push else POSES["arms_cross"], 1.05, T, shadow=True,
                 expr="smirk", flip=True, rot=slope * 0.5)
    fx.snow(c, T, n=220, wind=1.8, alpha=180)
    c.restore()
    statement(c, p, t, beat, y=p.get("text_y", 230), size=p.get("text_size", 84))
    day_label(c, p, t, d)


# ----------------------------------------------------------------------------- fights

MOVES = {
    # name: (attacker, windup pose, strike pose, beats)
    "punch": ("hero", "guard", "punch", 1.0),
    "punch2": ("hero", "guard", "punch2", 1.0),
    "kick": ("hero", "guard", "kick", 1.5),
    "uppercut": ("hero", "crouch", "uppercut", 1.5),
    "s_punch": ("shadow", "guard", "punch", 1.0),
    "s_kick": ("shadow", "guard", "kick", 1.5),
    "block": ("shadow", "guard", "punch", 1.0),     # shadow attacks, hero blocks
    "finisher": ("hero", "crouch", "punch", 2.0),
}


def fight_timeline(p, beat):
    """[(t_start, t_end, move, impact_t)] for a fight shot."""
    out = []
    tt = p.get("lead", 1.0) * beat
    for m in p["moves"]:
        b = MOVES[m][3] * beat
        out.append((tt, tt + b, m, tt + b * 0.42))
        tt += b
    return out, tt


def fight_events(p, beat):
    tl, _ = fight_timeline(p, beat)
    ev = []
    for (a, b, m, imp) in tl:
        ev.append((imp - 0.18, "whoosh", 0.5))
        if m == "block":
            ev.append((imp, "metal", 0.5))
        elif m == "finisher":
            ev += [(a, "riser", 0.4), (imp, "boom", 1.0), (imp, "punch", 1.0)]
        else:
            ev.append((imp, "punch", 0.9))
    return ev


def shot_fight(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    tl, _ = fight_timeline(p, beat)
    hero_hits = [x for x in tl if MOVES[x[2]][0] == "hero"]
    hp0, hp1 = p.get("hp", (1.0, 0.6))
    hp = hp0
    for i, (a, b, m, imp) in enumerate(hero_hits):
        if t >= imp:
            hp = lerp(hp0, hp1, (i + 1) / len(hero_hits))
    xh, xs = p.get("xh", 830), p.get("xs", 1110)
    hpose, spose = POSES["guard"], POSES["guard"]
    hdx = sdx = 0.0
    srot = 0.0
    salpha = 255
    impact = None
    sexpr, hexpr = "smirk", "determined"
    for (a, b, m, imp) in tl:
        if not (a <= t < b) and not (m == "finisher" and t >= a):
            continue
        u = (t - a) / (b - a)
        who, wind, strike, _ = MOVES[m]
        wp, sp = POSES[wind], POSES[strike]
        if u < 0.3:
            ap = blend(POSES["guard"], wp, ease_in_out(u / 0.3))
        elif u < 0.45:
            ap = blend(wp, sp, ease_out_cubic((u - 0.3) / 0.15))
        elif u < 0.75:
            ap = sp
        else:
            ap = blend(sp, POSES["guard"], ease_in_out((u - 0.75) / 0.25))
        after = t - imp
        if who == "hero":
            hpose = ap
            hdx = 60 * math.sin(math.pi * clamp(u / 0.6))
            if m == "finisher":
                hdx = 260 * ease_out_cubic(clamp(u / 0.42))
            if after >= 0:
                kb = 90 if m != "finisher" else 900
                sdx = kb * ease_out_cubic(clamp(after / 0.35)) * (1 if m == "finisher" else math.exp(-after * 2.5) + 0.2)
                spose = POSES["hit"] if after < 0.5 or m == "finisher" else blend(POSES["hit"], POSES["guard"], clamp((after - 0.5) / 0.3))
                sexpr = "hurt"
                if m == "finisher":
                    srot = 120 * ease_out_cubic(clamp(after / 0.6))
                    salpha = int(255 * (1 - clamp((after - 0.3) / 0.8)))
                impact = (after, xs + sdx * 0.2 - 40, 520)
        else:
            spose = ap
            sdx = -60 * math.sin(math.pi * clamp(u / 0.6))
            if after >= 0:
                if m == "block":
                    hpose = dict(POSES["guard"], torso=168)
                    hdx = -30 * math.exp(-after * 4)
                else:
                    hpose = POSES["hit"] if after < 0.45 else blend(POSES["hit"], POSES["guard"], clamp((after - 0.45) / 0.3))
                    hdx = -110 * ease_out_cubic(clamp(after / 0.3)) * math.exp(-after * 1.5)
                    hexpr = "angry"
                impact = (after, xh + hdx + 60, 520)
    c.save()
    if impact and impact[0] < 0.3:
        shake(c, 14 * (1 - impact[0] / 0.3), T)
    camera(c, t, d, dict(p, zoom=p.get("zoom", (1.04, 1.1))))
    env = p.get("env", "void")
    if env == "void":
        c.drawImage(fx.void(), 0, 0)
        fx.fog(c, T, y=G - 40, color="#3A1015", alpha=60)
    elif env == "street":
        c.drawImage(fx.street(), 0, 0)
    elif env == "hill":
        c.drawImage(fx.hill(slope=False), 0, 0)
    elif env == "room":
        _room_bg(c, p, T)
    elif env == "gym":
        c.drawImage(fx.gym(), 0, 0)
    draw_guy(c, xs + sdx, G, spose, 1.22, T, shadow=True, expr=sexpr, flip=True, alpha=salpha, rot=srot)
    draw_guy(c, xh + hdx, G, hpose, 1.18, T, expr=hexpr, hoodie=p.get("hoodie", env in ("street", "hill")))
    if impact:
        fx.sparks(c, impact[1], impact[2], impact[0], color=WARM, power=1.3 if salpha < 255 else 1.0)
    if p.get("snow"):
        fx.snow(c, T, n=120, wind=1.0, alpha=140)
    c.restore()
    if impact and impact[0] < 0.06:
        fx.flash(c, 0.35)
    fx.hp_bar(c, W - 560, fx.BAR + 50, 480, hp, label="LATER", color=RED)
    statement(c, p, t, beat, y=p.get("text_y", 240), size=p.get("text_size", 80))
    day_label(c, p, t, d)


def shot_kneel(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    c.save()
    camera(c, t, d, dict(p, zoom=p.get("zoom", (1.0, 1.12)), focus=(800, 700)))
    env = p.get("env", "hill")
    c.drawImage(fx.hill(slope=False) if env == "hill" else fx.void(), 0, 0)
    grow = 1.6 + 0.4 * ease_in_out(t / d)
    draw_guy(c, 1250, G + 10, POSES["arms_cross"], grow, T, shadow=True, expr="smirk", flip=True, glow=1.0)
    draw_guy(c, 760, G, POSES["kneel"], 1.0, T, expr="sad" if t < d * 0.7 else "angry", breath=0.8, hoodie=p.get("hoodie", True))
    fx.snow(c, T, n=200, wind=1.5, alpha=170)
    c.restore()
    statement(c, p, t, beat, y=p.get("text_y", 230), size=p.get("text_size", 90))
    day_label(c, p, t, d)


def shot_rise(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    k = t / d
    c.save()
    camera(c, t, d, dict(p, zoom=p.get("zoom", (1.1, 1.0)), focus=(820, 700)))
    c.drawImage(fx.hill(slope=False) if p.get("env", "hill") == "hill" else fx.void(), 0, 0)
    glow_spot(c, 760, 640, 260 + 140 * k, "#F2D492", int(140 * ease_in_out(k)))
    if k < 0.4:
        pose = blend(POSES["kneel"], POSES["crouch"], ease_in_out(k / 0.4))
    elif k < 0.75:
        pose = blend(POSES["crouch"], POSES["stand"], ease_in_out((k - 0.4) / 0.35))
    else:
        pose = blend(POSES["stand"], POSES["fists"], ease_in_out((k - 0.75) / 0.25))
    back = ease_in_out(clamp((k - 0.5) / 0.5))
    draw_guy(c, 1250 + 160 * back, G + 10, POSES["arms_cross"] if back < 0.3 else POSES["hit"], 2.0 - 0.6 * back, T,
             shadow=True, expr="smirk" if back < 0.3 else "angry", flip=True)
    draw_guy(c, 760, G, pose, 1.0, T, expr="angry", breath=1.0, hoodie=p.get("hoodie", True))
    fx.embers(c, T, n=50, color=WARM, area=(500, 300, 520, 600), alpha=int(220 * k))
    fx.snow(c, T, n=160, wind=1.2, alpha=150)
    c.restore()
    statement(c, p, t, beat, y=p.get("text_y", 230), size=p.get("text_size", 96))


PANELS = ("alarm", "read", "lift", "run", "write", "water", "walk", "plan", "sleep", "phone_down")


def _panel(c, kind, x, y, w, h, T, label):
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fill("#15171D"))
    gy = y + h - 70
    s = 0.62
    cx = x + w / 2
    if kind == "alarm":
        Th.draw(c, "alarm", cx + 90, gy - 110, 0.8, T, ring=1.0)
        draw_guy(c, cx - 60, gy, POSES["sit"], s, T, expr="tired", seat=gy - 60)
    elif kind == "read":
        j = draw_guy(c, cx, gy, dict(POSES["sit"], ua_r=60, fa_r=140, head=160), s, T, expr="neutral", seat=gy - 60)
        Th.draw(c, "books", j["hand_r"][0], j["hand_r"][1] + 10, 0.4, T)
    elif kind == "lift":
        j = draw_guy(c, cx, gy, lift_pose(T * 0.6), s, T, expr="angry", sweat=0.6)
        Th.draw(c, "barbell", (j["hand_r"][0] + j["hand_l"][0]) / 2, (j["hand_r"][1] + j["hand_l"][1]) / 2, 0.6, T)
    elif kind == "run":
        _scrolling_small = (T * 300) % w
        for i in range(3):
            lx = x + (i * w / 2 - _scrolling_small) % (w + 100) - 50
            c.drawLine(lx, gy, lx, gy - 160, stroke("#2A2D36", 6))
        draw_guy(c, cx, gy, run_pose(T * 1.6), s, T, expr="determined", breath=0.6)
    elif kind == "write":
        Th.draw(c, "desk", cx + 60, gy, 0.7, T)
        Th.draw(c, "notebook", cx + 90, gy - 120, 0.4, T, ticks=int(T * 2) % 6)
        draw_guy(c, cx - 30, gy, POSES["type"], s, T, expr="determined", seat=gy - 58)
    elif kind == "water":
        j = draw_guy(c, cx, gy, dict(POSES["stand"], ua_r=140, fa_r=200, head=196), s, T, expr="neutral")
        Th.draw(c, "mug", j["hand_r"][0], j["hand_r"][1] + 20, 0.6, T)
    elif kind == "walk":
        draw_guy(c, cx, gy, walk_pose(T), s, T, expr="happy", breath=0.5)
        Th.draw(c, "plant", x + 40, gy, 0.6, T)
    elif kind == "plan":
        Th.draw(c, "calendar", cx + 70, gy - 160, 0.6, T, marks=int(T * 3) % 20)
        draw_guy(c, cx - 50, gy, POSES["point"], s, T, expr="determined")
    elif kind == "sleep":
        Th.draw(c, "bed", cx, gy, 0.6, T)
        draw_guy(c, cx - 40, gy - 70, POSES["stand"], 0.55, T, expr="ko", rot=-90, seat=gy - 76)
        draw_text(c, "z", cx + 60 + math.sin(T * 2) * 6, gy - 150 - (T * 30) % 40, BIG, 40, color="#C8CCD4", alpha=160)
    elif kind == "phone_down":
        Th.draw(c, "desk", cx, gy, 0.7, T)
        Th.draw(c, "phone", cx + 40, gy - 112, 0.9, T, glow=0.0)
        draw_guy(c, cx - 120, gy, walk_pose(T * 0.8), s, T, expr="determined", flip=True)
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), stroke("#2E313B", 3))
    draw_text(c, label, x + w / 2, y + h - 22, UI, 26, color="#C8CCD4")


def shot_montage(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    c.clear(col("#08090C"))
    panels = p["panels"]
    n = len(panels)
    gap = 26
    pw = (W - 160 - gap * (n - 1)) / n
    ph = 600
    y = 250
    for i, (kind, label) in enumerate(panels):
        tt = t - i * p.get("every", 2) * beat
        if tt < 0:
            continue
        a = clamp(tt / 0.25)
        x = 80 + i * (pw + gap)
        c.save()
        c.translate(0, (1 - ease_out_cubic(a)) * 60)
        _panel(c, kind, x, y, pw, ph, T, label)
        c.restore()
    day_label(c, p, t, d)
    statement(c, p, t, beat, y=p.get("text_y", 200), size=p.get("text_size", 70))


def shot_dawn(c, ctx):
    t, d, T, p, beat = ctx["t"], ctx["d"], ctx["T"], ctx["p"], ctx["beat"]
    k = t / d
    dawn = round(min(1.0, 0.35 + 0.65 * ease_in_out(clamp(k * 1.4))), 2)
    c.save()
    camera(c, t, d, dict(p, zoom=p.get("zoom", (1.08, 1.0))))
    c.drawImage(fx.hill(slope=False, dawn=dawn), 0, 0)
    fade = ease_in_out(clamp(k * 1.6))
    if fade < 1:
        draw_guy(c, 600, G + 10, POSES["arms_cross"], 1.2, T, shadow=True, expr="hurt", alpha=int(255 * (1 - fade)), glow=1 - fade)
        fx.embers(c, T, n=50, color=RED, area=(480, 450, 260, 450), alpha=int(220 * (1 - fade)))
    pose = POSES[p.get("pose", "victory" if k > 0.55 else "stand")]
    draw_guy(c, 1100, G, pose, 1.0, T, expr="happy" if k > 0.55 else "determined", breath=0.4 * (1 - k),
             hoodie=p.get("hoodie", True))
    fx.snow(c, T, n=int(80 * (1 - k)), wind=0.3, alpha=120)
    c.restore()
    statement(c, p, t, beat, y=p.get("text_y", 230), size=p.get("text_size", 90))
    day_label(c, p, t, d)


SHOTS = {
    "title": shot_title, "end": shot_end, "text": shot_text, "stat": shot_stat, "room": shot_room,
    "gym": shot_gym, "run": shot_run, "climb": shot_climb, "fight": shot_fight, "kneel": shot_kneel,
    "rise": shot_rise, "montage": shot_montage, "dawn": shot_dawn,
}
