"""Dutch Kochi (S12, shot-list clips 16-17): the courtyard of the Dutch fort, where VOC
officials sign pepper contracts with the small rajas while porters carry pepper out
through the sea gate to a moored East Indiaman.

Laid out to match the Flow reference frames/flow_refs/K16_v1 (camera inside the fort
looking west toward the sea gate): orange crenellated walls round a sandy courtyard, a
cream canopy over a patterned carpet, a table with a blank parchment, quill and a chest
of gold, two seated Dutch officials facing three rajas, crates and palms, and through
the open gate a jetty running out to the ship. Details borrowed from K16_v2: gate
towers with small tiled pavilions, brick showing through the plaster, a brick stair.

Coordinates: metres, Z up, courtyard floor at z = 0, centred on the origin. West (-X)
is the sea, so the high shot at the end has the sea on the left like the map.
New assets (fort, canopy, carpet, furniture, seated officials, rajas, porters) are
built here in the colachel_kit style: flat-shaded bmesh builds, library objects
instanced, figures drawn from boxes, cones and icospheres.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import colachel_kit as kit
import colachel_world as cw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau

# extra colours for this set (people, wood and sea colours come from kit.PALETTE)
PALETTE = {
    "fort":         (0.92, 0.49, 0.17),   # Dutch orange-ochre plaster
    "fort_lt":      (0.96, 0.62, 0.27),   # copings and walk tops
    "fort_dk":      (0.76, 0.38, 0.13),   # plinths, string courses
    "stain":        (0.82, 0.42, 0.15),   # rain streaks under the spouts
    "brick":        (0.66, 0.29, 0.17),
    "brick_lt":     (0.76, 0.38, 0.22),
    "mortar":       (0.84, 0.66, 0.46),
    "court":        (0.63, 0.59, 0.42),   # courtyard earth (olive khaki, as in K16)
    "court_dk":     (0.59, 0.55, 0.40),
    "paving":       (0.71, 0.65, 0.53),
    "paving_dk":    (0.63, 0.57, 0.46),
    "tile":         (0.70, 0.30, 0.18),   # red roof tiles (as on the map's fort)
    "tile_dk":      (0.58, 0.24, 0.14),
    "plaster":      (0.90, 0.84, 0.70),
    "pole":         (0.17, 0.13, 0.11),
    "cloth_cream":  (0.91, 0.85, 0.68),   # canopy cloth   # canopy posts (near black)
    "wood_tbl":     (0.56, 0.37, 0.23),
    "wood_chair":   (0.44, 0.29, 0.18),
    "wood_door":    (0.42, 0.30, 0.20),
    "rug":          (0.55, 0.36, 0.33),   # carpet field (mauve brown)
    "rug_dk":       (0.42, 0.25, 0.22),
    "rug_gold":     (0.84, 0.67, 0.41),
    "breeches":     (0.82, 0.73, 0.52),
    "stocking":     (0.94, 0.93, 0.89),
    "jute":         (0.72, 0.60, 0.42),
    "rope":         (0.52, 0.42, 0.28),
    "pepper":       (0.17, 0.12, 0.10),
    "basket":       (0.78, 0.62, 0.38),
    "dirt":         (0.68, 0.55, 0.38),
    "grass_lt":     (0.50, 0.62, 0.26),
    "flag_r":       (0.78, 0.16, 0.12),
    "flag_b":       (0.14, 0.24, 0.55),
    "umbrella":     (0.72, 0.14, 0.10),
    "gull":         (0.95, 0.95, 0.93),
}


def register_palette():
    """Add this set's colours to the kit palette and create their materials
    (call after kit.reset_scene)."""
    for name, rgb in PALETTE.items():
        kit.PALETTE[name] = rgb
        kit.mat(name, rgb)


# ------------------------------------------------------------------- layout
IN_X, IN_Y = 11.0, 13.0        # half size of the courtyard (inner faces of the curtain walls)
WALL_T = 3.0                    # wall thickness (the walk on top is this wide)
WALL_H = 3.2                    # walk level (merlons rise 1.25 above it)
OUT_X, OUT_Y = IN_X + WALL_T, IN_Y + WALL_T
BASTION_R = 6.5                 # corner bastions: diamonds this far from the outer corner
GATE_Y = 4.6                    # sea gate (west wall) and land gate (east wall) centre line
GATE_W, GATE_H = 4.0, 2.75
FOUND = -1.6                    # walls go this far down (the beach falls away outside)
SEA_Z = -0.9
BEACH_X = -(IN_X + 3.0) - 1.5   # the beach starts sloping here
SHORE_X = BEACH_X - 6.9          # where the beach meets the sea (mean)
JETTY_X0, JETTY_LEN, JETTY_W = BEACH_X - 1.5, 18.0, 2.7
JETTY_Y = 4.65
DECK_TOP = 0.02                 # jetty deck level (flush with the top of the beach)
TABLE = (-0.5, -3.0)             # the treaty table: long side along X, officials south of it
TABLE_H = 0.70
SHED = (-4.3, 11.0)             # open pepper shed against the north wall


def shore_x(y):
    return SHORE_X + 1.1 * math.sin(y / 9.0) + 0.5 * math.sin(y / 4.1 + 1.0)


def _ss(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def in_fort(x, y, pad=0.0):
    """Inside the fort's footprint (curtain walls plus bastions)."""
    if abs(x) < OUT_X + pad and abs(y) < OUT_Y + pad:
        return True
    cx, cy = math.copysign(OUT_X, x), math.copysign(OUT_Y, y)
    return abs(x - cx) + abs(y - cy) < BASTION_R + pad


def height(x, y):
    """Ground height: flat courtyard and town, the beach sloping into the sea westward."""
    if x < BEACH_X:
        sx = shore_x(y)
        d = x - BEACH_X                      # negative going west
        slope = SEA_Z / (sx - BEACH_X)       # reaches sea level at the shore line
        return max(-3.0, d * slope)
    n = 0.08 * math.sin(x / 7.3 + 1.1) * math.sin(y / 6.1)
    return 0.0 if in_fort(x, y, 1.0) else n * _ss(20, 30, max(abs(x), abs(y)))


def ground_z(x, y):
    """Where a walker's feet are: the jetty deck over the water, the ground elsewhere."""
    if x < JETTY_X0 + 0.3 and abs(y - JETTY_Y) < JETTY_W / 2 + 0.2:
        return DECK_TOP
    return height(x, y)


# ----------------------------------------------------------- mesh helpers
def bar(mb, p0, p1, w, z0, z1, m, off=0.0):
    """Box standing on the line p0 -> p1 (2D), w thick, from z0 to z1, shifted sideways by off."""
    a = Vector((p0[0], p0[1], 0))
    b = Vector((p1[0], p1[1], 0))
    d = b - a
    c = (a + b) / 2
    ang = math.atan2(d.y, d.x)
    mb.box(T(c.x, c.y, (z0 + z1) / 2) @ Rz(ang) @ T(0, off, 0) @ S(d.length, w, z1 - z0), m)


