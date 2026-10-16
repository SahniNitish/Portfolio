"""Voice synthesis (Piper TTS), procedural music and sound effects. Everything is generated
locally, so the whole soundtrack is copyright-free."""
import hashlib
import os
import subprocess
import wave

import numpy as np

SR = 44100
VOICE_DIR = os.environ.get("PIPER_VOICES", "/tmp/claude-0/-home-user-Portfolio/a407bbff-05e9-5c1b-a923-3182d2d8a599/scratchpad/voices")
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "tts")

VOICES = {
    # speaker: (model, length_scale, ffmpeg filter)
    # Both models are trained from scratch on public-domain recordings (LJ Speech / the voice author's own recordings),
    # so the generated narration is safe for a monetised channel.
    "bolt": ("en_US-ljspeech-high", 1.0, "rubberband=pitch=1.12:formant=preserved,highpass=f=90"),
    "later": ("en_US-bryce-medium", 1.05, "rubberband=pitch=0.84,aecho=0.8:0.6:45:0.18,lowpass=f=7000"),
}

_loaded = {}


def _voice(model):
    if model not in _loaded:
        from piper import PiperVoice
        _loaded[model] = PiperVoice.load(os.path.join(VOICE_DIR, model + ".onnx"))
    return _loaded[model]


def read_wav(path):
    with wave.open(path, "rb") as w:
        n = w.getnframes()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        ch = w.getnchannels()
        if ch > 1:
            data = data.reshape(-1, ch).mean(axis=1)
        return data, w.getframerate()


def write_wav(path, data, sr=SR):
    data = np.clip(data, -1, 1)
    if data.ndim == 1:
        data = data[:, None]
    with wave.open(path, "wb") as w:
        w.setnchannels(data.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((data * 32767).astype(np.int16).tobytes())


def tts(text, speaker):
    """Return mono float32 audio at SR for a line (cached on disk)."""
    from piper import SynthesisConfig
    model, ls, filt = VOICES[speaker]
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(f"{speaker}|{model}|{ls}|{filt}|{text}".encode()).hexdigest()[:16]
    out = os.path.join(CACHE, f"{speaker}_{key}.wav")
    if not os.path.exists(out):
        from . import qa
        v = _voice(model)
        best = None
        tries = 4 if qa.available() else 1
        for k in range(tries):
            raw = out + f".raw{k}.wav"
            cand = out + f".cand{k}.wav"
            with wave.open(raw, "wb") as wf:
                v.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=ls, noise_scale=0.6, noise_w_scale=0.75))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", filt + f",aresample={SR}",
                            "-ac", "1", cand], check=True)
            os.remove(raw)
            score = 0.0
            if tries > 1:
                ca, _ = read_wav(cand)
                score = qa.wer(text, qa.transcribe(ca, SR))
            if best is None or score < best[0]:
                if best:
                    os.remove(best[1])
                best = (score, cand)
            else:
                os.remove(cand)
            if score <= 0.05:
                break
        os.replace(best[1], out)
        with open(out + ".score", "w") as f:
            f.write(f"{best[0]:.3f}\n")
    a, sr = read_wav(out)
    assert sr == SR
    # trim leading/trailing silence
    thr = 0.012
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx):
        a = a[max(0, idx[0] - 1500): idx[-1] + 2000]
    peak = np.max(np.abs(a)) or 1
    return (a / peak * 0.89).astype(np.float32)


def envelope(a, fps):
    """Per-frame mouth-open values in 0..1."""
    hop = SR / fps
    n = int(np.ceil(len(a) / hop))
    env = np.zeros(n, dtype=np.float32)
    for i in range(n):
        seg = a[int(i * hop): int((i + 1) * hop)]
        if len(seg):
            env[i] = np.sqrt(np.mean(seg ** 2))
    if env.max() > 0:
        env = env / np.percentile(env[env > 0.01], 90) if np.any(env > 0.01) else env
    env = np.clip(env, 0, 1)
    # make it chattery: emphasise variation between frames
    out = np.where(env > 0.12, 0.25 + 0.75 * env, 0)
    return np.clip(out, 0, 1)


# --------------------------------------------------------------------------
# Procedural music
# --------------------------------------------------------------------------

