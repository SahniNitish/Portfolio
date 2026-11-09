#!/usr/bin/env bash
# Render scene.json with the user's KazChart copy in 4 parallel chunks, then join and add the voiceover.
#   KAZ=/path/to/kazchart-skill VO=/path/to/vo.mp3 bash render_parallel.sh [scale]
set -e
KAZ=${KAZ:-/tmp/claude-0/kaz_zip/kazchart-skill}; VO=${VO:-/tmp/claude-0/wb13_audio/vo.mp3}; SC=${1:-1}
HERE="$(cd "$(dirname "$0")" && pwd)"; OUT=${OUT:-/tmp/claude-0/wb13_render}; mkdir -p "$OUT"
export NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules}
python3 - <<PY
import json
s=json.load(open("$HERE/scene.json")); s.pop("audio",None); json.dump(s,open("$OUT/scene_noaudio.json","w"))
print("total", s["shots"][-1]["end"])
PY
TOTAL=$(python3 -c "import json;print(json.load(open('$OUT/scene_noaudio.json'))['shots'][-1]['end'])")
N=4
for i in $(seq 0 $((N-1))); do
  A=$(python3 -c "print(round($TOTAL*$i/$N,3))"); B=$(python3 -c "print(round($TOTAL*($i+1)/$N,3))")
  ( cd "$KAZ" && node scripts/render.mjs "$OUT/scene_noaudio.json" "$OUT/chunk$i.mp4" --scale $SC --from $A --to $B > "$OUT/chunk$i.log" 2>&1 ) &
done
wait
: > "$OUT/list.txt"; for i in $(seq 0 $((N-1))); do echo "file '$OUT/chunk$i.mp4'" >> "$OUT/list.txt"; done
ffmpeg -nostdin -y -loglevel error -f concat -safe 0 -i "$OUT/list.txt" -i "$VO" -c:v copy \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.84:level=disabled" -c:a aac -ac 2 -ar 44100 -b:a 192k -shortest -movflags +faststart "$OUT/wb13_religious_imagination.mp4"
echo FINISHED
