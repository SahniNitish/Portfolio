---
name: make-deeptime-episode
description: Make a complete 10–12 minute Deep Time Academy video (history, geopolitics, game theory) in the channel's flat 2D "animated history" style. Covers script, approval, Figma AI art, Fish Audio narration, animation in Python, music and sound effects, render, checks, thumbnail and YouTube text. Use whenever the user asks to make, continue, extend, re-voice or fix a Deep Time Academy episode or a Game Theory series video. Not for the LunchBox Express stick-figure channel (that is make-episode).
---

# Skill: make a Deep Time Academy episode (10–12 minutes)

The reference episode is `video-studio/deeptime/ep01-dating-game/`. **Read its `episode.py` before you start.** Every new scene type you need probably already exists there, so copy and adapt it.

**Continuing EP01?** Its full shot list, art prompts, timing and checklist are in `ep01-dating-game/PRODUCTION_PLAN.md`. Follow that file line by line. Also read the "Current work" section of `/CLAUDE.md`, and update it when you finish a step.

Files:
- `video-studio/deeptime/dta.py`: the shared animation library (characters, gold titles, labels, logo sting, chalk, props, music, sound effects). Its docstring lists every function.
- `video-studio/tools/engine.py`: low-level engine (`cam`, `load_bg`, `key_green`, `Timeline`, `sfx`, `clean_voice`, `finish_audio`, `render`).
- `video-studio/deeptime/README.md`: channel look, the character prompts and the voice.
- `video-studio/deeptime/ep01-dating-game/script.md`: an example of the script format the user approved.

**Work in this order and never skip a step:**
1. script
2. user approves
3. art
4. voice
5. animation
6. preview
7. render
8. checks
9. deliver

---

## 0. Rules that never change

1. **Script first.** Write `script.md` and show it to the user, either by sending it with `SendUserFile` or by pasting it. **Wait for approval before spending any Fish Audio credits or Figma credits.**
2. **Original writing only.** The user's topics often come from Professor Jiang Xueqin's *Predictive History* lectures.
   - Never copy his transcript, footage or voice.
   - Write a new script on the same ideas, built on facts you can check.
   - Credit him in the description: "Inspired by Professor Jiang Xueqin's Predictive History lectures."
3. **Facts must be real.**
   - Every name, year, number and claim must be something you are sure of. If you aren't sure, leave it out or hedge it ("studies keep finding…").
   - List the sources at the bottom of `script.md`. This is an education channel: one wrong date costs trust.
4. **Look:** flat 2D cartoon "animated history" style.
   - Characters are green-screen cut-outs that move over separate backgrounds.
   - All text is drawn in code. Never ask the image AI to draw words.
   - Titles use gold Cinzel (`gold_text`), labels use Anton (`label`), and the series tag and watermark come from `chrome()`.
5. **Voice:** Fish Audio voice **WNBA VOICEOVER**, `voice_id = fb7ec16ca51a45a5a4db881244d7990a`, model **`drama-3`**. Keep the same voice for the whole channel unless the user changes it.
6. **No celebrity sound-alike voices** (Markiplier, Elon Musk and so on). They put YouTube monetization at risk.
7. **Never commit `.mp4` files** (`.gitignore` already blocks them). Commit everything else and push to the working branch.
8. **Never paste API keys** into files or chat.

---

## 1. One-time setup (each new cloud session)

```bash
python3 -m venv ~/venvs/render && ~/venvs/render/bin/pip install -q pillow numpy faster-whisper
```

You only need the Kokoro voice environment for a free draft voice (see `make-episode` step 1). Fish Audio runs through its MCP connector, so it needs no install.

Fonts: `video-studio/assets/fonts/Cinzel.ttf` (variable font: Regular/Bold/Black) and `Anton.ttf` are in the repo. **Anton has no symbols.** For ♥ ★ ♦ $ use `sym(size)` (DejaVu). For ✗ or ✓ inside a label, write plain words instead.

---

## 2. Script → `epNN-slug/script.md`, then `lines.txt`

