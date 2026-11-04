# Project memory (read me first)

This repo is the user's YouTube production studio. Everything lives in `video-studio/`. The user follows sessions from the **Claude mobile app**, writes short messages and wants simple, friendly replies. Send finished videos and files with `SendUserFile`.

## Two channels, two skills
| Channel | Style | Skill | Folder |
|---|---|---|---|
| **Deep Time Academy** (@DeepTimeAcademy), "History • Geopolitics • Documentaries" | Flat 2D cartoon "animated history" style, gold Cinzel titles, cut-out characters | **`make-deeptime-episode`** | `video-studio/deeptime/` |
| LunchBox Express | Stick-figure "what if" stories | `make-episode` | `video-studio/episodes/` |

## Current work (update this section when it changes)
- **Deep Time Academy, Game Theory #1 "The Dating Game"** (`video-studio/deeptime/ep01-dating-game/`)
  - Opening (lines 1–14) is done and approved: `dating_game_v2.mp4`, 1:28, WNBA VOICEOVER voice.
  - Full 11-minute script written: `script.md`, 119 lines, 8 chapters.
  - **Next:** build lines 15–119 following **`PRODUCTION_PLAN.md`**. It has a step-by-step checklist, timing, art prompts, a shot list for every line, a music plan and metadata.
  - Fish Audio credits were about 4,750 on 2026-11-04. The rest of the episode needs about 8,500, so check `get_credit_balance` and tell the user if a top-up is needed.

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
