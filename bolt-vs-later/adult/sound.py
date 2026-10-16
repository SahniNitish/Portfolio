"""Dark cinematic score and sound design, synthesised from scratch (no copyright risk).

The score follows an intensity curve: 0 = pad only, 1 = + pulse/bass, 2 = + drums, 3 = full (+ hats, lead).
"""
import numpy as np

from engine.audio import SR, _lowpass, _note

KEYS = [  # (root midi, progression in semitones from root) all minor-ish
    (45, [0, 8, 3, 10]),    # A minor: i VI III VII
    (40, [0, 8, 5, 7]),     # E minor: i VI iv v
    (43, [0, 3, 8, 10]),    # G minor
    (38, [0, 8, 3, 10]),    # D minor
    (41, [0, 5, 8, 7]),     # F minor
]


def _env(n, a, r):
    e = np.ones(n, dtype=np.float32)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def _saw(f, t, partials=6):
    out = np.zeros_like(t)
    for k in range(1, partials + 1):
        out += np.sin(2 * np.pi * f * k * t) / k
    return out


def _reverb(x, amount=0.3):
    out = x.copy()
    for d, g in ((0.031, 0.5), (0.053, 0.42), (0.079, 0.35), (0.113, 0.28), (0.167, 0.2), (0.241, 0.14)):
        n = int(d * SR)
        out[n:] += x[:-n] * g * amount * 2
    return out


