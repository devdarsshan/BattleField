"""Colachel beach, November 1740 to June 1741: the Dutch come (S30, S31, S32, S34, S38).

The SAME beach as S01-S06 (colachel_world: land, sea, sky, sun, haze, village, palms), before
the Dutch stockade exists. Each beat adds its own set on top (a collection that is shown only in
that beat's frames), so one timeline holds the five beats with clean cuts between them:

  S30 (K37) three Dutch warships sail along the coast and fire broadsides at the shore.
  S31 (K38) seven ships at anchor; longboats full of soldiers row in; men wade ashore, form up.
  S32 (K39) De Lannoy on the beach points out the stockade line; soldiers carry posts and crates.
  S34 (K41) the stockade goes up post by post at STOCKADE; a column marches inland past
            villages, and smoke rises from one village after another.
  S38 (S05 storm look) the monsoon: rain, wind, rough sea, surf on the beach, the half-built
            stockade soaked, one ship pitching far out.
"""
import math
import random

import bpy
from mathutils import Vector

import colachel_kit as kit
import colachel_world as cw
import port_world as pw

_BASE_HEIGHT = cw.height


def _landing_height(x, y):
    """colachel_world.height without the S06 battery hillock and with the inland hills lowered to
    a third, so the palm-lined coast reads flat as in K37/K38 (nothing here is on those hills)."""
    h = _BASE_HEIGHT(x, y)
    bx, by = cw.BATTERY
    h -= 12.0 * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / 16.0 ** 2)
    d = y - cw.shore_y(x)
    if h > 4.0:
        h = 4.0 + (h - 4.0) * (1.0 - 0.82 * cw._smooth(35, 90, d))
    return h


def install_height():
    """Make colachel_world.height the lowered-hills version (call after film.py has run its reloads)."""
    global H
    cw.height = _landing_height
    H = _landing_height
    base_grass = cw.grass_line
    if not getattr(base_grass, "_landing", False):
        def grass_line(x, y):
            return base_grass(x, y) + 110.0       # sand and palms right back to the villages (K41)
        grass_line._landing = True
        cw.grass_line = grass_line


H = _BASE_HEIGHT
SY = cw.shore_y
SW = cw.stockade_world
COAST_RZ = math.atan2(1.0, 0.3)          # rot_z that points a kit ship's bow WNW along the coast

# the track inland from the stockade gate (S34), and the villages along it
PATH = [(61.4, 9.8), (62.0, 20.0), (60.5, 34.0), (58.0, 48.0), (57.5, 62.0), (60.0, 76.0), (64.0, 90.0),
        (66.0, 105.0), (64.0, 120.0), (62.0, 136.0), (63.0, 152.0)]
HAMLET_AT = [(3, 13.0), (6, -14.0), (8, 13.0)]            # (path point, metres to the side)
NX, NY = 0.287, 0.958                                     # inland, across the coast
TX, TY = 0.958, -0.287                                    # along the coast (ESE)
DL_POS = (50.0, SY(50.0) + 7.0)                          # De Lannoy marks out the stockade (S32)


def cy(x, d):
    """Point d metres inland of the waterline at x (negative d: out at sea)."""
    return (x, SY(x) + d)


def all_objects(coll):
    out = list(coll.objects)
    for ch in coll.children:
        out += all_objects(ch)
    return out


def _is_lib(ob):
    return ob.hide_render and ob.location.z <= -499


def set_vis(coll, ranges):
    """Show every object of coll (and its children collections) only inside the frame ranges."""
    keys = []
    if ranges[0][0] > 1:
        keys.append((1, True))
    for a, b in ranges:
        keys.append((a, False))
        keys.append((b + 1, True))
    for ob in all_objects(coll):
        if _is_lib(ob):
            continue
        for f, hid in keys:
            ob.hide_render = hid
            ob.hide_viewport = hid
            ob.keyframe_insert("hide_render", frame=f)
            ob.keyframe_insert("hide_viewport", frame=f)


def _dense(pts, step=2.0):
    out = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / step))
        out += [(ax + (bx - ax) * k / n, ay + (by - ay) * k / n) for k in range(n)]
    return out + [pts[-1]]


PATH_D = _dense(PATH, 1.5)


def near_path(x, y, r):
    return any((x - a) ** 2 + (y - b) ** 2 < r * r for a, b in PATH_D)


def hamlet_centres():
    out = []
    for i, side in HAMLET_AT:
        (ax, ay), (bx, by) = PATH[i], PATH[i + 1]
        L = math.hypot(bx - ax, by - ay)
        nx, ny = (by - ay) / L, -(bx - ax) / L
        out.append(((ax + bx) / 2 + nx * side, (ay + by) / 2 + ny * side))
    return out


def path_point(s):
    """Point and heading at arc length s along PATH (s < 0 runs back through the gate)."""
    if s < 0:
        (ax, ay), (bx, by) = PATH[0], PATH[1]
        L = math.hypot(bx - ax, by - ay)
        return (ax + (bx - ax) / L * s, ay + (by - ay) / L * s), ((bx - ax) / L, (by - ay) / L)
    for (ax, ay), (bx, by) in zip(PATH, PATH[1:]):
        L = math.hypot(bx - ax, by - ay)
        if s <= L:
            return (ax + (bx - ax) / L * s, ay + (by - ay) / L * s), ((bx - ax) / L, (by - ay) / L)
        s -= L
    (ax, ay), (bx, by) = PATH[-2], PATH[-1]
    L = math.hypot(bx - ax, by - ay)
    return PATH[-1], ((bx - ax) / L, (by - ay) / L)


def _face(dx, dy):
    return math.atan2(dy, dx) - math.pi / 2


# ===================================================================== shared land
def clear_around(cam_points, r=8.0, clearance=15.0):
    """Remove palms, trees and bushes a camera would fly through or brush past."""
    kinds = ("Palm", "GrovePalm", "Tree", "Bush", "GroveBush", "S32Palm", "BatteryPalm")
    for ob in [o for o in bpy.data.objects if o.name.startswith(kinds)]:
        x, y = ob.location.x, ob.location.y
        top = H(x, y) + clearance
        for cx, cy_, cz in cam_points:
            if cz < top and (cx - x) ** 2 + (cy_ - y) ** 2 < r * r:
                bpy.data.objects.remove(ob, do_unlink=True)
                break


# ===================================================================== shared land (continued)
def tidy_trees():
    """Clear the broad-leaf trees off the track and the village sites."""
    hams = hamlet_centres()
    for ob in [o for o in bpy.data.objects if o.name.startswith("Tree")]:
        x, y = ob.location.x, ob.location.y
        if near_path(x, y, 5.5) or any(math.hypot(x - a, y - b) < 15 for a, b in hams) or                 (-115 < x < 210 and y - SY(x) < 150):
            bpy.data.objects.remove(ob, do_unlink=True)


def build_groves(c, rng):
    """Palm groves several rows deep behind the landing beach, as in K38 / K41."""
    palms = [bpy.data.objects[f"LibPalm{i}"] for i in range(6)]
    bushes = [bpy.data.objects[f"LibBush{i}"] for i in range(3)]
    hams = hamlet_centres()
    spots = [(o.location.x, o.location.y) for o in bpy.data.objects if o.name.startswith("Palm")]
    huts = [(o.location.x, o.location.y) for o in bpy.data.objects if o.name.startswith(("Hut", "Fence", "Rock"))]

    def ok(px, py, r=3.0):
        if cw.in_stockade(px, py, 4.5) or near_path(px, py, 7.0) or any(math.hypot(px - a, py - b) < 13
                                                                         for a, b in hams):
            return False
        if px < 40 and any(math.hypot(px - a, py - b) < 8.0 for a, b in huts):
            return False
        return all((px - a) ** 2 + (py - b) ** 2 > r * r for a, b in spots)

    k = 0
    x = -115.0
    while x < 205:
        for row in range(15):
            d = 9 + row * 3.4 + rng.uniform(-1.5, 1.5)
            if 34 < x < 118 and d < 18:
                continue
            px = x + rng.uniform(-1.8, 1.8)
            py = SY(px) + d
            if not ok(px, py):
                continue
            spots.append((px, py))
            kit.instance(palms[k % 6], f"GrovePalm{k}", c, (px, py, H(px, py) - 0.1), rot_z=rng.uniform(0, 6.28),
                         scale=rng.uniform(0.85, 1.2))
            k += 1
        x += rng.uniform(2.8, 3.8)
    # palms along the path and round the villages inland
    for i, (px, py) in enumerate(PATH_D[6::3]):
        for side in (-1, 1):
            qx, qy = px + side * rng.uniform(8.0, 12.0), py + rng.uniform(-2, 2)
            if ok(qx, qy, 3.5):
                spots.append((qx, qy))
                kit.instance(palms[k % 6], f"GrovePalm{k}", c, (qx, qy, H(qx, qy) - 0.1),
                             rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.9, 1.25))
                k += 1
    # a few palms right at the top of the beach, framing the landing (K39)
    for x, d in ((33.5, 6.0), (37.5, 4.0), (41.0, 8.0)):
        px, py = cy(x, d)
        if not cw.in_stockade(px, py, 2.0):
            kit.instance(palms[k % 6], f"GrovePalm{k}", c, (px, py, H(px, py) - 0.1), rot_z=rng.uniform(0, 6.28),
                         scale=rng.uniform(0.95, 1.15))
            k += 1
    for i in range(300):                     # more palms round the track and villages inland
        px = rng.uniform(25, 115)
        py = SY(px) + rng.uniform(42, 150)
        if ok(px, py, 3.4):
            spots.append((px, py))
            kit.instance(palms[k % 6], f"GrovePalm{k}", c, (px, py, H(px, py) - 0.1), rot_z=rng.uniform(0, 6.28),
                         scale=rng.uniform(0.9, 1.25))
            k += 1
    for i in range(90):
        x = rng.uniform(34, 190)
        d = rng.uniform(14, 48)
        px, py = cy(x, d)
        if ok(px, py, 1.5):
            kit.instance(bushes[i % 3], f"GroveBush{i}", c, (px, py, H(px, py) - 0.05), rot_z=rng.uniform(0, 6.28),
                         scale=rng.uniform(0.8, 1.5))
    return spots


