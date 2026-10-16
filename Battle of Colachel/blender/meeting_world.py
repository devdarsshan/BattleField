"""The meeting under the royal canopy (S21-S23, shot-list clips 27-30), Meeting.blend.

Laid out to match the Flow references frames/flow_refs/K27.jpeg (S21-S22: van Imhoff,
backed by two musketeers, points firmly at Marthanda Varma, seated on his throne with Nair
guards behind him; a low table between them) and K30.jpeg (S23: the king on his throne,
arms folded, calm, a draped canopy and dense green planting behind).

The set: an open, sandy clearing in a palm grove; a big cloth canopy with a red valance
over a red and gold carpet; the throne, a side table with a brass pot, standing brass oil
lamps; white tents to both sides; raised planting beds and hedges; rows of palms several
deep, broadleaf trees and banana clumps; tiled palace roofs among the palms behind. Sky,
sun and haze are colachel_world.scene_base; every figure is a kit figure (Imhoff and the
king are posable kit rigs: kit.make_rig).

Coordinates: metres, Z up, ground ~0. The canopy is centred near the origin. The opening
camera looks north (+Y) from the south, so +X is screen right: the Dutch stand on the left
(west), the king sits on the right (east), facing west toward Imhoff.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import colachel_kit as kit
import colachel_world as cw
import palace_world as pw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau

CANOPY = (0.0, 0.5)            # centre of the canopy
CANOPY_W, CANOPY_D, CANOPY_H = 4.4, 3.6, 3.0
THRONE = (1.45, 0.95)
THRONE_RZ = math.radians(135)  # the throne and king face west and a little toward the camera
IMHOFF = (-1.0, 0.3)
IMHOFF_RZ = math.radians(-90)
CLEARING_R = 13.0


def face(dx, dy):
    """rot_z that turns a kit figure (facing +Y) toward direction (dx, dy)."""
    return math.atan2(-dx, dy)


def _n(x, y, s, o=0.0):
    return math.sin(x / s + o) * math.cos(y / (s * 1.3) + o * 0.7)


def height(x, y):
    """Flat clearing, gently rolling grove, a slow rise to the north."""
    r = math.hypot(x, (y - 2.0) * 0.9)
    h = 0.25 * _n(x, y, 9.0, 1.1) + 0.12 * _n(x, y, 3.5, 2.3)
    h *= kit_smooth(CLEARING_R - 2, CLEARING_R + 8, r)
    h += max(0.0, y - 25.0) * 0.06
    return h


def kit_smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def in_clearing(x, y, pad=0.0):
    return math.hypot(x, (y - 2.0) * 0.9) < CLEARING_R + pad + 1.5 * _n(x, y, 4.0, 0.7)


def on_path(x, y):
    """Sandy avenue running north from the canopy toward the palace."""
    return abs(x - 4.0 - 0.08 * (y - 10)) < 2.2 + 0.4 * _n(x, y, 3.0) and y > 8


def make_ground(coll, seed=5):
    rng = random.Random(seed)
    xs = pw._axis([-220, -60, -30, 30, 60, 220], [20, 4, 1.5, 4, 20])
    ys = pw._axis([-120, -30, -12, 30, 70, 260], [20, 4, 1.5, 4, 20])
    bm = bmesh.new()
    grid = []
    for j, (y, sy) in enumerate(ys):
        row = []
        for i, (x, sx) in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                jx, jy = rng.uniform(-0.28, 0.28) * sx, rng.uniform(-0.28, 0.28) * sy
            px, py = x + jx, y + jy
            row.append(bm.verts.new((px, py, height(px, py))))
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    mats = ["sand", "court", "grass", "grass_lt", "jungle"]
    for f in bm.faces:
        x, y, z = f.calc_center_median()
        if in_clearing(x, y) or on_path(x, y):
            m = "sand" if rng.random() > 0.25 else "court"
        elif in_clearing(x, y, 2.5):
            m = "court"
        else:
            k = _n(x, y, 7.0, 3.3)
            m = "grass_lt" if k > 0.2 else ("jungle" if k < -0.45 else "grass")
        f.material_index = mats.index(m)
    me = bpy.data.meshes.new("Ground")
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Ground", me)
    coll.objects.link(ob)
    return ob


# ------------------------------------------------------------------- the royal set
def carpet_pattern(coll, w, d):
    """Gold border motifs, corner pieces and a centre medallion on the canopy's red carpet."""
    mb = kit.MB()
    z = 0.052
    bw = 0.32

    def flat(cx, cy, sx, sy, zz, m, rot=0.0):
        mb.box(T(cx, cy, zz) @ Rz(rot) @ S(sx, sy, 0.004), m)

    for sgn in (-1, 1):                                      # inner gold rule
        flat(0, sgn * (d / 2 - bw), w - 2 * bw, 0.05, z, "carpet_gold")
        flat(sgn * (w / 2 - bw), 0, 0.05, d - 2 * bw, z, "carpet_gold")
    for side in range(4):                                    # diamonds round the border band
        L = (w if side % 2 == 0 else d) - 0.3
        n = int(L / 0.38)
        off = (d if side % 2 == 0 else w) / 2 - bw / 2 - 0.02
        for i in range(n):
            t = -L / 2 + (i + 0.5) * L / n
            cx, cy = [(t, -off), (off, t), (t, off), (-off, t)][side]
            flat(cx, cy, 0.13, 0.13, z, "carpet_gold" if i % 2 == 0 else "red", rot=math.pi / 4)
    flat(0, 0, 1.2, 1.2, z, "carpet_gold", rot=math.pi / 4)           # medallion
    flat(0, 0, 0.95, 0.95, z + 0.002, "carpet_red", rot=math.pi / 4)
    flat(0, 0, 0.55, 0.55, z + 0.004, "carpet_gold", rot=math.pi / 4)
    for a in range(4):
        ang = a * math.pi / 2
        flat(1.0 * math.cos(ang), 0.75 * math.sin(ang), 0.42, 0.12, z, "carpet_gold", rot=ang)
    fx, fy = w / 2 - bw - 0.35, d / 2 - bw - 0.3
    for sx in (-1, 1):
        for sy in (-1, 1):
            flat(sx * fx, sy * fy, 0.55, 0.1, z, "carpet_gold")
            flat(sx * (fx + 0.22), sy * (fy - 0.18), 0.1, 0.45, z, "carpet_gold")
            flat(sx * (fx - 0.1), sy * (fy - 0.15), 0.16, 0.16, z, "carpet_gold", rot=math.pi / 4)
    return mb.obj("CarpetPattern", coll)


