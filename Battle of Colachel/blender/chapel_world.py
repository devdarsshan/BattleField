"""The small stone chapel inside Udayagiri fort (S60; clip 73, ref K73): De Lannoy's tomb.

A floating ground tile on a dark backdrop. A stone chapel open to the front: a back wall with three arched
recesses (the middle one a tall window that lets a shaft of warm light fall on the tomb), a left wall with two
arched windows, a broken low right wall, stone vault ribs, a flagstone floor, the sarcophagus on a plinth with a
plain carved cross, candles in dishes, a wooden bench, ivy and bushes on the ruined top. No text anywhere.
Coordinates: metres, tile top at z = 0, the back wall at y = +4.6, the camera looks from -y / +x.
"""
import math
import random

import bpy
from mathutils import Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S
import mini_dio as md

BACK_Y = 4.4
HALF_X = 2.9
SPRING = 2.5


def register_palette():
    for k, v in {"chapel_glow": (1.0, 0.92, 0.72), "ivy": (0.28, 0.42, 0.20), "tomb": (0.58, 0.55, 0.50),
                 "tomb_lt": (0.68, 0.65, 0.59), "candle": (0.94, 0.90, 0.80)}.items():
        kit.PALETTE.setdefault(k, v)
        kit.mat(k, kit.PALETTE[k])


def arch_pts(w, spring, n=7, rf=0.62):
    """Outline points (u, z, tangent angle) of a pointed arch of span w, springing at height `spring`, left to right
    over the apex. Two arcs of radius rf * w (rf = 1 is an equilateral arch, smaller is a flatter point)."""
    R = rf * w
    uc = -w / 2 + R
    th_a = math.acos((-uc) / R)                                   # angle at the apex (u = 0)
    left = []
    for i in range(n + 1):
        t = math.pi - (math.pi - th_a) * i / n
        left.append((uc + R * math.cos(t), spring + R * math.sin(t), t - math.pi / 2))
    right = [(-u, z, -tg) for (u, z, tg) in reversed(left[:-1])]
    return left + right


def pointed_arch(mb, cx, y, z0, w, spring, normal, fill, ring="fort_stone_lt", axis="x", depth=0.22, blocks=True, thick=0.36):
    """A pointed-arch recess drawn on a wall face (axis 'x': the face runs along X at height y; axis 'y': it runs along
    Y at x = y): a fill (dark or glowing) inside a ring of voussoir blocks and jamb blocks."""
    pts = arch_pts(w, spring)

    def w3(u, z, off):
        if axis == "x":
            return (cx + u, y + normal * off, z)
        return (y + normal * off, cx + u, z)

    outline = [(-w / 2, z0), (w / 2, z0)] + [(u, z) for u, z, _ in pts[::-1]]
    vs = [mb.bm.verts.new(w3(u, z, 0.0)) for u, z in outline]
    mid = mb.bm.verts.new(w3(0.0, (z0 + spring) / 2, 0.0))
    for i in range(len(vs)):
        mb.face([mid, vs[i], vs[(i + 1) % len(vs)]], fill)
    if blocks:
        for u, z, tg in pts:
            p = w3(u * 1.0, z, 0.07)
            if axis == "x":
                mb.box(T(*p) @ Ry(-tg) @ S(0.34, depth, thick), ring)
            else:
                mb.box(T(*p) @ Rz(math.pi / 2) @ Ry(-tg) @ S(0.34, depth, thick), ring)
        for sgn in (-1, 1):
            n_ = max(1, int((spring - z0) / 0.55))
            for k in range(n_):
                zz = z0 + (k + 0.5) * (spring - z0) / n_
                p = w3(sgn * (w / 2 + 0.05), zz, 0.07)
                if axis == "x":
                    mb.box(T(*p) @ S(0.32, depth, (spring - z0) / n_ - 0.04), ring)
                else:
                    mb.box(T(*p) @ S(depth, 0.32, (spring - z0) / n_ - 0.04), ring)


def pointed_rib(mb, y, span, spring, mat="fort_stone", thick=0.62):
    """A freestanding pointed arch of chunky blocks across the chapel at depth y (a stone rib)."""
    for u, z, tg in arch_pts(span, spring, n=12):
        mb.box(T(u, y, z) @ Ry(-tg) @ S(0.62, thick, 0.46), mat)
    for sgn in (-1, 1):
        n_ = max(1, int(spring / 0.5))
        for k in range(n_):
            mb.box(T(sgn * (span / 2), y, (k + 0.5) * spring / n_) @ S(0.46, thick, spring / n_ - 0.03), mat)


def make_tomb(c):
    mb = kit.MB(bevel=0.03)
    mb.box(T(0, 0, 0.1) @ S(3.9, 2.3, 0.2), "tomb")
    mb.box(T(0, 0, 0.3) @ S(3.4, 1.9, 0.2), "tomb_lt")
    mb.box(T(0, 0, 0.9) @ S(2.7, 1.2, 1.0), "tomb")
    mb.box(T(0, 0, 1.45) @ S(2.95, 1.4, 0.18), "tomb_lt")
    mb.box(T(0, 0, 1.6) @ S(2.5, 1.0, 0.12), "tomb")
    # a plain raised cross on the lid, and a small carved panel on the face
    mb.box(T(0, 0, 1.7) @ S(1.5, 0.12, 0.08), "tomb_lt")
    mb.box(T(-0.1, 0, 1.7) @ S(0.12, 0.7, 0.08), "tomb_lt")
    mb.box(T(0, -0.62, 0.95) @ S(1.4, 0.04, 0.55), "fort_stone_dk")
    return mb.obj("Tomb", c)


