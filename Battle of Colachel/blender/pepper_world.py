"""Pepper hills (S09): a terraced pepper garden in the foothills, and the river jetty
where the pepper goes onto a ship.

Laid out to match the Flow reference frames/flow_refs/K11a_v1 with the camera looking
north (+Y) up the hill: a dirt drying yard with round trays and baskets of black
pepper, a raised grass mound with a curved stone wall on the right, stone-walled
terraces climbing to the left and back with vine-wrapped trees, a thatched mud hut on
the first terrace, palms and jungle trees, and misty faceted hills behind. The ground
falls away west (-X) into a river valley; the ship waits at a jetty there for the
last sentence ("Ships have come for it for centuries").

Coordinates: metres, Z up. The drying yard is at z = 0, the river surface at WATER_Z.
New assets (pepper vines, baskets, trays, mats, pots, pepper sacks) are defined here
in the colachel_kit style: flat-shaded bmesh builds, library objects instanced.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

import colachel_kit as kit
import colachel_world as cw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau

# extra colours for this set (the greens and woods come from kit.PALETTE)
PALETTE = {
    "dirt":         (0.64, 0.47, 0.31),
    "dirt_dk":      (0.54, 0.40, 0.27),
    "grass_lt":     (0.46, 0.60, 0.18),
    "jungle":       (0.32, 0.46, 0.21),
    "far_hill":     (0.38, 0.52, 0.27),
    "bank":         (0.76, 0.64, 0.46),
    "river":        (0.46, 0.64, 0.62),
    "stone_lt":     (0.66, 0.63, 0.57),
    "stone_dk":     (0.47, 0.45, 0.42),
    "mud":          (0.64, 0.47, 0.32),
    "leaf_lt":      (0.38, 0.56, 0.21),
    "vine_leaf":    (0.19, 0.40, 0.13),
    "vine_leaf_lt": (0.30, 0.53, 0.17),
    "vine_stem":    (0.30, 0.34, 0.16),
    "berry_red":    (0.72, 0.09, 0.06),
    "berry_org":    (0.80, 0.30, 0.08),
    "berry_grn":    (0.42, 0.60, 0.16),
    "pepper":       (0.17, 0.12, 0.10),
    "pepper_br":    (0.30, 0.21, 0.15),
    "basket":       (0.78, 0.62, 0.38),
    "basket_dk":    (0.62, 0.47, 0.28),
    "tray":         (0.82, 0.68, 0.45),
    "mat_lt":       (0.84, 0.72, 0.48),
    "mat_dk":       (0.70, 0.57, 0.36),
    "clay":         (0.74, 0.38, 0.22),
    "clay_dk":      (0.58, 0.28, 0.16),
    "jute":         (0.56, 0.44, 0.30),
    "rope":         (0.52, 0.42, 0.28),
}


def register_palette():
    """Add this set's colours to the kit palette and create their materials
    (call after kit.reset_scene)."""
    for name, rgb in PALETTE.items():
        kit.PALETTE[name] = rgb
        kit.mat(name, rgb)


# ------------------------------------------------------------------- layout
WATER_Z = -7.0
BANK_Z = WATER_Z + 0.5
RIVER_HALF = 10.0               # half width of the river
GARDEN_EDGE = -9.5              # x where the yard starts to fall toward the river
# Measured off K11a: camera ~5.5 m above the yard, pitched ~9 deg down; trays 10-15 m
# ahead, hut ~20 m ahead on the first terrace, terraces climbing a hill behind it to
# the right, the right-hand mound's wall curving past the baskets toward the camera.
TERR_C = (8.6, 20.4)            # centre of the terraced hill
RINGS = (19.1, 13.6, 9.6, 6.0)  # terrace risers, outermost first
RISE = 1.3                      # height of one terrace step
WALL_H = 0.55                   # the stone-faced foot of each step; a grass bank rises above it
MOUND_C, MOUND_AX = (8.5, 1.5), (8.5, 9.0)     # raised grass mound right of the yard
YARD = (-2.8, -1.6)             # centre of the dirt drying yard
YARD_R = 7.4
HUT = (2.7, 4.6)                # mud hut on the first terrace
HUT2 = (-2.8, 17.8)             # a second, smaller hut up the terraces
PATH = ((-1.4, 0.2), (2.4, 2.5))   # dirt path from the yard up to the hut door
JETTY_Y = -6.0                  # the jetty runs west into the river at this y


def river_x(y):
    """x of the river's centre line (it runs roughly north-south)."""
    return -34.0 + 5.0 * math.sin(y / 37.0 + 0.6)


# The landing (K11b, frames/flow_refs/K11b.jpeg): a flat sandy bank at the jetty root
# with pepper stacked on it, a jetty out into the river, a small ship moored at its end.
LANDING_X = river_x(JETTY_Y) + RIVER_HALF + 1.2      # jetty root
JETTY_LEN = 13.0
SHIP_SCALE = 0.42                                    # kit East Indiaman scaled to a ~16 m trader
SHIP_ROT = 2.21                                      # heading: bow down-river, away to the left of the last shot (K11b)
LANDING = (LANDING_X - 1.5, LANDING_X + 6.5, JETTY_Y - 9.0, JETTY_Y + 7.0)
END_CAM = (LANDING_X + 5.2, JETTY_Y - 5.4)           # last camera position (ground x, y)
END_LOOK = (LANDING_X - 14.0, JETTY_Y + 5.0)         # and where it looks (the ship)


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


def _ss(e0, e1, x):
    """Smoothstep from e0 to e1 (either order)."""
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _down(t, edge, w=0.7):
    """1 inside a riser (t < edge), 0 outside, with a steep ramp of width w."""
    return _ss(edge + w / 2, edge - w / 2, t)


def _riser(t, R):
    """One terrace step at contour R: a low stone-faced wall at the foot (R + 0.9),
    then a grass bank climbing to the next tread (as in K11a)."""
    return WALL_H * _down(t, R + 0.9, 0.25) + (RISE - WALL_H) * _ss(R + 0.75, R - 0.9, t)


def terr_d(x, y):
    """Distance from the terrace hill centre, wobbled so the contours are not circles."""
    return math.hypot(x - TERR_C[0], y - TERR_C[1]) + 1.2 * _n(x, y, 14.0, 4.2)


def mound_e(x, y):
    """Signed distance (roughly metres) outside the mound's edge."""
    (cx, cy), (ax, ay) = MOUND_C, MOUND_AX
    return (math.hypot((x - cx) / ax, (y - cy) / ay) - 1.0) * min(ax, ay) + 0.6 * _n(x, y, 9.0, 2.7)


def garden_level(x, y):
    d = terr_d(x, y)
    terr = sum(_riser(d, R) for R in RINGS) + max(0.0, RINGS[-1] - d) * 0.3
    e = mound_e(x, y)
    mound = _riser(e, -0.9) + max(0.0, -e - 3.0) * 0.08
    return max(terr, mound)


def garden_mask(x):
    return _ss(GARDEN_EDGE - 7.0, GARDEN_EDGE + 1.0, x)


def height(x, y):
    xr = river_x(y)
    d = x - xr
    bank_d = abs(d) - RIVER_HALF
    if d >= 0:
        t = _ss(xr + RIVER_HALF + 1.5, GARDEN_EDGE, x)          # 0 at the bank, 1 in the garden
        h = BANK_Z * (1 - t) + garden_level(x, y) * garden_mask(x)
        # the hill behind the garden (not over the river valley, so the K11a view sees down it)
        h += max(0.0, y - 25.0) * 0.42 * _ss(-24.0, -8.0, x) + max(0.0, x - 19.0) * 0.38 \
            + max(0.0, -y - 24.0) * 0.12
        rough = 0.07 + 0.30 * (1 - t) * _ss(1.0, 4.0, bank_d)
    else:
        h = BANK_Z + max(0.0, bank_d - 2.0) * 0.14
        rough = 0.07 + 0.35 * _ss(1.0, 4.0, bank_d)
    # far hills: faceted ridges rising out of the haze
    D = math.hypot(x, y - 10.0)
    ridge = (1.0 - abs(_n(x, y, 150.0, 7.7))) ** 2
    h += _ss(60.0, 420.0, D) * (12.0 + 60.0 * ridge + 18.0 * _n(x, y, 60.0, 3.3)) + _ss(380.0, 900.0, D) * 70.0
    rough += _ss(40.0, 200.0, D) * 2.5
    h += rough * (_n(x, y, 5.0, 1.1) + 0.5 * _n(x, y, 2.3, 5.4))
    # the flat landing at the jetty root
    x0, x1, y0, y1 = LANDING
    dr = math.hypot(max(x0 - x, 0.0, x - x1), max(y0 - y, 0.0, y - y1))
    w = _ss(3.5, 0.0, dr)
    h = h * (1 - w) + (BANK_Z + 0.25 + 0.06 * _n(x, y, 3.0, 8.8)) * w
    # river channel
    c = _ss(RIVER_HALF + 0.8, RIVER_HALF - 1.5, abs(d))
    return h * (1 - c) + (WATER_Z - 2.5) * c


