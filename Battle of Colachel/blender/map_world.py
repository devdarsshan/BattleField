"""The 3D map world of the Kerala coast (look: Flow refs frames/flow_refs/K08a_v2, K08b_v2).

No parchment. A painted sea (turquoise shallows into blue, light wave strokes) and the
land as a dense faceted low-poly mesh: a warm sand strip, a thick belt of palms several
rows deep, sharp ridged hills cut by river valleys with the rivers running along the
valley floors, earthy ridge tops, forest patches on the lower slopes, a backwater lagoon
with a sand rim, and small ponds. Ships at sea, and the stockade with a red tent at
Colachel. Detail is concentrated along the camera's path (DETAIL_BOX).

Units: Blender metres on the kerala_geo projection (50 m per real km, Colachel at 0,0).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

import colachel_kit as kit
import kerala_geo as geo

HERE = os.path.dirname(os.path.abspath(__file__))
RX0, RX1, RY0, RY1 = geo.MAP_REGION
DETAIL_BOX = (-9000.0, 3000.0, -2500.0, 11000.0)  # fine mesh and dense props here (camera path)
# backwater canals and the channel to the sea (lat, lon pairs), S08
CANALS = [((9.52, 76.47), (9.52, 76.37)), ((9.41, 76.49), (9.43, 76.39)), ((9.66, 76.47), (9.64, 76.41)),
          ((9.80, 76.36), (9.80, 76.26))]

MAP_PALETTE = {
    # greens and sand follow the beach palette (kit.PALETTE grass/hill/sand) so the map
    # matches the earlier clips
    "m_sand":   (0.86, 0.72, 0.52),
    "m_g1":     (0.42, 0.56, 0.24),
    "m_g2":     (0.36, 0.50, 0.20),
    "m_g3":     (0.48, 0.60, 0.27),
    "m_g4":     (0.30, 0.44, 0.18),
    "m_earth":  (0.58, 0.44, 0.30),
    "m_river":  (0.17, 0.44, 0.72),
    "m_lagoon": (0.26, 0.60, 0.68),
    "m_cloud":  (0.80, 0.81, 0.84),
    "m_cloud2": (0.64, 0.66, 0.70),
    "m_red":    (0.82, 0.10, 0.10),
    "m_palm":   (0.24, 0.55, 0.14),
    "m_palm2":  (0.33, 0.62, 0.18),
    "m_tree":   (0.32, 0.55, 0.19),
    "m_tree2":  (0.40, 0.62, 0.22),
}


def mmat(name):
    return kit.mat(name, MAP_PALETTE[name])


def _smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _nz(x, y, s, o=0.0):
    return 0.5 + 0.5 * noise.noise(Vector((x / s + o, y / s - o, 0.37 + o)))


def _ridge(x, y, s, o=0.0):
    v = noise.ridged_multi_fractal(Vector((x / s + o, y / s + o * 0.5, 0.5)), 1.0, 2.0, 3, 1.0, 2.0)
    return max(0.0, min(1.0, (v - 0.4) / 1.4))


def in_box(x, y, box, pad=0.0):
    return box[0] - pad < x < box[1] + pad and box[2] - pad < y < box[3] + pad


def clip_poly(poly, x0, x1, y0, y1):
    """Sutherland-Hodgman clip of a polygon to a box."""
    def clip(pts, inside, cut):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia:
                    out.append(cut(a, b))
                out.append(b)
            elif ia:
                out.append(cut(a, b))
        return out

    def cx(v):
        return lambda a, b: (v, a[1] + (b[1] - a[1]) * (v - a[0]) / (b[0] - a[0]))

    def cy(v):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (v - a[1]) / (b[1] - a[1]), v)

    pts = list(poly)
    pts = clip(pts, lambda p: p[0] >= x0, cx(x0))
    pts = clip(pts, lambda p: p[0] <= x1, cx(x1))
    pts = clip(pts, lambda p: p[1] >= y0, cy(y0))
    pts = clip(pts, lambda p: p[1] <= y1, cy(y1))
    return pts


def river_path(src, mouth, seed):
    """Winding river from source to a little past the mouth: [(x, y, half_width)]."""
    rng = random.Random(seed)
    (sx, sy), (mx, my) = geo.xy(*src), geo.xy(*mouth)
    L = math.hypot(mx - sx, my - sy)
    ux, uy = (mx - sx) / L, (my - sy) / L
    nx, ny = -uy, ux
    ph = rng.uniform(0, 6)
    n = max(10, int(L / 35))
    pts = []
    for k in range(n + 8):
        t = k / n
        env = math.sin(math.pi * min(t, 1.0)) ** 0.7
        wob = (math.sin(t * 7 + ph) * 0.55 + math.sin(t * 19 + ph * 2) * 0.3 + math.sin(t * 43 + ph) * 0.12) \
            * L * 0.075 * env
        pts.append((sx + (mx - sx) * t + nx * wob, sy + (my - sy) * t + ny * wob, 14 + 22 * min(t, 1.0)))
    return pts


class Land:
    """Height and surface rules for the map land."""

    def __init__(self):
        self.coast = geo.coast_detailed(150.0)
        self.poly = geo.land_polygon_detailed(60.0)
        self.rivers = []
        for i, (name, src, mouth) in enumerate(geo.RIVERS):
            pts = river_path(src, mouth, 100 + i)
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            self.rivers.append((pts, (min(xs), max(xs), min(ys), max(ys))))
        self.lagoons = [self.backwater(3900.0, 5400.0, 260.0, 470.0),    # Kollam backwater (K08b)
                        self.backwater(6700.0, 9900.0, 260.0, 640.0)]    # Vembanad backwaters (S08)
        for i, (src, mouth) in enumerate(CANALS):
            pts = [(x, y, w * 0.55) for x, y, w in river_path(src, mouth, 300 + i)]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            self.rivers.append((pts, (min(xs), max(xs), min(ys), max(ys))))
        self.lakes = []
        for lat, lon, a_km, b_km, ang in geo.LAKES:
            cx, cy = geo.xy(lat, lon)
            self.lakes.append((cx, cy, a_km * geo.MAP_SCALE, b_km * geo.MAP_SCALE, math.radians(ang)))
        rng = random.Random(7)
        tries = 0
        while len(self.lakes) < len(geo.LAKES) + 0 and tries < 500:     # (ponds read as blotches from above)
            tries += 1
            x, y = rng.uniform(DETAIL_BOX[0], DETAIL_BOX[1]), rng.uniform(DETAIL_BOX[2], DETAIL_BOX[3])
            if not geo.point_in_poly(x, y, self.poly):
                continue
            d = self.coast_dist(x, y)
            if 520 < d < 1500 and self.river_dist(x, y) > 250 and not self.in_lagoon(x, y):
                self.lakes.append((x, y, rng.uniform(55, 120), rng.uniform(35, 70), rng.uniform(0, 3.1)))

    def backwater(self, y0, y1, d0, d1):
        """A long thin lagoon behind the beach, following the coast between y0 and y1,
        from d0 to d1 metres inland, tapering at both ends."""
        pts = [(x, y) for x, y in geo.coast_detailed(80.0) if y0 <= y <= y1 and x < 0]   # west coast only
        pts.sort(key=lambda p: p[1])
        inner, outer = [], []
        for i, (x, y) in enumerate(pts):
            j = min(i + 1, len(pts) - 1)
            k = max(i - 1, 0)
            tx, ty = pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]
            L = math.hypot(tx, ty) or 1.0
            nx, ny = ty / L, -tx / L                   # inland normal for a north-running west coast
            t = i / max(1, len(pts) - 1)
            taper = math.sin(math.pi * t) ** 0.5
            mid = (d0 + d1) / 2 + 60 * math.sin(t * 9)
            half = (d1 - d0) / 2 * taper
            inner.append((x + nx * (mid - half), y + ny * (mid - half)))
            outer.append((x + nx * (mid + half), y + ny * (mid + half)))
        return inner + outer[::-1]

    def in_lagoon(self, x, y):
        return any(geo.point_in_poly(x, y, p) for p in self.lagoons)

    def lagoon_dist(self, x, y):
        return min(geo.dist_to_polyline(x, y, p + p[:1])[0] for p in self.lagoons)

    def coast_dist(self, x, y):
        return geo.dist_to_polyline(x, y, self.coast)[0]

    def river_dist(self, x, y, reach=900.0):
        best = 1e9
        for pts, (x0, x1, y0, y1) in self.rivers:
            if x0 - reach < x < x1 + reach and y0 - reach < y < y1 + reach:
                best = min(best, geo.dist_to_polyline(x, y, [(p[0], p[1]) for p in pts])[0])
        return best

    def in_lake(self, x, y, grow=1.0):
        for cx, cy, a, b, t in self.lakes:
            dx, dy = x - cx, y - cy
            u = (dx * math.cos(t) + dy * math.sin(t)) / (a * grow)
            v = (-dx * math.sin(t) + dy * math.cos(t)) / (b * grow)
            if u * u + v * v < 1.0:
                return True
        return False

    def lowland(self, x, y, d):
        """1 in the flat backwater country round Vembanad, 0 elsewhere."""
        return _smooth(6000, 6900, y) * (1 - _smooth(10000, 10800, y)) * (1 - _smooth(2200, 3400, d))

    def height(self, x, y, d=None):
        d = self.coast_dist(x, y) if d is None else d
        base = 5.0 + 12.0 * _smooth(0, 450, d)
        hills = _smooth(380, 1400, d) * (90.0 + 1150.0 * _ridge(x, y, 3400, 1.7) ** 1.4)   # exaggerated, as in Flow
        hills += 1.2 * geo.ghats_height(x, y, lambda a, b: _nz(a, b, 2600, 0.3)) * _smooth(800, 3000, d)
        hills += 30.0 * _nz(x, y, 300, 4.0) * _smooth(250, 800, d)
        # the backwater country round Vembanad is low and flat, with the hills far inland
        hills *= 1.0 - 0.9 * self.lowland(x, y, d)
        dr = self.river_dist(x, y)
        valley = 1.0 - 0.88 * math.exp(-(dr / 260.0) ** 2)          # rivers cut valleys into the hills
        h = base + hills * valley
        if self.in_lake(x, y, 1.3) or self.in_lagoon(x, y):
            h = min(h, 2.0)
        return h


def build_land(coll, land):
    rng = random.Random(11)
    poly = clip_poly(land.poly, RX0, RX1, RY0, RY1)
    verts = [Vector((x, y)) for x, y in poly]
    nb = len(verts)
    for box, step, skip_box in ((DETAIL_BOX, 85.0, None), ((RX0, RX1, RY0, RY1), 240.0, DETAIL_BOX)):
        y = box[2] + step / 2
        while y < box[3]:
            x = box[0] + step / 2
            while x < box[1]:
                px, py = x + rng.uniform(-0.38, 0.38) * step, y + rng.uniform(-0.38, 0.38) * step
                if (skip_box is None or not in_box(px, py, skip_box)) and geo.point_in_poly(px, py, poly) \
                        and land.coast_dist(px, py) > 45:
                    verts.append(Vector((px, py)))
                x += step
            y += step
    out = delaunay_2d_cdt(verts, [], [list(range(nb))], 1, 0.01)
    vco, faces = out[0], out[2]
    bm = bmesh.new()
    bv = []
    for v in vco:
        d = land.coast_dist(v.x, v.y)
        bv.append(bm.verts.new((v.x, v.y, land.height(v.x, v.y, d) if d > 1 else 4.0)))
    mats = ["m_sand", "m_g1", "m_g2", "m_g3", "m_g4", "m_earth"]
    for f in faces:
        if len(f) < 3:
            continue
        try:
            bm.faces.new([bv[i] for i in f])
        except ValueError:
            continue
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    for face in bm.faces:
        c = face.calc_center_median()
        n = face.normal
        d = land.coast_dist(c.x, c.y)
        sand_w = 300 + 140 * _nz(c.x, c.y, 700, 5.0)
        zone = _nz(c.x, c.y, 650, 3.3)
        near_water = land.in_lake(c.x, c.y, 1.45) or (in_box(c.x, c.y, DETAIL_BOX) and land.lagoon_dist(c.x, c.y) < 75)
        if d < sand_w or near_water:
            m = "m_sand"
        elif (c.z > 600 and abs(n.z) < 0.7 and _nz(c.x, c.y, 220, 8.1) > 0.64) or \
                (c.z > 800 and _nz(c.x, c.y, 260, 6.6) > 0.62):
            m = "m_earth"
        elif c.z < 70:
            m = "m_g3" if zone > 0.5 else "m_g1"
        elif c.z < 300:
            m = "m_g1" if zone > 0.45 else "m_g2"
        else:
            m = "m_g2" if zone > 0.4 else "m_g4"
        if m.startswith("m_g") and rng.random() < 0.15:
            m = {"m_g1": "m_g3", "m_g2": "m_g1", "m_g3": "m_g1", "m_g4": "m_g2"}[m]
        face.material_index = mats.index(m)
    me = bpy.data.meshes.new("MapLand")
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(mmat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("MapLand", me)
    coll.objects.link(ob)
    bvh = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices for p in me.polygons])
    print("map land:", len(me.vertices), "verts,", len(me.polygons), "faces")
    return ob, bvh


def ground_z(bvh, x, y, default=4.0):
    hit = bvh.ray_cast(Vector((x, y, 5000.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else default


def build_sea(coll, land, frames=600):
    """Faceted low-poly sea, the same look as the beach clips (clip 01) scaled up for map
    height: a jittered, triangulated grid whose facets catch the sky light and dark,
    turquoise along the shore deepening to blue, and a slow rolling swell (flat near the
    coast so it never laps over the beach)."""
    rng = random.Random(53)
    step = 115.0
    shallow = kit.srgb_to_linear((0.52, 0.83, 0.80))
    mid = kit.srgb_to_linear((0.38, 0.67, 0.83))
    deep = kit.srgb_to_linear((0.28, 0.55, 0.79))
    coast = geo.coast_detailed(300.0)
    nx_, ny_ = int((RX1 - RX0) / step) + 1, int((RY1 - RY0) / step) + 1
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new("Col")
    dl = bm.verts.layers.deform.verify()
    grid = []
    for j in range(ny_):
        row = []
        for i in range(nx_):
            x, y = RX0 + i * step, RY0 + j * step
            if 0 < i < nx_ - 1 and 0 < j < ny_ - 1:
                x += rng.uniform(-0.32, 0.32) * step
                y += rng.uniform(-0.32, 0.32) * step
            v = bm.verts.new((x, y, 0.0))
            d = geo.dist_to_polyline(x, y, coast)[0]
            t1 = _smooth(150, 900, d)
            t2 = _smooth(900, 3200, d)
            c = [shallow[k] * (1 - t1) + mid[k] * t1 for k in range(3)]
            c = [c[k] * (1 - t2) + deep[k] * t2 for k in range(3)]
            sh = rng.uniform(0.95, 1.05)
            v[col] = (c[0] * sh, c[1] * sh, c[2] * sh, 1.0)
            v[dl][0] = _smooth(250, 900, d)            # swell fades out at the shore
            row.append(v)
        grid.append(row)
    for j in range(ny_ - 1):
        for i in range(nx_ - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("MapSea")
    bm.to_mesh(me)
    bm.free()
    m = bpy.data.materials.new("MapSea")
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["Specular IOR Level"].default_value = 0.6
    me.materials.append(m)
    for poly in me.polygons:
        poly.use_smooth = False
    sea = bpy.data.objects.new("MapSea", me)
    coll.objects.link(sea)
    sea.vertex_groups.new(name="Swell")
    # travel is metres per 10 s, so the swell keeps the same pace however long the segment is
    for name, scale, strength, travel in (("MapSwellA", 420.0, 95.0, (550.0, 1500.0)),
                                          ("MapSwellB", 160.0, 38.0, (-750.0, 520.0))):
        travel = (travel[0] * frames / 240.0, travel[1] * frames / 240.0)
        tex = bpy.data.textures.new(name, "CLOUDS")
        tex.noise_scale = scale
        tex.noise_depth = 0
        mod = sea.modifiers.new(name, "DISPLACE")
        mod.texture = tex
        mod.texture_coords = "OBJECT"
        mod.strength = strength
        mod.mid_level = 0.5
        mod.vertex_group = "Swell"
        drv = bpy.data.objects.new(name + "Driver", None)
        coll.objects.link(drv)
        mod.texture_coords_object = drv

        def keys(drv=drv, travel=travel):
            drv.location = (0, 0, 0)
            drv.keyframe_insert("location", frame=1)
            drv.location = (travel[0], travel[1], 0)
            drv.keyframe_insert("location", frame=frames)
        kit.keyframe_linear(keys)
    kit.mat("m_deep", (0.28, 0.55, 0.79))
    dp = kit.MB()
    dp.box(kit.T(0, 0, -40.0) @ kit.S(200000, 200000, 1.0), "m_deep")
    dp.obj("MapDeepSea", coll)


def build_water(coll, land, bvh):
    """River ribbons on the valley floors, the lagoon and the ponds."""
    mb = kit.MB()
    for pts, _ in land.rivers:
        rows = []
        for i, (x, y, w) in enumerate(pts):
            if not (RX0 < x < RX1 and RY0 < y < RY1):
                continue
            j = min(i + 1, len(pts) - 1)
            k = max(i - 1, 0)
            tx, ty = pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]
            L = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / L, tx / L
            pa, pb = (x + nx * w, y + ny * w), (x - nx * w, y - ny * w)
            za, zb = ground_z(bvh, *pa, default=-50), ground_z(bvh, *pb, default=-50)
            if za < 0 and zb < 0:
                if rows:
                    rows.append((mb.bm.verts.new((*pa, 0.6)), mb.bm.verts.new((*pb, 0.6))))
                    break
                continue
            z = max(min(za, zb), 1.0) + 3.0
            rows.append((mb.bm.verts.new((*pa, z)), mb.bm.verts.new((*pb, z))))
        for (a0, b0), (a1, b1) in zip(rows, rows[1:]):
            mb.face([a0, a1, b1, b0], "m_river")
    mmat("m_river")
    mb.obj("MapRivers", coll)
    lk = kit.MB()
    for cx, cy, a, b, t in land.lakes:
        if not (geo.point_in_poly(cx, cy, land.poly) and land.coast_dist(cx, cy) > 140):
            continue
        pts = []
        for k in range(36):
            u = k / 36 * math.tau
            wob = 1 + 0.14 * math.sin(3 * u + 1) + 0.08 * math.sin(7 * u)
            ex, ey = a * 0.8 * math.cos(u) * wob, b * 0.8 * math.sin(u) * wob
            x, y = cx + ex * math.cos(t) - ey * math.sin(t), cy + ex * math.sin(t) + ey * math.cos(t)
            for _ in range(30):      # keep water behind the beach, never out in the sea
                if geo.point_in_poly(x, y, land.poly) and land.coast_dist(x, y) > 140:
                    break
                x, y = x + (cx - x) * 0.15, y + (cy - y) * 0.15
            pts.append((x, y))
        lk.face([lk.bm.verts.new((x, y, 5.0)) for x, y in pts], "m_lagoon")
    for poly in land.lagoons:
        lk.face([lk.bm.verts.new((x, y, 5.0)) for x, y in poly], "m_lagoon")
    mmat("m_lagoon")
    lk.obj("MapLagoons", coll)


def _recolor(ob, mapping):
    for i, m in enumerate(ob.data.materials):
        if m and m.name in mapping:
            ob.data.materials[i] = mmat(mapping[m.name])


def build_vegetation(coll, land, bvh, lib_c):
    """A thick palm belt along the shore, palms along the rivers, forest on the lower slopes."""
    rng = random.Random(29)
    palms = [kit.make_palm(f"MapLibPalm{i}", lib_c, seed=40 + i, height=8.0 + 0.6 * i) for i in range(6)]
    for i, p in enumerate(palms):
        kit.hide_source(p)
    trees = [kit.make_tree(f"MapLibTree{i}", lib_c, seed=60 + i, height=6.0 + i) for i in range(4)]
    for i, t in enumerate(trees):
        kit.hide_source(t)

    def ok(x, y, pad=200):
        return (RX0 + pad < x < RX1 - pad and RY0 + pad < y < RY1 - pad and geo.point_in_poly(x, y, land.poly)
                and not land.in_lake(x, y, 1.2) and not land.in_lagoon(x, y))

    n_palm = n_tree = 0
    # palm belt: several rows deep, denser where the camera goes
    coast = geo.coast_detailed(45.0)
    for i in range(len(coast) - 1):
        (ax, ay), (bx, by) = coast[i], coast[i + 1]
        detail = in_box(ax, ay, DETAIL_BOX, 600)
        if not detail and i % 3:
            continue
        seg = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / seg, (bx - ax) / seg
        if not geo.point_in_poly(ax + nx * 300, ay + ny * 300, land.poly):
            nx, ny = -nx, -ny
        for _ in range(rng.choice((3, 4, 4, 5)) if detail else 2):
            off = rng.uniform(110, 560) if rng.random() < 0.88 else rng.uniform(560, 820)
            x, y = ax + nx * off + rng.uniform(-30, 30), ay + ny * off + rng.uniform(-30, 30)
            if not ok(x, y) or land.lagoon_dist(x, y) < 45:
                continue
            kit.instance(palms[n_palm % 6], f"MapPalm{n_palm}", coll, (x, y, ground_z(bvh, x, y) - 2),
                         rot_z=rng.uniform(0, 6.28), scale=rng.uniform(12.0, 16.0))
            n_palm += 1
    # palms lining the lowland reaches of the rivers
    for pts, _ in land.rivers:
        for (x, y, w) in pts[::2]:
            if not in_box(x, y, DETAIL_BOX) or land.coast_dist(x, y) > 1500:
                continue
            for side in (-1, 1):
                if rng.random() < 0.6:
                    px, py = x + side * rng.uniform(w + 25, w + 110), y + rng.uniform(-40, 40)
                    if ok(px, py):
                        kit.instance(palms[n_palm % 6], f"MapPalm{n_palm}", coll,
                                     (px, py, ground_z(bvh, px, py) - 2), rot_z=rng.uniform(0, 6.28),
                                     scale=rng.uniform(7.0, 10.0))
                        n_palm += 1
    # coconut groves covering the flat backwater country (S08: "thick with coconut palms")
    y = 6000.0
    while y < 10800:
        x = DETAIL_BOX[0]
        while x < DETAIL_BOX[1]:
            px, py = x + rng.uniform(-35, 35), y + rng.uniform(-35, 35)
            if ok(px, py):
                d = land.coast_dist(px, py)
                if d > 140 and rng.random() < 0.55 * land.lowland(px, py, d) and land.lagoon_dist(px, py) > 40:
                    kit.instance(palms[n_palm % 6], f"MapPalm{n_palm}", coll, (px, py, ground_z(bvh, px, py) - 2),
                                 rot_z=rng.uniform(0, 6.28), scale=rng.uniform(11.0, 15.0))
                    n_palm += 1
            x += 85.0
        y += 85.0
    # forest patches on the lower slopes and in the valleys
    step = 62.0
    y = DETAIL_BOX[2]
    while y < DETAIL_BOX[3]:
        x = DETAIL_BOX[0]
        while x < DETAIL_BOX[1]:
            px, py = x + rng.uniform(-25, 25), y + rng.uniform(-25, 25)
            if ok(px, py):
                d = land.coast_dist(px, py)
                if 1600 < d < 5000:
                    z = ground_z(bvh, px, py)
                    dens = _nz(px, py, 700, 9.4) * 0.5 + (0.55 if land.river_dist(px, py, 400) < 300 else 0.0)
                    if z < 260 and dens > 0.62:
                        kit.instance(trees[n_tree % 4], f"MapTree{n_tree}", coll, (px, py, z - 3),
                                     rot_z=rng.uniform(0, 6.28), scale=rng.uniform(7.0, 10.0))
                        n_tree += 1
            x += step
        y += step
    return n_palm, n_tree


def build_ships(coll, placements):
    src = [kit.make_ship(f"MapShipSrc{i}", coll, length=36 + 3 * i, seed=50 + i) for i in range(2)]
    for s in src:
        kit.hide_source(s)
    for i, (x, y, rot) in enumerate(placements):
        ob = kit.instance(src[i % 2], f"MapShip{i}", coll, (x, y, 0.0), rot_z=math.radians(rot), scale=6.0)
        rng = random.Random(70 + i)
        fx, fy = -math.sin(math.radians(rot)), math.cos(math.radians(rot))
        f, k = 1 + rng.randint(0, 12), 0
        while f <= 900:                       # drift forward, rock and bob on the swell
            s = 1 if k % 2 == 0 else -1
            ob.location = (x + fx * f * 0.12, y + fy * f * 0.12, 4.0 * s)
            ob.rotation_euler = (math.radians(3.0 * s), math.radians(-2.0 * s), math.radians(rot + 1.5 * s))
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)
            f += rng.randint(20, 28)
            k += 1


def build_colachel_mark(coll, lib_c, bvh):
    """The Dutch stockade and a red tent at Colachel, as in the Flow reference."""
    x, y = 120.0, 160.0
    z = ground_z(bvh, x, y)
    st = kit.make_stockade("MapStockade", coll, (0, 0), -16.7, 15.0, 12.0, lambda a, b: 0.3, gate=3.5, seed=8)
    st.location = (x, y, z)
    st.scale = (9, 9, 9)
    tent = kit.make_cone_tent("MapRedTentSrc", lib_c, r=2.2, h=3.4)
    tent.data.materials[0] = mmat("m_red")
    kit.hide_source(tent)
    kit.instance(tent, "MapRedTent", coll, (x + 260, y + 40, ground_z(bvh, x + 260, y + 40) - 1), scale=11)


def cloud_material():
    """Soft volumetric cloud: noisy density inside a spherical falloff."""
    m = bpy.data.materials.get("MapCloudVol")
    if m:
        return m
    m = bpy.data.materials.new("MapCloudVol")
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.2
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.6
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.24
    ramp.inputs["From Max"].default_value = 0.42
    ramp.inputs["To Max"].default_value = 0.06
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], grad.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mul.inputs[0])
    nt.links.new(grad.outputs["Fac"], mul.inputs[1])
    nt.links.new(mul.outputs["Value"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], vol.inputs["Density"])
    vol.inputs["Color"].default_value = (*kit.srgb_to_linear((0.86, 0.87, 0.90)), 1)
    vol.inputs["Anisotropy"].default_value = 0.2
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return m


def build_clouds(coll, cam, open_frames):
    """Soft volumetric storm clouds that cover the opening frame (for the dissolve from the
    beach), then part to the corners (K08a). They ride with the camera, ~2 km below it,
    where the frame is only ~2.4 x 1.4 km across."""
    rng = random.Random(41)
    f0, f1 = open_frames
    m = cloud_material()
    rig = bpy.data.objects.new("CloudRig", None)
    coll.objects.link(rig)
    c = rig.constraints.new("COPY_LOCATION")
    c.target = cam
    cx = cy = 0.0
    for i in range(24):
        mb = kit.MB()
        mb.ico(kit.Matrix.Identity(4), "MapCloudVol", r=1.0, sub=3)
        ob = mb.obj(f"MapCloud{i}", coll)
        ob.data.materials[0] = m
        ob.visible_shadow = False
        ob.parent = rig
        a = i / 24 * math.tau + rng.uniform(-0.2, 0.2)
        outer = i % 2 == 1                   # outer ring covers the corners at the start
        r0 = rng.uniform(800, 1300) if outer else rng.uniform(0, 450)
        r1 = rng.uniform(2100, 2600) if outer else rng.uniform(1500, 2000)
        z = -rng.uniform(1800, 2300)
        rx, ry, rz = rng.uniform(1000, 1300), rng.uniform(700, 950), rng.uniform(240, 340)
        start = (cx + r0 * math.cos(a), cy + r0 * math.sin(a) * 0.6, z)
        end = (cx + r1 * math.cos(a), cy + r1 * math.sin(a) * 0.6, z + 120)
        gone = (cx + r1 * 1.9 * math.cos(a), cy + r1 * 1.9 * math.sin(a) * 0.6, z + 400)
        ob.rotation_euler[2] = rng.uniform(0, 6.28)
        for f, loc, k in ((f0, start, 1.0), (f0 + 12, start, 1.0), (f1, end, 0.9), (f1 + 60, gone, 0.0)):
            ob.location = loc
            ob.scale = (rx * k + 1e-3, ry * k + 1e-3, rz * k + 1e-3)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("scale", frame=f)
    ee = bpy.context.scene.eevee
    ee.volumetric_end = 6000.0
    ee.volumetric_start = 50.0
    ee.volumetric_tile_size = "4"
    ee.volumetric_samples = 64


def setup_light():
    w = bpy.data.worlds.new("MapSky")
    bpy.context.scene.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*kit.srgb_to_linear((0.78, 0.86, 1.0)), 1)
    bg.inputs["Strength"].default_value = 0.5
    ld = bpy.data.lights.new("MapSun", "SUN")
    ld.energy = 6.5
    ld.color = (1.0, 0.93, 0.80)
    ld.angle = math.radians(3)
    sun = bpy.data.objects.new("MapSun", ld)
    bpy.context.scene.collection.objects.link(sun)
    # low sun from the upper left (north-west): long shadows down-right, as in the Flow refs
    sun.rotation_euler = Vector((0.62, -0.52, -0.45)).normalized().to_track_quat("-Z", "Y").to_euler()


def build_map_world(frames=600):
    coll = kit.new_collection("Map")
    lib_c = kit.new_collection("MapLibrary")
    land = Land()
    _, bvh = build_land(coll, land)
    build_sea(coll, land, frames)
    build_water(coll, land, bvh)
    n_palm, n_tree = build_vegetation(coll, land, bvh, lib_c)
    build_colachel_mark(coll, lib_c, bvh)
    build_ceylon(coll, lib_c)
    setup_light()
    print("map world:", n_palm, "palms,", n_tree, "trees,", len(land.lakes), "lakes/ponds")
    return coll, land, bvh


# ------------------------------------------------------------- kingdoms (S10)
# The small kingdoms of the coast in the early 1700s: (name, lat, lon, wall colour).
# Plain coloured flags only (no symbols, no text).
KINGDOMS = [
    ("Kochi", 9.80, 76.56, (0.93, 0.92, 0.88)),       # the raja's seat, inland of the Dutch fort
    ("Vadakkumkur", 9.74, 76.50, (0.55, 0.42, 0.70)),
    ("Thekkumkur", 9.58, 76.60, (0.42, 0.65, 0.48)),
    ("Purakkad", 9.36, 76.40, (0.78, 0.45, 0.30)),
    ("Kayamkulam", 9.17, 76.52, (0.86, 0.70, 0.30)),
    ("Kollam", 8.89, 76.63, (0.55, 0.70, 0.86)),
    ("Kottarakkara", 9.00, 76.78, (0.82, 0.55, 0.62)),
    ("Attingal", 8.69, 76.83, (0.95, 0.80, 0.55)),
    ("Travancore", 8.25, 77.33, (0.80, 0.22, 0.18)),
]


INLAND = {"Kottarakkara", "Thekkumkur", "Kochi"}


def make_fort(name, collection, wall_rgb, seed=0):
    """A small walled kingdom seat: square wall, round corner towers, a gatehouse, a
    palace with a tiled hip roof, and a flag pole with a plain flag in the wall colour.
    About 30 m across at scale 1; scale it up for the map."""
    rng = random.Random(seed)
    wall = f"fort_{name}"
    kit.mat(wall, wall_rgb)
    kit.mat("fort_roof", (0.70, 0.30, 0.18))
    kit.mat("fort_stone", (0.62, 0.58, 0.52))
    mb = kit.MB(bevel=0.08)
    h = 15.0
    mb.box(kit.T(0, 0, 0.4) @ kit.S(32, 32, 0.8), "fort_stone")
    for sx, sy, w, d in ((0, -h, 31, 3.0), (0, h, 31, 3.0), (-h, 0, 3.0, 31), (h, 0, 3.0, 31)):
        mb.box(kit.T(sx, sy, 2.8) @ kit.S(w, d, 4.8), wall)
        n = int(max(w, d) / 2.2)
        for k in range(n):                                       # crenellations
            t = (k + 0.5) / n - 0.5
            px, py = (sx + t * w, sy) if w > d else (sx, sy + t * d)
            mb.box(kit.T(px, py, 5.55) @ kit.S(1.0 if w > d else 3.0, 3.0 if w > d else 1.0, 0.8), wall)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cone(kit.T(sx * h, sy * h, 3.8), wall, segments=10, r1=3.4, r2=3.1, depth=7.6)
            mb.cone(kit.T(sx * h, sy * h, 8.9), wall, segments=10, r1=3.8, r2=0.3, depth=2.8)
    mb.box(kit.T(0, -h, 3.6) @ kit.S(6, 3.4, 6.4), wall)                    # gatehouse
    mb.box(kit.T(0, -h - 0.9, 1.6) @ kit.S(2.2, 1.8, 3.0), "dark")
    mb.box(kit.T(0, 3, 3.0) @ kit.S(12, 8, 5.0), wall)                       # palace
    mb.cone(kit.T(0, 3, 6.8) @ kit.S(1, 8 / 12, 1) @ kit.Rz(math.pi / 4), "fort_roof", segments=4,
            r1=9.0, r2=1.2, depth=3.0)
    mb.box(kit.T(0, 0, 0.9) @ kit.S(27, 27, 0.2), wall)                      # courtyard in the colour
    for k in range(3):
        mb.box(kit.T(-4.5 + k * 4.5, -3.05, 2.6) @ kit.S(1.4, 0.2, 2.2), "dark")
    mb.seg((6, 6, 5), (6, 6, 15), 0.25, 0.2, "post", sides=6)                 # flag pole
    mb.box(kit.T(8.2, 6, 13.8) @ kit.S(4.2, 0.25, 2.4), wall)                 # plain flag
    for k in range(rng.randint(3, 5)):                                        # houses inside the walls
        x, y = rng.uniform(-10, 10), rng.uniform(-11, -5)
        mb.box(kit.T(x, y, 1.6) @ kit.S(3, 2.6, 2.4), "wall")
        mb.cone(kit.T(x, y, 3.6) @ kit.Rz(math.pi / 4), "thatch", segments=4, r1=2.4, r2=0.1, depth=1.6)
    return mb.obj(name, collection)


def build_kingdoms(coll, bvh, appear_frames, scale=11.0):
    """One coloured fort per kingdom along the coast; they pop up one after another
    (south to north) between appear_frames[0] and appear_frames[1]."""
    f0, f1 = appear_frames
    order = sorted(KINGDOMS, key=lambda k: k[1])
    forts = []
    coast = geo.coast_detailed(100.0)
    poly = geo.land_polygon_detailed(60.0)
    for i, (name, lat, lon, rgb) in enumerate(order):
        x, y = geo.xy(lat, lon)
        if name in INLAND:                     # hill kingdoms stay where they were
            z = ground_z(bvh, x, y)
            ob = make_fort(f"Fort_{name}", coll, rgb, seed=i)
            ob.location = (x, y, z - 1)
            t = f0 + (f1 - f0) * i / max(1, len(order) - 1)
            for f, s in ((t - 1, 0.0), (t + 8, scale * 1.15), (t + 14, scale)):
                ob.scale = (s, s, s)
                ob.keyframe_insert("scale", frame=round(f))
            forts.append(ob)
            continue
        # stand each coastal fort on the strip, just behind the beach (as in K13)
        _, si = geo.dist_to_polyline(x, y, coast)
        (ax, ay), (bx, by) = coast[si], coast[si + 1]
        L = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / L, (bx - ax) / L
        if not geo.point_in_poly(ax + nx * 300, ay + ny * 300, poly):
            nx, ny = -nx, -ny
        x, y = (ax + bx) / 2 + nx * 560, (ay + by) / 2 + ny * 560
        z = ground_z(bvh, x, y)
        ob = make_fort(f"Fort_{name}", coll, rgb, seed=i)
        ob.location = (x, y, z - 1)
        ob.rotation_euler[2] = random.Random(i).uniform(-0.3, 0.3)
        t = f0 + (f1 - f0) * i / max(1, len(order) - 1)
        for f, s in ((t - 1, 0.0), (t + 8, scale * 1.15), (t + 14, scale)):
            ob.scale = (s, s, s)                 # invisible until it pops up
            ob.keyframe_insert("scale", frame=round(f))
        forts.append(ob)
    return forts


# ---------------------------------------------------------- Dutch Kochi (S11)
FORT_KOCHI = (9.966, 76.243)     # the Dutch fort at Kochi (taken from the Portuguese, 1663)


def make_star_fort(name, collection, wall_mat):
    """Five-pointed star fort (as in Flow ref K14_v2): a thick star-shaped rampart with a
    sand glacis and a moat ring outside, parade ground, barracks and a flag pole with a
    plain flag. About 70 m across at scale 1. Rampart and buildings use `wall_mat`."""
    mb = kit.MB(bevel=0.12)
    kit.PALETTE["m_lagoon"] = (0.26, 0.60, 0.68)
    kit.mat("m_lagoon", (0.26, 0.60, 0.68))
    kit.PALETTE["fort_roof"] = (0.70, 0.30, 0.18)
    kit.mat("fort_roof", (0.70, 0.30, 0.18))

    def star(r_out, r_in, rot=math.pi / 2):
        pts = []
        for k in range(10):
            r = r_out if k % 2 == 0 else r_in
            a = rot + k * math.pi / 5
            pts.append(Vector((r * math.cos(a), r * math.sin(a), 0)))
        return pts

    def slab(outer, inner, z0, z1, m):
        ob = [mb.bm.verts.new((p.x, p.y, z0)) for p in outer]
        ot = [mb.bm.verts.new((p.x, p.y, z1)) for p in outer]
        ib = [mb.bm.verts.new((p.x, p.y, z0)) for p in inner]
        it = [mb.bm.verts.new((p.x, p.y, z1)) for p in inner]
        n = len(outer)
        for k in range(n):
            j = (k + 1) % n
            mb.face([ot[k], ot[j], it[j], it[k]], m)            # top of the wall
            mb.face([ob[k], ob[j], ot[j], ot[k]], m)            # outer face
            mb.face([it[k], it[j], ib[j], ib[k]], m)            # inner face

    slab(star(46, 30), star(38, 24), 0.2, 0.8, "m_lagoon")        # moat
    slab(star(38, 24), star(35, 21), 0.2, 1.4, "sand")            # glacis
    slab(star(35, 21), star(29, 16), 0.4, 6.0, wall_mat)          # rampart
    inner = star(29, 16)
    mb.face([mb.bm.verts.new((p.x, p.y, 0.9)) for p in inner], "sand")   # parade ground
    for x, y, w, d in ((-7, -4, 12, 6), (8, 2, 6, 12), (-2, 9, 10, 6)):  # barracks and hall
        mb.box(kit.T(x, y, 3.0) @ kit.S(w, d, 4.2), wall_mat)
        mb.cone(kit.T(x, y, 6.2) @ kit.S(1, d / w, 1) @ kit.Rz(math.pi / 4), "fort_roof", segments=4,
                r1=w * 0.72, r2=0.6, depth=2.4)
    mb.seg((0, -12, 1), (0, -12, 18), 0.35, 0.3, "post", sides=6)
    mb.box(kit.T(3.0, -12, 16.4) @ kit.S(5.6, 0.3, 3.2), wall_mat)       # plain flag
    return mb.obj(name, collection)


def build_dutch_kochi(coll, bvh, turn_frames, ships_c, scale=14.0):
    """The Dutch fort at Kochi, stone-coloured until turn_frames, then Dutch orange,
    with Dutch ships moored off it."""
    m = bpy.data.materials.new("DutchOrange")
    try:
        m.use_nodes = True
    except Exception:
        pass
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.85
    kit.mat("fort_roof", (0.70, 0.30, 0.18))
    kit.mat("fort_stone", (0.62, 0.58, 0.52))
    for f, rgb in ((turn_frames[0], (0.78, 0.74, 0.66)), (turn_frames[1], (0.96, 0.46, 0.10))):
        bsdf.inputs["Base Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
        bsdf.inputs["Base Color"].keyframe_insert("default_value", frame=f)
    mb_name = "DutchOrange"
    x, y = geo.xy(*FORT_KOCHI)
    fort = make_star_fort("DutchFortKochi", coll, mb_name)
    fort.data.materials[[mm.name for mm in fort.data.materials].index("DutchOrange")] = m
    fort.location = (x + 120, y + 60, ground_z(bvh, x + 120, y + 60) - 1)
    fort.rotation_euler[2] = math.radians(12)
    fort.scale = (scale, scale, scale)
    src = bpy.data.objects.get("MapShipSrc0")
    for i, (dx, dy, rot) in enumerate(((-700, -200, 170), (-950, 260, 190), (-620, 520, 160))):
        ob = kit.instance(src, f"DutchShipKochi{i}", ships_c, (x + dx, y + dy, 0.0), rot_z=math.radians(rot), scale=6.0)
        rng = random.Random(90 + i)
        f, k = 1, 0
        while f <= 2400:
            s = 1 if k % 2 == 0 else -1
            ob.location.z = 3.0 * s
            ob.rotation_euler = (math.radians(2.5 * s), math.radians(-1.5 * s), math.radians(rot + s))
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)
            f += rng.randint(20, 28)
            k += 1
    return fort


# ------------------------------------------------------ Travancore grows (S16)
TRAVANCORE_RED = (0.86, 0.16, 0.12)


TERRITORY_WASH = (0.98, 0.47, 0.45)


def territory_material(name, rgb, show_frames, alpha=0.5):
    """Translucent tint laid over the land; fades in over show_frames."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        m.blend_method = "BLEND"
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
    bsdf.inputs["Roughness"].default_value = 0.9
    # a little self-light so the wash stays pink in the hill shadows instead of going brown
    bsdf.inputs["Emission Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
    bsdf.inputs["Emission Strength"].default_value = 0.35
    a = bsdf.inputs["Alpha"]
    for f, v in ((show_frames[0], 0.0), (show_frames[1], alpha)):
        a.default_value = v
        a.keyframe_insert("default_value", frame=f)
    return m


def build_territory(coll, land_ob, bvh, stages, sea_test=None):
    """Travancore's land, tinted red stage by stage. stages: [(name, test(x, y) -> bool,
    (f0, f1))]; each stage tints the land faces that pass its test and not an earlier one,
    and draws a red border ribbon along its northern edge while it is the frontier."""
    me = land_ob.data
    taken = set()
    borders = []
    for si, (name, test, frames) in enumerate(stages):
        bm = bmesh.new()
        vmap = {}
        for p in me.polygons:
            if p.index in taken:
                continue
            c = p.center
            if not test(c.x, c.y):
                continue
            taken.add(p.index)
            vs = []
            for vi in p.vertices:
                if vi not in vmap:
                    co = me.vertices[vi].co
                    vmap[vi] = bm.verts.new((co.x, co.y, co.z + 6.0))
                vs.append(vmap[vi])
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
        if sea_test is not None:                 # flat wash over the sea inside the frontier
            step = 120.0
            y = -6000.0
            while y < 8000:
                x = -9000.0
                while x < 8000:
                    cx, cy = x + step / 2, y + step / 2
                    if test(cx, cy) and sea_test(cx, cy) and (si == 0 or not stages[si - 1][1](cx, cy)):
                        vs = [bm.verts.new((x + dx, y + dy, 75.0)) for dx, dy in ((0, 0), (step, 0), (step, step), (0, step))]
                        bm.faces.new(vs)
                    x += step
                y += step
        tme = bpy.data.meshes.new(f"Territory_{name}")
        bm.to_mesh(tme)
        bm.free()
        tme.materials.append(territory_material(f"TerritoryMat_{name}", TERRITORY_WASH, frames))
        ob = bpy.data.objects.new(f"Territory_{name}", tme)
        ob.visible_shadow = False
        coll.objects.link(ob)
    return borders


def build_border(coll, bvh, pts, frames_on, frames_off=None, name="Border"):
    """A bold red frontier ribbon draped over the land along pts [(x, y)]; it grows in
    (scale) at frames_on and shrinks away at frames_off."""
    mb = kit.MB()
    kit.mat("border_red", (0.72, 0.10, 0.08))
    rows = []
    for i, (x, y) in enumerate(pts):
        j = min(i + 1, len(pts) - 1)
        k = max(i - 1, 0)
        tx, ty = pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L * 45, tx / L * 45
        za = ground_z(bvh, x + nx, y + ny) + 9
        zb = ground_z(bvh, x - nx, y - ny) + 9
        rows.append((mb.bm.verts.new((x + nx, y + ny, za)), mb.bm.verts.new((x - nx, y - ny, zb))))
    for (a0, b0), (a1, b1) in zip(rows, rows[1:]):
        mb.face([a0, a1, b1, b0], "border_red")
    ob = mb.obj(name, coll)
    ob.visible_shadow = False
    keys = [(frames_on[0], 0.0), (frames_on[1], 1.0)]
    if frames_off:
        keys += [(frames_off[0], 1.0), (frames_off[1], 0.0)]
    for f, s in keys:
        ob.hide_render = s == 0.0
        ob.keyframe_insert("hide_render", frame=f)
    return ob


def recolor_fort(name, rgb, frames):
    """Animate a kingdom fort's wall colour to rgb over frames (it is taken)."""
    m = bpy.data.materials.get(f"fort_Fort_{name}")         # make_fort names it after the object
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    old = tuple(bsdf.inputs["Base Color"].default_value)
    for f, c in ((frames[0], old), (frames[1], (*kit.srgb_to_linear(rgb), 1))):
        bsdf.inputs["Base Color"].default_value = c
        bsdf.inputs["Base Color"].keyframe_insert("default_value", frame=f)


# ================================================================ S19: Ceylon & Dutch Galleon
CEYLON_CENTER = (15000.0, -6000.0)


def build_ceylon(coll, lib_c):
    """Faceted Ceylon island with green highlands, sand beach, turquoise shallow rim,
    Adam's bridge, and the Dutch star fort on the west coast. Matches Flow ref K25."""
    rng = random.Random(55)
    cx, cy = CEYLON_CENTER

    # 1. Island polygon and height mesh
    verts_2d = []
    perim_pts = []
    for k in range(28):
        u = k / 28 * math.tau
        r = 3800.0 * (1.0 - 0.35 * math.sin(u)) + rng.uniform(-80, 80)
        px = cx + r * math.cos(u) * 0.90
        py = cy + r * math.sin(u) * 1.35
        perim_pts.append((px, py))
        verts_2d.append(Vector((px, py)))

    nb = len(verts_2d)
    step = 260.0
    for y in range(int(cy - 5500), int(cy + 4200), int(step)):
        for x in range(int(cx - 3600), int(cx + 3600), int(step)):
            px = x + rng.uniform(-0.35, 0.35) * step
            py = y + rng.uniform(-0.35, 0.35) * step
            if geo.point_in_poly(px, py, perim_pts):
                verts_2d.append(Vector((px, py)))

    out = delaunay_2d_cdt(verts_2d, [], [list(range(nb))], 1, 0.01)
    vco, faces = out[0], out[2]

    bm = bmesh.new()
    bv = []
    for v in vco:
        dx = (v.x - (cx + 300)) / 2800.0
        dy = (v.y - (cy - 500)) / 3800.0
        d_sq = dx * dx + dy * dy
        if d_sq < 1.0:
            h = 4.0 + 980.0 * ((1.0 - d_sq) ** 1.4) + 60.0 * _nz(v.x, v.y, 800, 1.2)
        else:
            h = 4.0
        bv.append(bm.verts.new((v.x, v.y, h)))

    for f in faces:
        if len(f) < 3:
            continue
        try:
            bm.faces.new([bv[i] for i in f])
        except ValueError:
            continue

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("MapCeylon")
    bm.to_mesh(me)
    bm.free()

    for m in ("m_sand", "m_g1", "m_g2", "m_g3", "m_earth"):
        me.materials.append(mmat(m))

    for p in me.polygons:
        p.use_smooth = False
        cz = p.center.z
        if cz < 35.0:
            p.material_index = 0  # sand
        elif cz < 280.0:
            p.material_index = 1  # g1
        elif cz < 550.0:
            p.material_index = 2  # g2
        elif cz < 750.0:
            p.material_index = 3  # g3
        else:
            p.material_index = 4  # earth

    ob = bpy.data.objects.new("MapCeylon", me)
    coll.objects.link(ob)

    # 2. Turquoise shallow water halo around Ceylon
    halo_bm = bmesh.new()
    outer_halo = []
    for px, py in perim_pts:
        nx, ny = (px - cx) / 3800.0, (py - cy) / 5000.0
        L = math.hypot(nx, ny) or 1.0
        outer_halo.append((px + (nx / L) * 550.0, py + (ny / L) * 550.0))

    r_in = [halo_bm.verts.new((px, py, 1.2)) for px, py in perim_pts]
    r_out = [halo_bm.verts.new((px, py, 0.6)) for px, py in outer_halo]
    n = len(perim_pts)
    for i in range(n):
        j = (i + 1) % n
        halo_bm.faces.new([r_in[i], r_in[j], r_out[j], r_out[i]])

    bmesh.ops.triangulate(halo_bm, faces=halo_bm.faces[:])
    halo_me = bpy.data.meshes.new("CeylonShallows")
    halo_bm.to_mesh(halo_me)
    halo_bm.free()
    halo_me.materials.append(mmat("m_lagoon"))
    halo_ob = bpy.data.objects.new("CeylonShallows", halo_me)
    halo_ob.visible_shadow = False
    coll.objects.link(halo_ob)

    # 3. Adam's Bridge (shoals connecting Rameshwaram to Mannar)
    bridge_mb = kit.MB()
    shoal_coords = [
        (8200, 900), (9100, 450), (9900, 50), (10800, -400),
        (11600, -850), (12400, -1350)
    ]
    for i, (sx, sy) in enumerate(shoal_coords):
        bridge_mb.cone(kit.T(sx, sy, 2.0) @ kit.S(260, 160, 3.0), "m_sand", segments=8, r1=1.0, r2=0.8, depth=1.0)
        bridge_mb.cone(kit.T(sx, sy, 0.8) @ kit.S(400, 260, 1.0), "m_lagoon", segments=8, r1=1.0, r2=0.8, depth=0.5)
    bridge_ob = bridge_mb.obj("AdamsBridge", coll)
    bridge_ob.data.materials.append(mmat("m_sand"))
    bridge_ob.data.materials.append(mmat("m_lagoon"))

    # 4. Dutch Star Fort at Ceylon (Galle / Colombo on west coast)
    kit.PALETTE["DutchOrange"] = (0.96, 0.46, 0.10)
    kit.mat("DutchOrange", (0.96, 0.46, 0.10))
    fort_x, fort_y = 12200.0, -5800.0
    fort = make_star_fort("DutchFortCeylon", coll, "DutchOrange")
    fort.location = (fort_x, fort_y, 4.0)
    fort.rotation_euler[2] = math.radians(25)
    fort.scale = (14.0, 14.0, 14.0)

    # Harbor jetty & small moored ships
    j_mb = kit.MB(bevel=0.05)
    j_mb.box(kit.T(fort_x - 300, fort_y - 120, 2.5) @ kit.S(420, 45, 3.0), "plank")
    for k in range(5):
        j_mb.cone(kit.T(fort_x - 120 - k * 80, fort_y - 120, 0.5), "post", segments=6, r1=6, r2=5, depth=4.5)
    j_ob = j_mb.obj("CeylonJetty", coll)
    j_ob.data.materials.append(kit.mat("plank", kit.PALETTE["plank"]))
    j_ob.data.materials.append(kit.mat("post", kit.PALETTE["post"]))

    # 5. Palms around Ceylon coast
    palm_src = bpy.data.objects.get("MapLibPalm0")
    if palm_src:
        for i in range(55):
            u = rng.uniform(0, math.tau)
            r = rng.uniform(2800, 3600) * (1.0 - 0.35 * math.sin(u))
            px = cx + r * math.cos(u) * 0.90 + rng.uniform(-60, 60)
            py = cy + r * math.sin(u) * 1.35 + rng.uniform(-60, 60)
            kit.instance(palm_src, f"CeylonPalm{i}", coll, (px, py, 3.5),
                         rot_z=rng.uniform(0, 6.28), scale=rng.uniform(11.0, 15.0))

    return ob


def make_sailing_galleon(name, coll):
    """Detailed Dutch 3-masted war galleon with billowing sails and Dutch flag (Flow ref K25)."""
    mb = kit.MB(bevel=0.08)
    # Hull
    mb.box(kit.T(0, 0, 1.8) @ kit.S(16.0, 48.0, 4.2), "post")
    mb.box(kit.T(0, -18.0, 3.4) @ kit.S(15.5, 14.0, 5.0), "post")   # High sterncastle
    mb.cone(kit.T(0, 24.0, 2.2) @ kit.Rx(0.2) @ kit.S(0.6, 1.0, 1.0), "post", segments=6, r1=7.5, r2=1.0, depth=14.0) # Bow
    # Decks
    mb.box(kit.T(0, 0, 3.8) @ kit.S(14.0, 42.0, 0.4), "plank")
    # 3 Masts: Fore, Main, Mizzen
    for my, mh, mr in ((14.0, 32.0, 0.8), (0.0, 38.0, 0.9), (-14.0, 28.0, 0.7)):
        mb.cone(kit.T(0, my, mh / 2 + 3.0), "post", segments=8, r1=mr, r2=mr * 0.6, depth=mh)
        # 2 Cross-yards with billowing sails per mast
        for sy, sh, sw, sd in ((0, mh * 0.52 + 3.0, 18.0, 7.5), (0, mh * 0.82 + 3.0, 14.0, 6.0)):
            mb.box(kit.T(0, my, sh) @ kit.S(sw, 0.6, 0.6), "post") # Spar
            # Billowing canvas sail (curved cone segment)
            mb.cone(kit.T(0, my + 1.2, sh - sd / 2) @ kit.Rx(-0.18) @ kit.S(1.0, 0.4, 1.0),
                    "canvas", segments=8, r1=sw * 0.48, r2=sw * 0.42, depth=sd)
    # Bowsprit
    mb.seg((0, 24.0, 3.5), (0, 38.0, 8.5), 0.7, 0.4, "post", sides=6)
    # Dutch orange flag atop main mast
    mb.box(kit.T(3.2, 0.0, 41.5) @ kit.S(6.0, 0.2, 3.2), "gold")
    # Wake mesh (foam trailing from stern)
    mb.cone(kit.T(0, -38.0, 0.2) @ kit.Rx(math.pi / 2) @ kit.S(0.4, 1.0, 1.0), "canvas",
            segments=4, r1=8.0, r2=1.0, depth=26.0)

    ob = mb.obj(name, coll)
    for m in ("post", "plank", "canvas", "gold"):
        ob.data.materials.append(kit.mat(m, kit.PALETTE[m]))
    return ob


def build_s19_fleet(coll, frames):
    """Dutch fleet sailing from Ceylon across Gulf of Mannar toward Kerala (S19, K25)."""
    f0, f1 = frames
    galleon = make_sailing_galleon("S19Galleon", coll)
    galleon.scale = (16.0, 16.0, 16.0)

    # Route: departs Ceylon (11800, -4800) -> Gulf of Mannar (5200, -1600)
    start_pos = (11800.0, -4800.0, 2.0)
    end_pos = (4800.0, -1400.0, 2.0)
    heading = math.radians(-118)

    galleon.rotation_euler = (0, 0, heading)
    galleon.location = start_pos
    galleon.keyframe_insert("location", frame=f0)
    galleon.location = end_pos
    galleon.keyframe_insert("location", frame=f1)

    # Gentle wave rock
    rng = random.Random(77)
    f = f0
    while f <= f1:
        s = rng.choice([-1, 1])
        galleon.rotation_euler = (math.radians(2.2 * s), math.radians(1.4 * s), heading + math.radians(1.0 * s))
        galleon.keyframe_insert("rotation_euler", frame=f)
        f += 24

    # Visibility: active only during S19
    galleon.hide_render = True
    galleon.keyframe_insert("hide_render", frame=1)
    galleon.keyframe_insert("hide_render", frame=f0 - 1)
    galleon.hide_render = False
    galleon.keyframe_insert("hide_render", frame=f0)
    galleon.keyframe_insert("hide_render", frame=f1)
    galleon.hide_render = True
    galleon.keyframe_insert("hide_render", frame=f1 + 1)
    return galleon


# ================================================================ S24: Fort Kochi Mobilization
def build_s24_mobilization(coll, frames):
    """Giant orange VOC war banner atop Fort Kochi and marching Dutch column (S24, K31)."""
    f0, f1 = frames
    kx, ky = geo.xy(*FORT_KOCHI)
    kx += 120
    ky += 60

    # 1. Giant Orange VOC War Banner on flagpole
    b_mb = kit.MB(bevel=0.08)
    b_mb.cone(kit.T(kx + 10, ky + 10, 45.0), "post", segments=8, r1=1.5, r2=0.8, depth=90.0) # Tall mast
    # Billowing orange war banner
    b_mb.box(kit.T(kx + 45, ky + 10, 78.0) @ kit.S(70.0, 1.5, 36.0), "gold")
    banner_ob = b_mb.obj("VOCWarBanner", coll)
    banner_ob.data.materials.append(kit.mat("post", kit.PALETTE["post"]))
    banner_ob.data.materials.append(kit.mat("gold", (0.96, 0.46, 0.10))) # Dutch orange

    # 2. Marching Dutch Column winding south out of the fort
    # Path down the coastal road: from fort (kx, ky-60) south along the coast
    col_mb = kit.MB(bevel=0.04)
    march_pts = [
        (kx, ky - 60), (kx - 80, ky - 250), (kx - 120, ky - 500),
        (kx - 100, ky - 800), (kx - 60, ky - 1100), (kx, ky - 1400)
    ]
    # Place rows of 3 blue soldier counters along the path
    rng = random.Random(88)
    n_soldiers = 0
    for i in range(len(march_pts) - 1):
        p0, p1 = march_pts[i], march_pts[i + 1]
        steps = 14
        for s in range(steps):
            t = s / steps
            mx = p0[0] + (p1[0] - p0[0]) * t
            my = p0[1] + (p1[1] - p0[1]) * t
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L, dx / L
            for lane in (-18, 0, 18):
                px = mx + nx * lane + rng.uniform(-3, 3)
                py = my + ny * lane + rng.uniform(-3, 3)
                # Blue coat, white breeches, black tricorn
                col_mb.box(kit.T(px, py, 9.0) @ kit.S(12.0, 12.0, 18.0), "coat_blue")
                col_mb.box(kit.T(px, py, 20.0) @ kit.S(9.0, 9.0, 6.0), "black")
                n_soldiers += 1

    march_ob = col_mb.obj("DutchMarchColumn", coll)
    march_ob.data.materials.append(kit.mat("coat_blue", (0.16, 0.32, 0.62)))
    march_ob.data.materials.append(kit.mat("black", (0.12, 0.12, 0.14)))

    for ob in (banner_ob, march_ob):
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.keyframe_insert("hide_render", frame=f0 - 1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f0)
        ob.keyframe_insert("hide_render", frame=f1)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=f1 + 1)


