"""The 3D map world of the Kerala coast (look: Flow refs frames/flow_refs/K08a_v2, K08b_v2).

No parchment. A painted sea (turquoise shallows into blue, light wave strokes) and the
land as a dense faceted low-poly mesh: a warm sand strip, a thick belt of palms several
rows deep, sharp ridged hills cut by river valleys with the rivers running along the
valley floors, earthy ridge tops, forest patches on the lower slopes, a backwater lagoon
with a sand rim, and small ponds. Ships at sea, and the stockade with a red tent at
Colachel. Detail is concentrated along the camera's path (DETAIL_BOX).

S19-S28 (rebuilt): Ceylon at its real place with the Colombo star fort and the governor's
ship (K25), a sea extension beyond MAP_REGION, the war banner and marching column at Kochi
(K31), and the armies at the frontier near Kollam (K35). Each is shown only in its own beat.

Units: Blender metres on the kerala_geo projection (50 m per real km, Colachel at 0,0).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
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
        SWELLS.append((tex, strength, travel, frames))     # (read by sea_lift for S19-S28 ships)
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


def cloud_material(name="MapCloudVol", density=0.06, rgb=(0.86, 0.87, 0.90)):
    """Soft volumetric cloud: noisy density inside a spherical falloff."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
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
    ramp.inputs["To Max"].default_value = density
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], grad.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mul.inputs[0])
    nt.links.new(grad.outputs["Fac"], mul.inputs[1])
    nt.links.new(mul.outputs["Value"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], vol.inputs["Density"])
    vol.inputs["Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
    if name != "MapCloudVol":                  # (the approved S07 storm clouds stay as they were)
        glow = nt.nodes.new("ShaderNodeMath")     # a little self-light where the cloud is dense,
        glow.operation = "MULTIPLY"               # so corner clouds read white, not grey
        glow.inputs[1].default_value = 0.3
        nt.links.new(ramp.outputs["Result"], glow.inputs[0])
        nt.links.new(glow.outputs["Value"], vol.inputs["Emission Strength"])
        vol.inputs["Emission Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
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

# ====================================================================== S19-S28 (rebuilt)
# Everything below is built after the approved S07-S18 set and is shown only in its own beat
# (show_only), and existing objects are only hidden with keys inside the new beats
# (hide_during), so the S07-S18 frames stay exactly as approved.
SWELLS = []          # (texture, strength, travel, frames) of the map sea, filled by build_sea


def show_only(obs, f0, f1):
    """Render these objects only from f0 to f1."""
    for ob in obs:
        for f, h in ((1, True), (f0 - 1, True), (f0, False), (f1, False), (f1 + 1, True)):
            ob.hide_render = h
            ob.keyframe_insert("hide_render", frame=f)


def hide_during(obs, f0, f1):
    """Hide existing objects from f0 to f1 only (their state before and after is kept)."""
    sc = bpy.context.scene
    obs = list(obs)
    sc.frame_set(f0 - 1)
    before = [ob.hide_render for ob in obs]
    sc.frame_set(f1 + 1)
    after = [ob.hide_render for ob in obs]
    for ob, b, a in zip(obs, before, after):
        for f, h in ((f0 - 1, b), (f0, True), (f1, True), (f1 + 1, a)):
            ob.hide_render = h
            ob.keyframe_insert("hide_render", frame=f)


def build_late_swell(coll, end):
    """Drivers for the swell of the seas built after S18 (the S19 sea, the matte copy, the
    wakes). The approved sea's own drivers are keyed over S07-S18 only (their ease depends on
    that length, so S07-S18 never change when beats are added); these run at the same pace,
    strictly linear, to the end of the film."""
    for tex, strength, (tx, ty), frames in SWELLS:
        drv = bpy.data.objects.new(tex.name + "Late", None)
        coll.objects.link(drv)
        vx, vy = tx / (frames - 1), ty / (frames - 1)
        for f in (1, end):
            drv.location = (vx * (f - 1), vy * (f - 1), 0.0)
            drv.keyframe_insert("location", frame=f)
        LATE[tex.name] = (tex, strength, (vx, vy), drv)
    for drv in [v[3] for v in LATE.values()]:
        sc = bpy.context.scene
        for f in (2, end - 1):                       # check it really is linear
            sc.frame_set(f)
            exp = LATE[drv.name[:-4]][2][0] * (f - 1)
            assert abs(drv.location.x - exp) < 1.0 or _linearise(drv), drv.name


def _linearise(drv):
    """Set every key of the driver to linear interpolation (works with layered actions)."""
    ad = drv.animation_data
    act = ad.action
    curves = []
    try:
        curves = list(act.fcurves)
    except AttributeError:
        for layer in act.layers:
            for strip in layer.strips:
                curves += list(strip.channelbag(ad.action_slot).fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return True


LATE = {}


def sea_lift(x, y, f, w=1.0, names=("MapSwellA", "MapSwellB"), late=False):
    """Height of the map sea's swell at (x, y) on frame f (same textures as the Displace
    modifiers), so ships ride on the faceted sea instead of sinking into its crests.
    late: the linear drivers of S29 on (build_late_swell)."""
    z = 0.0
    if late:
        for name, (tex, strength, (vx, vy), _) in LATE.items():
            if name in names:
                z += (tex.evaluate((x - vx * (f - 1), y - vy * (f - 1), 0.0))[3] - 0.5) * strength
        return z * w
    for tex, strength, (tx, ty), frames in SWELLS:
        if tex.name not in names:
            continue
        u = min(1.0, max(0.0, (f - 1) / max(1, frames - 1)))
        z += (tex.evaluate((x - tx * u, y - ty * u, 0.0))[3] - 0.5) * strength
    return z * w


def add_swell(ob, group="Swell", names=("MapSwellA", "MapSwellB"), sea="MapSea", late=False):
    """Give a mesh the sea's Displace modifiers (same textures and drivers), so it follows
    the faceted swell. The vertex group must exist."""
    sea = bpy.data.objects[sea]
    for m in sea.modifiers:
        if m.type != "DISPLACE" or m.name not in names:
            continue
        mod = ob.modifiers.new(m.name, "DISPLACE")
        mod.texture = m.texture
        mod.texture_coords = "OBJECT"
        mod.texture_coords_object = LATE[m.name][3] if late else m.texture_coords_object
        mod.strength = m.strength
        mod.mid_level = m.mid_level
        mod.vertex_group = group


def kit_colours(*names):
    """Colours from the approved sets that the kit palette does not hold yet (port_world:
    set sails, plain Dutch orange / English red flags)."""
    import port_world as port
    for n in names:
        kit.PALETTE.setdefault(n, port.PALETTE[n])
        kit.mat(n, kit.PALETTE[n])


def dutch_ship(name, coll, sails=True, seed=7):
    """The kit East Indiaman with the S17 rig: full bellied sails and plain orange flags."""
    import port_world as port
    kit_colours("sail_set", "flag_o")
    ship = kit.make_ship(name, coll, length=38.0, beam=10.0, seed=seed)
    plan = {0: (1, 2), 1: (0, 1, 2), 2: (0, 1, 2)} if sails else {1: (1,), 2: (1,)}
    rig = port.make_rig(name, coll, ship, plan, "flag_o", belly=1.6, seed=seed)
    parts = [ship] + [c for c in coll.objects if c.parent == ship]
    return ship, parts, rig


def rock_ship(ob, frames, base_rot_z, amp=(1.6, 2.4), bob=3.0, seed=0, path=None, lift_w=1.0,
              swells=("MapSwellA", "MapSwellB"), late=False):
    """Roll, pitch and heave on the swell (keys every 6 frames). path(f) -> (x, y) sails
    the ship; its height follows the sea's swell at the hull."""
    ph = random.Random(seed).uniform(0, 10)
    x0, y0 = ob.location.x, ob.location.y
    for f in range(1, frames + 7, 6):
        x, y = path(f) if path else (x0, y0)
        ob.location = (x, y, sea_lift(x, y, f, lift_w, swells, late) + bob * math.sin(f / 19.0 + ph))
        ob.rotation_euler = (math.radians(amp[0] * math.sin(f / 21.0 + ph)),
                             math.radians(amp[1] * math.sin(f / 15.0 + 1 + ph)), base_rot_z)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)


def build_corner_clouds(coll, cam, frames, seed=0, depth=3800.0, spots=None, drift=0.06):
    """Soft volumetric clouds in the corners of a shot (as in K25 / K31), riding with the
    camera at `depth` metres in front of it, drifting slowly outward."""
    rng = random.Random(seed)
    f0, f1 = frames
    m = cloud_material("MapCornerCloudVol", density=0.14, rgb=(0.96, 0.96, 0.97))
    spots = spots or ((-1, 1, 1.3), (1, 1, 1.0), (-1, -1, 1.05), (1, -1, 1.15))
    hx, hy = 0.6 * depth, 0.3375 * depth
    obs = []
    for k, (sx, sy, size) in enumerate(spots):
        for j in range(4):
            mb = kit.MB()
            mb.ico(kit.Matrix.Identity(4), "MapCornerCloudVol", r=1.0, sub=3)
            ob = mb.obj(f"{cam.name}Cloud{k}_{j}", coll)
            ob.data.materials[0] = m
            ob.visible_shadow = False
            ob.parent = cam
            r = depth * 0.16 * size * rng.uniform(0.75, 1.15)
            ob.scale = (r * rng.uniform(1.2, 1.6), r * rng.uniform(0.85, 1.05), r * 0.45)
            ob.rotation_euler[2] = rng.uniform(0, 6.28)
            cx = sx * hx * rng.uniform(0.92, 1.12) - sx * j * r * 0.55 * rng.uniform(0.6, 1.0)
            cy = sy * hy * rng.uniform(0.95, 1.2) - sy * (j % 2) * r * 0.5 * rng.uniform(0.3, 1.0)
            for f, k2 in ((f0, 1.0), (f1, 1.0 + drift)):
                ob.location = (cx * k2, cy * k2, -depth * rng.uniform(0.97, 1.03))
                ob.keyframe_insert("location", frame=f)
            obs.append(ob)
    show_only(obs, f0, f1)
    return obs


# ------------------------------------------------------------------- S19: Ceylon (K25)
class Ceylon:
    """Height and surface rules for Ceylon, the same recipe as the Kerala land."""

    def __init__(self):
        self.coast = geo.outline_detailed(geo.ceylon_xy(), 60.0)
        self.kd = KDTree(len(self.coast))
        for i, (x, y) in enumerate(self.coast):
            self.kd.insert((x, y, 0.0), i)
        self.kd.balance()
        xs, ys = [p[0] for p in self.coast], [p[1] for p in self.coast]
        self.box = (min(xs), max(xs), min(ys), max(ys))
        self.hills = [(*geo.xy(a, b), k) for a, b, k in geo.CEYLON_HILLS]

    def coast_dist(self, x, y):
        _, i, best = self.kd.find((x, y, 0.0))
        n = len(self.coast)
        for j in (i - 1, i):
            (ax, ay), (bx, by) = self.coast[j % n], self.coast[(j + 1) % n]
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
            best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
        return best

    def inside(self, x, y):
        return in_box(x, y, self.box) and geo.point_in_poly(x, y, self.coast)

    def height(self, x, y, d):
        base = 5.0 + 12.0 * _smooth(0, 450, d)
        hl = 0.0
        for hx, hy, k in self.hills:
            hl = max(hl, k * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / 3000.0 ** 2))
        mount = 1700.0 * hl * (0.5 + 0.7 * _ridge(x, y, 2100, 2.9))
        rolling = (70.0 + 420.0 * _ridge(x, y, 3000, 5.1) ** 1.5) * (0.3 + 0.7 * _nz(x, y, 5200, 1.1))
        h = base + _smooth(380, 1700, d) * (mount + rolling)
        h += 30.0 * _nz(x, y, 300, 4.0) * _smooth(250, 800, d)
        return h


def build_ceylon_land(coll, cey):
    """Faceted Ceylon: CDT over the island with relief and the build_land colour rules."""
    rng = random.Random(19)
    verts = [Vector((x, y)) for x, y in cey.coast]
    nb = len(verts)
    step = 105.0
    x0, x1, y0, y1 = cey.box
    y = y0 + step / 2
    while y < y1:
        x = x0 + step / 2
        while x < x1:
            px, py = x + rng.uniform(-0.38, 0.38) * step, y + rng.uniform(-0.38, 0.38) * step
            if cey.inside(px, py) and cey.coast_dist(px, py) > 45:
                verts.append(Vector((px, py)))
            x += step
        y += step
    out = delaunay_2d_cdt(verts, [], [list(range(nb))], 1, 0.01)
    vco, faces = out[0], out[2]
    bm = bmesh.new()
    bv = []
    for v in vco:
        d = cey.coast_dist(v.x, v.y)
        bv.append(bm.verts.new((v.x, v.y, cey.height(v.x, v.y, d) if d > 1 else 4.0)))
    for f in faces:
        if len(f) >= 3:
            try:
                bm.faces.new([bv[i] for i in f])
            except ValueError:
                pass
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    mats = ["m_sand", "m_g1", "m_g2", "m_g3", "m_g4", "m_earth"]
    for face in bm.faces:
        if face.normal.z < 0:
            face.normal_flip()
        c = face.calc_center_median()
        n = face.normal
        d = cey.coast_dist(c.x, c.y)
        sand_w = 240 + 140 * _nz(c.x, c.y, 700, 5.0)
        zone = _nz(c.x, c.y, 650, 3.3)
        if d < sand_w:
            m = "m_sand"
        elif (c.z > 1050 and abs(n.z) < 0.62 and _nz(c.x, c.y, 220, 8.1) > 0.6) or \
                (c.z > 1400 and _nz(c.x, c.y, 260, 6.6) > 0.58):
            m = "m_earth"
        elif c.z < 70:
            m = "m_g3" if zone > 0.5 else "m_g1"
        elif c.z < 320:
            m = "m_g1" if zone > 0.45 else "m_g2"
        else:
            m = "m_g2" if zone > 0.4 else "m_g4"
        if m.startswith("m_g") and rng.random() < 0.15:
            m = {"m_g1": "m_g3", "m_g2": "m_g1", "m_g3": "m_g1", "m_g4": "m_g2"}[m]
        face.material_index = mats.index(m)
    me = bpy.data.meshes.new("MapCeylon")
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(mmat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("MapCeylon", me)
    coll.objects.link(ob)
    bvh = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices for p in me.polygons])
    print("ceylon land:", len(me.vertices), "verts")
    return ob, bvh