def prism(mb, pts, z0, z1, m, top=None):
    """Vertical prism over a polygon (counter-clockwise seen from above)."""
    lo = [mb.bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [mb.bm.verts.new((x, y, z1)) for x, y in pts]
    mb.face(hi, top or m)
    mb.face(lo[::-1], m)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        mb.face([lo[i], lo[j], hi[j], hi[i]], m)


def merlons(mb, p0, p1, z, m, w=0.55, size=0.85, gap=0.6, h=0.8, off=0.0):
    """Crenellation along p0 -> p1: a breast wall to z + 0.45 with merlons above it."""
    a, b = Vector((*p0, 0)), Vector((*p1, 0))
    L = (b - a).length
    bar(mb, p0, p1, w, z, z + 0.45, m, off)
    n = max(1, int((L + gap) / (size + gap)))
    step = L / n
    d = (b - a).normalized()
    for i in range(n):
        c = a + d * (step * (i + 0.5))
        q0 = c - d * (size / 2)
        q1 = c + d * (size / 2)
        bar(mb, q0.xy, q1.xy, w, z + 0.44, z + 0.45 + h, m, off)
        bar(mb, q0.xy, q1.xy, w + 0.06, z + 0.43 + h, z + 0.5 + h, "fort_lt", off)


def flat(mb, cx, cy, sx, sy, z, m, rot=0.0, th=0.004):
    """Thin flat inlay (carpet patterns, paving)."""
    mb.box(T(cx, cy, z + th / 2) @ Rz(rot) @ S(sx, sy, th), m)


def brick_patch(mb, origin, along, normal, w, h, rng, depth=0.03):
    """Plaster fallen away: a mortar bed with staggered bricks, on a wall face.
    origin is the patch's bottom corner on the face; it runs along normal x up."""
    normal, up = Vector(normal), Vector((0, 0, 1))
    along = normal.cross(up)          # keeps the frame right-handed (outward normals)
    o = Vector(origin)
    M0 = kit.frame_matrix(o + along * (w / 2) + up * (h / 2) + normal * 0.01, along, normal, up)
    mb.box(M0 @ S(w, 0.03, h), "mortar")
    bw, bh = 0.26, 0.11
    row = 0
    z = 0.03
    while z + bh < h:
        x = 0.02 + (bw / 2 if row % 2 else 0.0)
        # ragged outline: rows get shorter toward the top and bottom
        inset = abs(z - h / 2) / (h / 2) * w * 0.25 + rng.uniform(0, 0.15)
        while x + bw < w - 0.02:
            if inset < x < w - inset - bw and rng.random() > 0.08:
                c = o + along * (x + bw / 2) + up * (z + bh / 2) + normal * (0.025 + depth / 2)
                M = kit.frame_matrix(c, along, normal, up)
                mb.box(M @ S(bw - 0.03, depth, bh - 0.025), "brick" if rng.random() > 0.3 else "brick_lt")
            x += bw
        z += bh
        row += 1


def tile_roof(mb, cx, cy, w, d, z, rise, m="tile", ridge="tile_dk", rot=0.0):
    """Hipped tiled roof over a w x d rectangle at height z, with a ridge and eave edge."""
    M = T(cx, cy, z) @ Rz(rot)
    hw, hd = w / 2 + 0.35, d / 2 + 0.35
    # a 4-sided cone scaled to the rectangle
    mb.cone(M @ T(0, 0, rise / 2) @ S(hw * math.sqrt(2), hd * math.sqrt(2), 1) @ Rz(math.pi / 4), m,
            segments=4, r1=1.0, r2=0.12, depth=rise)
    ridge_len = max(0.0, w - d) + 0.3
    if ridge_len > 0.3:
        mb.box(M @ T(0, 0, rise - 0.02) @ S(ridge_len, 0.22, 0.14), ridge)
    mb.box(M @ T(0, 0, -0.04) @ S(2 * hw, 2 * hd, 0.08), ridge)   # eave edge


def door(mb, c, along, normal, w=1.0, h=2.0, frame="wood_door"):
    """Dark doorway with a wooden frame on a wall face (c = bottom centre on the face)."""
    normal, up = Vector(normal), Vector((0, 0, 1))
    along = normal.cross(up)          # keeps the frame right-handed (outward normals)
    c = Vector(c)
    F = lambda p: kit.frame_matrix(p, along, normal, up)
    mb.box(F(c + up * (h / 2) + normal * 0.01) @ S(w, 0.06, h), "dark")
    for s in (-1, 1):
        mb.box(F(c + along * (s * (w / 2 + 0.07)) + up * (h / 2 + 0.05) + normal * 0.05) @ S(0.14, 0.1, h + 0.1), frame)
    mb.box(F(c + up * (h + 0.1) + normal * 0.05) @ S(w + 0.4, 0.12, 0.16), frame)
    mb.box(F(c + up * 0.04 + normal * 0.18) @ S(w + 0.3, 0.36, 0.08), "fort_dk")


def window(mb, c, along, normal, w=0.6, h=0.8, shutters=True):
    normal, up = Vector(normal), Vector((0, 0, 1))
    along = normal.cross(up)          # keeps the frame right-handed (outward normals)
    c = Vector(c)
    F = lambda p: kit.frame_matrix(p, along, normal, up)
    mb.box(F(c + normal * 0.01) @ S(w, 0.05, h), "dark")
    mb.box(F(c - up * (h / 2 + 0.05) + normal * 0.06) @ S(w + 0.24, 0.14, 0.09), "fort_lt")
    for k in (-1, 0, 1):                                   # iron bars
        mb.box(F(c + along * (k * w / 4) + normal * 0.04) @ S(0.03, 0.03, h), "iron")
    if shutters:
        for s in (-1, 1):
            mb.box(F(c + along * (s * (w * 0.75 + 0.02)) + normal * 0.05) @ S(w / 2, 0.04, h), "wood_door")


# ================================================================ the fort
def _wall_segments():
    """Curtain wall runs (centre lines) with gaps for the two gates."""
    cx, cy = IN_X + WALL_T / 2, IN_Y + WALL_T / 2
    g0, g1 = GATE_Y - GATE_W / 2, GATE_Y + GATE_W / 2
    return [  # (p0, p1, inward normal)
        ((-cx, -OUT_Y), (-cx, g0), (1, 0)), ((-cx, g1), (-cx, OUT_Y), (1, 0)),     # west, sea gate
        ((cx, -OUT_Y), (cx, g0 + 0.5), (-1, 0)), ((cx, g1 - 0.5), (cx, OUT_Y), (-1, 0)),  # east, land gate
        ((-OUT_X, -cy), (OUT_X, -cy), (0, 1)),                                    # south
        ((-OUT_X, cy), (OUT_X, cy), (0, -1)),                                     # north
    ]


def build_fort(coll, rng):
    """Curtain walls, star bastions, gate towers, gates, wall-walk merlons."""
    mb = kit.MB(bevel=0.025)
    # ---- curtain walls
    for p0, p1, n in _wall_segments():
        bar(mb, p0, p1, WALL_T, FOUND, WALL_H, "fort")
        n = Vector((*n, 0))
        a, b = Vector((*p0, 0)), Vector((*p1, 0))
        d = (b - a).normalized()
        L = (b - a).length
        inner = WALL_T / 2
        # walk: merlons on the outer edge, a low lip and a coping on the inside
        merlons(mb, (a - n * (inner - 0.28)).xy, (b - n * (inner - 0.28)).xy, WALL_H, "fort")
        bar(mb, (a + n * (inner - 0.15)).xy, (b + n * (inner - 0.15)).xy, 0.32, WALL_H, WALL_H + 0.3, "fort")
        bar(mb, (a + n * (inner + 0.02)).xy, (b + n * (inner + 0.02)).xy, 0.12, WALL_H - 0.18, WALL_H, "fort_lt")
        # plinth along both faces, string course halfway up the outside
        bar(mb, (a + n * (inner + 0.05)).xy, (b + n * (inner + 0.05)).xy, 0.2, -0.05, 0.42, "fort_dk")
        bar(mb, (a - n * (inner + 0.05)).xy, (b - n * (inner + 0.05)).xy, 0.25, FOUND, 0.5, "fort_dk")
        bar(mb, (a - n * (inner + 0.04)).xy, (b - n * (inner + 0.04)).xy, 0.12, 1.8, 1.95, "fort_dk")
        # shallow pilasters on the inner face, and rain spouts with streaks
        s = 2.2 + rng.uniform(0, 1.0)
        while s < L - 1.5:
            p = a + d * s + n * (inner + 0.07)
            mb.box(T(p.x, p.y, WALL_H / 2) @ Rz(math.atan2(d.y, d.x)) @ S(0.55, 0.14, WALL_H), "fort")
            q = a + d * (s + 2.6) + n * (inner + 0.2)
            if s + 2.6 < L - 1.0:
                mb.box(T(q.x, q.y, WALL_H - 0.35) @ Rz(math.atan2(n.y, n.x)) @ S(0.45, 0.14, 0.12), "fort_dk")
                q2 = a + d * (s + 2.6) + n * (inner + 0.02)
                mb.box(T(q2.x, q2.y, WALL_H - 1.4) @ Rz(math.atan2(d.y, d.x)) @ S(0.16, 0.04, 2.0), "stain")
            s += 5.2 + rng.uniform(-0.6, 0.6)
    # ---- bastions: diamonds round the outer corners (a star from above, like the map)
    R = BASTION_R
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * OUT_X, sy * OUT_Y
            pts = [(cx, cy - sy * R), (cx + sx * R, cy), (cx, cy + sy * R), (cx - sx * R, cy), (cx, cy)]
            if sx * sy < 0:
                pts = pts[::-1]
            prism(mb, pts, FOUND, WALL_H, "fort", top="fort_lt")
            tip_pts = [(cx, cy - sy * R), (cx + sx * R, cy), (cx, cy + sy * R), (cx - sx * R, cy)]
            for i in range(3):
                p, q = Vector((*tip_pts[i], 0)), Vector((*tip_pts[i + 1], 0))
                ctr = Vector((cx, cy, 0))
                mid = (p + q) / 2
                inw = (ctr - mid).normalized()
                merlons(mb, (p + inw * 0.3).xy, (q + inw * 0.3).xy, WALL_H, "fort")
                bar(mb, (p - inw * 0.06).xy, (q - inw * 0.06).xy, 0.2, FOUND, 0.5, "fort_dk")
            # sentry box (garita) on the point
            tip = Vector((cx, cy, 0)) + Vector((sx, sy, 0)).normalized() * (R * 0.62)
            mb.cone(T(tip.x, tip.y, WALL_H + 1.2), "fort", segments=8, r1=0.62, r2=0.58, depth=2.4)
            mb.cone(T(tip.x, tip.y, WALL_H + 2.6), "tile", segments=8, r1=0.8, r2=0.05, depth=0.9)
            mb.ico(T(tip.x, tip.y, WALL_H + 3.1), "fort_lt", r=0.12, sub=1)
            for k in range(3):
                a_ = math.atan2(sy, sx) + (k - 1) * 0.9
                mb.box(T(tip.x + 0.6 * math.cos(a_), tip.y + 0.6 * math.sin(a_), WALL_H + 1.6) @ Rz(a_)
                       @ S(0.08, 0.16, 0.5), "dark")
    # ---- gate towers either side of the sea gate, with tiled pavilions on top
    tw, th = 3.2, 5.6
    for gy in (GATE_Y - GATE_W / 2 - tw / 2, GATE_Y + GATE_W / 2 + tw / 2):
        x = -(IN_X + WALL_T / 2)
        mb.box(T(x, gy, (FOUND + th) / 2) @ S(tw, tw, th - FOUND), "fort")
        mb.box(T(x, gy, th + 0.06) @ S(tw + 0.2, tw + 0.2, 0.14), "fort_lt")
        mb.box(T(x, gy, 0.2) @ S(tw + 0.24, tw + 0.24, 0.5), "fort_dk")
        mb.box(T(x, gy, WALL_H + 0.1) @ S(tw + 0.12, tw + 0.12, 0.16), "fort_dk")
        c = tw / 2
        for p0, p1 in (((-c, -c), (c, -c)), ((c, -c), (c, c)), ((c, c), (-c, c)), ((-c, c), (-c, -c))):
            merlons(mb, (x + p0[0] * 0.9, gy + p0[1] * 0.9), (x + p1[0] * 0.9, gy + p1[1] * 0.9), th + 0.1,
                    "fort", size=0.6, gap=0.45, h=0.6, w=0.35)
        for face in (-1, 1):                                   # arrow slits
            for z in (1.6, 4.4):
                mb.box(T(x + face * (c + 0.01), gy, z) @ S(0.06, 0.2, 0.75), "dark")
        # pavilion: four posts and a little pyramid roof
        for px in (-0.85, 0.85):
            for py in (-0.85, 0.85):
                mb.box(T(x + px, gy + py, th + 1.0) @ S(0.18, 0.18, 1.9), "wood_door")
        mb.box(T(x, gy, th + 1.95) @ S(2.2, 2.2, 0.16), "wood_door")
        mb.cone(T(x, gy, th + 2.55) @ Rz(math.pi / 4), "tile", segments=4, r1=1.85, r2=0.08, depth=1.15)
        mb.ico(T(x, gy, th + 3.15), "brass", r=0.1, sub=1)
    # ---- sea gate: lintel, frame, open leaves
    x0 = -IN_X
    g0, g1 = GATE_Y - GATE_W / 2, GATE_Y + GATE_W / 2
    mb.box(T(-(IN_X + WALL_T / 2), GATE_Y, (GATE_H + WALL_H) / 2) @ S(WALL_T, GATE_W, WALL_H - GATE_H), "fort")
    for y in (g0 - 0.2, g1 + 0.2):
        mb.box(T(x0 + 0.06, y, GATE_H / 2) @ S(0.25, 0.45, GATE_H), "fort_dk")
    mb.box(T(x0 + 0.06, GATE_Y, GATE_H + 0.2) @ S(0.25, GATE_W + 0.9, 0.4), "fort_dk")
    mb.box(T(-(IN_X + WALL_T / 2), GATE_Y, -0.02) @ S(WALL_T + 0.3, GATE_W, 0.06), "paving_dk")
    # east (land) gate: a smaller opening with closed doors
    xe = IN_X + WALL_T / 2
    e0, e1 = GATE_Y - GATE_W / 2 + 0.5, GATE_Y + GATE_W / 2 - 0.5
    mb.box(T(xe, GATE_Y, (2.6 + WALL_H) / 2) @ S(WALL_T, e1 - e0, WALL_H - 2.6), "fort")
    mb.box(T(IN_X + WALL_T - 0.4, GATE_Y, 1.3) @ S(0.16, e1 - e0, 2.6), "wood_door")
    for z in (0.5, 1.3, 2.1):
        mb.box(T(IN_X + WALL_T - 0.3, GATE_Y, z) @ S(0.06, e1 - e0, 0.1), "iron")
    for y in (e0 - 0.2, e1 + 0.2):
        mb.box(T(IN_X - 0.06, y, 1.3) @ S(0.25, 0.45, 2.6), "fort_dk")
    fort = mb.obj("Fort", coll)

    # gate leaves, swung open into the courtyard (separate so they can be planked)
    for k, (hy, s) in enumerate(((g0, -1), (g1, 1))):
        lv = kit.MB(bevel=0.01)
        lw = GATE_W / 2 - 0.05
        for i in range(6):
            lv.box(T((i + 0.5) * lw / 6, 0, GATE_H / 2 - 0.05) @ S(lw / 6 - 0.02, 0.14, GATE_H - 0.12),
                   "wood_door" if i % 2 else "plank")
        for z in (0.45, 1.35, 2.25):
            lv.box(T(lw / 2, 0.09, z) @ S(lw, 0.04, 0.13), "iron")
            for i in range(5):
                lv.box(T((i + 0.5) * lw / 5, 0.12, z) @ S(0.05, 0.03, 0.05), "iron")
        lv.box(T(lw * 0.85, 0.12, 1.3) @ S(0.08, 0.05, 0.2), "iron")
        leaf = lv.obj(f"GateLeaf{k}", coll)
        leaf.location = (x0 + 0.1, hy - s * 0.1, 0.02)
        # hinged at the gate edge on the inner face; swung ~80 degrees open into the courtyard
        leaf.rotation_euler[2] = math.radians(-s * 10)
    return fort


def build_wall_details(coll, rng):
    """Brick patches, doors into the wall casemates, lamps, the brick stair."""
    mb = kit.MB(bevel=0.008)
    # brick patches on wall faces: (origin on face, along, normal, w, h)
    patches = [((-IN_X, -7.5, 1.0), (0, 1, 0), (1, 0, 0), 1.5, 1.0),
               ((-IN_X, 9.0, 1.6), (0, 1, 0), (1, 0, 0), 1.2, 0.8),
               ((-7.0, IN_Y, 1.0), (-1, 0, 0), (0, -1, 0), 1.8, 1.1),
               ((2.5, IN_Y, 1.8), (-1, 0, 0), (0, -1, 0), 1.3, 0.9),
               ((-1.5, -IN_Y, 2.0), (1, 0, 0), (0, 1, 0), 1.2, 0.7),
               ((IN_X, 3.0, 1.2), (0, -1, 0), (-1, 0, 0), 1.4, 1.0),
               ((-(IN_X + WALL_T), -4.0, 1.0), (0, -1, 0), (-1, 0, 0), 1.6, 1.1),
               ((-(IN_X + WALL_T), 12.5, 0.6), (0, -1, 0), (-1, 0, 0), 1.3, 0.9)]
    for o, al, n, w, h in patches:
        brick_patch(mb, o, al, n, w, h, rng)
    # casemate door in the north wall, one in the west wall, a barred window
    door(mb, (1.6, IN_Y, 0), (-1, 0, 0), (0, -1, 0), w=1.2, h=2.1)
    door(mb, (-IN_X, -2.2, 0), (0, 1, 0), (1, 0, 0), w=1.1, h=2.0)
    window(mb, (2.9, IN_Y, 2.0), (-1, 0, 0), (0, -1, 0), w=0.5, h=0.6)
    # wall lamps by the gate
    for y in (GATE_Y - 3.0, GATE_Y + 3.0):
        p = Vector((-IN_X + 0.15, y, 2.3))
        mb.box(T(p) @ S(0.3, 0.05, 0.05), "iron")
        mb.box(T(p + Vector((0.2, 0, -0.22))) @ S(0.18, 0.18, 0.3), "iron")
        mb.box(T(p + Vector((0.2, 0, -0.22))) @ S(0.13, 0.19, 0.22), "parchment")
        mb.cone(T(p + Vector((0.2, 0, -0.02))), "iron", segments=4, r1=0.15, r2=0.02, depth=0.14)
    # brick stair up to the south wall walk, climbing east
    x0, run, rise = 1.0, 0.42, WALL_H / 10
    nst = 10
    for i in range(nst):
        x = x0 + i * run
        z = (i + 1) * rise
        mb.box(T(x + run / 2, -IN_Y + 0.75, z - 0.05) @ S(run + 0.02, 1.5, 0.1), "fort_lt")
        mb.box(T(x + run / 2, -IN_Y + 0.75, z / 2) @ S(run, 1.5, z), "fort")
    # brick side of the stair: a sloping band of exposed bricks
    for i in range(nst):
        x = x0 + i * run
        for zz in range(i + 1):
            for j in range(2):
                z = zz * rise + j * rise / 2 + rise / 4
                xb = x + (0.1 if (zz + j) % 2 else 0.22)
                mb.box(T(xb, -IN_Y + 1.51, z) @ S(0.2, 0.03, rise / 2 - 0.02),
                       "brick" if rng.random() > 0.3 else "brick_lt")
    return mb.obj("WallDetails", coll)


def build_buildings(coll, rng):
    """Barracks (flat roof) along the south wall, a tiled godown in the south-east corner,
    the governor's house in the north-east corner, an open pepper shed by the north wall."""
    mb = kit.MB(bevel=0.02)
    # barracks along the west half of the south wall
    bx0, bx1, by0, by1, bh = -IN_X + 0.2, -3.0, -IN_Y, -9.3, 2.7
    mb.box(T((bx0 + bx1) / 2, (by0 + by1) / 2, bh / 2) @ S(bx1 - bx0, by1 - by0, bh), "fort")
    mb.box(T((bx0 + bx1) / 2, (by0 + by1) / 2, bh + 0.05) @ S(bx1 - bx0 + 0.25, by1 - by0 + 0.25, 0.14), "fort_lt")
    mb.box(T((bx0 + bx1) / 2, by1 + 0.02, 0.2) @ S(bx1 - bx0 + 0.1, 0.12, 0.42), "fort_dk")
    merlons(mb, (bx0, by1 - 0.1), (bx1, by1 - 0.1), bh + 0.1, "fort", w=0.25, size=0.5, gap=0.5, h=0.35)
    for i, x in enumerate((bx0 + 1.2, bx0 + 3.8, bx0 + 6.4)):
        door(mb, (x, by1, 0), (1, 0, 0), (0, 1, 0), w=1.1 - 0.1 * (i % 2), h=2.1 - 0.1 * (i % 2))
        window(mb, (x + 1.3, by1, 1.7), (1, 0, 0), (0, 1, 0), w=0.55, h=0.7)
    for x in (bx0 + 2.5, bx0 + 5.1):                        # spouts
        mb.box(T(x, by1 + 0.25, bh - 0.2) @ S(0.12, 0.5, 0.12), "fort_dk")
    mb.box(T(bx1 + 0.02, (by0 + by1) / 2, bh / 2) @ S(0.06, by1 - by0, 0.2), "fort_dk")
    # godown in the south-east corner: plaster with a red tiled roof, doors facing north
    gx0, gx1, gy0, gy1, gh = 6.9, IN_X, -IN_Y, -8.6, 3.2
    mb.box(T((gx0 + gx1) / 2, (gy0 + gy1) / 2, gh / 2) @ S(gx1 - gx0, gy1 - gy0, gh), "plaster")
    mb.box(T((gx0 + gx1) / 2, (gy0 + gy1) / 2, 0.22) @ S(gx1 - gx0 + 0.12, gy1 - gy0 + 0.12, 0.44), "fort_dk")
    tile_roof(mb, (gx0 + gx1) / 2, (gy0 + gy1) / 2, gx1 - gx0, gy1 - gy0, gh, 1.8)
    for x in (gx0 + 1.2, gx0 + 3.2):
        door(mb, (x, gy1, 0), (1, 0, 0), (0, 1, 0), w=1.4, h=2.3)
    window(mb, (gx1 - 0.6, gy1, 2.0), (1, 0, 0), (0, 1, 0), w=0.45, h=0.6)
    # governor's house, two storeys, north-east corner, front facing south
    hx0, hx1, hy0, hy1, hh = 4.0, IN_X, 7.2, IN_Y, 6.0
    mb.box(T((hx0 + hx1) / 2, (hy0 + hy1) / 2, hh / 2) @ S(hx1 - hx0, hy1 - hy0, hh), "plaster")
    mb.box(T((hx0 + hx1) / 2, (hy0 + hy1) / 2, 3.0) @ S(hx1 - hx0 + 0.1, hy1 - hy0 + 0.1, 0.18), "fort")
    mb.box(T((hx0 + hx1) / 2, (hy0 + hy1) / 2, 0.25) @ S(hx1 - hx0 + 0.12, hy1 - hy0 + 0.12, 0.5), "fort")
    tile_roof(mb, (hx0 + hx1) / 2, (hy0 + hy1) / 2, hx1 - hx0, hy1 - hy0, hh, 2.4)
    for x in (hx0 + 1.2, hx0 + 3.4, hx0 + 5.8):
        window(mb, (x, hy0, 1.6), (1, 0, 0), (0, -1, 0), w=0.7, h=1.1)
        window(mb, (x, hy0, 4.5), (1, 0, 0), (0, -1, 0), w=0.7, h=1.1)
    dxh = hx0 + 4.6
    door(mb, (dxh, hy0, 0.5), (1, 0, 0), (0, -1, 0), w=1.2, h=2.2)
    for i in range(3):                                        # steps up to the door
        mb.box(T(dxh, hy0 - 0.3 - i * 0.3, 0.5 - (i + 1) * 0.16) @ S(1.9, 0.3, 0.16 * (3 - i) + 0.1), "fort_lt")
    for x in (hx0 + 0.3, hx1 - 0.3):                          # corner quoins
        mb.box(T(x, hy0 + 0.02, hh / 2) @ S(0.5, 0.1, hh), "fort")
    # balcony on the first floor, on posts
    bxc = hx0 + 2.3
    mb.box(T(bxc, hy0 - 0.6, 3.25) @ S(3.4, 1.2, 0.14), "wood_door")
    for i in range(12):
        mb.box(T(bxc - 1.6 + i * 0.29, hy0 - 1.15, 3.7) @ S(0.06, 0.06, 0.8), "wood_door")
    mb.box(T(bxc, hy0 - 1.15, 4.1) @ S(3.4, 0.1, 0.08), "wood_door")
    for x in (bxc - 1.6, bxc + 1.6):
        mb.box(T(x, hy0 - 1.15, 1.6) @ S(0.12, 0.12, 3.2), "wood_door")
    # open pepper shed against the north wall: posts, mono-pitch tiled roof
    sx0, sx1 = SHED[0] - 3.8, SHED[0] + 3.8
    front = IN_Y - 3.3
    for x in (sx0, sx0 + 2.55, sx0 + 5.1, sx1):
        mb.box(T(x, front, 1.2) @ S(0.2, 0.2, 2.4), "wood_door")
        mb.box(T(x, front, 0.08) @ S(0.34, 0.34, 0.16), "fort_dk")
    mb.box(T(SHED[0], front, 2.42) @ S(sx1 - sx0 + 0.3, 0.22, 0.2), "wood_door")
    ang = math.atan2(0.75, IN_Y - front)
    L = math.hypot(IN_Y - front, 1.0) + 0.6
    mb.box(T(SHED[0], (front + IN_Y) / 2 - 0.25, 2.98) @ Rx(ang) @ S(sx1 - sx0 + 0.8, L, 0.14), "tile")
    for k in range(9):                                       # tile ribs
        mb.box(T(sx0 - 0.3 + k * (sx1 - sx0 + 0.6) / 8, (front + IN_Y) / 2 - 0.25, 3.07) @ Rx(ang)
               @ S(0.1, L, 0.06), "tile_dk")
    return mb.obj("Buildings", coll)


def build_courtyard(coll, rng):
    """Courtyard floor, darker patches, the paved road between the gates."""
    mb = kit.MB()
    mb.box(T(0, 0, -0.05) @ S(2 * IN_X + 0.2, 2 * IN_Y + 0.2, 0.1), "court")
    for i in range(16):
        x, y = rng.uniform(-13, 13), rng.uniform(-11, 11)
        if abs(x - TABLE[0]) < 4 and abs(y - TABLE[1]) < 4:
            continue
        pts = []
        r = rng.uniform(0.8, 2.2)
        for k in range(7):
            a = k * TAU / 7
            rr = r * rng.uniform(0.6, 1.0)
            pts.append((x + rr * math.cos(a), y + rr * 0.7 * math.sin(a)))
        prism(mb, pts, -0.01, 0.003, "court_dk")
    # paved road: irregular slabs from the sea gate to the land gate, wider at the gates
    x = -IN_X - WALL_T
    while x < IN_X + WALL_T:
        if -IN_X + 2.6 < x < IN_X - 2.2:
            x += 0.6
            continue
        w = rng.uniform(0.5, 0.8)
        y = GATE_Y - 1.5
        while y < GATE_Y + 1.5:
            h = rng.uniform(0.45, 0.75)
            if rng.random() > 0.06:
                flat(mb, x + w / 2, y + h / 2, w - 0.06, h - 0.06, 0.0, "paving" if rng.random() > 0.35 else "paving_dk",
                     rot=rng.uniform(-0.04, 0.04), th=0.03)
            y += h
        x += w
    return mb.obj("Courtyard", coll)


# ============================================================== the meeting
def make_carpet(name, coll, w=6.0, d=6.0):
    """Large carpet, mauve-brown field with a gold border of geometric inlay (no text)."""
    mb = kit.MB()
    mb.box(T(0, 0, 0.012) @ S(w, d, 0.024), "rug_gold")
    bw = 0.62                                          # border width
    flat(mb, 0, 0, w - 0.1, d - 0.1, 0.024, "rug_dk", th=0.002)
    flat(mb, 0, 0, w - 0.18, d - 0.18, 0.026, "rug_gold", th=0.002)
    flat(mb, 0, 0, w - 2 * bw, d - 2 * bw, 0.028, "rug_dk", th=0.002)
    flat(mb, 0, 0, w - 2 * bw - 0.1, d - 2 * bw - 0.1, 0.030, "rug_gold", th=0.002)
    flat(mb, 0, 0, w - 2 * bw - 0.2, d - 2 * bw - 0.2, 0.032, "rug", th=0.002)
    z = 0.028
    # border motifs: diamonds and little crosses alternating round the band
    for side in range(4):
        L = (w if side % 2 == 0 else d) - bw
        n = int(L / 0.42)
        for i in range(n):
            t = -L / 2 + (i + 0.5) * L / n
            off = (d if side % 2 == 0 else w) / 2 - bw / 2 - 0.04
            if side == 0:
                cx, cy = t, -off
            elif side == 1:
                cx, cy = off, t
            elif side == 2:
                cx, cy = t, off
            else:
                cx, cy = -off, t
            if i % 2 == 0:
                flat(mb, cx, cy, 0.2, 0.2, z, "rug_dk", rot=math.pi / 4)
                flat(mb, cx, cy, 0.09, 0.09, z + 0.003, "rug_gold", rot=math.pi / 4)
            else:
                flat(mb, cx, cy, 0.24, 0.05, z, "rug_dk", rot=(math.pi / 2 if side % 2 else 0) + math.pi / 4)
                flat(mb, cx, cy, 0.24, 0.05, z, "rug_dk", rot=(math.pi / 2 if side % 2 else 0) - math.pi / 4)
    # field: centre medallion, corner pieces, a scatter of small lozenges
    z = 0.034
    flat(mb, 0, 0, 1.5, 1.5, z, "rug_gold", rot=math.pi / 4)
    flat(mb, 0, 0, 1.25, 1.25, z + 0.002, "rug_dk", rot=math.pi / 4)
    flat(mb, 0, 0, 0.9, 0.9, z + 0.004, "rug", rot=math.pi / 4)
    flat(mb, 0, 0, 0.42, 0.42, z + 0.006, "rug_gold", rot=math.pi / 4)
    for a in range(4):
        ang = a * math.pi / 2
        flat(mb, 1.25 * math.cos(ang), 1.25 * math.sin(ang), 0.36, 0.36, z, "rug_gold", rot=math.pi / 4)
    fx, fy = w / 2 - bw - 0.1, d / 2 - bw - 0.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * fx, sy * fy
            flat(mb, cx - sx * 0.45, cy - sy * 0.12, 0.9, 0.24, z, "rug_gold")
            flat(mb, cx - sx * 0.12, cy - sy * 0.45, 0.24, 0.9, z, "rug_gold")
            flat(mb, cx - sx * 0.55, cy - sy * 0.55, 0.22, 0.22, z, "rug_gold", rot=math.pi / 4)
    for i in range(-2, 3):
        for j in range(-2, 3):
            if abs(i) + abs(j) in (3, 4) and not (abs(i) == 2 and abs(j) == 2):
                flat(mb, i * 0.78, j * 0.78, 0.14, 0.14, z, "rug_gold", rot=math.pi / 4)
    # tassels on the short ends
    for sy in (-1, 1):
        for i in range(int(w / 0.18)):
            x = -w / 2 + 0.09 + i * 0.18
            mb.box(T(x, sy * (d / 2 + 0.05), 0.006) @ S(0.05, 0.1, 0.012), "rug_gold")
    return mb.obj(name, coll)


def make_canopy(name, coll, w=4.6, d=3.8, h=3.15, seed=0):
    """Cream cloth canopy on four dark posts, with a sagging roof and valance."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * w / 2, sy * d / 2, 0), (sx * w / 2, sy * d / 2, h + 0.18), 0.065, 0.055, "pole", sides=6)
            mb.box(T(sx * w / 2, sy * d / 2, h + 0.22) @ S(0.13, 0.13, 0.08), "pole")
            mb.box(T(sx * w / 2, sy * d / 2, 0.05) @ S(0.22, 0.22, 0.1), "pole")
    posts = mb.obj(name + "Posts", coll)
    # roof cloth: a grid that sags between the posts, a little lumpy
    cl = kit.MB()
    nx, ny = 10, 8
    W, D = w + 0.2, d + 0.2
    vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            sag = 0.16 * (1 - (2 * u - 1) ** 2) * (1 - (2 * v - 1) ** 2) + 0.03 * math.sin(u * 7 + v * 3)
            row.append(cl.bm.verts.new(((u - 0.5) * W, (v - 0.5) * D, h + 0.12 - sag)))
        vs.append(row)
    for j in range(ny):
        for i in range(nx):
            cl.face([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]], "cloth_cream")
    # valance: hanging flaps with a scalloped edge and a thin gold trim
    for side in range(4):
        horiz = side % 2 == 0
        L = W if horiz else D
        sgn = -1 if side < 2 else 1
        n = int(L / 0.38)
        for i in range(n):
            t = -L / 2 + (i + 0.5) * L / n
            x, y = (t, sgn * D / 2) if horiz else (sgn * W / 2, t)
            sx, sy = (L / n + 0.01, 0.025) if horiz else (0.025, L / n + 0.01)
            cl.box(T(x, y, h + 0.0) @ S(sx, sy, 0.24), "cloth_cream")
            cl.cone(T(x, y, h - 0.17) @ Rx(math.pi) @ (Rz(0) if horiz else Rz(math.pi / 2)) @ S(1, 0.15, 1), "cloth_cream",
                    segments=4, r1=L / n * 0.55, r2=0.0, depth=0.12)
        if horiz:
            cl.box(T(0, sgn * (D / 2 + 0.015), h - 0.06) @ S(W, 0.01, 0.035), "rug_gold")
        else:
            cl.box(T(sgn * (W / 2 + 0.015), 0, h - 0.06) @ S(0.01, D, 0.035), "rug_gold")
    roof = cl.obj(name + "Cloth", coll)
    sol = roof.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.03
    return posts, roof


def make_table(name, coll, w=1.9, d=0.95, h=TABLE_H):
    mb = kit.MB(bevel=0.012)
    mb.box(T(0, 0, h - 0.025) @ S(w, d, 0.05), "wood_tbl")
    mb.box(T(0, 0, h - 0.07) @ S(w - 0.12, d - 0.12, 0.06), "wood_chair")
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - 0.1), sy * (d / 2 - 0.1)
            mb.cone(T(x, y, 0.15), "wood_chair", segments=6, r1=0.035, r2=0.05, depth=0.3)
            mb.ico(T(x, y, 0.36), "wood_chair", r=0.065, sub=1)
            mb.cone(T(x, y, 0.53), "wood_chair", segments=6, r1=0.05, r2=0.04, depth=0.26)
            mb.box(T(x, y, 0.025) @ S(0.09, 0.09, 0.05), "wood_chair")
    mb.box(T(0, 0, 0.14) @ S(w - 0.2, 0.05, 0.04), "wood_chair")
    for sx in (-1, 1):
        mb.box(T(sx * (w / 2 - 0.1), 0, 0.14) @ S(0.05, d - 0.2, 0.04), "wood_chair")
    return mb.obj(name, coll)


def make_table_props(name, coll, z, seed=0):
    """Blank parchment (rolled ends), quill and inkpot, an open chest of gold coins,
    loose coins, a candlestick, sealing wax and tied scrolls. Origin at the table centre."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.004)
    # the contract: a blank sheet with rolled ends, turned toward the rajas
    px, py, pw, pd = 0.0, 0.02, 0.62, 0.44
    mb.box(T(px, py, z + 0.003) @ Rz(0.06) @ S(pw, pd, 0.006), "parchment")
    for s in (-1, 1):
        mb.seg((px - pw / 2 + 0.02, py + s * pd / 2, z + 0.022), (px + pw / 2 + 0.02, py + s * pd / 2 + 0.03, z + 0.022),
               0.025, 0.025, "parchment", sides=8)
    # quill in the inkpot hand's reach, feather lying on the table
    qx, qy = -0.52, -0.18
    mb.cone(T(qx, qy, z + 0.03), "black", segments=8, r1=0.045, r2=0.035, depth=0.06)
    mb.cone(T(qx, qy, z + 0.065), "brass", segments=8, r1=0.03, r2=0.02, depth=0.015)
    q0, q1 = Vector((-0.28, -0.3, z + 0.006)), Vector((-0.02, -0.16, z + 0.02))
    mb.seg(q0, q1, 0.006, 0.004, "white", sides=4)
    d = (q1 - q0).normalized()
    mid = q0.lerp(q1, 0.6)
    mb.box(T(mid) @ Rz(math.atan2(d.y, d.x)) @ S(0.22, 0.045, 0.006), "white")
    # chest of gold, lid thrown back
    cx, cy = 0.62, 0.12
    mb.box(T(cx, cy, z + 0.065) @ S(0.3, 0.2, 0.13), "wood_door")
    for t in (-0.1, 0.1):
        mb.box(T(cx + t, cy, z + 0.066) @ S(0.03, 0.21, 0.135), "brass")
    mb.box(T(cx, cy + 0.101, z + 0.08) @ S(0.05, 0.01, 0.05), "brass")
    mb.box(T(cx, cy - 0.15, z + 0.17) @ Rx(-0.35) @ S(0.3, 0.025, 0.2), "wood_door")
    mb.box(T(cx, cy - 0.137, z + 0.17) @ Rx(-0.35) @ S(0.31, 0.02, 0.03), "brass")
    for i in range(14):                                     # heaped coins
        mb.cone(T(cx + rng.uniform(-0.12, 0.12), cy + rng.uniform(-0.07, 0.07), z + 0.13 + rng.uniform(0, 0.03))
                @ Rx(rng.uniform(-0.4, 0.4)) @ Ry(rng.uniform(-0.4, 0.4)), "gold", segments=8, r1=0.022, r2=0.022, depth=0.008)
    mb.ico(T(cx, cy, z + 0.118) @ S(1.4, 0.9, 0.25), "gold", r=0.1, sub=1)
    for i in range(6):                                      # loose coins on the table
        mb.cone(T(cx - 0.25 + rng.uniform(-0.12, 0.12), cy - 0.05 + rng.uniform(-0.12, 0.12), z + 0.004),
                "gold", segments=8, r1=0.022, r2=0.022, depth=0.008)
    # candlestick, sealing wax, tied scrolls
    mb.cone(T(-0.75, 0.25, z + 0.01), "brass", segments=8, r1=0.06, r2=0.05, depth=0.02)
    mb.cone(T(-0.75, 0.25, z + 0.08), "brass", segments=6, r1=0.015, r2=0.015, depth=0.14)
    mb.cone(T(-0.75, 0.25, z + 0.2), "white", segments=6, r1=0.02, r2=0.02, depth=0.12)
    mb.box(T(0.3, -0.3, z + 0.01) @ Rz(0.4) @ S(0.1, 0.02, 0.02), "red")
    mb.cone(T(0.42, -0.32, z + 0.03), "brass", segments=8, r1=0.02, r2=0.03, depth=0.06)
    for k, (sx_, sy_) in enumerate(((0.75, -0.25), (0.8, -0.32))):
        mb.seg((sx_ - 0.13, sy_, z + 0.03 + k * 0.0), (sx_ + 0.13, sy_ + 0.03, z + 0.03), 0.03, 0.03, "parchment", sides=8)
        mb.cone(T(sx_, sy_ + 0.015, z + 0.03) @ Ry(math.pi / 2), "red", segments=8, r1=0.033, r2=0.033, depth=0.02)
    return mb.obj(name, coll)


def make_chair(name, coll):
    """Wooden armless chair, seat top at 0.47, back toward -Y."""
    mb = kit.MB(bevel=0.008)
    mb.box(T(0, 0.08, 0.45) @ S(0.5, 0.48, 0.05), "wood_chair")
    for sx in (-1, 1):
        for y in (-0.13, 0.29):
            mb.box(T(sx * 0.21, y, 0.215) @ S(0.05, 0.05, 0.43), "wood_chair")
        mb.box(T(sx * 0.21, -0.17, 0.6) @ S(0.055, 0.055, 1.2), "wood_chair")
        mb.ico(T(sx * 0.21, -0.17, 1.23), "wood_chair", r=0.04, sub=1)
        mb.box(T(sx * 0.21, 0.08, 0.12) @ S(0.03, 0.4, 0.03), "wood_chair")
    for z in (0.72, 1.12):
        mb.box(T(0, -0.17, z) @ S(0.42, 0.045, 0.08 if z < 1 else 0.12), "wood_chair")
    for x in (-0.09, 0.0, 0.09):
        mb.box(T(x, -0.17, 0.92) @ S(0.04, 0.03, 0.36), "wood_tbl")
    return mb.obj(name, coll)


def make_stool(name, coll):
    """Low carved stool with a red cushion (the rajas' seats). Seat top at 0.47."""
    mb = kit.MB(bevel=0.008)
    mb.box(T(0, 0.05, 0.4) @ S(0.5, 0.46, 0.05), "wood_tbl")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * 0.2, 0.05 + sy * 0.18, 0), (sx * 0.17, 0.05 + sy * 0.15, 0.38), 0.035, 0.03, "wood_tbl", sides=6)
    mb.box(T(0, 0.05, 0.445) @ S(0.48, 0.44, 0.06), "red")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.ico(T(sx * 0.22, 0.05 + sy * 0.2, 0.47), "gold", r=0.025, sub=1)
    return mb.obj(name, coll)


