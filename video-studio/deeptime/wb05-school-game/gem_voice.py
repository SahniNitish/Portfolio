"""Voice the video with Gemini TTS (model gemini-3.8-flash-tts, voice Bodi, no direction), by chapter, then split per line using word timestamps.
Free-tier key: TTS works, image generation does not. Usage: python gem_voice.py   (needs GEMINI_API_KEY; never print it)
"""
import base64, difflib, json, os, re, subprocess, sys, time, urllib.request, urllib.error, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
LINES = [re.sub(r"\[[^\]]*\]\s*", "", l.strip()) for l in open(os.path.join(HERE, "lines.txt")) if l.strip()]
CHAPTERS = [(1, 6), (7, 12), (13, 19), (20, 29), (30, 37), (38, 45), (46, 52), (53, 58)]
KEY = os.environ["GEMINI_API_KEY"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent"
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


def synth(text, out):
    body = {"contents": [{"role": "user", "parts": [{"text": text}]}], "generationConfig": {"responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Bodi"}}}}}
    for attempt in range(5):
        req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json", "x-goog-api-key": KEY})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=170))
            for p in r["candidates"][0]["content"]["parts"]:
                d = p.get("inlineData") or p.get("inline_data")
                if d:
                    open(out, "wb").write(base64.b64decode(d["data"])); return True
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, "attempt", attempt, flush=True)
            if e.code not in (429, 500, 503):
                return False
        except Exception as e:
            print("ERR", type(e).__name__, flush=True)
        time.sleep(25 * (attempt + 1))
    return False


def words_of(wav):
    from faster_whisper import WhisperModel
    global _m
    try: _m
    except NameError: _m = WhisperModel("base", compute_type="int8")
    a = np.frombuffer(subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", wav, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout, np.int16).astype(np.float32) / 32768
    segs, _ = _m.transcribe(a, language="en", word_timestamps=True)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def split(ch, a, b, wav):
    ws = words_of(wav)
    script = [(i, t) for i in range(a, b + 1) for t in LINES[i - 1].split()]
    sm = difflib.SequenceMatcher(None, [norm(t) for _, t in script], [norm(w) for w, _, _ in ws], autojunk=False)
    first, last = {}, {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            ln = script[blk.a + k][0]; w = ws[blk.b + k]
            first[ln] = min(first.get(ln, 1e9), w[1]); last[ln] = max(last.get(ln, 0), w[2])
    miss = [i for i in range(a, b + 1) if i not in first]
    if miss: raise SystemExit(f"chapter {ch}: could not align lines {miss}")
    w_ = wave.open(wav); sr = w_.getframerate(); data = np.frombuffer(w_.readframes(w_.getnframes()), np.int16); w_.close()
    n = b - a + 1
    for j, i in enumerate(range(a, b + 1)):
        t0 = 0.0 if j == 0 else (last[i - 1] + first[i]) / 2
        t1 = len(data) / sr if j == n - 1 else (last[i] + first[i + 1]) / 2
        seg = data[int(t0 * sr):int(t1 * sr)]
        with wave.open(os.path.join(HERE, "audio", "gem", f"l{i}.wav"), "wb") as o:
            o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(seg.tobytes())


if __name__ == "__main__":
    for k, (a, b) in enumerate(CHAPTERS, 1):
        wav = os.path.join(HERE, "audio", "gem", f"chapter{k}.wav")
        if not os.path.exists(wav):
            print("voicing chapter", k, flush=True)
            if not synth(" ".join(LINES[a - 1:b]), wav):
                raise SystemExit(f"chapter {k} failed")
            time.sleep(6)
        split(k, a, b, wav)
        print("chapter", k, "ok", flush=True)
    print("ALL DONE")
