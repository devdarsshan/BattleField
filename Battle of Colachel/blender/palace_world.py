"""Padmanabhapuram (S14, shot-list clip 19): the palace town of the young Marthanda Varma.

Laid out to match the Flow references frames/flow_refs/K19a_v1 (high view of the palace
town) and K19b_v2 (the king alone on a carved upper veranda): dark carved-wood halls
with steep tiered terracotta-tile roofs (hip-and-gable "Kerala" roofs with carved
sunburst gables), pillared verandas, a sandy inner courtyard, a reddish laterite
boundary wall with a gate house, a stepped stone temple tank, a town of plastered
tile-roofed houses along dirt roads, dense palms and round trees, faceted green hills.

Coordinates: metres, Z up, ground at z = 0. North is +Y; the opening camera looks
north-north-east from the south-west, the sun is low in the west-south-west.
The palace compound is centred on the origin.

New assets (tile roofs, Kerala halls, carved verandas, laterite wall, gate house,
temple tank, town houses, banana plants, the young king) are defined here in the
colachel_kit style: flat-shaded bmesh builds; repeated pieces are library objects
that are instanced.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

import colachel_kit as kit
import colachel_world as cw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau
UP = Vector((0, 0, 1))

# extra colours for this set (greens, skin, cloth and gold come from kit.PALETTE)
PALETTE = {
    "tile":        (0.66, 0.28, 0.15),
    "tile_lt":     (0.75, 0.36, 0.19),
    "tile_dk":     (0.54, 0.21, 0.12),
    "tile_under":  (0.36, 0.16, 0.11),
    "teak":        (0.27, 0.17, 0.11),
    "teak_dk":     (0.17, 0.11, 0.08),
    "teak_lt":     (0.38, 0.25, 0.16),
    "plaster":     (0.70, 0.65, 0.58),     # town house walls (K19a: grey-beige)
    "plaster_g":   (0.62, 0.59, 0.54),
    "plaster_y":   (0.90, 0.75, 0.52),     # warm palace interior walls (K19b)
    "laterite":    (0.60, 0.29, 0.21),
    "laterite_dk": (0.50, 0.23, 0.17),
    "laterite_lt": (0.67, 0.35, 0.25),
    "granite":     (0.60, 0.58, 0.55),
    "granite_dk":  (0.48, 0.47, 0.45),
    "floor":       (0.33, 0.13, 0.10),     # red-oxide floor
    "court":       (0.80, 0.66, 0.47),     # sandy courtyard
    "road":        (0.77, 0.61, 0.43),
    "grass_lt":    (0.45, 0.56, 0.21),
    "hill_lt":     (0.56, 0.67, 0.34),
    "far_hill":    (0.47, 0.60, 0.31),
    "jungle":      (0.31, 0.46, 0.20),
    "water":       (0.48, 0.66, 0.70),
    "banana":      (0.40, 0.60, 0.20),
    "banana_dk":   (0.30, 0.50, 0.16),
}
TILE_MATS = (("tile", 0.5), ("tile_lt", 0.27), ("tile_dk", 0.23))


def register_palette():
    """Add this set's colours to the kit palette and create their materials
    (call after kit.reset_scene)."""
    for name, rgb in PALETTE.items():
        kit.PALETTE[name] = rgb
        kit.mat(name, rgb)
    w = bpy.data.materials["water"].node_tree.nodes.get("Principled BSDF")
    w.inputs["Roughness"].default_value = 0.18
    w.inputs["Specular IOR Level"].default_value = 0.5


# ------------------------------------------------------------------- layout
WALL = (-36.0, 36.0, -26.0, 26.0)        # x0, x1, y0, y1 of the laterite wall's centre line
WALL_H = 3.3
WALL_T = 0.9
GATE_X, GATE_W = -16.0, 4.4              # gate in the south wall (front left, as in K19a)
TANK = (-4.0, -52.0, 14.0, 9.0)          # centre x, y and half sizes of the top step
TANK_STEPS, STEP_H, STEP_W = 6, 0.55, 0.85
WATER_Z = -2.0
# halls: (key, centre x, y, rot_z, W, D, seed). Ridges run along local X; local -Y is the front.
HALL_A = (0.0, 10.0, math.pi / 2)        # main hall, three roof tiers, gables to north and south
HALL_B = (23.0, -1.0, -math.pi / 2)      # the king's hall: upper veranda and bay face west
HALL_C = (-20.0, -8.0, math.pi / 2)      # front-left hall, two tiers
# dirt roads: (polyline, half width)
ROADS = [
    ([(-44, -34), (44, -34), (44, 34), (-44, 34), (-44, -34)], 3.0),      # ring road
    ([(GATE_X, -26), (GATE_X, -34)], 2.2),                                # gate to the ring
    ([(GATE_X, -34), (-25, -62), (-28, -150), (-40, -260)], 3.0),         # south
    ([(30, -34), (48, -70), (70, -130), (92, -230)], 2.8),               # south-east
    ([(44, 4), (90, 10), (160, 4), (260, 14)], 2.8),                      # east
    ([(-44, -4), (-100, -10), (-170, 0), (-260, -12)], 2.8),              # west
    ([(4, 34), (10, 80), (0, 140)], 2.4),                                 # north, toward the hills
    ([(-25, -62), (-60, -66), (-120, -72)], 2.2),                         # past the tank
]


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


def _ss(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _rect_dist(x, y, x0, x1, y0, y1):
    """Distance from (x, y) to a rectangle (0 inside)."""
    dx = max(x0 - x, 0.0, x - x1)
    dy = max(y0 - y, 0.0, y - y1)
    return math.hypot(dx, dy)


def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(px - ax - vx * t, py - ay - vy * t)


def road_dist(x, y):
    """Distance outside the nearest road's edge (negative on the road)."""
    best = 1e9
    for pts, hw in ROADS:
        for a, b in zip(pts, pts[1:]):
            best = min(best, _seg_dist(x, y, a, b) - hw)
    return best


def tank_rect(k=0):
    """Outer rectangle of tank step ring k (k = 0 is the top step)."""
    cx, cy, hx, hy = TANK
    d = k * STEP_W
    return (cx - hx + d, cx + hx - d, cy - hy + d, cy + hy - d)


def in_tank(x, y, pad=0.0):
    x0, x1, y0, y1 = tank_rect(0)
    return x0 - pad < x < x1 + pad and y0 - pad < y < y1 + pad


def height(x, y):
    if in_tank(x, y, -0.25):
        return -3.8                                         # pit under the steps
    h = 0.35 * _n(x, y, 40.0, 1.3) + 0.12 * _n(x, y, 11.0, 2.1)
    h *= _ss(2.0, 14.0, _rect_dist(x, y, WALL[0] - 1, WALL[1] + 1, WALL[2] - 1, WALL[3] + 1))
    # faceted green hills behind (north) and to the sides
    q = -0.62 * x + 0.78 * y                                 # distance "behind" as seen from the south-east
    m = max(_ss(150.0, 320.0, q), _ss(320.0, 520.0, math.hypot(x, y)))
    if m > 0:
        ridge = (1.0 - abs(_n(x, y, 150.0, 7.7))) ** 2
        h += m * (18.0 + 85.0 * ridge + 22.0 * _n(x, y, 60.0, 3.3))
        h += _ss(380.0, 750.0, q) * 120.0 * (1.0 - abs(_n(x, y, 260.0, 1.9))) ** 2   # far ridges
    return h


# ------------------------------------------------------------------ terrain
def _axis(edges, steps):
    out = []
    for (a, b), s in zip(zip(edges, edges[1:]), steps):
        n = max(1, round((b - a) / s))
        out += [(a + (b - a) * i / n, (b - a) / n) for i in range(n)]
    out.append((edges[-1], steps[-1]))
    return out


