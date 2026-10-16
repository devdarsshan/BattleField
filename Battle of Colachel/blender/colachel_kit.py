"""Reusable low-poly kit for the Colachel film (Blender 5.x, EEVEE).

Flat-shaded, matte, faceted assets built from code so every clip shares the
same look. Asset builders return a Blender object; their origin sits on the
ground at (0, 0, 0) unless noted.
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

FPS = 24
CLIP_FRAMES = 240  # 10 seconds per clip


# ---------------------------------------------------------------- materials
PALETTE = {
    # ground
    "sand":       (0.86, 0.72, 0.52),
    "sand_wet":   (0.72, 0.62, 0.50),
    "grass":      (0.42, 0.56, 0.24),
    "hill":       (0.36, 0.48, 0.26),
    "rock":       (0.56, 0.54, 0.51),
    # buildings
    "wall":       (0.52, 0.44, 0.36),
    "beam":       (0.36, 0.29, 0.23),
    "thatch":     (0.80, 0.62, 0.30),
    "thatch_dk":  (0.72, 0.55, 0.27),
    "stone":      (0.58, 0.55, 0.50),
    "dark":       (0.10, 0.08, 0.07),
    # wood props
    "plank":      (0.55, 0.43, 0.32),
    "post":       (0.40, 0.31, 0.24),
    "hull":       (0.48, 0.36, 0.26),
    "hull_in":    (0.40, 0.30, 0.22),
    "crate":      (0.58, 0.46, 0.33),
    "crate_edge": (0.43, 0.33, 0.24),
    # plants
    "trunk":      (0.46, 0.33, 0.22),
    "frond":      (0.27, 0.52, 0.15),
    "frond_dk":   (0.20, 0.42, 0.13),
    "leaf":       (0.26, 0.48, 0.17),
    "leaf_dk":    (0.18, 0.38, 0.14),
    "coconut":    (0.36, 0.30, 0.18),
    # people
    "skin":       (0.36, 0.24, 0.17),
    "hair":       (0.08, 0.06, 0.05),
    "cloth_w":    (0.86, 0.82, 0.72),
    "cloth_t":    (0.62, 0.50, 0.38),
    "cloth_r":    (0.55, 0.22, 0.17),
    "skin_pale":  (0.86, 0.70, 0.60),
    "wig":        (0.88, 0.87, 0.84),
    "coat_blue":  (0.10, 0.17, 0.42),
    "white":      (0.92, 0.90, 0.86),
    "black":      (0.08, 0.08, 0.09),
    "steel":      (0.62, 0.63, 0.66),
    "gold":       (0.86, 0.66, 0.26),
    "brass":      (0.74, 0.58, 0.30),
    "red":        (0.74, 0.12, 0.09),
    "shield":     (0.45, 0.30, 0.18),
    "canvas":     (0.95, 0.91, 0.82),
    "carpet_red": (0.58, 0.13, 0.10),
    "carpet_gold":(0.80, 0.62, 0.26),
    "parchment":  (0.86, 0.78, 0.60),
    "log":        (0.52, 0.35, 0.20),
    "log_end":    (0.70, 0.52, 0.32),
    "hull_dark":  (0.26, 0.18, 0.12),
    "hull_band":  (0.62, 0.48, 0.28),
    "sail":       (0.88, 0.84, 0.74),
    "cloud":      (0.40, 0.42, 0.46),
    "rain":       (0.80, 0.84, 0.90),
    "iron":       (0.16, 0.16, 0.18),
    "smoke":      (0.88, 0.87, 0.84),
    "coat_dark":   (0.24, 0.22, 0.22),
    "paddy_water": (0.32, 0.46, 0.35),
    "paddy_green": (0.38, 0.58, 0.22),
    "paddy_bund":  (0.48, 0.36, 0.24),
    "laterite_rd": (0.66, 0.42, 0.28),
    "earth_wall":  (0.52, 0.32, 0.20),
    "roof_thatch": (0.72, 0.58, 0.34),
    "fire_yellow": (1.00, 0.88, 0.18),
    "fire_orange": (1.00, 0.48, 0.05),
    "fire_red":    (0.90, 0.18, 0.08),
    "smoke_dk":    (0.24, 0.24, 0.26),
    "smoke_md":    (0.42, 0.42, 0.45),
    "rice":       (0.95, 0.94, 0.88),
    "soil":       (0.42, 0.29, 0.18),
    "soil_dk":    (0.30, 0.21, 0.14),
    "ghat_lo":    (0.44, 0.58, 0.24),
    "ghat_hi":    (0.30, 0.46, 0.17),
    "table":      (0.80, 0.761, 0.698),
    "fire_yellow":(1.0, 0.85, 0.20),
    "fire_orange":(1.0, 0.45, 0.05),
    "fire_red":   (0.90, 0.15, 0.05),
    "coat_dark":  (0.18, 0.20, 0.22),
    "paddy_water":(0.35, 0.52, 0.45),
    "laterite":   (0.68, 0.32, 0.22),
    "laterite_dk":(0.50, 0.22, 0.14),
}


def mat_emit(name, rgb, strength=20.0):
    """Glowing material (muzzle flash)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = mat(name, rgb)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Color"].default_value = (*srgb_to_linear(rgb), 1)
    bsdf.inputs["Emission Strength"].default_value = strength
    return m


