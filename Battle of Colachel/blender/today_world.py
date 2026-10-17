"""Colachel today (S65-S69; clips 78-82): the victory pillar on the beach, then the sunset over the empty shore.

Same beach diorama as S01-S06 and S30-S48 (land, faceted sea, village, palm groves), in clear daylight.
  S65 (K78) glide in to the victory pillar on its stepped plaza among palms; boats on the sand, a few visitors.
  S66       slow orbit of the pillar.
  S67 (K80) the camera rises from the pillar out over the sea; the long coast and palm belt behind it.
  S68 (K82) sunset over the empty beach where the stockade stood: only a ring of old post stumps remains.
  S69       the same shore as the light goes (the end-screen runs over it).
No text anywhere (a plain plaque, no letters).
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S
import colachel_world as cw
import landing_world as lw
import siege_world as sw

H = cw.height
SY = cw.shore_y
ST = cw.STOCKADE
SW = cw.stockade_world
NX, NY, TX, TY = sw.NX, sw.NY, sw.TX, sw.TY
set_vis = lw.set_vis
PILLAR = SW(-6.0, 2.0)
SEA = math.atan2(-NY, -NX)                 # direction from the land out to sea                  # the plaza sits on the old stockade ground, west of its centre


def register_palette():
    for k, v in {"pillar": (0.66, 0.64, 0.60), "pillar_dk": (0.52, 0.50, 0.47), "pillar_lt": (0.76, 0.74, 0.70),
                 "plaque": (0.78, 0.60, 0.22), "cloud_white": (0.97, 0.96, 0.94), "stump": (0.36, 0.26, 0.17),
                 "stump_dk": (0.27, 0.19, 0.12), "sun_disc": (1.0, 0.62, 0.22)}.items():
        kit.PALETTE.setdefault(k, v)
        kit.mat(k, kit.PALETTE[k])


def make_pillar(name, c, h=12.0):
    """A tall square obelisk on a stepped plinth with a pyramid cap and a plain plaque (K78)."""
    mb = kit.MB(bevel=0.03)
    mb.box(T(0, 0, 0.3) @ S(5.6, 5.6, 0.6), "pillar_dk")
    mb.box(T(0, 0, 0.8) @ S(4.6, 4.6, 0.5), "pillar")
    mb.box(T(0, 0, 1.3) @ S(3.6, 3.6, 0.5), "pillar_lt")
    z = 1.55
    shaft = h - 2.3
    mb.cone(T(0, 0, z + shaft / 2) @ Rz(math.pi / 4), "pillar", segments=4, r1=1.25, r2=0.72, depth=shaft)
    for k in range(1, 5):
        zz = z + shaft * k / 5
        mb.cone(T(0, 0, zz) @ Rz(math.pi / 4), "pillar_dk", segments=4, r1=1.25 - 0.106 * k * 1.0 + 0.06, r2=1.25 - 0.106 * k + 0.06, depth=0.12)
    mb.cone(T(0, 0, z + shaft + 0.45) @ Rz(math.pi / 4), "pillar_lt", segments=4, r1=0.74, r2=0.03, depth=0.9)
    mb.box(T(0, -1.82, 1.1) @ S(1.4, 0.06, 0.4), "plaque")
    return mb.obj(name, c)


def make_plaza(name, c, ground):
    """The railed stone enclosure round the pillar, with gate steps and corner posts (K78): a low wall with a
    coping, four corner posts, sand-grey paving inside."""
    px, py = PILLAR
    mb = kit.MB(bevel=0.03)
    hw = 6.4
    ang = math.atan2(NY, NX) - math.pi / 2
    R = Rz(ang)

    def P(x, y, z):
        v = R @ Vector((x, y, 0))
        return (px + v.x, py + v.y, ground(px + v.x, py + v.y) + z)

    mb.box(T(*P(0, 0, 0.1)) @ R @ S(2 * hw, 2 * hw, 0.25), "pillar")                 # paving slab
    for (x0, y0, x1, y1, gate) in ((-hw, -hw, hw, -hw, True), (hw, -hw, hw, hw, False), (hw, hw, -hw, hw, False), (-hw, hw, -hw, -hw, False)):
        L = math.hypot(x1 - x0, y1 - y0)
        a = math.atan2(y1 - y0, x1 - x0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        segs = ((-L / 2, -1.2), (1.2, L / 2)) if gate else ((-L / 2, L / 2),)
        for (u0, u1) in segs:
            uc = (u0 + u1) / 2
            wx, wy = cx + math.cos(a) * uc, cy + math.sin(a) * uc
            mb.box(T(*P(wx, wy, 0.55)) @ R @ Rz(a) @ S(u1 - u0, 0.5, 0.9), "pillar_dk")
            mb.box(T(*P(wx, wy, 1.05)) @ R @ Rz(a) @ S(u1 - u0 + 0.05, 0.62, 0.14), "pillar_lt")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(T(*P(sx * hw, sy * hw, 0.8)) @ R @ S(0.8, 0.8, 1.5), "pillar")
            mb.box(T(*P(sx * hw, sy * hw, 1.65)) @ R @ S(0.95, 0.95, 0.18), "pillar_lt")
    for k in range(3):                                                                # gate steps
        mb.box(T(*P(0, -hw - 0.5 - k * 0.45, 0.15 + 0.05 * (2 - k))) @ R @ S(2.4, 0.6, 0.3 - 0.0 * k), "pillar_lt")
    return mb.obj(name, c)


def build_monument(c, lib_c, rng):
    px, py = PILLAR
    g = H(px, py) + 0.04
    ob = make_pillar("VictoryPillar", c)
    ob.location = (px, py, g)
    pl = make_plaza("PillarPlaza", c, H)
    # palms and bushes round it, boats on the sand, a few visitors strolling
    palms = [bpy.data.objects[f"LibPalm{i}"] for i in range(6)]
    bushes = [bpy.data.objects[f"LibBush{i}"] for i in range(3)]
    for k in range(9):
        # palms stand on the landward half and the flanks only, so the camera that circles the sea side sees the pillar clear
        a = SEA + math.pi + (k - 4) * 0.42 + rng.uniform(-0.12, 0.12)
        r = rng.uniform(11.0, 17.0)
        x, y = px + math.cos(a) * r, py + math.sin(a) * r
        if y < SY(x) + 5.0:
            continue
        kit.instance(palms[k % 6], f"MonPalm{k}", c, (x, y, H(x, y) - 0.1), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.9, 1.15))
    for k in range(10):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(8.0, 11.0)
        x, y = px + math.cos(a) * r, py + math.sin(a) * r
        if y < SY(x) + 3.0:
            continue
        kit.instance(bushes[k % 3], f"MonBush{k}", c, (x, y, H(x, y) - 0.05), rot_z=rng.uniform(0, 6.28))
    # boats drawn up on the sand, nets, baskets (K78/K80), and a long line of beach boats down the coast
    boat = bpy.data.objects["LibBoat"]
    for k in range(48):
        x = rng.uniform(-70, 190)
        d = rng.uniform(3.0, 7.0)
        bx, by = lw.cy(x, d)
        if math.hypot(bx - px, by - py) < 12.0:
            continue
        kit.instance(boat, f"BeachBoat{k}", c, (bx, by, H(bx, by) - 0.05), rot_z=math.atan2(NY, NX) + math.pi / 2 + rng.uniform(-0.25, 0.25), scale=rng.uniform(0.9, 1.1))
    return ob, pl


def build_visitors(c, f0, f1):
    """A few people walk the sand and the plaza: villagers, one in a robe."""
    rng = random.Random(65)
    px, py = PILLAR
    paths = [((px - 10, py - 3), (px + 9, py - 5)), ((px + 8, py + 6), (px - 8, py + 7)), ((px - 4, py - 9), (px + 4, py - 8)),
             ((px + 12, py - 2), (px + 2, py - 6)), ((px - 12, py + 3), (px - 3, py + 7))]
    for k, (a, b) in enumerate(paths):
        root, parts = kit.make_villager(f"Visitor{k}", c, seed=70 + k, robe=k % 2 == 0, cloth=("cloth_t", "cloth_w", "cloth_r")[k % 3])
        kit.animate_walk(root, parts, [a, b, a], H, start=f0, end=f1, stride_frames=16, speed=0.55)


def build_stumps(c, rng):
    """Where the stockade stood: a broken ring of old post stumps, a few fallen logs."""
    mb = kit.MB(bevel=0.02)
    n = 0
    for (x, y, side, s, Lw, inw) in kit.stockade_posts(ST["center"], ST["axis_deg"], ST["half_u"], ST["half_v"], 3.5, 3):
        if rng.random() < 0.40:
            continue
        hh = rng.choice((0.25, 0.4, 0.55, 0.8, 1.1)) * rng.uniform(0.8, 1.3)
        g = H(x, y)
        mb.seg((x, y, g - 0.2), (x + rng.uniform(-0.05, 0.08), y + rng.uniform(-0.05, 0.08), g + hh), 0.22, 0.19,
               "stump" if n % 3 else "stump_dk", sides=6)
        # a broken, splintered top
        mb.cone(T(x, y, g + hh + 0.06) @ Rx(rng.uniform(-0.2, 0.2)), "stump_dk", segments=5, r1=0.19, r2=0.04, depth=rng.uniform(0.1, 0.3))
        n += 1
    for k in range(5):
        x, y = SW(rng.uniform(-13, 13), rng.uniform(-10, 10))
        a = rng.uniform(0, 3.1)
        mb.seg((x, y, H(x, y) + 0.15), (x + math.cos(a) * 2.2, y + math.sin(a) * 2.2, H(x, y) + 0.17), 0.18, 0.17, "stump", sides=6)
    return mb.obj("StockadeStumps", c)


def build_sky_clouds(c, rng, n=12):
    srcs = [kit.make_cloud(f"LibSunCloud{i}", c, seed=70 + i, size=0.45 + 0.07 * i) for i in range(4)]
    for s in srcs:
        kit.recolor(s, {"cloud": "cloud_white"})
        kit.hide_source(s)
    for i in range(n):
        x = rng.uniform(-60, 200)
        px, py = lw.cy(x, -rng.uniform(120, 360))
        cl = kit.instance(srcs[i % 4], f"SunCloud{i}", c, (px, py, rng.uniform(60, 110)), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.9, 1.5))
        cl.visible_shadow = False


def build_sun_disc(c, frames):
    """A big flat low-poly sun low over the sea for the sunset, with a soft larger halo behind it (K82)."""
    kit.PALETTE.setdefault("sun_halo", (1.0, 0.6, 0.25))
    mb = kit.MB()
    mb.cone(T(0, 0.0, 0) @ Rx(math.pi / 2), "sun_disc", segments=14, r1=1.0, r2=1.0, depth=0.1)
    mb.cone(T(0, 0.12, 0) @ Rx(math.pi / 2), "sun_halo", segments=14, r1=1.75, r2=1.75, depth=0.1)
    ob = mb.obj("SunDisc", c)
    ob.visible_shadow = False
    ob.data.materials[0] = kit.mat_emit("SunDiscGlow", (1.0, 0.80, 0.32), 8.0)
    ob.data.materials[1] = kit.mat_emit("SunHaloGlow", (1.0, 0.50, 0.16), 2.2)
    return ob


def build_world(ev):
    """ev: end, r65..r69 frame ranges."""
    end = ev["end"]
    register_palette()
    world_c = kit.new_collection("World")
    village_c = kit.new_collection("Village")
    props_c = kit.new_collection("Props")
    plants_c = kit.new_collection("Plants")
    people_c = kit.new_collection("People")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    rng = random.Random(9)
    kit.PALETTE.update({"sand": (0.93, 0.74, 0.40), "sand_wet": (0.74, 0.58, 0.34), "grass": (0.36, 0.55, 0.20)})   # golden sand, richer green (K78)
    cw.make_land(world_c)
    cw.SEA_SHALLOW, cw.SEA_DEEP = (0.20, 0.76, 0.74), (0.08, 0.46, 0.66)           # turquoise to deep blue (K78, K80)
    sea = cw.make_sea(world_c)
    # stronger facet-to-facet variation in the sea colour, as in K80
    srng = random.Random(3)
    ca = sea.data.color_attributes["Col"]
    for i in range(len(ca.data)):
        k = srng.uniform(0.72, 1.28)
        c0 = ca.data[i].color
        ca.data[i].color = (c0[0] * k, c0[1] * k, c0[2] * k, 1.0)
    cw.animate_sea(sea, rig_c, end, [])
    sun = cw.scene_base(rig_c)
    cw.build_village(village_c, props_c, plants_c, people_c, lib_c, end)
    lw.tidy_trees()
    lw.build_groves(plants_c, rng)
    lw.build_path(world_c)
    lw.build_hamlets(village_c, rng)
    # keep the old stockade ground and the plaza clear of trees
    px, py = PILLAR
    for ob in [o for o in bpy.data.objects if o.name.startswith(("Palm", "GrovePalm", "Bush", "GroveBush", "Tree"))]:
        x, y = ob.location.x, ob.location.y
        if (cw.in_stockade(x, y, 6.0) or math.hypot(x - px, y - py) < 14.0) and y > SY(x) + 1.0:
            bpy.data.objects.remove(ob, do_unlink=True)
    for ob in [o for o in bpy.data.objects if o.name.startswith(("Jetty",)) or "Hero" in o.name]:
        pass
    # the sea runs on to the true horizon: a huge flat plane of deep water far below the faceted tile
    far = bpy.data.meshes.new("FarSea")
    R = 90000.0
    far.from_pydata([(-R, -R, -0.9), (R, -R, -0.9), (R, R, -0.9), (-R, R, -0.9)], [], [(0, 1, 2, 3)])
    fm = bpy.data.materials.new("FarSeaMat")
    fm.use_nodes = True
    fb = fm.node_tree.nodes.get("Principled BSDF")
    fb.inputs["Base Color"].default_value = (*kit.srgb_to_linear((0.09, 0.44, 0.62)), 1)
    fb.inputs["Roughness"].default_value = 0.45
    far.materials.append(fm)
    fo = bpy.data.objects.new("FarSea", far)
    world_c.objects.link(fo)
    # a clear blue day sky (the sea reflects it when seen from above)
    ramp = next(n for n in bpy.context.scene.world.node_tree.nodes if n.bl_idname == "ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*kit.srgb_to_linear((0.99, 0.88, 0.68)), 1)
    ramp.color_ramp.elements[1].color = (*kit.srgb_to_linear((0.88, 0.90, 0.92)), 1)
    ramp.color_ramp.elements[-1].color = (*kit.srgb_to_linear((0.68, 0.80, 0.94)), 1)
    ramp.color_ramp.elements[1].position = 0.06
    ramp.color_ramp.elements[-1].position = 0.32
    # fishing boats out on the water
    boat = bpy.data.objects["LibBoat"]
    sea_c = kit.new_collection("SeaBoats")
    brng = random.Random(44)
    for k in range(10):
        x = brng.uniform(-60, 150)
        bx, by = lw.cy(x, -brng.uniform(22, 130))
        ob = kit.instance(boat, f"SeaBoat{k}", sea_c, (bx, by, 0.05), rot_z=brng.uniform(0, 6.28), scale=1.1)
        kit.animate_idle(ob, brng, 1, ev["end"], amount=0.05)
    cloud_c = kit.new_collection("SkyClouds")
    build_sky_clouds(cloud_c, random.Random(31))

    mon_c = kit.new_collection("Monument")
    build_monument(mon_c, lib_c, rng)
    vis_c = kit.new_collection("Visitors")
    build_visitors(vis_c, ev["r65"][0], ev["r67"][1])
    stump_c = kit.new_collection("Stumps")
    build_stumps(stump_c, random.Random(17))
    disc_c = kit.new_collection("Sunset")
    disc = build_sun_disc(disc_c, ev)
    set_vis(stump_c, [(ev["r68"][0], end)])
    set_vis(mon_c, [(ev["r65"][0], ev["r67"][1])])
    set_vis(vis_c, [(ev["r65"][0], ev["r67"][1])])
    for ob in lib_c.objects:
        kit.hide_source(ob)
    lw.sway_palms(ev["r65"][0], end, PILLAR, 200, rng, amount=0.04)
    return rig_c, sun, disc
