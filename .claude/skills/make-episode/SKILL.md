---
name: make-episode
description: Make a complete LunchBox Express animated story video (script → Figma AI images → narration → animated 16:9 render → thumbnails → YouTube/Facebook text). Use whenever the user asks to make, continue, remake or fix an episode, a part of a series, or a video in the channel's stick-figure "what if" style.
---

# Skill: make a LunchBox Express episode, end to end

This is the exact process behind "My Phone Showed Me the Future" (Parts 1 and 2). Follow the steps in order. **Don't skip the checks.** Every check exists because something went wrong once.

Everything lives in `video-studio/` in this repo:
- **Style bible:** `PLAYBOOK.md`
- **Engine reference:** `RECIPE.md` (function list in section 6)
- **Template to copy:** `episodes/ep05-grey-coat/`

---

## 0. What you need

| Thing | Where it comes from |
|---|---|
| **Figma connector** with AI image credits | claude.ai connectors (Figma). It provides `generate_image` and `download_assets`. **Daily credit limit:** about 20–25 images, reset at 00:00 UTC |
| Figma file to put images in | Reuse `fileKey = mYCHq9ept7nhO6j3oJPCIx`. To make a new one, call `whoami` for the `planKey`, then `create_new_file(fileName, planKey, editorType="design")` |
| Python 3.12 environment with Kokoro (voice) | step 1 |
| Python environment with Pillow, numpy and faster-whisper (render and checks) | step 1 |
| ffmpeg | preinstalled in Claude cloud sessions |
| Optional: ElevenLabs | env secrets `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`. If set, `tools/tts.py` uses it automatically |

---

## 1. One-time setup (every new cloud session)

```bash
python3 -m venv ~/venvs/render && ~/venvs/render/bin/pip install pillow numpy faster-whisper
python3.12 -m venv ~/venvs/voice
~/venvs/voice/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
~/venvs/voice/bin/pip install kokoro soundfile numpy        # MUST be Python 3.12 (spacy won't build on 3.13)
```

---

## 2. Script → `episodes/epNN-slug/lines.txt`

Start the folder from the template:

```bash
cd video-studio && cp -r episodes/ep05-grey-coat episodes/epNN-slug
rm -rf episodes/epNN-slug/{audio,img,*.jpg,*.mp4,_preview.jpg} && mkdir -p episodes/epNN-slug/{audio,img}
```

**Rules for `lines.txt`:**
- **One line = one sentence or a short group = one voice clip = one timing slot.** Break the line wherever the picture should change.
- **Length:** 3–5 minutes per episode, which is about 65–100 lines (550–850 words).
- **House style ("slow, clean, explained"):**
  1. **Hook first** (4–5 lines): the most dramatic moment, before anything else.
  2. **Part 2+:** a recap ("Last time…", 8–10 lines), then a title card.
  3. The story itself, in short sentences.
  4. Explain anything confusing out loud ("Think about what that means…"), and bring in the host card for it.
  5. Say the big reveal plainly.
  6. The last line is a comment question ("What would you do…? Tell us in the comments."), or "To be continued." on a cliffhanger part.
- **If the user gives their own script,** use it word for word. Only split it into lines and spell out numbers.
- **Spell numbers the way they're spoken:** "five fifty nine", "six p.m.", "forty hours times eight dollars". Kokoro misreads digits.
- **Use brand names** only if the user's script has them. Otherwise keep them generic.
- No blank lines in the middle of the file.

---

## 3. Images in Figma (the "graphics" step)

### 3.1 Make a shot list first
Go through `lines.txt` and give every group of 2–5 lines a picture. Re-use pictures with different camera moves. An episode needs about **12–18 new images** plus 1 thumbnail base.

### 3.2 Character bible: paste the fragment into every prompt the character is in
- **HERO** (nightcap series): `a stick figure character with a big round white head with a black outline, simple dot eyes, solid black thin body, wearing a blue-and-white striped nightcap with a white pom-pom`
- **HOST** (already cut out, at `assets/characters/host_glasses_green.png`): glasses and a red bow tie. No need to generate it.
- **New series character:** invent **one signature item** (a cap, scarf, glasses or colour) and write a fixed fragment like the HERO one. Use that exact fragment in every prompt, word for word, so the character looks the same in every picture.
- **Older or younger versions:** add `OLD, wrinkles, white bushy eyebrows, slightly hunched`, or `young`.

### 3.3 Prompt templates (copy exactly; fill the `<…>`)