def make_candle(c, name, h=0.4):
    mb = kit.MB()
    mb.cone(T(0, 0, 0.02), "brass", segments=8, r1=0.16, r2=0.12, depth=0.04)
    mb.cone(T(0, 0, 0.04 + h / 2), "candle", segments=8, r1=0.055, r2=0.05, depth=h)
    ob = mb.obj(name, c)
    fm = kit.MB()
    fm.cone(T(0, 0, 0.12), "fx_core", segments=5, r1=0.075, r2=0.0, depth=0.28)
    fl = fm.obj(name + "Flame", c)
    fl.location = (0, 0, 0.04 + h)
    fl.parent = ob
    return ob, fl


def make_bench(c):
    mb = kit.MB(bevel=0.02)
    mb.box(T(0, 0, 0.5) @ S(2.6, 0.55, 0.1), "plank")
    for sx in (-1, 1):
        mb.box(T(sx * 1.15, 0, 0.25) @ S(0.12, 0.45, 0.5), "plank")
    return mb.obj("Bench", c)


def build_chapel(c, lib_c, rng, ev):
    register_palette()
    for k, v in {"fort_stone": (0.66, 0.58, 0.47), "fort_stone_dk": (0.50, 0.43, 0.35), "fort_stone_lt": (0.78, 0.69, 0.56),
                 "fort_grey": (0.52, 0.46, 0.40), "flag_a": (0.70, 0.62, 0.50), "flag_b": (0.60, 0.53, 0.43), "flag_c": (0.78, 0.70, 0.57)}.items():
        kit.PALETTE[k] = v
    kit.fx_materials()
    # floor: irregular flagstones over the whole footprint
    kit.make_flagstones("ChapelFloor", c, -HALF_X - 0.6, HALF_X + 0.6, -4.6, BACK_Y, seed=3, step=(1.25, 1.0))
    hw = HALF_X + 0.35
    # back wall: blocks up to the springing, then a pointed gable
    back = kit.make_stone_wall("BackWall", c, 2 * hw + 0.7, SPRING + 1.8, thick=0.9, seed=4, crenel=False)
    back.location = (0, BACK_Y + 0.45, 0)
    gb = kit.MB(bevel=0.03)
    zt = SPRING + 1.8
    for u, z, tg in arch_pts(2 * hw + 0.7, zt, n=12):
        gb.box(T(u, BACK_Y + 0.45, z) @ Ry(-tg) @ S(0.62, 1.0, 0.5), "fort_stone")
    for k in range(10):                                            # fill under the gable
        uu = -hw + k * 2 * hw / 9
        top = zt + (0.58 * (2 * hw + 0.7)) * (1 - abs(uu) / (hw + 0.35)) * 0.9
        gb.box(T(uu, BACK_Y + 0.45, (zt + top) / 2) @ S(2 * hw / 9 + 0.1, 0.84, max(0.1, top - zt)), "fort_stone")
    gb.obj("BackGable", c)
    # left wall and a low broken right wall
    left = kit.make_stone_wall("LeftWall", c, 9.6, SPRING + 1.4, thick=0.8, seed=5, crenel=False)
    left.location = (-HALF_X - 0.45, 0.2, 0)
    left.rotation_euler[2] = math.pi / 2
    right = kit.make_stone_wall("RightWall", c, 9.6, 1.5, thick=0.8, seed=6, crenel=False)
    right.location = (HALF_X + 0.45, 0.2, 0)
    right.rotation_euler[2] = math.pi / 2
    # arched recesses on the inner faces: the window in the back wall (glowing), panels in the left and back walls
    mb = kit.MB()
    fy = BACK_Y - 0.01
    pointed_arch(mb, 0.0, fy, 0.9, 1.7, 4.2, -1, "chapel_glow")
    pointed_arch(mb, -1.0, -HALF_X, 0.0, 1.9, 2.7, 1, "fort_stone_dk", axis="y")
    pointed_arch(mb, 2.3, -HALF_X, 0.0, 1.9, 2.7, 1, "fort_stone_dk", axis="y")
    pointed_arch(mb, -1.9, fy, 0.0, 1.5, 2.6, -1, "fort_stone_dk")
    pointed_arch(mb, 1.9, fy, 0.0, 1.5, 2.6, -1, "fort_stone_dk")
    mb.obj("ArchPanels", c)
    pane = bpy.data.objects["ArchPanels"]
    glow = kit.mat_emit("ChapelGlowMat", (1.0, 0.92, 0.72), 3.0)
    for i, m in enumerate(pane.data.materials):
        if m and m.name == "chapel_glow":
            pane.data.materials[i] = glow
    cm = kit.MB()
    cm.box(T(0.0, BACK_Y - 0.3, 3.0) @ S(0.1, 0.1, 3.1), "fort_stone_dk")
    cm.box(T(0.0, BACK_Y - 0.3, 3.1) @ S(1.5, 0.1, 0.1), "fort_stone_dk")
    cm.obj("WindowCross", c)
    # pointed stone ribs across the nave, and sloping roof slabs over the left half between the back ribs
    rb = kit.MB(bevel=0.03)
    for y in (-4.1, -1.5, 1.1, 3.7):
        pointed_rib(rb, y, 2 * HALF_X, SPRING)
    rb.obj("VaultRibs", c)
    rf = kit.MB(bevel=0.03)
    for (y0, y1) in ((-1.5, 1.1), (1.1, 3.7)):
        x0, z0 = -HALF_X, SPRING + 0.2
        x1, z1 = -0.35, SPRING + 0.58 * 2 * HALF_X - 0.5
        L = math.hypot(x1 - x0, z1 - z0)
        ang = math.atan2(z1 - z0, x1 - x0)
        rf.box(T((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2 + 0.2) @ Ry(-ang) @ S(L, y1 - y0 - 0.12, 0.26), "fort_grey")
    rf.obj("RoofSlabs", c)
    # tomb, candles, bench
    tomb = make_tomb(c)
    tomb.location = (0.2, -0.5, 0.0)
    for i, (x, y, h) in enumerate(((-1.9, -1.9, 0.5), (2.2, -1.7, 0.6), (-1.7, 0.9, 0.45), (2.2, 0.6, 0.55), (0.3, -2.3, 0.4))):
        cd, fm = make_candle(c, f"Candle{i}", h)
        cd.location = (x, y, 0.07)
        ld = bpy.data.lights.new(f"CandleLight{i}", "POINT")
        ld.color = (1.0, 0.62, 0.30)
        ld.energy = 170.0
        ld.shadow_soft_size = 0.15
        lo = bpy.data.objects.new(f"CandleLight{i}", ld)
        c.objects.link(lo)
        lo.location = (x, y, 0.07 + h + 0.2)
        md.flicker(ld, "energy", 170.0, 0.28, 1, ev["end"], rng)
    for i, (x, y) in enumerate(((-0.8, 0.0), (1.3, 0.1))):
        cd, fm = make_candle(c, f"TombCandle{i}", 0.38)
        cd.location = (0.2 + x, -0.5 + y, 1.66)
        ld = bpy.data.lights.new(f"TombCandleLight{i}", "POINT")
        ld.color = (1.0, 0.62, 0.30)
        ld.energy = 110.0
        ld.shadow_soft_size = 0.12
        lo = bpy.data.objects.new(f"TombCandleLight{i}", ld)
        c.objects.link(lo)
        lo.location = (0.2 + x, -0.5 + y, 2.2)
        md.flicker(ld, "energy", 110.0, 0.3, 1, ev["end"], rng)
    bench = make_bench(c)
    bench.location = (-HALF_X + 0.5, -2.6, 0.0)
    bench.rotation_euler[2] = math.pi / 2
    # a shaft of window light onto the tomb
    sp = bpy.data.lights.new("WindowLight", "SPOT")
    sp.color = (1.0, 0.90, 0.68)
    sp.energy = 9000.0
    sp.spot_size = math.radians(48)
    sp.spot_blend = 0.5
    sp.shadow_soft_size = 0.5
    so = bpy.data.objects.new("WindowLight", sp)
    c.objects.link(so)
    so.location = (0.0, BACK_Y - 0.3, 3.0)
    so.rotation_euler = (Vector((0.2, -0.5, 1.0)) - so.location).to_track_quat("-Z", "Y").to_euler()
    # ivy, bushes and rocks on the ruined top and round the base
    bushes = [kit.make_bush(f"LibChBush{i}", lib_c, seed=30 + i, size=0.8 + 0.2 * i) for i in range(3)]
    rocks = [kit.make_rock(f"LibChRock{i}", lib_c, seed=40 + i, size=0.4 + 0.25 * i) for i in range(3)]
    for s_ in bushes + rocks:
        kit.hide_source(s_)
    for k, (x, y, z) in enumerate(((-2.4, BACK_Y + 0.45, SPRING + 3.4), (1.6, BACK_Y + 0.45, SPRING + 2.9), (-HALF_X - 0.45, -2.5, SPRING + 1.4),
                                   (-HALF_X - 0.45, 2.0, SPRING + 1.4), (HALF_X + 0.45, -3.0, 1.5), (HALF_X + 0.45, 1.0, 1.5))):
        kit.instance(bushes[k % 3], f"WallBush{k}", c, (x, y, z), rot_z=rng.uniform(0, 6.28), scale=0.9)
    for k in range(18):
        x, y = rng.uniform(-6.0, 6.0), rng.uniform(-6.0, 5.8)
        if abs(x) < HALF_X + 1.0 and -4.8 < y < BACK_Y + 1.0:
            continue
        kit.instance((bushes + rocks)[k % 6], f"ChOutside{k}", c, (x, y, 0.0), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.8, 1.4))
