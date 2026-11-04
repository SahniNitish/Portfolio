"""Voice every line of an episode that has no audio/lN.wav yet, with Fish Audio's REST API (uses the API balance,
NOT the package credits that the Fish connector spends).

    export FISH_AUDIO_API_KEY=...        # set as an environment secret, never paste it into chat or files
    python tools/voice_missing.py deeptime/ep01-dating-game --dry-run        # show what would be voiced and the byte cost
    python tools/voice_missing.py deeptime/ep01-dating-game                  # voice all missing lines
    python tools/voice_missing.py deeptime/ep01-dating-game --only 74,76,77  # just these (1-based script lines)

Voice: WNBA VOICEOVER (fb7ec16ca51a45a5a4db881244d7990a). Override with FISH_VOICE_ID.
Model: the connector used "drama-3" for lines 1-75. This script tries FISH_MODEL if set, otherwise drama-3, then
s2.1-pro, then s1, and PRINTS which model answered. If it is not drama-3 the new lines may sound a little different
from lines 1-75: tell the user and let them decide (re-voicing everything costs about 9,800 bytes of credit).
After each line it transcribes nothing; run the transcription check from the skill (step 4) when it finishes.
"""
import argparse, json, os, subprocess, sys, urllib.error, urllib.request

URL = "https://api.fish.audio/v1/tts"
VOICE = os.environ.get("FISH_VOICE_ID", "fb7ec16ca51a45a5a4db881244d7990a")
MODELS = [os.environ["FISH_MODEL"]] if os.environ.get("FISH_MODEL") else ["drama-3", "s2.1-pro", "s1"]


def tts(text, model, key):
    body = json.dumps({"text": text, "reference_id": VOICE, "format": "mp3", "mp3_bitrate": 192, "normalize": True}).encode()
    req = urllib.request.Request(URL, body, method="POST", headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json", "model": model})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--only", help="comma-separated 1-based line numbers")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    lines = [l.strip() for l in open(os.path.join(a.episode, "lines.txt")) if l.strip()]
    audio = os.path.join(a.episode, "audio")
    os.makedirs(audio, exist_ok=True)
    want = [int(x) for x in a.only.split(",")] if a.only else [i for i in range(1, len(lines) + 1)
                                                               if not os.path.exists(os.path.join(audio, f"l{i}.wav"))]
    cost = sum(len(lines[i - 1].encode()) for i in want)
    print(f"{len(want)} lines to voice, {cost} bytes of text (about ${cost * 15 / 1e6:.3f} at $15 per million bytes)")
    if a.dry_run or not want:
        print("lines:", want)
        return
    key = os.environ.get("FISH_AUDIO_API_KEY")
    if not key:
        sys.exit("FISH_AUDIO_API_KEY is not set. Ask the user to add it as an environment secret (cloud environment menu > Edit).")
    model = None
    for i in want:
        data = None
        for m in ([model] if model else MODELS):
            try:
                data = tts(lines[i - 1], m, key)
                if model is None:
                    model = m
                    print("model that answered:", model, "(drama-3 matches lines 1-75)")
                break
            except urllib.error.HTTPError as e:
                print(f"line {i}: model {m} -> HTTP {e.code} {e.read()[:200]!r}")
                if e.code in (401, 402, 403):
                    sys.exit("The API refused the key or the balance is empty. Stop and tell the user.")
        if data is None:
            sys.exit(f"line {i}: no model worked")
        base = os.path.join(audio, f"l{i}")
        open(base + ".mp3", "wb").write(data)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", base + ".mp3", "-ac", "1", "-ar", "48000",
                        base + ".wav"], check=True)
        print(f"l{i} ok  {lines[i - 1][:60]}", flush=True)


if __name__ == "__main__":
    main()