def make_terrain(collection, seed=3):
    rng = random.Random(seed)
    xs = _axis([-950, -230, -115, 115, 230, 950], [34, 6, 1.0, 6, 34])
    ys = _axis([-600, -170, -95, 72, 170, 1200], [34, 6, 1.0, 6, 34])
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
    mats = ["grass", "grass_lt", "court", "road", "hill_lt", "far_hill", "jungle", "granite_dk"]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    x0, x1, y0, y1 = WALL
    for f in bm.faces:
        x, y, z = f.calc_center_median()
        if in_tank(x, y, 0.3):
            m = "granite_dk"
        elif x0 < x < x1 and y0 < y < y1:
            m = "court"
        elif z > 7.0:
            k = _n(x, y, 45.0, 9.1)
            m = "far_hill" if k > 0.15 else ("jungle" if k < -0.25 or f.normal.z < 0.7 else "hill_lt")
        elif abs(x) < 300 and road_dist(x, y) < 0.35 * _n(x, y, 3.0, 4.2):
            m = "road"
        else:
            m = "grass_lt" if _n(x, y, 18.0, 5.5) > 0.12 else "grass"
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


# ================================================================ tile roofs
def _pick(rng, weighted):
    r = rng.random()
    for name, w in weighted:
        r -= w
        if r <= 0:
            return name
    return weighted[-1][0]


def tile_plane(mb, poly, rng, tw=0.44, tl=0.5, step=0.37, th=0.075, mats=TILE_MATS):
    """Cover a planar roof polygon with rows of overlapping terracotta tiles.
    poly: world points, first edge = the (horizontal) eave. Each tile is a wedge,
    thick at its lower edge, so every row reads as a step; rows are staggered by half
    a tile and clipped to the polygon (hips, valleys, gable notches). A dark underlay
    fills the gaps."""
    poly = [Vector(p) for p in poly]
    n = Vector((0.0, 0.0, 0.0))
    for a, b in zip(poly, poly[1:] + poly[:1]):
        n.x += (a.y - b.y) * (a.z + b.z)
        n.y += (a.z - b.z) * (a.x + b.x)
        n.z += (a.x - b.x) * (a.y + b.y)
    n.normalize()
    if n.z < 0:
        n = -n
    u = poly[1] - poly[0]
    u.z = 0
    u.normalize()
    v = n.cross(u)
    if v.z < 0:
        u, v = -u, -v
    o = poly[0]
    st = [((p - o).dot(u), (p - o).dot(v)) for p in poly]
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(st, st[1:] + st[:1]))
    under = [mb.bm.verts.new(p - n * 0.01) for p in (poly if area > 0 else poly[::-1])]
    mb.face(under, "tile_under")
    tmin = min(t for _, t in st)
    tmax = max(t for _, t in st)

    def W(s, t, h):
        return o + u * s + v * t + n * h

    g = 0.016
    i = 0
    t = tmin - 0.07
    while t < tmax - 0.1:
        tc = min(t + step, tmax - 0.02)
        xs = []
        for (s0, t0), (s1, t1) in zip(st, st[1:] + st[:1]):
            if (t0 <= tc < t1) or (t1 <= tc < t0):
                xs.append(s0 + (tc - t0) / (t1 - t0) * (s1 - s0))
        xs.sort()
        off = (i % 2) * tw * 0.5
        for a, b in zip(xs[0::2], xs[1::2]):
            k = math.floor((a - off) / tw)
            while True:
                s0 = off + k * tw
                k += 1
                if s0 >= b:
                    break
                c0, c1 = max(s0, a), min(s0 + tw, b)
                if c1 - c0 < 0.1:
                    continue
                hh = th * rng.uniform(0.8, 1.2)
                m = _pick(rng, mats)
                A, B = mb.bm.verts.new(W(c0 + g, t, 0)), mb.bm.verts.new(W(c1 - g, t, 0))
                C, D = mb.bm.verts.new(W(c1 - g, t, hh)), mb.bm.verts.new(W(c0 + g, t, hh))
                E, F = mb.bm.verts.new(W(c0 + g, t + tl, 0.012)), mb.bm.verts.new(W(c1 - g, t + tl, 0.012))
                mb.face([A, B, C, D], m)
                mb.face([D, C, F, E], m)
                mb.face([A, D, E], m)
                mb.face([B, F, C], m)
        t += step
        i += 1


def ridge_cap(mb, p0, p1, r=0.14, m="tile_dk", seg=0.5):
    """Row of rounded ridge tiles along a ridge or hip line."""
    p0, p1 = Vector(p0) + UP * r * 0.55, Vector(p1) + UP * r * 0.55
    L = (p1 - p0).length
    n = max(1, round(L / seg))
    for k in range(n):
        a = p0.lerp(p1, k / n)
        b = p0.lerp(p1, (k + 1) / n)
        mb.seg(a, b + (b - a) * 0.06, r * 1.08, r * 0.92, m, sides=6)


def _prism(mb, pts, thick, side, m):
    """Flat polygon (pts, in a vertical plane) extruded by `thick` along `side`."""
    side = Vector(side).normalized() * thick / 2
    a = [mb.bm.verts.new(Vector(p) + side) for p in pts]
    b = [mb.bm.verts.new(Vector(p) - side) for p in pts]
    mb.face(a, m)
    mb.face(b[::-1], m)
    k = len(pts)
    for i in range(k):
        j = (i + 1) % k
        mb.face([a[i], b[i], b[j], a[j]], m)


def carved_gable(mb, base_c, half, height, out, rays=9, depth=0.1):
    """Kerala carved gable: dark triangular panel, base beam, sunburst slats radiating
    from a half-round boss at the bottom centre, a king post, and a finial on top.
    base_c: centre of the gable base; out: horizontal unit vector the gable faces."""
    out = Vector(out).normalized()
    side = out.cross(UP).normalized()
    c = Vector(base_c)
    apex = c + UP * height
    _prism(mb, [c - side * half, c + side * half, apex], depth, out, "teak_dk")
    f = out * (depth / 2 + 0.03)                                   # carving stands proud
    mb.box(kit.frame_matrix(c + f + UP * 0.1, side, out, UP) @ S(half * 2.0, 0.12, 0.2), "teak")
    for k in range(rays):
        a = math.pi * (k + 0.5) / rays
        # point on the sloped edges in direction a from the base centre
        d = side * math.cos(a) + UP * math.sin(a)
        # intersect ray with the triangle's edges: |s|/half + z/height = 1
        tt = 1.0 / (abs(math.cos(a)) / half + math.sin(a) / height)
        tip = c + d * tt * 0.9
        mb.seg(c + f + UP * 0.2, tip + f, 0.035, 0.03, "teak", sides=4)
    mb.cone(kit.frame_matrix(c + f * 1.4 + UP * 0.2, side, UP, -out), "teak",
            segments=10, r1=min(0.32, half * 0.2), r2=min(0.32, half * 0.2), depth=0.06)
    mb.seg(c + f + UP * 0.2, apex + f - UP * 0.15, 0.06, 0.05, "teak", sides=4)
    # finial (kodumudi)
    mb.seg(apex + out * 0.1, apex + out * 0.1 + UP * 0.9, 0.07, 0.025, "brass", sides=6)
    mb.ico(T(apex + out * 0.1 + UP * 0.35), "brass", r=0.11, sub=1)


def bargeboards(mb, a, apex, b, out, teeth=True):
    """Thick dark boards under the sloped tile edges of a gable, with a fringe of
    hanging carved drops."""
    out = Vector(out).normalized()
    for p, q in ((a, apex), (b, apex)):
        p, q = Vector(p), Vector(q)
        d = (q - p)
        L = d.length
        d.normalize()
        nrm = out.cross(d).normalized()
        if nrm.z < 0:
            nrm = -nrm
        M = kit.frame_matrix((p + q) / 2 - nrm * 0.12, d, out, nrm)
        mb.box(M @ S(L, 0.1, 0.3), "teak")
        if teeth:
            k = int(L / 0.42)
            for i in range(1, k):
                c = p + d * (L * i / k) - nrm * 0.3
                mb.box(T(c - UP * 0.07) @ S(0.07, 0.07, 0.16) @ Rz(math.atan2(out.y, out.x)), "teak")


