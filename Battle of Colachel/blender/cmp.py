"""python cmp.py PREFIX FRAME KREF : side-by-side of renders/PREFIX_fNNN.png and the Flow ref -> renders/compare/PREFIX_f_K.png"""
import sys
from PIL import Image
pre, f, k = sys.argv[1:4]
a = Image.open(f"renders/{pre}_f{int(f):03d}.png").convert("RGB")
b = Image.open(f"../frames/flow_refs/{k}.jpeg").convert("RGB")
h = 540
b = b.resize((int(b.width * h / b.height), h)); a = a.resize((int(a.width * h / a.height), h))
m = Image.new("RGB", (a.width + b.width, h)); m.paste(a, (0, 0)); m.paste(b, (a.width, 0))
m.save(f"renders/compare/{pre}_f{f}_{k}.png")