def matte_sea_material():
    """The map sea's material (vertex colours) with softer highlights for the later, lower,
    tilted map shots, where the approved one throws hard white glints (K25, K31, K35 have none)."""
    m = bpy.data.materials.get("MapSeaMatte")
    if m:
        return m
    m = bpy.data.materials["MapSea"].copy()
    m.name = "MapSeaMatte"
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    return m


def show_ranges(ob, ranges):
    """Render an object only inside the given frame ranges."""
    keys = [(1, True)]
    for a, b in ranges:
        keys += [(a - 1, True), (a, False), (b, False), (b + 1, True)]
    for f, h in keys:
        ob.hide_render = h
        ob.keyframe_insert("hide_render", frame=f)


def matte_sea_copy(coll, ranges, name="MapSeaMatte", late=False):
    """The approved map sea (same mesh, swell and colours) with the matte material, swapped
    in for the given beats."""
    sea = bpy.data.objects["MapSea"]
    cp = sea.copy()
    cp.name = name
    coll.objects.link(cp)
    cp.animation_data_clear()
    cp.material_slots[0].link = "OBJECT"
    cp.material_slots[0].material = matte_sea_material()
    for m in cp.modifiers:                 # a calmer swell for the low, tilted shots
        if m.type == "DISPLACE":
            m.strength *= 0.5
            if late:
                m.texture_coords_object = LATE[m.name][3]
    show_ranges(cp, ranges)
    for a, b in ranges:
        hide_during([sea], a, b)
    return cp


def swap_forts(coll, f0, f1, keep=(), scale=12.0):
    """Hide the kingdom forts for a close beat; the ones in `keep` come back as smaller
    copies of the same forts (same mesh and colours) on the same spot, so the armies and
    the star fort read as in the Flow refs instead of being dwarfed by map-scale forts."""
    forts = [o for o in bpy.data.objects if o.name.startswith("Fort_")]
    hide_during(forts, f0, f1)
    obs = []
    for o in forts:
        if o.name[5:] in keep:
            obs.append(kit.instance(o, f"Small{o.name}", coll, tuple(o.location), rot_z=o.rotation_euler[2],
                                    scale=scale))
    show_only(obs, f0, f1)
    return obs


