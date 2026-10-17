"""The Padmanabha temple (S64; clip 77, ref K77): the king lays his sword down at the temple door.

A dark floating island on a navy backdrop: a tiered temple gateway tower (red-brown base with pilasters, a carved
wooden door between two free-standing carved pillars, six receding tan tiers with eaves, niches and a vaulted crown
with gold finials), three steps with rows of clay oil lamps, the king in red kneeling at the door with his sword,
two priests with joined hands, kneeling devotees, spear guards, banana plants, palms, rocks. No text.
Coordinates: metres, island top at z = 0, the tower at the back (+y), the camera looks from -x / -y.
"""
import math
import random

import bpy
from mathutils import Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S
import inland_world as iw
import palace_world as palw
import landing_world as lw
import mini_dio as md

face = lw._face
TOWER = (2.6, 3.4)                       # centre of the tower base
PORCH_Z = 0.55


def register_palette():
    try:
        palw.register_palette()
    except Exception:
        pass
    for k, v in {"t_red": (0.50, 0.19, 0.15), "t_red_lt": (0.62, 0.28, 0.20), "t_tan": (0.80, 0.58, 0.32), "t_tan_dk": (0.58, 0.38, 0.22),
                 "t_tan_lt": (0.90, 0.70, 0.42), "t_grey": (0.50, 0.47, 0.44), "t_grey_lt": (0.62, 0.59, 0.55), "t_door": (0.46, 0.25, 0.11),
                 "t_ground": (0.25, 0.19, 0.15), "t_gold": (0.95, 0.74, 0.22), "t_step": (0.58, 0.54, 0.50)}.items():
        kit.PALETTE.setdefault(k, v)
        kit.mat(k, kit.PALETTE[k])


def make_tower(c):
    mb = kit.MB(bevel=0.03)
    W, D = 6.8, 3.8
    mb.box(T(0, 0, 0.25) @ S(W + 1.0, D + 1.0, 0.5), "t_grey")
    zb = 0.5
    mb.box(T(0, 0, zb + 1.7) @ S(W, D, 3.4), "t_red")
    fy = -D / 2
    for k in range(7):                                   # pilasters across the front
        x = -W / 2 + 0.3 + k * (W - 0.6) / 6
        mb.box(T(x, fy - 0.07, zb + 1.7) @ S(0.3, 0.16, 3.4), "t_red_lt")
        mb.box(T(x, fy - 0.1, zb + 3.3) @ S(0.42, 0.2, 0.18), "t_tan_dk")
    for zq in (0.55, 1.0, 2.55, 2.95):                                  # carved bands between the pilasters
        mb.box(T(0, fy - 0.09, zb + zq) @ S(W - 0.2, 0.1, 0.12), "t_tan_dk")
    for k in range(6):
        x = -W / 2 + 0.95 + k * (W - 1.9) / 5
        mb.box(T(x, fy - 0.08, zb + 1.9) @ S(0.55, 0.06, 1.0), "t_red_lt")
    mb.box(T(0, fy - 0.03, zb + 3.4) @ S(W + 0.3, 0.3, 0.2), "t_tan_dk")                   # cornice
    # the door: dark recess, two plank leaves with studs, a lintel
    mb.box(T(0, fy - 0.02, zb + 1.35) @ S(1.9, 0.1, 2.7), "dark")
    for sx in (-1, 1):
        mb.box(T(sx * 0.46, fy - 0.1, zb + 1.3) @ S(0.82, 0.1, 2.5), "t_door")
        for r in range(4):
            for q in range(2):
                mb.box(T(sx * (0.2 + 0.4 * q), fy - 0.17, zb + 0.4 + r * 0.6) @ S(0.1, 0.06, 0.1), "brass")
    mb.box(T(0, fy - 0.12, zb + 2.78) @ S(2.3, 0.3, 0.28), "t_grey_lt")
    mb.box(T(0, fy - 0.12, zb + 3.02) @ S(1.5, 0.26, 0.24), "t_tan_dk")
    # two free-standing carved pillars at the porch front, a lamp shelf and a porch roof slab
    for sx in (-1, 1):
        px = sx * 1.75
        mb.box(T(px, fy - 1.1, zb + 0.15) @ S(0.95, 0.95, 0.3), "t_grey_lt")
        mb.box(T(px, fy - 1.1, zb + 1.8) @ S(0.62, 0.62, 3.0), "t_grey")
        for q in range(4):
            mb.box(T(px, fy - 1.1, zb + 0.7 + q * 0.7) @ S(0.74, 0.74, 0.14), "t_grey_lt")
        mb.box(T(px, fy - 1.1, zb + 3.4) @ S(0.95, 0.95, 0.25), "t_grey_lt")
    mb.box(T(0, fy - 0.75, zb + 3.62) @ S(4.6, 1.8, 0.24), "t_tan_dk")
    # tiers
    z = zb + 3.5
    w, d = W - 0.4, D - 0.3
    for t in range(6):
        h = 1.15 - 0.03 * t
        mb.box(T(0, 0, z + h / 2) @ S(w, d, h), "t_tan" if t % 2 == 0 else "t_tan_lt")
        mb.box(T(0, 0, z + 0.07) @ S(w + 0.55, d + 0.55, 0.16), "t_tan_dk")                # eave ledge
        mb.box(T(0, 0, z + h + 0.04) @ S(w + 0.2, d + 0.2, 0.1), "t_red")
        n = max(2, int(w / 1.05))
        for k in range(n):                                                                # niches with tiny roofs
            x = -w / 2 + (k + 0.5) * w / n
            mb.box(T(x, -d / 2 - 0.03, z + h * 0.5) @ S(0.55, 0.08, h * 0.55), "dark")
            mb.box(T(x, -d / 2 - 0.1, z + h * 0.84) @ S(0.7, 0.2, 0.1), "t_tan_dk")
        for sx in (-1, 1):                                                                # corner rooflets
            mb.cone(T(sx * (w / 2 + 0.2), -d / 2 - 0.2, z + 0.4) @ Rz(math.pi / 4), "t_red", segments=4, r1=0.42, r2=0.05, depth=0.55)
        z += h + 0.1
        w, d = w * 0.82, d * 0.84
    # barrel-vault crown and gold finials
    mb.box(T(0, 0, z + 0.3) @ S(w + 0.3, d + 0.2, 0.6), "t_tan_dk")
    mb.cone(T(0, 0, z + 0.6) @ Ry(math.pi / 2), "t_red", segments=8, r1=d * 0.55, r2=d * 0.55, depth=w + 0.3)
    for k in range(3):
        mb.cone(T((k - 1) * (w * 0.32), 0, z + 0.6 + d * 0.55 + 0.25), "t_gold", segments=6, r1=0.14, r2=0.02, depth=0.7)
    ob = mb.obj("TempleTower", c)
    ob.location = (TOWER[0], TOWER[1], 0.0)
    return ob


