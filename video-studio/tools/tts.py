"""Voice every line of an episode's lines.txt into audio/l1.wav, l2.wav, ...

Voice engine, best first: ElevenLabs when ELEVENLABS_API_KEY is set, else Kokoro (free, offline,
natural; run with a Python 3.12 env that has `pip install kokoro soundfile`), else Piper.
ElevenLabs also saves audio/lN.align.json (per-character timings) for exact caption/card sync.

    python tools/tts.py episodes/ep01-never-sleep
    python tools/tts.py episodes/ep01-never-sleep --only 3     # redo just line 3
"""
import argparse, base64, json, os, subprocess, sys, urllib.request

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
SETTINGS = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25, "use_speaker_boost": True, "speed": 1.05}
PIPER_MODEL = os.environ.get("PIPER_MODEL", "")
KOKORO_VOICE = os.environ.get("KOKORO_VOICE", "af_heart")   # male option: am_michael
KOKORO_SPEED = float(os.environ.get("KOKORO_SPEED", "1.0"))
_kokoro = None


def kokoro(text, out_base):
    global _kokoro
    import numpy as np, soundfile as sf
    if _kokoro is None:
        from kokoro import KPipeline
        _kokoro = KPipeline(lang_code="a" if KOKORO_VOICE[0] == "a" else "b")
    audio = np.concatenate([np.asarray(a) for _, _, a in _kokoro(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED)])
    sf.write(out_base + ".wav", audio, 24000)


def have_kokoro():
    try:
        import kokoro as _  # noqa: F401
        return True
    except ImportError:
        return False


def eleven(text, prev, nxt, out_base):
    body = json.dumps({"text": text, "model_id": MODEL_ID, "voice_settings": SETTINGS,
                       "previous_text": prev, "next_text": nxt}).encode()
    req = urllib.request.Request(ELEVEN_URL.format(voice=VOICE_ID), body, method="POST", headers={
        "xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.load(r)
    open(out_base + ".mp3", "wb").write(base64.b64decode(res["audio_base64"]))
    json.dump(res.get("alignment"), open(out_base + ".align.json", "w"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out_base + ".mp3",
                    "-ac", "1", "-ar", "48000", out_base + ".wav"], check=True)


def piper(text, out_base):
    if not PIPER_MODEL:
        sys.exit("No ELEVENLABS_API_KEY and no PIPER_MODEL set; see PLAYBOOK.md > Environment setup")
    subprocess.run(["piper", "-m", PIPER_MODEL, "--length_scale", "0.92", "--sentence_silence", "0.15",
                    "-f", out_base + ".wav"], input=text.encode(), check=True, stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--only", type=int, help="1-based line number to regenerate")
    a = ap.parse_args()
    lines = [l.strip() for l in open(os.path.join(a.episode, "lines.txt")) if l.strip()]
    os.makedirs(os.path.join(a.episode, "audio"), exist_ok=True)
    use_eleven = bool(os.environ.get("ELEVENLABS_API_KEY"))
    use_kokoro = not use_eleven and have_kokoro()
    print("voice engine:", "elevenlabs" if use_eleven else f"kokoro ({KOKORO_VOICE})" if use_kokoro else "piper")
    if use_eleven and not VOICE_ID:
        sys.exit("Set ELEVENLABS_VOICE_ID (copy it from the voice's page in ElevenLabs)")
    for i, text in enumerate(lines, 1):
        if a.only and i != a.only:
            continue
        base = os.path.join(a.episode, "audio", f"l{i}")
        if use_eleven:
            eleven(text, " ".join(lines[max(0, i - 3):i - 1]), " ".join(lines[i:i + 2]), base)
        elif use_kokoro:
            kokoro(text, base)
        else:
            piper(text, base)
        print(f"l{i} ok  {text[:60]}")


if __name__ == "__main__":
    main()
