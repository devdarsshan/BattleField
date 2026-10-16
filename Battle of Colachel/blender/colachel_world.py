"""Colachel beach diorama: terrain, sea, sky, light, haze and the fishing village.

Coordinates: metres, Z up. The coastline runs diagonally (see shore_y); land is
on the +Y side of it. The village sits around the origin.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector, noise

import colachel_kit as kit
import kerala_geo as geo

TX0, TX1, TY0, TY1 = geo.TILE        # the diorama tile on the map
BATTERY = (87.5, 26.8)                # Travancore gun battery on a hillock behind the stockade (S06)


# ------------------------------------------------------------------ terrain
def shore_y(x):
    return -0.3 * x + 2.2 * math.sin(x / 13.0) + 1.2 * math.sin(x / 5.3 + 1.0)


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


def grass_line(x, y):
    return 26.0 + 7.0 * _n(x, y, 25, 3.1)


# Dutch stockade on the beach (rectangle in shore-aligned axes) and the Travancore camp inland.
STOCKADE = dict(center=(58.0, -2.0), axis_deg=-16.7, half_u=15.0, half_v=12.0)
CAMP = (62.0, 56.0)
CAMP_R = 30.0


def stockade_local(x, y):
    """(u, v) of a point in the stockade's frame."""
    a = math.radians(STOCKADE["axis_deg"])
    dx, dy = x - STOCKADE["center"][0], y - STOCKADE["center"][1]
    return dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)


def stockade_world(u, v):
    a = math.radians(STOCKADE["axis_deg"])
    cx, cy = STOCKADE["center"]
    return cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a)


def in_stockade(x, y, pad=0.0):
    u, v = stockade_local(x, y)
    return abs(u) < STOCKADE["half_u"] + pad and abs(v) < STOCKADE["half_v"] + pad


def in_camp(x, y, pad=0.0):
    return math.hypot(x - CAMP[0], y - CAMP[1]) < CAMP_R + pad


def _smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def height(x, y):
    d = y - shore_y(x)
    if d < 0:
        return max(-3.0, d * 0.2) - 0.04
    h = 0.75 * (1 - math.exp(-d / 9.0)) + 0.22 * _n(x, y, 9, 1.3) * min(1.0, d / 8.0)
    g = grass_line(x, y)
    if d > g:
        h += (d - g) * 0.08
    bx, by = BATTERY
    h += 12.0 * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / 16.0 ** 2)
    h0 = 70 + 75 * _smooth(22, 48, x)          # hills start further inland behind the camp
    if d > h0:
        k = min(1.0, (d - h0) / 80.0)
        ridge = 1.0 - abs(_n(x, y, 55, 7.7))
        h += k * (12 + 38 * ridge ** 2) + (d - h0) * 0.12
    return h


def make_land(collection, seed=1):
    rng = random.Random(seed)
    xs = [x for x in range(-700, -150, 9)] + [x * 1.0 for x in range(-150, 222, 3)] + \
        [x for x in range(222, 400, 9)] + [TX1]
    ys = [y for y in range(-160, -30, 9)] + [y * 1.0 for y in range(-30, 120, 3)] + \
        [y for y in range(120, 420, 9)] + [TY1]
    bm = bmesh.new()
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                step = 3.0 if (-150 < x < 222 and -30 < y < 120) else 9.0
                jx, jy = rng.uniform(-0.3, 0.3) * step, rng.uniform(-0.3, 0.3) * step
            px, py = x + jx, y + jy
            row.append(bm.verts.new((px, py, height(px, py))))
        grid.append(row)
    sand, wet, grass = 0, 1, 2
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            c = f.calc_center_median()
            d = c.y - shore_y(c.x)
            sandy = in_stockade(c.x, c.y, 3) or                 math.hypot(c.x - CAMP[0], c.y - CAMP[1]) < CAMP_R - 4 + 5 * _n(c.x, c.y, 8, 2.2)
            if d > grass_line(c.x, c.y) and not sandy:
                f.material_index = grass
            elif d < 1.6:
                f.material_index = wet
            else:
                f.material_index = sand
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("Land")
    bm.to_mesh(me)
    bm.free()
    for m in ("sand", "sand_wet", "grass"):
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Land", me)
    collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------------- sea
SEA_SHALLOW = (0.50, 0.72, 0.76)
SEA_DEEP = (0.44, 0.54, 0.74)
SEA_FOAM = (0.86, 0.88, 0.88)