def build_path(c):
    """Red-brown dirt track from the stockade gate inland past the villages (K41)."""
    mb = kit.MB()
    pts = PATH_D
    rows = []
    rng = random.Random(4)
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = 1.7 + rng.uniform(-0.25, 0.25)
        row = []
        for s in (-1.0, -0.4, 0.4, 1.0):
            px, py = x + nx * w * s, y + ny * w * s
            row.append(mb.bm.verts.new((px, py, H(px, py) + 0.05 + (0.02 if abs(s) < 1 else 0.0))))
        rows.append(row)
    for i in range(len(rows) - 1):
        for j in range(3):
            mb.face([rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]],
                    "laterite_rd" if j == 1 else "field_dirt_dk")
    return mb.obj("InlandTrack", c)


def build_hamlets(c, rng):
    """Small thatched villages along the track inland (they fall in S34)."""
    gable = [bpy.data.objects[f"LibHutGable{i}"] for i in range(3)]
    hip = [bpy.data.objects[f"LibHutHip{i}"] for i in range(2)]
    fence, crate, barrel = (bpy.data.objects[n] for n in ("LibFence", "LibCrate", "LibBarrel"))
    huts = []
    for hi, (hx, hy) in enumerate(hamlet_centres()):
        for k in range(6):
            a = k * math.tau / 6 + rng.uniform(-0.3, 0.3)
            r = rng.uniform(4.5, 8.0)
            x, y = hx + math.cos(a) * r, hy + math.sin(a) * r
            if near_path(x, y, 4.0):
                continue
            src = (gable + hip)[(k + hi) % 5]
            ob = kit.instance(src, f"Hamlet{hi}Hut{k}", c, (x, y, H(x, y) - 0.1), rot_z=_face(hx - x, hy - y) + math.pi,
                              scale=rng.uniform(0.9, 1.05))
            huts.append((hi, ob))
        for k, (dx, dy) in enumerate(((2.0, -1.0), (-1.5, 2.5), (0.5, 1.5))):
            x, y = hx + dx, hy + dy
            kit.instance((crate, barrel, crate)[k], f"Hamlet{hi}Prop{k}", c, (x, y, H(x, y) - 0.02),
                         rot_z=rng.uniform(0, 3))
        x, y = hx - 9.0, hy + 3.0
        kit.instance(fence, f"Hamlet{hi}Fence", c, (x, y, H(x, y) - 0.02), rot_z=rng.uniform(0, 3))
    return huts


# ===================================================================== ships
def make_sailing_ship(name, c, length, beam, plan, belly, seed):
    ship = kit.make_ship(name, c, length=length, beam=beam, seed=seed)
    pw.make_rig(name + "Rig", c, ship, plan, "flag_o", length=length, beam=beam, belly=belly, seed=seed)
    return ship


FLEET = [(-60.0, -92.0, 262.0, 36.0), (-35.0, -78.0, 76.0, 40.0), (-10.0, -100.0, 248.0, 38.0),
         (15.0, -82.0, 88.0, 42.0), (40.0, -104.0, 270.0, 37.0), (65.0, -86.0, 62.0, 39.0),
         (90.0, -108.0, 255.0, 41.0)]
FLEET_SAILS = [{1: (1, 2), 2: (1,)}, {}, {1: (1, 2), 2: (1, 2), 0: (1,)}, {1: (1,)}, {1: (1, 2), 2: (1, 2)}, {},
               {1: (1,), 2: (1,)}]


def build_fleet(c, end):
    """The seven ships of February 1741 at anchor off the beach (S31-S34)."""
    ships = []
    for i, (x, off, rot, L) in enumerate(FLEET):
        ship = make_sailing_ship(f"Fleet{i}", c, L, 9.5 + 0.12 * (L - 36), FLEET_SAILS[i], 0.8, 20 + i)
        y = SY(x) + off
        ship.location = (x, y, -0.4)
        rz = math.radians(rot)
        ship.rotation_euler = (0, 0, rz)
        pw.rock(ship, end, (0, 0, rz), -0.4, amp=(0.8, 1.3), bob=0.12, seed=20 + i)
        ships.append(ship)
    return ships


# ===================================================================== S30
def build_s30(c, lib, ev):
    """Three warships sail WNW along the coast and fire broadsides at the shore (K37)."""
    rng = random.Random(30)
    end = ev["end"]
    f0, f1 = ev["r30"]
    kit.fx_materials()
    splash_src = []
    for k in range(3):
        ob = kit.make_splash(f"LibSplash{k}", lib, seed=k, h=5.5 + k)
        kit.hide_source(ob)
        splash_src.append(ob)
    sand_src = kit.make_puff("LibSandPuff", lib, seed=3, m="sand")
    kit.hide_source(sand_src)
    dirx, diry = -math.sin(COAST_RZ), math.cos(COAST_RZ)       # bow direction (WNW)
    speed = 1.1
    ships = []
    for i, (x, off, L) in enumerate(((66.0, -60.0, 40.0), (30.0, -55.0, 37.0), (-6.0, -52.0, 39.0))):
        ship = make_sailing_ship(f"S30Ship{i}", c, L, 9.5 + 0.12 * (L - 36), {0: (1, 2), 1: (0, 1, 2), 2: (0, 1, 2)},
                                 1.45, 10 + i)
        back = 19.0                                              # starts this far back along its course
        x0, y0 = x - dirx * back, SY(x) + off - diry * back

        def course(f, x0=x0, y0=y0):
            d = speed * (f - f0) / kit.FPS
            return x0 + dirx * d, y0 + diry * d
        pw.rock(ship, end, (0, 0, COAST_RZ), -0.4, amp=(1.0, 1.6), bob=0.16, seed=10 + i, path=course)
        ships.append((ship, course, L))
    # broadsides: starboard guns (facing the shore), ripple from bow to stern
    for i, (ship, course, L) in enumerate(ships):
        for vf in ev["volleys"][i]:
            ship.location = (*course(vf), -0.4)
            ship.rotation_euler = (0, 0, COAST_RZ)
            kit.ship_broadside(ship, c, [vf], end, side=1, length=L, beam=9.5 + 0.12 * (L - 36), seed=100 * i + vf,
                               ripple=3, puffs=2, flash=5.2, smoke=(2.8, 4.4), drift=(0.6, 0.9), linger=170)
            # a short orange light pulse at the guns, so the flash glows on sails, hull and water
            ld = bpy.data.lights.new(f"S30Glow{i}_{vf}", "POINT")
            ld.color = (1.0, 0.55, 0.15)
            ld.energy = 0.0
            ld.shadow_soft_size = 1.5
            glow = bpy.data.objects.new(f"S30Glow{i}_{vf}", ld)
            c.objects.link(glow)
            glow.parent = ship
            glow.location = (6.0 / ship.scale.x, 0.0, 4.5 / ship.scale.x)
            for df, e in ((-2, 0.0), (1, 9000.0), (6, 7000.0), (14, 0.0)):
                ld.energy = e
                ld.keyframe_insert("energy", frame=vf + df)
            # the shot lands: plumes in the shallows, sand thrown up on the beach below the village
            for k in range(6):
                x = rng.uniform(-28, 52)
                t = vf + 16 + k * 3 + rng.randint(0, 4)
                if k < 4:
                    px, py = cy(x, -rng.uniform(3, 16))
                    sp = kit.instance(splash_src[k % 3], f"S30Splash{i}_{vf}_{k}", c, (px, py, 0.0),
                                      rot_z=rng.uniform(0, 6.28), scale=0.0)
                    kit.animate_splash(sp, t, size=rng.uniform(0.8, 1.2))
                else:
                    px, py = cy(x, rng.uniform(2.0, 6.5))
                    for m in range(3):
                        pf = kit.instance(sand_src, f"S30Sand{i}_{vf}_{k}_{m}", c, (px, py, H(px, py)), scale=0.0)
                        kit.animate_puff(pf, t + m, end, (px + rng.uniform(-0.6, 0.6), py + rng.uniform(-0.6, 0.6),
                                                          H(px, py) + 0.3),
                                         (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(2.5, 4.5)), s0=0.3,
                                         s1=rng.uniform(1.0, 1.6), grow=8.0, drag=2.2, step=4,
                                         fade=(t + 30, t + 70))
    # villagers run inland from the beach when the shot starts to fall
    run0 = ev["volleys"][0][0] + 20
    for i, (x0, d0, x1, d1) in enumerate(((-4, 4, -10, 22), (3, 5, 0, 24), (9, 3, 14, 23), (-14, 6, -20, 25),
                                          (18, 4, 24, 22), (-8, 7, -2, 26), (12, 6, 6, 24))):
        root, parts = kit.make_villager(f"S30Runner{i}", c, seed=40 + i, robe=i % 3 == 0,
                                        cloth=("cloth_w", "cloth_t", "cloth_r")[i % 3])
        a, b = cy(x0, d0), cy(x1, d1)
        kit.animate_route(root, parts, [(f0, run0 + 3 * i, a, a), (run0 + 3 * i, run0 + 3 * i + 170, a, b)], H,
                          stride_frames=9, swing=0.7, lean=0.18)
    return ships