# ================================================================== figures
# Figures face +Y, built as separate parts under a root empty (so heads nod and arms
# gesture). Parts are drawn in standing-figure coordinates (kit layout: hips 0.88,
# shoulders 1.4, head 1.63) and placed at their pivots; a seated figure has its upper
# body dropped by SEAT_DROP and its legs drawn bent onto a 0.47 m seat.
SEAT_DROP = -0.36


class Figure:
    PIV = {"hips": ((0, 0, 0), None), "body": ((0, 0, 0.92), "hips"), "head": ((0, 0, 1.45), "body"),
           "armR": ((0.27, 0, 1.4), "body"), "armL": ((-0.27, 0, 1.4), "body"),
           "foreR": ((0.27, 0, 1.12), "armR"), "foreL": ((-0.27, 0, 1.12), "armL"),
           "legR": ((0.1, 0, 0.88), "hips"), "legL": ((-0.1, 0, 0.88), "hips")}

    def __init__(self, seated=False):
        self.mbs = {p: kit.MB(bevel=kit.FIG_BEVEL) for p in self.PIV}
        self.seated = seated

    def put(self, part, prim, M, m, **kw):
        piv = Vector(self.PIV[part][0])
        getattr(self.mbs[part], prim)(T(-piv) @ M, m, **kw)

    def build(self, name, coll, loc=(0, 0, 0), rot=0.0):
        root = bpy.data.objects.new(name, None)
        root.empty_display_size = 0.3
        coll.objects.link(root)
        root.location = loc
        root.rotation_euler[2] = rot
        parts = {}
        for p, (piv, par) in self.PIV.items():           # parents come first in PIV
            ob = self.mbs[p].obj(f"{name}_{p}", coll, parent=parts[par] if par else root)
            pp = Vector(self.PIV[par][0]) if par else Vector((0, 0, 0))
            ob.location = Vector(piv) - pp + Vector((0, 0, SEAT_DROP if (p == "body" and self.seated) else 0.0))
            parts[p] = ob
        return root, parts


