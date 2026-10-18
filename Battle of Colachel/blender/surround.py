"""Surroundings for the stand-alone scenes (S60 chapel, S62 treaty tent, S64 temple), so each sits in a real place
and not on a floating tile in a void: a faceted terrain that is flat round the scene and rolls up into low hills, a
huge far plane to the horizon, rings of distant low-poly hills, scattered palms / trees / bushes / rocks, and a sky
gradient that meets the horizon colour (no empty background).

  terrain(coll, mat_top, flat_r, amp, seed)         faceted ground, flat inside flat_r
  far_ground(coll, rgb)                              the plane out to the horizon
  far_hills(coll, rgb, n, r0, r1)                    ring of faceted hills
  scatter(coll, lib, rng, n, r0, r1, kinds, avoid)   palms, trees, bushes, rocks
  sky(horizon, mid, top, strength)                   world gradient
"""
import math
import random

import bpy
import bmesh
from mathutils import Vector, noise

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


def height_fn(flat_r, amp, seed, center=(0.0, 0.0)):
    cx, cy = center

    def h(x, y):
        d = math.hypot(x - cx, y - cy)
        k = max(0.0, min(1.0, (d - flat_r) / 70.0))
        k = k * k * (3 - 2 * k)
        return k * amp * (0.55 + 0.9 * _n(x, y, 38.0, seed)) + 0.35 * k * _n(x, y, 9.0, seed + 3)
    return h


def terrain(coll, mat_top, flat_r=14.0, amp=14.0, seed=1, size=260.0, cell=5.0, center=(0.0, 0.0), alt_mat=None):
    """Faceted ground: flat (z = 0) round the scene, rolling up to hills beyond. Returns (object, height function)."""
    rng = random.Random(seed)
    h = height_fn(flat_r, amp, seed, center)
    mb = kit.MB()
    n = int(size / cell)
    half = size / 2
    grid = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            x = center[0] - half + i * cell
            y = center[1] - half + j * cell
            if 0 < i < n and 0 < j < n:
                x += rng.uniform(-0.3, 0.3) * cell
                y += rng.uniform(-0.3, 0.3) * cell
            row.append(mb.bm.verts.new((x, y, h(x, y) - 0.02)))
        grid.append(row)
    for j in range(n):
        for i in range(n):
            m = mat_top
            if alt_mat and rng.random() < 0.18:
                m = alt_mat
            a, b, c2, d = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]
            mb.face([a, b, c2], m)
            mb.face([a, c2, d], m)
    return mb.obj("SurroundTerrain", coll), h


def far_ground(coll, rgb, z=-1.5, R=60000.0):
    me = bpy.data.meshes.new("FarGround")
    me.from_pydata([(-R, -R, z), (R, -R, z), (R, R, z), (-R, R, z)], [], [(0, 1, 2, 3)])
    m = bpy.data.materials.new("FarGroundMat")
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
    b.inputs["Roughness"].default_value = 0.9
    me.materials.append(m)
    ob = bpy.data.objects.new("FarGround", me)
    coll.objects.link(ob)
    ob.visible_shadow = False
    return ob


def far_hills(coll, rgb, n=46, r0=260.0, r1=900.0, seed=5, hmin=40.0, hmax=170.0, skip=None):
    """A ring of big faceted low-poly hills on the horizon."""
    rng = random.Random(seed)
    kit.PALETTE["far_hill"] = rgb
    kit.mat("far_hill", rgb)
    mb = kit.MB()
    for k in range(n):
        a = k * math.tau / n + rng.uniform(-0.05, 0.05)
        if skip and skip(a):
            continue
        r = rng.uniform(r0, r1)
        x, y = math.cos(a) * r, math.sin(a) * r
        hgt = rng.uniform(hmin, hmax)
        w = rng.uniform(90, 230)
        mb.cone(T(x, y, hgt / 2 - 8) @ Rz(rng.uniform(0, 3)), "far_hill", segments=rng.choice((7, 8, 9)), r1=w * 1.4, r2=w * rng.uniform(0.2, 0.5), depth=hgt)
    ob = mb.obj("FarHills", coll)
    ob.visible_shadow = False
    return ob


def scatter(coll, lib_c, rng, n, r0, r1, avoid=None, height=None, palms=0.45, trees=0.25, bushes=0.2, rocks=0.1, scale=(0.9, 1.4)):
    """Palms, broad trees, bushes and rocks scattered in a ring r0..r1 round the origin. avoid(x, y) -> True to skip."""
    palm_src = [kit.make_palm(f"LibSurPalm{i}", lib_c, seed=300 + i, height=7.5 + 0.7 * i) for i in range(5)]
    tree_src = [kit.make_tree(f"LibSurTree{i}", lib_c, seed=310 + i, height=5.5 + i) for i in range(3)]
    bush_src = [kit.make_bush(f"LibSurBush{i}", lib_c, seed=320 + i, size=0.9 + 0.25 * i) for i in range(3)]
    rock_src = [kit.make_rock(f"LibSurRock{i}", lib_c, seed=330 + i, size=0.7 + 0.5 * i) for i in range(3)]
    for s in palm_src + tree_src + bush_src + rock_src:
        kit.hide_source(s)
    placed = 0
    tries = 0
    while placed < n and tries < n * 8:
        tries += 1
        a = rng.uniform(0, math.tau)
        r = rng.uniform(r0, r1)
        x, y = math.cos(a) * r, math.sin(a) * r
        if avoid and avoid(x, y):
            continue
        z = height(x, y) if height else 0.0
        u = rng.random()
        if u < palms:
            src, nm = palm_src[placed % 5], "SurPalm"
        elif u < palms + trees:
            src, nm = tree_src[placed % 3], "SurTree"
        elif u < palms + trees + bushes:
            src, nm = bush_src[placed % 3], "SurBush"
        else:
            src, nm = rock_src[placed % 3], "SurRock"
        kit.instance(src, f"{nm}{placed}", coll, (x, y, z - 0.1), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(*scale))
        placed += 1
    return placed


def sky(horizon, mid, top, strength=1.0):
    """World gradient from the horizon colour up through mid to top (positions are compressed toward the horizon, as the
    map-range of the scene's own worlds is)."""
    w = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = w
    w.use_nodes = True
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
    cr.elements[0].color = (*kit.srgb_to_linear(horizon), 1)
    e = cr.elements.new(0.08)
    e.color = (*kit.srgb_to_linear(mid), 1)
    cr.elements[-1].position = 0.34
    cr.elements[-1].color = (*kit.srgb_to_linear(top), 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return w
