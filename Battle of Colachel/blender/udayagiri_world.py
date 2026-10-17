"""Udayagiri: the king's offer, the drill ground and the title (S55-S58; clips 67-70), Udayagiri.blend.

Laid out to match the Flow references frames/flow_refs/K67-K70.jpeg:
  S55 (K67) inside the stone hill fort: courtyard walls with a crenellated gatehouse, a dais with the throne
            and a canopy, King Marthanda Varma with Nair guards, De Lannoy (hatless) alone in the middle.
  S56 (K68) the same courtyard, close: stairs and a dark doorway behind; De Lannoy bows to the king.
  S57 (K69) the drill ground outside, in daylight: three ranks of Travancore musketeers firing volleys with
            white smoke, two field guns and their crews, De Lannoy directing; a low stone wall being rebuilt
            (scaffold, masons, stacked blocks) and a cannonball works (furnace, shed, piles of iron shot).
  S58 (K70) the same ground, closer: the king puts a gold sash over De Lannoy's shoulder; ranks behind, tents
            and a pavilion.

Everything is kit parts (figures, rigs, cannon, tents, palms, trees, bushes, boulders, puffs, flames). The only new
parts, kept here so they can be merged into the kit later (they use kit.MB and kit.PALETTE colours):
  make_stone_wall (blocky stone curtain wall / tower / gatehouse with merlons and an optional gateway),
  make_stairs, make_flagstones, make_canopy_open, make_pavilion, make_ball_pile, make_furnace, make_shed,
  make_scaffold, make_block_stack, make_gravel, make_musketeer (Travancore firing pose), make_delannoy_hatless,
  make_tricorn, make_sash, make_banner.

Coordinates: metres, Z up. The fort courtyard is centred on the origin (walls at x = +-12.8, y = +-9.8). The
drill ground is a plateau centred on DRILL = (100, 0); local drill coordinates (u, v) = world - DRILL.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

import colachel_kit as kit
from colachel_kit import FIRE_POSE, MUSKET_MUZZLE, STAND_POSE, STONES, _blocks, _musket_drop, _redcoat, court_robe, make_ball_pile, make_banner, make_block_stack, make_canopy_open, make_delannoy_hatless, make_flagstones, make_furnace, make_gate_doors, make_gravel, make_musketeer, make_pavilion, make_sash, make_scaffold, make_shed, make_stairs, make_stone_wall, make_tricorn
import colachel_world as cw
import landing_world as lw
import port_world as pw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau
DRILL = (100.0, 0.0)

EXTRA = {
    "fort_stone":    (0.52, 0.48, 0.42),
    "fort_stone_dk": (0.42, 0.39, 0.35),
    "fort_stone_lt": (0.61, 0.57, 0.50),
    "fort_grey":     (0.40, 0.38, 0.36),
    "flag_a":        (0.56, 0.50, 0.42),
    "flag_b":        (0.49, 0.44, 0.37),
    "flag_c":        (0.61, 0.55, 0.46),
    "pavilion":      (0.80, 0.70, 0.55),
    "tent_tan":      (0.78, 0.69, 0.52),
}


def register_palette():
    pw.register_palette()
    for k, v in EXTRA.items():
        kit.PALETTE.setdefault(k, v)
        kit.mat(k, kit.PALETTE[k])


def face(dx, dy):
    """rot_z that turns a kit figure (facing +Y) toward direction (dx, dy)."""
    return math.atan2(-dx, dy)


def dw(u, v):
    """Drill-local (u, v) to world (x, y)."""
    return DRILL[0] + u, DRILL[1] + v


# ====================================================================== terrain
def _sm(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


def _g(x, y, cx, cy, sx, sy):
    return math.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2) / 2)


def plateau_mask(x, y):
    """0 on the two flat plateaus (the fort hilltop and the drill ground), 1 away from them."""
    r1 = math.hypot(x / 21.0, y / 16.0)
    r2 = math.hypot((x - DRILL[0]) / 37.0, y / 27.0)
    return _sm(1.0, 1.8, min(r1, r2))


def height(x, y):
    m = plateau_mask(x, y)
    far = max(0.0, y - 30.0) * 0.20 * (1 + 0.35 * _n(x, y, 22.0, 5.0))
    out = -4.2 + 2.8 * _n(x, y, 16.0, 1.3) + 1.0 * _n(x, y, 5.5, 2.1) + far
    out += 15.0 * _g(x, y, DRILL[0] + 14, 52, 20, 15) + 11.0 * _g(x, y, DRILL[0] - 34, 58, 20, 16)
    out += 12.0 * _g(x, y, -34, 42, 18, 15) + 9.0 * _g(x, y, 32, 40, 16, 14) + 8.0 * _g(x, y, -18, -52, 22, 14)
    inner = 0.0 if x < 60 else 0.10 * _n(x, y, 3.3, 0.4)
    return inner * (1 - m) + m * out


def _axis(a0, a1, bands, coarse):
    vals, v = [], a0
    while v < a1:
        vals.append(v)
        step = coarse
        for lo, hi, st in bands:
            if lo <= v < hi:
                step = st
        v += step
    return vals + [a1]


def make_terrain(coll, seed=3):
    rng = random.Random(seed)
    xs = _axis(-170.0, 270.0, [(-30, 30, 0.9), (30, 66, 3.0), (66, 136, 0.9)], 4.5)
    ys = _axis(-150.0, 170.0, [(-36, 36, 0.9), (36, 80, 2.2)], 4.5)
    bm = bmesh.new()
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                sx = xs[i + 1] - xs[i]
                sy = ys[j + 1] - ys[j]
                jx, jy = rng.uniform(-0.25, 0.25) * sx, rng.uniform(-0.25, 0.25) * sy
            px, py = x + jx, y + jy
            row.append(bm.verts.new((px, py, height(px, py))))
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    names = ["field_dirt", "field_dirt_dk", "grass", "grass_lt", "jungle", "far_hill", "rock", "dirt_dk", "laterite", "dirt"]
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        m = plateau_mask(c.x, c.y)
        nz = f.normal.z
        k = _n(c.x, c.y, 7.0, 3.3) + rng.uniform(-0.15, 0.15)
        if m < 0.015:
            f.material_index = 9 if k < 0.3 else 7
        elif nz < 0.62:
            f.material_index = 6 if rng.random() < 0.45 else (8 if rng.random() < 0.08 else 7)
        elif m < 0.12 and k < 0.3:
            f.material_index = 7
        elif c.z > 7.0:
            f.material_index = 5 if k > -0.1 else 4
        else:
            f.material_index = 3 if k > 0.2 else (4 if k < -0.42 else 2)
    me = bpy.data.meshes.new("Terrain")
    bm.to_mesh(me)
    bm.free()
    for nm in names:
        me.materials.append(kit.mat(nm))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Terrain", me)
    coll.objects.link(ob)
    return ob


# ====================================================================== new kit-style parts
# ----- figures
# ====================================================================== library
def build_lib(lib):
    """Hidden source meshes shared by every beat (kit parts, plus the few new parts above)."""
    L = {}
    L["guard"] = [kit.make_figure(f"LibUGuard{i}", lib, "nair_spear" if i % 2 == 0 else "nair", seed=i) for i in range(4)]
    L["spear"] = [kit.make_figure(f"LibUSpear{i}", lib, "nair_spear", seed=30 + i) for i in range(4)]
    L["musket"] = [make_musketeer(f"LibUMusket{i}", lib, seed=40 + i) for i in range(4)]
    L["rank"] = [make_musketeer(f"LibURank{i}", lib, seed=90 + i, pose={
        "body": kit.Matrix.Identity(4), "legL": T(0.1, 0, 0.88), "legR": T(-0.1, 0, 0.88),
        "armL": T(0.27, 0, 1.4) @ Rx(0.04), "armR": T(-0.27, 0, 1.4) @ Rx(0.5) @ Rz(-0.1)}, shoulder=True) for i in range(4)]
    L["ready"] = [make_musketeer(f"LibUReady{i}", lib, seed=50 + i, pose={
        "body": kit.Matrix.Identity(4), "legL": T(0.1, 0, 0.88), "legR": T(-0.1, 0, 0.88),
        "armL": T(0.27, 0, 1.4) @ Rx(0.04), "armR": T(-0.27, 0, 1.4) @ Rx(0.5) @ Rz(-0.1)}, shoulder=True)
        for i in range(2)]
    for sp in L["spear"]:
        kit.recolor(sp, strip=("shield", "brass"))
    L["crew"] = [kit.make_figure(f"LibUCrew{i}", lib, "nair", seed=60 + i) for i in range(3)]
    L["worker"] = [kit.make_figure(f"LibUWork{i}", lib, "villager", seed=70 + i,
                                   cloth=("cloth_t", "cloth_w", "cloth_r", "cloth_t")[i]) for i in range(4)]
    L["cannon"] = kit.make_cannon("LibUCannon", lib)
    L["puff"] = [kit.make_puff(f"LibUPuff{k}", lib, seed=80 + k, m="smoke") for k in range(3)]
    L["puff_dk"] = kit.make_puff("LibUPuffDk", lib, seed=90, m="smoke_md")
    L["flames"] = [kit.make_flames(f"LibUFlames{k}", lib, seed=k, size=0.4) for k in range(2)]
    kit.mat_emit("flash", (1.0, 0.62, 0.22), 40.0)
    mb = kit.MB()
    mb.ico(kit.Matrix.Identity(4), "flash", r=0.6, sub=1)
    L["flash"] = mb.obj("LibUFlash", lib)
    L["barrel"] = kit.make_barrel("LibUBarrel", lib)
    L["crate"] = kit.make_crate("LibUCrate", lib, size=0.8)
    L["sack"] = kit.make_sack("LibUSack", lib)
    L["boulder"] = [kit.make_boulder(f"LibUBoulder{i}", lib, seed=i, size=0.7 + 0.3 * i,
                                     m=("rock", "fort_stone_dk", "fort_grey", "fort_stone")[i % 4]) for i in range(5)]
    L["bush"] = [kit.make_bush(f"LibUBush{i}", lib, seed=120 + i, size=0.9 + 0.25 * i) for i in range(4)]
    L["tree"] = [kit.make_tree(f"LibUTree{i}", lib, seed=110 + i, height=6.0 + 1.3 * i) for i in range(5)]
    L["palm"] = [kit.make_palm(f"LibUPalm{i}", lib, seed=100 + i, height=5.5 + 1.0 * i) for i in range(6)]
    L["cone"] = [kit.make_cone_tent(f"LibUCone{i}", lib, r=2.0 + 0.3 * i, h=3.0 + 0.4 * i, seed=i) for i in range(2)]
    L["ridge"] = kit.make_ridge_tent("LibURidge", lib)
    for t_ in L["cone"] + [L["ridge"]]:
        kit.recolor(t_, {"canvas": "tent_tan"})
    L["balls"] = [make_ball_pile(f"LibUBalls{i}", lib, base=3 + i, seed=i) for i in range(2)]
    L["blocks"] = [make_block_stack(f"LibUBlocks{i}", lib, seed=i, n=12 + 2 * i) for i in range(2)]
    L["gravel"] = [make_gravel(f"LibUGravel{i}", lib, seed=i) for i in range(2)]
    mb = kit.MB()
    rng = random.Random(4)
    mb.ico(S(1.0, 0.8, 0.07), "grass", r=1.8, sub=1, jitter=0.25, rng=rng)
    L["patch"] = mb.obj("LibUPatch", lib)
    for k in (L["guard"] + L["spear"] + L["musket"] + L["ready"] + L["rank"] + L["crew"] + L["worker"] + L["puff"] + L["flames"] +
              L["boulder"] + L["bush"] + L["tree"] + L["palm"] + L["cone"] + L["balls"] + L["blocks"] + L["gravel"] +
              [L["cannon"], L["puff_dk"], L["flash"], L["barrel"], L["crate"], L["sack"], L["ridge"], L["patch"]]):
        kit.hide_source(k)
    return L


def put(src, name, c, x, y, rz=0.0, s=1.0, z=None, sink=0.02):
    zz = height(x, y) if z is None else z
    return kit.instance(src, name, c, (x, y, zz - sink), rot_z=rz, scale=s)


def wall(name, c, x, y, rz, length, h, **kw):
    ob = make_stone_wall(name, c, length, h, **kw)
    ob.location = (x, y, 0.0)
    ob.rotation_euler[2] = rz
    return ob


# ====================================================================== the fort (S55, S56)
def build_fort(c, L, rng):
    """Courtyard walls, gatehouse with doors, towers, terrace and stairs, dais with throne and canopy,
    paving, props, banners, plants, and the guards at the gate (always there)."""
    HP = math.pi / 2
    # north wall (back), the gatehouse projects into the courtyard
    wall("WallN1", c, -5.2, 9.8, 0.0, 16.4, 4.2, seed=1, thick=1.6)
    wall("WallN2", c, 11.7, 9.8, 0.0, 3.4, 4.2, seed=2, thick=1.6)
    wall("Gatehouse", c, 6.5, 9.8, 0.0, 7.0, 6.2, seed=3, thick=3.4, c_h=0.95, gap=(-1.3, 1.3, 3.6), broken=0.12)
    d = make_gate_doors("GateDoors", c, -1.3, 1.3, 3.6, 3.4)
    d.location = (6.5, 9.8, 0.0)
    wall("WallW", c, -12.8, 0.0, HP, 20.6, 3.9, seed=4, thick=1.6)
    wall("WallE", c, 12.8, 0.0, HP, 20.6, 3.0, seed=5, thick=1.6, broken=0.22)
    wall("WallS", c, 0.0, -9.8, 0.0, 27.0, 1.9, seed=6, thick=1.6, broken=0.35, c_h=0.7)
    wall("TowerNW", c, -12.8, 9.8, 0.0, 4.4, 6.8, seed=7, thick=4.4, c_h=0.95, broken=0.1)
    wall("TowerNE", c, 12.8, 9.8, 0.0, 4.4, 5.6, seed=8, thick=4.4, c_h=0.9, broken=0.2)
    wall("TowerSW", c, -12.8, -9.8, 0.0, 4.2, 3.4, seed=9, thick=4.2, c_h=0.8, broken=0.3)
    wall("TowerSE", c, 12.8, -9.8, 0.0, 4.2, 2.6, seed=10, thick=4.2, c_h=0.7, broken=0.4)
    # terrace against the back wall with a stair up to it (K68)
    wall("Terrace", c, -9.0, 7.45, 0.0, 6.0, 2.2, seed=11, thick=3.1, crenel=False)
    st = make_stairs("Stairs", c, n=8, w=2.2)
    st.location = (-1.9, 7.6, 0.0)
    # dais, steps, carpet, throne and canopy (K67)
    mb = kit.MB(bevel=0.025)
    mb.box(T(-9.45, 1.5, 0.17) @ S(5.0, 5.5, 0.62), "fort_stone_lt")
    mb.box(T(-9.45, 1.5, 0.457) @ S(4.7, 5.2, 0.04), "fort_stone")
    mb.box(T(-9.6, 1.5, 0.48) @ S(3.4, 3.9, 0.03), "carpet_gold")
    mb.box(T(-9.6, 1.5, 0.5) @ S(3.1, 3.6, 0.03), "carpet_red")
    mb.box(T(-6.75, 1.5, 0.12) @ S(0.55, 3.6, 0.5), "fort_stone")
    mb.box(T(-6.3, 1.5, 0.05) @ S(0.45, 3.2, 0.3), "fort_stone_dk")
    mb.obj("Dais", c)
    th = kit.make_throne("Throne", c)
    th.location = (-11.0, 1.5, 0.46)
    th.rotation_euler[2] = -HP
    cn = make_canopy_open("DaisCanopy", c, w=4.4, d=5.0, h=3.7)
    cn.location = (-9.5, 1.5, 0.46)
    # paving
    skip = lambda x, y: (-12.4 < x < -5.8 and -1.5 < y < 4.5) or (x < -1.4 and y > 5.6) or _n(x, y, 2.6, 4.0) > (0.5 if y > 1.0 else -0.05)
    make_flagstones("Paving", c, -12.0, 12.0, -9.0, 9.0, seed=3, skip=skip, step=(1.5, 1.1))
    # props: barrels and crates by the gate, weapons stand, sacks, boulders
    for k, (x, y) in enumerate(((9.2, 7.6), (9.9, 7.0), (8.9, 6.9), (-0.2, 8.4), (0.5, 8.2))):
        put(L["barrel"], f"Barrel{k}", c, x, y, rng.uniform(0, 6), s=1.0)
    for k, (x, y, rz) in enumerate(((10.6, 6.2, 0.4), (-0.6, 7.6, 0.2), (11.2, -3.5, 0.5))):
        put(L["crate"], f"Crate{k}", c, x, y, rz, s=1.1)
    for k, (x, y) in enumerate(((10.4, -4.1), (10.9, -2.9), (1.3, 8.0))):
        put(L["sack"], f"Sack{k}", c, x, y, rng.uniform(0, 6), s=1.2)
    mb = kit.MB(bevel=0.01)
    for sx in (-1, 1):
        mb.seg((sx * 1.2, 0, 0), (sx * 1.2, 0, 1.3), 0.06, 0.05, "post", sides=5)
    mb.box(T(0, 0, 0.85) @ S(2.5, 0.08, 0.08), "post")
    mb.box(T(0, 0, 0.3) @ S(2.5, 0.08, 0.08), "post")
    for k in range(7):
        x = -1.0 + k * 0.33
        mb.seg((x, 0.1, 0.0), (x + 0.1, 0.25, 2.1), 0.025, 0.02, "post", sides=4)
        mb.seg((x + 0.1, 0.25, 2.1), (x + 0.12, 0.28, 2.4), 0.05, 0.0, "steel", sides=4)
    rack = mb.obj("SpearRack", c)
    rack.location = (-11.5, -5.0, 0.0)
    rack.rotation_euler[2] = HP
    for k, (x, y, s_, i) in enumerate(((-3.4, -7.9, 1.1, 0), (-2.6, -8.3, 0.7, 1), (5.8, -8.4, 1.2, 2), (-10.4, -7.2, 1.0, 3),
                                       (3.5, 5.4, 0.55, 4), (8.4, 4.4, 0.6, 1), (-4.5, 3.6, 0.5, 2))):
        put(L["boulder"][i], f"Rock{k}", c, x, y, rng.uniform(0, 6), s=s_ * 1.1)
    # banners on the walls (plain red and gold, no emblem) and pennants on poles
    for k, (x, y, rz) in enumerate(((-11.78, -5.2, -HP), (-11.78, 6.0, -HP), (-4.5, 8.78, 0.0), (1.8, 8.78, 0.0),
                                    (11.78, 0.6, HP))):
        b = make_banner(f"Banner{k}", c, w=0.95, h=1.9)
        b.location = (x, y, 1.4)
        b.rotation_euler[2] = rz
    for k, (x, y) in enumerate(((3.0, -1.5), (6.6, -4.4), (-3.4, -5.6), (9.2, 1.2))):
        pw.flag_on_pole(c, f"Pennant{k}", (x, y, 0.0), 2.3, 0.7, 0.45, m="flag_r", heading=200.0)
    # plants and grass patches along the inner foot of the walls
    for k in range(70):
        side = rng.choice("NWES")
        if side == "N":
            x, y = rng.uniform(-11.5, 11.5), rng.uniform(7.9, 8.8)
        elif side == "W":
            x, y = rng.uniform(-11.5, -11.0), rng.uniform(-8.7, 8.7)
        elif side == "E":
            x, y = rng.uniform(11.0, 11.7), rng.uniform(-8.7, 8.7)
        else:
            x, y = rng.uniform(-11.5, 11.5), rng.uniform(-8.8, -8.0)
        if (-12.4 < x < -5.8 and -1.5 < y < 4.5) or (x < -1.4 and y > 5.4) or (4.0 < x < 9.0 and y > 6.0):
            continue
        put(L["bush"][k % 4], f"FBush{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(0.7, 1.3), sink=0.0)
    for k, (x, y) in enumerate(((-10.5, -3.6), (-5.2, 6.3), (3.2, -8.0), (9.2, -6.0), (11.0, 4.0),
                                (-2.8, 8.4), (6.5, -9.0), (-11.0, -8.0))):
        put(L["patch"], f"Patch{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(0.7, 1.2), sink=0.0)
    # guards at the gate (K68), seen from both beats, and on the east wall side
    for k, (x, y) in enumerate(((4.4, 7.1), (6.1, 7.4), (7.8, 7.1))):
        ob = put(L["guard"][k % 2 * 2], f"GateGuard{k}", c, x, y, face(0.2, -1.0))
        kit.animate_idle(ob, rng, 1, ev_end, 0.012)
    for k, (x, y, dx, dy) in enumerate(((11.4, 2.5, -1, 0), (11.2, -2.0, -1, 0.1))):
        ob = put(L["guard"][(k + 1) % 4], f"WallGuard{k}", c, x, y, face(dx, dy))
        kit.animate_idle(ob, rng, 1, ev_end, 0.012)


ev_end = 1200


def build_surroundings_fort(c, L, rng, avoid):
    """Trees and palms on and below the hill round the fort; broadleaf trees right behind the north wall."""
    taken = [(a, b, 8.0) for a, b in avoid]

    def free(x, y, r):
        if any(math.hypot(x - a, y - b) < r + q for a, b, q in taken):
            return False
        taken.append((x, y, r))
        return True
    for i in range(16):
        x, y = -15.0 + i * 2.0 + rng.uniform(-0.6, 0.6), 12.5 + rng.uniform(0, 5.5)
        if free(x, y, 1.6):
            put(L["tree"][i % 5], f"FTree{i}", c, x, y, rng.uniform(0, 6), s=rng.uniform(0.8, 1.15), sink=0.1)
    for k in range(260):
        a = rng.uniform(0, TAU)
        r = rng.uniform(1.1, 3.0)
        x, y = 21.0 * r * math.cos(a), 16.0 * r * math.sin(a)
        if abs(x) < 14.2 and abs(y) < 11.5:
            continue
        if y < -9 and abs(x - 6) < 22 and r < 1.5:          # keep the S55 camera's ground clear
            continue
        if not free(x, y, 1.3):
            continue
        z = height(x, y)
        kind = rng.random()
        if kind < 0.38:
            put(L["palm"][min(5, int(r * 1.3) + rng.randint(0, 2))], f"FPalm{k}", c, x, y, rng.uniform(0, 6),
                s=rng.uniform(0.85, 1.2), z=z - 0.15)
        elif kind < 0.7:
            put(L["tree"][k % 5], f"FTreeB{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(0.9, 1.4), z=z - 0.1)
        else:
            put(L["bush"][k % 4], f"FBushB{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(1.2, 2.2), z=z)
    for k in range(40):
        a = rng.uniform(0, TAU)
        r = rng.uniform(1.0, 2.2)
        x, y = 21.0 * r * math.cos(a), 16.0 * r * math.sin(a)
        if abs(x) < 14.2 and abs(y) < 11.5:
            continue
        put(L["boulder"][k % 5], f"FRock{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(0.8, 2.0), z=height(x, y) - 0.1)


def build_s55(c, L, ev, rng):
    """King, De Lannoy, guards; the offer."""
    f0, f1 = ev["r55"]
    king, kp = kit.make_rig("King55", c, "king")
    court_robe("Robe55", kp)
    king.location = (-8.3, 0.4, 0.46)
    king.rotation_euler[2] = face(6.0, -1.2)
    king.scale = (1.04, 1.04, 1.04)
    dl, dp = make_delannoy_hatless("DeLannoy55", c)
    dl.location = (-2.4, -0.9, 0.0)
    dl.rotation_euler[2] = face(-6.0, 1.8)
    kit.key_pose(kp, f0, {**kit.ARM_REST, "head": (0, 0, 0)})
    kit.key_pose(dp, f0, {**kit.ARM_REST, "head": (0, 0, 0)})
    o = ev["offer55"]
    kit.key_pose(kp, o - 6, kit.ARM_REST)
    kit.key_pose(kp, o + 14, {"armL": (1.0, -0.8, 0.0), "head": (0, 0, -0.08)})        # open hand toward De Lannoy
    kit.key_pose(kp, o + 64, {"armL": (0.95, -0.75, 0.0), "head": (0, 0, -0.06)})
    kit.key_pose(kp, o + 90, {**kit.ARM_REST, "head": (0, 0, 0)})
    kit.key_pose(dp, o + 10, {"head": (0, 0, 0)})
    kit.key_pose(dp, o + 34, {"head": (-0.07, 0, 0.04)})
    kit.key_pose(dp, o + 80, {"head": (-0.03, 0, 0.0)})
    kit.animate_rig_idle(kp, rng, f0, f1, body=0.008, head=0.0, skip=("head",))
    kit.animate_rig_idle(dp, rng, f0, f1, body=0.006, head=0.0, skip=("head",))
    for k, (x, y, dx, dy) in enumerate(((-9.3, 3.7, 1, -0.7), (-8.0, 4.1, 1, -0.9), (-6.9, 3.4, 1, -0.8))):
        ob = put(L["guard"][k], f"G55a{k}", c, x, y, face(dx, dy), z=0.46)
        kit.animate_idle(ob, rng, f0, f1, 0.012)
    for k, (x, y, dx, dy) in enumerate(((-10.4, -2.5, 1, 0.2), (-9.4, -2.9, 1, 0.3), (-8.4, -2.6, 1, 0.35))):
        ob = put(L["guard"][(k + 1) % 4], f"G55b{k}", c, x, y, face(dx, dy))
        kit.animate_idle(ob, rng, f0, f1, 0.012)
    for k, (x, y, dx, dy) in enumerate(((-3.5, 6.6, 0.4, -1), (-1.6, 6.8, 0.2, -1))):
        ob = put(L["guard"][(k + 2) % 4], f"G55c{k}", c, x, y, face(dx, dy))
        kit.animate_idle(ob, rng, f0, f1, 0.012)


def build_s56(c, L, ev, rng):
    """The bow: De Lannoy bows deeply, a hand on his chest; the king, arms folded, calm."""
    f0, f1 = ev["r56"]
    king, kp = kit.make_rig("King56", c, "king", fold=True)
    court_robe("Robe56", kp)
    king.location = (2.7, 4.3, 0.0)
    king.rotation_euler[2] = face(-1.0, -0.9)
    king.scale = (1.04, 1.04, 1.04)
    dl, dp = make_delannoy_hatless("DeLannoy56", c)
    dl.location = (0.3, 4.1, 0.0)
    dl.rotation_euler[2] = face(1.0, -0.4)
    y = ev["yes56"]
    kit.key_pose(kp, f0, {**kit.ARM_REST, "head": (0, 0, 0)})
    kit.pose_arms_folded(kp, f0 + 3, f0 + 16)
    kit.key_pose(kp, y + 40, {"head": (0, 0, 0)})
    kit.key_pose(kp, y + 64, {"head": (0.06, 0, 0.05)})                                  # a small nod
    kit.key_pose(kp, f1, {"head": (0.02, 0, 0.02)})
    hz = 0.95
    chest = {"armL": (1.15, 0.0, 1.0)}
    kit.key_pose(dp, f0, {**kit.ARM_REST, "head": (0, 0, 0)})
    kit.key_pose(dp, y - 22, kit.ARM_REST)
    kit.key_pose(dp, y - 4, chest)
    body = dp["body"]

    def bow(f, th):
        body.rotation_euler = (-th, 0.0, 0.0)
        body.location = (0.0, -hz * math.sin(th), hz * (1 - math.cos(th)))
        body.keyframe_insert("rotation_euler", frame=f)
        body.keyframe_insert("location", frame=f)
    bow(f0, 0.0)
    bow(y - 6, 0.0)
    bow(y + 22, 0.62)                                    # down on "yes"
    bow(y + 70, 0.66)
    bow(y + 108, 0.0)
    kit.key_pose(dp, y + 6, {"head": (0.0, 0, 0.0)})
    kit.key_pose(dp, y + 26, {"head": (0.38, 0, 0.0), "armR": (-0.5, 0.0, -0.25)})
    kit.key_pose(dp, y + 80, {"head": (0.38, 0, 0.0), "armR": (-0.45, 0.0, -0.2)})
    kit.key_pose(dp, y + 118, {"head": (0.0, 0, 0.0), "armR": (0.0, 0.0, 0.0)})
    kit.key_pose(dp, y + 106, chest)
    kit.key_pose(dp, y + 130, kit.ARM_REST)
    kit.animate_rig_idle(kp, rng, f0, f1, body=0.006, head=0.0, skip=("head",))
    for k, (x, y_, dx, dy) in enumerate(((5.0, 6.7, -0.3, -1), (6.5, 6.9, -0.4, -1))):
        ob = put(L["guard"][(k + 1) % 4], f"G56{k}", c, x, y_, face(dx, dy))
        kit.animate_idle(ob, rng, f0, f1, 0.012)


# ====================================================================== the drill ground (S57, S58)
DWALL = ("fort_stone_dk", "fort_grey", "fort_stone", "fort_stone_dk", "fort_grey")


def _anim_walk(c, L, name, kind, load, pts, f0, f1, seed, cloth="cloth_t"):
    root, parts = kit.make_carrier(name, c, load=load, seed=seed, kind=kind)
    path = []
    for _ in range(4):
        path += pts + pts[::-1][1:-1]
    kit.animate_walk(root, parts, path, height, start=f0, end=f1, stride_frames=15, speed=0.95)
    kit.fix_carry_arms(parts, load)
    return root


def build_drill(c, L, ev, rng):
    """The drill ground: stone wall (half rebuilt, scaffold, masons), the cannonball works, camp, plants.
    Always there; the beats add their people on top."""
    HP = math.pi / 2
    ox, oy = DRILL
    f0, f1 = ev["r57"][0], ev["r58"][1]

    def W(u, v):
        return ox + u, oy + v
    # the wall: finished east part, half-built west part, west and east returns
    x, y = W(7.0, 19.8)
    wall("DWallN", c, x, y, 0.0, 30.0, 2.7, seed=31, thick=1.5, crenel=False, mats=DWALL)
    x, y = W(-17.0, 19.8)
    wall("DWallNW", c, x, y, 0.0, 15.5, 1.15, seed=32, thick=1.5, crenel=False, mats=DWALL)
    x, y = W(-24.6, 6.4)
    wall("DWallW", c, x, y, HP, 26.0, 2.4, seed=33, thick=1.5, crenel=False, mats=DWALL)
    x, y = W(22.6, 14.0)
    wall("DWallE", c, x, y, HP, 12.0, 2.2, seed=34, thick=1.5, crenel=False, mats=DWALL, broken=0.0)
    # masons: scaffold on the south face, loose blocks on the half-built course, stacks of cut stone
    x, y = W(-16.5, 18.2)
    sc = make_scaffold("Scaffold", c, length=8.0, h=3.2, seed=2)
    sc.location = (x, y, 0.0)
    for k in range(7):
        bx, by = W(-23.0 + k * 1.25, 19.8)
        mb = kit.MB(bevel=0.02)
        mb.box(T(0, 0, 0.0) @ S(0.9, 1.3, 0.3), rng.choice(DWALL))
        ob = mb.obj(f"CourseBlock{k}", c)
        ob.location = (bx, by, 1.3 + (0.15 if k % 2 else 0.0))
        ob.rotation_euler[2] = rng.uniform(-0.1, 0.1)
    for k, (u, v, i) in enumerate(((-11.0, 15.8, 0), (-21.4, 15.2, 1), (-6.0, 17.6, 1))):
        put(L["blocks"][i], f"Blocks{k}", c, *W(u, v), rng.uniform(-0.3, 0.3), s=1.1)
    for k, (u, v) in enumerate(((-13.6, 17.3), (-19.5, 17.6), (-16.2, 17.3))):                   # masons on the deck
        ob = put(L["worker"][k % 4], f"MasonDeck{k}", c, *W(u, v), face(0, 1), z=height(*W(u, v)) + 1.25)
        kit.animate_idle(ob, rng, f0, f1, 0.04)
    for k, (u, v, dz) in enumerate(((-12.6, 14.2, 0.3), (-20.0, 14.0, 0.0), (-9.4, 16.2, 0.0))):  # masons on the ground
        ob = put(L["worker"][(k + 1) % 4], f"MasonGround{k}", c, *W(u, v), face(-0.2, 1) + 0.5)
        kit.animate_idle(ob, rng, f0, f1, 0.06)
    _anim_walk(c, L, "StoneCarrier0", "villager", "sack", [W(-11.5, 15.0), W(-14.5, 16.8)], f0, f1, 3)
    _anim_walk(c, L, "StoneCarrier1", "villager", "sack", [W(-21.0, 14.6), W(-18.5, 16.7)], f0, f1, 5)
    # the cannonball works: shed, furnace, piles of iron shot, anvil, crates, workers, smoke and fire
    sx, sy = W(15.0, 13.2)
    sh = make_shed("WorksShed", c)
    sh.location = (sx, sy, height(sx, sy))
    sh.rotation_euler[2] = -0.15
    fx, fy = W(11.0, 10.4)
    fu = make_furnace("Furnace", c)
    fu.location = (fx, fy, height(fx, fy))
    fu.rotation_euler[2] = face(0.35, -1.0)
    fz = height(fx, fy)
    fl = kit.instance(L["flames"][0], "FurnaceFire", c, (fx + 0.22, fy - 0.72, fz + 0.28), scale=0.55)
    kit.animate_flicker(fl, rng, f0, f1, amount=0.3, every=(3, 5))
    top = (fx, fy, fz + 2.85)
    t = f0 - 100
    k = 0
    while t < f1:
        ob = kit.instance(L["puff_dk"], f"FurnaceSmoke{k}", c, top, scale=0.0)
        kit.animate_puff(ob, t, min(f1 + 5, t + 150), top, (0.7 + rng.uniform(-0.2, 0.2), 0.3, 1.5), s0=0.25, s1=1.3,
                         grow=30.0, drag=0.25, step=6, fade=(t + 80, t + 150))
        t += 15
        k += 1
    for k, (u, v, i, s_) in enumerate(((17.8, 9.4, 1, 1.0), (19.6, 10.8, 0, 1.0), (17.0, 7.4, 0, 0.9), (13.2, 8.2, 0, 0.8))):
        put(L["balls"][i], f"Shot{k}", c, *W(u, v), rng.uniform(0, 6), s=s_)
    for k in range(18):                                                                          # loose shot on the ground
        u, v = rng.uniform(10.0, 21.0), rng.uniform(6.0, 12.0)
        mb = kit.MB()
        mb.ico(T(0, 0, 0.13), "iron", r=0.13, sub=1)
        ob = mb.obj(f"LooseShot{k}", c)
        ob.location = (*W(u, v), height(*W(u, v)))
    ax, ay = W(12.6, 13.2)
    mb = kit.MB(bevel=0.015)
    mb.cone(T(0, 0, 0.25), "post", segments=7, r1=0.34, r2=0.3, depth=0.5)
    mb.box(T(0, 0, 0.58) @ S(0.55, 0.28, 0.16), "iron")
    mb.box(T(0.38, 0, 0.58) @ S(0.3, 0.14, 0.08), "iron")
    an = mb.obj("Anvil", c)
    an.location = (ax, ay, height(ax, ay))
    for k, (u, v, rz) in enumerate(((19.0, 14.6, 0.3), (20.4, 14.0, 0.6), (9.4, 13.6, 0.1))):
        put(L["crate"], f"WorksCrate{k}", c, *W(u, v), rz, s=1.1)
    for k, (u, v) in enumerate(((11.2, 8.6), (13.0, 10.6), (16.6, 11.2), (12.3, 12.2))):
        ob = put(L["worker"][k % 4], f"Smith{k}", c, *W(u, v), face(0.3 * (-1) ** k, -1 if k < 3 else 0.5))
        kit.animate_idle(ob, rng, f0, f1, 0.05)
    _anim_walk(c, L, "ShotCarrier0", "villager", "crate", [W(13.2, 9.4), W(16.4, 8.6)], f0, f1, 7)
    _anim_walk(c, L, "ShotCarrier1", "villager", "crate", [W(19.5, 8.6), W(14.5, 7.0)], f0, f1, 9)
    # the camp behind the lines: tents and the pavilion with its flag
    pv = make_pavilion("Pavilion", c)
    px, py = W(5.0, 15.4)
    pv.location = (px, py, height(px, py))
    pw.flag_on_pole(c, "PavilionFlag", (px, py, height(px, py) + 3.5), 2.2, 1.3, 0.8, m="flag_r", heading=205.0)
    for k, (u, v, rz, i, kind) in enumerate(((-6.0, 15.4, 0.15, 0, "ridge"), (-1.2, 15.0, 0.0, 1, "cone"),
                                             (-9.0, 13.2, -0.3, 0, "cone"), (10.6, 16.8, 0.6, 0, "ridge"))):
        src = L["ridge"] if kind == "ridge" else L["cone"][i]
        put(src, f"Tent{k}", c, *W(u, v), rz, s=1.0)
    # props about the ground, boulders, gravel, grass patches
    for k, (u, v, i, s_) in enumerate(((-13.0, 0.5, 0, 0.6), (-17.0, -3.0, 2, 0.8), (9.0, -3.5, 3, 0.7), (12.8, 5.5, 1, 0.6),
                                       (-4.0, -8.0, 4, 0.9), (4.5, -8.5, 0, 0.7), (-9.0, -6.0, 1, 0.7), (6.0, 11.0, 2, 0.6),
                                       (-7.0, 12.0, 3, 0.7), (-24.0, 16.0, 1, 1.0), (21.0, 4.0, 4, 1.0), (14.5, -5.0, 2, 0.8))):
        put(L["boulder"][i], f"DRock{k}", c, *W(u, v), rng.uniform(0, 6), s=s_ * 0.85)
    for k in range(10):
        put(L["gravel"][k % 2], f"DGravel{k}", c, *W(rng.uniform(-18, 20), rng.uniform(-9, 12)), rng.uniform(0, 6), s=rng.uniform(0.8, 1.5), sink=0.0)
    for k in range(14):
        u, v = rng.uniform(-25, 24), rng.uniform(-14, 20)
        if v > 19.0 and abs(u) < 25:
            continue
        put(L["patch"], f"DPatch{k}", c, *W(u, v), rng.uniform(0, 6), s=rng.uniform(0.7, 1.4), sink=0.0)
    for k in range(60):
        u, v = rng.uniform(-30, 29), rng.uniform(-20, 21)
        if v > 18.5 and u < 23 and u > -25.5:
            continue
        if math.hypot(u / 37.0, v / 27.0) < 0.85 and rng.random() < 0.8:                           # only near the plateau rim
            continue
        put(L["bush"][k % 4], f"DBush{k}", c, *W(u, v), rng.uniform(0, 6), s=rng.uniform(0.9, 1.6), sink=0.0)


def build_surroundings_drill(c, L, rng, avoid):
    """Palms and trees round and behind the drill ground (K69), hills with plants."""
    ox, oy = DRILL
    taken = [(a, b, 8.0) for a, b in avoid]

    def free(x, y, r):
        if any(math.hypot(x - a, y - b) < r + q for a, b, q in taken):
            return False
        taken.append((x, y, r))
        return True
    for k in range(420):
        a = rng.uniform(0, TAU)
        r = rng.uniform(0.98, 2.5)
        u, v = 37.0 * r * math.cos(a), 27.0 * r * math.sin(a)
        x, y = ox + u, oy + v
        if r < 1.04 and not (v > 19.0 or u < -24.5):                         # keep the ground itself clear
            continue
        if v > 18.5 and abs(u) < 26 and r < 1.04:
            continue
        if v < -20 and r < 1.6:                                              # the camera side stays open
            continue
        if not free(x, y, 1.3):
            continue
        z = height(x, y)
        kind = rng.random()
        if kind < 0.42:
            put(L["palm"][min(5, int(r * 1.8) + rng.randint(0, 2))], f"DPalm{k}", c, x, y, rng.uniform(0, 6),
                s=rng.uniform(0.9, 1.3), z=z - 0.15)
        elif kind < 0.68:
            put(L["tree"][k % 5], f"DTree{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(1.0, 1.5), z=z - 0.1)
        else:
            put(L["bush"][k % 4], f"DBushB{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(1.4, 2.6), z=z)
    for k in range(70):
        a = rng.uniform(0, TAU)
        r = rng.uniform(1.0, 2.4)
        x, y = ox + 37.0 * r * math.cos(a), oy + 27.0 * r * math.sin(a)
        if r < 1.1:
            continue
        put(L["boulder"][k % 5], f"DHillRock{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(0.8, 2.2), z=height(x, y) - 0.1)


# ----- smoke and recoil
def musket_shot(c, L, p0, rz, f, rng, end, tag):
    """One musket shot: a white puff blown out ahead of the muzzle, rolling away and fading."""
    q = kit.Rz(rz) @ Vector(MUSKET_MUZZLE)
    pos = (p0[0] + q.x, p0[1] + q.y, p0[2] + q.z)
    fw = kit.Rz(rz) @ Vector((0, 1, 0))
    ob = kit.instance(L["puff"][rng.randint(0, 2)], f"{tag}Puff", c, pos, scale=0.0)
    kit.animate_puff(ob, f, end, pos, (fw.x * 1.6 + rng.uniform(-0.3, 0.3), fw.y * 1.6 + rng.uniform(-0.3, 0.3), 0.55),
                     s0=0.1, s1=rng.uniform(0.32, 0.45), grow=16.0, drag=1.3, step=5, fade=(f + 45, f + 100))


def cannon_shot(c, L, gun, p0, aim, f, rng, end, tag):
    """Flash, a big plume of smoke, and the gun's recoil."""
    muz = Vector(p0) + kit.Rz(aim) @ Vector(kit.CANNON_MUZZLE)
    fw = kit.Rz(aim) @ Vector((0, 1, 0))
    fl = kit.instance(L["flash"], f"{tag}Flash", c, muz + fw * 0.4, scale=0.0)
    fl.keyframe_insert("scale", frame=f - 1)
    fl.scale = (1.3, 1.3, 1.3)
    fl.keyframe_insert("scale", frame=f)
    fl.scale = (0.0, 0.0, 0.0)
    fl.keyframe_insert("scale", frame=f + 3)
    for q in range(5):
        ob = kit.instance(L["puff"][q % 3], f"{tag}Smoke{q}", c, tuple(muz), scale=0.0)
        t = f + q * 2
        pos = muz + fw * (0.3 + 0.3 * q)
        kit.animate_puff(ob, t, end, tuple(pos), (fw.x * 3.2 + rng.uniform(-0.6, 0.6), fw.y * 3.2 + rng.uniform(-0.6, 0.6),
                                                  rng.uniform(0.4, 1.0)), s0=0.2, s1=rng.uniform(0.7, 1.05), grow=20.0,
                         drag=1.1, step=5, fade=(t + 50, t + 120))
    base = gun.location.copy()
    back = -fw * 0.55
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        for ff, k in ((f - 1, 0.0), (f + 3, 1.0), (f + 30, 0.0)):
            gun.location = base + back * k
            gun.keyframe_insert("location", frame=ff)
    finally:
        prefs.keyframe_new_interpolation_type = old
    gun.location = base


