"""Bolt vs Later - build script.

usage:
  python make.py durations          # synthesize voices, print episode lengths
  python make.py render 1 2 3       # render episodes to output/videos
  python make.py preview 1          # still frames for each beat -> build/preview
  python make.py thumbs             # thumbnails -> output/thumbnails
  python make.py metadata           # titles, descriptions, chapters, tags -> output/
"""
import copy
import importlib
import os
import sys

from engine.build import build_timeline, render


def load(n):
    return copy.deepcopy(importlib.import_module(f"episodes.ep{n:02d}").EP)


def main():
    cmd = sys.argv[1]
    nums = [int(x) for x in sys.argv[2:]] or list(range(1, 11))
    if cmd == "durations":
        for n in nums:
            ep = load(n)
            total, voice, _, _ = build_timeline(ep)
            words = sum(len(b["say"].split()) for b in ep["beats"])
            print(f"ep{n:02d}  {int(total // 60)}:{int(total % 60):02d}  ({total:.1f}s, {len(ep['beats'])} beats, {words} words)", flush=True)
    elif cmd == "render":
        for n in nums:
            render(load(n))
    elif cmd == "preview":
        out = os.path.join("build", "preview")
        os.makedirs(out, exist_ok=True)
        for n in nums:
            ep = load(n)
            build_timeline(ep)
            pts = [(os.path.join(out, f"ep{n:02d}_b{i:02d}.png"), b["start"] + min(2.4, b["dur"] - 0.4))
                   for i, b in enumerate(ep["beats"])]
            render(load(n), preview=pts)
    elif cmd == "metadata":
        from engine.metadata import make_all as meta_all
        for m in meta_all():
            print(m["episode"], m["duration"], m["title"])
    elif cmd == "thumbs":
        from engine.thumbs import make_all
        make_all(nums)


if __name__ == "__main__":
    main()
