# EP01 "The Dating Game": production plan for the full 11-minute video

## STATUS (2026-11-04): EPISODE 1 IS FINISHED. Read this first.
- **Final video:** `dating_game_full_v1.mp4` (git-ignored, about 176 MB): 12:58, 1920x1080, 30 fps, -15.9 LUFS, peak -1.7 dBFS. All 119 lines are voiced (Fish Audio, WNBA VOICEOVER, drama-3; every line transcription-checked; line 80 re-voiced because "Betraying" lost its first syllable).
- **Also done:** `thumb_a.jpg` (recommended) and `thumb_b.jpg`, `metadata.json` (title, description with chapters from the real timeline, sources, tags). Chapter times: 0:00 intro, 1:25, 2:23, 3:46 (approx.), then 7:24, 9:16, 10:43, 11:36 for chapters 5-8 (exact list in `metadata.json`).
- **Audio note:** the render writes a master at about -15.4 LUFS but AAC encoding added about +1 dB on two loud sound effects (6:07 and 11:27). After rendering, re-mux with `ffmpeg -i video.mp4 -i _mix.wav -map 0:v -map 1:a -c:v copy -af "alimiter=limit=0.70:level=disabled" -c:a aac -b:a 256k -shortest out.mp4` and re-measure (target peak below -1 dBFS). This is now a pitfall row in the skill.
- **What the user may still ask for:** shorter cut (pauses can be tightened: default gap 0.45 s, chapter-card gaps 2.6 s; the video is about 1 minute over the 10-12 min target), different thumbnail text, music changes, re-voiced lines (about 80-170 credits each), a Shorts cut.
- **Next episode:** "Game Theory #2: a game played by entire nations" (teased in the outro). Use the skill `make-deeptime-episode`: script first, show it, wait for approval, check Fish credits (connector credits, NOT the API balance) before voicing.

*The detailed shot list below was written for the FIRST version of the script. The code in `episode.py` is now the source of truth; use the list only as background.*


**Status (2026-11-04):**
- The opening (lines 1–14) is **done**: voiced with WNBA VOICEOVER, animated and approved. Its render is `dating_game_v2.mp4`.
- Lines 15–119 have a written script (`script.md`) but are **not voiced or animated yet**.
- The user approved the overall direction ("I like everything you've done so far"). **Still show them the script before voicing**: ask "script approved?" if they haven't said so explicitly.

Follow `.claude/skills/make-deeptime-episode/SKILL.md` for *how*. This file says *what* to build for each line.

---

## Step-by-step checklist (do these in order)

- [ ] 1. Confirm the script with the user (`script.md`). Apply any edits.
- [ ] 2. `get_credit_balance` (Fish). Lines 15–119 need about **8,500 credits**. If the balance is lower, tell the user and stop.
- [ ] 3. Copy lines 15–119 (text only, tags kept) into `lines.txt` **below** the existing 14 lines. The file must end up with 119 lines and no blank lines.
- [ ] 4. Voice lines 15–119 with Fish MCP `text_to_speech`:
  - `voice_id fb7ec16ca51a45a5a4db881244d7990a`, `model drama-3`
  - Send 10–15 calls in parallel per message.
  - Save each as `audio/l15.mp3` … `audio/l119.mp3`, then convert to `.wav` (48 kHz mono).
- [ ] 5. Transcribe and check every new line (skill step 4). Re-voice only the bad ones.
- [ ] 6. Generate the new art listed below (Figma), download it immediately, key the cut-outs and check the contact sheet.
- [ ] 7. Extend `episode.py`:
  - GAPS for the new lines
  - new scene functions
  - chapter cards
  - add them to `SCENES`
  - sound effects in `build_audio()`
  - set the output name to `dating_game_full_v1.mp4`
