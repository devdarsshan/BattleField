"""The Varkala Cliff Halt & Nair Shield Wall (Beat S27, Clip 34).

Matches Flow reference:
- frames/flow_refs/K34.jpeg (S27: Sheer red laterite cliffs, turquoise sea, coconut palms,
  massive Nair warrior shield wall halting the advancing Dutch and allied column).
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S

VARKALA_PALETTE = {
    "laterite_rd":  (0.72, 0.32, 0.20),
    "laterite_dk":  (0.52, 0.22, 0.14),
    "sand":         (0.88, 0.80, 0.62),
    "sand_wet":     (0.74, 0.66, 0.50),
    "sea_turq":     (0.20, 0.56, 0.64),
    "sea_deep":     (0.12, 0.38, 0.52),
    "sea_foam":     (0.92, 0.96, 0.96),
    "dirt_track":   (0.68, 0.52, 0.36),
    "grass_coast":  (0.42, 0.58, 0.24),
    "turban_turq":  (0.15, 0.68, 0.72),
    "turban_saffron":(0.96, 0.58, 0.12),
    "turban_green": (0.22, 0.62, 0.28),
    "turban_orange":(0.92, 0.42, 0.10),
}


def register_palette():
    for name, rgb in VARKALA_PALETTE.items():
        kit.PALETTE[name] = rgb
        kit.mat(name, rgb)


def vmat(name):
    if name in VARKALA_PALETTE:
        return kit.mat(name, VARKALA_PALETTE[name])
    return kit.mat(name, kit.PALETTE[name])


def setup_sky():
    w = bpy.data.worlds.new("VarkalaSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        # Soft luminous coastal sky
        bg.inputs["Color"].default_value = (0.84, 0.90, 0.96, 1.0)
        bg.inputs["Strength"].default_value = 1.0


def build_varkala_terrain(coll, rng):
    """Faceted sea, sandy beach, red laterite cliffs, cliff-top road, and inland ridge."""
    mb = kit.MB(bevel=0.0)

    # 1. Faceted Turquoise Sea (left side: X from -55 to -10, Y from -40 to +40)
    sea_steps_x = 10
    sea_steps_y = 16
    sx_min, sx_max = -55.0, -10.0
    sy_min, sy_max = -40.0, 40.0
    dx = (sx_max - sx_min) / sea_steps_x
    dy = (sy_max - sy_min) / sea_steps_y

    for ix in range(sea_steps_x):
        for iy in range(sea_steps_y):
            x0 = sx_min + ix * dx
            x1 = x0 + dx
            y0 = sy_min + iy * dy
            y1 = y0 + dy
            # Subtle wave heights
            z00 = math.sin(x0 * 0.4 + y0 * 0.3) * 0.18 - 0.05
            z10 = math.sin(x1 * 0.4 + y0 * 0.3) * 0.18 - 0.05
            z11 = math.sin(x1 * 0.4 + y1 * 0.3) * 0.18 - 0.05
            z01 = math.sin(x0 * 0.4 + y1 * 0.3) * 0.18 - 0.05
            v0 = mb.bm.verts.new((x0, y0, z00))
            v1 = mb.bm.verts.new((x1, y0, z10))
            v2 = mb.bm.verts.new((x1, y1, z11))
            v3 = mb.bm.verts.new((x0, y1, z01))
            col_name = "sea_turq" if ix > 4 else "sea_deep"
            mb.face((v0, v1, v2, v3), col_name)

    # 2. Sandy Beach & Shoreline (X = -10 to -5)
    for iy in range(sea_steps_y):
        y0 = sy_min + iy * dy
        y1 = y0 + dy
        # Wet sand strip
        v0 = mb.bm.verts.new((-10.0, y0, 0.05))
        v1 = mb.bm.verts.new((-8.2, y0, 0.4))
        v2 = mb.bm.verts.new((-8.2, y1, 0.4))
        v3 = mb.bm.verts.new((-10.0, y1, 0.05))
        mb.face((v0, v1, v2, v3), "sand_wet")
        # Dry sand strip
        v4 = mb.bm.verts.new((-8.2, y0, 0.4))
        v5 = mb.bm.verts.new((-5.5, y0, 1.2))
        v6 = mb.bm.verts.new((-5.5, y1, 1.2))
        v7 = mb.bm.verts.new((-8.2, y1, 0.4))
        mb.face((v4, v5, v6, v7), "sand")

    # 3. Towering Sheer Red Laterite Cliffs (X = -5.5 to 0.0, rising to Z = 11.5)
    cliff_segments = 24
    cy_step = (sy_max - sy_min) / cliff_segments
    for ci in range(cliff_segments):
        y0 = sy_min + ci * cy_step
        y1 = y0 + cy_step
        # Mid cliff ledge with faceted irregularity
        jx0 = rng.uniform(-0.4, 0.4)
        jx1 = rng.uniform(-0.4, 0.4)
        jz0 = rng.uniform(-0.3, 0.3)
        jz1 = rng.uniform(-0.3, 0.3)

        # Lower cliff wall
        v0 = mb.bm.verts.new((-5.5, y0, 1.2))
        v1 = mb.bm.verts.new((-3.2 + jx0, y0, 6.2 + jz0))
        v2 = mb.bm.verts.new((-3.2 + jx1, y1, 6.2 + jz1))
        v3 = mb.bm.verts.new((-5.5, y1, 1.2))
        mb.face((v0, v1, v2, v3), "laterite_dk")

        # Upper cliff wall
        top_x0 = rng.uniform(-0.3, 0.3)
        top_x1 = rng.uniform(-0.3, 0.3)
        v4 = mb.bm.verts.new((-3.2 + jx0, y0, 6.2 + jz0))
        v5 = mb.bm.verts.new((0.0 + top_x0, y0, 11.5))
        v6 = mb.bm.verts.new((0.0 + top_x1, y1, 11.5))
        v7 = mb.bm.verts.new((-3.2 + jx1, y1, 6.2 + jz1))
        mb.face((v4, v5, v6, v7), "laterite_rd")

    # 4. Coastal Plateau & Clifftop Road (X = 0.0 to 9.0, Z = 11.5)
    # Coastal grass buffer (X = 0.0 to 1.0)
    mb.box(T(0.5, 0.0, 11.45) @ S(1.2, 82.0, 0.2), "grass_coast")
    # Central dirt road (X = 1.0 to 6.5, width 5.5m)
    mb.box(T(3.75, 0.0, 11.48) @ S(5.5, 82.0, 0.2), "dirt_track")
    # Inland grass buffer (X = 6.5 to 9.0)
    mb.box(T(7.75, 0.0, 11.45) @ S(2.5, 82.0, 0.2), "grass_coast")

    # 5. Inland Laterite Hillside & Upper Ridge (X = 9.0 to 26.0, rising to Z = 20.0)
    for ci in range(cliff_segments):
        y0 = sy_min + ci * cy_step
        y1 = y0 + cy_step
        v0 = mb.bm.verts.new((9.0, y0, 11.5))
        v1 = mb.bm.verts.new((15.5, y0, 17.5))
        v2 = mb.bm.verts.new((15.5, y1, 17.5))
        v3 = mb.bm.verts.new((9.0, y1, 11.5))
        mb.face((v0, v1, v2, v3), "laterite_rd")

        v4 = mb.bm.verts.new((15.5, y0, 17.5))
        v5 = mb.bm.verts.new((26.0, y0, 20.5))
        v6 = mb.bm.verts.new((26.0, y1, 20.5))
        v7 = mb.bm.verts.new((15.5, y1, 17.5))
        mb.face((v4, v5, v6, v7), "grass_coast")

    # 6. Beach Boulders (red laterite rocks at base of cliff)
    boulder_spots = [
        (-6.2, -18.0, 1.2), (-7.0, -12.0, 1.0), (-6.5, -4.0, 1.3),
        (-6.8, 6.0, 1.1), (-7.2, 14.0, 0.9), (-6.0, 22.0, 1.4),
        (-8.5, -2.0, 0.5), (-8.0, 10.0, 0.6), (-7.5, -24.0, 0.8),
    ]
    for bx, by, bz in boulder_spots:
        br = rng.uniform(0.7, 1.4)
        mb.ico(T(bx, by, bz), "laterite_rd", r=br, sub=1, jitter=0.25, rng=rng)

    terr_ob = mb.obj("VarkalaTerrain", coll)
    for m_name in ("sea_turq", "sea_deep", "sand_wet", "sand", "laterite_dk", "laterite_rd", "grass_coast", "dirt_track"):
        terr_ob.data.materials.append(vmat(m_name))

    # 7. Dense Coconut Palm Groves (clifftop edge and inland ridge)
    palm_c = kit.new_collection("VarkalaPalms")
    # Palms lining the cliff edge (X = -1.2 to -0.4, strictly keeping to outer cliff brink)
    for i in range(12):
        py = -30.0 + i * 5.5 + rng.uniform(-0.5, 0.5)
        # Keep clear of immediate camera foreground
        if -22.0 < py < -10.0:
            continue
        px = rng.uniform(-1.2, -0.4)
        p = kit.make_palm(f"CliffPalm_{i}", palm_c, seed=100 + i, height=rng.uniform(7.0, 9.0))
        p.location = (px, py, 11.5)
        p.rotation_euler = (rng.uniform(-0.04, 0.04), rng.uniform(-0.20, -0.10), rng.uniform(0, 6.28))

    # Palms on the inland ridge (X = 14.5 to 26.0, well back on the upper hillside)
    for i in range(22):
        py = -34.0 + (i % 11) * 6.5 + rng.uniform(-0.8, 0.8)
        px = 16.0 + (i // 11) * 5.0 + rng.uniform(-0.5, 1.5)
        pz = 17.5 if px < 19.0 else 20.5
        p = kit.make_palm(f"InlandPalm_{i}", palm_c, seed=200 + i, height=rng.uniform(8.5, 11.0))
        p.location = (px, py, pz)
        p.rotation_euler = (rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), rng.uniform(0, 6.28))


def build_nair_shield_wall(coll):
    """Travancore Nair phalanx blocking the clifftop road (K34).
    
    Dense formation: 8 columns wide x 12 ranks deep = 96 warriors!
    Positioned at Y = 5.0 to 17.0, X = 1.0 to 6.2, Z = 11.5.
    Facing south (-Y) towards the advancing allied column.
    """
    nair_c = kit.new_collection("NairShieldWall")
    rng = random.Random(88)

    warriors = []
    for rank in range(12):
        for col in range(8):
            nx = 1.2 + col * 0.68 + rng.uniform(-0.04, 0.04)
            ny = 5.2 + rank * 0.95 + rng.uniform(-0.05, 0.05)
            # Front ranks hold shields forward and swords ready
            w = kit.make_figure(f"NairWall_{rank}_{col}", nair_c, "nair", seed=500 + rank * 8 + col)
            w.location = (nx, ny, 11.5)
            w.rotation_euler = (0, 0, 0.0)  # Facing south (-Y)
            warriors.append(w)

    return warriors


def build_allied_column(coll):
    """The allied invasion column halted on the clifftop road (K34).
    
    Includes:
    - Dutch VOC regular infantry in blue coats, tricorns, and muskets.
    - Indian allied infantry in white tunics with vivid colorful turbans.
    - Orange VOC war banner.
    Positioned from Y = -18.0 to -1.0, X = 1.0 to 6.5, Z = 11.5.
    Facing north (+Y) towards the Nair shield wall.
    """
    allied_c = kit.new_collection("AlliedAdvanceColumn")
    rng = random.Random(99)

    figures = []
    # 1. Front Allied Vanguard: Dutch & Indian soldiers intermixed (K34)
    # 6 columns wide x 8 ranks deep
    turban_colors = ["turban_turq", "turban_saffron", "turban_green", "turban_orange"]
    for rank in range(8):
        for col in range(6):
            ax = 1.4 + col * 0.85 + rng.uniform(-0.06, 0.06)
            ay = -16.0 + rank * 1.8 + rng.uniform(-0.08, 0.08)

            is_dutch = (rank + col) % 2 == 0
            if is_dutch:
                fig = kit.make_figure(f"AlliedDutch_{rank}_{col}", allied_c, "dutch",
                                      seed=700 + rank * 6 + col, armed=True)
            else:
                cloth_choice = turban_colors[(rank * 3 + col) % len(turban_colors)]
                fig = kit.make_figure(f"AlliedIndian_{rank}_{col}", allied_c, "nair",
                                      seed=800 + rank * 6 + col, cloth=cloth_choice)
            fig.location = (ax, ay, 11.5)
            fig.rotation_euler = (0, 0, math.pi)  # Facing north (+Y)
            figures.append(fig)

    # 2. Orange VOC War Banner carried by Dutch officer on the right flank
    b_mb = kit.MB(bevel=0.03)
    b_mb.cone(T(6.2, -9.0, 13.8), "post", segments=6, r1=0.05, r2=0.035, depth=4.6)
    b_mb.box(T(7.1, -9.0, 15.2) @ Ry(-0.08) @ S(1.8, 0.05, 1.2), "voc_orange")
    banner_ob = b_mb.obj("AlliedClifftopBanner", allied_c)
    banner_ob.data.materials.append(kit.mat("post", kit.PALETTE["post"]))
    banner_ob.data.materials.append(kit.mat("voc_orange", (0.96, 0.42, 0.08)))

    return {"figures": figures, "banner": banner_ob}


def build_world(end_frame=460):
    register_palette()
    setup_sky()
    coll = bpy.data.collections.new("VarkalaWorld")
    bpy.context.scene.collection.children.link(coll)
    rng = random.Random(44)

    build_varkala_terrain(coll, rng)
    nairs = build_nair_shield_wall(coll)
    allies = build_allied_column(coll)

    # Coastal Sunlight (coming from west over the sea, low afternoon angle)
    sun_data = bpy.data.lights.new(name="VarkalaSun", type="SUN")
    sun_data.color = (1.0, 0.94, 0.86)
    sun_data.energy = 4.5
    sun_ob = bpy.data.objects.new("VarkalaSun", sun_data)
    sun_ob.location = (-40.0, -10.0, 25.0)
    # Angled from west (-X) towards east (+X) and slightly south
    sun_ob.rotation_euler = (math.radians(35), math.radians(-32), math.radians(-50))
    coll.objects.link(sun_ob)

    # Ambient Sky Fill
    fill_data = bpy.data.lights.new(name="SkyFill", type="SUN")
    fill_data.color = (0.76, 0.86, 0.96)
    fill_data.energy = 1.4
    fill_ob = bpy.data.objects.new("SkyFill", fill_data)
    fill_ob.location = (20.0, 20.0, 30.0)
    fill_ob.rotation_euler = (math.radians(-45), math.radians(15), math.radians(135))
    coll.objects.link(fill_ob)

    return {"collection": coll, "nairs": nairs, "allies": allies}