def _face(fg, skin, moustache=True, brows="hair"):
    """Neck, head and face into the head part (kit proportions)."""
    fg.put("head", "cone", T(0, 0, 1.47), skin, segments=6, r1=0.065, r2=0.065, depth=0.1)
    fg.put("head", "ico", T(0, 0, 1.63) @ S(0.9, 0.95, 1.05), skin, r=0.145, sub=1)
    for sx in (-1, 1):
        fg.put("head", "box", T(sx * 0.048, 0.128, 1.655) @ S(0.032, 0.02, 0.034), "black")
        fg.put("head", "box", T(sx * 0.05, 0.126, 1.7) @ S(0.045, 0.015, 0.012), brows)
        fg.put("head", "box", T(sx * 0.128, 0.0, 1.63) @ S(0.03, 0.05, 0.06), skin)          # ears
    fg.put("head", "box", T(0, 0.14, 1.618) @ S(0.034, 0.04, 0.055), skin)                  # nose
    if moustache:
        fg.put("head", "box", T(0, 0.132, 1.585) @ S(0.12, 0.025, 0.026), "hair")
        for sx in (-1, 1):
            fg.put("head", "box", T(sx * 0.066, 0.128, 1.595) @ Rz(0) @ Ry(sx * 0.6) @ S(0.03, 0.022, 0.022), "hair")
    else:
        fg.put("head", "box", T(0, 0.134, 1.575) @ S(0.05, 0.012, 0.012), "rug_dk")           # mouth


def _seated_legs(fg, thigh, shin, shoe, robe=None):
    """Legs bent onto a 0.47 m seat, in root space (hips part)."""
    for sx in (-1, 1):
        fg.put("hips", "box", T(sx * 0.1, 0.18, 0.555) @ S(0.17, 0.5, 0.16), thigh)
        fg.put("hips", "box", T(sx * 0.1, 0.41, 0.3) @ S(0.15, 0.16, 0.5), shin)
        fg.put("hips", "box", T(sx * 0.1, 0.47, 0.035) @ S(0.15, 0.27, 0.07), shoe)
    if robe:
        fg.put("hips", "box", T(0, 0.15, 0.6) @ S(0.44, 0.56, 0.1), robe)
        fg.put("hips", "box", T(0, 0.455, 0.47) @ S(0.42, 0.06, 0.32), robe)
        fg.put("hips", "cone", T(0, -0.02, 0.6), robe, segments=8, r1=0.3, r2=0.26, depth=0.18)


def make_official(name, coll, seed=0, seated=True, hat=True):
    """VOC official: navy coat with two rows of brass buttons and turned-back cuffs,
    white cravat and jabot, powdered wig with side curls and queue, black tricorn,
    buff breeches, white stockings, buckled black shoes. No musket or cross-belts."""
    rng = random.Random(seed)
    fg = Figure(seated)
    skin = "skin_pale"
    if seated:
        _seated_legs(fg, "breeches", "stocking", "black")
        for sx in (-1, 1):
            fg.put("hips", "box", T(sx * 0.1, 0.6, 0.075) @ S(0.07, 0.03, 0.04), "brass")    # shoe buckles
            fg.put("hips", "box", T(sx * 0.1, 0.42, 0.54) @ S(0.17, 0.17, 0.05), "breeches")  # knee band
            fg.put("hips", "box", T(sx * 0.115, 0.12, 0.665) @ Rx(-0.05) @ S(0.2, 0.36, 0.05), "coat_blue")  # skirts
            fg.put("hips", "box", T(sx * 0.24, -0.02, 0.5) @ S(0.05, 0.3, 0.32), "coat_blue")
        fg.put("hips", "box", T(0, -0.17, 0.45) @ S(0.46, 0.05, 0.34), "coat_blue")
    else:
        for leg, sx in (("legR", 1), ("legL", -1)):
            fg.put(leg, "box", T(sx * 0.1, 0, 0.66) @ S(0.17, 0.18, 0.4), "breeches")
            fg.put(leg, "box", T(sx * 0.1, 0, 0.27) @ S(0.15, 0.16, 0.46), "stocking")
            fg.put(leg, "box", T(sx * 0.1, 0.05, 0.035) @ S(0.15, 0.26, 0.07), "black")
            fg.put(leg, "box", T(sx * 0.1, 0.17, 0.075) @ S(0.07, 0.03, 0.04), "brass")
        fg.put("body", "cone", T(0, 0, 0.73), "coat_blue", segments=8, r1=0.29, r2=0.24, depth=0.42)
    # body
    fg.put("body", "cone", T(0, 0, 1.17) @ Rz(math.pi / 4) @ S(1.0, 0.62, 1.0), "coat_blue", segments=4,
           r1=0.24, r2=0.32, depth=0.48)
    fg.put("body", "cone", T(0, 0, 0.96), "coat_blue", segments=8, r1=0.25, r2=0.24, depth=0.12)
    fg.put("body", "box", T(0, 0.15, 1.15) @ S(0.2, 0.04, 0.5), "coat_blue")
    fg.put("body", "box", T(0, 0.168, 1.15) @ S(0.012, 0.01, 0.48), "black")                  # coat opening
    for z in (0.98, 1.06, 1.14, 1.22, 1.30):
        for sx in (-1, 1):
            fg.put("body", "box", T(sx * 0.07, 0.175, z) @ S(0.03, 0.02, 0.03), "brass")
    for sx in (-1, 1):                                                                     # pocket flaps
        fg.put("body", "box", T(sx * 0.17, 0.12, 0.99) @ S(0.11, 0.04, 0.04), "coat_blue")
        fg.put("body", "box", T(sx * 0.17, 0.142, 0.99) @ S(0.03, 0.01, 0.03), "brass")
    fg.put("body", "box", T(0, 0.15, 1.42) @ S(0.15, 0.06, 0.09), "white")                   # cravat
    fg.put("body", "cone", T(0, 0.17, 1.33) @ Rx(math.pi), "white", segments=6, r1=0.065, r2=0.015, depth=0.15)
    fg.put("body", "cone", T(0, 0, 1.415), "coat_blue", segments=8, r1=0.11, r2=0.09, depth=0.06)  # collar
    # arms: navy sleeves, deep cuffs, lace, pale hands
    for arm, fore, sx in (("armR", "foreR", 1), ("armL", "foreL", -1)):
        fg.put(arm, "box", T(sx * 0.27, 0, 1.27) @ S(0.13, 0.14, 0.3), "coat_blue")
        fg.put(fore, "box", T(sx * 0.27, 0, 0.98) @ S(0.125, 0.135, 0.3), "coat_blue")
        fg.put(fore, "box", T(sx * 0.27, 0, 0.86) @ S(0.16, 0.17, 0.1), "coat_blue")
        fg.put(fore, "box", T(sx * 0.27, 0.088, 0.86) @ S(0.03, 0.01, 0.03), "brass")
        fg.put(fore, "box", T(sx * 0.27, 0, 0.8) @ S(0.11, 0.12, 0.04), "white")
        fg.put(fore, "box", T(sx * 0.27, 0.01, 0.74) @ S(0.1, 0.11, 0.1), skin)
    # head: face, wig with curls and queue, tricorn
    _face(fg, skin, moustache=False, brows="wig")
    fg.put("head", "ico", T(0, -0.06, 1.68) @ S(1.02, 0.9, 0.88), "wig", r=0.145, sub=1)
    for sx in (-1, 1):
        for z in (1.6, 1.53):                                                              # side curls
            fg.mbs["head"].seg(Vector((sx * 0.14, -0.13, z + 0.04 - 1.45)), Vector((sx * 0.14, -0.02, z + 0.04 - 1.45)),
                               0.036, 0.036, "wig", sides=6)
    fg.mbs["head"].seg(Vector((0, -0.15, 0.17)), Vector((0, -0.19, -0.02)), 0.045, 0.03, "wig", sides=6)
    fg.put("head", "box", T(0, -0.17, 1.55) @ S(0.1, 0.03, 0.05), "black")                   # queue ribbon
    if hat:
        rot = rng.uniform(-0.1, 0.1) + math.pi / 2
        fg.put("head", "cone", T(0, 0, 1.79) @ Rz(rot), "black", segments=3, r1=0.32, r2=0.28, depth=0.1)
        fg.put("head", "cone", T(0, 0, 1.845) @ Rz(rot), "black", segments=3, r1=0.29, r2=0.25, depth=0.035)
        fg.put("head", "ico", T(0, 0, 1.83) @ S(1, 1, 0.55), "black", r=0.145, sub=1)
        fg.put("head", "ico", T(0.0, 0.22, 1.82), "black", r=0.025, sub=1)
    return fg.build(name, coll)


