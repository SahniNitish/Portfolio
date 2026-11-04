"""Two YouTube thumbnails (1280x720 JPG) for Game Theory #1, drawn from the episode's own art.

    python deeptime/ep01-dating-game/thumbnails.py   ->  thumb_a.jpg, thumb_b.jpg
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
from engine import *  # noqa: E402,F401,F403
import dta as D       # noqa: E402
from dta import *     # noqa: E402,F401,F403

p = lambda *a: os.path.join(HERE, *a)
D.SERIES_TAG = "GAME THEORY  ·  EP 1"
STAGE = load_bg(p("img", "bg_stage.png"))
load_cuts(p("img"), ["man_shocked", "man_curious", "woman_confident", "woman_phone"])


def base(zoom=1.25, cx=0.5, cy=0.6, dark=0.35):
    f = cam(STAGE, cx, cy, zoom)
    f = darken(f, dark)
    # vignette + warm centre glow
    yy, xx = np.ogrid[0:H:4, 0:W:4]
    m = np.exp(-(((xx - W * 0.62) / 700) ** 2 + ((yy - H * 0.45) / 420) ** 2)) * 90
    f.alpha_composite(Image.fromarray(np.dstack([m, m * 0.62, m * 0.2, m * 1.6]).clip(0, 255).astype(np.uint8), "RGBA").resize((W, H), Image.BILINEAR))
    return f


def outlined(f, xy, text, size, fill, stroke=14, anchor="la"):
    ImageDraw.Draw(f).text(xy, text, font=font(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(10, 8, 6))


def paste_char(f, name, x, base_y, h, flip=False):
    im = scaled(name, h, flip)
    sh = Image.new("RGBA", (im.width + 80, 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((10, 20, im.width + 70, 62), fill=(0, 0, 0, 120))
    f.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (round(x - sh.width / 2), round(base_y - 40)))
    f.alpha_composite(im, (round(x - im.width / 2), round(base_y - im.height)))


def badge(f, text="GAME THEORY  #1", xy=(60, 56)):
    d = ImageDraw.Draw(f)
    d.rounded_rectangle((xy[0], xy[1], xy[0] + 470, xy[1] + 86), 18, fill=(14, 12, 10, 235), outline=GOLD, width=4)
    d.text((xy[0] + 235, xy[1] + 44), text, font=cinzel(44, "Black"), fill=GOLD, anchor="mm")


def thumb_a():                      # "WHO MOVES FIRST?"
    f = base()
    paste_char(f, "man_shocked", 400, 1130, 1020)
    badge(f)
    outlined(f, (780, 250), "WHO MOVES", 235, (255, 255, 255))
    outlined(f, (780, 480), "FIRST?", 330, (235, 45, 45), stroke=16)
    ImageDraw.Draw(f).text((790, 915), "THE MATH OF DATING", font=cinzel(70, "Black"), fill=GOLD, anchor="la", stroke_width=5, stroke_fill=(10, 8, 6))
    return f


def thumb_b():                      # "WAIT = LOSE"
    f = base(cx=0.5)
    paste_char(f, "man_curious", 290, 1130, 960)
    paste_char(f, "woman_confident", 1700, 1130, 980, flip=True)
    badge(f)
    outlined(f, (W / 2 - 40, 200), "THE SIDE THAT", 150, (255, 255, 255), anchor="mm")
    outlined(f, (W / 2 - 40, 470), "WAITS", 400, (235, 45, 45), stroke=18, anchor="mm")
    outlined(f, (W / 2 - 40, 770), "ALWAYS LOSES?", 165, (255, 214, 90), stroke=14, anchor="mm")
    return f


if __name__ == "__main__":
    for name, fn in [("thumb_a.jpg", thumb_a), ("thumb_b.jpg", thumb_b)]:
        im = fn().convert("RGB").resize((1280, 720), Image.LANCZOS)
        im.save(p(name), quality=92)
        print(name, os.path.getsize(p(name)) // 1024, "KB")
