"""English port (S17, shot-list clip 23): a small coastal trading post in land that
Travancore has just taken. Pepper that used to go to the Dutch now goes onto an
English ship.

Laid out to match the Flow reference frames/flow_refs/K23_v2 (camera south-west of the
port looking north-east along the coast): a palm-lined beach curving away to misty
hills; a small white square English fort with crenellated walls, round corner turrets
and a plain red flag; porters in white mundus carrying sacks of pepper on their heads
from the fort gate past heaps of pepper baskets and sacks, along a long wooden jetty and
up a gangplank onto a moored three-masted English ship (dark hull, cream sails partly
set, plain red flag); a thatched hut; the faceted sea. Far out, a Dutch ship with a
plain orange flag sails away empty. Details borrowed from K23_v1: more baskets in the
foreground, figures on the fort walls.

Coordinates: metres, Z up. The sea is east (+X) of the shore line shore_x(y); the
jetty runs east along y = 0. Sea level is SEA_Z; the top of the beach is about z = 0.3.
Reused: pepper baskets, sacks, mats, broad-leaf plants and the mist composite from
pepper_world; porters, the fort mesh helpers (bar, merlons, door, window, tile roof),
gulls and the swell from kochi_world. New here: terrain and sea for this coast, the
fort, flags in one plain colour, the ships' set sails, rigging and rails, the porters'
carry cycle.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

import colachel_kit as kit
import colachel_world as cw
import kochi_world as kw
import pepper_world as pw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau

# extra colours for this set (people, wood, greens and the sea come from kit.PALETTE / cw)
PALETTE = {
    "fort":         (0.93, 0.91, 0.86),   # whitewashed plaster (K23)
    "fort_lt":      (0.97, 0.96, 0.92),   # copings and merlon caps
    "fort_dk":      (0.80, 0.77, 0.71),   # door steps, string courses
    "fort_base":    (0.62, 0.59, 0.54),   # stone footing
    "roof":         (0.50, 0.44, 0.40),   # turret roofs (grey-brown, as in K23_v2)
    "tile":         (0.70, 0.30, 0.18),
    "tile_dk":      (0.58, 0.24, 0.14),
    "wood_door":    (0.42, 0.30, 0.20),
    "flag_r":       (0.80, 0.12, 0.09),   # English: plain red, no symbols
    "flag_o":       (0.95, 0.50, 0.10),   # Dutch: plain orange, no symbols
    "sail_set":     (0.93, 0.88, 0.74),   # cream sail cloth
    "dirt":         (0.60, 0.45, 0.32),
    "dirt_dk":      (0.53, 0.40, 0.29),
    "grass_lt":     (0.48, 0.61, 0.25),
    "jungle":       (0.32, 0.46, 0.21),
    "far_hill":     (0.42, 0.55, 0.31),
    "leaf_lt":      (0.38, 0.56, 0.21),
    "pepper":       (0.17, 0.12, 0.10),
    "pepper_br":    (0.30, 0.21, 0.15),
    "basket":       (0.80, 0.63, 0.38),
    "basket_dk":    (0.64, 0.48, 0.28),
    "tray":         (0.82, 0.68, 0.45),
    "mat_lt":       (0.84, 0.72, 0.48),
    "mat_dk":       (0.70, 0.57, 0.36),
    "clay":         (0.74, 0.38, 0.22),
    "clay_dk":      (0.58, 0.28, 0.16),
    "jute":         (0.74, 0.63, 0.47),   # light burlap, as in K23
    "rope":         (0.52, 0.42, 0.28),
    "rug_dk":       (0.42, 0.25, 0.22),
    "gull":         (0.95, 0.95, 0.93),
}


def register_palette():
    """Add this set's colours to the kit palette and create their materials
    (call after kit.reset_scene, before anything that builds with them)."""
    for name, rgb in PALETTE.items():
        kit.PALETTE[name] = rgb
        kit.mat(name, rgb)


# ------------------------------------------------------------------- layout
SEA_Z = -0.5
FORT = (-16.0, 9.0)            # centre of the fort
FH = 6.5                       # half size of the fort (outer faces of the curtain walls)
WALL_T, WALL_H = 1.3, 4.2      # curtain wall thickness and height above the ground
TURRET_R = 1.9
GATE_Y = FORT[1] - 1.5         # gate in the east wall (toward the beach)
JETTY_X0, JETTY_X1 = -2.0, 21.5   # jetty from the top of the beach out to the ship
JETTY_W = 2.6
JETTY_DECK = SEA_Z + 0.95      # top of the deck planks
SHIP_SCALE = 0.62              # kit East Indiaman scaled to a ~24 m trader
SHIP_POS = (22.0, 4.75)        # moored along the north side of the jetty end, bow toward the land
SHIP_ROT = math.pi / 2         # ship +Y (bow) points west (-X)
SHIP_Z = SEA_Z - 0.4
SHIP_DECK = SHIP_Z + 4.0 * SHIP_SCALE
GX = 19.2                      # gangplank from the jetty up to the ship's waist
HATCH = (SHIP_POS[0] - 6.27 * SHIP_SCALE, SHIP_POS[1] - 1.2 * SHIP_SCALE)   # the cargo hatch the porters go down
HEAPS = (-4.5, -4.5)           # centre of the pepper heaps
PICKUP = (-4.3, 0.9)           # where each porter takes a sack off the stack
HUTS = [(-25.5, -3.5, 0.15, "gable"), (-6.0, 21.5, -0.2, "hip"), (-11.5, 25.0, 0.3, "gable")]
DUTCH_START = (60.0, 128.0)    # the Dutch ship, sailing away north-east
DUTCH_DIR = (0.78, 0.63)
DUTCH_SPEED = 2.6              # m/s


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


_ss = pw._ss


def shore_x(y):
    """x of the waterline: a gently wavy beach running north, curving west (left in
    the K23 view) into a bay beyond the fort."""
    x = 3.0 + 0.7 * math.sin(y / 6.3 + 0.4) + 0.35 * math.sin(y / 2.7 + 1.3)
    k = y - 24.0
    if k > 0:
        x -= 0.5 * (k * k / 24.0 if k < 12.0 else k - 6.0)
    return x


def height(x, y):
    d = shore_x(y) - x                       # metres inland (negative offshore)
    if d < 0:
        return max(SEA_Z - 7.0, SEA_Z - 0.2 + d * 0.22)
    h = SEA_Z - 0.2 + 1.0 * _ss(-0.5, 6.0, d)                    # wet sand up to the top of the beach
    h += 0.01 * max(0.0, d - 6.0) + 0.1 * _n(x, y, 5.0, 1.1) * _ss(6.0, 12.0, d)
    # misty faceted hills behind the coast
    ridge = (1.0 - abs(_n(x, y, 110.0, 7.7))) ** 2
    h += _ss(55.0, 190.0, d) * (14.0 + 55.0 * ridge + 14.0 * _n(x, y, 45.0, 3.3))
    h += _ss(200.0, 650.0, d) * 70.0
    h += _ss(40.0, 150.0, d) * 1.6 * _n(x, y, 7.0, 5.4)
    return h


def ground_z(x, y):
    """Where a walker's feet are: the jetty deck, the ramp onto it, or the ground."""
    if abs(y) < JETTY_W / 2 + 0.1:
        if x >= JETTY_X0:
            return JETTY_DECK
        if x > JETTY_X0 - 1.6:
            t = (x - (JETTY_X0 - 1.6)) / 1.6
            return height(JETTY_X0 - 1.6, y) * (1 - t) + JETTY_DECK * t
    return height(x, y)


def in_fort(x, y, pad=0.0):
    return abs(x - FORT[0]) < FH + pad and abs(y - FORT[1]) < FH + pad


def is_yard(x, y):
    """Trodden earth: the open ground between the fort, the beach and the heaps, and
    the courtyard inside the fort."""
    if in_fort(x, y, -0.5):
        return True
    e = math.hypot((x + 9.0) / 14.0, (y - 1.0) / 12.5) + 0.12 * _n(x, y, 4.0, 0.7)
    if e < 1.0:
        return True
    return math.hypot((x - HUTS[0][0]) / 5.0, (y - HUTS[0][1]) / 4.0) + 0.15 * _n(x, y, 3.0, 2.0) < 1.0


