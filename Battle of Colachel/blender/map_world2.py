"""Map beats of the epilogue: S59 (K71), S61 (K74), S63 (K76). Built on top of map_world, shown only in their own beats.

S59 Travancore takes Kollam and Kayamkulam and goes on north; the Nedumkotta wall line is drawn across the north.
S61 The Dutch star fort at Kanyakumari, the tip; two Dutch ships sail away from it.
S63 The red Travancore is the biggest colour on the coast; pepper ships stream to its ports.
No text on the map. Everything appears with hide_render / scale keys inside its beat.
"""
import math
import random

import bpy
import bmesh
from mathutils import Vector

import colachel_kit as kit
import kerala_geo as geo
import map_world as mw

RED = (0.86, 0.16, 0.12)


def _clear_anim(ob):
    ob.animation_data_clear()


def appear(obs, f_on, f_off=None):
    """Render only from f_on (to f_off). Replaces any earlier hide keys."""
    for ob in obs:
        _clear_anim(ob)
        keys = [(1, True), (f_on - 1, True), (f_on, False)]
        if f_off is not None:
            keys += [(f_off, False), (f_off + 1, True)]
        for f, h in keys:
            ob.hide_render = h
            ob.keyframe_insert("hide_render", frame=f)


def hide_other_washes(f0, f1, keep_prefixes):
    """Old territory tints and frontier ribbons are off while this beat runs (their later state is kept)."""
    olds = [o for o in bpy.data.objects if o.name.startswith(("Territory_", "Border_")) and not o.name.startswith(keep_prefixes)]
    mw.hide_during(olds, f0, f1)


def stone_wall_line(coll, bvh, pts, f_on, f_off, f_end, name="Nedumkotta", step=300.0, h=260.0):
    """A long wall with square towers along pts: it grows from the first point to the last between f_on and f_off-ish."""
    kit.mat("m_wall", (0.88, 0.82, 0.68))
    kit.mat("m_wall_dk", (0.55, 0.45, 0.34))
    segs = []
    # resample at `step`
    dists = [0.0]
    for a, b in zip(pts, pts[1:]):
        dists.append(dists[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = dists[-1]
    n = int(total / step)
    samples = []
    for k in range(n + 1):
        s = total * k / n
        i = max(j for j in range(len(dists)) if dists[j] <= s + 1e-6)
        i = min(i, len(pts) - 2)
        u = (s - dists[i]) / max(1e-6, dists[i + 1] - dists[i])
        samples.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u))
    objs = []
    for k in range(n):
        (ax, ay), (bx, by) = samples[k], samples[k + 1]
        za = mw.ground_z(bvh, ax, ay)
        zb = mw.ground_z(bvh, bx, by)
        L = math.hypot(bx - ax, by - ay)
        ang = math.atan2(by - ay, bx - ax)
        mb = kit.MB(bevel=3.0)
        zc = (za + zb) / 2
        mb.box(kit.T(0, 0, h / 2) @ kit.S(L + 10, 200, h), "m_wall")
        mb.box(kit.T(0, 0, h + 15) @ kit.S(L + 14, 226, 36), "m_wall_dk")
        if k % 4 == 0:                                   # a square tower every fourth stretch
            mb.box(kit.T(0, 0, h + 70) @ kit.S(360, 360, 330), "m_wall")
            mb.box(kit.T(0, 0, h + 250) @ kit.S(420, 420, 50), "m_wall_dk")
        ob = mb.obj(f"{name}{k}", coll)
        ob.location = ((ax + bx) / 2, (ay + by) / 2, zc - 20.0)
        ob.rotation_euler[2] = ang
        ob.visible_shadow = True
        t = f_on + (f_off - f_on) * k / max(1, n - 1)
        _clear_anim(ob)
        for f, s, hid in ((1, 0.01, True), (round(t) - 1, 0.01, True), (round(t), 0.01, False), (round(t) + 12, 1.0, False),
                          (f_end, 1.0, False), (f_end + 1, 1.0, True)):
            ob.scale = (1.0, 1.0, s)
            ob.hide_render = hid
            ob.keyframe_insert("scale", frame=f)
            ob.keyframe_insert("hide_render", frame=f)
        objs.append(ob)
    return objs


