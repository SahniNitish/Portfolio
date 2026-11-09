"""Hand-written SVG art for the KazChart scene (flat silhouettes, no outlines). Each function returns a markup string for an {"type": "svg"} element.
World size is 1920x1080. Colours are dark so the shapes read against a glow, a sun or a fire behind them."""
import math

DARK = "#07090a"


def _f(v):
    return f"{v:.1f}"


def fig(x, y, h=300, pose="stand", col=DARK, flip=False, extra=""):
    """Silhouette person standing with feet at (x, y). pose: stand, up, carry, sit, dance, point, hunch, hold."""
    s = -1 if flip else 1
    r = 0.095 * h
    hip, sh, hc = (0, -0.47 * h), (0, -0.80 * h), (0, -0.90 * h)
    leg_w, arm_w, tor_w = 0.075 * h, 0.06 * h, 0.14 * h
    legs = {"stand": [(-0.07, 0), (0.07, 0)], "dance": [(-0.2, 0), (0.18, -0.02)], "sit": [(-0.3, -0.04), (0.28, -0.04)], "hunch": [(-0.08, 0), (0.08, 0)]}.get(pose, [(-0.07, 0), (0.07, 0)])
    arms = {"stand": [(-0.14, -0.50), (0.14, -0.50)], "up": [(-0.22, -1.05), (0.22, -1.05)], "carry": [(-0.1, -0.55), (0.12, -0.98)], "sit": [(-0.18, -0.40), (0.2, -0.38)],
            "dance": [(-0.3, -1.02), (0.3, -0.95)], "point": [(-0.14, -0.50), (0.42, -0.84)], "hunch": [(-0.12, -0.38), (0.12, -0.38)], "hold": [(-0.32, -0.56), (0.32, -0.56)]}.get(pose, [(-0.14, -0.5), (0.14, -0.5)])
    if pose == "hunch":
        hc = (0.06 * h, -0.84 * h); sh = (0.03 * h, -0.76 * h)
    g = f'<g transform="translate({_f(x)} {_f(y)}) scale({s} 1)" fill="{col}" stroke="{col}" stroke-linecap="round" stroke-linejoin="round">'
    for lx, ly in legs:
        g += f'<line x1="{_f(hip[0])}" y1="{_f(hip[1])}" x2="{_f(lx * h)}" y2="{_f(ly * h)}" stroke-width="{_f(leg_w)}"/>'
    g += f'<line x1="{_f(hip[0])}" y1="{_f(hip[1])}" x2="{_f(sh[0])}" y2="{_f(sh[1])}" stroke-width="{_f(tor_w)}"/>'
    for ax, ay in arms:
        g += f'<line x1="{_f(sh[0])}" y1="{_f(sh[1] + 0.02 * h)}" x2="{_f(ax * h)}" y2="{_f(ay * h)}" stroke-width="{_f(arm_w)}"/>'
    g += f'<circle cx="{_f(hc[0])}" cy="{_f(hc[1])}" r="{_f(r)}" stroke="none"/>{extra}</g>'
    return g


def headdress(x, y, h, col="#2a1608"):
    """feathers above a standing figure's head (use with fig at same x,y,h)."""
    top = y - 0.99 * h
    s = ""
    for k in range(-3, 4):
        s += f'<path d="M{_f(x + k * 0.03 * h)},{_f(top)} L{_f(x + k * 0.07 * h)},{_f(top - 0.2 * h)} L{_f(x + k * 0.03 * h + 0.025 * h)},{_f(top)} Z" fill="{col}"/>'
    return s