def srgb_to_linear(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def mat(name, rgb=None, roughness=0.85):
    """Get-or-create a matte flat-colour material."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    rgb = rgb or PALETTE[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*srgb_to_linear(rgb), 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    m.diffuse_color = (*srgb_to_linear(rgb), 1)
    return m


# ------------------------------------------------------------------ helpers
def T(x, y=None, z=None):
    return Matrix.Translation(x if y is None else (x, y, z))
def Rx(a): return Matrix.Rotation(a, 4, "X")
def Ry(a): return Matrix.Rotation(a, 4, "Y")
def Rz(a): return Matrix.Rotation(a, 4, "Z")
def S(x, y, z): return Matrix.Diagonal((x, y, z, 1))


def frame_matrix(origin, x_axis, y_axis, z_axis):
    m = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
    m.translation = origin
    return m


class MB:
    """Small bmesh builder: primitives with per-part material names.
    bevel > 0 rounds every sharp edge on finish, so corners catch the light."""

    def __init__(self, bevel=0.0):
        self.bm = bmesh.new()
        self.mats = []
        self.bevel = bevel

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _assign(self, verts, m):
        i = self.mi(m)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i
        return verts

    def box(self, M, m):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        bmesh.ops.transform(self.bm, matrix=M, verts=r["verts"])
        return self._assign(r["verts"], m)

    def cone(self, M, m, segments=6, r1=1.0, r2=1.0, depth=1.0):
        r = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=segments,
                                  radius1=r1, radius2=r2, depth=depth)
        bmesh.ops.transform(self.bm, matrix=M, verts=r["verts"])
        return self._assign(r["verts"], m)

    def ico(self, M, m, r=1.0, sub=1, jitter=0.0, rng=None):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r)
        if jitter and rng:
            for v in res["verts"]:
                v.co *= 1.0 + rng.uniform(-jitter, jitter)
        bmesh.ops.transform(self.bm, matrix=M, verts=res["verts"])
        return self._assign(res["verts"], m)

    def seg(self, p0, p1, r0, r1, m, sides=6, spin=0.0):
        """Tapered prism from p0 to p1."""
        p0, p1 = Vector(p0), Vector(p1)
        v = p1 - p0
        q = v.to_track_quat("Z", "Y").to_matrix().to_4x4()
        M = T(p0 + v / 2) @ q @ Rz(spin)
        return self.cone(M, m, segments=sides, r1=r0, r2=r1, depth=v.length)

    def face(self, verts, m):
        f = self.bm.faces.new(verts)
        f.material_index = self.mi(m)
        return f

    def obj(self, name, collection, parent=None):
        me = bpy.data.meshes.new(name)
        self.bm.normal_update()
        if self.bevel > 0:
            sharp = [e for e in self.bm.edges if e.is_manifold and e.calc_face_angle(0) > math.radians(35)]
            if sharp:
                bmesh.ops.bevel(self.bm, geom=sharp, offset=self.bevel, offset_type="OFFSET",
                                segments=2, profile=0.5, affect="EDGES", clamp_overlap=True,
                                material=-1)  # bevel faces take the colour of their neighbours
            self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(mat(m))
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        if parent:
            ob.parent = parent
        return ob


def instance(src, name, collection, loc, rot_z=0.0, scale=1.0):
    ob = bpy.data.objects.new(name, src.data)
    ob.location = loc
    ob.rotation_euler[2] = rot_z
    ob.scale = (scale, scale, scale) if not hasattr(scale, "__len__") else scale
    collection.objects.link(ob)
    return ob


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def hide_source(ob):
    """Library objects stay in the file but out of every render."""
    ob.hide_render = True
    ob.hide_viewport = True
    ob.location = (0, 0, -500)


# ================================================================ buildings
def _thatch_teeth(mb, start, end, down, normal, rng, size=(0.3, 0.45, 0.16)):
    """Ragged thatch fringe hanging along an eave from start to end."""
    start, end = Vector(start), Vector(end)
    along = (end - start)
    n = max(2, int(along.length / 0.3))
    ax = along.normalized()
    for i in range(n):
        p = start + along * ((i + 0.5) / n)
        ln = size[1] * rng.uniform(0.6, 1.3)
        M = frame_matrix(p + down * (ln / 2 - 0.05) + normal * rng.uniform(-0.02, 0.05),
                         ax, down, normal) @ Ry(rng.uniform(-0.15, 0.15)) @ S(size[0], ln, size[2])
        mb.box(M, "thatch" if rng.random() > 0.3 else "thatch_dk")


def _wall_details(mb, w, d, base, h, rng, door_x=0.0, windows=True):
    top = base + h
    # corner posts and top beams
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(T(sx * w / 2, sy * d / 2, base + h / 2) @ S(0.2, 0.2, h + 0.05), "beam")
    for sy in (-1, 1):
        mb.box(T(0, sy * d / 2, top - 0.08) @ S(w + 0.1, 0.18, 0.16), "beam")
        mb.box(T(0, sy * d / 2, base + 0.08) @ S(w + 0.1, 0.16, 0.16), "beam")
    for sx in (-1, 1):
        mb.box(T(sx * w / 2, 0, top - 0.08) @ S(0.18, d + 0.1, 0.16), "beam")
    # vertical boards: thin raised strips that read as planks
    x = -w / 2 + 0.45
    while x < w / 2 - 0.3:
        if abs(x - door_x) > 0.6:
            mb.box(T(x, -d / 2 - 0.02, base + h / 2) @ S(0.05, 0.04, h - 0.3), "beam")
        x += 0.5 + rng.uniform(-0.05, 0.05)
    # door with frame
    mb.box(T(door_x, -d / 2 - 0.03, base + 0.85) @ S(0.85, 0.08, 1.7), "dark")
    for sx in (-1, 1):
        mb.box(T(door_x + sx * 0.5, -d / 2 - 0.06, base + 0.9) @ S(0.14, 0.12, 1.8), "beam")
    mb.box(T(door_x, -d / 2 - 0.06, base + 1.82) @ S(1.14, 0.12, 0.14), "beam")
    if windows:
        for sx in (-1, 1):
            wx = sx * (w / 2 + 0.03)
            mb.box(T(wx, 0, base + h * 0.62) @ S(0.08, 0.5, 0.42), "dark")
            mb.box(T(wx, 0, base + h * 0.62) @ S(0.1, 0.66, 0.08) @ T(0, 0, 3.0), "beam")
            mb.box(T(wx, 0, base + h * 0.62 - 0.25) @ S(0.12, 0.7, 0.1), "beam")
        wx2 = (w / 2 - 0.7) * (1 if door_x <= 0 else -1)
        mb.box(T(wx2, -d / 2 - 0.03, base + h * 0.62) @ S(0.5, 0.08, 0.42), "dark")
        mb.box(T(wx2, -d / 2 - 0.06, base + h * 0.62 - 0.26) @ S(0.68, 0.12, 0.1), "beam")
    # front step
    mb.box(T(door_x, -d / 2 - 0.45, base * 0.5) @ S(1.2, 0.6, base), "stone")


def make_hut_gable(name, collection, w=4.2, d=3.4, h=2.1, seed=0):
    """Rectangular hut, plank walls, thick tiered thatch with a ragged fringe.
    Ridge runs along X, door faces -Y."""
    rng = random.Random(seed)
    mb = MB(bevel=0.03)
    base = 0.3
    top = base + h
    mb.box(T(0, 0, base / 2) @ S(w + 0.5, d + 0.5, base), "stone")
    mb.box(T(0, 0, base + h / 2) @ S(w, d, h), "wall")
    _wall_details(mb, w, d, base, h, rng, door_x=rng.choice([-0.6, 0.0, 0.5]))

    rh = d * 0.62                      # ridge height above wall top
    a = math.atan2(rh, d / 2)
    ov, ovx = 0.6, 0.45
    slant = (d / 2) / math.cos(a) + ov
    ridge = Vector((0, 0, top + rh))
    # gable-end attic (wall coloured triangle prism)
    v = [mb.bm.verts.new(p) for p in [(-w / 2, -d / 2, top), (-w / 2, d / 2, top), (-w / 2, 0, top + rh),
                                      (w / 2, -d / 2, top), (w / 2, d / 2, top), (w / 2, 0, top + rh)]]
    for f in ([0, 2, 1], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]):
        mb.face([v[i] for i in f], "wall")
    mb.box(T(-w / 2 - 0.02, 0, top + rh * 0.45) @ S(0.06, 0.12, rh * 0.9), "beam")
    mb.box(T(w / 2 + 0.02, 0, top + rh * 0.45) @ S(0.06, 0.12, rh * 0.9), "beam")
    X = Vector((1, 0, 0))
    length = w + 2 * ovx
    tiers = 3
    for s in (-1, 1):
        e = Vector((0, s * math.cos(a), -math.sin(a)))          # down the slope
        n = Vector((0, s * math.sin(a), math.cos(a)))           # out of the roof
        for k in range(tiers):
            lt = slant / tiers * 1.18
            c = ridge + e * (slant * (k + 0.55) / tiers) + n * (0.16 + 0.06 * k)
            M = frame_matrix(c, X, e if s > 0 else -e, n if s > 0 else n) @ S(length + 0.06 * k, lt, 0.3)
            # keep a right-handed frame on both slopes
            if s < 0:
                M = frame_matrix(c, -X, e, n) @ S(length + 0.06 * k, lt, 0.3)
            mb.box(M, "thatch" if k != 1 else "thatch_dk")
        eave = ridge + e * slant + n * (0.16 + 0.06 * (tiers - 1))
        _thatch_teeth(mb, eave - X * (length / 2), eave + X * (length / 2), e, n, rng)
    mb.box(T(ridge + Vector((0, 0, 0.36))) @ S(length + 0.2, 0.55, 0.34), "thatch_dk")
    return mb.obj(name, collection)


def make_hut_hip(name, collection, w=3.8, d=3.4, h=2.0, seed=0):
    """Hut with a steep hipped (pyramid) thatch roof in two tiers. Door faces -Y."""
    rng = random.Random(seed)
    mb = MB(bevel=0.03)
    base = 0.3
    top = base + h
    mb.box(T(0, 0, base / 2) @ S(w + 0.5, d + 0.5, base), "stone")
    mb.box(T(0, 0, base + h / 2) @ S(w, d, h), "wall")
    _wall_details(mb, w, d, base, h, rng, door_x=0.0)
    ov = 0.65
    hw, hd = w / 2 + ov, d / 2 + ov
    R = math.hypot(hw, hd)
    asp = (1.0, hd / hw)
    rh = 2.6
    r_scale = S(1.0, asp[1], 1.0) @ S(hw * math.sqrt(2) / R, hw * math.sqrt(2) / R, 1)
    mb.cone(T(0, 0, top + rh * 0.22) @ S(1, asp[1], 1) @ Rz(math.pi / 4), "thatch",
            segments=4, r1=hw * math.sqrt(2), r2=hw * math.sqrt(2) * 0.55, depth=rh * 0.48)
    mb.cone(T(0, 0, top + rh * 0.62) @ S(1, asp[1], 1) @ Rz(math.pi / 4), "thatch_dk",
            segments=4, r1=hw * math.sqrt(2) * 0.66, r2=0.08, depth=rh * 0.8)
    z = top - 0.02
    corners = [Vector((-hw, -hd, z)), Vector((hw, -hd, z)), Vector((hw, hd, z)), Vector((-hw, hd, z))]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        out = (a + b) / 2
        out.z = 0
        out.normalize()
        down = (Vector((0, 0, -1)) + out * 0.35).normalized()
        _thatch_teeth(mb, a, b, down, out, rng, size=(0.32, 0.4, 0.14))
    return mb.obj(name, collection)


# ==================================================================== plants
def _frond(mb, top, az, elev, length, width, droop, m, rng, steps=7, fold=0.45):
    """Folded, arching palm leaf: V cross-section, serrated width."""
    pos = Vector(top)
    e = elev
    up = Vector((0, 0, 1))
    rows = []
    seg = length / steps
    for i in range(steps):
        t = i / steps
        d = Vector((math.cos(az) * math.cos(e), math.sin(az) * math.cos(e), math.sin(e)))
        side = d.cross(up)
        side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
        down = side.cross(d).normalized()
        if down.z > 0:
            down = -down
        w = width * max(0.05, math.sin(math.pi * min(1.0, 0.12 + t * 0.95)) ** 0.6)
        if i % 2 == 1:
            w *= rng.uniform(0.62, 0.8)            # serrated outline
        rows.append((mb.bm.verts.new(pos + side * w + down * (w * fold)),
                     mb.bm.verts.new(pos),
                     mb.bm.verts.new(pos - side * w + down * (w * fold))))
        pos = pos + d * seg
        e -= droop / steps
    tip = mb.bm.verts.new(pos)
    for i in range(steps - 1):
        L0, S0, R0 = rows[i]
        L1, S1, R1 = rows[i + 1]
        mb.face([L0, L1, S1, S0], m)
        mb.face([S0, S1, R1, R0], m)
    L0, S0, R0 = rows[-1]
    mb.face([L0, tip, S0], m)
    mb.face([S0, tip, R0], m)


def make_palm(name, collection, seed=0, height=9.0):
    rng = random.Random(seed)
    mb = MB()
    az = rng.uniform(0, math.tau)
    bend = rng.uniform(0.12, 0.32)
    lean = Vector((math.cos(az), math.sin(az), 0))

    def p(t):
        return Vector((0, 0, height * t)) + lean * (height * bend * t * t)

    n = 9
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        r0 = 0.40 * (1 - 0.45 * t0)
        r1 = 0.40 * (1 - 0.45 * t1)
        mb.seg(p(t0), p(t1) + (p(t1) - p(t0)) * 0.02, r0 * 1.12, r1 * 0.92, "trunk", sides=6,
               spin=rng.uniform(0, 1))
    top = p(1.0)
    mb.ico(T(top) @ S(1, 1, 0.8), "trunk", r=0.5, sub=1)
    for k in range(3 + rng.randint(0, 2)):
        a = rng.uniform(0, math.tau)
        mb.ico(T(top + Vector((0.3 * math.cos(a), 0.3 * math.sin(a), -0.35))), "coconut", r=0.17, sub=1)
    nf = rng.randint(10, 13)
    for k in range(nf):
        a = k * math.tau / nf + rng.uniform(-0.18, 0.18)
        _frond(mb, top, a, math.radians(rng.uniform(18, 55)), rng.uniform(4.6, 6.0),
               rng.uniform(0.8, 1.0), math.radians(rng.uniform(70, 115)),
               "frond" if rng.random() > 0.35 else "frond_dk", rng)
    return mb.obj(name, collection)


def make_bush(name, collection, seed=0, size=1.0):
    """Broad-leaf ground plant (like the clumps at the palm bases)."""
    rng = random.Random(seed)
    mb = MB()
    nf = rng.randint(7, 10)
    for k in range(nf):
        a = k * math.tau / nf + rng.uniform(-0.3, 0.3)
        _frond(mb, (0, 0, 0.05), a, math.radians(rng.uniform(35, 70)), size * rng.uniform(0.9, 1.4),
               size * rng.uniform(0.28, 0.38), math.radians(rng.uniform(50, 90)),
               "leaf" if rng.random() > 0.4 else "frond", rng, steps=4, fold=0.35)
    return mb.obj(name, collection)


def make_tree(name, collection, seed=0, height=6.0):
    """Rounded broad-leaf tree made of faceted blobs."""
    rng = random.Random(seed)
    mb = MB()
    mb.seg((0, 0, 0), (0, 0, height * 0.6), 0.28, 0.18, "trunk", sides=5)
    for k in range(rng.randint(4, 7)):
        r = height * rng.uniform(0.2, 0.32)
        off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)) * height * 0.18
        z = height * rng.uniform(0.6, 0.9)
        mb.ico(T(off + Vector((0, 0, z))) @ S(1, 1, 0.8) @ Rz(rng.uniform(0, 3)),
               "leaf" if rng.random() > 0.4 else "leaf_dk", r=r, sub=1, jitter=0.12, rng=rng)
    return mb.obj(name, collection)


def make_rock(name, collection, seed=0, size=1.0):
    rng = random.Random(seed)
    mb = MB()
    mb.ico(S(size, size * rng.uniform(0.7, 1.0), size * rng.uniform(0.45, 0.7)), "rock",
           r=1.0, sub=1, jitter=0.2, rng=rng)
    return mb.obj(name, collection)


# ===================================================================== props
def make_boat(name, collection, length=4.4, width=1.5, seed=0):
    """Open wooden rowboat lying along Y (bow at +Y) with thwarts."""
    rng = random.Random(seed)
    mb = MB()
    n = 10
    wall = 0.08
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        y = (t - 0.5) * length
        w = width / 2 * max(0.03, math.sin(math.pi * (0.16 + 0.84 * t)) ** 0.55)
        if t < 0.05:
            w = width / 2 * 0.62
        zg = 0.62 + 0.55 * (2 * t - 1) ** 4 * (1.0 if t > 0.5 else 0.45)
        zk = 0.0 + 0.4 * max(0.0, (t - 0.75) / 0.25) ** 2
        prof = [(-w, zg), (-w * 0.92, zk + 0.32), (-w * 0.55, zk + 0.04), (0, zk),
                (w * 0.55, zk + 0.04), (w * 0.92, zk + 0.32), (w, zg)]
        outer.append([mb.bm.verts.new((x, y, z)) for x, z in prof])
        wi = max(0.0, w - wall)
        s = wi / w if w > 0 else 0
        inner.append([mb.bm.verts.new((x * s, y, (z - zk) * 0.9 + zk + wall if j not in (0, 6) else z))
                      for j, (x, z) in enumerate(prof)])
    for i in range(n):
        for j in range(6):
            mb.face([outer[i][j], outer[i][j + 1], outer[i + 1][j + 1], outer[i + 1][j]], "hull")
            mb.face([inner[i][j + 1], inner[i][j], inner[i + 1][j], inner[i + 1][j + 1]], "hull_in")
        for j in (0, 6):
            a, b = (outer, inner) if j == 0 else (inner, outer)
            mb.face([a[i][j], a[i + 1][j], b[i + 1][j], b[i][j]], "plank")
    for ring, flip in ((0, False), (n, True)):
        for j in range(6):
            q = [outer[ring][j], inner[ring][j], inner[ring][j + 1], outer[ring][j + 1]]
            mb.face(q[::-1] if flip else q, "hull")
    for t in (0.25, 0.5, 0.72):
        y = (t - 0.5) * length
        w = width / 2 * math.sin(math.pi * (0.16 + 0.84 * t)) ** 0.55
        mb.box(T(0, y, 0.48) @ S(2 * w - 0.12, 0.26, 0.07), "plank")
    return mb.obj(name, collection)


def make_jetty(name, collection, length=10.0, width=1.8, deck=0.75, seed=0):
    """Wooden jetty along +Y from (0,0). Posts go down into the seabed."""
    rng = random.Random(seed)
    mb = MB()
    y = 0.0
    while y < length:
        pw = rng.uniform(0.22, 0.3)
        mb.box(T(rng.uniform(-0.03, 0.03), y + pw / 2, deck) @ Rx(rng.uniform(-0.03, 0.03))
               @ Ry(rng.uniform(-0.03, 0.03)) @ S(width + rng.uniform(-0.1, 0.1), pw, 0.08), "plank")
        y += pw + 0.05
    for sx in (-1, 1):
        mb.box(T(sx * (width / 2 - 0.2), length / 2, deck - 0.12) @ S(0.14, length, 0.16), "post")
    k = 0
    y = 0.4
    while y < length:
        for sx in (-1, 1):
            tall = 0.5 if k % 2 == 0 else 0.15
            mb.seg((sx * width / 2, y, -2.5), (sx * width / 2, y, deck + tall), 0.12, 0.11, "post", sides=6)
        y += 1.8
        k += 1
    return mb.obj(name, collection)


def make_crate(name, collection, size=0.8):
    mb = MB(bevel=0.012)
    s = size
    mb.box(S(s * 0.94, s * 0.94, s * 0.94) @ T(0, 0, 0.5), "crate")
    e = 0.08 * s / 0.8
    h = s / 2
    for a in (-1, 1):
        for b in (-1, 1):
            mb.box(T(a * h, b * h, h) @ S(e, e, s), "crate_edge")
            mb.box(T(a * h, 0, h + b * h) @ S(e, s, e), "crate_edge")
            mb.box(T(0, a * h, h + b * h) @ S(s, e, e), "crate_edge")
    for a in (-1, 1):  # diagonal braces on two faces
        mb.box(T(0, a * (h + 0.005), h) @ Ry(math.pi / 4) @ S(s * 1.3, e * 0.7, e), "crate_edge")
        mb.box(T(a * (h + 0.005), 0, h) @ Rx(math.pi / 4) @ S(e * 0.7, s * 1.3, e), "crate_edge")
    return mb.obj(name, collection)


def make_barrel(name, collection, h=0.95, r=0.33):
    mb = MB(bevel=0.015)
    mb.cone(T(0, 0, h * 0.25), "crate", segments=8, r1=r * 0.88, r2=r, depth=h * 0.5)
    mb.cone(T(0, 0, h * 0.75), "crate", segments=8, r1=r, r2=r * 0.88, depth=h * 0.5)
    for z in (0.15, 0.5, 0.85):
        rr = r * (1.02 if z == 0.5 else 0.94)
        mb.cone(T(0, 0, h * z), "crate_edge", segments=8, r1=rr + 0.015, r2=rr + 0.015, depth=0.06)
    return mb.obj(name, collection)


def make_fence(name, collection, length=4.0, height=1.1, seed=0):
    """Post-and-stake fence along +X from (0,0)."""
    rng = random.Random(seed)
    mb = MB()
    x = 0.0
    while x <= length:
        hh = height * rng.uniform(0.85, 1.1)
        mb.box(T(x, 0, hh / 2) @ Rz(rng.uniform(-0.1, 0.1)) @ S(0.11, 0.11, hh), "post")
        x += 0.32
    for z in (0.35, 0.8):
        mb.box(T(length / 2, 0.08, z * height) @ S(length + 0.2, 0.06, 0.1), "post")
    return mb.obj(name, collection)


def make_stump(name, collection, r=0.3, h=0.4):
    mb = MB()
    mb.cone(T(0, 0, h / 2), "post", segments=7, r1=r * 1.15, r2=r, depth=h)
    return mb.obj(name, collection)


# ==================================================================== people
# Figures face +Y. Limbs pivot at hip/shoulder. A figure is drawn either into one
# static mesh (crowds) or into separate part objects (walkers).
FIG_BEVEL = 0.014
PIVOTS = {"body": (0, 0, 0), "legL": (0.1, 0, 0.88), "legR": (-0.1, 0, 0.88),
          "armL": (0.27, 0, 1.4), "armR": (-0.27, 0, 1.4)}


def _draw_figure(get, kind, rng, cloth="cloth_w", armed=True):
    """get(part) -> (MB, matrix taking part-local coords to target space)."""
    def put(part, prim, M, m, **kw):
        mb, P = get(part)
        getattr(mb, prim)(P @ M, m, **kw)

    skin = "skin_pale" if kind in ("dutch", "imhoff") else "skin"
    # ---- legs
    for leg in ("legL", "legR"):
        if kind == "dutch":
            put(leg, "box", T(0, 0, -0.24) @ S(0.17, 0.18, 0.5), "white")
            put(leg, "box", T(0, 0, -0.64) @ S(0.16, 0.17, 0.42), "black")
            put(leg, "box", T(0, 0.05, -0.86) @ S(0.16, 0.26, 0.07), "black")
        elif kind == "imhoff":
            put(leg, "box", T(0, 0, -0.24) @ S(0.17, 0.18, 0.5), "white")
            put(leg, "box", T(0, 0, -0.64) @ S(0.16, 0.17, 0.42), "white")
            put(leg, "box", T(0, 0.05, -0.86) @ S(0.16, 0.26, 0.07), "black")
            put(leg, "box", T(0, 0.11, -0.85) @ S(0.08, 0.04, 0.04), "gold")
        else:
            put(leg, "box", T(0, 0, -0.42) @ S(0.15, 0.16, 0.84), skin)
            put(leg, "box", T(0, 0.05, -0.86) @ S(0.15, 0.24, 0.07), skin)
    # ---- arms
    for arm in ("armL", "armR"):
        if kind == "dutch":
            put(arm, "box", T(0, 0, -0.27) @ S(0.13, 0.14, 0.56), "coat_blue")
            put(arm, "box", T(0, 0, -0.52) @ S(0.14, 0.15, 0.08), "white")
            put(arm, "box", T(0, 0, -0.6) @ S(0.1, 0.11, 0.1), skin)
        elif kind == "imhoff":
            put(arm, "box", T(0, 0, -0.27) @ S(0.14, 0.15, 0.56), "coat_dark")
            put(arm, "box", T(0, 0, -0.52) @ S(0.15, 0.16, 0.08), "white")
            put(arm, "box", T(0, 0, -0.6) @ S(0.1, 0.11, 0.1), skin)
        else:
            put(arm, "box", T(0, 0, -0.29) @ S(0.11, 0.12, 0.58), skin)
            put(arm, "box", T(0, 0.01, -0.63) @ S(0.12, 0.13, 0.13), skin)          # hand
        if kind == "king":
            put(arm, "cone", T(0, 0, -0.12), "gold", segments=6, r1=0.075, r2=0.075, depth=0.05)
    if kind in ("nair", "nair_spear"):
        put("armL", "cone", T(0.1, 0.0, -0.36) @ Ry(math.pi / 2), "shield", segments=12, r1=0.36, r2=0.36, depth=0.05)
        put("armL", "cone", T(0.125, 0.0, -0.36) @ Ry(math.pi / 2), "brass", segments=12, r1=0.37, r2=0.37, depth=0.02)
        put("armL", "cone", T(0.15, 0.0, -0.36) @ Ry(math.pi / 2), "brass", segments=8, r1=0.09, r2=0.04, depth=0.06)
        if kind == "nair_spear":
            put("armR", "box", T(0, 0.06, -0.15) @ S(0.04, 0.04, 2.3), "post")
            put("armR", "cone", T(0, 0.06, 1.08), "steel", segments=4, r1=0.05, r2=0.0, depth=0.25)
        else:
            put("armR", "box", T(0, 0.12, -0.62) @ Rx(0.5) @ S(0.03, 0.06, 0.6), "steel")

    # ---- body
    def body(prim, M, m, **kw):
        put("body", prim, M, m, **kw)

    torso = {"dutch": "coat_blue", "imhoff": "coat_dark", "commander": "white", "villager_robe": cloth}.get(kind, skin)
    body("cone", T(0, 0, 1.17) @ Rz(math.pi / 4) @ S(1.0, 0.62, 1.0), torso, segments=4, r1=0.24, r2=0.32, depth=0.48)
    body("cone", T(0, 0, 1.47), skin, segments=6, r1=0.065, r2=0.065, depth=0.1)
    body("ico", T(0, 0, 1.63) @ S(0.9, 0.95, 1.05), skin, r=0.145, sub=1)
    for sx in (-1, 1):                                                                   # eyes
        body("box", T(sx * 0.048, 0.128, 1.655) @ S(0.032, 0.02, 0.034), "black")
    body("box", T(0, 0.14, 1.618) @ S(0.034, 0.04, 0.055), skin)                       # nose
    if kind in ("king", "nair", "nair_spear", "commander", "villager"):
        body("box", T(0, 0.13, 1.585) @ S(0.11, 0.025, 0.026), "hair")                 # moustache
    turban = None
    if kind == "dutch":
        body("cone", T(0, 0, 0.78), "coat_blue", segments=4, r1=0.27, r2=0.22, depth=0.42)
        body("box", T(0, 0.15, 1.12) @ S(0.16, 0.04, 0.55), "white")                      # waistcoat
        for a in (-1, 1):                                                                   # cross-belts
            body("box", T(0, 0.17, 1.17) @ Ry(a * 0.62) @ S(0.06, 0.03, 0.68), "white")
            body("box", T(0, -0.17, 1.17) @ Ry(a * 0.62) @ S(0.06, 0.03, 0.68), "white")
        body("box", T(0, 0, 0.98) @ S(0.44, 0.3, 0.07), "white")
        body("ico", T(0, -0.07, 1.68) @ S(1.0, 0.85, 0.85), "wig", r=0.14, sub=1)
        for z in (1.0, 1.08, 1.16, 1.24):                                                # brass buttons
            body("box", T(0, 0.175, z) @ S(0.03, 0.02, 0.03), "brass")
        body("cone", T(0, 0, 1.78) @ Rz(rng.uniform(-0.1, 0.1) + math.pi / 2), "black",
             segments=3, r1=0.31, r2=0.27, depth=0.1)                                       # tricorn
        body("ico", T(0, 0, 1.82) @ S(1, 1, 0.55), "black", r=0.145, sub=1)
        if armed:
            body("box", T(-0.36, 0.08, 0.95) @ S(0.06, 0.08, 0.7), "post")                # musket stock
            body("box", T(-0.36, 0.08, 1.55) @ S(0.035, 0.035, 0.6), "steel")             # musket barrel
    elif kind == "imhoff":
        body("cone", T(0, 0, 0.78), "coat_dark", segments=4, r1=0.28, r2=0.22, depth=0.44)
        body("box", T(0, 0.15, 1.14) @ S(0.17, 0.04, 0.52), "white")                      # waistcoat
        body("box", T(0, 0.17, 1.34) @ S(0.13, 0.05, 0.20), "canvas")                     # lace jabot
        for z in (0.96, 1.04, 1.12, 1.20, 1.28):                                          # gold buttons
            body("box", T(-0.06, 0.175, z) @ S(0.025, 0.02, 0.025), "gold")
            body("box", T(0.06, 0.175, z) @ S(0.025, 0.02, 0.025), "gold")
        body("ico", T(0, -0.07, 1.68) @ S(1.15, 1.05, 1.0), "wig", r=0.16, sub=1)        # wig
        body("box", T(-0.16, 0.02, 1.46) @ S(0.08, 0.10, 0.36), "wig")
        body("box", T(0.16, 0.02, 1.46) @ S(0.08, 0.10, 0.36), "wig")
        body("box", T(0, -0.14, 1.48) @ S(0.30, 0.09, 0.36), "wig")
    elif kind in ("nair", "nair_spear"):
        body("cone", T(0, 0, 0.74), "cloth_w", segments=8, r1=0.22, r2=0.19, depth=0.48)
        body("cone", T(0, 0, 0.53), "red", segments=8, r1=0.225, r2=0.225, depth=0.05)
        body("cone", T(0, 0, 0.96), "red", segments=8, r1=0.21, r2=0.21, depth=0.08)
        turban = ("red", None)
    elif kind == "commander":
        body("cone", T(0, 0, 0.55), "white", segments=8, r1=0.28, r2=0.2, depth=0.9)
        body("box", T(0, 0, 1.17) @ Ry(0.6) @ S(0.08, 0.36, 0.7), "red")
        body("cone", T(0, 0, 0.98), "red", segments=8, r1=0.215, r2=0.215, depth=0.09)
        turban = ("red", None)
    elif kind == "king":
        body("cone", T(0, 0, 0.56), "white", segments=8, r1=0.29, r2=0.21, depth=0.88)
        body("cone", T(0, 0, 0.14), "gold", segments=8, r1=0.295, r2=0.295, depth=0.06)
        body("cone", T(0, 0, 0.99), "red", segments=8, r1=0.22, r2=0.22, depth=0.1)
        body("box", T(0, 0, 1.18) @ Ry(0.6) @ S(0.09, 0.37, 0.72), "red")
        body("box", T(0, 0.005, 1.18) @ Ry(0.6) @ S(0.1, 0.36, 0.06), "gold")
        for z, r in ((1.42, 0.17), (1.33, 0.2)):                                             # necklaces
            body("cone", T(0, 0.02, z) @ Rx(-0.25), "gold", segments=10, r1=r, r2=r, depth=0.025)
        turban = ("red", "gold")
        for i in range(4):                                                                  # curved sword
            body("box", T(0.27 + 0.03 * i, 0.12 - 0.2 * i, 0.82 - 0.06 * i) @ Rx(-0.5 + i * 0.22)
                 @ S(0.03, 0.22, 0.05), "steel")
        body("box", T(0.26, 0.24, 0.9) @ S(0.05, 0.12, 0.05), "gold")
    else:  # villagers
        robe = kind == "villager_robe"
        bottom = 0.12 if robe else 0.5
        body("cone", T(0, 0, (0.98 + bottom) / 2), cloth, segments=8, r1=0.27 if robe else 0.22,
             r2=0.19, depth=0.98 - bottom)
        body("ico", T(0, -0.025, 1.68) @ S(0.98, 1.0, 0.75), "hair", r=0.145, sub=1)
        if robe:
            body("box", T(0, 0, 1.38) @ S(0.62, 0.3, 0.1), cloth)
    if turban:                                                                           # wrapped turban
        cloth_m, trim = turban
        body("cone", T(0, 0, 1.71), cloth_m, segments=8, r1=0.158, r2=0.168, depth=0.08)
        body("cone", T(0, -0.01, 1.775) @ Rx(-0.12), cloth_m, segments=8, r1=0.165, r2=0.14, depth=0.07)
        body("ico", T(0, -0.01, 1.81) @ S(1.0, 1.0, 0.55), cloth_m, r=0.13, sub=1)
        body("ico", T(0.11, -0.06, 1.77), cloth_m, r=0.045, sub=1)
        if trim:
            body("cone", T(0, 0, 1.745) @ Rx(-0.06), trim, segments=8, r1=0.17, r2=0.17, depth=0.03)
            body("ico", T(0, 0.155, 1.79), trim, r=0.04, sub=1)
            body("box", T(0, 0.16, 1.85) @ S(0.02, 0.02, 0.1), "white")                # aigrette


SIT = {"body": T(0, 0, -0.78),
       "legL": T(0.1, 0, 0.1) @ Rx(math.pi / 2), "legR": T(-0.1, 0, 0.1) @ Rx(math.pi / 2),
       "armL": T(0.27, 0, 0.62) @ Rx(0.7), "armR": T(-0.27, 0, 0.62) @ Rx(0.75)}

POINT = {"body": Matrix.Identity(4),
         "legL": T(0.1, 0, 0.88), "legR": T(-0.1, 0, 0.88),
         "armL": T(0.27, 0, 1.4) @ Rx(0.15) @ Ry(0.1),
         "armR": T(-0.27, 0, 1.4) @ Rx(-math.pi / 2 + 0.15) @ Rz(-0.35) @ Ry(-0.1)}

WRITE = {"body": T(0, 0, -0.78),
         "legL": T(0.1, 0, 0.1) @ Rx(math.pi / 2), "legR": T(-0.1, 0, 0.1) @ Rx(math.pi / 2),
         "armL": T(0.27, 0, 0.62) @ Rx(0.85) @ Ry(-0.2),
         "armR": T(-0.27, 0, 0.62) @ Rx(1.05) @ Ry(0.25) @ Rz(-0.2)}

SIT_ARMS_FOLDED = {"body": T(0, 0, -0.78),
                   "legL": T(0.1, 0, 0.1) @ Rx(math.pi / 2), "legR": T(-0.1, 0, 0.1) @ Rx(math.pi / 2),
                   "armL": T(0.27, 0, 0.62) @ Rx(1.1) @ Ry(0.4) @ Rz(0.6),
                   "armR": T(-0.27, 0, 0.62) @ Rx(1.1) @ Ry(-0.4) @ Rz(-0.6)}

POSES = {"stand": None, "sit": SIT, "point": POINT, "write": WRITE, "sit_arms_folded": SIT_ARMS_FOLDED}


def make_figure(name, collection, kind, seed=0, cloth="cloth_w", pose="stand", armed=True):
    """Static single-mesh figure (for crowds and instancing).
    pose: 'stand', 'sit', 'point', 'write', 'sit_arms_folded'.
    """
    rng = random.Random(seed)
    mb = MB(bevel=FIG_BEVEL)
    pdict = POSES.get(pose)
    if pdict:
        _draw_figure(lambda p: (mb, pdict[p]), kind, rng, cloth, armed=armed)
    else:
        _draw_figure(lambda p: (mb, T(*PIVOTS[p])), kind, rng, cloth, armed=armed)
    return mb.obj(name, collection)


def make_walker(name, collection, kind, seed=0, cloth="cloth_w"):
    """Figure with separate limb objects under a root empty. Returns (root, parts)."""
    rng = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    root.empty_display_size = 0.3
    collection.objects.link(root)
    mbs = {p: MB(bevel=FIG_BEVEL) for p in PIVOTS}
    _draw_figure(lambda p: (mbs[p], Matrix.Identity(4)), kind, rng, cloth)
    parts = {}
    for p, mb in mbs.items():
        ob = mb.obj(f"{name}_{p}", collection, parent=root)
        ob.location = PIVOTS[p]
        parts[p] = ob
    return root, parts


def make_villager(name, collection, seed=0, robe=False, cloth="cloth_w"):
    return make_walker(name, collection, "villager_robe" if robe else "villager", seed, cloth)


def animate_idle(ob, rng, start, end, amount=0.03):
    """Small random sway so standing crowds never look frozen."""
    f = start + rng.randint(0, 30)
    base = ob.rotation_euler.copy()
    while f <= end:
        ob.rotation_euler = (base.x + rng.uniform(-amount, amount), base.y + rng.uniform(-amount, amount),
                             base.z + rng.uniform(-amount * 2, amount * 2))
        ob.keyframe_insert("rotation_euler", frame=f)
        f += rng.randint(40, 70)
    ob.rotation_euler = base


# ================================================================ army camp
def make_stockade(name, collection, center, axis_deg, half_u, half_v, ground, gate=3.0, seed=0):
    """Sharpened-log wall around a rectangle (u along axis_deg, v across it), built in
    world space so every log stands on the terrain. Gate gap centred on the +v wall."""
    rng = random.Random(seed)
    mb = MB()
    c = Vector((center[0], center[1], 0))
    a = math.radians(axis_deg)
    u = Vector((math.cos(a), math.sin(a), 0))
    v = Vector((-math.sin(a), math.cos(a), 0))
    corners = [c - u * half_u - v * half_v, c + u * half_u - v * half_v,
               c + u * half_u + v * half_v, c - u * half_u + v * half_v]
    inward = [v, -u, -v, u]
    for side in range(4):
        p0, p1 = corners[side], corners[(side + 1) % 4]
        L = (p1 - p0).length
        d = (p1 - p0).normalized()
        s = 0.0
        while s < L:
            r = rng.uniform(0.2, 0.27)
            s += r
            if side == 2 and abs(s - L / 2) < gate / 2:
                s += r
                continue
            p = p0 + d * s
            z = ground(p.x, p.y) - 0.3
            h = rng.uniform(3.4, 4.1)
            tilt = Vector((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), 1)).normalized()
            top = Vector((p.x, p.y, z)) + tilt * h
            mb.seg((p.x, p.y, z), top, r, r * 0.95, "log", sides=6, spin=rng.uniform(0, 1))
            mb.seg(top, top + tilt * rng.uniform(0.55, 0.8), r * 0.95, 0.02, "log_end", sides=6)
            s += r + 0.01
        # inner rail and diagonal braces
        n = inward[side]
        mid = (p0 + p1) / 2 + n * 0.45
        mb.box(T(mid.x, mid.y, ground(mid.x, mid.y) + 2.5) @ Rz(math.atan2(d.y, d.x)) @ S(L, 0.18, 0.2), "log")
        k = 2.0
        while k < L - 1:
            q = p0 + d * k
            g = ground(q.x, q.y)
            mb.seg(q + n * 2.2 + Vector((0, 0, g - 0.1)), q + n * 0.4 + Vector((0, 0, g + 2.6)),
                   0.12, 0.11, "log", sides=6)
            k += 4.5
    # tall gate posts
    gm = (corners[2] + corners[3]) / 2
    for sgn in (-1, 1):
        p = gm + u * sgn * (gate / 2 + 0.3)
        z = ground(p.x, p.y) - 0.3
        mb.seg((p.x, p.y, z), (p.x, p.y, z + 4.8), 0.3, 0.28, "log", sides=6)
    return mb.obj(name, collection)


def make_cone_tent(name, collection, r=2.2, h=3.4, seed=0):
    """White bell tent with a dark door slit facing +Y."""
    mb = MB()
    mb.cone(T(0, 0, h / 2), "canvas", segments=9, r1=r, r2=0.12, depth=h)
    mb.seg((0, 0, h - 0.1), (0, 0, h + 0.5), 0.05, 0.04, "post", sides=5)
    a = math.atan2(h, r)
    door_h = h * 0.45
    p = Vector((0, r * 0.97, 0))
    tip = Vector((0, r * 0.97 - door_h / math.tan(a), door_h))
    v = [mb.bm.verts.new(x) for x in (p + Vector((-0.45, 0.03, 0)), p + Vector((0.45, 0.03, 0)), tip + Vector((0, 0.05, 0)))]
    mb.face(v, "dark")
    return mb.obj(name, collection)


def make_ridge_tent(name, collection, w=2.6, length=3.6, h=2.2):
    """A-frame canvas tent, ridge along Y, open end facing +Y."""
    mb = MB()
    v = [mb.bm.verts.new(p) for p in [(-w / 2, -length / 2, 0), (w / 2, -length / 2, 0), (0, -length / 2, h),
                                      (-w / 2, length / 2, 0), (w / 2, length / 2, 0), (0, length / 2, h)]]
    mb.face([v[0], v[3], v[5], v[2]], "canvas")
    mb.face([v[1], v[2], v[5], v[4]], "canvas")
    mb.face([v[0], v[2], v[1]], "canvas")
    d = [mb.bm.verts.new(p) for p in [(-0.5, length / 2 + 0.01, 0), (0.5, length / 2 + 0.01, 0),
                                      (0, length / 2 + 0.01, h * 0.75)]]
    mb.face(d, "dark")
    f = [mb.bm.verts.new(p) for p in [(-w / 2, length / 2, 0), (-0.5, length / 2 + 0.005, 0),
                                      (0, length / 2 + 0.005, h * 0.75), (0, length / 2, h)]]
    mb.face(f, "canvas")
    f = [mb.bm.verts.new(p) for p in [(0.5, length / 2 + 0.005, 0), (w / 2, length / 2, 0), (0, length / 2, h),
                                      (0, length / 2 + 0.005, h * 0.75)]]
    mb.face(f, "canvas")
    for y in (-length / 2, length / 2):
        mb.seg((0, y, 0), (0, y, h + 0.3), 0.05, 0.04, "post", sides=5)
    return mb.obj(name, collection)


def make_canopy(name, collection, w=4.6, d=3.8, h=2.7):
    """Royal canopy: four posts, cloth roof with a red valance, carpet and low table."""
    mb = MB(bevel=0.015)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.seg((sx * w / 2, sy * d / 2, 0), (sx * w / 2, sy * d / 2, h + 0.15), 0.07, 0.06, "post", sides=6)
    mb.box(T(0, 0, h + 0.05) @ S(w + 0.3, d + 0.3, 0.08), "canvas")
    for sy in (-1, 1):
        mb.box(T(0, sy * (d / 2 + 0.15), h - 0.12) @ S(w + 0.3, 0.04, 0.3), "red")
    for sx in (-1, 1):
        mb.box(T(sx * (w / 2 + 0.15), 0, h - 0.12) @ S(0.04, d + 0.3, 0.3), "red")
    mb.box(T(0, 0, 0.02) @ S(w * 0.86, d * 0.82, 0.04), "carpet_gold")
    mb.box(T(0, 0, 0.03) @ S(w * 0.78, d * 0.72, 0.04), "carpet_red")
    mb.box(T(0, -0.3, 0.45) @ S(1.7, 0.8, 0.06), "plank")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(T(sx * 0.75, -0.3 + sy * 0.32, 0.22) @ S(0.07, 0.07, 0.44), "post")
    mb.box(T(-0.3, -0.3, 0.5) @ S(0.7, 0.5, 0.02), "parchment")
    mb.ico(T(0.45, -0.25, 0.52), "brass", r=0.07, sub=1)
    mb.ico(T(0.6, -0.45, 0.52), "brass", r=0.06, sub=1)
    return mb.obj(name, collection)


def make_throne(name, collection, w=1.1, d=0.9, h=1.8):
    """Ornate royal throne for King Marthanda Varma (matches refs K27, K30)."""
    mb = MB(bevel=0.015)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cone(T(sx * (w / 2 - 0.08), sy * (d / 2 - 0.08), 0.22), "plank", segments=8, r1=0.07, r2=0.05, depth=0.44)
            mb.cone(T(sx * (w / 2 - 0.08), sy * (d / 2 - 0.08), 0.15), "gold", segments=8, r1=0.08, r2=0.08, depth=0.04)
    mb.box(T(0, 0, 0.46) @ S(w, d, 0.08), "plank")
    mb.box(T(0, 0, 0.52) @ S(w * 0.94, d * 0.94, 0.08), "carpet_red")
    mb.box(T(0, 0, 0.52) @ S(w * 0.96, d * 0.96, 0.03), "gold")
    for sx in (-1, 1):
        mb.box(T(sx * (w / 2 - 0.06), 0.05, 0.72) @ S(0.10, d * 0.75, 0.06), "plank")
        mb.box(T(sx * (w / 2 - 0.06), 0.05, 0.75) @ S(0.08, d * 0.70, 0.02), "gold")
        mb.cone(T(sx * (w / 2 - 0.06), d * 0.35, 0.78), "gold", segments=6, r1=0.04, r2=0.01, depth=0.08)
    mb.box(T(0, -d / 2 + 0.06, 1.15) @ S(w * 0.9, 0.08, 1.1), "plank")
    mb.box(T(0, -d / 2 + 0.08, 1.15) @ S(w * 0.78, 0.04, 0.95), "carpet_red")
    mb.cone(T(0, -d / 2 + 0.06, 1.75), "gold", segments=8, r1=w * 0.45, r2=0.0, depth=0.25)
    for sx in (-1, 1):
        mb.ico(T(sx * (w * 0.42), -d / 2 + 0.06, 1.72), "gold", r=0.06, sub=1)
    mb.ico(T(0, -d / 2 + 0.06, 1.90), "gold", r=0.07, sub=1)
    return mb.obj(name, collection)


def make_sack(name, collection):
    mb = MB()
    mb.ico(T(0, 0, 0.28) @ S(0.42, 0.32, 0.3), "canvas", r=1.0, sub=1)
    mb.cone(T(0, 0, 0.6), "canvas", segments=6, r1=0.1, r2=0.14, depth=0.14)
    return mb.obj(name, collection)


# ==================================================================== cannon
def make_cannon(name, collection):
    """Field gun on a wooden carriage, barrel pointing +Y. Muzzle at CANNON_MUZZLE."""
    mb = MB(bevel=0.02)
    mb.box(T(0, -0.1, 0.5) @ Rx(-0.12) @ S(0.62, 1.7, 0.36), "plank")
    mb.box(T(0, -1.0, 0.2) @ S(0.5, 0.5, 0.3), "plank")
    for sx in (-1, 1):
        mb.cone(T(sx * 0.42, 0.25, 0.48) @ Ry(math.pi / 2), "post", segments=12, r1=0.48, r2=0.48, depth=0.12)
        mb.cone(T(sx * 0.49, 0.25, 0.48) @ Ry(math.pi / 2), "iron", segments=8, r1=0.1, r2=0.1, depth=0.06)
    mb.seg((0, -0.7, 0.82), (0, 1.55, 0.95), 0.22, 0.15, "iron", sides=10)
    mb.seg((0, 1.45, 0.946), (0, 1.62, 0.955), 0.18, 0.18, "iron", sides=10)
    mb.ico(T(0, -0.78, 0.82), "iron", r=0.13, sub=1)
    return mb.obj(name, collection)


CANNON_MUZZLE = (0.0, 1.65, 0.955)


def make_paddy_field(name, collection, w=35.0, d=20.0, ridge_w=1.2, ridge_h=0.45):
    """Rectangular flooded rice paddy field with earthen dikes (matches K32)."""
    mb = MB(bevel=0.02)
    mb.box(T(0, 0, 0.1) @ S(w - ridge_w * 2, d - ridge_w * 2, 0.15), "grass")
    for i in range(-2, 3):
        mb.box(T(0, i * (d / 6), 0.12) @ S(w - ridge_w * 2.2, d / 14, 0.02), "paddy_water")
    for sy in (-1, 1):
        mb.box(T(0, sy * (d / 2 - ridge_w / 2), ridge_h / 2) @ S(w, ridge_w, ridge_h), "soil")
    for sx in (-1, 1):
        mb.box(T(sx * (w / 2 - ridge_w / 2), 0, ridge_h / 2) @ S(ridge_w, d - ridge_w * 2, ridge_h), "soil")
    return mb.obj(name, collection)


def make_explosion(name, collection, seed=0, scale=1.0):
    """Low-poly faceted explosion burst with fire shards & smoke clouds (matches K33)."""
    rng = random.Random(seed)
    mb = MB(bevel=0.0)
    for _ in range(8):
        pos = Vector((rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), rng.uniform(0.8, 3.2))) * scale
        s = rng.uniform(0.7, 1.6) * scale
        c = rng.choice(["fire_yellow", "fire_orange", "fire_red"])
        mb.ico(T(pos) @ S(s, s, s * rng.uniform(0.9, 1.4)), c, r=1.0, sub=1, jitter=0.2, rng=rng)
    for k in range(12):
        z_frac = k / 12.0
        pos = Vector((rng.uniform(-1.0, 1.0) * (1.0 + z_frac * 1.5),
                      rng.uniform(-1.0, 1.0) * (1.0 + z_frac * 1.5),
                      2.5 + z_frac * 6.5)) * scale
        s = (1.2 + z_frac * 2.2) * scale
        smk = "dark" if rng.random() < 0.55 else "smoke"
        mb.ico(T(pos) @ S(s, s, s * 0.9), smk, r=1.0, sub=1, jitter=0.22, rng=rng)
    for _ in range(7):
        pos = Vector((rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), rng.uniform(1.5, 4.5))) * scale
        rot = (rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), rng.uniform(0, 3.14))
        mb.box(T(pos) @ Rx(rot[0]) @ Ry(rot[1]) @ Rz(rot[2]) @ S(0.12 * scale, 1.4 * scale, 0.08 * scale), "plank")
    return mb.obj(name, collection)


# ================================================================== weather
def make_cloud(name, collection, seed=0, size=1.0):
    """Dark low-poly storm cloud: a flattened cluster of faceted blobs."""
    rng = random.Random(seed)
    mb = MB()
    for k in range(rng.randint(5, 8)):
        r = size * rng.uniform(8, 17)
        off = Vector((rng.uniform(-20, 20), rng.uniform(-9, 9), rng.uniform(-2, 4))) * size
        mb.ico(T(off) @ S(1.0, 0.8, 0.55) @ Rz(rng.uniform(0, 3)), "cloud", r=r, sub=1, jitter=0.12, rng=rng)
    return mb.obj(name, collection)


RAIN_PERIOD = 60.0


def make_rain(name, collection, seed=0, half=45.0, count=1700):
    """Rain streaks in a 2*half square, stacked twice (0-60 m and 60-120 m) so the
    field can scroll down by RAIN_PERIOD and jump back without a visible seam."""
    rng = random.Random(seed)
    mb = MB()
    pts = []
    while len(pts) < count:   # leave a clear zone round the camera so no streak crosses the lens
        x, y = rng.uniform(-half, half), rng.uniform(-half, half)
        if math.hypot(x, y) > 6.0:
            pts.append((x, y, rng.uniform(0, RAIN_PERIOD)))
    for stack in (0.0, RAIN_PERIOD):
        for x, y, z in pts:
            mb.box(T(x, y, z + stack) @ Rx(0.14) @ S(0.025, 0.025, 1.0), "rain")
    return mb.obj(name, collection)


# ===================================================================== ships
def make_ship(name, collection, length=38.0, beam=10.0, seed=0):
    """Low-poly East Indiaman at anchor: dark hull, gunport band, stern castle,
    three masts with furled sails. Bow at +Y, waterline at z=0."""
    rng = random.Random(seed)
    mb = MB()
    n = 14
    rings = []
    deck_z = []
    for i in range(n + 1):
        t = i / n
        y = (t - 0.5) * length
        w = beam / 2 * max(0.05, math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.5)
        if t < 0.06:
            w = beam / 2 * 0.78
        sheer = 4.0 + 2.2 * max(0.0, (0.25 - t) / 0.25) + 1.2 * max(0.0, (t - 0.8) / 0.2)
        keel = -3.0 + 2.0 * max(0.0, (t - 0.85) / 0.15) ** 2
        prof = [(-w * 0.86, sheer), (-w, 1.8), (-w * 0.9, 0.0), (-w * 0.55, -2.2), (0, keel),
                (w * 0.55, -2.2), (w * 0.9, 0.0), (w, 1.8), (w * 0.86, sheer)]
        rings.append([mb.bm.verts.new((x, y, z)) for x, z in prof])
        deck_z.append(sheer)
    for i in range(n):
        for j in range(8):
            m = "hull_band" if j in (0, 7) else "hull_dark"
            mb.face([rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]], m)
        mb.face([rings[i][8], rings[i + 1][8], rings[i + 1][0], rings[i][0]], "plank")
    mb.face(rings[0][::-1], "hull_dark")
    mb.face(rings[n], "hull_dark")
    # gunports and cannon muzzles along both sides
    for i in range(2, n - 2):
        t = (i + 0.5) / n
        y = (t - 0.5) * length
        w = beam / 2 * math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.5
        for sx in (-1, 1):
            mb.box(T(sx * w * 0.99, y, 2.7) @ S(0.12, 0.7, 0.6), "dark")
            mb.seg((sx * w * 0.95, y, 2.7), (sx * (w + 0.55), y, 2.7), 0.13, 0.11, "black", sides=6)
    # stern castle and forecastle
    sy = -length / 2 + length * 0.11
    mb.box(T(0, sy, deck_z[1] + 1.4) @ S(beam * 0.74, length * 0.2, 2.8), "hull_dark")
    mb.box(T(0, sy, deck_z[1] + 2.85) @ S(beam * 0.78, length * 0.21, 0.15), "hull_band")
    mb.box(T(0, -length / 2 + 0.2, deck_z[0] + 1.8) @ S(beam * 0.7, 0.3, 2.2), "hull_band")
    for k in range(4):
        mb.box(T(-beam * 0.24 + k * beam * 0.16, -length / 2 + 0.05, deck_z[0] + 1.9) @ S(0.6, 0.15, 0.8), "dark")
    mb.box(T(0, length * 0.36, deck_z[-3] + 0.7) @ S(beam * 0.45, length * 0.1, 1.4), "hull_dark")
    # bowsprit
    mb.seg((0, length * 0.42, deck_z[-1] - 0.5), (0, length * 0.68, deck_z[-1] + 4.5), 0.3, 0.15, "post", sides=6)
    # masts, yards, furled sails
    for t, mh in ((0.3, 24.0), (0.55, 29.0), (0.78, 22.0)):
        y = (t - 0.5) * length
        z0 = 4.0
        mb.seg((0, y, z0 - 1), (0, y, z0 + mh), 0.42, 0.18, "post", sides=8)
        mb.box(T(0, y, z0 + mh * 0.62) @ S(1.6, 1.6, 0.4), "post")
        for f, span in ((0.32, 0.95), (0.58, 0.75), (0.82, 0.55)):
            z = z0 + mh * f
            half = beam * span
            mb.seg((-half, y, z), (half, y, z), 0.16, 0.16, "post", sides=6)
            mb.seg((-half * 0.92, y + 0.15, z + 0.3), (half * 0.92, y + 0.15, z + 0.3), 0.32, 0.32, "sail", sides=6)
        mb.seg((0, y, z0 + mh), (0, y, z0 + mh + 2.5), 0.06, 0.05, "post", sides=5)
    # stays (rigging lines) from mast tops to bow and stern
    tops = [Vector((0, (t - 0.5) * length, 4.0 + mh)) for t, mh in ((0.3, 24.0), (0.55, 29.0), (0.78, 22.0))]
    mb.seg(tops[2], (0, length * 0.66, deck_z[-1] + 4.3), 0.04, 0.04, "black", sides=4)
    mb.seg(tops[1], tops[2] - Vector((0, 0, 4)), 0.04, 0.04, "black", sides=4)
    mb.seg(tops[0], (0, -length / 2, deck_z[0] + 3), 0.04, 0.04, "black", sides=4)
    for tp in tops:
        for sx in (-1, 1):
            mb.seg(tp - Vector((0, 0, 3)), (sx * beam * 0.5, tp.y - 1.5, 4.2), 0.03, 0.03, "black", sides=4)
    return mb.obj(name, collection)


def animate_walk(root, parts, waypoints, ground, start=1, end=CLIP_FRAMES, stride_frames=14,
                 swing=0.45, speed=None):
    """Walk the villager along waypoints (x, y) at constant speed, legs and arms swinging.
    `ground(x, y)` returns terrain height."""
    pts = [Vector((x, y, 0)) for x, y in waypoints]
    lengths = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(lengths) or 1.0
    if speed:  # walk at a real pace, then stop
        end = min(end, start + max(stride_frames, int(total / speed * FPS)))
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        f = start
        step = 6
        while f <= end + step:
            s = (min(f, end) - start) / max(1, end - start) * total
            i = 0
            while i < len(lengths) - 1 and s > lengths[i]:
                s -= lengths[i]
                i += 1
            a, b = pts[i], pts[i + 1]
            u = min(1.0, s / lengths[i]) if lengths[i] else 0
            p = a.lerp(b, u)
            root.location = (p.x, p.y, ground(p.x, p.y))
            d = b - a
            root.rotation_euler = (0, 0, math.atan2(d.y, d.x) - math.pi / 2)
            root.keyframe_insert("location", frame=min(f, end))
            root.keyframe_insert("rotation_euler", frame=min(f, end))
            if f >= end:
                break
            f += step
    finally:
        prefs.keyframe_new_interpolation_type = old
    if total < 0.1:
        return
    f = start
    k = 0
    while f <= end:
        sgn = 1 if k % 2 == 0 else -1
        parts["legL"].rotation_euler = (sgn * swing, 0, 0)
        parts["legR"].rotation_euler = (-sgn * swing, 0, 0)
        parts["armL"].rotation_euler = (-sgn * swing * 0.8, 0, 0)
        parts["armR"].rotation_euler = (sgn * swing * 0.8, 0, 0)
        for key in ("legL", "legR", "armL", "armR"):
            parts[key].keyframe_insert("rotation_euler", frame=f)
        parts["body"].location = (0, 0, 0.0)
        parts["body"].keyframe_insert("location", frame=f)
        parts["body"].location = (0, 0, 0.035)
        parts["body"].keyframe_insert("location", frame=f + stride_frames // 2)
        f += stride_frames
        k += 1
    for key in ("legL", "legR", "armL", "armR"):
        parts[key].rotation_euler = (0, 0, 0)
        parts[key].keyframe_insert("rotation_euler", frame=f)


# ===================================================================== battle assets (S25-S26)
def make_paddy_field(name, collection, w=15.0, l=14.0, rim_h=0.35):
    """Flooded paddy field basin with green rice shoots and raised earthen bunds."""
    mb = MB(bevel=0.02)
    mb.box(T(0, 0, 0.05) @ S(w, l, 0.08), "paddy_water")
    mb.box(T(0, 0, 0.08) @ S(w * 0.94, l * 0.94, 0.02), "paddy_green")
    bw = 0.55
    mb.box(T(0, l / 2, rim_h / 2) @ S(w + bw * 2, bw, rim_h), "paddy_bund")
    mb.box(T(0, -l / 2, rim_h / 2) @ S(w + bw * 2, bw, rim_h), "paddy_bund")
    mb.box(T(w / 2, 0, rim_h / 2) @ S(bw, l, rim_h), "paddy_bund")
    mb.box(T(-w / 2, 0, rim_h / 2) @ S(bw, l, rim_h), "paddy_bund")
    return mb.obj(name, collection)


def make_earthworks(name, collection, length=32.0, w=5.5, h=2.5):
    """Reinforced red-mud defensive rampart with firing step and embrasures."""
    mb = MB(bevel=0.08)
    # Slanted main rampart
    mb.box(T(0, 0, h * 0.45) @ S(w, length, h * 0.9), "earth_wall")
    # Top firing parapet
    mb.box(T(-w * 0.25, 0, h + 0.3) @ S(w * 0.45, length, 0.65), "earth_wall")
    # Laterite foundation revetment
    mb.box(T(0, 0, 0.15) @ S(w * 1.15, length + 0.5, 0.3), "laterite_rd")
    # Timber palisade posts embedded in the earthwork
    for i in range(int(length / 2.2)):
        py = -length / 2 + 1.1 + i * 2.2
        mb.cone(T(-w * 0.45, py, h * 0.6), "log", segments=6, r1=0.18, r2=0.14, depth=h * 1.2)
    return mb.obj(name, collection)


def make_powder_store(name, collection, w=6.0, d=4.5, h=3.2):
    """Timber plank gunpowder magazine shed with pitched thatched/tiled roof."""
    mb = MB(bevel=0.03)
    # Timber plank walls
    mb.box(T(0, 0, h * 0.45) @ S(w, d, h * 0.9), "plank")
    # Pitched roof
    mb.cone(T(0, 0, h + 0.75) @ S(1.0, d / w, 1.0) @ Rz(math.pi / 4), "roof_thatch",
            segments=4, r1=w * 0.75, r2=0.2, depth=1.6)
    # Heavy timber cross-braced door
    mb.box(T(0, -d / 2 - 0.05, h * 0.35) @ S(1.6, 0.12, h * 0.7), "dark")
    mb.box(T(0, -d / 2 - 0.08, h * 0.35) @ S(1.8, 0.08, 0.08), "iron")
    return mb.obj(name, collection)


def make_explosion(name, collection, radius=8.0):
    """Dramatic explosion mesh: faceted fire core, smoke boulders, and debris (K33)."""
    mb = MB(bevel=0.0)
    rng = random.Random(42)
    # 1. Fire core (faceted yellow/orange icos)
    mb.ico(T(0, 0, radius * 0.35), "fire_yellow", r=radius * 0.55, sub=1, jitter=0.25, rng=rng)
    mb.ico(T(0, 0, radius * 0.55), "fire_orange", r=radius * 0.75, sub=1, jitter=0.22, rng=rng)
    mb.ico(T(0, 0, radius * 0.75), "fire_red", r=radius * 0.90, sub=1, jitter=0.20, rng=rng)
    # 2. Billowing smoke boulders rising upwards
    smoke_spots = [
        (-radius * 0.4, -radius * 0.3, radius * 1.1, radius * 0.65, "smoke_dk"),
        (radius * 0.4, -radius * 0.2, radius * 1.2, radius * 0.70, "smoke_dk"),
        (0.0, radius * 0.3, radius * 1.4, radius * 0.80, "smoke_dk"),
        (-radius * 0.25, radius * 0.2, radius * 1.8, radius * 0.90, "smoke_md"),
        (radius * 0.25, 0.0, radius * 2.2, radius * 1.05, "smoke_md"),
        (0.0, -radius * 0.1, radius * 2.7, radius * 1.15, "smoke"),
    ]
    for sx, sy, sz, sr, sm in smoke_spots:
        mb.ico(T(sx, sy, sz), sm, r=sr, sub=1, jitter=0.18, rng=rng)
    # 3. Flying debris: timber planks and barrel fragments blasting outward
    for i in range(16):
        a = rng.uniform(0, math.tau)
        elev = rng.uniform(0.3, 1.1)
        dist = radius * rng.uniform(0.8, 1.8)
        px = math.cos(a) * math.cos(elev) * dist
        py = math.sin(a) * math.cos(elev) * dist
        pz = math.sin(elev) * dist + radius * 0.4
        mb.box(T(px, py, pz) @ Rx(rng.uniform(0, 3)) @ Ry(rng.uniform(0, 3)) @ S(0.35, 1.8, 0.2), "plank")
    return mb.obj(name, collection)


# ===================================================================== scene
def reset_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
                bpy.data.textures, bpy.data.actions, bpy.data.worlds):
        for item in list(blk):
            blk.remove(item)


def keyframe_linear(fn):
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        fn()
    finally:
        prefs.keyframe_new_interpolation_type = old


# ===================================================================== posable kit figures (S20-S23)
# The same figures as make_figure (same _draw_figure parts, colours and proportions), split into
# objects so they can act: root empty -> body -> head, armL, armR (+ legs, or bent legs on a seat).
# Use for named characters who must move (Imhoff writing / pointing, the king gesturing, folding
# his arms). Every part rotates about its pivot; the figure faces +Y.
SEAT_H = 0.5            # seat top height for seated rigs (desk chairs 0.5; raise a throne's figure to its seat)
RIG_SEAT_DROP = -0.30   # seated: the upper body is lowered so the hips rest on the seat
RIG_HEAD = (0.0, 0.0, 1.47)


class _SplitMB:
    """Routes _draw_figure's body primitives to the body or the head part (above the neck),
    and drops the long lower garment of a seated figure (the seated legs replace it)."""

    def __init__(self, body, head, seated):
        self.body, self.head, self.seated = body, head, seated
        self.off = T(-Vector(RIG_HEAD))

    def _pick(self, p):
        if p.z > 1.445 and abs(p.x) < 0.25:
            return self.head, self.off
        if self.seated and p.z < 0.8:
            return None, None
        return self.body, Matrix.Identity(4)

    def box(self, M, m, **kw):
        mb, P = self._pick(M.translation)
        if mb:
            mb.box(P @ M, m, **kw)

    def cone(self, M, m, **kw):
        mb, P = self._pick(M.translation)
        if mb:
            mb.cone(P @ M, m, **kw)

    def ico(self, M, m, **kw):
        mb, P = self._pick(M.translation)
        if mb:
            mb.ico(P @ M, m, **kw)

    def seg(self, p0, p1, r0, r1, m, **kw):
        mb, P = self._pick(Vector(p0))
        if mb:
            mb.seg(P @ Vector(p0), P @ Vector(p1), r0, r1, m, **kw)


def _rig_seated_legs(mb, kind):
    """Legs bent onto a seat of height SEAT_H, in root space (knees forward along +Y)."""
    hz = SEAT_H + 0.09
    mats = {"imhoff": ("white", "white", "black"), "dutch": ("white", "black", "black")}
    thigh, shin, shoe = mats.get(kind, ("skin", "skin", "skin"))
    for sx in (-1, 1):
        x = sx * 0.1
        mb.box(T(x, 0.2, hz) @ S(0.17, 0.52, 0.17), thigh)
        mb.box(T(x, 0.44, hz / 2) @ S(0.15, 0.16, hz), shin)
        mb.box(T(x, 0.5, 0.035) @ S(0.15, 0.27, 0.07), shoe)
        if kind == "imhoff":
            mb.box(T(x, 0.635, 0.075) @ S(0.07, 0.03, 0.04), "gold")
    if kind in ("imhoff", "dutch"):                       # coat skirts over the seat
        c = "coat_dark" if kind == "imhoff" else "coat_blue"
        mb.cone(T(0, -0.02, hz + 0.08), c, segments=8, r1=0.29, r2=0.25, depth=0.2)
        for sx in (-1, 1):
            mb.box(T(sx * 0.13, 0.12, hz + 0.1) @ S(0.17, 0.34, 0.05), c)
    if kind in ("king", "commander"):                     # white mundu over the lap, to the ankles
        mb.cone(T(0, 0.0, hz + 0.04), "white", segments=8, r1=0.3, r2=0.27, depth=0.26)
        mb.box(T(0, 0.2, hz + 0.02) @ S(0.5, 0.56, 0.2), "white")
        mb.box(T(0, 0.5, (hz + 0.12) / 2 + 0.04) @ S(0.47, 0.1, hz - 0.04), "white")
        mb.box(T(0, 0.5, 0.11) @ S(0.48, 0.11, 0.05), "gold")
        if kind == "king":                                # red and gold border down the front
            mb.box(T(0.08, 0.556, hz / 2 + 0.06) @ S(0.11, 0.012, hz - 0.02), "red")
            mb.box(T(0.08, 0.558, hz / 2 + 0.06) @ S(0.035, 0.012, hz - 0.02), "gold")
            mb.box(T(0.0, 0.48, hz + 0.13) @ S(0.5, 0.06, 0.05), "gold")


def make_rig(name, collection, kind, seed=0, cloth="cloth_w", seated=False, armed=True, fold=False):
    """Posable version of make_figure. Returns (root, parts) with parts body, head, armL, armR
    (+ legL/legR standing, or 'hips' seated). fold=True adds parts['fold'], crossed forearms in
    front of the chest (see pose_arms_folded)."""
    rng = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    root.empty_display_size = 0.3
    collection.objects.link(root)
    mbs = {p: MB(bevel=FIG_BEVEL) for p in ("body", "head", "armL", "armR", "legL", "legR")}
    split = _SplitMB(mbs["body"], mbs["head"], seated)

    def get(p):
        if p == "body":
            return split, Matrix.Identity(4)
        return mbs[p], Matrix.Identity(4)

    _draw_figure(get, kind, rng, cloth, armed=armed)
    parts = {}
    body = mbs["body"].obj(f"{name}_body", collection, parent=root)
    body.location = (0, 0, RIG_SEAT_DROP if seated else 0.0)
    parts["body"] = body
    head = mbs["head"].obj(f"{name}_head", collection, parent=body)
    head.location = RIG_HEAD
    parts["head"] = head
    for a in ("armL", "armR"):
        ob = mbs[a].obj(f"{name}_{a}", collection, parent=body)
        ob.location = PIVOTS[a]
        parts[a] = ob
    if seated:
        legs = MB(bevel=FIG_BEVEL)
        _rig_seated_legs(legs, kind)
        parts["hips"] = legs.obj(f"{name}_hips", collection, parent=root)
        mbs["legL"].bm.free()
        mbs["legR"].bm.free()
    else:
        for leg in ("legL", "legR"):
            ob = mbs[leg].obj(f"{name}_{leg}", collection, parent=root)
            ob.location = PIVOTS[leg]
            parts[leg] = ob
    if fold:
        skin = "skin_pale" if kind in ("dutch", "imhoff") else "skin"
        fm = MB(bevel=FIG_BEVEL)
        for sgn in (-1, 1):                                # two forearms crossing over the chest
            z = 1.13 + 0.035 * sgn
            fm.box(T(0, 0.21 + 0.025 * sgn, z) @ Rz(0.2 * sgn) @ Ry(0.14 * sgn) @ S(0.44, 0.12, 0.12), skin)
            fm.box(T(-sgn * 0.21, 0.2, z + 0.02) @ S(0.11, 0.13, 0.13), skin)              # hands on the arms
            if kind == "king":
                fm.cone(T(sgn * 0.13, 0.21 + 0.025 * sgn, z) @ Rz(0.2 * sgn) @ Ry(math.pi / 2), "gold",
                        segments=6, r1=0.072, r2=0.072, depth=0.04)
        ob = fm.obj(f"{name}_fold", collection, parent=body)
        ob.scale = (0, 0, 0)
        parts["fold"] = ob
    return root, parts


def key_pose(parts, frame, pose):
    """pose: {part: (rx, ry, rz)} in radians. Keys those parts' rotations at frame."""
    for p, r in pose.items():
        if p in parts:
            parts[p].rotation_euler = r
            parts[p].keyframe_insert("rotation_euler", frame=frame)


ARM_REST_SEATED = {"armL": (0.62, -0.1, 0.0), "armR": (0.62, 0.1, 0.0)}      # forearms toward the armrests
ARM_REST = {"armL": (0.04, -0.06, 0.0), "armR": (0.04, 0.06, 0.0)}
ARMS_FOLDED = {"armL": (0.36, 0.0, -0.3), "armR": (0.36, 0.0, 0.3)}          # upper arms in; 'fold' part shown
POINT_R = {"armR": (1.5, 0.0, 0.15)}                                         # right arm straight out, forward
GESTURE_OUT_L = {"armL": (1.0, -0.8, 0.0)}                                   # left arm swept out, palm open


def pose_arms_folded(parts, f0, f1):
    """Arms move in over f0..f1 and the crossed forearms appear (needs make_rig(fold=True))."""
    key_pose(parts, f0, {a: tuple(parts[a].rotation_euler) for a in ("armL", "armR")})
    key_pose(parts, f1, ARMS_FOLDED)
    fold = parts.get("fold")
    if fold:
        fold.scale = (0, 0, 0)
        fold.keyframe_insert("scale", frame=f0 + (f1 - f0) // 2)
        fold.scale = (1, 1, 1)
        fold.keyframe_insert("scale", frame=f1)


def animate_rig_idle(parts, rng, start, end, body=0.015, head=0.1, every=(40, 75), skip=()):
    """Breathing sway of the body and small head turns/nods, so a character never freezes.
    Key the rig's pose first; parts named in skip are left alone."""
    for p, amt, z_amt in (("body", body, body * 1.5), ("head", head * 0.35, head)):
        if p not in parts or p in skip:
            continue
        ob = parts[p]
        base = ob.rotation_euler.copy()
        f = start + rng.randint(0, 20)
        while f <= end:
            ob.rotation_euler = (base.x + rng.uniform(-amt, amt), base.y + rng.uniform(-amt * 0.5, amt * 0.5),
                                 base.z + rng.uniform(-z_amt, z_amt))
            ob.keyframe_insert("rotation_euler", frame=f)
            f += rng.randint(*every)
        ob.rotation_euler = base


# ===================================================================== court props (S21-S23)
def make_brass_lamp(name, collection, h=1.5, lit=True):
    """Kerala standing brass oil lamp (nilavilakku): stepped round foot, ringed stem, a wide
    oil dish with five wick spouts and a finial. lit=True adds small glowing flames."""
    mb = MB(bevel=0.008)
    mb.cone(T(0, 0, 0.04), "brass", segments=12, r1=0.26, r2=0.22, depth=0.08)
    mb.cone(T(0, 0, 0.12), "brass", segments=12, r1=0.18, r2=0.12, depth=0.1)
    mb.seg((0, 0, 0.16), (0, 0, h * 0.78), 0.04, 0.03, "brass", sides=8)
    for t in (0.3, 0.5, 0.68):
        mb.ico(T(0, 0, h * t) @ S(1, 1, 0.6), "gold", r=0.065, sub=1)
    dz = h * 0.8
    mb.cone(T(0, 0, dz), "brass", segments=12, r1=0.08, r2=0.24, depth=0.08)
    mb.cone(T(0, 0, dz + 0.05), "gold", segments=12, r1=0.245, r2=0.245, depth=0.02)
    for k in range(5):
        a = k * math.tau / 5
        mb.cone(T(0.24 * math.cos(a), 0.24 * math.sin(a), dz + 0.05) @ Rz(a) @ Ry(math.pi / 2),
                "brass", segments=4, r1=0.035, r2=0.015, depth=0.08)
    mb.seg((0, 0, dz + 0.05), (0, 0, h), 0.025, 0.02, "brass", sides=6)
    mb.cone(T(0, 0, h + 0.06), "gold", segments=8, r1=0.06, r2=0.0, depth=0.14)
    ob = mb.obj(name, collection)
    if lit:
        fl = MB()
        for k in range(5):
            a = k * math.tau / 5
            fl.ico(T(0.29 * math.cos(a), 0.29 * math.sin(a), dz + 0.12) @ S(0.03, 0.03, 0.06), "lamp_flame",
                   r=1.0, sub=1)
        mat_emit("lamp_flame", (1.0, 0.72, 0.28), strength=12.0)
        fl.obj(name + "Flames", collection, parent=ob)
    return ob


def make_drape(name, collection, h=2.8, w=0.7, seed=0, tie=0.45):
    """Cloth curtain hanging from a canopy corner, gathered and tied to the post at tie*h
    with a gold tassel (K30). Hangs in the local XZ plane from x=0 (the post) toward +X."""
    rng = random.Random(seed)
    mb = MB()
    nz, nx = 10, 6
    vs = []
    zt = h * tie
    for j in range(nz + 1):
        z = h * (1 - j / nz)
        g = abs(z - zt) / max(zt, h - zt)                 # 0 at the tie, 1 at top and bottom
        width = w * (0.18 + 0.82 * g ** 0.8)
        row = []
        for i in range(nx + 1):
            u = i / nx
            fold = 0.07 * math.sin(u * math.pi * 4 + j * 0.3) * (0.4 + g)
            row.append(mb.bm.verts.new((0.06 + u * width, fold + rng.uniform(-0.01, 0.01), z)))
        vs.append(row)
    for j in range(nz):
        for i in range(nx):
            mb.face([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]], "canvas")
    mb.cone(T(0.1, 0, zt), "gold", segments=8, r1=0.08, r2=0.08, depth=0.06)
    mb.seg((0.14, 0.03, zt), (0.16, 0.05, zt - 0.32), 0.03, 0.055, "gold", sides=6)
    ob = mb.obj(name, collection)
    sol = ob.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.025
    return ob


# ============================================================================
# S25-S27 shared parts (battle near Kollam, Varkala cliffs). Append-only block:
# allied soldiers, extra poses, routed walkers, paddies, ramparts, fire and smoke.
# ============================================================================
for _k, _v in {
    "flag_o":     (0.95, 0.50, 0.10),     # Dutch: plain orange, no symbols (same as port_world)
    "turban_or":  (0.93, 0.52, 0.12),     # allied (Kollam / Kayamkulam / Kochi) turbans, K32 / K34
    "turban_gr":  (0.22, 0.56, 0.27),
    "turban_bl":  (0.20, 0.58, 0.70),
    "turban_ye":  (0.92, 0.78, 0.22),
    "field_dirt": (0.76, 0.62, 0.44),     # dry battlefield ground between the paddies (K32)
    "field_dirt_dk": (0.66, 0.52, 0.36),
    "paddy_lt":   (0.50, 0.68, 0.26),     # light rows in a paddy
    "char":       (0.15, 0.11, 0.09),     # burnt timber
    "ash":        (0.38, 0.35, 0.33),
}.items():
    PALETTE.setdefault(_k, _v)

# Nair warrior with sword raised and the shield held in front (K34 shield wall).
SWORD_UP = {"body": Matrix.Identity(4),
            "legL": T(0.1, 0, 0.88), "legR": T(-0.1, 0, 0.88),
            "armL": T(0.27, 0, 1.4) @ Rx(0.45) @ Rz(math.pi / 2 - 0.35),
            "armR": T(-0.27, 0, 1.4) @ Rx(math.pi - 0.5) @ Ry(0.15)}
POSES.setdefault("sword_up", SWORD_UP)

ALLY_TURBANS = ("turban_or", "turban_gr", "turban_bl", "turban_ye", "red", "cloth_w")


def recolor(ob, mapping=None, strip=()):
    """Swap materials on a mesh by palette name (old -> new) and delete the faces that use
    any material in `strip`. Works in place on the mesh data (shared by its instances)."""
    me = ob.data
    names = [m.name if m else "" for m in me.materials]
    if strip:
        bm = bmesh.new()
        bm.from_mesh(me)
        idx = {i for i, n in enumerate(names) if n in strip}
        dead = [f for f in bm.faces if f.material_index in idx]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(me)
        bm.free()
    for i, n in enumerate(names):
        if mapping and n in mapping:
            me.materials[i] = mat(mapping[n])
    return ob


def make_ally(name, collection, seed=0, turban="turban_or", pose="stand", shield=False):
    """Soldier of the rajas allied to the Dutch (Kollam, Kayamkulam, Kochi): the Nair body
    with a white mundu, a turban in his raja's colour and a spear; no shield by default."""
    ob = make_figure(name, collection, "nair_spear", seed=seed, pose=pose)
    return recolor(ob, {"red": turban}, strip=() if shield else ("shield", "brass"))


def make_ally_walker(name, collection, seed=0, turban="turban_or", shield=False):
    root, parts = make_walker(name, collection, "nair_spear", seed=seed)
    for p in parts.values():
        recolor(p, {"red": turban}, strip=() if shield else ("shield", "brass"))
    return root, parts


def clone_walker(parts, name, collection):
    """A new walker that shares the limb meshes of `parts` (cheap crowds of walkers)."""
    root = bpy.data.objects.new(name, None)
    root.empty_display_size = 0.3
    collection.objects.link(root)
    out = {}
    for p, src in parts.items():
        ob = bpy.data.objects.new(f"{name}_{p}", src.data)
        collection.objects.link(ob)
        ob.parent = root
        ob.location = PIVOTS[p]
        out[p] = ob
    return root, out


def animate_route(root, parts, legs, ground, stride_frames=14, swing=0.45, turn=10, lean=0.0,
                  bob=0.035, phase=0, heading=None):
    """Walk (or run) a figure through timed legs [(f0, f1, (x0, y0), (x1, y1)), ...]. It stands
    still between legs and turns on the spot over `turn` frames at the start of a leg, so a
    column can halt and turn back. lean > 0 tips the body forward (running)."""
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    head = heading
    for li, (f0, f1, a, b) in enumerate(legs):
        a3, b3 = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
        d = b3 - a3
        moving = d.length > 1e-3
        h = math.atan2(d.y, d.x) - math.pi / 2 if moving else (head or 0.0)
        if head is not None:
            h = head + ((h - head + math.pi) % math.tau - math.pi)
        t_turn = min(turn, max(1, (f1 - f0) // 3)) if head is not None and abs(h - head) > 0.05 else 0
        m0 = f0 + t_turn
        prefs.keyframe_new_interpolation_type = "LINEAR"
        try:
            if t_turn:
                root.location = (a3.x, a3.y, ground(a3.x, a3.y))
                root.rotation_euler = (0, 0, head)
                root.keyframe_insert("location", frame=f0)
                root.keyframe_insert("rotation_euler", frame=f0)
            f = m0
            while True:
                ff = min(f, f1)
                u = (ff - m0) / max(1, f1 - m0)
                p = a3.lerp(b3, u)
                root.location = (p.x, p.y, ground(p.x, p.y))
                root.rotation_euler = (-lean if moving else 0.0, 0, h)
                root.keyframe_insert("location", frame=ff)
                root.keyframe_insert("rotation_euler", frame=ff)
                if ff >= f1:
                    break
                f += 6
            if moving and lean:
                root.rotation_euler = (0, 0, h)
                root.keyframe_insert("rotation_euler", frame=f1 + 3)
        finally:
            prefs.keyframe_new_interpolation_type = old
        head = h
        if not moving:
            continue
        for key in ("legL", "legR", "armL", "armR"):
            parts[key].rotation_euler = (0, 0, 0)
            parts[key].keyframe_insert("rotation_euler", frame=m0)
        f = m0 + 2 + phase % max(1, stride_frames // 2)
        k = 0
        while f < f1 - stride_frames // 2:
            sgn = 1 if k % 2 == 0 else -1
            parts["legL"].rotation_euler = (sgn * swing, 0, 0)
            parts["legR"].rotation_euler = (-sgn * swing, 0, 0)
            parts["armL"].rotation_euler = (-sgn * swing * 0.8, 0, 0)
            parts["armR"].rotation_euler = (sgn * swing * 0.8, 0, 0)
            for key in ("legL", "legR", "armL", "armR"):
                parts[key].keyframe_insert("rotation_euler", frame=f)
            parts["body"].location = (0, 0, 0.0)
            parts["body"].keyframe_insert("location", frame=f)
            parts["body"].location = (0, 0, bob)
            parts["body"].keyframe_insert("location", frame=f + stride_frames // 2)
            f += stride_frames
            k += 1
        for key in ("legL", "legR", "armL", "armR"):
            parts[key].rotation_euler = (0, 0, 0)
            parts[key].keyframe_insert("rotation_euler", frame=f1)
        parts["body"].location = (0, 0, 0)
        parts["body"].keyframe_insert("location", frame=f1)


def animate_bob(ob, rng, start, end, height=0.12, period=(14, 22), sway=0.04):
    """Rhythmic up-and-down (warriors stamping and brandishing) with a little sway."""
    base_z = ob.location.z
    base = ob.rotation_euler.copy()
    f = start + rng.randint(0, 8)
    per = rng.randint(*period)
    up = False
    while f <= end:
        ob.location.z = base_z + (height * rng.uniform(0.7, 1.1) if up else 0.0)
        ob.rotation_euler = (base.x + rng.uniform(-sway, sway), base.y + rng.uniform(-sway, sway), base.z)
        ob.keyframe_insert("location", index=2, frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
        up = not up
        f += per // 2
    ob.location.z = base_z
    ob.rotation_euler = base


# --------------------------------------------------------------- battlefield
def make_paddy_cell(name, collection, w=14.0, d=10.0, seed=0, bund=0.9, bund_h=0.38):
    """One rice paddy: rows of young rice in two greens (the stripes in K32) inside a raised
    earth bund. Long side along X; origin at the centre on the ground."""
    rng = random.Random(seed)
    mb = MB(bevel=0.04)
    rows = max(4, int(d / 1.1))
    iw, idp = w - 2 * bund, d - 2 * bund
    for i in range(rows):
        y = -idp / 2 + (i + 0.5) * idp / rows
        mb.box(T(0, y, 0.06 + rng.uniform(0, 0.03)) @ S(iw, idp / rows * 1.001, 0.12),
               "paddy_green" if i % 2 else "paddy_lt")
    for sy in (-1, 1):
        mb.box(T(0, sy * (d / 2 - bund / 2), bund_h / 2) @ S(w, bund, bund_h), "paddy_bund")
    for sx in (-1, 1):
        mb.box(T(sx * (w / 2 - bund / 2), 0, bund_h / 2) @ S(bund, d - 2 * bund + 0.02, bund_h), "paddy_bund")
    return mb.obj(name, collection)


def make_rampart(name, collection, length=12.0, h=2.2, base_w=5.0, top_w=1.8, seed=0,
                 side="earth_wall", top="paddy_bund"):
    """Faceted earth rampart (packed red-brown earth) running along Y, tapered ends.
    Origin on the ground at its centre."""
    rng = random.Random(seed)
    mb = MB()
    n = max(3, int(length / 1.4))
    rings = []
    for i in range(n + 1):
        t = i / n
        y = (t - 0.5) * length
        end = min(1.0, min(t, 1 - t) * length / 1.1)       # steep ends
        hh = h * (0.25 + 0.75 * end) * rng.uniform(0.92, 1.06)
        tw = top_w * rng.uniform(0.85, 1.15)
        prof = [(-base_w * 0.5, 0.0), (-tw * 0.5 + rng.uniform(-0.15, 0.15), hh),
                (tw * 0.5 + rng.uniform(-0.15, 0.15), hh * rng.uniform(0.95, 1.05)), (base_w * 0.5, 0.0)]
        inner = 0 < i < n
        rings.append([mb.bm.verts.new((x + rng.uniform(-0.12, 0.12), y + rng.uniform(-0.2, 0.2) * inner, z - 0.3 * (z == 0)))
                      for x, z in prof])
    for i in range(n):
        for j in range(3):
            mb.face([rings[i][j], rings[i + 1][j], rings[i + 1][j + 1], rings[i][j + 1]], top if j == 1 else side)
    mb.face(rings[0][::-1], side)
    mb.face(rings[n], side)
    return mb.obj(name, collection)


def make_bronze_cannon(name, collection):
    """kit field gun with a bronze barrel (the Travancore guns in K32)."""
    return recolor(make_cannon(name, collection), {"iron": "brass"})


def make_boulder(name, collection, seed=0, size=1.0, m="laterite"):
    """Faceted fallen block in any palette colour (laterite boulders under the Varkala cliffs)."""
    rng = random.Random(seed)
    mb = MB()
    mb.ico(S(size, size * rng.uniform(0.7, 1.0), size * rng.uniform(0.55, 0.85)) @ Rz(rng.uniform(0, 3)), m,
           r=1.0, sub=1, jitter=0.22, rng=rng)
    return mb.obj(name, collection)


# ------------------------------------------------------------ fire and smoke
def fx_materials():
    """Glowing fire colours (emissive) and the grey smoke shades, created once."""
    for name, rgb, k in (("fx_core", (1.0, 0.74, 0.12), 1.3), ("fx_fire", (1.0, 0.40, 0.02), 1.1),
                         ("fx_fire_dk", (0.90, 0.22, 0.02), 0.85), ("fx_ember", (0.90, 0.26, 0.02), 0.7)):
        if not bpy.data.materials.get(name):
            m = mat_emit(name, rgb, k)
            # mostly glow, little diffuse: lit by the sun, a bright orange washes out to salmon
            m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value =                 (*[c * 0.12 for c in srgb_to_linear(rgb)], 1)
    for k in ("smoke", "smoke_md", "smoke_dk", "char", "ash"):
        mat(k)


def make_fireball(name, collection, seed=0, r=4.0):
    """Faceted low-poly fireball (K33): a glowing yellow core, orange facet blobs and long
    spikes thrown outward. Origin at the centre; grow it from scale 0 when it goes off."""
    fx_materials()
    rng = random.Random(seed)
    mb = MB()
    mb.ico(S(r * 0.55, r * 0.55, r * 0.6), "fx_core", r=1.0, sub=1, jitter=0.2, rng=rng)
    for k in range(14):
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 1))).normalized()
        s = r * rng.uniform(0.32, 0.5)
        mb.ico(T(d * r * rng.uniform(0.45, 0.7)) @ S(s, s, s * rng.uniform(0.9, 1.2)) @ Rz(rng.uniform(0, 3)),
               ("fx_fire", "fx_core", "fx_fire", "fx_fire_dk")[k % 4], r=1.0, sub=1, jitter=0.18, rng=rng)
    for k in range(11):
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.1, 1))).normalized()
        mb.seg(d * r * 0.4, d * r * rng.uniform(1.2, 1.7), r * 0.16, 0.0, "fx_core" if k % 2 else "fx_fire",
               sides=4, spin=rng.uniform(0, 1))
    return mb.obj(name, collection)