def roof_hipgable(mb, rng, cx, cy, z0, X0, Y0, pitch=43.0, gable=0.42, ext=0.45, tile=None, carve=True):
    """Kerala hip-and-gable roof, ridge along X: hipped ends whose top part becomes a
    carved vertical gable that the side slopes overhang. X0, Y0: half sizes of the eave
    outline (overhang included); gable: fraction of the rise that is gable."""
    tile = tile or {}
    ta = math.tan(math.radians(pitch))
    H = Y0 * ta
    hg = H * (1 - gable)
    xg = X0 - hg / ta
    if xg < 0.3:
        xg = 0.3
        hg = (X0 - xg) * ta
    yb = Y0 - hg / ta
    zr, zg = z0 + H, z0 + hg
    e = ext if yb > 0.25 else 0.0
    P = lambda x, y, z: Vector((cx + x, cy + y, z))
    for sy in (-1, 1):                                              # long slopes
        pts = [P(-sy * X0, sy * Y0, z0), P(sy * X0, sy * Y0, z0), P(sy * xg, sy * yb, zg)]
        if e:
            pts += [P(sy * (xg + e), sy * yb, zg)]
        pts += [P(sy * (xg + e), 0, zr), P(-sy * (xg + e), 0, zr)]
        if e:
            pts += [P(-sy * (xg + e), sy * yb, zg)]
        pts += [P(-sy * xg, sy * yb, zg)]
        tile_plane(mb, pts, rng, **tile)
    for sx in (-1, 1):                                              # hipped ends
        pts = [P(sx * X0, -sx * Y0, z0), P(sx * X0, sx * Y0, z0), P(sx * xg, sx * yb, zg)]
        if yb > 0.05:
            pts.append(P(sx * xg, -sx * yb, zg))
        tile_plane(mb, pts, rng, **tile)
        for sy in (-1, 1):
            ridge_cap(mb, P(sx * X0, sy * Y0, z0), P(sx * xg, sy * yb, zg))
        if yb > 0.25 and carve:
            out = Vector((sx, 0, 0))
            carved_gable(mb, P(sx * (xg + 0.06), 0, zg), yb, H - hg, out)
            bargeboards(mb, P(sx * (xg + e), -yb - 0.05, zg - 0.05), P(sx * (xg + e), 0, zr),
                        P(sx * (xg + e), yb + 0.05, zg - 0.05), out)
    ridge_cap(mb, P(-xg - e - 0.1, 0, zr), P(xg + e + 0.1, 0, zr), r=0.16)
    _eave_fascia(mb, [P(-X0, -Y0, z0), P(X0, -Y0, z0), P(X0, Y0, z0), P(-X0, Y0, z0)])
    return zr


def _eave_fascia(mb, corners, m="teak"):
    for a, b in zip(corners, corners[1:] + corners[:1]):
        d = b - a
        mb.box(T((a + b) / 2 - UP * 0.1) @ Rz(math.atan2(d.y, d.x)) @ S(d.length + 0.1, 0.1, 0.22), m)


def roof_skirt(mb, rng, cx, cy, z0, X0, Y0, r, pitch=34.0, tile=None):
    """Lean-to tile skirt round a storey (a lower tier of a tiered roof): eave outline
    X0, Y0 at z0, rising inward by r to meet the next storey's wall."""
    tile = tile or {}
    z1 = z0 + r * math.tan(math.radians(pitch))
    Xi, Yi = X0 - r, Y0 - r
    P = lambda x, y, z: Vector((cx + x, cy + y, z))
    for sy in (-1, 1):
        tile_plane(mb, [P(-sy * X0, sy * Y0, z0), P(sy * X0, sy * Y0, z0), P(sy * Xi, sy * Yi, z1),
                        P(-sy * Xi, sy * Yi, z1)], rng, **tile)
    for sx in (-1, 1):
        tile_plane(mb, [P(sx * X0, -sx * Y0, z0), P(sx * X0, sx * Y0, z0), P(sx * Xi, sx * Yi, z1),
                        P(sx * Xi, -sx * Yi, z1)], rng, **tile)
        for sy in (-1, 1):
            ridge_cap(mb, P(sx * X0, sy * Y0, z0), P(sx * Xi, sy * Yi, z1))
    _eave_fascia(mb, [P(-X0, -Y0, z0), P(X0, -Y0, z0), P(X0, Y0, z0), P(-X0, Y0, z0)])
    return z1


# ============================================================ carved woodwork
def pillar(mb, x, y, z0, h, w=0.25, base="granite"):
    """Turned wooden pillar on a stone base: octagonal shaft, rings, neck and a
    wide capital block."""
    mb.box(T(x, y, z0 + 0.11) @ S(w * 1.75, w * 1.75, 0.22), base)
    mb.box(T(x, y, z0 + 0.3) @ S(w * 1.3, w * 1.3, 0.16), "teak")
    mb.seg((x, y, z0 + 0.38), (x, y, z0 + h - 0.42), w * 0.56, w * 0.52, "teak", sides=8, spin=math.pi / 8)
    for zz in (0.55, h * 0.62):
        mb.box(T(x, y, z0 + zz) @ S(w * 1.12, w * 1.12, 0.07), "teak_dk")
    mb.box(T(x, y, z0 + h - 0.36) @ S(w * 1.22, w * 1.22, 0.14), "teak")
    mb.box(T(x, y, z0 + h - 0.15) @ S(w * 1.7, w * 1.7, 0.2), "teak")


def bracket(mb, x, y, ztop, d, size=0.62):
    """Carved triangular bracket from a pillar top out along the beam direction d,
    with a hanging drop under its tip."""
    d = Vector((d[0], d[1], 0)).normalized()
    p = Vector((x, y, ztop - 0.25)) + d * 0.14
    pts = [p, p + d * size, p - UP * size * 0.9]
    _prism(mb, pts, 0.08, d.cross(UP), "teak")
    mb.seg(p + d * size * 0.55 - UP * 0.05, p + d * size * 0.55 - UP * 0.42, 0.05, 0.02, "teak_lt", sides=6)


def railing(mb, p0, p1, z, h=0.92, sp=0.16):
    """Wooden balustrade from p0 to p1: top and bottom rails, a skirting board and a
    row of turned (double-cone) balusters."""
    p0, p1 = Vector((p0[0], p0[1], 0)), Vector((p1[0], p1[1], 0))
    d = p1 - p0
    L = d.length
    if L < 0.2:
        return
    a = math.atan2(d.y, d.x)
    c = (p0 + p1) / 2
    mb.box(T(c.x, c.y, z + h - 0.05) @ Rz(a) @ S(L, 0.14, 0.1), "teak")
    mb.box(T(c.x, c.y, z + 0.14) @ Rz(a) @ S(L, 0.12, 0.08), "teak")
    mb.box(T(c.x, c.y, z + 0.05) @ Rz(a) @ S(L, 0.16, 0.1), "teak_dk")
    n = max(1, int(L / sp))
    bh = (h - 0.28) / 2
    for k in range(n):
        q = p0 + d * ((k + 0.5) / n)
        mb.cone(T(q.x, q.y, z + 0.18 + bh / 2), "teak", segments=4, r1=0.028, r2=0.062, depth=bh)
        mb.cone(T(q.x, q.y, z + 0.18 + bh * 1.5), "teak", segments=4, r1=0.062, r2=0.028, depth=bh)


