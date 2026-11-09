"""Build the KazChart scene JSON for "The Religious Imagination: How Early Humans Understood the Universe".

    python build_scene.py                      -> scene.json, timed by ESTIMATE (2.6 words/second)
    python build_scene.py words.json           -> scene.json, timed by the real voiceover (words.json from KazChart's timestamps.py)
    python build_scene.py words.json --total 600   (optional: force the end time)

The KazChart renderer itself is NOT in this repo (proprietary, owner's licence): run it from your own copy of the skill.
Sentences are the lines of script.txt (a line starting with "§" is a chapter heading that may or may not be spoken).
"""
import difflib, json, os, re, sys
from art import *

HERE = os.path.dirname(os.path.abspath(__file__))
LINES = [l.strip() for l in open(os.path.join(HERE, "script.txt")) if l.strip()]
HEAD = [l.startswith("§") for l in LINES]
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


# ------------------------------------------------------------------ timing
def estimate():
    t, out = 0.4, []
    for i, l in enumerate(LINES):
        if HEAD[i]:
            out.append((t, t)); continue
        n = len(l.split())
        d = n / 2.6 + 0.12
        out.append((t, t + d)); t += d + (0.45 if l.rstrip().endswith((".", "?", "!")) else 0.25)
    return out, t + 1.0


