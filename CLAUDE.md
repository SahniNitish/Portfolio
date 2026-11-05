# Project memory (read me first)

This repo is the user's YouTube production studio. Everything lives in `video-studio/`. The user follows sessions from the **Claude mobile app**, writes short messages and wants simple, friendly replies. Send finished videos and files with `SendUserFile`.

## Two channels, two skills
| Channel | Style | Skill | Folder |
|---|---|---|---|
| **Deep Time Academy** (@DeepTimeAcademy), "History • Geopolitics • Documentaries" | Flat 2D cartoon "animated history" style, gold Cinzel titles, cut-out characters | **`make-deeptime-episode`** | `video-studio/deeptime/` |
| LunchBox Express | Stick-figure "what if" stories | `make-episode` | `video-studio/episodes/` |

## Current work (update this section when it changes)
- **Deep Time Academy, Game Theory #1 "The Dating Game"** (`video-studio/deeptime/ep01-dating-game/`): finished and delivered earlier (12:58, Fish WNBA VOICEOVER narrator).
- **Whiteboard video "Why Faking It Is Actually a Superpower"** (`video-studio/deeptime/wb01-fake-it/`): **finished** (5:36). The user asked for a **white background, stick-figure** style; everything is drawn in code with `video-studio/deeptime/stick.py` (hand-drawn boiling lines, posable stick figures, props, bubbles; read its docstring). Script = the user's own (`script.md`, `lines.txt`, 43 lines); `episode.py` has one `sc_*` scene per line group, FX cue table and music. `python deeptime/wb01-fake-it/episode.py` renders in about 4 min on 4 cores.
  - **Voice is a free draft (Kokoro am_michael)** because the Fish connector had 3,816 credits and the full narration needs 4,225 (4,048 without tags). To get the WNBA VOICEOVER version: top up Fish credits, voice each line of `lines.txt` with the connector (voice `fb7ec16ca51a45a5a4db881244d7990a`, model `drama-3`), put the files in `audio/lN.wav` (see `tools/fetch_fish_audio.py`), delete `audio/clean/`, re-run `episode.py`.
  - Known script issues left as written: "four-word rule" vs the three-word quote "Action produces information"; Varun Mayya and Brian Armstrong attributions unverified; Cortes scuttled (not burned) his ships (the label says "scuttles").
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