def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
    return math.hypot(px - ax - vx * t, py - ay - vy * t)


def is_dirt(x, y):
    """Bare earth: the drying yard, the hut terrace and the path between them."""
    if math.hypot(x - YARD[0], y - YARD[1]) < YARD_R + 1.6 * _n(x, y, 4.0, 0.7) and garden_level(x, y) < 0.4:
        return True
    if math.hypot((x - HUT[0]) / 1.3, y - HUT[1]) < 4.2 + 0.8 * _n(x, y, 3.0, 1.9) and \
            0.6 < garden_level(x, y) < 2.0:
        return True
    return _seg_dist(x, y, *PATH) < 1.0 + 0.3 * _n(x, y, 2.0, 3.0)


# ------------------------------------------------------------------ terrain
def _axis(edges, steps):
    """Grid coordinates: edges [a, b, c, ...] with a step size per interval."""
    out = []
    for (a, b), s in zip(zip(edges, edges[1:]), steps):
        n = max(1, round((b - a) / s))
        out += [(a + (b - a) * i / n, (b - a) / n) for i in range(n)]
    out.append((edges[-1], steps[-1]))
    return out


def make_terrain(collection, seed=3):
    rng = random.Random(seed)
    xs = _axis([-650, -110, -48, 34, 110, 650], [16, 3, 0.5, 3, 16])
    ys = _axis([-500, -90, -34, 50, 140, 900], [16, 3, 0.5, 3, 16])
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
    mats = ["grass", "grass_lt", "dirt", "dirt_dk", "jungle", "bank", "far_hill"]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        x, y, z = c
        D = math.hypot(x, y - 10.0)
        lvl = garden_level(x, y) * garden_mask(x)
        if (z < BANK_Z + 0.35 and abs(x - river_x(y)) < RIVER_HALF + 3.5) or \
                (LANDING[0] < x < LANDING[1] + 1.0 and LANDING[2] < y < LANDING[3]):
            m = "bank"
        elif D > 75:
            m = "far_hill" if _n(x, y, 40.0, 9.1) > -0.15 else "jungle"
        elif f.normal.z < 0.82 and lvl > 0.05 and x > GARDEN_EDGE - 2:
            m = "grass"                            # grass banks between the terraces
        elif is_dirt(x, y):
            m = "dirt"
        elif lvl > 0.6 and x > GARDEN_EDGE - 2:
            m = "grass_lt"                         # terrace treads and the mound
        elif f.normal.z < 0.8:
            m = "jungle"
        else:
            m = "grass"
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


def make_river(collection, seed=4):
    """Faceted river surface following river_x, with a little vertex jitter so the
    facets catch the light like the sea in the beach clips."""
    rng = random.Random(seed)
    mb = kit.MB()
    rows = []
    y = -420.0
    while y <= 700.0:
        step = 2.0 if -60 < y < 80 else 12.0
        xr = river_x(y)
        w = RIVER_HALF + 1.6
        row = []
        for k in range(9):
            u = -1 + 2 * k / 8
            row.append(mb.bm.verts.new((xr + u * w + rng.uniform(-0.25, 0.25) * (k not in (0, 8)),
                                        y, WATER_Z + rng.uniform(-0.03, 0.03))))
        rows.append(row)
        y += step
    for a, b in zip(rows, rows[1:]):
        for k in range(8):
            mb.face([a[k], a[k + 1], b[k + 1], b[k]], "river")
    bmesh.ops.triangulate(mb.bm, faces=mb.bm.faces[:])
    ob = mb.obj("River", collection)
    m = ob.data.materials[0]
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    return ob


# ------------------------------------------------------------ stone walls
def _terr_point(R, phi):
    """Point on terrace riser R in direction phi from the hill centre (solves the wobble)."""
    dx, dy = math.cos(phi), math.sin(phi)
    rho = R
    for _ in range(6):
        x, y = TERR_C[0] + dx * rho, TERR_C[1] + dy * rho
        rho = R - 1.2 * _n(x, y, 14.0, 4.2)
    return Vector((TERR_C[0] + dx * rho, TERR_C[1] + dy * rho, 0.0)), Vector((dx, dy, 0.0))


def _mound_point(phi):
    (cx, cy), (ax, ay) = MOUND_C, MOUND_AX
    k = 1.0
    for _ in range(6):
        x, y = cx + ax * math.cos(phi) * k, cy + ay * math.sin(phi) * k
        k = 1.0 - 0.6 * _n(x, y, 9.0, 2.7) / min(ax, ay)
    out = Vector((math.cos(phi) / ax, math.sin(phi) / ay, 0.0)).normalized()
    return Vector((cx + ax * math.cos(phi) * k, cy + ay * math.sin(phi) * k, 0.0)), out


def _wall_along(mb, pts, rng, gaps=()):
    """Dry-stone retaining wall along a sampled contour [(point, outward)]: staggered
    courses of rounded blocks from the lower ground up to just above the upper tread."""
    arc = [0.0]
    for (a, _), (b, _) in zip(pts, pts[1:]):
        arc.append(arc[-1] + (b - a).length)
    total = arc[-1]

    def at(s):
        i = 0
        while i < len(arc) - 2 and arc[i + 1] < s:
            i += 1
        u = (s - arc[i]) / max(1e-6, arc[i + 1] - arc[i])
        p = pts[i][0].lerp(pts[i + 1][0], u)
        tang = (pts[i + 1][0] - pts[i][0]).normalized()
        out = Vector((tang.y, -tang.x, 0.0))
        if out.dot(pts[i][1]) < 0:
            out = -out
        return p, tang, out

    course_h = 0.34
    for c in range(3):
        s = (c % 2) * 0.3 + rng.uniform(0, 0.1)
        while s < total:
            L = rng.uniform(0.42, 0.68)
            p, tang, out = at(min(total, s + L / 2))
            s += L
            if any((p - Vector((gx, gy, 0))).length < gr for gx, gy, gr in gaps):
                continue
            lo = height(*(p + out * 0.6).xy)
            hi = height(*(p - out * 0.5).xy)
            if hi - lo < 0.3:
                continue
            zc = lo - 0.12 + (c + 0.5) * course_h
            if zc - course_h / 2 > lo + WALL_H - 0.05:
                continue
            ctr = p + out * (0.12 + rng.uniform(-0.03, 0.04)) + Vector((0, 0, zc))
            M = kit.frame_matrix(ctr, -tang, out, Vector((0, 0, 1))) @ Rz(rng.uniform(-0.06, 0.06)) \
                @ S(L - 0.05, 0.46, course_h * rng.uniform(0.86, 0.98))
            mb.box(M, rng.choice(("stone", "stone", "stone_lt", "stone_dk")))


def build_walls(collection, seed=8):
    rng = random.Random(seed)
    gaps = [(*_path_crossing(), 1.0)]
    mb = kit.MB(bevel=0.05)
    for R in RINGS:
        pts = []
        phi = math.radians(-178)
        while phi < math.radians(-2):
            p, out = _terr_point(R + 0.9, phi)
            if -21.0 < p.x < 26.0 and garden_mask(p.x) > 0.5:
                pts.append((p, out))
            elif len(pts) > 1:
                _wall_along(mb, pts, rng, gaps)
                pts = []
            phi += 0.15 / R
        if len(pts) > 1:
            _wall_along(mb, pts, rng, gaps)
    pts = []
    phi = math.radians(60)
    while phi < math.radians(300):
        pts.append(_mound_point(phi))
        phi += 0.012
    _wall_along(mb, pts, rng, gaps)
    walls = mb.obj("StoneWalls", collection)
    # stone steps where the path climbs to the hut terrace
    cx, cy = _path_crossing()
    (ax, ay), (bx, by) = PATH
    fwd = Vector((bx - ax, by - ay, 0)).normalized()
    side = Vector((fwd.y, -fwd.x, 0))
    st = kit.MB(bevel=0.04)
    lo, hi = height(cx - fwd.x * 0.8, cy - fwd.y * 0.8), height(cx + fwd.x * 2.0, cy + fwd.y * 2.0)
    n = 5
    for k in range(n):
        p = Vector((cx, cy, 0)) + fwd * (-0.1 + k * 0.42)
        top = lo + (hi - lo) * (k + 1) / n
        st.box(kit.frame_matrix(Vector((p.x, p.y, (lo - 0.3 + top) / 2)), side, fwd, Vector((0, 0, 1)))
               @ S(1.5, 0.46, top - lo + 0.3), "stone_lt" if k % 2 else "stone")
    st.obj("PathSteps", collection)
    return walls


