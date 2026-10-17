"""Side-by-side stills vs. the Flow references: python compare_siege.py TAG f133:K49 f445:K50 ..."""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1]
os.makedirs(os.path.join(HERE, "renders", "compare"), exist_ok=True)
for pair in sys.argv[2:]:
    f, k = pair.split(":")
    a = Image.open(os.path.join(HERE, "renders", tag, f"f_{f}.png")).convert("RGB")
    ref = os.path.join(HERE, "..", "frames", "flow_refs", f"{k}.jpeg")
    b = Image.open(ref).convert("RGB")
    h = 540
    b = b.resize((int(b.width * h / b.height), h))
    m = Image.new("RGB", (a.width + b.width, h))
    m.paste(a.resize((a.width, h)), (0, 0)); m.paste(b, (a.width, 0))
    m.save(os.path.join(HERE, "renders", "compare", f"{tag}_{f}_{k}.png"))
