# Video Studio Playbook

How we make every episode, from idea to posted on YouTube and Facebook. If something isn't written here, it isn't part of the process yet.

**The show:** *What If…?*, animated "what if" stories told to the viewer as "you", starring a stick-figure hero in a striped nightcap.
**Main format:** 16:9 YouTube video, 8–12 min.
**Spin-off format:** 9:16 Shorts / Reels, 20–60 s, cut from each episode.

---

## 1. The pipeline at a glance

```
 IDEA ──► 1. SCRIPT ──► 2. VOICE ──► 3. GRAPHICS ──► 4. RENDER ──► 5. PACKAGE ──► 6. PUBLISH
          Claude        ElevenLabs    Figma AI        render.py     thumbnail +     YouTube API
          lines.txt     audio/l*.wav  img/*.jpg/png   episode.mp4   metadata.json   Facebook Graph API
```

| Step | Tool | Input | Output | Who |
|---|---|---|---|---|
| 1 Script | Claude | title + premise | `lines.txt` (one narration line per row) + shot list | Claude writes, you approve |
| 2 Voice | ElevenLabs (`tools/tts.py`) | `lines.txt` | `audio/l1.wav …` + timing JSON | automatic |
| 3 Graphics | Figma AI `generate_image` | prompts from the shot list | backgrounds `.jpg`, characters on green `.png` | Claude, you approve |
| 4 Render | Python + ffmpeg (`render.py`) | audio + images | `episode.mp4` 1920×1080 30fps | automatic |
| 5 Package | Claude | episode | `thumbnail.jpg`, `metadata.json`, 9:16 reel cut | Claude, you approve |
| 6 Publish | `tools/publish_youtube.py`, `tools/publish_facebook.py` | metadata + video | private/draft uploads, then go live | you hit go |

Folder layout:

```
video-studio/
  PLAYBOOK.md                 ← this file
  assets/fonts/Anton.ttf      ← the only font we use
  assets/characters/          ← master character sheets (green background)
  tools/tts.py                ← step 2
  tools/publish_youtube.py    ← step 6
  tools/publish_facebook.py   ← step 6
  episodes/ep01-never-sleep/
    lines.txt  render.py  metadata.json  img/  audio/
```

---

## 2. Style bible

### 2.1 Look
- **Backgrounds:** painted 2D cartoon scenes with bold clean black outlines and soft painterly shading. Bright, warm colours in normal life, cold blues at night, desaturated greys in sad or late-story moments.
- **Characters:** flat stick figures with a big round white head, a thick black outline, dot eyes and a solid black stick body. They are always cut-outs: drawn separately on green, keyed out, then moved over the background.
- **Rule:** the background can be detailed, but the characters stay simple. That contrast is the whole look.

### 2.2 Cast
| Character | Look | Job | Prompt fragment |
|---|---|---|---|
| **Hero ("you")** | stick figure, blue-and-white striped nightcap with white pom-pom | lives the story | `stick figure with a big round white head with a black outline, simple dot eyes, solid black thin body, arms and legs, wearing a blue-and-white striped nightcap with a white pom-pom` |
| **Host** | stick figure, thick black rectangular glasses, red bow tie, smirk | explains rules and numbers to camera | `narrator host stick figure with a big round white head with a black outline, thick black-rimmed rectangular glasses, a red bow tie, confident knowing smirk, solid black thin body` |
| **Extras** | simple coloured cartoon people, no stick bodies | crowds, family, officials | `simple cartoon townspeople, rounded shapes, muted colours` |

The nightcap is the hero's signature. It appears in every frame he's in, including the thumbnail. **Never copy another channel's character** (the pink-beanie / sunglasses pair from the reference video is theirs).

### 2.3 On-screen info (HUD)
Shown in every story shot, but not on the host card shots or the end.