def wall_panel(mb, p0, p1, z0, h, style, rng, out, door=False, thick=0.16):
    """Wall between two points with its detail on the `out` side.
    style "wood": dark boarded wall with battens and lattice windows.
    style "plaster": cream plaster between wooden posts and beams, barred windows."""
    p0, p1 = Vector((p0[0], p0[1], z0)), Vector((p1[0], p1[1], z0))
    d = p1 - p0
    L = d.length
    d.normalize()
    out = Vector((out[0], out[1], 0)).normalized()
    F = kit.frame_matrix(p0, d, out, UP)                        # local: a along wall, b outward, z up
    body = "teak_dk" if style == "wood" else style
    mb.box(F @ T(L / 2, 0, h / 2) @ S(L, thick, h), body)
    b = thick / 2 + 0.03
    mb.box(F @ T(L / 2, b, h - 0.12) @ S(L, 0.08, 0.2), "teak")
    mb.box(F @ T(L / 2, b, 0.1) @ S(L, 0.08, 0.2), "teak")
    door_a = L / 2 if door else -9.0
    # bays between posts
    nb = max(1, round(L / 2.2))
    for i in range(nb + 1):
        a = L * i / nb
        mb.box(F @ T(a, b, h / 2) @ S(0.16, 0.1, h), "teak")
    for i in range(nb):
        a = L * (i + 0.5) / nb
        if abs(a - door_a) < 1.0:
            continue
        win = (i + (1 if style == "wood" else 0)) % 2 == 0 or style != "wood"
        if win:
            wz, wh, ww = h * 0.6, min(1.0, h * 0.36), min(1.0, L / nb * 0.5)
            mb.box(F @ T(a, b - 0.02, wz) @ S(ww, 0.06, wh), "dark")
            for k in range(4):
                mb.box(F @ T(a - ww / 2 + ww * (k + 0.5) / 4, b + 0.01, wz) @ S(0.045, 0.05, wh), "teak")
            mb.box(F @ T(a, b + 0.02, wz + wh / 2 + 0.05) @ S(ww + 0.22, 0.08, 0.1), "teak")
            mb.box(F @ T(a, b + 0.02, wz - wh / 2 - 0.05) @ S(ww + 0.22, 0.1, 0.1), "teak")
        if style == "wood":                                       # vertical battens
            k0 = -0.5 * L / nb + 0.2
            s = k0
            while s < 0.5 * L / nb - 0.15:
                if not win or abs(s) > 0.65:
                    mb.box(F @ T(a + s, b - 0.02, h * 0.42 if win else h / 2) @
                           S(0.05, 0.05, h * 0.72 if win else h - 0.3), "teak")
                s += 0.3
    if door:
        dw, dh = 1.15, min(2.15, h - 0.35)
        mb.box(F @ T(L / 2, b - 0.01, dh / 2 + 0.05) @ S(dw, 0.08, dh), "dark")
        for sx in (-1, 1):
            mb.box(F @ T(L / 2 + sx * (dw / 2 + 0.07), b + 0.03, dh / 2 + 0.05) @ S(0.14, 0.12, dh + 0.1), "teak")
        mb.box(F @ T(L / 2, b + 0.03, dh + 0.12) @ S(dw + 0.5, 0.14, 0.16), "teak")


def _ring(X, Y, sp):
    """Points round a rectangle (corners included) at about sp spacing, as
    [(point, side index)], plus the side directions."""
    corners = [(-X, -Y), (X, -Y), (X, Y), (-X, Y)]
    pts = []
    for s in range(4):
        a, b = Vector(corners[s]), Vector(corners[(s + 1) % 4])
        n = max(1, round((b - a).length / sp))
        for k in range(n):
            pts.append((a.lerp(b, k / n), s))
    return pts


OUTWARD = [Vector((0, -1)), Vector((1, 0)), Vector((0, 1)), Vector((-1, 0))]   # per side of _ring


def storey(mb, rng, X, Y, z0, h, kind, style, ci=1.5, sp=2.3, doors=(0, 2), skip=None):
    """One storey of a hall in local coordinates. Outline half sizes X, Y.
    kind "pillared": open veranda of pillars round a walled core inset by ci.
    kind "veranda": the same with a balustrade between the pillars (upper floors).
    kind "band": closed upper storey, walls on the outline.
    skip(side, a, b): True to leave a railing gap (the bay opening)."""
    mb.box(T(0, 0, z0 - 0.08) @ S(2 * X + 0.3, 2 * Y + 0.3, 0.16), "floor")
    if kind == "band":
        cs = [(-X, -Y), (X, -Y), (X, Y), (-X, Y)]
        for s in range(4):
            wall_panel(mb, cs[s], cs[(s + 1) % 4], z0, h, style, rng, OUTWARD[s], door=False)
        mb.box(T(0, 0, z0 + h - 0.05) @ S(2 * X, 2 * Y, 0.1), "teak_dk")
        return
    ring = _ring(X, Y, sp)
    for p, s in ring:
        pillar(mb, p.x, p.y, z0, h)
    for i, (p, s) in enumerate(ring):
        q, s2 = ring[(i + 1) % len(ring)]
        d = (q - p).normalized()
        bracket(mb, p.x, p.y, z0 + h, d)
        bracket(mb, q.x, q.y, z0 + h, -d)
        if kind == "veranda" and not (skip and skip(s, p, q)):
            railing(mb, p + d * 0.2, q - d * 0.2, z0)
    for s, (a, b) in enumerate([((-X, -Y), (X, -Y)), ((X, -Y), (X, Y)), ((X, Y), (-X, Y)), ((-X, Y), (-X, -Y))]):
        a, b = Vector(a), Vector(b)
        c = (a + b) / 2
        mb.box(T(c.x, c.y, z0 + h - 0.1) @ Rz(math.atan2(b.y - a.y, b.x - a.x)) @ S((b - a).length + 0.3, 0.3, 0.28),
               "teak")
    mb.box(T(0, 0, z0 + h + 0.02) @ S(2 * X + 0.2, 2 * Y + 0.2, 0.1), "teak_dk")     # veranda ceiling
    cX, cY = X - ci, Y - ci
    cs = [(-cX, -cY), (cX, -cY), (cX, cY), (-cX, cY)]
    for s in range(4):
        wall_panel(mb, cs[s], cs[(s + 1) % 4], z0, h - 0.1, style, rng, OUTWARD[s], door=s in doors)


def make_hall(name, coll, W, D, seed, storeys, plinth=0.8, o=0.9, top_pitch=43.0, skirt_pitch=34.0,
              gable=0.42, bay=None, sp=2.3):
    """Kerala palace hall, ridge along local X, front toward local -Y.
    storeys: [(kind, height, wall style, inset from the storey below)], ground first.
    Each storey below the top gets a tile skirt that rises to the next storey's wall;
    the top storey gets the hip-and-gable roof.
    bay: dict(x=centre along X, w=width, p=projection) adds a projecting balcony with
    its own carved gable on the front of the top storey (the king's veranda).
    Returns (object, anchors) with anchors["king"] in local coordinates."""
    rng = random.Random(seed)
    mb = kit.MB()
    X, Y = W / 2, D / 2
    anchors = {}
    # plinth with a moulded top and steps front and back
    mb.box(T(0, 0, plinth / 2) @ S(W + 1.2, D + 1.2, plinth), "laterite_dk")
    mb.box(T(0, 0, plinth - 0.06) @ S(W + 1.4, D + 1.4, 0.14), "granite")
    mb.box(T(0, 0, 0.08) @ S(W + 1.5, D + 1.5, 0.16), "granite")
    for sy in (-1, 1):
        for k in range(4):
            zz = plinth * (k + 1) / 4
            mb.box(T(0, sy * (D / 2 + 0.6 + 0.3 * (3 - k) + 0.15), zz / 2) @ S(2.4, 0.32, zz), "granite")
    z = plinth
    for k, (kind, h, style, inset) in enumerate(storeys):
        last = k == len(storeys) - 1
        skip = None
        if last and bay:
            bx, bw = bay["x"], bay["w"]
            skip = lambda s, p, q: s == 0 and abs((p.x + q.x) / 2 - bx) < bw / 2
        storey(mb, rng, X, Y, z, h, kind, style, sp=sp, skip=skip)
        zt = z + h
        if not last:
            r = o + storeys[k + 1][3]
            z = roof_skirt(mb, rng, 0, 0, zt, X + o, Y + o, r, skirt_pitch)
            X, Y = X - storeys[k + 1][3], Y - storeys[k + 1][3]
        else:
            anchors["ridge"] = roof_hipgable(mb, rng, 0, 0, zt, X + o, Y + o, top_pitch, gable)
            if bay:
                _bay(mb, rng, bay, X, Y, z, h, o, top_pitch, anchors)
    return mb.obj(name, coll), anchors


