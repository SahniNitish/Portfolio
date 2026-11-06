"""Two YouTube thumbnails (1280x720) for "Why School Sucks, According to Game Theory": stickman trapped inside a giant report card.

    python deeptime/wb05-school-game/thumbnails.py  ->  thumb_a.jpg, thumb_b.jpg
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from stick import *  # noqa: E402,F401,F403


def report_card(cv, x, y, s=1.0, rot=0):
    with cv.at(x, y, s, rot):
        cv.rect(-330, -420, 330, 420, r=14, fill=PAPER, w=14)
        cv.text("REPORT CARD", 0, -350, size=84, font="marker", col=NAVY)
        for k, (sub, gr) in enumerate((("MATH", "F"), ("ENGLISH", "D"), ("HISTORY", "C-"), ("CURIOSITY", "?"))):
            yy = -240 + k * 120
            cv.text(sub, -250, yy, size=54, font="hand", anchor="lm")
            cv.text(gr, 230, yy, size=88, font="marker", col=RED if k < 3 else GREY)
            cv.line((-290, yy + 52), (290, yy + 52), w=5, col=GREY)
        for bx in range(-270, 300, 90):                                       # cell bars across the card
            cv.line((bx, -300), (bx, 400), w=11, col=INK, amp=0.8)


def thumb_a():
    cv = Canvas(1.2)
    report_card(cv, 520, 520, 1.05, -3)
    figure(cv, 520, 880, h=520, pose="fear", face="scared", w=14)
    cv.band(1000, 130, 1830, 500, col=LGOLD, alpha=0.95)
    cv.text("SCHOOL", 1400, 250, size=170, font="marker", col=NAVY)
    cv.text("ISN'T BROKEN", 1400, 420, size=108, font="marker", col=RED)
    cv.text("GAME THEORY EXPLAINS WHY", 1400, 620, size=58, font="hand", col=GREY)
    return cv.finish()


def thumb_b():
    cv = Canvas(2.0)
    report_card(cv, 480, 520, 1.05, 2)
    figure(cv, 480, 880, h=520, pose="point_up", face="sad", w=14)
    cv.text("ROBBED?", 1360, 220, size=110, font="marker", col=GREY)
    cv.band(920, 350, 1800, 590, col=LGOLD, alpha=0.95)
    cv.text("IT'S A GAME.", 1360, 470, size=130, font="marker", col=NAVY)
    cv.text("SCHOOL ISN'T BROKEN", 1360, 740, size=64, font="marker", col=RED)
    return cv.finish()


if __name__ == "__main__":
    for name, fn in (("thumb_a.jpg", thumb_a), ("thumb_b.jpg", thumb_b)):
        im = fn().resize((1280, 720))
        im.save(os.path.join(HERE, name), quality=93)
        print(name)