def sea_material():
    m = bpy.data.materials.get("Sea")
    if m:
        return m
    m = bpy.data.materials.new("Sea")
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    mix = _color_mix(nt, "StormMix", (0.27, 0.35, 0.39))
    nt.links.new(attr.outputs["Color"], _sock(mix.inputs, "A_Color"))
    nt.links.new(_sock(mix.outputs, "Result_Color"), bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.38
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    m.diffuse_color = (*kit.srgb_to_linear(SEA_DEEP), 1)
    return m


def make_sea(collection, seed=2):
    rng = random.Random(seed)
    xs = [x for x in range(-700, -160, 12)] + [x * 1.0 for x in range(-160, 160, 3)] + \
         [x for x in range(160, 400, 12)] + [TX1]
    ys = [y for y in range(-700, -150, 12)] + [y * 1.0 for y in range(-150, 60, 3)] + \
         [y for y in range(60, 420, 12)] + [TY1]
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new("Col")
    dl = bm.verts.layers.deform.verify()
    lin = [kit.srgb_to_linear(c) for c in (SEA_SHALLOW, SEA_DEEP, SEA_FOAM)]
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            step = 3.0 if (-160 <= x < 160 and -150 <= y < 60) else 12.0
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                jx, jy = rng.uniform(-0.3, 0.3) * step, rng.uniform(-0.3, 0.3) * step
            px, py = x + jx, y + jy
            v = bm.verts.new((px, py, 0.0))
            depth = shore_y(px) - py
            t = max(0.0, min(1.0, depth / 25.0))
            t = t * t * (3 - 2 * t)
            c = [lin[0][k] * (1 - t) + lin[1][k] * t for k in range(3)]
            if depth < 1.2:
                u = max(0.0, 1.0 - max(0.0, depth) / 1.2)
                c = [c[k] * (1 - u) + lin[2][k] * u for k in range(3)]
            shade = rng.uniform(0.95, 1.05)
            v[col] = (c[0] * shade, c[1] * shade, c[2] * shade, 1.0)
            edge = min(px - TX0, TX1 - px, py - TY0, TY1 - py)
            mask = _smooth(0, 40, edge)                      # waves die out at the tile edge
            v[dl][0] = mask
            v[dl][1] = mask * _smooth(4, 45, depth)          # storm swell only offshore
            row.append(v)
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("Sea")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(sea_material())
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Sea", me)
    collection.objects.link(ob)
    ob.vertex_groups.new(name="SwellMask")
    ob.vertex_groups.new(name="Offshore")
    return ob


def animate_sea(sea, rig, frames, storm=()):
    drv = bpy.data.objects.new("WaveDriver", None)
    rig.objects.link(drv)
    calm_storm = {"SwellA": (0.65, 1.3), "SwellB": (0.18, 0.4), "Storm": (0.0, 3.4)}
    for name, scale, strength, travel in (("SwellA", 7.0, 0.65, (3.0, 9.0)),
                                          ("SwellB", 2.6, 0.18, (-4.0, 3.0)),
                                          ("Storm", 22.0, 0.0, (-6.0, 40.0))):
        tex = bpy.data.textures.new(name, "CLOUDS")
        tex.noise_scale = scale
        tex.noise_depth = 0
        mod = sea.modifiers.new(name, "DISPLACE")
        mod.texture = tex
        mod.texture_coords = "OBJECT"
        e = bpy.data.objects.new(name + "Driver", None)
        rig.objects.link(e)
        mod.texture_coords_object = e
        mod.strength = strength
        mod.mid_level = 0.5
        mod.vertex_group = "Offshore" if name == "Storm" else "SwellMask"
        a, b = calm_storm[name]
        key_storm(mod, "strength", storm, a, b)

        def keys(e=e, travel=travel):
            e.location = (0, 0, 0)
            e.keyframe_insert("location", frame=1)
            e.location = (travel[0], travel[1], 0)
            e.keyframe_insert("location", frame=frames)
        kit.keyframe_linear(keys)
    bpy.data.objects.remove(drv)


# --------------------------------------------------------------- sky & light
def setup_world(haze_density=0.0032):
    w = bpy.data.worlds.new("Dawn")
    bpy.context.scene.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value = -0.05
    mr.inputs["From Max"].default_value = 0.7
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (*kit.srgb_to_linear((0.99, 0.86, 0.78)), 1)
    mid = cr.elements.new(0.35)
    mid.color = (*kit.srgb_to_linear((0.95, 0.86, 0.82)), 1)
    cr.elements[-1].position = 1.0
    cr.elements[-1].color = (*kit.srgb_to_linear((0.84, 0.82, 0.88)), 1)
    mix = _color_mix(nt, "StormMix", (0.50, 0.53, 0.58))
    nt.links.new(ramp.outputs["Color"], _sock(mix.inputs, "A_Color"))
    nt.links.new(_sock(mix.outputs, "Result_Color"), bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.95
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def add_haze(collection, density=0.0008, color=(0.97, 0.88, 0.82)):
    """Aerial-perspective haze as a big bounded volume box. (A world volume
    blacks out the sky in EEVEE, so the haze must be an object.)"""
    m = bpy.data.materials.new("Haze")
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
    vol.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    mb = kit.MB()
    mb.box(kit.T(-100, 100, 90) @ kit.S(1800, 1600, 200), "Haze")
    ob = mb.obj("Haze", collection)
    ob.data.materials[0] = m
    ob.display_type = "BOUNDS"
    return ob


# Low sun far up the coast, so shadows fall toward the camera and to the right.
def add_sun(collection, direction=(0.7, -0.45, -0.38), energy=8.0, color=(1.0, 0.86, 0.72), angle=9.0):
    ld = bpy.data.lights.new("Sun", "SUN")
    ld.energy = energy
    ld.color = color
    ld.angle = math.radians(angle)
    sun = bpy.data.objects.new("Sun", ld)
    collection.objects.link(sun)
    sun.rotation_euler = Vector(direction).normalized().to_track_quat("-Z", "Y").to_euler()
    return sun


def setup_render(width=1280, height=720, samples=48):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = width
    sc.render.resolution_y = height
    sc.render.resolution_percentage = 100
    sc.render.fps = kit.FPS
    ee = sc.eevee
    ee.taa_render_samples = samples
    ee.use_raytracing = True
    ee.use_shadows = True
    ee.volumetric_end = 1500
    ee.volumetric_tile_size = "8"
    ee.use_volumetric_shadows = True
    try:
        ee.fast_gi_method = "GLOBAL_ILLUMINATION"
        ee.use_fast_gi = True
    except Exception:
        pass
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium Low Contrast", "AgX - Base Contrast", "None"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    return sc


# ------------------------------------------------------------------ village
def build_village(coll, props_c, plants_c, people_c, lib_c, frames):
    rng = random.Random(21)
    g = height

    def put(src, name, c, x, y, rz=0.0, s=1.0, sink=0.05):
        return kit.instance(src, name, c, (x, y, g(x, y) - sink), rot_z=rz, scale=s)

    # ---- library (hidden sources, instanced below)
    gable = [kit.make_hut_gable(f"LibHutGable{i}", lib_c, w=w, d=d, h=h, seed=i)
             for i, (w, d, h) in enumerate([(4.2, 3.4, 2.1), (5.0, 3.8, 2.3), (3.8, 3.2, 2.0)])]
    hip = [kit.make_hut_hip(f"LibHutHip{i}", lib_c, seed=10 + i) for i in range(2)]
    palms = [kit.make_palm(f"LibPalm{i}", lib_c, seed=i, height=7.5 + 0.5 * i) for i in range(6)]
    bushes = [kit.make_bush(f"LibBush{i}", lib_c, seed=i, size=1.0 + 0.2 * i) for i in range(3)]
    trees = [kit.make_tree(f"LibTree{i}", lib_c, seed=i, height=6 + i) for i in range(4)]
    rocks = [kit.make_rock(f"LibRock{i}", lib_c, seed=i, size=0.5 + 0.3 * i) for i in range(3)]
    boat = kit.make_boat("LibBoat", lib_c)
    crate = kit.make_crate("LibCrate", lib_c)
    barrel = kit.make_barrel("LibBarrel", lib_c)
    fence = kit.make_fence("LibFence", lib_c)
    stump = kit.make_stump("LibStump", lib_c)
    jetty = kit.make_jetty("Jetty", props_c, length=11.0)
    for ob in lib_c.objects:
        kit.hide_source(ob)

    # ---- huts: hero row (end of clip 01) plus the hipped ones nearer the start camera
    huts = [
        (gable[0], -9.0, 15.0, -0.10, 1.0),
        (gable[1], 0.5, 17.0, 0.05, 1.0),
        (gable[2], 10.0, 13.5, 0.20, 1.0),
        (hip[0], 18.0, 9.0, 0.35, 1.0),
        (hip[1], 25.5, 14.0, 0.30, 1.05),
        (gable[0], 31.0, 7.0, 0.45, 0.95),
        (gable[2], -19.0, 21.0, -0.2, 0.9),
        (hip[0], 34.5, 15.5, 0.4, 0.9),
    ]
    for i, (src, x, y, rz, s) in enumerate(huts):
        put(src, f"Hut{i}", coll, x, y, rz, s, sink=0.1)

    # ---- jetty: from the beach out to sea, angled seaward
    jx, jy = -8.0, shore_y(-8.0) + 3.0
    jetty.location = (jx, jy, 0)
    jetty.rotation_euler[2] = math.radians(150)

    # ---- boats: beached along the waterline and a few afloat
    for i, (x, dd, rz) in enumerate([(-22, 0.5, 2.2), (-28, 0.2, 2.6), (6, 0.2, 2.4), (16, -0.4, 2.6),
                                     (12, -0.6, 2.8), (21, 0.4, 2.5), (28, -0.3, 2.7)]):
        y = shore_y(x) + dd
        put(boat, f"Boat{i}", props_c, x, y, rz, 1.0, sink=0.15 if dd >= 0 else 0.0)
    for i, (x, y, rz) in enumerate([(-30, -2, 2.0), (-10.5, -2.0, 2.6), (-40, 3, 1.6), (8, -14, 2.9), (-4, -12, 2.4)]):
        kit.instance(boat, f"BoatSea{i}", props_c, (x, y + shore_y(x), -0.25), rot_z=rz)

    # ---- crates, barrels, fences, stumps around the huts and jetty
    def scatter(src, name, spots, c=props_c, srange=(0.85, 1.15)):
        for i, (x, y) in enumerate(spots):
            put(src, f"{name}{i}", c, x, y, rng.uniform(-0.5, 0.5), rng.uniform(*srange), sink=0.02)

    scatter(crate, "Crate", [(-7.2, 11.6), (-6.4, 12.2), (2.6, 13.6), (3.4, 13.4), (2.9, 14.4), (-2.0, 9.5),
                             (6.0, 8.0), (12.4, 10.6), (13.1, 10.2), (-11.5, 9.5), (-11.0, 10.4), (17.0, 6.0),
                             (21.0, 9.0), (-4.5, 5.0), (8.5, 4.0)])
    scatter(barrel, "Barrel", [(-12.2, 12.3), (-12.8, 11.6), (-5.5, 12.9), (4.2, 14.1), (13.8, 11.2),
                               (-10.5, 9.0), (22.0, 10.4)])
    for i, (x, y, rz, s) in enumerate([(-15.0, 14.5, 0.1, 1.0), (-4.8, 18.0, 0.0, 0.8), (6.0, 16.0, 0.15, 0.9),
                                       (13.0, 15.5, 0.3, 1.0), (21.5, 6.0, 0.4, 0.8), (-16.5, 10.0, 1.4, 0.9)]):
        put(fence, f"Fence{i}", props_c, x, y, rz, s, sink=0.02)
    scatter(stump, "Stump", [(6.5, 4.5), (-1.0, 3.5), (15.5, 3.0)])
    for i, (x, y) in enumerate([(9.0, 5.5), (26.0, 4.0), (-26.0, 8.0), (-34.0, 12.0)]):
        put(rocks[i % 3], f"Rock{i}", props_c, x, y, rng.uniform(0, 3), 1.0, sink=0.1)

    # ---- palms: grove west of the hero huts, a line along the coast, some behind the village
    palm_spots = [(-16, 9), (-21, 6), (-24, 12), (-27, 7), (-29, 15), (-32, 10), (-36, 14), (-13, 20),
                  (-23, 19), (-40, 9), (-45, 16), (-52, 13), (-60, 20), (-68, 18), (-76, 25), (-85, 27),
                  (-95, 33), (-105, 36), (-118, 42), (-132, 47), (-146, 55), (-160, 58),
                  (-4, 23), (6, 22), (14, 21), (22, 20), (29, 22), (38, 12), (41, 4), (-6, 28),
                  (18, 26), (-30, 25), (45, 18)]
    for i, (x, y) in enumerate(palm_spots):
        put(palms[i % len(palms)], f"Palm{i}", plants_c, x + rng.uniform(-1, 1), y + rng.uniform(-1, 1),
            rng.uniform(0, 6.28), rng.uniform(0.9, 1.2), sink=0.1)
    for i in range(40):
        x, y = rng.uniform(-60, 45), rng.uniform(5, 26)
        d = y - shore_y(x)
        if d < 4 or any(abs(x - hx) < 4 and abs(y - hy) < 4 for _, hx, hy, _, _ in huts):
            continue
        put(bushes[i % 3], f"Bush{i}", plants_c, x, y, rng.uniform(0, 6.28), rng.uniform(0.8, 1.4), sink=0.05)

    # ---- broad-leaf woods behind the village and up the hills
    k = 0
    for i in range(420):
        x, y = rng.uniform(-260, 120), rng.uniform(15, 260)
        d = y - shore_y(x)
        if d < grass_line(x, y) - 4 or in_stockade(x, y, 6) or in_camp(x, y, 4) or (46 < x < 74 and y < 62) or \
                math.hypot(x - BATTERY[0], y - BATTERY[1]) < 22 or not (TX0 + 8 < x < TX1 - 8 and y < TY1 - 8):
            continue
        put(trees[k % 4], f"Tree{k}", plants_c, x, y, rng.uniform(0, 6.28),
            rng.uniform(0.8, 1.3) * (1 + min(1.0, max(0, d - 60) / 120)), sink=0.3)
        k += 1

    # ---- villagers
    walkers = [
        # (waypoints, robe, cloth)
        ([(-1.5, 7.5), (-0.5, 11.5), (0.0, 13.5)], True, "cloth_t"),
        ([(-5.0, 12.5), (-2.5, 10.0)], False, "cloth_w"),
        ([(-3.5, 12.5), (-1.0, 9.8)], False, "cloth_w"),
        ([(7.5, 12.0), (8.5, 9.0)], False, "cloth_r"),
        ([(-8.0, 9.0), (-11.0, 6.0)], False, "cloth_w"),
        ([(14.0, 9.5), (16.0, 12.0)], True, "cloth_t"),
    ]
    for i, (wp, robe, cloth) in enumerate(walkers):
        root, parts = kit.make_villager(f"Villager{i}", people_c, seed=i, robe=robe, cloth=cloth)
        kit.animate_walk(root, parts, wp, g, end=frames, stride_frames=14 + (i % 3) * 2, speed=0.55)


# ------------------------------------------------------- Dutch stockade (S02)
def _face(dx, dy):
    """rot_z that turns a +Y-facing asset to look along (dx, dy)."""
    return math.atan2(dy, dx) - math.pi / 2


def build_stockade(coll, lib_c, frames):
    rng = random.Random(41)
    g = height
    st = STOCKADE
    axis = math.radians(st["axis_deg"])
    kit.make_stockade("Stockade", coll, st["center"], st["axis_deg"], st["half_u"], st["half_v"], g,
                      gate=3.5, seed=3)
    hut = bpy.data.objects["LibHutGable0"]
    hut2 = bpy.data.objects["LibHutGable1"]
    for i, (src, u, v) in enumerate([(hut, -6.5, 7.6), (hut2, 5.5, 7.4)]):
        x, y = stockade_world(u, v)
        kit.instance(src, f"StockadeHut{i}", coll, (x, y, g(x, y) - 0.1), rot_z=axis)
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    sack = kit.make_sack("LibSack", lib_c)
    for i, (src, u, v) in enumerate([(crate, -10.5, 6.0), (crate, -11.2, 5.2), (barrel, -9.6, 4.8),
                                     (barrel, 13.6, 6.0), (crate, 0.0, 9.5), (sack, -1.2, 9.8)]):
        x, y = stockade_world(u, v)
        kit.instance(src, f"StockadeProp{i}", coll, (x, y, g(x, y) - 0.02), rot_z=rng.uniform(0, 6.28))

    # S05: hungry soldiers sitting round the last, nearly empty rice sacks
    sacks_c = (11.0, 3.3)
    for i, (u, v, sz) in enumerate([(10.7, 3.0, 0.35), (11.5, 3.6, 0.3), (11.1, 3.9, 0.22)]):
        x, y = stockade_world(u, v)
        ob = kit.instance(sack, f"EmptySack{i}", coll, (x, y, g(x, y) - 0.02), rot_z=rng.uniform(0, 6.28),
                          scale=(1.1, 1.1, sz))
    x, y = stockade_world(10.9, 3.4)
    mbr = kit.MB()
    for k in range(9):
        mbr.ico(kit.T(rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.12) @ kit.S(1, 1, 0.5), "rice",
                r=rng.uniform(0.05, 0.09), sub=1)
    pile = mbr.obj("RicePile", coll)
    pile.location = (x, y, g(x, y))
    sitters = [kit.make_figure(f"LibDutchSit{i}", lib_c, "dutch", seed=30 + i, pose="sit") for i in range(3)]
    for i, (u, v) in enumerate([(9.4, 2.0), (10.6, 1.6), (12.1, 2.1), (13.0, 3.3), (9.1, 3.8), (12.6, 4.6),
                                (10.3, 5.0)]):
        x, y = stockade_world(u, v)
        cx, cy = stockade_world(*sacks_c)
        ob = kit.instance(sitters[i % 3], f"DutchSitting{i}", coll, (x, y, g(x, y) - 0.02),
                          rot_z=_face(cx - x, cy - y) + rng.uniform(-0.25, 0.25))
        kit.animate_idle(ob, rng, 1, frames, amount=0.025)

    # garrison drawn up in ranks, facing west along the beach (toward the camera's approach)
    dutch = [kit.make_figure(f"LibDutch{i}", lib_c, "dutch", seed=i) for i in range(3)]
    face = _face(-math.cos(axis), -math.sin(axis))
    n = 0
    for r, v in enumerate([-7.6, -6.0, -4.4, -2.8, -1.2, 0.4]):
        u = -9.0
        while u <= 9.0:
            x, y = stockade_world(u + rng.uniform(-0.12, 0.12), v + rng.uniform(-0.12, 0.12))
            ob = kit.instance(dutch[n % 3], f"Dutch{n}", coll, (x, y, g(x, y) - 0.02),
                              rot_z=face + rng.uniform(-0.08, 0.08), scale=rng.uniform(0.96, 1.04))
            kit.animate_idle(ob, rng, 1, frames, amount=0.02)
            u += 1.35
            n += 1


# ------------------------------------------------------ Travancore camp (S03)
def build_camp(coll, lib_c, frames):
    rng = random.Random(77)
    g = height
    cx, cy = CAMP

    def at(dx, dy, src, name, rz=0.0, s=1.0, sink=0.03):
        x, y = cx + dx, cy + dy
        return kit.instance(src, name, coll, (x, y, g(x, y) - sink), rot_z=rz, scale=s)

    canopy = kit.make_canopy("LibCanopy", lib_c)
    at(0, 0, canopy, "RoyalCanopy", rz=math.pi)            # table side toward -Y (the approach)
    king = kit.make_figure("LibKing", lib_c, "king", seed=1)
    k = at(0, 0.9, king, "MarthandaVarma", rz=math.pi, s=1.06)
    kit.animate_idle(k, rng, 1, frames, amount=0.015)
    cmd = [kit.make_figure(f"LibCommander{i}", lib_c, "commander", seed=i) for i in range(2)]
    for i, (dx, dy) in enumerate([(-1.7, 0.4), (1.7, 0.4), (-2.0, -0.9), (2.0, -0.9)]):
        ob = at(dx, dy, cmd[i % 2], f"Commander{i}", rz=_face(-dx, -0.3 - dy))
        kit.animate_idle(ob, rng, 1, frames, amount=0.02)
    nair = [kit.make_figure(f"LibNair{i}", lib_c, "nair" if i % 2 else "nair_spear", seed=i) for i in range(4)]
    for i, dx in enumerate((-2.9, 2.9)):
        at(dx, -2.4, nair[0], f"Guard{i}", rz=math.pi)

    # tents in a loose ring, leaving the lane toward the sea (-Y) open
    cone = [kit.make_cone_tent(f"LibConeTent{i}", lib_c, r=2.0 + 0.4 * i, h=3.2 + 0.4 * i) for i in range(2)]
    ridge = kit.make_ridge_tent("LibRidgeTent", lib_c)
    spots = []

    def free(dx, dy, r):
        return all(math.hypot(dx - a, dy - b) > r + rb for a, b, rb in spots)

    def lane(dx, dy):
        return dy < -3 and abs(dx) < 6 + (-dy) * 0.25

    tries = 0
    while len([1 for s in spots if s[2] > 1.5]) < 22 and tries < 2000:
        tries += 1
        a = rng.uniform(0, math.tau)
        r = rng.uniform(7, 27)
        dx, dy = r * math.cos(a), r * math.sin(a)
        if lane(dx, dy) or not free(dx, dy, 2.6) or (1 < dx < 9 and 3 < dy < 12):
            continue
        spots.append((dx, dy, 2.6))
        src = ridge if rng.random() < 0.25 else rng.choice(cone)
        at(dx, dy, src, f"Tent{len(spots)}", rz=_face(-dx, -dy) + rng.uniform(-0.3, 0.3), s=rng.uniform(0.9, 1.1))
    palms = [bpy.data.objects[f"LibPalm{i}"] for i in range(6)]
    for i in range(16):
        for _ in range(50):
            a = rng.uniform(0, math.tau)
            r = rng.uniform(6, 32)
            dx, dy = r * math.cos(a), r * math.sin(a)
            if free(dx, dy, 1.0) and not (dy < -3 and abs(dx) < 9) and not (-1 < dx < 11 and 1 < dy < 15):
                spots.append((dx, dy, 1.0))
                at(dx, dy, palms[i % 6], f"CampPalm{i}", rz=rng.uniform(0, 6.28), s=rng.uniform(0.85, 1.15), sink=0.1)
                break
    # soldiers standing about the camp, and a few walking through it
    for i in range(26):
        for _ in range(50):
            a = rng.uniform(0, math.tau)
            r = rng.uniform(4.5, 24)
            dx, dy = r * math.cos(a), r * math.sin(a)
            if free(dx, dy, 0.5):
                spots.append((dx, dy, 0.5))
                ob = at(dx, dy, nair[i % 4], f"Nair{i}", rz=rng.uniform(0, 6.28))
                kit.animate_idle(ob, rng, 1, frames, amount=0.03)
                break
    start = max(1, frames - 720)
    paths = [[(-9, -8), (-2, -5), (6, -9)], [(8, -3), (3, -12)], [(-6, -14), (-1, -6), (-4, 2)],
             [(11, -6), (4, -2)], [(-12, -2), (-5, -3)], [(2, -16), (7, -8)]]
    for i, wp in enumerate(paths):
        root, parts = kit.make_walker(f"NairWalker{i}", coll, "nair_spear" if i % 2 else "nair", seed=20 + i)
        kit.animate_walk(root, parts, [(cx + x, cy + y) for x, y in wp], g, start=start, end=frames,
                         stride_frames=15, speed=0.9)


# ----------------------------------------------------------- Dutch fleet (S04)
def build_fleet(coll, frames, storm=()):
    rng = random.Random(5)
    ships = [kit.make_ship(f"Ship{i}", coll, length=36 + 3 * i, beam=9.5 + 0.5 * i, seed=i) for i in range(3)]
    placements = [(ships[0], 46, -92, 200), (ships[1], 74, -104, 186), (ships[2], 22, -112, 208),
                  (ships[0], 98, -88, 192)]
    for i, (src, x, y, rot) in enumerate(placements):
        ob = src if i < 3 else kit.instance(src, f"Ship{i}", coll, (0, 0, 0))
        ob.location = (x, y, -0.4)
        ob.rotation_euler = (0, 0, math.radians(rot))
        f = 1 + rng.randint(0, 40)
        k = 0
        while f <= frames + 60:
            s = 1 if k % 2 == 0 else -1
            w = storm_at(storm, f)
            ob.rotation_euler = (math.radians((1.0 + 6.0 * w) * s), math.radians((0.6 + 3.0 * w) * -s),
                                 math.radians(rot))
            ob.location.z = -0.4 + (0.15 + 1.1 * w) * s
            ob.keyframe_insert("rotation_euler", frame=f)
            ob.keyframe_insert("location", frame=f)
            f += rng.randint(50, 70) - int(25 * w)
            k += 1
    boat = bpy.data.objects["LibBoat"]
    for i, (x, y, rz) in enumerate([(52, -80, 2.2), (60, -86, 1.9), (30, -100, 2.6)]):
        kit.instance(boat, f"ShipBoat{i}", coll, (x, y, -0.25), rot_z=rz)


# ------------------------------------------------------------------ weather
# A weather timeline is a list of (frame, value) points; storm 0 = clear dawn, 1 = monsoon.
def _sock(socks, ident):
    return next(s for s in socks if s.identifier == ident)


def _color_mix(nt, name, rgb):
    mix = nt.nodes.new("ShaderNodeMix")
    mix.name = name
    mix.data_type = "RGBA"
    _sock(mix.inputs, "B_Color").default_value = (*kit.srgb_to_linear(rgb), 1)
    mix.inputs["Factor"].default_value = 0.0
    return mix


def storm_at(points, f):
    if not points:
        return 0.0
    if f <= points[0][0]:
        return points[0][1]
    for (f0, v0), (f1, v1) in zip(points, points[1:]):
        if f0 <= f <= f1:
            t = (f - f0) / max(1, f1 - f0)
            return v0 + (v1 - v0) * t * t * (3 - 2 * t)
    return points[-1][1]


def key_storm(owner, attr, points, calm, storm, index=-1):
    """Key owner.attr at each weather point, blending calm -> storm values."""
    for f, w in points:
        if isinstance(calm, tuple):
            val = tuple(c + (s_ - c) * w for c, s_ in zip(calm, storm))
        else:
            val = calm + (storm - calm) * w
        setattr(owner, attr, val)
        owner.keyframe_insert(attr, frame=f, index=index)


def apply_weather(sun, haze, weather):
    storm = weather.get("storm", [])
    if not storm:
        return
    lin = kit.srgb_to_linear
    key_storm(sun.data, "energy", storm, 8.0, 1.6)
    key_storm(sun.data, "color", storm, (1.0, 0.86, 0.72), (0.80, 0.86, 0.96))
    w = bpy.context.scene.world.node_tree
    key_storm(w.nodes["StormMix"].inputs["Factor"], "default_value", storm, 0.0, 0.85)
    bg = next(n for n in w.nodes if n.bl_idname == "ShaderNodeBackground")
    key_storm(bg.inputs["Strength"], "default_value", storm, 0.95, 0.6)
    sea = bpy.data.materials["Sea"].node_tree
    key_storm(sea.nodes["StormMix"].inputs["Factor"], "default_value", storm, 0.0, 0.75)
    vol = next(n for n in haze.data.materials[0].node_tree.nodes if n.bl_idname == "ShaderNodeVolumePrincipled")
    key_storm(vol.inputs["Color"], "default_value", storm, (*lin((0.97, 0.88, 0.82)), 1), (*lin((0.62, 0.65, 0.70)), 1))
    # haze thickens in the storm and is gone once the camera is up at map height
    dens = [(f, 0.0008 + 0.0012 * v) for f, v in storm]
    for f, v in weather.get("map", []):
        dens.append((f, None if v == 0 else 0.0))
    dens.sort(key=lambda t: t[0])
    last = 0.0008
    for f, v in dens:
        if v is None:
            v = 0.0008 + 0.0012 * storm_at(storm, f)
        vol.inputs["Density"].default_value = v
        vol.inputs["Density"].keyframe_insert("default_value", frame=f)


def build_clouds(coll, weather):
    """Storm clouds roll in from the sea, then thin away as the camera rises to the map."""
    storm = weather.get("storm", [])
    if not storm:
        return
    rng = random.Random(91)
    start, full = storm[0][0], storm[1][0]
    clear0, clear1 = storm[2][0], storm[3][0]
    srcs = [kit.make_cloud(f"LibCloud{i}", coll, seed=i, size=1.0 + 0.15 * i) for i in range(4)]
    for ob in srcs:
        kit.hide_source(ob)
    for i in range(34):
        x, y = rng.uniform(-220, 300), rng.uniform(-300, 60)
        z = rng.uniform(85, 140)
        ob = kit.instance(srcs[i % 4], f"Cloud{i}", coll, (x, y - 160, z), rot_z=rng.uniform(0, 6.28), scale=0.0)
        sz = rng.uniform(0.8, 1.4)
        for f, loc, sc in ((start, (x, y - 160, z), 0.0), (full, (x, y, z), sz),
                           (clear0, (x, y + 25, z), sz), (clear1, (x + 60, y + 80, z + 30), 0.0)):
            ob.location = loc
            ob.scale = (sc, sc, sc)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("scale", frame=f)


def build_rain(coll, cam, rain_points, frames, speed=0.42):
    """Rain that follows the camera across the ground; scrolls down every frame."""
    if not rain_points:
        return None
    rain = kit.make_rain("Rain", coll)
    c = rain.constraints.new("COPY_LOCATION")
    c.target = cam
    c.use_z = False
    for f, v in rain_points:
        rain.scale = (v, v, v) if v > 0 else (0.0001, 0.0001, 0.0001)
        rain.keyframe_insert("scale", frame=f)
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "CONSTANT"
    try:
        f0, f1 = rain_points[0][0], rain_points[-1][0]
        for f in range(f0, f1 + 1):
            rain.location.z = -((f * speed * kit.RAIN_PERIOD / 25.0) % kit.RAIN_PERIOD)
            rain.keyframe_insert("location", index=2, frame=f)
    finally:
        prefs.keyframe_new_interpolation_type = old
    return rain


# ---------------------------------------------------------------- tile sides
def make_tile_skirt(coll, step=8.0):
    """Layered soil sides of the diorama tile, from its surface down to the map sheet."""
    mb = kit.MB()
    z0 = geo.MAP_Z
    corners = [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)]
    pts = []
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / step))
        for k in range(n):
            pts.append((ax + (bx - ax) * k / n, ay + (by - ay) * k / n))
    pts.append(pts[0])

    def top(x, y):
        return max(height(x, y), 0.0)

    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        ta, tb = top(ax, ay), top(bx, by)
        wet = height(ax, ay) < 0 and height(bx, by) < 0
        bands = [(0.0, 1.4, "sea_side" if wet else ("grass" if ta > 1.6 else "sand")),
                 (1.4, 3.0, "soil"), (3.0, None, "soil_dk")]
        for d0, d1, m in bands:
            za0, zb0 = ta - d0, tb - d0
            za1 = z0 if d1 is None else ta - d1
            zb1 = z0 if d1 is None else tb - d1
            v = [mb.bm.verts.new(p) for p in ((ax, ay, za0), (bx, by, zb0), (bx, by, zb1), (ax, ay, za1))]
            mb.face(v, m)
    kit.mat("sea_side", (0.27, 0.52, 0.60))
    return mb.obj("TileSides", coll)


