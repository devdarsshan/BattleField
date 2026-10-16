"""The Royal Meeting under the Canopy (Beats S21, S22, S23, Clips 27-30).

Built in its own file Meeting.blend.
Matches Flow references:
- frames/flow_refs/K27.jpeg (S21-S22: Van Imhoff standing & pointing vs King Marthanda Varma seated on throne under canopy)
- frames/flow_refs/K30.jpeg (S23: Close-up on the calm King with arms folded)
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S

MEETING_PALETTE = {
    "tent_white":   (0.92, 0.90, 0.85),
    "canopy_cloth": (0.95, 0.92, 0.86),
    "tassel_gold":  (0.85, 0.68, 0.25),
    "table_dark":   (0.38, 0.25, 0.16),
    "sand_court":   (0.88, 0.76, 0.58),
    "roof_tile":    (0.70, 0.30, 0.18),
    "nair_shield":  (0.22, 0.20, 0.18),
}


def register_palette():
    for name, rgb in MEETING_PALETTE.items():
        kit.PALETTE[name] = rgb
        kit.mat(name, rgb)


def smat(name):
    if name in MEETING_PALETTE:
        return kit.mat(name, MEETING_PALETTE[name])
    return kit.mat(name, kit.PALETTE[name])


def make_seated_king(name, collection, pose="regal"):
    """Seated King Marthanda Varma matching K27 and K30.
    pose: 'regal' (hands on sword / lap as in K27), 'arms_folded' (as in K30).
    """
    mb = kit.MB(bevel=kit.FIG_BEVEL)
    skin = "skin"

    # Head and neck (proportional to torso)
    mb.cone(T(0, 0, 1.43), skin, segments=6, r1=0.075, r2=0.07, depth=0.08)
    mb.ico(T(0, 0, 1.56) @ S(0.95, 1.0, 1.05), skin, r=0.145, sub=1)
    # Eyes & nose
    for sx in (-1, 1):
        mb.box(T(sx * 0.048, 0.128, 1.585) @ S(0.032, 0.02, 0.034), "black")
    mb.box(T(0, 0.14, 1.548) @ S(0.034, 0.04, 0.055), skin)
    # Royal moustache
    mb.box(T(0, 0.13, 1.515) @ S(0.12, 0.025, 0.026), "hair")

    # Red & gold royal turban with white aigrette feather (matches K27 & K30!)
    mb.cone(T(0, 0, 1.64), "red", segments=8, r1=0.16, r2=0.17, depth=0.08)
    mb.cone(T(0, -0.01, 1.705) @ Rx(-0.12), "red", segments=8, r1=0.168, r2=0.14, depth=0.07)
    mb.ico(T(0, -0.01, 1.74) @ S(1.0, 1.0, 0.55), "red", r=0.13, sub=1)
    mb.cone(T(0, 0, 1.675) @ Rx(-0.06), "gold", segments=8, r1=0.172, r2=0.172, depth=0.03)
    mb.ico(T(0, 0.155, 1.72), "gold", r=0.04, sub=1)
    mb.box(T(0, 0.16, 1.80) @ S(0.025, 0.02, 0.13), "white") # Aigrette plume

    # Torso (bare chest with gold ornaments)
    mb.cone(T(0, 0, 1.15), skin, segments=8, r1=0.25, r2=0.20, depth=0.55)
    # Gold necklaces hanging on chest
    for z, r in ((1.32, 0.17), (1.23, 0.20), (1.14, 0.22)):
        mb.cone(T(0, 0.02, z) @ Rx(-0.25), "gold", segments=10, r1=r, r2=r, depth=0.025)
    # Red & gold sash around waist
    mb.box(T(0, 0, 0.88) @ S(0.48, 0.36, 0.08), "red")
    mb.box(T(0, 0.005, 0.88) @ S(0.50, 0.36, 0.04), "gold")

    # Lower body: seated lap and hanging dhoti (mundu)
    # Lap on throne
    mb.box(T(0, 0.18, 0.72) @ S(0.52, 0.44, 0.24), "white")
    # Dhoti draping down vertically in front of chair
    mb.box(T(0, 0.35, 0.38) @ S(0.48, 0.18, 0.48), "white")
    # Gold & red border strip running down center of dhoti
    mb.box(T(0, 0.37, 0.38) @ S(0.11, 0.17, 0.49), "red")
    mb.box(T(0, 0.375, 0.38) @ S(0.04, 0.17, 0.49), "gold")
    # Bare feet resting on carpet
    mb.box(T(-0.14, 0.38, 0.06) @ S(0.11, 0.22, 0.08), skin)
    mb.box(T(0.14, 0.38, 0.06) @ S(0.11, 0.22, 0.08), skin)

    # Arms
    if pose == "arms_folded":
        # Arms crossed across chest (K30)
        # Left arm
        mb.box(T(0.16, 0.12, 1.26) @ Rz(-0.35) @ Ry(0.8) @ S(0.10, 0.11, 0.42), skin)
        # Right arm
        mb.box(T(-0.16, 0.14, 1.22) @ Rz(0.35) @ Ry(-0.8) @ S(0.10, 0.11, 0.42), skin)
        # Forearms crossed
        mb.box(T(0.0, 0.21, 1.20) @ S(0.48, 0.11, 0.11), skin)
        # Gold armbands
        mb.box(T(0.24, 0.05, 1.34) @ S(0.12, 0.12, 0.04), "gold")
        mb.box(T(-0.24, 0.05, 1.34) @ S(0.12, 0.12, 0.04), "gold")
    else:
        # Regal seated pose (K27): hands on sword & knee
        mb.box(T(-0.24, 0.10, 1.15) @ Rx(0.4) @ S(0.10, 0.11, 0.36), skin)
        mb.box(T(0.24, 0.10, 1.15) @ Rx(0.4) @ S(0.10, 0.11, 0.36), skin)
        # Forearms forward towards lap
        mb.box(T(-0.22, 0.26, 0.90) @ Rx(1.2) @ S(0.09, 0.10, 0.30), skin)
        mb.box(T(0.20, 0.24, 0.88) @ Rx(1.1) @ Rz(-0.2) @ S(0.09, 0.10, 0.30), skin)
        # Royal sword resting along leg
        for i in range(4):
            mb.box(T(0.22 + 0.02 * i, 0.12 + 0.12 * i, 0.72 - 0.12 * i) @ Rx(-0.7 + i * 0.18) @ S(0.03, 0.22, 0.05), "steel")
        mb.box(T(0.20, 0.18, 0.88) @ S(0.06, 0.12, 0.06), "gold") # Sword hilt
        # Gold armbands
        mb.box(T(0.25, 0.05, 1.28) @ S(0.12, 0.12, 0.04), "gold")
        mb.box(T(-0.25, 0.05, 1.28) @ S(0.12, 0.12, 0.04), "gold")

    return mb.obj(name, collection)


def make_nair_guard(name, collection, seed=0, has_spear=True):
    """Nair warrior with shield matching K27 and K30."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=kit.FIG_BEVEL)
    skin = "skin"

    # Head & neck
    mb.cone(T(0, 0, 1.47), skin, segments=6, r1=0.065, r2=0.065, depth=0.1)
    mb.ico(T(0, 0, 1.63) @ S(0.9, 0.95, 1.05), skin, r=0.145, sub=1)
    for sx in (-1, 1):
        mb.box(T(sx * 0.048, 0.128, 1.655) @ S(0.032, 0.02, 0.034), "black")
    mb.box(T(0, 0.14, 1.618) @ S(0.034, 0.04, 0.055), skin)
    mb.box(T(0, 0.13, 1.585) @ S(0.11, 0.025, 0.026), "hair")

    # Red headband / turban
    mb.cone(T(0, 0, 1.71), "red", segments=8, r1=0.16, r2=0.16, depth=0.07)
    mb.ico(T(0, -0.01, 1.74) @ S(1.0, 1.0, 0.5), "red", r=0.13, sub=1)

    # Torso (bare chest)
    mb.cone(T(0, 0, 1.15), skin, segments=8, r1=0.24, r2=0.19, depth=0.55)
    mb.box(T(0, 0, 0.88) @ S(0.44, 0.32, 0.08), "red")

    # Lower body (white dhoti with red sash)
    mb.cone(T(0, 0, 0.44), "white", segments=8, r1=0.22, r2=0.20, depth=0.80)
    mb.box(T(0, 0.16, 0.44) @ S(0.08, 0.08, 0.78), "red") # Sash
    # Feet
    mb.box(T(-0.1, 0.04, 0.03) @ S(0.10, 0.20, 0.06), skin)
    mb.box(T(0.1, 0.04, 0.03) @ S(0.10, 0.20, 0.06), skin)

    # Left arm holding round shield
    mb.box(T(0.24, 0.05, 1.15) @ Rx(0.3) @ S(0.10, 0.11, 0.42), skin)
    # Round Kerala dhal shield
    mb.cone(T(0.32, 0.20, 1.05) @ Ry(math.pi / 2), "nair_shield", segments=14, r1=0.38, r2=0.38, depth=0.05)
    mb.cone(T(0.35, 0.20, 1.05) @ Ry(math.pi / 2), "brass", segments=8, r1=0.09, r2=0.03, depth=0.06)
    for a in range(4):
        ang = a * math.pi / 2 + 0.3
        mb.ico(T(0.34, 0.20 + math.cos(ang) * 0.22, 1.05 + math.sin(ang) * 0.22), "brass", r=0.035, sub=1)

    # Right arm holding tall spear
    mb.box(T(-0.24, 0.05, 1.15) @ Rx(0.2) @ S(0.10, 0.11, 0.42), skin)
    if has_spear:
        mb.box(T(-0.28, 0.18, 1.15) @ S(0.04, 0.04, 2.5), "plank") # Spear shaft
        mb.cone(T(-0.28, 0.18, 2.45), "steel", segments=4, r1=0.05, r2=0.0, depth=0.28) # Spear head

    return mb.obj(name, collection)


