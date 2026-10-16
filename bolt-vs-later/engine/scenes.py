"""Scene templates. Every scene is drawn from (beat, local time) so videos are fully procedural."""
import math
import random

import skia

from . import props as P
from .characters import draw_bolt, draw_later
from .gfx import (INK, WHITE, blurred, circle, clamp, col, draw_text, ease_in_out, ease_out_back,
                  ease_out_cubic, fill, fit_lines, hexrgb, lerp, mix, oval, poly, pop, rrect,
                  star_path, stroke, text_width, wrap)

W, H = 1920, 1080
TITLE_FONT = "LuckiestGuy.ttf"
BODY_FONT = "Fredoka-Bold.ttf"
SEMI_FONT = "Fredoka-SemiBold.ttf"
YELLOW = "#FFD60A"
GREEN = "#2EC4B6"
RED = "#EF476F"


# ----------------------------------------------------------------------------
# backgrounds
# ----------------------------------------------------------------------------

def bg_burst(c, c1, c2, T, cx=W / 2, cy=H / 2, rays=18, speed=4.0):
    paint = fill(c1)
    paint.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), 1300,
                                                   [col(mix(c1, "#FFFFFF", 0.25)), col(c1), col(c2)],
                                                   [0.0, 0.45, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), paint)
    c.save()
    c.translate(cx, cy)
    c.rotate(T * speed)
    ray = fill("#FFFFFF", 26)
    for i in range(rays):
        a0 = math.radians(i * 360 / rays)
        a1 = math.radians(i * 360 / rays + 360 / rays / 2)
        c.drawPath(poly([(0, 0), (math.cos(a0) * 2400, math.sin(a0) * 2400),
                         (math.cos(a1) * 2400, math.sin(a1) * 2400)]), ray)
    c.restore()
    _vignette(c, 70)


def _vignette(c, strength=90):
    p = fill("#000000")
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1150,
                                               [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, strength)],
                                               [0.0, 0.6, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def bg_room(c, pal, T, dim=0.0):
    wall, floor = pal["wall"], pal["floor"]
    p = fill(wall)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 820)],
                                               [col(mix(wall, "#FFFFFF", 0.35)), col(wall)]))
    c.drawRect(skia.Rect.MakeWH(W, 820), p)
    # wallpaper dots
    dot = fill("#FFFFFF", 40)
    for i in range(0, 22):
        for j in range(0, 9):
            x = i * 92 + (46 if j % 2 else 0)
            circle(c, x, 40 + j * 92, 7, dot)
    # window
    wx, wy, ww, wh = 1500, 120, 300, 260
    rrect(c, wx - 14, wy - 14, ww + 28, wh + 28, 18, fill("#FFFFFF"))
    rrect(c, wx - 14, wy - 14, ww + 28, wh + 28, 18, stroke(INK, 6))
    sky = fill("#8ECAE6")
    sky.setShader(skia.GradientShader.MakeLinear([skia.Point(0, wy), skia.Point(0, wy + wh)],
                                                 [col(mix("#4CC9F0", "#3A0CA3", dim)), col(mix("#CAF0F8", "#7209B7", dim))]))
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), sky)
    if dim < 0.5:
        circle(c, wx + 220, wy + 70, 36, fill("#FFE45C"))
    else:
        circle(c, wx + 220, wy + 70, 32, fill("#FFF3C4"))
    cx = wx + ((T * 18) % (ww + 200)) - 100
    for (dx, dy, r) in ((0, 0, 30), (32, -12, 34), (64, 0, 28)):
        circle(c, cx + dx, wy + 160 + dy, r, fill("#FFFFFF", 230))
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(wx + ww / 2 - 5, wy, 10, wh), fill("#FFFFFF"))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy + wh / 2 - 5, ww, 10), fill("#FFFFFF"))
    # poster
    rrect(c, 110, 140, 230, 300, 12, fill(pal["accent"]))
    rrect(c, 110, 140, 230, 300, 12, stroke(INK, 6))
    b = poly([(222, 190), (175, 300), (220, 300), (198, 400), (275, 270), (228, 270), (255, 190)])
    c.drawPath(b, fill("#FFD60A"))
    c.drawPath(b, stroke(INK, 5))
    # floor
    fp = fill(floor)
    fp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 820), skia.Point(0, H)],
                                                [col(floor), col(mix(floor, "#000000", 0.18))]))
    c.drawRect(skia.Rect.MakeXYWH(0, 820, W, H - 820), fp)
    c.drawRect(skia.Rect.MakeXYWH(0, 806, W, 18), fill(mix(wall, "#FFFFFF", 0.6)))
    c.drawLine(0, 824, W, 824, stroke(INK, 5))
    if dim > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#1B0F3B", int(110 * dim)))


