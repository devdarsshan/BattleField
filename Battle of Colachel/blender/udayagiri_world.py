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
import colachel_world as cw
import landing_world as lw
import port_world as pw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau
DRILL = (100.0, 0.0)

EXTRA = {
    "fort_stone":    (0.62, 0.59, 0.53),
    "fort_stone_dk": (0.52, 0.49, 0.44),
    "fort_stone_lt": (0.70, 0.67, 0.61),
    "fort_grey":     (0.47, 0.45, 0.43),
    "flag_a":        (0.64, 0.59, 0.51),
    "flag_b":        (0.57, 0.53, 0.46),
    "flag_c":        (0.69, 0.64, 0.56),
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
    names = ["field_dirt", "field_dirt_dk", "grass", "grass_lt", "jungle", "far_hill", "rock", "dirt_dk", "laterite"]
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        m = plateau_mask(c.x, c.y)
        nz = f.normal.z
        k = _n(c.x, c.y, 7.0, 3.3) + rng.uniform(-0.15, 0.15)
        if m < 0.015:
            f.material_index = 1 if k > 0.28 else 0
        elif nz < 0.62:
            f.material_index = 6 if rng.random() < 0.45 else (8 if rng.random() < 0.3 else 7)
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
STONES = ("fort_stone", "fort_stone", "fort_stone_dk", "fort_stone_lt", "fort_stone")


def _blocks(mb, a, b, nrm, h, rng, gap=None, ch=0.42, z0=-0.35, mats=STONES, jit=0.07):
    """Courses of chunky stone blocks on a wall face from plan point a to b, outward normal nrm.
    gap = (s0, s1, z_top) in metres along the face: no blocks there (a gateway)."""
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    ang = math.atan2(uy, ux)
    n = max(2, int(round((h - z0) / ch)))
    hh = (h - z0) / n
    for i in range(n):
        z = z0 + (i + 0.5) * hh
        s = -rng.uniform(0.0, 0.9)
        while s < L - 0.05:
            w = rng.uniform(0.75, 1.55)
            s0, s1 = max(s, 0.0), min(s + w, L)
            s += w
            if s1 - s0 < 0.2:
                continue
            sm = (s0 + s1) / 2
            if gap and gap[0] < sm < gap[1] and z < gap[2]:
                continue
            d = 0.14 - rng.uniform(0.0, jit * 2)
            cx, cy = ax + ux * sm - nrm[0] * d, ay + uy * sm - nrm[1] * d
            mb.box(T(cx, cy, z) @ Rz(ang) @ S(s1 - s0 - 0.04, 0.28, hh * rng.uniform(0.9, 1.0) - 0.03),
                   rng.choice(mats))


def make_stone_wall(name, coll, length, h, thick=1.6, seed=0, crenel=True, c_h=0.85, gap=None, broken=0.0,
                    mats=STONES, ends=True, core_m="fort_stone_dk", cap=True):
    """Blocky low-poly stone wall along X, centred on the origin, base below ground. Both long faces (and the
    ends) are courses of chunky blocks; the top has a coping and chunky merlons. gap=(x0, x1, z_top) leaves a
    gateway through the thickness, with jambs and a lintel (a tower or gatehouse is a short thick wall)."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.022)
    L, t = length, thick
    z0 = -0.4
    if gap:
        g0, g1, zh = gap
        for xa, xb, za, zb in ((-L / 2, g0, z0, h), (g1, L / 2, z0, h), (g0, g1, zh, h)):
            mb.box(T((xa + xb) / 2, 0, (za + zb) / 2) @ S(xb - xa - 0.1, t - 0.2, zb - za), core_m)
        for xj in (g0 - 0.22, g1 + 0.22):
            mb.box(T(xj, 0, (zh + z0) / 2) @ S(0.44, t + 0.04, zh - z0), "fort_stone_lt")
        mb.box(T((g0 + g1) / 2, 0, zh + 0.12) @ S(g1 - g0 + 0.9, t + 0.06, 0.28), "fort_stone_lt")
    else:
        mb.box(T(0, 0, (h + z0) / 2) @ S(L - 0.1, t - 0.2, h - z0), core_m)
    gs_f = (gap[0] + L / 2, gap[1] + L / 2, gap[2]) if gap else None
    gs_b = (L / 2 - gap[1], L / 2 - gap[0], gap[2]) if gap else None
    _blocks(mb, (-L / 2, t / 2), (L / 2, t / 2), (0, 1), h, rng, gs_f, mats=mats)
    _blocks(mb, (L / 2, -t / 2), (-L / 2, -t / 2), (0, -1), h, rng, gs_b, mats=mats)
    if ends:
        _blocks(mb, (L / 2, t / 2), (L / 2, -t / 2), (1, 0), h, rng, mats=mats)
        _blocks(mb, (-L / 2, -t / 2), (-L / 2, t / 2), (-1, 0), h, rng, mats=mats)
    if cap:
        mb.box(T(0, 0, h + 0.07) @ S(L + 0.02, t + 0.1, 0.14), "fort_stone_lt")
    if crenel:
        x = -L / 2 + 0.55
        while x < L / 2 - 0.4:
            if not (gap and gap[0] - 0.5 < x < gap[1] + 0.5 and False) and rng.random() >= broken:
                hh = c_h * (rng.uniform(0.55, 0.85) if broken and rng.random() < 0.3 else 1.0)
                mb.box(T(x, 0, h + 0.14 + hh / 2) @ Rz(rng.uniform(-0.04, 0.04)) @ S(0.95, t * 0.94, hh),
                       rng.choice(mats))
                mb.box(T(x, 0, h + 0.14 + hh + 0.05) @ S(1.04, t * 1.0, 0.1), "fort_stone_lt")
            x += 1.75
    return mb.obj(name, coll)


def make_gate_doors(name, coll, x0, x1, zh, thick):
    """Two plank door leaves swung open into the courtyard (-Y side) and a dark passage behind them.
    Local coordinates, centred on the gateway like make_stone_wall's gap."""
    mb = kit.MB(bevel=0.015)
    wd = (x1 - x0) / 2
    yin = -thick / 2 + 0.1
    for sgn in (-1, 1):
        hx = (x0 - 0.05) if sgn < 0 else (x1 + 0.05)
        ang = 1.2
        cx, cy = hx - sgn * math.cos(ang) * wd / 2 * -1, yin - math.sin(ang) * wd / 2
        cx = hx + (math.cos(ang) if sgn < 0 else -math.cos(ang)) * wd / 2
        mb.box(T(cx, cy, (zh - 0.1) / 2) @ Rz(-ang if sgn < 0 else ang) @ S(wd, 0.12, zh - 0.1), "wood_door")
        for z in (0.5, zh - 0.7):
            mb.box(T(cx, cy - 0.07, z) @ Rz(-ang if sgn < 0 else ang) @ S(wd, 0.05, 0.14), "iron")
    mb.box(T((x0 + x1) / 2, thick / 2 - 0.35, zh / 2) @ S(x1 - x0 - 0.05, 0.1, zh - 0.05), "dark")
    return mb.obj(name, coll)


def make_stairs(name, coll, n=8, w=2.2, rise=0.275, run=0.5, wedge=True):
    """Stone stairs rising toward -X from x=0 (first step top at +rise); width along Y (centred)."""
    mb = kit.MB(bevel=0.02)
    for i in range(n):
        top = rise * (i + 1)
        mb.box(T(-i * run - run / 2, 0, (top - 0.4) / 2) @ S(run + 0.02, w, top + 0.4), "fort_stone_lt" if i % 2 else "fort_stone")
    if wedge:
        for sgn in (-1, 1):
            v = [mb.bm.verts.new(p) for p in
                 [(0, sgn * (w / 2 + 0.2), -0.4), (-n * run, sgn * (w / 2 + 0.2), -0.4),
                  (-n * run, sgn * (w / 2 + 0.2), n * rise + 0.5), (0, sgn * (w / 2 + 0.2), 0.55),
                  (0, sgn * (w / 2 - 0.1), -0.4), (-n * run, sgn * (w / 2 - 0.1), -0.4),
                  (-n * run, sgn * (w / 2 - 0.1), n * rise + 0.5), (0, sgn * (w / 2 - 0.1), 0.55)]]
            for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (3, 2, 6, 7), (1, 5, 6, 2), (0, 3, 7, 4)):
                mb.face([v[k] for k in f], "fort_stone_dk")
    return mb.obj(name, coll)