def build_meeting_canopy(coll, x=0.0, y=0.0, z=0.0, w=5.8, d=4.6, h=3.3):
    """Grand royal canopy matching K27 with draped curtains, tassels, carpet, and treaty table."""
    mb = kit.MB(bevel=0.015)
    # 4 carved wooden corner posts
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = x + sx * (w / 2), y + sy * (d / 2)
            mb.cone(T(px, py, z + h / 2), "plank", segments=8, r1=0.08, r2=0.07, depth=h)
            mb.cone(T(px, py, z + h + 0.1), "gold", segments=8, r1=0.09, r2=0.02, depth=0.2)
            # Gold tassel hanging from corner
            mb.seg((px, py, z + h - 0.05), (px, py, z + h - 0.35), 0.02, 0.04, "gold", sides=6)

    # Canopy canvas roof with slight sag (matches K27 canvas dip!)
    mb.box(T(x, y, z + h + 0.05) @ S(w + 0.4, d + 0.4, 0.06), "canopy_cloth")
    # Thin valance on front and back
    for sy in (-1, 1):
        mb.box(T(x, y + sy * (d / 2 + 0.18), z + h - 0.08) @ S(w + 0.4, 0.03, 0.20), "carpet_red")
        mb.box(T(x, y + sy * (d / 2 + 0.19), z + h - 0.17) @ S(w + 0.4, 0.02, 0.04), "gold")
    for sx in (-1, 1):
        mb.box(T(x + sx * (w / 2 + 0.18), y, z + h - 0.08) @ S(0.03, d + 0.4, 0.20), "carpet_red")
        mb.box(T(x + sx * (w / 2 + 0.19), y, z + h - 0.17) @ S(0.02, d + 0.4, 0.04), "gold")

    # Draped side curtains tied to the back and side posts (matches K27 & K30!)
    for sx in (-1, 1):
        # Curtain fabric bundle tied with gold sash
        mb.cone(T(x + sx * (w / 2 - 0.25), y - d / 2 + 0.35, z + h * 0.65), "canopy_cloth",
                segments=8, r1=0.24, r2=0.14, depth=h * 0.55)
        mb.box(T(x + sx * (w / 2 - 0.25), y - d / 2 + 0.35, z + h * 0.42) @ S(0.30, 0.30, 0.08), "gold")
        mb.cone(T(x + sx * (w / 2 - 0.25), y - d / 2 + 0.35, z + h * 0.2), "canopy_cloth",
                segments=8, r1=0.15, r2=0.26, depth=h * 0.35)

    # Red and gold ceremonial carpet on the sand
    mb.box(T(x, y, z + 0.02) @ S(w * 0.94, d * 0.88, 0.03), "gold")
    mb.box(T(x, y, z + 0.03) @ S(w * 0.86, d * 0.80, 0.03), "carpet_red")
    mb.box(T(x, y, z + 0.035) @ S(w * 0.58, d * 0.52, 0.02), "carpet_gold")
    mb.box(T(x, y, z + 0.04) @ S(w * 0.48, d * 0.42, 0.02), "carpet_red")

    # Low treaty table in center (between Imhoff on left and King on right)
    tw, td, th = 1.3, 0.75, 0.52
    mb.box(T(x, y, z + th) @ S(tw, td, 0.06), "table_dark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cone(T(x + sx * (tw / 2 - 0.08), y + sy * (td / 2 - 0.08), z + th / 2), "table_dark",
                    segments=6, r1=0.06, r2=0.04, depth=th)
    # Treaty parchments and cylindrical brass weights on table
    mb.box(T(x - 0.18, y, z + th + 0.04) @ S(0.42, 0.32, 0.01), "parchment")
    mb.cone(T(x + 0.12, y + 0.06, z + th + 0.06) @ Ry(math.pi / 2), "parchment", segments=8, r1=0.035, r2=0.035, depth=0.30)
    for ox in (-0.05, 0.05, 0.22):
        mb.cone(T(x + ox, y - 0.10, z + th + 0.05), "brass", segments=8, r1=0.025, r2=0.025, depth=0.05)

    ob = mb.obj("MeetingCanopy", coll)
    for m in MEETING_PALETTE:
        ob.data.materials.append(smat(m))
    for m in ("gold", "carpet_red", "carpet_gold", "plank", "brass", "parchment"):
        ob.data.materials.append(kit.mat(m, kit.PALETTE[m]))
    return ob