def _path_crossing():
    """Where the hut path meets the wall at the foot of the first step."""
    (ax, ay), (bx, by) = PATH
    lo, hi = 0.0, 1.0
    for _ in range(30):
        m = (lo + hi) / 2
        if garden_level(ax + (bx - ax) * m, ay + (by - ay) * m) < WALL_H / 2:
            lo = m
        else:
            hi = m
    return ax + (bx - ax) * lo, ay + (by - ay) * lo


# ============================================================== pepper vine
HEART = [(0.0, 0.10), (0.30, -0.04), (0.50, 0.20), (0.46, 0.48), (0.26, 0.76), (0.0, 1.0),
         (-0.26, 0.76), (-0.46, 0.48), (-0.50, 0.20), (-0.30, -0.04)]


def _heart(mb, base, d, side, n, L, W):
    """Heart-shaped pepper leaf, folded along the midrib: a light half and a dark half."""
    c = mb.bm.verts.new(base + d * (0.42 * L) + n * (0.07 * L))
    ring = [mb.bm.verts.new(base + side * (x * W) + d * (y * L) - n * (abs(x) * 0.14 * L)) for x, y in HEART]
    k = len(ring)
    for i in range(k):
        xm = HEART[i][0] + HEART[(i + 1) % k][0]
        mb.face([c, ring[i], ring[(i + 1) % k]], "vine_leaf_lt" if xm > 0 else "vine_leaf")


def _spike(mb, top, out, rng, length, scheme):
    """A hanging string of pepper berries."""
    n = max(4, int(length / 0.075))
    mb.seg(top + Vector((0, 0, 0.1)) - out * 0.08, top, 0.014, 0.014, "vine_stem", sides=3)
    for i in range(n):
        f = i / (n - 1)
        p = top + Vector((0, 0, -i * 0.075)) + out * (0.05 * f * f)
        r = 0.058 * (1.0 - 0.35 * f)
        for k in range(2):
            a = rng.uniform(0, TAU)
            q = p + Vector((math.cos(a), math.sin(a), 0)) * 0.032
            if scheme == "red":
                m = "berry_red" if rng.random() > 0.15 else "berry_org"
            elif scheme == "green":
                m = "berry_grn"
            else:
                m = "berry_grn" if rng.random() < 0.6 - 0.5 * f else "berry_red"
            mb.ico(T(q), m, r=r, sub=1)


def _vine(mb, path, radius, t0, t1, rng, leaves_per_m=10.0, spikes_per_m=2.0, leaf=1.0, strands=2,
          red=0.6):
    """Pepper vine climbing a trunk: helical stems, heart leaves hugging the trunk,
    and strings of red and green berries hanging from it. path(t) is the trunk's
    centre line (t in 0..1), radius(t) its radius."""
    up = Vector((0, 0, 1))

    def frame(t):
        t = max(0.0, min(1.0, t))
        tang = (path(min(1.0, t + 0.01)) - path(max(0.0, t - 0.01))).normalized()
        a = tang.cross(Vector((1, 0, 0)) if abs(tang.x) < 0.9 else Vector((0, 1, 0))).normalized()
        b = tang.cross(a)
        return path(t), tang, a, b

    def radial(t, ang):
        p, tang, a, b = frame(t)
        return p, tang, a * math.cos(ang) + b * math.sin(ang)

    pts = [path(t0 + (t1 - t0) * i / 30) for i in range(31)]
    length = sum((pts[i + 1] - pts[i]).length for i in range(30))
    for s in range(strands):                                    # stems
        a0 = rng.uniform(0, TAU)
        turns = length / rng.uniform(1.3, 2.2)
        n = int(length / 0.22) + 2
        prev = None
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            p, tang, out = radial(t, a0 + turns * TAU * i / n * (1 if s % 2 == 0 else -1))
            q = p + out * (radius(t) + 0.03)
            if prev is not None:
                mb.seg(prev, q, 0.03, 0.028, "vine_stem", sides=4)
            prev = q
    for i in range(int(length * leaves_per_m)):                 # leaves
        t = t0 + (t1 - t0) * (rng.random() ** 0.85)
        p, tang, out = radial(t, rng.uniform(0, TAU))
        base = p + out * (radius(t) + 0.03)
        e = math.radians(rng.uniform(-60, 25))
        d = (out * math.cos(e) + tang * math.sin(e)).normalized()
        side = tang.cross(out).normalized()
        side = Matrix.Rotation(rng.uniform(-0.5, 0.5), 3, d) @ side
        side = (side - d * side.dot(d)).normalized()
        nrm = side.cross(d)
        if nrm.dot(out) < 0:
            nrm = -nrm
        L = rng.uniform(0.26, 0.40) * leaf
        _heart(mb, base, d, side, nrm, L, L * 0.82)
    for i in range(int(length * spikes_per_m)):                 # berry strings
        t = rng.uniform(t0 + 0.05 * (t1 - t0), t1)
        p, tang, out = radial(t, rng.uniform(0, TAU))
        out.z = 0
        out = out.normalized() if out.length > 1e-3 else Vector((1, 0, 0))
        top = p + out * (radius(t) + 0.12)
        u = rng.random()
        scheme = "red" if u < red else ("green" if u < red + 0.25 else "mix")
        _spike(mb, top, out, rng, rng.uniform(0.32, 0.6), scheme)


def make_vine_tree(name, collection, seed=0, height=10.0, vine=True, vine_top=None):
    """Tall jungle tree (straight trunk, a few branches, faceted crown) with a pepper
    vine wrapped round the trunk."""
    rng = random.Random(seed)
    mb = kit.MB()
    lean = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * 0.05 * height

    def path(t):
        return Vector((0, 0, height * 0.78 * t)) + lean * (t * t)

    r0 = 0.2 + 0.012 * height

    def rad(t):
        return r0 * (1 - 0.45 * t)

    n = 5
    for i in range(n):
        a, b = path(i / n), path((i + 1) / n)
        mb.seg(a, b + (b - a) * 0.04, rad(i / n) * 1.06, rad((i + 1) / n), "trunk", sides=6,
               spin=rng.uniform(0, 1))
    mb.cone(T(0, 0, 0.22), "trunk", segments=6, r1=r0 * 1.7, r2=r0 * 1.0, depth=0.44)   # root flare
    top = path(1.0)
    greens = ("leaf", "leaf_lt", "leaf_dk", "leaf_lt")
    for k in range(rng.randint(2, 3)):                                # side branches with crowns
        a = rng.uniform(0, TAU)
        z = rng.uniform(0.62, 0.86)
        p0 = path(z)
        p1 = p0 + Vector((math.cos(a), math.sin(a), 0)) * height * 0.2 + Vector((0, 0, height * 0.13))
        mb.seg(p0, p1, rad(z) * 0.55, rad(z) * 0.3, "trunk", sides=5)
        mb.ico(T(p1 + Vector((0, 0, height * 0.05))) @ S(1, 1, 0.8) @ Rz(rng.uniform(0, 3)),
               rng.choice(greens), r=height * rng.uniform(0.1, 0.14), sub=1, jitter=0.12, rng=rng)
    for k in range(rng.randint(4, 6)):                                # crown
        r = height * rng.uniform(0.12, 0.18)
        off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.2, 0.7))) * height * 0.12
        mb.ico(T(top + off) @ S(1, 1, 0.82) @ Rz(rng.uniform(0, 3)), rng.choice(greens), r=r, sub=1,
               jitter=0.12, rng=rng)
    if vine:
        _vine(mb, path, rad, 0.0, vine_top or rng.uniform(0.55, 0.72), rng)
    return mb.obj(name, collection)


def make_vine_palm(name, collection, seed=0, height=8.0):
    """kit palm with a pepper vine up its curved trunk."""
    rng = random.Random(seed + 500)
    palm = kit.make_palm("_palm_tmp", collection, seed=seed, height=height)
    mb = kit.MB()
    mb.bm.from_mesh(palm.data)
    mb.mats = [m.name for m in palm.data.materials]
    me = palm.data
    bpy.data.objects.remove(palm)
    bpy.data.meshes.remove(me)
    r0 = random.Random(seed)                  # same draws as make_palm, to follow its trunk
    az = r0.uniform(0, TAU)
    bend = r0.uniform(0.12, 0.32)
    lean = Vector((math.cos(az), math.sin(az), 0))

    def path(t):
        return Vector((0, 0, height * t)) + lean * (height * bend * t * t)

    _vine(mb, path, lambda t: 0.40 * (1 - 0.45 * t) * 1.05, 0.0, rng.uniform(0.45, 0.7), rng,
          leaves_per_m=9.0, spikes_per_m=1.6)
    return mb.obj(name, collection)