def _bay(mb, rng, bay, X, Y, z, h, o, top_pitch, anchors):
    """Projecting balcony on the front (-Y) of the top storey, posts down to the
    ground, balustrade on three sides, carved pillars and a cross-gable roof whose
    sunburst gable faces out (K19b)."""
    bx, bw, bp = bay["x"], bay["w"], bay["p"]
    y0, y1 = -Y, -Y - bp                                   # back (storey outline) and front of the bay
    zt = z + h
    # floor: slab, deep fascia beam and joist ends
    mb.box(T(bx, (y0 + y1) / 2, z - 0.06) @ S(bw + 0.3, bp + 0.2, 0.2), "floor")
    mb.box(T(bx, y1 - 0.06, z - 0.28) @ S(bw + 0.4, 0.2, 0.42), "teak")
    for sx in (-1, 1):
        mb.box(T(bx + sx * (bw / 2 + 0.12), (y0 + y1) / 2, z - 0.28) @ S(0.2, bp + 0.2, 0.42), "teak")
    for k in range(int(bw / 0.45)):
        mb.box(T(bx - bw / 2 + 0.3 + k * 0.45, y1 - 0.18, z - 0.52) @ S(0.1, 0.24, 0.1), "teak_dk")
    # posts to the ground with brackets under the floor
    for sx in (-1, 1):
        px = bx + sx * (bw / 2 - 0.05)
        pillar(mb, px, y1 + 0.12, 0.0, z - 0.45, w=0.3)
        bracket(mb, px, y1 + 0.12, z - 0.45, (0, 1), size=0.9)
        bracket(mb, px, y1 + 0.12, z - 0.45, (-sx, 0), size=0.7)
        pillar(mb, px, y1 + 0.12, z, h, w=0.27)
        bracket(mb, px, y1 + 0.12, zt, (-sx, 0), size=0.75)
        bracket(mb, px, y1 + 0.12, zt, (0, 1), size=0.6)
        railing(mb, (px, y1 + 0.3), (px, y0 - 0.15), z)
    railing(mb, (bx - bw / 2 + 0.2, y1 + 0.12), (bx + bw / 2 - 0.2, y1 + 0.12), z)
    mb.box(T(bx, y1 + 0.12, zt - 0.12) @ S(bw + 0.3, 0.3, 0.3), "teak")
    mb.box(T(bx, (y0 + y1) / 2, zt + 0.02) @ S(bw + 0.2, bp + 0.3, 0.1), "teak_dk")
    # cross-gable roof: ridge along Y, eaves level with the main roof's
    o2 = 0.55
    Xb = bw / 2 + o2
    Hb = Xb * math.tan(math.radians(45.0))
    yf = y1 - 0.75                                        # gable overhang
    ym = -(Y + o)                                         # main roof eave line
    yv = ym + Hb / math.tan(math.radians(top_pitch))      # where the bay ridge meets the main roof
    zr = zt + Hb
    for sx in (-1, 1):
        tile_plane(mb, [Vector((bx + sx * Xb, yf, zt)), Vector((bx + sx * Xb, ym, zt)),
                        Vector((bx, yv, zr)), Vector((bx, yf, zr))], rng)
    ridge_cap(mb, (bx, yf - 0.05, zr), (bx, yv, zr), r=0.16)
    _eave_fascia(mb, [Vector((bx - Xb, yf, zt)), Vector((bx + Xb, yf, zt)), Vector((bx + Xb, ym, zt)),
                      Vector((bx - Xb, ym, zt))])
    out = Vector((0, -1, 0))
    carved_gable(mb, (bx, y1 - 0.2, zt + 0.12), Xb - 0.45, Hb - 0.45, out, rays=11)
    bargeboards(mb, (bx - Xb, yf + 0.05, zt - 0.02), (bx, yf + 0.05, zr), (bx + Xb, yf + 0.05, zt - 0.02), out)
    anchors["king"] = Vector((bx - 0.35, y1 + 0.75, z + 0.04))


def make_pavilion(name, coll, w=4.4, seed=0, h=2.6):
    """Small open pavilion (mandapam): raised platform, four pillars, steep tile roof."""
    rng = random.Random(seed)
    mb = kit.MB()
    mb.box(T(0, 0, 0.3) @ S(w + 0.8, w + 0.8, 0.6), "granite")
    mb.box(T(0, 0, 0.62) @ S(w + 0.6, w + 0.6, 0.06), "granite_dk")
    for k in range(3):
        mb.box(T(0, -(w / 2 + 0.55 + 0.25 * (2 - k)), 0.1 + 0.2 * k) @ S(1.8, 0.3, 0.2 + 0.4 * k), "granite")
    X = w / 2 - 0.2
    for sx in (-1, 1):
        for sy in (-1, 1):
            pillar(mb, sx * X, sy * X, 0.65, h)
            bracket(mb, sx * X, sy * X, 0.65 + h, (-sx, 0))
            bracket(mb, sx * X, sy * X, 0.65 + h, (0, -sy))
    for s in range(4):
        a = s * math.pi / 2
        mb.box(Rz(a) @ T(0, -X, 0.65 + h - 0.1) @ S(2 * X + 0.3, 0.3, 0.28), "teak")
    mb.box(T(0, 0, 0.65 + h + 0.02) @ S(2 * X + 0.2, 2 * X + 0.2, 0.1), "teak_dk")
    roof_hipgable(mb, rng, 0, 0, 0.65 + h, X + 0.8, X + 0.75, 46.0, gable=0.3, ext=0.25)
    return mb.obj(name, coll)


# ========================================================== walls and gate
def make_laterite_wall(name, coll, segs, h=WALL_H, t=WALL_T, seed=0):
    """Laterite boundary wall along [(p0, p1)]: a core with staggered block courses
    standing proud on both faces, a stone footing and a coping."""
    rng = random.Random(seed)
    mb = kit.MB()
    for p0, p1 in segs:
        p0, p1 = Vector((*p0, 0)), Vector((*p1, 0))
        d = p1 - p0
        L = d.length
        d.normalize()
        nrm = UP.cross(d)
        F = kit.frame_matrix(p0, d, nrm, UP)
        mb.box(F @ T(L / 2, 0, h / 2 - 0.3) @ S(L + t, t, h + 0.6), "laterite_dk")
        mb.box(F @ T(L / 2, 0, h + 0.09) @ S(L + t + 0.12, t + 0.14, 0.18), "laterite_dk")
        mb.box(F @ T(L / 2, 0, 0.12) @ S(L + t + 0.1, t + 0.24, 0.3), "laterite_dk")
        ch = 0.42
        for row in range(int((h - 0.3) / ch)):
            zc = 0.3 + ch * (row + 0.5)
            for side in (-1, 1):
                a = -t / 2 + (row % 2) * 0.45 + rng.uniform(-0.1, 0.1)
                while a < L + t / 2 - 0.1:
                    bl = rng.uniform(0.75, 1.05)
                    a0, a1 = max(a, -t / 2), min(a + bl, L + t / 2)
                    if a1 - a0 > 0.15:
                        m = rng.choice(("laterite", "laterite", "laterite_lt", "laterite_dk"))
                        mb.box(F @ T((a0 + a1) / 2, side * (t / 2 + 0.015), zc) @
                               S(a1 - a0 - 0.05, 0.05, ch - 0.05), m)
                    a += bl
    return mb.obj(name, coll)


