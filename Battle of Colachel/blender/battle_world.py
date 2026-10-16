"""The Battle of the Earthworks & Powder Magazine Explosion (Beats S25, S26).

Built in its own file Battle.blend.
Matches Flow references:
- frames/flow_refs/K32.jpeg (S25: Allied columns advancing through paddy fields toward Travancore earthworks)
- frames/flow_refs/K33.jpeg (S26: Travancore 16-gun earthwork battery, mortar shell arc, powder store explosion)
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S

BATTLE_PALETTE = {
    "paddy_water":  (0.32, 0.46, 0.35),
    "paddy_green":  (0.38, 0.58, 0.22),
    "paddy_bund":   (0.48, 0.36, 0.24),
    "laterite_rd":  (0.66, 0.42, 0.28),
    "earth_wall":   (0.52, 0.32, 0.20),
    "roof_thatch":  (0.72, 0.58, 0.34),
    "wood_plank":   (0.42, 0.28, 0.18),
    "table_dark":   (0.42, 0.28, 0.18),
    "nair_shield":  (0.22, 0.20, 0.18),
    "fire_yellow":  (1.00, 0.88, 0.18),
    "fire_orange":  (1.00, 0.48, 0.05),
    "fire_red":     (0.90, 0.18, 0.08),
    "smoke_dk":     (0.24, 0.24, 0.26),
    "smoke_md":     (0.42, 0.42, 0.45),
}


def register_palette():
    for name, rgb in BATTLE_PALETTE.items():
        kit.PALETTE[name] = rgb
        m = kit.mat(name, rgb)
        # Give fire materials brilliant glowing emission!
        if name in ("fire_yellow", "fire_orange", "fire_red"):
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Emission Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
                bsdf.inputs["Emission Strength"].default_value = 4.5 if name == "fire_yellow" else 3.2


def bmat(name):
    if name in BATTLE_PALETTE:
        return kit.mat(name, BATTLE_PALETTE[name])
    return kit.mat(name, kit.PALETTE[name])


def setup_sky():
    w = bpy.data.worlds.new("BattleSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.82, 0.88, 0.94, 1.0)
        bg.inputs["Strength"].default_value = 1.0


def build_terrain(coll, rng):
    """Flooded paddy fields, raised bunds, dirt road, palms, and foothills (matches K32)."""
    mb = kit.MB(bevel=0.0)

    # Broad ground plane
    mb.box(T(0, 0, -0.2) @ S(140.0, 100.0, 0.4), "laterite_rd")

    # Central dusty red-brown dirt road (along X from -65 to +65, width 8.5m)
    mb.box(T(0, 0, 0.02) @ S(140.0, 8.5, 0.04), "laterite_rd")

    # 4 Large Rectangular Flooded Paddy Fields with green rice shoots & mud bunds (matching K32)
    paddy_spots = [
        (-2.0, 12.5, 14.0, 13.0),
        (-2.0, -12.5, 14.0, 13.0),
        (-18.0, 12.5, 14.0, 13.0),
        (-18.0, -12.5, 14.0, 13.0),
    ]
    for px, py, pw, pl in paddy_spots:
        mb.box(T(px, py, 0.06) @ S(pw, pl, 0.05), "paddy_water")
        mb.box(T(px, py, 0.08) @ S(pw * 0.94, pl * 0.94, 0.02), "paddy_green")
        bw = 0.55
        mb.box(T(px, py + pl / 2, 0.15) @ S(pw + bw * 2, bw, 0.22), "paddy_bund")
        mb.box(T(px, py - pl / 2, 0.15) @ S(pw + bw * 2, bw, 0.22), "paddy_bund")
        mb.box(T(px + pw / 2, py, 0.15) @ S(bw, pl, 0.22), "paddy_bund")
        mb.box(T(px - pw / 2, py, 0.15) @ S(bw, pl, 0.22), "paddy_bund")

    # Distant green Western Ghats foothills
    mb.cone(T(28.0, 42.0, 12.0) @ S(40.0, 24.0, 1.0), "hill", segments=6, r1=1.0, r2=0.08, depth=24.0)
    mb.cone(T(-10.0, 45.0, 14.0) @ S(45.0, 26.0, 1.0), "hill", segments=5, r1=1.0, r2=0.06, depth=28.0)
    mb.cone(T(-45.0, 38.0, 10.0) @ S(32.0, 20.0, 1.0), "hill", segments=6, r1=1.0, r2=0.1, depth=20.0)

    t_ob = mb.obj("BattleTerrain", coll)
    for m in ("laterite_rd", "paddy_water", "paddy_green", "paddy_bund", "hill"):
        t_ob.data.materials.append(bmat(m))

    # Palm trees framing background and flanks
    palm_c = kit.new_collection("BattlePalms")
    palm_spots = [
        (-38, 24), (-30, 26), (-22, 25), (-12, 26), (-2, 27), (8, 26), (18, 25), (28, 26), (38, 24),
        (-38, -24), (-28, -26), (-18, -25), (-8, -26), (4, -26), (16, -25), (26, -26), (36, -24),
        (38, 8), (42, -6), (40, 18), (-45, 12), (-45, -10),
    ]
    for i, (px, py) in enumerate(palm_spots):
        p = kit.make_palm(f"BPalm_{i}", palm_c, seed=i * 5 + 7, height=rng.uniform(8.5, 11.5))
        p.location = (px + rng.uniform(-1.5, 1.5), py + rng.uniform(-1.5, 1.5), 0.0)
        p.rotation_euler = (rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), rng.uniform(0, 6.28))


def build_travancore_earthworks(coll):
    """Reinforced red-mud earthworks with 16 heavy guns, Nair defenders, and powder magazine."""
    ew_c = kit.new_collection("TravancoreFortifications")

    # 1. Main red-mud rampart (X = +16.0, length = 32m along Y)
    ew = kit.make_earthworks("RedMudEarthworks", ew_c, length=34.0, w=5.5, h=2.5)
    ew.location = (16.0, 0.0, 0.0)
    ew.rotation_euler = (0, 0, math.pi / 2)  # Facing west (-X)

    # 2. 16 Heavy Cannons deployed along the rampart facing west (-X)
    cannon_c = kit.new_collection("TravancoreBattery")
    cannon_src = kit.make_cannon("BatteryGunSrc", cannon_c)
    kit.hide_source(cannon_src)

    cannons = []
    for i in range(16):
        cy = -15.0 + i * 2.0
        c_ob = kit.instance(cannon_src, f"TravancoreGun_{i}", ew_c,
                            (14.2, cy, 1.4), rot_z=math.pi)
        cannons.append(c_ob)

    # 3. Powder Magazine Shed & Barrels (X = +24.0, Y = -4.5)
    store_c = kit.new_collection("PowderMagazine")
    store = kit.make_powder_store("PowderStoreShed", store_c, w=6.2, d=4.6, h=3.4)
    store.location = (24.0, -4.5, 0.0)
    store.rotation_euler = (0, 0, 0.1)

    # Barrels and crates
    b_mb = kit.MB(bevel=0.03)
    barrel_coords = [
        (21.8, -3.2, 0.0), (22.4, -3.2, 0.0), (22.1, -3.2, 0.65),
        (21.8, -5.5, 0.0), (22.4, -5.5, 0.0), (26.2, -3.5, 0.0),
        (26.2, -5.2, 0.0), (23.2, -7.2, 0.0), (23.8, -7.2, 0.0),
    ]
    for bx, by, bz in barrel_coords:
        b_mb.cone(T(bx, by, bz + 0.35), "plank", segments=8, r1=0.28, r2=0.25, depth=0.7)
        b_mb.cone(T(bx, by, bz + 0.35), "iron", segments=8, r1=0.29, r2=0.29, depth=0.06)
    b_mb.box(T(22.0, -6.8, 0.35) @ S(0.8, 0.8, 0.7), "table_dark")
    b_mb.box(T(26.5, -4.2, 0.35) @ S(0.9, 0.7, 0.7), "table_dark")
    bar_ob = b_mb.obj("PowderBarrelsCrates", store_c)
    bar_ob.data.materials.append(kit.mat("plank", kit.PALETTE["plank"]))
    bar_ob.data.materials.append(kit.mat("iron", kit.PALETTE["iron"]))
    bar_ob.data.materials.append(kit.mat("table_dark", (0.42, 0.28, 0.18)))

    # 4. Nair Warriors stationed behind the rampart & charging forward
    nair_c = kit.new_collection("NairWarriors")
    rng = random.Random(61)
    nairs = []
    for i in range(24):
        ny = -14.0 + i * 1.2 + rng.uniform(-0.2, 0.2)
        nx = 17.2 + rng.uniform(-0.3, 0.5)
        n = kit.make_figure(f"NairDef_{i}", nair_c, "nair", seed=100 + i)
        n.location = (nx, ny, 1.4)
        n.rotation_euler = (0, 0, math.pi + rng.uniform(-0.2, 0.2))
        nairs.append(n)

    return {"earthworks": ew, "store": store, "barrels": bar_ob, "cannons": cannons}


def build_allied_army(coll):
    """Advancing Dutch VOC columns and Indian allied infantry (Flow ref K32)."""
    army_c = kit.new_collection("AlliedArmy")
    rng = random.Random(72)

    # 1. Dutch VOC Regulars Column: 2 neat ranks of 16 soldiers (32 total)
    # Starting at X = -10.0 to -12.5 (right in frame between paddy fields!)
    dutch_soldiers = []
    for rank in range(2):
        for col in range(16):
            dx = -10.5 - rank * 2.0
            dy = -10.5 + col * 1.4
            d = kit.make_figure(f"DutchSol_{rank}_{col}", army_c, "dutch", seed=200 + rank * 16 + col, armed=True)
            d.location = (dx, dy, 0.0)
            d.rotation_euler = (0, 0, 0.0)  # Facing +X
            dutch_soldiers.append(d)

    # 2. Indian Allied Infantry Column: 2 ranks of 12 warriors (24 total)
    allied_soldiers = []
    for rank in range(2):
        for col in range(12):
            ax = -10.5 - rank * 2.0
            ay = 4.5 + col * 1.4
            a = kit.make_figure(f"AlliedSol_{rank}_{col}", army_c, "nair", seed=300 + rank * 12 + col)
            a.location = (ax, ay, 0.0)
            a.rotation_euler = (0, 0, 0.0)  # Facing +X
            allied_soldiers.append(a)

    # 3. Two Dutch Field Cannons advancing along the road
    cannon_c = kit.new_collection("AlliedArtillery")
    c1 = kit.make_cannon("AlliedGun1", cannon_c)
    c1.location = (-6.5, 1.8, 0.0)
    c1.rotation_euler = (0, 0, 0.0)

    c2 = kit.make_cannon("AlliedGun2", cannon_c)
    c2.location = (-6.5, -1.8, 0.0)
    c2.rotation_euler = (0, 0, 0.0)

    # 4. Orange VOC War Banner carried by Dutch commander
    v_mb = kit.MB(bevel=0.04)
    v_mb.cone(T(-8.5, -3.5, 2.5), "post", segments=6, r1=0.06, r2=0.04, depth=5.0)
    v_mb.box(T(-7.1, -3.5, 4.2) @ S(2.6, 0.06, 1.6), "gold")
    v_ob = v_mb.obj("AlliedBanner", army_c)
    v_ob.data.materials.append(kit.mat("post", kit.PALETTE["post"]))
    v_ob.data.materials.append(kit.mat("gold", (0.96, 0.46, 0.10)))

    return {"dutch": dutch_soldiers, "allies": allied_soldiers, "guns": [c1, c2], "banner": v_ob}


def build_mortar_and_explosion(coll, blast_frame=400):
    """The mortar shell arc and the dramatic powder store detonation (S26, K33)."""
    fx_c = kit.new_collection("ExplosionFX")

    # 1. Mortar Cannonball
    mb = kit.MB()
    mb.ico(Matrix.Identity(4), "iron", r=0.28, sub=2)
    ball = mb.obj("MortarShell", fx_c)
    ball.data.materials.append(kit.mat("iron", kit.PALETTE["iron"]))

    # Flight arc from allied side into powder store (24.0, -4.5)
    f_launch = blast_frame - 48
    ball.location = (2.0, -2.0, 2.5)
    ball.keyframe_insert("location", frame=f_launch)
    ball.location = (13.0, -3.2, 16.5)  # Peak of high mortar arc
    ball.keyframe_insert("location", frame=f_launch + 24)
    ball.location = (24.0, -4.5, 2.0)  # Direct hit on powder store roof
    ball.keyframe_insert("location", frame=blast_frame)

    ball.hide_render = True
    ball.keyframe_insert("hide_render", frame=1)
    ball.keyframe_insert("hide_render", frame=f_launch - 1)
    ball.hide_render = False
    ball.keyframe_insert("hide_render", frame=f_launch)
    ball.keyframe_insert("hide_render", frame=blast_frame)
    ball.hide_render = True
    ball.keyframe_insert("hide_render", frame=blast_frame + 1)

    # 2. Dramatic Multi-Cluster Explosion Mesh matching K33.jpeg
    mb_exp = kit.MB(bevel=0.0)
    rng = random.Random(77)

    # A. Glowing Fire Core: clustered faceted icos of yellow, orange, and red
    fire_clusters = [
        (0.0, 0.0, 1.8, 1.8, "fire_yellow"),
        (-0.8, -0.6, 2.4, 2.0, "fire_yellow"),
        (0.7, -0.5, 2.2, 1.9, "fire_orange"),
        (-0.5, 0.8, 2.6, 2.2, "fire_orange"),
        (0.6, 0.7, 2.8, 2.1, "fire_orange"),
        (-1.4, 0.2, 3.2, 2.2, "fire_red"),
        (1.2, -0.4, 3.4, 2.0, "fire_red"),
        (0.2, -1.3, 3.2, 2.1, "fire_red"),
        (0.0, 0.0, 4.0, 2.5, "fire_orange"),
        (-0.9, -0.8, 4.6, 2.4, "fire_red"),
        (0.8, 0.6, 4.8, 2.3, "fire_orange"),
    ]
    for fx, fy, fz, fr, fm in fire_clusters:
        mb_exp.ico(T(fx, fy, fz), fm, r=fr, sub=1, jitter=0.22, rng=rng)

    # B. Billowing Smoke Plume climbing in a tall faceted chimney column (K33)
    smoke_column = [
        (-0.6, 0.4, 6.0, 2.3, "smoke_dk"),
        (0.7, -0.5, 6.8, 2.5, "smoke_dk"),
        (-0.4, -0.7, 7.8, 2.6, "smoke_dk"),
        (0.5, 0.6, 8.8, 2.7, "smoke_dk"),
        (-0.6, -0.3, 10.0, 2.8, "smoke_md"),
        (0.6, 0.4, 11.2, 2.9, "smoke_md"),
        (-0.3, 0.7, 12.5, 3.0, "smoke_md"),
        (0.4, -0.5, 13.8, 3.1, "smoke_md"),
        (-0.5, -0.4, 15.2, 3.2, "smoke_md"),
        (0.3, 0.5, 16.8, 3.2, "smoke_md"),
        (0.0, 0.0, 18.5, 3.0, "smoke_md"),
    ]
    for sx, sy, sz, sr, sm in smoke_column:
        mb_exp.ico(T(sx, sy, sz), sm, r=sr, sub=1, jitter=0.20, rng=rng)

    # C. Flying Debris: blasting timber beams, thatch, and shrapnel
    for i in range(24):
        a = rng.uniform(0, math.tau)
        elev = rng.uniform(0.2, 1.2)
        dist = rng.uniform(3.5, 9.0)
        px = math.cos(a) * math.cos(elev) * dist
        py = math.sin(a) * math.cos(elev) * dist
        pz = math.sin(elev) * dist + 2.5
        mb_exp.box(T(px, py, pz) @ Rx(rng.uniform(0, 3)) @ Ry(rng.uniform(0, 3)) @ S(0.28, 1.6, 0.18), "plank")

    exp_ob = mb_exp.obj("PowderExplosion", fx_c)
    for m_name in ("fire_yellow", "fire_orange", "fire_red", "smoke_dk", "smoke_md", "plank"):
        exp_ob.data.materials.append(bmat(m_name))

    exp_ob.location = (24.0, -4.5, 0.0)

    # Dynamic explosion growth keyframes
    exp_ob.scale = (0.01, 0.01, 0.01)
    exp_ob.keyframe_insert("scale", frame=blast_frame - 1)
    exp_ob.scale = (0.4, 0.4, 0.4)
    exp_ob.keyframe_insert("scale", frame=blast_frame)
    exp_ob.scale = (0.9, 0.9, 1.0)
    exp_ob.keyframe_insert("scale", frame=blast_frame + 6)
    exp_ob.scale = (1.05, 1.05, 1.2)
    exp_ob.keyframe_insert("scale", frame=blast_frame + 24)
    exp_ob.scale = (1.15, 1.15, 1.45)
    exp_ob.keyframe_insert("scale", frame=blast_frame + 70)
    exp_ob.scale = (1.25, 1.25, 1.7)
    exp_ob.keyframe_insert("scale", frame=blast_frame + 180)

    # Flash point light
    blast_light = bpy.data.lights.new("BlastLight", "POINT")
    blast_light.color = (1.0, 0.70, 0.20)
    blast_light.energy = 0.0
    blast_light_ob = bpy.data.objects.new("BlastLight", blast_light)
    blast_light_ob.location = (24.0, -4.5, 3.8)
    fx_c.objects.link(blast_light_ob)

    blast_light.keyframe_insert("energy", frame=blast_frame - 1)
    blast_light.energy = 8000.0
    blast_light.keyframe_insert("energy", frame=blast_frame + 2)
    blast_light.energy = 2500.0
    blast_light.keyframe_insert("energy", frame=blast_frame + 16)
    blast_light.energy = 400.0
    blast_light.keyframe_insert("energy", frame=blast_frame + 50)
    blast_light.energy = 0.0
    blast_light.keyframe_insert("energy", frame=blast_frame + 100)

    exp_ob.hide_render = True
    exp_ob.keyframe_insert("hide_render", frame=1)
    exp_ob.keyframe_insert("hide_render", frame=blast_frame - 1)
    exp_ob.hide_render = False
    exp_ob.keyframe_insert("hide_render", frame=blast_frame)

    return {"shell": ball, "explosion": exp_ob, "light": blast_light_ob}


def build_world(end_frame=700, blast_frame=400):
    register_palette()
    setup_sky()
    coll = bpy.data.collections.new("BattleWorld")
    bpy.context.scene.collection.children.link(coll)
    rng = random.Random(33)

    build_terrain(coll, rng)
    tw = build_travancore_earthworks(coll)
    army = build_allied_army(coll)
    fx = build_mortar_and_explosion(coll, blast_frame=blast_frame)

    # Sunlight
    sun_data = bpy.data.lights.new(name="BattleSun", type="SUN")
    sun_data.color = (1.0, 0.94, 0.84)
    sun_data.energy = 4.2
    sun_ob = bpy.data.objects.new("BattleSun", sun_data)
    sun_ob.location = (-30.0, -25.0, 35.0)
    sun_ob.rotation_euler = (math.radians(42), math.radians(16), math.radians(-35))
    coll.objects.link(sun_ob)

    # Ambient Skyfill
    fill_data = bpy.data.lights.new(name="SkyFill", type="SUN")
    fill_data.color = (0.78, 0.86, 0.96)
    fill_data.energy = 1.5
    fill_ob = bpy.data.objects.new("SkyFill", fill_data)
    fill_ob.location = (20.0, 20.0, 30.0)
    fill_ob.rotation_euler = (math.radians(-50), math.radians(10), math.radians(130))
    coll.objects.link(fill_ob)

    return {"collection": coll, "allied": army, "travancore": tw, "fx": fx}