def sun(x, y, r, col="#ffcf7a"):
    return (f'<defs><radialGradient id="wsun"><stop offset="0" stop-color="#fff3d0" stop-opacity="1"/><stop offset=".35" stop-color="{col}" stop-opacity=".85"/>'
            f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient></defs><circle cx="{x}" cy="{y}" r="{r}" fill="url(#wsun)"/>')


def glow(x, y, r, col="#ff9a3c", op=0.9, gid="wglow"):
    return (f'<defs><radialGradient id="{gid}"><stop offset="0" stop-color="{col}" stop-opacity="{op}"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#{gid})"/>')


def hills(y, col, amp=60, seed=1):
    pts = []
    for i in range(0, 9):
        pts.append((i * 300 - 200, y + amp * math.sin(i * 1.3 + seed) * 0.8))
    d = f"M-200,{y + 400} L" + " L".join(f"{_f(px)},{_f(py)}" for px, py in pts) + f" L2200,{y + 400} Z"
    return f'<path d="{d}" fill="{col}"/>'


def ground(y, col):
    return f'<rect x="-400" y="{y}" width="2800" height="900" fill="{col}"/>'


def acacia(x, y, s=1.0, col=DARK):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{col}"><path d="M-8,0 C-6,-90 -20,-150 -60,-200 L-40,-205 C-15,-175 0,-160 10,-150 C20,-165 40,-190 70,-205 L90,-198 C45,-160 18,-110 14,0 Z"/>'
            f'<ellipse cx="0" cy="-215" rx="170" ry="38"/><ellipse cx="-70" cy="-195" rx="90" ry="22"/><ellipse cx="85" cy="-200" rx="95" ry="24"/></g>')


def tall_tree(x, y, s=1.0, col=DARK):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{col}"><rect x="-14" y="-620" width="28" height="620"/><ellipse cx="0" cy="-640" rx="150" ry="120"/>'
            f'<ellipse cx="-90" cy="-560" rx="110" ry="80"/><ellipse cx="95" cy="-570" rx="115" ry="85"/><ellipse cx="0" cy="-500" rx="130" ry="70"/></g>')


def antelope(x, y, s=1.0, col=DARK, flip=False):
    sx = -s if flip else s
    return (f'<g transform="translate({x} {y}) scale({sx} {s})" fill="{col}" stroke="{col}" stroke-linecap="round"><ellipse cx="0" cy="-130" rx="95" ry="42" stroke="none"/>'
            f'<path d="M70,-150 L120,-215 L138,-208 L96,-135 Z" stroke="none"/><ellipse cx="140" cy="-218" rx="30" ry="18" stroke="none" transform="rotate(-20 140 -218)"/>'
            f'<line x1="132" y1="-232" x2="118" y2="-300" stroke-width="7"/><line x1="146" y1="-232" x2="168" y2="-296" stroke-width="7"/>'
            f'<line x1="-60" y1="-110" x2="-72" y2="0" stroke-width="12"/><line x1="-30" y1="-108" x2="-30" y2="0" stroke-width="12"/><line x1="40" y1="-108" x2="48" y2="0" stroke-width="12"/><line x1="70" y1="-112" x2="92" y2="0" stroke-width="12"/>'
            f'<path d="M-92,-140 Q-130,-130 -128,-100" fill="none" stroke-width="9"/></g>')


def fire(x, y, s=1.0):
    return (glow(x, y - 60 * s, 330 * s, "#ff8a2a", .85, "wfire") +
            f'<g transform="translate({x} {y}) scale({s})"><path d="M-70,0 C-90,-60 -30,-90 -40,-150 C-10,-110 10,-130 0,-190 C40,-140 90,-90 70,0 Z" fill="#ff7a1a"/>'
            f'<path d="M-42,0 C-55,-40 -18,-60 -22,-100 C0,-70 18,-80 8,-120 C30,-85 55,-50 44,0 Z" fill="#ffc24a"/><path d="M-18,0 C-24,-22 -4,-34 0,-56 C12,-34 24,-20 18,0 Z" fill="#fff0b0"/>'
            f'<line x1="-90" y1="6" x2="80" y2="-6" stroke="#2a1608" stroke-width="14" stroke-linecap="round"/><line x1="-80" y1="-6" x2="90" y2="6" stroke="#2a1608" stroke-width="14" stroke-linecap="round"/></g>')