# ------------------------------------------------------------------ terrain
def make_terrain(collection, seed=3):
    rng = random.Random(seed)
    xs = pw._axis([-760, -160, -60, 30, 70], [25, 5, 0.7, 2.5])
    ys = pw._axis([-220, -46, 42, 150, 950], [10, 0.7, 3, 25])
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
    mats = ["sand", "sand_wet", "dirt", "dirt_dk", "grass", "grass_lt", "jungle", "far_hill"]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    for f in bm.faces:
        x, y, z = f.calc_center_median()
        d = shore_x(y) - x
        if d < 1.3 + 0.4 * _n(x, y, 3.0, 4.4):
            m = "sand_wet"
        elif d < 6.8 + 1.4 * _n(x, y, 6.0, 2.2) and not (is_yard(x, y) and d > 5.0):
            m = "sand"
        elif is_yard(x, y):
            m = "dirt" if _n(x, y, 2.5, 6.1) > -0.25 else "dirt_dk"
        elif d > 70:
            m = "far_hill" if _n(x, y, 40.0, 9.1) > -0.15 else "jungle"
        elif f.normal.z < 0.8:
            m = "jungle"
        else:
            m = "grass_lt" if _n(x, y, 7.0, 3.7) > 0.1 else "grass"
        f.material_index = mats.index(m)
    me = bpy.data.meshes.new("Terrain")
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Terrain", me)
    collection.objects.link(ob)
    return ob


def make_sea(collection, seed=2):
    """Faceted sea like the beach clips: jittered triangles, shallow green-blue at the
    shore turning deep blue offshore, a pale foam line on the sand. Fine cells round
    the port, coarse ones out to the horizon."""
    rng = random.Random(seed)
    xs = pw._axis([-480, -40, 130, 1600], [20, 2.4, 20])
    ys = pw._axis([-500, -70, 175, 1600], [20, 2.4, 20])
    lin = [kit.srgb_to_linear(c) for c in (cw.SEA_SHALLOW, cw.SEA_DEEP, cw.SEA_FOAM)]
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new("Col")
    grid = []
    for j, (y, sy) in enumerate(ys):
        row = []
        for i, (x, sx) in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                jx, jy = rng.uniform(-0.3, 0.3) * sx, rng.uniform(-0.3, 0.3) * sy
            px, py = x + jx, y + jy
            v = bm.verts.new((px, py, SEA_Z + rng.uniform(-0.03, 0.03)))
            depth = px - shore_x(py)
            t = _ss(0.0, 45.0, depth)
            c = [lin[0][k] * (1 - t) + lin[1][k] * t for k in range(3)]
            if depth < 1.3:
                u = max(0.0, 1.0 - max(0.0, depth) / 1.3)
                c = [c[k] * (1 - u) + lin[2][k] * u for k in range(3)]
            s = rng.uniform(0.94, 1.06)
            v[col] = (c[0] * s, c[1] * s, c[2] * s, 1.0)
            row.append(v)
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("Sea")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(cw.sea_material())
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Sea", me)
    collection.objects.link(ob)
    return ob


# ============================================================== the fort
def make_flag(name, coll, w=2.4, h=1.5, m="flag_r"):
    """Flag in one plain colour (no emblem, no text), waving with a Wave modifier.
    Origin at the hoist top; the fly runs along +X."""
    mb = kit.MB()
    nx, nz = 12, 6
    vs = [[mb.bm.verts.new((w * i / nx, 0, -h * j / nz)) for i in range(nx + 1)] for j in range(nz + 1)]
    for j in range(nz):
        for i in range(nx):
            mb.face([vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]], m)
    ob = mb.obj(name, coll)
    sol = ob.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.02
    wv = ob.modifiers.new("Wave", "WAVE")
    wv.use_x, wv.use_y = True, False
    wv.use_normal = True
    wv.use_normal_y = True
    wv.use_normal_x = wv.use_normal_z = False
    wv.height = h * 0.09
    wv.width = w * 0.45
    wv.narrowness = 1.2
    wv.speed = 0.035
    wv.start_position_x = -w * 0.1
    wv.falloff_radius = 0.0
    ob.modifiers.move(1, 0)
    return ob


def flag_on_pole(coll, name, base, pole_h, w, h, m="flag_r", heading=200.0, r=0.08):
    """A pole with a brass knob and a waving plain flag at its top."""
    x, y, z = base
    p = kit.MB()
    p.seg((x, y, z), (x, y, z + pole_h), r, r * 0.75, "post", sides=6)
    p.ico(T(x, y, z + pole_h + 0.08), "brass", r=r * 1.3, sub=1)
    p.obj(name + "Pole", coll)
    fl = make_flag(name, coll, w=w, h=h, m=m)
    fl.location = (x + 0.05, y, z + pole_h - 0.12)
    fl.rotation_euler[2] = math.radians(heading)
    return fl