def make_gatehouse(name, coll, seed=0, gw=GATE_W):
    """Gate in the south wall: laterite piers, open teak doors, and a pillared
    gate hall with a carved hip-and-gable roof straddling the wall. Faces -Y."""
    rng = random.Random(seed)
    mb = kit.MB()
    for sx in (-1, 1):
        x = sx * (gw / 2 + 0.75)
        mb.box(T(x, 0, 2.1) @ S(1.5, 1.6, 4.2), "laterite")
        mb.box(T(x, 0, 4.28) @ S(1.7, 1.8, 0.18), "laterite_dk")
        # door leaves, swung open inward
        hinge = Vector((sx * gw / 2, 0.3, 0))
        a = sx * 1.25
        M = T(hinge) @ Rz(a) @ T(-sx * gw / 4, 0, 1.6)
        mb.box(M @ S(gw / 2, 0.12, 3.1), "teak")
        for k in range(4):
            mb.box(M @ T(0, -0.08, -1.2 + k * 0.8) @ S(gw / 2 - 0.1, 0.05, 0.1), "teak_dk")
        for k in range(3):
            for j in range(3):
                mb.ico(M @ T(-gw / 6 + j * gw / 6, -0.1, -0.8 + k * 0.8), "brass", r=0.05, sub=1)
    mb.box(T(0, 0, 3.55) @ S(gw + 0.4, 1.2, 0.3), "teak")
    X, Y = gw / 2 + 1.6, 2.4
    for sx in (-1, 1):
        for sy in (-1, 1):
            pillar(mb, sx * X, sy * Y, 0.0, 3.9, w=0.27)
            bracket(mb, sx * X, sy * Y, 3.9, (0, -sy))
    for sy in (-1, 1):
        mb.box(T(0, sy * Y, 3.8) @ S(2 * X + 0.3, 0.3, 0.3), "teak")
    for sx in (-1, 1):
        mb.box(T(sx * X, 0, 3.8) @ S(0.3, 2 * Y + 0.3, 0.3), "teak")
    mb.box(T(0, 0, 3.98) @ S(2 * X, 2 * Y, 0.1), "teak_dk")
    # roof turned so its carved gables face out of and into the compound
    rmb = kit.MB()
    roof_hipgable(rmb, rng, 0, 0, 3.95, Y + 0.9, X + 0.9, 45.0, gable=0.45)
    rmb.bm.transform(Rz(math.pi / 2))
    ob = mb.obj(name, coll)
    r = rmb.obj(name + "Roof", coll, parent=ob)
    return ob


# ================================================================ temple tank
def make_tank(name, coll, seed=0):
    """Stepped temple tank: granite step rings going down to the water, a coping
    round the top, steep stair flights down the north and long sides, faceted water."""
    rng = random.Random(seed)
    mb = kit.MB()
    bot = -3.9
    for k in range(TANK_STEPS):
        x0, x1, y0, y1 = tank_rect(k)
        ix0, ix1, iy0, iy1 = tank_rect(k + 1)
        top = -k * STEP_H
        m = "granite" if k % 2 == 0 else "granite_dk"
        hz = top - bot
        zc = (top + bot) / 2
        mb.box(T((x0 + x1) / 2, (y0 + iy0) / 2, zc) @ S(x1 - x0, iy0 - y0, hz), m)
        mb.box(T((x0 + x1) / 2, (iy1 + y1) / 2, zc) @ S(x1 - x0, y1 - iy1, hz), m)
        mb.box(T((x0 + ix0) / 2, (iy0 + iy1) / 2, zc) @ S(ix0 - x0, iy1 - iy0, hz), m)
        mb.box(T((ix1 + x1) / 2, (iy0 + iy1) / 2, zc) @ S(x1 - ix1, iy1 - iy0, hz), m)
        # a lip on each step edge
        mb.box(T((ix0 + ix1) / 2, iy0 - 0.05, top + 0.02) @ S(ix1 - ix0 + 0.1, 0.12, 0.06), "granite_dk")
        mb.box(T((ix0 + ix1) / 2, iy1 + 0.05, top + 0.02) @ S(ix1 - ix0 + 0.1, 0.12, 0.06), "granite_dk")
    x0, x1, y0, y1 = tank_rect(0)
    c = 1.2
    for (cx, cy, sx, sy) in [((x0 + x1) / 2, y0 - c / 2, x1 - x0 + 2 * c, c), ((x0 + x1) / 2, y1 + c / 2, x1 - x0 + 2 * c, c),
                             (x0 - c / 2, (y0 + y1) / 2, c, y1 - y0), (x1 + c / 2, (y0 + y1) / 2, c, y1 - y0)]:
        mb.box(T(cx, cy, -0.15) @ S(sx, sy, 0.6), "granite")
        mb.box(T(cx, cy, 0.17) @ S(sx + 0.05, sy + 0.05, 0.06), "granite_dk")
    # stair flights: (start on the rim, inward direction)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    flights = [((cx, y1), (0, -1), 2.6), ((cx - 7, y0), (0, 1), 1.8), ((cx + 7, y0), (0, 1), 1.8),
               ((x0, cy), (1, 0), 1.8), ((x1, cy), (-1, 0), 1.8)]
    for (px, py), (dx, dy), fw in flights:
        d = Vector((dx, dy, 0))
        side = Vector((-dy, dx, 0))
        p = Vector((px, py, 0))
        n = int((-WATER_Z + 0.3) / 0.2)
        for j in range(n):
            zt = -0.2 * (j + 1) + 0.05
            q = p + d * (0.26 * (j + 0.5))
            mb.box(T(q.x, q.y, (zt + bot) / 2) @ Rz(math.atan2(dy, dx)) @ S(0.27, fw, zt - bot), "granite")
        for s in (-1, 1):                                      # sloping side walls
            a = p + side * s * (fw / 2 + 0.2)
            b = a + d * (0.26 * n)
            mb.seg(a + UP * 0.2, b + UP * (-0.2 * n + 0.35), 0.17, 0.17, "granite_dk", sides=4, spin=math.pi / 4)
    # water: faceted, slightly jittered
    wx0, wx1, wy0, wy1 = tank_rect(4)
    nx, ny = 14, 8
    rows = []
    for j in range(ny + 1):
        rows.append([mb.bm.verts.new((wx0 + (wx1 - wx0) * i / nx + (rng.uniform(-0.15, 0.15) if 0 < i < nx else 0),
                                      wy0 + (wy1 - wy0) * j / ny + (rng.uniform(-0.15, 0.15) if 0 < j < ny else 0),
                                      WATER_Z + rng.uniform(-0.025, 0.025)))
                     for i in range(nx + 1)])
    for j in range(ny):
        for i in range(nx):
            mb.face([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]], "water")
    return mb.obj(name, coll)


# ================================================================ town houses
def make_house(name, coll, w=6.5, d=5.0, seed=0, veranda=False, gable=0.3, wall="plaster", h=2.7):
    """Kerala town house: low stone plinth, plastered walls with wooden posts,
    door and barred windows, steep tiled hip(-and-gable) roof. Door faces -Y."""
    rng = random.Random(seed)
    mb = kit.MB()
    pl = 0.45
    mb.box(T(0, 0, pl / 2 - 0.1) @ S(w + 0.6, d + 0.6, pl + 0.2), "laterite_dk")
    vd = 1.5 if veranda else 0.0
    y0 = -d / 2 + vd
    cs = [(-w / 2, y0), (w / 2, y0), (w / 2, d / 2), (-w / 2, d / 2)]
    for s in range(4):
        wall_panel(mb, cs[s], cs[(s + 1) % 4], pl, h, wall, rng, OUTWARD[s], door=(s == 0), thick=0.22)
    if veranda:
        for x in (-w / 2 + 0.15, -w / 6, w / 6, w / 2 - 0.15):
            pillar(mb, x, -d / 2 + 0.15, pl, h, w=0.18)
        mb.box(T(0, -d / 2 + 0.15, pl + h - 0.1) @ S(w + 0.2, 0.22, 0.22), "teak")
        mb.box(T(0, -d / 2 + vd / 2, pl + h + 0.02) @ S(w, vd, 0.08), "teak_dk")
    mb.box(T(0, 0, pl + h + 0.02) @ S(w, d, 0.08), "teak_dk")
    roof_hipgable(mb, rng, 0, 0, pl + h, w / 2 + 0.6, d / 2 + 0.6, rng.uniform(38, 44), gable=gable,
                  ext=0.3, tile=dict(tw=0.5, tl=0.56, step=0.43), carve=gable > 0.15)
    return mb.obj(name, coll)