def make_raja(name, coll, seed=0, seated=False, sash_tilt=0.0):
    """A small raja: white jama with long sleeves and a gold hem, wide red waist sash
    edged in gold with a tucked dagger, layered gold necklaces, gold armlets and
    bracelets, earrings, big red turban with gold bands, a jewel and a white plume."""
    rng = random.Random(seed)
    fg = Figure(seated)
    if seated:
        _seated_legs(fg, "white", "white", "black", robe="white")
        fg.put("hips", "box", T(0, 0.485, 0.32) @ S(0.43, 0.02, 0.04), "gold")
    else:
        for sx in (-1, 1):
            fg.put("hips", "box", T(sx * 0.1, 0, 0.25) @ S(0.15, 0.16, 0.42), "white")
            fg.put("hips", "box", T(sx * 0.1, 0.05, 0.035) @ S(0.15, 0.26, 0.07), "black")
            fg.put("hips", "cone", T(sx * 0.1, 0.19, 0.08) @ Rx(-1.0), "black", segments=4, r1=0.04, r2=0.0, depth=0.1)
        fg.put("body", "cone", T(0, 0, 0.66), "white", segments=8, r1=0.31, r2=0.22, depth=0.64)
        fg.put("body", "cone", T(0, 0, 0.36), "gold", segments=8, r1=0.315, r2=0.31, depth=0.04)
    fg.put("body", "cone", T(0, 0, 1.17) @ Rz(math.pi / 4) @ S(1.0, 0.62, 1.0), "white", segments=4,
           r1=0.24, r2=0.32, depth=0.48)
    fg.put("body", "box", T(0.05, 0.15, 1.2) @ Rz(0.0) @ Ry(0.5) @ S(0.012, 0.02, 0.36), "gold")   # angarkha fold
    fg.put("body", "cone", T(0, 0, 0.99), "red", segments=8, r1=0.232, r2=0.232, depth=0.13)
    for z in (0.92, 1.06):
        fg.put("body", "cone", T(0, 0, z), "gold", segments=8, r1=0.236, r2=0.236, depth=0.02)
    fg.put("body", "box", T(-0.08, 0.2, 0.8) @ Ry(sash_tilt) @ S(0.09, 0.03, 0.32), "red")         # sash end
    fg.put("body", "box", T(-0.08, 0.2, 0.65) @ Ry(sash_tilt) @ S(0.095, 0.035, 0.03), "gold")
    fg.put("body", "box", T(0.09, 0.21, 1.0) @ Rz(0.2) @ S(0.04, 0.03, 0.12), "gold")               # dagger hilt
    for z, r in ((1.42, 0.165), (1.35, 0.19), (1.28, 0.21)):
        fg.put("body", "cone", T(0, 0.02, z) @ Rx(-0.25), "gold", segments=10, r1=r, r2=r, depth=0.022)
    fg.put("body", "ico", T(0, 0.19, 1.24), "red", r=0.03, sub=1)
    fg.put("body", "ico", T(0, 0.19, 1.24) @ S(1.4, 0.5, 1.4), "gold", r=0.026, sub=1)
    for arm, fore, sx in (("armR", "foreR", 1), ("armL", "foreL", -1)):
        fg.put(arm, "box", T(sx * 0.27, 0, 1.27) @ S(0.125, 0.135, 0.3), "white")
        fg.put(arm, "cone", T(sx * 0.27, 0, 1.24), "gold", segments=6, r1=0.082, r2=0.082, depth=0.05)
        fg.put(fore, "box", T(sx * 0.27, 0, 0.97) @ S(0.12, 0.13, 0.3), "white")
        fg.put(fore, "cone", T(sx * 0.27, 0, 0.84), "gold", segments=6, r1=0.075, r2=0.075, depth=0.04)
        fg.put(fore, "box", T(sx * 0.27, 0.01, 0.77) @ S(0.11, 0.12, 0.12), "skin")
    _face(fg, "skin")
    for sx in (-1, 1):
        fg.put("head", "ico", T(sx * 0.135, 0.01, 1.57), "gold", r=0.022, sub=1)
    # turban: wrapped red dome with two gold bands, front jewel, white plume
    fg.put("head", "cone", T(0, -0.005, 1.72), "red", segments=8, r1=0.162, r2=0.178, depth=0.11)
    fg.put("head", "ico", T(0, -0.01, 1.8) @ S(1.0, 1.0, 0.62), "red", r=0.178, sub=1)
    fg.put("head", "cone", T(0, -0.005, 1.705) @ Rx(-0.05), "gold", segments=8, r1=0.168, r2=0.168, depth=0.025)
    fg.put("head", "cone", T(0, -0.01, 1.775) @ Rx(0.1), "gold", segments=8, r1=0.18, r2=0.18, depth=0.025)
    fg.put("head", "ico", T(0, 0.17, 1.77), "gold", r=0.04, sub=1)
    fg.put("head", "ico", T(0, 0.2, 1.77), "red", r=0.02, sub=1)
    fg.mbs["head"].seg(Vector((0, 0.16, 0.36)), Vector((0, 0.11, 0.58)), 0.026, 0.006, "white", sides=5)
    fg.mbs["head"].seg(Vector((0, 0.11, 0.58)), Vector((0, 0.06, 0.62)), 0.008, 0.003, "white", sides=4)
    return fg.build(name, coll)


def make_porter(name, coll, seed=0, robe_cloth="cloth_w"):
    """Bare-chested porter in a white mundu with a cloth coil on his head (the sack
    sits on it). Separate legs and arms for walking. Returns (root, parts)."""
    rng = random.Random(seed)
    fg = Figure(False)
    skin = "skin"
    for leg, sx in (("legR", 1), ("legL", -1)):
        fg.put(leg, "box", T(sx * 0.1, 0, 0.46) @ S(0.15, 0.16, 0.84), skin)
        fg.put(leg, "box", T(sx * 0.1, 0.05, 0.035) @ S(0.15, 0.24, 0.07), skin)
    fg.put("body", "cone", T(0, 0, 1.17) @ Rz(math.pi / 4) @ S(1.0, 0.62, 1.0), skin, segments=4,
           r1=0.24, r2=0.32, depth=0.48)
    fg.put("body", "cone", T(0, 0, 0.66), robe_cloth, segments=8, r1=0.26, r2=0.215, depth=0.64)   # mundu
    fg.put("body", "cone", T(0, 0, 0.97), robe_cloth, segments=8, r1=0.222, r2=0.215, depth=0.07)
    fg.put("body", "box", T(0.12, 0.2, 0.75) @ S(0.08, 0.02, 0.38), robe_cloth)                    # fold
    if rng.random() > 0.5:                                                                        # shoulder cloth
        fg.put("body", "box", T(0.05, 0.0, 1.22) @ Ry(0.55) @ S(0.06, 0.3, 0.5), "cloth_w")
    for arm, fore, sx in (("armR", "foreR", 1), ("armL", "foreL", -1)):
        fg.put(arm, "box", T(sx * 0.27, 0, 1.27) @ S(0.11, 0.12, 0.3), skin)
        fg.put(fore, "box", T(sx * 0.27, 0, 0.97) @ S(0.105, 0.115, 0.3), skin)
        fg.put(fore, "box", T(sx * 0.27, 0.01, 0.77) @ S(0.12, 0.13, 0.13), skin)
    _face(fg, skin, moustache=rng.random() > 0.3)
    fg.put("head", "ico", T(0, -0.025, 1.69) @ S(0.98, 1.0, 0.72), "hair", r=0.145, sub=1)
    fg.put("head", "cone", T(0, -0.01, 1.8), "cloth_w", segments=8, r1=0.12, r2=0.1, depth=0.06)   # head pad
    root, parts = fg.build(name, coll)
    # the sack, on the head pad (scaled to 0 while the porter walks back empty)
    sm = kit.MB()
    sm.ico(T(0, 0, 0.2) @ S(0.44, 0.3, 0.2), "jute", r=1.0, sub=1, jitter=0.06, rng=rng)
    sm.cone(T(0.44, 0, 0.2) @ Ry(math.pi / 2), "jute", segments=6, r1=0.09, r2=0.12, depth=0.12)
    sm.cone(T(0.39, 0, 0.2) @ Ry(math.pi / 2), "rope", segments=6, r1=0.1, r2=0.1, depth=0.04)
    sack = sm.obj(f"{name}_sack", coll, parent=parts["head"])
    sack.location = (0, -0.01, 0.37)
    sack.rotation_euler[2] = rng.uniform(-0.3, 0.3)
    parts["sack"] = sack
    return root, parts


def make_attendant(name, coll, seed=0):
    """A raja's attendant holding the ceremonial red umbrella with a gold fringe."""
    root, parts = make_porter(name, coll, seed)
    parts["sack"].scale = (0, 0, 0)
    um = kit.MB(bevel=0.005)
    um.seg((0, 0, -0.1), (0, 0, 1.6), 0.025, 0.025, "wood_door", sides=6)
    um.cone(T(0, 0, 1.65), "umbrella", segments=12, r1=0.65, r2=0.05, depth=0.35)
    um.cone(T(0, 0, 1.5), "gold", segments=12, r1=0.66, r2=0.66, depth=0.05)
    for k in range(24):
        a = k * TAU / 24
        um.box(T(0.65 * math.cos(a), 0.65 * math.sin(a), 1.43) @ Rz(a) @ S(0.03, 0.06, 0.12), "gold")
    um.ico(T(0, 0, 1.87), "gold", r=0.06, sub=1)
    u = um.obj(f"{name}_umbrella", coll, parent=parts["foreR"])
    u.location = (0, 0.06, -0.33)
    parts["umbrella"] = u
    return root, parts


# ============================================================== animation
def key_set(ob, path, frame, value):
    setattr(ob, path, value)
    ob.keyframe_insert(path, frame=frame)


def with_interp(kind, fn):
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = kind
    try:
        fn()
    finally:
        prefs.keyframe_new_interpolation_type = old


def pose(parts, rots):
    """Set rest rotations: {part: (rx, ry, rz)}."""
    for p, r in rots.items():
        parts[p].rotation_euler = r


def idle(parts, rng, frames, body=0.025, head=0.12, every=(45, 80)):
    """Breathing sway of the body, the head looking about and nodding."""
    b0 = parts["body"].rotation_euler.copy()
    h0 = parts["head"].rotation_euler.copy()
    f = 1
    while f <= frames + 40:
        key_set(parts["body"], "rotation_euler", f,
                (b0.x + rng.uniform(-body, body), b0.y + rng.uniform(-body, body), b0.z + rng.uniform(-body, body) * 2))
        f += rng.randint(*every)
    f = 1 + rng.randint(0, 20)
    while f <= frames + 40:
        key_set(parts["head"], "rotation_euler", f,
                (h0.x + rng.uniform(-0.6, 1.0) * head * 0.6, h0.y + rng.uniform(-0.3, 0.3) * head,
                 h0.z + rng.uniform(-1, 1) * head * 2))
        f += rng.randint(*every)


def gesture(parts, side, f0, f1, lift=1.1, fore=0.9, out=0.25, beats=2):
    """Arm raised forward from f0, the forearm beating `beats` times, lowered by f1."""
    arm, frm = parts["arm" + side], parts["fore" + side]
    a0, r0 = arm.rotation_euler.copy(), frm.rotation_euler.copy()
    sgn = 1 if side == "R" else -1
    key_set(arm, "rotation_euler", f0, a0)
    key_set(frm, "rotation_euler", f0, r0)
    up = f0 + 10
    key_set(arm, "rotation_euler", up, (a0.x + lift, a0.y, a0.z + sgn * out))
    key_set(frm, "rotation_euler", up, (r0.x + fore, r0.y, r0.z))
    span = (f1 - 12) - up
    for k in range(beats):
        fm = up + span * (k + 0.5) / beats
        key_set(frm, "rotation_euler", int(fm), (r0.x + fore + 0.35, r0.y, r0.z - sgn * 0.2))
        key_set(arm, "rotation_euler", int(fm), (a0.x + lift - 0.1, a0.y, a0.z + sgn * out * 1.3))
        fm2 = up + span * (k + 1.0) / beats
        key_set(frm, "rotation_euler", int(fm2), (r0.x + fore, r0.y, r0.z))
        key_set(arm, "rotation_euler", int(fm2), (a0.x + lift, a0.y, a0.z + sgn * out))
    key_set(arm, "rotation_euler", f1, a0)
    key_set(frm, "rotation_euler", f1, r0)


