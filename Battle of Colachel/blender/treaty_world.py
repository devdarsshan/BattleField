"""The treaty tent at Mavelikkara (S62; clip 75, ref K75): Dutch and Travancore envoys sign the scroll.

A floating ground tile on a pale warm backdrop. A gabled cream marquee, ridge running front to back, open at the
front, canvas down to the ground at the sides, a red valance along the gable edges and the eaves, poles and guy
ropes. Inside, a long table (running into the tent) with a scroll, quills and inkwells; Dutch officers (wigs, blue
coats) along the left and at the far end, Travancore envoys (red turbans, white mundus) along the right; guards in
front: Dutch soldiers at the left, Nairs with shields at the right; palms and bushes at the sides. No text.
Coordinates: metres, ground top at z = 0, the tent's front gable at y = -4.2, the camera looks from -x / -y.
"""
import math
import random

import bpy
from mathutils import Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S
import landing_world as lw
import mini_dio as md

face = lw._face
TW, TD = 9.2, 8.4                        # tent width (x) and depth (y)
BACK_Y = TD / 2
RIDGE_Z = 4.1
TABLE_Y = 0.6
SEAT = kit.SEAT_H


def register_palette():
    for k, v in {"tent_cream": (0.93, 0.89, 0.76), "tent_cream_dk": (0.82, 0.77, 0.63), "valance": (0.62, 0.12, 0.16),
                 "scroll": (0.93, 0.89, 0.76), "ink": (0.10, 0.09, 0.10), "chair": (0.38, 0.22, 0.12),
                 "tablecloth": (0.55, 0.14, 0.16), "sand_path": (0.84, 0.72, 0.50), "candle": (0.94, 0.90, 0.80)}.items():
        kit.PALETTE.setdefault(k, v)
        kit.mat(k, kit.PALETTE[k])


def quad(mb, a, b, c, d, m):
    mb.face([mb.bm.verts.new(p) for p in (a, b, c, d)], m)


def make_tent(c):
    """Gabled marquee (K75): ridge along y, front gable open, sloping canvas to the ground at the sides."""
    mb = kit.MB()
    hx, fy, by = TW / 2, -TD / 2, TD / 2
    eave = 1.7
    n = 8
    for side in (-1, 1):
        for i in range(n):
            ya, yb = fy + TD * i / n, fy + TD * (i + 1) / n
            m = "tent_cream" if i % 2 == 0 else "tent_cream_dk"
            quad(mb, (side * hx, ya, eave), (side * hx, yb, eave), (0.0, yb, RIDGE_Z), (0.0, ya, RIDGE_Z), m)
            quad(mb, (side * (hx + 0.55), ya, 0.0), (side * (hx + 0.55), yb, 0.0), (side * hx, yb, eave), (side * hx, ya, eave), m)
    mb.face([mb.bm.verts.new(p) for p in ((-hx, by, eave), (hx, by, eave), (0.0, by, RIDGE_Z))], "tent_cream_dk")
    quad(mb, (-hx - 0.55, by, 0.0), (hx + 0.55, by, 0.0), (hx, by, eave), (-hx, by, eave), "tent_cream_dk")
    # the red valance: along both front gable edges, scalloped along the eaves
    for side in (-1, 1):
        quad(mb, (side * hx, fy, eave), (0.0, fy, RIDGE_Z), (0.0, fy - 0.03, RIDGE_Z - 0.42), (side * hx, fy - 0.03, eave - 0.42), "valance")
        for i in range(n):
            ya, yb = fy + TD * i / n, fy + TD * (i + 1) / n
            mb.face([mb.bm.verts.new(p) for p in ((side * hx, ya, eave), (side * hx, yb, eave), (side * (hx + 0.03), (ya + yb) / 2, eave - 0.4))], "valance")
    # poles and guy ropes
    mb.seg((0, by, 0), (0, by, RIDGE_Z + 0.2), 0.07, 0.06, "post", sides=6)
    mb.seg((0, fy, RIDGE_Z), (0, by, RIDGE_Z), 0.05, 0.05, "post", sides=5)
    for sx in (-1, 1):
        mb.seg((sx * hx, fy, 0), (sx * hx, fy, eave + 0.1), 0.06, 0.05, "post", sides=5)
    for px, py in ((-hx - 1.6, fy - 1.0), (hx + 1.6, fy - 1.0), (-hx - 1.6, by + 1.0), (hx + 1.6, by + 1.0)):
        mb.seg((px * 0.5, py * 0.85, eave + 1.1), (px, py, 0.0), 0.025, 0.02, "post", sides=4)
    # a sand floor and a red carpet under the table
    mb.box(T(0, 0, 0.012) @ S(TW + 0.5, TD + 0.5, 0.02), "sand_path")
    mb.box(T(0, TABLE_Y, 0.03) @ S(3.6, 6.4, 0.03), "carpet_red")
    return mb.obj("TreatyTent", c)