def formation(coll, tpls, name, centre, face, rows, cols, spacing, scale, ground, rng, f_on, f_off, banner=False):
    """A block of marching soldiers (static, idle bob) that appears at f_on and goes at f_off."""
    obs = []
    cx, cy = centre
    ca, sa = math.cos(face), math.sin(face)
    for r in range(rows):
        for c in range(cols):
            lx, ly = (c - (cols - 1) / 2) * spacing, -r * spacing
            x, y = cx + lx * ca - ly * sa, cy + lx * sa + ly * ca
            root, parts = mw.new_walker(f"{name}_{r}_{c}", coll, tpls[(r + c) % len(tpls)], scale * rng.uniform(0.96, 1.04))
            root.location = (x, y, ground(x, y))
            root.rotation_euler = (0, 0, face - math.pi / 2 + math.pi / 2 * 0)
            for f, h in ((1, True), (f_on - 1, True), (f_on, False), (f_off, False), (f_off + 1, True)):
                for o in parts.values():
                    o.hide_render = h
                    o.keyframe_insert("hide_render", frame=f)
            obs += list(parts.values())
            if banner and r == 0 and c == cols // 2:
                import port_world as port
                kit_colour = mw.kit_colours("flag_r") if "flag_r" not in kit.PALETTE else None
                flag = mw.standard(f"{name}Flag", coll, root, (0.45, 0.0), "flag_r", pole_h=5.2, w=2.2, h=1.4)
                for o in flag:
                    for f, h in ((1, True), (f_on - 1, True), (f_on, False), (f_off, False), (f_off + 1, True)):
                        o.hide_render = h
                        o.keyframe_insert("hide_render", frame=f)
                obs += flag
    return obs


# ======================================================================= S59
def build_s59(coll, lib_c, land_ob, land, bvh, frames, T_of, frontier_xy, words, T_old=4700.0, T_mid=6300.0, T_north=9300.0):
    f0, f1 = frames
    land_poly = geo.land_polygon_detailed(120.0)
    # the red wash: the old frontier at once, then Kollam and Kayamkulam, then on north to the Nedumkotta line
    stages = [("S59a", lambda x, y: T_of(x, y) < T_old, (f0, f0 + 1)),
              ("S59b", lambda x, y: T_of(x, y) < T_mid, (words["kollam"], words["kollam"] + 36)),
              ("S59c", lambda x, y: T_of(x, y) < T_north, (words["north"], words["north"] + 70))]
    mw.build_territory(coll, land_ob, bvh, stages)
    terr = [bpy.data.objects[f"Territory_{n}"] for n, _, _ in stages]
    mw.show_only(terr, f0, f1)
    hide_other_washes(f0, f1, ("Territory_S59",))
    # the frontier ribbon at the north edge, drawn when the wash gets there
    pts = [frontier_xy(T_north, w) for w in range(-300, 4600, 60)]
    pts = [p for p in pts if geo.point_in_poly(p[0], p[1], land_poly)]
    border = mw.build_border(coll, bvh, pts, (f0, f0 + 1), None, name="Border_S59")
    for v in border.data.vertices:
        if v.co.z < 20:
            v.co.z = 50.0
    appear([border], words["north"] + 20, f1)
    # Kollam's and Kayamkulam's forts turn red
    for nm in ("Kollam", "Kayamkulam"):
        try:
            mw.recolor_fort(nm, RED, (words["kollam"] + 6, words["kollam"] + 30))
        except Exception:
            pass
    # the Nedumkotta: a long wall and ditch line across the north, from the sea inland to the hills
    wall = [frontier_xy(T_north + 120.0, w) for w in range(-300, 7600, 40)]
    wall = [p for p in wall if geo.point_in_poly(p[0], p[1], land_poly)]
    wall_obs = stone_wall_line(coll, bvh, wall, words["wall"], words["wall"] + 110, f1)
    # red soldiers in blocks on the new land, appearing with each stage
    rng = random.Random(59)
    tpls = [mw.walker_template(f"S59Tpl{i}", lib_c, "nair", seed=70 + i) for i in range(3)]
    ground = lambda x, y: mw.ground_z(bvh, x, y) - 0.5
    path = mw.beach_path(land, 8600, 3000, inland=700.0)
    spots = [(0.12, words["kollam"] - 10), (0.27, words["kollam"] + 30), (0.42, words["kollam"] + 70), (0.58, words["north"] + 20),
             (0.72, words["north"] + 55), (0.86, words["north"] + 90), (0.19, f0 + 30), (0.5, words["north"] + 40)]
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
    obs = []
    centres = [mw.path_at(path, total * u)[0] for u, _ in spots]
    clear = [o for o in bpy.data.objects if o.name.startswith(("MapPalm", "MapTree")) and any(math.hypot(o.location.x - cx, o.location.y - cy) < 420.0 for cx, cy in centres)]
    mw.hide_during(clear, f0, f1)
    for k, (u, t) in enumerate(spots):
        (x, y), d = mw.path_at(path, total * u)
        face = math.atan2(d[1], d[0]) + math.pi * 0.0
        obs += formation(coll, tpls, f"S59Troop{k}", (x, y), face, 3, 4, 230.0, 150.0, ground, rng, t, f1, banner=True)
    return terr + [border] + wall_obs + obs


