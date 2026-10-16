"""Shorthand for writing adult-season shot lists."""


def title(beats=8):
    return dict(type="title", beats=beats, music=0)


def end(nxt, beats=8):
    return dict(type="end", beats=beats, music=0, p=dict(next=nxt))


def room(beats=10, music=1, vo=None, who="narrator", vo_at=2, **p):
    d = dict(type="room", beats=beats, music=music, p=p)
    if vo:
        d.update(vo=vo, who=who, vo_at=vo_at)
    return d


def text(lines, beats=10, music=1, vo=None, vo_at=1, every=5, **p):
    d = dict(type="text", beats=beats, music=music, p=dict(p, text=lines, every=every))
    if vo:
        d.update(vo=vo, vo_at=vo_at)
    return d


def stat(num, label, source, beats=10, music=1, **p):
    return dict(type="stat", beats=beats, music=music, p=dict(p, num=num, label=label, source=source))


def climb(lines, day, beats=16, music=2, push_at=11, **p):
    return dict(type="climb", beats=beats, music=music,
                p=dict(p, text=lines, every=5, day=day, push_at=push_at, **{"from": 250, "to": 1000}))


def kneel(lines, beats=10, music=1, whisper=None, **p):
    d = dict(type="kneel", beats=beats, music=music, p=dict(p, text=lines, text_at=1, every=4))
    if whisper:
        d.update(vo=whisper, who="later", vo_at=3)
    return d


def rise(line, beats=8, music=2, **p):
    return dict(type="rise", beats=beats, music=music, p=dict(p, text=[line], text_at=4))


def fight(line, vo, moves, hp, env="void", music=3, **p):
    return dict(type="fight", music=music, vo=vo, vo_at=1,
                p=dict(p, moves=moves, hp=hp, text=[line], text_at=0.5, text_size=70, env=env,
                       snow=p.get("snow", env in ("street", "hill"))))


def run(lines, day, beats=14, music=3, **p):
    return dict(type="run", beats=beats, music=music, p=dict(p, text=lines, text_at=2, every=4, day=day))


def gym(act, day, beats=12, music=3, **p):
    return dict(type="gym", beats=beats, music=music, p=dict(p, act=act, day=day, reps=True, sweat=0.8))


def montage(panels, day, beats=12, music=2):
    return dict(type="montage", beats=beats, music=music, p=dict(panels=panels, every=3, day=day))


def dawn(lines, day, beats=16, music=1):
    return dict(type="dawn", beats=beats, music=music, p=dict(text=lines, every=5, day=day))


COMBOS = [
    ["s_punch", "block", "punch", "punch2"],
    ["punch", "s_punch", "block", "kick"],
    ["s_kick", "block", "uppercut", "finisher"],
    ["punch2", "punch", "s_kick", "block", "kick"],
    ["kick", "s_punch", "block", "uppercut"],
    ["s_punch", "block", "punch", "punch2", "finisher"],
]