def _turret(mb, cx, cy, z0, r, h, rng, out):
    """Round corner turret: stone footing, white drum with arrow slits, a moulded band,
    and a grey conical roof with a finial."""
    seg = 14
    mb.cone(T(cx, cy, z0 - 0.3), "fort_base", segments=seg, r1=r + 0.25, r2=r + 0.12, depth=1.4)
    mb.cone(T(cx, cy, z0 + h / 2), "fort", segments=seg, r1=r, r2=r * 0.97, depth=h)
    top = z0 + h
    mb.cone(T(cx, cy, top - 0.75), "fort_dk", segments=seg, r1=r + 0.05, r2=r + 0.05, depth=0.12)
    mb.cone(T(cx, cy, top + 0.12), "fort_lt", segments=seg, r1=r + 0.06, r2=r + 0.22, depth=0.24)
    mb.cone(T(cx, cy, top + 0.34), "fort_lt", segments=seg, r1=r + 0.22, r2=r + 0.22, depth=0.2)
    mb.cone(T(cx, cy, top + 0.44 + 1.35), "roof", segments=seg // 2 * 2 - 2, r1=r + 0.45, r2=0.05, depth=2.7)
    mb.seg((cx, cy, top + 3.0), (cx, cy, top + 3.6), 0.05, 0.03, "post", sides=5)
    mb.ico(T(cx, cy, top + 3.62), "brass", r=0.1, sub=1)
    # arrow slits on the outward half
    base_a = math.atan2(out[1], out[0])
    for k in (-1, 0, 1):
        a = base_a + k * 0.75
        for zz in (z0 + h * 0.42, z0 + h * 0.78):
            if k != 0 and zz < z0 + h * 0.5:
                continue
            mb.box(T(cx + math.cos(a) * (r - 0.02), cy + math.sin(a) * (r - 0.02), zz) @ Rz(a)
                   @ S(0.08, 0.16, 0.62), "dark")


def build_fort(coll, rng):
    """The English fort: white crenellated curtain walls on a stone footing, round
    corner turrets, a gate in the east wall, a crenellated keep with the red flag, a
    tiled warehouse along the back wall, guns on the walls and a sentry."""
    cx, cy = FORT
    z0 = height(cx + FH, cy - FH) - 0.05
    mb = kit.MB(bevel=0.03)
    cs = [(cx - FH, cy - FH), (cx + FH, cy - FH), (cx + FH, cy + FH), (cx - FH, cy + FH)]
    for i in range(4):
        a, b = Vector((*cs[i], 0)), Vector((*cs[(i + 1) % 4], 0))
        d = (b - a).normalized()
        n_in = Vector((-d.y, d.x, 0))                     # walls run counter-clockwise: inward is left
        pa, pb = a + n_in * (WALL_T / 2), b + n_in * (WALL_T / 2)
        kw.bar(mb, pa.xy, pb.xy, WALL_T, z0 - 0.8, z0 + WALL_H, "fort")
        kw.bar(mb, a.xy, b.xy, 0.5, z0 - 0.8, z0 + 0.55, "fort_base")           # footing
        kw.bar(mb, (a - n_in * 0.03).xy, (b - n_in * 0.03).xy, 0.12, z0 + WALL_H - 0.55, z0 + WALL_H - 0.4,
               "fort_dk")                                                        # string course
        kw.bar(mb, pa.xy, pb.xy, WALL_T + 0.1, z0 + WALL_H - 0.08, z0 + WALL_H + 0.04, "fort_lt")
        # breast wall and merlons along the outer edge, a low lip on the inner edge
        q0, q1 = a + n_in * 0.24, b + n_in * 0.24
        kw.merlons(mb, q0.xy, q1.xy, z0 + WALL_H, "fort", w=0.48, size=0.72, gap=0.55, h=0.62)
        r0, r1 = a + n_in * (WALL_T - 0.1), b + n_in * (WALL_T - 0.1)
        kw.bar(mb, r0.xy, r1.xy, 0.2, z0 + WALL_H, z0 + WALL_H + 0.35, "fort_lt")
        # loopholes along the face
        L = (b - a).length
        for k in range(1, 5):
            p = a + d * (L * k / 5) - n_in * 0.02
            if i == 1 and abs(p.y - GATE_Y) < 2.0:
                continue
            mb.box(T(p.x, p.y, z0 + WALL_H - 1.25) @ Rz(math.atan2(d.y, d.x)) @ S(0.16, 0.08, 0.5), "dark")
    for (x, y) in cs:
        _turret(mb, x, y, z0, TURRET_R, WALL_H + 1.5, rng, (x - cx, y - cy))
    # the gate (east wall, facing the beach): dark doorway, wooden frame, a pediment
    gx = cx + FH
    kw.door(mb, (gx, GATE_Y, z0 + 0.05), (0, 1, 0), (1, 0, 0), w=2.0, h=2.7)
    mb.box(T(gx + 0.08, GATE_Y, z0 + 3.25) @ S(0.2, 3.0, 0.22), "fort_lt")
    mb.box(T(gx + 0.06, GATE_Y, z0 + 3.55) @ S(0.16, 2.2, 0.4), "fort")
    for s in (-1, 1):                                                           # pilasters
        mb.box(T(gx + 0.06, GATE_Y + s * 1.55, z0 + 1.6) @ S(0.16, 0.36, 3.2), "fort_lt")
    # inner face lip so the walk reads from above
    # keep: a crenellated square tower in the courtyard, taller than the walls
    kx, ky, kh = cx + 1.5, cy - 1.5, 7.6
    mb.box(T(kx, ky, z0 + kh / 2 - 0.3) @ S(4.2, 4.2, kh + 0.6), "fort")
    mb.box(T(kx, ky, z0 + 0.25) @ S(4.5, 4.5, 0.6), "fort_base")
    mb.box(T(kx, ky, z0 + kh - 0.6) @ S(4.34, 4.34, 0.14), "fort_dk")
    mb.box(T(kx, ky, z0 + kh + 0.02) @ S(4.4, 4.4, 0.12), "fort_lt")
    kc = [(kx - 2.1, ky - 2.1), (kx + 2.1, ky - 2.1), (kx + 2.1, ky + 2.1), (kx - 2.1, ky + 2.1)]
    for i in range(4):
        a, b = Vector((*kc[i], 0)), Vector((*kc[(i + 1) % 4], 0))
        d = (b - a).normalized()
        n_in = Vector((-d.y, d.x, 0))
        kw.merlons(mb, (a + n_in * 0.2).xy, (b + n_in * 0.2).xy, z0 + kh, "fort", w=0.4, size=0.6, gap=0.45, h=0.5)
    for (nx_, ny_) in ((0, -1), (1, 0)):                                         # windows on the keep
        for zz in (z0 + 3.0, z0 + 5.4):
            kw.window(mb, (kx + nx_ * 2.1, ky + ny_ * 2.1, zz), (0, 0, 0), (nx_, ny_, 0), w=0.5, h=0.7,
                      shutters=zz < z0 + 4)
    kw.door(mb, (kx + 0.5, ky - 2.1, z0 + 0.05), (1, 0, 0), (0, -1, 0), w=1.0, h=2.0)
    # warehouse along the north wall, its tiled roof showing above the walls
    wx, wy, ww, wd, wh = cx - 0.5, cy + FH - WALL_T - 2.0, 9.0, 3.6, 4.4
    mb.box(T(wx, wy, z0 + wh / 2) @ S(ww, wd, wh), "fort")
    kw.tile_roof(mb, wx, wy, ww, wd, z0 + wh, 1.7, rows=True)
    # inner stair up to the wall walk (south-east corner)
    for k in range(8):
        mb.box(T(cx + FH - WALL_T - 0.45, cy - FH + WALL_T + 0.5 + k * 0.38, z0 + (k + 1) * WALL_H / 8 / 2)
               @ S(0.9, 0.4, (k + 1) * WALL_H / 8), "fort_dk")
    fort = mb.obj("Fort", coll)
    # the courtyard floor is the terrain (dirt); guns on the east wall and the front wall
    cannon = kit.make_cannon("LibCannon", coll)
    kit.hide_source(cannon)
    for i, (x, y, rz) in enumerate(((cx + FH - 0.75, cy + 2.5, -math.pi / 2), (cx + FH - 0.75, cy - 4.0, -math.pi / 2),
                                    (cx - 2.0, cy - FH + 0.75, math.pi))):
        kit.instance(cannon, f"WallGun{i}", coll, (x, y, z0 + WALL_H), rot_z=rz, scale=0.62)
    # the red flag on the keep
    flag_on_pole(coll, "FortFlag", (kx - 1.2, ky - 1.2, z0 + kh + 0.05), 5.4, 2.6, 1.55, "flag_r", heading=195)
    return dict(fort=fort, z0=z0, keep=(kx, ky, z0 + kh))


# ============================================================== the ships
MASTS = ((0.3, 24.0), (0.55, 29.0), (0.78, 22.0))        # kit ship: mizzen, main, fore (t along the hull, height)
YARDS = ((0.32, 0.95), (0.58, 0.75), (0.82, 0.55))       # yard height (fraction of the mast) and half span (x beam)


def _hull_w(t, beam):
    """Half width of the kit hull at deck level, t along the hull from the stern."""
    return beam / 2 * max(0.05, math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.5) * 0.86


def _sheer(t):
    return 4.0 + 2.2 * max(0.0, (0.25 - t) / 0.25) + 1.2 * max(0.0, (t - 0.8) / 0.2)


def _sail_sheet(mb, corners, belly_dir, belly, m, nx=6, nz=4):
    """A sail as a bellied grid between four corners (top-left, top-right, bottom-right,
    bottom-left), pushed out along belly_dir most in the middle."""
    tl, tr, br, bl = (Vector(c) for c in corners)
    rows = []
    for j in range(nz + 1):
        v = j / nz
        a, b = tl.lerp(bl, v), tr.lerp(br, v)
        row = []
        for i in range(nx + 1):
            u = i / nx
            p = a.lerp(b, u) + Vector(belly_dir) * (belly * math.sin(math.pi * u) * math.sin(math.pi * min(1.0, 0.15 + v * 0.85)))
            row.append(mb.bm.verts.new(p))
        rows.append(row)
    for j in range(nz):
        for i in range(nx):
            mb.face([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]], m)