def build_s57(c, L, ev, rng):
    """Three ranks fire rolling volleys; two guns and crews; De Lannoy directs."""
    f0, f1 = ev["r57"]
    end = f1
    ox, oy = DRILL
    rows = [(5.0, 11, -6.0), (6.5, 11, -5.5), (8.0, 11, -6.0)]
    for r, (v, n, u0) in enumerate(rows):
        for i in range(n):
            u = u0 + i * 1.05 + rng.uniform(-0.06, 0.06)
            x, y = ox + u, oy + v + rng.uniform(-0.08, 0.08)
            rz = math.pi + rng.uniform(-0.08, 0.08)
            ob = put(L["musket"][(i + r) % 4], f"Mus{r}_{i}", c, x, y, rz)
            kit.animate_idle(ob, rng, f0, f1, 0.012)
            z = ob.location.z
            for q, vf in enumerate(ev["volleys57"]):
                t = vf + (2 - r) * 9 + rng.randint(0, 6)                    # the front rank fires first
                musket_shot(c, L, (x, y, z), rz, t, rng, end, f"M{r}_{i}_{q}")
                ob.rotation_euler = (-0.08, 0.0, rz)                        # a small kick back
                ob.keyframe_insert("rotation_euler", frame=t + 2)
                ob.rotation_euler = (0.0, 0.0, rz)
                ob.keyframe_insert("rotation_euler", frame=t + 14)
    for k, (u, v, dx, dy) in enumerate(((-12.0, 4.0, 0.2, -1), (-11.5, 8.0, 0.3, -1), (6.5, 6.0, -0.4, -1))):
        put(L["rank"][k % 4], f"Reserve{k}", c, ox + u, oy + v, face(dx, dy))
    # the guns and their crews
    guns = [((2.4, -3.6), math.pi + 0.22, ((0.8, -2.6), (4.0, -4.2), (2.8, -6.0)), (6.0, -4.8)),
            ((-9.6, -0.6), math.pi - 0.25, ((-11.2, 0.8), (-8.0, 0.2), (-8.6, -2.4)), (-6.2, -2.4))]
    for gi, ((u, v), aim, crew, pile) in enumerate(guns):
        x, y = ox + u, oy + v
        gun = put(L["cannon"], f"Gun{gi}", c, x, y, aim, sink=0.0)
        for k, (cu, cv) in enumerate(crew):
            ob = put(L["crew"][k], f"Crew{gi}_{k}", c, ox + cu, oy + cv, face(u - cu, v - cv) + (0.4 if k == 2 else 0.0))
            kit.animate_idle(ob, rng, f0, f1, 0.04)
        put(L["balls"][0], f"GunShot{gi}", c, ox + pile[0], oy + pile[1], rng.uniform(0, 6), s=1.0)
        _anim_walk(c, L, f"Ammo{gi}", "nair", "crate", [(ox + pile[0], oy + pile[1]), (ox + crew[1][0] + 0.8, oy + crew[1][1] + 0.6)],
                   f0, f1, 11 + gi)
        for q, cf in enumerate(ev["cannon57"]):
            cannon_shot(c, L, gun, (x, y, height(x, y)), aim, cf + gi * 28, rng, end, f"C{gi}_{q}")
    # the near ground: spare shot, kegs, crates, sitting crew, loose gravel and tussocks (K69 is full to the edge)
    for k, (u, v) in enumerate(((-3.0, -6.4), (8.6, -4.0), (-14.0, -4.6), (11.0, -7.0))):
        put(L["balls"][k % 2], f"FgShot{k}", c, ox + u, oy + v, rng.uniform(0, 6), s=1.0)
    for k, (u, v) in enumerate(((5.0, -7.2), (5.9, -6.9), (-6.8, -6.8), (-7.6, -6.3), (13.4, -3.2))):
        put((L["barrel"], L["crate"])[k % 2], f"FgStore{k}", c, ox + u, oy + v, rng.uniform(0, 3))
    for k, (u, v) in enumerate(((1.0, -8.2), (-11.0, -7.4), (9.5, -8.6))):
        put(L["gravel"][k % 2], f"FgGravel{k}", c, ox + u, oy + v, rng.uniform(0, 6), s=1.6, sink=0.0)
    for k, (u, v) in enumerate(((-1.5, -9.0), (7.0, -9.4), (-9.0, -9.2), (12.5, -8.6), (-15.0, -7.5))):
        put(L["bush"][k % 4], f"FgBush{k}", c, ox + u, oy + v, rng.uniform(0, 6), s=0.55)
    for k, (u, v) in enumerate(((-4.4, -4.6), (-3.2, -5.2), (9.8, -6.0))):
        ob = put(L["crew"][k % 3], f"FgRest{k}", c, ox + u, oy + v, rng.uniform(0, 6))
        kit.animate_idle(ob, rng, f0, f1, 0.03)
    # De Lannoy, in the tricorn, directing the drill
    dl, dp = kit.make_delannoy("DeLannoy57", c, rig=True)
    dl.location = (ox + 7.6, oy + 3.4, height(ox + 7.6, oy + 3.4))
    dl.rotation_euler[2] = face(-1.0, 0.25)
    kit.key_pose(dp, f0, {**kit.ARM_REST, **kit.DELANNOY_POINT})
    for vf in ev["volleys57"]:
        kit.key_pose(dp, vf - 14, {"armL": (0.3, -1.25, 0.0)})
        kit.key_pose(dp, vf, {"armL": (0.45, -1.35, 0.0)})
        kit.key_pose(dp, vf + 22, {"armL": (0.3, -1.25, 0.0)})
    kit.animate_rig_idle(dp, rng, f0, f1, body=0.008, head=0.0, skip=("head",))