def make_vine_pole(name, collection, seed=0, height=6.0):
    """Squared wooden support post smothered in pepper vine (the foreground post in K11a)."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.02)
    mb.box(T(0, 0, height / 2) @ Rz(0.3) @ S(0.3, 0.3, height), "post")
    mb.box(T(0, 0, height + 0.05) @ Rz(0.3) @ S(0.34, 0.34, 0.1), "beam")
    mb.cone(T(0, 0, 0.12), "soil", segments=7, r1=0.55, r2=0.3, depth=0.24)
    _vine(mb, lambda t: Vector((0, 0, height * t)), lambda t: 0.19, 0.0, 0.97, rng,
          leaves_per_m=26.0, spikes_per_m=6.0, leaf=1.15, strands=3, red=0.7)
    return mb.obj(name, collection)


# ===================================================================== props
def make_basket(name, collection, r=0.34, h=0.36, seed=0, fill=0.93):
    """Round woven basket (checker weave, thick dark rim) heaped with black pepper."""
    rng = random.Random(seed)
    mb = kit.MB()
    segs, rows = 16, 6
    rb = r * 0.8

    def rad(z):
        return rb + (r - rb) * (z / h) + 0.025 * math.sin(math.pi * z / h)

    angs = [TAU * j / segs for j in range(segs)]
    rings = []
    for i in range(rows + 1):
        z = h * i / rows
        rings.append([mb.bm.verts.new((rad(z) * math.cos(a), rad(z) * math.sin(a), z)) for a in angs])
    for i in range(rows):
        for j in range(segs):
            k = (j + 1) % segs
            mb.face([rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]],
                    "basket" if (i + j) % 2 == 0 else "basket_dk")
    mb.face(rings[0][::-1], "basket_dk")
    for j in range(segs):                                   # rim
        a0, a1 = angs[j], angs[(j + 1) % segs]
        mb.seg((rad(h) * math.cos(a0), rad(h) * math.sin(a0), h), (rad(h) * math.cos(a1), rad(h) * math.sin(a1), h),
               0.04, 0.04, "basket_dk", sides=5)
    for z in (0.02, h * 0.5):                               # binding bands
        rr = rad(z) + 0.012
        mb.cone(T(0, 0, z), "basket_dk", segments=segs, r1=rr, r2=rr, depth=0.03)
    zf = h * fill                                           # heap of pepper
    rf = rad(zf) - 0.01
    mb.cone(T(0, 0, zf - 0.03), "pepper", segments=segs, r1=rf, r2=rf * 0.45, depth=0.1)
    for k in range(int(150 * (r / 0.34) ** 2)):
        u = math.sqrt(rng.random()) * (rf - 0.03)
        a = rng.uniform(0, TAU)
        zz = zf + 0.02 if u < rf * 0.45 else zf + 0.02 - 0.1 * (u - rf * 0.45) / (rf * 0.55)
        mb.ico(T(u * math.cos(a), u * math.sin(a), zz + 0.008) @ S(1, 1, 0.8),
               "pepper" if rng.random() > 0.3 else "pepper_br", r=rng.uniform(0.022, 0.03), sub=1)
    return mb.obj(name, collection)


def make_tray(name, collection, r=0.62, seed=0):
    """Flat round woven drying tray with black pepper spread over it."""
    rng = random.Random(seed)
    mb = kit.MB()
    segs = 22
    mb.cone(T(0, 0, 0.025), "tray", segments=segs, r1=r, r2=r, depth=0.05)
    for k, rr in enumerate((0.72, 0.42)):                       # woven rings
        mb.cone(T(0, 0, 0.051), "mat_dk", segments=segs, r1=r * rr, r2=r * rr, depth=0.002)
        mb.cone(T(0, 0, 0.052), "tray", segments=segs, r1=r * rr - 0.04, r2=r * rr - 0.04, depth=0.002)
    for j in range(segs):                                       # rim
        a0, a1 = TAU * j / segs, TAU * (j + 1) / segs
        mb.seg((r * math.cos(a0), r * math.sin(a0), 0.07), (r * math.cos(a1), r * math.sin(a1), 0.07),
               0.035, 0.035, "basket_dk", sides=5)
    # pepper spread thick in the middle, thinning toward the rim (straw shows through)
    for k in range(int(700 * (r / 0.72) ** 2)):
        u = r * 0.88 * math.sqrt(rng.random()) ** 0.75
        a = rng.uniform(0, TAU)
        mb.ico(T(u * math.cos(a), u * math.sin(a), 0.07) @ S(1, 1, 0.75),
               "pepper" if rng.random() > 0.3 else "pepper_br", r=rng.uniform(0.02, 0.028), sub=1)
    return mb.obj(name, collection)


def make_woven_mat(name, collection, w=2.0, d=1.4, pepper=0.0, seed=0):
    """Rectangular woven mat (checker of light and dark strips), optionally with pepper
    spread on it (pepper = corns per square metre)."""
    rng = random.Random(seed)
    mb = kit.MB()
    nx, ny = max(2, round(w / 0.13)), max(2, round(d / 0.13))
    vs = [[mb.bm.verts.new((-w / 2 + w * i / nx, -d / 2 + d * j / ny, 0.012 + rng.uniform(-0.004, 0.004)))
           for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            mb.face([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]],
                    "mat_lt" if (i // 1 + j // 2) % 2 == 0 else "mat_dk")
    for sy in (-1, 1):                                           # bound edges
        mb.box(T(0, sy * d / 2, 0.015) @ S(w + 0.04, 0.05, 0.03), "basket_dk")
    for sx in (-1, 1):
        mb.box(T(sx * w / 2, 0, 0.015) @ S(0.05, d + 0.04, 0.03), "basket_dk")
    if pepper:
        cx, cy = rng.uniform(-0.1, 0.1) * w, rng.uniform(-0.1, 0.1) * d
        for k in range(int(pepper * w * d)):
            x = cx + rng.gauss(0, w * 0.26)
            y = cy + rng.gauss(0, d * 0.26)
            if abs(x) < w / 2 - 0.06 and abs(y) < d / 2 - 0.06:
                mb.ico(T(x, y, 0.03) @ S(1, 1, 0.75), "pepper" if rng.random() > 0.3 else "pepper_br",
                       r=rng.uniform(0.02, 0.028), sub=1)
    return mb.obj(name, collection)


def make_pot(name, collection, h=0.55, seed=0):
    """Terracotta water/storage pot (lathe profile, flared lip, darker shoulder band)."""
    s = h / 0.55
    prof = [(0.0, 0.0), (0.13, 0.0), (0.21, 0.06), (0.27, 0.19), (0.27, 0.3), (0.21, 0.42), (0.14, 0.48),
            (0.13, 0.51), (0.17, 0.55), (0.15, 0.56), (0.11, 0.52)]
    segs = 12
    mb = kit.MB()
    rings = [[mb.bm.verts.new((r * s * math.cos(TAU * j / segs), r * s * math.sin(TAU * j / segs), z * s))
              for j in range(segs)] for r, z in prof[1:]]
    bottom = mb.bm.verts.new((0, 0, 0))
    for j in range(segs):
        mb.face([bottom, rings[0][(j + 1) % segs], rings[0][j]], "clay_dk")
    for i in range(len(rings) - 1):
        m = "clay_dk" if i in (3, 8) else "clay"
        for j in range(segs):
            k = (j + 1) % segs
            mb.face([rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]], m)
    mb.face(rings[-1][::-1], "dark")
    return mb.obj(name, collection)


def make_pepper_sack(name, collection, lying=False, seed=0):
    """Jute sack of pepper, tied at the neck (or lying flat, for stacks)."""
    rng = random.Random(seed)
    mb = kit.MB()
    if lying:
        mb.ico(T(0, 0, 0.2) @ S(0.5, 0.32, 0.21), "jute", r=1.0, sub=2, jitter=0.03, rng=rng)
        mb.cone(T(0.5, 0, 0.2) @ Ry(math.pi / 2), "jute", segments=6, r1=0.1, r2=0.13, depth=0.14)
        mb.cone(T(0.44, 0, 0.2) @ Ry(math.pi / 2), "rope", segments=6, r1=0.105, r2=0.105, depth=0.04)
    else:
        mb.ico(T(0, 0, 0.3) @ S(0.36, 0.3, 0.32), "jute", r=1.0, sub=2, jitter=0.03, rng=rng)
        mb.cone(T(0, 0, 0.66), "jute", segments=6, r1=0.1, r2=0.15, depth=0.16)
        mb.cone(T(0, 0, 0.6), "rope", segments=6, r1=0.105, r2=0.105, depth=0.04)
    return mb.obj(name, collection)


def make_bigleaf(name, collection, seed=0, size=1.4):
    """Broad-leaf ground plant (taro / wild banana) for the lush foreground."""
    rng = random.Random(seed)
    mb = kit.MB()
    nf = rng.randint(6, 9)
    for k in range(nf):
        a = k * TAU / nf + rng.uniform(-0.3, 0.3)
        kit._frond(mb, (0, 0, 0.05), a, math.radians(rng.uniform(35, 70)), size * rng.uniform(0.85, 1.25),
                   size * rng.uniform(0.34, 0.46), math.radians(rng.uniform(40, 80)),
                   rng.choice(("leaf", "leaf_lt", "frond", "leaf_dk")), rng, steps=5, fold=0.3)
    return mb.obj(name, collection)


def make_woodpile(name, collection, seed=0):
    rng = random.Random(seed)
    mb = kit.MB()
    for row, n in enumerate((5, 4, 3)):
        for k in range(n):
            x = (k - (n - 1) / 2) * 0.24
            z = 0.12 + row * 0.2
            L = rng.uniform(1.1, 1.4)
            mb.seg((x, -L / 2, z), (x, L / 2, z), 0.11, 0.11, "log", sides=6)
            mb.cone(T(x, L / 2 + 0.001, z) @ Rx(math.pi / 2), "log_end", segments=6, r1=0.1, r2=0.1, depth=0.01)
    return mb.obj(name, collection)


def make_sack_bundle(name, collection, seed=0):
    """Four sacks in a rope sling with a hook ring, for the ship's hoist. Origin at the ring."""
    rng = random.Random(seed)
    mb = kit.MB()
    for k, (x, y) in enumerate(((-0.28, -0.2), (0.28, -0.2), (-0.28, 0.2), (0.28, 0.2))):
        mb.ico(T(x, y, -1.45) @ Rz(rng.uniform(-0.3, 0.3)) @ S(0.3, 0.24, 0.26), "jute", r=1.0, sub=1,
               jitter=0.06, rng=rng)
    mb.ico(T(0, 0, -1.12) @ S(0.3, 0.22, 0.2), "jute", r=1.0, sub=1)
    for x, y in ((-0.5, -0.4), (0.5, -0.4), (-0.5, 0.4), (0.5, 0.4)):
        mb.seg((0, 0, 0), (x, y, -1.5), 0.02, 0.02, "rope", sides=4)
    mb.cone(T(0, 0, 0), "iron", segments=8, r1=0.07, r2=0.07, depth=0.04)
    return mb.obj(name, collection)