def make_flagstones(name, coll, x0, x1, y0, y1, seed=0, skip=None, step=(1.7, 1.25)):
    """A paving of irregular flat slabs (K68), one mesh."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.012)
    y = y0
    r = 0
    while y < y1:
        x = x0 + (0.6 if r % 2 else 0.0)
        while x < x1:
            cx, cy = x + rng.uniform(-0.1, 0.1), y + rng.uniform(-0.1, 0.1)
            if not (skip and skip(cx, cy)):
                sx, sy = step[0] * rng.uniform(0.78, 0.98), step[1] * rng.uniform(0.75, 0.96)
                mb.box(T(cx, cy, 0.025 + rng.uniform(-0.01, 0.02)) @ Rz(rng.uniform(-0.18, 0.18)) @ S(sx, sy, 0.07),
                       rng.choice(("flag_a", "flag_b", "flag_c", "flag_a")))
            x += step[0] * rng.uniform(0.95, 1.1)
        y += step[1] * rng.uniform(0.95, 1.05)
        r += 1
    return mb.obj(name, coll)


def make_canopy_open(name, coll, w=5.0, d=5.6, h=3.4):
    """Cloth canopy over the dais: four posts, canvas roof, red valance, gold braid."""
    mb = kit.MB(bevel=0.015)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * w / 2, sy * d / 2, 0), (sx * w / 2, sy * d / 2, h + 0.1), 0.09, 0.07, "post", sides=6)
            mb.ico(T(sx * w / 2, sy * d / 2, h + 0.18), "gold", r=0.1, sub=1)
    mb.box(T(0, 0, h + 0.05) @ S(w + 0.4, d + 0.4, 0.08), "canvas")
    for sy in (-1, 1):
        mb.box(T(0, sy * (d / 2 + 0.2), h - 0.18) @ S(w + 0.4, 0.05, 0.4), "red")
        mb.box(T(0, sy * (d / 2 + 0.2), h - 0.4) @ S(w + 0.4, 0.06, 0.05), "gold")
    for sx in (-1, 1):
        mb.box(T(sx * (w / 2 + 0.2), 0, h - 0.18) @ S(0.05, d + 0.4, 0.4), "red")
        mb.box(T(sx * (w / 2 + 0.2), 0, h - 0.4) @ S(0.06, d + 0.4, 0.05), "gold")
    return mb.obj(name, coll)


def make_pavilion(name, coll, w=4.4, d=3.6, h=2.8):
    """Raised plank platform with a tan hipped cloth roof on four posts (K70's pavilion)."""
    mb = kit.MB(bevel=0.02)
    mb.box(T(0, 0, 0.18) @ S(w + 0.6, d + 0.6, 0.36), "plank")
    mb.box(T(0, 0, 0.38) @ S(w + 0.2, d + 0.2, 0.04), "carpet_red")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * w / 2, sy * d / 2, 0.36), (sx * w / 2, sy * d / 2, h), 0.09, 0.08, "post", sides=6)
    mb.cone(T(0, 0, h + 0.55) @ Rz(math.pi / 4), "pavilion", segments=4, r1=w * 0.86, r2=0.2, depth=1.2)
    mb.cone(T(0, 0, h + 0.04) @ Rz(math.pi / 4), "red", segments=4, r1=w * 0.9, r2=w * 0.9, depth=0.14)
    mb.seg((0, 0, h + 1.1), (0, 0, h + 1.5), 0.05, 0.03, "post", sides=5)
    return mb.obj(name, coll)