- [ ] 8. `tools/preview.py deeptime/ep01-dating-game 15 119`, then fix what's wrong.
- [ ] 9. Render in the background (about 40 minutes), then run the checks: duration 10–12 minutes, loudness about −14 to −16 LUFS, and 5 sample frames.
- [ ] 10. Make the thumbnail (2 variants), write `metadata.json` (title, description with chapters and sources, tags), commit, push, and send the video to the user.

---

## Timing (GAPS, 0-based indexes; line N in script.md = index N-1)

- Default gap: 0.45 s. Keep the existing GAPS for indexes 0–13. **Change index 13** (line 14) from 3.6 to **0.6**, because the old end card is replaced by the story continuing.
- **Chapter cards** take a 2.6 s gap *before* each chapter's first line. Set the gap of the line **before** it:

| Chapter | First line | Set GAPS[index] = 2.6 |
|---|---|---|
| CH1 "FOR MOST OF HISTORY" | line 15 | index 13 → 2.6 (this replaces the 0.6 above) |
| CH2 "WHAT IS A GAME?" | line 24 | index 22 |
| CH3 "THE ALGORITHM OF LOVE" | line 38 | index 36 |
| CH4 "SIGNALS" | line 58 | index 56 |
| CH5 "THE TRUST TRAP" | line 73 | index 71 |
| CH6 "THE CASINO IN YOUR POCKET" | line 90 | index 88 |
| CH7 "WHEN TO STOP" | line 101 | index 99 |
| CH8 "HOW TO WIN THE GAME" | line 108 | index 106 |

- Card start time: `END(index) + 0.15`. Draw it with `chapter_card(t, t0, num, "TITLE")`.
- Card sounds: `sfx("whoosh")*0.4` at t0−0.3, `sfx("boom")*0.5` and `fx_shimmer()` at t0+0.3. Music `dgain` drops to 0.4 during cards.
- **Reveal pauses (0.8 s):** indexes 46 (line 47), 49 (line 50), 53 (line 54), 67 (line 68), 77 (line 78), 86 (line 87), 98 (line 99), 105 (line 106), 115 (line 116).
- **Outro:** index 118 (line 119) gets 3.8 s for the end card.

---

## New art to generate (Figma, about 14 images)

Use the prompt templates in the skill. STYLE = the style prefix. MAN and WOMAN = the character fragments.

| File | Type | Prompt core |
|---|---|---|
| `bg_rome.png` | background | an ancient Roman villa courtyard with columns, a fountain and red roof tiles, warm afternoon light |
| `bg_castle.png` | background | a medieval European castle great hall with banners left blank, a long wooden table, torches |
| `bg_china.png` | background | an imperial Chinese palace courtyard with red pillars, golden roofs and lanterns, blank plaques |
| `bg_india.png` | background | a Mughal-era Indian palace courtyard with arches, a reflecting pool and marigold garlands |
| `families_deal.png` | cut-out, 1536x1024 | two groups of elderly parents in simple timeless historical robes, the fathers shaking hands over a rolled scroll, the mothers watching, a nervous young couple in the middle glancing at each other |
| `bg_market.png` | background | an old town marketplace with empty wooden stalls and hanging lanterns at dusk |
| `nash_board.png` | cut-out | a young 1950s mathematician with neat dark hair, white shirt, rolled sleeves and loosened tie, holding chalk, a confident excited expression (a generic character, not a portrait of a real person) |
| `bg_1973_office.png` | background | a 1970s corporate office with wood panelling, an orange chair, a desk with a framed blank diploma and a typewriter |
| `peacock.png` | cut-out, 1536x1024 | a proud peacock with its huge tail fully fanned, side view |
| `fox.png` | cut-out | a sneaky orange fox crouching, looking right, hungry eyes |
| `man_phone_car.png` | cut-out | MAN, sitting in the driver's seat of a small red cartoon car (side view, car included), smiling, determined, both hands on the wheel |
| `robots.png` | cut-out, 1536x1024 | four cute retro 1980s computer-terminal robots with screen faces (left blank), facing each other in pairs |
| `skinner_lab.png` | background | a 1950s psychology laboratory with a white pigeon in a box beside a small lever and a food tray, lab coats on hooks |
| `doors.png` | background | a long corridor with seven identical closed wooden doors in a row, side-on view, warm light |