def bg_dark(c, T):
    p = fill("#2A1B4A")
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                               [col("#3C2470"), col("#170E2E")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    rnd = random.Random(7)
    for i in range(60):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H * 0.75)
        tw = 0.5 + 0.5 * math.sin(T * 2 + i)
        circle(c, x, y, rnd.uniform(1.5, 3.5), fill("#FFFFFF", int(60 + 140 * tw)))
    for i in range(7):
        x = (rnd.uniform(0, W) + T * (12 + i * 4)) % (W + 600) - 300
        y = rnd.uniform(650, 1050)
        oval(c, x, y, rnd.uniform(220, 380), rnd.uniform(50, 90), blurred("#8E74D0", 30, 60))
    _vignette(c, 120)


def bg_dots(c, base, T, accent=None):
    p = fill(base)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(W, H)],
                                               [col(mix(base, "#FFFFFF", 0.3)), col(base)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    off = (T * 25) % 80
    d = fill("#FFFFFF", 45)
    for i in range(-1, 26):
        for j in range(-1, 15):
            circle(c, i * 80 + off + (40 if j % 2 else 0), j * 80 + off, 6, d)
    _vignette(c, 50)


def bg_arena(c, pal, T):
    p = fill(pal["accent2"])
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 820)],
                                               [col("#FF9E6D"), col("#FFD6A5")]))
    c.drawRect(skia.Rect.MakeWH(W, 820), p)
    circle(c, 960, 640, 260, fill("#FFF3C4", 200))
    for i, (x, h, colr) in enumerate(((150, 260, "#E76F51"), (520, 330, "#F4A261"), (1300, 300, "#E76F51"), (1750, 360, "#F4A261"))):
        c.drawPath(poly([(x - 320, 820), (x, 820 - h), (x + 320, 820)]), fill(colr))
    fp = fill("#6A994E")
    fp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 820), skia.Point(0, H)],
                                                [col("#90BE6D"), col("#4F772D")]))
    c.drawRect(skia.Rect.MakeXYWH(0, 810, W, H - 810), fp)
    c.drawLine(0, 812, W, 812, stroke(INK, 5))


# ----------------------------------------------------------------------------
# UI elements
# ----------------------------------------------------------------------------

def card_height(w, title=None, sub=None, icon=None, tag=None, title_size=92):
    h = 70 + (10 if tag else 0) + (215 if icon else 0)
    if title:
        tl, ts = fit_lines(title, TITLE_FONT, title_size, w - 90, 2 if sub else 3)
        h += len(tl) * ts * 0.95 + 16
    if sub:
        sl, ss = fit_lines(sub, SEMI_FONT, 48, w - 100, 3, 30)
        h += len(sl) * ss * 1.18
    return h + 20


def card(c, cx, cy, w, h, t, title=None, sub=None, icon=None, tag=None, accent="#FF006E",
         T=0.0, title_size=92, delay=0.0, tag_color=None):
    t = t - delay
    if t < 0:
        return
    if h is None:
        h = card_height(w, title, sub, icon, tag, title_size)
    k = pop(t, 0.5)
    c.save()
    c.translate(cx, cy)
    c.scale(k, k)
    c.rotate((1 - min(1, t / 0.5)) * -6)
    rrect(c, -w / 2 + 12, -h / 2 + 16, w, h, 36, blurred("#000000", 12, 70))
    rrect(c, -w / 2, -h / 2, w, h, 36, fill("#FFFFFF"))
    rrect(c, -w / 2, -h / 2, w, h, 36, stroke(INK, 8))
    y = -h / 2 + 40
    if tag:
        tw = text_width(tag, BODY_FONT, 40) + 60
        rrect(c, -tw / 2, -h / 2 - 34, tw, 68, 34, fill(tag_color or accent))
        rrect(c, -tw / 2, -h / 2 - 34, tw, 68, 34, stroke(INK, 6))
        draw_text(c, tag, 0, -h / 2 + 14, BODY_FONT, 40, color=WHITE)
        y += 10
    if icon:
        ib = 1 + 0.04 * math.sin(T * 3)
        P.draw(c, icon, 0, y + 95, 0.82 * ib, T)
        y += 215
    if title:
        lines, size = fit_lines(title, TITLE_FONT, title_size, w - 90, 2 if sub else 3)
        for i, ln in enumerate(lines):
            y += size * 0.95
            draw_text(c, ln, 0, y, TITLE_FONT, size, color=INK)
        y += 16
    if sub:
        lines, size = fit_lines(sub, SEMI_FONT, 48, w - 100, 3, 30)
        for ln in lines:
            y += size * 1.18
            draw_text(c, ln, 0, y, SEMI_FONT, size, color="#5C677D")
    c.restore()