def make_steps(c):
    mb = kit.MB(bevel=0.02)
    x0, x1 = TOWER[0] - 3.1, TOWER[0] + 3.1
    fy = TOWER[1] - 1.9
    for k in range(4):
        zt = PORCH_Z - 0.14 * k
        yy = fy - 0.15 - 0.7 * k - 0.45
        mb.box(T((x0 + x1) / 2, yy + 0.15, zt / 2) @ S(x1 - x0 + k * 0.5, 1.4 - 0.0, zt), "t_step")
    # carved side blocks (balustrades)
    for sx in (-1, 1):
        mb.box(T(TOWER[0] + sx * 3.25, fy - 1.1, 0.55) @ S(0.4, 3.4, 1.1), "t_grey")
    return mb.obj("TempleSteps", c)


def make_kneeler(c, name, kind, seed, cloth="cloth_w", pray=True):
    """The kit rig kneeling (as the king of the Thiruvattar set): seated legs turned onto the knees."""
    root, parts = kit.make_rig(name, c, kind, seed=seed, seated=True, cloth=cloth)
    waist = bpy.data.objects.new(name + "_waist", None)
    c.objects.link(waist)
    waist.parent = root
    hip_z = kit.SEAT_H + 0.09
    waist.location = (0, 0, hip_z)
    body = parts["body"]
    body.parent = waist
    body.location = (0, 0, kit.RIG_SEAT_DROP - hip_z)
    hips = parts["hips"]
    hips.rotation_euler = (-math.pi / 2, 0, 0)
    hips.location = (0, -hip_z, hip_z)
    parts["waist"] = waist
    if kind == "commander":                       # a devotee: bare head and a plain white mundu (no red turban or sash)
        kit.recolor(parts["head"], strip=("red",))
        kit.recolor(parts["body"], {"red": "white"})
    kit.key_pose(parts, 1, {"armL": (1.0, 0.0, 0.55), "armR": (1.0, 0.0, -0.55), "waist": (-0.25, 0, 0), "head": (-0.15, 0, 0)})
    return root, parts