def make_ball_pile(name, coll, base=4, r=0.14, seed=0):
    """A pyramid of iron cannonballs."""
    rng = random.Random(seed)
    mb = kit.MB()
    for layer in range(base):
        n = base - layer
        for i in range(n):
            for j in range(n):
                x = (i - (n - 1) / 2) * r * 2.05
                y = (j - (n - 1) / 2) * r * 2.05
                mb.ico(T(x, y, r + layer * r * 1.7), "iron", r=r * rng.uniform(0.96, 1.04), sub=1)
    return mb.obj(name, coll)


def make_furnace(name, coll):
    """Clay furnace for casting shot: a squat kiln with a chimney, a glowing mouth, bellows and a tub."""
    mb = kit.MB(bevel=0.03)
    mb.box(T(0, 0, 0.35) @ S(1.5, 1.3, 0.7), "clay")
    mb.cone(T(0, 0, 1.2) @ Rz(0.4), "clay", segments=6, r1=0.75, r2=0.4, depth=1.0)
    mb.cone(T(0, 0, 2.25), "clay_dk", segments=6, r1=0.38, r2=0.3, depth=1.3)
    mb.box(T(0, 0.64, 0.38) @ S(0.62, 0.1, 0.5), "dark")
    mb.box(T(0, 0.7, 0.14) @ S(0.8, 0.22, 0.12), "fort_stone_dk")
    mb.box(T(0.95, 0.1, 0.3) @ S(0.55, 0.9, 0.5), "plank")
    mb.seg((0.95, 0.5, 0.45), (0.5, 0.64, 0.4), 0.06, 0.04, "iron", sides=5)
    mb.cone(T(-1.15, 0.5, 0.25), "soil_dk", segments=8, r1=0.4, r2=0.34, depth=0.5)
    return mb.obj(name, coll)


