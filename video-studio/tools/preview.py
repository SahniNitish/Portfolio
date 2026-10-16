"""Contact sheet of one frame per narration line, to check framing before a full render.

    python tools/preview.py episodes/ep05-grey-coat            -> episodes/ep05-grey-coat/_preview.jpg
    python tools/preview.py episodes/ep05-grey-coat 10 20      -> only lines 10..20 (1-based)
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw

ep_dir = os.path.abspath(sys.argv[1])
spec = importlib.util.spec_from_file_location("episode", os.path.join(ep_dir, "episode.py"))
ep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ep)
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 1
hi = int(sys.argv[3]) if len(sys.argv) > 3 else ep.N
tw, th, cols = 384, 216, 6
idx = list(range(lo - 1, hi))
sheet = Image.new("RGB", (cols * tw, ((len(idx) + cols - 1) // cols) * (th + 22)), (40, 40, 40))
for n, i in enumerate(idx):
    t = ep.L(i) + 0.7 * (ep.END(i) - ep.L(i))
    fr = ep.frame_at(t).convert("RGB").resize((tw, th))
    x, y = (n % cols) * tw, (n // cols) * (th + 22)
    sheet.paste(fr, (x, y + 22))
    ImageDraw.Draw(sheet).text((x + 6, y + 4), f"line {i + 1}  t={t:.1f}s", fill=(255, 255, 0))
out = os.path.join(ep_dir, "_preview.jpg")
sheet.save(out, quality=85)
print(out, f"(total {ep.TOTAL:.1f}s)")