def _note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _adsr(n, a=0.01, d=0.1, s=0.6, r=0.2):
    env = np.ones(n, dtype=np.float32) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    env[:na] = np.linspace(0, 1, na)
    if na + nd < n:
        env[na:na + nd] = np.linspace(1, s, nd)
    if nr < n:
        env[-nr:] *= np.linspace(1, 0, nr)
    return env


def _lowpass(x, alpha):
    y = np.empty_like(x)
    acc = 0.0
    # vectorised one-pole using lfilter-like cumulative approach
    try:
        from scipy.signal import lfilter
        return lfilter([alpha], [1, alpha - 1], x).astype(np.float32)
    except Exception:
        for i in range(len(x)):
            acc += alpha * (x[i] - acc)
            y[i] = acc
        return y


STYLES = [
    # (bpm, root midi, progression (scale degrees -> semitone offsets), mode)
    dict(bpm=96, root=60, prog=[0, 7, 9, 5], minor=False),       # I V vi IV
    dict(bpm=104, root=62, prog=[0, 5, 9, 7], minor=False),      # I IV vi V
    dict(bpm=88, root=57, prog=[0, 8, 3, 10], minor=True),       # i VI III VII
    dict(bpm=110, root=64, prog=[0, 9, 5, 7], minor=False),      # I vi IV V
    dict(bpm=92, root=59, prog=[0, 5, 7, 5], minor=False),
]