def pill(c, cx, cy, txt, size, bgc, fg=WHITE, t=10, pad=40, outline=True):
    k = pop(t, 0.4)
    if k <= 0:
        return
    w = text_width(txt, BODY_FONT, size) + pad * 2
    h = size * 1.6
    c.save()
    c.translate(cx, cy)
    c.scale(k, k)
    rrect(c, -w / 2, -h / 2, w, h, h / 2, fill(bgc))
    if outline:
        rrect(c, -w / 2, -h / 2, w, h, h / 2, stroke(INK, 6))
    draw_text(c, txt, 0, size * 0.36, BODY_FONT, size, color=fg)
    c.restore()


def big_title(c, lines, cx, y0, t, size=124, color=WHITE, stagger=0.18, line_gap=1.0):
    y = y0
    for i, ln in enumerate(lines):
        tt = t - i * stagger
        if tt < 0:
            y += size * line_gap
            continue
        k = ease_out_back(clamp(tt / 0.5))
        c.save()
        c.translate(cx, y)
        c.scale(k, k)
        draw_text(c, ln, 0, 0, TITLE_FONT, size, color=color, outline=INK, ow=size * 0.16,
                  shadow=(0, size * 0.09, INK, 255))
        c.restore()
        y += size * line_gap


def impact_burst(c, x, y, t, word="POW!", size=1.0):
    if t < 0 or t > 1.0:
        return
    k = ease_out_back(clamp(t / 0.25)) * (1 if t < 0.75 else 1 - (t - 0.75) / 0.25)
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(k * size, k * size)
    c.rotate(-8)
    c.drawPath(star_path(0, 0, 200, 120, 12), fill("#FFD60A"))
    c.drawPath(star_path(0, 0, 200, 120, 12), stroke(INK, 8))
    c.drawPath(star_path(0, 0, 140, 90, 12), fill("#FF7B00"))
    draw_text(c, word, 0, 30, TITLE_FONT, 92 if len(word) < 6 else 70, color=WHITE, outline=INK, ow=14)
    c.restore()


def confetti(c, T, t, n=90, seed=1):
    rnd = random.Random(seed)
    colors = ["#FF006E", "#FFD60A", "#3A86FF", "#06D6A0", "#FB5607", "#8338EC"]
    for i in range(n):
        x0 = rnd.uniform(0, W)
        sp = rnd.uniform(160, 380)
        ph = rnd.uniform(0, 3)
        y = -40 + ((t + ph) * sp) % (H + 80)
        x = x0 + math.sin(t * 2 + i) * 40
        c.save()
        c.translate(x, y)
        c.rotate((t * 200 + i * 37) % 360)
        cc = colors[i % len(colors)]
        c.drawRect(skia.Rect.MakeXYWH(-9, -5, 18, 10), fill(cc))
        c.restore()


def logo(c, x=40, y=34, s=1.0, alpha=230):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    w = text_width("BOLT vs LATER", BODY_FONT, 34) + 92
    rrect(c, 0, 0, w, 60, 30, fill(INK, int(alpha * 0.75)))
    b = poly([(34, 8), (20, 34), (32, 34), (24, 54), (48, 24), (36, 24), (44, 8)])
    c.drawPath(b, fill("#FFD60A", alpha))
    draw_text(c, "BOLT vs LATER", 64, 42, BODY_FONT, 34, color=WHITE, align="left", alpha=alpha)
    c.restore()


