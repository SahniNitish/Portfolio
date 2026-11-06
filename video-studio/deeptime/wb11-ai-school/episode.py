"""Deep Time Academy: "Why School Sucks, According to Game Theory" with PAINTED cartoon scenes (Figma image AI) instead of code-drawn stick scenes.

43 scene pictures (art/ or art_jpg/, one per scene of wb05) + a black text card. Same script, same Gemini Bodi voice, same sound design as wb05-school-game
(timeline, SFX cues, music are imported from wb05). New here: slow Ken Burns camera moves, cross-fades, big stroked text tags that pop in with the narration,
and word-by-word bottom captions. All words are drawn in code (the image AI was told to draw none).

    python deeptime/wb11-ai-school/episode.py      # renders wb11_ai_school.mp4 (about 6 min on 4 cores)
"""
import importlib.util, json, math, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("wb05", os.path.join(HERE, "..", "wb05-school-game", "episode.py"))
w5 = importlib.util.module_from_spec(_s); sys.modules["wb05"] = w5; _s.loader.exec_module(w5)
p = lambda *a: os.path.join(HERE, *a)
from PIL import ImageFont

FONTS = os.path.join(HERE, "..", "..", "assets", "fonts")
_fc = {}
def F(px, name="Anton.ttf"):
    k = (name, px)
    if k not in _fc:
        f = ImageFont.truetype(os.path.join(FONTS, name), px)
        if name == "Cinzel.ttf":
            f.set_variation_by_name("Bold")
        _fc[k] = f
    return _fc[k]