# ----------------------------------------------------------- battery (S06)
def build_battery(coll, lib_c, frames, shot=None):
    """Travancore guns on the hillock behind palms, aimed at the stockade."""
    rng = random.Random(61)
    g = height
    bx, by = BATTERY
    cx, cy = STOCKADE["center"]
    dx, dy = cx - bx, cy - by
    L = math.hypot(dx, dy)
    fx, fy = dx / L, dy / L                      # toward the stockade
    px_, py_ = -fy, fx                           # sideways
    aim = math.atan2(fy, fx) - math.pi / 2
    cannon = kit.make_cannon("LibCannon", lib_c)
    guns = []
    for i, off in enumerate((-1.8, 1.8)):
        x, y = bx + px_ * off, by + py_ * off
        guns.append(kit.instance(cannon, f"Cannon{i}", coll, (x, y, g(x, y) - 0.05), rot_z=aim))
    # earth rampart in front, with gaps for the muzzles
    soil = kit.MB(bevel=0.05)
    for k in range(-6, 7):
        if abs(k * 0.62 - 1.8) < 0.7 or abs(k * 0.62 + 1.8) < 0.7:
            continue
        x, y = bx + fx * 2.6 + px_ * k * 0.62, by + fy * 2.6 + py_ * k * 0.62
        soil.box(kit.T(x - bx, y - by, g(x, y) - g(bx, by) + 0.35) @ kit.Rz(aim) @ kit.S(0.6, 0.7, 0.75), "soil")
    ramp = soil.obj("Rampart", coll)
    ramp.location = (bx, by, g(bx, by))
    nair = bpy.data.objects["LibNair0"]
    cmdr = bpy.data.objects["LibCommander0"]
    for i, (a, b, src) in enumerate([(-3.2, -0.8, nair), (-0.4, -1.2, nair), (0.6, -1.0, nair), (3.3, -0.6, nair),
                                     (0.0, -3.0, cmdr)]):
        x, y = bx + px_ * a + fx * b, by + py_ * a + fy * b
        ob = kit.instance(src, f"Gunner{i}", coll, (x, y, g(x, y) - 0.03), rot_z=aim + rng.uniform(-0.4, 0.4))
        kit.animate_idle(ob, rng, 1, frames, amount=0.03)
    # palms screening the battery, leaving the line of sight to the guns open
    palms = [bpy.data.objects[f"LibPalm{i}"] for i in range(6)]
    for i, (ang, r) in enumerate([(-62, 12), (-38, 15), (-22, 10), (24, 11), (40, 14), (66, 12), (-80, 17),
                                  (85, 16), (180, 9), (150, 13)]):
        a = math.radians(ang)
        x = bx + (fx * math.cos(a) - fy * math.sin(a)) * r
        y = by + (fx * math.sin(a) + fy * math.cos(a)) * r
        kit.instance(palms[i % 6], f"BatteryPalm{i}", coll, (x, y, g(x, y) - 0.1), rot_z=rng.uniform(0, 6.28),
                     scale=rng.uniform(0.9, 1.15))
    if shot is None:
        return
    # muzzle flash and a rolling puff of smoke from the first gun
    # (matrix_world is stale until the depsgraph updates, so build the gun's matrix directly)
    g0 = guns[0]
    mw = (kit.T(g0.location) @ kit.Rz(aim)) @ Vector(kit.CANNON_MUZZLE)
    kit.mat_emit("flash", (1.0, 0.62, 0.22), 40.0)
    mb = kit.MB()
    mb.ico(kit.Matrix.Identity(4), "flash", r=0.6, sub=1)
    flash = mb.obj("MuzzleFlash", coll)
    flash.location = mw + Vector((fx, fy, 0)) * 0.5
    for f, sc in ((shot - 1, 0.0), (shot, 2.6), (shot + 2, 1.5), (shot + 6, 0.0)):
        flash.scale = (sc, sc, sc)
        flash.keyframe_insert("scale", frame=f)
    puff_src = kit.MB()
    puff_src.ico(kit.Matrix.Identity(4), "smoke", r=1.0, sub=1, jitter=0.15, rng=rng)
    puff_mesh = puff_src.obj("LibPuff", lib_c)
    kit.hide_source(puff_mesh)
    for i in range(18):   # a rolling plume: small puffs released one after another
        t0 = shot + i // 3
        base = mw + Vector((fx, fy, 0)) * rng.uniform(0.5, 4.0) + Vector((rng.uniform(-0.6, 0.6),
                                                                          rng.uniform(-0.6, 0.6),
                                                                          rng.uniform(-0.2, 0.8)))
        drift = Vector((fx, fy, 0)) * rng.uniform(1.5, 5) + Vector((2.5, 1.0, rng.uniform(3, 8)))
        size = rng.uniform(0.45, 1.0)
        ob = kit.instance(puff_mesh, f"Smoke{i}", coll, base, scale=0.0)
        ob.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
        for f, loc, sc in ((t0, mw, 0.05), (t0 + 7, base, size),
                           (t0 + 75, base + drift, size * 2.2), (t0 + 175, base + drift * 1.7, 0.0)):
            ob.location = loc
            ob.scale = (sc, sc, sc)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("scale", frame=f)


