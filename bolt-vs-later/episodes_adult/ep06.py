from .kit import *

EP = dict(num=6, bpm=90, key=0, title_lines=["MOTIVATION", "IS A *LIE.*"], shots=[
    title(),
    room(10, 0, "January first. Big goals. Huge energy.", act="bed_wake", x=960, day="JAN 1", wake_at=1.0, clock=False),
    room(10, 1, act="bed_phone", x=960, day="JAN 14", text=["Two weeks later...", "*the feeling is gone.*"], every=4),
    text(["Motivation is *weather.*", "Discipline is *climate.*"], 12,
         vo="Motivation comes and goes like the weather. If you only move when you feel it, you'll barely move.", every=6),
    room(12, 1, "Wait until you feel like it.", who="later", vo_at=4, act="chair_phone", x=1000, shadow="lean", sx=1500),
    stat(66, "average days for a habit to feel automatic. The range: 18 to 254.", "Lally et al., University College London", suffix=" DAYS"),
    climb(["You won't feel like it.", "*Go anyway.*"], "DAY 9"),
    kneel(["*Most people quit here.*"], whisper="Everyone quits. Why not you?"),
    rise("*Act first.*"),
    fight("*If-then plans.*", "Use if then plans. If it's seven a.m., then shoes on. A review of ninety four studies found they help people follow through.",
          COMBOS[3], (1.0, 0.66), "street"),
    fight("*Stack it.*", "Stack the new habit on an old one. After coffee, one page.",
          COMBOS[1], (0.66, 0.33), "gym"),
    fight("*Don't break the chain.*", "Then mark every day you show up, and watch the chain grow.",
          COMBOS[5], (0.33, 0.0), "hill"),
    gym("lift", "DAY 40"),
    montage([("alarm", "7:00 AM"), ("water", "COFFEE"), ("read", "ONE PAGE")], (40, 66)),
    dawn(["You never felt ready.", "*You did it anyway.*"], "DAY 66"),
    end("Your Future Self"),
])