def score(duration, intensity, bpm=92, key=0, seed=0):
    """intensity: list of (t0, t1, level) segments."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    t_all = np.arange(n) / SR
    level = np.zeros(n, dtype=np.float32)
    for (t0, t1, lv) in intensity:
        level[int(t0 * SR):int(t1 * SR)] = lv
    # smooth level changes a little
    k = int(0.05 * SR)
    cs = np.concatenate([[0.0], np.cumsum(level, dtype=np.float64)])
    idx = np.arange(n)
    level = ((cs[np.clip(idx + k, 0, n)] - cs[np.clip(idx - k, 0, n)]) / (2 * k)).astype(np.float32)

    root, prog = KEYS[key % len(KEYS)]
    beat = 60 / bpm
    bar = beat * 4
    pad = np.zeros(n, dtype=np.float32)
    bass = np.zeros(n, dtype=np.float32)
    drums = np.zeros(n, dtype=np.float32)
    hats = np.zeros(n, dtype=np.float32)
    lead = np.zeros(n, dtype=np.float32)
    keys_ = np.zeros(n, dtype=np.float32)
    nbars = int(duration / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        s0 = int(t0 * SR)
        if s0 >= n:
            break
        L = min(int(bar * SR), n - s0)
        tt = np.arange(L) / SR
        r = root + prog[b % len(prog)]
        minor = prog[b % len(prog)] in (0, 5, 7)
        chord = [r + 12, r + 12 + (3 if minor else 4), r + 19]
        for m in chord:
            f = _note(m)
            pad[s0:s0 + L] += (_saw(f, tt, 5) * 0.5 + _saw(f * 1.004, tt, 5) * 0.5) * _env(L, 0.6, 0.5) * 0.03
        # sub bass: 8th note pulse
        for i in range(8):
            bs = s0 + int(i * beat / 2 * SR)
            bl = int(beat / 2 * SR * 0.9)
            if bs + bl > n:
                continue
            tb = np.arange(bl) / SR
            f = _note(r)
            bass[bs:bs + bl] += (np.sin(2 * np.pi * f * tb) + 0.3 * np.sin(4 * np.pi * f * tb)) * _env(bl, 0.004, 0.05) * 0.22
        # sparse piano-ish notes
        for i in (0, 3, 6):
            if rng.random() < 0.7:
                ks = s0 + int(i * beat / 2 * SR)
                kl = int(1.6 * SR)
                if ks + kl > n:
                    continue
                tk = np.arange(kl) / SR
                f = _note(chord[rng.integers(0, 3)] + 12)
                keys_[ks:ks + kl] += (np.sin(2 * np.pi * f * tk) + 0.25 * np.sin(4 * np.pi * f * tk)) * np.exp(-tk * 2.6) * 0.06
        # drums
        for i in range(4):
            ds = s0 + int(i * beat * SR)
            dl = int(0.35 * SR)
            if ds + dl > n:
                continue
            td = np.arange(dl) / SR
            f = 120 * np.exp(-td * 22) + 42
            drums[ds:ds + dl] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-td * 9) * 0.55
            if i in (1, 3):
                nz = rng.standard_normal(dl).astype(np.float32)
                nz = nz - _lowpass(nz, 0.15)
                body = np.sin(2 * np.pi * 190 * td) * np.exp(-td * 20)
                drums[ds:ds + dl] += (nz * np.exp(-td * 11) * 0.22 + body * 0.25)
            for h in range(4):
                hs = ds + int(h * beat / 4 * SR)
                hl = int(0.04 * SR)
                if hs + hl < n:
                    nz = rng.standard_normal(hl).astype(np.float32)
                    nz = nz - _lowpass(nz, 0.7)
                    hats[hs:hs + hl] += nz * np.exp(-np.arange(hl) / SR * 90) * (0.05 if h % 2 else 0.035)
        # lead arpeggio (only heard at full intensity)
        for i in range(8):
            ls_ = s0 + int(i * beat / 2 * SR)
            ll = int(beat / 2 * SR)
            if ls_ + ll > n:
                continue
            tl = np.arange(ll) / SR
            f = _note(chord[[0, 1, 2, 1][i % 4]] + 12)
            lead[ls_:ls_ + ll] += _saw(f, tl, 4) * np.exp(-tl * 6) * 0.04
    pad = _lowpass(pad, 0.12)
    lead = _lowpass(lead, 0.3)
    g1 = np.clip(level, 0, 1)
    g2 = np.clip(level - 1, 0, 1)
    g3 = np.clip(level - 2, 0, 1)
    mixd = pad * (0.8 + 0.4 * g1) + keys_ * (1 - 0.6 * g2) + bass * g1 + drums * g2 + hats * g3 + lead * g3
    mixd = _reverb(mixd, 0.25)
    mixd = mixd[: int(duration * SR)]
    fo = int(2.5 * SR)
    mixd[-fo:] *= np.linspace(1, 0, fo)
    return mixd / (np.max(np.abs(mixd)) or 1)


def sfx(name, seed=0, dur=None):
    rng = np.random.default_rng(seed)
    if name == "punch":
        L = int(0.35 * SR)
        t = np.arange(L) / SR
        f = 180 * np.exp(-t * 30) + 50
        thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
        nz = rng.standard_normal(L) * np.exp(-t * 45)
        return ((thump * 0.9 + nz * 0.5) * 0.9).astype(np.float32)
    if name == "boom":
        L = int(2.2 * SR)
        t = np.arange(L) / SR
        f = 70 * np.exp(-t * 2.5) + 28
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
        nz = _lowpass(rng.standard_normal(L).astype(np.float32), 0.02) * np.exp(-t * 3) * 3
        return ((b + nz) * 0.9).astype(np.float32)
    if name == "whoosh":
        L = int(0.5 * SR)
        t = np.arange(L) / SR
        nz = rng.standard_normal(L).astype(np.float32)
        out = _lowpass(nz, 0.25)
        out = out - _lowpass(out, 0.04)
        return (out * np.sin(np.pi * t / t[-1]) ** 2 * 1.2).astype(np.float32)
    if name == "riser":
        L = int((dur or 2.0) * SR)
        t = np.arange(L) / SR
        nz = rng.standard_normal(L).astype(np.float32)
        out = nz - _lowpass(nz, 0.05)
        sweep = np.sin(2 * np.pi * np.cumsum(200 + 900 * (t / t[-1]) ** 2) / SR) * 0.15
        return ((out * 0.25 + sweep) * (t / t[-1]) ** 2).astype(np.float32)
    if name == "heartbeat":
        L = int(1.0 * SR)
        out = np.zeros(L, dtype=np.float32)
        for d in (0.0, 0.22):
            s = int(d * SR)
            tt = np.arange(int(0.25 * SR)) / SR
            out[s:s + len(tt)] += (np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 18)).astype(np.float32) * (0.9 if d == 0 else 0.6)
        return out
    if name == "wind":
        L = int((dur or 4.0) * SR)
        t = np.arange(L) / SR
        nz = rng.standard_normal(L).astype(np.float32)
        out = _lowpass(nz, 0.03) * 6
        mod = 0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * t) * np.sin(2 * np.pi * 0.11 * t + 1)
        e = _env(L, 0.8, 0.8)
        return (out * mod * e * 0.5).astype(np.float32)
    if name == "alarm":
        L = int(1.2 * SR)
        t = np.arange(L) / SR
        gate = (np.sin(2 * np.pi * 8 * t) > 0).astype(np.float32)
        return (np.sign(np.sin(2 * np.pi * 1760 * t)) * 0.12 * gate * np.exp(-t * 0.5)).astype(np.float32)
    if name == "glitch":
        L = int(0.35 * SR)
        out = np.zeros(L, dtype=np.float32)
        for i in range(6):
            s = rng.integers(0, L - 2000)
            out[s:s + 1500] += (rng.standard_normal(1500) * 0.3).astype(np.float32)
            out[s:s + 1500] += np.sign(np.sin(2 * np.pi * rng.integers(80, 600) * np.arange(1500) / SR)).astype(np.float32) * 0.1
        return out
    if name == "tick":
        L = int(0.04 * SR)
        t = np.arange(L) / SR
        return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 150) * 0.3).astype(np.float32)
    if name == "thud":
        L = int(0.5 * SR)
        t = np.arange(L) / SR
        f = 90 * np.exp(-t * 15) + 40
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10) * 0.8).astype(np.float32)
    if name == "metal":
        L = int(0.8 * SR)
        t = np.arange(L) / SR
        tone = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((620, 0.4), (1340, 0.3), (2110, 0.2)))
        return (tone * np.exp(-t * 7) * 0.4).astype(np.float32)
    if name == "swell":
        L = int((dur or 2.5) * SR)
        t = np.arange(L) / SR
        out = np.zeros(L, dtype=np.float32)
        for m in (57, 60, 64, 69):
            out += _saw(_note(m), t, 4).astype(np.float32) * 0.04
        return (_lowpass(out, 0.08) * (t / t[-1]) ** 1.5 * 3).astype(np.float32)
    raise KeyError(name)
