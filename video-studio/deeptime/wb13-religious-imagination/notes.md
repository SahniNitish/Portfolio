# "The Religious Imagination" in the KazChart style

Status: scene file built with ESTIMATED timing (2.6 words/second). Waiting for the user's ElevenLabs voiceover (vo.mp3).

How the video is made
- Engine: the user's "KazChart Skill" (zip, proprietary: only its owner may copy/modify/share it, owner email in rights/OWNERSHIP_AND_RIGHTS.txt).
  It is NOT stored in this repo. Run it from your own copy: `export NODE_PATH=/opt/node-tools/node_modules` then
  `node scripts/render.mjs <scene.json> out.mp4 --audio vo.mp3 [--music bed.mp3]` (Playwright + Chromium + ffmpeg are preinstalled in sessions).
- This repo holds only our own files: `script.txt` (155 sentences, headings start with a section sign), `art.py` (SVG silhouettes drawn in code: people, trees, fire, huts, cave handprints, malimo, phones, city...),
  `build_scene.py` (69 shots, preset "ink", captions with orange keywords, stamps, pills, counters), `scene.json` (output).
- With real audio: `python3 scripts/timestamps.py vo.mp3 words.json` (from the skill, faster-whisper), then `python3 build_scene.py words.json` re-times every shot to the actual voice, then render. Parallel render: use `--from/--to` chunks on 4 cores and join with ffmpeg.
- The skill's ocean creatures are not used (the topic is early humans). Backgrounds are re-coloured (forest green, firelight, cave brown, cold city blue).

Claims in the script to check or soften before publishing (the video says them as facts)
- "for 97% of human history" and "peaceful, egalitarian" as the default: contested. Archaeology shows both cooperation and violence (e.g. Jebel Sahaba, Nataruk); the 97% figure is not a standard number.
- "no hierarchy, uniform homes, equal status of men and women" for all early humans: generalization; varied by group.
- "40,000-year-old bone flutes": supported (Hohle Fels / Geissenklösterle flutes, about 35-40 thousand years old).
- "Pygmies ... malimo": the standard names are Mbuti/BaMbuti/Aka (Pygmy is considered outdated by many) and the instrument is usually spelled molimo (Colin Turnbull's account); his work is debated.
- "same worldview across Europe, Amazon, Congo without contact": a strong claim; anthropologists describe animism with large variation.
Credit Prof. Jiang Xueqin's lectures if the script is based on them.