def make_rig(name, coll, ship, plan, flag_m, length=38.0, beam=10.0, belly=1.0, seed=0, gangway=None):
    """Set sails, jibs, spanker, shrouds, deck rails, a hatch, deck cargo and plain
    flags for a kit ship, built in the ship's local space and parented to it.
    plan: {mast index: yards whose sail is set (0 course, 1 topsail, 2 topgallant)};
    gangway: ship-local y of a gap in the port-side rail for the gangplank."""
    rng = random.Random(seed)
    z0 = 4.0
    sails = kit.MB()
    gear = kit.MB(bevel=0.0)
    fwd = (0, 1, 0)
    for mi, (t, mh) in enumerate(MASTS):
        y = (t - 0.5) * length
        for k in plan.get(mi, ()):
            f, span = YARDS[k]
            ztop = z0 + mh * f - 0.15
            if k == 0:
                zbot, half_b = ztop - mh * 0.23, beam * span * 0.98
            else:
                zbot, half_b = z0 + mh * YARDS[k - 1][0] + 0.55, beam * YARDS[k - 1][1] * 0.95
            half_t = beam * span * 0.9
            _sail_sheet(sails, [(-half_t, y + 0.35, ztop), (half_t, y + 0.35, ztop), (half_b, y + 0.35, zbot),
                                (-half_b, y + 0.35, zbot)], fwd, belly * (1.5 if k == 0 else 1.1), "sail_set", nx=7, nz=4)
            if k == 0:                                     # sheets from the clews down to the rail
                for sx in (-1, 1):
                    gear.seg((sx * half_b, y + 0.4, zbot), (sx * _hull_w(t, beam), y - 3.0, _sheer(t) + 0.9),
                             0.05, 0.05, "black", sides=4)
        # shrouds: four a side from the mast top down to the rail, ratlines across them
        wt = _hull_w(t, beam)
        top = Vector((0, y, z0 + mh * 0.62))
        for sx in (-1, 1):
            feet = [Vector((sx * (wt + 0.25), y + dy, _sheer(t) + 0.4)) for dy in (-2.6, -1.6, -0.6, 0.4)]
            for p in feet:
                gear.seg(top + Vector((sx * 0.4, 0, 0)), p, 0.06, 0.06, "black", sides=4)
            for r in range(1, 9):                            # ratlines
                u = r / 10
                a = (top + Vector((sx * 0.4, 0, 0))).lerp(feet[0], u)
                b = (top + Vector((sx * 0.4, 0, 0))).lerp(feet[-1], u)
                gear.seg(a, b, 0.035, 0.035, "black", sides=3)
            gear.box(T(sx * (wt + 0.25), y - 1.1, _sheer(t) + 0.45) @ S(0.25, 3.6, 0.25), "hull_dark")   # chain wale
        # pennant at the masthead
        tp = z0 + mh + 2.4
        L = 7.0 if mi == 1 else 5.0
        sails.face([sails.bm.verts.new((0, y, tp)), sails.bm.verts.new((0, y, tp - 0.9)),
                    sails.bm.verts.new((0.3, y - L, tp - 0.55))], flag_m)
    # spanker on the mizzen (fore-and-aft, aft of the mast) with gaff and boom
    t, mh = MASTS[0]
    ym = (t - 0.5) * length
    luff0, luff1 = z0 + 3.0, z0 + mh * 0.5
    peak = Vector((0.0, ym - 9.0, z0 + mh * 0.62))
    clew = Vector((0.0, ym - 10.0, z0 + 3.0))
    _sail_sheet(sails, [(0, ym - 0.4, luff1), peak, clew, (0, ym - 0.4, luff0)], (1, 0, 0), 0.6 * belly + 0.3,
                "sail_set", nx=5, nz=4)
    gear.seg((0, ym, luff1), peak + Vector((0, -0.4, 0.1)), 0.18, 0.12, "post", sides=6)       # gaff
    gear.seg((0, ym, luff0 - 0.1), clew + Vector((0, -0.6, -0.1)), 0.2, 0.14, "post", sides=6)  # boom
    # jibs from the foremast down to the bowsprit
    t, mh = MASTS[2]
    yf = (t - 0.5) * length
    for (hz, ty_, tz, cy_, cz) in ((0.78, 24.6, 9.1, 16.0, 6.9), (0.62, 21.0, 7.8, 15.2, 6.4)):
        head = Vector((0, yf + 0.4, z0 + mh * hz))
        tack, clw = Vector((0, ty_, tz)), Vector((0, cy_, cz))
        mid = (head + tack + clw) / 3 + Vector((0.7 * belly, 0, 0))
        vs = [sails.bm.verts.new(p) for p in (head, tack, clw, mid)]
        sails.face([vs[0], vs[1], vs[3]], "sail_set")
        sails.face([vs[1], vs[2], vs[3]], "sail_set")
        sails.face([vs[2], vs[0], vs[3]], "sail_set")
        gear.seg(head, tack, 0.05, 0.05, "black", sides=4)
    # deck rails: posts and a top rail along both sides
    n = 14
    for sx in (-1, 1):
        prev = None
        for i in range(1, n):
            tt = i / n
            yy = (tt - 0.5) * length
            p = Vector((sx * _hull_w(tt, beam), yy, _sheer(tt)))
            gear.seg(p, p + Vector((0, 0, 1.0)), 0.09, 0.09, "hull_band", sides=4)
            if prev is not None and not (sx < 0 and gangway and prev.y < gangway < p.y):
                gear.seg(prev + Vector((0, 0, 1.0)), p + Vector((0, 0, 1.0)), 0.12, 0.12, "hull_band", sides=4)
            prev = p
    # cargo hatch amidships (between main and fore masts) and a smaller one aft
    hy = 0.5 * (MASTS[1][0] + MASTS[2][0] - 1.0) * length
    gear.box(T(-1.2, hy, z0 + 0.15) @ S(3.4, 3.0, 0.3), "hull_band")
    gear.box(T(-1.2, hy, z0 + 0.31) @ S(2.8, 2.4, 0.04), "dark")
    gear.box(T(0, -4.0, z0 + 0.15) @ S(2.2, 1.8, 0.3), "hull_band")
    gear.box(T(0, -4.0, z0 + 0.31) @ S(1.6, 1.2, 0.04), "dark")
    # ship's wheel and the capstan
    gear.cone(T(0, -12.2, _sheer(0.18) + 1.2) @ Rx(math.pi / 2), "post", segments=10, r1=0.75, r2=0.75, depth=0.12)
    gear.cone(T(0, 6.0, z0 + 0.6), "post", segments=8, r1=0.5, r2=0.4, depth=1.2)
    sl = sails.obj(name + "Sails", coll, parent=ship)
    sol = sl.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.12
    gr = gear.obj(name + "Gear", coll, parent=ship)
    # flag at the main top (plain colour), and an ensign on a stern staff
    t, mh = MASTS[1]
    fl = make_flag(name + "Flag", coll, w=4.6, h=2.9, m=flag_m)
    fl.parent = ship
    fl.location = (0.0, (t - 0.5) * length, z0 + mh + 2.3)
    fl.rotation_euler[2] = -math.pi / 2
    st = kit.MB()
    st.seg((0, -length / 2 - 0.2, _sheer(0.0) + 1.0), (0, -length / 2 - 0.9, _sheer(0.0) + 6.5), 0.12, 0.1, "post", sides=6)
    st.obj(name + "Staff", coll, parent=ship)
    en = make_flag(name + "Ensign", coll, w=3.6, h=2.3, m=flag_m)
    en.parent = ship
    en.location = (0.0, -length / 2 - 0.9, _sheer(0.0) + 6.3)
    en.rotation_euler[2] = -math.pi / 2
    return dict(sails=sl, gear=gr, hatch_y=hy)


def rock(ob, frames, base_rot, base_z, amp=(0.6, 1.1), bob=0.08, seed=0, path=None):
    """Gentle roll, pitch and heave (keys every 24 frames, smooth Bezier between);
    path(f) -> (x, y) moves the ship too (then keys every 4 frames, so it runs evenly)."""
    ph = random.Random(seed).uniform(0, 10)
    step = 4 if path else 24
    for f in range(1, frames + step + 1, step):
        ob.rotation_euler = (base_rot[0] + math.radians(amp[0] * math.sin(f / 21.0 + ph)),
                             base_rot[1] + math.radians(amp[1] * math.sin(f / 15.0 + 1 + ph)), base_rot[2])
        z = base_z + bob * math.sin(f / 19.0 + ph)
        if path:
            x, y = path(f)
            ob.location = (x, y, z)
        else:
            ob.location.z = z
        ob.keyframe_insert("rotation_euler", frame=f)
        ob.keyframe_insert("location", frame=f)