def make_side_table(name, coll):
    """Small carved side table with a brass water pot (kindi) and a cup (K30)."""
    mb = kit.MB(bevel=0.008)
    mb.box(T(0, 0, 0.6) @ S(0.5, 0.5, 0.05), "plank")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * 0.2, sy * 0.2, 0), (sx * 0.2, sy * 0.2, 0.58), 0.03, 0.025, "post", sides=6)
    mb.cone(T(0, 0, 0.72), "brass", segments=10, r1=0.07, r2=0.11, depth=0.14)
    mb.cone(T(0, 0, 0.84), "brass", segments=10, r1=0.11, r2=0.035, depth=0.12)
    mb.cone(T(0, 0, 0.95), "brass", segments=8, r1=0.03, r2=0.045, depth=0.1)
    mb.seg((0.09, 0, 0.78), (0.18, 0, 0.86), 0.015, 0.01, "brass", sides=5)
    mb.cone(T(-0.15, 0.1, 0.66), "gold", segments=8, r1=0.035, r2=0.05, depth=0.07)
    return mb.obj(name, coll)


def build_royal_set(coll, lib_c, frames, rng):
    cx, cy = CANOPY
    can = kit.make_canopy("Canopy", coll, w=CANOPY_W, d=CANOPY_D, h=CANOPY_H)
    can.location = (cx, cy, 0.0)
    pat = carpet_pattern(coll, CANOPY_W * 0.78, CANOPY_D * 0.72)
    pat.location = (cx, cy, 0.0)
    # gathered drapes at the two rear posts, hanging along the side edges (K30; K27's front stays open)
    for sx in (-1, 1):
        for sy in (1,):
            dr = kit.make_drape(f"Drape{sx}{sy}", coll, h=CANOPY_H - 0.3, w=0.55, seed=sx + 3 * sy)
            dr.location = (cx + sx * CANOPY_W / 2, cy + sy * CANOPY_D / 2, 0.0)
            dr.rotation_euler[2] = math.pi / 2 if sy < 0 else -math.pi / 2
    # throne, side table, brass lamps
    th = kit.make_throne("Throne", coll)
    th.location = (THRONE[0], THRONE[1], 0.05)
    th.rotation_euler[2] = THRONE_RZ
    st = make_side_table("SideTable", coll)
    st.location = (THRONE[0] - 0.7, THRONE[1] + 0.62, 0.05)          # at the king's left hand (K30)
    for i, (x, y) in enumerate(((1.95, 2.05), (-1.95, 2.05))):
        lamp = kit.make_brass_lamp(f"Lamp{i}", coll, h=1.45)
        lamp.location = (x, y, 0.05)
    # papers and brass on the table (the kit canopy's low table at its centre-front)
    mb = kit.MB(bevel=0.004)
    tz = 0.49
    for k in range(3):
        mb.box(T(cx - 0.3 + k * 0.01, cy - 0.32, tz + 0.006 + k * 0.01) @ Rz(0.1 - k * 0.05) @ S(0.42, 0.3, 0.008),
               "parchment")
    mb.seg((cx + 0.1, cy - 0.15, tz + 0.04), (cx + 0.45, cy - 0.2, tz + 0.04), 0.035, 0.035, "parchment", sides=8)
    mb.cone(T(cx + 0.55, cy - 0.45, tz + 0.04), "brass", segments=8, r1=0.05, r2=0.04, depth=0.08)
    mb.box(T(cx + 0.25, cy - 0.45, tz + 0.02) @ S(0.25, 0.15, 0.04), "plank")
    mb.obj("TableProps", coll)