Reuse from ep01 (no new credits): `bg_stage`, `bg_city`, `bg_office` (chalkboard via `board(t)`), `bg_map`, `man_curious`, `man_shocked`, `woman_confident`, `woman_phone`, `professors`.

If Figma credits run out: missing images can be replaced with a `blurred(stage)` background plus badges and labels. Never stall: finish the voice and code, and tell the user which images are still missing.

---

## Shot list (line → scene)

`at(i, f)` = time at fraction f of line index i. "Pop" = `label`/`pop_img` with `sfx("pop")`. Every scene: `motes`, plus a slow push-in or pan.

### CH1: For most of history, you didn't play (lines 15–23)
| Line | Scene | What happens |
|---|---|---|
| 15 | `bg_stage` | `man_curious` pops up centre. A big gold "?" bobs (copy `sc_strange`) |
| 16 | same, darken 0.4 | Label "IT WASN'T YOU" stamps in at `at(15,0.6)`, red, angle −5 |
| 17 | **map tour** on `bg_map` | Camera pans to Rome (0.47,0.33) → Europe (0.5,0.27) → China (0.75,0.36) → India (0.66,0.46), following "Rome / Europe / China / India" at about 0.25 / 0.45 / 0.65 / 0.85 of the line. A gold pin drops at each, with a `tick`. Then a quick crossfade to the matching `bg_rome` / `bg_castle` / `bg_china` / `bg_india` cut (0.6 s each) at the end of the line. Or put those four backgrounds in a 2×2 split-screen; either works |
| 18 | `bg_castle` blurred | `families_deal` cut-out slides up from the bottom. Badges `land` → `coin` → `sword` pop at 0.2 / 0.5 / 0.8 ("land / money / armies") with `coin`, `coin`, `boom*0.4` |
| 19 | same | A small heart badge pops, then shrinks to 40% and slides to the corner. Label "BONUS" (angle 6) |
| 20 | `bg_map` sepia → full colour | An hourglass badge, with a label "A NEW IDEA: CHOOSE FOR LOVE". The map's colour fades from sepia to full |
| 21 | `bg_market` | MAN enters left, WOMAN right. Gold "MARKET" title drops at `at(20,0.75)` with `fx_hit()` |
| 22 | same | Labels "COMPETITION", "BARGAINING", "STRATEGY" pop in a row at 0.2 / 0.5 / 0.8 |
| 23 | `bg_stage` | Gold "GAME THEORY" with a shine (copy the end of `sc_finale`). Riser before, hit on |

### CH2: What is a game? (lines 24–37)
| Line | Scene | What happens |
|---|---|---|
| 24 | `bg_office` sepia | Label "DECISIONS THAT DEPEND ON OTHERS". Two thought-bubble circles with arrows pointing at each other (draw them) |
| 25 | same | Year counter "1944" (copy `sc_years`, but count up from 1900). Label "VON NEUMANN & MORGENSTERN" |
| 26 | `board(t)` chalkboard | `nash_board` slides in from the right. Label "JOHN NASH" at chest height. Chalk draws a 2×2 grid |
| 27 | `bg_stage` blurred | Label "4 PARTS" in big gold text |
| 28–31 | same | Badges `players`, `strategy`, `payoff`, `info` pop in a row (x = 420 / 780 / 1140 / 1500), one per line, each with a label underneath (PLAYERS / STRATEGIES / PAYOFFS / INFORMATION). Earlier badges stay on screen and dim to 60% |
| 32 | `bg_stage` | MAN left, WOMAN right enter. The 4 badges shrink into a row at the top |
| 33 | same | The `players` badge glows. Labels "YOU" over the man and "EVERYONE ELSE" over the woman |
| 34 | same | The `strategy` badge glows. Three labels cycle: "APPROACH / WAIT", "COMMIT / KEEP OPTIONS", "TRUTH / BEST SIDE" |
| 35 | same | The `payoff` badge glows. Heart, house and payoff badges pop, then `man_shocked` swaps in for a "HEARTBREAK" label in red |
| 36 | same, darken | The `info` badge glows. Question marks appear over both characters' heads. Label "TERRIBLE" stamp + `fx_hit()` |
| 37 | same | Push in. Gold "BUILT FOR THIS" shine |