# ======================================================================= S61
def build_s61(coll, lib_c, land, bvh, frames, end, leave):
    f0, f1 = frames
    mw.swap_forts(coll, f0, f1)
    hide_other_washes(f0, f1, ("Territory_S61",))
    for nm in ("DutchFortKochi",):
        ob = bpy.data.objects.get(nm)
        if ob:
            mw.hide_during([ob], f0, f1)
    tx, ty = geo.xy(8.0883, 77.5385)
    kit.mat("dutch_or2", (0.96, 0.46, 0.10))
    fort = mw.make_star_fort("S61DutchFort", coll, "dutch_or2")
    fx, fy = tx - 230.0, ty + 300.0
    fort.location = (fx, fy, mw.ground_z(bvh, fx, fy) - 1.0)
    fort.rotation_euler[2] = math.radians(18)
    fort.scale = (24.0, 24.0, 24.0)
    palms = [o for o in bpy.data.objects if o.name.startswith("MapPalm") and math.hypot(o.location.x - fx, o.location.y - fy) < 900.0]
    mw.hide_during(palms, f0, f1)
    obs = [fort]
    sea = "MapSeaMatteLate"
    courses = (((tx + 420, ty - 780), (tx + 3900, ty - 1900), 0.0), ((tx - 650, ty - 620), (tx - 3600, ty - 2100), 0.0))
    for i, (p0, p1, _) in enumerate(courses):
        ship, parts, _ = mw.dutch_ship(f"S61Ship{i}", coll, seed=30 + i)
        ship.scale = (13.0, 13.0, 13.0)
        hd = math.atan2(-(p1[0] - p0[0]), p1[1] - p0[1])
        carrier = bpy.data.objects.new(f"S61Path{i}", None)
        coll.objects.link(carrier)
        carrier.rotation_euler[2] = hd
        t0 = leave + 20 * i

        def course(f, p0=p0, p1=p1, t0=t0):
            u = min(1.0, max(0.0, (f - t0) / max(1, f1 - t0)))
            u = u * u * (3 - 2 * u) * 0.9 + u * 0.1
            return p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u

        def sail(carrier=carrier, course=course):
            for f in range(f0 - 4, f1 + 5, 4):
                x, y = course(f)
                carrier.location = (x, y, mw.sea_lift(x, y, f, 0.5, late=True))
                carrier.keyframe_insert("location", frame=f)
        kit.keyframe_linear(sail)
        ship.parent = carrier
        for f in range(f0 - 6, f1 + 7, 6):
            ship.rotation_euler = (math.radians(1.6 * math.sin(f / 13.0 + i)), math.radians(2.0 + 1.6 * math.sin(f / 17.0)), 0)
            ship.keyframe_insert("rotation_euler", frame=f)
        wake = mw.build_wake(f"S61Wake{i}", coll, carrier, length=247.0, beam=70.0, seed=61 + i, reach=2200.0, size=0.9, sea=sea, late=True)
        for f, s_ in ((t0 - 2, 0.01), (t0 + 30, 1.0)):
            wake.scale = (s_, s_, 1.0)
            wake.keyframe_insert("scale", frame=f)
        obs += parts + [wake]
    mw.show_only(obs, f0, f1)
    return obs