# =================================================================== scene
def _put(src, name, coll, x, y, rz=0.0, s=1.0, sink=0.05):
    return kit.instance(src, name, coll, (x, y, height(x, y) - sink), rot_z=rz, scale=s)


def _blocked(x, y, keep, scale=1.0):
    """True where something tall would block the camera. keep holds
    ("seg", ax, ay, bx, by, r): a ground corridor (the camera's low path, lines of sight),
    ("cone", cx, cy, tx, ty, half_deg, dist): the near part of a key view, and
    ("disc", x, y, r): the air round a key camera position. Cones and discs are kept
    open for trees only (scale >= 1); low plants (scale < 1) may stand in them."""
    for k in keep:
        if k[0] == "seg":
            _, ax, ay, bx, by, r = k
            if _seg_dist(x, y, (ax, ay), (bx, by)) < r * scale:
                return True
        elif k[0] == "disc":
            if scale >= 1.0 and math.hypot(x - k[1], y - k[2]) < k[3]:
                return True
        elif scale >= 1.0:
            _, cx, cy, tx, ty, half, dist = k
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if 0 < d < dist:
                a = math.atan2(dx, dy) - math.atan2(tx - cx, ty - cy)
                a = (a + math.pi) % TAU - math.pi
                if abs(a) < math.radians(half):
                    return True
    return False


def _in_view(x, y, keep):
    """Inside the angle of a key view's cone, at any distance."""
    for k in keep:
        if k[0] == "cone":
            _, cx, cy, tx, ty, half, dist = k
            a = math.atan2(x - cx, y - cy) - math.atan2(tx - cx, ty - cy)
            if abs((a + math.pi) % TAU - math.pi) < math.radians(half + 4):
                return True
    return False


def _clear_of_walls(x, y, pad=1.2):
    if garden_mask(x) > 0.3:
        d = terr_d(x, y)
        if any(abs(d - R) < pad for R in RINGS):
            return False
    return abs(mound_e(x, y)) > pad