**Scene:**
```
2D cartoon explainer animation style, clean bold black outlines, soft painterly shading, <light / mood>.
<WHO is doing WHAT, WHERE, camera angle>. <character fragment>. No text, no words, no letters, no numbers, no logos.
```
**Empty background:**
```
2D cartoon explainer animation background, clean bold black outlines, soft painterly shading, <mood>.
<PLACE, side-on view>. No people, no text, no words, no letters, no numbers, blank signs.
```
**Thumbnail base** (use `model="gemini-3.1-flash-image"`, better quality):
```
2D cartoon explainer animation style, … vibrant saturated colors, high contrast, thumbnail composition.
Big close-up on the left half of the frame: <character fragment> with <strong emotion>, <holding the key object>.
The right half is an empty dark <colour> to black gradient background with light rays. No text, no words, no letters.
```

### 3.4 Call the tools
1. Call `generate_image` with `fileKey`, `prompt`, `width=1920` and `height=1080`. The model defaults to `gemini-3.1-flash-lite-image`, the cheapest.
   - Send **5–6 calls in parallel** in one message.
   - The result has a `nodeId`, and sometimes an `image.url` directly.
2. Get the file:
   - If the result has `image.url`, download it straight away.
   - Otherwise call `download_assets(fileKey, nodeId)` and take `rawImages[0].url`.
3. **Download immediately**, because the URLs expire:
   ```bash
   curl -fsSL -o episodes/epNN-slug/img/<name>.jpg "<url>" && identify episodes/epNN-slug/img/<name>.jpg
   ```
   `identify` must print `JPEG 1376x768`. Save the thumbnail base as `img/thumb_base.png`.
4. **Review everything:**
   ```bash
   montage episodes/epNN-slug/img/*.jpg -tile 4x -geometry 400x225+4+4 /tmp/contact.jpg
   ```
   Open it with the Read tool. Regenerate any picture with the wrong character design, garbled text or extra limbs.

### 3.5 Rules
- **Never ask the AI to draw readable text.** Signs, notes, cheques and screens should be **blank**. Draw the real text in code with `text_on(img, (x, y), "TEXT", size, fill, angle)` on the original image, before resizing.
- **Finding text coordinates:**
  1. Make a grid overlay: `convert x.jpg -resize 688x384 -fill none -stroke red -draw "line …" grid.png`.
  2. Read the coordinates from it and multiply by 2.
- **"Insufficient Figma AI credits":** wait for 00:00 UTC. Missing images render as labelled placeholders, so you can keep going with the voice, code and preview. Schedule a reminder (`send_later`) to finish once credits reset.

---

## 4. Voice

```bash
cd video-studio
KOKORO_SPEED=0.92 ~/venvs/voice/bin/python tools/tts.py episodes/epNN-slug           # all lines (≈10 s each)
KOKORO_SPEED=0.92 ~/venvs/voice/bin/python tools/tts.py episodes/epNN-slug --only 12 # redo one line
```
- **Voice:** `af_heart` by default. Keep the same voice for a whole series.
- **Engine order:** ElevenLabs if its key is set, otherwise Kokoro, otherwise Piper.
- **Check every line by transcribing it back.** The script is in `RECIPE.md` step 5. Numbers coming back as digits ("559") are fine. Missing *words* are not.
- **Editing only some lines:** delete just those `audio/lN.wav` files, then voice them again. Careful: `rm audio/l8*.wav` also deletes l8, l80–l89. Delete exact names instead.

---

## 5. Animate → `episodes/epNN-slug/episode.py`

Edit the copied template. Its sections, top to bottom:

1. **Voice cleaning + timeline:** no changes needed. Each line is cleaned (high-pass, de-ess, compression, −18 LUFS).
2. **`GAPS`:** the pause after each line, keyed by **0-based** line index.
   - Default **0.6 s**.
   - 0.8–1.4 s after reveals, 0.1–0.3 s in fast action.
   - 1.6 s for a "Silence." beat (with a black screen).
   - 2.8–3.2 s for a title card.
   - 3–3.5 s after the last line, for the end card.
3. **`IMG`:** load every image name with `load_bg()`. Earlier-episode images load through `P1(...)`. Text baked onto an image (sign, note) uses `text_on` first.
4. **Copy constants:** headlines, card items (3 or fewer, each about 25 characters or fewer, ALL CAPS) and messages.
5. **`hud_state(t)`:** returns `(("LEFT LABEL", value), ("RIGHT LABEL", value), (dashes_lit, time_lit))` or `None`.
   - Hide it on title cards, host scenes and black frames.
   - Values can animate with `ease(seg(t, i, j))`.