# ======================================================================= S63
def build_s63(coll, lib_c, land_ob, land, bvh, frames, T_of, frontier_xy, words, T_north=9300.0):
    f0, f1 = frames
    mw.swap_forts(coll, f0, f1)
    hide_other_washes(f0, f1, ("Territory_S63", "Border_S63"))
    stages = [("S63", lambda x, y: T_of(x, y) < T_north, (words["big"], words["big"] + 90))]
    mw.build_territory(coll, land_ob, bvh, stages)
    t = bpy.data.objects["Territory_S63"]
    mw.show_only([t], f0, f1)
    land_poly = geo.land_polygon_detailed(120.0)
    pts = [frontier_xy(T_north, w) for w in range(-300, 4600, 60)]
    pts = [p for p in pts if geo.point_in_poly(p[0], p[1], land_poly)]
    border = mw.build_border(coll, bvh, pts, (f0, f0 + 1), None, name="Border_S63")
    for v in border.data.vertices:
        if v.co.z < 20:
            v.co.z = 50.0
    appear([border], words["big"] + 40, f1)
    # a red Travancore fort at its main seats, and the sea lanes of the pepper ships
    obs = [t, border]
    rng = random.Random(63)
    sea = "MapSeaMatteLate"
    lane = mw.beach_path(land, 6200, 200, inland=-1300.0)
    ltot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(lane, lane[1:]))
    n = 26
    for i in range(n):
        (px, py), _d = mw.path_at(lane, ltot * (i + rng.uniform(0.2, 0.8)) / n)
        p1 = (px - rng.uniform(0, 500), py + rng.uniform(-200, 200))
        p0 = (px - rng.uniform(3500, 7500), py + rng.uniform(-2500, 1500))
        ship, parts, _ = mw.dutch_ship(f"S63Ship{i}", coll, seed=40 + i, sails=True)
        ship.scale = (15.0, 15.0, 15.0)
        hd = math.atan2(-(p1[0] - p0[0]), p1[1] - p0[1])
        carrier = bpy.data.objects.new(f"S63Path{i}", None)
        coll.objects.link(carrier)
        carrier.rotation_euler[2] = hd
        t0 = f0 + rng.randint(0, 60)

        def course(f, p0=p0, p1=p1, t0=t0):
            u = min(1.0, max(0.0, (f - t0) / max(1, f1 - t0)))
            u = 1 - (1 - u) ** 1.6
            return p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u

        def sail(carrier=carrier, course=course):
            for f in range(f0 - 4, f1 + 5, 6):
                x, y = course(f)
                carrier.location = (x, y, mw.sea_lift(x, y, f, 0.5, late=True))
                carrier.keyframe_insert("location", frame=f)
        kit.keyframe_linear(sail)
        ship.parent = carrier
        for f in range(f0 - 6, f1 + 7, 8):
            ship.rotation_euler = (math.radians(1.4 * math.sin(f / 13.0 + i)), math.radians(2.0 + 1.4 * math.sin(f / 17.0 + i)), 0)
            ship.keyframe_insert("rotation_euler", frame=f)
        obs += parts
        if i % 2 == 0:
            wake = mw.build_wake(f"S63Wake{i}", coll, carrier, length=247.0, beam=70.0, seed=63 + i, reach=1800.0, size=0.8, sea=sea, late=True)
            obs.append(wake)
    mw.show_only(obs[2:], f0, f1)
    return obs