def music(duration, style=0, seed=0):
    st = STYLES[style % len(STYLES)]
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    out = np.zeros(n, dtype=np.float32)
    beat = 60 / st["bpm"]
    bar = beat * 4
    t_all = np.arange(n) / SR
    nbars = int(duration / bar) + 2
    third = 3 if st["minor"] else 4
    arp_pat = [0, 2, 1, 2, 0, 2, 1, 3]
    for b in range(nbars):
        t0 = b * bar
        root = st["root"] + st["prog"][b % len(st["prog"])]
        is_minor_chord = (st["prog"][b % len(st["prog"])] in (9, 2, 4)) != st["minor"]
        th = 3 if is_minor_chord else 4
        chord = [root, root + th, root + 7, root + 12]
        # pad
        s0 = int(t0 * SR)
        L = int(bar * SR)
        if s0 >= n:
            break
        L = min(L, n - s0)
        tt = np.arange(L) / SR
        pad = np.zeros(L, dtype=np.float32)
        for m in chord[:3]:
            f = _note(m)
            for det in (-0.12, 0.12):
                ph = 2 * np.pi * f * (1 + det / 100) * tt
                pad += (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)).astype(np.float32)
        pad *= _adsr(L, 0.35, 0.3, 0.8, 0.4) * 0.035
        out[s0:s0 + L] += pad
        # bass (root, octave down) on beats 1 and 3, plus a pickup
        for k, (bt, ln) in enumerate(((0, 1.5), (2, 1.0), (3.5, 0.5))):
            bs = int((t0 + bt * beat) * SR)
            bl = int(ln * beat * SR)
            if bs + bl > n:
                continue
            tb = np.arange(bl) / SR
            f = _note(root - 24 + (12 if k == 2 else 0))
            tone = np.sin(2 * np.pi * f * tb) + 0.25 * np.sin(4 * np.pi * f * tb)
            out[bs:bs + bl] += (tone * _adsr(bl, 0.005, 0.15, 0.6, 0.06) * 0.16).astype(np.float32)
        # plucky arpeggio in 8ths
        for i in range(8):
            if rng.random() < 0.12:
                continue
            m = chord[arp_pat[i]] + 12
            ps = int((t0 + i * beat / 2) * SR)
            pl = int(0.45 * SR)
            if ps + pl > n:
                continue
            tp = np.arange(pl) / SR
            f = _note(m)
            tone = np.sin(2 * np.pi * f * tp) + 0.5 * np.sin(4 * np.pi * f * tp) * np.exp(-tp * 30)
            out[ps:ps + pl] += (tone * np.exp(-tp * 9) * 0.05).astype(np.float32)
        # drums
        for i in range(4):
            ks = int((t0 + i * beat) * SR)
            kl = int(0.22 * SR)
            if ks + kl > n:
                continue
            tk = np.arange(kl) / SR
            if i in (0, 2):
                f = 110 * np.exp(-tk * 18) + 45
                out[ks:ks + kl] += (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk * 14) * 0.22).astype(np.float32)
            else:
                nz = rng.standard_normal(kl).astype(np.float32)
                nz = nz - _lowpass(nz, 0.3)
                out[ks:ks + kl] += nz * np.exp(-tk * 22) * 0.05
            # hats on off-beats
            hs = int((t0 + i * beat + beat / 2) * SR)
            hl = int(0.06 * SR)
            if hs + hl < n:
                nz = rng.standard_normal(hl).astype(np.float32)
                nz = nz - _lowpass(nz, 0.6)
                out[hs:hs + hl] += nz * np.exp(-np.arange(hl) / SR * 70) * 0.03
    out = _lowpass(out, 0.55)
    out = out[: int(duration * SR)]
    # fades
    fi, fo = int(0.5 * SR), int(2.5 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out / (np.max(np.abs(out)) or 1)


# --------------------------------------------------------------------------
# Sound effects
# --------------------------------------------------------------------------

def sfx(name, seed=0):
    rng = np.random.default_rng(seed)
    if name == "pop":
        L = int(0.12 * SR)
        t = np.arange(L) / SR
        f = 900 * np.exp(-t * 25) + 300
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * 0.5).astype(np.float32)
    if name == "whoosh":
        L = int(0.45 * SR)
        t = np.arange(L) / SR
        nz = rng.standard_normal(L).astype(np.float32)
        out = np.zeros(L, dtype=np.float32)
        acc = 0
        alpha = np.clip(0.02 + 0.35 * np.sin(np.pi * t / t[-1]), 0, 1)
        try:
            out = _lowpass(nz, 0.2)
            out = out - _lowpass(out, 0.03)
        except Exception:
            pass
        return (out * np.sin(np.pi * t / t[-1]) ** 2 * 0.9).astype(np.float32)
    if name == "ding":
        L = int(1.2 * SR)
        t = np.arange(L) / SR
        tone = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((1318.5, 1), (2637, 0.4), (1975.5, 0.3)))
        return (tone * np.exp(-t * 4) * 0.28).astype(np.float32)
    if name == "impact":
        L = int(0.5 * SR)
        t = np.arange(L) / SR
        f = 160 * np.exp(-t * 12) + 40
        thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
        nz = rng.standard_normal(L) * np.exp(-t * 25) * 0.6
        return ((thump + nz) * 0.7).astype(np.float32)
    if name == "boing":
        L = int(0.5 * SR)
        t = np.arange(L) / SR
        f = 180 + 260 * t / t[-1] + 40 * np.sin(2 * np.pi * 18 * t)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * 0.4).astype(np.float32)
    if name == "sparkle":
        L = int(0.9 * SR)
        out = np.zeros(L, dtype=np.float32)
        for i, m in enumerate((84, 88, 91, 96)):
            s = int(i * 0.07 * SR)
            tt = np.arange(L - s) / SR
            out[s:] += (np.sin(2 * np.pi * _note(m) * tt) * np.exp(-tt * 7) * 0.18).astype(np.float32)
        return out
    if name == "sad":
        L = int(0.9 * SR)
        t = np.arange(L) / SR
        f = 420 - 180 * t / t[-1]
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5) * 0.25 * (1 + 0.3 * np.sin(2 * np.pi * 6 * t))).astype(np.float32)
    if name == "tick":
        L = int(0.05 * SR)
        t = np.arange(L) / SR
        return (np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 120) * 0.35).astype(np.float32)
    if name == "fanfare":
        out = np.zeros(int(1.6 * SR), dtype=np.float32)
        for i, (m, d) in enumerate(((72, 0.15), (76, 0.15), (79, 0.15), (84, 0.9))):
            s = int(i * 0.15 * SR)
            L = int(d * SR)
            tt = np.arange(L) / SR
            f = _note(m)
            tone = np.sign(np.sin(2 * np.pi * f * tt)) * 0.3 + np.sin(2 * np.pi * f * tt)
            out[s:s + L] += (tone * _adsr(L, 0.01, 0.1, 0.7, 0.1) * 0.14).astype(np.float32)
        return _lowpass(out, 0.35)
    raise KeyError(name)
