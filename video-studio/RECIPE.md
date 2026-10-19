# RECIPE: How to Make One Episode, Step by Step

This file is written so **any assistant, including a smaller model, can make an episode by following it exactly**.
`PLAYBOOK.md` explains the *why* (style, story formula, publishing). This file is the *how*: exact commands, files and checks.
**Copy the newest episode (`episodes/ep05-grey-coat/`) as your template. It uses every feature below.**

---

## 0. Hard rules (never break these)

1. **Length:** every episode is **at least 3–4 minutes**. That's about 520–600 narration words in 55–65 lines.
2. **Format:** 16:9, 1920×1080, 30 fps, H.264 + AAC. No subtitles on the long video.
3. **Series parts (Part 2, Part 3…):**
   - Start with a **20–30 second recap**: 6–8 short lines beginning "Last time, …", shown with a "PREVIOUSLY" tag.
   - Then a black **title card** ("PART 2" / subtitle) during a 3-second gap.
   - End with "TO BE CONTINUED" or "THE END".
4. **House style is "slow, clean and explained"** (the channel owner asked for it after Part 2 v1):
   - **Hook first:** 4–5 lines showing the biggest moment, before any recap or setup ("This man saved your life… twenty years later you find out who he was").
   - **Pace:** voice with `KOKORO_SPEED=0.92`, and use **0.6 s** as the default gap (longer, 0.8–1.4 s, after reveals).
   - **Explain the twist out loud:** "Think about what that means…". Bring the host back with a card for any idea that could confuse viewers, and say the final reveal plainly ("It was you. It was always you.").
   - **Final line asks a question** ("Tell us what you think in the comments"), shown over an end card.
5. **The hero** is always the stick figure with the **blue-and-white striped nightcap**. **The host** always has black glasses and a red bow tie. Copy the prompt fragments in section 4 *exactly*.
5. **No text inside AI images.** All words (headlines, signs, cheques, counters) are drawn in code.
6. **Audio:** voice through `clean_voice`, mastered to −14 LUFS by `finish_audio`. These are already wired into the template, so don't remove them.
7. **Never commit `.mp4` files** (too big). Commit everything else. Send the video to the user as a file.
8. **Never paste API keys into chat or files.** Keys come from environment variables.

---

## 1. Repo map

```
video-studio/
  PLAYBOOK.md                 style bible, story formula, publishing (read once)
  RECIPE.md                   this file
  assets/fonts/Anton.ttf      the only display font
  assets/characters/          host_glasses_green.png, hero_nightcap_green.png (green screen cut-outs)
  tools/engine.py             ALL drawing/animation/audio helpers (API in section 6)
  tools/tts.py                narration: ElevenLabs → Kokoro → Piper
  tools/preview.py            contact sheet of one frame per line
  tools/publish_youtube.py    upload (private) / schedule
  tools/publish_facebook.py   post video or reel (draft by default)
  episodes/epNN-slug/
    lines.txt                 narration, ONE line = one audio clip = one timing slot
    episode.py                shots + sound + thumbnail + render (copy from ep05)
    metadata.json             title, description with chapters, tags
    img/                      scene images (.jpg), thumb_base.png
    audio/                    l1.wav … lN.wav (raw voice); audio/clean/ is generated
```

---

## 2. One-time setup in a fresh cloud session

The scratchpad is wiped between sessions. Put the environments anywhere outside the repo, e.g. `~/venvs`.

```bash
# Render environment (any Python 3.10+)
python3 -m venv ~/venvs/render
~/venvs/render/bin/pip install pillow numpy faster-whisper

# Voice environment: MUST be Python 3.12 (Kokoro's dependency spacy fails to build on 3.13)
python3.12 -m venv ~/venvs/voice
~/venvs/voice/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
~/venvs/voice/bin/pip install kokoro soundfile numpy
# First run downloads the Kokoro model + spaCy English model automatically (needs internet, about 1 min).

ffmpeg -version | head -1   # ffmpeg is preinstalled; the 'deesser' and 'loudnorm' filters are used
```

If `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` are set as environment secrets, `tts.py` uses ElevenLabs instead. That's the best quality, and it needs no voice environment.

---

## 3. Step-by-step for a new episode

### Step 1: Create the folder
```bash
cd video-studio
cp -r episodes/ep05-grey-coat episodes/ep06-<slug>
rm -rf episodes/ep06-<slug>/{audio,img,*.jpg,*.mp4} && mkdir -p episodes/ep06-<slug>/{audio,img}
```