# ===================================================================== S31
def build_s31(c, lib, ev, fleet):
    """Seven ships at anchor; longboats row in; soldiers wade ashore and form up (K38)."""
    rng = random.Random(31)
    end = ev["end"]
    f0, f1 = ev["r31"]
    wade = ev["wade"]
    walker_tpl = []
    for k in range(3):
        root, parts = kit.make_walker(f"LibWader{k}", lib, "dutch", seed=80 + k)
        root.location = (0, 0, -500)
        for p in parts.values():
            p.hide_render = True
        walker_tpl.append(parts)
    dutch = [kit.make_figure(f"LibLDutch{k}", lib, "dutch", seed=k) for k in range(3)]
    for ob in dutch:
        kit.hide_source(ob)
    # formed-up blocks on the sand, facing inland
    blocks = [(70.0, 9.0, 6, 5), (88.0, 10.5, 5, 5), (54.0, 7.0, 6, 4), (104.0, 11.0, 4, 4)]
    n = 0
    slots = []
    for bx, bd, cols, ranks in blocks:
        cx, cyy = cy(bx, bd)
        for r in range(ranks):
            for k in range(cols):
                u = (k - (cols - 1) / 2) * 1.15
                v = (r - (ranks - 1) / 2) * 1.25
                x = cx + u * 0.958 + v * 0.287 + rng.uniform(-0.1, 0.1)
                y = cyy + u * -0.287 + v * 0.958 + rng.uniform(-0.1, 0.1)
                ob = kit.instance(dutch[n % 3], f"S31Rank{n}", c, (x, y, H(x, y) - 0.02),
                                  rot_z=_face(0.287, 0.958) + rng.uniform(-0.08, 0.08))
                kit.animate_idle(ob, rng, 1, end, amount=0.02)
                n += 1
        # the next free slots at the back of each block, for the men coming up the beach
        for k in range(cols):
            u = (k - (cols - 1) / 2) * 1.15
            v = -((ranks + 1) / 2) * 1.25
            slots.append((cx + u * 0.958 + v * 0.287, cyy + u * -0.287 + v * 0.958))
    # unloaded stores at the top of the wet sand: crates, barrels, two guns
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    cannon = bpy.data.objects.get("LibCannon") or kit.make_cannon("LibCannon", lib)
    kit.hide_source(cannon)
    for pi, (px_, pd) in enumerate(((62.0, 3.0), (79.0, 2.5), (96.0, 3.5))):
        cx, cyy = cy(px_, pd)
        for k in range(9):
            x, y = cx + rng.uniform(-1.8, 1.8), cyy + rng.uniform(-1.2, 1.2)
            src = barrel if k % 4 == 3 else crate
            z = H(x, y) - 0.02 + (0.75 if k in (2, 6) else 0.0)
            kit.instance(src, f"S31Store{pi}_{k}", c, (x, y, z), rot_z=rng.uniform(0, 1.5))
        if pi < 2:
            x, y = cx + 3.0, cyy + 0.5
            kit.instance(cannon, f"S31Gun{pi}", c, (x, y, H(x, y) - 0.03), rot_z=_face(0.287, 0.958) + 0.3)
    # longboats: a stream from the ships to the beach
    boats = []
    for i in range(32):
        ship = fleet[(i * 3) % len(fleet)]
        sx, sy = ship.location.x, ship.location.y
        if i < 16:      # the boats that ground: one every ~5.5 m, in a shuffled order
            bx = 42 + 84.0 * ((i * 7) % 16) / 15.0 + rng.uniform(-0.6, 0.6)
        else:           # the rest are still out in the bay
            bx = 44 + 80.0 * ((i * 11) % 32) / 31.0 + rng.uniform(-1.5, 1.5)
        p1 = cy(bx, -2.2)
        side = rng.choice((-1, 1))
        p0 = (sx + side * rng.uniform(6, 12), sy + rng.uniform(6, 14))
        dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        dur = int(dist / 1.9 * kit.FPS)
        # a few already ashore, some grounding while the men wade in, the rest still pulling across the bay
        if i < 5:
            arrive = f0 - 220 + i * 38
        elif i < 11:
            arrive = wade[0] - 30 + (i - 5) * 22
        else:
            arrive = f0 + 150 + (i - 11) * 40
        arrive += rng.randint(-10, 10)
        start = arrive - dur
        boat, oars = kit.make_troop_boat(f"S31Boat{i}", c, seed=i, rows=3, standing=1 + (i % 2))
        kit.animate_boat_path(boat, start, arrive, p0, p1, end, z=-0.3, seed=i, beach_z=-0.42)
        kit.animate_oars(oars, max(1, start), arrive, period=34 + i % 5, phase=i % 7)
        boats.append((boat, p0, p1, arrive))
    # soldiers wading ashore from the boats that have landed, up to their places
    w = 0
    for bi, (boat, p0, p1, arrive) in enumerate(boats):
        if not (f0 - 140 < arrive < wade[1]):
            continue
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        for k in range(3):
            if not slots:
                break
            sx, sy = slots.pop(rng.randrange(len(slots)))
            sx, sy = sx + rng.uniform(-1.2, 1.2), sy + rng.uniform(-1.0, 1.0)
            a = (p1[0] + dx / L * 3.0 + rng.uniform(-1.6, 1.6), p1[1] + dy / L * 3.0 + rng.uniform(-1.2, 1.2))
            t0 = max(arrive + 8, wade[0]) + k * 26 + rng.randint(0, 30)
            dist = math.hypot(sx - a[0], sy - a[1])
            t1 = t0 + int(dist / 1.05 * kit.FPS)
            root, parts = kit.clone_walker(walker_tpl[w % 3], f"S31Wader{w}", c)
            kit.animate_route(root, parts, [(t0, t1, a, (sx, sy))], H, stride_frames=15, swing=0.4,
                              heading=_face(dx, dy))
            root.scale = (0, 0, 0)
            root.keyframe_insert("scale", frame=t0 - 1)
            root.scale = (1, 1, 1)
            root.keyframe_insert("scale", frame=t0)
            w += 1
    # carriers bring the stores up from the beached boats
    for i in range(8):
        load = ("crate", "crate", "sack")[i % 3]
        root, parts = kit.make_carrier(f"S31Carrier{i}", c, load=load, seed=90 + i)
        x = rng.uniform(55, 100)
        a, b = cy(x, -0.5), cy(x + rng.uniform(-6, 6), rng.uniform(2.5, 5.0))
        t0 = f0 + rng.randint(-40, 120)
        kit.animate_route(root, parts, [(t0, t0 + int(math.hypot(b[0] - a[0], b[1] - a[1]) / 1.0 * kit.FPS), a, b)],
                          H, stride_frames=15, swing=0.35)
        kit.fix_carry_arms(parts, load)
    # officers walking the line
    for i, (x0, x1) in enumerate(((60, 76), (94, 82))):
        root, parts = kit.make_walker(f"S31Officer{i}", c, "dutch", seed=95 + i)
        kit.animate_route(root, parts, [(f0 - 30, f1, cy(x0, 12.5), cy(x1, 13.5))], H, stride_frames=16, swing=0.35)
    return boats


# ===================================================================== beach camp (S32-S38)
def make_log_pile(name, c, rng, n=9, lie=0.0):
    """Stack of sharpened stockade posts lying on the sand (K39, K41)."""
    mb = kit.MB()
    k = 0
    layer = 0
    while k < n:
        row = max(1, 4 - layer)
        for j in range(row):
            if k >= n:
                break
            y = (j - (row - 1) / 2) * 0.46
            z = 0.22 + layer * 0.4
            L = rng.uniform(3.6, 4.3)
            x0 = rng.uniform(-0.3, 0.3)
            mb.seg((x0 - L / 2, y, z), (x0 + L / 2, y, z), 0.22, 0.21, "log", sides=6, spin=rng.uniform(0, 1))
            mb.seg((x0 + L / 2, y, z), (x0 + L / 2 + 0.6, y, z), 0.21, 0.02, "log_end", sides=6)
            mb.cone(kit.T(x0 - L / 2 - 0.01, y, z) @ kit.Ry(math.pi / 2), "log_end", segments=6, r1=0.2, r2=0.2,
                    depth=0.02)
            k += 1
        layer += 1
    return mb.obj(name, c)


def build_beach_camp(c, lib, ev):
    """Stores, beached boats and piles of posts round the stockade site (S32 on)."""
    rng = random.Random(32)
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    sack = bpy.data.objects.get("LibSack") or kit.make_sack("LibSack", lib)
    kit.hide_source(sack)
    cannon = bpy.data.objects.get("LibCannon") or kit.make_cannon("LibCannon", lib)
    kit.hide_source(cannon)
    piles = []
    for i, (u, v, rz) in enumerate(((-18.5, -7.0, 0.1), (-19.0, 3.0, -0.2), (6.0, -15.0, 1.5), (18.5, -6.0, 0.3),
                                    (18.0, 5.0, -0.1), (-6.0, 15.5, 1.6))):
        x, y = SW(u, v)
        pile = make_log_pile(f"LogPile{i}", c, rng, n=rng.randint(7, 10))
        pile.location = (x, y, H(x, y) - 0.05)
        pile.rotation_euler[2] = math.radians(ST_AXIS) + rz
        piles.append((x, y))
    # piles beside De Lannoy (S32 foreground, K39): low and to the sides, so the camera sees over them
    for i, (a, b, rz) in enumerate(((4.6, 1.2, 0.15), (-6.0, 0.4, -0.2))):
        x, y = DL_POS[0] + TX * a + NX * b, DL_POS[1] + TY * a + NY * b
        pile = make_log_pile(f"DLPile{i}", c, rng, n=6)
        pile.location = (x, y, H(x, y) - 0.05)
        pile.rotation_euler[2] = math.radians(ST_AXIS) + rz
    # crate stacks, barrels and sacks
    for i, (u, v) in enumerate(((-17.0, -11.0), (-16.0, 8.0), (16.5, -10.0), (-9.5, -15.0), (12.0, -14.5))):
        cx, cyy = SW(u, v)
        for k in range(8):
            x, y = cx + rng.uniform(-1.6, 1.6), cyy + rng.uniform(-1.6, 1.6)
            src = (crate, crate, barrel, sack)[k % 4]
            z = H(x, y) - 0.02 + (0.76 if k == 4 and src is crate else 0.0)
            kit.instance(src, f"CampStore{i}_{k}", c, (x, y, z), rot_z=rng.uniform(0, 1.5))
    for i, (u, v) in enumerate(((-12.0, -16.0), (14.0, -16.5))):
        x, y = SW(u, v)
        kit.instance(cannon, f"CampGun{i}", c, (x, y, H(x, y) - 0.03), rot_z=math.radians(ST_AXIS) + math.pi + 0.2 * i)
    # the longboats pulled up at the waterline
    hull = bpy.data.objects.get("LibTroopBoatHull")
    for i, x in enumerate((36.0, 41.5, 46.0, 58.5, 63.0, 71.0, 76.5)):
        px, py = cy(x, rng.uniform(-0.8, 0.6))
        kit.instance(hull, f"BeachedBoat{i}", c, (px, py, max(H(px, py), -0.3) - 0.12),
                     rot_z=_face(0.287, 0.958) + rng.uniform(-0.35, 0.35))
    return piles


