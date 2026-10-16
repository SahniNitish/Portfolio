"""Turn an episode script into a finished MP4."""
import math
import os
import re
import subprocess
import sys
import time

import numpy as np
import skia

from . import audio as A
from .gfx import clamp
from .scenes import SCENES, W, H, captions, logo, wipe

FPS = 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output", "videos")

GAP = 0.42          # silence after each line
SCENE_GAP = 0.25    # extra breathing room before a scene change


def clean_tts(s):
    s = s.replace("*", "")
    s = s.replace("—", ", ").replace("–", ", ")
    return s


def caption_words(s):
    out = []
    for m in re.finditer(r"\*([^*]+)\*(\S*)|(\S+)", s):
        if m.group(1):
            ws = m.group(1).split()
            ws[-1] += m.group(2) or ""
            for w in ws:
                out.append((w, True))
        else:
            out.append((m.group(3), False))
    return out


def make_chunks(words, start, end, max_chars=40):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        n = sum(len(x[0]) + 1 for x in cur)
        if n >= max_chars or w[0][-1] in ".!?":
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and sum(len(x[0]) + 1 for x in cur) < 12:
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)

    def weight(ch):
        n = sum(len(x[0]) + 1 for x in ch)
        n += sum(5 for x in ch if x[0][-1] in ",;:")
        n += sum(9 for x in ch if x[0][-1] in ".!?")
        return n
    ws = [weight(ch) for ch in chunks]
    tot = sum(ws) or 1
    res, t = [], start
    for ch, wgt in zip(chunks, ws):
        d = (end - start) * wgt / tot
        res.append((t, t + d, ch))
        t += d
    return res


def build_timeline(ep):
    beats = ep["beats"]
    cursor = 0.0
    prev_scene = None
    hp = 1.0
    voice = []      # (start_time, samples, speaker)
    chunks = []
    sfx = []
    for i, b in enumerate(beats):
        scene = b.get("scene") or prev_scene
        b["scene"] = scene
        if prev_scene is not None and scene != prev_scene:
            cursor += SCENE_GAP
            b["_cut"] = True
            sfx.append((cursor - 0.22, "whoosh", 0.35))
        b["start"] = cursor
        pre = b.get("pre", 0.15 if i else 0.9)
        who = b.get("who", "bolt")
        a = A.tts(clean_tts(b.get("tts", b["say"])), who)
        sp = cursor + pre
        voice.append((sp, a, who))
        dur_speech = len(a) / A.SR
        chunks += make_chunks(caption_words(b["say"]), sp, sp + dur_speech)
        b["dur"] = pre + dur_speech + GAP + b.get("extra", 0)
        if scene == "fight":
            b["hp_prev"] = hp
            hp = b["hp"]
            b["dur"] = max(b["dur"], 2.6)
            ht = b.get("hit_t", 1.1)
            sfx += [(cursor + ht - 0.55, "whoosh", 0.5), (cursor + ht, "impact", 0.8)]
        if scene == "title":
            sfx += [(cursor + 0.2, "fanfare", 0.6), (cursor + 0.65, "boing", 0.35)]
        if scene in ("talk", "compare") and (b.get("card") or b.get("icon") or scene == "compare"):
            sfx.append((cursor + 0.04, "pop", 0.5))
            if scene == "compare":
                sfx.append((cursor + b.get("right_at", min(b["dur"] * 0.45, 3.0)), "pop", 0.5))
        if scene == "stat":
            for k in range(10):
                sfx.append((cursor + 0.2 + k * 0.13, "tick", 0.35))
            sfx.append((cursor + 1.55, "ding", 0.45))
        if scene == "list":
            n = len(b["items"])
            span = max(0.6, (b["dur"] - 1.0)) / n
            for k in range(n):
                sfx.append((cursor + 0.3 + k * span, "pop", 0.45))
        if scene == "win" and b.get("_cut"):
            sfx += [(cursor + 0.05, "fanfare", 0.55), (cursor + 0.3, "sparkle", 0.6)]
        if scene == "later" and b.get("_cut"):
            sfx.append((cursor + 0.1, "sad", 0.4))
        if scene == "outro" and b.get("_cut"):
            sfx += [(cursor + 3.0, "pop", 0.6), (cursor + 3.4, "ding", 0.4)]
        cursor += b["dur"]
        prev_scene = scene
    total = cursor + ep.get("tail", 2.5)
    beats[-1]["dur"] += ep.get("tail", 2.5)
    # scene-run start times
    run_start = 0
    for i, b in enumerate(beats):
        if i == 0 or b["scene"] != beats[i - 1]["scene"] or b.get("restart"):
            run_start = b["start"]
        b["run_start"] = run_start
    return total, voice, chunks, sfx