def make_table(c):
    mb = kit.MB(bevel=0.02)
    L, Wd = 5.6, 1.15
    mb.box(T(0, 0, 0.78) @ S(Wd, L, 0.09), "table")
    for sx in (-1, 1):
        mb.box(T(sx * (Wd / 2 - 0.01), 0, 0.6) @ S(0.03, L, 0.34), "tablecloth")
    for sy in (-1, 1):
        mb.box(T(0, sy * (L / 2 - 0.01), 0.6) @ S(Wd, 0.03, 0.34), "tablecloth")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * 0.45, sy * (L / 2 - 0.2), 0), (sx * 0.45, sy * (L / 2 - 0.2), 0.75), 0.07, 0.06, "post", sides=5)
    # the treaty: a long scroll with a ribbon, loose sheets, inkwells with quills, brass candlesticks
    mb.box(T(0.0, -0.1, 0.835) @ Rz(0.03) @ S(0.62, 2.3, 0.012), "scroll")
    mb.seg((0.0, -1.3, 0.86), (0.05, -1.3, 0.86), 0.05, 0.05, "scroll", sides=8)
    mb.seg((0.0, 1.05, 0.86), (0.05, 1.05, 0.86), 0.05, 0.05, "scroll", sides=8)
    mb.box(T(0.0, -0.1, 0.842) @ S(0.76, 0.08, 0.01), "valance")
    for k, (x, y) in enumerate(((-0.4, -1.9), (0.4, -1.4), (-0.4, 0.7), (0.4, 1.4), (-0.4, 2.0), (0.4, -0.5))):
        mb.box(T(x, y, 0.835) @ Rz(0.2 * (k - 2)) @ S(0.34, 0.45, 0.01), "parchment")
        mb.cone(T(x * 1.35, y, 0.86), "ink", segments=7, r1=0.055, r2=0.045, depth=0.09)
        mb.seg((x * 1.35, y, 0.9), (x * 1.35 + 0.1, y - 0.05, 1.06), 0.009, 0.005, "white", sides=4)
    for y in (-2.45, 2.45):
        mb.cone(T(0, y, 0.88), "brass", segments=8, r1=0.09, r2=0.05, depth=0.08)
        mb.seg((0, y, 0.9), (0, y, 1.2), 0.03, 0.03, "brass", sides=6)
        mb.cone(T(0, y, 1.28), "candle", segments=6, r1=0.04, r2=0.04, depth=0.16)
    ob = mb.obj("TreatyTable", c)
    ob.location = (0, TABLE_Y, 0)
    return ob


def make_chair(name, c, h=1.1):
    mb = kit.MB(bevel=0.015)
    mb.box(T(0, 0, SEAT - 0.04) @ S(0.62, 0.6, 0.08), "chair")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * 0.26, sy * 0.25, 0), (sx * 0.26, sy * 0.25, SEAT - 0.06), 0.035, 0.03, "chair", sides=4)
    mb.box(T(0, -0.27, SEAT + (h - SEAT) / 2 + 0.05) @ S(0.62, 0.06, h - SEAT), "chair")
    for sx in (-1, 1):
        mb.seg((sx * 0.29, -0.27, SEAT), (sx * 0.29, -0.27, h + 0.1), 0.03, 0.03, "chair", sides=4)
    return mb.obj(name, c)