def build_s19_sea(coll, cey, frames, late=False, step=360.0, name="S19", swells=("MapSwellA",), boost=1.0,
                  dark=1.0, desat=0.0, region=None):
    """The faceted sea for the S19 view over the Gulf of Mannar (geo.SEA_EXT, well past
    MAP_REGION, so there is no edge anywhere in the shot). Same colours and swell as
    build_sea, with facets sized for the very high shot (K25) and turquoise shallows round
    both India and Ceylon. The approved sea is swapped out for this beat only."""
    rng = random.Random(57)
    x0, x1, y0, y1 = region or geo.SEA_EXT
    nx_, ny_ = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
    shallow = kit.srgb_to_linear((0.52, 0.83, 0.80))
    mid = kit.srgb_to_linear((0.38, 0.67, 0.83))
    deep = kit.srgb_to_linear((0.28, 0.55, 0.79))
    coast = geo.coast_detailed(300.0)
    india = geo.land_polygon_detailed(300.0)
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new("Col")
    dl = bm.verts.layers.deform.verify()
    grid = []
    for j in range(ny_):
        row = []
        for i in range(nx_):
            x, y = x0 + i * step, y0 + j * step
            if 0 < i < nx_ - 1 and 0 < j < ny_ - 1:
                x += rng.uniform(-0.32, 0.32) * step
                y += rng.uniform(-0.32, 0.32) * step
            d = geo.dist_to_polyline(x, y, coast)[0]
            t1, t2 = _smooth(150, 1100, d), _smooth(1100, 3600, d)
            w = 0.0 if geo.point_in_poly(x, y, india) else _smooth(250, 900, d)
            if in_box(x, y, cey.box, 6000):
                if cey.inside(x, y):
                    t1 = t2 = w = 0.0
                else:
                    dc = cey.coast_dist(x, y)
                    t1 = min(t1, _smooth(150, 1300, dc))
                    t2 = min(t2, _smooth(1300, 4200, dc))
                    w = min(w, _smooth(250, 900, dc))
            c = [shallow[k] * (1 - t1) + mid[k] * t1 for k in range(3)]
            c = [c[k] * (1 - t2) + deep[k] * t2 for k in range(3)]
            if dark != 1.0 or desat:                      # storm light (S39): greyer, darker water
                g = sum(c) / 3.0
                c = [(c[k] * (1 - desat) + g * desat) * dark for k in range(3)]
            sh = rng.uniform(0.94, 1.06)
            v = bm.verts.new((x, y, 0.0))
            v[col] = (c[0] * sh, c[1] * sh, c[2] * sh, 1.0)
            v[dl][0] = w
            row.append(v)
        grid.append(row)
    for j in range(ny_ - 1):
        for i in range(nx_ - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("MapSea" + name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(matte_sea_material())
    for poly in me.polygons:
        poly.use_smooth = False
    ob = bpy.data.objects.new("MapSea" + name, me)
    coll.objects.link(ob)
    ob.vertex_groups.new(name="Swell")
    add_swell(ob, names=swells, late=late)
    for mod in ob.modifiers:
        mod.strength *= boost
    show_only([ob], *frames)
    hide_during([bpy.data.objects["MapSea"]], *frames)
    print("S19 sea:", len(me.vertices), "verts")
    return ob


def build_ceylon_life(coll, lib_c, cey, bvh, fort_xy, frames, end):
    """Dense palms several rows deep round the coast, palm groves on the lowlands, forest on
    the hill slopes (bare faceted tops), and a cleared town round the Colombo fort."""
    rng = random.Random(61)
    palms = [bpy.data.objects[f"MapLibPalm{i}"] for i in range(6)]
    trees = [bpy.data.objects[f"MapLibTree{i}"] for i in range(4)]
    fx, fy = fort_xy
    obs = []

    def free(x, y):
        return math.hypot(x - fx, y - fy) > 1500

    n = 0
    coast = geo.outline_detailed(geo.ceylon_xy(), 70.0)
    for i in range(len(coast)):
        (ax, ay), (bx, by) = coast[i - 1], coast[i]
        seg = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / seg, (bx - ax) / seg
        if not cey.inside(ax + nx * 300, ay + ny * 300):
            nx, ny = -nx, -ny
        for _ in range(rng.choice((2, 3, 3, 4))):
            off = rng.uniform(170, 750) if rng.random() < 0.85 else rng.uniform(750, 1200)
            x, y = ax + nx * off + rng.uniform(-40, 40), ay + ny * off + rng.uniform(-40, 40)
            if not (cey.inside(x, y) and free(x, y)) or cey.coast_dist(x, y) < 130:
                continue
            obs.append(kit.instance(palms[n % 6], f"CeylonPalm{n}", coll, (x, y, ground_z(bvh, x, y) - 2),
                                    rot_z=rng.uniform(0, 6.28), scale=rng.uniform(36.0, 46.0)))
            n += 1
    nt = 0
    step = 215.0
    x0, x1, y0, y1 = cey.box
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            px, py = x + rng.uniform(-60, 60), y + rng.uniform(-60, 60)
            if cey.inside(px, py) and free(px, py) and cey.coast_dist(px, py) > 1000:
                z = ground_z(bvh, px, py)
                dens = _nz(px, py, 1600, 2.2) * 0.7 + 0.3 * rng.random()
                if z < 300 and dens > 0.45:
                    obs.append(kit.instance(palms[n % 6], f"CeylonPalm{n}", coll, (px, py, z - 2),
                                            rot_z=rng.uniform(0, 6.28), scale=rng.uniform(34.0, 44.0)))
                    n += 1
                elif 300 <= z < 760 and dens > 0.5:
                    obs.append(kit.instance(trees[nt % 4], f"CeylonTree{nt}", coll, (px, py, z - 4),
                                            rot_z=rng.uniform(0, 6.28), scale=rng.uniform(48.0, 62.0)))
                    nt += 1
            x += step
        y += step
    # the town of Colombo round the fort: huts, a jetty and moored ships
    hut_src = [kit.make_hut_hip("CeylonHutSrc0", lib_c, seed=3), kit.make_hut_gable("CeylonHutSrc1", lib_c, seed=4),
               kit.make_hut_gable("CeylonHutSrc2", lib_c, w=5.0, d=3.6, seed=5)]
    for h in hut_src:
        kit.hide_source(h)
    k = 0
    tries = 0
    while k < 26 and tries < 600:
        tries += 1
        a, r = rng.uniform(0, 6.28), rng.uniform(1050, 1900)
        x, y = fx + r * math.cos(a), fy + r * math.sin(a)
        if not cey.inside(x, y) or cey.coast_dist(x, y) < 220:
            continue
        obs.append(kit.instance(hut_src[k % 3], f"CeylonHut{k}", coll, (x, y, ground_z(bvh, x, y) - 1),
                                rot_z=rng.uniform(0, 6.28), scale=rng.uniform(40.0, 50.0)))
        k += 1
    for k in range(40):                                  # a few palms between the houses
        a, r = rng.uniform(0, 6.28), rng.uniform(1100, 1600)
        x, y = fx + r * math.cos(a), fy + r * math.sin(a)
        if cey.inside(x, y) and cey.coast_dist(x, y) > 160 and rng.random() < 0.6:
            obs.append(kit.instance(palms[k % 6], f"CeylonTownPalm{k}", coll, (x, y, ground_z(bvh, x, y) - 2),
                                    rot_z=rng.uniform(0, 6.28), scale=rng.uniform(24.0, 30.0)))
    print("ceylon:", n, "palms,", nt, "trees,", k, "houses")
    return obs


def build_s19(coll, lib_c, frames, end, ship_path):
    """S19 (K25): Ceylon at its real place across the Gulf of Mannar, with the Dutch star
    fort at Colombo, and a Dutch ship under full sail crossing from it toward India with a
    foaming wake. The sea is extended (no seam) and shallows ring the island."""
    f0, f1 = frames
    cey = Ceylon()
    land_ob, bvh = build_ceylon_land(coll, cey)
    build_s19_sea(coll, cey, frames)
    # the Dutch fort at Colombo on the west coast (same star fort as Kochi, Dutch orange)
    cx, cy = geo.xy(*geo.COLOMBO)
    _, ci, _ = cey.kd.find((cx, cy, 0.0))
    (ax, ay), (bx, by) = cey.coast[ci - 1], cey.coast[(ci + 1) % len(cey.coast)]
    L = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / L, (bx - ax) / L
    if not cey.inside(cey.coast[ci][0] + nx * 300, cey.coast[ci][1] + ny * 300):
        nx, ny = -nx, -ny
    fx, fy = cey.coast[ci][0] + nx * 560, cey.coast[ci][1] + ny * 560
    kit.mat("DutchOrangeCeylon", (0.96, 0.46, 0.10))
    fort = make_star_fort("DutchFortColombo", coll, "DutchOrangeCeylon")
    fort.location = (fx, fy, ground_z(bvh, fx, fy) - 2)
    fort.rotation_euler[2] = math.radians(-8)
    fort.scale = (27.0, 27.0, 27.0)
    life = build_ceylon_life(coll, lib_c, cey, bvh, (fx, fy), frames, end)
    # jetty into the harbour south of the fort, two ships moored at it
    jet = kit.make_jetty("ColomboJetty", coll, length=11.0, width=1.8, deck=0.9, seed=6)
    jx, jy = cey.coast[ci][0] - nx * 40 + (bx - ax) / L * -900, cey.coast[ci][1] - ny * 40 + (by - ay) / L * -900
    jet.location = (jx, jy, 2.0)
    jet.rotation_euler[2] = math.atan2(nx, -ny)            # jetty +Y points out to sea
    jet.scale = (38.0, 38.0, 38.0)
    out = (-nx, -ny)
    src = [bpy.data.objects["MapShipSrc0"], bpy.data.objects["MapShipSrc1"]]
    moored = []
    for k, (along, side) in enumerate(((330, 230), (380, -260))):
        x = jx + out[0] * along + out[1] * side
        y = jy + out[1] * along - out[0] * side
        ob = kit.instance(src[k], f"ColomboShip{k}", coll, (x, y, 0.0),
                          rot_z=math.atan2(-out[0], out[1]) + 0.2 * k, scale=10.0)
        rock_ship(ob, end, ob.rotation_euler[2], amp=(1.5, 1.0), bob=2.0, seed=40 + k, lift_w=0.4,
                  swells=("MapSwellA",))
        moored.append(ob)
    # the governor's ship: full sails, plain orange flag, sailing north-west for India
    (sx0, sy0), (sx1, sy1) = ship_path
    heading = math.atan2(-(sx1 - sx0), sy1 - sy0)
    carrier = bpy.data.objects.new("S19ShipPath", None)
    coll.objects.link(carrier)
    carrier.rotation_euler[2] = heading

    def course(f):
        u = min(1.0, max(0.0, (f - f0) / (f1 - f0)))
        u = u * 0.92 + 0.08 * u * u                         # gathers way a little
        return sx0 + (sx1 - sx0) * u, sy0 + (sy1 - sy0) * u
    def sail():
        for f in range(f0 - 4, f1 + 5, 4):
            x, y = course(f)
            carrier.location = (x, y, sea_lift(x, y, f, names=("MapSwellA",)) + 6.0)
            carrier.keyframe_insert("location", frame=f)
    kit.keyframe_linear(sail)
    ship, parts, _ = dutch_ship("S19Ship", coll, seed=7)
    ship.parent = carrier
    ship.scale = (52.0, 52.0, 52.0)
    ph = 1.3
    for f in range(f0 - 6, f1 + 7, 6):                     # heel to the wind, pitch and roll
        ship.rotation_euler = (math.radians(1.8 * math.sin(f / 13.0 + ph)),
                               math.radians(4.0 + 2.2 * math.sin(f / 17.0 + ph)), 0.0)
        ship.location = (0.0, 0.0, 0.2 * math.sin(f / 11.0))
        ship.keyframe_insert("rotation_euler", frame=f)
        ship.keyframe_insert("location", frame=f)
    wake = build_wake("S19Wake", coll, carrier, length=1976.0, beam=520.0, seed=19, reach=5200.0, size=1.7)
    show_only(parts + [wake], f0, f1)
    hide_during([o for o in bpy.data.objects if o.name.startswith(("Territory_", "Border_"))], f0, f1)
    print("S19 built")
    return fort


def build_wake(name, coll, carrier, length=1140.0, beam=300.0, seed=0, spread_deg=17.0, reach=3000.0, size=1.0,
               sea=None, late=False):
    """Foam wake behind a ship: a broken V of white streaks and a churned centre trail,
    fading out astern. It follows the carrier in x, y and heading and rides the sea's
    swell (same Displace modifiers), so it lies on the faceted water."""
    rng = random.Random(seed)
    kit.mat("m_foam", (0.94, 0.97, 0.97))
    kit.mat("m_foam2", (0.78, 0.90, 0.93))
    mb = kit.MB()
    stern = -length / 2

    def streak(cx, cy, ang, ln, wd, m):
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for u, v in ((-0.5, -0.5), (0.5, -0.35), (0.5, 0.35), (-0.5, 0.5)):
            lx, ly = u * ln, v * wd
            pts.append(mb.bm.verts.new((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, 0.0)))
        mb.face(pts, m)

    sp = math.radians(spread_deg)
    for arm in (-1, 1):
        k = 0.0
        while k < reach:
            t = k / reach
            y = stern - 60 - k
            x = arm * (beam * 0.4 + k * math.tan(sp)) + rng.uniform(-20, 20)
            if rng.random() > 0.55 * t:
                ln = rng.uniform(90, 160) * (1 - 0.5 * t) * size
                streak(x, y, math.pi / 2 - arm * sp + rng.uniform(-0.1, 0.1), ln, rng.uniform(16, 30) * (1 - 0.6 * t) * size,
                       "m_foam" if t < 0.45 else "m_foam2")
            k += rng.uniform(70, 120)
    k = 0.0
    while k < reach * 0.8:
        t = k / (reach * 0.8)
        for _ in range(2):
            if rng.random() > 0.6 * t:
                streak(rng.uniform(-1, 1) * beam * (0.25 + 0.5 * t), stern - 30 - k + rng.uniform(-20, 20),
                       math.pi / 2 + rng.uniform(-0.3, 0.3), rng.uniform(60, 130) * (1 - 0.4 * t) * size,
                       rng.uniform(20, 45) * (1 - 0.5 * t) * size, "m_foam" if t < 0.35 else "m_foam2")
        k += rng.uniform(40, 70)
    ob = mb.obj(name, coll)
    ob.visible_shadow = False
    vg = ob.vertex_groups.new(name="Swell")
    vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    if sea:
        add_swell(ob, sea=sea, late=late)
    else:
        add_swell(ob, names=("MapSwellA",))
    c = ob.constraints.new("COPY_LOCATION")
    c.target = carrier
    c.use_z = False
    r = ob.constraints.new("COPY_ROTATION")
    r.target = carrier
    r.use_x = r.use_y = False
    ob.location.z = 9.0
    return ob


# ------------------------------------------------------- S24: Kochi declares war (K31)
def walker_template(name, lib_c, kind, seed=0):
    root, parts = kit.make_walker(name, lib_c, kind, seed=seed)
    for p in parts.values():
        kit.hide_source(p)
    return parts


def new_walker(name, coll, tpl, scale):
    """A kit walker sharing the template's meshes (same figure, cheap to repeat)."""
    root = bpy.data.objects.new(name, None)
    coll.objects.link(root)
    root.scale = (scale, scale, scale)
    parts = {}
    for p, src in tpl.items():
        ob = bpy.data.objects.new(f"{name}_{p}", src.data)
        coll.objects.link(ob)
        ob.parent = root
        ob.location = kit.PIVOTS[p]
        parts[p] = ob
    return root, parts


def standard(name, coll, parent, local, flag_m, pole_h=4.2, w=1.8, h=1.15):
    """A plain-colour flag on a pole, carried by (parented to) a figure or a block."""
    import port_world as port
    p = kit.MB()
    p.seg((local[0], local[1], 0.6), (local[0], local[1], pole_h), 0.05, 0.04, "post", sides=6)
    p.ico(kit.T(local[0], local[1], pole_h + 0.05), "brass", r=0.08, sub=1)
    pole = p.obj(name + "Pole", coll, parent=parent)
    fl = port.make_flag(name, coll, w=w, h=h, m=flag_m)
    fl.parent = parent
    fl.location = (local[0] + 0.04, local[1], pole_h - 0.05)
    return [pole, fl]


def beach_path(land, y_top, y_bot, inland=75.0, step=45.0):
    """A path along the beach (inland of the waterline by `inland` m), north to south."""
    coast = [(x, y) for x, y in geo.coast_detailed(step) if y_bot <= y <= y_top and x < 0]
    coast.sort(key=lambda p: -p[1])
    out = []
    for i, (x, y) in enumerate(coast):
        j, k = min(i + 1, len(coast) - 1), max(i - 1, 0)
        tx, ty = coast[j][0] - coast[k][0], coast[j][1] - coast[k][1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        if not geo.point_in_poly(x + nx * 300, y + ny * 300, land.poly):
            nx, ny = -nx, -ny
        out.append((x + nx * inland, y + ny * inland))
    sm = []                                             # smooth the wobble out of the line
    for i in range(len(out)):
        a, b = max(0, i - 3), min(len(out), i + 4)
        sm.append((sum(p[0] for p in out[a:b]) / (b - a), sum(p[1] for p in out[a:b]) / (b - a)))
    return sm


def path_at(path, s):
    """Point and unit direction at arc length s along a polyline (clamped, extrapolated)."""
    acc = 0.0
    for i in range(len(path) - 1):
        (ax, ay), (bx, by) = path[i], path[i + 1]
        L = math.hypot(bx - ax, by - ay)
        if s <= acc + L or i == len(path) - 2:
            u = (s - acc) / (L or 1.0)
            return (ax + (bx - ax) * u, ay + (by - ay) * u), ((bx - ax) / (L or 1), (by - ay) / (L or 1))
        acc += L
    return path[-1], (0.0, -1.0)


def build_s24(coll, lib_c, land, bvh, frames, end, hoist, march, leave):
    """S24 (K31): over the Dutch star fort at Kochi a huge plain orange war banner is hoisted
    as the line says the Dutch declare war, and a column of Dutch soldiers marches out and
    south down the beach; van Imhoff's ship sails away; huts among the palms."""
    f0, f1 = frames
    fort = bpy.data.objects["DutchFortKochi"]
    fx, fy, fz = fort.location
    obs = []
    # 1. the war banner: a tall mast at the fort's heart, the flag hoisted to the top
    import port_world as port
    kit_colours("sail_set", "flag_o")
    mb = kit.MB(bevel=0.3)
    mb.seg((fx, fy, fz + 20), (fx, fy, fz + 470), 7.0, 4.5, "post", sides=8)
    mb.ico(kit.T(fx, fy, fz + 474), "brass", r=9.0, sub=1)
    mb.cone(kit.T(fx, fy, fz + 26), "stone", segments=8, r1=26.0, r2=20.0, depth=14.0)
    obs.append(mb.obj("S24BannerMast", coll))
    flag = port.make_flag("S24WarBanner", coll, w=2.6, h=1.6, m="flag_o")
    flag.scale = (125.0, 125.0, 125.0)
    flag.rotation_euler[2] = math.radians(-12)           # flies east, its face to the camera
    wv = flag.modifiers["Wave"]
    wv.height *= 2.6
    wv.width *= 0.8
    wv.speed *= 1.6
    for f, z in ((f0, fz + 120), (hoist[0], fz + 120), (hoist[1], fz + 466)):
        flag.location = (fx + 4, fy, z)
        flag.keyframe_insert("location", frame=f)
    obs.append(flag)
    # 2. the column: three files of Dutch soldiers on the beach south of the fort; they stand
    #    until the war is declared, then march south
    path = beach_path(land, fy - 560, fy - 3200, inland=55.0)
    swap_forts(coll, f0, f1)                             # only the Dutch star fort here (K31)
    tpls = [walker_template(f"S24DutchTpl{i}", lib_c, "dutch", seed=30 + i) for i in range(3)]
    rng = random.Random(24)
    sc_fig, ranks, gap, files = 24.0, 32, 30.0, (-19.0, 0.0, 19.0)
    road = []
    for o in bpy.data.objects:                           # keep the beach road clear for the march
        if o.name.startswith(("MapPalm", "MapTree")) and fy - 3300 < o.location.y < fy - 300:
            if min(math.hypot(o.location.x - x, o.location.y - y) for x, y in path) < 105:
                road.append(o)
    hide_during(road, f0, f1)
    head0 = 70.0 + gap * (ranks - 1)
    dist = 62.0 * (f1 - march) / kit.FPS                    # metres marched by the end
    ground = lambda x, y: ground_z(bvh, x, y) - 0.5
    n = 0
    for r in range(ranks):
        for c, off in enumerate(files):
            root, parts = new_walker(f"S24Soldier{n}", coll, tpls[(r + c) % 3], sc_fig * rng.uniform(0.96, 1.04))
            s0 = head0 - r * gap + rng.uniform(-2, 2)
            wps = []
            for k in range(13):
                (px, py), (dx, dy) = path_at(path, s0 + dist * k / 12)
                wps.append((px - dy * off, py + dx * off))
            (px, py), (dx, dy) = path_at(path, s0)
            root.location = (wps[0][0], wps[0][1], ground(*wps[0]))
            root.rotation_euler = (0, 0, math.atan2(dy, dx) - math.pi / 2)
            kit.animate_idle(root, random.Random(n), f0, march - 14, amount=0.03)
            kit.animate_walk(root, parts, wps, ground, start=march + int(r * 0.3), end=f1 + 2,
                             stride_frames=12, swing=0.5)
            if r in (1, ranks // 2, ranks - 3) and c == 1:
                obs += standard(f"S24Standard{r}", coll, root, (0.32, 0.05), "flag_o", pole_h=4.6, w=2.0, h=1.25)
            obs += list(parts.values())
            n += 1
    # 3. van Imhoff leaves: a Dutch ship under sail stands out from the fort, heading south-west
    kx, ky = geo.xy(*FORT_KOCHI)
    ship, parts, _ = dutch_ship("S24LeavingShip", coll, seed=11)
    ship.scale = (6.5, 6.5, 6.5)
    p0, p1 = (kx - 820, ky - 380), (kx - 2000, ky - 1950)
    hd = math.atan2(-(p1[0] - p0[0]), p1[1] - p0[1])

    def course(f):
        u = min(1.0, max(0.0, (f - leave[0]) / (leave[1] - leave[0])))
        u = u * u * (3 - 2 * u) * 0.75 + 0.25 * min(1.0, max(0.0, (f - leave[0]) / (f1 - leave[0])))
        return p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u
    ship.location = (*p0, 0)
    rock_ship(ship, end, hd, amp=(1.4, 2.0), bob=2.0, seed=13, path=course, lift_w=0.3)
    obs += parts
    # the three ships moored off the fort rock on the swell (copies of the S11 ships)
    olds = [bpy.data.objects[f"DutchShipKochi{i}"] for i in range(3)]
    for i, o in enumerate(olds):
        cp = kit.instance(o, f"S24KochiShip{i}", coll, tuple(o.location), rot_z=0.0, scale=6.0)
        cp.animation_data_clear()
        sc_ = bpy.context.scene
        sc_.frame_set(f0)
        rz = o.matrix_world.to_euler()[2]
        cp.location = o.matrix_world.translation
        rock_ship(cp, end, rz, amp=(1.6, 1.2), bob=2.0, seed=60 + i, lift_w=0.25)
        obs.append(cp)
    hide_during(olds, f0, f1)
    # 4. huts in clearings among the palms, east of the beach (K31)
    srcs = [kit.make_hut_hip("S24HutSrc0", lib_c, seed=21), kit.make_hut_gable("S24HutSrc1", lib_c, seed=22),
            kit.make_hut_gable("S24HutSrc2", lib_c, w=4.8, d=3.6, seed=23)]
    for s in srcs:
        kit.hide_source(s)
    k = tries = 0
    while k < 34 and tries < 3000:
        tries += 1
        x, y = rng.uniform(fx - 600, fx + 1500), rng.uniform(fy - 2600, fy + 900)
        if math.hypot(x - fx, y - fy) < 820 or not geo.point_in_poly(x, y, land.poly):
            continue
        d = land.coast_dist(x, y)
        if not (230 < d < 1500) or land.in_lagoon(x, y) or land.lagoon_dist(x, y) < 70 or \
                land.river_dist(x, y) < 70 or land.in_lake(x, y, 1.3):
            continue
        for _ in range(rng.choice((1, 2, 3))):          # small clusters
            hx, hy = x + rng.uniform(-90, 90), y + rng.uniform(-90, 90)
            obs.append(kit.instance(srcs[k % 3], f"S24Hut{k}", coll, (hx, hy, ground_z(bvh, hx, hy) - 0.5),
                                    rot_z=rng.uniform(0, 6.28), scale=rng.uniform(13.0, 16.0)))
            k += 1
    show_only(obs, f0, f1)
    print("S24 built:", n, "marching soldiers,", k, "huts")


# ------------------------------------------------- S28: the frontier near Kollam (K35)
_CD = (-0.677, 0.735)            # along the coast (north-west); same as map_film
_CN = (0.735, 0.677)             # inland


def build_s28(coll, lib_c, bvh, frames, end, centre):
    """S28 (K35): the two armies face each other on the coastal plain at Travancore's
    frontier near Kollam, Dutch blue to the north in front of the allied Kollam fort,
    Travancore red to the south in front of its fort, and the line goes back and forth: a
    push south, a push north, a push south, then stalemate. Musket smoke at each volley,
    ground arrows for each push, banners, guns, ships rocking at sea.
    centre: a point 130 m inland of the waterline where the frontier meets the coast."""
    f0, f1 = frames
    n = f1 - f0
    rng = random.Random(28)
    obs = []
    kit_colours("flag_o", "flag_r")
    front0 = -90.0                       # the line, metres along the coast from `centre` (+ = north-west)
    keys = [(0.0, 0.0), (0.10, 0.0), (0.40, -150.0), (0.50, -150.0), (0.78, 110.0), (0.86, 110.0), (1.0, 10.0)]

    def front(f):
        u = (f - f0) / n
        for (ua, va), (ub, vb) in zip(keys, keys[1:]):
            if u <= ub:
                t = 0.0 if ub == ua else max(0.0, min(1.0, (u - ua) / (ub - ua)))
                return front0 + va + (vb - va) * t * t * (3 - 2 * t)
        return front0 + keys[-1][1]

    def at(along, inland):
        return (centre[0] + _CD[0] * along + _CN[0] * inland, centre[1] + _CD[1] * along + _CN[1] * inland)

    def local(x, y):
        dx, dy = x - centre[0], y - centre[1]
        return dx * _CD[0] + dy * _CD[1], dx * _CN[0] + dy * _CN[1]

    # the home forts, smaller so the armies read (Kollam allied north, Attingal and
    # Kottarakkara Travancore red); the palms are cleared off the battlefield for the beat
    swap_forts(coll, f0, f1, keep=("Kollam", "Attingal"), scale=11.0)
    clear = []
    for o in bpy.data.objects:
        if o.name.startswith(("MapPalm", "MapTree")):
            a, i = local(o.location.x, o.location.y)
            if abs(a - front0) < 720 and -160 < i < 1050:
                clear.append(o)
    hide_during(clear, f0, f1)
    figs = {"dutch": [kit.make_figure(f"S28DutchSrc{i}", lib_c, "dutch", seed=80 + i) for i in range(3)],
            "nair": [kit.make_figure(f"S28NairSrc{i}", lib_c, "nair", seed=90 + i) for i in range(2)]
            + [kit.make_figure(f"S28NairSpearSrc{i}", lib_c, "nair_spear", seed=95 + i) for i in range(2)]}
    gun = kit.make_cannon("S28GunSrc", lib_c)
    for s_ in figs["dutch"] + figs["nair"] + [gun]:
        kit.hide_source(s_)
    sc_fig, sp = 26.0, 28.0
    face_s = math.atan2(_CD[0], -_CD[1])                  # looking south-east (down the coast)
    face_n = math.atan2(-_CD[0], _CD[1])                  # looking north-west
    gap = 72.0
    blocks = []
    sides = (("dutch", 1, (10.0, 300.0), 10, 7, "flag_o"),
             ("nair", -1, (10.0, 300.0), 10, 8, "flag_r"))
    for side, sgn, centres, files, ranks, fm in sides:
        for bi, inl in enumerate(centres):
            emp = bpy.data.objects.new(f"S28Block_{side}{bi}", None)
            coll.objects.link(emp)
            blocks.append((emp, sgn, inl))
            for r in range(ranks):
                for c in range(files):
                    if side == "nair" and r == ranks - 1 and rng.random() < 0.4:
                        continue                               # a ragged rear rank
                    lx = (c - (files - 1) / 2) * sp + rng.uniform(-4, 4)
                    ly = r * sp + rng.uniform(-4, 4)
                    # block frame: x inland, y away from the enemy
                    wx = _CN[0] * lx + _CD[0] * ly * sgn
                    wy = _CN[1] * lx + _CD[1] * ly * sgn
                    ob = kit.instance(rng.choice(figs[side]), f"S28{side}{bi}_{r}_{c}", coll, (wx, wy, 0.0),
                                      rot_z=(face_s if sgn > 0 else face_n) + rng.uniform(-0.15, 0.15),
                                      scale=sc_fig * rng.uniform(0.95, 1.05))
                    ob.parent = emp
                    kit.animate_idle(ob, random.Random(len(obs)), f0, f1, amount=0.06)
                    obs.append(ob)
            for k, lx in enumerate((-70.0, 70.0)):                 # two banners in each block
                ly = (ranks - 1) * sp * 0.55
                st = bpy.data.objects.new(f"S28Std_{side}{bi}{k}", None)
                coll.objects.link(st)
                st.parent = emp
                st.location = (_CN[0] * lx + _CD[0] * ly * sgn, _CN[1] * lx + _CD[1] * ly * sgn, 0)
                st.scale = (sc_fig, sc_fig, sc_fig)
                obs += standard(f"S28Flag_{side}{bi}{k}", coll, st, (0, 0), fm, pole_h=5.6, w=2.4, h=1.5)
            for k, lx in enumerate((-150.0, 150.0)):               # guns on the block's flanks
                g = kit.instance(gun, f"S28Gun_{side}{bi}{k}", coll,
                                 (_CN[0] * lx + _CD[0] * 10 * sgn, _CN[1] * lx + _CD[1] * 10 * sgn, 0),
                                 scale=sc_fig * 1.25, rot_z=face_s if sgn > 0 else face_n)
                g.parent = emp
                obs.append(g)
    for emp, sgn, inl in blocks:
        for f in range(f0 - 2, f1 + 4, 3):
            x, y = at(front(f) + sgn * gap, inl)
            emp.location = (x, y, ground_z(bvh, x, y) - 0.5)
            emp.keyframe_insert("location", frame=f)
    # smoke: volleys along both fronts and from the guns, puffs swell and thin away
    kit.mat("smoke", kit.PALETTE["smoke"])
    smk = kit.MB()
    smk.ico(kit.Matrix.Identity(4), "smoke", r=1.0, sub=1, jitter=0.18, rng=rng)
    smk_ob = smk.obj("S28PuffSrc", lib_c)
    kit.hide_source(smk_ob)
    p = 0
    for fv in range(f0 + 5, f1 - 8, 13):
        for side, sgn, centres, *_ in sides:
            if rng.random() < 0.3:
                continue
            for inl in centres:
                for _ in range(rng.randint(2, 4)):
                    x, y = at(front(fv) + sgn * (gap - 12) + rng.uniform(-12, 12), inl + rng.uniform(-130, 130))
                    z = ground_z(bvh, x, y) + rng.uniform(22, 40)
                    ob = kit.instance(smk_ob, f"S28Puff{p}", coll, (x, y, z), rot_z=rng.uniform(0, 6.28), scale=0.01)
                    r = rng.uniform(16, 28)
                    for f, s_, dz in ((fv - 1, 0.01, 0), (fv + 3, r, 4), (fv + 16, r * 1.6, 20), (fv + 34, r * 0.2, 36)):
                        ob.scale = (s_, s_, s_ * 0.8)
                        ob.location.z = z + dz
                        ob.keyframe_insert("scale", frame=f)
                        ob.keyframe_insert("location", frame=f)
                    obs.append(ob)
                    p += 1
    # ground arrows for each push (orange = the Dutch push south, red = Travancore pushes back)
    kit.mat("arrow_o", (0.98, 0.50, 0.08))
    kit.mat("arrow_r", (0.66, 0.06, 0.05))
    for k, (ua, ub, sgn, m) in enumerate(((0.10, 0.48, -1, "arrow_o"), (0.50, 0.86, 1, "arrow_r"),
                                          (0.86, 1.0, -1, "arrow_o"))):
        fa, fb = f0 + round(ua * n), f0 + round(ub * n)
        tail = front(fa) - sgn * 190
        ob = build_ground_arrow(f"S28Arrow{k}", coll, bvh, at(tail, 640.0), (sgn * _CD[0], sgn * _CD[1]),
                                470.0 if k < 2 else 300.0, 80.0, m, lift=16.0)
        for f, s_ in ((fa - 1, 0.02), (fa + 16, 1.0), (fb, 1.0)):
            ob.scale = (1.0, s_, 1.0)
            ob.keyframe_insert("scale", frame=f)
        show_only([ob], fa, fb)
    # ships at sea off the battlefield, rocking (the S07 ship there is hidden for the beat)
    hide_during([bpy.data.objects["MapShip3"]], f0, f1)
    src = [bpy.data.objects["MapShipSrc0"], bpy.data.objects["MapShipSrc1"]]
    for k, (along, out) in enumerate(((-1300, 700), (-650, 1150), (150, 800), (800, 1300), (-1900, 1250),
                                      (500, 1900))):
        x, y = at(along, -out)
        rz = math.radians(rng.choice((20, 160, 200, 340)) + rng.uniform(-15, 15))
        ob = kit.instance(src[k % 2], f"S28Ship{k}", coll, (x, y, 0), rot_z=rz, scale=6.0)
        rock_ship(ob, end, rz, amp=(2.0, 1.4), bob=2.5, seed=70 + k, lift_w=0.3,
                  path=lambda f, x=x, y=y, rz=rz: (x - math.sin(rz) * 0.25 * (f - f0), y + math.cos(rz) * 0.25 * (f - f0)))
        obs.append(ob)
    show_only(obs, f0, f1)
    print("S28 built:", len([o for o in obs if o.name.startswith("S28dutch")]), "Dutch,",
          len([o for o in obs if o.name.startswith("S28nair")]), "Travancore,", p, "puffs,", len(clear), "palms cleared")


def build_ground_arrow(name, coll, bvh, tail, direction, length, width, m, lift=12.0):
    """A flat arrow draped over the ground (a fine grid, every vertex just above the
    terrain); origin at the tail so scaling local Y grows it out from the tail."""
    dx, dy = direction
    rot = math.atan2(-dx, dy)
    ca, sa = math.cos(rot), math.sin(rot)
    shaft, head = length * 0.66, width * 1.25
    rows = []
    for k in range(25):
        ly = length * k / 24
        if k and rows[-1][0] < shaft <= ly:
            rows.append((shaft, width / 2))
            rows.append((shaft + 0.01, head))
        rows.append((ly, width / 2 if ly < shaft else head * (length - ly) / (length - shaft)))
    mb = kit.MB()
    grid = []
    for ly, hw in rows:
        row = []
        for i in range(7):
            lx = -hw + 2 * hw * i / 6
            wx, wy = tail[0] + lx * ca - ly * sa, tail[1] + lx * sa + ly * ca
            row.append(mb.bm.verts.new((lx, ly, ground_z(bvh, wx, wy) + lift)))
        grid.append(row)
    for r0, r1 in zip(grid, grid[1:]):
        for i in range(6):
            try:
                mb.face([r0[i], r0[i + 1], r1[i + 1], r1[i]], m)
            except ValueError:
                pass
    ob = mb.obj(name, coll)
    ob.location = (tail[0], tail[1], 0.0)
    ob.rotation_euler[2] = rot
    ob.visible_shadow = False
    return ob


# ------------------------------------------- S29: fresh troops, a new plan (K36)
def sea_route(land, start, y_end, off=1100.0, step=45.0):
    """A sea lane parallel to the coast, `off` metres out, from `start` south to y_end and
    round the tip toward Colachel: [(x, y)] smoothed, north to south."""
    coast = [(x, y) for x, y in geo.coast_detailed(step) if x < 900 and y_end - 2500 < y < start[1] + 200]
    # follow the coast in order (it runs north to south on the west side, then east past the tip)
    coast.sort(key=lambda p: -(p[1] - 0.35 * p[0]))
    pts = []
    for i, (x, y) in enumerate(coast):
        j, k = min(i + 1, len(coast) - 1), max(i - 1, 0)
        tx, ty = coast[j][0] - coast[k][0], coast[j][1] - coast[k][1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        if geo.point_in_poly(x + nx * 300, y + ny * 300, land.poly):
            nx, ny = -nx, -ny
        pts.append((x + nx * off, y + ny * off))
    sm = []
    for i in range(len(pts)):
        a, b = max(0, i - 12), min(len(pts), i + 13)
        sm.append((sum(p[0] for p in pts[a:b]) / (b - a), sum(p[1] for p in pts[a:b]) / (b - a)))
    return [start] + [p for p in sm if p[1] < start[1] - 400]


def build_s29(coll, lib_c, land, bvh, frames, end, arrive, land_men, route):
    """S29 (K36): a Dutch ship from Ceylon, with the fresh soldiers, comes up the coast and
    berths at the orange Kochi star fort (wake behind it); the soldiers go ashore; then the
    new plan: a dotted sea route of small white dots swings south from Kochi along the coast
    to the tip, ending in a dotted arrowhead off Colachel. Travancore's land stays red."""
    f0, f1 = frames
    obs = []
    swap_forts(coll, f0, f1)                             # only the star fort, as in K36
    matte_sea_copy(coll, [frames], name="MapSeaMatteS29", late=True)
    kx, ky = geo.xy(*FORT_KOCHI)
    fort = bpy.data.objects["DutchFortKochi"]
    fx, fy, fz = fort.location
    # 1. the ship from Ceylon: up the coast from the south-west, to a berth off the fort
    ship, parts, _ = dutch_ship("S29CeylonShip", coll, seed=17)
    ship.scale = (6.5, 6.5, 6.5)
    p0, p1 = (kx - 2300, ky - 3600), (kx - 760, ky - 520)
    hd = math.atan2(-(p1[0] - p0[0]), p1[1] - p0[1])
    carrier = bpy.data.objects.new("S29ShipPath", None)
    coll.objects.link(carrier)
    carrier.rotation_euler[2] = hd

    def course(f):
        u = min(1.0, max(0.0, (f - f0 + 40) / (arrive - f0 + 40)))
        u = 1 - (1 - u) ** 2.2                              # slows as it comes in
        return p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u

    def sail():
        for f in range(f0 - 4, f1 + 5, 4):
            x, y = course(f)
            carrier.location = (x, y, sea_lift(x, y, f, 0.5, late=True))
            carrier.keyframe_insert("location", frame=f)
    kit.keyframe_linear(sail)
    ship.parent = carrier
    for f in range(f0 - 6, f1 + 7, 6):
        ship.rotation_euler = (math.radians(1.6 * math.sin(f / 13.0)), math.radians(2.5 + 1.8 * math.sin(f / 17.0)), 0)
        ship.keyframe_insert("rotation_euler", frame=f)
    wake = build_wake("S29Wake", coll, carrier, length=247.0, beam=70.0, seed=29, reach=1400.0, size=0.45,
                      sea="MapSeaMatteS29", late=True)
    # the wake dies away once the ship has stopped
    for f, s_ in ((arrive - 30, 1.0), (arrive + 50, 0.0)):
        wake.scale = (max(s_, 0.01), max(s_, 0.01), 1.0)
        wake.keyframe_insert("scale", frame=f)
    obs += parts + [wake]
    # 2. the fresh soldiers come ashore below the fort and march up to it
    tpls = [walker_template(f"S29DutchTpl{i}", lib_c, "dutch", seed=50 + i) for i in range(3)]
    rng = random.Random(29)
    shore = beach_path(land, fy - 350, fy - 1500, inland=45.0)
    (sx, sy), _ = path_at(shore, 120.0)
    gate = (fx + 260, fy - 520)
    ground = lambda x, y: ground_z(bvh, x, y) - 0.5
    for k in range(36):
        r, c = divmod(k, 3)
        root, prt = new_walker(f"S29Soldier{k}", coll, tpls[k % 3], 20.0 * rng.uniform(0.96, 1.04))
        a = (sx - 30 + c * 18 + rng.uniform(-4, 4), sy - 180 - r * 26)
        b = (gate[0] - 30 + c * 18, gate[1] + 40 - r * 26 + 150)
        root.location = (a[0], a[1], ground(*a))
        root.rotation_euler = (0, 0, math.atan2(b[1] - a[1], b[0] - a[0]) - math.pi / 2)
        st = land_men + k // 3 * 3
        kit.animate_walk(root, prt, [a, ((a[0] + b[0]) / 2 + 40, (a[1] + b[1]) / 2), b], ground,
                         start=st, end=min(f1, st + 150), stride_frames=12, swing=0.5)
        for f, h in ((1, True), (land_men - 1, True), (land_men, False), (f1, False), (f1 + 1, True)):
            for o in prt.values():
                o.hide_render = h
                o.keyframe_insert("hide_render", frame=f)
    # the ships moored off the fort rock on the swell
    olds = [bpy.data.objects[f"DutchShipKochi{i}"] for i in range(3)]
    sc_ = bpy.context.scene
    sc_.frame_set(f0)
    for i, o in enumerate(olds):
        cp = kit.instance(o, f"S29KochiShip{i}", coll, tuple(o.matrix_world.translation), scale=6.0)
        rock_ship(cp, end, o.matrix_world.to_euler()[2], amp=(1.6, 1.2), bob=2.0, seed=160 + i, lift_w=0.25,
                  late=True)
        obs.append(cp)
    hide_during(olds, f0, f1)
    # 3. the new plan: a dotted route south along the coast to the tip, then a dotted arrowhead
    r0, r1 = route
    path = sea_route(land, (kx - 900, ky - 900), 0.0)
    tail_end = (-400.0, -850.0)                             # off Colachel, the head points at the beach
    path = [p for p in path if p[0] < -900 or p[1] > 600] + [tail_end]
    pts, acc, spacing = [], 0.0, 150.0
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
    s = 0.0
    while s < total - 60:
        (x, y), d = path_at(path, s)
        pts.append((x, y, d))
        s += spacing
    kit.mat("m_route", (0.97, 0.97, 0.95))
    dot = kit.MB()
    dot.cone(kit.Matrix.Identity(4), "m_route", segments=8, r1=1.0, r2=0.8, depth=0.5)
    dot_src = dot.obj("S29DotSrc", lib_c)
    kit.hide_source(dot_src)
    n = len(pts)
    for i, (x, y, d) in enumerate(pts):
        f = round(r0 + (r1 - r0) * i / max(1, n - 1))
        ob = kit.instance(dot_src, f"S29Dot{i}", coll, (x, y, 48.0), scale=0.01)
        for fk, s_ in ((f - 1, 0.01), (f + 4, 72.0), (f + 9, 56.0)):
            ob.scale = (s_, s_, s_)
            ob.keyframe_insert("scale", frame=fk)
        ob.visible_shadow = False
        obs.append(ob)
    # dotted arrowhead: two short rows of dots swept back from the tip
    (ex, ey), (dx, dy) = path_at(path, total)
    for side in (-1, 1):
        for k in range(1, 5):
            bx = ex - dx * k * 150 + side * (-dy) * k * 130
            by = ey - dy * k * 150 + side * dx * k * 130
            ob = kit.instance(dot_src, f"S29Head{side}_{k}", coll, (bx, by, 48.0), scale=0.01)
            for fk, s_ in ((r1 + 2 + k * 2, 0.01), (r1 + 7 + k * 2, 78.0), (r1 + 12 + k * 2, 60.0)):
                ob.scale = (s_, s_, s_)
                ob.keyframe_insert("scale", frame=fk)
            ob.visible_shadow = False
            obs.append(ob)
    tip = kit.instance(dot_src, "S29HeadTip", coll, (ex, ey, 48.0), scale=0.01)
    for fk, s_ in ((r1, 0.01), (r1 + 5, 84.0), (r1 + 10, 64.0)):
        tip.scale = (s_, s_, s_)
        tip.keyframe_insert("scale", frame=fk)
    obs.append(tip)
    show_only(obs, f0, f1)
    print("S29 built:", n, "route dots, 36 soldiers ashore")


# ------------------------------------------------- S39: a Dutch ship turns back in the storm (K48)
def storm_weather(frames, strength=(0.55, 1.0), full_at=0.35):
    """Monsoon light for one beat: the sun dims and goes cool, the sky greys. Keys are calm on
    the frames either side of the beat, so no other beat changes. strength = storm at the
    first and at the full frame."""
    f0, f1 = frames
    sun = bpy.data.objects["MapSun"].data
    bg = next(n for n in bpy.context.scene.world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
    calm = dict(energy=sun.energy, color=tuple(sun.color), sky=tuple(bg.inputs["Color"].default_value)[:3],
                sky_e=bg.inputs["Strength"].default_value)
    storm = dict(energy=1.9, color=(0.84, 0.88, 0.95), sky=tuple(kit.srgb_to_linear((0.58, 0.60, 0.63))), sky_e=0.5)
    calm["angle"], storm["angle"] = sun.angle, math.radians(16)

    def put(f, w):
        sun.energy = calm["energy"] + (storm["energy"] - calm["energy"]) * w
        sun.color = tuple(a + (b - a) * w for a, b in zip(calm["color"], storm["color"]))
        bg.inputs["Color"].default_value = (*[a + (b - a) * w for a, b in zip(calm["sky"], storm["sky"])], 1.0)
        bg.inputs["Strength"].default_value = calm["sky_e"] + (storm["sky_e"] - calm["sky_e"]) * w
        sun.angle = calm["angle"] + (storm["angle"] - calm["angle"]) * w
        sun.keyframe_insert("angle", frame=f)
        sun.keyframe_insert("energy", frame=f)
        sun.keyframe_insert("color", frame=f)
        bg.inputs["Color"].keyframe_insert("default_value", frame=f)
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
    put(f0 - 1, 0.0)
    put(f0, strength[0])
    put(f0 + int((f1 - f0) * full_at), strength[1])
    put(f1, strength[1])
    put(f1 + 1, 0.0)


def build_storm_clouds(coll, lib_c, frames, anchor, fw, groups, seed=39):
    """Dark low-poly storm clouds (kit.make_cloud) hanging over the sea at the given
    spots. groups: (forward m, sideways m, height m, scale) from the anchor point along the
    view direction fw=(x, y). Clouds drift slowly sideways across the beat."""
    f0, f1 = frames
    rng = random.Random(seed)
    right = (fw[1], -fw[0])
    srcs = [kit.make_cloud(f"S39CloudSrc{i}", lib_c, seed=30 + i, size=1.0 + 0.1 * i) for i in range(4)]
    kit.mat("m_scloud_a", (0.56, 0.56, 0.57))
    kit.mat("m_scloud_b", (0.36, 0.36, 0.37))
    for i, ob in enumerate(srcs):
        ob.data.materials.clear()
        ob.data.materials.append(bpy.data.materials["m_scloud_a" if i % 2 == 0 else "m_scloud_b"])
        kit.hide_source(ob)
    obs = []
    n = 0
    for gf, gs, gz, gsc in groups:
        for k in range(rng.randint(3, 4)):
            df, ds = gf + rng.uniform(-0.9, 0.9) * gsc * 22, gs + rng.uniform(-1.0, 1.0) * gsc * 30
            dz = gz + rng.uniform(-150, 250)
            sc = gsc * rng.uniform(0.75, 1.2)
            x = anchor[0] + fw[0] * df + right[0] * ds
            y = anchor[1] + fw[1] * df + right[1] * ds
            ob = kit.instance(srcs[n % 4], f"S39Cloud{n}", coll, (x, y, dz), rot_z=rng.uniform(0, 6.28), scale=sc)
            ob.keyframe_insert("location", frame=f0)
            ob.location = (x + right[0] * 4.0 * sc, y + right[1] * 4.0 * sc, dz)
            ob.keyframe_insert("location", frame=f1)
            obs.append(ob)
            n += 1
    return obs


def build_map_rain(coll, frames, anchor, fw, spots, seed=39, period=1050.0, streak=720.0, per_spot=170, speed=95.0):
    """Rain streaks falling under the cloud spots (forward m, sideways m, radius m): thin long
    boxes in two stacked layers, scrolled down one layer per loop so it never shows a seam
    (the beach rain, scaled up for map height)."""
    f0, f1 = frames
    rng = random.Random(seed)
    right = (fw[1], -fw[0])
    kit.mat("m_rain", (0.88, 0.90, 0.93))
    mb = kit.MB()
    pts = []
    for gf, gs, rad in spots:
        for _ in range(per_spot):
            a, r = rng.uniform(0, 6.283), rad * math.sqrt(rng.random())
            df, ds = gf + r * math.cos(a), gs + r * math.sin(a)
            pts.append((anchor[0] + fw[0] * df + right[0] * ds, anchor[1] + fw[1] * df + right[1] * ds,
                        rng.uniform(0, period)))
    for stack in (0.0, period):
        for x, y, z in pts:
            mb.box(kit.T(x, y, z + stack) @ kit.Rx(0.14) @ kit.S(7.0, 7.0, streak), "m_rain")
    rain = mb.obj("S39Rain", coll)
    rain.visible_shadow = False
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "CONSTANT"
    try:
        for f in range(f0, f1 + 1):
            rain.location.z = 150.0 - ((f * speed) % period)
            rain.keyframe_insert("location", index=2, frame=f)
    finally:
        prefs.keyframe_new_interpolation_type = old
    show_only([rain], f0, f1)
    return rain


def build_whitecaps(coll, frames, region, count, seed=39, boost=1.7, size=(70.0, 150.0), late=True):
    """Low-poly white crests scattered over the storm sea (K48 shows chunky white shards on the
    waves): small flattened faceted blobs that ride the same swell as the sea mesh."""
    rng = random.Random(seed)
    kit.mat("m_cap", (0.95, 0.97, 0.98))
    mb = kit.MB()
    x0, x1, y0, y1 = region
    for _ in range(count):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        ang = rng.uniform(0, 3.14)
        for k in range(rng.randint(3, 6)):
            r = rng.uniform(*size)
            ox, oy = rng.uniform(-1, 1) * r * 2.2, rng.uniform(-1, 1) * r * 1.2
            ca, sa = math.cos(ang), math.sin(ang)
            mb.ico(kit.T(cx + ox * ca - oy * sa, cy + ox * sa + oy * ca, 8.0 + rng.uniform(0, 14)) @
                   kit.Rz(rng.uniform(0, 3)) @ kit.S(1.5, 0.9, 0.38), "m_cap", r=r, sub=0, jitter=0.25, rng=rng)
    ob = mb.obj("S39Whitecaps", coll)
    ob.visible_shadow = False
    vg = ob.vertex_groups.new(name="Swell")
    vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    add_swell(ob, names=("MapSwellA", "MapSwellB"), late=late)
    for mod in ob.modifiers:
        mod.strength *= boost
    show_only([ob], *frames)
    return ob


def build_s39(coll, lib_c, frames, end, anchor, azimuth, ship_start, boost=1.7):
    """S39 (K48): wide over a stormy sea. Ceylon (the S19 island, always in the scene) is a low
    green strip far off; a Dutch East Indiaman in the foreground pitches in the rough swell and
    comes about as the storm hits, her heading reversing from the way she was sailing to the
    way back toward Ceylon. Dark clouds hang over the far sea with rain under them.
    anchor: ground point the camera centres on; azimuth: view direction in degrees from +x."""
    f0, f1 = frames
    cey = Ceylon()
    az = math.radians(azimuth)
    fw = (math.cos(az), math.sin(az))
    storm_weather(frames)
    sea = build_s19_sea(coll, cey, frames, late=True, step=380.0, name="S39", swells=("MapSwellA", "MapSwellB"),
                        boost=boost, dark=0.86, desat=0.35,
                        region=(-14000.0, 33000.0, -24000.0, 10000.0))
    hide_during([o for o in bpy.data.objects if o.name.startswith(("Territory_", "Border_"))], f0, f1)
    obs = []
    # the ship: a broad turn, 190 deg (west, away from Ceylon) round through north to 10 deg
    ship, parts, _ = dutch_ship("S39Ship", coll, seed=23)
    scale = 90.0
    ship.scale = (scale, scale, scale)
    carrier = bpy.data.objects.new("S39ShipPath", None)
    coll.objects.link(carrier)
    ship.parent = carrier
    L, W = 38.0 * scale * 0.8, 10.0 * scale * 0.8
    turn0, turn1 = 0.30, 0.88
    head0, head1 = math.radians(190.0), math.radians(10.0)
    lift = lambda x, y, f: sea_lift(x, y, f, boost, names=("MapSwellA", "MapSwellB"), late=True)

    def heading(f):
        u = (f - f0) / (f1 - f0)
        t = min(1.0, max(0.0, (u - turn0) / (turn1 - turn0)))
        t = t * t * (3 - 2 * t)
        return head0 + (head1 - head0) * t           # decreasing: clockwise from above, through north

    # integrate the track so the turn is an arc (slower while she comes about)
    x, y = ship_start
    track = {}
    for f in range(f0 - 6, f1 + 8):
        h = heading(f)
        u = (f - f0) / (f1 - f0)
        sp = 3.0 if turn0 < u < turn1 else 4.5
        track[f] = (x, y, h)
        x += math.cos(h) * sp
        y += math.sin(h) * sp
    ph = 2.1

    def sail():
        for f in range(f0 - 6, f1 + 8, 3):
            x, y, h = track[f]
            ca, sa = math.cos(h), math.sin(h)
            zb, zs = lift(x + ca * L / 2, y + sa * L / 2, f), lift(x - ca * L / 2, y - sa * L / 2, f)
            zp, zt = lift(x - sa * W / 2, y + ca * W / 2, f), lift(x + sa * W / 2, y - ca * W / 2, f)  # port, starboard
            zc = lift(x, y, f)
            carrier.location = (x, y, 0.5 * zc + 0.25 * (zb + zs) + 40.0)
            carrier.rotation_euler = (0, 0, h - math.pi / 2)
            carrier.keyframe_insert("location", frame=f)
            carrier.keyframe_insert("rotation_euler", frame=f)
            pitch = math.atan2(zb - zs, L) * 0.8
            roll = -math.atan2(zt - zp, W) * 0.7 + math.radians(3.5 * math.sin(f / 9.0 + ph))
            ship.rotation_euler = (pitch + math.radians(2.0 * math.sin(f / 7.0)), roll, 0.0)
            ship.keyframe_insert("rotation_euler", frame=f)
    kit.keyframe_linear(sail)
    # white water round the hull: chunks of foam at the bow and along both sides
    rng = random.Random(48)
    kit.mat("m_cap", (0.95, 0.97, 0.98))
    mb = kit.MB()
    for k in range(46):
        side = rng.choice((-1, 1))
        yy = rng.uniform(-0.55, 0.5) * 38.0
        r = rng.uniform(1.6, 3.8)
        mb.ico(kit.T(side * rng.uniform(5.0, 9.0), yy, rng.uniform(-0.2, 0.8)) @ kit.Rz(rng.uniform(0, 3)) @ kit.S(1.2, 1.0, 0.5),
               "m_cap", r=r, sub=0, jitter=0.25, rng=rng)
    for k in range(16):
        mb.ico(kit.T(rng.uniform(-3, 3), 0.55 * 38.0 + rng.uniform(-1, 3), rng.uniform(-0.2, 1.0)) @ kit.Rz(rng.uniform(0, 3)),
               "m_cap", r=rng.uniform(1.8, 4.2), sub=0, jitter=0.25, rng=rng)
    spray = mb.obj("S39HullFoam", coll)
    spray.parent = ship
    spray.visible_shadow = False
    obs += parts + [spray]
    # the sea state: white crests, clouds with rain, all in the beat only
    obs.append(build_whitecaps(coll, frames, (anchor[0] - 9500, anchor[0] + 12000, anchor[1] - 8000, anchor[1] + 9000),
                               count=40, boost=boost, size=(130.0, 260.0)))
    clouds = build_storm_clouds(coll, lib_c, frames, anchor, fw,
                                [(4400, -3400, 1500, 78.0), (5000, 2900, 1600, 72.0), (5400, -300, 1400, 40.0)])
    build_map_rain(coll, frames, anchor, fw, [(4600, -3600, 2200), (5200, 2800, 2000)])
    show_only(obs + clouds, f0, f1)
    print("S39 built; sea", len(sea.data.vertices), "verts")
    return ship