# ===================================================================== plants
def make_banana(name, coll, seed=0, height=2.4):
    """Banana plant: a short ringed pseudo-stem and a few huge arching leaves."""
    rng = random.Random(seed)
    mb = kit.MB()
    mb.seg((0, 0, 0), (0, 0, height), 0.16, 0.11, "banana_dk", sides=6)
    nf = rng.randint(6, 8)
    for k in range(nf):
        a = k * TAU / nf + rng.uniform(-0.3, 0.3)
        kit._frond(mb, (0, 0, height), a, math.radians(rng.uniform(35, 65)), rng.uniform(1.8, 2.4),
                   rng.uniform(0.38, 0.48), math.radians(rng.uniform(60, 100)),
                   "banana" if rng.random() > 0.4 else "banana_dk", rng, steps=5, fold=0.2)
    return mb.obj(name, coll)


# ===================================================================== people
def make_young_king(name, coll, seed=0):
    """Marthanda Varma at about 24: the kit king, slimmer and a touch shorter in the
    body, hands forward resting toward the balustrade. Faces +Y."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=kit.FIG_BEVEL)
    pose = {"body": T(0, 0, 0) @ S(0.88, 0.92, 1.0),
            "legL": T(0.088, 0, 0.88) @ S(0.9, 0.92, 1.0), "legR": T(-0.088, 0, 0.88) @ S(0.9, 0.92, 1.0),
            "armL": T(0.24, 0, 1.4) @ Rx(0.32) @ Ry(0.06) @ S(0.88, 0.9, 1.0),
            "armR": T(-0.24, 0, 1.4) @ Rx(0.32) @ Ry(-0.06) @ S(0.88, 0.9, 1.0)}
    kit._draw_figure(lambda p: (mb, pose[p]), "king", rng)
    return mb.obj(name, coll)


# ================================================================== assembly
def _put(src, name, coll, x, y, rz=0.0, s=1.0, sink=0.05, z=None):
    return kit.instance(src, name, coll, (x, y, (height(x, y) if z is None else z) - sink), rot_z=rz, scale=s)


def _place(ob, x, y, rz, z=0.0):
    ob.location = (x, y, z)
    ob.rotation_euler[2] = rz
    return ob


def to_world(local, centre, rz):
    v = Vector(local)
    c, s = math.cos(rz), math.sin(rz)
    return Vector((centre[0] + v.x * c - v.y * s, centre[1] + v.x * s + v.y * c, v.z))


def build_palace(coll, lib_c, plants, frames):
    """The walled palace: halls, gate, pavilion, courtyard planting and people.
    Returns anchors (world space)."""
    anchors = {}
    # main hall: three tiers
    a, _ = make_hall("HallA", coll, 19.0, 13.0, 1,
                     [("pillared", 3.2, "wood", 0), ("band", 2.5, "wood", 1.6), ("band", 2.2, "wood", 1.5)])
    _place(a, *HALL_A)
    # the king's hall: carved upper veranda with the projecting bay facing the courtyard
    b, anc = make_hall("HallB", coll, 24.0, 11.0, 2,
                       [("pillared", 3.0, "wood", 0), ("veranda", 2.75, "plaster_y", 1.6)],
                       bay=dict(x=8.0, w=4.2, p=2.3))
    _place(b, *HALL_B)
    anchors["king"] = to_world(anc["king"], HALL_B[:2], HALL_B[2])
    c, _ = make_hall("HallC", coll, 14.0, 10.0, 3,
                     [("pillared", 3.0, "wood", 0), ("band", 2.4, "wood", 1.5)], top_pitch=45.0)
    _place(c, *HALL_C)
    # single-storey ranges: front (south, facing the courtyard), north-west, kitchen block
    for nm, (x, y, rz, W, D, seed) in {"RangeS": (2.0, -18.5, math.pi, 20.0, 7.0, 4),
                                        "RangeNW": (-21.0, 16.5, 0.0, 15.0, 7.5, 5),
                                        "RangeNE": (16.0, 20.0, 0.0, 12.0, 6.0, 6)}.items():
        r, _ = make_hall(nm, coll, W, D, seed, [("pillared", 3.0, "plaster", 0)], plinth=0.6, gable=0.38)
        _place(r, x, y, rz)
    _place(make_pavilion("Pavilion", coll, seed=7), -5.5, -6.0, 0.0)

    # laterite wall with the gate gap, and the gate house
    x0, x1, y0, y1 = WALL
    g0, g1 = GATE_X - GATE_W / 2 - 1.5, GATE_X + GATE_W / 2 + 1.5
    segs = [((x0, y0), (g0, y0)), ((g1, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    make_laterite_wall("LateriteWall", coll, segs)
    _place(make_gatehouse("GateHouse", coll), GATE_X, y0, 0.0)

    # courtyard planting: palms in raised stone beds, banana clumps, bushes
    def bed(x, y, w, d):
        mb = kit.MB()
        mb.box(T(0, 0, 0.18) @ S(w, d, 0.36), "granite")
        mb.box(T(0, 0, 0.3) @ S(w - 0.3, d - 0.3, 0.2), "grass")
        _place(mb.obj(f"Bed{x:.0f}_{y:.0f}", coll), x, y, 0.0)
    rng = random.Random(41)
    for x, y, w, d in [(21.5, -19.8, 3.2, 2.4), (13.5, 2.5, 3.2, 5.0), (-9.0, 13.0, 3.0, 3.0), (-12.0, -18.0, 3.0, 2.4)]:
        bed(x, y, w, d)
        for k in range(2):
            _put(plants["bushes"][k % 3], f"BedBush{x:.0f}{k}", coll, x + rng.uniform(-w / 3, w / 3),
                 y + rng.uniform(-d / 3, d / 3), rng.uniform(0, 6), rng.uniform(0.6, 0.9), z=0.4)
    court_palms = [(21.3, -20.0), (14.6, 3.6), (-9.0, 13.2), (30.8, -18.5), (31.5, 15.0), (-31.0, 21.0),
                   (-30.5, -21.5), (25.0, -20.5), (-12.0, -18.0), (10.0, -23.0)]
    for i, (x, y) in enumerate(court_palms):
        _put(plants["palms"][i % len(plants["palms"])], f"CourtPalm{i}", coll, x, y, rng.uniform(0, 6.3),
             rng.uniform(0.85, 1.05), z=0.3)
    for i, (x, y) in enumerate([(-33.0, 0.0), (-32.5, 8.0), (33.0, 4.0), (33.2, -10.0), (-2.0, 23.0), (8.0, 23.5),
                                (-28.0, -22.0), (27.0, 23.0)]):
        _put(plants["bananas"][i % 3], f"CourtBanana{i}", coll, x, y, rng.uniform(0, 6.3), rng.uniform(0.9, 1.15))
    return anchors


def build_town(coll, lib_c, plants, seed=11):
    """Houses along the roads outside the wall, the temple tank, and the trees."""
    rng = random.Random(seed)
    houses = [make_house(f"LibHouse{i}", lib_c, w=w, d=d, seed=20 + i, veranda=v, gable=g, wall=wl)
              for i, (w, d, v, g, wl) in enumerate([(6.5, 5.0, False, 0.0, "plaster"),
                                                    (7.5, 5.5, True, 0.35, "plaster"),
                                                    (5.6, 4.6, False, 0.3, "plaster_g"),
                                                    (8.0, 6.0, True, 0.0, "plaster_g"),
                                                    (6.0, 5.0, False, 0.35, "plaster"),
                                                    (9.0, 6.0, False, 0.3, "plaster")])]
    make_tank("TempleTank", coll)
    spots = []
    for pts, hw in ROADS:
        for a, b in zip(pts, pts[1:]):
            a, b = Vector(a), Vector(b)
            L = (b - a).length
            d = (b - a).normalized()
            nrm = Vector((-d.y, d.x))
            s = rng.uniform(2, 6)
            while s < L:
                for side in (-1, 1):
                    if rng.random() < 0.18:
                        continue
                    off = hw + rng.uniform(5.0, 7.0)
                    p = a + d * s + nrm * side * off
                    spots.append((p, -nrm * side))
                s += rng.uniform(10.0, 14.0)
    placed = []
    for p, face in spots:
        x, y = p
        if math.hypot(x, y * 1.2) > 175 or height(x, y) > 2.5:
            continue
        if _rect_dist(x, y, *WALL) < 13 or in_tank(x, y, 6.0) or road_dist(x, y) < 3.5:
            continue
        if any((p - q).length < 10.0 for q in placed):
            continue
        placed.append(p)
        rz = math.atan2(face.x, -face.y) + rng.uniform(-0.12, 0.12)
        _put(houses[len(placed) % len(houses)], f"House{len(placed)}", coll, x, y, rz, rng.uniform(0.92, 1.08),
             sink=0.1)
    # trees: palms near the town, round trees and banana clumps, forest up the hills
    k = 0
    for i in range(9000):
        x, y = rng.uniform(-330, 330), rng.uniform(-200, 420)
        z = height(x, y)
        if z > 14 + 30 * max(0.0, _n(x, y, 60.0, 2.2)) or _rect_dist(x, y, *WALL) < 2.5 or in_tank(x, y, 3.0) or road_dist(x, y) < 1.2:
            continue
        if any((Vector((x, y)) - q).length < 6.0 for q in placed if abs(q.x - x) < 7 and abs(q.y - y) < 7):
            continue
        dist = math.hypot(x, y)
        if dist < 160 and _n(x, y, 25.0, 6.6) < -0.3:
            continue                                           # keep some clearings in the town
        if dist > 160 and rng.random() < 0.55:
            continue
        r = rng.random()
        if z > 25:
            src, sc = plants["trees"][k % 4], rng.uniform(1.2, 1.8)
        elif r < 0.48:
            src, sc = plants["palms"][k % len(plants["palms"])], rng.uniform(0.85, 1.25)
        elif r < 0.85:
            src, sc = plants["trees"][k % 4], rng.uniform(0.9, 1.35)
        else:
            src, sc = plants["bananas"][k % 3], rng.uniform(0.9, 1.3)
        _put(src, f"Tree{k}", coll, x, y, rng.uniform(0, 6.3), sc, sink=0.15)
        k += 1
    return placed


def build_people(coll, frames, anchors, seed=5):
    rng = random.Random(seed)
    # guards with spears at the gate, outside and inside
    for i, (x, y, rz) in enumerate([(GATE_X - 2.0, WALL[2] - 2.6, math.pi), (GATE_X + 2.0, WALL[2] - 2.6, math.pi),
                                    (GATE_X - 1.7, WALL[2] + 1.6, math.pi), (GATE_X + 1.7, WALL[2] + 1.6, math.pi),
                                    (15.6, -10.2, math.pi / 2), (15.6, -3.8, math.pi / 2)]):
        g = kit.make_figure(f"Guard{i}", coll, "nair_spear", seed=i)
        _place(g, x, y, rz, height(x, y) if abs(y) > 26 else 0.0)
        kit.animate_idle(g, rng, 1, frames, 0.02)
    # courtiers in the courtyard
    for i, (x, y, rz, cl) in enumerate([(-2.0, -0.6, 0.4, "cloth_w"), (-1.2, -1.4, 2.6, "cloth_w"),
                                        (4.0, -9.0, 1.9, "cloth_t")]):
        f = kit.make_figure(f"Courtier{i}", coll, "villager", seed=10 + i, cloth=cl)
        _place(f, x, y, rz)
        kit.animate_idle(f, rng, 1, frames, 0.03)
    # townspeople walking the roads (about 1 m/s)
    walks = [([(-17, -37), (-23.5, -57)], "cloth_w", False), ([(-25.5, -66), (-19.0, -43)], "cloth_t", True),
             ([(-30, -34.5), (-8, -34.5)], "cloth_r", False), ([(10, -33.5), (-6, -33.5)], "cloth_w", True),
             ([(44.5, -20), (44.5, 0)], "cloth_w", False), ([(-44, 12), (-43.5, -8)], "cloth_t", False),
             ([(52, 5.5), (70, 7.5)], "cloth_w", True), ([(30, -35), (40, -55)], "cloth_r", False),
             ([(-15.5, -27.5), (-16.2, -36)], "cloth_w", False)]
    for i, (wp, cl, robe) in enumerate(walks):
        root, parts = kit.make_villager(f"Walker{i}", coll, seed=30 + i, robe=robe, cloth=cl)
        kit.animate_walk(root, parts, wp, height, start=1, end=frames, stride_frames=14 + (i % 3) * 2, speed=1.0)
    # the king on his veranda, facing the courtyard (+Y of the figure turned to world -X)
    king = make_young_king("Marthanda Varma", coll)
    p = anchors["king"]
    _place(king, p.x, p.y, math.pi / 2 + 0.35, p.z)
    kit.animate_idle(king, rng, 1, frames, 0.015)
    return king


def add_mist_box(collection, name, center, size, density, color=(0.97, 0.92, 0.86)):
    """A bounded volume of haze (a world volume blacks out EEVEE, so haze is an object)."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*kit.srgb_to_linear(color), 1)
    vol.inputs["Density"].default_value = density
    vol.inputs["Anisotropy"].default_value = 0.4
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    mb = kit.MB()
    mb.box(T(*center) @ S(*size), name)
    ob = mb.obj(name, collection)
    ob.data.materials[0] = m
    ob.display_type = "BOUNDS"
    return ob