ST_AXIS = cw.STOCKADE["axis_deg"]
S32_PALMS = ((52.4, 3.2), (40.0, 6.0))


def make_plank_stack(name, lib):
    """A few sawn planks lying together (K39 foreground)."""
    mb = kit.MB()
    for k in range(4):
        mb.box(kit.T(0.0, (k - 1.5) * 0.32, 0.08 + 0.02 * (k % 2)) @ kit.S(2.6, 0.28, 0.1), "plank")
    mb.box(kit.T(0.2, 0.0, 0.28) @ kit.S(2.4, 0.3, 0.1), "plank")
    return mb.obj(name, lib)


def make_rope_coil(name, lib):
    """A coiled rope on the sand: two rings of short segments."""
    mb = kit.MB()
    for r, z in ((0.5, 0.06), (0.4, 0.15)):
        n = 12
        for k in range(n):
            a0, a1 = math.tau * k / n, math.tau * (k + 1) / n
            mb.seg((r * math.cos(a0), r * math.sin(a0), z), (r * math.cos(a1), r * math.sin(a1), z), 0.07, 0.07, "cloth_t",
                   sides=5)
    return mb.obj(name, lib)


def make_tuft(name, lib):
    """A little tuft of beach grass: a few thin faceted blades."""
    mb = kit.MB()
    rng = random.Random(5)
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(-0.3, 0.3)
        h = rng.uniform(0.35, 0.6)
        mb.seg((0.05 * math.cos(a), 0.05 * math.sin(a), 0.0), (0.22 * math.cos(a), 0.22 * math.sin(a), h), 0.035, 0.005,
               "frond", sides=3)
    return mb.obj(name, lib)


# ===================================================================== S32
def sq(x):
    """Squeeze the S32 crowd toward De Lannoy: the camera only sees a few metres either side of him."""
    return DL_POS[0] + (x - DL_POS[0]) * 0.8


def build_s32(c, lib, ev):
    """De Lannoy on the beach, pointing out the line of the stockade (K39)."""
    rng = random.Random(132)
    end = ev["end"]
    f0, f1 = ev["r32"]
    x, y = DL_POS
    root, parts = kit.make_delannoy("DeLannoy", c)
    root.location = (x, y, H(x, y) - 0.02)
    root.rotation_euler[2] = _face(0.287, 0.958) - 0.25          # faces inland, toward the camera
    kit.key_pose(parts, f0, kit.ARM_REST)
    kit.key_pose(parts, ev["point"] - 10, kit.ARM_REST)
    kit.key_pose(parts, ev["point"], kit.DELANNOY_POINT)
    kit.animate_rig_idle(parts, rng, f0, ev["point"] - 20, body=0.012, head=0.12)
    parts["head"].rotation_euler = (0, 0, 0)
    parts["head"].keyframe_insert("rotation_euler", frame=ev["point"] - 14)
    parts["head"].rotation_euler = (-0.12, 0, -0.6)                       # looks where he points
    parts["head"].keyframe_insert("rotation_euler", frame=ev["point"] + 4)
    # soldiers carrying posts and crates up from the boats, others standing by the stores
    # (they keep clear of the camera, which looks seaward at him from a few metres inland)
    for i, (xa, da, xb, db, load, t) in enumerate((
            (44.0, -0.5, 44.5, 7.5, "post", -60), (57.0, -0.6, 57.5, 7.0, "post", -150),
            (46.0, -0.6, 43.0, 6.0, "crate", -20), (59.0, -0.4, 60.0, 8.0, "crate", -110),
            (41.0, -0.5, 41.5, 8.5, "post", 40), (55.5, -0.4, 58.5, 6.5, "crate", 60),
            (61.5, -0.5, 62.0, 8.5, "post", -200), (38.5, -0.6, 40.0, 7.0, "crate", -90),
            (47.5, -0.5, 45.5, 5.0, "sack", 0), (63.5, -0.3, 64.0, 7.0, "sack", 100))):
        root_c, parts_c = kit.make_carrier(f"S32Carrier{i}", c, load=load, seed=200 + i)
        a, b = cy(sq(xa), da), cy(sq(xb), db)
        t0 = f0 + t
        dur = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.95 * kit.FPS)
        kit.animate_route(root_c, parts_c, [(t0, t0 + dur, a, b)], H, stride_frames=16, swing=0.35)
        kit.fix_carry_arms(parts_c, load)
    # and others crossing behind him along the beach (K39 mid-ground)
    for i, (xa, xb, dd, load, t) in enumerate(((43.0, 57.0, 3.2, "post", -40), (58.0, 45.0, 2.4, "crate", 30),
                                               (41.0, 55.0, 1.6, "post", 150), (60.0, 47.0, 3.8, "sack", 220))):
        root_c, parts_c = kit.make_carrier(f"S32Crosser{i}", c, load=load, seed=230 + i)
        a, b = cy(sq(xa), dd), cy(sq(xb), dd)
        t0 = f0 + t
        kit.animate_route(root_c, parts_c, [(t0, t0 + int(abs(sq(xb) - sq(xa)) / 0.9 * kit.FPS), a, b)], H, stride_frames=16,
                          swing=0.35)
        kit.fix_carry_arms(parts_c, load)
    dutch = [bpy.data.objects[f"LibLDutch{k}"] for k in range(3)]
    for i, (f, l, look) in enumerate(((3.0, -3.4, 1.0), (4.2, 2.8, 2.6), (7.0, -1.2, 3.0), (5.6, 5.2, 0.5),
                                      (8.5, 3.2, 2.2), (6.6, -5.2, 3.4), (10.0, -3.0, 1.4))):
        px, py = DL_POS[0] - NX * f + TX * l, DL_POS[1] - NY * f + TY * l
        ob = kit.instance(dutch[i % 3], f"S32Soldier{i}", c, (px, py, H(px, py) - 0.02), rot_z=look)
        kit.animate_idle(ob, rng, 1, end, amount=0.03)
    # palms still standing on the stockade site (cut for posts by S34: stumps there later)
    palms = [bpy.data.objects[f"LibPalm{i}"] for i in range(6)]
    for i, (xx, dd) in enumerate(S32_PALMS):
        px, py = cy(xx, dd)
        kit.instance(palms[(i + 2) % 6], f"S32Palm{i}", c, (px, py, H(px, py) - 0.1), rot_z=rng.uniform(0, 6.28),
                     scale=rng.uniform(0.95, 1.1))
    # a big leaning palm at the left of the frame and others behind him (K39), clear of the camera path
    x0, y0 = DL_POS
    for i, (a, b, sc) in enumerate(((16.0, -9.0, 1.15), (-17.0, -12.0, 1.05), (-24.0, -18.0, 1.1), (24.0, -16.0, 1.0))):
        px, py = x0 + TX * a + NX * b, y0 + TY * a + NY * b
        kit.instance(palms[(i + 4) % 6], f"DLPalm{i}", c, (px, py, H(px, py) - 0.1), rot_z=rng.uniform(0, 6.28),
                     scale=sc)
    # a young palm leaning in from the left with its leaves in frame, and K39's foreground clutter
    from mathutils import Matrix
    px, py = x0 + TX * 5.0 - NX * 5.5, y0 + TY * 5.0 - NY * 5.5
    palm = kit.instance(palms[2], "DLPalmLean", c, (px, py, H(px, py) - 0.1), rot_z=0.0, scale=0.62)
    dx, dy = x0 - px, y0 - py
    ln = math.hypot(dx, dy)
    palm.rotation_euler = Matrix.Rotation(0.45, 4, (-dy / ln, dx / ln, 0.0)).to_euler()
    plank = bpy.data.objects.get("LibPlankStack") or make_plank_stack("LibPlankStack", lib)
    rope = bpy.data.objects.get("LibRope") or make_rope_coil("LibRope", lib)
    tuft = bpy.data.objects.get("LibTuft") or make_tuft("LibTuft", lib)
    sack_s = bpy.data.objects.get("LibSack") or kit.make_sack("LibSack", lib)
    for ob in (plank, rope, tuft, sack_s):
        kit.hide_source(ob)
    crate_s, barrel_s = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    for i, (a, b, kind, rz) in enumerate((
            (2.5, -1.4, "crate", 0.3), (3.2, -1.1, "crate", 0.9), (2.8, -1.3, "crate_top", 0.5), (3.7, -0.3, "barrel", 0.0),
            (2.0, -0.2, "sack", 0.4), (1.5, 0.7, "rope", 0.0), (-2.4, -1.6, "crate", 0.2), (-3.0, -1.2, "barrel", 0.0),
            (-1.8, -0.7, "rope", 1.0), (-2.2, 0.8, "sack", 1.2), (3.3, 3.0, "plank", 0.2), (-1.5, 3.4, "tuft", 0.0),
            (1.9, 3.8, "tuft", 1.0), (-5.0, 3.0, "tuft", 2.0), (4.6, 3.6, "tuft", 0.5), (0.8, 2.2, "tuft", 1.6),
            (-2.2, 1.6, "tuft", 2.6), (2.9, 1.2, "tuft", 0.7), (-0.6, 1.2, "tuft", 0.3), (1.2, -0.8, "tuft", 1.9))):
        sx, sy = x0 + TX * a + NX * b, y0 + TY * a + NY * b
        src = {"crate": crate_s, "crate_top": crate_s, "barrel": barrel_s, "sack": sack_s, "rope": rope,
               "plank": plank, "tuft": tuft}[kind]
        z = H(sx, sy) - 0.02 + (0.76 if kind == "crate_top" else 0.0)
        kit.instance(src, f"S32Fg{i}", c, (sx, sy, z), rot_z=rz)
    # the ships are far out on the horizon in K39: three small ones instead of the anchored fleet
    for i, (a, b, rot, L) in enumerate(((10.0, -300.0, 236.0, 40.0), (95.0, -365.0, 70.0, 38.0),
                                        (150.0, -420.0, 250.0, 41.0))):
        ship = make_sailing_ship(f"S32Ship{i}", c, L, 9.5 + 0.12 * (L - 36), {0: (1,), 1: (1, 2), 2: (1,)}, 0.8, 60 + i)
        sx, sy = x0 + TX * a + NX * b, y0 + TY * a + NY * b
        ship.location = (sx, sy, -0.4)
        rz = math.radians(rot)
        ship.rotation_euler = (0, 0, rz)
        pw.rock(ship, end, (0, 0, rz), -0.4, amp=(0.5, 0.8), bob=0.1, seed=60 + i)
    crate = bpy.data.objects["LibCrate"]
    for i, (xx, dd) in enumerate(((46.6, 8.6), (47.2, 9.2), (46.9, 8.9), (55.0, 5.0), (55.6, 4.6))):
        px, py = cy(xx, dd)
        kit.instance(crate, f"S32Crate{i}", c, (px, py, H(px, py) - 0.02 + (0.76 if i == 2 else 0.0)),
                     rot_z=rng.uniform(0, 1.0))
    # two men in a beached boat handing out crates
    hull = bpy.data.objects.get("LibTroopBoatHull")
    for i, xx in enumerate((52.0,)):
        px, py = cy(xx, -1.6)
        boat = kit.instance(hull, f"S32Boat{i}", c, (px, py, max(H(px, py), -0.3) - 0.1),
                            rot_z=_face(0.287, 0.958) + 0.2)
        for k, (lx, ly) in enumerate(((0.3, 0.8), (-0.3, -1.4))):
            fig = kit.instance(dutch[k], f"S32BoatMan{k}", c, (lx, ly, 0.15), rot_z=0.4 * k)
            fig.parent = boat
            kit.animate_idle(fig, rng, 1, end, amount=0.04)
    return root, parts


