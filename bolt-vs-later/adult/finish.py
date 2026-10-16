"""Finish an adult episode for upload: optional re-rendered patch over a time range (e.g. the dawn shot),
light denoise (the per-frame film grain otherwise costs ~1 Mbit/s per second of video), two-pass loudnorm."""
import json
import os
import re
import subprocess
import sys

from . import film

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def loud_stats(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))


def finish(n, patch_dawn=False):
    src = os.path.join(ROOT, "output", "adult", "videos", f"ep{n:02d}.mp4")
    raw = os.path.join(ROOT, "build", "adult", f"ep{n:02d}_raw.mp4")
    if not os.path.exists(raw):
        os.replace(src, raw)
    st = loud_stats(raw)
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
          f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", raw]
    vf = "[0:v]hqdn3d=4:3:8:6[v]"
    if patch_dawn:
        ep = film.load(n)
        film.timeline(ep)
        sh = [s for s in ep["shots"] if s["type"] == "dawn"][0]
        seg = os.path.join(ROOT, "build", "adult", f"ep{n:02d}_dawn.mp4")
        a, b = film.render(film.load(n), segment=(sh["start"], sh["start"] + sh["dur"], seg))
        cmd += ["-itsoffset", f"{a:.4f}", "-i", seg]
        vf = (f"[0:v][1:v]overlay=eof_action=pass:enable='between(t,{a:.4f},{b - 0.001:.4f})'[o];"
              f"[o]hqdn3d=4:3:8:6[v]")
    cmd += ["-filter_complex", vf, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-tune", "animation", "-pix_fmt", "yuv420p", "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", src + ".part.mp4"]
    subprocess.run(cmd, check=True)
    os.replace(src + ".part.mp4", src)
    print(f"finished ep{n:02d}: {os.path.getsize(src) / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    patch = "--patch-dawn" in sys.argv
    for a in sys.argv[1:]:
        if a.isdigit():
            finish(int(a), patch_dawn=patch)