def make_flames(name, collection, seed=0, size=1.0):
    """Cluster of faceted flame tongues for a burning ruin. Origin at the base."""
    fx_materials()
    rng = random.Random(seed)
    mb = MB()
    for k in range(rng.randint(5, 8)):
        x, y = rng.uniform(-0.6, 0.6) * size, rng.uniform(-0.6, 0.6) * size
        hgt = size * rng.uniform(1.0, 2.3)
        mb.cone(T(x, y, hgt / 2) @ Rx(rng.uniform(-0.15, 0.15)) @ Ry(rng.uniform(-0.15, 0.15)),
                "fx_fire" if k % 3 else "fx_core", segments=5, r1=size * rng.uniform(0.3, 0.5), r2=0.0, depth=hgt)
    mb.ico(T(0, 0, 0.25 * size) @ S(size * 0.8, size * 0.8, size * 0.35), "fx_fire_dk", r=1.0, sub=1)
    return mb.obj(name, collection)


def animate_flicker(ob, rng, start, end, amount=0.22, every=(3, 6)):
    """Fire flicker: quick random scale keys."""
    base = ob.scale.copy()
    f = start
    while f <= end:
        ob.scale = (base.x * (1 + rng.uniform(-amount, amount) * 0.5),
                    base.y * (1 + rng.uniform(-amount, amount) * 0.5),
                    base.z * (1 + rng.uniform(-amount, amount)))
        ob.keyframe_insert("scale", frame=f)
        f += rng.randint(*every)
    ob.scale = base