### Length and structure (10–12 minutes)
- **About 1,500–1,700 spoken words, in 110–130 lines.** With this narrator that is about 160 words per minute of voice, plus about 0.5 s of pause per line, which gives about 11 minutes.
- One line is one sentence (or a short group) = one voice clip = one picture change.
- Use this chapter template (every chapter needs a curiosity question or a twist):

| Part | Lines | Purpose |
|---|---|---|
| **Cold open** | 12–15 | Hook in line 1. Raise the stakes. Title line ("Welcome... to X"), then the logo sting. Tease 2–3 questions the video will answer. |
| **Chapter 1: deep history** | 8–10 | The channel's angle: how this worked for most of history |
| **Chapter 2: the core idea** | 10–14 | Define the concept simply (for example: players, strategies, payoffs, information) |
| **Chapters 3–7** | 12–20 each | One big idea each, made of a real person, a year, a simple example, a twist and the lesson |
| **Chapter 8: lessons** | 8–10 | Number the lessons (one from each chapter), then the emotional close |
| **Outro** | 3 | Comment question, next-episode tease, subscribe line |

### Writing rules
- **Short sentences.** Spell out numbers the way they're spoken: "nineteen sixty-two", "thirty-seven percent", "twenty twelve".
- **Curious energy:**
  - Ask questions out loud: "So who should make the first move?"
  - Use "Here's the strange part" and "But there's a twist".
  - Pay off every question you tease.
- **Delivery tags for drama-3** go at the start of a line in square brackets: `[curious]`, `[curious, intrigued]`, `[serious]`, `[mysterious]`, `[mysterious, slow]`, `[excited]`.
  - Use `<emphasis>word</emphasis>` for one stressed word.
  - Tag about 1 line in 3, not every line.
- **Avoid `?` after short noun lists.** "Your happiness. Your family." got read with rising question pitch once. Prefer full stops.
- `script.md`: chapters with `## headings`, numbered lines, and one *Visual:* note per chapter. Fact sources go at the bottom.
- After approval, copy the numbered lines (text only, tags kept, no numbers) into `lines.txt`, one per line, with no blank lines.

---

## 3. Art (Figma AI images)

Use the Figma connector tools `create_session`, `generate_image` and `download_assets`.
- File: `fileKey = mYCHq9ept7nhO6j3oJPCIx`. Call `create_session` once and pass its `sessionId` on every call.
- Model: the default (`gpt-image-2.5-flare`). Size: `1920x1080` for backgrounds, `1024x1536` for one standing character, `1536x1024` for two characters.
- **Send 5–6 `generate_image` calls in parallel.** Download each `image.url` straight away (the links expire):
  `curl -fsSL -o img/<name>.png "<image.url>"`
- For a 10–12 minute episode, plan about **15–25 new images**:
  - 6–10 backgrounds
  - 6–12 character poses
  - 1–2 thumbnail bases
- **Reuse ep01 art freely** with `load_bg("../ep01-dating-game/img/bg_stage.png")`. ep01 has a stage, a city, an office, a world map and both main characters in several poses.

### Prompt templates (copy exactly; fill the `<…>`)

**Style prefix**, used in every prompt:
`Flat 2D cartoon animation style of a modern animated history explainer, clean bold dark outlines, flat colors with soft cel shading, slightly exaggerated proportions.`

**Character cut-out:**
`<STYLE PREFIX> Full body character standing, three-quarter view facing <left|right>, <pose and expression>: <CHARACTER FRAGMENT>. Isolated on a solid pure bright green (#00FF00) background, no shadow on the ground. No text, no words, no letters, no logos.`

**Background:**
`Flat 2D cartoon animation background in the style of a modern animated history explainer, clean bold outlines, flat colors with soft shading, <mood/palette>. <PLACE, side-on or wide view>. No people, no text, no words, no letters, no numbers, no logos.`

