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
    "rice":       (0.95, 0.94, 0.88),
    "soil":       (0.42, 0.29, 0.18),
    "soil_dk":    (0.30, 0.21, 0.14),
    "ghat_lo":    (0.44, 0.58, 0.24),
    "ghat_hi":    (0.30, 0.46, 0.17),
    "table":      (0.80, 0.761, 0.698),
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

    skin = "skin_pale" if kind == "dutch" else "skin"
    # ---- legs
    for leg in ("legL", "legR"):
        if kind == "dutch":
            put(leg, "box", T(0, 0, -0.24) @ S(0.17, 0.18, 0.5), "white")
            put(leg, "box", T(0, 0, -0.64) @ S(0.16, 0.17, 0.42), "black")
            put(leg, "box", T(0, 0.05, -0.86) @ S(0.16, 0.26, 0.07), "black")
        else:
            put(leg, "box", T(0, 0, -0.42) @ S(0.15, 0.16, 0.84), skin)
            put(leg, "box", T(0, 0.05, -0.86) @ S(0.15, 0.24, 0.07), skin)
    # ---- arms
    for arm in ("armL", "armR"):
        if kind == "dutch":
            put(arm, "box", T(0, 0, -0.27) @ S(0.13, 0.14, 0.56), "coat_blue")
            put(arm, "box", T(0, 0, -0.52) @ S(0.14, 0.15, 0.08), "white")
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

    torso = {"dutch": "coat_blue", "commander": "white", "villager_robe": cloth}.get(kind, skin)
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


def make_figure(name, collection, kind, seed=0, cloth="cloth_w", pose="stand"):
    """Static single-mesh figure (for crowds and instancing). pose: "stand" or "sit"."""
    rng = random.Random(seed)
    mb = MB(bevel=FIG_BEVEL)
    if pose == "sit":
        _draw_figure(lambda p: (mb, SIT[p]), kind, rng, cloth, armed=False)
    else:
        _draw_figure(lambda p: (mb, T(*PIVOTS[p])), kind, rng, cloth)
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
