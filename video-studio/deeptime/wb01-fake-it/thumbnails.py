"""Two YouTube thumbnails (1280x720) for "Why Faking It Is Actually a Superpower": white paper, stick figure, navy + gold.

    python deeptime/wb01-fake-it/thumbnails.py   ->  thumb_a.jpg (WING IT. WIN IT.), thumb_b.jpg (FRAUD -> FOUNDER)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from stick import *  # noqa: E402,F401,F403
from PIL import Image  # noqa: E402


def thumb_a():
    cv = Canvas(1.3)
    ground(cv, 980, 60, 1860)
    cv.band(900, 190, 1850, 470, col=LGOLD, alpha=0.0)
    J = figure(cv, 470, 990, h=830, pose="arms_out", face="big", w=17, outfit=("suit", "pajamas", "crown"))
    cv.text("WING IT.", 1330, 330, size=250, font="marker", col=NAVY)
    cv.band(860, 480, 1850, 700, col=LGOLD, alpha=0.9)
    cv.text("WIN IT.", 1330, 590, size=250, font="marker", col=NAVY)
    cv.text("THE SUPERPOWER OF FAKING IT", 1330, 830, size=62, font="hand", col=GREY)
    sparkles(cv, 470, 300, 1.3, n=6, r=240)
    return cv.finish()


def thumb_b():
    cv = Canvas(2.1)
    ground(cv, 980, 60, 1860)
    cv.text("FRAUD", 640, 250, size=260, font="marker", col=GREY)
    cv.line((140, 270), (1150, 250), w=26, col=RED, amp=2.0)
    cv.band(70, 440, 1230, 700, col=LGOLD, alpha=0.9)
    cv.text("FOUNDER", 650, 580, size=260, font="marker", col=NAVY)
    potato(cv, 1540, 960, 2.8, face="smile", arms="down", t=2.1)
    crown(cv, 1540, 590, 2.4, rot=-6)
    cv.text("3 YEARS OF SHOWING UP", 650, 850, size=64, font="hand", col=GREY)
    sparkles(cv, 1540, 640, 2.1, n=7, r=260)
    return cv.finish()


if __name__ == "__main__":
    for name, fn in [("thumb_a.jpg", thumb_a), ("thumb_b.jpg", thumb_b)]:
        im = fn().resize((1280, 720), Image.LANCZOS) if False else fn().resize((1280, 720))
        im.save(os.path.join(HERE, name), quality=93)
        print(name, os.path.getsize(os.path.join(HERE, name)) // 1024, "KB")