def make_puff(name, collection, seed=0, m="smoke_md"):
    """One faceted smoke puff (radius 1) for smoke columns and gun smoke."""
    rng = random.Random(seed)
    mb = MB()
    mb.ico(S(1.0, 1.0, 0.88) @ Rz(rng.uniform(0, 3)), m, r=1.0, sub=1, jitter=0.16, rng=rng)
    return mb.obj(name, collection)


def animate_puff(ob, born, end, p0, vel, s0=0.4, s1=3.0, grow=40.0, drag=0.0, step=6, fade=None):
    """Puff appears at `born` (scale 0 before), drifts with `vel` (m/s, slowing with `drag`)
    and swells from s0 to s1 with time constant `grow` frames. fade=(f0, f1) shrinks it away."""
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        ob.scale = (0, 0, 0)
        ob.location = p0
        ob.keyframe_insert("scale", frame=born - 1)
        ob.keyframe_insert("location", frame=born - 1)
        f = born
        while True:
            ff = min(f, end)
            t = (ff - born) / FPS
            k = t if drag <= 0 else (1 - math.exp(-drag * t)) / drag
            ob.location = (p0[0] + vel[0] * k, p0[1] + vel[1] * k, p0[2] + vel[2] * k)
            s = s0 + (s1 - s0) * (1 - math.exp(-(ff - born) / grow))
            if fade and ff > fade[0]:
                s *= max(0.0, 1 - (ff - fade[0]) / max(1, fade[1] - fade[0]))
            ob.scale = (s, s, s)
            ob.keyframe_insert("location", frame=ff)
            ob.keyframe_insert("scale", frame=ff)
            if ff >= end:
                break
            f += step if ff > born else 2
    finally:
        prefs.keyframe_new_interpolation_type = old


