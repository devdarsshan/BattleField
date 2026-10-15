"""Paint the aged parchment map of Kerala (no text) for the map sequences.

  python make_map_texture.py        -> textures/kerala_map.jpg (+ a small preview)

Everything is drawn from kerala_geo.py, so the 3D hills and palms placed in Blender
line up with the painted coast.
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

X0, X1, Y0, Y1 = geo.SHEET
W = 6144
H = round(W * (Y1 - Y0) / (X1 - X0))
rng = np.random.default_rng(7)
prng = random.Random(7)

PARCH = np.array([231, 213, 172], np.float32)
SEA = np.array([146, 186, 204], np.float32)
SHALLOW = np.array([170, 208, 206], np.float32)
INK = (88, 62, 40)
RIVER = (92, 140, 172)
TABLE = np.array([204, 194, 178], np.float32)


def px(x, y):
    return ((x - X0) / (X1 - X0) * W, (Y1 - y) / (Y1 - Y0) * H)


def lowfreq(cell, seed):
    r = np.random.default_rng(seed)
    small = (r.random((H // cell + 3, W // cell + 3)) * 255).astype(np.uint8)
    img = Image.fromarray(small).resize((W + 3 * cell, H + 3 * cell), Image.BICUBIC)
    return np.asarray(img.crop((cell, cell, cell + W, cell + H)), np.float32) / 255.0


print("canvas", W, "x", H)
# ---------------------------------------------------------------- masks
land_img = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(land_img)
d.polygon([px(x, y) for x, y in geo.land_polygon_xy()], fill=255)
lake_img = Image.new("L", (W, H), 0)
dl = ImageDraw.Draw(lake_img)
for lat, lon, a_km, b_km, ang in geo.LAKES:
    cx, cy = geo.xy(lat, lon)
    a, b = a_km * geo.MAP_SCALE, b_km * geo.MAP_SCALE
    t = math.radians(ang)
    pts = []
    for k in range(48):
        u = k / 48 * math.tau
        ex, ey = a * math.cos(u), b * math.sin(u)
        wob = 1 + 0.12 * math.sin(3 * u + 1) + 0.08 * math.sin(7 * u)
        pts.append(px(cx + (ex * math.cos(t) - ey * math.sin(t)) * wob, cy + (ex * math.sin(t) + ey * math.cos(t)) * wob))
    dl.polygon(pts, fill=255)
land_img = Image.fromarray(np.minimum(np.asarray(land_img), 255 - np.asarray(lake_img)))
land = np.asarray(land_img, np.float32) / 255.0
water = 1.0 - land

# soft distance-like field from the coast (for shallows and waterlines)
near = np.asarray(land_img.filter(ImageFilter.GaussianBlur(70)), np.float32) / 255.0
near2 = np.asarray(land_img.filter(ImageFilter.GaussianBlur(18)), np.float32) / 255.0

# ---------------------------------------------------------------- parchment base
n1, n2, n3 = lowfreq(900, 1), lowfreq(220, 2), lowfreq(40, 3)
grain = rng.integers(0, 255, (H, W), dtype=np.uint8).astype(np.float32) / 255.0
shade = 0.86 + 0.10 * n1 + 0.05 * n2 + 0.02 * n3 + 0.025 * grain
blot = lowfreq(520, 4)
shade -= np.clip(blot - 0.64, 0, None) * 0.28
img = PARCH[None, None, :] * shade[..., None]

# ---------------------------------------------------------------- sea wash
sea_mix = water * 0.62
shallow_k = np.clip(near * 2.2, 0, 1) * water
col = SEA[None, None, :] * (1 - shallow_k[..., None]) + SHALLOW[None, None, :] * shallow_k[..., None]
col = col * (0.92 + 0.08 * n2[..., None])
img = img * (1 - sea_mix[..., None]) + col * sea_mix[..., None]

# land: faint green-ochre wash over the hills
step = 16
gh = np.zeros((H // step + 1, W // step + 1), np.float32)
for j in range(gh.shape[0]):
    y = Y1 - j * step / H * (Y1 - Y0)
    for i in range(gh.shape[1]):
        x = X0 + i * step / W * (X1 - X0)
        gh[j, i] = geo.ghats_height(x, y)
gh_img = Image.fromarray((np.clip(gh / 700.0, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
hills = np.asarray(gh_img, np.float32) / 255.0 * land
img = img * (1 - 0.32 * hills[..., None]) + np.array([168, 176, 120], np.float32) * 0.32 * hills[..., None]
del gh_img, col, shallow_k, n3, grain

# ---------------------------------------------------------------- ink layer (drawn in L, then multiplied)
ink = Image.new("L", (W, H), 0)
di = ImageDraw.Draw(ink)
edge = np.asarray(land_img.filter(ImageFilter.MaxFilter(5)), np.int16) - np.asarray(land_img.filter(ImageFilter.MinFilter(5)), np.int16)
ink_arr = np.clip(edge, 0, 255).astype(np.uint8)
# waterlines parallel to the coast
for lo, hi, strength in ((0.30, 0.325, 150), (0.16, 0.175, 110), (0.07, 0.078, 80)):
    band = (near > lo) & (near < hi) & (water > 0.5)
    ink_arr = np.maximum(ink_arr, (band * strength).astype(np.uint8))
ink = Image.fromarray(ink_arr)
di = ImageDraw.Draw(ink)

# open-sea wave marks
sea_pts = 0
while sea_pts < 900:
    x, y = prng.uniform(0, W), prng.uniform(0, H)
    if water[int(y) % H, int(x) % W] > 0.5 and near[int(y) % H, int(x) % W] < 0.03:
        w = prng.uniform(40, 70)
        for k in range(2):
            ox = x + k * w * 0.9
            di.arc([ox, y - w * 0.25, ox + w, y + w * 0.25], 200, 340, fill=110, width=4)
        sea_pts += 1

# mountain strokes along the Ghats
crest = [geo.xy(a, b) for a, b, _ in geo.GHATS]
for i in range(len(crest) - 1):
    (ax, ay), (bx, by) = crest[i], crest[i + 1]
    k = geo.GHATS[i][2]
    seg = math.hypot(bx - ax, by - ay)
    for s in np.arange(0, seg, 420):
        t = s / seg
        for off in (-1300, -650, 0, 650, 1300):
            if prng.random() < 0.25:
                continue
            nx, ny = -(by - ay) / seg, (bx - ax) / seg
            x = ax + (bx - ax) * t + nx * off + prng.uniform(-150, 150)
            y = ay + (by - ay) * t + ny * off + prng.uniform(-150, 150)
            p, q = px(x, y)
            size = (55 + 40 * k) * (1.0 - abs(off) / 2600) * prng.uniform(0.8, 1.2)
            di.line([(p - size, q + size * 0.55), (p - size * 0.1, q - size * 0.6), (p + size * 0.25, q - size * 0.1),
                     (p + size * 0.5, q - size * 0.35), (p + size, q + size * 0.55)], fill=150, width=5)
            di.line([(p - size * 0.1, q - size * 0.6), (p + size * 0.05, q + size * 0.4)], fill=90, width=3)

# grid and border
for gx in np.arange(math.ceil(X0 / 2500) * 2500, X1, 2500):
    di.line([px(gx, Y0), px(gx, Y1)], fill=70, width=3)
for gy in np.arange(math.ceil(Y0 / 2500) * 2500, Y1, 2500):
    di.line([px(X0, gy), px(X1, gy)], fill=70, width=3)
for inset, wdt in ((150, 7), (185, 3)):
    di.rectangle([inset, inset, W - inset, H - inset], outline=170, width=wdt)

ink_k = np.asarray(ink, np.float32)[..., None] / 255.0
img = img * (1 - ink_k) + np.array(INK, np.float32) * ink_k
del ink_k, edge, ink_arr

# rivers (drawn in colour, wobbling)
riv = Image.new("L", (W, H), 0)
dr = ImageDraw.Draw(riv)
for name, src, mouth in geo.RIVERS:
    (sx, sy), (mx, my) = geo.xy(*src), geo.xy(*mouth)
    L = math.hypot(mx - sx, my - sy)
    nx, ny = -(my - sy) / L, (mx - sx) / L
    ph = prng.uniform(0, 6)
    pts = []
    for k in range(61):
        t = k / 60
        wob = (math.sin(t * 9 + ph) * 0.6 + math.sin(t * 23 + ph * 2) * 0.25) * L * 0.035 * math.sin(math.pi * t)
        pts.append(px(sx + (mx - sx) * t + nx * wob, sy + (my - sy) * t + ny * wob))
    for k in range(60):
        dr.line([pts[k], pts[k + 1]], fill=255, width=int(3 + 5 * k / 60))
riv_k = (np.asarray(riv.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0 * land)[..., None]
img = img * (1 - riv_k * 0.85) + np.array(RIVER, np.float32) * riv_k * 0.85
del riv_k

# creases and stains
for cx_ in (W * 0.5,):
    k = np.exp(-((np.arange(W) - cx_) / 5.0) ** 2).astype(np.float32)
    img *= (1 - 0.07 * k)[None, :, None]
k = np.exp(-((np.arange(H) - H * 0.5) / 5.0) ** 2).astype(np.float32)
img *= (1 - 0.07 * k)[:, None, None]
yy, xx = np.ogrid[:H, :W]
for _ in range(7):
    cx_, cy_, r = prng.uniform(0, W), prng.uniform(0, H), prng.uniform(120, 420)
    ring = np.exp(-((np.sqrt((xx - cx_) ** 2 + (yy - cy_) ** 2) - r) / 12.0) ** 2).astype(np.float32)
    img *= (1 - 0.045 * ring)[..., None]

# burnt, ragged edges fading to the table
de = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy)).astype(np.float32)
de = de + (lowfreq(120, 9) - 0.5) * 160 + (lowfreq(30, 10) - 0.5) * 40
burn = np.clip((150 - de) / 110, 0, 1) ** 1.6
img = img * (1 - 0.65 * burn[..., None]) + np.array([118, 78, 40], np.float32) * 0.65 * burn[..., None]
outside = (de < 38)[..., None]
img = np.where(outside, TABLE[None, None, :], img)

out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
out.save(os.path.join(OUT, "kerala_map.jpg"), quality=92)
out.resize((W // 8, H // 8), Image.LANCZOS).save(os.path.join(OUT, "kerala_map_preview.jpg"), quality=90)
print("wrote", os.path.join(OUT, "kerala_map.jpg"))