def make_standing_prayer(c, name, seed):
    root, parts = kit.make_rig(name, c, "villager", seed=seed, cloth="cloth_w")
    kit.key_pose(parts, 1, {"armL": (1.15, 0.0, 0.55), "armR": (1.15, 0.0, -0.55), "head": (-0.05, 0, 0)})
    return root, parts


def lamp_row(c, lamp, p0, p1, z, step, rng, name, fl):
    p0, p1 = Vector(p0), Vector(p1)
    n = max(1, int((p1 - p0).length / step))
    for i in range(n + 1):
        p = p0 + (p1 - p0) * (i / n)
        ob = kit.instance(lamp, f"{name}{i}", c, (p.x, p.y, z), rot_z=rng.uniform(0, 6.28))
        if rng.random() < 0.4:
            kit.animate_flicker(ob, rng, fl[0], fl[1], amount=0.18, every=(4, 9))


def build_temple(c, lib_c, rng, ev):
    register_palette()
    f0, f1 = ev["s64"]
    make_tower(c)
    make_steps(c)
    lamp = iw._clay_lamp(lib_c)
    kit.hide_source(lamp)
    tx, ty = TOWER
    fy = ty - 1.9
    fl = (f0, f1)
    # lamps: along each step edge, the porch front and round the pillar bases
    for k in range(4):
        zt = PORCH_Z - 0.14 * k + 0.02
        yy = fy - 0.15 - 0.7 * k - 0.95
        lamp_row(c, lamp, (tx - 2.9, yy), (tx + 2.9, yy), zt, 0.42, rng, f"StepLamp{k}_", fl)
    lamp_row(c, lamp, (tx - 3.0, ty - 1.9), (tx - 1.0, ty - 1.9), PORCH_Z + 0.02, 0.4, rng, "PorchL", fl)
    lamp_row(c, lamp, (tx + 1.0, ty - 1.9), (tx + 3.0, ty - 1.9), PORCH_Z + 0.02, 0.4, rng, "PorchR", fl)
    for sx in (-1, 1):
        lamp_row(c, lamp, (tx + sx * 1.25, ty - 3.1), (tx + sx * 2.25, ty - 3.1), PORCH_Z + 0.32, 0.3, rng, f"PillarLamp{sx}_", fl)
    # the king kneeling on the porch edge, sword before him (S37's kneeling king, re-used)
    lay = f0 + int(0.5 * (f1 - f0))
    root, parts, held, floor = iw.make_kneeling_king(c, f1, {"s37": (f0, f1), "lay": lay}, rng)
    root.location = (tx + 0.9, ty - 2.55, PORCH_Z)
    root.rotation_euler[2] = face(-0.12, 1.0)
    iw.pose_king(root, parts, held, floor, {"s37": (f0, f1), "lay": lay}, step_z=PORCH_Z)
    kit.animate_rig_idle(parts, rng, f0, f1, body=0.006, head=0.04, skip=("waist", "armL", "armR", "head"))
    # two priests with joined hands at the left of the door
    for i, (dx, dy) in enumerate(((-0.9, -2.2), (-1.7, -2.3))):
        pr, pp = make_standing_prayer(c, f"Priest{i}", 20 + i)
        pr.location = (tx + dx, ty + dy, PORCH_Z)
        pr.rotation_euler[2] = face(0.35, 1.0)
        kit.animate_rig_idle(pp, rng, f0, f1, skip=("armL", "armR", "head"))
    # kneeling devotees on the ground: a group at the left, a short row at the front right
    spots = [(-2.4, -1.9), (-3.5, -1.5), (-2.0, -3.1), (-3.1, -3.0), (-4.2, -2.6)]
    for i, (x, y) in enumerate(spots):
        dv, dp = make_kneeler(c, f"DevoteeL{i}", "commander", 30 + i)
        dv.location = (x, y, 0.0)
        dv.rotation_euler[2] = face(1.0, 0.6) + rng.uniform(-0.15, 0.15)
        kit.animate_rig_idle(dp, rng, f0, f1, body=0.006, head=0.04, skip=("waist", "armL", "armR", "head"))
    for i, (x, y) in enumerate(((5.2, -2.3), (6.2, -1.9), (5.6, -3.5))):
        dv, dp = make_kneeler(c, f"DevoteeR{i}", "commander", 40 + i)
        dv.location = (x, y, 0.0)
        dv.rotation_euler[2] = face(-0.7, 0.8) + rng.uniform(-0.15, 0.15)
        kit.animate_rig_idle(dp, rng, f0, f1, body=0.006, head=0.04, skip=("waist", "armL", "armR", "head"))
    for i, (x, y) in enumerate(((tx + 4.0, ty - 5.2), (tx + 4.8, ty - 5.0))):
        pr, pp = make_standing_prayer(c, f"StandDevotee{i}", 50 + i)
        pr.location = (x, y, 0.0)
        pr.rotation_euler[2] = face(-0.7, 1.0)
        kit.animate_rig_idle(pp, rng, f0, f1, skip=("armL", "armR", "head"))
    for i, (x, y) in enumerate(((-5.0, -0.9), (-5.6, -2.6), (tx + 5.6, ty - 6.2))):
        g = kit.make_figure(f"SpearGuard{i}", c, "nair_spear", seed=60 + i)
        g.location = (x, y, 0.0)
        g.rotation_euler[2] = face(0.6, 1.0)
        kit.animate_idle(g, rng, f0, f1, 0.02)
    # plants and rocks
    bananas = [palw.make_banana(f"LibTBanana{i}", lib_c, seed=i, height=2.6 + 0.4 * i) for i in range(3)]
    palms = [kit.make_palm(f"LibTPalm{i}", lib_c, seed=80 + i, height=7.0 + i) for i in range(3)]
    rocks = [kit.make_rock(f"LibTRock{i}", lib_c, seed=70 + i, size=0.5 + 0.3 * i) for i in range(3)]
    for s in bananas + palms + rocks:
        kit.hide_source(s)
    for k, (x, y) in enumerate(((-6.4, 3.0), (-5.8, 5.2), (-6.9, 0.8), (-7.2, 6.4), (tx + 5.2, ty + 0.2), (tx + 5.9, ty - 2.0), (tx + 4.6, ty - 5.0))):
        kit.instance(bananas[k % 3], f"TBanana{k}", c, (x, y, 0.0), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.95, 1.2))
    for k, (x, y) in enumerate(((-7.2, 3.4), (-6.2, 6.6), (tx + 6.2, ty + 3.0))):
        kit.instance(palms[k % 3], f"TPalm{k}", c, (x, y, 0.0), rot_z=rng.uniform(0, 6.28), scale=1.0)
    for k, (x, y) in enumerate(((-8.0, -1.0), (tx + 6.6, ty - 6.0), (-2.0, -8.7), (3.0, -9.0), (tx + 6.8, ty + 4.8))):
        kit.instance(rocks[k % 3], f"TRock{k}", c, (x, y, 0.0), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(1.0, 1.8))
    bushes = [kit.make_bush(f"LibTBush{i}", lib_c, seed=90 + i, size=0.9 + 0.2 * i) for i in range(3)]
    for b_ in bushes:
        kit.hide_source(b_)
    for k in range(26):
        a = rng.uniform(0, math.tau)
        x, y = 7.2 * math.cos(a) * rng.uniform(0.7, 1.0) , 6.0 * math.sin(a) * rng.uniform(0.7, 1.0)
        if y < -1.0 and -6.5 < x < 7:
            continue
        kit.instance(bushes[k % 3], f"TBush{k}", c, (x, y, 0.0), rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.8, 1.3))
    # warm point lights at the door and on the king
    for i, (x, y, z, e) in enumerate(((tx - 0.5, ty - 3.2, 1.6, 60.0), (tx + 1.6, ty - 3.4, 1.0, 40.0), (tx - 2.6, ty - 3.9, 0.8, 30.0))):
        ld = bpy.data.lights.new(f"TempleLamp{i}", "POINT")
        ld.color = (1.0, 0.58, 0.26)
        ld.energy = e
        ld.shadow_soft_size = 0.3
        lo = bpy.data.objects.new(f"TempleLamp{i}", ld)
        c.objects.link(lo)
        lo.location = (x, y, z)
        md.flicker(ld, "energy", e, 0.25, f0, f1, rng)