def build_ships(coll, lib, frames):
    """The English ship moored at the jetty (sails partly set, loading pepper) and the
    Dutch ship far out, sails full, sailing away empty."""
    sc_ = SHIP_SCALE
    ship = kit.make_ship("EnglishShip", coll, length=38.0, beam=10.0, seed=1)
    ship.location = (*SHIP_POS, SHIP_Z)
    ship.rotation_euler[2] = SHIP_ROT
    ship.scale = (sc_, sc_, sc_)
    rig = make_rig("English", coll, ship, {1: (1, 2), 2: (1, 2), 0: (1,)}, "flag_r", belly=0.7, seed=1,
                   gangway=(SHIP_POS[0] - GX) / sc_)
    rock(ship, frames, (0, 0, SHIP_ROT), SHIP_Z, amp=(0.5, 0.9), bob=0.07, seed=1)
    # cargo on deck, sailors (children of the ship, real size)
    inv = 1.0 / sc_
    put = lambda src, nm, lx, ly, lz, rz=0.0: _child(src, nm, coll, ship, (lx, ly, lz), rz, inv)
    hy = rig["hatch_y"]
    for i, (lx, ly) in enumerate(((1.6, hy - 1.4), (2.4, hy - 0.6), (1.7, hy + 0.3), (2.6, hy + 1.2))):
        put(lib["sack_lying"], f"DeckSack{i}", lx, ly, 4.0, rz=rng_angle(i))
    for i, (lx, ly) in enumerate(((2.4, hy + 3.8), (2.4, hy + 5.0), (-2.6, -1.5))):
        put(lib["crate"], f"DeckCrate{i}", lx, ly, 4.0, rz=0.1 * i)
    for i, (lx, ly) in enumerate(((-2.8, -6.2), (-2.8, -7.4))):
        put(lib["barrel"], f"DeckBarrel{i}", lx, ly, 4.0)
    for i, (lx, ly, rz, kind) in enumerate(((-0.6, hy + 2.2, 2.6, "villager"), (0.8, -9.0, 0.4, "villager"),
                                            (-1.8, hy - 2.8, -1.2, "villager"))):
        fig = kit.make_figure(f"Sailor{i}", coll, kind, seed=70 + i, cloth=("cloth_t", "cloth_w", "cloth_r")[i])
        fig.parent = ship
        fig.location = (lx, ly, 4.0)
        fig.rotation_euler[2] = rz
        fig.scale = (inv, inv, inv)
        kit.animate_idle(fig, random.Random(70 + i), 1, frames, amount=0.03)
    # mooring lines from bow and stern to jetty posts
    rope = kit.MB()
    for lyl, jx in ((10.5, 12.5), (-9.6, JETTY_X1 - 0.3)):
        a = Vector((jx, 1.15, JETTY_DECK + 0.45))
        lp = Vector((-4.2, lyl, 5.0)) * sc_
        b = Vector(SHIP_POS + (SHIP_Z,)) + Vector((-lp.y, lp.x, lp.z))
        rope.seg(a, b, 0.03, 0.03, "rope", sides=4)
    rope.obj("MooringLines", coll)

    # the Dutch ship: full sails, high in the water (empty), running away north-east
    dutch = kit.make_ship("DutchShip", coll, length=38.0, beam=10.0, seed=7)
    s2 = 0.6
    dutch.scale = (s2, s2, s2)
    heading = math.atan2(-DUTCH_DIR[0], DUTCH_DIR[1])
    make_rig("Dutch", coll, dutch, {0: (1, 2), 1: (0, 1, 2), 2: (0, 1, 2)}, "flag_o", belly=1.6, seed=7)
    dz = SEA_Z - 0.4 + 0.45                                    # light ship: rides high

    def course(f):
        d = DUTCH_SPEED * (f - 1) / kit.FPS
        return DUTCH_START[0] + DUTCH_DIR[0] * d, DUTCH_START[1] + DUTCH_DIR[1] * d
    rock(dutch, frames, (0, 0, heading), dz, amp=(1.2, 1.8), bob=0.15, seed=7, path=course)
    return dict(ship=ship, dutch=dutch, hatch_y=hy)


def rng_angle(i):
    return (i * 0.37) % 0.6 - 0.3


def _child(src, name, coll, parent, loc, rz, scale):
    ob = kit.instance(src, name, coll, loc, rot_z=rz, scale=scale)
    ob.parent = parent
    return ob


def ship_world(lx, ly, lz=0.0):
    """World position of a point on the English ship (ship-local, unscaled metres)."""
    p = Vector((lx, ly, lz)) * SHIP_SCALE
    return Vector((SHIP_POS[0] - p.y, SHIP_POS[1] + p.x, SHIP_Z + p.z))


# ============================================================== the landing
def build_jetty(coll, lib, frames):
    """Jetty with a ramp from the beach, a gangplank up to the ship, rowboats."""
    jlen = JETTY_X1 - JETTY_X0
    jetty = kit.make_jetty("Jetty", coll, length=jlen, width=JETTY_W, deck=JETTY_DECK - 0.04 - SEA_Z, seed=4)
    jetty.location = (JETTY_X0, 0.0, SEA_Z)
    jetty.rotation_euler[2] = -math.pi / 2                 # +Y of the kit jetty -> east
    # cross bracing under the deck (K23_v2) and a ramp onto it from the sand
    mb = kit.MB(bevel=0.01)
    x = JETTY_X0 + 0.4 + 1.8
    while x < JETTY_X1 - 0.5:
        for sy in (-1, 1):
            mb.seg((x - 1.8, sy * JETTY_W / 2, SEA_Z - 0.3), (x, sy * JETTY_W / 2, JETTY_DECK - 0.25), 0.07, 0.07,
                   "post", sides=4)
        mb.box(T(x, 0, JETTY_DECK - 0.3) @ S(0.14, JETTY_W + 0.2, 0.14), "post")
        x += 3.6
    x0 = JETTY_X0 - 1.6
    z0 = height(x0, 0.0)
    for k in range(6):
        u = (k + 0.5) / 6
        mb.box(T(x0 + 1.6 * u, 0, z0 + (JETTY_DECK - z0) * u - 0.04) @ Ry(-math.atan2(JETTY_DECK - z0, 1.6))
               @ S(0.27, JETTY_W - 0.2, 0.07), "plank")
    # gangplank from the jetty up to the ship's waist, with cleats
    p0, p1 = Vector((GX, 0.15, JETTY_DECK + 0.02)), Vector((GX, 2.35, SHIP_DECK + 0.05))
    d = p1 - p0
    mb.box(T((p0 + p1) / 2) @ Rz(math.atan2(d.y, d.x)) @ Ry(-math.atan2(d.z, d.xy.length)) @ S(d.length + 0.3, 0.85, 0.07),
           "plank")
    for k in range(6):
        q = p0.lerp(p1, (k + 0.5) / 6)
        mb.box(T(q + Vector((0, 0, 0.05))) @ S(0.8, 0.05, 0.05), "post")
    for sx in (-1, 1):                                                       # hand ropes
        mb.seg(p0 + Vector((sx * 0.45, 0, 0.9)), p1 + Vector((sx * 0.45, 0, 0.9)), 0.025, 0.025, "rope", sides=4)
        for q in (p0, p1):
            mb.seg(q + Vector((sx * 0.45, 0, 0)), q + Vector((sx * 0.45, 0, 0.95)), 0.04, 0.04, "post", sides=4)
    mb.obj("JettyBits", coll)
    # rowboats: one tied to the jetty with baskets in it, two drawn up on the beach
    boat = kit.make_boat("LibBoat", lib["lib_c"])
    for i, (x, y, rz, z) in enumerate(((8.5, -2.6, math.pi / 2, SEA_Z - 0.28), (1.4, -9.0, 1.9, None),
                                       (0.9, 12.5, 1.4, None), (30.0, -16.0, 0.9, SEA_Z - 0.28))):
        zz = height(x, y) - 0.05 if z is None else z
        b = kit.instance(boat, f"Boat{i}", coll, (x, y, zz), rot_z=rz)
        if z is not None:
            rock(b, frames, (0, 0, rz), zz, amp=(1.5, 1.0), bob=0.05, seed=30 + i)
    for i, dx in enumerate((-1.0, 0.0, 1.0)):
        kit.instance(lib["baskets"][i % 2], f"BoatBasket{i}", coll, (8.5 + dx, -2.6, SEA_Z + 0.05), rot_z=i)
    # sacks waiting on the jetty end, a capstan post
    k = 0
    for layer, n in enumerate((3, 2)):
        for j in range(n):
            kit.instance(lib["sack_lying"], f"JettySack{k}", coll,
                         (JETTY_X1 - 1.4 + (j - (n - 1) / 2) * 0.62, -0.75, JETTY_DECK + layer * 0.34),
                         rot_z=math.pi / 2 + 0.1 * j)
            k += 1
    return jetty


# ============================================================== the heaps
def _put(src, name, coll, x, y, rz=0.0, s=1.0, z=0.0, sink=0.03):
    return kit.instance(src, name, coll, (x, y, height(x, y) - sink + z), rot_z=rz, scale=s)