def hut(x, y, w=170, col=DARK):
    return f'<g transform="translate({x} {y})" fill="{col}"><path d="M{-w / 2},0 L{-w / 2 + 10},{-w * 0.45} L0,{-w * 0.85} L{w / 2 - 10},{-w * 0.45} L{w / 2},0 Z"/><rect x="{-w * 0.09}" y="{-w * 0.3}" width="{w * 0.18}" height="{w * 0.3}" fill="#000" opacity=".5"/></g>'


def handprint(x, y, s=1.0, col="#c46a3a", rot=0):
    return (f'<g transform="translate({x} {y}) rotate({rot}) scale({s})" fill="{col}" opacity=".92"><ellipse cx="0" cy="0" rx="52" ry="62"/>'
            + "".join(f'<ellipse cx="{dx}" cy="{dy}" rx="14" ry="{ry}" transform="rotate({a} {dx} {dy})"/>' for dx, dy, ry, a in [(-48, -64, 44, -22), (-22, -92, 50, -8), (6, -98, 54, 0), (34, -88, 48, 10), (62, -42, 40, 52)]) + '</g>')


def bison(x, y, s=1.0, col="#7a3b1c"):
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{col}"><path d="M-170,-60 C-140,-170 -40,-190 20,-150 C70,-190 150,-160 168,-92 L196,-76 L170,-60 L150,-20 L150,62 L122,62 L116,-6 L40,2 L36,62 L8,62 L2,-4 L-90,6 L-100,62 L-128,62 L-130,-6 L-160,-8 Z"/>'
            f'<path d="M170,-96 L206,-132 L198,-84 Z"/></g>')


def flute(x, y, s=1.0, col="#e8dcc0"):
    holes = "".join(f'<circle cx="{-110 + i * 48}" cy="0" r="8" fill="#2a2018"/>' for i in range(5))
    return f'<g transform="translate({x} {y}) rotate(-12) scale({s})"><rect x="-150" y="-17" width="300" height="34" rx="17" fill="{col}"/>{holes}</g>'


def malimo(x, y, s=1.0, col="#4a2b14"):
    return (f'<g transform="translate({x} {y}) rotate(-28) scale({s})" fill="{col}"><path d="M-260,-16 L120,-26 L250,-70 L250,70 L120,26 L-260,16 Z"/>'
            f'<ellipse cx="250" cy="0" rx="26" ry="70" fill="#1f1108"/><rect x="-100" y="-30" width="16" height="60" fill="#8a6a3a"/><rect x="40" y="-34" width="16" height="68" fill="#8a6a3a"/></g>')


def waves(x, y, n=4, col="#ffb85c", s=1.0):
    return "".join(f'<path d="M{x + k * 60 * s},{y - 70 * s} Q{x + k * 60 * s + 40 * s},{y} {x + k * 60 * s},{y + 70 * s}" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round" opacity="{0.9 - 0.18 * k}"/>' for k in range(n))


def phone(x, y, s=1.0, screen="#6ec6ff", col="#0c1117"):
    return (f'<g transform="translate({x} {y}) scale({s})"><rect x="-120" y="-230" width="240" height="460" rx="34" fill="{col}" stroke="#3a4550" stroke-width="6"/>'
            f'<rect x="-100" y="-205" width="200" height="410" rx="16" fill="{screen}" opacity=".9"/><rect x="-36" y="-218" width="72" height="10" rx="5" fill="#222"/></g>')


def alarm_clock(x, y, s=1.0):
    return (f'<g transform="translate({x} {y}) scale({s})"><circle cx="-80" cy="-120" r="44" fill="#b72a2a"/><circle cx="80" cy="-120" r="44" fill="#b72a2a"/><circle r="120" fill="#d94040"/><circle r="96" fill="#f3efe6"/>'
            f'<line x1="0" y1="0" x2="0" y2="-66" stroke="#222" stroke-width="9" stroke-linecap="round"/><line x1="0" y1="0" x2="50" y2="22" stroke="#222" stroke-width="9" stroke-linecap="round"/>'
            f'<line x1="-60" y1="116" x2="-80" y2="150" stroke="#8a1c1c" stroke-width="12" stroke-linecap="round"/><line x1="60" y1="116" x2="80" y2="150" stroke="#8a1c1c" stroke-width="12" stroke-linecap="round"/></g>')


