# Project memory (read me first)

This repo is the user's YouTube production studio. Everything lives in `video-studio/`. The user follows sessions from the **Claude mobile app**, writes short messages and wants simple, friendly replies. Send finished videos and files with `SendUserFile`.

## Two channels, two skills
| Channel | Style | Skill | Folder |
|---|---|---|---|
| **Deep Time Academy** (@DeepTimeAcademy), "History • Geopolitics • Documentaries" | Flat 2D cartoon "animated history" style, gold Cinzel titles, cut-out characters | **`make-deeptime-episode`** | `video-studio/deeptime/` |
| LunchBox Express | Stick-figure "what if" stories | `make-episode` | `video-studio/episodes/` |

## Current work (update this section when it changes)
- **Deep Time Academy, Game Theory #1 "The Dating Game"** (`video-studio/deeptime/ep01-dating-game/`): finished and delivered earlier (12:58, Fish WNBA VOICEOVER narrator).
- **Whiteboard video "Why Faking It Is Actually a Superpower"** (`video-studio/deeptime/wb01-fake-it/`): **finished** (5:05) with the **Fish WNBA VOICEOVER** narrator. The user asked for a **white background, stick-figure** style; everything is drawn in code with `video-studio/deeptime/stick.py` (hand-drawn boiling lines, posable stick figures, props, bubbles; read its docstring). `episode.py` has one `sc_*` scene per line group, FX cue table and music. `python deeptime/wb01-fake-it/episode.py` renders in about 4 min on 4 cores.
  - The Fish script (`lines.txt`) is the user's script **lightly tightened** to fit 3,816 credits (list in `script.md`); original wording is `lines_full.txt` (needs 4,225 credits). The free Kokoro version's wavs were kept in `audio/kokoro/` (git-ignored). Fish mp3s + links are in `audio/fish/`.
  - After rendering, re-attach audio with a limiter (`alimiter=limit=0.66`) so the peak lands below -1 dBFS; final was -16.4 LUFS / -1.7 dBFS.
  - Script issues: Varun Mayya and Brian Armstrong attributions unverified; Cortes scuttled (not burned) his ships (the label says "scuttles"). The "four-word rule" mistake was fixed in the Fish version.
- **Reel (9:16, 50 s) from the whiteboard video** (`video-studio/deeptime/wb02-reel/`): **finished**. Built only from old assets: 9 existing Fish lines of wb01 (0 credits), `stick.py` (Canvas now supports `size=(1080,1920)`), wb01's music and SFX. `episode.py` imports wb01 as a module; `words.json` = word timings for the word-by-word captions (spoken word is red); `caption.md` has the caption and hashtags. Renders in about 40 s. -15.6 LUFS / -1.7 dBFS. The user's attached reference clip (Prof. Jiang clips) was used only as format reference.
- **Next:** Game Theory #2 "a game played by entire nations" (proposed, not started; script first, get approval before spending credits).

## What the user likes (keep doing this)
- **"Animated history" style:** flat 2D cartoon characters that move (slide in, hop, land, breathe), animated maps and diagrams, pop-up labels, gold titles with a shine. **Not** painted still images. They rejected that early on.
- **Narration with curious energy:** questions out loud, twists, "here's the strange part". The voice is Fish Audio **WNBA VOICEOVER** (`fb7ec16ca51a45a5a4db881244d7990a`), model `drama-3`, with `[curious]` / `[serious]` / `[mysterious]` tags.
- **Sound effects on everything:** whooshes, pops, ticks, booms, shimmer, heartbeat, chalk, coins, plus a curious pizzicato music track.
- **Show work in small steps:** script first, then a short sample, then the full video. They review and ask for edits.
- Videos should be **10–12 minutes** for this channel.

## Rules
- **Original scripts only.** Topics often come from Professor Jiang Xueqin's *Predictive History* lectures. Never copy his transcript, footage or voice. Write a new script with real, checkable facts and credit him in the description.
- No celebrity sound-alike voices.
- All text in images is drawn in code. Never ask the image AI for words.
- Never commit `.mp4` files. Commit and push everything else to the working branch (currently `bolt-vs-later-youtube`).
- Never paste API keys into chat or files.
- Fish Audio and Figma both cost credits. Check the balance and get the user's OK before large spends. Never re-call text-to-speech just to download a file again.

## Tools available in sessions
- **Fish Audio MCP** (voice: `text_to_speech`, `search_voices`, `get_credit_balance`)
- **Figma MCP** (art: `create_session` → `generate_image`, fileKey `mYCHq9ept7nhO6j3oJPCIx`)
- Python render environment: `~/venvs/render` (Pillow, numpy, faster-whisper). Recreate it in a fresh session with the skill's setup step. ffmpeg is preinstalled.
- Library: `video-studio/deeptime/dta.py` (see its docstring). Engine: `video-studio/tools/engine.py`.