def build_surroundings(coll, rng):
    """Palms, military tents, sandy ground, and palace rooflines in distance."""
    mb = kit.MB(bevel=0.0)
    # Ground plane (sand courtyard)
    mb.box(T(0, 0, -0.1) @ S(90.0, 90.0, 0.2), "sand_court")
    ob = mb.obj("GroundSand", coll)
    ob.data.materials.append(smat("sand_court"))

    prop_c = kit.new_collection("Props")

    # Military tents in background (+Y direction, behind canopy)
    t1 = kit.make_ridge_tent("Tent1", prop_c, length=4.5, w=3.5, h=2.5)
    t1.location = (-7.5, 6.0, 0.0)
    t1.rotation_euler = (0, 0, 0.2)

    t2 = kit.make_ridge_tent("Tent2", prop_c, length=4.5, w=3.5, h=2.5)
    t2.location = (8.0, 5.5, 0.0)
    t2.rotation_euler = (0, 0, -0.25)

    t3 = kit.make_cone_tent("Tent3", prop_c, r=2.0, h=3.0)
    t3.location = (-11.0, 8.5, 0.0)

    t4 = kit.make_cone_tent("Tent4", prop_c, r=2.0, h=3.0)
    t4.location = (11.5, 8.0, 0.0)

    # Coconut palms framing the scene left, right, and deep background
    palm_c = kit.new_collection("Palms")
    palm_coords = [
        (-8.5, -3.0, 8.5), (-9.5, 2.0, 9.0), (-12.0, 6.0, 10.0), (-6.0, 10.5, 9.5),
        (8.5, -2.5, 8.5), (9.5, 3.0, 9.0), (12.5, 7.0, 10.0), (6.5, 11.0, 9.5),
        (-2.5, 12.0, 10.5), (2.0, 12.5, 10.0), (-14.0, -1.0, 9.0), (14.0, -0.5, 9.0),
    ]
    for i, (px, py, ph) in enumerate(palm_coords):
        p = kit.make_palm(f"Palm_{i}", palm_c, seed=i * 7 + 3, height=ph)
        p.location = (px, py, 0.0)
        p.rotation_euler = (rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), rng.uniform(0, 6.28))

    # Traditional Kerala palace rooflines in distant background (+Y)
    p_mb = kit.MB(bevel=0.02)
    p_mb.box(T(0.0, 22.0, 3.5) @ S(16.0, 7.0, 7.0), "wall")
    p_mb.cone(T(0.0, 22.0, 8.2) @ S(17.5, 8.5, 1.0), "roof_tile", segments=4, r1=1.0, r2=0.08, depth=2.8)
    p_mb.cone(T(0.0, 18.0, 7.2) @ S(4.5, 3.5, 1.0), "roof_tile", segments=3, r1=0.9, r2=0.05, depth=1.8)
    p_ob = p_mb.obj("DistantPalace", prop_c)
    p_ob.data.materials.append(kit.mat("wall", kit.PALETTE["wall"]))
    p_ob.data.materials.append(smat("roof_tile"))