### Character fragments (word for word, so the characters always look the same)
- **MAN:** `a young man cartoon character with big expressive eyes, short messy dark brown hair, wearing a navy blue blazer over a white shirt and a red tie, brown trousers and brown shoes`
- **WOMAN:** `a young woman cartoon character with big expressive eyes, black hair in a high bun, wearing a red knee-length dress, gold hoop earrings and black flat shoes`
- **Historical figures:** describe the clothes of their era and one signature item. Never claim a figure is a portrait of a real person's actual face.
- Poses already made in ep01: `man_curious` (scratching his head), `man_shocked`, `woman_confident` (arms crossed), `woman_phone`, `professors`.

### Check the art
Key all the cut-outs, then look at a contact sheet with the Read tool:
```bash
cd video-studio/deeptime/epNN-slug/img && ~/venvs/render/bin/python -c "
import sys; sys.path.insert(0,'../../../tools'); from engine import key_green
import glob
for f in glob.glob('*.png'):
    if not f.startswith('bg_') and not f.endswith('_cut.png'): key_green(f).save(f[:-4]+'_cut.png')"
montage -background '#556' *_cut.png -tile 6x -geometry 300x400+4+4 /tmp/cuts.jpg
```
Regenerate any image with extra limbs, the wrong outfit, garbled text or a green fringe.

---

## 4. Voice (Fish Audio MCP)

1. **Check credits first:** `get_credit_balance`.
   - Cost is 1 credit per UTF-8 byte of text, tags included. A full 1,600-word episode costs about **9,000–10,000 credits**.
   - The free plan has about 7,000 and allows at most 500 bytes per call.
   - **If credits are short, stop and tell the user.** Never voice half an episode without asking.
2. **One `text_to_speech` call per line**, with `voice_id = fb7ec16ca51a45a5a4db881244d7990a` and `model = "drama-3"`.
   - Send 10–15 calls in parallel per message.
   - Keep each result's `audio_url` in order. **Never call it again for the same text just to download it**: that charges again.
3. Download the files and convert them (line numbers are 1-based):
   ```bash
   curl -fsSL -o audio/l$i.mp3 "<audio_url>" && ffmpeg -y -loglevel error -i audio/l$i.mp3 -ac 1 -ar 48000 audio/l$i.wav
   ```
4. **Check every line by transcribing it back.** faster-whisper's own file decoder is broken in this environment, so decode with ffmpeg first:
   ```bash
   mkdir -p /tmp/fa && for i in $(seq 1 N); do ffmpeg -y -loglevel error -i audio/l$i.wav -ar 16000 -ac 1 /tmp/fa/l$i.wav; done
   ~/venvs/render/bin/python -c "
   from faster_whisper import WhisperModel; import wave, numpy as np
   m=WhisperModel('base.en',device='cpu',compute_type='int8')
   for i in range(1,N+1):
       w=wave.open(f'/tmp/fa/l{i}.wav'); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
       print(i,'|',' '.join(s.text.strip() for s in m.transcribe(a)[0]))"
   ```
   - Digits ("1962") and spelling differences ("Gail") are fine.
   - Missing words, or a tag read aloud ("curious intrigued…"), are not. Re-voice only those lines.
5. Delete `audio/clean/` whenever you replace voice files. `episode.py` re-cleans voice files that are newer than their clean copies, but delete it anyway to be safe.

---

## 5. Animation: `epNN-slug/episode.py`

Copy `ep01-dating-game/episode.py` and keep its skeleton.

**1. Imports.** `sys.path` gets `..` (for `dta`) and `../../tools` (for `engine`). Then `import dta as D; from dta import *`, and set `D.SERIES_TAG = "GAME THEORY  ·  EP 2"`.

**2. Timeline.**
- `GAPS` = the pause after each line, by **0-based** index. Use 0.45 s by default.
- Use 0.7–1.0 s after a reveal, about 2.5 s before a new chapter (for a chapter card) and 3.5 s after the last line (end card).
- The title line gets about 4.6 s, which is where the logo sting plays: `STING = END(title_idx) + 0.9`.