def crown(x, y, s=1.0, col="#e8b838"):
    return f'<g transform="translate({x} {y}) scale({s})" fill="{col}"><path d="M-90,0 L-100,-90 L-45,-45 L0,-110 L45,-45 L100,-90 L90,0 Z"/><rect x="-92" y="6" width="184" height="22" rx="4"/></g>'


def money_bag(x, y, s=1.0):
    return (f'<g transform="translate({x} {y}) scale({s})"><path d="M-70,0 C-110,-60 -50,-110 -30,-130 L30,-130 C50,-110 110,-60 70,0 Z" fill="#6a8a3a"/><rect x="-40" y="-150" width="80" height="24" rx="8" fill="#4a6a28"/>'
            f'<text x="0" y="-36" font-family="Poppins" font-weight="800" font-size="86" text-anchor="middle" fill="#e8f0c8">$</text></g>')


def office_window(x, y, s=1.0):
    return f'<g transform="translate({x} {y}) scale({s})"><rect x="-130" y="-170" width="260" height="340" fill="#16232f" stroke="#7a8c9c" stroke-width="8"/><line x1="0" y1="-170" x2="0" y2="170" stroke="#7a8c9c" stroke-width="6"/><line x1="-130" y1="0" x2="130" y2="0" stroke="#7a8c9c" stroke-width="6"/><circle cx="60" cy="-80" r="26" fill="#ffd27a" opacity=".8"/></g>'


def pyramid(x, y, w=520, h=420, col="#394a58"):
    rows = 5
    s = ""
    for i in range(rows):
        yy = y - h + i * h / rows
        half = (i + 1) * w / rows / 2
        s += f'<rect x="{_f(x - half)}" y="{_f(yy)}" width="{_f(half * 2 - 8)}" height="{_f(h / rows - 8)}" fill="{col}" opacity="{0.55 + 0.1 * i}"/>'
    return s


def skull_crack(x, y, s=1.0):
    return (f'<g transform="translate({x} {y}) scale({s})"><ellipse cx="0" cy="-20" rx="120" ry="110" fill="#e8e2d0"/><rect x="-60" y="60" width="120" height="70" rx="14" fill="#e8e2d0"/>'
            f'<ellipse cx="-44" cy="-14" rx="26" ry="32" fill="#1a1612"/><ellipse cx="44" cy="-14" rx="26" ry="32" fill="#1a1612"/><path d="M0,28 L-12,56 L12,56 Z" fill="#1a1612"/>'
            f'<path d="M20,-128 L8,-90 L30,-64 L6,-30" fill="none" stroke="#b02a2a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></g>')


def spear(x, y, s=1.0, rot=-30):
    return f'<g transform="translate({x} {y}) rotate({rot}) scale({s})"><line x1="-260" y1="0" x2="240" y2="0" stroke="#5a3a1c" stroke-width="12" stroke-linecap="round"/><path d="M240,-26 L330,0 L240,26 Z" fill="#9aa4ac"/></g>'


def orb(x, y, r=110, col="#fff0b0", rays=14):
    s = glow(x, y, r * 3, col, .6, "worb")
    s += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>'
    for k in range(rays):
        a = k / rays * math.tau
        s += f'<line x1="{_f(x + math.cos(a) * r * 1.3)}" y1="{_f(y + math.sin(a) * r * 1.3)}" x2="{_f(x + math.cos(a) * r * 2.0)}" y2="{_f(y + math.sin(a) * r * 2.0)}" stroke="{col}" stroke-width="5" opacity=".5" stroke-linecap="round"/>'
    return s