def animate_ballistic(ob, f0, p0, vel, ground, end, spin=(3.0, 2.0, 1.0), g=9.8, step=2, hide_before=True):
    """Thrown debris: hidden before f0, flies from p0 with vel (m/s) under gravity, tumbling,
    and comes to rest where it lands."""
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        sc = ob.scale.copy()
        if hide_before:
            ob.scale = (0, 0, 0)
            ob.keyframe_insert("scale", frame=f0 - 1)
            ob.scale = sc
            ob.keyframe_insert("scale", frame=f0)
        else:
            ob.keyframe_insert("location", frame=f0 - 1)
            ob.keyframe_insert("rotation_euler", frame=f0 - 1)
        f = f0
        r0 = ob.rotation_euler.copy()
        while f <= end:
            t = (f - f0) / FPS
            x, y = p0[0] + vel[0] * t, p0[1] + vel[1] * t
            z = p0[2] + vel[2] * t - 0.5 * g * t * t
            gz = ground(x, y) + 0.1
            landed = z <= gz and t > 0.1
            ob.location = (x, y, max(z, gz))
            ob.rotation_euler = (r0.x + spin[0] * t, r0.y + spin[1] * t, r0.z + spin[2] * t)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)
            if landed:
                break
            f += step
    finally:
        prefs.keyframe_new_interpolation_type = old