# ===================================================================== S34
def build_stockade(c, lib, ev, full=False):
    """The stockade wall goes up post by post (S34) and stands half-built (S38); full=True: the
    finished wall, standing from frame 1 (the siege, S40 on)."""
    t0, t1 = ev["build"]
    pre = (0.42, 0.3, 0.22, 0.34)                  # built when S34 opens: seaward, east, inland, west walls
    done = (0.92, 0.72, 0.55, 0.78)                # built when S34 ends (S38 shows this)

    def plant(side, s, L):
        if full:
            return -200
        q = s / L
        if side == 3:
            q = 1 - q                              # the west wall is built from the seaward corner
        if q <= pre[side]:
            return t0 - 40
        if q <= done[side]:
            return t0 + int((q - pre[side]) / (done[side] - pre[side]) * (t1 - t0))
        return None
    st = cw.STOCKADE
    posts = kit.build_stockade_rise("Stockade", c, st["center"], st["axis_deg"], st["half_u"], st["half_v"], H, plant,
                                    gate=3.5, seed=3)
    # tents, stores and the flag inside
    rng = random.Random(341)
    cone = [kit.make_cone_tent(f"LibLConeTent{i}", lib, r=1.9 + 0.3 * i, h=3.0 + 0.4 * i) for i in range(2)]
    ridge = kit.make_ridge_tent("LibLRidgeTent", lib)
    for ob in cone + [ridge]:
        kit.hide_source(ob)
    axis = math.radians(st["axis_deg"])
    for i, (src, u, v, rz) in enumerate(((cone[0], -8.0, 5.0, 0.2), (cone[1], -2.5, 7.0, -0.3),
                                         (cone[0], 7.5, 6.0, 0.5), (ridge, 10.5, -3.0, 1.57), (ridge, -10.0, -4.5, 1.4),
                                         (cone[1], 3.0, -6.5, 0.0))):
        x, y = SW(u, v)
        kit.instance(src, f"StockadeTent{i}", c, (x, y, H(x, y) - 0.03), rot_z=axis + rz)
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    sack = bpy.data.objects["LibSack"]
    for i, (u, v) in enumerate(((-4.0, 1.0), (4.5, 1.5), (0.5, 9.0), (-11.0, 8.5))):
        cx, cyy = SW(u, v)
        for k in range(7):
            x, y = cx + rng.uniform(-1.4, 1.4), cyy + rng.uniform(-1.4, 1.4)
            src = (crate, barrel, crate, sack)[k % 4]
            kit.instance(src, f"StockadeStore{i}_{k}", c, (x, y, H(x, y) - 0.02), rot_z=rng.uniform(0, 1.5))
    stump = bpy.data.objects["LibStump"]
    for i, (xx, dd) in enumerate(S32_PALMS):
        px, py = cy(xx, dd)
        kit.instance(stump, f"PalmStump{i}", c, (px, py, H(px, py) - 0.05), scale=1.2)
    x, y = SW(-9.5, 9.0)
    pw.flag_on_pole(c, "StockadeFlag", (x, y, H(x, y)), 8.5, 2.6, 1.6, "flag_o", heading=150)
    return posts


def build_s34(c, lib, ev):
    """Builders at the wall, the column marching inland, smoke over the fallen villages (K41)."""
    rng = random.Random(34)
    end = ev["end"]
    f0, f1 = ev["r34"]
    st = cw.STOCKADE
    dutch = [bpy.data.objects[f"LibLDutch{k}"] for k in range(3)]
    # men at the working ends of the walls: holding posts, ramming them in, carrying more
    sides = [((-st["half_u"], -st["half_v"]), (1, 0), 0.67), ((st["half_u"], -st["half_v"]), (0, 1), 0.51),
             ((st["half_u"], st["half_v"]), (-1, 0), 0.38), ((-st["half_u"], -st["half_v"]), (0, 1), 0.44)]
    for si, ((u0, v0), (du, dv), q) in enumerate(sides):
        L = 2 * (st["half_u"] if du else st["half_v"])
        u, v = u0 + du * L * q, v0 + dv * L * q
        for k, (au, av) in enumerate(((dv * 1.6, du * 1.6), (dv * 1.4 + du * 1.2, du * 1.4 + dv * 1.2),
                                      (dv * 2.8 - du * 0.8, du * 2.8 - dv * 0.8))):
            uu, vv = u + au * (1 if si != 3 else -1), v + av
            x, y = SW(uu, vv)
            wx, wy = SW(u, v)
            ob = kit.instance(dutch[(si + k) % 3], f"S34Builder{si}_{k}", c, (x, y, H(x, y) - 0.02),
                              rot_z=_face(wx - x, wy - y))
            if k == 1:
                kit.animate_bob(ob, rng, f0 - 10, f1, height=0.1, period=(16, 22), sway=0.08)
            else:
                kit.animate_idle(ob, rng, f0 - 10, f1, amount=0.04)
    for i in range(8):
        load = "post" if i % 3 else "crate"
        root, parts = kit.make_carrier(f"S34Carrier{i}", c, load=load, seed=300 + i)
        pu, pv = ((-18.5, -7.0), (-19.0, 3.0), (18.5, -6.0), (18.0, 5.0))[i % 4]
        tu, tv = ((-13.5, -9.0), (-13.0, 1.0), (13.0, -4.0), (12.5, 5.5))[i % 4]
        a, b = SW(pu + rng.uniform(-1, 1), pv + rng.uniform(-1, 1)), SW(tu + rng.uniform(-1, 1), tv + rng.uniform(-1, 1))
        t0 = f0 - 40 + i * 20
        kit.animate_route(root, parts, [(t0, t0 + int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.9 * kit.FPS), a, b)],
                          H, stride_frames=16, swing=0.35)
        kit.fix_carry_arms(parts, load)
    # the column: out of the gate and up the track, three abreast
    tpl = []
    for k in range(3):
        root, parts = kit.make_walker(f"LibMarcher{k}", lib, "dutch", seed=120 + k)
        root.location = (0, 0, -500)
        for p in parts.values():
            p.hide_render = True
        tpl.append(parts)
    speed = 1.7
    n = 0
    t_go = ev["march"]                      # "Then they march inland.": they stand at the gate until then

    def march(name, s_start, t_start, ranks, files=3, spacing=1.45):
        nonlocal n
        for r in range(ranks):
            for fl in range(files):
                root, parts = kit.clone_walker(tpl[n % 3], f"{name}{n}", c)
                lat = (fl - (files - 1) / 2) * 1.05
                s0 = s_start - r * spacing
                s1 = s0 + speed * (f1 + 6 - t_start) / kit.FPS
                wps = []
                s = s0
                while True:
                    (px, py), (dx, dy) = path_point(min(s, s1))
                    wps.append((px - dy * lat, py + dx * lat))
                    if s >= s1:
                        break
                    s += 3.0
                kit.animate_walk(root, parts, wps, H, start=t_start + (r * 3 + fl) % 5, end=f1 + 6,
                                 stride_frames=14, swing=0.42)
                n += 1
    march("S34March", 4.0, t_go, 9)
    march("S34Vanguard", 60.0, t_go - 100, 4)
    # one village after another falls: fire in the huts, smoke rolling up and away inland
    flames_src = [kit.make_flames(f"LibLFlames{k}", lib, seed=k, size=1.1) for k in range(2)]
    puffs = [kit.make_puff(f"LibLSmoke{k}", lib, seed=50 + k, m=("smoke_md", "smoke_md", "smoke_dk")[k])
             for k in range(3)]
    for ob in flames_src + puffs:
        kit.hide_source(ob)
    for hi, (hx, hy) in enumerate(hamlet_centres()):
        t = ev["falls"][hi]
        for col in range(3):
            bx, by = hx + rng.uniform(-6, 6), hy + rng.uniform(-6, 6)
            fl = kit.instance(flames_src[col % 2], f"S34Fire{hi}_{col}", c, (bx, by, H(bx, by) + 0.4), scale=0.0)
            fl.keyframe_insert("scale", frame=t + col * 6 - 1)
            fl.scale = (1.3, 1.3, 1.3)
            fl.keyframe_insert("scale", frame=t + col * 6 + 8)
            kit.animate_flicker(fl, rng, t + col * 6 + 10, f1)
            for k in range(26):
                born = t + col * 6 + k * 5
                if born > f1:
                    break
                ob = kit.instance(puffs[k % 3 if k % 2 else 1], f"S34Smoke{hi}_{col}_{k}", c, (bx, by, 0), scale=0.0)
                ob.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
                kit.animate_puff(ob, born, f1, (bx + rng.uniform(-0.5, 0.5), by + rng.uniform(-0.5, 0.5),
                                                H(bx, by) + 2.5),
                                 (1.2 + rng.uniform(-0.3, 0.3), 0.8 + rng.uniform(-0.3, 0.3), 5.2 + rng.uniform(-0.6, 0.8)),
                                 s0=0.5, s1=rng.uniform(1.4, 2.1), grow=50.0, step=6)