def build_garden(coll, lib_c, keep_clear=()):
    """The drying yard, hut terrace, terraces and their planting. keep_clear: [(x, y, r)]
    spots (the camera's path) where nothing tall may stand."""
    rng = random.Random(11)
    props = kit.new_collection("GardenProps", coll)
    plants = kit.new_collection("GardenPlants", coll)

    # ---- library
    trays = [make_tray(f"LibTray{i}", lib_c, r=0.7 + 0.06 * i, seed=i) for i in range(3)]
    baskets = [make_basket(f"LibBasket{i}", lib_c, r=r, h=h, seed=i)
               for i, (r, h) in enumerate([(0.4, 0.4), (0.34, 0.44), (0.44, 0.34), (0.32, 0.34)])]
    mats = [make_woven_mat("LibMat0", lib_c, 2.3, 1.6), make_woven_mat("LibMat1", lib_c, 2.6, 1.0, pepper=520, seed=1),
            make_woven_mat("LibMat2", lib_c, 1.8, 1.2, pepper=480, seed=2)]
    pots = [make_pot(f"LibPot{i}", lib_c, h=h, seed=i) for i, h in enumerate((0.55, 0.42, 0.62))]
    sack = make_pepper_sack("LibPepperSack", lib_c)
    sack_lying = make_pepper_sack("LibPepperSackLying", lib_c, lying=True, seed=3)
    woodpile = make_woodpile("LibWoodpile", lib_c)
    crate = kit.make_crate("LibCrate", lib_c, size=0.7)
    barrel = kit.make_barrel("LibBarrel", lib_c)
    fence = kit.make_fence("LibFence", lib_c, length=3.8, height=1.0)
    hut = kit.make_hut_gable("LibHutMud", lib_c, w=5.0, d=3.8, h=2.2, seed=2)
    hut2 = kit.make_hut_hip("LibHutMud2", lib_c, w=3.6, d=3.2, h=1.9, seed=12)
    for h_ in (hut, hut2):                                    # mud walls, like the Flow frames
        for i, m in enumerate(h_.data.materials):
            if m.name == "wall":
                h_.data.materials[i] = kit.mat("mud")
    # toy scale, as in K11a: trees about 1.5-2.5 times the hut's height
    vtrees = [make_vine_tree(f"LibVineTree{i}", lib_c, seed=i, height=6.8 + 0.8 * i) for i in range(5)]
    ptrees = [make_vine_tree(f"LibJungleTree{i}", lib_c, seed=20 + i, height=8.0 + 1.5 * i, vine=False)
              for i in range(3)]
    vpalms = [make_vine_palm(f"LibVinePalm{i}", lib_c, seed=i, height=6.6 + 0.5 * i) for i in range(4)]
    palms = [kit.make_palm(f"LibPalm{i}", lib_c, seed=10 + i, height=7.0 + 0.5 * i) for i in range(4)]
    rtrees = [kit.make_tree(f"LibTree{i}", lib_c, seed=i, height=5 + i) for i in range(4)]
    bushes = [kit.make_bush(f"LibBush{i}", lib_c, seed=i, size=0.9 + 0.25 * i) for i in range(3)]
    bigleaf = [make_bigleaf(f"LibBigLeaf{i}", lib_c, seed=i, size=1.2 + 0.35 * i) for i in range(3)]
    pole = make_vine_pole("LibVinePole", lib_c, seed=5, height=6.5)
    rocks = [kit.make_rock(f"LibRock{i}", lib_c, seed=i, size=0.35 + 0.15 * i) for i in range(3)]

    # ---- drying yard: trays of pepper, baskets on a mat at the foot of the mound wall
    for i, (x, y, k) in enumerate([(-4.6, -4.7, 0), (-2.3, -4.1, 1), (-6.4, -2.2, 2), (-4.1, -1.8, 0),
                                   (-5.9, 0.5, 1), (-3.4, 0.6, 2), (-7.6, -0.2, 0)]):
        _put(trays[k], f"Tray{i}", props, x, y, rng.uniform(0, 6.3), 1.0, sink=0.0)
    _put(baskets[0], "YardBasket0", props, -6.9, -4.5, 0.3, 1.0, sink=0.0)
    mx, my = -0.6, -2.8
    _put(mats[0], "BasketMat", props, mx, my, -0.3, 1.0, sink=-0.01)
    for i, (dx, dy, k, s) in enumerate([(-0.6, -0.35, 0, 1.0), (0.25, -0.45, 1, 1.0), (0.55, 0.35, 2, 1.0),
                                        (-0.35, 0.45, 3, 1.1), (-0.9, 1.5, 0, 0.9), (0.3, 1.4, 1, 0.95),
                                        (-1.6, -0.2, 3, 1.0)]):
        _put(baskets[k], f"Basket{i}", props, mx + dx, my + dy, rng.uniform(0, 6.3), s, sink=-0.02)
    for i, (x, y, k) in enumerate([(0.5, -4.6, 0), (1.0, -4.0, 1), (-1.4, 0.9, 2)]):
        _put(pots[k], f"Pot{i}", props, x, y, rng.uniform(0, 6.3), 1.0, sink=0.0)
    for i, (x, y) in enumerate([(-2.3, 2.3), (-1.7, 2.6)]):
        _put(sack, f"YardSack{i}", props, x, y, rng.uniform(0, 6.3), 1.0, sink=0.02)

    # ---- hut terrace: mud hut, fences, crates, woodpile, more pepper
    _put(hut, "Hut", props, HUT[0], HUT[1], -0.1, 1.0, sink=0.1)
    _put(hut2, "Hut2", props, HUT2[0], HUT2[1], -0.35, 0.95, sink=0.1)
    for i, (x, y, rz, s) in enumerate([(-2.4, 4.4, 0.08, 0.95), (3.9, 2.0, -0.05, 0.85), (6.3, 2.3, 1.5, 0.9),
                                       (-5.4, 15.8, -0.1, 0.8)]):
        _put(fence, f"Fence{i}", props, x, y, rz, s, sink=0.02)
    for i, (x, y, src) in enumerate([(-0.4, 5.0, crate), (0.25, 5.3, crate), (-0.1, 5.15, crate), (5.4, 5.6, barrel),
                                     (5.0, 4.9, crate), (1.0, 2.7, baskets[1]), (4.6, 3.0, baskets[0])]):
        _put(src, f"HutProp{i}", props, x, y, rng.uniform(-0.4, 0.4), 1.0, sink=0.02)
    bpy.data.objects["HutProp2"].location.z += 0.68            # third crate sits on the first two
    _put(woodpile, "Woodpile", props, 6.3, 4.1, 1.5, 1.0, sink=0.02)
    _put(pots[2], "HutPot", props, 0.5, 2.9, 0.0, 1.0, sink=0.0)

    # pepper drying on mats along the terraces (the dark rows in K11a)
    for i, (R, phi, k) in enumerate([(17.2, -128, 1), (17.4, -137, 2), (17.2, -146, 1), (17.0, -155, 2),
                                      (12.4, -122, 2), (12.5, -133, 1), (12.4, -144, 2), (17.3, -98, 1)]):
        p, out = _terr_point(R, math.radians(phi))
        if garden_mask(p.x) > 0.7 and math.hypot(p.x - HUT[0], p.y - HUT[1]) > 4.0 and                 math.hypot(p.x - HUT2[0], p.y - HUT2[1]) > 3.5:
            _put(mats[k], f"TerraceMat{i}", props, p.x, p.y, math.radians(phi) + math.pi / 2, 1.0, sink=-0.01)

    # ---- hero vines: a smothered post on the mound (right foreground), vine trees round the yard
    _put(pole, "VinePole", plants, 2.3, -8.6, 0.4, 1.0, sink=0.1)       # the camera passes it
    _put(pole, "VinePole2", plants, 5.4, -4.2, 1.1, 1.1, sink=0.1)
    for i, (x, y, k, s) in enumerate([(6.9, 4.3, 0, 1.15), (9.6, 0.4, 4, 1.1)]):
        if not _blocked(x, y, [c for c in keep_clear if c[0] == "seg"], 0.4):
            _put(vtrees[k], f"YardVineTree{i}", plants, x, y, rng.uniform(0, 6.3), s, sink=0.15)
    for i, (x, y, k, s) in enumerate([(8.6, -3.4, 1, 1.35), (10.4, -8.0, 2, 1.25)]):    # tall palms, right edge
        _put(vpalms[k], f"MoundPalm{i}", plants, x, y, rng.uniform(0, 6.3), s, sink=0.15)
    for i, (x, y, k, s) in enumerate([(-11.4, 5.2, 2, 1.0), (-12.2, -1.0, 3, 1.1)]):
        if not _blocked(x, y, [c for c in keep_clear if c[0] == "seg"], 0.6):
            _put(vpalms[k], f"YardPalm{i}", plants, x, y, rng.uniform(0, 6.3), s, sink=0.15)

    # rows of vine trees along the upper terrace treads (the lower ones stay open, as in K11a)
    for k in range(1, len(RINGS) - 1):
        R = (RINGS[k] + RINGS[k + 1]) / 2 + 0.4
        phi = math.radians(-178)
        while phi < math.radians(-2):
            p, out = _terr_point(R, phi)
            phi += rng.uniform(8.0, 11.0) / R
            x, y = p.x, p.y
            if garden_mask(x) < 0.6 or not -16 < x < 24 or (k == 0 and x > -3.0) or                     math.hypot(x - HUT[0], y - HUT[1]) < 5.0 or math.hypot(x - HUT2[0], y - HUT2[1]) < 4.0 or                     _seg_dist(x, y, *PATH) < 2.0 or _blocked(x, y, keep_clear):
                continue
            src = rng.choice(vtrees + vpalms[:2])
            _put(src, f"TerraceTree{k}_{len(plants.objects)}", plants, x + rng.uniform(-0.4, 0.4),
                 y + rng.uniform(-0.4, 0.4), rng.uniform(0, 6.3), rng.uniform(0.85, 1.1), sink=0.15)

    # ground plants: along the wall feet, the yard edge and under the trees
    k = 0
    for i in range(900):
        x, y = rng.uniform(-24, 30), rng.uniform(-22, 48)
        if is_dirt(x, y) or not _clear_of_walls(x, y, 0.7) or abs(x - river_x(y)) < RIVER_HALF + 0.5 or                 math.hypot(x - YARD[0], y - YARD[1]) < YARD_R + 0.6 or math.hypot(x - HUT[0], y - HUT[1]) < 4.5 or math.hypot(x - HUT2[0], y - HUT2[1]) < 3.5 or                 _blocked(x, y, keep_clear, 0.8):
            continue
        src = rng.choice(bushes + bigleaf + bigleaf[:1])
        _put(src, f"Plant{k}", plants, x, y, rng.uniform(0, 6.3), rng.uniform(0.7, 1.3), sink=0.05)
        k += 1
    # lush foreground clumps framing the yard (bottom corners of K11a)
    for i, (x, y, s) in enumerate([(-7.6, -7.4, 1.4), (-5.4, -8.6, 1.2), (-9.4, -5.4, 1.3), (3.0, -8.0, 1.1),
                                   (5.4, -6.8, 1.0), (-7.8, 3.0, 1.2), (-6.2, 4.6, 1.0), (7.4, -5.4, 1.3)]):
        if not _blocked(x, y, keep_clear, 0.8):
            _put(bigleaf[i % 3], f"FgLeaf{i}", plants, x, y, rng.uniform(0, 6.3), s, sink=0.05)
    for i, (x, y) in enumerate([(1.4, -6.2), (-7.6, -1.4), (-1.0, 3.7), (7.2, -4.0)]):
        _put(rocks[i % 3], f"Rock{i}", props, x, y, rng.uniform(0, 3), 1.0, sink=0.1)
    return dict(vtrees=vtrees, ptrees=ptrees, vpalms=vpalms, palms=palms, rtrees=rtrees, bushes=bushes,
                bigleaf=bigleaf, baskets=baskets, sack=sack, sack_lying=sack_lying, crate=crate, pots=pots)