### Step 2: Write `lines.txt`
- 55–65 lines, 520–600 words total. Kokoro speaks about 176 words a minute, and the gaps add about 20%.
- One sentence or a short group per line. **Each line becomes one shot slot**, so break lines where the picture should change.
- Write numbers the way they should be *spoken*: "five fifty nine", "six p.m.", "four to one". Kokoro reads digits badly.
- Structure: hook (2 lines) → "Here's how it started" or a recap → premise → 3 rules (host card, 4 lines) → escalating steps (each ends on a teaser line) → twist → final line.
- Part 2+: the first 6–8 lines are the recap ("Last time, …").
- No blank lines in the middle of the file.

### Step 3: Make the shot list
Write it as a comment block or table: for every line number (1-based), give the image, camera move, overlay (phone, card, message) and sound effect. Re-use images: one image can cover 2–5 lines with different camera moves. An episode needs about **12–18 new images**.

### Step 4: Generate the images (Figma AI)
Tools: `mcp__Figma__generate_image`, then `mcp__Figma__download_assets`.
- Use the existing Figma file `fileKey = mYCHq9ept7nhO6j3oJPCIx` ("Zombie Reel - Episode 1 frames"). No need to create a new one.
- Scenes: `width=1920, height=1080`. The default model is `gemini-3.1-flash-lite-image` (cheapest). Use `gemini-3.1-flash-image` only for the thumbnail base.
- You can send 5–6 `generate_image` calls in parallel.
- For each result `nodeId`, call `download_assets(fileKey, nodeId)` and **immediately** download `rawImages[0].url`, because the URLs expire within minutes:
  ```bash
  curl -sSL -o episodes/ep06-<slug>/img/<name>.jpg "<rawImages[0].url>"
  identify episodes/ep06-<slug>/img/<name>.jpg     # must print JPEG 1376x768 (or PNG); else re-download
  ```
- Review every image on a contact sheet before using it:
  ```bash
  cd episodes/ep06-<slug>/img && montage *.jpg -tile 4x -geometry 400x225+4+4 /tmp/contact.jpg
  ```
  Then look at `/tmp/contact.jpg` with the Read tool. Regenerate anything with the wrong hero design, stray text or extra limbs.
- **"Insufficient Figma AI credits":** the daily limit is used up. It resets at 00:00 UTC. Keep working: `episode.py` draws a labelled placeholder for any missing image, so you can finish the voice, code and preview, then add the art later.

### Step 5: Voice
```bash
~/venvs/voice/bin/python tools/tts.py episodes/ep06-<slug>            # all lines, about 10 s per line on CPU
~/venvs/voice/bin/python tools/tts.py episodes/ep06-<slug> --only 12  # redo one line
```
Default voice: `af_heart` (female, cleanest). For a male narrator: `KOKORO_VOICE=am_michael`. Keep the same voice for every part of a series.

**Check pronunciation** by transcribing every line back and comparing it with `lines.txt`:
```bash
~/venvs/render/bin/python - <<'EOF'
import wave, numpy as np
from faster_whisper import WhisperModel
ep = "episodes/ep06-<slug>"; m = WhisperModel("base.en", compute_type="int8")
for i, ref in enumerate(open(f"{ep}/lines.txt").read().split("\n"), 1):
    if not ref.strip(): continue
    w = wave.open(f"{ep}/audio/l{i}.wav"); sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)
    print(i, "|", " ".join(s.text.strip() for s in m.transcribe(a)[0]), "|", ref)
EOF
```

### Step 6: Write `episode.py` (edit the copied template)
Change only these parts:
1. **Docstring and title.**
2. **`GAPS`:** the pause after each line, keyed by 0-based line index.
   - 0.45 s is the default.
   - Use 0.6–1.0 after a big reveal and 1.5 for a "Silence." beat.
   - Use 3.2 for the title card after the recap, and 3.4 after the final line for the end card.
3. **`IMG` loading:** list your image names (files in `img/` without `.jpg`). Part 2+ can load Part 1 images through the `P1(...)` helper.
4. **Copy constants:** headlines, rules (`RULES` max 3 items, each 25 characters or fewer) and messages.
5. **`hud_state(t)`:** return `(left, right, step)` or `None`.
   - `left`/`right` are `(LABEL, value)`.
   - `step` is `(lit_dashes, time_lit)` for the 12-dash progress bar. Use `-9` as `time_lit` when the bar shouldn't flash.
6. **`frame_at(t)`:** an `if/elif` chain on `t < L(k)`, where `L(k)` is the start of line k (0-based).
   - Each branch builds `f` from `cam(IMG[name], cx, cy, zoom)`, then adds overlays.
   - Use `seg(t, i, j)` to get 0→1 progress through lines i..j and drive camera moves.
7. **`build_audio()`:** place sound effects with `place(fx, sfx("ping"), time)`. Set `gain` windows to drop the music for action or climax moments.
8. **`THUMB_TEXT`:** 2–3 variants of (small line, big line, filename).

