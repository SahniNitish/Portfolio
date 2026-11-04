# Project memory (read me first)

This repo is the user's YouTube production studio. Everything lives in `video-studio/`. The user follows sessions from the **Claude mobile app**, writes short messages and wants simple, friendly replies. Send finished videos and files with `SendUserFile`.

## Two channels, two skills
| Channel | Style | Skill | Folder |
|---|---|---|---|
| **Deep Time Academy** (@DeepTimeAcademy), "History • Geopolitics • Documentaries" | Flat 2D cartoon "animated history" style, gold Cinzel titles, cut-out characters | **`make-deeptime-episode`** | `video-studio/deeptime/` |
| LunchBox Express | Stick-figure "what if" stories | `make-episode` | `video-studio/episodes/` |

## Current work (update this section when it changes)
- **Deep Time Academy, Game Theory #1 "The Dating Game"** (`video-studio/deeptime/ep01-dating-game/`): **read `PRODUCTION_PLAN.md` "STATUS" first.**
  - Done: revised 119-line script (`script.md`), all art, the full animation code for every line, voice for lines 1-73 and 75, a partial preview video.
  - **Blocked on voice:** line 74 and lines 76-119 (45 lines, about 3,700 credits). The Fish *connector* spends package credits (plan "free", about 23 left). The user's extra $5 is *API* balance, so it only works through the REST API with `FISH_AUDIO_API_KEY` as an environment secret (`tools/voice_missing.py`). Ask the user which route they want (API key or top-up).
  - After voicing: transcription check, `python episode.py` (about 30 min, refuses to run with missing voice), checks, thumbnails, metadata, send the video.

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