# ================================================================ S28: Frontier Battle Clash
def build_s28_frontier_clash(coll, bvh, frames):
    """Push-and-pull battle frontlines: Dutch & Travancore army blocks, tactical arrows,
    and battle smoke puffs (S28, K35)."""
    f0, f1 = frames
    fx, fy = -2500.0, 3200.0  # Coastal sand plain near Kollam
    fz = ground_z(bvh, fx, fy, default=4.0)

    mb = kit.MB(bevel=0.06)

    # 1. Northern Dutch army block (blue & orange)
    for row in range(5):
        for col in range(12):
            px = fx - 160 + col * 28
            py = fy + 240 + row * 24
            pz = ground_z(bvh, px, py, default=fz)
            mb.box(kit.T(px, py, pz + 8.0) @ kit.S(14.0, 12.0, 16.0), "coat_blue")
            mb.box(kit.T(px, py, pz + 18.0) @ kit.S(10.0, 10.0, 6.0), "gold")
    # Dutch orange camp banner
    mb.cone(kit.T(fx, fy + 380, fz + 24.0), "post", segments=6, r1=1.0, r2=0.6, depth=48.0)
    mb.box(kit.T(fx + 20, fy + 380, fz + 42.0) @ kit.S(36.0, 1.0, 20.0), "gold")

    # 2. Southern Travancore army block (red & white)
    for row in range(5):
        for col in range(12):
            px = fx - 160 + col * 28
            py = fy - 240 - row * 24
            pz = ground_z(bvh, px, py, default=fz)
            mb.box(kit.T(px, py, pz + 8.0) @ kit.S(14.0, 12.0, 16.0), "carpet_red")
            mb.box(kit.T(px, py, pz + 18.0) @ kit.S(10.0, 10.0, 6.0), "gold")
    # Travancore red camp banner
    mb.cone(kit.T(fx, fy - 380, fz + 24.0), "post", segments=6, r1=1.0, r2=0.6, depth=48.0)
    mb.box(kit.T(fx + 20, fy - 380, fz + 42.0) @ kit.S(36.0, 1.0, 20.0), "carpet_red")

    # 3. Tactical push-pull arrows drawn on the sand (matching K35!)
    # Orange arrow pointing south into Travancore
    for t_step in range(12):
        ay = fy + 160 - t_step * 24
        ax = fx - 50 + math.sin(t_step * 0.4) * 45
        az = ground_z(bvh, ax, ay, default=fz) + 3.0
        mb.box(kit.T(ax, ay, az) @ kit.S(14.0, 16.0, 1.5), "gold")
    # Arrow head
    mb.cone(kit.T(fx - 50, fy - 110, fz + 3.0) @ kit.Rx(math.pi / 2), "gold", segments=3, r1=32.0, r2=0.0, depth=45.0)

    # Red arrow pushing back north into Dutch lines
    for t_step in range(12):
        ay = fy - 160 + t_step * 24
        ax = fx + 50 - math.sin(t_step * 0.4) * 45
        az = ground_z(bvh, ax, ay, default=fz) + 3.5
        mb.box(kit.T(ax, ay, az) @ kit.S(14.0, 16.0, 1.5), "carpet_red")
    # Arrow head
    mb.cone(kit.T(fx + 50, fy + 110, fz + 3.5) @ kit.Rx(-math.pi / 2), "carpet_red", segments=3, r1=32.0, r2=0.0, depth=45.0)

    # 4. White puffs of cannon / musket smoke between the lines
    rng = random.Random(99)
    for i in range(12):
        sx = fx + rng.uniform(-160, 160)
        sy = fy + rng.uniform(-90, 90)
        sz = ground_z(bvh, sx, sy, default=fz) + rng.uniform(12.0, 35.0)
        mb.ico(kit.T(sx, sy, sz), "canvas", r=rng.uniform(18.0, 32.0), sub=1)

    clash_ob = mb.obj("FrontierClash", coll)
    for m in ("coat_blue", "carpet_red", "gold", "post", "canvas"):
        clash_ob.data.materials.append(kit.mat(m, kit.PALETTE[m]))

    clash_ob.hide_render = True
    clash_ob.keyframe_insert("hide_render", frame=1)
    clash_ob.keyframe_insert("hide_render", frame=f0 - 1)
    clash_ob.hide_render = False
    clash_ob.keyframe_insert("hide_render", frame=f0)
    clash_ob.keyframe_insert("hide_render", frame=f1)
    clash_ob.hide_render = True
    clash_ob.keyframe_insert("hide_render", frame=f1 + 1)
    return clash_ob