def _sack_stack(coll, lib, name, cx, cy, rot, layers, rng, rope=False):
    """Stack of lying sacks in courses, each course on the gaps of the one below."""
    c, s_ = math.cos(rot), math.sin(rot)
    ground = height(cx, cy) - 0.03
    k = 0
    for layer, (nu, nv) in enumerate(layers):
        for i in range(nu):
            for j in range(nv):
                u = (i - (nu - 1) / 2) * 0.62
                v = (j - (nv - 1) / 2) * 0.95
                kit.instance(lib["sack_lying"], f"{name}{k}", coll,
                             (cx + u * c - v * s_, cy + u * s_ + v * c, ground + layer * 0.34),
                             rot_z=rot + math.pi / 2 + rng.uniform(-0.12, 0.12))
                k += 1
    if rope:                                                           # lashing over the stack
        mb = kit.MB()
        nu, nv = layers[0]
        top = ground + len(layers) * 0.34 + 0.05
        hu, hv = nu * 0.31 + 0.05, nv * 0.48 + 0.05
        for a in (-0.3, 0.3):
            pts = [(-hu, a * hv * 2, ground + 0.1), (-hu * 0.6, a * hv * 2, top), (hu * 0.6, a * hv * 2, top),
                   (hu, a * hv * 2, ground + 0.1)]
            w = [Vector((cx + u * c - v * s_, cy + u * s_ + v * c, z)) for u, v, z in pts]
            for p, q in zip(w, w[1:]):
                mb.seg(p, q, 0.025, 0.025, "rope", sides=4)
        mb.obj(name + "Rope", coll)