def build_world(frames):
    register_palette()
    world_c = kit.new_collection("World")
    palace_c = kit.new_collection("Palace")
    town_c = kit.new_collection("Town")
    people_c = kit.new_collection("People")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    make_terrain(world_c)
    w = cw.setup_world()
    for nd in w.node_tree.nodes:                     # less sky fill: crisper sun and shadow
        if nd.bl_idname == "ShaderNodeBackground":
            nd.inputs["Strength"].default_value = 0.7
    # haze only in the distance, over the hills (the town itself stays crisp, as in K19a)
    for i, (ctr, size, dens) in enumerate([((-150, 420, 150), (1300, 560, 420), 0.0030),     # north-west, the hills behind
                                           ((-520, 60, 150), (560, 760, 420), 0.0030),       # west
                                           ((150, 900, 200), (2400, 600, 500), 0.0035),      # far north
                                           ((560, 200, 150), (500, 1000, 420), 0.0026)]):    # east
        add_mist_box(world_c, f"FarMist{i}", ctr, size, dens)
    cw.add_sun(rig_c, direction=(0.85, 0.35, -0.42), energy=9.5, color=(1.0, 0.87, 0.72), angle=3.0)
    plants = dict(palms=[kit.make_palm(f"LibPalm{i}", lib_c, seed=i, height=8.0 + 0.6 * i) for i in range(6)],
                  trees=[kit.make_tree(f"LibTree{i}", lib_c, seed=i, height=6.5 + i) for i in range(4)],
                  bushes=[kit.make_bush(f"LibBush{i}", lib_c, seed=i, size=1.0 + 0.2 * i) for i in range(3)],
                  bananas=[make_banana(f"LibBanana{i}", lib_c, seed=i, height=2.2 + 0.3 * i) for i in range(3)])
    anchors = build_palace(palace_c, lib_c, plants, frames)
    build_town(town_c, lib_c, plants)
    king = build_people(people_c, frames, anchors)
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c, anchors, king