# ===================================================================== S38
def build_s38(c, lib, ev):
    """The monsoon: surf running up the beach, a ship pitching far out, men sheltering."""
    rng = random.Random(38)
    end = ev["end"]
    f0, f1 = ev["r38"]
    full = ev["storm"][1][0]
    # breakers: rows of surf rolling in along the beach in front of the stockade, again and again,
    # growing as the storm arrives
    src = [kit.make_breaker(f"LibBreaker{k}", lib, length=13.0 + 3 * k, seed=k, h=0.9 + 0.2 * k) for k in range(3)]
    for ob in src:
        kit.hide_source(ob)

    def grow(f):
        return min(1.0, max(0.0, (f - f0) / max(1, full - f0)))
    k = 0
    for lane, x in enumerate(range(4, 132, 10)):
        f = f0 + rng.randint(-30, 20)
        while f < f1 + 20:
            x0 = x + rng.uniform(-2, 2)
            p_from, p_to = cy(x0, -16.0), cy(x0, 3.0)
            sz = 0.7 + 0.6 * grow(f + 35)
            ob = kit.instance(src[k % 3], f"S38Surf{k}", c, (*p_from, 0.0), scale=0.0)
            kit.animate_surge(ob, f, f + 62, p_from, p_to, z_from=0.0, z_to=H(*p_to) + 0.05, size=sz * rng.uniform(0.9, 1.2),
                              heading=math.radians(ST_AXIS))
            f += rng.randint(32, 46)
            k += 1
    # one ship far out, pitching hard, unable to come in
    ship = make_sailing_ship("S38Ship", c, 40.0, 10.0, {}, 0.6, 77)
    x, y = 30.0, SY(30.0) - 240.0
    ship.location = (x, y, -0.4)
    rz = math.radians(235)
    f = 1
    s = 1
    while f <= end + 40:
        ship.rotation_euler = (math.radians(7.5 * s), math.radians(4.0 * -s), rz)
        ship.location.z = -0.4 + 1.3 * s
        ship.keyframe_insert("rotation_euler", frame=f)
        ship.keyframe_insert("location", frame=f)
        f += rng.randint(28, 40)
        s = -s
    # sentries standing out the rain at the gate and by the tents
    dutch = [bpy.data.objects[f"LibLDutch{k}"] for k in range(3)]
    for i, (u, v, rz2) in enumerate(((-2.6, 13.0, 0.0), (2.6, 13.0, 0.0), (-6.0, 3.0, 2.0), (6.5, 4.0, 3.5))):
        x, y = SW(u, v)
        ob = kit.instance(dutch[i % 3], f"S38Sentry{i}", c, (x, y, H(x, y) - 0.02),
                          rot_z=math.radians(ST_AXIS) + rz2)
        kit.animate_idle(ob, rng, 1, end, amount=0.03)


def sway_palms(f0, f1, near, radius, rng, amount=0.17):
    """Palms bend and whip in the monsoon wind (S38): keys only inside f0..f1."""
    for ob in bpy.data.objects:
        if not (ob.name.startswith("Palm") or ob.name.startswith("GrovePalm")):
            continue
        if math.hypot(ob.location.x - near[0], ob.location.y - near[1]) > radius:
            continue
        base = ob.rotation_euler.copy()
        ob.keyframe_insert("rotation_euler", frame=f0)
        f = f0 + 30
        ph = rng.uniform(0, 6)
        while f <= f1:
            k = min(1.0, (f - f0) / 170.0)
            ob.rotation_euler = (base.x + amount * k * (0.6 + 0.4 * math.sin(f / 7.0 + ph)),
                                 base.y - amount * 0.7 * k * (0.6 + 0.4 * math.sin(f / 9.0 + ph)), base.z)
            ob.keyframe_insert("rotation_euler", frame=f)
            f += rng.randint(9, 14)