def mix_audio(ep, total, voice, sfx, path):
    n = int(total * A.SR) + A.SR
    vtrack = np.zeros(n, dtype=np.float32)
    for (st, a, who) in voice:
        s = int(st * A.SR)
        vtrack[s:s + len(a)] += a[: max(0, min(len(a), n - s))]
    music = A.music(total, ep.get("music", 0), seed=ep["num"])
    music = np.pad(music, (0, max(0, n - len(music))))[:n]
    # ducking from a smoothed voice envelope
    env = np.abs(vtrack)
    k = int(0.25 * A.SR)
    cs = np.concatenate([[0.0], np.cumsum(env, dtype=np.float64)])
    lo = np.clip(np.arange(n) - k // 2, 0, n)
    hi = np.clip(np.arange(n) + k // 2, 0, n)
    env = ((cs[hi] - cs[lo]) / k).astype(np.float32)
    duck = 1.0 - 0.55 * np.clip(env / 0.05, 0, 1)
    mtrack = music * 0.20 * duck
    ftrack = np.zeros(n, dtype=np.float32)
    for (st, name, g) in sfx:
        s = int(st * A.SR)
        if s < 0 or s >= n:
            continue
        a = A.sfx(name, seed=s) * g
        e = min(n, s + len(a))
        ftrack[s:e] += a[: e - s]
    mixd = vtrack * 0.95 + mtrack + ftrack * 0.6
    # light stereo: music and sfx slightly wide
    left = mixd + 0.02 * np.roll(mtrack, 300)
    right = mixd + 0.02 * np.roll(mtrack, -300)
    st = np.stack([left, right], axis=1)
    st = st / max(1.0, np.max(np.abs(st)) / 0.95)
    A.write_wav(path, st[: int(total * A.SR)])
    return vtrack


def mouth_tracks(voice, nframes):
    tracks = {"bolt": np.zeros(nframes, dtype=np.float32), "later": np.zeros(nframes, dtype=np.float32)}
    for (st, a, who) in voice:
        env = A.envelope(a, FPS)
        f0 = int(round(st * FPS))
        e = min(nframes, f0 + len(env))
        if e > f0:
            tracks[who][f0:e] = np.maximum(tracks[who][f0:e], env[: e - f0])
    return tracks


def render(ep, out_path=None, preview=None, start_frame=0, end_frame=None):
    t0 = time.time()
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    slug = f"ep{ep['num']:02d}"
    total, voice, chunks, sfx = build_timeline(ep)
    nframes = int(total * FPS)
    wav = os.path.join(BUILD, f"{slug}.wav")
    mix_audio(ep, total, voice, sfx, wav)
    mouths = mouth_tracks(voice, nframes)
    beats = ep["beats"]
    pal = ep["pal"]
    print(f"[{slug}] duration {total:.1f}s, {nframes} frames, {len(beats)} beats", flush=True)

    surface = skia.Surface(W, H)
    c = surface.getCanvas()

    def frame(fi):
        T = fi / FPS
        bi = 0
        for i, b in enumerate(beats):
            if b["start"] <= T:
                bi = i
        b = beats[bi]
        ctx = dict(t=T - b["start"], T=T, dur=b["dur"], beat=b, pal=pal, ep=ep,
                   bm=float(mouths["bolt"][fi]), lm=float(mouths["later"][fi]),
                   st=T - b["run_start"])
        c.save()
        c.clear(skia.ColorWHITE)
        SCENES[b["scene"]](c, ctx)
        c.restore()
        if b["scene"] != "title":
            logo(c, 36, 30, 0.9)
        captions(c, chunks, T)
        # wipe around scene cuts
        for nb in beats:
            if nb.get("_cut"):
                d = T - nb["start"]
                if -0.3 < d < 0.3:
                    wipe(c, (d + 0.3) / 0.6, pal["accent"])
        # fade in/out
        if T < 0.4:
            c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * (1 - T / 0.4)))))
        if T > total - 0.8:
            a = clamp((T - (total - 0.8)) / 0.8)
            c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * a))))
        return surface.makeImageSnapshot().toarray()

    if preview is not None:
        for (name, tsec) in preview:
            fi = min(nframes - 1, int(tsec * FPS))
            img = frame(fi)
            from PIL import Image
            Image.fromarray(img[:, :, [2, 1, 0]]).save(name)
        return total

    out_path = out_path or os.path.join(OUT, f"{slug}.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "animation",
           "-pix_fmt", "yuv420p", "-threads", "2",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    end_frame = end_frame or nframes
    for fi in range(start_frame, end_frame):
        proc.stdin.write(frame(fi).tobytes())
        if fi % 600 == 0:
            el = time.time() - t0
            print(f"[{slug}] frame {fi}/{nframes} ({el:.0f}s)", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"[{slug}] done in {time.time() - t0:.0f}s -> {out_path}", flush=True)
    return total