# ------------------------------------------------------------------- people
def build_cast(coll, lib_c, frames, rng):
    """Imhoff and the king as posable kit rigs; musketeers and Nair guards as kit figures."""
    imhoff, ip = kit.make_rig("VanImhoff", coll, "imhoff")
    imhoff.location = (IMHOFF[0], IMHOFF[1], height(*IMHOFF) + 0.05)
    imhoff.rotation_euler[2] = IMHOFF_RZ
    king, kp = kit.make_rig("MarthandaVarma", coll, "king", seated=True, fold=True)
    king.location = (THRONE[0], THRONE[1], 0.11)
    king.rotation_euler[2] = THRONE_RZ
    king.scale = (1.04, 1.04, 1.04)
    # two musketeers behind Imhoff (K27), muskets at the shoulder
    dutch = kit.make_figure("LibDutch", lib_c, "dutch", seed=2)
    for i, (x, y) in enumerate(((-2.6, -0.1), (-2.05, 1.0))):
        ob = kit.instance(dutch, f"Musketeer{i}", coll, (x, y, 0.05), rot_z=face(1, -0.15))
        kit.animate_idle(ob, rng, 1, frames, 0.012)
    # Nair guards with shields and spears round the throne (K27, K30)
    nairs = [kit.make_figure(f"LibNair{i}", lib_c, "nair_spear", seed=20 + i) for i in range(3)]
    guards = [(-0.55, 2.4), (2.2, 2.05), (2.85, 0.6), (3.0, -0.95)]
    for i, (x, y) in enumerate(guards):
        ob = kit.instance(nairs[i % 3], f"Guard{i}", coll, (x, y, 0.05), rot_z=face(-1.0, -0.55))
        kit.animate_idle(ob, rng, 1, frames, 0.015)
    return (imhoff, ip), (king, kp)