def walk_loop(root, parts, loop, phase, speed, frames, pauses=(), step_len=0.62):
    """Walk a closed polyline over and over (phase 0..1 staggers several walkers).
    pauses: [(loop vertex index, seconds, "drop" | "pick")]: the walker stops there
    before walking on. The sack shows only between a pick and a drop; while it is
    carried the right arm is raised to steady it on the head."""
    pts = [Vector((x, y, 0)) for x, y in loop]
    n = len(pts)
    segs = [(pts[(i + 1) % n] - pts[i]).length for i in range(n)]
    pmap = {i: (sec, kind) for i, sec, kind in pauses}
    # timeline: (start time, duration, "pause"/"walk", vertex or segment index, carrying)
    timeline, t, carrying = [], 0.0, False
    for _ in range(2):                         # first pass settles the carry state
        timeline, t = [], 0.0
        for i in range(n):
            if i in pmap:
                timeline.append((t, pmap[i][0], "pause", i, carrying))
                t += pmap[i][0]
                carrying = pmap[i][1] == "pick"
            timeline.append((t, segs[i] / speed, "walk", i, carrying))
            t += segs[i] / speed
    period = t
    walked = [sum(segs[:i]) for i in range(n)]

    def state(time):
        time %= period
        for t0, dur, kind, i, c in timeline:
            if time < t0 + dur:
                u = (time - t0) / dur
                if kind == "pause":
                    after = pmap[i][1] == "pick"
                    return pts[i], (i - 1) % n, walked[i], (c if u < 0.5 else after), True
                return pts[i].lerp(pts[(i + 1) % n], u), i, walked[i] + segs[i] * u, c, False
        return pts[0], n - 1, 0.0, False, False

    prev = None
    for f in range(1, frames + 1, 2):
        p, si, dist, carry, paused = state((f - 1) / kit.FPS + phase * period)
        d = pts[(si + 1) % n] - pts[si]
        rz = math.atan2(d.y, d.x) - math.pi / 2
        if prev is not None:                    # unwrap, so a turn never spins the long way round
            rz += TAU * round((prev - rz) / TAU)
        prev = rz
        key_set(root, "location", f, (p.x, p.y, ground_z(p.x, p.y)))
        key_set(root, "rotation_euler", f, (0, 0, rz))
        sw = 0.0 if paused else math.sin(math.pi * dist / step_len)
        key_set(parts["legR"], "rotation_euler", f, (0.42 * sw, 0, 0))
        key_set(parts["legL"], "rotation_euler", f, (-0.42 * sw, 0, 0))
        key_set(parts["body"], "location", f, (0, 0, 0.92 + 0.03 * abs(sw)))
        if carry:
            key_set(parts["armR"], "rotation_euler", f, (0.25, -2.7, 0.0))
            key_set(parts["foreR"], "rotation_euler", f, (0.0, -0.3, 0.0))
        else:
            key_set(parts["armR"], "rotation_euler", f, (0.35 * sw, 0, 0))
            key_set(parts["foreR"], "rotation_euler", f, (0.25, 0, 0))
        key_set(parts["armL"], "rotation_euler", f, (-0.35 * sw, 0, 0))
        key_set(parts["foreL"], "rotation_euler", f, (0.25, 0, 0))
        k = 1.0 if carry else 0.0
        with_interp("CONSTANT", lambda: key_set(parts["sack"], "scale", f, (k, k, k)))


# =================================================================== scene
def make_sea(coll, seed=2):
    """Faceted sea west of the beach, shallow green-blue near the shore, with foam."""
    rng = random.Random(seed)
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new("Col")
    xs = [x for x in range(-700, -130, 15)] + [x * 1.0 for x in range(-130, -14, 3)]
    ys = [y for y in range(-700, -120, 15)] + [y * 1.0 for y in range(-120, 121, 3)] + [y for y in range(135, 701, 15)]
    lin = [kit.srgb_to_linear(c) for c in (cw.SEA_SHALLOW, cw.SEA_DEEP, cw.SEA_FOAM)]
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            step = 3.0 if (x >= -130 and -120 <= y <= 120) else 15.0
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                jx, jy = rng.uniform(-0.3, 0.3) * step, rng.uniform(-0.3, 0.3) * step
            px, py = x + jx, y + jy
            v = bm.verts.new((px, py, SEA_Z + rng.uniform(-0.03, 0.03)))
            depth = shore_x(py) - px
            t = _ss(0, 45, depth)
            c = [lin[0][k] * (1 - t) + lin[1][k] * t for k in range(3)]
            if depth < 1.4:
                u = max(0.0, 1.0 - max(0.0, depth) / 1.4)
                c = [c[k] * (1 - u) + lin[2][k] * u for k in range(3)]
            s = rng.uniform(0.95, 1.05)
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
    coll.objects.link(ob)
    return ob


def animate_sea(sea, rig, frames):
    """Gentle swell: a cloud-noise displacement drifting slowly shoreward."""
    tex = bpy.data.textures.new("KochiSwell", "CLOUDS")
    tex.noise_scale = 5.0
    tex.noise_depth = 0
    mod = sea.modifiers.new("Swell", "DISPLACE")
    mod.texture = tex
    mod.texture_coords = "OBJECT"
    e = bpy.data.objects.new("SwellDriver", None)
    rig.objects.link(e)
    mod.texture_coords_object = e
    mod.strength = 0.35
    mod.mid_level = 0.5

    def keys():
        e.location = (0, 0, 0)
        e.keyframe_insert("location", frame=1)
        e.location = (5.0, 2.0, 0)
        e.keyframe_insert("location", frame=frames)
    kit.keyframe_linear(keys)


def make_land(coll, seed=1):
    """Ground round the fort: beach to the west, open sandy glacis, grass and dirt
    yards in the town beyond. (The courtyard floor is its own object.)"""
    rng = random.Random(seed)
    xs = [x for x in range(-260, -60, 10)] + [x * 1.0 for x in range(-60, 61, 2)] + [x for x in range(70, 261, 10)]
    ys = [y for y in range(-260, -60, 10)] + [y * 1.0 for y in range(-60, 61, 2)] + [y for y in range(70, 261, 10)]
    bm = bmesh.new()
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            step = 2.0 if (-60 <= x <= 60 and -60 <= y <= 60) else 10.0
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                jx, jy = rng.uniform(-0.3, 0.3) * step, rng.uniform(-0.3, 0.3) * step
            px, py = x + jx, y + jy
            h = height(px, py)
            if abs(px) < OUT_X - 0.5 and abs(py) < OUT_Y - 0.5:
                h = -0.2
            row.append(bm.verts.new((px, py, h)))
        grid.append(row)
    sand, wet, grass, dirt, grass_lt = range(5)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            c = f.calc_center_median()
            n = math.sin(c.x / 5.1 + 0.7) * math.sin(c.y / 4.3) + rng.uniform(-0.35, 0.35)
            if c.x < BEACH_X:
                f.material_index = wet if c.x < shore_x(c.y) + 1.8 else sand
            elif in_fort(c.x, c.y, 9.0) or abs(c.y - GATE_Y) < 2.2 and c.x > 0:
                f.material_index = sand if n > -0.6 else dirt
            else:
                f.material_index = grass if n > 0.2 else (grass_lt if n > -0.4 else dirt)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("Land")
    bm.to_mesh(me)
    bm.free()
    for m in ("sand", "sand_wet", "grass", "dirt", "grass_lt"):
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Land", me)
    coll.objects.link(ob)
    return ob


def make_house(name, coll, w, d, h, seed=0, tiled=True):
    """Town house: plaster walls, tiled hip roof, door and windows on the -Y face."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.02)
    wall = rng.choice(("plaster", "plaster", "fort_lt", "wall"))
    mb.box(T(0, 0, 0.15) @ S(w + 0.3, d + 0.3, 0.3), "stone")
    mb.box(T(0, 0, h / 2) @ S(w, d, h), wall)
    door(mb, (rng.uniform(-w / 4, w / 4), -d / 2, 0.2), (1, 0, 0), (0, -1, 0), w=0.9, h=1.8)
    for sx in (-1, 1):
        window(mb, (sx * (w / 2 - 0.8), -d / 2, h * 0.6), (1, 0, 0), (0, -1, 0), w=0.5, h=0.6)
    if tiled:
        tile_roof(mb, 0, 0, w, d, h, min(w, d) * 0.45)
    return mb.obj(name, coll)


def build_town(coll, lib_c, rng):
    """Houses, huts, palms and trees round the fort, outside the open glacis."""
    houses = [make_house(f"LibHouse{i}", lib_c, *dims, seed=i)
              for i, dims in enumerate(((6, 4.5, 3.2), (5, 4, 2.8), (8, 5, 3.5), (4.5, 4.5, 2.6)))]
    huts = [kit.make_hut_hip("LibHutHip", lib_c, seed=3), kit.make_hut_gable("LibHutGable", lib_c, seed=4)]
    palms = [kit.make_palm(f"LibPalm{i}", lib_c, seed=40 + i, height=8.0 + i) for i in range(4)]
    trees = [kit.make_tree(f"LibTree{i}", lib_c, seed=60 + i, height=6.5) for i in range(2)]
    placed = []

    def free(x, y, r):
        if in_fort(x, y, 11.0) or x < -19.0 or (abs(y - GATE_Y) < 4.0 and x > 0):
            return False
        return all(math.hypot(x - a, y - b) > r + rb for a, b, rb in placed)
    # streets of houses facing the fort (rotated so their doors look toward it)
    for k in range(260):
        x, y = rng.uniform(-18, 130), rng.uniform(-130, 130)
        if math.hypot(x, y) > 135:
            continue
        r = 4.5
        if not free(x, y, r):
            continue
        near = math.hypot(x, y) < 70
        src = rng.choice(houses) if (near or rng.random() > 0.5) else rng.choice(huts)
        face = math.atan2(-y, -x) - math.pi / 2 + math.pi
        face = round(face / (math.pi / 2)) * (math.pi / 2) + rng.uniform(-0.08, 0.08)
        kit.instance(src, f"Town{k}", coll, (x, y, height(x, y) - 0.05), rot_z=face + math.pi)
        placed.append((x, y, r))
    for k in range(320):
        x, y = rng.uniform(-24, 150), rng.uniform(-150, 150)
        if not free(x, y, 1.5):
            continue
        if x < -19:
            continue
        src = rng.choice(palms) if rng.random() > 0.25 else rng.choice(trees)
        kit.instance(src, f"TownPlant{k}", coll, (x, y, height(x, y) - 0.1), rot_z=rng.uniform(0, TAU),
                     scale=rng.uniform(0.85, 1.2))
        placed.append((x, y, 1.5))
    # palms along the beach north and south of the fort
    for k in range(40):
        y = rng.uniform(-150, 150)
        if abs(y) < OUT_Y + BASTION_R + 3:
            continue
        x = rng.uniform(BEACH_X - 1.5, BEACH_X + 5)
        kit.instance(rng.choice(palms), f"BeachPalm{k}", coll, (x, y, height(x, y) - 0.1),
                     rot_z=rng.uniform(0, TAU), scale=rng.uniform(0.85, 1.15))
    return palms


def make_sails(name, ship, coll, length=38.0, beam=10.0):
    """Set (loosely bellied) cream sails under the kit ship's yards, plus pennants.
    Built in the ship's local space and parented to it, so they rock with it."""
    mb = kit.MB()
    for t, mh in ((0.3, 24.0), (0.55, 29.0), (0.78, 22.0)):
        y = (t - 0.5) * length
        z0 = 4.0
        spans = ((0.32, 0.95), (0.58, 0.75), (0.82, 0.55))
        for k, (f, span) in enumerate(spans):
            ztop = z0 + mh * f
            zbot = (z0 + mh * spans[k - 1][0] + 0.8) if k > 0 else z0 + mh * f - mh * 0.24
            half_t = beam * span * 0.9
            half_b = beam * (spans[k - 1][1] if k > 0 else span) * 0.95
            nx, nz = 6, 4
            rows = []
            for j in range(nz + 1):
                v = j / nz
                z = ztop + (zbot - ztop) * v
                half = half_t + (half_b - half_t) * v
                row = []
                for i in range(nx + 1):
                    u = i / nx
                    belly = 1.4 * math.sin(math.pi * u) * math.sin(math.pi * min(1.0, v * 0.9 + 0.1))
                    row.append(mb.bm.verts.new(((u - 0.5) * 2 * half, y + 0.3 + belly, z)))
                rows.append(row)
            for j in range(nz):
                for i in range(nx):
                    mb.face([rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]], "sail")
        # pennant at the masthead
        top = z0 + mh + 2.4
        mb.face([mb.bm.verts.new((0, y, top)), mb.bm.verts.new((0, y, top - 0.8)),
                 mb.bm.verts.new((0.2, y - 5.0, top - 0.5))], "flag_r")
    ob = mb.obj(name, coll, parent=ship)
    sol = ob.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.12
    # stern ensign: Dutch tricolour on a staff at the stern
    fl = make_flag(name + "Ensign", coll, w=4.0, h=2.6)
    fl.parent = ship
    fl.location = (0, -length / 2 - 0.5, 9.0)
    fl.rotation_euler[2] = -math.pi / 2
    staff = kit.MB()
    staff.seg((0, -length / 2 - 0.3, 6.0), (0, -length / 2 - 0.5, 11.8), 0.12, 0.1, "post", sides=6)
    staff.obj(name + "Staff", coll, parent=ship)
    return ob