def captions(c, chunks, T):
    """chunks: list of (start, end, [(word, emph)])."""
    for (s, e, words) in chunks:
        if s <= T < e:
            t = T - s
            k = 0.85 + 0.15 * ease_out_back(clamp(t / 0.18))
            size = 58
            lines = []
            cur, curw = [], 0
            space = text_width(" ", BODY_FONT, size)
            for (wd, em) in words:
                ww = text_width(wd, BODY_FONT, size)
                if cur and curw + space + ww > 1500:
                    lines.append((cur, curw))
                    cur, curw = [], 0
                cur.append((wd, em, ww))
                curw += (space if len(cur) > 1 else 0) + ww
            if cur:
                lines.append((cur, curw))
            y0 = 1010 - (len(lines) - 1) * 70
            c.save()
            c.translate(W / 2, y0)
            c.scale(k, k)
            for li, (ln, lw) in enumerate(lines):
                x = -lw / 2
                y = li * 70
                for (wd, em, ww) in ln:
                    draw_text(c, wd, x, y, BODY_FONT, size, color=YELLOW if em else WHITE,
                              outline=INK, ow=13, align="left")
                    x += ww + space
            c.restore()
            return


def wipe(c, p, colr):
    """Diagonal band wipe. p in [0,1]; covers screen fully at p=0.5."""
    if p <= 0 or p >= 1:
        return
    x = lerp(-2 * W - 400, W + 400, ease_in_out(p))
    band = poly([(x, 0), (x + 2 * W, 0), (x + 2 * W - 400, H), (x - 400, H)])
    c.drawPath(band, fill(colr))
    c.drawPath(poly([(x + 2 * W, 0), (x + 2 * W + 60, 0), (x + 2 * W - 340, H), (x + 2 * W - 400, H)]), fill("#FFD60A"))
    c.drawPath(poly([(x - 60, 0), (x, 0), (x - 400, H), (x - 460, H)]), fill(INK))


# ----------------------------------------------------------------------------
# Scene renderers.  ctx: dict(t, T, dur, beat, pal, bm (bolt mouth), lm (later mouth), st (scene time))
# ----------------------------------------------------------------------------

def _bolt_talk_pose(ctx, default="point"):
    b = ctx["beat"]
    return b.get("pose", default)


