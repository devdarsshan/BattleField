"""Van Imhoff's study in the Dutch fort at Kochi, at night (S20, shot-list clip 26).

Laid out to match the Flow reference frames/flow_refs/K26.jpeg: a beamed room with cream
plaster walls, dark timber posts and knee braces, plank floor, a patterned carpet, stacked
crates and pepper sacks; a tall bookcase full of books; Imhoff (kit "imhoff", posable rig)
writing at a big desk by one candle, with blank papers, a rolled map, scrolls, an inkwell, a
sealed letter and a brass globe; an orange-framed casement window, open, looking out on the
moonlit harbour: the faceted sea, a jetty with a sentry and a lantern, palms and a moored
East Indiaman under set sails.

Light (the film's one interior / night exception to colachel_world.scene_base): a warm
candle key and a cool blue moon fill through the window. Palette, figures, palms, ship,
jetty, crates and sea are the shared kit parts.

Coordinates: metres, Z up, room floor at z = 0 (the study is an upper floor of the fort, the
harbour water lies about 1 m below it). The desk is at the origin with its front toward +Y (the camera);
the back wall is at y = BACK_Y, the window in it at x = WIN_X.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import colachel_kit as kit
import colachel_world as cw
import kochi_world as kw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau

# ------------------------------------------------------------------- layout
BACK_Y = -2.9                 # inner face of the back wall
LEFT_X, RIGHT_X = -3.9, 4.6   # inner faces of the side walls (+X is screen LEFT: the camera looks down -Y)
CEIL = 3.5
WIN_X, WIN_W, WIN_Z0, WIN_H = -2.45, 1.75, 0.85, 1.7     # window centre x, width, sill height, height
DESK = (0.0, 0.0)
DESK_H = 0.78
IMHOFF = (0.55, -0.72)       # root of the seated rig (behind the desk, facing +Y)
CANDLE = (-0.02, 0.18)
SEA_Z = -1.1                  # harbour water level below the room floor


def shore_y(x):
    return -15.0 + 1.6 * math.sin(x / 9.0) + 0.8 * math.sin(x / 3.7 + 1.0)


# ------------------------------------------------------------------- light
def setup_night_world():
    """Night sky: deep blue zenith, lighter blue-grey horizon (the cool fill's source)."""
    w = bpy.data.worlds.new("Night")
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
    mr.inputs["From Min"].default_value = -0.02
    mr.inputs["From Max"].default_value = 0.5
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    cr.elements[0].color = (*kit.srgb_to_linear((0.22, 0.30, 0.46)), 1)
    cr.elements[1].color = (*kit.srgb_to_linear((0.05, 0.08, 0.18)), 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.9
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w


def add_lights(coll, frames):
    """Warm candle key (flickering) + cool moonlight and window fill."""
    rng = random.Random(4)
    cx, cy = CANDLE
    key = bpy.data.lights.new("CandleKey", "POINT")
    key.color = (1.0, 0.62, 0.30)
    key.energy = 70.0
    key.shadow_soft_size = 0.06
    ko = bpy.data.objects.new("CandleKey", key)
    ko.location = (cx, cy, DESK_H + 0.42)
    coll.objects.link(ko)
    glow = bpy.data.lights.new("CandleGlow", "POINT")       # the candle's soft spill on the room
    glow.color = (1.0, 0.66, 0.36)
    glow.energy = 45.0
    glow.shadow_soft_size = 0.6
    go = bpy.data.objects.new("CandleGlow", glow)
    go.location = (cx, cy + 0.2, DESK_H + 0.75)
    coll.objects.link(go)
    f = 1
    while f <= frames:                                         # flicker
        k = rng.uniform(0.82, 1.12)
        key.energy = 70.0 * k
        glow.energy = 45.0 * (0.9 + 0.1 * k)
        key.keyframe_insert("energy", frame=f)
        glow.keyframe_insert("energy", frame=f)
        f += rng.randint(2, 5)
    moon = bpy.data.lights.new("Moon", "SUN")
    moon.color = (0.55, 0.68, 1.0)
    moon.energy = 0.45
    moon.angle = math.radians(2.0)
    mo = bpy.data.objects.new("Moon", moon)
    mo.rotation_euler = Vector((0.85, 0.4, -0.38)).normalized().to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(mo)
    fill = bpy.data.lights.new("WindowFill", "AREA")          # cool light falling in through the window
    fill.shape = "RECTANGLE"
    fill.size, fill.size_y = WIN_W, WIN_H
    fill.color = (0.5, 0.64, 1.0)
    fill.energy = 160.0
    fo = bpy.data.objects.new("WindowFill", fill)
    fo.location = (WIN_X, BACK_Y - 0.6, WIN_Z0 + WIN_H / 2)
    fo.rotation_euler = (math.radians(-90), 0, 0)              # pointing +Y into the room
    coll.objects.link(fo)
    room = bpy.data.lights.new("NightFill", "AREA")            # night spill from the open side
    room.size = 6.0
    room.color = (0.5, 0.62, 1.0)
    room.energy = 190.0
    ro = bpy.data.objects.new("NightFill", room)
    ro.location = (1.0, 5.5, 3.0)
    ro.rotation_euler = Vector((-0.1, -1.0, -0.35)).normalized().to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(ro)
    return ko, go


# ------------------------------------------------------------------- room
def build_room(coll, rng):
    mb = kit.MB(bevel=0.012)
    # floor boards along X, alternating tones
    y = BACK_Y
    k = 0
    while y < 5.0:
        w = rng.uniform(0.24, 0.32)
        x = LEFT_X
        while x < RIGHT_X:
            L = rng.uniform(1.6, 3.2)
            L = min(L, RIGHT_X - x)
            mb.box(T(x + L / 2, y + w / 2, -0.04) @ S(L - 0.02, w - 0.02, 0.08),
                   ("plank", "crate", "plank")[(k + int(x)) % 3])
            x += L
        y += w
        k += 1
    mb.box(T((LEFT_X + RIGHT_X) / 2, 1.0, -0.12) @ S(RIGHT_X - LEFT_X + 0.5, 8.5, 0.1), "post")
    # back wall with the window opening
    wx0, wx1 = WIN_X - WIN_W / 2, WIN_X + WIN_W / 2
    t = 0.2
    yc = BACK_Y - t / 2
    mb.box(T((LEFT_X + wx0) / 2, yc, CEIL / 2) @ S(wx0 - LEFT_X, t, CEIL), "white")
    mb.box(T((wx1 + RIGHT_X) / 2, yc, CEIL / 2) @ S(RIGHT_X - wx1, t, CEIL), "white")
    mb.box(T(WIN_X, yc, WIN_Z0 / 2) @ S(WIN_W, t, WIN_Z0), "white")
    top = WIN_Z0 + WIN_H
    mb.box(T(WIN_X, yc, (top + CEIL) / 2) @ S(WIN_W, t, CEIL - top), "white")
    # side walls; a dark doorway in the left wall and another at the back left (K26)
    mb.box(T(LEFT_X - t / 2, 0.0, CEIL / 2) @ S(t, 6.4, CEIL), "white")
    mb.box(T(RIGHT_X + t / 2, 0.6, CEIL / 2) @ S(t, 7.6, CEIL), "white")
    for (x, y, rz) in ((RIGHT_X - 0.02, -0.4, -math.pi / 2), (2.75, BACK_Y + 0.02, 0.0)):
        M = T(x, y, 0) @ Rz(rz)
        mb.box(M @ T(0, 0.0, 1.05) @ S(1.05, 0.04, 2.1), "dark")
        mb.box(M @ T(0, 0.03, 2.16) @ S(1.3, 0.1, 0.14), "hull_dark")
        for sx in (-1, 1):
            mb.box(M @ T(sx * 0.6, 0.03, 1.08) @ S(0.12, 0.1, 2.16), "hull_dark")
    mb.box(T(2.75 - 0.18, BACK_Y + 0.08, 1.0) @ Rz(-0.5) @ S(0.9, 0.05, 1.95), "wood_door")   # door ajar
    # skirting board and a dado rail
    for x0, x1 in ((LEFT_X, wx0), (wx1, RIGHT_X)):
        mb.box(T((x0 + x1) / 2, BACK_Y + 0.02, 0.08) @ S(x1 - x0, 0.04, 0.16), "hull_dark")
    mb.box(T(RIGHT_X - 0.02, 0.6, 0.08) @ S(0.04, 7.6, 0.16), "hull_dark")
    # ceiling boards, beams, wall plates, posts and knee braces (dark timber frame of K26)
    mb.box(T((LEFT_X + RIGHT_X) / 2, 0.8, CEIL + 0.06) @ S(RIGHT_X - LEFT_X + 0.6, 8.0, 0.12), "hull_dark")
    mb.box(T((LEFT_X + RIGHT_X) / 2, BACK_Y + 0.12, CEIL - 0.13) @ S(RIGHT_X - LEFT_X, 0.24, 0.26), "hull_dark")
    for x in (-3.3, -1.2, 1.2, 3.1):
        mb.box(T(x, 0.6, CEIL - 0.14) @ S(0.24, 7.6, 0.28), "hull_dark")
    for y in (-1.2, 1.6, 4.0):
        mb.box(T((LEFT_X + RIGHT_X) / 2, y, CEIL - 0.34) @ S(RIGHT_X - LEFT_X, 0.26, 0.3), "hull_dark")
    for x in (-1.32, 1.2):
        mb.box(T(x, BACK_Y + 0.14, CEIL / 2) @ S(0.26, 0.26, CEIL), "hull_dark")
        for sx in (-1, 1):
            mb.box(T(x + sx * 0.42, BACK_Y + 0.14, CEIL - 0.55) @ Ry(sx * math.radians(45)) @ S(0.16, 0.16, 1.15),
                   "hull_dark")
    for y in (-1.2, 1.6):                                      # posts on the side walls
        for x, sgn in ((LEFT_X + 0.14, 1), (RIGHT_X - 0.14, -1)):
            mb.box(T(x, y, CEIL / 2) @ S(0.24, 0.24, CEIL), "hull_dark")
            for sy in (-1, 1):
                mb.box(T(x, y + sy * 0.42, CEIL - 0.55) @ Rx(-sy * math.radians(45)) @ S(0.15, 0.15, 1.15),
                       "hull_dark")
    return mb.obj("StudyRoom", coll)


def build_window(coll, frames):
    """Orange casement frame with mullions; the screen-left leaf stands open into the room (K26)."""
    mb = kit.MB(bevel=0.012)
    y = BACK_Y
    x0, x1 = WIN_X - WIN_W / 2, WIN_X + WIN_W / 2
    z0, z1 = WIN_Z0, WIN_Z0 + WIN_H
    fw = 0.13
    mb.box(T(WIN_X, y + 0.02, z0 - fw / 2) @ S(WIN_W + 2 * fw, 0.34, fw), "fort")
    mb.box(T(WIN_X, y + 0.0, z1 + fw / 2) @ S(WIN_W + 2 * fw, 0.3, fw), "fort")
    for x in (x0 - fw / 2, x1 + fw / 2):
        mb.box(T(x, y, (z0 + z1) / 2) @ S(fw, 0.3, WIN_H + 2 * fw), "fort")
    mb.box(T(WIN_X, y + 0.1, z0 - fw - 0.04) @ S(WIN_W + 0.5, 0.2, 0.06), "fort_dk")       # sill
    mb.obj("WindowFrame", coll)
    # open leaf, hinged at the +X (screen-left) jamb, swung ~100 degrees into the room
    leaf = kit.MB(bevel=0.01)
    lw = WIN_W / 2
    bars = 0.06
    leaf.box(T(lw / 2, 0, 0.0) @ S(lw, 0.05, bars), "fort")
    leaf.box(T(lw / 2, 0, WIN_H) @ S(lw, 0.05, bars), "fort")
    for x in (0.0, lw):
        leaf.box(T(x, 0, WIN_H / 2) @ S(bars, 0.05, WIN_H), "fort")
    leaf.box(T(lw / 2, 0, WIN_H / 2) @ S(0.04, 0.04, WIN_H), "fort")
    for k in (1, 2):
        leaf.box(T(lw / 2, 0, WIN_H * k / 3) @ S(lw, 0.04, 0.04), "fort")
    lo = leaf.obj("WindowLeaf", coll)
    lo.location = (x1 - 0.03, y + 0.05, z0)
    lo.rotation_euler = (0, 0, math.radians(80))
    lo.keyframe_insert("rotation_euler", frame=1)                # a breath of night wind moves it
    lo.rotation_euler = (0, 0, math.radians(76))
    lo.keyframe_insert("rotation_euler", frame=frames // 2)
    lo.rotation_euler = (0, 0, math.radians(79))
    lo.keyframe_insert("rotation_euler", frame=frames)
    # the other leaf open outward against the outer wall
    lr = kit.MB(bevel=0.01)
    lr.box(T(-lw / 2, 0, WIN_H / 2) @ S(lw, 0.05, WIN_H), "fort_dk")
    ro = lr.obj("WindowLeafOut", coll)
    ro.location = (x0, y - 0.25, z0)                         # folded flat against the outer wall
    ro.rotation_euler = (0, 0, 0.0)


def build_bookcase(coll, rng, x=-0.15, w=1.6, h=2.35, d=0.42):
    mb = kit.MB(bevel=0.01)
    y = BACK_Y + d / 2 + 0.02
    mb.box(T(x, y - d / 2 + 0.02, h / 2) @ S(w, 0.04, h), "hull_dark")                   # back
    for sx in (-1, 1):
        mb.box(T(x + sx * (w / 2 - 0.03), y, h / 2) @ S(0.06, d, h), "wood_door")
    mb.box(T(x, y, h + 0.04) @ S(w + 0.12, d + 0.06, 0.08), "wood_door")
    mb.box(T(x, y, 0.06) @ S(w, d, 0.12), "wood_door")
    shelves = [0.12, 0.62, 1.1, 1.58, 2.02]
    for z in shelves[1:]:
        mb.box(T(x, y, z) @ S(w - 0.06, d, 0.04), "wood_door")
    colours = ["red", "coat_blue", "leaf", "gold", "cloth_r", "hull_dark", "flag_b", "frond_dk", "cloth_t",
               "parchment", "red", "coat_blue", "leaf_dk"]
    for i in range(len(shelves) - 1):
        z = shelves[i] + 0.02
        top = shelves[i + 1] - 0.03
        cx = x - w / 2 + 0.08
        end = x + w / 2 - 0.08
        while cx < end - 0.05:
            r = rng.random()
            if r < 0.07:                                       # a gap
                cx += rng.uniform(0.08, 0.2)
                continue
            if r < 0.14 and end - cx > 0.35:                   # a flat stack
                n = rng.randint(2, 4)
                bw = rng.uniform(0.24, 0.3)
                for k in range(n):
                    mb.box(T(cx + bw / 2, y + 0.02, z + 0.035 + k * 0.07) @ Rz(rng.uniform(-0.1, 0.1))
                           @ S(bw, d * 0.7, 0.065), rng.choice(colours))
                cx += bw + 0.03
                continue
            bt = rng.uniform(0.045, 0.095)
            bh = rng.uniform(0.28, min(0.44, top - z))
            lean = rng.uniform(-0.12, 0.12) if rng.random() < 0.15 else 0.0
            mb.box(T(cx + bt / 2, y + 0.03, z + bh / 2) @ Ry(lean) @ S(bt, d * rng.uniform(0.6, 0.78), bh),
                   rng.choice(colours))
            cx += bt + rng.uniform(0.004, 0.015)
    return mb.obj("Bookcase", coll)


def build_desk(coll, rng):
    x, y = DESK
    w, d, h = 2.1, 1.0, DESK_H
    mb = kit.MB(bevel=0.014)
    mb.box(T(x, y, h - 0.03) @ S(w + 0.1, d + 0.1, 0.06), "wood_tbl")
    mb.box(T(x, y, h - 0.09) @ S(w, d, 0.06), "wood_door")
    for sx in (-1, 1):                                          # two pedestals with panelled fronts
        px = x + sx * (w / 2 - 0.3)
        mb.box(T(px, y, (h - 0.12) / 2) @ S(0.58, d - 0.04, h - 0.12), "wood_door")
        for k in range(3):
            zc = 0.14 + k * 0.21
            mb.box(T(px, y + d / 2 - 0.0, zc) @ S(0.48, 0.03, 0.17), "hull_dark")
            mb.box(T(px, y + d / 2 + 0.02, zc) @ S(0.08, 0.03, 0.03), "brass")
    mb.box(T(x, y + d / 2 - 0.04, h - 0.2) @ S(w - 1.2, 0.04, 0.16), "hull_dark")     # centre drawer
    mb.box(T(x, y - d / 2 + 0.06, h / 2) @ S(w - 1.2, 0.03, 0.5), "hull_dark")         # modesty panel
    return mb.obj("Desk", coll)


def build_desk_props(coll, rng):
    """Blank papers, an open blank sheet under the quill, a rolled-up map, scrolls, the inkwell,
    the sealed letter, the brass globe and the candle (no writing anywhere)."""
    z = DESK_H
    mb = kit.MB(bevel=0.004)
    # stack of blank paper, front left
    for k in range(7):
        mb.box(T(0.5 + rng.uniform(-0.02, 0.02), 0.27 + rng.uniform(-0.02, 0.02), z + 0.006 + k * 0.012)
               @ Rz(-0.12 + rng.uniform(-0.05, 0.05)) @ S(0.46, 0.34, 0.01), "white")
    # the sheet he writes on
    mb.box(T(0.72, -0.16, z + 0.004) @ Rz(0.08) @ S(0.5, 0.36, 0.006), "parchment")
    # rolled map lying open across the desk, centre-right (K26), with two rolled ends
    mb.box(T(-0.42, -0.18, z + 0.004) @ Rz(-0.15) @ S(0.72, 0.42, 0.006), "parchment")
    for k, (px, py, sx, sy) in enumerate(((-0.3, -0.25, 0.2, 0.1), (-0.55, -0.1, 0.14, 0.12), (-0.36, -0.06, 0.1, 0.07))):
        mb.box(T(px, py, z + 0.009) @ Rz(0.15 + k) @ S(sx, sy, 0.004), ("leaf", "sand", "cloth_t")[k])
    for s in (-1, 1):
        mb.seg((-0.42 + s * 0.36 + 0.03, -0.18 - 0.2, z + 0.03), (-0.42 + s * 0.36 - 0.03, -0.18 + 0.22, z + 0.03),
               0.03, 0.03, "parchment", sides=8)
    # a big scroll lying diagonally in front (K26), with end caps
    a, b = Vector((-0.08, 0.26, z + 0.045)), Vector((-0.62, 0.02, z + 0.045))
    mb.seg(a, b, 0.045, 0.045, "parchment", sides=10)
    for p in (a, b):
        mb.seg(p - (b - a).normalized() * 0.01, p + (b - a).normalized() * 0.005, 0.03, 0.03, "cloth_t", sides=8)
    mb.box(T(0.08, 0.36, z + 0.004) @ Rz(-0.4) @ S(0.3, 0.18, 0.006), "parchment")         # loose sheet
    # inkwell and a spare quill
    mb.box(T(-0.66, -0.3, z + 0.05) @ S(0.11, 0.11, 0.1), "coat_dark")
    mb.cone(T(-0.66, -0.3, z + 0.11), "coat_dark", segments=8, r1=0.05, r2=0.035, depth=0.03)
    mb.seg((-0.66, -0.3, z + 0.1), (-0.6, -0.36, z + 0.36), 0.006, 0.004, "white", sides=4)
    mb.box(T(-0.62, -0.335, z + 0.27) @ Rx(0.25) @ Ry(0.25) @ S(0.012, 0.035, 0.16), "white")
    # sealed letter with red wax, front right
    mb.box(T(-0.62, 0.3, z + 0.005) @ Rz(0.2) @ S(0.3, 0.19, 0.008), "white")
    mb.cone(T(-0.62, 0.3, z + 0.012), "red", segments=8, r1=0.035, r2=0.035, depth=0.012)
    # a small brass ring weight (K26) by the candle
    mb.cone(T(-0.2, 0.32, z + 0.05) @ Rx(math.pi / 2) @ Rz(-0.4), "brass", segments=8, r1=0.05, r2=0.05, depth=0.02)
    # globe on a turned stand at the right end of the desk
    gx, gy = -0.9, -0.28
    mb.cone(T(gx, gy, z + 0.02), "brass", segments=10, r1=0.12, r2=0.1, depth=0.04)
    mb.seg((gx, gy, z + 0.04), (gx, gy, z + 0.2), 0.025, 0.02, "brass", sides=8)
    mb.ico(T(gx, gy, z + 0.38) @ Ry(0.4), "gold", r=0.17, sub=2)
    for k in range(14):                                         # meridian half-ring
        a0, a1 = math.pi * k / 14 - math.pi / 2, math.pi * (k + 1) / 14 - math.pi / 2
        r = 0.205
        p0 = Vector((gx + r * math.cos(a0) * 0.15, gy + r * math.cos(a0), z + 0.38 + r * math.sin(a0)))
        p1 = Vector((gx + r * math.cos(a1) * 0.15, gy + r * math.cos(a1), z + 0.38 + r * math.sin(a1)))
        mb.seg(p0, p1, 0.012, 0.012, "brass", sides=4)
    mb.seg((gx, gy - 0.205, z + 0.38 - 0.01), (gx, gy - 0.205, z + 0.2), 0.012, 0.012, "brass", sides=4)
    # candlestick: brass saucer with a ring handle, socket and the candle
    cx, cy = CANDLE
    mb.cone(T(cx, cy, z + 0.015), "brass", segments=10, r1=0.11, r2=0.12, depth=0.03)
    mb.cone(T(cx - 0.13, cy, z + 0.035) @ Rx(math.pi / 2), "brass", segments=8, r1=0.035, r2=0.035, depth=0.012)
    mb.seg((cx, cy, z + 0.03), (cx, cy, z + 0.12), 0.03, 0.028, "brass", sides=8)
    mb.cone(T(cx, cy, z + 0.13), "brass", segments=8, r1=0.045, r2=0.05, depth=0.02)
    mb.seg((cx, cy, z + 0.13), (cx, cy, z + 0.32), 0.024, 0.024, "white", sides=8)
    mb.ico(T(cx - 0.02, cy, z + 0.25) @ S(0.7, 0.7, 1.4), "white", r=0.012, sub=1)        # wax drip
    ob = mb.obj("DeskProps", coll)
    # flame: glowing drop above the wick, flickering
    fl = kit.MB()
    fl.ico(T(0, 0, 0.035) @ S(0.022, 0.022, 0.05), "candle_flame", r=1.0, sub=1)
    kit.mat_emit("candle_flame", (1.0, 0.62, 0.2), strength=9.0)
    flame = fl.obj("CandleFlame", coll)
    flame.location = (cx, cy, z + 0.325)
    return ob, flame


def flicker(flame, frames, rng):
    f = 1
    while f <= frames:
        s = rng.uniform(0.85, 1.15)
        flame.scale = (rng.uniform(0.9, 1.1), rng.uniform(0.9, 1.1), s)
        flame.rotation_euler = (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0)
        flame.keyframe_insert("scale", frame=f)
        flame.keyframe_insert("rotation_euler", frame=f)
        f += rng.randint(2, 4)


def build_clutter(coll, rng):
    """Crates, pepper sacks, a barrel and a chest round the walls; the carpet; the chair."""
    crate = [kit.make_crate(f"LibCrate{i}", coll, size=s) for i, s in enumerate((0.8, 0.65, 0.55))]
    sack = kit.make_sack("LibSack", coll)
    barrel = kit.make_barrel("LibBarrel", coll)
    lib = crate + [sack, barrel]
    spots = [  # (lib index, x, y, z, rot); +X is screen left
        (0, 3.4, -2.3, 0.0, -0.1), (0, 1.75, -2.35, 0.0, 0.05), (1, 3.35, -2.25, 0.8, -0.3),
        (0, 4.05, -1.2, 0.0, -0.2), (2, 4.05, -1.25, 0.8, 0.2),
        (0, 3.9, 2.4, 0.0, -0.35), (1, 3.2, 2.9, 0.0, 0.3), (2, 3.85, 2.4, 0.8, 0.0),
        (0, 2.55, 2.1, 0.0, 0.15), (1, 2.0, 2.7, 0.0, -0.4),
        (0, -3.3, 2.0, 0.0, 0.25), (1, -3.35, 1.1, 0.0, -0.15), (2, -3.3, 2.0, 0.8, -0.5),
        (0, -2.2, 2.2, 0.0, 0.3),
        (4, -3.35, -1.9, 0.0, 0.0), (4, -3.4, -1.15, 0.0, 0.0), (3, -3.2, -0.5, 0.0, -0.6),
        (3, 1.95, -2.4, 0.0, -1.2), (3, 2.2, -2.55, 0.0, -0.2), (3, 3.7, -0.4, 0.0, 0.4),
    ]
    for i, (li, x, y, z, rz) in enumerate(spots):
        kit.instance(lib[li], f"Clutter{i}", coll, (x, y, z), rot_z=rz)
    for ob in lib:
        kit.hide_source(ob)
    rug = kw.make_carpet("Carpet", coll, w=2.8, d=3.6)
    rug.location = (2.25, 0.3, 0.0)
    rug.rotation_euler[2] = -0.05
    chair = kw.make_chair("Chair", coll)
    chair.location = (IMHOFF[0], IMHOFF[1] - 0.05, 0.0)
    # wooden chest under the window, a sea chart rolled in a basket
    mb = kit.MB(bevel=0.012)
    mb.box(T(-1.75, BACK_Y + 0.35, 0.25) @ S(0.9, 0.5, 0.5), "wood_door")
    mb.box(T(-1.75, BACK_Y + 0.35, 0.53) @ S(0.94, 0.54, 0.08), "hull_dark")
    for sx in (-1, 1):
        mb.box(T(-1.75 + sx * 0.3, BACK_Y + 0.61, 0.3) @ S(0.06, 0.02, 0.5), "brass")
    for k in range(4):
        a = k * 1.4
        mb.seg((1.6 + 0.1 * math.cos(a), BACK_Y + 0.4 + 0.1 * math.sin(a), 0.0),
               (1.6 + 0.16 * math.cos(a), BACK_Y + 0.4 + 0.18 * math.sin(a), 0.95), 0.04, 0.04, "parchment", sides=8)
    mb.cone(T(1.6, BACK_Y + 0.4, 0.22), "basket", segments=10, r1=0.2, r2=0.24, depth=0.44)
    mb.obj("Chest", coll)


# ------------------------------------------------------------------- harbour outside
def height(x, y):
    d = y - shore_y(x)                                         # > 0 on land (toward the fort)
    if d < 0:
        return SEA_Z - 1.5
    return SEA_Z + min(1.4, 0.25 + d * 0.12) + 0.15 * math.sin(x * 0.7) * math.sin(y * 0.9)


def make_shore(coll, seed=3):
    rng = random.Random(seed)
    x0, x1, y0, y1, st = -80.0, 40.0, -22.0, -3.0, 1.5
    nx, ny = int((x1 - x0) / st), int((y1 - y0) / st)
    bm = bmesh.new()
    grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = x0 + i * st + (rng.uniform(-0.3, 0.3) * st if 0 < i < nx else 0)
            y = y0 + j * st + (rng.uniform(-0.3, 0.3) * st if 0 < j < ny else 0)
            row.append(bm.verts.new((x, y, height(x, y))))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            c = f.calc_center_median()
            d = c.y - shore_y(c.x)
            f.material_index = 2 if d > 6 + 2 * math.sin(c.x * 0.3) else (1 if d < 1.2 else 0)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("Shore")
    bm.to_mesh(me)
    bm.free()
    for m in ("sand", "sand_wet", "grass"):
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Shore", me)
    coll.objects.link(ob)
    return ob


def build_harbour(coll, rig_c, frames, rng):
    make_shore(coll)
    sea = cw.make_faceted_sea(coll, rig_c, frames, (-220.0, 120.0, -320.0, -6.0),
                              lambda x, y: (shore_y(x) - y) * 0.3, step=2.0, far_step=10.0,
                              detail_box=(-90.0, 20.0, -90.0, -6.0))
    sea.location.z = SEA_Z
    # jetty out from the beach below the fort, a sentry walking it with a lantern post at the end
    jx, jy0, jlen = -11.0, shore_y(-11.0) + 3.0, 30.0
    ja = -0.5                                                 # jetty heading (toward -Y, a little to -X)
    jetty = kit.make_jetty("Jetty", coll, length=jlen, width=2.2, deck=0.9, seed=4)
    jetty.location = (jx, jy0, SEA_Z)
    jetty.rotation_euler[2] = math.pi + ja
    along = Vector((math.sin(ja), -math.cos(ja), 0))
    end = Vector((jx, jy0, 0)) + along * jlen
    lp = kit.MB()
    lp.seg((0, 0, 0), (0, 0, 2.6), 0.08, 0.07, "post", sides=6)
    lp.box(T(0.25, 0, 2.5) @ S(0.5, 0.06, 0.06), "post")
    lp.box(T(0.45, 0, 2.25) @ S(0.22, 0.22, 0.3), "iron")
    lp.obj("LanternPost", coll).location = (end.x - 0.9, end.y + 1.2, SEA_Z + 0.95)
    lan = kit.MB()
    lan.box(S(0.16, 0.16, 0.22), "jetty_lamp")
    kit.mat_emit("jetty_lamp", (1.0, 0.7, 0.32), strength=25.0)
    lan.obj("Lantern", coll).location = (end.x - 0.45, end.y + 1.2, SEA_Z + 0.95 + 2.25)
    ll = bpy.data.lights.new("LanternLight", "POINT")
    ll.color = (1.0, 0.65, 0.3)
    ll.energy = 400.0
    ll.shadow_soft_size = 0.2
    lo = bpy.data.objects.new("LanternLight", ll)
    lo.location = (end.x - 0.45, end.y + 1.2, SEA_Z + 0.95 + 2.0)
    coll.objects.link(lo)
    deck = SEA_Z + 0.94
    g = lambda x, y: deck
    root, parts = kit.make_walker("Sentry", coll, "dutch", seed=3)
    a, b = Vector((jx, jy0, 0)) + along * 6, end
    kit.animate_walk(root, parts, [(a.x, a.y), (b.x + 0.4, b.y + 2.0), (a.x, a.y)], g, 1, frames,
                     stride_frames=16)
    for i, (dx, dy) in enumerate(((0.5, 3.0), (-0.4, 4.2))):
        ob = kit.make_figure(f"JettyHand{i}", coll, "villager", seed=10 + i, cloth="cloth_w")
        ob.location = (end.x + dx, end.y + dy, deck)
        ob.rotation_euler[2] = rng.uniform(0, TAU)
        kit.animate_idle(ob, rng, 1, frames, 0.03)
    # boats at the jetty
    for i, (dx, dy, rz) in enumerate(((2.2, 8.0, 0.2), (-2.4, 12.0, -0.1))):
        p = Vector((jx, jy0, 0)) + along * dy
        bt = kit.make_boat(f"Boat{i}", coll, seed=i)
        bt.location = (p.x + dx, p.y, SEA_Z + 0.05)
        bt.rotation_euler[2] = ja + rz
        bob(bt, frames, rng, amp=0.04)
    # the East Indiaman at anchor beyond the jetty, sails set loosely, rocking
    ship = kit.make_ship("Ship", coll, seed=2)
    ship.scale = (0.62, 0.62, 0.62)
    ship.location = (-36.0, -54.0, SEA_Z - 0.3)
    ship.rotation_euler[2] = math.radians(-119)
    kw.make_sails("ShipSails", ship, coll)
    bob(ship, frames, rng, amp=0.15, roll=0.025)
    # palms and bushes along the beach under the fort
    palms = [kit.make_palm(f"LibPalm{i}", coll, seed=40 + i, height=8.5 + i) for i in range(4)]
    for k, (x, y) in enumerate(((-3.4, -11.0), (1.5, -9.0), (-14.5, -12.0), (-19.0, -10.5), (4.0, -11.0),
                                (-27.0, -12.5), (9.0, -12.0), (-34.0, -11.0), (-11.5, -9.5), (-40.0, -12.5))):
        kit.instance(palms[k % 4], f"Palm{k}", coll, (x, y, height(x, y) - 0.1), rot_z=rng.uniform(0, TAU),
                     scale=rng.uniform(0.85, 1.1))
    bush = [kit.make_bush(f"LibBush{i}", coll, seed=60 + i, size=1.2) for i in range(2)]
    for k in range(18):
        x, y = rng.uniform(-45, 15), rng.uniform(-11, -5)
        kit.instance(bush[k % 2], f"Bush{k}", coll, (x, y, height(x, y)), rot_z=rng.uniform(0, TAU),
                     scale=rng.uniform(0.8, 1.4))
    for ob in palms + bush:
        kit.hide_source(ob)
    # moon low over the sea, and a scatter of stars
    mm = kit.MB()
    mm.ico(T(0, 0, 0), "moon", r=5.0, sub=2)
    kit.mat_emit("moon", (0.92, 0.94, 1.0), strength=6.0)
    mm.obj("MoonDisc", coll).location = (-250.0, -110.0, 110.0)
    st = kit.MB()
    for k in range(160):
        a = rng.uniform(-1.3, 0.2)
        e = rng.uniform(0.12, 0.7)
        r = 300.0
        st.ico(T(-r * math.cos(e) * math.sin(a) - 40, -r * math.cos(e) * math.cos(a), r * math.sin(e)), "star",
               r=rng.uniform(0.25, 0.55), sub=0)
    kit.mat_emit("star", (0.9, 0.92, 1.0), strength=5.0)
    st.obj("Stars", coll)


def bob(ob, frames, rng, amp=0.1, roll=0.02):
    base = ob.location.copy()
    rz = ob.rotation_euler[2]
    ph = rng.uniform(0, TAU)
    f = 1
    while f <= frames + 24:
        t = f / kit.FPS
        ob.location = (base.x, base.y, base.z + amp * math.sin(t * 1.1 + ph))
        ob.rotation_euler = (roll * math.sin(t * 0.9 + ph), roll * 0.6 * math.sin(t * 0.7 + ph + 1), rz)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
        f += 12


# ------------------------------------------------------------------- Imhoff
def build_imhoff(coll):
    root, parts = kit.make_rig("VanImhoff", coll, "imhoff", seated=True)
    root.location = (IMHOFF[0], IMHOFF[1], 0.0)
    # quill in his writing hand: armL, at the figure's +X = screen left when he faces the camera (K26)
    q = kit.MB()
    a, b = Vector((0.0, 0.06, -0.7)), Vector((0.13, 0.33, -0.5))
    q.seg(a, b, 0.006, 0.004, "white", sides=4)
    d = (b - a).normalized()
    q.seg(a.lerp(b, 0.3), b + d * 0.06, 0.035, 0.012, "white", sides=3)
    q.obj("Quill", coll, parent=parts["armL"])
    return root, parts


PEN = "armL"
WRITE_POSE = {"armL": (1.05, -0.22, 0.18), "armR": (0.95, 0.25, -0.25), "body": (0.14, 0, 0), "head": (0.1, 0, -0.25)}
LOOK_UP = {"body": (0.02, 0, 0), "head": (-0.08, 0, -0.12)}
PEN_REST = (0.8, -0.15, 0.1)


def animate_imhoff(parts, frames, beats, rng):
    """Writes in small quick strokes, lifts the pen once to think, then at the last line ('And he
    believes the answer is force') stops, straightens and lifts his head."""
    stop, look = beats["stop"], beats["look"]
    kit.key_pose(parts, 1, WRITE_POSE)
    base = WRITE_POSE[PEN]
    f = 4
    dip = beats.get("dip")
    while f < stop:
        if dip and dip <= f < dip + 30:                        # pen lifted a moment
            kit.key_pose(parts, dip, {PEN: base})
            kit.key_pose(parts, dip + 10, {PEN: (0.78, -0.12, 0.05)})
            kit.key_pose(parts, dip + 24, {PEN: base})
            f = dip + 30
            continue
        kit.key_pose(parts, f, {PEN: (base[0] + rng.uniform(-0.04, 0.04), base[1] + rng.uniform(-0.05, 0.05),
                                      base[2] + rng.uniform(-0.1, 0.1))})
        f += rng.randint(4, 7)
    kit.key_pose(parts, stop, {PEN: base})
    # his head follows the pen a little while he writes
    f = 1
    while f < stop:
        kit.key_pose(parts, f, {"head": (0.1 + rng.uniform(-0.04, 0.04), 0, -0.25 + rng.uniform(-0.08, 0.08))})
        f += rng.randint(30, 50)
    kit.key_pose(parts, stop, {"head": WRITE_POSE["head"], "body": WRITE_POSE["body"]})
    kit.key_pose(parts, look, {**LOOK_UP, PEN: PEN_REST})
    kit.key_pose(parts, frames, {"head": (-0.06, 0, -0.1), "body": (0.0, 0, 0), PEN: PEN_REST})


# ------------------------------------------------------------------- assembly
def build_world(frames, beats):
    """beats: {'stop', 'look', 'dip'} frame numbers for Imhoff's action."""
    rng = random.Random(20)
    kw.register_palette()
    kit.mat("basket", kw.PALETTE["basket"])
    rig_c = kit.new_collection("Rig")
    room_c = kit.new_collection("Room")
    props_c = kit.new_collection("Props")
    out_c = kit.new_collection("Harbour")
    cast_c = kit.new_collection("Cast")
    setup_night_world()
    add_lights(rig_c, frames)
    build_room(room_c, rng)
    build_window(room_c, frames)
    build_bookcase(props_c, rng)
    build_desk(props_c, rng)
    _, flame = build_desk_props(props_c, rng)
    flicker(flame, frames, rng)
    build_clutter(props_c, rng)
    build_harbour(out_c, rig_c, frames, rng)
    root, parts = build_imhoff(cast_c)
    animate_imhoff(parts, frames, beats, rng)
    return {"imhoff": root, "parts": parts, "rig": rig_c}