def from_words(path):
    words = json.load(open(path))
    words = words["words"] if isinstance(words, dict) else words
    ws = [(w.get("word", w.get("text", "")), w["start"], w["end"]) for w in words]
    toks = [(i, norm(t)) for i, l in enumerate(LINES) for t in l.replace("§", "").split() if norm(t)]
    sm = difflib.SequenceMatcher(None, [t for _, t in toks], [norm(w) for w, _, _ in ws], autojunk=False)
    first, last = {}, {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            i = toks[blk.a + k][0]; w = ws[blk.b + k]
            first[i] = min(first.get(i, 1e9), w[1]); last[i] = max(last.get(i, 0), w[2])
    out = []
    for i in range(len(LINES)):
        out.append((first.get(i), last.get(i)))
    # fill gaps (headings, unmatched lines)
    for i in range(len(out)):
        if out[i][0] is None:
            prev = next((out[j][1] for j in range(i - 1, -1, -1) if out[j][1] is not None), 0.0)
            nxt = next((out[j][0] for j in range(i + 1, len(out)) if out[j][0] is not None), prev + 1)
            out[i] = (prev + 0.05, max(prev + 0.1, min(nxt - 0.05, prev + 1.5)))
    return out, ws[-1][2] + 1.5


args = [a for a in sys.argv[1:] if not a.startswith("--")]
if args:
    TT, TOTAL = from_words(args[0])
else:
    TT, TOTAL = estimate()
if "--total" in sys.argv:
    TOTAL = float(sys.argv[sys.argv.index("--total") + 1])


# ------------------------------------------------------------------ DSL
def S(i, off=0.0): return ("S", i, off)
def F(i, frac): return ("F", i, frac)


def svg(markup, at=0.0, fade=0.7, t1=None):
    e = {"type": "svg", "markup": markup, "t0": at, "fade": fade}
    if t1 is not None: e["t1"] = t1
    return e


def cap(text, at, until=None, pos="bottom", size=None):
    e = {"type": "caption", "text": text, "t0": at, "pos": pos}
    if until is not None: e["t1"] = until
    if size: e["size"] = size
    return e


def pill(text, x, y, at, check=False, tone=None, size=None, w=None):
    e = {"type": "pill", "text": text, "x": x, "y": y, "t0": at}
    if check: e["check"] = True
    if tone: e["tone"] = tone
    if size: e["size"] = size
    if w: e["w"] = w
    return e


def stack(items, x, y, gap=78, size=26, w=None):
    e = {"type": "factstack", "x": x, "y": y, "gap": gap, "size": size, "items": [{"text": t, "t0": a, **({"tone": tone} if tone else {}), **({"check": True} if ck else {})} for t, a, tone, ck in items]}
    if w: e["w"] = w
    return e


def stamp(text, x, y, at, color=None, rot=-6, size=60):
    e = {"type": "stamp", "text": text, "x": x, "y": y, "t0": at, "rotate": rot, "size": size}
    if color: e["color"] = color
    return e


def circle(x, y, rx, ry, at, color=None, seed=3):
    e = {"type": "circle", "x": x, "y": y, "rx": rx, "ry": ry, "t0": at, "seed": seed}
    if color: e["color"] = color
    return e


def redx(x, y, at, size=90): return {"type": "redx", "x": x, "y": y, "t0": at, "size": size}
def tag(text, at=0.0, x=70, y=80, size=28, box=False): return {"type": "tag", "text": text, "x": x, "y": y, "t0": at, "size": size, "box": box}
def big(to, x, y, at, frm=0, suffix="", prefix="", size=170, dur=1.6, color=None):
    e = {"type": "bignumber", "from": frm, "to": to, "x": x, "y": y, "t0": at, "suffix": suffix, "prefix": prefix, "size": size, "dur": dur}
    if color: e["color"] = color
    return e
def doc(title, at, x=960, y=540, w=560, h=640, header="", footer="", rot=-1): return {"type": "doccard", "title": title, "t0": at, "x": x, "y": y, "w": w, "h": h, "header": header, "footer": footer, "rotate": rot}
def check(title, items, x, y, at, w=560): return {"type": "checklist", "title": title, "x": x, "y": y, "t0": at, "w": w, "items": [{"text": t, **({"check": c} if c is not None else {})} for t, c in items]}
def name(title, sub, x, y, at, w=320): return {"type": "namecard", "title": title, "sub": sub, "x": x, "y": y, "t0": at, "w": w}
def meter(x, y, w, value, at, title="", number=None, unit="", sub="", dur=2.0):
    e = {"type": "meter", "x": x, "y": y, "w": w, "value": value, "t0": at, "dur": dur}
    if title: e["title"] = title
    if number is not None: e["number"] = number
    if unit: e["unit"] = unit
    if sub: e["sub"] = sub
    return e


# ------------------------------------------------------------------ backgrounds
COLD = {"top": "#2e4052", "bottom": "#080d13", "rays": False, "particleCount": 30}
EARTH = {"top": "#a9652f", "bottom": "#1b0e07", "rays": True, "rayOpacity": 0.1}
DUSK = {"top": "#6a3f2e", "bottom": "#120a07", "rays": True, "rayOpacity": 0.08}
FOREST = {"top": "#1f5d47", "bottom": "#04100b", "rays": True, "rayOpacity": 0.11}
NIGHT = {"top": "#0c2218", "bottom": "#020605", "rays": False}
CAVE = {"mode": "paper"}
CITY = {"top": "#44586a", "bottom": "#090e13", "rays": False, "particleCount": 25}
BLACK = {"mode": "black"}
DARKRED = {"top": "#3a1612", "bottom": "#0b0505", "rays": False}


def cam(z0=1.0, z1=1.1, x=960, y=540, pan=0, py=0): return {"zoomFrom": z0, "zoomTo": z1, "x": x, "y": y, "panX": pan, "panY": py}


SHOTS = []


def sh(a, b, bg, els, camera=None, fadeIn=0.0, fadeOut=0.0, vignette=None):
    SHOTS.append({"a": a, "b": b, "bg": bg, "els": els, "cam": camera or cam(), "fadeIn": fadeIn, "fadeOut": fadeOut, "vignette": vignette})


# =============================================================== COLD OPEN (sentences 0-16)
sh(0, 0, COLD, [tag("A QUESTION", S(0, .4)), cap("something *UNCOMFORTABLE*", S(0, .8), pos="center", size=64)], fadeIn=0.8)
sh(1, 2, COLD, [svg(phone(1360, 540, 1.7), S(1, 1)), cap("genuinely *CONNECTED*?", S(1, .6), S(2, -.1), size=52), redx(1360, 540, S(2, .8), 150), cap("Not through your *phone*.", S(2, .5), size=52)], cam(1, 1.12, 1360, 540))
sh(3, 3, COLD, [stack([("#mindfulness", S(3, .9), None, False), ("#blessed", S(3, 1.5), None, False), ("#goodvibes", S(3, 2.1), None, False)], 200, 330, 96, 34),
                stamp("CURATED", 1460, 560, S(3, 2.4), "#e5383b", -8, 80), cap("a curated *Instagram* post", S(3, .3), size=48)])
sh(4, 4, EARTH, [svg(sun(1320, 520, 540), S(4, 0)), svg(hills(780, "#0c0906", 50) + ground(870, "#050403"), 0, .01), svg(acacia(1560, 880, 1.4), 0, .01),
                 svg(fig(900, 880, 420, "up"), S(4, 1.5)), cap("connected to the *EARTH*", S(4, 1.8), size=56)], cam(1, 1.15, 900, 600))
sh(5, 6, COLD, [cap("something *WORSE*", S(5, .4), S(6, -.1), pos="center", size=70), svg(fig(700, 900, 520, "stand"), S(6, .4)), svg(fig(1220, 900, 520, "stand"), S(6, .4)),
                cap("truly *EQUAL*?", S(6, 1.2), size=60)], cam(1, 1.1, 960, 520))
sh(7, 8, COLD, [doc("THEORY", S(7, .2), 560, 540, 460, 560, "political sense", "not this"), redx(560, 540, S(7, 1.5), 200),
                svg(fig(1180, 900, 480, "stand"), S(8, 0)), svg(fig(1500, 900, 480, "stand"), S(8, .1)), circle(1340, 600, 330, 330, S(8, .7), "#f2e35b", 5), cap("*ACTUALLY* equal", S(8, .3), size=54)])
sh(9, 11, COLD, [stack([("NO BOSSES", F(10, .05), None, True), ("NO LANDLORDS", F(10, .35), None, True), ("NO ALGORITHM DECIDING YOUR WORTH", F(10, .62), None, True)], 220, 330, 100, 34),
                 cap("No one *ABOVE* you. No one *BELOW* you.", S(9, .2), S(10, -.1), size=48), cap("Just... *EQUAL*.", S(11, .1), size=64, pos="center")])
sh(12, 12, EARTH, [svg(person_row(300, 330 + r * 62, 20, 52, 17 if r == 4 else None), S(12, 1.4 + 0.45 * r)) for r in range(5)] + [tag("HUMAN HISTORY  -  EACH ICON = 1%", S(12, 1.2), 300, 250, 26),
                   big(97, 1500, 520, S(12, 3.0), 0, "%", "", 150, 1.6), cap("the default. the other *3%* is the world you know.", S(12, 5.0), pos="top", size=44), cap("for *97%* of human history", S(12, 1.0), size=56)], cam(1, 1.06, 960, 520))
sh(13, 13, BLACK, [stamp("JUST A TUESDAY", 960, 500, S(13, 1.0), "#f5a623", -4, 96), cap("that was just... *TUESDAY*", S(13, .2), pos="top", size=54)])
sh(14, 14, COLD, [svg(alarm_clock(1360, 520, 1.5), S(14, 2.6)), cap("You're lucky if you catch a *GLIMPSE*", S(14, .2), size=50), big(1, 560, 560, S(14, 2.2), 0, " / MONTH", "", 150, 1.2), cap("before the alarm drags you back to the *GRIND*", S(14, 3.4), size=44, pos="top")], cam(1, 1.1, 1000, 540))
sh(15, 16, BLACK, [cap("what we *LOST*", S(15, 1.2), S(16, -.1), pos="center", size=74), cap("the way you see your life might *SHIFT*", S(16, .8), pos="center", size=56)], fadeOut=0.7)

# =============================================================== PART 1 (17-47): the world you were never told about
sh(17, 18, EARTH, [svg(sun(1300, 480, 560), 0.2), svg(hills(800, "#0c0906", 45, 2) + ground(880, "#050403"), 0, .01), svg(acacia(420, 890, 1.3), 0, .01), svg(acacia(1650, 890, 1.0), 0, .01),
                   svg(fig(1000, 890, 330, "carry") + fig(1100, 890, 300, "stand") + fig(1190, 890, 320, "stand"), S(18, 1)), tag("PART 1  /  THE WORLD YOU WERE NEVER TOLD ABOUT", S(17, .3), 70, 80, 30),
                   big(300000, 960, 330, S(18, .6), 0, " YEARS", "", 150, 3.0), cap("a reality fundamentally *DIFFERENT* from yours", S(18, 3.2), size=48)], cam(1, 1.12, 1000, 560), fadeIn=0.7)
sh(19, 21, EARTH, [svg(sun(1500, 380, 480), 0), svg(hills(820, "#0c0906", 40, 5) + ground(890, "#050403"), 0, .01), doc("ARCHAEOLOGICAL\nFACTS", S(21, 0), 1370, 520, 520, 600, "field notes", "evidence, not romance", 2),
                   stamp("NOT ROMANCE", 520, 380, S(20, .6), "#f5a623", -5, 56), stamp("NOBLE SAVAGE NONSENSE?", 700, 640, S(19, 2.4), "#e5383b", 4, 38), cap("*STAY* with me", S(19, 3.4), until=S(20, -.1), size=48), cap("This is about *FACTS*.", S(21, .1), size=56)], cam(1, 1.08, 960, 540))
sh(22, 22, EARTH, [svg(sun(960, 460, 640), 0), svg(hills(830, "#0c0906", 35, 7) + ground(895, "#050403"), 0, .01), svg(ring_of_people(960, 860, 420, 7, 250), S(22, .4)),
                   stack([("PEACEFUL", F(22, .58), None, True), ("EGALITARIAN", F(22, .72), None, True), ("ARTISTIC", F(22, .9), None, True)], 120, 300, 90, 38)], cam(1, 1.1, 960, 620))
sh(23, 23, DUSK, [svg(sun(1450, 520, 560), 0), svg(hills(830, "#0b0705", 40, 3) + ground(900, "#040302"), 0, .01), svg(fig(560, 890, 320, "sit") + fig(700, 890, 300, "sit"), S(23, .3)), svg(fire(630, 880, 0.9), S(23, .4)),
                  svg(spear(1360, 560, 1.0, -32), S(23, 1.6)), redx(1360, 560, S(23, 3.0), 140), cap("organized warfare didn't exist *YET*", S(23, 3.4), size=46)], cam(1, 1.1, 900, 580))
sh(24, 26, DARKRED, [svg(skull_crack(560, 560, 1.4), S(24, .4)), pill("OCCASIONAL SKULL FRACTURES", 1000, 380, S(24, 1.2), size=30), pill("SOMEONE GOT CLUBBED", 1000, 470, S(25, .6), None, "red", 30),
                    stamp("LARGE-SCALE SLAUGHTER", 1210, 720, S(26, 1.2), "#e5383b", -4, 54), cap("a relatively *RECENT* invention", S(26, 2.4), size=50)], cam(1, 1.08, 800, 560))
sh(27, 28, COLD, [svg(pyramid(960, 800), S(27, 1.4)), redx(960, 560, S(28, .5), 330), cap("*EGALITARIAN*. No rigid hierarchy.", S(27, .1), size=52), tag("WHERE IT GETS UNCOMFORTABLE", S(27, .9), 70, 80, 24)], cam(1, 1.07, 960, 560))
sh(29, 29, COLD, [svg(crown(420, 560, 2.0), S(29, .2)), redx(420, 560, S(29, 1.0), 150), svg(money_bag(960, 650, 2.0), S(29, 1.2)), redx(960, 560, S(29, 2.1), 150), svg(office_window(1500, 560, 1.4), S(29, 2.3)), redx(1500, 560, S(29, 3.2), 190),
                  pill("NO KINGS", 300, 800, S(29, .3), size=30), pill("NO BILLIONAIRES", 720, 800, S(29, 1.3), size=30), pill("NO CORNER OFFICES", 1240, 800, S(29, 2.4), size=30)], cam(1, 1.06, 960, 540))
sh(30, 31, EARTH, [svg(sun(1000, 400, 540), 0), svg(hills(800, "#0c0906", 30, 4) + ground(880, "#050403"), 0, .01), svg("".join(hut(250 + i * 280, 890, 170) for i in range(6)), S(30, .3)),
                   {"type": "bracket", "x1": 165, "y1": 640, "x2": 1655, "y2": 640, "t0": S(30, 1.6), "label": "uniform in SIZE"}, cap("wealth didn't *CONCENTRATE*", S(31, .2), size=54)], cam(1, 1.1, 960, 620))
sh(32, 32, EARTH, [svg(sun(960, 420, 520), 0), svg(hills(840, "#0c0906", 30, 6) + ground(900, "#050403"), 0, .01), svg(fig(780, 890, 420, "stand") + fig(1140, 890, 420, "stand"), S(32, .5)),
                   {"type": "bracket", "x1": 640, "y1": 380, "x2": 1280, "y2": 380, "t0": S(32, 2.2), "label": "= roughly equal status and power"}, cap("men and women *SHARED* power", S(32, .4), size=52)], cam(1, 1.08, 960, 600))
sh(33, 35, NIGHT, [svg(glow(960, 560, 560, "#ffb85c", .35, "wsp"), 0), svg(fig(960, 890, 460, "stand") + headdress(960, 890, 460), S(33, 1.0)), name("SHAMAN", "the people who understood the invisible world", 960, 960, S(33, 2.0), 640),
                   pill("WARRIORS", 200, 380, S(34, .2), None, "red", 30), pill("CEOs", 200, 470, S(34, 1.0), None, "red", 30), pill("INFLUENCERS", 200, 560, S(34, 1.7), None, "red", 30),
                   cap("elevated status? *SPIRITUAL LEADERS*", S(33, .3), S(34, -.1), size=48), cap("the *INVISIBLE* world", S(35, .2), size=56)], cam(1, 1.12, 960, 560), vignette=0.85)
sh(36, 38, EARTH, [svg(sun(1000, 440, 520), 0), svg(hills(830, "#0c0906", 35, 8) + ground(895, "#050403"), 0, .01), svg(fig(560, 890, 430, "carry"), S(36, 2)), big(47, 1220, 470, S(38, .5), 0, "", "", 230, 1.4),
                   cap("pairs of shoes", S(38, 1.9), pos="bottom", size=40), redx(1220, 440, S(38, 3.6), 220), cap("everything you owned, carried on your *BACK*", S(38, 3.4), pos="top", size=46)], cam(1, 1.1, 900, 580))
sh(39, 40, CAVE, [svg(handprint(520, 560, 1.4, "#b85a2c", -8) + handprint(760, 620, 1.2, "#c46a3a", 6) + handprint(960, 520, 1.5, "#a84e24", 0), S(39, .4)), cap("*ARTISTIC*, but not for profit", S(39, .3), until=S(40, -.1), size=52),
                  pill("NO BRAND DEALS", 1180, 430, S(40, .1), None, "red", 32), pill("NO LIKES", 1180, 520, S(40, 1.0), None, "red", 32)], cam(1, 1.1, 800, 560))
sh(41, 41, CAVE, [svg(bison(780, 760, 2.0), S(41, 1.0)), svg(handprint(1500, 460, 1.3), S(41, 1.4)), svg(flute(1400, 800, 1.5), S(41, 3.0)), tag("40,000 YEARS OLD", S(41, 3.2), 1180, 930, 30, True),
                  cap("painted caves, carved figurines, *BONE FLUTES*", S(41, .2), size=44)], cam(1, 1.12, 960, 560))
sh(42, 43, CAVE, [svg(glow(960, 560, 700, "#ffb85c", .4, "wspir"), 0), svg(handprint(960, 600, 2.6, "#e88a44"), S(42, .3)), cap("not a commodity.", S(42, .3), until=S(43, -.1), pos="top", size=52), cap("a direct line to the *SPIRIT WORLD*", S(43, .3), size=58)], cam(1, 1.15, 960, 560))
sh(44, 46, COLD, [svg(calendar(540, 520, 1.4), S(45, .8)), svg(office_window(1340, 520, 1.4), S(45, .1)), pill("YOUR APARTMENT", 200, 900, S(45, .1), size=30), pill("YOUR CALENDAR", 560, 900, S(45, .9), size=30), pill("YOUR BANK ACCOUNT", 950, 900, S(46, .1), size=30),
                  cap("never feels like *ENOUGH*", S(46, 1.6), pos="top", size=54), cap("Now look at *YOUR* life.", S(44, .1), until=S(45, -.1), size=56)], cam(1, 1.06, 960, 540))
sh(47, 47, BLACK, [cap("is this *BETTER*?", S(47, 1.3), pos="center", size=84)], fadeOut=0.9)

# =============================================================== PART 2 (48-80): the worldview that held everything together
sh(48, 49, FOREST, [svg(tall_tree(300, 1000, 1.0, "#04120c") + tall_tree(1620, 1000, 1.1, "#04120c") + tall_tree(1000, 1000, 0.8, "#06170f"), 0), tag("PART 2  /  THE WORLDVIEW THAT HELD EVERYTHING TOGETHER", S(48, .3), 70, 80, 26),
                    cap("they weren't *STUPID*", S(49, 1.4), pos="center", size=70)], cam(1, 1.1, 960, 540), fadeIn=0.8)
sh(50, 52, FOREST, [stamp("SUPERSTITION", 600, 460, S(50, .8), "#e5383b", -5, 66), redx(600, 460, S(50, 2.2), 260), stamp("A SOPHISTICATED, COHERENT WORLDVIEW", 1000, 700, S(51, .6), "#3ecf6a", 3, 42),
                    stamp("IT WORKED", 1300, 400, S(52, .2), "#3ecf6a", -4, 76)], cam(1, 1.08, 960, 560))
sh(53, 55, FOREST, [pill("ANCIENT EUROPE", 160, 300, S(53, 1.7), size=32), pill("THE AMAZON", 160, 420, S(53, 2.5), size=32), pill("THE CONGO", 160, 540, S(53, 3.3), size=32),
                    svg('<g stroke="#bfe8d0" stroke-width="6" fill="none" stroke-linecap="round" opacity=".7"><path d="M720,320 Q1000,420 1100,560 M720,440 L1100,560 M720,560 L1100,560"/></g>' + orb(1250, 560, 90), S(54, .4)),
                    cap("*EERILY* consistent", S(54, .3), until=S(55, -.1), size=56), stamp("WITHOUT CONTACT", 1300, 800, S(55, 1.6), "#f5a623", -4, 56)], cam(1, 1.07, 960, 560))
sh(56, 58, FOREST, [svg(orb(960, 480, 120, "#fff0b0", 16), S(56, 1.0)), doc("1\nONE SOURCE", S(56, .3), 420, 560, 480, 520, "the first idea", "a mother spirit", 2), svg(antelope(1500, 890, 1.0, "#04120c", True) + tall_tree(1700, 900, 0.7, "#04120c") + river(960, "#2f6f86"), S(58, .6)),
                    cap("a mother spirit. a primordial *WOMB*", S(57, .2), S(58, 1.3), size=50), cap("the same spiritual *ESSENCE*", S(58, 1.5), size=50)], cam(1, 1.1, 960, 560))
sh(59, 61, FOREST, [svg(mountain(560, 880, 700, 520, "#06170f") + river(900) + antelope(1450, 880, 1.2, "#04120c", True), S(61, .8)), svg(fig(960, 900, 560, "stand", "#04120c"), S(59, .2)), svg(glow(960, 500, 420, "#9be8c0", .45, "wnat"), S(60, .2)),
                    cap("You are not *SEPARATE* from nature.", S(59, .2), until=S(60, -.1), size=54), cap("You ARE *NATURE*.", S(60, .1), until=S(61, -.1), size=70), cap("the same stuff as the river, the mountain, the antelope", S(61, .3), size=44)], cam(1, 1.12, 960, 560))
sh(62, 64, FOREST, [doc("2\nTHE SOUL IS\nPERMANENT", S(62, .2), 420, 560, 520, 620, "the second idea", "not a void", 2), svg(arrow_loop(1250, 450, 150) + orb(1250, 450, 40), S(63, .4)), cap("not a terrifying *VOID*", S(63, .4), until=S(64, -.1), size=52), cap("a transition. a *RETURN*.", S(64, .2), size=56)], cam(1, 1.08, 960, 560))
sh(65, 65, FOREST, [svg(ground(880, "#06170f") + fig(700, 880, 330, "sit", "#04120c"), S(65, .2)), svg(orb(1280, 260, 70, "#fff0b0", 10), S(65, 1.6)),
                    svg('<path d="M720,560 Q980,380 1240,300" fill="none" stroke="#fff0b0" stroke-width="6" stroke-dasharray="14 12"/>', S(65, 1.4)), pill("THE SOUL  ->  THE SPIRIT WORLD", 960, 660, S(65, 1.6), size=28), pill("THE BODY  ->  THE EARTH", 960, 750, S(65, 3.2), size=28)], cam(1, 1.1, 960, 560))
sh(66, 68, COLD, [cap("how *TERRIFIED* your culture is of death", S(66, .2), until=S(67, -.1), size=48), pill("THE INDUSTRY BUILT AROUND DENYING IT", 200, 420, S(67, .5), None, "red", 30), stamp("THEY LIVED WITH IT DAILY", 1000, 700, S(68, .3), "#f5a623", -4, 50), stamp("DIDN'T CRUMBLE", 1300, 860, S(68, 2.4), "#3ecf6a", 5, 56)], cam(1, 1.07, 960, 560))
sh(69, 70, NIGHT, [svg('<rect x="1100" y="200" width="620" height="640" fill="#1c2a22"/>' + fig(760, 880, 420, "stand", "#04120c") + '<g transform="translate(1410 880)">' + fig(0, 0, 420, "stand", "#0a120e") + "</g>", S(69, .4)),
                   doc("3\nTHE PHYSICAL WORLD\nIS THE SHADOW", S(69, .1), 420, 520, 560, 620, "the third idea", "", 2), cap("What you see and touch? A *SHADOW*.", S(70, .2), size=52)], cam(1, 1.08, 960, 560))
sh(71, 73, FOREST, [svg(orb(1360, 440, 130, "#fff0b0", 16), S(71, 1.4)), pill("MATTER", 200, 440, S(72, .6), None, None, 38, 320), pill("SPIRIT", 1060, 620, S(73, .3), "check", None, 38, 320),
                    cap("the real reality happens in the *SPIRIT WORLD*", S(71, .3), size=46), cap("You think matter is primary. They thought *SPIRIT* was.", S(72, .3), pos="top", size=50)], cam(1, 1.07, 960, 560))
sh(74, 75, FOREST, [doc("4\nRECIPROCITY", S(74, .3), 400, 540, 480, 560, "the fourth idea", "the crucial one", 2), svg(fig(1000, 880, 400, "point", "#04120c") + antelope(1500, 880, 1.2, "#04120c", True), S(75, .2)), circle(1250, 700, 330, 220, S(75, 1.4), "#f2e35b", 7),
                    cap("sharing an origin means killing requires *NEGOTIATION*", S(75, .4), size=44)], cam(1, 1.08, 1000, 560))
sh(76, 78, FOREST, [check("BEFORE THE HUNT", [("Ask", S(77, .5)), ("Apologize", S(77, 1.4)), ("Give something back", S(77, 2.4))], 240, 460, S(76, .6), 640), stamp("NO TRIBUTE = RETRIBUTION", 1330, 720, S(78, 1.4), "#e5383b", -5, 44), cap("You can't just *TAKE*.", S(76, .1), until=S(77, -.1), size=56)], cam(1, 1.06, 960, 560))
sh(79, 80, FOREST, [svg(arrow_loop(560, 520, 150, "#7ec8a0"), S(79, .5)), redx(560, 540, S(79, 3.0), 200), cap("good to the planet because you *RECYCLE*?", S(79, .1), until=S(80, -.1), size=48), svg(fig(1000, 880, 400, "point", "#04120c") + antelope(1460, 880, 1.2, "#04120c", True) + '<g fill="#fff0b0" opacity=".9"><circle cx="1180" cy="520" r="10"/><circle cx="1230" cy="500" r="8"/><circle cx="1275" cy="520" r="6"/></g>', S(80, .2)),
                    cap("conversations with the *SPIRITS* of the animals they ate", S(80, .3), size=44)], cam(1, 1.08, 960, 560), fadeOut=0.7)

# =============================================================== PART 3 (81-109): the Pygmies and the truth about "pretending"
sh(81, 82, NIGHT, [svg(tall_tree(240, 1000, 1.3, "#030a07") + tall_tree(700, 1000, 1.0, "#040c08") + tall_tree(1250, 1000, 1.2, "#030a07") + tall_tree(1720, 1000, 1.4, "#030a07"), 0), tag("PART 3  /  THE PYGMIES AND THE TRUTH ABOUT \"PRETENDING\"", S(81, .3), 70, 80, 24),
                   tag("CONGO BASIN  -  AFRICAN RAINFOREST", S(82, 1.0), 70, 140, 24), cap("the *RAINFOREST*", S(82, .6), size=64)], cam(1, 1.12, 960, 560), fadeIn=0.7)
sh(83, 83, NIGHT, [svg(glow(960, 520, 520, "#ffb85c", .3, "wmal"), 0), svg(malimo(900, 560, 1.6), S(83, 1.2)), name("MALIMO", "a trumpet-like instrument", 960, 900, S(83, 2.4), 480), cap("a trumpet-like instrument called the *MALIMO*", S(83, .2), size=46)], cam(1, 1.1, 960, 560))
sh(84, 84, NIGHT, [svg(glow(960, 520, 520, "#ffb85c", .3, "wmal"), 0), svg(malimo(780, 620, 1.4) + waves(1050, 420, 5, "#ffb85c", 1.3), S(84, .3)), cap("the living sound, the *SPIRIT*, of the forest", S(84, .6), size=48)], cam(1, 1.12, 900, 540))
sh(85, 86, NIGHT, [svg(tall_tree(300, 1000, 1.2, "#030a07") + tall_tree(1620, 1000, 1.3, "#030a07"), 0), svg('<circle cx="1480" cy="260" r="120" fill="#e8edd8" opacity=".85"/><circle cx="1530" cy="240" r="105" fill="#0c2218"/>', S(86, .5)),
                   stack([("ILLNESS", S(85, .8), None, False), ("FAILED HUNTS", S(85, 1.6), None, False), ("DEATH", S(85, 2.6), "red", False)], 200, 360, 90, 34), cap("the forest has fallen *ASLEEP*", S(86, .2), size=54)], cam(1, 1.08, 960, 560))
sh(87, 89, NIGHT, [svg(fire(960, 880, 1.3), S(87, 0)), svg(fig(560, 890, 380, "dance") + fig(760, 890, 330, "up") + fig(1180, 890, 340, "dance", DARK, True) + fig(1380, 890, 390, "up", DARK, True), S(87, .5)),
                   cap("they stay up *ALL NIGHT*", S(87, .2), until=S(88, -.1), pos="top", size=54), cap("singing. dancing. playing the *MALIMO*.", S(88, .1), until=S(89, -.1), size=48), cap("not to *ENTERTAIN* themselves", S(89, .1), size=52)], cam(1, 1.14, 960, 640))
sh(90, 91, FOREST, [svg(tall_tree(300, 1000, 1.2, "#04120c") + tall_tree(1620, 1000, 1.3, "#04120c") + fire(960, 900, 1.0), 0), svg(orb(960, 380, 100, "#fff0b0", 16), S(90, .4)), cap("to *WAKE* the forest", S(90, .1), until=S(91, -.1), pos="center", size=76), cap("to restore *HARMONY*", S(91, .2), pos="center", size=76)], cam(1, 1.1, 960, 560))
sh(92, 94, COLD, [doc("ANTHROPOLOGISTS", S(93, .2), 420, 540, 520, 600, "first encounters", "wrote it off", 2), stack([("\"THEY'RE PRETENDING\"", S(94, .2), "red", False), ("\"IT'S MAKE-BELIEVE\"", S(94, 1.0), "red", False), ("\"CUTE PRIMITIVE SUPERSTITION\"", S(94, 1.9), "red", False)], 880, 380, 110, 34),
                  cap("Now here's what's *FASCINATING*.", S(92, .1), size=50)], cam(1, 1.06, 960, 560))
sh(95, 97, NIGHT, [svg(fire(960, 880, 1.2), 0), svg(ring_of_people(960, 860, 330, 7, 240), S(96, .2)), stamp("NOT A GAME", 960, 420, S(96, 1.0), "#3ecf6a", -4, 80), cap("more *REAL* than the physical world itself", S(97, .2), size=50)], cam(1, 1.1, 960, 600))
sh(98, 102, DARKRED, [stack([("DISRESPECTFUL?", S(98, 2.4), None, False)], 200, 340, 90, 38), stamp("A CRIME", 960, 520, S(99, .3), "#e5383b", -5, 110), cap("a crime against the *COMMUNITY*", S(100, .1), until=S(101, -.1), size=52), cap("a crime against *REALITY* itself", S(101, .1), until=S(102, -.1), size=52),
                      svg(globe(1500, 560, 190) + cracks(1500, 470, 1.4), S(101, .5)), cap("if the community stops believing, the shared world *COLLAPSES*", S(102, .3), size=44)], cam(1, 1.1, 960, 560))
sh(103, 104, NIGHT, [svg(fire(960, 880, 1.0) + ring_of_people(960, 870, 480, 11, 210), S(103, .5)), svg(chain_hands(960, 470), S(104, .6)), cap("held together by collective *BELIEF* and participation", S(104, .2), size=46)], cam(1, 1.12, 960, 640))
sh(105, 107, COLD, [svg(phone(420, 540, 1.3) + phone(760, 540, 1.3, "#e86a6a") + phone(1100, 540, 1.3, "#7be8a0") + phone(1440, 540, 1.3, "#e8d06a"), S(105, .3)), cap("*SCROLLING*.", S(106, .2), until=S(106, .9), size=60, pos="top"), cap("*CONSUMING*.", S(106, .9), until=S(106, 1.7), size=60, pos="top"), cap("*PERFORMING*.", S(106, 1.7), until=S(107, -.1), size=60, pos="top"),
                    cap("half-believing in everything, fully believing in *NOTHING*", S(107, .2), size=46)], cam(1, 1.07, 960, 560))
sh(108, 109, COLD, [check("CEREMONIES I'D STAY UP ALL NIGHT FOR", [("(none)", None)], 140, 440, S(108, .3), 640), doc("NETFLIX QUEUE", S(109, .2), 1300, 520, 520, 620, "up next", "", 2), svg(list_rows(1300, 600, 5, 380), S(109, .4)), cap("You have a *NETFLIX* queue.", S(109, .2), size=56)], cam(1, 1.07, 960, 560), fadeOut=0.7)

# =============================================================== PART 4 (110-131): what we became
sh(110, 111, CITY, [svg(skyline(850), 0), svg(cracks(960, 400, 2.4), S(111, 1.0)), tag("PART 4  /  WHAT WE BECAME", S(110, .3), 70, 80, 26), cap("everything *FRACTURED*", S(111, 1.0), pos="center", size=76)], cam(1, 1.12, 960, 560), fadeIn=0.7)
sh(112, 112, CITY, [svg(skyline(850), 0), svg(padlock(960, 520, 2.4), S(112, 1.8)), cap("one relationship to nature: *CONTROL*", S(112, .6), size=56)], cam(1, 1.1, 960, 520))
sh(113, 114, CITY, [svg(cage(520, 800, 420, 340) + antelope(520, 790, 0.8, "#10161c"), S(113, .5)), svg(parking_lot(820), S(114, .3)), pill("ZOOS FOR ANIMALS WE'VE DISPLACED", 160, 300, S(113, 1.0), size=30), pill("PARKING LOTS WHERE FORESTS WERE", 160, 392, S(114, .8), size=30),
                       cap("we pave forests to build *PARKING LOTS*", S(114, .2), size=48)], cam(1, 1.07, 960, 600))
sh(115, 116, CITY, [svg(globe(1400, 500, 220), S(116, .3)), svg(price_tag(1600, 330, 1.6), S(116, 1.6)), stack([("MANAGED", S(115, 1.2), None, False), ("EXPLOITED", S(115, 2.4), None, False), ("CONQUERED", S(115, 3.6), "red", False)], 180, 340, 90, 38), cap("we turned the living earth into a *RESOURCE*", S(116, .2), size=46)], cam(1, 1.08, 1000, 540))
sh(117, 121, CITY, [pill("HOURS: WORK IN UNITS OF TIME", 140, 300, S(118, .1), size=30), meter(940, 316, 840, 0.95, S(118, .3), "", None, "", "", 1.6), pill("PRODUCTIVITY: PEOPLE AS METRICS", 140, 520, S(119, .1), size=30), meter(940, 536, 840, 0.85, S(119, .3), "", None, "", "", 1.6),
                    pill("BANK ACCOUNT: SUCCESS AS MONEY", 140, 740, S(120, .1), size=30), meter(940, 756, 840, 1.0, S(120, .3), "", None, "", "", 1.6),
                    cap("we turned ourselves into *RESOURCES* too", S(117, .2), pos="top", size=54), stamp("A TRANSACTION", 1500, 900, S(121, .6), "#e5383b", -6, 64)], cam(1, 1.05, 960, 560))
sh(122, 125, NIGHT, [svg(ring_of_people(960, 880, 520, 9, 230) + fig(960, 880, 260, "hunch"), S(125, .3)), check("TRUST THAT...", [("the river will do what rivers do", S(123, .8)), ("the spirits will be negotiated with", S(124, .8)), ("the community will catch you if you fall", S(125, .8))], 140, 340, S(122, 1.2), 780),
                    cap("the ancient animist framework was built on *TRUST*", S(122, .2), until=S(123, -.1), pos="top", size=46)], cam(1, 1.07, 960, 560))
sh(126, 129, CITY, [svg(house_row(880), S(127, .2)), meter(260, 300, 700, 0.9, S(126, 1.0), "CONTROL", None, "", "", 3.0), meter(960, 300, 700, 0.9, S(126, 1.3), "FEAR", None, "", "", 3.0), cap("built on *FEAR*, and its cousin, control", S(126, .1), until=S(127, -.1), size=48), cap("we trust *NOTHING*", S(127, .1), until=S(128, -.1), size=56),
                    cap("so we try to control *EVERYTHING*", S(128, .1), until=S(129, -.1), size=52), cap("the more we control, the more *FRIGHTENED* we become", S(129, .1), size=48)], cam(1, 1.07, 960, 580))
sh(130, 131, CITY, [svg('<g>' + tall_tree(260, 900, 1.0, "#061d13") + tall_tree(480, 900, 0.8, "#061d13") + tall_tree(700, 900, 1.1, "#061d13") + '</g>', 0), svg(house_row(900).replace('translate(', 'translate(', 1), S(131, .2)), cap("The ancients didn't fear the *JUNGLE*.", S(130, .1), pos="top", size=56), cap("We're terrified of our own *NEIGHBORHOODS*.", S(131, .1), size=54)], cam(1, 1.08, 960, 560), fadeOut=0.7)

# =============================================================== CONCLUSION (132-154): the question that should haunt you
sh(132, 134, EARTH, [svg(sun(960, 460, 640), 0), svg(hills(820, "#0c0906", 35, 9) + ground(890, "#050403"), 0, .01), tag("CONCLUSION  /  THE QUESTION THAT SHOULD HAUNT YOU", S(132, .3), 70, 80, 24),
                     stack([("PEACEFUL", S(134, .1), None, True), ("ARTISTIC", S(134, .9), None, True), ("ECOLOGICALLY BALANCED", S(134, 1.7), None, True), ("EQUAL", S(134, 2.7), None, True)], 120, 330, 92, 36), svg(ring_of_people(1380, 880, 330, 7, 240), S(133, .6)),
                     cap("hundreds of thousands of years *HELD TOGETHER*", S(133, .2), until=S(134, -.1), size=46)], cam(1, 1.1, 960, 600), fadeIn=0.7)
sh(135, 135, BLACK, [cap("then something *SHIFTED*", S(135, .3), pos="center", size=76)])
sh(136, 138, COLD, [{"type": "rect", "x": 160, "y": 520, "w": 1600, "h": 60, "fill": "#7aa89a", "opacity": .55, "t0": S(136, 1.0)}, {"type": "rect", "x": 1690, "y": 520, "w": 70, "h": 60, "fill": "#e5383b", "t0": S(136, 4.2)},
                    tag("300,000 YEARS OF HUMANS", S(136, 1.2), 160, 480, 24), tag("THE WORLD YOU LIVE IN", S(136, 4.4), 1260, 640, 24), stamp("RELATIVELY NEW", 1300, 380, S(136, 5.2), "#e5383b", -5, 64), cap("not an *INEVITABILITY*", S(137, .1), until=S(138, -.1), pos="top", size=54), cap("not \"just how *PEOPLE* are\"", S(138, .1), pos="top", size=54),
                    cap("the hierarchy, the warfare, the greed, the exhaustion, the alienation", S(136, 1.0), until=S(136, 5), size=42)], cam(1, 1.06, 960, 540))
sh(139, 140, BLACK, [stamp("A CHOICE", 960, 460, S(139, .5), "#f5a623", -4, 120), cap("and then *FORGOT* it had made it", S(140, .1), size=58)])
sh(141, 143, COLD, [stack([("INEQUALITY", S(142, .6), None, False), ("EXPLOITATION", S(142, 1.5), None, False), ("ANXIETY AT 3 A.M.", S(142, 2.4), "red", False)], 180, 360, 92, 36), stamp("INVENTIONS", 1350, 620, S(143, .3), "#f5a623", -5, 78), cap("not eternal *LAWS OF NATURE*", S(143, .1), until=S(143, 1.4), pos="top", size=52), cap("Think about that.", S(141, .1), until=S(142, -.1), size=52)], cam(1, 1.06, 960, 560))
sh(144, 145, COLD, [svg('<g fill="none" stroke="#bfe8d0" stroke-width="10" stroke-linecap="round"><path d="M400,780 Q800,780 960,560 T1500,330"/><path d="M960,560 Q1180,680 1500,760" stroke="#7a8c9c" stroke-dasharray="14 16"/><path d="M960,560 Q1120,420 1400,500" stroke="#7a8c9c" stroke-dasharray="14 16"/></g>', S(144, .4)),
                    cap("*RECENT* ones", S(144, .1), until=S(145, -.1), pos="top", size=56), cap("inventions that could *THEORETICALLY* be different", S(145, .3), size=48)], cam(1, 1.07, 960, 560))
sh(146, 148, BLACK, [cap("if the original default was *PEACE*, *EQUALITY*, and *CONNECTION*...", S(146, .2), until=S(147, -.1), pos="center", size=54), svg(price_tag(960, 560, 3.4), S(147, 1.0)), cap("what exactly have we been *SOLD*?", S(147, .3), until=S(148, -.1), pos="top", size=62), cap("and what did it *COST*?", S(148, .3), size=70)])
sh(149, 151, DARKRED, [{"type": "reticle", "x": 960, "y": 520, "r": 120, "t0": S(149, .4)}, cap("the answer leads somewhere *DARKER*", S(149, .2), until=S(150, -.1), pos="top", size=54), cap("the shift happened for a *REASON*", S(150, .1), until=S(151, -.1), size=56), stamp("NOT AN ACCIDENT", 960, 520, S(151, .3), "#e5383b", -5, 90)], cam(1, 1.12, 960, 520), vignette=0.9)
sh(152, 154, BLACK, [cap("what broke... and why... and what *WAITS* if you reclaim it", S(152, .2), pos="center", size=50), svg('<g transform="translate(960 640)"><rect x="-230" y="-70" width="460" height="140" rx="70" fill="#d62828"/><path d="M-22,-34 L34,0 L-22,34 Z" fill="#fff"/><text x="110" y="14" font-family="Poppins" font-weight="800" font-size="40" text-anchor="middle" fill="#fff">HIT IT</text></g>', S(153, .1)),
                    cap("and let's find out *TOGETHER*", S(154, .1), size=58)], fadeOut=1.2)


# ------------------------------------------------------------------ build
def resolve(v, base, cache=None):
    if isinstance(v, tuple) and v and v[0] in ("S", "F"):
        kind, i, x = v
        a, b = TT[i]
        return round((a + x if kind == "S" else a + (b - a) * x) - base, 3)
    if isinstance(v, list):
        return [resolve(x, base) for x in v]
    if isinstance(v, dict):
        return {k: resolve(x, base) for k, x in v.items()}
    return v


def build():
    def fg_time(s):
        """absolute time of the first foreground element that is tied to the voice (tuple time), or None"""
        ts = []
        for e in s["els"]:
            t0 = e.get("t0")
            if isinstance(t0, tuple):
                kind, i, x = t0
                a, bb = TT[i]
                ts.append(a + x if kind == "S" else a + (bb - a) * x)
        return min(ts) if ts else None
    starts = []
    for k, s in enumerate(SHOTS):
        if k == 0:
            starts.append(0.0); continue
        st = TT[s["a"]][0] - (0.2 if not HEAD[s["a"]] else 0.1)
        ft = fg_time(s)
        if ft is not None and ft - 0.45 > st:                  # first visual comes late: start the shot later so there is no empty beat
            st = min(ft - 0.45, TT[s["a"]][0] + 1.3)
        starts.append(max(0.0, st))
    for k in range(1, len(starts)):                       # keep strictly increasing
        if starts[k] <= starts[k - 1] + 0.8:
            starts[k] = starts[k - 1] + 0.8
    shots = []
    for k, s in enumerate(SHOTS):
        end = starts[k + 1] if k + 1 < len(SHOTS) else TOTAL
        d = {"start": round(starts[k], 3), "end": round(end, 3), "bg": s["bg"], "camera": s["cam"], "elements": [resolve(e, starts[k]) for e in s["els"]]}
        if s["fadeIn"]: d["fadeIn"] = s["fadeIn"]
        if s["fadeOut"]: d["fadeOut"] = s["fadeOut"]
        if s["vignette"]: d["vignette"] = s["vignette"]
        shots.append(d)
    return {"preset": "ink", "width": 1920, "height": 1080, "fps": 30, "grain": 0.05, "tokens": {"hl": "#ff9d2e", "pill": "#1a1410"}, "audio": "vo.mp3", "shots": shots}


if __name__ == "__main__":
    scene = build()
    out = os.path.join(HERE, "scene.json")
    json.dump(scene, open(out, "w"))
    n = len(scene["shots"])
    print(f"{n} shots, total {TOTAL:.1f}s ({'real voiceover timing' if args else 'ESTIMATED timing'}) ->", out)
    longest = max(scene["shots"], key=lambda s: s["end"] - s["start"])
    print("longest shot", round(longest["end"] - longest["start"], 1), "s")