def make_shed(name, coll, w=4.6, d=3.6, h=2.4):
    """Open timber shed with a thatch hip roof (the cannonball works)."""
    mb = kit.MB(bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * w / 2, sy * d / 2, 0), (sx * w / 2, sy * d / 2, h), 0.1, 0.09, "post", sides=6)
    for sy in (-1, 1):
        mb.box(T(0, sy * d / 2, h - 0.1) @ S(w + 0.1, 0.12, 0.14), "post")
    for sx in (-1, 1):
        mb.box(T(sx * w / 2, 0, h - 0.1) @ S(0.12, d + 0.1, 0.14), "post")
    mb.cone(T(0, 0, h + 0.6) @ Rz(math.pi / 4), "thatch", segments=4, r1=w * 0.88, r2=0.25, depth=1.3)
    mb.cone(T(0, 0, h + 0.05) @ Rz(math.pi / 4), "thatch_dk", segments=4, r1=w * 0.95, r2=w * 0.95, depth=0.14)
    mb.box(T(0, -d / 2 + 0.3, 0.3) @ S(w - 0.6, 0.7, 0.6), "plank")
    return mb.obj(name, coll)


def make_scaffold(name, coll, length=8.0, h=3.2, seed=0):
    """Bamboo-and-plank scaffold along X, two levels, with ladders."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.008)
    n = int(length / 2.0) + 1
    xs = [-length / 2 + i * length / (n - 1) for i in range(n)]
    for y in (-0.45, 0.45):
        for x in xs:
            mb.seg((x, y, -0.2), (x + rng.uniform(-0.05, 0.05), y, h + 0.3), 0.045, 0.04, "trunk", sides=5)
        for z in (1.15, 2.25):
            mb.seg((-length / 2, y, z), (length / 2, y, z), 0.04, 0.04, "trunk", sides=5)
    for z in (1.2, 2.3):
        for k in range(int(length / 0.45)):
            mb.box(T(-length / 2 + 0.25 + k * 0.45, 0, z + 0.04) @ S(0.4, 1.0, 0.05), "plank")
    for x in xs:
        mb.seg((x, -0.45, 0.0), (x, 0.45, 1.15), 0.04, 0.04, "trunk", sides=4)
    mb.seg((xs[1] - 0.6, -0.5, 0.0), (xs[1] - 0.6, -0.5, 2.3), 0.05, 0.05, "post", sides=4)
    return mb.obj(name, coll)


def make_block_stack(name, coll, seed=0, n=14):
    """Squared stone blocks piled in a heap (for the masons)."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.02)
    for k in range(n):
        layer = k // 5
        i = k % 5
        mb.box(T((i - 2) * 0.62 + layer * 0.2 + rng.uniform(-0.05, 0.05), rng.uniform(-0.2, 0.2) + layer * 0.1,
                 0.2 + layer * 0.4) @ Rz(rng.uniform(-0.2, 0.2)) @ S(0.58, 0.5, 0.38), rng.choice(STONES))
    return mb.obj(name, coll)


def make_gravel(name, coll, seed=0, n=46, r=1.3):
    rng = random.Random(seed)
    mb = kit.MB()
    for k in range(n):
        a, d = rng.uniform(0, TAU), r * math.sqrt(rng.random())
        mb.ico(T(math.cos(a) * d * 1.3, math.sin(a) * d, 0.02) @ S(1, 1, 0.6), rng.choice(("rock", "stone", "fort_stone_dk")),
               r=rng.uniform(0.03, 0.07), sub=1)
    return mb.obj(name, coll)


def make_banner(name, coll, w=0.9, h=1.9):
    """Hanging cloth banner on a wall (plain red, gold border, no emblem)."""
    mb = kit.MB(bevel=0.01)
    mb.box(T(0, 0, h / 2) @ S(w, 0.04, h), "red")
    mb.box(T(0, 0.01, h - 0.05) @ S(w + 0.12, 0.06, 0.08), "gold")
    for sx in (-1, 1):
        mb.box(T(sx * (w / 2 - 0.03), 0.012, h / 2) @ S(0.05, 0.04, h - 0.1), "gold")
    v = [mb.bm.verts.new(p) for p in [(-w / 2, 0.0, 0.0), (0, 0.0, -0.3), (w / 2, 0.0, 0.0)]]
    mb.face(v, "red")
    return mb.obj(name, coll)


