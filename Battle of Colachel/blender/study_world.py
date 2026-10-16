"""Van Imhoff's Study in Dutch Kochi Fort (S20, shot-list clip 26).

Laid out to match Flow reference frames/flow_refs/K26.jpeg:
Interior room inside the Dutch fort at night. Van Imhoff in powdered wig and dark
governor's coat seated on the left at his desk writing by candlelight, with scrolls,
quill, inkwell, brass globe on the right, tall bookcase with colorful books,
stacks of crates, patterned rug, and an open casement window on the right looking
out onto the moonlit harbor with a moored Dutch East Indiaman ship.

Coordinates: metres, Z up, floor at z = 0. Camera looks south (-Y), so -X is right.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import colachel_kit as kit
import colachel_world as cw
from colachel_kit import T, Rx, Ry, Rz, S

STUDY_PALETTE = {
    "wall_plaster": (0.88, 0.84, 0.76),
    "beam_dark":    (0.24, 0.18, 0.14),
    "floor_plank":  (0.48, 0.36, 0.26),
    "wood_desk":    (0.40, 0.28, 0.20),
    "wood_shelf":   (0.34, 0.24, 0.17),
    "book_red":     (0.68, 0.18, 0.14),
    "book_blue":    (0.16, 0.28, 0.52),
    "book_green":   (0.22, 0.44, 0.22),
    "book_gold":    (0.78, 0.62, 0.26),
    "book_page":    (0.86, 0.82, 0.72),
    "window_frame": (0.84, 0.46, 0.20),
    "rug_base":     (0.38, 0.28, 0.36),
    "rug_pattern":  (0.72, 0.65, 0.48),
    "wax_red":      (0.75, 0.12, 0.10),
    "candle_wax":   (0.92, 0.88, 0.75),
    "flame":        (1.00, 0.78, 0.25),
}


def register_palette():
    for name, rgb in STUDY_PALETTE.items():
        kit.PALETTE[name] = rgb
        kit.mat(name, rgb)


def smat(name):
    if name in STUDY_PALETTE:
        return kit.mat(name, STUDY_PALETTE[name])
    return kit.mat(name, kit.PALETTE[name])


def build_room(coll):
    """Room walls, ceiling beams, wooden floor, and open window on west wall (-X)."""
    mb = kit.MB(bevel=0.015)
    # Floor: 8m wide x 7m deep
    mb.box(T(0, 0, -0.05) @ S(8.0, 7.0, 0.1), "floor_plank")
    # Back wall (Y = -3.5)
    mb.box(T(0, -3.5, 2.0) @ S(8.0, 0.2, 4.0), "wall_plaster")
    # Right wall (X = 4.0) solid
    mb.box(T(4.0, 0, 2.0) @ S(0.2, 7.0, 4.0), "wall_plaster")
    # Left/West wall (X = -4.0) with cutout for window (center at Y = -0.3, Z = 1.75)
    mb.box(T(-4.0, -2.6, 2.0) @ S(0.2, 2.0, 4.0), "wall_plaster")
    mb.box(T(-4.0, 2.0, 2.0) @ S(0.2, 3.0, 4.0), "wall_plaster")
    mb.box(T(-4.0, -0.3, 0.4) @ S(0.2, 2.6, 0.8), "wall_plaster")
    mb.box(T(-4.0, -0.3, 3.2) @ S(0.2, 2.6, 1.6), "wall_plaster")

    # Dark timber beams along ceiling and walls
    mb.box(T(0, -3.4, 3.8) @ S(8.0, 0.25, 0.25), "beam_dark")
    mb.box(T(-3.9, 0, 3.8) @ S(0.25, 7.0, 0.25), "beam_dark")
    mb.box(T(3.9, 0, 3.8) @ S(0.25, 7.0, 0.25), "beam_dark")
    for x in (-2.5, 0.0, 2.5):
        mb.box(T(x, 0, 3.85) @ S(0.2, 7.0, 0.2), "beam_dark")
    # Posts & braces
    mb.box(T(3.85, -3.35, 1.9) @ S(0.25, 0.25, 3.8), "beam_dark")
    mb.box(T(-0.8, -3.35, 1.9) @ S(0.25, 0.25, 3.8), "beam_dark")
    mb.box(T(-0.8, -3.32, 3.3) @ Ry(0.7) @ S(0.18, 0.18, 1.1), "beam_dark")
    mb.box(T(-0.8, -3.32, 3.3) @ Ry(-0.7) @ S(0.18, 0.18, 1.1), "beam_dark")

    # Patterned rug on floor
    mb.box(T(0.5, -0.5, 0.01) @ S(3.5, 4.2, 0.02), "rug_base")
    mb.box(T(0.5, -0.5, 0.015) @ S(3.2, 3.9, 0.015), "rug_pattern")
    mb.box(T(0.5, -0.5, 0.02) @ S(2.8, 3.5, 0.015), "rug_base")

    # Window frame on west wall (X = -3.95, Y = -0.3, Z = 1.75)
    wx, wy, wz = -3.95, -0.3, 1.75
    ww, wh = 2.0, 1.7
    mb.box(T(wx, wy, wz - wh / 2) @ S(0.25, ww + 0.15, 0.1), "window_frame")
    mb.box(T(wx, wy, wz + wh / 2) @ S(0.25, ww + 0.15, 0.1), "window_frame")
    mb.box(T(wx, wy - ww / 2, wz) @ S(0.25, 0.1, wh), "window_frame")
    mb.box(T(wx, wy + ww / 2, wz) @ S(0.25, 0.1, wh), "window_frame")
    # Open window casement swinging outward into the night
    mb.box(T(wx - 0.5, wy - 0.4, wz) @ Rz(-1.2) @ S(0.06, 0.95, wh - 0.1), "window_frame")
    for sy in (-0.28, 0.28):
        mb.box(T(wx - 0.5, wy - 0.4 + sy, wz) @ Rz(-1.2) @ S(0.07, 0.05, wh - 0.1), "window_frame")
    for sz in (-0.38, 0.0, 0.38):
        mb.box(T(wx - 0.5, wy - 0.4, wz + sz) @ Rz(-1.2) @ S(0.07, 0.9, 0.05), "window_frame")

    ob = mb.obj("StudyRoom", coll)
    for m in STUDY_PALETTE:
        ob.data.materials.append(smat(m))
    return ob


def build_bookcase(coll, x=1.4, y=-3.3, z=0.0):
    """Tall wooden bookcase against back wall with colorful books."""
    mb = kit.MB(bevel=0.01)
    bw, bd, bh = 1.8, 0.45, 2.5
    mb.box(T(x, y, z + bh / 2) @ S(bw, bd, bh), "wood_shelf")
    shelves_z = [0.4, 0.9, 1.4, 1.9, 2.3]
    rng = random.Random(42)
    book_colors = ["book_red", "book_blue", "book_green", "book_gold", "beam_dark"]
    for sz in shelves_z[:-1]:
        curr_x = x - bw / 2 + 0.15
        while curr_x < x + bw / 2 - 0.15:
            b_th = rng.uniform(0.04, 0.08)
            b_ht = rng.uniform(0.30, 0.42)
            c = rng.choice(book_colors)
            mb.box(T(curr_x + b_th / 2, y + 0.08, z + sz + b_ht / 2) @ S(b_th, bd * 0.7, b_ht), c)
            curr_x += b_th + rng.uniform(0.005, 0.02)
    ob = mb.obj("Bookcase", coll)
    for m in STUDY_PALETTE:
        ob.data.materials.append(smat(m))
    return ob


def build_desk_and_props(coll, x=0.0, y=-0.5, z=0.0):
    """Large executive wooden desk, chair, candle, parchment, scrolls, inkwell, globe."""
    mb = kit.MB(bevel=0.01)
    dw, dd, dh = 2.2, 1.1, 0.82
    mb.box(T(x, y, z + dh) @ S(dw, dd, 0.08), "wood_desk")
    mb.box(T(x - dw / 2 + 0.18, y, z + dh / 2) @ S(0.28, dd * 0.92, dh), "wood_desk")
    mb.box(T(x + dw / 2 - 0.18, y, z + dh / 2) @ S(0.28, dd * 0.92, dh), "wood_desk")
    mb.box(T(x, y + dd / 2 - 0.08, z + dh * 0.55) @ S(dw - 0.4, 0.06, dh * 0.7), "wood_desk")

    # Desk chair behind desk on the East side (facing +Y towards desk)
    cx, cy, cz = x + 0.35, y - 0.45, z
    mb.box(T(cx, cy, cz + 0.46) @ S(0.65, 0.65, 0.08), "beam_dark")
    mb.box(T(cx, cy - 0.28, cz + 0.92) @ S(0.65, 0.08, 0.84), "beam_dark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(T(cx + sx * 0.26, cy + sy * 0.26, cz + 0.23) @ S(0.06, 0.06, 0.46), "beam_dark")

    # Desk props (matches K26!):
    # 1. Blank parchment manuscript in front of Imhoff
    mb.box(T(x + 0.25, y, z + dh + 0.05) @ S(0.65, 0.45, 0.01), "book_page")
    mb.box(T(x + 0.55, y, z + dh + 0.06) @ S(0.35, 0.42, 0.03), "white")

    # 2. Rolled parchment scroll
    mb.cone(T(x - 0.15, y + 0.12, z + dh + 0.08) @ Ry(math.pi / 2), "book_page", segments=8, r1=0.06, r2=0.06, depth=0.45)

    # 3. Sealed letter with red wax stamp
    mb.box(T(x - 0.35, y - 0.12, z + dh + 0.05) @ S(0.26, 0.18, 0.01), "white")
    mb.ico(T(x - 0.35, y - 0.12, z + dh + 0.06), "wax_red", r=0.035, sub=1)

    # 4. Brass candlestick with candle & flame (between Imhoff and scroll)
    cand_x, cand_y, cand_z = x - 0.08, y + 0.15, z + dh + 0.04
    mb.cone(T(cand_x, cand_y, cand_z + 0.03), "brass", segments=8, r1=0.12, r2=0.08, depth=0.06)
    mb.cone(T(cand_x, cand_y, cand_z + 0.10), "brass", segments=8, r1=0.03, r2=0.02, depth=0.14)
    mb.cone(T(cand_x, cand_y, cand_z + 0.20), "candle_wax", segments=6, r1=0.025, r2=0.025, depth=0.16)
    mb.ico(T(cand_x, cand_y, cand_z + 0.30) @ S(0.025, 0.025, 0.05), "flame", r=1.0, sub=1)

    # 5. Inkwell and white quill
    mb.box(T(x - 0.52, y + 0.20, z + dh + 0.08) @ S(0.12, 0.12, 0.12), "dark")
    mb.box(T(x - 0.52, y + 0.20, z + dh + 0.22) @ Rx(0.3) @ S(0.015, 0.015, 0.28), "white")

    # 6. Tabletop brass globe on wooden stand (West side of desk -> RIGHT of camera view!)
    gx, gy, gz = x - 0.85, y + 0.10, z + dh + 0.04
    mb.cone(T(gx, gy, gz + 0.04), "wood_shelf", segments=8, r1=0.12, r2=0.08, depth=0.08)
    mb.seg((gx, gy, gz + 0.08), (gx, gy, gz + 0.24), 0.025, 0.025, "brass", sides=6)
    mb.ico(T(gx, gy, gz + 0.32), "gold", r=0.15, sub=1)
    mb.seg((gx - 0.16, gy, gz + 0.32), (gx + 0.16, gy, gz + 0.32), 0.015, 0.015, "brass", sides=6)

    ob = mb.obj("StudyDeskAndProps", coll)
    for m in STUDY_PALETTE:
        ob.data.materials.append(smat(m))
    for m in ("white", "dark", "brass", "gold", "beam_dark"):
        ob.data.materials.append(kit.mat(m, kit.PALETTE[m]))

    # Warm point light for candle
    lamp_data = bpy.data.lights.new(name="CandleLight", type="POINT")
    lamp_data.color = (1.0, 0.72, 0.35)
    lamp_data.energy = 45.0
    lamp_data.shadow_soft_size = 0.15
    lamp_ob = bpy.data.objects.new("CandleLight", lamp_data)
    lamp_ob.location = (cand_x, cand_y, cand_z + 0.35)
    coll.objects.link(lamp_ob)

    return ob, (cand_x, cand_y, cand_z)


def build_exterior_harbor(coll):
    """Night harbor scene outside the west window (-X direction)."""
    ext_c = kit.new_collection("HarborExterior")
    w_mb = kit.MB(bevel=0.0)
    w_mb.box(T(-18.0, 5.0, -0.6) @ S(30.0, 30.0, 0.2), "paddy_water")
    w_ob = w_mb.obj("HarborWater", ext_c)
    w_ob.data.materials.append(kit.mat("paddy_water", (0.05, 0.12, 0.22)))

    j = kit.make_jetty("HarborJetty", ext_c, length=18.0, width=2.4)
    j.location = (-5.5, 0.8, -0.4)
    j.rotation_euler = (0, 0, -0.05)

    ship = kit.make_ship("HarborShip", ext_c, length=24.0, beam=6.5)
    ship.location = (-8.5, 2.2, 0.2)
    ship.rotation_euler = (0, 0, 2.1)
    ship.scale = (0.75, 0.75, 0.75)

    palm = kit.make_palm("HarborPalm", ext_c, seed=15, height=5.5)
    palm.location = (-4.8, -0.6, -0.4)

    # Cool blue moonlight entering through the west window
    moon_data = bpy.data.lights.new(name="Moonlight", type="SUN")
    moon_data.color = (0.35, 0.60, 0.95)
    moon_data.energy = 5.0
    moon_ob = bpy.data.objects.new("Moonlight", moon_data)
    moon_ob.location = (-12.0, 2.0, 6.0)
    moon_ob.rotation_euler = (math.radians(35), math.radians(-25), math.radians(55))
    coll.objects.link(moon_ob)

    # Warm room ambient fill
    amb_data = bpy.data.lights.new(name="RoomAmb", type="POINT")
    amb_data.color = (0.95, 0.88, 0.78)
    amb_data.energy = 110.0
    amb_ob = bpy.data.objects.new("RoomAmb", amb_data)
    amb_ob.location = (0.5, 1.2, 2.8)
    coll.objects.link(amb_ob)


def build_world(end_frame=360):
    register_palette()
    coll = bpy.data.collections.new("StudyWorld")
    bpy.context.scene.collection.children.link(coll)

    build_room(coll)
    build_bookcase(coll, x=1.4, y=-3.3, z=0.0)
    desk_ob, cand_pos = build_desk_and_props(coll, x=0.0, y=-0.5, z=0.0)

    # Stack of crates in east corner
    cr_c = kit.new_collection("Crates")
    c1 = kit.make_crate("Crate1", cr_c, size=0.7)
    c1.location = (3.2, 1.8, 0.0)
    c2 = kit.make_crate("Crate2", cr_c, size=0.6)
    c2.location = (3.2, 1.8, 0.7)
    c3 = kit.make_crate("Crate3", cr_c, size=0.65)
    c3.location = (3.1, 0.9, 0.0)
    c3.rotation_euler = (0, 0, -0.3)

    # Van Imhoff figure seated at desk writing (elevated to chair height z=0.48)
    fig_c = kit.new_collection("Cast")
    imhoff = kit.make_figure("VanImhoff", fig_c, "imhoff", pose="write")
    imhoff.location = (0.35, -0.85, 0.48)
    imhoff.rotation_euler = (0, 0, -0.15)

    build_exterior_harbor(coll)

    return {"collection": coll, "imhoff": imhoff, "candle": cand_pos}
