"""Channel branding: profile picture (800x800) and YouTube banner (2560x1440).

    python tools/brand.py                      # name from CHANNEL below
    python tools/brand.py "Some Other Name"    # try another name

The mascot head is drawn in code (supersampled), so it stays crisp at any size.
"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "brand")
ANTON = os.path.join(ROOT, "assets", "fonts", "Anton.ttf")
CHANNEL = sys.argv[1] if len(sys.argv) > 1 else "LunchBox Express"
TAGLINE = "WHAT IF… STORIES WITH A TWIST"
SUBLINE = "NEW EPISODE EVERY WEEK"
NAVY, NAVY2, BLUE, YELLOW, INK, WHITE = (16, 26, 52), (38, 30, 78), (74, 127, 208), (255, 204, 0), (0, 0, 0), (255, 255, 255)


def night_sky(w, h, seed=2):
    """Vertical navy→purple gradient with a sprinkle of stars."""
    sky = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(sky)
    for y in range(h):
        u = y / h
        d.line((0, y, w, y), fill=tuple(round(a + (b - a) * u) for a, b in zip(NAVY, NAVY2)))
    rng = random.Random(seed)
    for _ in range(int(w * h / 9000)):
        x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.choice([1, 1, 1.5, 2, 3])
        a = rng.randint(120, 255)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(a, a, min(255, a + 20)))
    return sky


def mascot(size, mood="smirk"):
    """The hero's head in his striped nightcap, transparent background, size x size."""
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ow = round(S * 0.022)                                   # outline width
    cx, cy, r = S * 0.47, S * 0.60, S * 0.30
    # --- nightcap shape (drawn first so the head outline sits over its lower edge)
    cap = [(cx - r * 1.02, cy - r * 0.35), (cx - r * 0.85, cy - r * 0.95), (cx - r * 0.35, cy - r * 1.30),
           (cx + r * 0.30, cy - r * 1.42), (cx + r * 0.95, cy - r * 1.30), (cx + r * 1.45, cy - r * 0.95),
           (cx + r * 1.62, cy - r * 0.45), (cx + r * 1.50, cy - r * 0.40), (cx + r * 1.20, cy - r * 0.78),
           (cx + r * 0.90, cy - r * 0.70), (cx + r * 1.02, cy - r * 0.35)]
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(cap, fill=255)
    stripes = Image.new("RGBA", (S, S), WHITE + (255,))
    sd = ImageDraw.Draw(stripes)
    step = r * 0.32
    for k in range(-12, 12):
        x0 = cx + k * step
        sd.polygon([(x0, 0), (x0 + step / 2, 0), (x0 + step / 2 - S * 0.5, S), (x0 - S * 0.5, S)], fill=BLUE + (255,))
    img.paste(stripes, (0, 0), mask)
    d.line(cap + [cap[0]], fill=INK, width=ow, joint="curve")
    # --- head
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=INK, width=ow)
    # --- cap brim band across the forehead
    by = cy - r * 0.42
    d.rounded_rectangle((cx - r * 1.08, by - r * 0.16, cx + r * 1.08, by + r * 0.16), r * 0.16, fill=WHITE, outline=INK, width=ow)
    # --- pom-pom at the drooping tip
    px, py, pr = cx + r * 1.58, cy - r * 0.30, r * 0.24
    d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=WHITE, outline=INK, width=ow)
    # --- face
    er = r * 0.085
    for ex in (cx - r * 0.30, cx + r * 0.22):
        d.ellipse((ex - er, cy + r * 0.02 - er, ex + er, cy + r * 0.02 + er), fill=INK)
    if mood == "smirk":
        d.arc((cx - r * 0.38, cy + r * 0.12, cx + r * 0.34, cy + r * 0.62), 20, 150, fill=INK, width=ow)
        d.line((cx - r * 0.52, cy - r * 0.18, cx - r * 0.12, cy - r * 0.22), fill=INK, width=round(ow * 0.8))   # raised brow
    return img.resize((size, size), Image.LANCZOS)