# ----- figures
def _musket_drop(prim, M, m, kw):
    if m == "shield" or (m == "brass" and prim == "cone"):
        return True
    return m == "steel" and prim == "box"


FIRE_POSE = {"body": kit.Matrix.Identity(4), "legL": T(0.1, 0, 0.88), "legR": T(-0.1, 0, 0.88),
             "armR": T(-0.27, 0, 1.4) @ Rx(1.32) @ Rz(-0.3),
             "armL": T(0.27, 0, 1.4) @ Rx(1.18) @ Rz(0.42)}
MUSKET_MUZZLE = (-0.04, 1.42, 1.43)


def make_musketeer(name, coll, seed=0, cloth="cloth_w", pose=FIRE_POSE, shoulder=False):
    """Travancore soldier (kit 'nair': red turban, white dress) holding a musket at the ready. The kit's
    nair carries a sword and shield, so those parts are dropped and a musket added in the same mesh."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=kit.FIG_BEVEL)

    def get(p):
        return kit._PartFilter(mb, pose[p], _musket_drop), pose[p]
    kit._draw_figure(get, "nair", rng, cloth)
    if shoulder:                     # musket held upright at the side
        mb.box(T(-0.3, 0.12, 0.9) @ S(0.06, 0.08, 1.0), "post")
        mb.seg((-0.3, 0.12, 1.4), (-0.3, 0.12, 2.25), 0.022, 0.02, "steel", sides=4)
    else:
        mb.box(T(-0.07, 0.38, 1.38) @ Rx(0.02) @ S(0.07, 0.62, 0.08), "post")
        mb.seg((-0.05, 0.62, 1.42), MUSKET_MUZZLE, 0.022, 0.02, "steel", sides=4)
        mb.box(T(-0.07, 0.04, 1.36) @ S(0.06, 0.12, 0.14), "post")
    return mb.obj(name, coll)


def make_delannoy_hatless(name, coll, seed=0):
    """De Lannoy's rig (kit.make_delannoy) bare-headed: his dark hair, no tricorn (S55, S56)."""
    root, parts = kit.make_delannoy(name, coll, rig=True, seed=seed)
    ob = parts["head"]
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    names = [m.name for m in me.materials]
    kill = [f for f in bm.faces if names[f.material_index] in ("black", "gold") and f.calc_center_median().z > 0.235]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(me)
    bm.free()
    return root, parts


def make_tricorn(name, coll):
    mb = kit.MB(bevel=0.01)
    mb.cone(T(0, 0, 0.05) @ Rz(math.pi / 2), "black", segments=3, r1=0.33, r2=0.28, depth=0.1)
    mb.cone(T(0, 0, 0.007) @ Rz(math.pi / 2), "gold", segments=3, r1=0.345, r2=0.345, depth=0.024)
    mb.ico(T(0, 0, 0.09) @ S(1, 1, 0.55), "black", r=0.15, sub=1)
    return mb.obj(name, coll)


def make_sash(name, coll, parent):
    """Long gold sash over the left shoulder and down across the chest of a kit figure, built in the body's
    space, origin at the shoulder. Animate scale z 0 -> 1 to lay it on."""
    mb = kit.MB(bevel=0.008)
    p0, p1 = Vector((0.2, 0.17, 1.4)), Vector((-0.24, 0.205, 0.96))
    d = (p1 - p0)
    L = d.length
    # a flat band of length L along local -Z, width 0.13, depth 0.035, with a darker gold edge and fringe
    mb.box(T(0, 0, -L / 2) @ S(0.13, 0.035, L), "gold")
    mb.box(T(0.05, 0.004, -L / 2) @ S(0.025, 0.03, L), "carpet_gold")
    mb.box(T(-0.05, 0.004, -L / 2) @ S(0.025, 0.03, L), "carpet_gold")
    mb.box(T(0, 0, -L - 0.07) @ S(0.15, 0.04, 0.14), "carpet_gold")
    ob = mb.obj(name, coll, parent=parent)
    ob.location = p0
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    ob.scale = (1, 1, 0.0001)
    return ob, L
