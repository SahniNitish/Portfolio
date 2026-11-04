"""Download and convert narration made with the Fish Audio CONNECTOR (text_to_speech tool results).

Each tool result has an audio_url such as https://platform.r2.fish.audio/tasks/2026-11-04/<task_id>.mp3
Record them in <episode>/audio/urls/ids.txt, one per line:   <script line number> <task_id or full audio_url>
(a bare task_id is combined with the date in FISH_DATE, default 2026-11-04; paste the FULL url when the day differs).

    python tools/fetch_fish_audio.py deeptime/ep01-dating-game        # download + convert everything missing
    python tools/fetch_fish_audio.py deeptime/ep01-dating-game --all  # redo all

Also rebuilds audio/lN.wav from audio/lN.mp3 when a fresh checkout has only the mp3 files (wav files are git-ignored).
Never re-call text_to_speech just to download a line again: that charges credits again.
"""
import argparse, os, subprocess, urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    audio = os.path.join(a.episode, "audio")
    date = os.environ.get("FISH_DATE", "2026-11-04")
    ids = {}
    path = os.path.join(audio, "urls", "ids.txt")
    if os.path.exists(path):
        for row in open(path):
            if row.strip():
                n, ref = row.split()[:2]
                ids[int(n)] = ref if ref.startswith("http") else f"https://platform.r2.fish.audio/tasks/{date}/{ref}.mp3"
    for n, url in sorted(ids.items()):
        mp3, wav = os.path.join(audio, f"l{n}.mp3"), os.path.join(audio, f"l{n}.wav")
        if a.all or not os.path.exists(mp3):
            urllib.request.urlretrieve(url, mp3)
        if a.all or not os.path.exists(wav):
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", "48000", wav], check=True)
            print(f"l{n} ok")
    for f in sorted(os.listdir(audio)):                      # mp3 present but wav missing (fresh checkout)
        if f.startswith("l") and f.endswith(".mp3"):
            wav = os.path.join(audio, f[:-4] + ".wav")
            if not os.path.exists(wav):
                subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", os.path.join(audio, f), "-ac", "1",
                                "-ar", "48000", wav], check=True)
                print(f[:-4], "wav rebuilt")


if __name__ == "__main__":
    main()
