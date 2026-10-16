"""Build an adult-season episode: beat-locked shot timeline, sparse narration, score, SFX, render."""
import copy
import importlib
import math
import os
import subprocess
import time

import numpy as np
import skia

from engine import audio as A
from engine.gfx import clamp, draw_text, text_width, wrap
from . import fx, sound
from .shots import SHOTS, fight_events

FPS = 30
W, H = fx.W, fx.H
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build", "adult")
OUT = os.path.join(ROOT, "output", "adult", "videos")

# Public-domain Piper voices (see README): a calm deep narrator and LATER's low whisper.
A.VOICES["narrator"] = ("en_US-john-medium", 1.12, "rubberband=pitch=0.9,aecho=0.8:0.5:60:0.12,highpass=f=70")
A.VOICES["later"] = ("en_US-bryce-medium", 1.15, "rubberband=pitch=0.72,aecho=0.8:0.7:90:0.35,lowpass=f=5000")


def load(n):
    return copy.deepcopy(importlib.import_module(f"episodes_adult.ep{n:02d}").EP)


def timeline(ep):
    bpm = ep.get("bpm", 92)
    beat = 60 / bpm
    cur = 0.0
    voice, sfx, caps, music = [], [], [], []
    for i, s in enumerate(ep["shots"]):
        p = s.setdefault("p", {})
        beats = s.get("beats", 8)
        start = cur
        vo = s.get("vo")
        need = 0.0
        if vo:
            who = s.get("who", "narrator")
            a = A.tts(vo, who)
            at = start + s.get("vo_at", 1) * beat
            voice.append((at, a, who))
            dur = len(a) / A.SR
            caps.append((at, at + dur + 0.2, vo, who))
            need = (at - start) + dur + 0.5
        if s["type"] == "fight":
            from .shots import fight_timeline
            _, end = fight_timeline(p, beat)
            need = max(need, end + beat)
        d = max(beats * beat, need)
        d = math.ceil(d / (2 * beat) - 1e-6) * 2 * beat      # keep cuts on the half-bar grid
        s["start"], s["dur"] = start, d
        music.append((start, start + d, s.get("music", 1)))
        typ = s["type"]
        # automatic sound design
        if typ == "title":
            sfx += [(start + 0.4, "glitch", 0.5), (start + 1.0, "boom", 0.9)]
        if typ == "fight":
            sfx += [(start + t, n, g) for (t, n, g) in fight_events(p, beat)]
        if typ in ("climb", "kneel", "run") or p.get("wind"):
            sfx.append((start, "wind", 0.5 if typ != "run" else 0.3, d))
        if typ == "kneel":
            k = 0
            while k * 2 * beat < d - 0.5:
                sfx.append((start + k * 2 * beat, "heartbeat", 0.7))
                k += 1
        if typ == "rise":
            sfx += [(start, "riser", 0.5, d - 0.2), (start + d - 0.15, "boom", 0.9)]
        if typ == "montage":
            for k in range(len(p["panels"])):
                sfx.append((start + k * p.get("every", 2) * beat, "whoosh", 0.4))
        if typ == "climb" and p.get("push_at") is not None:
            sfx.append((start + p["push_at"] * beat, "thud", 0.8))
        if typ == "room" and p.get("act") == "bed_wake":
            sfx.append((start + 0.2, "alarm", 0.5))
        if typ == "room" and p.get("shadow") in ("offer", "behind", "loom"):
            sfx.append((start + 0.1, "glitch", 0.3))
        if typ == "dawn":
            sfx.append((start, "swell", 0.5, min(4.0, d)))
        if typ == "stat":
            for k in range(12):
                sfx.append((start + 0.3 + k * 0.13, "tick", 0.4))
            sfx.append((start + 1.9, "thud", 0.6))
        lines = p.get("text") or []
        if isinstance(lines, str):
            lines = [lines]
        for k in range(len(lines)):
            sfx.append((start + p.get("text_at", 0.6) * beat + k * p.get("every", 4) * beat, "thud", 0.35))
        for (bt, name, g) in s.get("sfx", []):
            sfx.append((start + bt * beat, name, g))
        cur += d
    return cur, beat, voice, sfx, caps, music