def fit_font(draw, text, size, maxw):
    while draw.textlength(text, font=ImageFont.truetype(ANTON, size)) > maxw:
        size -= 4
    return ImageFont.truetype(ANTON, size)


def profile():
    W = 800
    img = night_sky(W, W, seed=5).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.ellipse((W * 0.70, W * 0.08, W * 0.86, W * 0.24), fill=(255, 240, 190))            # moon
    d.ellipse((W * 0.74, W * 0.06, W * 0.90, W * 0.22), fill=NAVY + (255,))
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((W * 0.15, W * 0.22, W * 0.85, W * 0.92), fill=(120, 150, 255, 90))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(50)))
    img.alpha_composite(mascot(int(W * 0.86)), (int(W * 0.05), int(W * 0.09)))
    return img.convert("RGB")


def banner():
    W, H = 2560, 1440
    bg_path = os.path.join(ROOT, "episodes", "ep04-tomorrows-news", "img", "bridge.jpg")
    if os.path.exists(bg_path):                                                          # our own Bridge Road art
        bg = Image.open(bg_path).convert("RGB")
        ImageDraw.Draw(bg).text((410, 196), "BRIDGE RD", font=ImageFont.truetype(ANTON, 52), fill=WHITE, anchor="mm")
        bg = bg.resize((W, round(W * bg.height / bg.width)), Image.LANCZOS).crop((0, 0, W, H)) if bg.width / bg.height < W / H \
            else bg.resize((round(H * bg.width / bg.height), H), Image.LANCZOS)
        bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(3))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
    else:
        bg = night_sky(W, H)
    img = bg.convert("RGBA")
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))                                       # darken the safe band
    ImageDraw.Draw(shade).rectangle((0, 470, W, 970), fill=NAVY + (150,))
    img.alpha_composite(shade.filter(ImageFilter.GaussianBlur(60)))
    # safe area for all devices: 1546x423 centred -> x 507..2053, y 508..931
    m = mascot(470)
    img.alpha_composite(m, (520, 480))
    d = ImageDraw.Draw(img)
    x0, maxw = 1010, 2010 - 1010
    f1 = fit_font(d, CHANNEL.upper(), 210, maxw)
    d.text((x0, 545), CHANNEL.upper(), font=f1, fill=WHITE, stroke_width=8, stroke_fill=INK)
    f2 = fit_font(d, TAGLINE, 74, maxw)
    ty = 545 + f1.size + 30
    d.text((x0, ty), TAGLINE, font=f2, fill=YELLOW, stroke_width=4, stroke_fill=INK)
    f3 = ImageFont.truetype(ANTON, 46)
    d.text((x0, ty + f2.size + 26), SUBLINE, font=f3, fill=(210, 215, 235), stroke_width=3, stroke_fill=INK)
    return img.convert("RGB")


def safe_area_preview(b):
    """Same banner with the TV / desktop / mobile crop guides drawn on, for checking only."""
    p = b.copy()
    d = ImageDraw.Draw(p)
    for (w, h), col in [((2560, 423), (255, 80, 80)), ((1546, 423), (80, 255, 80))]:
        d.rectangle(((2560 - w) / 2, (1440 - h) / 2, (2560 + w) / 2, (1440 + h) / 2), outline=col, width=6)
    return p


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pp = profile(); pp.save(os.path.join(OUT, "profile_800.png"))
    mascot(1024).save(os.path.join(OUT, "mascot_1024.png"))
    b = banner(); b.save(os.path.join(OUT, "banner_2560x1440.png"))
    safe_area_preview(b).resize((1280, 720)).save(os.path.join(OUT, "_banner_guides.jpg"), quality=85)
    circ = Image.new("L", (800, 800), 0); ImageDraw.Draw(circ).ellipse((0, 0, 800, 800), fill=255)
    pc = Image.new("RGB", (800, 800), (255, 255, 255)); pc.paste(pp, (0, 0), circ)
    pc.save(os.path.join(OUT, "_profile_circle_preview.png"))
    print("saved to", OUT)