**Framing rule:** a phone overlay sits on the right (`x=1240`) and covers about 30% of the width. When a phone is on screen, shift the camera so the subject sits in the **left 60%**: increase `cx` by 0.1–0.15 (e.g. `cam(img, 0.6, 0.5, z)`). Centred phones (`x=680`) only go over a blurred background (`blurred(f)`).

**Drawing text onto an image** (blank sign, cheque):
1. Make a grid overlay to find the coordinates in original-image pixels:
   ```bash
   convert img/x.jpg -resize 688x384 -fill none -stroke red -draw "..." grid.png
   ```
   That's half size, so multiply the coordinates by 2.
2. Call `text_on(original_img, (x, y), "TEXT", size, fill, angle)` *before* resizing (see `bridge` in ep05).

### Step 7: Preview (always, before the full render)
```bash
~/venvs/render/bin/python tools/preview.py episodes/ep06-<slug>          # -> episodes/ep06-<slug>/_preview.jpg
```
Open `_preview.jpg` with the Read tool and check every tile:
- No faces hidden behind the phone or card.
- Text is readable.
- No `[placeholder]` tiles are left.
- The counters make sense.

Fix the issues, then preview again. A preview takes about 1 minute.

### Step 8: Render
```bash
cd episodes/ep06-<slug> && nohup ~/venvs/render/bin/python episode.py > /tmp/render.log 2>&1 &
# wait: about 4 s of render per 1 s of video (a 4-minute episode takes about 16 minutes); "done …" appears in /tmp/render.log
```
Check the result:
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 <video>.mp4                  # 180-240 s
ffmpeg -i <video>.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak"   # I about -14..-15
for t in 20 90 160; do ffmpeg -v error -y -ss $t -i <video>.mp4 -frames:v 1 -vf scale=640:-1 /tmp/f_$t.png; done
```

### Step 9: Thumbnail and metadata
- `thumbnail()` runs inside `episode.py` and writes `thumbnail.jpg` + variants. Look at them.
- Make `metadata.json` (copy from ep04). Compute the chapter times from the real timeline:
  ```bash
  ~/venvs/render/bin/python -c "import sys; sys.path.insert(0,'episodes/ep06-<slug>'); import episode as e; [print(f'{int(e.L(i)//60)}:{int(e.L(i)%60):02d}', i+1) for i in (0,8,20,34)]"
  ```

### Step 10: Save and share
```bash
cd /home/user/Portfolio && git add video-studio && git commit -m "Add EP06 <title>" && git push -u origin <branch>
```
Then send the `.mp4` and thumbnails to the user with `SendUserFile`.

---

## 4. Image prompt templates (copy exactly; fill the `<…>`)

**HERO fragment:**
`stick figure character with a big round white head with a black outline, simple dot eyes, solid black thin body, wearing a blue-and-white striped nightcap with a white pom-pom`

**Full scene:**
`2D cartoon explainer animation style, clean bold black outlines, soft painterly shading, <mood/light>. <WHO is doing WHAT, WHERE>. <HERO fragment if he is in it>. No text, no words, no letters, no numbers.`

**Empty background:**
`2D cartoon explainer animation background, clean bold black outlines, soft painterly shading, <mood>. <PLACE, side-on view like a stage>. No people, no characters, no text, no words, no letters.`

**Character for cut-out:**
`Single cartoon character on a perfectly flat solid pure green (#00FF00) chroma key background, no shadows, no floor. Full body, <POSE>, facing <left/right>. <HERO fragment>. 2D explainer animation style, bold clean outlines. No text.`
Load it with `key_green(path)`.

**Thumbnail base** (model `gemini-3.1-flash-image`):
`… vibrant saturated colors, high contrast, thumbnail composition. Big close-up on the left half: <HERO fragment> with <strong emotion>. Right half: empty dark red to black gradient with light rays. No text.`

**Recurring cast:**
- **Man in the grey coat:** `a mysterious man in a long grey trench coat and a grey wide-brimmed hat, face hidden in shadow`
- **Girl:** `a little cartoon girl with pigtails and a yellow raincoat, holding a red balloon`
- **Old hero:** add `old, wrinkles, white bushy eyebrows, slightly hunched` to the HERO fragment.

---

## 5. Shot patterns (copy from ep04/ep05)

| Pattern | Code idea |
|---|---|
| Slow push-in | `cam(IMG[n], 0.5, 0.5, 1.0 + 0.2 * ease(seg(t, i, j)))` |
| Pan | `cam(IMG[n], lerp(0.4, 0.6, seg(t, i, j)), 0.5, 1.1)` |
| Impact | `cam(..., shake=20)` for about 0.6 s, a 0.12 s white frame, then `sfx("boom")` |
| Rewind or recap montage | pick the image by `int(u * len(list))`, apply `rgb_split(f)` for rewinds or `grade(f, 0.55, 0.9)` + `previously(f)` for recaps |
| Host + rules | `blurred(cam(...))` background, `host_in(f, HOST, t, L(k))`, `card(f, t, L(k)+0.5, RULES, [L(k+1), L(k+2), L(k+3)])`, one `sfx("pop")` per item |
| News headline | `place_phone(f, news_phone(date, [headline], 1, breaking=True), t, t_in)` + `sfx("ping")` at `t_in` |
| Text message | `place_phone(f, message_phone("ME", "MY NUMBER", text, typed_0_to_1, glow, t=t), t, t_in, x=680, y=60)` on a blurred background |
| Sent history | `sent_phone(contact, list_of_msgs, shown_float, draft)` |
| SEND button | `send_phone(t)` |
| Stamp | `stamp(f, t, t_in, "IT ALL CAME TRUE", (x, y))` |
| Floating label | `float_text(f, t, t_in, "+$10", (x, y))` |
| Title or end card | black `Image.new("RGBA", (W, H), (0, 0, 0, 255))` + `big_title(f, "PART 2", "SUBTITLE", alpha)` |
| Dread turn | `grade(f, 1 - 0.8*u, 1 - 0.3*u)` + `sfx("boom")`, music gain to 0 |

---

## 6. `tools/engine.py` API (signatures)

```
cam(img, cx, cy, zoom, shake=0)                -> RGBA frame. cx, cy in 0..1; zoom 1 = widest
load_bg(path), key_green(path)                 -> background image / keyed sprite (RGBA)
blurred(frame, radius=14, dim=0.5), grade(frame, sat, bright), rgb_split(frame, off, scan)
text_on(img, (x, y), text, size, fill, anchor="mm", angle=0)
hud(frame, t, (labelL, valL), (labelR, valR), step=(n_lit, t_lit))
host_in(frame, host, t, t_in);  card(frame, t, t_card, items, item_times, x=1060, y=300, w=780)
news_phone(date_line, headlines, shown, breaking=False, highlight=None|"date")
message_phone(contact, number, text, typed, header_glow=0, t=0)      # typed=0 shows "typing…" dots
sent_phone(contact, sent_list, shown, draft="", cracked=True);  send_phone(t, pressed=0)
place_phone(frame, phone_img, t, t_in, x=1240, y=70, scale=0.95, wobble=0, out_at=None)
stamp(frame, t, t_in, text, (x, y));  float_text(frame, t, t_in, text, (x, y), color, size, rise, life)
big_title(frame, text, sub=None, a=1.0)
ease(u), ease_out_back(u), lerp(a, b, u), clamp01(x)
Timeline(line_wavs, gaps) -> .L(i) start of line i, .end(i) end of speech, .total, .voice_track()
sfx(kind): "ping" "pop" "whoosh" "boom" "tick" "buzz" "screech" "flash" "coin"
music_bed(total, chords, sec_per_chord, level);  place(track, clip, t)
clean_voice(src, dst);  finish_audio(voice, music, fx, out_wav, tmp_dir);  render(frame_at, total, wav, mp4)
```

---

## 7. Pitfalls already hit (don't repeat them)

| Problem | Fix |
|---|---|
| `box offset can't be negative` in `cam()` | already fixed: `cam` limits the view to the image's 16:9 area. Use `load_bg()` for all backgrounds. |
| Kokoro install fails (spacy, Cython) | use a **Python 3.12** environment |
| Figma download gives a broken JPEG | the URL expired or the transfer was cut. Call `download_assets` again and re-curl, then check with `identify` |
| Garbled text in AI images | the prompt must end with "No text, no words, no letters". Put real text on with `text_on` |
| Phone covers the hero's face | shift the camera `cx` by +0.1–0.15, or move the phone to `x=680` over a blurred background |
| Digits read wrongly by the voice | spell numbers out in `lines.txt` |
| `pkill -f <pattern>` killed my own shell | never `pkill -f` with a pattern that appears in the same command line. Kill by PID from `pgrep` instead |
| `.gitignore` didn't match subfolders | use `**/audio/clean/` style patterns (already in `video-studio/.gitignore`) |
| Thumbnail text overlaps the phone | keep the big line 600 px wide or less (auto-shrunk in the template) and the phone at y ≥ 268 |
| Using brand names (iMessage, etc.) | use generic UI labels ("Text Message") |

---

## 8. Final checklist (tick every box before telling the user it's done)

- [ ] 3–4 minutes or more (`ffprobe`); Part 2+ starts with a recap and title card
- [ ] Every line transcribed back correctly (step 5 check)
- [ ] `_preview.jpg` reviewed: no hidden faces, no placeholders, readable text
- [ ] Loudness about −14 to −15 LUFS integrated
- [ ] Thumbnails generated and looked at
- [ ] `metadata.json` with real chapter times
- [ ] Committed and pushed (no `.mp4`), video + thumbnails sent to the user