def build_crowd(coll, lib_c, frames, rng):
    """Guards along the clearing, Dutch soldiers by their tents, attendants and walkers."""
    nair = [kit.make_figure(f"LibNairB{i}", lib_c, k, seed=40 + i) for i, k in enumerate(("nair", "nair_spear", "nair_spear"))]
    for i in range(8):                                       # a line of guards across the back of the clearing
        x, y = -6.0 + 1.7 * i, 7.4 + 0.3 * (i % 2)
        if x > 1.5:                                          # keep K30's green wall behind the king clear
            continue
        ob = kit.instance(nair[i % 3], f"LineGuard{i}", coll, (x, y, height(x, y)), rot_z=face(0, -1))
        kit.animate_idle(ob, rng, 1, frames, 0.02)
    dutch = [kit.make_figure(f"LibDutchB{i}", lib_c, "dutch", seed=50 + i) for i in range(2)]
    for i, (x, y, dx, dy) in enumerate(((-7.6, -1.4, 1, 0.2), (-8.3, 0.4, 1, 0), (-6.3, 6.4, 0.5, -1),
                                         (-9.6, 6.0, 1, -0.5), (-11.0, 1.8, 1, 0))):
        ob = kit.instance(dutch[i % 2], f"DutchGuard{i}", coll, (x, y, height(x, y)), rot_z=face(dx, dy))
        kit.animate_idle(ob, rng, 1, frames, 0.02)
    commander = kit.make_figure("LibCourtier", lib_c, "commander", seed=60)
    for i, (x, y) in enumerate(((5.2, 3.4), (5.9, 2.4))):    # two courtiers waiting behind the guards
        ob = kit.instance(commander, f"Courtier{i}", coll, (x, y, height(x, y)), rot_z=face(-1, -0.3))
        kit.animate_idle(ob, rng, 1, frames, 0.02)
    walks = [([(-14, 9.5), (14, 11.0)], "villager", "cloth_w"), ([(16, 13.5), (-12, 12.0)], "villager_robe", "cloth_t"),
             ([(3.5, 30), (5.0, 9.0)], "nair", "cloth_w"), ([(5.8, 10), (4.3, 32)], "villager", "cloth_r"),
             ([(-20, 4), (-14.5, 9)], "dutch", "cloth_w"), ([(18, -4), (14, 16)], "villager", "cloth_w")]
    for i, (wp, kind, cl) in enumerate(walks):
        root, parts = kit.make_walker(f"Walker{i}", coll, kind, seed=70 + i, cloth=cl)
        kit.animate_walk(root, parts, wp, height, start=1, end=frames, stride_frames=14 + (i % 3) * 2, speed=1.0)


