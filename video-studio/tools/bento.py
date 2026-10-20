"""Code-drawn "Bento" concept: a mascot whose head is a lunchbox. Quick preview without AI credits.

    python tools/bento.py   -> assets/characters/concepts/bento_code_sample.jpg
"""
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INK, CREAM, BLUE, BLUE_D, YELLOW, SILVER, WHITE = (25, 25, 30), (250, 240, 220), (70, 130, 220), (45, 95, 175), \
    (255, 200, 40), (205, 210, 220), (255, 255, 255)


def bento(size=900, mood="happy"):
    S = size * 3
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ow = S // 90
    cx = S / 2
    # body + legs
    d.rounded_rectangle((cx - S * .16, S * .56, cx + S * .16, S * .86), S * .12, fill=CREAM, outline=INK, width=ow)
    for dx in (-.08, .08):
        d.rounded_rectangle((cx + S * dx - S * .045, S * .84, cx + S * dx + S * .045, S * .97), S * .03, fill=CREAM, outline=INK, width=ow)
    # arms + mitten hands (one waving when happy, both up when shocked)
    arms = [((-.15, .62), (-.30, .52 if mood == "shocked" else .74)), ((.15, .62), (.30, .40 if mood == "happy" else .52))]
    for (x0, y0), (x1, y1) in arms:
        d.line((cx + S * x0, S * y0, cx + S * x1, S * y1), fill=INK, width=ow * 5)
        d.line((cx + S * x0, S * y0, cx + S * x1, S * y1), fill=CREAM, width=ow * 3)
        d.ellipse((cx + S * x1 - S * .045, S * y1 - S * .045, cx + S * x1 + S * .045, S * y1 + S * .045), fill=WHITE, outline=INK, width=ow)
    # scarf
    d.rounded_rectangle((cx - S * .17, S * .53, cx + S * .17, S * .60), S * .03, fill=YELLOW, outline=INK, width=ow)
    d.polygon([(cx + S * .06, S * .58), (cx + S * .14, S * .58), (cx + S * .16, S * .72), (cx + S * .08, S * .70)], fill=YELLOW, outline=INK)
    # lunchbox head: box, lid (pops up when shocked), handle, latch
    top, bot, hw = S * .16, S * .54, S * .26
    lid_lift = S * .06 if mood == "shocked" else 0
    d.rounded_rectangle((cx - hw, S * .33, cx + hw, bot), S * .05, fill=BLUE, outline=INK, width=ow)          # box
    d.rounded_rectangle((cx - hw - S * .01, top - lid_lift, cx + hw + S * .01, S * .35 - lid_lift), S * .06,
                        fill=BLUE_D, outline=INK, width=ow)                                                     # lid
    d.arc((cx - S * .09, top - lid_lift - S * .09, cx + S * .09, top - lid_lift + S * .06), 180, 360, fill=INK, width=ow * 3)
    d.arc((cx - S * .09, top - lid_lift - S * .09, cx + S * .09, top - lid_lift + S * .06), 180, 360, fill=SILVER, width=ow)
    # face on the front of the box
    ey = S * .41
    for ex in (-.09, .09):
        r = S * (.055 if mood == "shocked" else .045)
        d.ellipse((cx + S * ex - r, ey - r, cx + S * ex + r, ey + r), fill=WHITE, outline=INK, width=ow)
        pr = r * .45
        d.ellipse((cx + S * ex - pr, ey - pr + S * .005, cx + S * ex + pr, ey + pr + S * .005), fill=INK)
        by = ey - r - S * (.04 if mood == "shocked" else .02)
        d.line((cx + S * ex - S * .05, by + (S * .01 if ex < 0 else 0), cx + S * ex + S * .05, by + (0 if ex < 0 else S * .01)),
               fill=INK, width=ow * 2)
    # latch mouth
    if mood == "shocked":
        d.rounded_rectangle((cx - S * .04, S * .47, cx + S * .04, S * .525), S * .015, fill=INK)
    else:
        d.arc((cx - S * .06, S * .44, cx + S * .06, S * .51), 20, 160, fill=INK, width=ow * 2)
    d.rounded_rectangle((cx - S * .03, S * .325 - lid_lift / 2, cx + S * .03, S * .365), S * .01, fill=SILVER, outline=INK, width=ow // 2)
    if mood == "shocked":                                                                            # surprise lines
        for k in range(3):
            x = cx - S * .12 + k * S * .12
            d.line((x, top - lid_lift - S * .12, x + (k - 1) * S * .03, top - lid_lift - S * .19), fill=INK, width=ow * 2)
    im = im.resize((size, size), Image.LANCZOS)
    # paper cut-out edge + soft shadow
    a = im.getchannel("A")
    edge = Image.new("RGBA", im.size, WHITE + (255,))
    edge.putalpha(a.filter(ImageFilter.MaxFilter(13)))
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 255))
    shadow.putalpha(a.filter(ImageFilter.MaxFilter(13)).point(lambda v: v * 0.35).filter(ImageFilter.GaussianBlur(12)))
    out = Image.new("RGBA", (size + 30, size + 30), (0, 0, 0, 0))
    out.alpha_composite(shadow, (18, 22)); out.alpha_composite(edge, (0, 0)); out.alpha_composite(im, (0, 0))
    return out


if __name__ == "__main__":
    out_dir = os.path.join(ROOT, "assets", "characters", "concepts")
    os.makedirs(out_dir, exist_ok=True)
    bg = Image.open(os.path.join(ROOT, "episodes", "ep01-never-sleep", "img", "street.jpg")).convert("RGBA")
    bg = bg.resize((1920, round(1920 * bg.height / bg.width)), Image.LANCZOS).crop((0, 0, 1920, 1080))
    bg.alpha_composite(bento(620, "happy"), (300, 420))
    bg.alpha_composite(bento(620, "shocked"), (1050, 420))
    bg.convert("RGB").save(os.path.join(out_dir, "bento_code_sample.jpg"), quality=92)
    bento(1024, "happy").save(os.path.join(out_dir, "bento_happy.png"))
    print("saved", out_dir)