def river(y=820, col="#2f6f86"):
    return f'<path d="M-200,{y} C200,{y - 50} 500,{y + 50} 900,{y} C1300,{y - 50} 1600,{y + 40} 2200,{y}" fill="none" stroke="{col}" stroke-width="46" stroke-linecap="round" opacity=".85"/>'


def mountain(x, y, w=520, h=360, col="#1b2a26"):
    return f'<path d="M{x - w / 2},{y} L{x - w * 0.1},{y - h} L{x + w * 0.05},{y - h * 0.72} L{x + w * 0.2},{y - h * 0.9} L{x + w / 2},{y} Z" fill="{col}"/>'


def arrow_loop(x, y, r=120, col="#bfe8d0"):
    return (f'<path d="M{x - r},{y} A{r},{r} 0 1 1 {x},{y + r}" fill="none" stroke="{col}" stroke-width="10" stroke-linecap="round"/>'
            f'<path d="M{x - 24},{y + r - 30} L{x},{y + r} L{x - 30},{y + r + 24}" fill="none" stroke="{col}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')


def cage(x, y, w=360, h=300, col="#8a96a0"):
    bars = "".join(f'<line x1="{x - w / 2 + i * w / 8}" y1="{y - h}" x2="{x - w / 2 + i * w / 8}" y2="{y}" stroke="{col}" stroke-width="10"/>' for i in range(9))
    return f'<g>{bars}<rect x="{x - w / 2 - 12}" y="{y - h - 14}" width="{w + 24}" height="18" fill="{col}"/><rect x="{x - w / 2 - 12}" y="{y - 6}" width="{w + 24}" height="18" fill="{col}"/></g>'


def parking_lot(y=840, cols=8):
    s = f'<rect x="-100" y="{y - 30}" width="2200" height="400" fill="#1b2128"/>'
    for i in range(cols):
        x = 120 + i * 230
        s += f'<line x1="{x}" y1="{y - 30}" x2="{x - 30}" y2="{y + 300}" stroke="#d8d8c8" stroke-width="8" opacity=".6"/>'
        if i % 3 != 2:
            s += f'<rect x="{x + 40}" y="{y + 80}" width="150" height="76" rx="18" fill="{["#7a2a2a", "#2a4a7a", "#8a8a8a"][i % 3]}"/><rect x="{x + 62}" y="{y + 50}" width="106" height="44" rx="14" fill="#10161c"/>'
    return s


def skyline(y=840, col="#0f1419", seed=3):
    s = ""
    x = -60
    i = 0
    while x < 2000:
        w = 120 + (i * 53 + seed * 31) % 110
        h = 220 + (i * 97 + seed * 57) % 360
        s += f'<rect x="{x}" y="{y - h}" width="{w}" height="{h + 300}" fill="{col}"/>'
        for r in range(0, h - 40, 52):
            for c in range(0, w - 30, 34):
                if (i + r + c) % 3:
                    s += f'<rect x="{x + 16 + c}" y="{y - h + 22 + r}" width="14" height="22" fill="#f2c96a" opacity=".55"/>'
        x += w + 10
        i += 1
    return s


def house_row(y=860, col="#10161c"):
    s = ""
    for i in range(7):
        x = 150 + i * 270
        s += f'<g transform="translate({x} {y})" fill="{col}"><path d="M-95,0 L-95,-120 L0,-200 L95,-120 L95,0 Z"/><rect x="-18" y="-70" width="36" height="70" fill="#000" opacity=".5"/><rect x="-70" y="-100" width="30" height="30" fill="#f2c96a" opacity=".55"/><rect x="40" y="-100" width="30" height="30" fill="#f2c96a" opacity=".55"/></g>'
        s += f'<g transform="translate({x + 8} {y - 4})"><rect x="-14" y="-62" width="28" height="30" rx="6" fill="#d8b84a"/><path d="M-9,-62 L-9,-76 A9,9 0 0 1 9,-76 L9,-62" fill="none" stroke="#d8b84a" stroke-width="5"/></g>'
    return s


