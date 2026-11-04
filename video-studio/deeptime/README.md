# Deep Time Academy (second channel)

History · Geopolitics · Documentaries. Look: flat 2D cartoon "animated history" style, gold Cinzel titles
(matches the channel banner), cut-out characters animated over separate backgrounds, code-drawn maps,
chalk diagrams, counters and props. Uses the shared engine in `../tools/engine.py`.

## Series: Game Theory
- `ep01-dating-game/`: "The Dating Game" (first-minute draft). Original script on the Gale–Shapley
  stable-matching result (1962; Nobel in Economics 2012). The topic was inspired by Professor Jiang
  Xueqin's Predictive History lectures; credit him in the description. Don't reuse his footage or audio.

## Characters (keep prompts word for word)
- MAN: `a young man cartoon character with big expressive eyes, short messy dark brown hair, wearing a navy blue blazer over a white shirt and a red tie, brown trousers and brown shoes`
- WOMAN: `a young woman cartoon character with big expressive eyes, black hair in a high bun, wearing a red knee-length dress, gold hoop earrings and black flat shoes`
- Style prefix: `Flat 2D cartoon animation style of a modern animated history explainer, clean bold dark outlines, flat colors with soft cel shading, slightly exaggerated proportions.`
- Cut-outs: end with `Isolated on a solid pure bright green (#00FF00) background, no shadow on the ground. No text, no words, no letters, no logos.`

## Voice
`tools/tts.py` uses Fish Audio when `FISH_AUDIO_API_KEY` is set (`FISH_VOICE_ID` = voice model id from
fish.audio, `FISH_MODEL` default `s1`). Lines may start with emotion tags like `(curious)`; other
engines strip them. Fallback draft voice: `KOKORO_VOICE=am_michael KOKORO_SPEED=0.95`.

## Fonts
`assets/fonts/Cinzel.ttf` is from Google Fonts (SIL Open Font License).