def build_s58(c, L, ev, rng):
    """The sash: the king lays a gold sash over De Lannoy's shoulder; the drilled ranks stand behind."""
    f0, f1 = ev["r58"]
    ox, oy = DRILL
    kx, ky = ox - 4.3, oy - 0.7
    king, kp = kit.make_rig("King58", c, "king")
    court_robe("Robe58", kp)
    king.location = (kx, ky, height(kx, ky))
    king.rotation_euler[2] = face(1.0, -0.9)
    king.scale = (1.04, 1.04, 1.04)
    dx_, dy_ = ox - 3.3, oy - 0.9
    dl, dp = kit.make_delannoy("DeLannoy58", c, rig=True)
    dl.location = (dx_, dy_, height(dx_, dy_))
    dl.rotation_euler[2] = face(-0.5, -1.0)
    hat = make_tricorn("Tricorn58", c)
    hat.parent = dp["body"]
    hat.location = (-0.3, 0.22, 0.96)
    hat.rotation_euler = (0.95, 0.0, 0.15)
    hat.scale = (0.85, 0.85, 0.85)
    sash, L_s = make_sash("Sash58", c, dp["body"])
    k = ev["title58"]
    kit.key_pose(kp, f0, {**kit.ARM_REST, "head": (0, 0, 0)})
    kit.key_pose(kp, k - 40, kit.ARM_REST)
    kit.key_pose(kp, k - 8, {"armL": (0.9, 0.0, -0.2), "armR": (0.8, 0.2, 0.1), "head": (0, 0, 0)})   # lifts the sash
    kit.key_pose(kp, k + 18, {"armL": (1.25, 0.0, -0.4), "armR": (1.05, 0.2, 0.15)})                    # over the shoulder
    kit.key_pose(kp, k + 60, {"armL": (1.2, 0.0, -0.4), "armR": (1.0, 0.2, 0.15)})
    kit.key_pose(kp, k + 100, {"armL": (0.3, -0.1, 0.0), "armR": (0.3, 0.1, 0.0)})
    kit.key_pose(dp, f0, {**kit.ARM_REST, "head": (0, 0, 0)})
    kit.key_pose(dp, k - 40, {"armR": (0.55, 0.05, -0.15), "head": (0, 0, 0.0)})
    kit.key_pose(dp, k + 20, {"head": (-0.03, 0, 0.12)})                                                   # looks to the king, proud
    sash.scale = (0.0001, 0.0001, 0.0001)
    sash.keyframe_insert("scale", frame=k - 6)
    sash.scale = (1, 1, 1)
    sash.keyframe_insert("scale", frame=k + 26)
    kit.animate_rig_idle(kp, rng, f0, f1, body=0.006, head=0.0, skip=("head", "armL", "armR"))
    kit.animate_rig_idle(dp, rng, f0, f1, body=0.006, head=0.0, skip=("head",))
    # two ranks standing at attention in a line receding to the right (K70)
    ang = math.radians(13)
    for r, (v0, off) in enumerate(((3.6, 0.0), (5.1, 0.6), (6.6, 0.0))):
        for i in range(15):
            u = -16.0 + i * 1.12 + off
            x, y = ox + u * math.cos(ang) - v0 * -math.sin(ang) * 0 , oy + v0 + u * math.sin(ang)
            x = ox + u * math.cos(ang)
            ob = put(L["rank"][(i + r) % 4], f"Rank{r}_{i}", c, x, y, face(0.18, -1.0) + rng.uniform(-0.04, 0.04))
            kit.animate_idle(ob, rng, f0, f1, 0.012)
    for k_, (u, v) in enumerate(((-13.5, 2.0), (3.0, 7.0))):
        ob = put(L["rank"][k_], f"Sentry{k_}", c, ox + u, oy + v, face(0.2, -1.0))
        kit.animate_idle(ob, rng, f0, f1, 0.012)
    for k_, (u, v, s_) in enumerate(((-6.8, -3.4, 0.8), (1.4, -4.2, 0.7), (4.5, 0.2, 0.6))):         # foreground stones (K70)
        put(L["boulder"][k_ % 5], f"S58Rock{k_}", c, ox + u, oy + v, rng.uniform(0, 6), s=s_ * 1.2)
    put(L["gravel"][0], "S58Gravel", c, ox + -1.5, oy - 2.6, 0.3, s=1.3, sink=0.0)
    put(L["tree"][2], "S58Tree", c, ox + 3.2, oy + 2.4, 0.5, s=1.0, sink=0.1)