# ------------------------------------------------------------------- grove, tents, palace
def build_surroundings(coll, lib_c, frames, rng):
    palms = [kit.make_palm(f"LibPalm{i}", lib_c, seed=100 + i, height=5.5 + 1.0 * i) for i in range(6)]
    trees = [kit.make_tree(f"LibTree{i}", lib_c, seed=110 + i, height=6.0 + 1.2 * i) for i in range(4)]
    bushes = [kit.make_bush(f"LibBush{i}", lib_c, seed=120 + i, size=1.0 + 0.25 * i) for i in range(4)]
    bananas = [pw.make_banana(f"LibBanana{i}", lib_c, seed=130 + i, height=2.2 + 0.35 * i) for i in range(3)]
    tents = [kit.make_cone_tent(f"LibTent{i}", lib_c, r=2.0 + 0.4 * i, h=3.3 + 0.4 * i) for i in range(2)]
    ridge = kit.make_ridge_tent("LibRidgeTent", lib_c)
    taken = []

    def free(x, y, r):
        if any(math.hypot(x - a, y - b) < r + c for a, b, c in taken):
            return False
        taken.append((x, y, r))
        return True

    # reserve the canopy, the camera's ground (south), the avenue and the palace plot
    taken += [(CANOPY[0], CANOPY[1], 6.0), (0.0, -7.0, 5.0), (-3.0, -4.5, 3.5), (3.0, -4.5, 3.5), (11.0, 44.0, 11.0)]
    # tents to both sides, just outside the canopy (K27)
    for i, (x, y, rz, k) in enumerate(((-6.6, 2.6, 0.4, 1), (-9.2, 7.8, 0.9, 0), (-6.0, 15.5, -0.2, 0),
                                        (8.4, -1.0, -0.6, 1), (14.5, 0.5, -1.0, 0), (-2.0, 16.5, 0.3, 0),
                                        (-12.0, 2.6, 1.4, 0))):
        kit.instance(tents[k], f"Tent{i}", coll, (x, y, height(x, y) - 0.05), rot_z=rz + face(-x, -y))
        taken.append((x, y, 2.6))
    for i, (x, y, rz) in enumerate(((-11.5, 13.5, 0.3), (11.5, -2.0, -1.2))):
        kit.instance(ridge, f"RidgeTent{i}", coll, (x, y, height(x, y) - 0.05), rot_z=rz)
        taken.append((x, y, 2.6))
    # raised planting beds with clipped bushes, either side behind the canopy (K27)
    for i, (x, y, w, d) in enumerate(((-4.6, 4.4, 4.0, 1.4), (4.6, 4.4, 4.0, 1.4), (-5.4, -2.4, 1.4, 3.2),
                                      (5.4, -2.2, 1.4, 3.6))):
        mb = kit.MB(bevel=0.02)
        mb.box(T(0, 0, 0.18) @ S(w, d, 0.36), "stone")
        mb.box(T(0, 0, 0.32) @ S(w - 0.2, d - 0.2, 0.12), "soil")
        bed = mb.obj(f"Bed{i}", coll)
        bed.location = (x, y, height(x, y))
        n = max(3, int(w * d / 1.1))
        for k in range(n):
            bx, by = x + rng.uniform(-w / 2 + 0.4, w / 2 - 0.4), y + rng.uniform(-d / 2 + 0.3, d / 2 - 0.3)
            kit.instance(bushes[k % 4], f"BedBush{i}_{k}", coll, (bx, by, height(x, y) + 0.35),
                         rot_z=rng.uniform(0, TAU), scale=rng.uniform(0.6, 0.85))
        taken.append((x, y, max(w, d) / 2))
    # palace: a two-tier hall and tiled houses among the palms to the north (K27 background)
    hall, _ = pw.make_hall("PalaceHall", coll, 16.0, 10.0, 7,
                           [("pillared", 3.0, "wood", 0), ("band", 2.4, "wood", 1.5)], top_pitch=44.0)
    hall.location = (11.0, 44.0, height(11.0, 44.0) - 0.2)
    for i, (x, y, rz, w, d) in enumerate(((-4.0, 40.0, 0.15, 7.0, 5.5), (24.0, 36.0, -0.3, 6.5, 5.0),
                                          (-17.0, 34.0, 0.4, 6.0, 5.0), (28.0, 50.0, 0.1, 8.0, 6.0))):
        h = pw.make_house(f"House{i}", coll, w=w, d=d, seed=140 + i, veranda=i % 2 == 0, gable=0.3)
        h.location = (x, y, height(x, y) - 0.1)
        h.rotation_euler[2] = rz
        taken.append((x, y, max(w, d) / 2 + 1))
    # banana clumps and bushes close behind the throne (K30's wall of green)
    for k in range(34):
        a = rng.uniform(-0.6, 1.6)
        r = rng.uniform(3.6, 9.0)
        x, y = THRONE[0] + r * math.cos(a), THRONE[1] + 1.2 + r * math.sin(a)
        if free(x, y, 0.9):
            src = bananas[k % 3] if k % 3 == 0 else bushes[k % 4]
            kit.instance(src, f"Banana{k}", coll, (x, y, height(x, y)), rot_z=rng.uniform(0, TAU),
                         scale=rng.uniform(0.9, 1.25) if k % 3 == 0 else rng.uniform(1.4, 2.2))
    # a wall of green behind the throne, seen behind the king in S23 (K30)
    for k in range(40):
        a = math.radians(rng.uniform(30, 95))
        r = rng.uniform(3.4, 12.0)
        x, y = THRONE[0] + r * math.cos(a), THRONE[1] + r * math.sin(a)
        if not free(x, y, 0.7):
            continue
        if k % 4 == 0:
            kit.instance(trees[k % 4], f"WallTree{k}", coll, (x, y, height(x, y) - 0.1), rot_z=rng.uniform(0, TAU),
                         scale=rng.uniform(0.6, 0.9))
        else:
            kit.instance(bushes[k % 4], f"WallBush{k}", coll, (x, y, height(x, y)), rot_z=rng.uniform(0, TAU),
                         scale=rng.uniform(1.8, 2.8))
    # palm grove: rows several deep all round, thicker to the north
    palm_obs = []
    k = 0
    for ring in range(9):
        r = 8.5 + ring * 3.6
        n = int(TAU * r / 3.4)
        for i in range(n):
            a = i * TAU / n + rng.uniform(-0.12, 0.12) + ring * 0.37
            x, y = CANOPY[0] + r * math.cos(a) * 1.15, CANOPY[1] + 2.0 + r * math.sin(a)
            x += rng.uniform(-1.2, 1.2)
            y += rng.uniform(-1.2, 1.2)
            if y < -6.0 and abs(x) < 9.0 + ring:                      # keep the camera side open
                continue
            if on_path(x, y) or not free(x, y, 1.3):
                continue
            pick = min(5, ring // 2 + rng.randint(0, 2))           # short palms close in, tall ones behind
            ob = kit.instance(palms[pick], f"Palm{k}", coll, (x, y, height(x, y) - 0.1), rot_z=rng.uniform(0, TAU),
                              scale=rng.uniform(0.85, 1.15))
            palm_obs.append(ob)
            k += 1
    # broadleaf trees and undergrowth between the palms
    for k in range(110):
        a = rng.uniform(0, TAU)
        r = rng.uniform(8.0, 40.0)
        x, y = CANOPY[0] + r * math.cos(a) * 1.15, CANOPY[1] + 2.0 + r * math.sin(a)
        if y < -6.0 and abs(x) < 10.0:
            continue
        if on_path(x, y) or not free(x, y, 1.8):
            continue
        kit.instance(trees[k % 4], f"Tree{k}", coll, (x, y, height(x, y) - 0.1), rot_z=rng.uniform(0, TAU),
                     scale=rng.uniform(0.8, 1.2))
    for k in range(260):
        a = rng.uniform(0, TAU)
        r = rng.uniform(7.0, 32.0)
        x, y = CANOPY[0] + r * math.cos(a) * 1.15, CANOPY[1] + 2.0 + r * math.sin(a)
        if (y < -5.5 and abs(x) < 6.0) or on_path(x, y) or in_clearing(x, y, -1.0) and r < 9:
            continue
        if any(math.hypot(x - a_, y - b_) < c_ * 0.7 for a_, b_, c_ in taken[:5]):
            continue
        src = bananas[k % 3] if k % 5 == 0 else bushes[k % 4]
        kit.instance(src, f"Under{k}", coll, (x, y, height(x, y)), rot_z=rng.uniform(0, TAU),
                     scale=rng.uniform(0.8, 1.5))
    # big foreground leaves at the bottom corners of the K27 view
    for i, (x, y) in enumerate(((-5.8, -6.2), (5.6, -6.0), (-7.0, -4.2), (7.2, -4.6), (-4.6, -7.4), (4.4, -7.6))):
        kit.instance(bushes[i % 4], f"FrontBush{i}", coll, (x, y, height(x, y)), rot_z=rng.uniform(0, TAU),
                     scale=rng.uniform(1.4, 1.9))
    # a slow breeze in the nearest palms
    for ob in palm_obs:
        if math.hypot(ob.location.x, ob.location.y) < 16 and rng.random() < 0.6:
            ph = rng.uniform(0, TAU)
            rz = ob.rotation_euler[2]
            f = 1
            while f <= frames + 48:
                t = f / kit.FPS
                ob.rotation_euler = (0.012 * math.sin(t * 0.8 + ph), 0.012 * math.cos(t * 0.65 + ph), rz)
                ob.keyframe_insert("rotation_euler", frame=f)
                f += 24


# ------------------------------------------------------------------- assembly
def build_world(frames):
    rng = random.Random(27)
    pw.register_palette()
    rig_c = kit.new_collection("Rig")
    world_c = kit.new_collection("World")
    set_c = kit.new_collection("RoyalSet")
    cast_c = kit.new_collection("Cast")
    crowd_c = kit.new_collection("Crowd")
    grove_c = kit.new_collection("Grove")
    lib_c = kit.new_collection("Library")
    # warm low sun from over the camera's left shoulder (K27: faces lit, shadows falling back and right)
    cw.scene_base(rig_c, sun_dir=(0.45, 0.72, -0.48), sun_energy=8.0, haze_density=0.0009)
    make_ground(world_c)
    build_royal_set(set_c, lib_c, frames, rng)
    imhoff, king = build_cast(cast_c, lib_c, frames, rng)
    build_crowd(crowd_c, lib_c, frames, rng)
    build_surroundings(grove_c, lib_c, frames, rng)
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return {"imhoff": imhoff, "king": king, "rig": rig_c}