def make_flag(name, coll, w=2.4, h=1.6):
    """Plain red-white-blue tricolour (no emblem or text), waving with a Wave modifier.
    Origin at the hoist top; the fly runs along +X, stripes top to bottom."""
    mb = kit.MB()
    nx, nz = 12, 6
    vs = [[mb.bm.verts.new((w * i / nx, 0, -h * j / nz)) for i in range(nx + 1)] for j in range(nz + 1)]
    for j in range(nz):
        m = ("flag_r", "white", "flag_b")[j * 3 // nz]
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


def make_gull(name, coll):
    mb = kit.MB()
    v = [mb.bm.verts.new(p) for p in ((0, 0.25, 0), (0.7, -0.05, 0.12), (0, -0.2, 0), (-0.7, -0.05, 0.12),
                                       (0, 0.05, 0.05))]
    mb.face([v[0], v[1], v[4]], "gull")
    mb.face([v[4], v[1], v[2]], "gull")
    mb.face([v[0], v[4], v[3]], "gull")
    mb.face([v[4], v[2], v[3]], "gull")
    return mb.obj(name, coll)


def build_harbour(coll, lib_c, frames, rng):
    """Beach, jetty, the moored East Indiaman with set sails, more ships at anchor,
    boats, the sack pile at the jetty end, gulls."""
    jetty = kit.make_jetty("Jetty", coll, length=JETTY_LEN, width=JETTY_W, deck=DECK_TOP - 0.04 - SEA_Z, seed=4)
    jetty.location = (JETTY_X0, JETTY_Y, SEA_Z)
    jetty.rotation_euler[2] = math.radians(90)                # runs west into the sea
    end_x = JETTY_X0 - JETTY_LEN
    # the ship, bow north, moored with its side against the jetty end
    sc_ = 0.6
    ship = kit.make_ship("Ship", coll, length=38.0, beam=10.0, seed=1)
    sx = end_x - 10.0 / 2 * sc_ - 0.7
    ship.location = (sx, JETTY_Y + 3.0, SEA_Z - 0.35)
    ship.scale = (sc_, sc_, sc_)
    make_sails("ShipSails", ship, coll)
    for f in range(1, frames + 41, 36):
        ship.rotation_euler = (math.radians(0.6 * math.sin(f / 21.0)), math.radians(1.1 * math.sin(f / 15.0 + 1)),
                               math.radians(1.5))
        ship.location.z = SEA_Z - 0.35 + 0.08 * math.sin(f / 19.0)
        ship.keyframe_insert("rotation_euler", frame=f)
        ship.keyframe_insert("location", frame=f)
    deck = SEA_Z - 0.35 + 4.0 * sc_
    # gangplank from the jetty end up to the ship's rail
    gp = kit.MB(bevel=0.01)
    p0, p1 = Vector((end_x + 0.6, JETTY_Y + 0.2, DECK_TOP + 0.03)), Vector((sx + 2.6, JETTY_Y + 0.4, deck + 0.3))
    d = p1 - p0
    gp.box(T((p0 + p1) / 2) @ Rz(math.atan2(d.y, d.x)) @ Ry(-math.atan2(d.z, d.xy.length)) @ S(d.length, 0.7, 0.06), "plank")
    for k in range(6):
        q = p0.lerp(p1, (k + 0.5) / 6)
        gp.box(T(q + Vector((0, 0, 0.04))) @ S(0.05, 0.7, 0.04), "post")
    gp.obj("Gangplank", coll)
    # other ships at anchor, furled sails
    others = []
    for i, (x, y, rot, s) in enumerate(((-95, 40, 175, 0.75), (-120, -35, 190, 0.8), (-160, 95, 168, 0.7))):
        o = kit.make_ship(f"AnchoredShip{i}", coll, length=38.0, beam=10.0, seed=10 + i)
        o.location = (x, y, SEA_Z - 0.3)
        o.scale = (s, s, s)
        f = 1 + rng.randint(0, 30)
        k = 0
        while f <= frames + 60:
            sg = 1 if k % 2 == 0 else -1
            o.rotation_euler = (math.radians(0.8 * sg), math.radians(-1.2 * sg), math.radians(rot))
            o.keyframe_insert("rotation_euler", frame=f)
            f += rng.randint(48, 66)
            k += 1
        others.append(o)
    # boats drawn up on the beach and one tied to the jetty
    boat = kit.make_boat("LibBoat", lib_c)
    for i, (x, y, rz, z) in enumerate(((-23.5, -6.0, 1.3, None), (-24.5, -9.5, 1.5, None), (-25.0, 16.5, 1.7, None),
                                       (-29.0, JETTY_Y - 2.6, math.pi / 2, SEA_Z - 0.3))):
        zz = height(x, y) - 0.05 if z is None else z
        kit.instance(boat, f"Boat{i}", coll, (x, y, zz), rot_z=rz)
    # sack pile at the jetty end (where the porters set their loads down), crates, barrels
    lying = kit.MB()
    lying.ico(T(0, 0, 0.2) @ S(0.5, 0.32, 0.21), "jute", r=1.0, sub=1, jitter=0.06, rng=rng)
    lying.cone(T(0.5, 0, 0.2) @ Ry(math.pi / 2), "jute", segments=6, r1=0.1, r2=0.13, depth=0.14)
    lying.cone(T(0.44, 0, 0.2) @ Ry(math.pi / 2), "rope", segments=6, r1=0.105, r2=0.105, depth=0.04)
    sack = lying.obj("LibSackLying", lib_c)
    k = 0
    for cx, cy, layers in ((end_x + 1.8, JETTY_Y - 0.55, (3, 2, 1)),):
        for layer, n in enumerate(layers):
            for j in range(n):
                kit.instance(sack, f"JettySack{k}", coll,
                             (cx + (j - (n - 1) / 2) * 0.62, cy, DECK_TOP + layer * 0.34), rot_z=math.pi / 2 + rng.uniform(-0.2, 0.2))
                k += 1
    # gulls wheeling over the gate and the ship
    for i in range(5):
        g = make_gull(f"Gull{i}", coll)
        cx, cy, r, z = rng.uniform(-40, -20), rng.uniform(-4, 14), rng.uniform(5, 10), rng.uniform(9, 15)
        w = rng.choice((-1, 1)) * rng.uniform(0.35, 0.5)
        a0 = rng.uniform(0, TAU)
        for f in range(1, frames + 1, 4):
            a = a0 + w * f / kit.FPS
            g.location = (cx + r * math.cos(a), cy + r * math.sin(a), z + 0.6 * math.sin(f / 13.0 + i))
            g.rotation_euler = (0, -0.35 * math.copysign(1, w), a + math.copysign(math.pi / 2, w) - math.pi / 2)
            g.keyframe_insert("location", frame=f)
            g.keyframe_insert("rotation_euler", frame=f)
    return dict(ship=ship, sack=sack, end_x=end_x)


def build_props(coll, lib_c, palms, rng, sack):
    """Crates, barrels, sack stacks, the weighing station, cannons, flag, palms, plants."""
    crate = kit.make_crate("LibCrate", lib_c, size=0.8)
    crate_big = kit.make_crate("LibCrateBig", lib_c, size=1.05)
    barrel = kit.make_barrel("LibBarrel", lib_c)
    bush = kit.make_bush("LibBush", lib_c, seed=5, size=0.6)
    cannon = kit.make_cannon("LibCannon", lib_c)

    def put(src, nm, x, y, z=0.0, rz=0.0, s=1.0):
        return kit.instance(src, nm, coll, (x, y, z), rot_z=rz, scale=s)
    # crates and barrels along the walls (as in K16: by the south wall, in the corners, by the north wall)
    spots = [(-9.6, -8.5, crate), (-8.7, -8.4, crate_big), (-9.1, -8.45, None),     # by the barracks
             (-5.6, -8.7, crate),
             (-10.2, -1.0, crate_big), (-10.1, -0.1, crate), (-10.15, -0.55, None),  # left of the sea gate
             (-10.2, 8.2, crate), (-10.3, 9.0, crate_big),                       # right of the sea gate
             (2.8, 12.1, crate_big), (3.3, 11.3, crate),                         # north wall, by the house
             (10.0, 2.4, barrel), (10.4, 1.7, barrel), (10.5, 3.0, barrel),       # by the land gate
             (-10.3, -4.2, barrel), (-10.4, -5.0, barrel),
             (6.2, -7.9, crate), (5.5, -7.5, crate_big), (10.2, -1.2, crate), (9.6, -6.4, barrel)]
    for i, (x, y, src) in enumerate(spots):
        if src is None:            # a crate on top of the two before it
            put(crate, f"CrateTop{i}", x, y, 0.95, rng.uniform(-0.2, 0.2))
            continue
        put(src, f"Prop{i}", x, y, 0.0, rng.uniform(-0.25, 0.25))
    # foreground crate stack (K16 lower right) shifted clear of camera frame 369
    for i, (x, y, z) in enumerate(((5.2, 0.2, 0), (5.9, -0.2, 0), (5.5, 0.0, 0.95), (6.1, 0.6, 0),
                                   (-1.0, -6.9, 0), (-1.9, -6.5, 0))):
        put(crate if i % 2 else crate_big, f"FgCrate{i}", x, y, z, rng.uniform(-0.3, 0.3))
    # pepper under the shed: stacks of lying sacks, upright sacks and baskets of pepper
    up = kit.MB()
    up.ico(T(0, 0, 0.3) @ S(0.36, 0.3, 0.32), "jute", r=1.0, sub=1, jitter=0.06, rng=rng)
    up.cone(T(0, 0, 0.66), "jute", segments=6, r1=0.1, r2=0.15, depth=0.16)
    up.cone(T(0, 0, 0.6), "rope", segments=6, r1=0.105, r2=0.105, depth=0.04)
    sack_up = up.obj("LibSackUp", lib_c)
    bk = kit.MB()
    bk.cone(T(0, 0, 0.18), "basket", segments=10, r1=0.3, r2=0.36, depth=0.36)
    bk.cone(T(0, 0, 0.35), "pepper", segments=10, r1=0.34, r2=0.1, depth=0.06)
    bk.cone(T(0, 0, 0.35), "basket", segments=10, r1=0.37, r2=0.37, depth=0.04)
    basket = bk.obj("LibBasket", lib_c)
    k = 0
    for cx, layers in ((SHED[0] - 2.2, (4, 3, 2, 1)), (SHED[0] + 1.6, (4, 3, 2))):
        for layer, n in enumerate(layers):
            for j in range(n):
                for row in (0, 1):
                    put(sack, f"ShedSack{k}", cx + (j - (n - 1) / 2) * 0.62, IN_Y - 0.9 - row * 0.95,
                        layer * 0.34, math.pi / 2 + rng.uniform(-0.15, 0.15))
                    k += 1
    for i, (x, y) in enumerate(((SHED[0] - 0.2, IN_Y - 2.6), (SHED[0] + 0.4, IN_Y - 2.9), (SHED[0] - 3.9, IN_Y - 2.5),
                                (SHED[0] + 3.4, IN_Y - 2.4))):
        put(sack_up, f"ShedSackUp{i}", x, y, 0, rng.uniform(0, TAU))
    for i, (x, y) in enumerate(((SHED[0] + 3.2, IN_Y - 1.0), (SHED[0] + 3.4, IN_Y - 1.8), (SHED[0] - 0.4, IN_Y - 1.2))):
        put(basket, f"ShedBasket{i}", x, y, 0, rng.uniform(0, TAU))
    # handcart with sacks by the shed
    cart = kit.MB(bevel=0.01)
    cart.box(T(0, 0, 0.62) @ S(1.1, 1.8, 0.08), "plank")
    for sx in (-1, 1):
        cart.box(T(sx * 0.55, 0, 0.78) @ S(0.06, 1.8, 0.25), "plank")
        cart.cone(T(sx * 0.68, -0.2, 0.42) @ Ry(math.pi / 2), "post", segments=10, r1=0.42, r2=0.42, depth=0.08)
        cart.cone(T(sx * 0.73, -0.2, 0.42) @ Ry(math.pi / 2), "iron", segments=6, r1=0.08, r2=0.08, depth=0.06)
        cart.box(T(sx * 0.35, 1.5, 0.55) @ Rx(-0.15) @ S(0.07, 1.4, 0.07), "post")
    cart_ob = cart.obj("Cart", coll)
    cart_ob.location = (SHED[0] + 5.6, IN_Y - 2.4, 0)
    cart_ob.rotation_euler[2] = 0.5
    for i in range(3):
        put(sack, f"CartSack{i}", SHED[0] + 5.6 + (i - 1) * 0.3, IN_Y - 2.4 + (i - 1) * 0.5, 0.66, 0.5 + math.pi / 2)
    # weighing station inside the sea gate: tripod, beam, two pans, the clerk's desk
    wx, wy = -IN_X + 3.4, 0.6
    ws = kit.MB(bevel=0.006)
    apex = Vector((wx, wy, 2.7))
    for k in range(3):
        a = k * TAU / 3 + 0.3
        ws.seg((wx + 1.1 * math.cos(a), wy + 1.1 * math.sin(a), 0), apex + Vector((0, 0, 0.1)), 0.06, 0.05, "post", sides=6)
    ws.seg(apex + Vector((0, 0, 0.05)), apex - Vector((0, 0, 0.35)), 0.015, 0.015, "iron", sides=4)
    beam_z = 2.3
    ws.box(T(wx, wy, beam_z) @ S(1.5, 0.07, 0.07), "wood_door")
    for s in (-1, 1):
        px = wx + s * 0.68
        for k in range(3):
            a = k * TAU / 3
            ws.seg((px, wy, beam_z), (px + 0.28 * math.cos(a), wy + 0.28 * math.sin(a), 0.95), 0.008, 0.008, "iron", sides=4)
        ws.cone(T(px, wy, 0.92), "brass", segments=10, r1=0.25, r2=0.32, depth=0.08)
    ws.ico(T(wx - 0.68, wy, 1.12) @ S(0.3, 0.22, 0.17), "jute", r=1.0, sub=1)
    for k, h_ in enumerate((0.12, 0.09, 0.07)):
        ws.cone(T(wx + 0.68 + (k - 1) * 0.1, wy, 0.96 + h_ / 2), "brass", segments=6, r1=0.06 - k * 0.01,
                r2=0.05 - k * 0.01, depth=h_)
    # clerk's desk with a blank ledger
    dx, dy = wx + 1.6, wy - 1.3
    ws.box(T(dx, dy, 0.78) @ Rx(0.12) @ S(0.9, 0.6, 0.05), "wood_tbl")
    for sx in (-1, 1):
        for sy in (-1, 1):
            ws.box(T(dx + sx * 0.38, dy + sy * 0.24, 0.38) @ S(0.05, 0.05, 0.76), "wood_chair")
    ws.box(T(dx, dy, 0.82) @ Rx(0.12) @ S(0.5, 0.36, 0.03), "parchment")
    ws.box(T(dx, dy, 0.835) @ Rx(0.12) @ S(0.01, 0.36, 0.035), "wood_door")
    ws.obj("WeighStation", coll)
    # cannons on the bastions and by the barracks, with a pyramid of shot
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * OUT_X, sy * OUT_Y
            for k, (ax, ay) in enumerate(((sx, 0.35 * sy), (0.35 * sx, sy))):
                d = Vector((ax, ay, 0)).normalized()
                p = Vector((cx, cy, 0)) + d * 3.0
                put(cannon, f"BastionGun{sx}{sy}{k}", p.x, p.y, WALL_H, math.atan2(d.y, d.x) - math.pi / 2, s=0.85)
    put(cannon, "YardGun", -2.4, -8.3, 0, math.radians(-160), 0.9)
    shot = kit.MB()
    n = 0
    for layer, size in enumerate((4, 3, 2, 1)):
        for i in range(size):
            for j in range(size):
                shot.ico(T(-0.5 + (i - (size - 1) / 2) * 0.24, -9.5 + (j - (size - 1) / 2) * 0.24, 0.12 + layer * 0.19),
                         "iron", r=0.12, sub=1)
    shot.obj("CannonShot", coll)
    # flag over the NW bastion (sea side) and on the land gate
    for i, (x, y, z, pole) in enumerate(((-OUT_X - 2.2, OUT_Y + 2.2, WALL_H, 7.5), (IN_X + WALL_T / 2, GATE_Y + 2.6, WALL_H, 5.0))):
        p = kit.MB()
        p.seg((x, y, z), (x, y, z + pole), 0.08, 0.06, "post", sides=6)
        p.ico(T(x, y, z + pole + 0.08), "brass", r=0.1, sub=1)
        p.obj(f"FlagPole{i}", coll)
        fl = make_flag(f"Flag{i}", coll, w=2.6 if i == 0 else 1.8, h=1.7 if i == 0 else 1.2)
        fl.location = (x + 0.05, y, z + pole - 0.15)
        fl.rotation_euler[2] = math.radians(200)
    # palms in the courtyard (K16: one behind the canopy by the south-west, one by the gate)
    for i, (x, y, s) in enumerate(((-IN_X + 2.2, -6.0, 1.0), (-IN_X + 1.6, 10.4, 0.95))):
        pm = kit.instance(palms[i % len(palms)], f"YardPalm{i}", coll, (x, y, -0.1), rot_z=rng.uniform(0, TAU), scale=s)
        kit.animate_idle(pm, rng, 1, 700, amount=0.012)
        ring = kit.MB(bevel=0.01)
        ring.cone(T(x, y, 0.12), "fort_dk", segments=8, r1=0.75, r2=0.7, depth=0.24)
        ring.cone(T(x, y, 0.2), "soil", segments=8, r1=0.62, r2=0.62, depth=0.1)
        ring.obj(f"PalmRing{i}", coll)
    # grass tufts along the wall feet
    for k in range(40):
        side = rng.randint(0, 3)
        t = rng.uniform(-1, 1)
        x, y = [(t * IN_X, -IN_Y + 0.4), (IN_X - 0.4, t * IN_Y), (t * IN_X, IN_Y - 0.4), (-IN_X + 0.4, t * IN_Y)][side]
        if abs(y - GATE_Y) < 3 and abs(x) > 13:
            continue
        put(bush, f"Tuft{k}", x, y, -0.02, rng.uniform(0, TAU), rng.uniform(0.35, 0.7))


def build_world(frames):
    """Everything but the camera and the cast; returns the collections."""
    register_palette()
    rng = random.Random(16)
    world_c = kit.new_collection("World")
    fort_c = kit.new_collection("Fort")
    props_c = kit.new_collection("Props")
    harbour_c = kit.new_collection("Harbour")
    town_c = kit.new_collection("Town")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    make_land(world_c)
    sea = make_sea(world_c)
    animate_sea(sea, rig_c, frames)
    w = cw.setup_world()
    for nd in w.node_tree.nodes:
        if nd.bl_idname == "ShaderNodeBackground":
            nd.inputs["Strength"].default_value = 0.75
    # haze only in the distance (a volume round the courtyard goes grainy at preview samples)
    for i, (ctr, size, dens) in enumerate([((-420, 0, 60), (600, 1400, 160), 0.0030),
                                           ((300, 0, 60), (400, 1400, 160), 0.0025),
                                           ((0, 330, 60), (300, 400, 160), 0.0025),
                                           ((0, -330, 60), (300, 400, 160), 0.0025)]):
        add_mist_box(world_c, f"FarMist{i}", ctr, size, dens)
    cw.add_sun(rig_c, direction=(-0.42, 0.55, -0.72), energy=6.0, color=(1.0, 0.88, 0.74), angle=5.0)
    build_courtyard(fort_c, rng)
    build_fort(fort_c, rng)
    build_wall_details(fort_c, rng)
    build_buildings(fort_c, rng)
    harbour = build_harbour(harbour_c, lib_c, frames, rng)
    palms = build_town(town_c, lib_c, rng)
    build_props(props_c, lib_c, palms, rng, harbour["sack"])
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return dict(rig=rig_c, props=props_c, lib=lib_c, harbour=harbour)


def add_mist_box(collection, name, center, size, density, color=(0.95, 0.90, 0.86)):
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


# ================================================================ the cast
def build_meeting(coll, frames, rng, beats):
    """Canopy, carpet, table and props, the two officials, three rajas, retinue and guards,
    animated. beats: dict of real frame numbers for the narration moments."""
    tx, ty = TABLE
    car = make_carpet("Carpet", coll)
    car.location = (tx + 0.2, ty + 1.0, 0)
    posts, roof = make_canopy("Canopy", coll, w=6.4, d=6.4, h=3.35)
    for ob in (posts, roof):
        ob.location = (tx + 0.1, ty - 0.6, 0)      # posts sit clear of all camera angles
    tbl = make_table("Table", coll)
    tbl.location = (tx, ty, 0)
    tp = make_table_props("TableProps", coll, TABLE_H)
    tp.location = (tx, ty, 0)
    chair = make_chair("LibChair", coll)
    stool = make_stool("LibStool", coll)
    for src in (chair, stool):
        kit.hide_source(src)
    cast = {}
    # officials, seated south of the table facing north
    for i, x in enumerate((-0.48, 0.5)):
        y = ty - 0.475 - 0.28
        kit.instance(chair, f"Chair{i}", coll, (tx + x, y, 0), rot_z=0.0)
        root, parts = make_official(f"Official{i}", coll, seed=3 + i)
        root.location = (tx + x, y, 0)
        root.rotation_euler[2] = (0.08, -0.12)[i]
        # forearms resting on the table edge
        pose(parts, {"armR": (0.18, 0, 0.05), "armL": (0.18, 0, -0.05),
                     "foreR": (1.32, 0, -0.25), "foreL": (1.32, 0, 0.25)})
        cast[f"official{i}"] = (root, parts)
    # rajas north of the table facing south: the near one stands and argues, two sit on stools
    rajas = [((1.45, 0.55), False, math.radians(160)), ((0.15, 0.85), True, math.radians(178)),
             ((-1.1, 0.7), True, math.radians(195))]
    for i, ((x, y), seated, rz) in enumerate(rajas):
        if seated:
            st = kit.instance(stool, f"Stool{i}", coll, (tx + x, ty + y + 0.6, 0), rot_z=rz)
        root, parts = make_raja(f"Raja{i}", coll, seed=11 + i, seated=seated, sash_tilt=0.1 * i)
        root.location = (tx + x, ty + y + 0.6, 0)
        root.rotation_euler[2] = rz
        if seated:
            pose(parts, {"armR": (0.35, 0, 0.1), "armL": (0.35, 0, -0.1), "foreR": (0.9, 0, -0.2),
                         "foreL": (0.9, 0, 0.2)})
        else:
            pose(parts, {"armR": (0.08, 0, 0.06), "armL": (0.1, 0, -0.06), "foreR": (0.25, 0, 0),
                         "foreL": (0.35, 0, 0)})
        cast[f"raja{i}"] = (root, parts)
    # the near raja's attendant with the ceremonial umbrella, a little behind him
    root, parts = make_attendant("Attendant", coll, seed=21)
    root.location = (tx - 2.3, ty + 3.4, 0)
    root.rotation_euler[2] = math.radians(185)
    pose(parts, {"armR": (0.3, 0, 0.1), "foreR": (1.3, 0, 0)})
    parts["umbrella"].rotation_euler[0] = -1.6          # keep the staff upright
    cast["attendant"] = (root, parts)
    # rajas' Nair escort waiting by the road, a Dutch guard behind the officials, two at the gate
    for i, (x, y, rz, kind) in enumerate(((tx + 1.2, ty + 5.6, 195, "nair_spear"), (tx + 2.1, ty + 6.0, 205, "nair_spear"),
                                          (tx - 3.4, ty - 2.8, 250, "dutch"), (-IN_X + 1.6, 1.9, 270, "dutch"),
                                          (-IN_X + 1.6, 7.3, 270, "dutch"))):
        fig = kit.make_figure(f"Escort{i}", coll, kind, seed=30 + i, cloth="cloth_w")
        fig.location = (x, y, 0)
        fig.rotation_euler[2] = math.radians(rz)
        kit.animate_idle(fig, rng, 1, frames, amount=0.02)
    # the weighing clerk, seated at his desk (no hat) beside the scales
    cx_, cy_ = -IN_X + 5.0, -0.7
    kit.instance(chair, "ClerkChair", coll, (cx_, cy_ - 0.75, 0), rot_z=0.0)
    root, parts = make_official("Clerk", coll, seed=9, hat=False)
    root.location = (cx_, cy_ - 0.75, 0)            # facing his desk (north)
    pose(parts, {"armR": (0.25, 0, 0.05), "armL": (0.25, 0, -0.05), "foreR": (1.2, 0, -0.2), "foreL": (1.2, 0, 0.2)})
    cast["clerk"] = (root, parts)
    # a sentry pacing the north wall walk
    w_root, w_parts = kit.make_walker("Sentry", coll, "dutch", seed=41)
    kit.animate_walk(w_root, w_parts, [(-8.0, IN_Y + 1.2), (3.0, IN_Y + 1.2)], lambda x, y: WALL_H,
                     start=1, end=frames, stride_frames=16)

    # ---- animation: idle everyone, then the beats of the narration
    for key, (root, parts) in cast.items():
        idle(parts, random.Random(sum(map(ord, key))), frames, body=0.02, head=0.1)
    o0, o1 = cast["official0"][1], cast["official1"][1]
    r0 = cast["raja0"][1]
    # "They sign contracts": the right-hand official taps the contract
    gesture(o1, "L", beats["contracts"], beats["contracts"] + 70, lift=0.15, fore=0.25, out=-0.2, beats=3)
    # the near raja argues with an open hand, twice
    gesture(r0, "R", beats["contracts"] + 20, beats["contracts"] + 95, lift=0.9, fore=0.9, out=0.3, beats=2)
    gesture(r0, "L", beats["refuse"], beats["refuse"] + 80, lift=0.8, fore=1.0, out=0.35, beats=2)
    # "Sell your pepper only to us": the other official points toward the gate
    gesture(o0, "R", beats["sell"], beats["sell"] + 75, lift=0.6, fore=0.2, out=0.6, beats=1)
    # "at our price": the clerk taps his ledger
    gesture(cast["clerk"][1], "R", beats["price"], beats["price"] + 50, lift=0.1, fore=0.2, out=0.0, beats=3)
    # the seated rajas turn their heads to each other on "none of them is strong enough"
    for k, ang in ((1, 0.45), (2, -0.45)):
        hd = cast[f"raja{k}"][1]["head"]
        h0 = hd.rotation_euler.copy()
        for f, z in ((beats["refuse"] + 10, 0.0), (beats["refuse"] + 30, ang), (beats["refuse"] + 75, ang),
                     (beats["refuse"] + 95, 0.0)):
            key_set(hd, "rotation_euler", f, (h0.x + 0.1, h0.y, h0.z + z))
    return cast


def build_porters(coll, frames, rng, n=8, speed=1.15):
    """Porters looping from the pepper shed out through the sea gate to the jetty end
    with sacks on their heads, and back empty-handed on the other side of the jetty."""
    end_x = JETTY_X0 - JETTY_LEN
    loop = [(SHED[0] + 1.7, IN_Y - 3.9),          # 0  in front of the shed, picking up
            (SHED[0] - 1.0, IN_Y - 4.2),          # 1
            (-IN_X + 3.2, GATE_Y + 0.6),          # 2
            (-IN_X + 0.5, GATE_Y + 0.6),          # 3  through the gate
            (BEACH_X, GATE_Y + 0.6),
            (JETTY_X0, JETTY_Y + 0.6),
            (end_x + 3.2, JETTY_Y + 0.6),         # 6  set the sack down on the pile
            (end_x + 3.2, JETTY_Y - 0.7),
            (JETTY_X0, JETTY_Y - 0.7),
            (BEACH_X, GATE_Y - 0.8),
            (-IN_X + 0.5, GATE_Y - 0.8),
            (-IN_X + 4.0, GATE_Y - 1.0),
            (SHED[0] + 2.4, GATE_Y + 1.4),
            (SHED[0] + 3.1, IN_Y - 3.8)]           # 13
    pauses = [(6, 1.4, "drop"), (0, 1.6, "pick")]
    cloth = ("cloth_w", "cloth_w", "cloth_t", "cloth_w", "rice", "cloth_w", "cloth_w", "cloth_t")
    for i in range(n):
        root, parts = make_porter(f"Porter{i}", coll, seed=100 + i, robe_cloth=cloth[i % len(cloth)])
        walk_loop(root, parts, loop, phase=i / n + rng.uniform(-0.02, 0.02), speed=speed * rng.uniform(0.93, 1.07),
                  frames=frames, pauses=pauses)