def build_forest(coll, lib, keep_clear=(), seed=31):
    """Jungle round the garden, down to the river and over the far hills."""
    rng = random.Random(seed)
    plants = kit.new_collection("Forest", coll)
    spots = []

    def ok(x, y, r):
        if abs(x - river_x(y)) < RIVER_HALF + 1.2:
            return False
        if is_dirt(x, y) or math.hypot(x - YARD[0], y - YARD[1]) < YARD_R + 2.5:
            return False
        if math.hypot(x - HUT[0], y - HUT[1]) < 7.0 or math.hypot(x - HUT2[0], y - HUT2[1]) < 4.5:
            return False
        low = height(x, y) < -2.5           # down the slope: its crown stays below the K11a eye line
        if _blocked(x, y, [k for k in keep_clear if not (low and k[0] == "cone")]):
            return False
        return all((x - a) ** 2 + (y - b) ** 2 > (r + rb) ** 2 for a, b, rb in spots)

    # near jungle: east bank slope, the hill behind the terraces, right of the mound
    k = 0
    for i in range(9000):
        x, y = rng.uniform(-60, 60), rng.uniform(-40, 95)
        lvl = garden_level(x, y) * garden_mask(x)
        on_terraces = lvl > 0.5 and terr_d(x, y) > RINGS[-1] and -16 < x < 22
        west = x < river_x(y)
        slope = not west and x < GARDEN_EDGE + 1
        r = 2.6 if slope or y > 24 else 1.8
        if _in_view(x, y, keep_clear) and not west and not slope:
            # behind the yard in the K11a view: open grass slopes with clumps of trees,
            # thickening into jungle toward the top of the hill
            if _n(x, y, 16.0, 6.6) < (0.0 if y < 40 else -0.35):
                continue
            r = 3.6 if y < 40 else 2.6
        if on_terraces or not _clear_of_walls(x, y, 1.6) or not ok(x, y, r):
            continue
        u = rng.random()
        if west:
            src = rng.choice(lib["palms"] + lib["rtrees"]) if u < 0.6 else rng.choice(lib["ptrees"])
        elif x < GARDEN_EDGE + 1:
            src = rng.choice(lib["vpalms"] + lib["palms"]) if u < 0.55 else rng.choice(lib["rtrees"] + lib["vtrees"])
        else:
            src = rng.choice(lib["vtrees"] + lib["ptrees"]) if u < 0.6 else rng.choice(lib["palms"] + lib["rtrees"])
        spots.append((x, y, r))
        _put(src, f"Jungle{k}", plants, x, y, rng.uniform(0, 6.3), rng.uniform(0.85, 1.25), sink=0.2)
        k += 1
        if k > 900:
            break
    # far forest on the hills, sized up so it still reads through the haze
    k = 0
    for i in range(9000):
        x, y = rng.uniform(-420, 380), rng.uniform(-200, 620)
        D = math.hypot(x, y - 10)
        if D < 62 or abs(x - river_x(y)) < RIVER_HALF + 3 or y < -60 and x > -60:
            continue
        if _n(x, y, 70.0, 5.5) < -0.25:
            continue                                        # leave some open grassy slopes
        src = rng.choice(lib["rtrees"] + lib["ptrees"] + lib["palms"][:2])
        _put(src, f"FarTree{k}", plants, x, y, rng.uniform(0, 6.3), rng.uniform(1.4, 2.4) * (1 + D / 500), sink=0.5)
        k += 1
        if k > 2600:
            break


