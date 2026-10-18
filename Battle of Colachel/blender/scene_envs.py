"""Full surroundings for S60 (Udayagiri fort courtyard), S62 (the Mavelikkara meadow) and S64 (the temple compound), so
no scene floats on an empty backdrop (user review 2026-10-18). Each function adds terrain, far ground, far hills, a sky
and the nearby buildings / trees around a scene that is built at the origin."""
import math
import random

import bpy

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S
import surround as sr


def _ring_wall(c, hx, hy, h, thick, seed, gate_front=None, skip_front=False, crenel=True, name="Wall"):
    """A rectangular curtain wall round (-hx..hx, -hy..hy) with corner towers; optional gateway in the front (-y) wall."""
    objs = []
    walls = [("N", 0, hy + thick / 2, 0.0, 2 * hx + thick * 2, None), ("S", 0, -hy - thick / 2, 0.0, 2 * hx + thick * 2, gate_front),
             ("W", -hx - thick / 2, 0, math.pi / 2, 2 * hy, None), ("E", hx + thick / 2, 0, math.pi / 2, 2 * hy, None)]
    for tag, x, y, rz, L, gap in walls:
        if tag == "S" and skip_front:
            continue
        w = kit.make_stone_wall(f"{name}{tag}", c, L, h, thick=thick, seed=seed + len(objs), crenel=crenel, gap=gap)
        w.location = (x, y, 0)
        w.rotation_euler[2] = rz
        objs.append(w)
    for sx in (-1, 1):
        for sy in (-1, 1):
            if skip_front and sy < 0:
                continue
            t = kit.make_stone_wall(f"{name}Tower{sx}{sy}", c, thick * 2.4, h + 2.2, thick=thick * 2.4, seed=seed + 9, crenel=True)
            t.location = (sx * (hx + thick / 2), sy * (hy + thick / 2), 0)
            objs.append(t)
    return objs


def fort_env(c, lib_c, rng):
    """S60: the chapel stands in a courtyard inside Udayagiri fort: flagstones, curtain wall with a gate, towers, two
    pavilions, a shed, then the fort's hill, trees and distant hills at dusk."""
    for k, v in {"grass": (0.30, 0.38, 0.19), "soil": (0.34, 0.27, 0.19)}.items():
        kit.PALETTE[k] = v
    ter, h = sr.terrain(c, "grass", flat_r=22.0, amp=18.0, seed=3, alt_mat="soil")
    sr.far_ground(c, (0.22, 0.28, 0.20))
    sr.far_hills(c, (0.30, 0.36, 0.42), n=44, r0=300, r1=1000, hmin=50, hmax=200)
    kit.make_flagstones("Courtyard", c, -17.0, 17.0, -15.0, 15.0, seed=9, step=(1.9, 1.5))
    _ring_wall(c, 17.0, 15.0, 5.6, 1.7, 21, gate_front=(-2.4, 2.4, 3.8), name="Fort")
    for i, (x, y, rz, w) in enumerate(((-11.5, 10.0, 0.0, 5.0), (11.8, 10.4, 0.0, 5.0), (-12.5, -9.5, math.pi, 4.6))):
        p = kit.make_pavilion(f"CourtPavilion{i}", c, w=w, d=3.8, h=3.0)
        p.location = (x, y, 0.0)
        p.rotation_euler[2] = rz
    sh = kit.make_shed("CourtShed", c, w=4.8, d=3.6, h=2.4)
    sh.location = (12.5, -9.0, 0.0)
    sh.rotation_euler[2] = math.pi
    bl = kit.make_ball_pile("CourtBalls", c, base=4, seed=3)
    bl.location = (-7.5, -11.0, 0.0)
    sr.scatter(c, lib_c, rng, 70, 24.0, 110.0, height=h)
    sr.sky((0.98, 0.64, 0.42), (0.52, 0.40, 0.52), (0.10, 0.12, 0.26), strength=0.22)