def build_treaty(c, lib_c, rng, ev):
    register_palette()
    make_tent(c)
    make_table(c)
    ty = TABLE_Y
    sx_ = 1.05
    seats = [(0.0, ty + 3.35, (0, -1), "dutch", 3), (-sx_, ty + 1.9, (1, 0), "dutch", 5), (-sx_, ty + 0.6, (1, 0), "dutch", 6),
             (-sx_, ty - 0.7, (1, 0), "dutch", 7), (-sx_, ty - 2.0, (1, 0), "dutch", 8),
             (sx_, ty + 1.9, (-1, 0), "commander", 2), (sx_, ty + 0.6, (-1, 0), "commander", 4),
             (sx_, ty - 0.7, (-1, 0), "commander", 5), (sx_, ty - 2.0, (-1, 0), "commander", 6)]
    chair = make_chair("LibChair", lib_c)
    kit.hide_source(chair)
    for k, (x, y, fc, kind, seed) in enumerate(seats):
        kit.instance(chair, f"Chair{k}", c, (x, y, 0.0), rot_z=face(fc[0], fc[1]))
        fig = kit.make_figure(f"Envoy{k}", c, kind, seed=seed, pose="sit")
        fig.location = (x, y, 0.0)
        fig.rotation_euler[2] = face(fc[0], fc[1])
        kit.animate_idle(fig, rng, 1, ev["end"], amount=0.015)
    guards = [(-3.6, -5.4, (0.9, 0.5), "dutch", 11), (-4.6, -4.8, (0.9, 0.5), "dutch", 12), (-3.3, -4.4, (0.9, 0.5), "dutch", 13),
              (-4.4, -6.2, (0.9, 0.5), "dutch", 14), (4.4, -5.0, (-0.9, 0.5), "nair", 15), (5.2, -4.6, (-0.9, 0.5), "nair_spear", 16)]
    for k, (x, y, fc, kind, seed) in enumerate(guards):
        g = kit.make_figure(f"Guard{k}", c, kind, seed=seed)
        g.location = (x, y, 0.0)
        g.rotation_euler[2] = face(fc[0], fc[1])
        kit.animate_idle(g, rng, 1, ev["end"], amount=0.02)
    # palms and bushes at the tent's sides
    palms = [kit.make_palm(f"LibTrPalm{i}", lib_c, seed=60 + i, height=8.0 + i * 0.6) for i in range(3)]
    bushes = [kit.make_bush(f"LibTrBush{i}", lib_c, seed=50 + i, size=1.0 + 0.2 * i) for i in range(3)]
    for s_ in palms + bushes:
        kit.hide_source(s_)
    for k, (x, y) in enumerate(((-6.4, 3.4), (-7.2, 0.6), (-6.0, 6.0), (6.6, 3.0), (7.4, -0.2), (6.2, 6.0))):
        kit.instance(palms[k % 3], f"TrPalm{k}", c, (x, y, 0.0), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.95, 1.1))
    for k, (x, y) in enumerate(((-6.0, -2.2), (-6.9, 2.0), (6.0, -2.4), (7.0, 2.4), (-4.2, 6.6), (4.4, 6.8), (-2.0, 7.0), (2.4, 7.2))):
        kit.instance(bushes[k % 3], f"TrBush{k}", c, (x, y, 0.0), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.9, 1.3))
    # a sand path to the tent mouth
    mb = kit.MB()
    for i in range(7):
        yy = -4.6 - i * 1.0
        mb.box(T(-0.4 + 0.5 * math.sin(i * 0.9), yy, 0.01) @ Rz(rng.uniform(-0.2, 0.2)) @ S(3.4 - i * 0.15, 1.3, 0.03), "sand_path")
    mb.obj("SandPath", c)