def build_jetty(coll, lib, frames, hoist=None, keep_clear=()):
    """The river landing: jetty, stacked pepper, moored ship, and a sling of sacks being
    hoisted aboard by the ship's main yard (hoist = (lift, top, over, down) frames)."""
    rng = random.Random(51)
    c = kit.new_collection("Landing", coll)
    root_x = LANDING_X
    jlen = JETTY_LEN
    deck = 0.95
    jetty = kit.make_jetty("Jetty", c, length=jlen, width=2.0, deck=deck, seed=4)
    jetty.location = (root_x, JETTY_Y, WATER_Z)
    jetty.rotation_euler[2] = math.radians(90)             # runs west into the river
    deck_z = WATER_Z + deck + 0.04
    end_x = root_x - jlen

    # ship moored off the jetty end, turned so the last shot sees it three-quarter on;
    # the port end of its main yard reaches out over the jetty end for the hoist
    sc_ = SHIP_SCALE
    ship = kit.make_ship("Ship", c, length=38.0, beam=10.0, seed=1)
    rot = Matrix.Rotation(SHIP_ROT, 3, "Z")
    mast = Vector((0.0, (0.55 - 0.5) * 38.0, 0.0)) * sc_       # main mast, ship-local
    yard_dir = rot @ Vector((-1.0, 0.0, 0.0))                  # along the yard, out to port
    yard_half = 10.0 * 0.95 * sc_
    yard_z = (4.0 + 29.0 * 0.32) * sc_
    tip = Vector((end_x + 1.3, JETTY_Y, 0.0))
    loc = tip - rot @ mast - yard_dir * (yard_half - 0.1)
    ship.location = (loc.x, loc.y, WATER_Z - 0.35)
    ship.rotation_euler[2] = SHIP_ROT
    ship.scale = (sc_, sc_, sc_)
    ship_deck = WATER_Z - 0.35 + 4.0 * sc_

    def on_ship(lx, ly):
        """World (x, y) of a ship-local point (metres, before scaling)."""
        q = Vector(ship.location) + rot @ (Vector((lx, ly, 0.0)) * sc_)
        return q.x, q.y

    # pepper stacked on the landing: sack piles, baskets, crates
    sack, lying, basket = lib["sack"], lib["sack_lying"], lib["baskets"]

    def put_l(src, name, x, y, rz=None, s=1.0, z=0.0):
        return kit.instance(src, name, c, (x, y, height(x, y) - 0.03 + z),
                            rot_z=rng.uniform(0, 6.3) if rz is None else rz, scale=s)

    k = 0
    for sx0, sy0 in [(root_x + 1.6, JETTY_Y - 2.8), (root_x + 2.8, JETTY_Y + 2.4)]:
        for layer, n in enumerate((4, 3)):
            for j in range(n):
                put_l(lying, f"SackStack{k}", sx0, sy0 + (j - (n - 1) / 2) * 0.62,
                      rz=rng.uniform(-0.15, 0.15), z=layer * 0.36)
                k += 1
    for i, (dx, dy, kb) in enumerate([(0.4, -1.0, 0), (1.0, -0.6, 1), (0.2, 1.3, 2), (1.6, 1.0, 3), (3.6, 0.0, 0),
                                       (4.1, -0.8, 2), (3.2, 4.4, 1), (0.6, 4.0, 3)]):
        put_l(basket[kb], f"LandingBasket{i}", root_x + dx, JETTY_Y + dy)
    for i, (dx, dy) in enumerate([(2.3, -0.4), (2.8, 0.5), (4.4, 1.8), (1.2, -4.6)]):
        put_l(sack, f"LandingSack{i}", root_x + dx, JETTY_Y + dy)
    crate = lib["crate"]
    for i, (dx, dy) in enumerate([(3.0, -2.2), (3.7, -1.8), (3.4, -2.0)]):
        put_l(crate, f"LandingCrate{i}", root_x + dx, JETTY_Y + dy, rz=rng.uniform(-0.3, 0.3),
              z=0.68 if i == 2 else 0.0)
    # the foreground of the last shot (K11b): a big basket heaped with pepper, sacks, crates
    cam, look = Vector(END_CAM), Vector(END_LOOK)
    fwd = (look - cam).normalized()
    left = Vector((-fwd.y, fwd.x))

    def near(ahead, side):
        p = cam + fwd * ahead + left * side
        return p.x, p.y

    big = make_basket("LibBigBasket", lib["lib_c"], r=0.62, h=0.5, seed=9)
    kit.hide_source(big)
    put_l(big, "HeroBasket", *near(4.1, 0.0))
    put_l(basket[2], "HeroBasket2", *near(3.7, 1.9))
    put_l(basket[2], "HeroBasket2b", *near(3.7, 1.9), z=0.33)
    put_l(basket[1], "HeroBasket3", *near(4.9, -0.8))
    for i, (a_, s_) in enumerate([(3.5, -1.5), (3.9, -2.1), (3.4, -2.6), (4.6, -2.4), (4.4, -1.6)]):
        put_l(sack, f"HeroSack{i}", *near(a_, s_))
    put_l(crate, "HeroCrate", *near(4.4, -3.4), rz=0.3)
    put_l(crate, "HeroCrate2", *near(5.4, -3.2), rz=0.1)
    put_l(crate, "HeroCrate3", *near(4.9, -3.3), rz=0.2, z=0.68)
    for i, (a_, s_) in enumerate([(3.2, 3.0), (3.5, 3.6)]):
        put_l(lying, f"HeroLying{i}", *near(a_, s_), rz=rng.uniform(0, 1))
    # sacks and baskets along the jetty deck, waiting for the hoist
    for i, (ax, ay, src) in enumerate([(-2.0, 0.45, lying), (-2.6, -0.4, lying), (-4.6, 0.5, basket[0]),
                                       (-5.2, -0.45, basket[1]), (-7.4, 0.4, lying), (-8.2, -0.5, basket[2]),
                                       (-9.6, 0.45, sack)]):
        kit.instance(src, f"DeckCargo{i}", c, (root_x + ax, JETTY_Y + ay, deck_z), rot_z=math.pi / 2)
    # cargo already aboard
    for i, (lx, ly) in enumerate([(0.0, -4.0), (1.4, -5.0), (-1.4, -4.6), (0.0, -6.2)]):
        kit.instance(lying, f"ShipCargo{i}", c, (*on_ship(lx, ly), ship_deck - 0.02),
                     rot_z=SHIP_ROT + rng.uniform(-0.2, 0.2))
    # a laden dugout tied at the jetty
    boat = kit.make_boat("LibBoat", c)
    kit.hide_source(boat)
    bt = kit.instance(boat, "Boat", c, (root_x - 4.5, JETTY_Y - 2.2, WATER_Z - 0.3), rot_z=math.radians(84))
    for i, dx in enumerate((-0.9, 0.0, 0.9)):
        kit.instance(basket[i % 2], f"BoatBasket{i}", c, (root_x - 4.5 + dx, JETTY_Y - 2.2, WATER_Z + 0.05),
                     rot_z=rng.uniform(0, 6.3), scale=0.9)
    # mooring lines from the bow and stern to the jetty posts
    rope = kit.MB()
    for ly in (10.5, -9.6):
        rope.seg((end_x + 0.2, JETTY_Y + (0.6 if ly > 0 else -0.6), deck_z + 0.4),
                 (*on_ship(-4.3, ly), ship_deck + 0.6), 0.025, 0.025, "rope", sides=4)
    rope.obj("MooringLines", c)

    # the hoist: tackle block runs out along the main yard, sling rises, swings in, lowers
    bundle = make_sack_bundle("SackSling", c)
    line = kit.MB()
    line.seg((0, 0, 0), (0, 0, -1), 0.022, 0.022, "rope", sides=4)
    tackle = line.obj("HoistLine", c)
    blk = kit.MB()
    blk.box(S(0.22, 0.16, 0.3), "post")
    block = blk.obj("HoistBlock", c)
    top_z = ship.location.z + yard_z - 0.15
    mast_w = Vector(ship.location).xy + (rot @ mast).xy
    u_out = yard_half - 0.1                  # along the yard: over the jetty end
    u_in = 0.9                               # over the ship's hold
    rest = deck_z + 1.55                     # sling resting on the deck (origin is the ring)
    lift_top = ship_deck + 3.6
    land = ship_deck + 1.55
    if hoist is None:
        f_lift, f_top, f_over, f_down = 190, 235, 262, 285
    else:
        f_lift, f_top, f_over, f_down = hoist
    for f in range(1, frames + 1):
        if f <= f_lift:
            u_, z = u_out, rest
        elif f <= f_top:
            u = _ss(f_lift, f_top, f)
            u_, z = u_out, rest + (lift_top - rest) * u
        elif f <= f_over:
            u = _ss(f_top, f_over, f)
            u_, z = u_out + (u_in - u_out) * u, lift_top + 0.25 * math.sin(math.pi * u)
        else:
            u = _ss(f_over, f_down, f)
            u_, z = u_in, lift_top + (land - lift_top) * u
        x, y = mast_w + yard_dir.xy * u_
        sway = 0.05 * math.sin(f / 9.0) * (1.0 if f_lift < f < f_down else 0.0)
        bundle.location = (x + sway, y, z)
        bundle.rotation_euler = (sway * 0.6, 0, SHIP_ROT + 0.15 * math.sin(f / 31.0))
        tackle.location = (x, y, top_z)
        tackle.scale = (1, 1, max(0.05, top_z - z))
        tackle.rotation_euler = (0, -sway / max(0.5, top_z - z), 0)
        block.location = (x, y, top_z + 0.1)
        for ob, paths in ((bundle, ("location", "rotation_euler")), (tackle, ("location", "scale", "rotation_euler")),
                          (block, ("location",))):
            for dp in paths:
                ob.keyframe_insert(dp, frame=f)
    # gentle rocking of the ship at its moorings
    for f in range(1, frames + 1, 40):
        ship.rotation_euler = (math.radians(0.5 * math.sin(f / 23.0)), math.radians(0.7 * math.sin(f / 17.0)),
                               SHIP_ROT)
        ship.keyframe_insert("rotation_euler", frame=f)
    # palms lining the banks around the landing
    for i, (x, y) in enumerate([(root_x + 3.5, JETTY_Y + 6.0), (root_x + 1.5, JETTY_Y - 7.5),
                                (root_x + 5.5, JETTY_Y - 4.5), (root_x + 2.2, JETTY_Y + 11.0),
                                (root_x + 0.8, JETTY_Y + 16.0), (root_x + 1.0, JETTY_Y - 13.0)]):
        if _blocked(x, y, keep_clear):
            continue
        src = rng.choice(lib["palms"] + lib["vpalms"])
        _put(src, f"LandingPalm{i}", c, x, y, rng.uniform(0, 6.3), rng.uniform(0.9, 1.15), sink=0.15)
    for i in range(30):                                      # palm-lined far bank
        y = JETTY_Y - 40 + i * 4.0 + rng.uniform(-1.2, 1.2)
        x = river_x(y) - RIVER_HALF - rng.uniform(1.5, 6.0)
        if _blocked(x, y, keep_clear):
            continue
        src = rng.choice(lib["palms"] + lib["vpalms"][:1])
        _put(src, f"FarBankPalm{i}", c, x, y, rng.uniform(0, 6.3), rng.uniform(0.85, 1.25), sink=0.15)
    return dict(ship=ship, jetty=jetty, root_x=root_x, end_x=end_x, deck_z=deck_z)


# ----------------------------------------------------------- light and haze
def add_mist_composite(scene, start=35.0, depth=420.0, strength=0.62, color=(0.95, 0.90, 0.83)):
    """Distance haze in the compositor: the render is mixed toward a warm mist colour by
    the mist pass (0 at `start` metres, 1 at start + depth, quadratic), so near props stay
    crisp and the far ridges fade like the misty hills in K11a/K11b."""
    scene.view_layers[0].use_pass_mist = True
    ms = scene.world.mist_settings
    ms.start, ms.depth, ms.falloff = start, depth, "QUADRATIC"
    tree = bpy.data.node_groups.new("PepperComposite", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers")
    rl.scene = scene
    mul = tree.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    mix = tree.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    a_in = next(i for i in mix.inputs if i.identifier == "A_Color")
    b_in = next(i for i in mix.inputs if i.identifier == "B_Color")
    out_c = next(o for o in mix.outputs if o.identifier == "Result_Color")
    b_in.default_value = (*kit.srgb_to_linear(color), 1)
    out = tree.nodes.new("NodeGroupOutput")
    tree.links.new(rl.outputs["Mist"], mul.inputs[0])
    tree.links.new(mul.outputs[0], mix.inputs["Factor"])
    tree.links.new(rl.outputs["Image"], a_in)
    tree.links.new(out_c, out.inputs[0])
    scene.compositing_node_group = tree
    scene.render.use_compositing = True
    return tree


def build_world(frames, hoist=None, keep_clear=()):
    register_palette()
    world_c = kit.new_collection("World")
    garden_c = kit.new_collection("Garden")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    make_terrain(world_c)
    make_river(world_c)
    w = cw.setup_world()
    for nd in w.node_tree.nodes:                              # less sky fill: crisper sun and shadow
        if nd.bl_idname == "ShaderNodeBackground":
            nd.inputs["Strength"].default_value = 0.6
    # Aerial haze is a mist-pass composite (add_mist_composite), not volume boxes: in this
    # set, volumes left a grain on the water and grass that more samples did not clear.
    cw.add_sun(rig_c, direction=(0.95, -0.3, -0.72), energy=10.5, color=(1.0, 0.86, 0.70), angle=4.0)
    build_walls(world_c)
    lib = build_garden(garden_c, lib_c, keep_clear)
    lib["lib_c"] = lib_c
    build_forest(garden_c, lib, keep_clear)
    build_jetty(garden_c, lib, frames, hoist, keep_clear)
    add_mist_composite(bpy.context.scene)
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c
