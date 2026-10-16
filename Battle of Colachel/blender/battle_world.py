"""Battle near Kollam (S25-S26, clips 32-33): the Dutch and the allied rajas march on the
Travancore lines; a shell hits the Travancore powder store, it blows up, the Nairs run and
the Dutch take the guns.

Laid out to match the Flow references frames/flow_refs/K32 (S25) and K33 (S26):
- a flat, warm dirt plain with rice paddies in a grid of raised bunds (two-green rows),
  dirt paths between them, dense palm groves and big faceted green hills behind;
- west: the allied army in ranks facing east: Dutch in blue coats with white cross-belts,
  the rajas' soldiers in white mundus with coloured turbans, field guns with gunners,
  an orange Dutch flag;
- east: a line of faceted earth ramparts with 16 bronze guns in the gaps, red-turbaned Nair
  ranks behind them, and a thatched powder store with barrels, crates and sacks.

Coordinates: metres, Z up. +X is east (toward the Travancore line), +Y north (the hills).
The battle plain is flat at z = 0. Reused: sky, sun and haze (colachel_world.scene_base),
palms, trees, bushes, huts, barrels, crates, sacks, cannons and every figure (colachel_kit),
big-leaf plants, jungle trees and the mist composite (pepper_world), the waving flag
(port_world). New kit parts (colachel_kit, S25-S27 block): allied soldiers, routed walkers,
paddy cells, ramparts, bronze guns, fireball, flames, smoke puffs, debris, ruin.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

import colachel_kit as kit
import colachel_world as cw
import pepper_world as pw
import port_world as ptw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau

ROAD = (-9.0, 9.0)                    # y range of the broad dirt road the Dutch advance along
RAMPART_X = 26.0                      # centre line of the Travancore ramparts
GAPS = [-28.0 + 8.0 * i for i in range(8)]   # embrasure gaps, two guns in each = 16 guns
GAP_W = 3.4
STORE = (47.0, 15.0)                  # the powder store
MORTAR = (-15.0, -15.0)               # the allied mortar that fires the shell
PADDIES = []                          # (cx, cy, w, d), filled below
for _cy, _d in ((17.0, 9.5), (29.5, 10.5), (-17.0, 9.5), (-29.5, 10.5), (-43.0, 11.0)):
    for _cx, _w in ((3.0, 11.0), (16.0, 11.5)):
        PADDIES.append((_cx, _cy, _w, _d))
PADDIES += [(-10.5, -43.0, 11.0, 11.0), (-24.0, -44.0, 11.5, 11.0), (29.5, -46.0, 11.5, 9.0),
            (3.0, 42.0, 11.0, 9.0), (16.0, 42.0, 11.5, 9.0)]

# Allied blocks: (name, kind, centre x, centre y, files along y, ranks along x)
BLOCKS = [("A", "dutch", -14.0, 0.0, 12, 6),
          ("B", "dutch", -16.0, 19.0, 10, 6),
          ("C", "ally", -17.0, -19.0, 10, 6),
          ("D", "ally", -31.0, 8.0, 12, 5),
          ("E", "ally", -31.0, -10.0, 10, 5),
          ("F", "dutch", -33.0, 26.0, 8, 4)]
FILE_SP, RANK_SP = 1.15, 1.3
PEAKS = [(-150.0, 112.0, 40.0, 55.0), (-85.0, 118.0, 46.0, 52.0), (-25.0, 128.0, 56.0, 58.0),
         (35.0, 112.0, 44.0, 48.0), (92.0, 124.0, 58.0, 60.0), (150.0, 104.0, 44.0, 50.0),
         (200.0, 60.0, 46.0, 55.0), (215.0, -10.0, 40.0, 55.0), (-5.0, 165.0, 70.0, 70.0), (130.0, 175.0, 72.0, 70.0)]
HAMLET = [(70.0, 30.0, 2.6), (78.0, 22.0, 2.0), (66.0, 41.0, 3.0), (-66.0, 10.0, -1.4), (-70.0, -4.0, -1.7)]
ALLIED_GUNS = [(-7.0, -11.5), (-7.0, 11.0), (-9.5, -30.0), (-11.0, 30.5)]


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


_smooth = cw._smooth


def height(x, y):
    """Flat plain (z = 0) for the battle, a soft rise at its edges, hills to the north and east."""
    dx = max(0.0, -75.0 - x, x - 105.0)
    dy = max(0.0, -85.0 - y, y - 48.0)
    d = math.hypot(dx, dy)
    h = min(1.0, d / 25.0) * (0.8 + 0.6 * _n(x, y, 18, 2.1)) if d > 0 else 0.0
    hill = 0.0
    for px, py, ph, pr in PEAKS:                    # separate faceted peaks with sky between them (K32)
        d = math.hypot(x - px, (y - py) * 1.3) / pr
        if d < 1.0:
            hill = max(hill, ph * (1 - d) ** 1.25)
    hill += _smooth(70, 100, y) * 4.0
    if hill > 1.0:
        hill += 2.5 * _n(x, y, 11, 3.3) * min(1.0, hill / 10)
    return h + hill


ground = height


def in_paddy(x, y, pad=0.0):
    return any(abs(x - cx) < w / 2 + pad and abs(y - cy) < d / 2 + pad for cx, cy, w, d in PADDIES)


def _axis(a0, a1, d0, d1, fine, coarse):
    vals, v = [], a0
    while v < a1:
        vals.append(v)
        v += fine if d0 <= v < d1 else coarse
    return vals + [a1]


def make_terrain(coll, seed=3):
    rng = random.Random(seed)
    xs = _axis(-260.0, 320.0, -80.0, 110.0, 2.5, 7.0)
    ys = _axis(-170.0, 320.0, -90.0, 55.0, 2.5, 7.0)
    bm = bmesh.new()
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                s = 2.5 if (-80 <= x < 110 and -90 <= y < 55) else 7.0
                jx, jy = rng.uniform(-0.3, 0.3) * s, rng.uniform(-0.3, 0.3) * s
            px, py = x + jx, y + jy
            row.append(bm.verts.new((px, py, height(px, py))))
        grid.append(row)
    names = ["field_dirt", "field_dirt_dk", "sand", "grass", "frond", "ghat_lo", "ghat_hi", "leaf"]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for f in bm.faces:
        c = f.calc_center_median()
        n = _n(c.x, c.y, 14, 6.1)
        if c.z > 3.0:
            k = _n(c.x, c.y, 40, 2.2) + rng.uniform(-0.25, 0.25)
            f.material_index = 4 if k < -0.15 else (5 if k < 0.2 else 6)
        elif grove_area(c.x, c.y) or c.z > 1.2:
            f.material_index = 3 if rng.random() > 0.25 else 7
        elif c.x > RAMPART_X + 2.5 + 3 * _n(c.x, c.y, 9, 4.4):
            # the Travancore side is grass (K33): faceted greens with worn dirt patches
            f.material_index = 0 if n > 0.38 else (3 if rng.random() < 0.55 else 5)
        elif ROAD[0] < c.y < ROAD[1] and -12 < c.x < RAMPART_X - 3:
            f.material_index = 0 if rng.random() > 0.3 else 2
        else:
            k = n + rng.uniform(-0.15, 0.15)
            f.material_index = 2 if k < 0.12 else (0 if k < 0.4 else 1)
    me = bpy.data.meshes.new("Terrain")
    bm.to_mesh(me)
    bm.free()
    for m in names:
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Terrain", me)
    coll.objects.link(ob)
    return ob


def grove_area(x, y):
    """Palm groves: north band, the east round the store (leaving the Nairs' escape open),
    the far west, and the foreground corners of the K32 view."""
    if 50 + 4 * _n(x, y, 12, 1.1) < y < 74 + 8 * _n(x, y, 30, 0.7):
        return True
    if x > 58 and y > 4 and math.hypot(x - STORE[0], y - STORE[1]) > 12:
        return True
    if x > 100:
        return True
    if x < -60 + 4 * _n(x, y, 10, 2.2):
        return True
    return False


# ----------------------------------------------------------------- library
def build_library(lib_c):
    pw.register_palette()                       # leaf_lt and friends for big-leaf plants and jungle trees
    lib = {}
    lib["palms"] = [kit.make_palm(f"LibPalm{i}", lib_c, seed=10 + i, height=7.5 + 0.6 * i) for i in range(6)]
    lib["trees"] = ([pw.make_vine_tree(f"LibJTree{i}", lib_c, seed=20 + i, height=7.5 + 1.2 * i, vine=False)
                     for i in range(3)] + [kit.make_tree(f"LibTree{i}", lib_c, seed=i, height=6 + i) for i in range(3)])
    lib["bushes"] = [kit.make_bush(f"LibBush{i}", lib_c, seed=i, size=0.9 + 0.25 * i) for i in range(3)]
    lib["bigleaf"] = [pw.make_bigleaf(f"LibBigLeaf{i}", lib_c, seed=i, size=1.2 + 0.35 * i) for i in range(3)]
    lib["rocks"] = [kit.make_rock(f"LibRock{i}", lib_c, seed=i, size=0.7 + 0.3 * i) for i in range(3)]
    lib["barrel"] = kit.make_barrel("LibBarrel", lib_c)
    lib["crate"] = kit.make_crate("LibCrate", lib_c, size=0.75)
    lib["sack"] = kit.make_sack("LibSack", lib_c)
    lib["cannon"] = kit.make_cannon("LibCannon", lib_c)
    lib["bronze"] = kit.make_bronze_cannon("LibBronzeCannon", lib_c)
    mb = kit.MB()
    for k, (x, y, z) in enumerate(((0, 0, 0.14), (0.29, 0, 0.14), (-0.29, 0, 0.14), (0.145, 0.25, 0.14),
                                   (-0.145, 0.25, 0.14), (0.0, -0.25, 0.14), (0.145, 0.08, 0.38), (-0.145, 0.08, 0.38),
                                   (0.0, -0.15, 0.38), (0.0, 0.0, 0.6))):
        mb.ico(T(x, y, z), "iron", r=0.14, sub=1)
    lib["balls"] = mb.obj("LibBalls", lib_c)
    lib["puffs"] = [kit.make_puff(f"LibPuff{i}", lib_c, seed=i, m=("smoke_md", "smoke_md", "smoke_dk", "smoke")[i % 4])
                    for i in range(8)]
    lib["white"] = [kit.make_puff(f"LibWhitePuff{i}", lib_c, seed=20 + i, m="smoke") for i in range(3)]
    lib["huts"] = [kit.make_hut_gable("LibHutG", lib_c, seed=3), kit.make_hut_hip("LibHutH", lib_c, seed=4)]
    # figures: static (instanced) and walker templates (cloned)
    lib["dutch"] = [kit.make_figure(f"LibDutch{i}", lib_c, "dutch", seed=i) for i in range(3)]
    lib["gunner"] = [kit.make_figure(f"LibGunner{i}", lib_c, "dutch", seed=10 + i, armed=False) for i in range(2)]
    lib["w_dutch"] = [kit.make_walker(f"LibWDutch{i}", lib_c, "dutch", seed=i) for i in range(3)]
    lib["w_officer"] = [kit.make_walker("LibWOfficer", lib_c, "dutch", seed=40)]
    kit.recolor(lib["w_officer"][0][1]["body"], strip=("steel", "post"))           # officer: no musket
    lib["w_ally"] = [kit.make_ally_walker(f"LibWAlly{i}", lib_c, seed=i, turban=t)
                     for i, t in enumerate(kit.ALLY_TURBANS)]
    lib["w_nair"] = [kit.make_walker(f"LibWNair{i}", lib_c, "nair", seed=i) for i in range(3)] + \
                    [kit.make_walker("LibWNairSp", lib_c, "nair_spear", seed=7)]
    lib["w_gunner"] = [kit.make_walker("LibWNGunner", lib_c, "commander", seed=3)]
    for root, parts in lib["w_dutch"] + lib["w_officer"] + lib["w_ally"] + lib["w_nair"] + lib["w_gunner"]:
        kit.hide_source(root)
        for p in parts.values():
            p.hide_render = p.hide_viewport = True
    return lib


def _put(src, name, coll, x, y, rz=0.0, s=1.0, sink=0.03, z=None):
    return kit.instance(src, name, coll, (x, y, (height(x, y) if z is None else z) - sink), rot_z=rz, scale=s)


def _walker(tmpl, name, coll):
    root, parts = kit.clone_walker(tmpl[1], name, coll)
    for p in parts.values():
        p.hide_render = p.hide_viewport = False
    return root, parts


# ----------------------------------------------------------------- the field
def build_paddies(coll):
    for k, (cx, cy, w, d) in enumerate(PADDIES):
        ob = kit.make_paddy_cell(f"Paddy{k}", coll, w=w, d=d, seed=k)
        ob.location = (cx, cy, height(cx, cy))


def build_ramparts(coll, lib):
    """Earth ramparts in segments along x = RAMPART_X with 8 gaps, two bronze guns in each,
    and a return wall running east at the south end (K32 lower right)."""
    edges = [-38.0] + [g for gy in GAPS for g in (gy - GAP_W / 2, gy + GAP_W / 2)] + [38.0]
    k = 0
    for a, b in zip(edges[0::2], edges[1::2]):
        L = b - a
        ob = kit.make_rampart(f"Rampart{k}", coll, length=L, h=1.95, base_w=3.8, top_w=2.4, seed=k)
        ob.location = (RAMPART_X, (a + b) / 2, 0.0)
        k += 1
    for j, (x0, x1) in enumerate(((RAMPART_X + 2.5, RAMPART_X + 11.0), (RAMPART_X + 13.5, RAMPART_X + 21.0))):
        ob = kit.make_rampart(f"RampartS{j}", coll, length=x1 - x0, h=2.0, base_w=4.2, top_w=2.2, seed=20 + j)
        ob.location = ((x0 + x1) / 2, -39.5, 0.0)
        ob.rotation_euler[2] = math.pi / 2
    guns = []
    for gi, gy in enumerate(GAPS):
        for s in (-1, 1):
            y = gy + s * 0.85
            g = _put(lib["bronze"], f"TGun{len(guns)}", coll, RAMPART_X + 1.2, y, rz=math.pi / 2, sink=0.0)
            guns.append(g)
        _put(lib["balls"], f"TBalls{gi}", coll, RAMPART_X + 4.2, gy + 0.3, rz=gi, sink=0.0)
        if gi % 2 == 0:
            _put(lib["barrel"], f"TPowder{gi}", coll, RAMPART_X + 4.6, gy - 1.3, sink=0.0)
    return guns


def build_store(coll, lib):
    """The thatched powder store with barrels, crates and sacks round it (K32 right).
    Returns (store object, the props that the blast throws)."""
    sx, sy = STORE
    store = kit.make_hut_gable("PowderStore", coll, w=5.4, d=4.2, h=2.3, seed=8)
    store.location = (sx, sy, 0.0)
    store.rotation_euler[2] = -math.pi / 2 + 0.08         # door toward the guns (west)
    props = []
    rng = random.Random(5)
    spots = [(-4.0, -1.5), (-4.0, -0.7), (-4.0, 0.1), (-4.7, -1.1), (-4.7, -0.3), (-3.5, 2.6), (-2.7, 2.9),
             (3.6, -2.9), (3.0, -3.4), (-1.0, -3.7), (-0.2, -3.8), (0.6, -3.7), (2.2, 3.5), (3.4, 3.2)]
    for k, (dx, dy) in enumerate(spots):
        props.append(_put(lib["barrel"], f"StoreBarrel{k}", coll, sx + dx, sy + dy, rz=rng.uniform(0, TAU), sink=0.0))
    for k, (dx, dy, dz) in enumerate(((-4.35, -0.7, 0.95), (-4.35, -1.5, 0.95), (-1.0, -3.7, 0.95))):
        props.append(_put(lib["barrel"], f"StoreBarrelTop{k}", coll, sx + dx, sy + dy, rz=k, sink=0.0, z=dz))
    for k, (dx, dy) in enumerate(((-3.6, 4.2), (4.2, 1.5), (4.0, 0.6), (-5.6, 1.6))):
        props.append(_put(lib["crate"], f"StoreCrate{k}", coll, sx + dx, sy + dy, rz=rng.uniform(-0.3, 0.3), sink=0.0))
    for k, (dx, dy) in enumerate(((1.6, -3.9), (2.3, -4.2), (-5.4, 3.0), (-5.0, 3.6))):
        props.append(_put(lib["sack"], f"StoreSack{k}", coll, sx + dx, sy + dy, rz=rng.uniform(0, TAU), sink=0.0))
    return store, props


def build_plants(coll, lib, keep=()):
    rng = random.Random(31)
    palms, trees, bushes, bigleaf = lib["palms"], lib["trees"], lib["bushes"], lib["bigleaf"]
    cell = {}

    def free(x, y, r):
        gx, gy = int(x // 6), int(y // 6)
        for i in range(gx - 1, gx + 2):
            for j in range(gy - 1, gy + 2):
                for a, b, rb in cell.get((i, j), ()):
                    if (x - a) ** 2 + (y - b) ** 2 < (r + rb) ** 2:
                        return False
        return True

    def add(x, y, r):
        cell.setdefault((int(x // 6), int(y // 6)), []).append((x, y, r))

    keep = list(keep) + [(x, y, 5.5) for x, y, _ in HAMLET]

    def kept(x, y):
        return any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep)

    k = 0
    for i in range(70000):                                  # dense groves, palms several rows deep
        x, y = rng.uniform(-200, 260), rng.uniform(-120, 160)
        if not grove_area(x, y) or kept(x, y):
            continue
        far = max(0.0, y - 90) + max(0.0, x - 130) + max(0.0, -110 - x)
        if height(x, y) > 30 or (far > 0 and rng.random() < 0.6):
            continue
        r = 2.3 if far == 0 else 3.6
        if not free(x, y, r):
            continue
        add(x, y, r)
        if rng.random() < 0.72:
            src, s = rng.choice(palms), rng.uniform(0.9, 1.25)
        else:
            src, s = rng.choice(trees), rng.uniform(0.9, 1.3)
        _put(src, f"Grove{k}", coll, x, y, rng.uniform(0, TAU), s * (1 + far / 300), sink=0.2)
        k += 1
        if k > 2800:
            break
    j = 0
    for i in range(9000):                                  # undergrowth in the groves
        x, y = rng.uniform(-120, 200), rng.uniform(-100, 110)
        if not grove_area(x, y) or kept(x, y) or height(x, y) > 12:
            continue
        _put(rng.choice(bushes + bigleaf), f"Under{j}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.8, 1.5))
        j += 1
        if j > 2600:
            break
    # foreground palms and big leaves in the corners of the K32 view, a few lone palms on the plain
    for i, (x, y, s) in enumerate(((-46, -58, 1.15), (-38, -64, 1.0), (-52, -49, 1.2), (-33, -55, 0.95),
                                   (-58, -62, 1.1), (44, -62, 1.1), (50, -56, 1.0), (-48, 34, 1.0),
                                   (-44, 40, 1.15), (-22, 46, 1.0), (36, 46, 1.1), (-33, -33, 1.1), (-37, -29, 0.95),
                                   (-31, -38, 1.2), (44, -47, 1.15), (39, -51, 1.0), (49, -50, 0.9))):
        if not kept(x, y):
            _put(palms[i % len(palms)], f"FgPalm{i}", coll, x, y, rng.uniform(0, TAU), s, sink=0.2)
    for i in range(60):
        x, y = rng.uniform(-62, -28), rng.uniform(-72, -44)
        if not kept(x, y):
            _put(rng.choice(bigleaf + bushes), f"FgLeaf{i}", coll, x, y, rng.uniform(0, TAU), rng.uniform(1.0, 1.8))
    for i in range(45):                                    # tufts and stones along the bunds and paths
        x, y = rng.uniform(-50, 45), rng.uniform(-55, 48)
        if in_paddy(x, y, 0.3) or abs(x - RAMPART_X) < 4 or kept(x, y):
            continue
        src = rng.choice(bushes) if rng.random() < 0.9 else rng.choice(lib["rocks"])
        _put(src, f"Tuft{i}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.4, 0.8))
    # a hamlet at the grove edge behind the Travancore line (K33 top right) and one far west
    for i, (x, y, rz) in enumerate(HAMLET):
        _put(lib["huts"][i % 2], f"Hut{i}", coll, x, y, rz, 1.0, sink=0.05)


# ----------------------------------------------------------------- the armies
def block_slots(cx, cy, files, ranks):
    """(x, y, rank) for each man of a block facing +X (rank 0 = front)."""
    out = []
    for r in range(ranks):
        for f in range(files):
            out.append((cx + (ranks - 1) / 2 * RANK_SP - r * RANK_SP, cy + (f - (files - 1) / 2) * FILE_SP, r))
    return out


def build_allies(coll, lib, ev):
    """The allied army. Blocks stand in ranks, march east from ev['march'], halt at the
    paddies; the front of block A charges the guns after the blast (ev['charge'] .. ev['taken'])."""
    rng = random.Random(9)
    end = ev["end"]
    walkers = []
    E = -math.pi / 2                                  # heading that faces +X
    for name, kind, cx, cy, files, ranks in BLOCKS:
        for i, (x, y, r) in enumerate(block_slots(cx, cy, files, ranks)):
            x += rng.uniform(-0.08, 0.08)
            y += rng.uniform(-0.08, 0.08)
            if kind == "dutch":
                tmpl = lib["w_dutch"][(i + r) % len(lib["w_dutch"])]
            else:
                tmpl = lib["w_ally"][rng.randrange(len(lib["w_ally"]))]
            root, parts = _walker(tmpl, f"{name}{i}", coll)
            root.location = (x, y, 0.0)
            root.rotation_euler = (0, 0, E)
            kit.animate_idle(root, rng, 1, ev["march"] - 8, amount=0.02)
            root.rotation_euler = (0, 0, E)
            front = cx + (ranks - 1) / 2 * RANK_SP
            if name == "A":
                d1 = 1.2 * (ev["charge"] - ev["march"]) / kit.FPS
                legs = [(ev["march"], ev["charge"], (x, y), (x + d1, y))]
                if r < 4:                              # the storming party
                    gap = min(GAPS, key=lambda g: abs(g - y))
                    tx = RAMPART_X + 2.5 + rng.uniform(0, 2.0) if abs(gap - y) < GAP_W / 2 - 0.4 else \
                        RAMPART_X - 3.2 - r * 0.9 + rng.uniform(-0.3, 0.3)
                    arrive = ev["taken"] - rng.randint(0, 18) + r * 6
                    run = (ev["charge"] + r * 4, min(arrive, end), (x + d1, y), (tx, y + rng.uniform(-0.4, 0.4)))
                    kit.animate_route(root, parts, legs, height, stride_frames=14, swing=0.45, heading=E, phase=r)
                    kit.animate_route(root, parts, [run], height, stride_frames=9, swing=0.8, lean=0.22,
                                      heading=E, bob=0.08, phase=i)
                else:
                    legs.append((ev["charge"], end, (x + d1, y), (x + d1 + 1.0 * (end - ev["charge"]) / kit.FPS, y)))
                    kit.animate_route(root, parts, legs, height, stride_frames=14, swing=0.45, heading=E, phase=r)
            else:
                stop = -4.5 if abs(cy) > 10 else -9.0      # halt short of the paddies
                f0 = ev["march"] + rng.randint(0, 6)
                dx = min(max(0.0, stop - front), 1.2 * (ev["halt"] - f0) / kit.FPS)
                legs = [(f0, f0 + max(20, int(dx / 1.2 * kit.FPS)), (x, y), (x + dx, y))]
                kit.animate_route(root, parts, legs, height, stride_frames=14, swing=0.45, heading=E, phase=r)
            walkers.append(root)
    # officers in front of the Dutch blocks, the orange flag carried with block A and B
    for k, (name, kind, cx, cy, files, ranks) in enumerate(BLOCKS[:2]):
        front = cx + (ranks - 1) / 2 * RANK_SP
        root, parts = _walker(lib["w_officer"][0], f"Officer{name}", coll)
        x, y = front + 1.8, cy - files * FILE_SP / 2 + 1.0
        root.location = (x, y, 0)
        d1 = 1.2 * (ev["charge"] - ev["march"]) / kit.FPS if name == "A" else max(0.0, -4.5 - front)
        f1 = ev["charge"] if name == "A" else ev["march"] + int(d1 / 1.2 * kit.FPS) + 20
        legs = [(ev["march"], f1, (x, y), (x + d1, y))]
        if name == "A":
            legs.append((ev["charge"], ev["taken"], (x + d1, y), (RAMPART_X - 2.0, y)))
        kit.animate_route(root, parts, legs, height, heading=E)
        bearer, bparts = _walker(lib["w_dutch"][0], f"FlagBearer{name}", coll)
        bx, by = cx + 0.3, cy + files * FILE_SP / 2 + 0.9
        bearer.location = (bx, by, 0)
        legs = [(ev["march"], f1, (bx, by), (bx + d1, by))]
        if name == "A":
            legs.append((ev["charge"], ev["taken"] + 10, (bx + d1, by), (RAMPART_X - 3.0, by)))
        kit.animate_route(bearer, bparts, legs, height, heading=E)
        pole = kit.MB()
        pole.seg((0.3, 0.05, 0.5), (0.3, 0.05, 4.6), 0.045, 0.04, "post", sides=6)
        pole.ico(T(0.3, 0.05, 4.68), "brass", r=0.07, sub=1)
        po = pole.obj(f"FlagPole{name}", coll, parent=bearer)
        fl = ptw.make_flag(f"Flag{name}", coll, w=1.9, h=1.25, m="flag_o")
        fl.parent = bearer
        fl.location = (0.33, 0.05, 4.5)
        fl.rotation_euler[2] = math.pi + 0.3
    # field guns with Dutch gunners; they fire at the start ("the war goes the Dutch way")
    shots = []
    for k, (x, y) in enumerate(ALLIED_GUNS):
        g = _put(lib["cannon"], f"AGun{k}", coll, x, y, rz=-math.pi / 2, sink=0.0)
        for j, (dx, dy, rz) in enumerate(((-1.6, 0.9, -1.2), (-1.4, -1.0, -1.9), (-2.4, 0.2, -1.6))):
            ob = _put(lib["gunner"][(k + j) % 2], f"AGunner{k}_{j}", coll, x + dx, y + dy, rz=rz, sink=0.0)
            kit.animate_idle(ob, rng, 1, end, amount=0.03)
        _put(lib["balls"], f"ABalls{k}", coll, x - 2.6, y - 1.4, sink=0.0)
        shots.append(((x + 1.65, y, 0.955), (1, 0, 0), ev["s25_shots"][k % len(ev["s25_shots"])] + 9 * k))
    # the mortar that fires the shell
    mx, my = MORTAR
    mo = _put(lib["cannon"], "Mortar", coll, mx, my, rz=-0.45, sink=0.0)
    mo.rotation_euler[0] = 0.5
    for j, (dx, dy, rz) in enumerate(((-1.3, -1.0, -0.9), (1.2, -1.2, -0.2))):
        ob = _put(lib["gunner"][j], f"MGunner{j}", coll, mx + dx, my + dy, rz=rz, sink=0.0)
        kit.animate_idle(ob, rng, 1, end, amount=0.03)
    return walkers, shots


def build_nairs(coll, lib, ev):
    """Nair ranks behind each rampart segment and gunners at the 16 guns. They stand ready
    (idle) and run east and south-east, away from the guns, after the blast."""
    rng = random.Random(17)
    end = ev["end"]
    W = math.pi / 2                                   # heading that faces -X (toward the allies)
    men = []
    edges = [-38.0] + [g for gy in GAPS for g in (gy - GAP_W / 2, gy + GAP_W / 2)] + [38.0]
    for si, (a, b) in enumerate(zip(edges[0::2], edges[1::2])):
        n_files = max(2, int((b - a - 0.6) / 0.95))
        for r in range(3):
            for f in range(n_files):
                y = a + 0.6 + (f + 0.5) * (b - a - 1.2) / n_files + rng.uniform(-0.1, 0.1)
                x = RAMPART_X + 3.0 + r * 1.15 + rng.uniform(-0.1, 0.1)
                men.append((x, y, lib["w_nair"][rng.randrange(len(lib["w_nair"]))]))
    for gy in GAPS:                                   # gun crews: one behind each gun
        for s in (-1, 1):
            men.append((RAMPART_X + 3.6 + rng.uniform(-0.2, 0.2), gy + s * 1.4, lib["w_gunner"][0]))
    for k in range(34):                               # reserve between the line and the store
        x, y = rng.uniform(37, 43), rng.uniform(-6, 26)
        if math.hypot(x - STORE[0], y - STORE[1]) < 6:
            continue
        men.append((x, y, lib["w_nair"][rng.randrange(len(lib["w_nair"]))]))
    roots = []
    for i, (x, y, tmpl) in enumerate(men):
        root, parts = _walker(tmpl, f"Nair{i}", coll)
        root.location = (x, y, 0.0)
        root.rotation_euler = (0, 0, W)
        f_run = ev["run"] + int(rng.uniform(0, 1) ** 1.5 * 30) + int(max(0.0, 20 - math.hypot(x - STORE[0], y - STORE[1])) * -0.6)
        kit.animate_idle(root, rng, 1, f_run - 6, amount=0.025)
        root.rotation_euler = (0, 0, W)
        # escape: east and south-east, fanning out, away from the guns and the burning store
        if y < -24:
            ang = math.radians(rng.uniform(-6, 14))             # along the south wall, eastward
        elif y < 4:
            ang = math.radians(rng.uniform(-55, -15))
        elif y < 26:
            ang = math.radians(rng.uniform(-62, -38))           # under the store, south-east
        else:
            ang = math.radians(rng.uniform(-25, 20))
        speed = rng.uniform(3.6, 4.8)
        dist = speed * (end - f_run) / kit.FPS
        tx, ty = x + math.cos(ang) * dist, y + math.sin(ang) * dist
        # do not run through the store: swing round it
        legs = [(f_run, end, (x, y), (tx, ty))]
        kit.animate_route(root, parts, legs, height, stride_frames=9, swing=0.8, lean=0.22, heading=W,
                          bob=0.08, turn=6, phase=i)
        roots.append(root)
    return roots


# ----------------------------------------------------------------- gun smoke, the shell, the blast
def gun_smoke(coll, lib, shots, end, rng, name="GunSmoke"):
    """A burst of faceted white smoke and a brief flash at each muzzle for each shot.
    shots: [((x, y, z) muzzle, (dx, dy, 0) barrel direction, frame)]."""
    k = 0
    kit.fx_materials()
    for (mx, my, mz), (dx, dy, _), f in shots:
        if f >= end:
            continue
        fl = kit.make_fireball(f"{name}Flash{k}", coll, seed=k, r=0.55)
        fl.location = (mx + dx * 0.5, my + dy * 0.5, mz)
        fl.scale = (0, 0, 0)
        fl.keyframe_insert("scale", frame=f - 1)
        fl.scale = (1, 1, 1)
        fl.keyframe_insert("scale", frame=f + 1)
        fl.scale = (0, 0, 0)
        fl.keyframe_insert("scale", frame=f + 4)
        for j in range(6):
            src = lib["white"][(k + j) % len(lib["white"])]
            ob = kit.instance(src, f"{name}{k}_{j}", coll, (mx, my, mz))
            v = (dx * rng.uniform(1.5, 4.0) + rng.uniform(-0.5, 0.5), dy * rng.uniform(1.5, 4.0) + rng.uniform(-0.5, 0.5),
                 rng.uniform(1.6, 3.0))
            kit.animate_puff(ob, f + j, min(end, f + 90), (mx + dx * 0.6 * j, my + dy * 0.6 * j, mz + 0.15 * j), v,
                             s0=0.3, s1=rng.uniform(0.6, 1.0), grow=10, drag=0.5, fade=(f + 25, f + 90))
        k += 1


def build_blast(coll, lib, ev, store, props, rng):
    """Mortar shot -> shell arc -> it crashes through the store roof (smoking fuse) -> the store
    blows up in a faceted fireball, debris flies, a tall column of grey smoke rises and the
    ruin keeps burning to the end ("Remember that gunpowder store")."""
    end = ev["end"]
    fire, hit, boom = ev["mortar"], ev["impact"], ev["blast"]
    sx, sy = STORE
    kit.fx_materials()
    # the mortar shot
    m0 = Vector((MORTAR[0] + 0.7, MORTAR[1] + 1.2, 1.9))
    gun_smoke(coll, lib, [((m0.x, m0.y, m0.z), (0.6, 0.35, 0), fire)], end, rng, name="MortarSmoke")
    # shell on a ballistic arc landing on the roof
    target = Vector((sx - 0.4, sy + 0.2, 3.6))
    shell = kit.make_shell("Shell", coll, r=0.55)
    t_fl = (hit - fire) / kit.FPS
    g = 9.8 * 0.55                                  # a slightly floaty arc so it reads on screen
    v = (target - m0) / t_fl
    v.z += 0.5 * g * t_fl
    kit.animate_ballistic(shell, fire, tuple(m0), tuple(v), lambda x, y: -50.0, hit, g=g, step=1)
    shell.scale = (1, 1, 1)
    shell.keyframe_insert("scale", frame=hit)
    shell.scale = (0, 0, 0)
    shell.keyframe_insert("scale", frame=hit + 1)
    for k in range(int(t_fl * kit.FPS / 2)):         # smoke trail
        f = fire + 2 * k
        t = (f - fire) / kit.FPS
        p = m0 + v * t
        p.z -= 0.5 * g * t * t
        ob = kit.instance(lib["white"][k % 3], f"ShellTrail{k}", coll, tuple(p))
        kit.animate_puff(ob, f, min(end, f + 70), tuple(p), (0, 0, 0.3), s0=0.18, s1=0.5, grow=10, fade=(f + 20, f + 70))
    # impact: thatch bursts, a thin fuse smoke curls up from the roof until the blast
    for k in range(8):
        ob = kit.make_puff(f"ThatchBurst{k}", coll, seed=40 + k, m="thatch")
        ob.scale = (0.35, 0.25, 0.12)
        kit.animate_ballistic(ob, hit, tuple(target), (rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(2, 5)),
                              height, boom, spin=(4, 3, 2))
    for k in range(int((boom - hit) / 4)):
        f = hit + 4 * k
        ob = kit.instance(lib["white"][k % 3], f"Fuse{k}", coll, tuple(target))
        kit.animate_puff(ob, f, boom, tuple(target), (0.3, 0.1, 1.4), s0=0.2, s1=0.7, grow=14)
    # BLAST: the store goes, the ruin appears
    swap = boom + 9                                   # the shed stands a moment inside the fireball (K33)
    store.keyframe_insert("scale", frame=swap - 1)
    store.scale = (0, 0, 0)
    store.keyframe_insert("scale", frame=swap)
    store.scale = (1, 1, 1)
    ruin = kit.make_ruin("StoreRuin", coll, w=5.4, d=4.2, seed=3)
    ruin.location = (sx, sy, 0.0)
    ruin.rotation_euler[2] = store.rotation_euler[2]
    ruin.scale = (0, 0, 0)
    ruin.keyframe_insert("scale", frame=swap - 1)
    ruin.scale = (1, 1, 1)
    ruin.keyframe_insert("scale", frame=swap)
    # fireball: grows in a few frames, swells, then sinks into the burning ruin
    for k, (r, off, seed) in enumerate(((4.2, (0, 0, 3.4), 1), (2.8, (1.6, -1.0, 5.6), 2), (2.5, (-1.8, 1.2, 5.0), 3),
                                        (2.2, (0.4, 1.6, 7.6), 4))):
        fb = kit.make_fireball(f"Fireball{k}", coll, seed=seed, r=r)
        fb.location = (sx + off[0], sy + off[1], off[2])
        fb.rotation_euler = (rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 6))
        for f, s in ((boom - 1, 0.0), (boom + 2 + k, 0.75), (boom + 7 + k, 1.0), (boom + 26, 1.12),
                     (boom + 44, 0.8), (boom + 70 - 6 * k, 0.0)):
            fb.scale = (s, s, s)
            fb.keyframe_insert("scale", frame=f)
        fb.keyframe_insert("rotation_euler", frame=boom)
        fb.rotation_euler.z += 0.5
        fb.keyframe_insert("rotation_euler", frame=boom + 70)
    # light from the blast (the sun stays the only key light; this is the explosion's own glow)
    ld = bpy.data.lights.new("BlastLight", "POINT")
    ld.color = (1.0, 0.62, 0.25)
    ld.shadow_soft_size = 3.0
    lo = bpy.data.objects.new("BlastLight", ld)
    coll.objects.link(lo)
    lo.location = (sx, sy, 6.0)
    for f, e in ((boom - 1, 0.0), (boom + 2, 30000.0), (boom + 12, 20000.0), (boom + 40, 8000.0),
                 (boom + 80, 4000.0), (end, 3500.0)):
        ld.energy = e
        ld.keyframe_insert("energy", frame=f)
    # debris: planks, thatch, barrels and crates flung outward
    for k in range(34):
        kind = k % 3
        mb = kit.MB(bevel=0.01)
        if kind == 0:
            mb.box(S(0.22, rng.uniform(1.2, 2.4), 0.07), "plank")
        elif kind == 1:
            mb.box(S(rng.uniform(0.6, 1.2), rng.uniform(0.5, 1.0), 0.14), rng.choice(("thatch", "thatch_dk")))
        else:
            mb.box(S(0.12, rng.uniform(0.6, 1.3), 0.12), "beam")
        ob = mb.obj(f"Debris{k}", coll)
        a = rng.uniform(0, TAU)
        sp = rng.uniform(6, 15)
        vel = (math.cos(a) * sp, math.sin(a) * sp, rng.uniform(7, 17))
        kit.animate_ballistic(ob, boom, (sx, sy, rng.uniform(1.5, 4.0)), vel, height, end,
                              spin=(rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(-4, 4)))
    for k, ob in enumerate(props):                  # the store's barrels, crates and sacks go too
        d = Vector((ob.location.x - sx, ob.location.y - sy, 0))
        d = d.normalized() if d.length > 0.1 else Vector((1, 0, 0))
        sp = rng.uniform(5, 12)
        kit.animate_ballistic(ob, boom + rng.randint(0, 2), tuple(ob.location),
                              (d.x * sp, d.y * sp, rng.uniform(5, 13)), height, end,
                              spin=(rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(-3, 3)), hide_before=False)
    # smoke: an expanding dark burst, then a tall column of grey faceted puffs to the end
    for k in range(18):
        a = rng.uniform(0, TAU)
        ob = kit.instance(lib["puffs"][k % 8], f"BlastSmoke{k}", coll, (sx, sy, 3))
        v = (math.cos(a) * rng.uniform(1.5, 3.5), math.sin(a) * rng.uniform(1.5, 3.5), rng.uniform(2.0, 6.0))
        kit.animate_puff(ob, boom + 2 + k % 5, end, (sx + math.cos(a), sy + math.sin(a), rng.uniform(2.5, 6)), v,
                         s0=0.8, s1=rng.uniform(2.0, 3.0), grow=20, drag=0.35)
    k = 0
    f = boom + 6
    while f < end:
        ob = kit.instance(lib["puffs"][k % 8], f"Column{k}", coll, (sx, sy, 4))
        rise = rng.uniform(3.4, 4.6)
        kit.animate_puff(ob, f, end, (sx + rng.uniform(-1.2, 1.2), sy + rng.uniform(-1.2, 1.2), rng.uniform(3, 5)),
                         (0.5 + rng.uniform(-0.3, 0.3), 0.5 + rng.uniform(-0.3, 0.3), rise), drag=0.16,
                         s0=0.9, s1=rng.uniform(1.6, 2.4) + 0.7 * min(1.0, (f - boom) / 120), grow=34)
        k += 1
        f += 3
    # the ruin burns
    for k, (dx, dy, s) in enumerate(((0.0, 0.0, 1.6), (-1.6, 1.0, 1.1), (1.5, -0.8, 1.2), (1.2, 1.3, 0.9),
                                     (-1.4, -1.2, 1.0), (-3.4, 2.0, 0.7), (3.0, -2.6, 0.7))):
        fl = kit.make_flames(f"Flames{k}", coll, seed=k, size=s)
        fl.location = (sx + dx, sy + dy, 0.25)
        fl.scale = (0, 0, 0)
        fl.keyframe_insert("scale", frame=boom + 8)
        fl.scale = (1, 1, 1)
        kit.animate_flicker(fl, rng, boom + 14, end)
    # a couple of burning patches where debris fell
    for k in range(6):
        a = rng.uniform(0, TAU)
        r = rng.uniform(5, 10)
        fl = kit.make_flames(f"SpotFire{k}", coll, seed=20 + k, size=0.45)
        x, y = sx + math.cos(a) * r, sy + math.sin(a) * r
        fl.location = (x, y, height(x, y))
        fl.scale = (0, 0, 0)
        fl.keyframe_insert("scale", frame=boom + 20 + k * 4)
        fl.scale = (1, 1, 1)
        kit.animate_flicker(fl, rng, boom + 24 + k * 4, end)
    return lo


def build_world(ev, keep=()):
    """Everything but the camera. ev: real frame numbers of the story events
    (march, s25_shots, t_shots, halt, mortar, impact, blast, run, charge, taken, end)."""
    rng = random.Random(23)
    world_c = kit.new_collection("World")
    field_c = kit.new_collection("Field")
    plants_c = kit.new_collection("Plants")
    allies_c = kit.new_collection("Allies")
    nairs_c = kit.new_collection("Nairs")
    fx_c = kit.new_collection("FX")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    # sky, low warm sun from the north-west (shadows fall to the right and toward the camera, K32), haze
    cw.scene_base(rig_c, sun_dir=(0.8, -0.28, -0.45), sun_energy=8.0, haze_density=0.0003)
    lib = build_library(lib_c)
    make_terrain(world_c)
    build_paddies(field_c)
    guns = build_ramparts(field_c, lib)
    store, props = build_store(field_c, lib)
    build_plants(plants_c, lib, keep)
    allies, shots = build_allies(allies_c, lib, ev)
    build_nairs(nairs_c, lib, ev)
    # the guns trade fire in S25: allied guns first, then the Travancore guns answer
    tshots = []
    for k, g in enumerate(guns):
        if k % 3 == 1:
            continue
        f = ev["t_shots"][0] + rng.randint(0, ev["t_shots"][1] - ev["t_shots"][0])
        tshots.append(((g.location.x - 1.65, g.location.y, 0.955), (-1, 0, 0), f))
    gun_smoke(fx_c, lib, shots + tshots, ev["mortar"] + 40, rng)
    build_blast(fx_c, lib, ev, store, props, rng)
    for ob in lib_c.objects:
        if ob.type == "MESH":
            kit.hide_source(ob)
    return rig_c