def setup_sky():
    w = bpy.data.worlds.new("MeetingSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.80, 0.88, 0.95, 1.0)
        bg.inputs["Strength"].default_value = 1.0


def build_world(end_frame=1300):
    setup_sky()
    register_palette()
    coll = bpy.data.collections.new("MeetingWorld")
    bpy.context.scene.collection.children.link(coll)
    rng = random.Random(27)

    # Build canopy structure
    build_meeting_canopy(coll, x=0.0, y=0.0, z=0.0, w=5.8, d=4.6, h=3.3)

    # Surroundings: ground, palms, tents, distant palace
    build_surroundings(coll, rng)

    # Royal Throne on the Right side (X = +1.6, Y = 0.0)
    throne_c = kit.new_collection("Throne")
    throne = kit.make_throne("RoyalThrone", throne_c, w=1.05, d=0.85, h=1.7)
    throne.location = (1.55, 0.0, 0.0)
    throne.rotation_euler = (0, 0, math.radians(115))  # Angled 3/4 towards Imhoff & camera

    # Small brass water vessel on side table (matches K30!)
    t_mb = kit.MB(bevel=0.01)
    t_mb.box(T(2.25, -0.45, 0.22) @ S(0.35, 0.35, 0.44), "table_dark")
    t_mb.ico(T(2.25, -0.45, 0.50), "brass", r=0.07, sub=1)
    t_mb.cone(T(2.25, -0.45, 0.60), "brass", segments=6, r1=0.03, r2=0.05, depth=0.12)
    t_ob = t_mb.obj("SideTableBrass", throne_c)
    t_ob.data.materials.append(smat("table_dark"))
    t_ob.data.materials.append(kit.mat("brass", kit.PALETTE["brass"]))

    # Cast collection for named figures and guards
    cast_c = kit.new_collection("Cast")

    # 1. King Marthanda Varma seated on throne
    # For S21-S22: king in regal pose
    king_regal = make_seated_king("KingMarthandaVarma_Regal", cast_c, pose="regal")
    king_regal.location = (1.55, 0.0, 0.0)
    king_regal.rotation_euler = (0, 0, math.radians(115))

    # For S23 (K30): king with arms folded across chest
    king_folded = make_seated_king("KingMarthandaVarma_Folded", cast_c, pose="arms_folded")
    king_folded.location = (1.55, 0.0, 0.0)
    king_folded.rotation_euler = (0, 0, math.radians(115))

    # Animate visibility between the two versions on frame 950 (transition from S22 to S23)
    king_regal.hide_render = False
    king_regal.hide_viewport = False
    king_regal.keyframe_insert("hide_render", frame=1)
    king_regal.keyframe_insert("hide_render", frame=950)
    king_regal.hide_render = True
    king_regal.keyframe_insert("hide_render", frame=951)

    king_folded.hide_render = True
    king_folded.hide_viewport = True
    king_folded.keyframe_insert("hide_render", frame=1)
    king_folded.keyframe_insert("hide_render", frame=950)
    king_folded.hide_render = False
    king_folded.keyframe_insert("hide_render", frame=951)

    # 2. Van Imhoff standing on the Left side pointing firmly at the King
    imhoff = kit.make_figure("VanImhoff", cast_c, "imhoff", pose="point")
    imhoff.location = (-1.55, 0.0, 0.0)
    imhoff.rotation_euler = (0, 0, -math.pi / 2)  # Facing east (+X) towards King

    # 3. Two Dutch soldiers standing behind Van Imhoff (X = -2.4) with muskets
    d1 = kit.make_figure("DutchGuard1", cast_c, "dutch", seed=10, armed=True)
    d1.location = (-2.4, 0.55, 0.0)
    d1.rotation_euler = (0, 0, -math.pi / 2 + 0.08)

    d2 = kit.make_figure("DutchGuard2", cast_c, "dutch", seed=20, armed=True)
    d2.location = (-2.4, -0.55, 0.0)
    d2.rotation_euler = (0, 0, -math.pi / 2 - 0.08)

    # 4. Three Nair royal bodyguards standing behind the King (X = +2.4)
    n1 = make_nair_guard("NairGuard1", cast_c, seed=30, has_spear=True)
    n1.location = (2.45, 0.75, 0.0)
    n1.rotation_euler = (0, 0, math.radians(125))

    n2 = make_nair_guard("NairGuard2", cast_c, seed=40, has_spear=False)
    n2.location = (2.65, -0.05, 0.0)
    n2.rotation_euler = (0, 0, math.radians(115))

    n3 = make_nair_guard("NairGuard3", cast_c, seed=50, has_spear=True)
    n3.location = (2.45, -0.85, 0.0)
    n3.rotation_euler = (0, 0, math.radians(105))

    # Lighting setup:
    # 1. Warm tropical exterior sun
    sun_data = bpy.data.lights.new(name="Sun", type="SUN")
    sun_data.color = (1.0, 0.95, 0.88)
    sun_data.energy = 4.0
    sun_ob = bpy.data.objects.new("Sun", sun_data)
    sun_ob.location = (-15.0, -18.0, 22.0)
    sun_ob.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))
    coll.objects.link(sun_ob)

    # 2. Camera-side soft warm daylight fill
    cam_fill_data = bpy.data.lights.new(name="FrontFill", type="SUN")
    cam_fill_data.color = (1.0, 0.98, 0.94)
    cam_fill_data.energy = 2.5
    cam_fill_ob = bpy.data.objects.new("FrontFill", cam_fill_data)
    cam_fill_ob.location = (0.0, -15.0, 10.0)
    cam_fill_ob.rotation_euler = (math.radians(60), 0, 0)
    coll.objects.link(cam_fill_ob)

    # 3. Soft ambient light under canopy
    canopy_light = bpy.data.lights.new(name="CanopyLight", type="AREA")
    canopy_light.shape = "RECTANGLE"
    canopy_light.size = 5.0
    canopy_light.size_y = 4.0
    canopy_light.color = (1.0, 0.95, 0.88)
    canopy_light.energy = 80.0
    canopy_ob = bpy.data.objects.new("CanopyLight", canopy_light)
    canopy_ob.location = (0.0, 0.0, 3.1)
    coll.objects.link(canopy_ob)

    return {"collection": coll, "king": king_regal, "imhoff": imhoff}