**3. Helpers.**
- `seg(t, i)` is 0→1 progress through line i.
- `at(i, frac)` is the time at a fraction of line i. **Time every pop-up to the word it matches**: if the word comes at about 60% of the sentence, use `at(i, 0.6)`.

**4. One scene function per shot**, `def sc_name(t): … return f`. Build a frame like this:
- **Background:** `cam(BG[name], cx, cy, zoom)` with a slow push-in (`1.0 + 0.1*ease(u)`) or a pan (`lerp`).
  - `sepia(f, k)` for history scenes.
  - `darken(f, k, color)` and `spot(f, k)` for drama.
  - `blurred(f, 10, 0.55)` behind cards.
- **Characters:** `char(f, name, t, t_in, x, base_y, height, enter="left"|"right"|"bottom"|"pop", walk=…, phase=…)`.
  - They slide in with hops, land with a squash and then breathe.
  - Use a height of 700–800 px with base_y about 1020–1060. Give two characters different `phase` values.
- **Text:**
  - `gold_text(f, "TITLE", (W/2, 300), 150, a=…, scale=…, shine=…)` for titles.
  - `label(f, t, t_in, "TEXT", (x, y), bg, fg, size, angle)` for pop-up labels. Use 3 words or fewer, ALL CAPS, and tilt them ±3–6°.
- **Graphics:**
  - `BADGE[...]` plus `pop_img` for icons: heart, house, hourglass, coin, sword, land, scroll, players, strategy, payoff, info.
  - `chapter_card(t, t0, num, title)` for chapter cards, `payoff_matrix(...)` for 2×2 games, `progress_bar(...)` for the 37% rule and countdowns.
  - `person_glyph` plus `chalk_line` on `board(t)` for chalkboard diagrams.
  - `heart_pts` for hearts, `arrow` for up/down results, `medal_img()` for awards, `reel_strip` for slot machines.
  - Year counters: see `sc_years`.
- **Particles:** `motes(f, t)` on most scenes, for warmth.

**5. Wiring.**
- `SCENES = [(start_time, scene_fn, show_chrome), …]`. Start each scene about 0.1–0.3 s before its first line, so the 0.3 s crossfade finishes as the voice starts.
- `frame_at` crossfades scenes automatically and adds `chrome()`. Set `show_chrome` to False on titles and the sting.

**6. Pacing rules for long videos.** Viewers leave when the screen stops changing.
- **Change something at least every 4–6 seconds**: a new shot, a character entering, a label, a graphic step or a camera move.
- Never hold one still image for longer than one line, unless a diagram is being built on it.
- **Chapter cards:**
  - When: in the 2.5 s gap before each chapter.
  - Background: black, plus `motes`.
  - Text: `gold_text(f, "CHAPTER 3", …, 70)` with the chapter name below it in `cinzel(54, "Bold")`.
  - Sound: whoosh plus a soft boom.
- **Reuse ep01 scenes** when an idea comes back (the chalkboard, the stage, the casino). It's cheaper and it builds a visual language.
- **Framing:**
  - Keep faces clear of labels. Put labels at chest level beside the character, or above their head.
  - Keep text away from the top-left 380×90 px (series tag) and the bottom-right (watermark).

**7. Audio, in `build_audio()`.**
- Music: `music(TOTAL, mgain, dgain)`. `mgain(t)` turns the pizzicato on or off (off in serious or tense moments). `dgain(t)` sets the overall bed level (lower under the sting).
- **One sound effect for every visual event**, placed with `place(fx, clip, time)`:
  - `sfx("whoosh")` on every scene change
  - `sfx("pop")` on labels
  - `sfx("tick")` on counters
  - `sfx("coin")` on wins
  - `fx_heartbeat()` on emotional beats
  - `fx_riser()` before a big reveal, then `fx_hit()` on it
  - `fx_shimmer()` on gold titles and medals
  - `fx_chalk()` on chalk lines
  - `sfx("boom")` on big moments
- `finish_audio` masters to −14 LUFS. Don't remove it.

---

## 6. Preview → fix → render → check