### CH3: The algorithm of love (lines 38–57)
This is the core chapter. **Reuse `board(t)` with `person_glyph` and `chalk_line` from `sc_chalk`.** Men are blue on the left (x=560), women are pink on the right (x=1360), and the rows use `MEN_Y`.
| Line | Scene | What happens |
|---|---|---|
| 38 | `bg_office` | `professors` slide in. Label "GALE & SHAPLEY" |
| 39 | board | 4 + 4 glyphs pop. Each one gets a tiny ranking strip of 4 coloured dots beside it (draw them) |
| 40 | board | Label "STEP 1". 4 blue arrows (chalk lines) draw to each man's first choice. Two men target the same woman |
| 41 | board | Label "STEP 2". Each woman keeps one arrow, which gets a yellow "MAYBE" tag. The others turn red and are crossed out (`screech*0.3`) |
| 42 | board | Label "STEP 3". Rejected men draw new arrows to their 2nd choice |
| 43 | board | One woman swaps: her old MAYBE turns red and her new one turns yellow. Label "TRADES UP" |
| 44 | board | Fast montage of rounds: arrows flick in quickly with ticks. Label "ROUND 2… 3… 4…" counting up |
| 45 | board | The final pairs turn gold. Label "STABLE MATCH" (green, like `sc_nobel`'s "STABLE!") |
| 46 | board | A dashed line between two non-partners tries to connect, then is blocked by a red X. Label "NOBODY RUNS OFF" |
| 47 | `bg_stage` | `professors` pop up. Gold "ALWAYS WORKS" |
| 48 | stage, red darken | `man_shocked` pops up. Label "THE TWIST" (reuse the `sc_twist` look) |
| 49–50 | reuse **`sc_firstmove`** exactly | (BEST MATCH / WORST MATCH cards) |
| 51 | same blurred stage | The two cards swap sides, and the man and woman swap sides. Label "WHO MOVES FIRST?" |
| 52 | stage | `man_curious` + a label "PROPOSERS: NO REASON TO LIE" |
| 53 | stage | `woman_confident` enters. A big "NO" speech bubble (draw a rounded rect + Anton "NO…?") |
| 54 | same | Gold "PLAYING HARD TO GET". Heart badge with a wink. `coin` |
| 55 | `bg_city` daytime-darkened | 3 rows of tiny hospital icons (draw a white square + red cross) with arrows from doctor glyphs. Label "NEW DOCTORS ↔ HOSPITALS". Swap ↔ for "TO" (Anton has no arrows) |
| 56 | `bg_city` | Tiny school icons (house badge, scaled) + label "NEW YORK HIGH SCHOOLS" |
| 57 | reuse the `sc_nobel` medal | Label "SHAPLEY & ROTH · 2012" |

### CH4: Signals (lines 58–72)
| Line | Scene | What happens |
|---|---|---|
| 58 | board | The stable-match diagram from CH3 cracks, with red jagged lines (draw them) |
| 59–60 | stage | MAN and WOMAN with closed "?" thought bubbles. Label "HIDDEN INFORMATION" |
| 61 | same | Two labels alternate over each head: "SERIOUS?" / "PASSING TIME?" and "INTERESTED?" / "POLITE?" |
| 62 | stage blurred | Gold "SIGNALING GAME" |
| 63 | `bg_1973_office` sepia | Year label "1973". Label "MICHAEL SPENCE" |
| 64 | same | The blank diploma glows (draw a gold rect with a shine over its location). Label "COSTLY TO FAKE" |
| 65–67 | `bg_market` or a stage blurred to green | `peacock` slides in. At 66, `fox` slides in from the right (`fx_hit`). Label "HEAVY. SLOW. RISKY." |
| 68 | same | Gold "HANDICAP PRINCIPLE" |
| 69 | `bg_city` night | `woman_phone`. Phone bubbles reading "I LOVE YOU" pop out (label, white), then tick to grey. Label "COST: 0" |
| 70 | `bg_city` | The `man_phone_car` cut-out drives across from left to right (x lerp, `walk=True` bounce). Labels "3 HOURS", "REMEMBERED", "MEET MY FAMILY" pop up one by one |
| 71 | same | Gold "COSTLY SIGNALS = TRUST" |
| 72 | `woman_phone` | A stack of "hey" bubbles piles up and falls off-screen. Label "MEANS ALMOST NOTHING" |

### CH5: The trust trap (lines 73–89)
| Line | Scene | What happens |
|---|---|---|
| 73 | stage | MAN + WOMAN, warm spot |
| 74 | stage darkened | Year "1950" + label "RAND CORPORATION". Gold "THE PRISONER'S DILEMMA" |
| 75–76 | blurred stage | `payoff_matrix(f, t, at(74,0.1))`. The cells build in. At 76, highlight (0,0) then (0,1) |
| 77 | same | MAN + WOMAN small at the sides with "?" over each head. Label "PROTECT MYSELF?" |
| 78 | same | Highlight (1,1). Label "BOTH LOSE" red + `fx_hit()` |
| 79 | stage | Labels "OPEN UP", "INVEST", "COMMIT" pop in green over the couple |
| 80 | stage | Labels "ONE FOOT OUT THE DOOR", "KEEP OPTIONS OPEN" in red |
| 81 | stage darkened | The couple's `t_out` fades them apart. Label "NEVER STARTS" |
| 82 | stage | `man_curious` scratching his head. Gold "?" |
| 83 | `bg_office` sepia | `robots` cut-out. Year label "1980". Label "AXELROD'S TOURNAMENT". Rapid ticks |
| 84 | same | One robot gets a gold crown (draw a polygon). Label "TIT FOR TAT" + `coin` |
| 85–86 | blurred | Three labels in sequence: "BE NICE", "RESPOND QUICKLY", "FORGIVE QUICKLY" |
| 87 | stage | Split: left label "ONE GAME: BETRAYAL PAYS", right "REPEATED GAME: TRUST WINS" (green) |
| 88 | stage, a long gold shadow | Draw a dark gradient quad stretching from the couple's feet toward the horizon. Gold "THE SHADOW OF THE FUTURE" |
| 89 | stage | The couple steps closer together (x lerp toward the centre). Label "THE ULTIMATE REPEATED GAME" |

### CH6: The casino in your pocket (lines 90–100)
| Line | Scene | What happens |
|---|---|---|
| 90 | `bg_city` night | `woman_phone` enters. Phone glow (copy from `sc_casino`) |
| 91 | same | Hundreds of tiny profile cards (cream rects with a circle "face") fan out of the phone in an arc |
| 92 | same | Label "A DREAM?", then it flips to "A TRAP" (red) |
| 93 | stage | The "shadow of the future" quad shrinks to nothing. Label "ONE SWIPE AWAY" |
| 94 | blurred | A pyramid of profile cards: the top 3 glow with many hearts, the bottom rows have none. Label "ATTENTION PILES UP AT THE TOP" |
| 95–96 | `bg_city` | Close on the phone (`woman_phone` scaled to 1100 px, cropped). Labels "SWIPE… NOTHING" ×2 with `tick`s, then a gold "IT'S A MATCH!" + `coin` |
| 97 | `skinner_lab` sepia | Year label "1950s". Label "B. F. SKINNER". A pigeon lever animation: draw a lever arm that moves, with random seed pellets + ticks |
| 98 | reuse the **`sc_casino`** slot machine | Final reels ♥ ♥ $ |
| 99 | split blurred | Left label "YOUR GAME: FIND SOMEONE". Right label "THE APP'S GAME: KEEP PLAYING" |
| 100 | same | Label "THE APP WINS WHEN YOU STAY" red + `fx_hit()` |

### CH7: When to stop (lines 101–107)
| Line | Scene | What happens |
|---|---|---|
| 101 | stage | `man_curious` + a big "?" |
| 102 | `doors` | Year "1960" + label "THE SECRETARY PROBLEM" |
| 103 | `doors` | The camera pans along the doors. Each door "opens" as a dark rect sliding over it. Label "NO GOING BACK" |
| 104 | `doors` | `progress_bar(f, frac, mark=0.37, label_txt="37%")` fills to 0.37. Label "JUST LOOK" |
| 105 | same | The bar continues. The next door glows gold with a star. Label "BETTER THAN ALL SO FAR" + `coin` |
| 106 | same | Label "BEST CHANCE OF THE BEST" |
| 107 | stage | Gold "DON'T SEARCH FOREVER" |

### CH8: How to win the game (lines 108–119)
| Line | Scene | What happens |
|---|---|---|
| 108 | stage | The couple in the centre. Gold "4 LESSONS" |
| 109 | stage blurred | A lesson card flips in (cream card, Anton): "1. MAKE THE FIRST MOVE" with a strategy badge |
| 110 | same | "2. SEND COSTLY SIGNALS" with the peacock cut-out small |
| 111 | same | "3. TRUST, FORGIVE, PLAY LONG" with a payoff badge |
| 112 | same | "4. EXPLORE, THEN STOP" with a progress bar. All 4 cards stay in a 2×2 grid |
| 113 | `bg_castle` sepia | `families_deal`. Label "FOR THOUSANDS OF YEARS…" |
| 114 | camera pull-back | `bg_city` night zooms out (zoom 1.4 → 1.0), then crossfades to `bg_map` with hearts popping everywhere (reuse `sc_map`) |
| 115 | `bg_map` | Label "THE RULES WERE NEVER WRITTEN DOWN" |
| 116 | stage, spot | Gold "NOW YOU KNOW" + shine + `fx_shimmer` |
| 117 | stage | Labels "MOVE FIRST?" (left) and "WAIT?" (right) over the man and the woman. Label "COMMENT BELOW" |
| 118 | `bg_map` → darkened | Flags or crowns (draw them) appear over nations. Label "NEXT: A GAME PLAYED BY NATIONS" |
| 119 | sting-style end card | Reuse `sting_frame`, or a black card with gold "DEEP TIME ACADEMY", "SUBSCRIBE" and "GAME THEORY · EP 2 COMING SOON" |

---

## Music plan (`mgain` / `dgain`)
- The pizzicato plays under explaining sections (CH2, CH3 steps, CH7, CH8 lessons).
- Turn the pizzicato **off** (mgain 0) for serious or tense moments: lines 16, 21, 36, 48, 78, 81, 100 and 113–116.
- `dgain` 0.4 during chapter cards and the logo sting, and 1.0 everywhere else.
- Optional: from CH6 on, add `fx_riser` swells before each chapter card for momentum.

## Metadata draft (write `metadata.json`)
- **Title options:**
  - "The Math Behind Dating: Who Should Make the First Move? | Game Theory #1"
  - "Game Theory #1: The Dating Game (The Side That Waits Always Loses)"
- **Tags:** game theory, dating game theory, stable marriage problem, gale shapley, prisoner's dilemma, signaling theory, dating apps psychology, secretary problem, 37% rule, history of marriage, deep time academy, predictive history, nash equilibrium.
- **Description:** see the skill step 7. Chapters come from `L(14)`, `L(23)`, `L(37)`, `L(57)`, `L(72)`, `L(89)`, `L(100)` and `L(107)` (0-based starts of each chapter's first line). Sources are at the bottom of `script.md`.
