"""python sheet.py PREFIX OUT.png f1 f2 ... : contact sheet of stills renders/PREFIX_f<N>.png (3 columns)"""
import sys
from PIL import Image
pre, out, fs = sys.argv[1], sys.argv[2], sys.argv[3:]
w, h = 640, 360
rows = (len(fs) + 2) // 3
m = Image.new("RGB", (w * 3, h * rows))
for i, f in enumerate(fs):
    im = Image.open(f"renders/{pre}_f{int(f):03d}.png").convert("RGB").resize((w, h))
    m.paste(im, ((i % 3) * w, (i // 3) * h))
m.save(out)