def padlock(x, y, s=1.0, col="#c8a040"):
    return f'<g transform="translate({x} {y}) scale({s})"><path d="M-50,-10 L-50,-70 A50,50 0 0 1 50,-70 L50,-10" fill="none" stroke="{col}" stroke-width="18"/><rect x="-82" y="-14" width="164" height="130" rx="18" fill="{col}"/><circle cx="0" cy="40" r="16" fill="#3a2a08"/></g>'


def globe(x, y, r=170):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#2a6f93"/><path d="M{x - r * .6},{y - r * .3} Q{x - r * .2},{y - r * .8} {x + r * .1},{y - r * .5} Q{x + r * .5},{y - r * .3} {x + r * .3},{y + r * .1} Q{x},{y + r * .4} {x - r * .4},{y + r * .1} Z" fill="#4aa06a"/>'
            f'<path d="M{x + r * .2},{y + r * .4} Q{x + r * .55},{y + r * .3} {x + r * .5},{y + r * .65} Q{x + r * .3},{y + r * .8} {x + r * .1},{y + r * .6} Z" fill="#4aa06a"/>')


def price_tag(x, y, s=1.0, col="#e8c040"):
    return f'<g transform="translate({x} {y}) rotate(-14) scale({s})"><path d="M-110,-50 L60,-50 L120,0 L60,50 L-110,50 Z" fill="{col}"/><circle cx="-80" cy="0" r="12" fill="#2a2208"/><text x="0" y="22" font-family="Poppins" font-weight="800" font-size="62" text-anchor="middle" fill="#2a2208">$</text></g>'


def cracks(x, y, s=1.0, col="#e9eef2"):
    d = "M0,0 L-60,50 L-30,120 L-120,200 M0,0 L70,60 L40,140 L130,230 M0,0 L10,-90 L-40,-170 M-60,50 L-160,40 M70,60 L170,30"
    return f'<g transform="translate({x} {y}) scale({s})" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" opacity=".85"><path d="{d}"/></g>'


def calendar(x, y, s=1.0):
    cells = ""
    for r in range(5):
        for c in range(7):
            col = ["#c24a3a", "#3a6ac2", "#c2a03a", "#4aa070"][(r * 7 + c) % 4]
            cells += f'<rect x="{-210 + c * 62}" y="{-70 + r * 62}" width="54" height="54" rx="6" fill="{col}" opacity=".75"/>'
    return f'<g transform="translate({x} {y}) scale({s})"><rect x="-240" y="-170" width="480" height="440" rx="18" fill="#e7e3d8"/><rect x="-240" y="-170" width="480" height="76" rx="18" fill="#b83a3a"/>{cells}</g>'


def list_rows(x, y, n=7, w=420):
    return "".join(f'<rect x="{x - w / 2}" y="{y + i * 70}" width="{w * (1 if i % 3 else 0.7)}" height="46" rx="8" fill="#e50914" opacity="{0.9 - i * 0.08}"/>' for i in range(n))


def ring_of_people(x, y, r=300, n=8, h=210, col=DARK):
    s = ""
    for k in range(n):
        a = k / n * math.tau
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.32
        s += fig(px, py, h, "hold", col)
    return s


def chain_hands(x, y):
    return "".join(f'<ellipse cx="{x + i * 90}" cy="{y}" rx="30" ry="16" fill="none" stroke="#ffcf7a" stroke-width="7"/>' for i in range(-4, 5))


def person_row(x0, y, cols=20, cell=52, red_from=None, col="#e8eef2", red="#d94040"):
    """one row of small person icons (used for the 97% pictogram)."""
    s = ""
    for c in range(cols):
        x = x0 + c * cell
        colr = red if (red_from is not None and c >= red_from) else col
        s += f'<g fill="{colr}"><circle cx="{x}" cy="{y - 20}" r="8"/><rect x="{x - 9}" y="{y - 10}" width="18" height="26" rx="8"/></g>'
    return s
