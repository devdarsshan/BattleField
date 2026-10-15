"""Paint the sea for the 3D map world (Flow refs K08a_v2 / K08b_v2): soft blue water,
turquoise shallows along the coast, and rows of light wave strokes. The land is 3D
geometry on top, so the land area here is just a sandy underlay.

  python make_sea_texture.py   -> textures/map_sea.jpg
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import kerala_geo as geo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures")
os.makedirs(OUT, exist_ok=True)

X0, X1, Y0, Y1 = geo.MAP_REGION
W = 4096
H = round(W * (Y1 - Y0) / (X1 - X0))
prng = random.Random(3)


def px(x, y):
    return ((x - X0) / (X1 - X0) * W, (Y1 - y) / (Y1 - Y0) * H)


land_img = Image.new("L", (W, H), 0)
ImageDraw.Draw(land_img).polygon([px(x, y) for x, y in geo.land_polygon_detailed()], fill=255)
land = np.asarray(land_img, np.float32) / 255.0
near = np.asarray(land_img.filter(ImageFilter.GaussianBlur(110)), np.float32) / 255.0
near_wide = np.asarray(land_img.filter(ImageFilter.GaussianBlur(120)), np.float32) / 255.0

DEEP = np.array([112, 172, 216], np.float32)
MID = np.array([132, 192, 222], np.float32)
SHALLOW = np.array([142, 226, 214], np.float32)
SAND = np.array([238, 206, 146], np.float32)

r = np.random.default_rng(5)
small = (r.random((H // 256 + 3, W // 256 + 3)) * 255).astype(np.uint8)
mott = np.asarray(Image.fromarray(small).resize((W + 768, H + 768), Image.BICUBIC).crop((256, 256, 256 + W, 256 + H)),
                  np.float32) / 255.0
k_mid = np.clip(near_wide * 2.4, 0, 1)
k_sh = np.clip((near - 0.03) * 3.0, 0, 1)
img = DEEP * (1 - k_mid[..., None]) + MID * k_mid[..., None]
img = img * (1 - k_sh[..., None]) + SHALLOW * k_sh[..., None]
img *= (0.96 + 0.06 * mott)[..., None]

# rows of light wave strokes (stronger offshore, none on the shallows)
strokes = Image.new("L", (W, H), 0)
ds = ImageDraw.Draw(strokes)
row = 26
for j in range(0, H, row):
    x = prng.uniform(-40, 0)
    while x < W:
        y = j + prng.uniform(-6, 6)
        w = prng.uniform(26, 44)
        if land[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))] < 0.5:
            ds.arc([x, y - w * 0.18, x + w, y + w * 0.18], 200, 340, fill=255, width=3)
        x += w * prng.uniform(1.05, 1.6)
st = np.asarray(strokes.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255.0
st *= (1 - np.clip(near * 3.0, 0, 1)) * (1 - land)
img = img * (1 - 0.38 * st[..., None]) + np.array([170, 214, 236], np.float32) * 0.38 * st[..., None]

# sandy underlay where the 3D land sits
img = img * (1 - land[..., None]) + SAND * land[..., None]

Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").save(os.path.join(OUT, "map_sea.jpg"), quality=92)
print("wrote", os.path.join(OUT, "map_sea.jpg"), W, H)
