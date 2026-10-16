"""Inland beats S33, S35, S36, S37 (shot-list clips 40, 42-43, 44-45, 46): three sets in one
scene, cut between beats (Inland.blend, built by inland_film.py).

Set A, the coast to the capital (S33 K40, S35 K42). World coordinates ARE the Colachel beach
coordinates of S01-S06 (colachel_world): the same village, palms, boats and jetty at the
origin, the same faceted sea, the Dutch fleet offshore. Inland (+Y) a broad band of rice paddies
(kit paddy cells, aligned with the coast) crossed by palm-grove strips with hamlets, then
Padmanabhapuram (palace_world: the palace, its town, tank and people, NOT remodelled; the whole
set hangs under one empty, PalaceRoot, at PAL) at the foot of faceted green hills. The diorama
compresses the 13 km to about 0.5 km, as the Flow reference does. A dirt road runs from the
village to the palace gate; the palace's south-east road runs on toward Kottar. S35's Dutch
column marches down that road past the palace, paddies to the west, houses to the east.

Set B, Kalkulam (S36 K44), centred on FO: a red laterite fort (palace_world laterite walls, taller,
with merlons, square towers and a carved gate), tents and sheds inside; the king arrives on the
royal elephant (kit) through a lane in a crowd of about two thousand Nairs (geometry-nodes
instances of kit figures, swaying, stamping after "he raises"), more streaming in down the road
from the palm forest, red banners, tents, hills behind.

Set C, Thiruvattar (S37 K46), centred on TO: the Adikesava Perumal temple at dawn: flagstone
court, a Kerala shrine with a stone-tiled roof (palace_world roof), a gopuram, a granite pillared
corridor, the tall brass flag-mast on its stepped plinth, rows of clay oil lamps, palms and trees
in pink-gold mist; the king (kit king rig) kneels and lays his sword before the shrine, a priest
waves a lamp.

Light: one sun from colachel_world.scene_base, re-aimed per beat by inland_film.py (the dawn beat
gets a low, warmer sun). Haze: the scene_base box over set A, one more box per other set.
No text anywhere; flags are plain colours (Dutch orange, Travancore red).
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

import colachel_kit as kit
import colachel_world as cw
import palace_world as palw
import pepper_world as pepw
import port_world as ptw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau
UP = Vector((0, 0, 1))
_smooth = cw._smooth

# ----------------------------------------------------------------- layout
PAL = (40.0, 330.0)                 # Padmanabhapuram palace centre (palace_world origin)
HILL_D0 = 430.0                     # the hills rise from this distance inland (metres from the shore)
COAST_A = math.atan(-0.3)           # the Colachel shoreline runs along this angle (shore_y = -0.3 x)
FO = (12000.0, 0.0)                 # Kalkulam fort set origin (the gate)
TO = (24000.0, 0.0)                 # Thiruvattar temple set origin
R_BEACH = ([(3.0, 24.0), (1.0, 48.0), (0.0, 70.0)], 2.6)          # village to the end of the palace south road
R_KOTTAR = ([(PAL[0] + 92.0, PAL[1] - 230.0), (200.0, 62.0), (320.0, 22.0), (520.0, -36.0), (850.0, -136.0)], 2.8)


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(px - ax - vx * t, py - ay - vy * t)


def _axis(spec):
    """spec: [(a, b, step), ...] contiguous ranges -> sorted coordinates."""
    out = []
    for a, b, s in spec:
        n = max(1, round((b - a) / s))
        out += [a + (b - a) * i / n for i in range(n)]
    out.append(spec[-1][1])
    return out


def _heightfield(coll, name, xs, ys, height, mat_fn, mats, seed=3):
    """Faceted jittered heightfield: triangulated grid, flat-shaded, material per face."""
    rng = random.Random(seed)
    bm = bmesh.new()
    grid = []
    for j, y in enumerate(ys):
        row = []
        sy = (ys[min(j + 1, len(ys) - 1)] - ys[max(j - 1, 0)]) / 2
        for i, x in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                sx = (xs[i + 1] - xs[i - 1]) / 2
                jx, jy = rng.uniform(-0.28, 0.28) * sx, rng.uniform(-0.28, 0.28) * sy
            px, py = x + jx, y + jy
            row.append(bm.verts.new((px, py, height(px, py))))
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = mats.index(mat_fn(c.x, c.y, c.z, f.normal.z, rng))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _face(dx, dy):
    """rot_z that turns a +Y-facing asset to look along (dx, dy)."""
    return math.atan2(dy, dx) - math.pi / 2


class Spacer:
    """Grid hash for 'is this spot free' tests while scattering."""

    def __init__(self, cell=6.0):
        self.cell, self.d = cell, {}

    def free(self, x, y, r):
        c = self.cell
        gx, gy = int(x // c), int(y // c)
        for i in range(gx - 1, gx + 2):
            for j in range(gy - 1, gy + 2):
                for a, b, rb in self.d.get((i, j), ()):
                    if (x - a) ** 2 + (y - b) ** 2 < (r + rb) ** 2:
                        return False
        return True

    def add(self, x, y, r):
        self.d.setdefault((int(x // self.cell), int(y // self.cell)), []).append((x, y, r))


# ================================================================= library
def build_library(lib_c):
    palw.register_palette()
    pepw.register_palette()
    lib = {}
    lib["palms"] = [kit.make_palm(f"LibIPalm{i}", lib_c, seed=10 + i, height=7.5 + 0.6 * i) for i in range(6)]
    lib["trees"] = [kit.make_tree(f"LibITree{i}", lib_c, seed=i, height=6.5 + i) for i in range(4)]
    lib["jtrees"] = [pepw.make_vine_tree(f"LibIJTree{i}", lib_c, seed=20 + i, height=8.0 + 1.5 * i, vine=False)
                     for i in range(3)]
    lib["bushes"] = [kit.make_bush(f"LibIBush{i}", lib_c, seed=i, size=0.9 + 0.25 * i) for i in range(3)]
    lib["bigleaf"] = [pepw.make_bigleaf(f"LibIBigLeaf{i}", lib_c, seed=i, size=1.1 + 0.3 * i) for i in range(3)]
    lib["bananas"] = [palw.make_banana(f"LibIBanana{i}", lib_c, seed=i, height=2.2 + 0.3 * i) for i in range(3)]
    lib["rocks"] = [kit.make_rock(f"LibIRock{i}", lib_c, seed=i, size=0.6 + 0.3 * i) for i in range(3)]
    lib["huts"] = [kit.make_hut_gable(f"LibIHutG{i}", lib_c, w=w, d=d, h=h, seed=40 + i)
                   for i, (w, d, h) in enumerate([(4.2, 3.4, 2.1), (5.0, 3.8, 2.3), (3.8, 3.2, 2.0)])] + \
                  [kit.make_hut_hip(f"LibIHutH{i}", lib_c, seed=50 + i) for i in range(2)]
    lib["crate"] = kit.make_crate("LibICrate", lib_c, size=0.75)
    lib["barrel"] = kit.make_barrel("LibIBarrel", lib_c)
    lib["sack"] = kit.make_sack("LibISack", lib_c)
    lib["fence"] = kit.make_fence("LibIFence", lib_c)
    lib["pot"] = pepw.make_pot("LibIPot", lib_c)
    lib["basket"] = pepw.make_basket("LibIBasket", lib_c)
    lib["villagers"] = [kit.make_figure(f"LibIVill{i}", lib_c, "villager", seed=60 + i, cloth=c)
                        for i, c in enumerate(("cloth_w", "cloth_t", "cloth_w", "cloth_r"))]
    lib["guard"] = kit.make_figure("LibIGuard", lib_c, "nair_spear", seed=3)
    # walker templates (cloned with kit.clone_walker)
    lib["w_dutch"] = [kit.make_walker(f"LibIWDutch{i}", lib_c, "dutch", seed=i) for i in range(3)]
    lib["w_officer"] = [kit.make_walker("LibIWOfficer", lib_c, "dutch", seed=40)]
    kit.recolor(lib["w_officer"][0][1]["body"], strip=("steel", "post"))          # officer: no musket
    lib["w_ally"] = [kit.make_ally_walker(f"LibIWAlly{i}", lib_c, seed=i, turban=t, shield=i % 2 == 0)
                     for i, t in enumerate(kit.ALLY_TURBANS)]
    lib["w_nair"] = [kit.make_walker(f"LibIWNair{i}", lib_c, "nair", seed=i) for i in range(2)] + \
                    [kit.make_walker(f"LibIWNairSp{i}", lib_c, "nair_spear", seed=7 + i) for i in range(2)]
    for root, parts in lib["w_dutch"] + lib["w_officer"] + lib["w_ally"] + lib["w_nair"]:
        kit.hide_source(root)
        for p in parts.values():
            p.hide_render = p.hide_viewport = True
    return lib


def _walker(tmpl, name, coll):
    root, parts = kit.clone_walker(tmpl[1], name, coll)
    for p in parts.values():
        p.hide_render = p.hide_viewport = False
    return root, parts


def _show_only(obs, f0, f1):
    """Scale 0 outside [f0, f1] (constant keys): keeps a group out of the other beats."""
    for ob in obs:
        s = ob.scale.copy()
        for f, v in ((1, 0.0), (f0, 1.0), (f1 + 1, 0.0)):
            ob.scale = (s.x * v, s.y * v, s.z * v) if v else (0, 0, 0)
            ob.keyframe_insert("scale", frame=f)
        ob.scale = s
        if ob.animation_data and ob.animation_data.action:
            for fc in _fcurves(ob.animation_data.action):
                if fc.data_path == "scale":
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"


def _fcurves(action):
    """All F-curves of an action (Blender 5 layered actions or the old flat list)."""
    try:
        return list(action.fcurves)
    except AttributeError:
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out += list(bag.fcurves)
        return out


# ===================================================================== SET A
def to_uv(x, y):
    """Coast frame: u along the shore, v inland (about metres from the shoreline)."""
    c, s = math.cos(COAST_A), math.sin(COAST_A)
    return x * c + y * s, -x * s + y * c


def from_uv(u, v):
    c, s = math.cos(COAST_A), math.sin(COAST_A)
    return u * c - v * s, u * s + v * c


def d_shore(x, y):
    return y - cw.shore_y(x)


def plain_h(x, y):
    d = d_shore(x, y)
    return 2.3 + 0.9 * _smooth(60.0, 480.0, d) + 0.06 * _n(x, y, 30.0, 4.4)


def hills_h(x, y):
    d = d_shore(x, y)
    m = _smooth(HILL_D0, HILL_D0 + 260.0, d)
    if m <= 0:
        return 0.0
    ridge = (1.0 - abs(_n(x, y, 170.0, 7.7))) ** 2
    h = m * (22.0 + 85.0 * ridge + 22.0 * _n(x, y, 70.0, 3.3))
    h += _smooth(HILL_D0 + 200.0, HILL_D0 + 650.0, d) * 170.0 * (1.0 - abs(_n(x, y, 300.0, 1.9))) ** 2
    return max(0.0, h)


PZ = 0.0                                                     # set in build_set_a (plain height at PAL)


def ground_a0(x, y):
    d = d_shore(x, y)
    if d < 70.0:
        hb = cw.height(x, y)                                     # the S01-S06 beach itself
        if d < 40.0:
            return hb
        w = _smooth(40.0, 70.0, d)
        return hb * (1 - w) + plain_h(x, y) * w
    h = plain_h(x, y) + hills_h(x, y)
    lx, ly = x - PAL[0], y - PAL[1]
    r = math.hypot(lx, ly)
    if r < 230.0:                       # the palace's own ground (sampled inside r 149: none of its hills)
        wp = 1.0 - _smooth(150.0, 230.0, r)
        k = min(1.0, 149.0 / max(r, 1e-6))
        h = h * (1 - wp) + (PZ + palw.height(lx * k, ly * k)) * wp
    return h


_CELLS = []           # planned paddy cells: (cx, cy, rot, w, d, z)
_CELL_HASH = {}


def _cell_local(c, x, y):
    cx, cy, rot = c[0], c[1], c[2]
    dx, dy = x - cx, y - cy
    cr, sr = math.cos(rot), math.sin(rot)
    return dx * cr + dy * sr, -dx * sr + dy * cr


def _cell_edge_dist(c, x, y):
    u, v = _cell_local(c, x, y)
    return math.hypot(max(abs(u) - c[3] / 2, 0.0), max(abs(v) - c[4] / 2, 0.0))


def ground_a(x, y):
    """Set A terrain height: the beach, the plain, the palace town and the hills, flattened
    under the paddy cells so they sit on it."""
    h = ground_a0(x, y)
    best, bc = 3.0, None
    for c in _CELL_HASH.get((int(x // 40), int(y // 40)), ()):
        e = _cell_edge_dist(c, x, y)
        if e <= 0.3:
            return c[5] - 0.07
        if e < best:
            best, bc = e, c
    if bc is None:
        return h
    t = _smooth(0.3, 3.0, best)
    return (bc[5] - 0.07) * (1 - t) + h * t


def _road_segs():
    segs = []
    for pts, hw in (R_BEACH, R_KOTTAR):
        for a, b in zip(pts, pts[1:]):
            segs.append((a, b, hw))
    for pts, hw in palw.ROADS:                                   # the palace town's roads, in world space
        for a, b in zip(pts, pts[1:]):
            segs.append(((a[0] + PAL[0], a[1] + PAL[1]), (b[0] + PAL[0], b[1] + PAL[1]), hw))
    out = []
    for a, b, hw in segs:
        out.append((a, b, hw, min(a[0], b[0]) - hw - 8, max(a[0], b[0]) + hw + 8,
                    min(a[1], b[1]) - hw - 8, max(a[1], b[1]) + hw + 8))
    return out


_SEGS = []


def road_dist(x, y, my_only=False):
    """Distance outside the nearest road edge (negative on a road); 99 when far from all."""
    best = 99.0
    for k, (a, b, hw, x0, x1, y0, y1) in enumerate(_SEGS):
        if my_only and k >= _N_MY:
            break
        if x0 < x < x1 and y0 < y < y1:
            best = min(best, _seg_dist(x, y, a, b) - hw)
    return best


_N_MY = len(R_BEACH[0]) - 1 + len(R_KOTTAR[0]) - 1


def grove(x, y):
    """Palm-grove strips and patches across the paddy band (K40)."""
    u, v = to_uv(x, y)
    if v < 47.0:
        return True
    b1 = 118.0 + 12.0 * _n(u, 0.0, 90.0, 2.0)
    if abs(v - b1) < 7.0 + 3.0 * _n(u, v, 40.0, 1.1):
        return True
    b2 = 238.0 + 14.0 * _n(u, 0.0, 120.0, 5.0)
    if abs(v - b2) < 6.5 and _n(u, v, 80.0, 3.3) > -0.15:
        return True
    return _n(x, y, 70.0, 8.8) > 0.42


def se_road_x(ly):
    """x (palace local) of the palace's south-east road at local y."""
    pts = palw.ROADS[3][0]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if by <= ly <= ay:
            return ax + (bx - ax) * (ly - ay) / (by - ay)
    return pts[-1][0] if ly < pts[-1][1] else pts[0][0]