def scene_title(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["st"], ctx["T"]
    bg_burst(c, pal["accent"], mix(pal["accent"], "#000000", 0.45), T)
    pill(c, W / 2, 110, f"EPISODE {ctx['ep']['num']}", 46, INK, t=t - 0.1)
    lines = ctx["ep"]["title_lines"]
    big_title(c, lines, W / 2, 290, t - 0.25, size=ctx["ep"].get("title_size", 128))
    if ctx["ep"].get("subtitle"):
        st = t - 0.25 - len(lines) * 0.18 - 0.1
        if st > 0:
            k = ease_out_back(clamp(st / 0.4))
            c.save()
            c.translate(W / 2, 290 + len(lines) * 128 + 10)
            c.scale(k, k)
            draw_text(c, ctx["ep"]["subtitle"], 0, 0, BODY_FONT, 64, color=YELLOW, outline=INK, ow=12)
            c.restore()
    jump_in = (1 - ease_out_back(clamp((t - 0.6) / 0.6))) * 700
    hop = abs(math.sin(t * 3.2)) * 30 if t > 1.2 else 0
    draw_bolt(c, 600, 790 + jump_in, 1.0, T, mood=b.get("mood", "excited"), pose=b.get("pose", "wave"),
              mouth=ctx["bm"], jump=hop, look=(0.2, 0.1))
    lx = 1350 + (1 - ease_out_cubic(clamp((t - 1.0) / 0.8))) * 800
    draw_later(c, lx, 760, 0.85, T, mood=b.get("later_mood", "smug"), mouth=ctx["lm"], look=(-0.8, 0.2))


def scene_talk(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    bg_room(c, pal, T)
    has_card = b.get("card") or b.get("icon")
    if has_card:
        pose = _bolt_talk_pose(ctx, "point")
        draw_bolt(c, 470, 640, 1.22, T, mood=b.get("mood", "happy"), pose=pose, mouth=ctx["bm"],
                  look=(0.55, 0.05), hold=b.get("hold"))
        card(c, 1260, 440, b.get("card_w", 860), b.get("card_h"), t, title=b.get("card"),
             sub=b.get("sub"), icon=b.get("icon"), tag=b.get("tag"), accent=pal["accent"], T=T,
             title_size=b.get("title_size", 92))
    else:
        pose = b.get("pose", "wave" if int(ctx["st"] / 3) % 2 == 0 else "hips")
        draw_bolt(c, 960, 620, 1.45, T, mood=b.get("mood", "happy"), pose=pose, mouth=ctx["bm"],
                  look=(0.0, 0.1), hold=b.get("hold"))
    if b.get("later_peek"):
        draw_later(c, 1780, 330, 0.55, T, mood="smug", mouth=ctx["lm"], look=(-0.8, 0.3))


def scene_later(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    bg_dark(c, T)
    st = ctx["st"]
    enter = (1 - ease_out_cubic(clamp(st / 0.8))) * 900
    draw_later(c, 1230 + enter, 470, 1.4, T, mood=b.get("later_mood", "smug"), mouth=ctx["lm"],
               look=(-0.8, 0.3), hold=b.get("later_hold"))
    shake = math.sin(T * 40) * 2 if b.get("bolt_mood", "scared") == "scared" else 0
    draw_bolt(c, 420 + shake, 690, 0.95, T, mood=b.get("bolt_mood", "scared"), pose=b.get("pose", "scared"),
              mouth=ctx["bm"], look=(0.7, -0.2))
    if b.get("card"):
        k = pop(t, 0.45)
        c.save()
        c.translate(W / 2, 120)
        c.scale(k, k)
        lines, size = fit_lines(b["card"], TITLE_FONT, 84, 1600, 1)
        draw_text(c, lines[0], 0, 30, TITLE_FONT, size, color="#E0D4FF", outline=INK, ow=14,
                  shadow=(0, 8, INK, 255))
        c.restore()


def scene_struggle(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    bg_room(c, pal, T, dim=b.get("dim", 0.55))
    P.draw(c, "clock", 1100, 250, 0.7, T, speed=b.get("clock_speed", 80))
    seat = b.get("seat", "sofa")
    if seat == "sofa":
        P.draw(c, "sofa", 640, 760, 1.3, T)
        draw_bolt(c, 640, 640, 1.0, T, mood=b.get("mood", "tired"), pose=b.get("pose", "hold"),
                  mouth=ctx["bm"], look=(0.4, 0.4), hold=b.get("hold", "phone"))
    elif seat == "bed":
        P.draw(c, "bed", 640, 760, 1.3, T)
        draw_bolt(c, 640, 630, 1.0, T, mood=b.get("mood", "tired"), pose=b.get("pose", "hold"),
                  mouth=ctx["bm"], look=(0.4, 0.4), hold=b.get("hold", "phone"), rot=-8)
    else:  # desk
        draw_bolt(c, 640, 600, 1.05, T, mood=b.get("mood", "tired"), pose=b.get("pose", "think"),
                  mouth=ctx["bm"], look=(0.3, 0.5), hold=b.get("hold"))
        rrect(c, 260, 700, 760, 50, 10, fill("#8D5A3B"))
        rrect(c, 260, 700, 760, 50, 10, stroke(INK, 6))
        for lx in (300, 960):
            rrect(c, lx, 745, 30, 140, 6, fill("#6B4226"))
            rrect(c, lx, 745, 30, 140, 6, stroke(INK, 5))
        P.draw(c, b.get("desk_prop", "laptop"), 760, 630, 0.75, T)
    draw_later(c, 1380, 440, 1.0, T, mood=b.get("later_mood", "smug"), mouth=ctx["lm"],
               look=(-0.8, 0.4), hold=b.get("later_hold"))
    if b.get("thought"):
        k = pop(t - 0.3, 0.4)
        if k > 0:
            c.save()
            c.translate(560, 230)
            c.scale(k, k)
            for (dx, dy, r) in ((40, 170, 14), (20, 130, 22)):
                circle(c, dx, dy, r, fill(WHITE))
                circle(c, dx, dy, r, stroke(INK, 5))
            lines, size = fit_lines(b["thought"], BODY_FONT, 52, 560, 2)
            bw = max(text_width(l, BODY_FONT, size) for l in lines) + 100
            bh = len(lines) * size * 1.25 + 60
            rrect(c, -bw / 2, -bh / 2, bw, bh, bh / 2.2, fill(WHITE))
            rrect(c, -bw / 2, -bh / 2, bw, bh, bh / 2.2, stroke(INK, 6))
            for i, ln in enumerate(lines):
                draw_text(c, ln, 0, -bh / 2 + 30 + size + i * size * 1.25 - 6, BODY_FONT, size, color=INK)
            c.restore()


def scene_stat(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    bg_burst(c, pal["accent2"], mix(pal["accent2"], "#000000", 0.5), T, cx=1150, cy=450)
    num = b["num"]
    p = ease_out_cubic(clamp((t - 0.2) / 1.3))
    val = num * p
    if isinstance(num, float) and not float(num).is_integer():
        s = f"{val:.1f}"
    else:
        s = f"{int(round(val)):,}"
    s = b.get("prefix", "") + s + b.get("suffix", "")
    k = pop(t, 0.5)
    c.save()
    c.translate(1170, 470)
    c.scale(k, k)
    size = b.get("num_size", 250)
    draw_text(c, s, 0, 0, TITLE_FONT, size, color=YELLOW, outline=INK, ow=24, shadow=(0, 16, INK, 255))
    lines, ls = fit_lines(b.get("label", ""), BODY_FONT, 66, 1150, 2)
    for i, ln in enumerate(lines):
        draw_text(c, ln, 0, 100 + i * ls * 1.15, BODY_FONT, ls, color=WHITE, outline=INK, ow=12)
    if b.get("source"):
        draw_text(c, b["source"], 0, 100 + len(lines) * ls * 1.15 + 20, SEMI_FONT, 32, color="#FFFFFF",
                  alpha=220)
    c.restore()
    draw_bolt(c, 330, 660, 1.0, T, mood=b.get("mood", "scared"), pose=b.get("pose", "shrug"),
              mouth=ctx["bm"], look=(0.6, -0.3))


def scene_compare(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    bg_dots(c, pal["bg"], T)
    lt, lb = b["left"]
    rt, rb = b["right"]
    right_at = b.get("right_at", min(ctx["dur"] * 0.45, 3.0))
    ch = max(card_height(800, lt, lb, b.get("licon"), "X", 80), card_height(800, rt, rb, b.get("ricon"), "X", 80)) + 30
    for (cx, title, body, tag, colr, delay, icon_ok) in ((500, lt, lb, b.get("ltag", "LORD LATER SAYS"), "#7B5EA7", 0.0, False),
                                                         (1420, rt, rb, b.get("rtag", "BOLT SAYS"), GREEN, right_at, True)):
        tt = t - delay
        if tt < 0:
            continue
        card(c, cx, 440, 800, ch, tt, title=title, sub=body, tag=tag, accent=colr, T=T, title_size=80,
             icon=b.get("licon" if not icon_ok else "ricon"))
        k = pop(tt - 0.25, 0.4)
        if k > 0:
            c.save()
            c.translate(cx + 360, 440 - ch / 2 + 10)
            c.scale(k, k)
            circle(c, 0, 0, 56, fill(GREEN if icon_ok else RED))
            circle(c, 0, 0, 56, stroke(INK, 7))
            pth = skia.Path()
            if icon_ok:
                pth.moveTo(-24, 2)
                pth.lineTo(-6, 22)
                pth.lineTo(26, -18)
            else:
                pth.moveTo(-20, -20)
                pth.lineTo(20, 20)
                pth.moveTo(20, -20)
                pth.lineTo(-20, 20)
            c.drawPath(pth, stroke(WHITE, 12))
            c.restore()
    draw_later(c, 110, 885, 0.48, T, mood="smug" if t < right_at else "angry", mouth=ctx["lm"], look=(0.5, 0), zzz=False)
    if t >= right_at:
        draw_bolt(c, 1810, 860, 0.55, T, mood="happy", pose="pointup", mouth=ctx["bm"], look=(-0.5, -0.4), flip=True)


def scene_fight(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    hit_t = b.get("hit_t", 1.1)
    # screen shake
    if hit_t <= t < hit_t + 0.35:
        amt = (1 - (t - hit_t) / 0.35) * 16
        c.translate(math.sin(t * 90) * amt, math.cos(t * 77) * amt)
    bg_arena(c, pal, T)
    hp0, hp1 = b["hp_prev"], b["hp"]
    hp = hp0 if t < hit_t else lerp(hp0, hp1, ease_out_cubic(clamp((t - hit_t) / 0.6)))
    ls = 0.7 + 0.5 * hp
    hurt = hit_t <= t < hit_t + 1.4
    lmood = "shocked" if hurt else b.get("later_mood", "angry")
    knock = 0
    if t >= hit_t:
        knock = math.exp(-(t - hit_t) * 5) * 120
    draw_later(c, 1460 + knock, 450, ls, T, mood=lmood, mouth=ctx["lm"], look=(-0.8, 0.2),
               rot=(knock / 6) if t >= hit_t else None)
    throw = (hit_t - 0.55) <= t < hit_t
    pose = "fist" if t >= hit_t - 0.55 else b.get("pose", "flex")
    draw_bolt(c, 420, 650, 1.15, T, mood=b.get("mood", "determined"), pose=pose, mouth=ctx["bm"],
              look=(0.8, -0.1), jump=(abs(math.sin(t * 6)) * 14 if t < hit_t - 0.55 else 0))
    if throw:
        p = (t - (hit_t - 0.55)) / 0.55
        x = lerp(660, 1400, p)
        y = lerp(560, 440, p) - math.sin(p * math.pi) * 200
        P.draw(c, b["weapon"], x, y, 0.7, T, rot=p * 540)
    elif t < hit_t - 0.55:
        P.draw(c, b["weapon"], 660, 540 + math.sin(T * 5) * 6, 0.6, T)
    impact_burst(c, 1380, 430, t - hit_t, b.get("hit", "POW!"))
    # HP bar
    bx, by, bw = 1180, 110, 640
    draw_text(c, "LORD LATER", bx, by + 4, TITLE_FONT, 44, color=WHITE, outline=INK, ow=10, align="left")
    rrect(c, bx, by + 22, bw, 46, 23, fill(INK))
    rrect(c, bx + 6, by + 28, (bw - 12) * max(0.02, hp), 34, 17, fill("#B4A0E5" if hp > 0.35 else RED))
    rrect(c, bx, by + 22, bw, 46, 23, stroke(INK, 6))
    # weapon tag
    k = pop(t, 0.45)
    c.save()
    c.translate(430, 210)
    c.scale(k, k)
    pill(c, 0, -50, b.get("tag", "WEAPON"), 40, pal["accent"], t=10)
    lines, size = fit_lines(b.get("name", ""), TITLE_FONT, 78, 700, 2)
    for i, ln in enumerate(lines):
        draw_text(c, ln, 0, 50 + i * size, TITLE_FONT, size, color=WHITE, outline=INK, ow=14,
                  shadow=(0, 8, INK, 255))
    c.restore()


def scene_win(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    bg_burst(c, "#FFB703", "#FB8500", T, speed=8)
    confetti(c, T, ctx["st"])
    prop = b.get("prop", "trophy")
    if prop:
        k = pop(t - 0.3, 0.5)
        if k > 0:
            circle(c, 1450, 500, 230 * k, fill("#FFFFFF", 90))
            P.draw(c, prop, 1450, 500, 1.4 * k, T, **b.get("prop_kw", {}))
    hop = abs(math.sin(ctx["st"] * 4)) * 60
    draw_bolt(c, 720, 600, 1.3, T, mood=b.get("mood", "excited"), pose=b.get("pose", "cheer"),
              mouth=ctx["bm"], jump=hop, squash=-0.05 if hop < 8 else 0.03, look=(0.2, -0.2))
    if b.get("card"):
        big_title(c, [b["card"]], W / 2, 170, t, size=b.get("title_size", 110), color=WHITE, stagger=0)
    if b.get("show_later", True):
        draw_later(c, 1780, 900, 0.32, T, mood="defeated", look=(0, 0), zzz=False)


def scene_list(c, ctx):
    b, pal, t, T = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"]
    bg_dots(c, pal["bg"], T)
    pill(c, 1150, 110, b.get("title", "RECAP"), 52, pal["accent"], t=t)
    items = b["items"]
    n = len(items)
    span = max(0.6, (ctx["dur"] - 1.0)) / n
    for i, it in enumerate(items):
        tt = t - 0.3 - i * span
        if tt < 0:
            continue
        k = ease_out_back(clamp(tt / 0.4))
        y = 250 + i * (560 / max(n, 1)) + 40
        c.save()
        c.translate(760, y)
        c.scale(k, k)
        rrect(c, 0, -62, 1060, 124, 30, fill(WHITE))
        rrect(c, 0, -62, 1060, 124, 30, stroke(INK, 6))
        circle(c, 70, 0, 38, fill(GREEN))
        circle(c, 70, 0, 38, stroke(INK, 6))
        pth = skia.Path()
        pth.moveTo(52, 2)
        pth.lineTo(66, 18)
        pth.lineTo(90, -14)
        c.drawPath(pth, stroke(WHITE, 10))
        lines, size = fit_lines(it, BODY_FONT, 54, 900, 1, 30)
        draw_text(c, lines[0], 135, 19, BODY_FONT, size, color=INK, align="left")
        c.restore()
    draw_bolt(c, 330, 640, 1.05, T, mood=b.get("mood", "happy"), pose=b.get("pose", "point"),
              mouth=ctx["bm"], look=(0.7, 0))


def scene_outro(c, ctx):
    b, pal, t, T, ep = ctx["beat"], ctx["pal"], ctx["t"], ctx["T"], ctx["ep"]
    st = ctx["st"]
    bg_burst(c, pal["accent"], mix(pal["accent"], "#000000", 0.5), T)
    draw_bolt(c, 430, 640, 1.2, T, mood="happy", pose="wave", mouth=ctx["bm"], look=(0.3, 0.1))
    card(c, 1250, 300, 980, 360, st, title=b.get("mission", ""), tag="YOUR MISSION", accent=GREEN,
         T=T, title_size=70)
    # subscribe button
    k = pop(st - 1.0, 0.45)
    if k > 0:
        subbed = st > 3.2
        press = 0.92 if 3.0 < st < 3.25 else 1.0
        pulse = 1 + 0.03 * math.sin(T * 6) if not subbed else 1
        c.save()
        c.translate(1100, 620)
        c.scale(k * press * pulse, k * press * pulse)
        rrect(c, -230, -62, 460, 124, 24, fill("#909090" if subbed else "#FF0033"))
        rrect(c, -230, -62, 460, 124, 24, stroke(INK, 7))
        draw_text(c, "SUBSCRIBED" if subbed else "SUBSCRIBE", 0, 20, TITLE_FONT, 60, color=WHITE)
        c.restore()
        # bell
        c.save()
        c.translate(1440, 620)
        c.scale(k, k)
        c.rotate(math.sin(T * 14) * 15 if st > 3.4 else 0)
        bell = skia.Path()
        bell.moveTo(-40, 30)
        bell.quadTo(-40, -50, 0, -50)
        bell.quadTo(40, -50, 40, 30)
        bell.lineTo(52, 42)
        bell.lineTo(-52, 42)
        bell.close()
        c.drawPath(bell, fill("#FFD60A"))
        c.drawPath(bell, stroke(INK, 7))
        circle(c, 0, 52, 12, fill(INK))
        c.restore()
        # cursor
        if 2.0 < st < 4.2:
            cp = ease_in_out(clamp((st - 2.0) / 1.0))
            cx, cy = lerp(1500, 1120, cp), lerp(900, 640, cp)
            cur = poly([(0, 0), (0, 60), (16, 46), (28, 74), (40, 68), (28, 42), (48, 42)])
            c.save()
            c.translate(cx, cy)
            c.drawPath(cur, fill(WHITE))
            c.drawPath(cur, stroke(INK, 5))
            c.restore()
    if b.get("next"):
        k2 = pop(st - 1.6, 0.45)
        if k2 > 0:
            c.save()
            c.translate(1250, 800)
            c.scale(k2, k2)
            txt = "NEXT: " + b["next"]
            lines, size = fit_lines(txt, BODY_FONT, 46, 960, 1, 26)
            w = text_width(lines[0], BODY_FONT, size) + 80
            rrect(c, -w / 2, -40, w, 80, 40, fill(INK))
            draw_text(c, lines[0], 0, size * 0.36, BODY_FONT, size, color=YELLOW)
            c.restore()


SCENES = {
    "title": scene_title, "talk": scene_talk, "later": scene_later, "struggle": scene_struggle,
    "stat": scene_stat, "compare": scene_compare, "fight": scene_fight, "win": scene_win,
    "list": scene_list, "outro": scene_outro,
}