```bash
cd video-studio
~/venvs/render/bin/python tools/preview.py deeptime/epNN-slug            # one frame per line -> _preview.jpg
~/venvs/render/bin/python tools/preview.py deeptime/epNN-slug 40 80      # just lines 40-80
```

**Read `_preview.jpg`, plus a few hand-picked frames** (`frame_at(t)` for the sting, titles and diagrams). Fix:
- Text missing or invisible. ep01 once had gold titles with alpha 0–1 instead of 0–255.
- Boxes (□) instead of symbols. The cause is a symbol inside an Anton label.
- Labels covering faces.
- Empty or frozen shots.

**Render** in the background. It takes about **3–4 seconds of render per second of video**, so an 11-minute episode takes about 35–45 minutes:
```bash
cd deeptime/epNN-slug && (nohup ~/venvs/render/bin/python episode.py > /tmp/render.log 2>&1; echo EXIT $? >> /tmp/render.log)   # run_in_background
```
Then wait with `until grep -qE "^done|EXIT|Traceback" /tmp/render.log; do sleep 15; done`.

**Checks:**
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 <video>.mp4            # 600-720 s
ffmpeg -i <video>.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -A14 Summary | grep -E "I:|Peak"   # I about -14..-16, Peak < -1
for t in 30 150 300 450 600; do ffmpeg -y -loglevel error -ss $t -i <video>.mp4 -frames:v 1 -vf scale=480:-1 /tmp/f$t.jpg; done
```
Look at those frames with the Read tool.

**Refactors:** if you change `dta.py`, save 10 reference frames first and compare pixels afterwards. The maximum difference must be 0 for ep01.

---

## 7. Thumbnail, title, description

- **Thumbnail:** generate a base with `model="gemini-3.1-flash-image"`:
  - Character close-up on the left with a strong emotion.
  - Dark gold-to-black gradient on the right.
  - Draw 2–4 huge words with `gold_text` or Anton, plus one red accent word. The channel's thumbnails use big bold text ("WHO WENT IN?", "WHY?").
  - Make 2 variants and recommend one.
- **Title:** 60 characters or fewer, curiosity first. Example: "Game Theory #1: The Math Behind Dating (Who Should Move First?)".
- **Description, in this order:**
  1. 2 hook lines
  2. A comment question
  3. Chapters with real times from `L(i)`: `python -c "import episode as e; print(int(e.L(14)//60), int(e.L(14)%60))"`
  4. Sources (from `script.md`)
  5. "Inspired by Professor Jiang Xueqin's Predictive History lectures."
  6. "Animated with AI-assisted artwork and narration."
  7. `#history #gametheory #documentary`
- Save it as `metadata.json`.

---

## 8. Save and deliver

```bash
cd /home/user/Portfolio && git add video-studio && git commit -m "Deep Time Academy EPNN: <title>" && git push -u origin <branch>
```
- Send the `.mp4` and thumbnails with `SendUserFile`.
- Tell the user the length, the credits used and what to check. Ask what to change.
- Edits: change only the lines or scenes asked about. Re-voice only changed lines (it costs credits), then re-render.

## 9. Pitfalls already hit

| Problem | Fix |
|---|---|
| Gold titles invisible | Layer alpha must be 0–255 (`* 255`) |
| □ boxes in labels | Anton has no ✗ ✓ ♥. Use words, or `sym()` text drawn separately |
| Label on a face | Move labels to chest level beside the character |
| `metadata_errors` error in faster-whisper | Decode to 16 kHz wav with ffmpeg and pass a numpy array |
| `?` intonation on a list | Use full stops in the script |
| Fish credits run out | Stop, tell the user the cost and the balance. Never re-call TTS just to re-download |
| Cinzel download blocked on GitHub | Already in the repo; mirror at `cdn.jsdelivr.net/gh/google/fonts@main/ofl/cinzel/` |
| `_scaled` NameError after editing dta | Module-level caches (`_scaled`, `_gold`, `_lab`) must stay in `dta.py` |