def _terrain_a(coll):
    xs = _axis([(-1200, -700, 25), (-700, -350, 6), (-350, PAL[0] - 125, 3), (PAL[0] - 125, PAL[0] + 125, 1.5),
                (PAL[0] + 125, 450, 3), (450, 800, 4), (800, 1200, 25)])
    ys = _axis([(-500, -150, 20), (-150, -40, 5), (-40, PAL[1] - 125, 3), (PAL[1] - 125, PAL[1] + 125, 1.5),
                (PAL[1] + 125, 600, 2.5)])
    mats = ["sand", "sand_wet", "grass", "grass_lt", "court", "road", "hill_lt", "ghat_lo", "ghat_hi", "granite_dk",
            "paddy_bund"]
    x0, x1, y0, y1 = palw.WALL

    def mat_fn(x, y, z, nz, rng):
        d = d_shore(x, y)
        if d < 1.6:
            return "sand_wet"
        if d < cw.grass_line(x, y) and d < 40:
            return "sand"
        lx, ly = x - PAL[0], y - PAL[1]
        if abs(lx) < 140 and abs(ly) < 140:
            if palw.in_tank(lx, ly, 0.3):
                return "granite_dk"
            if x0 < lx < x1 and y0 < ly < y1:
                return "court"
        if z > PZ + 6.0 and d > HILL_D0 - 60:
            k = rng.random() + 0.25 * _n(x, y, 120.0, 9.1)
            return "ghat_hi" if k > 0.72 else ("ghat_lo" if k > 0.35 else ("grass" if k > 0.1 else "hill_lt"))
        if road_dist(x, y) < 0.35 * _n(x, y, 3.0, 4.2):
            return "road"
        for c in _CELL_HASH.get((int(x // 40), int(y // 40)), ()):
            if _cell_edge_dist(c, x, y) < 0.6:
                return "paddy_bund"
        return "grass_lt" if _n(x, y, 18.0, 5.5) > 0.12 else "grass"
    ob = _heightfield(coll, "TerrainA", xs, ys, ground_a, mat_fn, mats, seed=3)
    # the hills behind: their own even, coarse grid (big facets, no slivers), tucked 1 m under the
    # plain where the two overlap
    hx = _axis([(-1300, 1300, 18)])
    hy = _axis([(560, 1800, 18)])
    _heightfield(coll, "TerrainHills", hx, hy, lambda x, y: ground_a(x, y) - (1.0 - _smooth(592.0, 606.0, y)),
                 mat_fn, mats, seed=4)
    return ob


def _plan_paddies(houses_w, seed=12):
    """Rice paddy cells in coast-aligned rows between the beach belt and the hills, kept off the
    roads, the palace town, the village, the battery hillock and the grove strips."""
    rng = random.Random(seed)
    cells = []
    hx = {}
    for (x, y) in houses_w:
        hx.setdefault((int(x // 30), int(y // 30)), []).append((x, y))
    def bad_at(px, py):
        lx, ly = px - PAL[0], py - PAL[1]
        if (grove(px, py) and math.hypot(lx, ly) > 260.0) or road_dist(px, py) < 1.6 or d_shore(px, py) > HILL_D0 - 10.0 or                 palw._rect_dist(lx, ly, *palw.WALL) < 16.0 or palw.in_tank(lx, ly, 5.0) or                 math.hypot(px - cw.BATTERY[0], py - cw.BATTERY[1]) < 30.0:
            return True
        if math.hypot(lx, ly) < 175 and ly > -58:                  # keep the town round the palace
            return True
        if -185 < ly < -44 and se_road_x(ly) + 2 < lx < se_road_x(ly) + 60:     # the S35 hamlet
            return True
        return any(math.hypot(px - q[0], py - q[1]) < 8.5 for q in hx.get((int(px // 30), int(py // 30)), ()))

    def try_cell(cu, cv, du, dv, depth):
        """A cell centred at (cu, cv) in the coast frame; split in four where it meets a road,
        a grove or a house, so the fields run right up to them."""
        cx, cy = from_uv(cu, cv)
        if not (-560 < cx < 760):
            return
        rot = COAST_A + rng.uniform(-0.025, 0.025)
        w, dd = du - 0.15, dv - 0.15
        cr, sr = math.cos(rot), math.sin(rot)
        na, nb = max(3, math.ceil(w / 7.0) + 1), max(3, math.ceil(dd / 7.0) + 1)
        pts = [(cx + a * w / 2 * cr - b * dd / 2 * sr, cy + a * w / 2 * sr + b * dd / 2 * cr)
               for a in [-1 + 2 * i / (na - 1) for i in range(na)] for b in [-1 + 2 * j / (nb - 1) for j in range(nb)]]
        if any(bad_at(px, py) for px, py in pts):
            if depth < 2 and du > 13.0:
                for su in (-0.25, 0.25):
                    for sv in (-0.25, 0.25):
                        try_cell(cu + su * du, cv + sv * dv, du / 2, dv / 2, depth + 1)
            return
        if rng.random() < 0.03:
            return
        z = max(ground_a0(px, py) for px, py in pts) + 0.02
        cells.append((cx, cy, rot, w, dd, z))

    v = 49.0
    while v < HILL_D0:
        dv = rng.uniform(18.0, 30.0)
        u = -760.0 + rng.uniform(0, 20)
        while u < 900.0:
            du = rng.uniform(26.0, 46.0)
            try_cell(u + du / 2, v + dv / 2, du, dv, 0)
            u += du
        v += dv
    _CELLS[:] = cells
    _CELL_HASH.clear()
    for c in cells:
        r = math.hypot(c[3], c[4]) / 2 + 3.5
        for i in range(int((c[0] - r) // 40), int((c[0] + r) // 40) + 1):
            for j in range(int((c[1] - r) // 40), int((c[1] + r) // 40) + 1):
                _CELL_HASH.setdefault((i, j), []).append(c)
    return cells


def in_paddy(x, y, pad=0.0):
    for c in _CELL_HASH.get((int(x // 40), int(y // 40)), ()):
        if _cell_edge_dist(c, x, y) <= pad:
            return True
    return False


def _build_paddies(coll):
    for k, (cx, cy, rot, w, d, z) in enumerate(_CELLS):
        ob = kit.make_paddy_cell(f"Paddy{k}", coll, w=w, d=d, seed=k, bund=0.5, bund_h=0.3)
        ob.location = (cx, cy, z - 0.04)
        ob.rotation_euler[2] = rot


def _build_palace(colls, lib, frames):
    """palace_world's palace, town, tank and people, unchanged, under one empty at PAL."""
    root = bpy.data.objects.new("PalaceRoot", None)
    root.empty_display_size = 5.0
    colls["palace"].objects.link(root)
    root.location = (PAL[0], PAL[1], PZ)
    plants = dict(palms=lib["palms"], trees=lib["trees"], bushes=lib["bushes"], bananas=lib["bananas"])
    anchors = palw.build_palace(colls["palace"], colls["lib"], plants, frames)
    palw.build_town(colls["town"], colls["lib"], plants)
    palw.build_people(colls["townpeople"], frames, anchors)
    for c in (colls["palace"], colls["town"], colls["townpeople"]):
        for ob in c.objects:
            if ob.parent is None and ob is not root:
                ob.parent = root
    # S35: the houses between the south road and the south-east road give way to paddies
    houses = []
    for ob in list(colls["town"].objects):
        if not ob.name.startswith("House"):
            continue
        lx, ly = ob.location.x, ob.location.y
        if ly < -56 and -19.0 < lx < se_road_x(ly) - 3.0:
            bpy.data.objects.remove(ob, do_unlink=True)
            continue
        if -110 < ly < -44 and se_road_x(ly) < lx < se_road_x(ly) + 16.0:      # thatched huts there instead (K42)
            bpy.data.objects.remove(ob, do_unlink=True)
            continue
        houses.append((lx + PAL[0], ly + PAL[1]))
    return root, houses


def _fit_town(colls, keep):
    """Snap the town's trees and houses to this terrain (beyond the palace's own ground) and
    clear trees out of the paddies, off the roads and off the S35 hamlet."""
    for ob in list(colls["town"].objects):
        if ob.type != "MESH" or ob.name.startswith(("TempleTank",)):
            continue
        lx, ly, lz = ob.location
        wx, wy = lx + PAL[0], ly + PAL[1]
        if ob.name.startswith("House") and any(math.hypot(wx - kx, wy - ky) < kr + 2.5 for kx, ky, kr in keep):
            bpy.data.objects.remove(ob, do_unlink=True)
            continue
        tree = ob.name.startswith("Tree")
        if tree and (in_paddy(wx, wy, 1.5) or road_dist(wx, wy) < 1.0 or ground_a(wx, wy) > PZ + 9.0 or
                     any(math.hypot(wx - kx, wy - ky) < kr for kx, ky, kr in keep)):
            bpy.data.objects.remove(ob, do_unlink=True)
            continue
        sink = palw.height(lx, ly) - lz
        ob.location.z = ground_a(wx, wy) - PZ - sink


def _build_village(colls, frames):
    """The Colachel village of S01-S06 (colachel_world.build_village) and the Dutch fleet
    offshore. Its broad-leaf woods inland are dropped: the paddy band takes their place."""
    cw.build_village(colls["village"], colls["props"], colls["plants"], colls["people"], colls["lib"], frames)
    for ob in list(colls["plants"].objects):
        if ob.name.startswith("Tree") and (d_shore(ob.location.x, ob.location.y) > 34 or
                                           in_paddy(ob.location.x, ob.location.y, 1.0)):
            bpy.data.objects.remove(ob, do_unlink=True)
    cw.build_fleet(colls["fleet"], frames)


def _put(src, name, coll, x, y, rz=0.0, s=1.0, sink=0.05, g=None):
    g = g or ground_a
    return kit.instance(src, name, coll, (x, y, g(x, y) - sink), rot_z=rz, scale=s)


def _build_groves(coll, lib, keep, rng):
    """Palms several rows deep in the grove strips, along the beach belt and round the hamlets;
    round trees mixed in; undergrowth; single palms on the paddy bunds; jungle at the hill foot."""
    sp = Spacer(6.0)

    def kept(x, y):
        return any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep)
    palms, trees = lib["palms"], lib["trees"] + lib["jtrees"][:1]
    k = 0
    for i in range(90000):
        u, v = rng.uniform(-820, 950), rng.uniform(30, HILL_D0 + 140)
        x, y = from_uv(u, v)
        if not (-640 < x < 860):
            continue
        d = v
        lx, ly = x - PAL[0], y - PAL[1]
        if math.hypot(lx, ly) < 300 and ly > -200:
            continue                                            # the palace town plants its own trees
        foot = d > HILL_D0 - 20
        if not (grove(x, y) or foot) or kept(x, y) or in_paddy(x, y, 1.2) or road_dist(x, y) < 1.2:
            continue
        if d < 34 or hills_h(x, y) > 10:
            continue
        far = abs(u - 100) > 520 or v > HILL_D0 - 40
        if far and rng.random() < 0.45:
            continue
        r = 2.4 if not far else 3.4
        if not sp.free(x, y, r):
            continue
        sp.add(x, y, r)
        if rng.random() < (0.78 if not foot else 0.35):
            src, s = rng.choice(palms), rng.uniform(0.9, 1.25)
        else:
            src, s = rng.choice(trees), rng.uniform(0.9, 1.4)
        _put(src, f"Grove{k}", coll, x, y, rng.uniform(0, TAU), s, sink=0.2)
        k += 1
        if k > 5200:
            break
    j = 0
    for i in range(30000):                                     # undergrowth near the S35 road and the beach
        x, y = rng.uniform(-200, 320), rng.uniform(30, PAL[1] - 30)
        if not grove(x, y) or kept(x, y) or in_paddy(x, y, 0.6) or road_dist(x, y) < 0.6 or d_shore(x, y) < 30:
            continue
        lx, ly = x - PAL[0], y - PAL[1]
        if palw._rect_dist(lx, ly, *palw.WALL) < 4 or palw.in_tank(lx, ly, 3):
            continue
        _put(rng.choice(lib["bushes"] + lib["bigleaf"]), f"Under{j}", coll, x, y, rng.uniform(0, TAU),
             rng.uniform(0.7, 1.4))
        j += 1
        if j > 1800:
            break
    m = 0
    for c in _CELLS:                                           # a lone palm on some bunds (K40)
        if rng.random() < 0.16:
            a = rng.choice((-1, 1))
            u = a * c[3] / 2
            v = rng.uniform(-c[4] / 2, c[4] / 2)
            cr, sr = math.cos(c[2]), math.sin(c[2])
            x, y = c[0] + u * cr - v * sr, c[1] + u * sr + v * cr
            if road_dist(x, y) > 2 and not kept(x, y):
                _put(rng.choice(palms), f"BundPalm{m}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.9, 1.15),
                     sink=0.15)
                m += 1
    return k


def _build_hamlets(coll, lib, rng, keep):
    """Thatched huts at the grove edges among the paddies (K40), with a few props."""
    sp = Spacer(10.0)
    out = 0
    for i in range(6000):
        u, v = rng.uniform(-600, 800), rng.uniform(55, HILL_D0 - 20)
        x, y = from_uv(u, v)
        if not (-500 < x < 700) or not grove(x, y) or in_paddy(x, y, 3.0) or road_dist(x, y) < 3.0:
            continue
        lx, ly = x - PAL[0], y - PAL[1]
        if math.hypot(lx, ly) < 190 or v < 60 or any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep):
            continue
        if not sp.free(x, y, 22.0):
            continue
        sp.add(x, y, 22.0)
        rz = COAST_A + rng.choice((0, math.pi)) + rng.uniform(-0.3, 0.3)
        _put(lib["huts"][out % len(lib["huts"])], f"FieldHut{out}", coll, x, y, rz, rng.uniform(0.9, 1.05), sink=0.1)
        for p in range(3):
            a = rng.uniform(0, TAU)
            px, py = x + 3.2 * math.cos(a), y + 3.2 * math.sin(a)
            _put(rng.choice((lib["crate"], lib["sack"], lib["pot"], lib["basket"])), f"FieldProp{out}_{p}", coll,
                 px, py, rng.uniform(0, TAU), rng.uniform(0.8, 1.1), sink=0.02)
        out += 1
        if out >= 28:
            break
    return out


# S35 hamlet: thatched huts, banana clumps, props and onlookers on the east side of the
# south-east road (palace local coordinates), opposite the paddies.
S35_CAM = [(51.0, -96.0), (54.0, -105.0), (57.0, -113.0), (61.0, -124.0)]   # S35 camera ground track (palace local): kept clear
S35_HUTS = [(-60.0, 8.5), (-73.0, 9.0), (-87.0, 8.0), (-101.0, 9.5), (-116.0, 8.5), (-131.0, 9.0), (-146.0, 8.5),
            (-162.0, 9.0), (-80.0, 19.0), (-108.0, 20.0), (-137.0, 19.0)]     # (palace-local y, metres east of the road)


def _build_s35_hamlet(coll, lib, frames, rng):
    """S35 (K42): thatched huts along the east side of the south-east road, facing it, with
    props, banana clumps, fences, a palm grove behind and villagers watching the column."""
    out = []
    face_road = _face(-0.939, -0.344)
    for i, (ly, off) in enumerate(S35_HUTS):
        lx = se_road_x(ly) + off
        x, y = lx + PAL[0], ly + PAL[1]
        rz = face_road + rng.uniform(-0.15, 0.15)
        _put(lib["huts"][i % len(lib["huts"])], f"S35Hut{i}", coll, x, y, rz, rng.uniform(0.95, 1.1), sink=0.1)
        out.append((x, y, 5.5))
        for p in range(5):
            a = rng.uniform(0, TAU)
            r = rng.uniform(2.8, 4.0)
            px, py = x + r * math.cos(a), y + r * math.sin(a)
            if road_dist(px, py) < 0.8:
                continue
            _put(rng.choice((lib["crate"], lib["sack"], lib["pot"], lib["basket"], lib["barrel"])),
                 f"S35Prop{i}_{p}", coll, px, py, rng.uniform(0, TAU), rng.uniform(0.85, 1.1), sink=0.02)
        bx, by = x + 3.8 * math.cos(rz + 0.9), y + 3.8 * math.sin(rz + 0.9)
        _put(lib["bananas"][i % 3], f"S35Banana{i}", coll, bx, by, rng.uniform(0, TAU), rng.uniform(0.9, 1.2))
        fx, fy = x - 4.2 * math.cos(rz), y - 4.2 * math.sin(rz)
        _put(lib["fence"], f"S35Fence{i}", coll, fx, fy, rz, 1.0, sink=0.02)
    sp = Spacer(5.0)
    for x, y, r in out:
        sp.add(x, y, 4.0)
    k = 0
    for i in range(1500):                                  # the palm grove behind and between the huts
        ly = rng.uniform(-190, -48)
        lx = se_road_x(ly) + rng.uniform(4.5, 48.0)
        x, y = lx + PAL[0], ly + PAL[1]
        if road_dist(x, y) < 1.5 or not sp.free(x, y, 2.2):
            continue
        sp.add(x, y, 2.2)
        _put(rng.choice(lib["palms"]) if rng.random() < 0.8 else rng.choice(lib["trees"]), f"S35Palm{k}", coll, x, y,
             rng.uniform(0, TAU), rng.uniform(0.9, 1.25), sink=0.2)
        k += 1
        if k > 150:
            break
    for i in range(120):
        ly = rng.uniform(-190, -48)
        lx = se_road_x(ly) + rng.uniform(3.5, 40.0)
        x, y = lx + PAL[0], ly + PAL[1]
        if road_dist(x, y) < 1.0 or any(math.hypot(x - a, y - b) < 3.5 for a, b, _ in out):
            continue
        _put(rng.choice(lib["bigleaf"] + lib["bushes"]), f"S35Leaf{i}", coll, x, y, rng.uniform(0, TAU),
             rng.uniform(0.8, 1.5))
    # villagers by their huts, watching the column go by
    for i, ly in enumerate((-66.0, -80.0, -93.0, -108.0, -123.0, -139.0, -152.0)):
        lx = se_road_x(ly) + rng.uniform(4.0, 5.5)
        x, y = lx + PAL[0], ly + PAL[1]
        ob = _put(lib["villagers"][i % 4], f"S35Onlooker{i}", coll, x, y, face_road + rng.uniform(-0.4, 0.4), 1.0,
                  sink=0.0)
        kit.animate_idle(ob, rng, 1, frames, 0.03)
    return out


def _build_farmers(coll, lib, frames, rng):
    """People at work in the paddies, near the S35 road and scattered across the band."""
    k = 0
    for c in _CELLS:
        near = math.hypot(c[0] - (PAL[0] + 50), c[1] - (PAL[1] - 120)) < 90
        if rng.random() > (0.5 if near else 0.07):
            continue
        for j in range(rng.randint(1, 3)):
            u, v = rng.uniform(-0.35, 0.35) * c[3], rng.uniform(-0.35, 0.35) * c[4]
            cr, sr = math.cos(c[2]), math.sin(c[2])
            x, y = c[0] + u * cr - v * sr, c[1] + u * sr + v * cr
            ob = kit.instance(lib["villagers"][k % 4], f"Farmer{k}", coll, (x, y, c[5]), rot_z=rng.uniform(0, TAU))
            kit.animate_idle(ob, rng, 1, frames, 0.05)
            k += 1
    return k


def _polyline_at(pts, s):
    """Point and unit direction at arc length s along a polyline (extended at both ends)."""
    n = len(pts) - 1
    for i in range(n):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        L = (b - a).length
        d = (b - a) / L
        if s <= L or i == n - 1:
            return a + d * s, d
        s -= L


def build_column(coll, lib, ev):
    """S35: the Dutch column with its allies, marching down the palace's south-east road toward
    Kottar, past the palace: an orange flag in front, Dutch in blue, the rajas' men behind, more
    Dutch at the rear. Hidden outside S35."""
    rng = random.Random(35)
    pts = [(p[0] + PAL[0], p[1] + PAL[1]) for p in palw.ROADS[3][0]] + R_KOTTAR[0][1:3]
    verts = []
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        acc += math.dist(a, b)
        verts.append(acc)
    f0, f1 = ev["s35"]
    speed = 1.15
    s_front0 = ev.get("col_front", 52.0)
    files = (-1.25, 0.0, 1.25)
    ranks = [[("flag", 0.0)], [("officer", 0.0)]] + [[("dutch", f) for f in files]] * 8 +             [[("ally", f) for f in files]] * 9 + [[("dutch", f) for f in files]] * 5
    roster = [(r, kind, lat) for r, rk in enumerate(ranks) for kind, lat in rk]
    roots = []
    for i, (rank, kind, lat) in enumerate(roster):
        s0 = s_front0 - rank * 1.45 - rng.uniform(0, 0.3)
        lat += rng.uniform(-0.15, 0.15)
        if kind == "flag":
            tmpl = lib["w_ally"][0]
        elif kind == "officer":
            tmpl = lib["w_officer"][0]
        elif kind == "dutch":
            tmpl = lib["w_dutch"][i % 3]
        else:
            tmpl = lib["w_ally"][1 + rng.randrange(len(lib["w_ally"]) - 1)]
        root, parts = _walker(tmpl, f"Col{i}", coll)
        # legs broken at the road's bends
        s1 = s0 + speed * (f1 - f0) / kit.FPS
        cuts = [s0] + [v for v in verts if s0 < v < s1] + [s1]
        legs = []
        for a, b in zip(cuts, cuts[1:]):
            pa, da = _polyline_at(pts, a + 0.01)
            pb, _ = _polyline_at(pts, b - 0.01)
            nrm = Vector((-da.y, da.x))
            ta = f0 + round((a - s0) / speed * kit.FPS)
            tb = f0 + round((b - s0) / speed * kit.FPS)
            legs.append((ta, tb, tuple((pa + nrm * lat).xy), tuple((pb + nrm * lat).xy)))
        kit.animate_route(root, parts, legs, ground_a, stride_frames=15, swing=0.42, turn=0,
                          phase=rank * 3 + rng.randint(0, 2))
        roots.append(root)
        if kind == "flag":
            pole = kit.MB()
            pole.seg((0.32, 0.12, 0.6), (0.32, 0.12, 4.4), 0.045, 0.04, "post", sides=6)
            pole.ico(T(0.32, 0.12, 4.48), "brass", r=0.07, sub=1)
            pole.obj("ColFlagPole", coll, parent=root)
            fl = ptw.make_flag("ColFlag", coll, w=1.7, h=1.15, m="flag_o")
            fl.parent = root
            fl.location = (0.35, 0.12, 4.3)
            fl.rotation_euler[2] = math.pi + 0.5
            parts["armR"].rotation_euler = (0.9, 0, 0)
    _show_only(roots, f0, f1)
    return len(roots)


def build_set_a(colls, lib, ev):
    """Everything of set A. ev: real frames (s33, s35 ranges, end)."""
    global PZ
    frames = ev["end"]
    rng = random.Random(33)
    _SEGS[:] = _road_segs()
    PZ = plain_h(*PAL)
    pal_root, houses = _build_palace(colls, lib, frames)
    _plan_paddies(houses)
    _terrain_a(colls["world"])
    _build_paddies(colls["paddies"])
    cw.make_faceted_sea(colls["world"], colls["rig"], frames + 20, (-1500.0, 1500.0, -1000.0, 560.0),
                        lambda x, y: cw.shore_y(x) - y, step=3.0, far_step=15.0,
                        detail_box=(-520.0, 820.0, -330.0, 240.0), name="SeaA")
    _build_village(colls, frames)
    hamlet = _build_s35_hamlet(colls["hamlet"], lib, frames, rng)
    cam_keep = [(x + PAL[0], y + PAL[1], 7.0) for x, y in S35_CAM]
    keep = hamlet + cam_keep + [(x, y, 7.0) for x, y in houses]
    _fit_town(colls, hamlet + cam_keep)
    _build_groves(colls["groves"], lib, keep, rng)
    _build_hamlets(colls["groves"], lib, rng, keep)
    _build_farmers(colls["people"], lib, frames, rng)
    n = build_column(colls["column"], lib, ev)
    # distant mist over the hills (palace_world's mist boxes), the town and beach stay crisp
    for i, (ctr, size, dens) in enumerate([((60, 1250, 200), (2600, 600, 500), 0.00015)]):
        palw.add_mist_box(colls["world"], f"HillMist{i}", ctr, size, dens)
    print(f"Set A: {len(_CELLS)} paddies, column {n}")
    return pal_root


# ===================================================================== SET B
def hB(x, y):
    """Kalkulam ground (fort-local metres): a flat dusty field before the gate, the fort court,
    a gentle rise into the palm forest and faceted hills behind (north) and to the east."""
    r = math.hypot(max(0.0, abs(x - 30.0) - 95.0), max(0.0, -100.0 - y, y - 110.0))
    h = 0.12 * _n(x, y, 9.0, 2.2) + min(1.0, r / 40.0) * (1.6 + 1.2 * _n(x, y, 30.0, 1.4))
    m = max(_smooth(115.0, 270.0, y), _smooth(170.0, 330.0, abs(x - 30.0)) * _smooth(-60.0, 120.0, y))
    if m > 0:
        ridge = (1.0 - abs(_n(x, y, 110.0, 4.4))) ** 2
        h += m * (14.0 + 75.0 * ridge + 20.0 * _n(x, y, 45.0, 2.7))
        h += _smooth(380.0, 700.0, y) * 110.0 * (1.0 - abs(_n(x, y, 200.0, 6.1))) ** 2
    return max(-0.2, h)


def gB(x, y):
    """Set B height at WORLD x, y."""
    return hB(x - FO[0], y - FO[1])


ROAD_B = [(-12.0, -26.0), (-38.0, -8.0), (-55.0, 30.0), (-62.0, 90.0), (-76.0, 170.0), (-104.0, 290.0)]
FORT_X = (-9.0, 80.0)              # the left gate tower is the fort's front-left corner (K44)
FORT_Y = (0.0, 75.0)
WALL_HB, TOWER_HB = 8.0, 10.5
LANE = [(-34.0, -19.0), (-4.0, -11.5)]             # the elephant's way through the crowd to the gate
STOP = (-4.0, -11.5)


FIELD_TENTS = [(10.0, -44.0, -0.4, "canopy"), (20.0, -36.0, -0.3, "ridge"), (-62.0, -40.0, 1.2, "cone"),
               (-64.0, -24.0, 1.4, "ridge"), (-44.0, 8.0, 0.8, "ridge"), (-30.0, -52.0, 0.2, "cone"),
               (24.0, -52.0, -0.5, "cone")]


def road_b(x, y):
    return min(_seg_dist(x, y, a, b) for a, b in zip(ROAD_B, ROAD_B[1:])) - 4.5


def _terrain_b(coll):
    xs = _axis([(-420, -130, 10), (-130, 130, 2.0), (130, 420, 10)])
    ys = _axis([(-320, -120, 10), (-120, 120, 2.0), (120, 760, 12)])
    xs = [x + FO[0] for x in xs]
    ys = [y + FO[1] for y in ys]
    mats = ["field_dirt", "field_dirt_dk", "court", "road", "grass", "grass_lt", "leaf", "ghat_lo", "ghat_hi", "sand"]

    def mat_fn(x, y, z, nz, rng):
        x, y = x - FO[0], y - FO[1]
        if FORT_X[0] < x < FORT_X[1] and FORT_Y[0] < y < FORT_Y[1]:
            return "court"
        if z > 6.0:
            k = _n(x, y, 40.0, 2.2) + rng.uniform(-0.2, 0.2)
            return "leaf" if k < -0.2 else ("ghat_lo" if k < 0.2 else "ghat_hi")
        if road_b(x, y) < 0.4 * _n(x, y, 3.0, 1.0):
            return "road"
        if -95 < x < 60 and -110 < y < 0 and _open_b(x, y) < 6.0:
            k = _n(x, y, 12.0, 6.1) + rng.uniform(-0.12, 0.12)
            return "field_dirt" if k < 0.1 else ("field_dirt_dk" if k < 0.45 else "sand")
        return "grass" if rng.random() > 0.3 else "grass_lt"
    return _heightfield(coll, "TerrainB", xs, ys, gB, mat_fn, mats, seed=5)


def _open_b(x, y):
    """Distance outside the open gathering ground in front of the gate (fort-local)."""
    dx = max(0.0, -92.0 - x, x - 52.0 - 0.15 * (y + 50))
    dy = max(0.0, -108.0 - y, y + 1.0)
    return math.hypot(dx, dy)


def _merlons(mb, p0, p1, z, out, rng, m="laterite"):
    """Crenellations along the outer edge of a wall top from p0 to p1 (outward normal out)."""
    p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
    d = p1 - p0
    L = d.length
    d.normalize()
    out = Vector((*out, 0)).normalized()
    n = max(1, int(L / 1.9))
    for i in range(n + 1):
        c = p0 + d * (L * i / n) + out * 0.0
        F = kit.frame_matrix(c + UP * (z + 0.5), d, out, UP)
        mb.box(F @ S(1.05, 0.55, 1.0), rng.choice((m, m, "laterite_lt", "laterite_dk")))
        mb.box(F @ T(0, 0, 0.53) @ S(1.15, 0.65, 0.08), "laterite_dk")


def _tower(coll, name, cx, cy, a, h, rng):
    """Square laterite bastion (palace_world block courses), slab top with merlons all round."""
    q = a / 2
    segs = [((cx - q, cy - q), (cx + q, cy - q)), ((cx + q, cy - q), (cx + q, cy + q)),
            ((cx + q, cy + q), (cx - q, cy + q)), ((cx - q, cy + q), (cx - q, cy - q))]
    ob = palw.make_laterite_wall(name, coll, segs, h=h, t=1.4, seed=rng.randint(0, 999))
    mb = kit.MB()
    mb.box(T(cx, cy, h - 0.2) @ S(a, a, 0.4), "laterite_dk")
    mb.box(T(cx, cy, h * 0.5) @ S(a - 1.0, a - 1.0, h), "laterite_dk")
    mb.box(T(cx, cy, h * 0.55) @ S(a + 0.5, a + 0.5, 0.35), "laterite_dk")     # string course
    for (p0, p1), out in zip(segs, ((0, -1), (1, 0), (0, 1), (-1, 0))):
        _merlons(mb, (p0[0] + out[0] * 0.45, p0[1] + out[1] * 0.45), (p1[0] + out[0] * 0.45, p1[1] + out[1] * 0.45),
                 h + 0.18, out, rng)
    mb.obj(name + "Top", coll)
    return ob


def _gate(coll, rng):
    """The gate block between the two gate towers: laterite piers and a high lintel wall, a
    carved stone frame (K44), open teak doors, and a dark passage."""
    for i, (p0, p1) in enumerate((((-6.0, 0.0), (-2.5, 0.0)), ((2.5, 0.0), (6.0, 0.0)))):
        palw.make_laterite_wall(f"GatePier{i}", coll, [(p0, p1)], h=10.0, t=3.0, seed=11 + i)
    top = palw.make_laterite_wall("GateLintel", coll, [((-2.5, 0.0), (2.5, 0.0))], h=4.0, t=3.0, seed=13)
    top.location.z = 6.0
    mb = kit.MB(bevel=0.02)
    fy = -1.62
    for (w, h, z0, m, t) in ((8.6, 9.0, 0.0, "plaster_y", 0.3), (7.4, 7.9, 0.0, "laterite_lt", 0.22),
                             (6.2, 6.9, 0.0, "plaster_y", 0.16)):
        mb.box(T(-w / 2 + 0.3, fy - t / 2, z0 + h / 2) @ S(0.6, t, h), m)
        mb.box(T(w / 2 - 0.3, fy - t / 2, z0 + h / 2) @ S(0.6, t, h), m)
        mb.box(T(0, fy - t / 2, z0 + h - 0.3) @ S(w, t, 0.6), m)
    for k in range(13):                                         # carved rosettes round the frame
        a = k / 12.0
        for x, z in ((-3.75, 0.6 + a * 7.6), (3.75, 0.6 + a * 7.6), (-3.75 + a * 7.5, 8.1)):
            mb.ico(T(x, fy - 0.32, z) @ S(1, 0.5, 1), "granite", r=0.13, sub=1)
    mb.box(T(0, 0.6, 2.8) @ S(4.6, 3.6, 5.6), "dark")                                   # passage shadow
    for sx in (-1, 1):                                                                  # door leaves, open
        hinge = Vector((sx * 2.4, -1.0, 0))
        M = T(hinge) @ Rz(sx * 1.35) @ T(-sx * 1.2, 0, 2.8)
        mb.box(M @ S(2.4, 0.16, 5.5), "teak")
        for j in range(5):
            mb.box(M @ T(0, -0.1, -2.2 + j * 1.1) @ S(2.3, 0.06, 0.12), "teak_dk")
        for j in range(4):
            for q in range(3):
                mb.ico(M @ T(-0.8 + q * 0.8, -0.12, -1.65 + j * 1.1), "brass", r=0.07, sub=1)
    mb.obj("GateFrame", coll)
    m2 = kit.MB()
    _merlons(m2, (-6.0, -1.6), (6.0, -1.6), 10.0, (0, -1), rng)
    m2.obj("GateMerlons", coll)


def build_fort(coll, lib, rng):
    """Kalkulam fort: laterite curtain walls with merlons, square towers, the gate (fort-local
    coordinates, built at the origin and moved to FO)."""
    x0, x1 = FORT_X
    y0, y1 = FORT_Y
    walls = [(((9.5, y0), (x1, y0)), (0, -1)), (((x1, y0), (x1, y1)), (1, 0)),
             (((x1, y1), (x0, y1)), (0, 1)), (((x0, y1), (x0, y0)), (-1, 0))]
    obs = []
    for i, (seg, out) in enumerate(walls):
        obs.append(palw.make_laterite_wall(f"FortWall{i}", coll, [seg], h=WALL_HB, t=2.4, seed=30 + i))
        mb = kit.MB()
        (ax, ay), (bx, by) = seg
        _merlons(mb, (ax + out[0] * 0.95, ay + out[1] * 0.95), (bx + out[0] * 0.95, by + out[1] * 0.95),
                 WALL_HB + 0.18, out, rng)
        mb.box(T((ax + bx) / 2, (ay + by) / 2, WALL_HB + 0.1) @ S(abs(bx - ax) + 2.4, abs(by - ay) + 2.4, 0.2),
               "laterite_dk")
        obs.append(mb.obj(f"FortWallTop{i}", coll))
    for i, (cx, cy, a) in enumerate([(-9.0, -1.0, 7.5), (9.0, -1.0, 7.5), (45.0, 0.0, 8.0), (x1, y0, 9.0),
                                     (x0, 38.0, 8.0), (x0, y1, 9.0), (x1, y1, 9.0), (x1, 38.0, 8.0)]):
        _tower(coll, f"FortTower{i}", cx, cy, a, TOWER_HB + (1.0 if i < 2 else 0.0), rng)
    _gate(coll, rng)


def _place_b(ob, x, y, rz=0.0, z=None, sink=0.0):
    ob.location = (x + FO[0], y + FO[1], (hB(x, y) if z is None else z) - sink)
    ob.rotation_euler[2] = rz
    return ob


def _put_b(src, name, coll, x, y, rz=0.0, s=1.0, sink=0.05):
    return kit.instance(src, name, coll, (x + FO[0], y + FO[1], hB(x, y) - sink), rot_z=rz, scale=s)


def build_fort_court(coll, lib, frames, rng):
    """Inside the fort: tents, a canopy, tiled sheds, stacks of supplies and guards; banners on
    the towers."""
    shed = palw.make_house("LibFortShed", bpy.data.collections["Library"], w=12.0, d=5.5, seed=71, veranda=True,
                           gable=0.0, wall="plaster_g")
    cone = kit.make_cone_tent("LibFortCone", bpy.data.collections["Library"], r=2.0, h=3.2)
    ridge = kit.make_ridge_tent("LibFortRidge", bpy.data.collections["Library"])
    canopy = kit.make_canopy("LibFortCanopy", bpy.data.collections["Library"])
    for i, (x, y, rz) in enumerate([(26.0, 16.0, 0.0), (50.0, 18.0, 0.0), (68.0, 40.0, math.pi / 2), (12.0, 58.0, math.pi),
                                    (40.0, 62.0, math.pi)]):
        _put_b(shed, f"FortShed{i}", coll, x, y, rz, 1.0, sink=0.1)
    for i in range(26):
        x, y = rng.uniform(-3, 75), rng.uniform(7, 70)
        if abs(x) < 7 and y < 20:
            continue
        _put_b(rng.choice((cone, ridge, ridge)), f"FortTent{i}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.9, 1.1))
    _put_b(canopy, "FortCanopy", coll, 6.0, 12.0, 0.0)
    for i in range(40):
        x, y = rng.uniform(-3, 76), rng.uniform(6, 72)
        _put_b(rng.choice((lib["crate"], lib["barrel"], lib["sack"])), f"FortProp{i}", coll, x, y,
               rng.uniform(0, TAU), rng.uniform(0.9, 1.2), sink=0.02)
    for i in range(40):
        x, y = rng.uniform(-3, 76), rng.uniform(6, 72)
        ob = _put_b(lib["guard"], f"FortMan{i}", coll, x, y, rng.uniform(0, TAU), 1.0, sink=0.0)
        kit.animate_idle(ob, rng, 1, frames, 0.03)
    for i, (x, y, z) in enumerate([(-9, -1, TOWER_HB + 1), (9, -1, TOWER_HB + 1), (45, 0, TOWER_HB), (80, 0, TOWER_HB),
                                   (-9, 38, TOWER_HB), (-9, 75, TOWER_HB), (80, 38, TOWER_HB)]):
        ptw.flag_on_pole(coll, f"TowerFlag{i}", (x + FO[0], y + FO[1], z), 3.6, 1.6, 1.0, m="red",
                         heading=200.0 + rng.uniform(-10, 10))


# ----------------------------------------------------------- the crowd (GN)
def crowd_node_group(name, lib_coll, cheer_frame, sway=0.035, bob=0.12):
    """Geometry nodes: instance the figures of lib_coll on points (attribute 'variant' picks the
    figure, 'rz' its heading, 'phase' de-syncs it). Everyone sways a little; after cheer_frame
    they stamp (rhythmic bob)."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput")
    go = N.new("NodeGroupOutput")

    def attr(nm, dt="FLOAT"):
        a = N.new("GeometryNodeInputNamedAttribute")
        a.data_type = dt
        a.inputs["Name"].default_value = nm
        return a.outputs["Attribute"]

    def math_node(op, a, b=None, c=None):
        m = N.new("ShaderNodeMath")
        m.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                L.new(v, m.inputs[i])
        return m.outputs[0]
    t = N.new("GeometryNodeInputSceneTime")
    phase = attr("phase")
    tp = math_node("ADD", math_node("MULTIPLY", t.outputs["Seconds"], 1.3), phase)
    sw_z = math_node("MULTIPLY", math_node("SINE", tp), sway * 2.0)
    sw_x = math_node("MULTIPLY", math_node("SINE", math_node("ADD", math_node("MULTIPLY", tp, 0.7), 1.1)), sway)
    rz = math_node("ADD", attr("rz"), sw_z)
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(sw_x, comb.inputs["X"])
    L.new(rz, comb.inputs["Z"])
    e2r = N.new("FunctionNodeEulerToRotation")
    L.new(comb.outputs[0], e2r.inputs[0])
    # stamping after cheer_frame: |sin| bob, eased in over a second
    on = math_node("MINIMUM", math_node("MAXIMUM", math_node("DIVIDE", math_node("SUBTRACT", t.outputs["Frame"],
                                                                                   cheer_frame), 24.0), 0.0), 1.0)
    st = math_node("ABSOLUTE", math_node("SINE", math_node("ADD", math_node("MULTIPLY", t.outputs["Seconds"], 5.5),
                                                           math_node("MULTIPLY", phase, 2.0))))
    lift = math_node("MULTIPLY", math_node("MULTIPLY", st, on), bob)
    off = N.new("ShaderNodeCombineXYZ")
    L.new(lift, off.inputs["Z"])
    setp = N.new("GeometryNodeSetPosition")
    L.new(gi.outputs[0], setp.inputs["Geometry"])
    L.new(off.outputs[0], setp.inputs["Offset"])
    ci = N.new("GeometryNodeCollectionInfo")
    ci.inputs["Collection"].default_value = lib_coll
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = N.new("GeometryNodeInstanceOnPoints")
    L.new(setp.outputs[0], iop.inputs["Points"])
    L.new(ci.outputs[0], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    L.new(attr("variant", "INT"), iop.inputs["Instance Index"])
    L.new(e2r.outputs[0], iop.inputs["Rotation"])
    L.new(iop.outputs[0], go.inputs[0])
    return ng


def gn_crowd(name, coll, ng, pts):
    """pts: [(x, y, z, rz, variant, phase)] in world space -> one point-cloud object."""
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pts))
    me.vertices.foreach_set("co", [c for p in pts for c in p[:3]])
    for nm, dt, idx in (("rz", "FLOAT", 3), ("variant", "INT", 4), ("phase", "FLOAT", 5)):
        a = me.attributes.new(nm, dt, "POINT")
        a.data.foreach_set("value", [p[idx] for p in pts])
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    mod = ob.modifiers.new(name, "NODES")
    mod.node_group = ng
    return ob


def build_crowd_b(coll, lib_c, ev, rng):
    """About two thousand Nairs gathered before the gate in loose companies facing the gate
    and the king, a lane kept for the elephant, columns standing on the road behind."""
    cl = kit.new_collection("CrowdLibB")
    kinds = [("nair", "stand", 0), ("nair", "stand", 1), ("nair", "sword_up", 2), ("nair_spear", "stand", 3),
             ("nair_spear", "stand", 4), ("nair", "stand", 5), ("nair_spear", "sword_up", 6), ("nair", "sword_up", 7)]
    for i, (k, pose, seed) in enumerate(kinds):
        ob = kit.make_figure(f"V{i:02d}_{k}_{pose}", cl, k, seed=seed, pose=pose)
        if i in (1, 4, 5):                                       # some carry no shield (K44)
            ob.data = ob.data.copy()
            kit.recolor(ob, strip=("shield", "brass"))
    bpy.context.view_layer.layer_collection.children[cl.name].exclude = True
    ng = crowd_node_group("CrowdB", cl, ev["raise"])
    pts = []
    gx, gy = 1.22, 1.5

    def lane_d(x, y):
        return _seg_dist(x, y, LANE[0], LANE[1])
    y = -66.0
    while y < -6.0:
        x = -80.0
        while x < 30.0:
            px, py = x + rng.uniform(-0.32, 0.32), y + rng.uniform(-0.32, 0.32)
            x += gx
            if _open_b(px, py) > 0 or road_b(px, py) < 1.0 and py > -10:
                continue
            if lane_d(px, py) < 4.2 or math.hypot(px - STOP[0], py - STOP[1]) < 7.5 or \
                    (abs(px) < 7.5 and py > -9.0):
                continue
            if (px + 80) % 31.0 < 1.7 or (py + 66) % 24.0 < 1.6:           # lanes between the companies
                continue
            if any(math.hypot(px - tx, py - ty) < 5.5 for tx, ty, _, _ in FIELD_TENTS):
                continue
            if py < -62 + 6 * _n(px, 0, 25.0, 1.0) or px < -76 + 5 * _n(0, py, 20.0, 2.0) or rng.random() < 0.08:
                continue
            tx, ty = STOP[0] + 2.0, STOP[1] + 1.0
            rz = _face(tx - px, ty - py) + rng.uniform(-0.3, 0.3)
            pts.append((px + FO[0], py + FO[1], hB(px, py), rz, rng.randrange(len(kinds)), rng.uniform(0, TAU)))
        y += gy
    # men standing in column on the road behind the field, heading for the gate
    acc = 0.0
    for a, b in zip(ROAD_B[1:], ROAD_B[2:]):
        a, b = Vector(a), Vector(b)
        L = (b - a).length
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x))
        s = 0.0
        while s < L:
            gap = (acc + s) % 26.0 > 19.0
            if not gap and 22.0 < acc + s < 78.0:
                for f in (-2.85, -1.9, -0.95, 0.0, 0.95, 1.9, 2.85):
                    p = a + d * s + nrm * f + Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1)))
                    pts.append((p.x + FO[0], p.y + FO[1], hB(p.x, p.y), _face(-d.x, -d.y) + rng.uniform(-0.1, 0.1),
                                rng.randrange(len(kinds)), rng.uniform(0, TAU)))
            s += 1.3
        acc += L
    gn_crowd("CrowdB", coll, ng, pts)
    return len(pts)


def build_stream_b(coll, lib, ev, rng):
    """More men streaming in down the road: walking columns that keep coming through S36."""
    f0, f1 = ev["s36"]
    pts = list(reversed(ROAD_B))
    verts = []
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        acc += math.dist(a, b)
        verts.append(acc)
    total = acc
    speed = 1.45
    n = 0
    roots = []
    for rank in range(60):
        s0 = 60.0 + rank * 1.4 + (rank // 12) * 5.0
        s1 = min(total - 10.0 - (rank % 12) * 0.2, s0 + speed * (f1 - f0) / kit.FPS)
        for f in (-1.0, 0.0, 1.0):
            root, parts = _walker(lib["w_nair"][rng.randrange(4)], f"Stream{n}", coll)
            lat = f + rng.uniform(-0.12, 0.12)
            ss0 = s0 + rng.uniform(-0.2, 0.2)
            cuts = [ss0] + [v for v in verts if ss0 < v < s1] + [s1]
            legs = []
            for a, b in zip(cuts, cuts[1:]):
                pa, da = _polyline_at(pts, a + 0.01)
                pb, _ = _polyline_at(pts, b - 0.01)
                nrm = Vector((-da.y, da.x))
                ta = f0 + round((a - ss0) / speed * kit.FPS)
                tb = f0 + round((b - ss0) / speed * kit.FPS)
                legs.append((ta, tb, tuple((pa + nrm * lat).xy + Vector(FO)), tuple((pb + nrm * lat).xy + Vector(FO))))
            kit.animate_route(root, parts, legs, gB, stride_frames=13, swing=0.45, turn=0, phase=rank * 2 + rng.randint(0, 3))
            roots.append(root)
            n += 1
    _show_only(roots, f0, f1)
    return n


def build_banners_b(coll, rng):
    """Red Travancore banners held up among the companies (K44)."""
    k = 0
    for x, y in [(-56, -30), (-46, -48), (-32, -40), (-14, -50), (4, -32), (16, -24), (-24, -22), (-40, -14),
                 (-8, -40), (24, -14), (-52, -12), (-20, -34), (-54, 18), (-58, 50), (-61, 80), (-68, 120),
                 (-36, -54), (2, -54), (-4, -20), (26, -40), (-60, -50), (12, -8)]:
        x += rng.uniform(-2, 2)
        y += rng.uniform(-2, 2)
        ptw.flag_on_pole(coll, f"Banner{k}", (x + FO[0], y + FO[1], hB(x, y)), 5.2, 1.3, 1.6, m="red",
                         heading=rng.uniform(150, 230), r=0.06)
        k += 1


def build_surround_b(coll, lib, rng):
    """Palm forest round the field, a strip between the road and the west wall, tents and
    canopies at the field edge, rocks, undergrowth; jungle on the hills."""
    cone = bpy.data.objects["LibFortCone"]
    ridge = bpy.data.objects["LibFortRidge"]
    canopy = bpy.data.objects["LibFortCanopy"]
    for i, (x, y, rz, kind) in enumerate(FIELD_TENTS):
        _put_b({"cone": cone, "ridge": ridge, "canopy": canopy}[kind], f"FieldTent{i}", coll, x, y, rz)
        for j in range(3):
            a = rng.uniform(0, TAU)
            _put_b(rng.choice((lib["crate"], lib["sack"], lib["barrel"], lib["pot"])), f"FieldTentProp{i}_{j}", coll,
                   x + 3.0 * math.cos(a), y + 3.0 * math.sin(a), rng.uniform(0, TAU), 1.0, sink=0.02)
    sp = Spacer(6.0)
    k = 0
    for i in range(40000):
        x, y = rng.uniform(-260, 280), rng.uniform(-220, 420)
        if _open_b(x, y) < 3.0 or road_b(x, y) < 1.5:
            continue
        if FORT_X[0] - 4 < x < FORT_X[1] + 4 and FORT_Y[0] - 4 < y < FORT_Y[1] + 4:
            continue
        h = hB(x, y)
        strip = -48.0 < x < FORT_X[0] - 3 and -6.0 < y < FORT_Y[1] + 10       # between the road and the west wall
        if strip and rng.random() < 0.45:
            continue
        far = max(0.0, abs(x - 20) - 140) + max(0.0, y - 160) + max(0.0, -150 - y)
        if far > 0 and rng.random() < 0.55:
            continue
        r = 2.3 if far == 0 else 3.8
        if not sp.free(x, y, r):
            continue
        sp.add(x, y, r)
        if h > 18 or (rng.random() < 0.22 and not strip):
            src, s = rng.choice(lib["trees"] + lib["jtrees"]), rng.uniform(0.9, 1.4)
        else:
            src, s = rng.choice(lib["palms"]), rng.uniform(0.9, 1.3)
        _put_b(src, f"BPlant{k}", coll, x, y, rng.uniform(0, TAU), s, sink=0.2)
        k += 1
        if k > 3200:
            break
    j = 0
    for i in range(12000):
        x, y = rng.uniform(-140, 120), rng.uniform(-150, 140)
        if _open_b(x, y) < 1.0 or road_b(x, y) < 0.5 or (FORT_X[0] - 3 < x < FORT_X[1] + 3 and FORT_Y[0] - 3 < y < FORT_Y[1] + 3):
            continue
        _put_b(rng.choice(lib["bushes"] + lib["bigleaf"] + lib["bigleaf"]), f"BUnder{j}", coll, x, y,
               rng.uniform(0, TAU), rng.uniform(0.8, 1.6))
        j += 1
        if j > 1600:
            break
    for i in range(20):
        x, y = rng.uniform(-95, 55), rng.uniform(-110, -2)
        if _open_b(x, y) > -2.0 and _open_b(x, y) < 3:
            _put_b(lib["rocks"][i % 3], f"BRock{i}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.6, 1.2), sink=0.15)


def build_elephant_b(coll, lib, ev, rng):
    """The royal elephant with the king in the howdah comes through the lane to the gate,
    stops and turns to face the gathering."""
    root, parts = kit.make_elephant("RoyalElephant", coll, seed=4)
    king = kit.make_figure("KingOnElephant", coll, "king", seed=1, pose="sit")
    king.parent = parts["seat"]
    kit.animate_rig_idle({"body": king}, rng, 1, ev["end"], body=0.02)
    f0 = ev["s36"][0]
    arrive = ev["arrive"]
    a = (LANE[0][0] - 9.0, LANE[0][1] - 2.4)
    b = STOP
    legs = [(f0, arrive, (a[0] + FO[0], a[1] + FO[1]), (b[0] + FO[0], b[1] + FO[1])),
            (arrive + 14, arrive + 60, (b[0] + FO[0], b[1] + FO[1]), (b[0] + FO[0] - 0.6, b[1] + FO[1] - 0.25))]
    kit.animate_elephant(root, parts, legs, gB, stride_frames=26, swing=0.26, end=ev["s36"][1])
    _show_only([root], f0, ev["s36"][1])
    # guards flanking the stop, attendants at the gate
    for i, (x, y) in enumerate([(-9.5, -7.0), (-9.0, -15.5), (1.5, -6.8), (2.5, -15.8), (-2.0, -4.5), (3.6, -4.2)]):
        ob = _put_b(lib["guard"], f"GateGuard{i}", coll, x, y, _face(STOP[0] - x, STOP[1] - y), 1.0, sink=0.0)
        kit.animate_idle(ob, rng, 1, ev["end"], 0.025)
    return root


def build_set_b(colls, lib, ev):
    rng = random.Random(36)
    _terrain_b(colls["world"])
    fort_c = colls["fort"]
    build_fort(fort_c, lib, rng)
    for ob in fort_c.objects:                                    # the fort was built at the origin
        if ob.parent is None:
            ob.location.x += FO[0]
            ob.location.y += FO[1]
    build_fort_court(fort_c, lib, ev["end"], rng)
    n = build_crowd_b(colls["crowd"], colls["lib"], ev, rng)
    s = build_stream_b(colls["crowd"], lib, ev, rng)
    build_banners_b(colls["crowd"], rng)
    build_surround_b(colls["plantsB"], lib, rng)
    build_elephant_b(colls["crowd"], lib, ev, rng)
    haze = cw.add_haze(colls["rig"], density=0.0003)
    haze.location = (FO[0] + 100.0, FO[1] + 100.0, 0.0)
    palw.add_mist_box(colls["world"], "HillMistB", (FO[0] + 20, FO[1] + 560, 120), (1200, 500, 300), 0.0022)
    print(f"Set B: crowd {n} + {s} streaming")


# ===================================================================== SET C
SHRINE = (-6.0, 4.5)            # temple-local centre of the shrine
SHR_W = 5.8                      # shrine wall width
PLINTH_H = 1.05
GOPURAM = (2.5, 13.5)
MAST = (4.5, -1.8)
CORR = (8.0, 36.0, 1.5, 8.5)    # colonnade x0, x1, y0, y1


def hC(x, y):
    """Thiruvattar ground (temple-local): the flagged court at 0, ground outside a little lower,
    rising gently into the grove behind."""
    if -20.0 < x < 38.0 and -26.0 < y < 34.0:
        return -0.3                                              # under the flagstones
    r = math.hypot(max(0.0, -20.0 - x, x - 38.0), max(0.0, -26.0 - y, y - 34.0))
    return -0.35 + 0.25 * _n(x, y, 8.0, 3.0) + _smooth(10.0, 120.0, r) * 6.0 * (1 + _n(x, y, 40.0, 1.7))


def gC(x, y):
    return hC(x - TO[0], y - TO[1])


def _stone_blocks(mb, rng, x0, x1, z0, z1, y, out, course=0.55, mats=("temple_st", "temple_st", "temple_st_lt",
                                                                        "temple_st_dk")):
    """Ashlar facing: rows of granite blocks standing proud of a wall face along X at y."""
    row = 0
    z = z0
    while z < z1 - 0.05:
        h = min(course, z1 - z)
        a = x0 + (row % 2) * 0.45
        while a < x1 - 0.05:
            bl = rng.uniform(0.9, 1.5)
            a0, a1 = max(a, x0), min(a + bl, x1)
            if a1 - a0 > 0.12:
                mb.box(T((a0 + a1) / 2, y + out * 0.02, z + h / 2) @ S(a1 - a0 - 0.05, 0.06, h - 0.05), rng.choice(mats))
            a += bl
        z += course
        row += 1


def _clay_lamp(lib_c):
    """Small clay oil lamp (vilakku) with a glowing flame."""
    kit.mat_emit("diya_flame", (1.0, 0.58, 0.16), strength=5.0)
    mb = kit.MB()
    mb.cone(T(0, 0, 0.035), "clay", segments=7, r1=0.07, r2=0.1, depth=0.07)
    mb.cone(T(0.085, 0, 0.07) @ Ry(math.pi / 2), "clay", segments=4, r1=0.025, r2=0.01, depth=0.05)
    mb.cone(T(0.09, 0, 0.13), "diya_flame", segments=5, r1=0.028, r2=0.0, depth=0.1)
    ob = mb.obj("LibClayLamp", lib_c)
    ob.data.transform(S(1.25, 1.25, 1.25))
    return ob


def _lamp_row(coll, lamp, p0, p1, z, step, rng, name, flicker=None):
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    n = max(1, int(L / step))
    out = []
    for i in range(n + 1):
        p = p0 + (p1 - p0) * (i / n)
        ob = kit.instance(lamp, f"{name}{i}", coll, (p.x + TO[0], p.y + TO[1], z), rot_z=rng.uniform(0, TAU))
        out.append(ob)
        if flicker and rng.random() < 0.35:
            kit.animate_flicker(ob, rng, flicker[0], flicker[1], amount=0.18, every=(4, 9))
    return out


def make_shrine(coll, rng):
    """Kerala sreekovil: moulded granite plinth, ashlar walls with pilasters, a dark doorway with
    a lamp glowing inside, front steps with side balustrades, a hip-and-gable roof of stone tiles
    (palace_world roof) with its carved gable to the front, and a finial."""
    cx, cy = SHRINE
    w = SHR_W
    mb = kit.MB(bevel=0.02)
    for i, (dw, z0, z1, m) in enumerate(((1.6, 0.0, 0.32, "temple_st_dk"), (1.2, 0.32, 0.55, "temple_st"),
                                         (1.45, 0.55, 0.75, "temple_st_lt"), (1.15, 0.75, PLINTH_H, "temple_st"))):
        mb.box(T(cx, cy, (z0 + z1) / 2) @ S(w + dw, w + dw, z1 - z0), m)
    zt = PLINTH_H + 3.0
    mb.box(T(cx, cy, (PLINTH_H + zt) / 2) @ S(w, w, zt - PLINTH_H), "temple_st_dk")
    for side, (out, axis) in enumerate((((0, -1), "x"), ((1, 0), "y"), ((0, 1), "x"), ((-1, 0), "y"))):
        sub = kit.MB()
        _stone_blocks(sub, rng, -w / 2, w / 2, PLINTH_H, zt, w / 2, 1)
        for k in range(5):                                       # pilasters
            px = -w / 2 + 0.25 + k * (w - 0.5) / 4
            if side == 0 and abs(px) < 1.0:
                continue
            sub.box(T(px, w / 2 + 0.1, (PLINTH_H + zt) / 2) @ S(0.32, 0.14, zt - PLINTH_H), "temple_st_lt")
        a = math.atan2(out[1], out[0]) - math.pi / 2
        sub.bm.transform(T(cx, cy, 0) @ Rz(a))
        sub.obj(f"ShrineWall{side}", coll)
    mb.box(T(cx, cy - w / 2 - 0.09, PLINTH_H + 1.15) @ S(1.25, 0.04, 2.3), "dark")                # doorway
    for sx in (-1, 1):
        mb.box(T(cx + sx * 0.75, cy - w / 2 - 0.08, PLINTH_H + 1.2) @ S(0.22, 0.18, 2.5), "temple_st_lt")
    mb.box(T(cx, cy - w / 2 - 0.08, PLINTH_H + 2.5) @ S(1.75, 0.2, 0.22), "temple_st_lt")
    kit.mat_emit("lamp_flame", (1.0, 0.72, 0.28), strength=12.0)
    mb.ico(T(cx, cy - w / 2 + 0.3, PLINTH_H + 0.9) @ S(0.06, 0.06, 0.12), "lamp_flame", r=1.0, sub=1)
    mb.box(T(cx, cy, zt + 0.12) @ S(w + 0.5, w + 0.5, 0.24), "temple_st_lt")                       # cornice
    # front steps down to the court, with side balustrades
    n = 4
    for k in range(n):
        h = PLINTH_H * (n - k) / n
        mb.box(T(cx, cy - w / 2 - 0.8 - 0.36 * k, h / 2) @ S(2.2, 0.36 + 0.02, h), "temple_st" if k % 2 else "temple_st_lt")
    for sx in (-1, 1):                                         # stepped side walls of the stair
        for k in range(n):
            h = PLINTH_H * (n - k) / n + 0.18
            mb.box(T(cx + sx * 1.28, cy - w / 2 - 0.8 - 0.36 * k, h / 2) @ S(0.34, 0.38, h),
                   "temple_st_dk" if k % 2 else "temple_st")
    ob = mb.obj("Shrine", coll)
    # roof: palace_world's hip-and-gable roof in stone tiles, turned so the gable faces the court
    rm = kit.MB()
    stone_tiles = dict(mats=(("temple_tile", 0.45), ("temple_st", 0.3), ("temple_st_dk", 0.25)), tw=0.5, tl=0.56,
                       step=0.43)
    zr = palw.roof_hipgable(rm, rng, 0, 0, zt + 0.2, w / 2 + 1.0, w / 2 + 1.0, 40.0, gable=0.45, ext=0.35,
                            tile=stone_tiles, carve=True)
    rm.cone(T(0, 0, zr + 0.25), "gold", segments=8, r1=0.18, r2=0.05, depth=0.5)
    rm.ico(T(0, 0, zr + 0.6), "gold", r=0.12, sub=1)
    rm.bm.transform(T(cx, cy, 0) @ Rz(math.pi / 2))
    roof = rm.obj("ShrineRoof", coll)
    kit.recolor(roof, {"tile_dk": "temple_st_dk", "tile_under": "dark", "teak": "temple_st_dk", "teak_dk": "dark",
                       "teak_lt": "temple_st", "brass": "gold"})
    return ob


def make_gopuram(coll, rng):
    """Gateway tower: a granite base storey with a dark doorway, four receding tiers with
    cornices, niches and corner pavilions, a barrel-vaulted crown and a row of finials."""
    gx, gy = GOPURAM
    W, D = 10.5, 6.8
    mb = kit.MB(bevel=0.02)
    mb.box(T(gx, gy, 0.4) @ S(W + 1.0, D + 1.0, 0.8), "temple_st_dk")
    h0 = 4.6
    mb.box(T(gx, gy, 0.8 + h0 / 2) @ S(W, D, h0), "temple_st")
    for out in (-1, 1):
        sub = kit.MB()
        _stone_blocks(sub, rng, -W / 2, W / 2, 0.8, 0.8 + h0, D / 2, 1)
        for k in range(7):
            sub.box(T(-W / 2 + 0.3 + k * (W - 0.6) / 6, D / 2 + 0.12, 0.8 + h0 / 2) @ S(0.4, 0.16, h0), "temple_st_lt")
        sub.bm.transform(T(gx, gy, 0) @ Rz(0 if out > 0 else math.pi))
        sub.obj(f"GopuramBase{out}", coll)
    for out in (-1, 1):
        mb.box(T(gx, gy + out * (D / 2 + 0.01), 0.8 + 2.2) @ S(2.6, 0.12, 4.4), "dark")
        mb.box(T(gx, gy + out * (D / 2 + 0.1), 0.8 + 4.6) @ S(3.4, 0.3, 0.35), "temple_st_lt")
    z = 0.8 + h0
    w, d = W, D
    for tier in range(3):
        mb.box(T(gx, gy, z + 0.15) @ S(w + 0.8, d + 0.8, 0.3), "temple_st_lt")                     # cornice
        mb.box(T(gx, gy, z + 0.4) @ S(w + 0.4, d + 0.4, 0.2), "temple_st_dk")
        w, d = w * 0.87, d * 0.85
        th = 2.0 - 0.15 * tier
        mb.box(T(gx, gy, z + 0.5 + th / 2) @ S(w, d, th), "temple_st")
        for sy in (-1, 1):
            for k in range(7):                                    # pilasters with recesses between
                px = gx - w / 2 + 0.2 + k * (w - 0.4) / 6
                mb.box(T(px, gy + sy * (d / 2 + 0.08), z + 0.5 + th / 2) @ S(0.3, 0.18, th), "temple_st_lt")
                if k < 6:
                    mb.box(T(px + (w - 0.4) / 12, gy + sy * (d / 2 + 0.01), z + 0.5 + th * 0.5) @
                           S(0.5, 0.06, th * 0.55), "temple_st_dk")
            mb.box(T(gx, gy + sy * (d / 2 + 0.12), z + 0.5 + th * 0.45) @ S(0.9, 0.1, th * 0.62), "dark")
            mb.box(T(gx, gy + sy * (d / 2 + 0.16), z + 0.5 + th * 0.8) @ S(1.3, 0.2, 0.22), "temple_st_lt")
            for k in range(9):                                    # row of small kudu arches on the cornice
                px = gx - w / 2 + 0.5 + k * (w - 1.0) / 8
                mb.cone(T(px, gy + sy * (d / 2 + 0.25), z + 0.42) @ Rx(math.pi / 2), "temple_st_lt", segments=6,
                        r1=0.2, r2=0.2, depth=0.12)
            for sx in (-1, 1):                                    # corner pavilions (kuta)
                cx_, cy_ = gx + sx * (w / 2 - 0.3), gy + sy * (d / 2 - 0.3)
                mb.box(T(cx_, cy_, z + 0.5 + th + 0.25) @ S(0.8, 0.8, 0.5), "temple_st_lt")
                mb.cone(T(cx_, cy_, z + 0.5 + th + 0.7) @ Rz(math.pi / 4), "temple_st", segments=4, r1=0.55,
                        r2=0.05, depth=0.5)
            for k in (-1, 1):                                     # side pavilions with barrel tops
                mb.box(T(gx + k * w * 0.22, gy + sy * (d / 2 - 0.2), z + 0.5 + th + 0.25) @ S(1.1, 0.6, 0.5),
                       "temple_st_lt")
        z += 0.5 + th
    # crown: barrel vault along X with horseshoe gables and finials
    mb.box(T(gx, gy, z + 0.2) @ S(w + 0.6, d + 0.6, 0.4), "temple_st_lt")
    L = w * 0.92
    mb.cone(T(gx, gy, z + 0.4 + 0.9) @ Ry(math.pi / 2) @ S(1.0, 1.25, 1.0), "temple_tile", segments=10, r1=d * 0.42,
            r2=d * 0.42, depth=L)
    for sx in (-1, 1):
        mb.cone(T(gx + sx * L / 2, gy, z + 0.4 + 0.9) @ Ry(math.pi / 2) @ S(1.0, 1.3, 1.0), "temple_st_lt",
                segments=10, r1=d * 0.48, r2=d * 0.48, depth=0.3)
    for sy in (-1, 1):                                            # the big arched window of the crown
        mb.cone(T(gx, gy + sy * d * 0.5, z + 1.6) @ Rx(math.pi / 2), "temple_st_lt", segments=8, r1=1.0, r2=1.0,
                depth=0.3)
        mb.cone(T(gx, gy + sy * (d * 0.5 + 0.08), z + 1.6) @ Rx(math.pi / 2), "dark", segments=8, r1=0.6, r2=0.6,
                depth=0.25)
    for k in range(7):
        fx = gx - L / 2 + 0.5 + k * (L - 1.0) / 6
        zt = z + 0.4 + 0.9 + d * 0.42 * 1.25
        mb.cone(T(fx, gy, zt + 0.2), "gold", segments=8, r1=0.16, r2=0.1, depth=0.3)
        mb.ico(T(fx, gy, zt + 0.48) @ S(1, 1, 1.3), "gold", r=0.16, sub=1)
        mb.cone(T(fx, gy, zt + 0.78), "gold", segments=6, r1=0.06, r2=0.0, depth=0.3)
    return mb.obj("Gopuram", coll)


def _carved_pillar(mb, x, y, z0, h, rng):
    """Granite temple pillar: square base, carved blocks and octagonal bands, bracket capital."""
    mb.box(T(x, y, z0 + 0.2) @ S(0.75, 0.75, 0.4), "temple_st_dk")
    z = z0 + 0.4
    seg = (h - 1.0) / 3
    for k in range(3):
        mb.box(T(x, y, z + seg * 0.5) @ S(0.56, 0.56, seg * 0.62), "temple_st")
        mb.cone(T(x, y, z + seg * 0.88) @ Rz(math.pi / 8), "temple_st_lt", segments=8, r1=0.3, r2=0.3,
                depth=seg * 0.26)
        mb.box(T(x, y, z + seg * 0.5) @ S(0.6, 0.6, 0.08), "temple_st_dk")
        z += seg
    mb.box(T(x, y, z + 0.15) @ S(0.7, 0.7, 0.3), "temple_st_lt")
    mb.box(T(x, y, z + 0.45) @ S(1.25, 0.6, 0.3), "temple_st")                               # bracket
    mb.box(T(x, y, z + 0.52) @ S(0.6, 1.1, 0.16), "temple_st")


def make_corridor(coll, rng):
    """Pillared corridor (K46 right): a high plinth with lamps, two rows of carved pillars, a dark
    back wall, a thick stone roof with a sloping eave."""
    x0, x1, y0, y1 = CORR
    mb = kit.MB(bevel=0.02)
    ph = 0.9
    mb.box(T((x0 + x1) / 2, (y0 + y1) / 2, ph / 2) @ S(x1 - x0, y1 - y0, ph), "temple_st")
    mb.box(T((x0 + x1) / 2, y0 + 0.05, ph - 0.1) @ S(x1 - x0 + 0.2, 0.3, 0.2), "temple_st_lt")
    mb.box(T((x0 + x1) / 2, y0 - 0.25, 0.25) @ S(x1 - x0, 0.6, 0.5), "temple_st_dk")          # step
    sub = kit.MB()
    _stone_blocks(sub, rng, x0, x1, 0.0, ph - 0.2, y0, -1, course=0.35)
    sub.obj("CorridorPlinthBlocks", coll)
    hgt = 3.7
    mb.box(T((x0 + x1) / 2, y1 - 0.35, ph + hgt / 2) @ S(x1 - x0, 0.7, hgt), "temple_st_dk")
    mb.box(T((x0 + x1) / 2, y1 - 0.72, ph + hgt / 2) @ S(x1 - x0 - 0.4, 0.05, hgt - 0.3), "dark")
    n = int((x1 - x0) / 2.6)
    for k in range(n + 1):
        x = x0 + 0.6 + k * (x1 - x0 - 1.2) / n
        _carved_pillar(mb, x, y0 + 0.75, ph, hgt, rng)
        _carved_pillar(mb, x, y0 + 3.6, ph, hgt, rng)
    zt = ph + hgt + 0.6
    mb.box(T((x0 + x1) / 2, (y0 + y1) / 2 + 0.2, zt) @ S(x1 - x0 + 0.4, y1 - y0 + 0.4, 0.45), "temple_st")
    # sloping stone eave over the front
    v = [mb.bm.verts.new(p) for p in ((x0 - 0.3, y0 - 1.0, zt - 0.2), (x1 + 0.3, y0 - 1.0, zt - 0.2),
                                      (x1 + 0.3, y1 + 0.2, zt + 1.4), (x0 - 0.3, y1 + 0.2, zt + 1.4))]
    mb.face(v, "temple_tile")
    mb.box(T((x0 + x1) / 2, y0 - 1.0, zt - 0.3) @ S(x1 - x0 + 0.6, 0.3, 0.25), "temple_st_dk")
    for k in range(int((x1 - x0) / 0.6)):                         # tile ribs down the slope
        x = x0 + 0.3 + k * 0.6
        mb.seg((x, y0 - 0.95, zt - 0.12), (x, y1 + 0.15, zt + 1.48), 0.06, 0.06, "temple_st_dk", sides=4)
    return mb.obj("Corridor", coll)


def make_flagmast(coll):
    """Dhwajastambham: a stepped granite plinth with lamp ledges and a tall gilded mast with
    rings, a capital of three tiers and small bells."""
    mx, my = MAST
    mb = kit.MB(bevel=0.02)
    z = 0.0
    for k, (a, h, m) in enumerate(((3.6, 0.4, "temple_st_dk"), (3.0, 0.36, "temple_st"), (2.4, 0.34, "temple_st_lt"),
                                   (1.5, 0.45, "temple_st"))):
        mb.box(T(mx, my, z + h / 2) @ S(a, a, h), m)
        z += h
    mb.cone(T(mx, my, z + 0.25), "gold", segments=8, r1=0.55, r2=0.32, depth=0.5)               # lotus base
    z += 0.5
    H = 15.5
    mb.seg((mx, my, z), (mx, my, z + H), 0.24, 0.17, "brass", sides=10)
    k = 0
    while k * 0.95 < H - 0.4:
        zz = z + 0.6 + k * 0.95
        r = 0.24 - 0.07 * (zz - z) / H
        mb.cone(T(mx, my, zz), "gold", segments=10, r1=r + 0.05, r2=r + 0.05, depth=0.14)
        k += 1
    zt = z + H
    for j, (a, h) in enumerate(((0.9, 0.2), (0.7, 0.2), (0.5, 0.25))):
        mb.box(T(mx, my, zt + 0.1 + j * 0.3) @ S(a, a, h), "gold")
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.cone(T(mx + sx * a / 2, my + sy * a / 2, zt + j * 0.3 - 0.04), "brass", segments=6, r1=0.06,
                        r2=0.02, depth=0.12)
    mb.cone(T(mx, my, zt + 1.15), "gold", segments=6, r1=0.1, r2=0.0, depth=0.5)
    ob = mb.obj("FlagMast", coll)
    gilt = bpy.data.materials.get("mast_gilt") or kit.mat("mast_gilt", (0.86, 0.60, 0.14), roughness=0.35)
    gilt.node_tree.nodes.get("Principled BSDF").inputs["Metallic"].default_value = 0.5
    ob.data.materials[ob.data.materials.find("brass")] = gilt
    return ob, (z - 0.5)


def make_court(coll, rng):
    """Flagstone court and the walls: big granite slabs with joints, a low wall with a lamp ledge
    on the left, a raised platform in the left foreground, the back wall."""
    mb = kit.MB(bevel=0.015)
    y = -26.0
    while y < 34.0:
        dy = rng.uniform(1.6, 2.6)
        x = -20.0 + rng.uniform(-1.0, 0.0)
        while x < 38.0:
            dx = rng.uniform(1.8, 3.2)
            x0, x1 = max(x, -20.0), min(x + dx, 38.0)
            y0, y1 = y, min(y + dy, 34.0)
            if x1 - x0 > 0.2 and y1 - y0 > 0.2:
                mb.box(T((x0 + x1) / 2, (y0 + y1) / 2, -0.05 + rng.uniform(-0.01, 0.015)) @
                       S(x1 - x0 - 0.06, y1 - y0 - 0.06, 0.12),
                       rng.choice(("temple_st", "temple_st", "temple_st_lt", "temple_st_dk", "temple_tile")))
            x += dx
        y += dy
    mb.box(T(9.0, 4.0, -0.2) @ S(58.2, 60.2, 0.2), "dark")                                  # joints
    mb.obj("Court", coll)
    # left wall (K46): thick ashlar wall with a coping and a lamp ledge in front
    wm = kit.MB(bevel=0.02)
    wm.box(T(-19.0, 4.0, 1.7) @ S(1.6, 60.0, 3.4), "temple_st_dk")
    sub = kit.MB()
    _stone_blocks(sub, rng, -34.0, 26.0, 0.0, 3.4, 0.82, 1, course=0.6)
    sub.bm.transform(T(-19.0, 0, 0) @ Rz(-math.pi / 2))
    sub.obj("LeftWallBlocks", coll)
    wm.box(T(-19.0, 4.0, 3.5) @ S(1.9, 60.2, 0.25), "temple_st_lt")
    wm.box(T(-17.75, 4.0, 0.35) @ S(1.0, 58.0, 0.7), "temple_st")                              # lamp ledge
    # back wall behind the shrine and gopuram, and the right wall
    wm.box(T(9.0, 34.5, 1.6) @ S(58.0, 1.4, 3.2), "temple_st_dk")
    wm.box(T(9.0, 34.5, 3.3) @ S(58.4, 1.7, 0.25), "temple_st_lt")
    wm.box(T(38.5, 4.0, 1.6) @ S(1.4, 60.0, 3.2), "temple_st_dk")
    # raised platform in the left foreground (lamps along its edge)
    wm.box(T(-14.0, -12.0, 0.3) @ S(9.0, 5.0, 0.6), "temple_st")
    wm.box(T(-14.0, -12.0, 0.65) @ S(9.3, 5.3, 0.12), "temple_st_lt")
    return wm.obj("TempleWalls", coll)


def make_kneeling_king(coll, frames, ev, rng):
    """The kit king rig kneeling (the seated legs turned down onto the knees, shins on the floor),
    a waist pivot for the bow, a sword held across both hands that he lays on the step."""
    root, parts = kit.make_rig("TempleKing", coll, "king", seed=1, seated=True)
    waist = bpy.data.objects.new("TempleKing_waist", None)
    coll.objects.link(waist)
    waist.parent = root
    hip_z = kit.SEAT_H + 0.09
    waist.location = (0, 0, hip_z)
    body = parts["body"]
    body.parent = waist
    body.location = (0, 0, kit.RIG_SEAT_DROP - hip_z)
    hips = parts["hips"]
    hips.rotation_euler = (-math.pi / 2, 0, 0)
    hips.location = (0, -hip_z, hip_z)
    parts["waist"] = waist
    # the sword: a curved blade, guard and hilt, along X in the hands
    sm = kit.MB(bevel=0.005)
    for i in range(6):
        sm.box(T(-0.45 + 0.15 * i, 0, 0.012 * (i - 2.5) ** 2 * 0.3) @ Ry(-0.04 * (i - 2.5)) @ S(0.16, 0.012, 0.045),
               "steel")
    sm.box(T(-0.56, 0, 0.0) @ S(0.05, 0.16, 0.05), "gold")
    sm.box(T(-0.68, 0, 0.0) @ S(0.2, 0.04, 0.04), "gold")
    sm.ico(T(-0.8, 0, 0.0), "gold", r=0.04, sub=1)
    held = sm.obj("KingSword", coll, parent=parts["armR"])
    held.location = (0.5, 0.03, -0.66)
    held.rotation_euler = (-1.25, 0, -0.25)
    floor = bpy.data.objects.new("KingSwordLaid", held.data)
    coll.objects.link(floor)
    return root, parts, held, floor


def pose_king(root, parts, held, floor, ev, step_z):
    """Kneels holding the sword up, bows and lays it on the step ("lays his sword"), then kneels
    with joined palms, head bowed."""
    f0, f1 = ev["s37"]
    lay = ev["lay"]
    kp = kit.key_pose
    up = {"armL": (1.25, 0.0, 0.25), "armR": (1.25, 0.0, -0.25), "waist": (0.0, 0, 0), "head": (-0.08, 0, 0)}
    kp(parts, f0, up)
    kp(parts, lay - 70, up)
    bow = {"armL": (0.8, 0.0, 0.25), "armR": (0.8, 0.0, -0.25), "waist": (-0.62, 0, 0), "head": (-0.25, 0, 0)}
    kp(parts, lay - 8, bow)
    kp(parts, lay + 6, bow)
    pray = {"armL": (1.0, 0.0, 0.55), "armR": (1.0, 0.0, -0.55), "waist": (-0.42, 0, 0), "head": (-0.3, 0, 0)}
    kp(parts, lay + 46, pray)
    kp(parts, f1, {"armL": (1.0, 0.0, 0.55), "armR": (1.0, 0.0, -0.55), "waist": (-0.3, 0, 0), "head": (-0.22, 0, 0)})
    sc = bpy.context.scene
    sc.frame_set(lay)
    M = held.matrix_world.copy()
    loc, rot, _ = M.decompose()
    e = rot.to_euler()
    floor.location = (loc.x, loc.y, step_z + 0.04)
    floor.rotation_euler = (0, 0, e.z)
    for ob, a, b in ((held, 1.0, 0.0), (floor, 0.0, 1.0)):
        for f, v in ((1, a), (lay, a), (lay + 1, b)):
            ob.scale = (v, v, v)
            ob.keyframe_insert("scale", frame=f)
        for fc in _fcurves(ob.animation_data.action):
            if fc.data_path == "scale":
                for k in fc.keyframe_points:
                    k.interpolation = "CONSTANT"
    sc.frame_set(1)


def make_priest(coll, ev, rng):
    """Temple priest in a white mundu, bare chest, holding a small brass lamp (arati) that he
    circles before the shrine."""
    root, parts = kit.make_rig("Priest", coll, "villager", seed=12, cloth="cloth_w")
    lamp = kit.make_brass_lamp("PriestLamp", coll, h=1.5, lit=True)
    lamp.parent = parts["armR"]
    lamp.scale = (0.3, 0.3, 0.3)
    lamp.location = (0.0, 0.02, -0.62)
    lamp.rotation_euler = (-1.05, 0, 0)
    f0, f1 = ev["s37"]
    kit.key_pose(parts, f0, {"armR": (1.05, 0.0, 0.1), "armL": (0.6, 0.0, -0.3)})
    f = f0 + 6
    k = 0
    while f < f1:                                              # slow circles with the lamp
        a = k * math.pi / 3
        kit.key_pose(parts, f, {"armR": (1.05 + 0.22 * math.sin(a), 0.0, 0.1 + 0.25 * math.cos(a))})
        f += 7
        k += 1
    kit.animate_rig_idle(parts, rng, f0, f1, skip=("armR", "armL"))
    return root, parts


def build_set_c(colls, lib, ev):
    rng = random.Random(37)
    c = colls["temple"]
    xs = _axis([(-200, -24, 8), (-24, 42, 2.0), (42, 220, 8)])
    ys = _axis([(-120, -30, 8), (-30, 38, 2.0), (38, 320, 8)])
    xs = [x + TO[0] for x in xs]
    ys = [y + TO[1] for y in ys]
    _heightfield(colls["world"], "TerrainC", xs, ys, gC,
                 lambda x, y, z, nz, r: "grass" if r.random() > 0.3 else ("leaf" if r.random() > 0.5 else "grass_lt"),
                 ["grass", "grass_lt", "leaf"], seed=7)
    tc = kit.new_collection("TempleBuild")
    make_court(tc, rng)
    make_shrine(tc, rng)
    make_gopuram(tc, rng)
    make_corridor(tc, rng)
    _, mast_top = make_flagmast(tc)
    for ob in tc.objects:
        if ob.parent is None:
            ob.location.x += TO[0]
            ob.location.y += TO[1]
    lamp = _clay_lamp(colls["lib"])
    fl = (ev["s37"][0], ev["s37"][1])
    sx, sy = SHRINE
    w = SHR_W + 1.15
    rows = [((sx - w / 2 + 0.1, sy - w / 2 + 0.05), (sx - 1.4, sy - w / 2 + 0.05), PLINTH_H, 0.42),
            ((sx + 1.4, sy - w / 2 + 0.05), (sx + w / 2 - 0.1, sy - w / 2 + 0.05), PLINTH_H, 0.42),
            ((sx - w / 2 + 0.05, sy - w / 2 + 0.2), (sx - w / 2 + 0.05, sy + w / 2), PLINTH_H, 0.42),
            ((sx + w / 2 - 0.05, sy - w / 2 + 0.2), (sx + w / 2 - 0.05, sy + w / 2), PLINTH_H, 0.42),
            ((sx - w / 2 - 0.55, sy - w / 2 - 0.35), (sx - 1.6, sy - w / 2 - 0.35), 0.32, 0.38),
            ((CORR[0] + 0.3, CORR[2] + 0.12), (CORR[1] - 0.3, CORR[2] + 0.12), 0.9, 0.55),
            ((-17.4, -24.0), (-17.4, 32.0), 0.7, 0.62),
            ((-18.3, -14.4), (-9.7, -14.4), 0.71, 0.36), ((-9.7, -14.4), (-9.7, -9.7), 0.71, 0.36),
            ((GOPURAM[0] - 6.0, GOPURAM[1] - 4.2), (GOPURAM[0] + 6.0, GOPURAM[1] - 4.2), 0.8, 0.5)]
    for i, (p0, p1, z, step) in enumerate(rows):
        _lamp_row(c, lamp, p0, p1, z, step, rng, f"Lamp{i}_", flicker=fl)
    mx, my = MAST
    for i, (a, z) in enumerate(((1.7, 0.4), (1.4, 0.76))):        # lamps round the mast plinth ledges
        q = a - 0.15
        for (p0, p1) in (((mx - q, my - q), (mx + q, my - q)), ((mx + q, my - q), (mx + q, my + q)),
                         ((mx + q, my + q), (mx - q, my + q)), ((mx - q, my + q), (mx - q, my - q))):
            _lamp_row(c, lamp, p0, p1, z, 0.4, rng, f"MastLamp{i}_", flicker=fl)
    # trees behind the walls: palms and broad crowns in the mist
    sp = Spacer(5.0)
    k = 0
    for i in range(8000):
        x, y = rng.uniform(-90, 110), rng.uniform(-24, 160)
        if -22.0 < x < 40.0 and -28.0 < y < 37.0:
            continue
        r = 2.6
        if not sp.free(x, y, r):
            continue
        sp.add(x, y, r)
        src = rng.choice(lib["palms"]) if rng.random() < 0.6 else rng.choice(lib["jtrees"] + lib["trees"])
        kit.instance(src, f"CTree{k}", c, (x + TO[0], y + TO[1], hC(x, y) - 0.2), rot_z=rng.uniform(0, TAU),
                     scale=rng.uniform(1.0, 1.4))
        k += 1
        if k > 700:
            break
    for i in range(160):
        x, y = rng.uniform(-60, 80), rng.uniform(-40, 90)
        if -21.0 < x < 39.0 and -27.0 < y < 35.5:
            continue
        kit.instance(rng.choice(lib["bushes"] + lib["bigleaf"]), f"CBush{i}", c, (x + TO[0], y + TO[1], hC(x, y)),
                     rot_z=rng.uniform(0, TAU), scale=rng.uniform(1.0, 1.8))
    # the king kneeling before the shrine steps, the priest beside the door
    root, parts, held, floor = make_kneeling_king(c, ev["end"], ev, rng)
    kx, ky = sx - 1.95, sy - SHR_W / 2 - 2.55
    root.location = (kx + TO[0], ky + TO[1], 0.0)
    root.rotation_euler[2] = _face(1.0, 0.25)
    pose_king(root, parts, held, floor, ev, step_z=0.0)
    kit.animate_rig_idle(parts, rng, ev["s37"][0], ev["s37"][1], body=0.006, head=0.04, skip=("waist", "armL", "armR", "head"))
    proot, pparts = make_priest(c, ev, rng)
    px, py = sx + 1.45, sy - SHR_W / 2 - 1.75
    proot.location = (px + TO[0], py + TO[1], 0.0)
    proot.rotation_euler[2] = _face(kx - px, ky - py + 0.8)
    for i, (x, y) in enumerate([(GOPURAM[0] - 2.2, GOPURAM[1] - 4.6), (GOPURAM[0] + 2.2, GOPURAM[1] - 4.6)]):
        g = kit.instance(lib["guard"], f"TempleGuard{i}", c, (x + TO[0], y + TO[1], 0.8), rot_z=math.pi)
        kit.animate_idle(g, rng, 1, ev["end"], 0.02)
    # dawn mist among the trees, and the set's haze
    palw.add_mist_box(colls["world"], "DawnMist", (TO[0] + 10.0, TO[1] + 95.0, 9.0), (320.0, 110.0, 22.0), 0.022,
                      color=(0.98, 0.84, 0.82))
    palw.add_mist_box(colls["world"], "DawnMistSide", (TO[0] - 70.0, TO[1] + 10.0, 8.0), (90.0, 200.0, 20.0), 0.02,
                      color=(0.98, 0.84, 0.82))
    haze = cw.add_haze(colls["rig"], density=0.0012, color=(0.98, 0.86, 0.84))
    haze.location = (TO[0] + 100.0, TO[1] - 100.0, -80.0)
    return root


# ================================================================= assembly
def build_world(ev, sets="ABC"):
    """Everything but the camera. ev: real frames (s33, s35, s36, s37 ranges, arrive, raise,
    lay, end). Returns (rig collection, sun)."""
    names = ["World", "Paddies", "Palace", "Town", "TownPeople", "Village", "Props", "Plants", "People", "Fleet",
             "Groves", "Hamlet", "Column", "Fort", "Crowd", "PlantsB", "Temple", "Rig", "Library"]
    colls = {n.lower(): kit.new_collection(n) for n in names}
    colls["lib"] = colls["library"]
    colls["townpeople"] = colls["townpeople"]
    colls["plantsB"] = colls["plantsb"]
    sun = cw.scene_base(colls["rig"], sun_dir=(0.75, -0.35, -0.5), sun_energy=8.0, haze_density=0.00005)
    lib = build_library(colls["lib"])
    if "A" in sets:
        build_set_a(colls, lib, ev)
    if "B" in sets:
        build_set_b(colls, lib, ev)
    if "C" in sets:
        build_set_c(colls, lib, ev)
    for ob in colls["lib"].objects:
        if ob.type == "MESH" and ob.parent is None:
            kit.hide_source(ob)
    return colls["rig"], sun