W, H, FPS = 1920, 1080, w5.FPS
LS, EN, AT, TL, TOTAL = w5.LS, w5.EN, w5.AT, w5.TL, w5.TOTAL
ST, SCENES, CHAPTERS = w5.ST, w5.SCENES, w5.CHAPTERS
NS = len(SCENES)
clamp01 = lambda x: min(max(x, 0.0), 1.0)
lerp = lambda a, b, u: a + (b - a) * u
ease = lambda x: (lambda y: y * y * (3 - 2 * y))(clamp01(x))
def eob(x, c=1.7):
    x = clamp01(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
BASE_W, BASE_H = 2304, 1296

# ------------------------------------------------------------- overlay text per scene: (text, script line, fraction of that line's voice)
OV = {
 1: [("READ.", 1, .55), ("THINK.", 2, .20), ("LOVE LEARNING.", 2, .62)],
 2: [("MEMORIZING  >  THINKING", 3, .10), ("COMPETITION  >  COLLABORATION", 3, .55)],
 3: [("NEVER AGAIN.", 4, .60)],
 5: [("YALE.", 6, .30), ("WHARTON.", 6, .40), ("CORNELL.", 6, .50), ("THEN: FIRED.", 6, .86)],
 6: [("SHENZHEN, CHINA  -  2008", 7, .35)],
 7: [("50 STUDENTS. ONE ROOM.", 9, .10), ("NO DISCUSSION.", 9, .35), ("NO DEBATE.", 9, .55), ("NO REAL IDEAS.", 9, .75)],
 8: [("SAT PREP = MEMORIZING LISTS", 10, .20)],
 9: [("MODEL UN", 11, .25), ("LOOKING INVOLVED  >  BEING INVOLVED", 11, .70)],
 10: [("NEW GAME", 12, .35)],
 11: [("SMALL SEMINARS", 13, .10), ("5,000-BOOK LIBRARY", 13, .55)],
 12: [("STUDENT-RUN COFFEE HOUSE", 14, .20)],
 13: [("REAL READING.", 15, .62), ("REAL WRITING.", 15, .74), ("REAL RESPONSIBILITY.", 15, .86)],
 14: [("RECORD ADMISSIONS", 16, .30), ("THE PROGRAM WORKED", 16, .75)],
 15: [("GREAT RESULTS.", 18, .55), ("TERRIBLE OUTCOME.", 18, .75)],
 16: [("CHANGED THE CLASSES", 19, .20), ("NOT THE GAME", 19, .60)],
 17: [("PLAYERS", 20, .50), ("INCENTIVES", 20, .65), ("POWER", 20, .82)],
 18: [("BIGGEST REWARD", 21, .30), ("LEAST EFFORT", 21, .70)],
 19: [("WHAT THEY SAY", 22, .20), ("WHAT THEY REWARD", 22, .60)],
 20: [("PARENTS", 23, .10), ("PRESTIGE  -  GRADES  -  CONTROL", 23, .45)],
 21: [("TEACHERS", 24, .10), ("MORE WORK. SAME SALARY.", 24, .60)],
 22: [("ADMINISTRATORS", 25, .10), ("DON'T CAUSE TROUBLE", 25, .75)],
 23: [("GOVERNMENT", 26, .10), ("STABILITY", 26, .55)],
 24: [("COLLEGES", 27, .10), ("FULL TUITION", 27, .60)],
 25: [("STUDENTS: EASY A", 28, .40), ("NOT EVERYONE. NOT ALWAYS.", 29, .20)],
 26: [("WHO HAS THE POWER?", 30, .10)],
 27: [("LEAST POWER", 32, .50)],
 28: [("CONVERGENCE", 33, .40), ("THE SCHOOL EVERYONE CAN TOLERATE", 33, .70)],
 29: [("EASY GRADES", 34, .10), ("HIGH FEES", 34, .30), ("LOW STRESS", 34, .50), ("IMPRESSIVE MARKETING", 34, .70)],
 30: [("REAL LEARNING: IN THE BROCHURE", 35, .40)],
 31: [("GRADE INFLATION", 36, .10), ("COSMETIC INNOVATION", 36, .30), ("CHEATING", 36, .50), ("TEACHER TURNOVER", 36, .70)],
 32: [("DECENT PEOPLE + BAD INCENTIVES", 37, .35), ("= BAD SYSTEMS", 37, .65)],
 33: [("COHESION  -  OPENNESS  -  ENERGY", 38, .55)],
 34: [("COHESION", 39, .10)],
 35: [("OPENNESS", 40, .10)],
 36: [("ENERGY", 41, .10)],
 37: [("FINLAND", 42, .30), ("CHINA, 1980s", 42, .45)],
 38: [("ZERO-SUM", 43, .30), ("YOUR CHILD'S SUCCESS = MY CHILD'S FAILURE", 43, .70)],
 39: [("A MARKETPLACE FOR ADVANTAGE", 45, .40)],
 40: [("I HAVE FIXED EVERYTHING!", 46, .30)],
 41: [("PARENTS: VISIBLE GROWTH", 50, .10), ("TEACHERS: REFORMS THEY CAN SUSTAIN", 50, .55), ("ADMINS: SAFE WINS", 51, .10), ("STUDENTS: REAL CHALLENGES", 51, .50), ("MOVE THE EQUILIBRIUM", 52, .30)],
 42: [("ASK A BETTER QUESTION", 53, .50), ("WHO GETS REWARDED?", 54, .10), ("WHO PAYS THE PRICE?", 54, .40), ("WHO CAN STOP IT?", 54, .62)],
 43: [("SCHOOL IS BROKEN?", 55, .30), ("WORKING EXACTLY AS DESIGNED", 56, .15)],
 44: [("LEARNING  -  OR LOOKING SUCCESSFUL?", 57, .10), ("SUBSCRIBE", 58, .30), ("DON'T JUST CHANGE THE SCHOOL. CHANGE THE GAME.", 58, .70)],
}

# ------------------------------------------------------------- pictures
_img = {}
def pic(n):
    if n not in _img:
        for d, ext in (("art", "png"), ("art_jpg", "jpg")):
            f = p(d, f"s{n:02d}.{ext}")
            if os.path.exists(f):
                _img[n] = Image.open(f).convert("RGB").resize((BASE_W, BASE_H), Image.LANCZOS)
                break
        else:
            raise FileNotFoundError(n)
    return _img[n]


def camera(n, u):
    """Ken Burns: four patterns by scene number. returns crop box in base-image pixels."""
    pat = n % 4
    s = lerp(1.0, 1.14, ease(u)) if pat != 3 else lerp(1.14, 1.0, ease(u))
    cw, ch = 1920 / s, 1080 / s
    mx, my = BASE_W - cw, BASE_H - ch
    fx, fy = {0: (lerp(0.15, 0.85, u), 0.5), 1: (lerp(0.85, 0.15, u), 0.5), 2: (0.5, lerp(0.7, 0.3, u)), 3: (0.5, 0.5)}[pat]
    x0 = mx * fx; y0 = my * fy
    return (x0, y0, x0 + cw, y0 + ch)


def black_card(t):
    im = Image.new("RGB", (W, H), (12, 12, 18)); d = ImageDraw.Draw(im)
    a = clamp01((t - (LS(5) + 0.25)) / 0.8); b = clamp01((t - AT(5, 0.52)) / 0.8)
    if a > 0:
        f = F(150); d.text((960, 400), "WHAT IF", font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
        f2 = F(128); d.text((960, 560), "SCHOOL ISN'T BROKEN?", font=f2, fill=(255, 255, 255), anchor="mm")
    if b > 0:
        d.text((960, 790), "IT'S WORKING EXACTLY AS THE SYSTEM REWARDS IT.", font=F(62), fill=(240, 200, 80), anchor="mm")
    return im


def scene_frame(k, t):
    n = k + 1
    u = clamp01((t - ST[k]) / max((ST[k + 1] if k + 1 < NS else TOTAL) - ST[k], 1e-6))
    if n == 4:
        return black_card(t)
    x0, y0, x1, y1 = camera(n, u)
    return pic(n).resize((W, H), Image.BICUBIC, box=(x0, y0, x1, y1))


# ------------------------------------------------------------- text tags (stacked top-left, pop in with the voice)
def draw_tags(im, k, t):
    n = k + 1
    items = OV.get(n, [])
    if not items:
        return
    d = ImageDraw.Draw(im)
    y = 112
    for text, line, frac in items:
        t0 = AT(line, frac)
        if t < t0:
            y += 94
            continue
        a = eob((t - t0) / 0.28)
        size = 70
        f = F(size)
        while d.textlength(text, font=f) > 1400 and size > 40:
            size -= 4; f = F(size)
        tw = d.textlength(text, font=f)
        off = (1 - a) * 90
        x = 70 - off
        d.rounded_rectangle([x - 26, y - size * 0.62, x + tw + 26, y + size * 0.62], radius=22, fill=(18, 20, 34, 235) if False else (18, 20, 34))
        d.text((x, y), text, font=f, fill=(255, 226, 90), anchor="lm")
        y += 94


# ------------------------------------------------------------- captions
WORDS = json.load(open(p("words.json")))
def make_chunks():
    ch = []
    for n in range(1, 59):
        ws = [(w, LS(n) + s, LS(n) + e) for w, s, e in WORDS[str(n)]]
        cur = []
        for i, wd in enumerate(ws):
            cur.append(wd)
            if len(cur) >= 4 or wd[0][-1] in ".,?!:;" or (i + 1 < len(ws) and ws[i + 1][1] - wd[2] > 0.35):
                ch.append(cur); cur = []
        if cur:
            ch.append(cur)
    return ch
CH = make_chunks()
CH_T0 = [c[0][1] - 0.03 for c in CH]


def draw_caption(im, t):
    import bisect
    i = bisect.bisect_right(CH_T0, t) - 1
    if i < 0:
        return
    ch = CH[i]
    nxt = CH_T0[i + 1] if i + 1 < len(CH) else 1e9
    t1 = nxt if nxt - ch[-1][2] < 0.6 else ch[-1][2] + 0.3
    if t >= t1:
        return
    d = ImageDraw.Draw(im)
    size = 78; f = F(size)
    words = [w.upper() for w, _, _ in ch]
    sp = d.textlength(" ", font=f) * 1.1; wd = [d.textlength(x, font=f) for x in words]
    x = 960 - (sum(wd) + sp * (len(words) - 1)) / 2; y = 985 - 6 * (1 - eob((t - CH_T0[i]) / 0.14))
    for (w, s, e), word, ww in zip(ch, words, wd):
        on = s - 0.02 <= t < e + 0.05
        d.text((x, y), word, font=f, fill=(255, 226, 90) if on else (255, 255, 255), anchor="lm", stroke_width=9, stroke_fill=(20, 16, 18))
        x += ww + sp


def draw_chrome(im, t):
    d = ImageDraw.Draw(im)
    d.text((1880, 1050), "DEEP TIME ACADEMY", font=F(24, "Cinzel.ttf"), fill=(255, 255, 255), anchor="rm", stroke_width=3, stroke_fill=(20, 16, 18))
    for n, title in CHAPTERS:
        a = clamp01((t - (LS(n) - 0.05)) / 0.3) * (1 - clamp01((t - (LS(n) + 2.8)) / 0.4))
        if a > 0:
            f = F(38)
            tw = d.textlength(title, font=f)
            d.rounded_rectangle([40, 30, 40 + tw + 56, 100], radius=14, fill=(240, 190, 60))
            d.text((68, 66), title, font=f, fill=(24, 30, 60), anchor="lm")


XF = 0.25


def frame_at(t):
    k = max(i for i, s in enumerate(ST) if s <= t)
    im = scene_frame(k, t)
    if k > 0 and t - ST[k] < XF:
        prev = scene_frame(k - 1, ST[k])
        im = Image.blend(prev, im, ease((t - ST[k]) / XF))
    im = im.copy()
    draw_tags(im, k, t)
    draw_chrome(im, t)
    draw_caption(im, t)
    return im


def _render_chunk(job):
    k0, k1, path = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-an", path], stdin=subprocess.PIPE)
    for k in range(k0, k1):
        ff.stdin.write(np.asarray(frame_at(k / FPS)).tobytes())
    ff.stdin.close(); ff.wait()
    return path


def render_parallel(total, audio_wav, out_mp4, procs=4, parts=24):
    import multiprocessing as mp
    nf = int(round(total * FPS))
    tmp = tempfile.mkdtemp(prefix="wb_parts_", dir=HERE)
    bounds = [round(nf * i / parts) for i in range(parts + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(tmp, f"part{i:02d}.mp4")) for i in range(parts)]
    with mp.get_context("fork").Pool(procs) as pool:
        for n, _ in enumerate(pool.imap_unordered(_render_chunk, jobs), 1):
            print(f"chunk {n}/{parts} done", flush=True)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio_wav, "-c:v", "copy",
                    "-af", "alimiter=limit=0.70:level=disabled", "-c:a", "aac", "-ac", "2", "-ar", "44100", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    wav = w5.build_audio()
    out = p("wb11_ai_school.mp4")
    render_parallel(TOTAL, wav, out)
    print("done", out, f"{TOTAL:.1f}s")