def build_heaps(coll, lib, rng):
    """Pepper on the open ground between the fort and the jetty: baskets heaped with
    black pepper (some stacked), lashed stacks of sacks, crates, mats of pepper drying,
    spilled corns and pebbles; the stack the porters take their sacks from."""
    hx, hy = HEAPS
    B = lib["baskets"]
    big = lib["big_basket"]
    # foreground baskets (K23_v1: a cluster, some stacked two high)
    spots = [(-6.6, -6.4, big, 1.0, 0), (-5.6, -7.3, B[0], 1.1, 0), (-7.6, -7.4, B[2], 1.1, 0),
             (-6.9, -5.2, B[1], 1.0, 1), (-5.2, -5.6, B[3], 1.15, 0), (-8.1, -6.2, B[0], 1.0, 0),
             (-4.6, -7.9, B[2], 1.0, 0), (-6.2, -8.4, B[1], 0.95, 0), (-3.5, -6.6, big, 0.9, 0),
             (-8.6, -4.6, B[3], 1.0, 1), (-2.5, -4.4, B[0], 1.05, 0), (-3.3, -3.4, B[2], 1.0, 0),
             (-7.4, -3.4, B[1], 1.0, 0), (-1.6, -6.6, B[3], 1.0, 0), (-9.3, -7.7, B[2], 1.0, 0),
             (-0.6, -3.8, B[1], 1.0, 1), (-5.0, -2.6, B[0], 0.95, 0)]
    for i, (x, y, src, s, stack) in enumerate(spots):
        _put(src, f"HeapBasket{i}", coll, x, y, rng.uniform(0, TAU), s)
        if stack:                                                     # a second basket on top
            _put(src, f"HeapBasketTop{i}", coll, x + 0.05, y - 0.03, rng.uniform(0, TAU), s * 0.95, z=0.33)
    # lashed stacks of sacks with crates beside them (K23_v2 centre)
    _sack_stack(coll, lib, "SackStackA", -2.6, -1.6, 0.25, [(4, 2), (3, 2), (2, 1)], rng, rope=True)
    _sack_stack(coll, lib, "SackStackB", -5.6, 1.0, -0.4, [(3, 2), (2, 2), (1, 1)], rng)   # the porters' stack
    _sack_stack(coll, lib, "SackStackC", -9.8, -1.8, 0.6, [(3, 2), (2, 1)], rng)
    crate = lib["crate"]
    for i, (x, y, z) in enumerate(((-1.0, -2.3, 0), (-0.95, -3.1, 0), (-1.0, -2.7, 0.68), (-0.2, -1.4, 0),
                                   (-10.4, 0.6, 0), (-11.2, 0.4, 0), (-10.8, 0.5, 0.68))):
        _put(crate, f"HeapCrate{i}", coll, x, y, rng.uniform(-0.3, 0.3), 1.0, z=z)
    for i, (x, y) in enumerate(((-0.4, -0.2), (-11.7, -0.6), (-12.3, -0.2))):
        _put(lib["barrel"], f"HeapBarrel{i}", coll, x, y, 0, 1.0)
    # upright sacks scattered round the baskets
    for i, (x, y) in enumerate(((-4.3, -5.0), (-4.0, -5.6), (-7.9, -5.3), (-2.0, -5.6), (-3.0, -8.2), (-5.6, -4.6),
                                (-1.6, -2.9), (-8.4, -3.2), (-6.0, -2.1), (-9.6, -5.6), (-0.3, -5.1))):
        _put(lib["sack"], f"HeapSack{i}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.9, 1.1))
    # mats of pepper drying, trays, pots
    for i, (x, y, rz, k) in enumerate(((-10.2, -3.8, 0.4, 1), (-12.0, -6.4, -0.2, 2), (-13.6, -2.8, 0.9, 1))):
        _put(lib["mats"][k], f"HeapMat{i}", coll, x, y, rz, 1.0, sink=-0.01)
    for i, (x, y) in enumerate(((-11.2, -8.6), (-13.0, -8.0))):
        _put(lib["trays"][i], f"HeapTray{i}", coll, x, y, rng.uniform(0, TAU), 1.0, sink=0.0)
    for i, (x, y) in enumerate(((-9.0, -8.9), (-8.4, -9.4))):
        _put(lib["pots"][i], f"HeapPot{i}", coll, x, y, 0, 1.0, sink=0.0)
    # spilled pepper and pebbles on the dirt
    sp = kit.MB()
    for k in range(18):
        x, y = hx + rng.gauss(0, 2.6), hy + rng.gauss(0, 2.0)
        z = height(x, y)
        sp.cone(T(x, y, z + 0.02), "pepper", segments=7, r1=rng.uniform(0.15, 0.35), r2=0.02, depth=rng.uniform(0.05, 0.1))
        for j in range(8):
            q = (x + rng.gauss(0, 0.35), y + rng.gauss(0, 0.35))
            sp.ico(T(q[0], q[1], height(*q) + 0.02), "pepper", r=0.03, sub=1)
    for k in range(70):
        x, y = rng.uniform(-14, 1), rng.uniform(-11, 4)
        if not is_yard(x, y):
            continue
        sp.ico(T(x, y, height(x, y)) @ S(1, 0.8, 0.55) @ Rz(rng.uniform(0, 3)), "rock", r=rng.uniform(0.06, 0.16), sub=1,
               jitter=0.2, rng=rng)
    sp.obj("SpillAndPebbles", coll)


# ============================================================== the village
def build_village(coll, lib, rng):
    """Thatched huts, a fence, barrels and baskets by them (K23_v2 left edge)."""
    huts = {"gable": kit.make_hut_gable("LibHutGable", lib["lib_c"], w=4.6, d=3.6, h=2.2, seed=5),
            "hip": kit.make_hut_hip("LibHutHip", lib["lib_c"], w=3.8, d=3.4, h=2.0, seed=6)}
    for i, (x, y, rz, kind) in enumerate(HUTS):
        _put(huts[kind], f"Hut{i}", coll, x, y, rz, 1.0, sink=0.12)
    fence = kit.make_fence("LibFence", lib["lib_c"], length=3.6, height=1.0)
    for i, (x, y, rz) in enumerate(((-24.6, -7.6, 0.1), (-21.0, -7.2, 0.0), (-22.6, 1.0, 1.6), (-8.2, 18.6, 0.2))):
        _put(fence, f"Fence{i}", coll, x, y, rz, 1.0, sink=0.02)
    for i, (x, y) in enumerate(((-22.8, -6.0), (-22.2, -6.5), (-22.6, -5.3))):
        _put(lib["barrel"], f"HutBarrel{i}", coll, x, y, 0, 1.0)
    for i, (x, y) in enumerate(((-21.5, -4.6), (-21.8, -3.6))):
        _put(lib["baskets"][i], f"HutBasket{i}", coll, x, y, rng.uniform(0, TAU), 1.0)
    _put(lib["woodpile"], "Woodpile", coll, -27.0, -0.8, 0.3, 1.0, sink=0.02)


# ============================================================== plants
def _blocked(x, y, keep):
    """keep: [(ax, ay, bx, by, r)] corridors (camera path, lines of sight) kept free of trees."""
    return any(pw._seg_dist(x, y, (ax, ay), (bx, by)) < r for ax, ay, bx, by, r in keep)


def build_plants(coll, lib, rng, keep=()):
    """Palms along the beach and round the fort, a palm-and-broadleaf grove behind it,
    forest over the far hills, big-leaf plants and bushes at the edges of the yard."""
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

    def clear_ground(x, y, pad):
        if is_yard(x, y) or in_fort(x, y, TURRET_R + pad):
            return False
        if any(math.hypot(x - hx, y - hy) < 4.0 + pad for hx, hy, _, _ in HUTS):
            return False
        return not _blocked(x, y, keep)

    k = 0
    # palms just behind the beach, north past the fort and south toward the camera
    for i in range(500):
        y = rng.uniform(-60, 170)
        d = rng.uniform(5.5, 13.0)
        x = shore_x(y) - d
        if not clear_ground(x, y, 1.0) or not free(x, y, 2.2):
            continue
        add(x, y, 2.2)
        _put(rng.choice(palms), f"BeachPalm{k}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.85, 1.2), sink=0.15)
        k += 1
    # the grove: palms mixed with broadleaf trees behind and round the fort
    for i in range(6000):
        x, y = rng.uniform(-75, 0), rng.uniform(-45, 120)
        d = shore_x(y) - x
        if d < 9.0 or not clear_ground(x, y, 1.5):
            continue
        r = 2.4 if d < 40 else 3.2
        if not free(x, y, r):
            continue
        add(x, y, r)
        if rng.random() < 0.62:
            src, s = rng.choice(palms), rng.uniform(0.85, 1.25)
        else:
            src, s = rng.choice(trees), rng.uniform(0.9, 1.3)
        _put(src, f"Grove{k}", coll, x, y, rng.uniform(0, TAU), s, sink=0.2)
        k += 1
        if k > 1100:
            break
    # far forest over the hills, sized up so it reads through the mist
    for i in range(7000):
        x, y = rng.uniform(-700, -40), rng.uniform(-150, 900)
        d = shore_x(y) - x
        if d < 60 or _n(x, y, 70.0, 5.5) < -0.3:
            continue
        src = rng.choice(trees + palms[:2])
        _put(src, f"FarTree{k}", coll, x, y, rng.uniform(0, TAU), rng.uniform(1.5, 2.4) * (1 + d / 600), sink=0.5)
        k += 1
        if k > 3600:
            break
    # ground plants: bushes and big leaves round the yard, the fort foot and under the trees
    j = 0
    for i in range(1600):
        x, y = rng.uniform(-45, 2), rng.uniform(-30, 60)
        d = shore_x(y) - x
        if d < 6.5 or in_fort(x, y, TURRET_R + 0.6) or is_yard(x, y) and _n(x, y, 3.0, 9.9) < 0.35:
            continue
        if any(math.hypot(x - hx, y - hy) < 3.2 for hx, hy, _, _ in HUTS) or _blocked(x, y, keep[:1]):
            continue
        src = rng.choice(bushes + bigleaf)
        _put(src, f"Plant{j}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.7, 1.3), sink=0.05)
        j += 1
    # lush foreground clumps (K23 bottom-left), and a few at the fort foot
    for i, (x, y, s) in enumerate(((-12.5, -10.5, 1.6), (-10.5, -12.0, 1.4), (-14.5, -8.5, 1.3), (-9.0, -11.0, 1.0),
                                   (-21.0, 2.8, 1.2), (-9.0, 2.6, 0.8), (-9.4, 13.4, 0.9), (-13.2, -10.0, 1.1))):
        _put(bigleaf[i % len(bigleaf)], f"FgLeaf{i}", coll, x, y, rng.uniform(0, TAU), s, sink=0.05)


# ============================================================== the porters
def carry_cycle(root, parts, pts, speed, frames, phase, pick=(3, 1.4), sink=1.4):
    """Porter's round: appear in the fort gate, walk to the sack stack, take a sack on
    the head, carry it along the jetty and up the gangplank, and go down the ship's
    hatch; then (unseen, inside the gate) start again. pts: polyline [(x, y)];
    pick: (vertex index, seconds paused there). Root keys every frame (so the jump back
    is clean), limbs every 2 frames."""
    P = [Vector((x, y, 0)) for x, y in pts]
    segs = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]
    t_walk = [s / speed for s in segs]
    i_pick, t_pick = pick
    starts, t = [], 0.0
    for i in range(len(segs)):
        if i == i_pick:
            t += t_pick
        starts.append(t)
        t += t_walk[i]
    period = t + sink + 0.6
    walked = [sum(segs[:i]) for i in range(len(segs) + 1)]

    def state(time):
        time %= period
        for i in range(len(segs)):
            if i == i_pick and starts[i] - t_pick <= time < starts[i]:
                u = (time - (starts[i] - t_pick)) / t_pick
                return P[i], i, walked[i], u > 0.45, True, 0.0
            if time < starts[i] + t_walk[i]:
                u = max(0.0, (time - starts[i]) / t_walk[i])
                return P[i].lerp(P[i + 1], u), i, walked[i] + segs[i] * u, i >= i_pick, False, 0.0
        u = min(1.0, (time - starts[-1] - t_walk[-1]) / sink)
        return P[-1], len(segs) - 1, walked[-1] + u * 0.6, True, False, u

    def z_at(p, i):
        if i >= len(segs) - 3:                                 # gangplank and deck
            if p.y > 2.3:
                return SHIP_DECK
            if p.y > 0.15:
                return JETTY_DECK + (SHIP_DECK - JETTY_DECK) * (p.y - 0.15) / 2.2
        return ground_z(p.x, p.y)

    prev = None
    for f in range(1, frames + 1):
        p, si, dist, carry, paused, down = state((f - 1) / kit.FPS + phase * period)
        d = P[si + 1] - P[si]
        rz = math.atan2(d.y, d.x) - math.pi / 2
        if prev is not None:
            rz += TAU * round((prev - rz) / TAU)
        prev = rz
        z = z_at(p, si) - 2.2 * down * down
        kw.key_set(root, "location", f, (p.x, p.y, z))
        kw.key_set(root, "rotation_euler", f, (0, 0, rz))
        if f % 2 and f != frames:
            continue
        sw = 0.0 if paused else math.sin(math.pi * dist / 0.62)
        kw.key_set(parts["legR"], "rotation_euler", f, (0.42 * sw, 0, 0))
        kw.key_set(parts["legL"], "rotation_euler", f, (-0.42 * sw, 0, 0))
        kw.key_set(parts["body"], "location", f, (0, 0, 0.92 + 0.03 * abs(sw)))
        if carry:                                              # both hands up, steadying the sack
            kw.key_set(parts["armR"], "rotation_euler", f, (0.2, -2.75, 0.0))
            kw.key_set(parts["foreR"], "rotation_euler", f, (0.0, -0.35, 0.0))
            kw.key_set(parts["armL"], "rotation_euler", f, (0.2, 2.75, 0.0))
            kw.key_set(parts["foreL"], "rotation_euler", f, (0.0, 0.35, 0.0))
        else:
            kw.key_set(parts["armR"], "rotation_euler", f, (0.35 * sw, 0, 0))
            kw.key_set(parts["foreR"], "rotation_euler", f, (0.25, 0, 0))
            kw.key_set(parts["armL"], "rotation_euler", f, (-0.35 * sw, 0, 0))
            kw.key_set(parts["foreL"], "rotation_euler", f, (0.25, 0, 0))
        k = 1.0 if carry else 0.0
        kw.with_interp("CONSTANT", lambda: kw.key_set(parts["sack"], "scale", f, (k, k, k)))


PORTER_PATH = [
    (FORT[0] + FH - 0.6, GATE_Y),          # 0  inside the gate (the jump back lands here, unseen)
    (FORT[0] + FH + 1.4, GATE_Y - 0.2),    # 1  out of the gate
    (-6.6, 3.4),                           # 2
    (PICKUP[0], PICKUP[1]),                # 3  take a sack off the stack
    (-2.2, -0.45),                         # 4  onto the jetty ramp
    (GX, -0.45),                           # 5  along the jetty
    (GX, 0.15),                            # 6  turn onto the gangplank
    (GX, 2.35),                            # 7  up to the rail
    (HATCH[0] + 0.3, HATCH[1] - 0.5),      # 8  across the deck
    HATCH,                                 # 9  down the hatch
]


def build_porters(coll, frames, rng, n=14, speed=1.12):
    """A line of porters on the carry cycle, plus porters and villagers standing at the
    heaps (sacks on heads, idling) and two on the fort walls (K23_v1)."""
    cloth = ("cloth_w", "cloth_w", "cloth_w", "cloth_t", "cloth_w", "rice", "cloth_w")
    for i in range(n):
        root, parts = kw.make_porter(f"Porter{i}", coll, seed=200 + i, robe_cloth=cloth[i % len(cloth)])
        carry_cycle(root, parts, PORTER_PATH, speed * rng.uniform(0.94, 1.06), frames,
                    phase=i / n + rng.uniform(-0.015, 0.015))
    # standing at the heaps: porters waiting with loads, villagers filling baskets
    for i, (x, y, rz, load) in enumerate(((-7.6, -1.6, -0.6, True), (-3.2, -2.2, 2.4, True), (-8.7, -8.4, -2.2, False),
                                          (-4.0, -9.0, 0.4, True), (-11.0, -4.8, 1.2, False))):
        root, parts = kw.make_porter(f"Waiting{i}", coll, seed=300 + i)
        root.location = (x, y, height(x, y))
        root.rotation_euler[2] = rz
        if load:
            kw.pose(parts, {"armR": (0.2, -2.75, 0), "foreR": (0, -0.35, 0), "armL": (0.2, 2.75, 0),
                            "foreL": (0, 0.35, 0)})
        else:
            parts["sack"].scale = (0, 0, 0)
            kw.pose(parts, {"armR": (0.5, 0, 0.1), "foreR": (0.8, 0, 0), "armL": (0.4, 0, -0.1), "foreL": (0.7, 0, 0)})
        kw.idle(parts, random.Random(300 + i), frames, body=0.02, head=0.1)
    for i, (x, y, rz) in enumerate(((-12.6, -4.3, 0.3), (-12.9, -5.1, 2.6))):
        fig = kit.make_figure(f"Sitter{i}", coll, "villager", seed=320 + i, pose="sit")
        fig.location = (x, y, height(x, y))
        fig.rotation_euler[2] = rz
        kit.animate_idle(fig, rng, 1, frames, amount=0.02)
    # a lookout on the front wall and one by the flag
    z0 = height(FORT[0] + FH, FORT[1] - FH) - 0.05
    for i, (x, y, rz) in enumerate(((FORT[0] - 1.5, FORT[1] - FH + 0.7, math.pi), (FORT[0] + FH - 0.7, FORT[1] + 1.0, -1.5))):
        fig = kit.make_figure(f"Lookout{i}", coll, "villager", seed=330 + i, cloth="cloth_w")
        fig.location = (x, y, z0 + WALL_H)
        fig.rotation_euler[2] = rz
        kit.animate_idle(fig, rng, 1, frames, amount=0.03)


def build_gulls(coll, frames, rng):
    for i in range(6):
        g = kw.make_gull(f"Gull{i}", coll)
        g.scale = (1.3, 1.3, 1.3)
        cx, cy, r, z = rng.uniform(6, 26), rng.uniform(-4, 10), rng.uniform(5, 11), rng.uniform(10, 17)
        w = rng.choice((-1, 1)) * rng.uniform(0.3, 0.45)
        a0 = rng.uniform(0, TAU)
        for f in range(1, frames + 1, 4):
            a = a0 + w * f / kit.FPS
            g.location = (cx + r * math.cos(a), cy + r * math.sin(a), z + 0.6 * math.sin(f / 13.0 + i))
            g.rotation_euler = (0, -0.35 * math.copysign(1, w), a + math.copysign(math.pi / 2, w) - math.pi / 2)
            g.keyframe_insert("location", frame=f)
            g.keyframe_insert("rotation_euler", frame=f)


# ============================================================== assembly
def build_library(lib_c):
    """Library meshes (instanced, hidden at the end)."""
    lib = dict(lib_c=lib_c)
    lib["baskets"] = [pw.make_basket(f"LibBasket{i}", lib_c, r=r, h=h, seed=i)
                      for i, (r, h) in enumerate([(0.4, 0.4), (0.34, 0.44), (0.44, 0.34), (0.32, 0.34)])]
    lib["big_basket"] = pw.make_basket("LibBigBasket", lib_c, r=0.6, h=0.5, seed=9)
    lib["sack"] = pw.make_pepper_sack("LibPepperSack", lib_c)
    lib["sack_lying"] = pw.make_pepper_sack("LibPepperSackLying", lib_c, lying=True, seed=3)
    lib["mats"] = [pw.make_woven_mat("LibMat0", lib_c, 2.3, 1.6),
                   pw.make_woven_mat("LibMat1", lib_c, 2.6, 1.2, pepper=520, seed=1),
                   pw.make_woven_mat("LibMat2", lib_c, 2.0, 1.4, pepper=480, seed=2)]
    lib["trays"] = [pw.make_tray(f"LibTray{i}", lib_c, r=0.7 + 0.06 * i, seed=i) for i in range(2)]
    lib["pots"] = [pw.make_pot(f"LibPot{i}", lib_c, h=h, seed=i) for i, h in enumerate((0.55, 0.42))]
    lib["woodpile"] = pw.make_woodpile("LibWoodpile", lib_c)
    lib["crate"] = kit.make_crate("LibCrate", lib_c, size=0.7)
    lib["barrel"] = kit.make_barrel("LibBarrel", lib_c)
    lib["palms"] = [kit.make_palm(f"LibPalm{i}", lib_c, seed=10 + i, height=7.5 + 0.6 * i) for i in range(6)]
    lib["trees"] = ([pw.make_vine_tree(f"LibJungleTree{i}", lib_c, seed=20 + i, height=7.5 + 1.2 * i, vine=False)
                     for i in range(3)] +
                    [kit.make_tree(f"LibTree{i}", lib_c, seed=i, height=6 + i) for i in range(3)])
    lib["bushes"] = [kit.make_bush(f"LibBush{i}", lib_c, seed=i, size=0.9 + 0.25 * i) for i in range(3)]
    lib["bigleaf"] = [pw.make_bigleaf(f"LibBigLeaf{i}", lib_c, seed=i, size=1.2 + 0.35 * i) for i in range(3)]
    return lib


def build_world(frames, keep=()):
    """Everything but the camera; returns the rig collection."""
    register_palette()
    rng = random.Random(23)
    world_c = kit.new_collection("World")
    fort_c = kit.new_collection("Fort")
    port_c = kit.new_collection("Port")
    ships_c = kit.new_collection("Ships")
    plants_c = kit.new_collection("Plants")
    people_c = kit.new_collection("People")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    make_terrain(world_c)
    sea = make_sea(world_c)
    kw.animate_sea(sea, rig_c, frames)
    w = cw.setup_world()
    for nd in w.node_tree.nodes:                              # less sky fill: crisper sun and shadow
        if nd.bl_idname == "ShaderNodeBackground":
            nd.inputs["Strength"].default_value = 0.7
    # warm morning sun from over the sea, a little in front: shadows fall left and away (K23)
    cw.add_sun(rig_c, direction=(-0.72, 0.42, -0.55), energy=9.5, color=(1.0, 0.87, 0.70), angle=4.0)
    lib = build_library(lib_c)
    build_fort(fort_c, rng)
    build_jetty(port_c, lib, frames)
    build_heaps(port_c, lib, rng)
    build_village(port_c, lib, rng)
    build_ships(ships_c, lib, frames)
    build_plants(plants_c, lib, rng, keep)
    build_porters(people_c, frames, rng)
    build_gulls(people_c, frames, rng)
    pw.add_mist_composite(bpy.context.scene, start=45.0, depth=480.0, strength=0.66)
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c