def meadow_env(c, lib_c, rng):
    """S62: Mavelikkara: a green meadow, a village of thatched huts behind the tent, two small encampments, palm groves,
    low hills on the horizon, a clear sky."""
    for k, v in {"grass": (0.42, 0.58, 0.24), "soil": (0.46, 0.36, 0.22)}.items():
        kit.PALETTE[k] = v
    ter, h = sr.terrain(c, "grass", flat_r=17.0, amp=12.0, seed=7, alt_mat="soil")
    sr.far_ground(c, (0.36, 0.50, 0.26))
    sr.far_hills(c, (0.36, 0.52, 0.50), n=46, r0=320, r1=1100, hmin=60, hmax=210)
    huts = [kit.make_hut_gable(f"LibMeadHut{i}", lib_c, w=4.0 + 0.5 * (i % 3), d=3.4, h=2.1, seed=40 + i) for i in range(3)]
    for s in huts:
        kit.hide_source(s)
    for i in range(9):
        a = math.radians(-25 + i * 22)
        r = 24 + 4 * (i % 3)
        x, y = r * math.cos(a) + (-6), r * math.sin(a) + 14
        kit.instance(huts[i % 3], f"MeadHut{i}", c, (x, y, h(x, y)), rot_z=rng.uniform(0, 6.28))
    tents = [kit.make_cone_tent(f"LibMeadTent{i}", lib_c, r=1.9 + 0.2 * i, h=3.0 + 0.3 * i, seed=i) for i in range(2)]
    for s in tents:
        kit.hide_source(s)
    for i, (x, y) in enumerate(((22.0, -9.0), (25.5, -6.0), (23.0, -3.2), (-24.0, -8.0), (-27.0, -4.5), (-22.5, -2.0))):
        kit.instance(tents[i % 2], f"MeadTent{i}", c, (x, y, h(x, y)), rot_z=rng.uniform(0, 6.28))
    sr.scatter(c, lib_c, rng, 90, 13.0, 100.0, height=h, avoid=lambda x, y: abs(x) < 9.5 and -12.5 < y < 9.5)
    sr.sky((0.98, 0.90, 0.76), (0.72, 0.84, 0.95), (0.42, 0.64, 0.92), strength=1.1)


def temple_env(c, lib_c, rng):
    """S64: the temple stands in its walled compound: flagstone court, side and back compound walls with lamp niches, a
    pillared hall to one side, then the temple town's roofs, palms and hills at dusk."""
    for k, v in {"grass": (0.26, 0.32, 0.17), "soil": (0.30, 0.22, 0.15)}.items():
        kit.PALETTE[k] = v
    ter, h = sr.terrain(c, "grass", flat_r=28.0, amp=18.0, seed=11, alt_mat="soil")
    sr.far_ground(c, (0.18, 0.22, 0.16))
    sr.far_hills(c, (0.26, 0.30, 0.42), n=44, r0=320, r1=1000, hmin=60, hmax=220)
    kit.PALETTE["court"] = (0.46, 0.40, 0.34)
    kit.PALETTE["flag_a"] = (0.50, 0.44, 0.37)
    kit.PALETTE["flag_b"] = (0.42, 0.37, 0.31)
    kit.PALETTE["flag_c"] = (0.56, 0.50, 0.42)
    kit.make_flagstones("TempleCourt", c, -15.0, 20.0, -13.0, 12.0, seed=12, step=(2.0, 1.6))
    # compound wall: back and both sides (the front is open toward the camera, with low gate piers)
    ws = _ring_wall(c, 17.5, 12.5, 4.4, 1.5, 31, skip_front=True, crenel=False, name="Compound")
    for o in ws:
        o.location.x += 2.5
    for sx in (-1, 1):
        p = kit.make_stone_wall(f"GatePier{sx}", c, 1.6, 3.2, thick=1.6, seed=44, crenel=False)
        p.location = (2.5 + sx * 4.0, -13.8, 0)
    # a pillared hall (mandapam) against the left wall, and houses of the temple town beyond the walls
    hall = kit.make_pavilion("Mandapam", c, w=7.0, d=4.2, h=3.2)
    hall.location = (-9.5, 5.5, 0.0)
    hall.rotation_euler[2] = math.pi / 2
    huts = [kit.make_hut_gable(f"LibTownHut{i}", lib_c, w=4.4 + 0.4 * (i % 3), d=3.6, h=2.3, seed=60 + i) for i in range(3)]
    for s in huts:
        kit.hide_source(s)
    for i in range(18):
        a = math.radians(-60 + i * 11)
        r = 36 + 5 * (i % 4)
        x, y = 2.5 + r * math.cos(a) * 0.9, 4 + r * math.sin(a) * 0.9 + 10
        kit.instance(huts[i % 3], f"TownHut{i}", c, (x, y, h(x, y)), rot_z=rng.uniform(0, 6.28))
    sr.scatter(c, lib_c, rng, 70, 30.0, 110.0, height=h)
    sr.sky((0.95, 0.60, 0.40), (0.46, 0.34, 0.52), (0.08, 0.10, 0.24), strength=0.28)