# ===================================================================== clear light at sea (S30-S31)
def sea_light(sun, f_last, sun_dir=(-0.72, 0.45, -0.32), haze=0.00028, spec=0.2, rough=0.45, sat=1.45, sky_last=None):
    """The two open-sea beats look west along the coast, straight into the default low sun, so
    haze and sun glare wash the water out. Up to f_last only: the sun comes from behind the
    camera's left, the haze is thinner and the sea is less glossy, so the facets read
    turquoise-to-blue (K37, K38). From f_last + 1 (the cut to S32) everything is as before."""
    from mathutils import Vector
    base_rot = sun.rotation_euler.copy()
    sun.rotation_euler = Vector(sun_dir).normalized().to_track_quat("-Z", "Y").to_euler()
    sun.keyframe_insert("rotation_euler", frame=1)
    sun.keyframe_insert("rotation_euler", frame=f_last)
    sun.rotation_euler = base_rot
    sun.keyframe_insert("rotation_euler", frame=f_last + 1)
    vol = next(n for n in bpy.data.objects["Haze"].data.materials[0].node_tree.nodes
               if n.bl_idname == "ShaderNodeVolumePrincipled")
    dens = vol.inputs["Density"]
    normal = 0.0008                                    # colachel_world's clear-weather density
    bsdf = bpy.data.materials["Sea"].node_tree.nodes.get("Principled BSDF")
    sp, ro = bsdf.inputs["Specular IOR Level"], bsdf.inputs["Roughness"]
    for sock, low, high in ((dens, haze, normal), (sp, spec, sp.default_value), (ro, rough, ro.default_value)):
        sock.default_value = low
        sock.keyframe_insert("default_value", frame=1)
        sock.keyframe_insert("default_value", frame=f_last)
        sock.default_value = high
        sock.keyframe_insert("default_value", frame=f_last + 1)
    # deeper turquoise-to-blue facets: a saturation lift on the sea colour, these beats only
    nt = bpy.data.materials["Sea"].node_tree
    mix = nt.nodes["StormMix"]
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    out = next(sk for sk in mix.outputs if sk.identifier == "Result_Color")
    nt.links.new(out, hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    sat_in = hsv.inputs["Saturation"]
    sat_in.default_value = sat
    sat_in.keyframe_insert("default_value", frame=1)
    sat_in.keyframe_insert("default_value", frame=f_last)
    sat_in.default_value = 1.0
    sat_in.keyframe_insert("default_value", frame=f_last + 1)
    # muzzle flashes (S30 only): a saturated orange glow instead of a pale, washed-out pink
    for name, rgb, k in (("muzzle_core", (1.0, 0.62, 0.02), 1.5), ("muzzle_fire", (1.0, 0.26, 0.0), 1.3)):
        m = bpy.data.materials.get(name)
        if m:
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Emission Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
            b.inputs["Emission Strength"].default_value = k
            b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
    # a bluer sky above a warm cream horizon (K37, K38), at sea only
    wnt = bpy.context.scene.world.node_tree
    sky_last = sky_last or f_last
    ramp = next(n for n in wnt.nodes if n.bl_idname == "ShaderNodeValToRGB").color_ramp
    bg = next(n for n in wnt.nodes if n.bl_idname == "ShaderNodeBackground").inputs["Strength"]
    for el, rgb, pos in zip(ramp.elements, ((1.0, 0.92, 0.78), (0.97, 0.91, 0.82), (0.55, 0.74, 0.95)),
                            (0.0, 0.18, 0.7)):
        keep, kpos = tuple(el.color), el.position
        el.color = (*kit.srgb_to_linear(rgb), 1)
        el.position = pos
        for f in (1, sky_last):
            el.keyframe_insert("color", frame=f)
            el.keyframe_insert("position", frame=f)
        el.color = keep
        el.position = kpos
        el.keyframe_insert("color", frame=sky_last + 1)
        el.keyframe_insert("position", frame=sky_last + 1)
    keep = bg.default_value
    bg.default_value = 1.4
    bg.keyframe_insert("default_value", frame=1)
    bg.keyframe_insert("default_value", frame=sky_last)
    bg.default_value = keep
    bg.keyframe_insert("default_value", frame=sky_last + 1)
    for owner in (sun, nt, bpy.data.objects["Haze"].data.materials[0].node_tree, wnt):
        ad = owner.animation_data
        _constant_cut(ad, f_last)
        if owner is wnt:
            _constant_cut(ad, sky_last)


def _constant_cut(ad, f_last):
    """No easing across the cut: keys at f_last hold flat until the jump at f_last + 1."""
    if not ad or not ad.action:
        return
    act = ad.action
    curves = []
    try:
        curves = list(act.fcurves)
    except AttributeError:
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves += list(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            if f_last - 0.5 < kp.co.x < f_last + 1.5 or kp.co.x < 1.5:
                kp.interpolation = "CONSTANT"


def make_foam_piece(name, lib, seed, kind):
    """Thin faceted foam: 'ridge' = two or three ragged tapered wedges along a crest (X); 'streak' = a long thin
    tail along Y, trailing downwind. No flat discs."""
    rng = random.Random(seed)
    mb = kit.MB()
    if kind == "ridge":
        x = -rng.uniform(0.8, 1.4)
        for _ in range(rng.randint(2, 3)):
            ln = rng.uniform(0.9, 2.0)
            y = rng.uniform(-0.3, 0.3)
            mb.seg((x, y, 0.06), (x + ln, y + rng.uniform(-0.25, 0.25), 0.1 + rng.uniform(0.0, 0.14)),
                   rng.uniform(0.28, 0.42), rng.uniform(0.04, 0.08), "foam", sides=3, spin=rng.uniform(0, 3))
            x += ln * rng.uniform(0.6, 1.0) + rng.uniform(0.0, 0.5)
    else:
        for _ in range(rng.randint(1, 2)):
            x = rng.uniform(-0.3, 0.3)
            ln = rng.uniform(2.5, 4.5)
            mb.seg((x, 0.0, 0.05), (x + rng.uniform(-0.3, 0.3), ln, 0.04), rng.uniform(0.1, 0.15), 0.015, "foam", sides=3,
                   spin=rng.uniform(0, 3))
    return mb.obj(name, lib)


def foam_on_waves(coll, lib, f0, f1, full, seed=11, n_ridge=340, n_streak=110, step=12):
    """Whitecaps that follow the real swell: at every `step` frames the evaluated sea is ray-cast, each
    foam piece is born on a local crest (higher than the water a few metres up- and down-wave of it),
    then rides the water: its height and tilt are keyed from the sea surface at each sample, it drifts
    downwind and fades out. Random positions (denser near the beach), sizes and headings: no rows.
    Call after everything is built and animated, before saving."""
    from mathutils.bvhtree import BVHTree
    sc = bpy.context.scene
    sea = bpy.data.objects["Sea"]
    rng = random.Random(seed)
    srcs = {"ridge": [make_foam_piece(f"LibFoamR{j}", lib, 40 + j, "ridge") for j in range(5)],
            "streak": [make_foam_piece(f"LibFoamS{j}", lib, 60 + j, "streak") for j in range(3)]}
    for lst in srcs.values():
        for ob in lst:
            kit.hide_source(ob)
    n_total = n_ridge + n_streak
    frames = list(range(f0, f1 + 1, step))

    def level(f):
        return min(1.0, max(0.0, (f - f0) / max(1, full - f0)))
    births = []
    for i in range(n_total):
        kind = "ridge" if i < n_ridge else "streak"
        life = rng.randint(4, 7) * step if kind == "ridge" else rng.randint(5, 8) * step
        # births weighted toward the middle/late storm, when the sea is up
        tb = frames[min(len(frames) - 1, int(len(frames) * rng.random() ** 0.8))]
        births.append(dict(kind=kind, tb=tb, te=tb + life, src=rng.choice(srcs[kind]), ob=None, pos=None,
                           yaw=rng.uniform(-0.5, 0.5), size=rng.uniform(1.6, 3.2), drift=rng.uniform(0.02, 0.05)))
    for f in frames:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        bvh = BVHTree.FromObject(sea, dg)

        def hz(x, y):
            hit = bvh.ray_cast((x, y, 40.0), (0.0, 0.0, -1.0), 80.0)
            return hit[0].z if hit[0] is not None else None
        lv = level(f)
        for bd in births:
            if not (bd["tb"] <= f <= bd["te"]):
                continue
            if bd["pos"] is None:
                for _ in range(60):          # find a crest: denser toward the beach
                    d = 3.0 + rng.expovariate(1.0 / 22.0)
                    if d > 85:
                        continue
                    x = rng.uniform(-10, 150)
                    px, py = cy(x, -d)
                    h0 = hz(px, py)
                    hu, hd = hz(px, py - 3.0), hz(px, py + 3.0)
                    if None in (h0, hu, hd):
                        continue
                    if h0 > hu + 0.03 and h0 > hd + 0.03 and h0 > 0.05:
                        bd["pos"] = (px, py)
                        break
                if bd["pos"] is None:
                    bd["te"] = -1
                    continue
                bd["ob"] = kit.instance(bd["src"], f"S38Foam{len(coll.objects)}", coll, (*bd["pos"], 0.0), scale=0.0)
                bd["ob"].keyframe_insert("scale", frame=max(1, f - step))
            x = bd["pos"][0]
            y = bd["pos"][1] + bd["drift"] * (f - bd["tb"])
            h = hz(x, y)
            if h is None:
                continue
            hx0, hx1, hy0, hy1 = hz(x - 1.0, y), hz(x + 1.0, y), hz(x, y - 1.0), hz(x, y + 1.0)
            if None in (hx0, hx1, hy0, hy1):
                hx0 = hx1 = hy0 = hy1 = h
            ob = bd["ob"]
            ob.location = (x, y, h - 0.03)
            ob.rotation_euler = (math.atan2(hy1 - hy0, 2.0), -math.atan2(hx1 - hx0, 2.0),
                                 math.radians(ST_AXIS) + bd["yaw"] if bd["kind"] == "ridge" else bd["yaw"] * 0.5)
            t = f - bd["tb"]
            grow = min(1.0, t / (2.0 * step), (bd["te"] - f) / (2.0 * step))
            sz = bd["size"] * (0.6 + 0.7 * lv) * max(0.0, grow)
            ob.scale = (sz, sz, sz)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_euler", frame=f)
            ob.keyframe_insert("scale", frame=f)
    for bd in births:
        if bd["ob"] is not None:                   # gone after the last key
            bd["ob"].scale = (0, 0, 0)
            bd["ob"].keyframe_insert("scale", frame=bd["te"] + step)
    sc.frame_set(1)


def heavy_rain(coll, cam, rain_points, frames, half=38.0, count=6200, speed=0.5):
    """The S38 monsoon rain: a much denser field than colachel_world.build_rain (about 5x the
    streaks, thicker and slanted by the wind), following the camera across the ground."""
    rng = random.Random(38)
    kit.mat("rain_heavy", (0.78, 0.84, 0.92))
    bsdf = bpy.data.materials["rain_heavy"].node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Color"].default_value = (*kit.srgb_to_linear((0.80, 0.86, 0.94)), 1)
    bsdf.inputs["Emission Strength"].default_value = 0.45
    pts = []
    while len(pts) < count:
        x, y = rng.uniform(-half, half), rng.uniform(-half, half)
        if math.hypot(x, y) > 4.5:
            pts.append((x, y, rng.uniform(0, kit.RAIN_PERIOD)))
    # three tiers switched on one after another (drizzle, then downpour, then the full wall of
    # rain), so it thickens without ever shrinking the field round the lens
    f_a = rain_points[0][0]
    f_full = next(f for f, v in rain_points if v >= 1.0)
    cuts = (0, int(count * 0.25), int(count * 0.6), count)
    starts = (f_a, f_a + int(0.4 * (f_full - f_a)), f_a + int(0.75 * (f_full - f_a)))
    tiers = []
    for ti in range(3):
        mb = kit.MB()
        for stack in (0.0, kit.RAIN_PERIOD):
            for x, y, z in pts[cuts[ti]:cuts[ti + 1]]:
                mb.box(kit.T(x, y, z + stack) @ kit.Rx(0.2) @ kit.S(0.022, 0.022, rng.uniform(1.3, 1.9)), "rain_heavy")
        rain = mb.obj(f"RainHeavy{ti}", coll)
        c = rain.constraints.new("COPY_LOCATION")
        c.target = cam
        c.use_z = False
        rain.hide_render = rain.hide_viewport = True
        rain.keyframe_insert("hide_render", frame=1)
        rain.keyframe_insert("hide_viewport", frame=1)
        rain.hide_render = rain.hide_viewport = False
        rain.keyframe_insert("hide_render", frame=starts[ti])
        rain.keyframe_insert("hide_viewport", frame=starts[ti])
        tiers.append(rain)
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "CONSTANT"
    try:
        for f in range(f_a, rain_points[-1][0] + 1):
            z = -((f * speed * kit.RAIN_PERIOD / 25.0) % kit.RAIN_PERIOD)
            for rain in tiers:
                rain.location.z = z
                rain.keyframe_insert("location", index=2, frame=f)
    finally:
        prefs.keyframe_new_interpolation_type = old
    return tiers


def storm_look(sun, storm, soak_names=()):
    """Push the S38 monsoon grey and gloomy: darker slate sky and sea, weak cold sun, thick grey
    haze, and wet, dark ground, timber and canvas as the storm arrives. Keys sit on the storm
    points (0 before S38, full at storm[1])."""
    lin = kit.srgb_to_linear
    wnt = bpy.context.scene.world.node_tree
    mix = wnt.nodes["StormMix"]
    cw._sock(mix.inputs, "B_Color").default_value = (*lin((0.42, 0.45, 0.50)), 1)
    cw.key_storm(mix.inputs["Factor"], "default_value", storm, 0.0, 0.9)
    bg = next(n for n in wnt.nodes if n.bl_idname == "ShaderNodeBackground")
    cw.key_storm(bg.inputs["Strength"], "default_value", storm, 0.95, 0.85)
    cw.key_storm(sun.data, "energy", storm, 9.5, 2.4)
    cw.key_storm(sun.data, "color", storm, (1.0, 0.72, 0.42), (0.66, 0.74, 0.86))
    snt = bpy.data.materials["Sea"].node_tree
    cw._sock(snt.nodes["StormMix"].inputs, "B_Color").default_value = (*lin((0.30, 0.42, 0.48)), 1)
    cw.key_storm(snt.nodes["StormMix"].inputs["Factor"], "default_value", storm, 0.0, 0.82)
    vol = next(n for n in bpy.data.objects["Haze"].data.materials[0].node_tree.nodes
               if n.bl_idname == "ShaderNodeVolumePrincipled")
    cw.key_storm(vol.inputs["Color"], "default_value", storm, (*lin((1.0, 0.82, 0.58)), 1), (*lin((0.60, 0.64, 0.70)), 1))
    cw.key_storm(vol.inputs["Density"], "default_value", storm, 0.0008, 0.0026)
    f_a, f_b = storm[0][0], storm[1][0]
    for name in soak_names:
        m = bpy.data.materials.get(name)
        if not m or not m.node_tree:
            continue
        b = m.node_tree.nodes.get("Principled BSDF")
        if not b:
            continue
        col, rough = tuple(b.inputs["Base Color"].default_value), b.inputs["Roughness"].default_value
        for f, k, rg in ((f_a, 1.0, rough), (f_b, 0.52, 0.3)):
            b.inputs["Base Color"].default_value = (col[0] * k * (0.92 if k < 1 else 1), col[1] * k * 0.97,
                                                    col[2] * k * (1.08 if k < 1 else 1), 1.0)
            b.inputs["Roughness"].default_value = rg
            b.inputs["Base Color"].keyframe_insert("default_value", frame=f)
            b.inputs["Roughness"].keyframe_insert("default_value", frame=f)
        b.inputs["Base Color"].default_value = col
        b.inputs["Roughness"].default_value = rough


def neutral_haze(f_a, f_b, rgb=(0.78, 0.84, 0.90)):
    """Over S34 only the distant haze is a neutral grey-blue (not warm), so the far inland reads as
    cool air over the hills rather than wet olive green. Golden again from f_b + 1."""
    lin = kit.srgb_to_linear
    vol = next(n for n in bpy.data.objects["Haze"].data.materials[0].node_tree.nodes
               if n.bl_idname == "ShaderNodeVolumePrincipled")
    col = vol.inputs["Color"]
    gold = (*lin((1.0, 0.82, 0.58)), 1)
    for f, c in ((f_a - 1, gold), (f_a, (*lin(rgb), 1)), (f_b, (*lin(rgb), 1)), (f_b + 1, gold)):
        col.default_value = c
        col.keyframe_insert("default_value", frame=f)
    dens = vol.inputs["Density"]
    for f, d in ((f_a - 1, 0.0008), (f_a, 0.0011), (f_b, 0.0011), (f_b + 1, 0.0008)):
        dens.default_value = d
        dens.keyframe_insert("default_value", frame=f)
    ad = vol.id_data.animation_data
    act = ad.action
    curves = []
    try:
        curves = list(act.fcurves)
    except AttributeError:
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves += list(bag.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points:
            if kp.co.x <= f_b + 1.5 and kp.co.x >= 1:
                kp.interpolation = "CONSTANT"


def low_clouds(coll, storm, rng):
    """Dark clouds banking up low over the sea, ahead of the rain (K10): they grow from nothing as
    the storm builds, so the sky visibly darkens behind the stockade."""
    srcs = [bpy.data.objects[f"LibCloud{i}"] for i in range(4)]
    f_a, f_b = storm[0][0], storm[1][0]
    for i in range(20):
        x = rng.uniform(-100, 220)
        y = SY(60.0) + rng.uniform(-330, -150)
        z = rng.uniform(50, 95)
        ob = kit.instance(srcs[i % 4], f"LowCloud{i}", coll, (x, y, z), rot_z=rng.uniform(0, 6.28), scale=0.0)
        sz = rng.uniform(1.3, 2.1)
        for f, loc, sc in ((f_a, (x - 30, y - 30, z), 0.0), (f_b, (x, y, z), sz), (storm[2][0], (x + 25, y + 15, z), sz)):
            ob.location = loc
            ob.scale = (sc, sc, sc * 0.9)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("scale", frame=f)


SOAK = ("sand", "sand_wet", "grass", "log", "log_end", "post", "thatch", "thatch_dk", "canvas", "crate",
        "crate_edge", "plank", "hull", "hull_in", "trunk", "frond", "frond_dk", "leaf", "leaf_dk", "wall", "beam", "rock",
        "laterite_rd", "field_dirt_dk", "coconut")
SEA_RAMP = [(0.0, (0.40, 0.80, 0.80)), (0.22, (0.30, 0.70, 0.78)), (0.55, (0.28, 0.52, 0.76)),
            (1.0, (0.22, 0.40, 0.68))]            # turquoise shallows to deep blue, by depth/60 m


def _sea_ramp(t):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(SEA_RAMP, SEA_RAMP[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return tuple(a + (b - a) * u for a, b in zip(c0, c1))
    return SEA_RAMP[-1][1]


def crisp_sea(sea, seed=5, bright=0.2, tilt=0.06):
    """Per-facet colour on the sea (K37/K38: every triangle a slightly different turquoise or blue),
    with a wider turquoise shallow band than the base sea. The foam line at the waterline is kept."""
    me = sea.data
    rng = random.Random(seed)
    old = me.attributes["Col"]
    n = len(me.vertices)
    flat = [0.0] * (n * 4)
    old.data.foreach_get("color", flat)
    vals = []
    for p in me.polygons:
        r = g = b = 0.0
        px = py = 0.0
        for vi in p.vertices:
            r += flat[vi * 4]
            g += flat[vi * 4 + 1]
            b += flat[vi * 4 + 2]
            px += me.vertices[vi].co.x
            py += me.vertices[vi].co.y
        k = len(p.vertices)
        r, g, b = r / k, g / k, b / k
        depth = SY(px / k) - py / k
        if depth >= 1.2:
            r, g, b = (kit.srgb_to_linear(_sea_ramp(depth / 60.0)))
        j, j2 = rng.uniform(-1, 1), rng.uniform(-1, 1)
        s = 1.0 + bright * j
        c = (r * s * (1 - tilt * j2), g * s * (1 + 0.3 * tilt * j2), b * s * (1 + tilt * j2), 1.0)
        vals += list(c) * p.loop_total
    me.attributes.remove(old)
    att = me.attributes.new("Col", "FLOAT_COLOR", "CORNER")
    att.data.foreach_set("color", vals)
    me.update()


# ===================================================================== whole set
def build_world(ev):
    end = ev["end"]
    world_c = kit.new_collection("World")
    village_c = kit.new_collection("Village")
    props_c = kit.new_collection("Props")
    plants_c = kit.new_collection("Plants")
    people_c = kit.new_collection("People")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    rng = random.Random(7)
    cw.make_land(world_c)
    sea = cw.make_sea(world_c)
    crisp_sea(sea)
    cw.animate_sea(sea, rig_c, end, ev["storm"])
    sun = cw.scene_base(rig_c)
    cw.apply_weather(sun, bpy.data.objects["Haze"], {"storm": ev["storm"]})
    cw.build_village(village_c, props_c, plants_c, people_c, lib_c, end)
    tidy_trees()
    build_groves(plants_c, rng)
    build_path(world_c)
    build_hamlets(village_c, rng)
    cw.build_clouds(kit.new_collection("Clouds"), {"storm": ev["storm"]})

    sets = {}
    sets["S30"] = kit.new_collection("S30_Broadside")
    build_s30(sets["S30"], lib_c, ev)
    sets["Fleet"] = kit.new_collection("Fleet_S31-S34")
    fleet = build_fleet(sets["Fleet"], end)
    sets["S31"] = kit.new_collection("S31_Landing")
    build_s31(sets["S31"], lib_c, ev, fleet)
    sets["Camp"] = kit.new_collection("BeachCamp_S32-S38")
    build_beach_camp(sets["Camp"], lib_c, ev)
    sets["S32"] = kit.new_collection("S32_DeLannoy")
    dl = build_s32(sets["S32"], lib_c, ev)
    sets["Stockade"] = kit.new_collection("Stockade_S34-S38")
    build_stockade(sets["Stockade"], lib_c, ev)
    sets["S34"] = kit.new_collection("S34_Inland")
    build_s34(sets["S34"], lib_c, ev)
    sets["S38"] = kit.new_collection("S38_Monsoon")
    build_s38(sets["S38"], lib_c, ev)
    sway_palms(ev["r38"][0], ev["r38"][1], cw.STOCKADE["center"], 140, rng)
    storm_look(sun, ev["storm"], SOAK)
    neutral_haze(ev["r34"][0], ev["r34"][1])
    cm = bpy.data.materials.get("cloud")
    if cm:
        cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*kit.srgb_to_linear((0.22, 0.24, 0.29)), 1)
    clouds_c = kit.new_collection("LowClouds")
    low_clouds(clouds_c, ev["storm"], random.Random(38))

    r30, r31, r32, r34, r38 = ev["r30"], ev["r31"], ev["r32"], ev["r34"], ev["r38"]
    set_vis(sets["S30"], [r30])
    set_vis(sets["Fleet"], [r31, r34])
    set_vis(sets["S31"], [r31])
    set_vis(sets["Camp"], [(r32[0], end)])
    set_vis(sets["S32"], [r32])
    set_vis(sets["Stockade"], [(r34[0], end)])
    set_vis(sets["S34"], [r34])
    set_vis(sets["S38"], [r38])
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c, sun, dl
