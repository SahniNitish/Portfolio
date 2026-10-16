"""Build a vertical story reel: title bar + Ken Burns scenes + voiceover + captions."""
import subprocess, json, os, re
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
IMG_Y, IMG_H = 560, 960
GAP, OUTRO = 0.35, 2.8
ORANGE = (247, 147, 30)
FONT = os.path.join(HERE, "fonts", "Anton.ttf")
TITLE = [("ZOMBIE", ORANGE), (" OUTBREAK:", (255, 255, 255))]
SUBTITLE = "TRAPPED IN A GAS STATION"
PART = "PART 1"
OUT = os.path.join(HERE, "zombie_gas_station_part1.mp4")

p = lambda *a: os.path.join(HERE, *a)
lines = open(p("lines.txt")).read().strip().splitlines()
lines[5] = "Day five. My flashlight landed on a trapdoor in the back room. It was bolted shut. Then... something knocked back."


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))


voice = [p("audio", f"l{i+1}.wav") for i in range(len(lines))]
scene_d = [dur(v) + GAP for v in voice]
scene_d[-1] += OUTRO
total = sum(scene_d)

# ---- title bar ----------------------------------------------------------
base = Image.new("RGB", (W, H), "black")
d = ImageDraw.Draw(base)


def fit(text, size, maxw):
    while True:
        f = ImageFont.truetype(FONT, size)
        if d.textlength(text, font=f) <= maxw:
            return f
        size -= 2


f1 = fit("".join(t for t, _ in TITLE), 112, 980)
x = (W - d.textlength("".join(t for t, _ in TITLE), font=f1)) / 2
for t, c in TITLE:
    d.text((x, 200), t, font=f1, fill=c, anchor="lt")
    x += d.textlength(t, font=f1)
f2 = fit(SUBTITLE, 112, 1000)
y2 = d.textbbox((0, 200), "Z", font=f1, anchor="lt")[3] + 22
d.text((W / 2, y2), SUBTITLE, font=f2, fill="white", anchor="mt")
y3 = d.textbbox((W / 2, y2), SUBTITLE, font=f2, anchor="mt")[3] + 26
d.text((W / 2, y3), PART, font=ImageFont.truetype(FONT, 52), fill="white", anchor="mt")
assert d.textbbox((W / 2, y3), PART, font=ImageFont.truetype(FONT, 52), anchor="mt")[3] < IMG_Y - 20
base.save(p("base.png"))

# ---- captions (ASS) -----------------------------------------------------
def ts(t):
    h, t = divmod(t, 3600); m, s = divmod(t, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


ass = [
    "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginV, Outline, Shadow",
    "Style: Cap,Anton,96,&H00FFFFFF,&H00000000,&H80000000,0,5,0,6,0", "",
    "[Events]", "Format: Layer, Start, End, Style, Text",
]
t0 = 0.0
for i, (line, v) in enumerate(zip(lines, voice)):
    words = line.split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == 3 or re.search(r"[.,!?]$", w):
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    speak = dur(v) - 0.25  # piper adds a short tail of silence
    weights = [sum(len(w) + 1 for w in c) + (6 if re.search(r"[.,!?]$", c[-1]) else 0) for c in chunks]
    t = t0 + 0.05
    for c, wt in zip(chunks, weights):
        dt = speak * wt / sum(weights)
        txt = " ".join(c).upper()
        txt = re.sub(r"^(DAY \w+\.)", r"{\\c&H1E93F7&}\1{\\c&HFFFFFF&}", txt)
        pop = r"{\pos(540,1700)\fscx80\fscy80\t(0,90,\fscx100\fscy100)}"
        ass.append(f"Dialogue: 0,{ts(t)},{ts(t + dt)},Cap,{pop}{txt}")
        t += dt
    t0 += scene_d[i]
ass.append(f"Dialogue: 0,{ts(total - OUTRO + 0.3)},{ts(total)},Cap,"
           r"{\pos(540,1700)\fad(250,0)\c&H1E93F7&}PART 2 TOMORROW")
ass.append(f"Dialogue: 0,{ts(total - OUTRO + 0.3)},{ts(total)},Cap,"
           r"{\pos(540,1800)\fs54\fad(250,0)}FOLLOW SO YOU DON'T MISS IT")
open(p("captions.ass"), "w").write("\n".join(ass) + "\n")

# ---- video --------------------------------------------------------------
inputs, fc = [], []
moves = [  # (zoom expr, x expr, y expr) — alternate push-ins and pans
    ("1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.12", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    ("1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih*0.45-(ih/zoom/2)"),
    ("1.10-0.08*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1+0.14*on/{n}", "iw/2-(iw/zoom/2)", "ih*0.42-(ih/zoom/2)"),
    ("1+0.18*on/{n}", "iw/2-(iw/zoom/2)", "ih*0.62-(ih/zoom/2)"),
]
for i, sd in enumerate(scene_d):
    inputs += ["-i", p("img", f"s{i+1}.jpg")]
    n = round(sd * FPS)
    z, xx, yy = (m.format(n=n) for m in moves[i])
    fc.append(
        f"[{i}:v]crop=iw-56:ih-56,scale=3240:3240,"
        f"zoompan=z='{z}':x='{xx}':y='{yy}':d={n}:s=1080x1080:fps={FPS},"
        f"crop=1080:{IMG_H},setsar=1,format=yuv420p[v{i}]"
    )
k = len(scene_d)
fc.append("".join(f"[v{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=0[scenes]")
inputs += ["-loop", "1", "-framerate", str(FPS), "-i", p("base.png")]
fc.append(f"[{k}:v]format=yuv420p[bg];[bg][scenes]overlay=0:{IMG_Y}:shortest=1,"
          f"ass={p('captions.ass')}:fontsdir={p('fonts')},fade=t=out:st={total-0.6:.2f}:d=0.6[vout]")

# ---- audio: voice lines padded to scene length + low ambient drone --------
for i, (v, sd) in enumerate(zip(voice, scene_d)):
    inputs += ["-i", v]
    fc.append(f"[{k+1+i}:a]aresample=44100,apad=whole_dur={sd:.3f}[a{i}]")
fc.append("".join(f"[a{i}]" for i in range(k)) + f"concat=n={k}:v=0:a=1,volume=1.15[vo]")
fc.append(
    f"sine=f=55:d={total:.2f},volume=0.35[s1];sine=f=82.4:d={total:.2f},volume=0.18,tremolo=f=0.25:d=0.7[s2];"
    f"anoisesrc=c=brown:d={total:.2f}:a=0.05,lowpass=f=400[nz];"
    f"[s1][s2][nz]amix=inputs=3:normalize=0,aresample=44100,volume=0.22,"
    f"afade=t=in:d=1.5,afade=t=out:st={total-1.5:.2f}:d=1.5[drone]"
)
fc.append("[vo][drone]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.9[aout]")

cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
       "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}", "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
print(json.dumps({"out": OUT, "seconds": round(total, 1)}))