| Position | Content | Style |
|---|---|---|
| top-left | `HOURS AWAKE` (the episode's main counter) + big number | label Anton 26px, number Anton 54px, white with 3px black outline |
| top-centre | 12-dash progress bar, one dash per step | lit = `#FFCC00`, unlit = `#5A5A5A`, a new dash flashes white for 0.5 s |
| top-right | a second stat that gets worse (`ENERGY`, `FRIENDS LEFT`, `SANITY`…) | same style as top-left, right-aligned |

Each episode picks its own two counters. See the episode list in section 9.

### 2.4 Info card (the host's "rules" box)
- White rounded rectangle, 6px black border, 26px corner radius, on the right half of the screen.
- Numbers in red `#DC2828`, text in near-black, Anton 62px, ALL CAPS, max 4 items.
- Pops in at 60% → 100% scale with a slight overshoot. Each item lands with a "pop" sound **on the word the narrator says**.
- Behind it, the current scene is blurred (radius 14) and darkened to 50%.

### 2.5 Type
- Font: **Anton** only (`assets/fonts/Anton.ttf`, free licence).
- ALL CAPS on screen. No captions on the 16:9 video (the reference has none). Shorts/Reels get big centred captions at 96px with a 6px black outline.

### 2.6 Colour palette
| Token | Hex | Use |
|---|---|---|
| yellow | `#FFCC00` | progress, highlights |
| red | `#DC2828` | card numbers, danger |
| night | `#1B2A4A` | night scenes, cold tones |
| paper | `#FFFFFF` | heads, cards |
| ink | `#000000` | outlines, bodies |

### 2.7 Motion rules
| Move | When | Settings |
|---|---|---|
| Slow push-in | any held shot | zoom 1.00 → 1.10 over the shot |
| Pan | establishing / walking shots | 25% of image width per shot |
| Fast push | reveal or dread line | zoom 1.00 → 1.45 |
| Character walk | hero moving | `abs(sin)` bounce 22px + ±4° sway at 9 rad/s, soft ellipse shadow |
| Host entrance | each host segment | slides in from the left with an overshoot in 0.45 s, idle bob 6px |
| Rewind montage | cold open → "here's how it started" | 5–10 shots at about 0.2 s each, RGB split 14px + scanlines, counter rolls back |
| Dread turn | last line of a step | colour drains to 15%, brightness to 55%, push-in, low boom |
| Hit / impact | something bad happens | 1–3 frames of black + screen shake 8px |
| Cut length | always | average shot about 4 s. Never hold an image more than 8 s without a move or a cut |

### 2.8 Sound
- **Voice:** ElevenLabs, one consistent narrator voice per channel. Calm, slightly wry, mid-pace. See section 4.
- **Music:** a soft pad under the voice at about −28 dB. It ducks out completely on dread lines. Only ever use our own synth pads or properly licensed music (YouTube Audio Library is safe).
- **Sound effects:** pop (card items), whoosh (rewind), low boom (cliffhangers, cut to black). Already built into `render.py`.
- **Loudness:** final mix averages about −16 to −18 dB with peaks no higher than −1 dB.

---

## 3. Step 1: Script

### 3.1 The story formula (copy this every time)
1. **Cold open hook (0:00–0:10).** Show the end state. *"This is you, after ten years without a single minute of sleep."*
2. **Rewind (0:10–0:12).** *"Here's how it started."* Montage plus the counter rolling back.
3. **Premise (0:12–0:25).** The everyday moment it begins. Keep it physical and specific.
4. **Rules (0:25–0:45).** The host and card set out 3–4 rules. The last rule is always the trap (*"and you can never switch it off"*).
5. **The ladder (0:45 to the end).** 12 steps, each about 10× bigger than the last (hour → day → week → year → decade…). Every step:
   - starts with the counter: *"Hour 24."*
   - shows 3–4 concrete, fun or awful consequences in short lines
   - includes one real fact or number (sourced, and checked before recording)
   - **ends on a teaser** that takes something away: *"It's the last time that's true."*
6. **Ending (last 30 s).** Something quiet and emotional, then one final twist line. Then a hard cut to black.

### 3.1b Length and series rules (decided with the channel owner)
- **Every episode runs at least 3–4 minutes** (about 520–600 words). Stretch the middle with more escalation steps, not padding.
- **Part 2, 3…** open with a quick **recap** (6–8 lines, about 25 s, "Last time…", with a PREVIOUSLY tag), then a title card.
- Exact production steps for any assistant are in **`RECIPE.md`**.

### 3.2 Writing rules
- Talk to the viewer as "you", in the present tense.
- Sentences of 12 words or fewer. Three short lines beat one long one.
- About 170 words per minute, so a 10-minute episode is about 1,700 words and a 20 s short about 55.
- One idea per line, and one image per line or two.
- Numbers must be real or clearly part of the fiction. Facts get a source in the shot list.
- Ban list: "imagine if", "let's dive in", "in this video", "smash that like".

### 3.3 Files Claude produces
- `lines.txt`: one narration line per row. **Each row becomes one audio clip and one timing slot.**
- `shotlist.md`: for every line, the scene/background, characters and pose, camera move, HUD values, card text and sound effect.

Example (from ep01):
```
lines.txt                                         shot
This is you, after ten years without ...          closeup.jpg  push-in   HOURS 87,600  ENERGY 3%
Here's how it started.                            montage      rewind    counter rolls 87,600 → 0
One night, you just can't fall asleep. ...        bed.jpg      fast push HOURS 0 → 7
From tonight, there are three rules.              host + card (blur bed)
You never get tired.                              card item 1  pop
You never dream.                                  card item 2  pop
And you can never switch it off.                  card item 3  pop
Day one feels like a superpower.                  street.jpg + hero walk   step 1 lights up
It won't stay that way.                           dread turn + boom → black
```

**Prompt to give Claude:** *"Write episode N of What If…? using PLAYBOOK.md section 3: '<title>'. Give me lines.txt and shotlist.md."*

---

## 4. Step 2: Voice (ElevenLabs)

**Setup (once):**
1. Get an ElevenLabs plan. Creator tier or above gives a commercial licence and enough characters: a 10-minute episode is about 10k characters.
2. In the **Voice Library**, pick one narrator voice. Look for a male or female voice tagged narrative or storytelling, calm, with an American accent. Copy its **Voice ID**.
3. Add these as **environment secrets**: open the cloud environment menu in the session title bar, click **Edit**, then add them under Network secrets or as environment variables. **Never paste keys into the chat.**
   - `ELEVENLABS_API_KEY`
   - `ELEVENLABS_VOICE_ID`
   - optional: `ELEVENLABS_MODEL_ID` (default `eleven_multilingual_v2`)
4. Allow outbound network to `api.elevenlabs.io` in the environment's network settings.

**Run:**
```bash
python tools/tts.py episodes/ep02-...            # all lines
python tools/tts.py episodes/ep02-... --only 7   # redo one line
```
- Each line is sent with the lines around it (`previous_text`/`next_text`), so the tone flows naturally from one line to the next.
- Voice settings live in `tools/tts.py`: stability 0.45, similarity 0.8, style 0.25, speed 1.05. Lower the stability if it sounds flat. Raise it if the voice wobbles between lines.
- `audio/lN.align.json` holds a timing for every character, which lets cards and captions land on exact words.
- With no key set, it uses **Kokoro**, a free offline voice that sounds natural. The default voice is `af_heart`. Set `KOKORO_VOICE=am_michael` for a male narrator. It needs a Python 3.12 environment with `pip install torch kokoro soundfile`. If Kokoro isn't installed either, it falls back to Piper (robotic, drafts only).
- **Clean audio, done automatically by `tools/engine.py`:**
  - each line gets a high-pass at 75 Hz, a de-esser and gentle compression, then is normalised to −18 LUFS
  - the music sits on soft sine pads and dips under the voice
  - sound effects are synthesised cleanly
  - the final master is −14 LUFS with true peak at −1.5 dB, which is YouTube's standard

---

## 5. Step 3: Graphics

### 5.1 What each episode needs
| Asset | Count (10-min ep) | Format |
|---|---|---|
| Backgrounds (no characters) | 15–25 | 16:9, `.jpg` |
| Full illustrated shots (close-ups, crowds, complex action) | 20–40 | 16:9, `.jpg` |
| Character poses on green | 6–12 (walk, point, shocked, sad, happy, sitting…) | square `.png` |

Reuse the poses from `assets/characters/` whenever possible. New poses get added there.

### 5.2 Prompt templates
**Background:**
```
2D cartoon explainer animation background, clean bold black outlines, soft painterly shading,
<mood colours>. <PLACE, side-on view like a stage, flat ground across the lower third>.
No people, no characters, no text, no words, no letters.
```
**Character on green (for cut-out animation):**
```
Single cartoon character on a perfectly flat solid pure green (#00FF00) chroma key background,
no shadows, no floor. Full body, <POSE>, facing <left/right>. <HERO or HOST fragment from 2.2>.
2D explainer animation style, bold clean outlines. No text.
```
**Full illustrated shot:**
```
2D cartoon explainer animation style, clean bold black outlines, soft painterly shading, <mood>.
<SHOT: who, doing what, where>. <HERO fragment>. No text, no words, no letters, no numbers.
```

### 5.3 Rules
- **Always** end with "no text, no words, no letters". The model draws garbled text otherwise. Real text goes in the HUD and cards.
- Request 1920×1080 for scenes and 1024×1024 for characters.
- The default model is `gemini-3.1-flash-lite-image`, the cheapest. Use `gemini-3.1-flash-image` for hero close-ups and thumbnails. Every image costs Figma AI credits.
- Review a contact sheet before rendering. Redo any image with a wrong character design, extra limbs or text.
- Upgrade path for consistency: Figma Weave models such as Nano Banana accept a **reference image** of the hero, which keeps him identical between shots.

---

## 6. Step 4: Render

> **New episodes use `tools/engine.py` + `episodes/<ep>/episode.py`** (see `ep04-tomorrows-news`).
>
> **What the engine provides:** shared building blocks for the camera, the cut-out characters, the on-screen counters, the host and card, a phone news screen (`news_phone`), a text-message screen (`message_phone`), stamps, floating text, a sound-effects library and clean audio mastering.
>
> **What the episode file holds:** only the shots, keyed to line numbers, plus the thumbnail. Run `python episodes/<ep>/episode.py`.
>
> The older `render.py` below is what ep01 used.

`episodes/<ep>/render.py` is a frame-by-frame compositor: Python, Pillow and numpy, piped into ffmpeg.
- **Timeline:** each line's start time comes from its audio length plus the `GAPS` list, so editing a line re-times everything after it automatically.
- **Scene functions:** `frame_at(t)` picks the scene by time. The building blocks are:
  - `cam()`: push, pan or shake on a background
  - character compositing with bounce, sway and shadow
  - host + `card()`
  - the rewind montage
  - the dread turn
  - `hud()`
- **Audio:** the voice, synth pad, whoosh, pops and booms are mixed in `build_audio()`.

**Make a new episode:**
1. Copy `episodes/ep01-never-sleep/` to `episodes/epNN-<slug>/`.
2. Drop in the new `lines.txt`, `audio/`, `img/`.
3. Edit the scene blocks in `frame_at()` to match the shot list (Claude does this), plus `RULES` and the HUD labels.
4. `python episodes/epNN-<slug>/render.py` takes about 3.5 s of render per 1 s of video. A 10-minute episode takes about 35 minutes.

**9:16 Reel cut:** reuse the same scenes. Crop to the centre and put the HUD in the top band and captions in the bottom band, like the ep1 zombie format (`build.py` pattern). Cut a 30–60 s run, usually the cold open plus step 1.

---

## 7. Step 5: Package

**Thumbnail (1280×720):**
- The hero's face, huge and expressive, on one side.
- One big number or object on the other side, such as `87,600 HOURS`.
- 3–5 words at most, Anton, yellow and white with a black outline. The thumbnail text should **not** repeat the title.
- High contrast, readable at phone size.

**Title:**
- Always "What If You …?", 60 characters or fewer.

**Description:**
- 2 lines of hook.
- Then the line "Animated with AI-assisted artwork and narration."
- Then chapters (`0:00 Hook`, `0:45 Hour 1` …).
- Then 3 hashtags.

**metadata.json:**

```json
{ "video": "...mp4", "reel_video": "...mp4", "thumbnail": "thumbnail.jpg",
  "title": "...", "description": "...", "reel_caption": "...", "tags": [...], "category_id": "27" }
```

---

## 8. Step 6: Publish

### 8.1 YouTube (once)
1. Go to Google Cloud Console and create a project, then enable **YouTube Data API v3**.
2. Under OAuth consent screen, choose External, add yourself as a test user, then **publish the app**. While it stays in testing, the refresh token expires after 7 days.
3. Under Credentials, create an **OAuth client ID** of type "Desktop app" and download `client_secret.json`.
4. On your own computer, run `pip install google-api-python-client google-auth-oauthlib` then `python tools/publish_youtube.py --auth client_secret.json`. Sign in with the channel's account.
5. Save `YT_CLIENT_ID`, `YT_CLIENT_SECRET` and `YT_REFRESH_TOKEN` as environment secrets.
6. Allow network access to `oauth2.googleapis.com` and `www.googleapis.com`.

**Quota:** about 1,600 units per upload against 10,000 per day by default, so roughly 6 uploads a day is plenty.

**Per episode:**

```bash
python tools/publish_youtube.py episodes/ep02-...                                     # private, you review
python tools/publish_youtube.py episodes/ep02-... --publish-at 2026-10-24T15:00:00Z   # scheduled
```
After the upload, set **Altered or synthetic content** in YouTube Studio if a scene looks realistic. Cartoons usually don't need it. Then add end screens and cards.

### 8.2 Facebook (once)
1. You need a **Facebook Page**, which can't be a personal profile, plus a Meta developer app (developers.facebook.com) of type Business.
2. In Graph API Explorer, get a **Page access token** with `pages_manage_posts`, `pages_read_engagement` and `publish_video`. Swap it for a long-lived token.
3. Save `FB_PAGE_ID` and `FB_PAGE_TOKEN` as environment secrets.
4. Allow network access to `graph.facebook.com`, `graph-video.facebook.com` and `rupload.facebook.com`.

**Per episode:**

```bash
python tools/publish_facebook.py episodes/ep02-...           # full video as unpublished draft
python tools/publish_facebook.py episodes/ep02-... --reel    # 9:16 reel as draft
python tools/publish_facebook.py episodes/ep02-... --live    # post now
```

> Both publish scripts haven't been run against real accounts yet. The first upload is a test: keep it private or draft and check it before going live.

### 8.3 Platform rules that protect the channel
- **YouTube monetisation** rejects "mass-produced or repetitive" content. Every episode needs an original script, a new story and real variety. Never upload templated filler.
- Label AI use: put the line in the description, and set the YouTube synthetic-content flag when something looks real.
- Only use music and sounds we made or licensed. Never copy another channel's characters, titles or scripts.
- Facts in scripts get checked. A wrong number in a "science-y" video kills trust.

### 8.4 Schedule
- **YouTube long-form:** 1 per week, same day and time (e.g. Saturday 15:00 UTC).
- **Shorts / Reels:** 3 per week from each episode (cold open, best step, ending). Each one ends on "full video on the channel".
- Post the Facebook full video 1–2 days after YouTube. Reels go out the same day as Shorts.

---

## 9. Next 10 episodes

Each one has two HUD counters (one goes up, one gets worse), a 12-step ladder and a teaser ending.

| # | Title | HUD left / right | Cold-open hook | Ladder | Final twist |
|---|---|---|---|---|---|
| 1 | **What If You Could Never Sleep Again?** *(ep01, pilot made)* | HOURS AWAKE / ENERGY | "This is you, after ten years without a single minute of sleep." | hour → day → week → … 10,000 years | The world finally falls asleep around you, and you're the only one left to watch it. |
| 2 | **What If You Woke Up 1,000 Years in the Future?** | YEAR / PEOPLE WHO UNDERSTAND YOU | "Nobody on Earth speaks your language anymore." | first minute → first day → each century you missed, explained | They've been expecting you. You're in their history books. |
| 3 | **What If You Could Hear Everyone's Thoughts?** | PEOPLE IN YOUR HEAD / SECRETS KNOWN | "You know what your best friend really thinks of you." | 1 person → your street → your city → 8 billion | One mind is quiet. And it's been listening to *you*. |
| 4 | **What If You Were the Last Person on Earth?** | DAYS ALONE / LIGHTS STILL ON | "The last light on Earth is the one in your kitchen." | day 1 → power fails → cities flood → nature takes over | On day 3,650, the radio crackles. |
| 5 | **What If You Got $1 Million Every Single Day?** | BANK BALANCE / REAL FRIENDS | "You're the richest person who has ever lived. And you've never been lonelier." | day 1 → you outgrow the banks → you could buy a country | The money keeps coming after you try to stop it. |
| 6 | **What If Time Froze for Everyone But You?** | FROZEN SECONDS / YOUR AGE | "It's been one second for them. It's been forty years for you." | 1 frozen hour → a frozen year → a lifetime in one second | The clock moves forward one tick. Someone else is unfrozen too. |
| 7 | **What If You Lived Your Life Backwards?** | YOUR AGE (counting down) / MEMORIES LEFT | "You were born at 90. Tomorrow you'll be 89." | 90 → 70 → 40 → 18 → 5 | You meet your own parents for the first time, and they don't know you yet. |
| 8 | **What If You Could Only Tell the Truth?** | LIES TOLD: 0 / FRIENDS LEFT | "You just told your boss exactly what you think of him." | day 1 → job → family dinner → becoming famous for it | Someone asks the one question you've never answered honestly. |
| 9 | **What If You Shrank 10× Smaller Every Day?** | YOUR HEIGHT / THINGS THAT CAN EAT YOU | "Yesterday you were a person. Today you're the size of an ant." | 1.8 m → 18 cm → ant → cell → atom | Below the atom, there's somebody waiting. |
| 10 | **What If You Never Forgot Anything?** | MEMORIES STORED / MOMENTS OF PEACE | "You remember every second of every day of your life. Including the worst one." | day 1 → year 1 → every face, every song, every word | The one thing you want to forget is the one thing you never will. |

**Thumbnail ideas (one per episode):**
1. the hero's huge bloodshot eyes, "87,600 HRS"
2. the hero in a futuristic crowd, "YEAR 3026"
3. a crowd of thought bubbles over the hero, "I HEAR YOU"
4. the hero alone in an empty Times Square, "DAY 3,650"
5. the hero on a mountain of cash, sad face, "$1M A DAY"
6. a frozen exploding wave with the hero walking through it, "0.0 SEC"
7. an old hero and a baby hero, "AGE 90 → 0"
8. the hero with a hand over his mouth, "I CAN'T LIE"
9. the hero standing on a giant ant's head, "DAY 3"
10. the hero's head full of glowing film strips, "EVERY SECOND"

**Spin-off Shorts series:** *Survival Diary*, the 9:16 zombie-reel format from the first test (title bar, "Day X" story, cliffhanger, Part 1/2/3). Good for daily Reels between the long episodes:
- Trapped in a Gas Station
- Stuck on a Cruise Ship
- Last Train Running
- Locked in the Mall
- Snowed into a Cabin

---

## 10. Environment setup (cloud session)

```bash
pip install pillow numpy requests piper-tts faster-whisper google-api-python-client google-auth-oauthlib
# ffmpeg is preinstalled. Free draft voice:
curl -L -o voices/en_US-ryan-high.onnx       https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx
curl -L -o voices/en_US-ryan-high.onnx.json  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json
export PIPER_MODEL=$PWD/voices/en_US-ryan-high.onnx
```

| Secret | Used by |
|---|---|
| `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` | tts.py |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | publish_youtube.py |
| `FB_PAGE_ID`, `FB_PAGE_TOKEN` | publish_facebook.py |

The workspace is wiped between cloud sessions. **Commit this folder to a git repo** so scripts, characters and episodes survive.

---

## 11. Per-episode checklist

- [ ] Title chosen from section 9, premise approved
- [ ] `lines.txt` + `shotlist.md` written, facts checked, about 1,700 words
- [ ] Voice generated, listened through, bad lines redone with `--only`
- [ ] Images generated, contact sheet reviewed, no text or wrong characters
- [ ] `render.py` scenes match the shot list, rendered, watched start to finish
- [ ] Loudness check: about −17 dB average, −1 dB peak (`ffmpeg -af volumedetect`)
- [ ] Thumbnail + metadata.json + chapters
- [ ] 9:16 reel cut (30–60 s)
- [ ] YouTube upload private, checked, scheduled
- [ ] Facebook video + reel as drafts, checked, published
- [ ] Shorts / Reels scheduled for the week