6. **`frame_at(t)`:** one `elif t < L(k):` block per shot, where `L(k)` is the start of line k (0-based).
   - **Background:** `cam(IMG[name], cx, cy, zoom, shake)`. Use a push-in `1.0 + 0.2*ease(seg(t,i,j))`, a pan via `lerp(cx0, cx1, u)`, and `shake` for impacts.
   - **Phone:** `news_phone(…)`, `message_phone(…)`, `sent_phone(…)` or `send_phone(t)`, placed with `place_phone(f, ph, t, t_in, x, y)`.
   - **Host explainer:** `blurred(cam(…))` background + `host_in(f, HOST, t, L(k))` + `card(f, t, t_in, items, times)`.
   - **Labels:** `float_text(f, t, t_in, "TEXT", (x, y))` and `stamp(f, t, t_in, "TEXT", (x, y))`.
   - **Title or end card:** `black()` + `big_title(f, "TITLE", "SUBTITLE", alpha)`.
   - **Framing rule:** a phone at the right (`x=1240`) covers about 30% of the screen. Shift `cx` by +0.1–0.15 so faces stay in the left 60%. If the face is on the right, put the phone at `x=140`. A centred phone (`x=680`) only goes over a blurred background.
7. **`build_audio()`:**
   - **Music:** `music_bed(TOTAL, chords, 4.0–4.5, 0.06)`. Shape it with a `gain` array: 0 in action scenes, low on title cards.
   - **Sound effects:** `place(fx, sfx("ping" | "pop" | "whoosh" | "boom" | "tick" | "buzz" | "screech" | "flash" | "coin"), time)`. Put one sound on every phone pop-in, card item, impact and reveal.
   - `finish_audio(...)` masters to −14 LUFS. Don't remove it.
8. **`THUMB_TEXT`:** 2 variants of (small line, big line, filename). The big line should be 600 px wide or less (it auto-shrinks), and add a corner badge (PART 2 / FINALE).

---

## 6. Preview → fix → render → check

```bash
~/venvs/render/bin/python tools/preview.py episodes/epNN-slug            # one frame per line → _preview.jpg
~/venvs/render/bin/python tools/preview.py episodes/epNN-slug 60 101     # just lines 60–101
```

**Read `_preview.jpg` and fix:**
- Faces hidden behind a phone or card.
- Unreadable text.
- `[placeholder]` tiles.
- Cards sitting empty for too long.
- Counters that don't make sense.

**Render** (about 4 s of render per 1 s of video; a 7-minute episode takes about 30 minutes):

```bash
cd episodes/epNN-slug && nohup ~/venvs/render/bin/python episode.py > /tmp/render.log 2>&1 &
# wait with a background `until grep -q "^done" /tmp/render.log; do sleep 15; done`
```

**Check:**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 <video>.mp4
ffmpeg -i <video>.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -A14 Summary | grep -E "I:|Peak"   # aim I ≈ -14..-15, Peak < -1
```
Also pull 3–4 frames with `ffmpeg -ss T -frames:v 1` and look at them.

---

## 7. Thumbnail, title, description

- **Thumbnails** are made inside `episode.py` (`thumbnail()`). Look at both and recommend one.
- **Title:** 60 characters or fewer, first person, curiosity plus danger. For example: "My Phone Showed Me the Future… Then It Showed MY Name".
- **`metadata.json` description, in this order:**
  1. 2 hook lines.
  2. A question for comments.
  3. "▶ Watch Part 1: [link]" (for Part 2+).
  4. Chapters with real times, from `L(i)`:
     ```bash
     python -c "import sys; sys.path.insert(0,'episodes/epNN-slug'); import episode as e; print(int(e.L(20)//60), int(e.L(20)%60))"
     ```
  5. 🍱 LunchBox Express line.
  6. "Animated with AI-assisted artwork and narration."
  7. `#whatif #animation #story`
- **Tags:** 10–15, only ones that match the video. Channel keywords and text are in `assets/brand/descriptions.md`.

---

## 8. Save and deliver

```bash
cd /home/user/Portfolio && git add video-studio && git commit -m "Add EPNN <title>" && git push -u origin <branch>
```
- `.mp4` files are git-ignored because they're too big. Send the video and thumbnails to the user with `SendUserFile`, and tell them to download the video.
- **Never paste API keys into chat or files.**

---

## 9. Pitfalls already hit

| Problem | Fix |
|---|---|
| `box offset can't be negative` | always load backgrounds with `load_bg()` (already fixed in `cam`) |
| Kokoro install fails | use Python **3.12** |
| Broken or partial JPEG from Figma | the URL expired. Download again and check with `identify` |
| Garbled text in pictures | prompts must end with "No text, no words, no letters, no numbers, no logos". Draw text with `text_on` |
| Phone covers the face | shift `cx`, or move the phone to the other side |
| Wrong numbers read aloud | spell them out in `lines.txt` |
| `pkill -f pattern` killed the shell | kill by PID instead |
| Credits run out mid-episode | placeholders + `send_later` reminder at 00:06 UTC |
| Thumbnail text overlaps the phone | keep the big text 600 px wide or less, and the phone low |