def make_ruin(name, collection, w=5.0, d=4.0, seed=0):
    """What is left of a timber shed after a blast: charred floor, broken posts, fallen
    planks, collapsed scorched thatch and glowing embers. Origin on the ground at the centre."""
    fx_materials()
    rng = random.Random(seed)
    mb = MB(bevel=0.02)
    mb.box(T(0, 0, 0.12) @ S(w + 0.5, d + 0.5, 0.24), "stone")
    mb.box(T(0, 0, 0.26) @ S(w, d, 0.06), "char")
    for sx in (-1, 1):
        for sy in (-1, 1):
            hgt = rng.uniform(0.6, 2.0)
            mb.box(T(sx * w / 2, sy * d / 2, 0.24 + hgt / 2) @ Rx(rng.uniform(-0.2, 0.2)) @ S(0.2, 0.2, hgt), "char")
    for k in range(14):
        a = rng.uniform(0, math.tau)
        L = rng.uniform(1.0, 2.6)
        x, y = rng.uniform(-w / 2, w / 2), rng.uniform(-d / 2, d / 2)
        mb.box(T(x, y, 0.4 + rng.uniform(0, 0.6)) @ Rz(a) @ Rx(rng.uniform(-0.5, 0.5)) @ S(0.22, L, 0.06),
               "char" if k % 3 else "hull_dark")
    for k in range(4):                      # wall stubs with ragged burnt tops
        x = rng.choice((-1, 1)) * w / 2 if k % 2 else rng.uniform(-w / 2, w / 2)
        y = rng.uniform(-d / 2, d / 2) if k % 2 else rng.choice((-1, 1)) * d / 2
        hgt = rng.uniform(0.5, 1.3)
        mb.box(T(x, y, 0.24 + hgt / 2) @ Rz(0 if k % 2 == 0 else math.pi / 2) @ S(rng.uniform(1.0, 2.2), 0.12, hgt),
               "char")
    for k in range(5):                      # heaps of scorched thatch
        x, y = rng.uniform(-w / 2, w / 2) * 0.8, rng.uniform(-d / 2, d / 2) * 0.8
        mb.ico(T(x, y, 0.3) @ S(rng.uniform(0.8, 1.4), rng.uniform(0.7, 1.2), 0.35), "ash" if k % 2 else "char",
               r=1.0, sub=1, jitter=0.2, rng=rng)
    for k in range(9):                      # embers
        x, y = rng.uniform(-w / 2, w / 2) * 0.9, rng.uniform(-d / 2, d / 2) * 0.9
        mb.ico(T(x, y, 0.32) @ S(rng.uniform(0.25, 0.5), rng.uniform(0.25, 0.5), 0.12), "fx_ember", r=1.0, sub=1)
    return mb.obj(name, collection)


def make_shell(name, collection, r=0.3):
    """Mortar shell: an iron ball with a short fuse."""
    mb = MB()
    mb.ico(Matrix.Identity(4), "iron", r=r, sub=2)
    mb.seg((0, 0, r * 0.9), (0, 0, r * 1.5), 0.035, 0.035, "post", sides=4)
    return mb.obj(name, collection)