# ---------------------------------------------------------------- map (S07+)
def build_map(coll, lib_c):
    """The parchment map of Kerala under the diorama, with 3D Ghats and palms."""
    sx0, sx1, sy0, sy1 = geo.SHEET
    z = geo.MAP_Z
    tex_path = os.path.join(os.path.dirname(os.path.abspath(geo.__file__)), "textures", "kerala_map.jpg")
    img = bpy.data.images.load(tex_path, check_existing=True)
    m = bpy.data.materials.new("MapSheet")
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Specular IOR Level"].default_value = 0.15
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img
    tn.interpolation = "Cubic"
    hsv = nt.nodes.new("ShaderNodeHueSaturation")      # deeper, warmer parchment under bright sun
    hsv.inputs["Saturation"].default_value = 1.35
    hsv.inputs["Value"].default_value = 0.78
    nt.links.new(tn.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    me = bpy.data.meshes.new("MapSheet")
    me.from_pydata([(sx0, sy0, z), (sx1, sy0, z), (sx1, sy1, z), (sx0, sy1, z)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for li, (u, v) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = (u, v)
    me.materials.append(m)
    sheet = bpy.data.objects.new("MapSheet", me)
    coll.objects.link(sheet)
    tb = kit.MB()
    tb.box(kit.T(0, 10000, z - 0.6) @ kit.S(200000, 200000, 1.0), "table")
    tb.obj("Table", coll)

    # Western Ghats as faceted green hills
    rng = random.Random(17)
    land = geo.land_polygon_xy()
    coast = geo.coast_xy()

    def nz(x, y):
        return 0.5 + 0.5 * noise.noise(Vector((x / 2600.0, y / 2600.0, 0.3)))

    step = 300.0
    xs = [sx0 + 500 + i * step for i in range(int((sx1 - sx0 - 1000) / step) + 1)]
    ys = [sy0 + 500 + j * step for j in range(int((sy1 - sy0 - 1000) / step) + 1)]
    bm = bmesh.new()
    grid, hgt = [], []
    for y in ys:
        row, hrow = [], []
        for x in xs:
            jx, jy = rng.uniform(-0.3, 0.3) * step, rng.uniform(-0.3, 0.3) * step
            px_, py_ = x + jx, y + jy
            h = 0.0
            if geo.point_in_poly(px_, py_, land) and not (TX0 - 300 < px_ < TX1 + 300 and TY0 - 300 < py_ < TY1 + 300):
                dc, _ = geo.dist_to_polyline(px_, py_, coast)
                h = geo.ghats_height(px_, py_, nz) * _smooth(400, 1800, dc)
            row.append(bm.verts.new((px_, py_, z + 0.8 + h)))
            hrow.append(h)
        grid.append(row)
        hgt.append(hrow)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            hs = (hgt[j][i], hgt[j][i + 1], hgt[j + 1][i + 1], hgt[j + 1][i])
            if max(hs) < 12:
                continue
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.material_index = 1 if sum(hs) / 4 > 300 else 0
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    gme = bpy.data.meshes.new("Ghats")
    bm.to_mesh(gme)
    bm.free()
    for mname in ("ghat_lo", "ghat_hi"):
        gme.materials.append(kit.mat(mname))
    for poly in gme.polygons:
        poly.use_smooth = False
    gh = bpy.data.objects.new("Ghats", gme)
    coll.objects.link(gh)

    # palms along the coastal strip (big enough to read from map height)
    palms = [bpy.data.objects[f"LibPalm{i}"] for i in range(6)]
    k = 0
    for i in range(len(coast) - 1):
        (ax, ay), (bx, by) = coast[i], coast[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / seg, (bx - ax) / seg
        if not geo.point_in_poly((ax + bx) / 2 + nx * 500, (ay + by) / 2 + ny * 500, land):
            nx, ny = -nx, -ny
        t = rng.uniform(0, 300)
        while t < seg:
            for _ in range(2):
                off = rng.uniform(220, 1000)
                x, y = ax + (bx - ax) * t / seg + nx * off, ay + (by - ay) * t / seg + ny * off
                if (TX0 - 150 < x < TX1 + 150 and TY0 - 150 < y < TY1 + 150) or not (sx0 + 400 < x < sx1 - 400
                                                                                     and sy0 + 400 < y < sy1 - 400):
                    continue
                if not geo.point_in_poly(x, y, land):
                    continue
                kit.instance(palms[k % 6], f"MapPalm{k}", coll, (x, y, z + 0.5), rot_z=rng.uniform(0, 6.28),
                             scale=rng.uniform(26, 34))
                k += 1
            t += rng.uniform(380, 560)


def build_world(frames, weather=None):
    world_c = kit.new_collection("World")
    village_c = kit.new_collection("Village")
    props_c = kit.new_collection("Props")
    plants_c = kit.new_collection("Plants")
    people_c = kit.new_collection("People")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    weather = weather or {}
    storm = weather.get("storm", [])
    make_land(world_c)
    make_tile_skirt(world_c)
    sea = make_sea(world_c)
    animate_sea(sea, rig_c, frames, storm)
    setup_world()
    haze = add_haze(world_c)
    sun = add_sun(rig_c)
    apply_weather(sun, haze, weather)
    build_village(village_c, props_c, plants_c, people_c, lib_c, frames)
    build_stockade(kit.new_collection("Stockade"), lib_c, frames)
    build_camp(kit.new_collection("Camp"), lib_c, frames)
    build_fleet(kit.new_collection("Fleet"), frames, storm)
    build_battery(kit.new_collection("Battery"), lib_c, frames, weather.get("shot"))
    build_clouds(kit.new_collection("Clouds"), weather)
    build_map(kit.new_collection("Map"), lib_c)
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c


# ============================================================ shared scene base
# EVERY scene (beach, close sets, battlefields, coasts) starts from these two, so the whole
# film shares one sky, one sun, one haze and one sea. Never write a scene-specific sky,
# fill light or flat-blue water plane: that is what made S19-S28 v1 look grey and flat.
def scene_base(rig_c, sun_dir=(0.7, -0.45, -0.38), sun_energy=8.0, haze_density=0.0008):
    """Standard warm-dawn sky gradient, low warm sun with long soft shadows, and the bounded
    haze box. Returns the sun object. Change only the direction/energy for time of day."""
    setup_world()
    add_haze(rig_c, density=haze_density)
    return add_sun(rig_c, direction=sun_dir, energy=sun_energy)


def make_faceted_sea(coll, rig_c, frames, box, depth_fn, step=2.5, far_step=10.0, detail_box=None,
                     name="Sea", seed=7):
    """The film's faceted low-poly sea for ANY coastline: a jittered triangulated grid with
    turquoise shallows -> blue depths, foam at the waterline and the rolling swell of the beach
    clips. box = (x0, x1, y0, y1) in metres; depth_fn(x, y) = metres of water (<= 0 on land, so
    the land mesh covers it). Fine `step` inside detail_box (default: whole box), coarse outside."""
    rng = random.Random(seed)
    x0, x1, y0, y1 = box
    dx0, dx1, dy0, dy1 = detail_box or box

    def axis(a0, a1, d0, d1):
        vals, v = [], a0
        while v < a1:
            vals.append(v)
            v += step if d0 <= v < d1 else far_step
        return vals + [a1]

    xs, ys = axis(x0, x1, dx0, dx1), axis(y0, y1, dy0, dy1)
    bm = bmesh.new()
    col = bm.verts.layers.float_color.new("Col")
    dl = bm.verts.layers.deform.verify()
    lin = [kit.srgb_to_linear(c) for c in (SEA_SHALLOW, SEA_DEEP, SEA_FOAM)]
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                s = step if (dx0 <= x < dx1 and dy0 <= y < dy1) else far_step
                jx, jy = rng.uniform(-0.3, 0.3) * s, rng.uniform(-0.3, 0.3) * s
            px, py = x + jx, y + jy
            v = bm.verts.new((px, py, 0.0))
            depth = depth_fn(px, py)
            t = max(0.0, min(1.0, depth / 25.0))
            t = t * t * (3 - 2 * t)
            c = [lin[0][k] * (1 - t) + lin[1][k] * t for k in range(3)]
            if depth < 1.2:
                u = max(0.0, 1.0 - max(0.0, depth) / 1.2)
                c = [c[k] * (1 - u) + lin[2][k] * u for k in range(3)]
            shade = rng.uniform(0.95, 1.05)
            v[col] = (c[0] * shade, c[1] * shade, c[2] * shade, 1.0)
            edge = min(px - x0, x1 - px, py - y0, y1 - py)
            mask = _smooth(0, 40, edge)
            v[dl][0] = mask * _smooth(0.5, 6, depth)          # calm right at the shore
            v[dl][1] = mask * _smooth(4, 45, depth)
            row.append(v)
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(sea_material())
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.vertex_groups.new(name="SwellMask")
    ob.vertex_groups.new(name="Offshore")
    animate_sea(ob, rig_c, frames)
    return ob
