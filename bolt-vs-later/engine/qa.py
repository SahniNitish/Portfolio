"""Optional speech-recognition check used to pick the clearest TTS take."""
import re

import numpy as np

_model = None


def _asr():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _model


def transcribe(a, sr):
    from scipy.signal import resample_poly
    a16 = resample_poly(a, 16000, sr).astype(np.float32)
    segs, _ = _asr().transcribe(a16, beam_size=1, language="en")
    return " ".join(s.text.strip() for s in segs)


def norm(s):
    from num2words import num2words
    s = s.lower().replace("%", " percent").replace("-", " ").replace("&", " and ")
    s = re.sub(r"(\d+)\.(\d+)", lambda m: m.group(1) + " point " + " ".join(m.group(2)), s)
    s = re.sub(r"\d+", lambda m: " " + num2words(int(m.group(0))) + " ", s)
    s = s.replace("-", " ").replace(",", " ")
    s = re.sub(r"[^a-z' ]", " ", s)
    return [w for w in s.split() if w not in ("and", "a", "the", "uh", "um")]


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev = cur
    return d[len(h)] / max(1, len(r))


def available():
    try:
        import faster_whisper  # noqa: F401
        import num2words  # noqa: F401
        return True
    except ImportError:
        return False