def mix(ep, total, voice, sfx, music, path):
    n = int(total * A.SR) + A.SR
    v = np.zeros(n, dtype=np.float32)
    for (st, a, who) in voice:
        s0 = int(st * A.SR)
        e = min(n, s0 + len(a))
        v[s0:e] += a[: e - s0] * (0.95 if who == "narrator" else 0.85)
    sc = sound.score(total, music, bpm=ep.get("bpm", 92), key=ep.get("key", 0), seed=ep["num"])
    sc = np.pad(sc, (0, max(0, n - len(sc))))[:n]
    env = np.abs(v)
    k = int(0.3 * A.SR)
    cs = np.concatenate([[0.0], np.cumsum(env, dtype=np.float64)])
    idx = np.arange(n)
    env = ((cs[np.clip(idx + k // 2, 0, n)] - cs[np.clip(idx - k // 2, 0, n)]) / k).astype(np.float32)
    duck = 1.0 - 0.45 * np.clip(env / 0.04, 0, 1)
    fxs = np.zeros(n, dtype=np.float32)
    for ev in sfx:
        st, name, g = ev[:3]
        dur = ev[3] if len(ev) > 3 else None
        s0 = int(st * A.SR)
        if s0 < 0 or s0 >= n:
            continue
        a = sound.sfx(name, seed=s0, dur=dur) * g
        e = min(n, s0 + len(a))
        fxs[s0:e] += a[: e - s0]
    out = v + sc * 0.42 * duck + fxs * 0.55
    left = out + 0.03 * np.roll(sc, 240)
    right = out + 0.03 * np.roll(sc, -240)
    st = np.stack([left, right], axis=1)
    st = st / max(1.0, np.max(np.abs(st)) / 0.95)
    A.write_wav(path, st[: int(total * A.SR)])


def captions(c, caps, T):
    for (s, e, txt, who) in caps:
        if s <= T < e:
            a = int(255 * clamp(min(T - s, e - T) / 0.2))
            lines = wrap(txt, "Inter-SemiBold.otf", 40, 1400)
            y = H - fx.BAR - 30 - (len(lines) - 1) * 50
            for i, ln in enumerate(lines):
                color = "#FF6B75" if who == "later" else "#E6E8EE"
                draw_text(c, ln, W / 2 + 2, y + i * 50 + 2, "Inter-SemiBold.otf", 40, color="#000000", alpha=int(a * 0.8))
                draw_text(c, ln, W / 2, y + i * 50, "Inter-SemiBold.otf", 40, color=color, alpha=a)
            return


def render(ep, preview=None, workers_hint=""):
    t0 = time.time()
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    slug = f"ep{ep['num']:02d}"
    total, beat, voice, sfx, caps, music = timeline(ep)
    shots = ep["shots"]
    nframes = int(total * FPS)
    surface = skia.Surface(W, H)
    c = surface.getCanvas()

    def frame(fi):
        T = fi / FPS
        si = 0
        for i, s in enumerate(shots):
            if s["start"] <= T:
                si = i
        s = shots[si]
        ctx = dict(t=T - s["start"], d=s["dur"], T=T, p=s["p"], beat=beat, ep=ep)
        c.save()
        c.clear(skia.ColorBLACK)
        SHOTS[s["type"]](c, ctx)
        c.restore()
        fx.vignette(c, 150)
        fx.grain(c, T)
        fx.bars(c)
        captions(c, caps, T)
        # fades: in from black on the first shot, out at the end, optional per-shot fade
        if T < 0.6:
            fx.flash(c, 1 - T / 0.6, "#000000")
        if T > total - 1.2:
            fx.flash(c, clamp((T - (total - 1.2)) / 1.2), "#000000")
        if s.get("fade_in") and T - s["start"] < 0.5:
            fx.flash(c, 1 - (T - s["start"]) / 0.5, "#000000")
        return surface.makeImageSnapshot().toarray()

    if preview is not None:
        from PIL import Image
        for (name, tsec) in preview:
            img = frame(min(nframes - 1, int(tsec * FPS)))
            Image.fromarray(img[:, :, [2, 1, 0]]).save(name)
        return total

    wav = os.path.join(BUILD, f"{slug}.wav")
    mix(ep, total, voice, sfx, music, wav)
    print(f"[adult {slug}] {total:.1f}s, {nframes} frames, {len(shots)} shots", flush=True)
    out = os.path.join(OUT, f"{slug}.mp4")
    tmp = out + ".part.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-tune", "animation",
           "-pix_fmt", "yuv420p", "-threads", "2", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac",
           "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", tmp]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(nframes):
        proc.stdin.write(frame(fi).tobytes())
        if fi % 900 == 0:
            print(f"[adult {slug}] frame {fi}/{nframes} ({time.time() - t0:.0f}s)", flush=True)
    proc.stdin.close()
    proc.wait()
    os.replace(tmp, out)
    print(f"[adult {slug}] done in {time.time() - t0:.0f}s -> {out}", flush=True)
    return total