# ====================================================================== whole set
def build_world(ev, avoid):
    """avoid: (x, y) points along the camera paths, kept clear of trees and palms."""
    global ev_end
    ev_end = ev["end"]
    end = ev["end"]
    register_palette()
    rig_c = kit.new_collection("Rig")
    world_c = kit.new_collection("World")
    fort_c = kit.new_collection("Fort")
    drill_c = kit.new_collection("Drill")
    plants_c = kit.new_collection("Plants")
    lib_c = kit.new_collection("Library")
    rng = random.Random(55)
    sun = cw.scene_base(rig_c, sun_dir=(0.55, -0.5, -0.62), sun_energy=8.0, haze_density=0.0007)
    make_terrain(world_c)
    L = build_lib(lib_c)
    build_fort(fort_c, L, rng)
    build_surroundings_fort(plants_c, L, rng, avoid)
    build_drill(drill_c, L, ev, rng)
    build_surroundings_drill(plants_c, L, rng, avoid)
    sets = {}
    for tag, fn in (("S55", build_s55), ("S56", build_s56), ("S57", build_s57), ("S58", build_s58)):
        sets[tag] = kit.new_collection(f"{tag}_Actors")
        fn(sets[tag], L, ev, rng)
    for tag in sets:
        lw.set_vis(sets[tag], [ev[f"r{tag[1:]}"]])
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c, sun
