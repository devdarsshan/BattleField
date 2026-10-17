"""Colachel beach, June to August 1741: the siege (S40-S48; clips 49-58) in Siege.blend.

The SAME beach, village, track, hamlets, palms, sea and stockade as the landing beats
(colachel_world + landing_world), now with the finished Dutch stockade standing and the
monsoon on. Each beat adds its own set on top (a collection shown only in that beat's frames):

  S40 (K49) the Travancore column drives the Dutch out of the hamlets, down the track, to the gate.
  S41 (K50) Travancore tents, camp fires and sentries ring the stockade ("ring" stays to the end).
  S42 (K51) the orbit continues to the fishing village beside the beach (nets, boats).
  S43 (K52) Mukkuvar fishermen refuse a Dutch officer's bag of coins.
  S44 (K53) fishermen push carts with painted palm trunks onto the dunes.
  S45 (K54) the row of palm-trunk "cannons" from behind, two Dutch ships far out.
  S46 (K55-K56) the two ships come in; the shore guns fire; the ships turn away.
  S47 (K57) inside the stockade in the rain: the last rice sacks are counted.
  S48 (K58) a gun on the hillside battery fires at the stockade.

Everything else comes from the kit; the only new parts are the fake cannon, cart, coin bag and net.
"""
import math
import random

import bpy
from mathutils import Vector

import colachel_kit as kit
import colachel_world as cw
import landing_world as lw
import port_world as pw

H = cw.height
SY = cw.shore_y
SW = cw.stockade_world
ST = cw.STOCKADE
AX = math.radians(ST["axis_deg"])
NX, NY = 0.287, 0.958                    # inland, across the coast
TX, TY = 0.958, -0.287                   # along the coast (ESE)
SEA_HEAD = math.atan2(-NY, -NX) - math.pi / 2          # rot_z that faces a figure out to sea
face = lw._face
cy = lw.cy
set_vis = lw.set_vis


def beach(x, d):
    """(x, y) d metres inland of the waterline at x."""
    return cy(x, d)


def at_beach(x, d, dx=0.0, dy=0.0):
    px, py = cy(x, d)
    return px + dx, py + dy


def put(src, name, c, x, y, rz=0.0, s=1.0, sink=0.02, dz=0.0):
    return kit.instance(src, name, c, (x, y, H(x, y) - sink + dz), rot_z=rz, scale=s)


# ===================================================================== library
def build_lib(lib):
    """Hidden source meshes shared by every siege beat (kit parts only)."""
    L = {}
    L["dutch"] = [kit.make_figure(f"LibSDutch{k}", lib, "dutch", seed=k) for k in range(3)]
    L["dutch_sit"] = [kit.make_figure(f"LibSDutchSit{k}", lib, "dutch", seed=10 + k, pose="sit") for k in range(3)]
    L["officer"] = kit.make_figure("LibSOfficer", lib, "dutch", seed=5, pose="point")
    L["nair"] = [kit.make_figure(f"LibNair{i}", lib, "nair" if i % 2 else "nair_spear", seed=i) for i in range(4)]
    L["nair_sit"] = [kit.make_figure(f"LibSNairSit{i}", lib, "nair", seed=20 + i, pose="sit") for i in range(2)]
    L["cmdr"] = [kit.make_figure(f"LibCommander{i}", lib, "commander", seed=i) for i in range(2)]
    L["fisher"] = [kit.make_figure(f"LibSFish{i}", lib, "villager", seed=30 + i,
                                   cloth=("cloth_w", "cloth_t", "cloth_r", "cloth_w")[i]) for i in range(4)]
    L["cone"] = [kit.make_cone_tent(f"LibSCone{i}", lib, r=1.9 + 0.3 * i, h=3.0 + 0.4 * i, seed=i) for i in range(3)]
    L["ridge"] = kit.make_ridge_tent("LibSRidge", lib)
    L["flames"] = [kit.make_flames(f"LibSFlames{k}", lib, seed=k, size=0.5) for k in range(2)]
    L["puff"] = [kit.make_puff(f"LibSPuff{k}", lib, seed=60 + k, m=("smoke", "smoke_md", "smoke")[k]) for k in range(3)]
    L["puff_dk"] = [kit.make_puff(f"LibSPuffDk{k}", lib, seed=70 + k, m="smoke_md") for k in range(2)]
    L["splash"] = [kit.make_splash(f"LibSSplash{k}", lib, seed=k, h=5.0 + k) for k in range(3)]
    L["coin"] = kit.make_coin_bag("LibSCoinBag", lib)
    L["net"] = [kit.make_fishing_net(f"LibSNet{k}", lib, length=2.8 + 0.6 * k, seed=k) for k in range(2)]
    L["cannon"] = kit.make_cannon("LibSCannon", lib)
    L["sack"] = bpy.data.objects.get("LibSack") or kit.make_sack("LibSack", lib)
    kit.mat_emit("flash", (1.0, 0.62, 0.22), 40.0)
    mb = kit.MB()
    mb.ico(kit.Matrix.Identity(4), "flash", r=0.6, sub=1)
    L["flash"] = mb.obj("LibSFlash", lib)
    mb = kit.MB()
    mb.cone(kit.T(0, 0, 0.04), "stone", segments=7, r1=0.55, r2=0.5, depth=0.08)
    for k in range(7):
        a = k * math.tau / 7
        mb.ico(kit.T(math.cos(a) * 0.5, math.sin(a) * 0.5, 0.1), "rock", r=0.13, sub=1)
    L["firering"] = mb.obj("LibSFireRing", lib)
    # one low dune: a flattened, faceted heap of sand
    mb = kit.MB()
    rng = random.Random(9)
    mb.ico(kit.T(0, 0, 0) @ kit.S(1.0, 0.55, 0.22), "sand", r=3.2, sub=2, jitter=0.1, rng=rng)
    L["dune"] = mb.obj("LibSDune", lib)
    for k in L["fisher"] + L["dutch"] + L["dutch_sit"] + L["nair"] + L["nair_sit"] + L["cmdr"] + L["cone"] + \
            L["flames"] + L["puff"] + L["puff_dk"] + L["splash"] + L["net"] + [L["ridge"], L["officer"], L["coin"],
                                                                                  L["cannon"], L["flash"], L["sack"],
                                                                                  L["firering"], L["dune"]]:
        kit.hide_source(k)
    return L


# ===================================================================== helpers
def route(s_from, s_to, lat, step=3.0):
    """Waypoints along the track from arc length s_from to s_to (either direction), lat metres to the side."""
    pts = []
    n = max(1, int(abs(s_to - s_from) / step))
    for k in range(n + 1):
        s = s_from + (s_to - s_from) * k / n
        (px, py), (dx, dy) = lw.path_point(s)
        pts.append((px - dy * lat, py + dx * lat))
    return pts


def fire_gun(c, L, gun_xy, aim, f, rng, end, tag, size=1.0, smoke=1.0):
    """Muzzle flash and a rolling plume of smoke from a field gun at gun_xy aimed along rot_z `aim`."""
    gx, gy = gun_xy
    base = Vector((gx, gy, H(gx, gy)))
    mw = base + kit.Rz(aim) @ Vector(kit.CANNON_MUZZLE)
    fw = Vector((-math.sin(aim), math.cos(aim), 0.0))
    fl = kit.instance(L["flash"], f"{tag}Flash", c, mw + fw * 0.5, scale=0.0)
    for ff, sc in ((f - 1, 0.0), (f, 2.4 * size), (f + 2, 1.4 * size), (f + 6, 0.0)):
        fl.scale = (sc, sc, sc)
        fl.keyframe_insert("scale", frame=ff)
    for i in range(int(14 * smoke)):
        t0 = f + i // 3
        p0 = mw + fw * rng.uniform(0.4, 3.0) + Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4),
                                                       rng.uniform(-0.1, 0.6)))
        ob = kit.instance(L["puff"][i % 3], f"{tag}Smoke{i}", c, p0, scale=0.0)
        ob.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
        kit.animate_puff(ob, t0, end, p0, (fw.x * rng.uniform(1.0, 3.5) + 0.9, fw.y * rng.uniform(1.0, 3.5) + 0.4,
                                           rng.uniform(0.6, 1.8)),
                         s0=0.4 * size, s1=rng.uniform(1.8, 2.8) * size, grow=34.0, drag=0.7, step=6,
                         fade=(t0 + 110, t0 + 190))


def turn_to(ob, f, to_rz, frames=14):
    """Keep ob's heading until f, then swing to rot_z `to_rz` over `frames`."""
    ob.keyframe_insert("rotation_euler", frame=max(1, f - 1))
    ob.rotation_euler[2] = to_rz
    ob.keyframe_insert("rotation_euler", frame=f + frames)


def puddles(c, rng, pts, n_each=3):
    mb = kit.MB()
    for (px, py) in pts:
        for _ in range(n_each):
            x, y = px + rng.uniform(-2.2, 2.2), py + rng.uniform(-2.2, 2.2)
            mb.cone(kit.T(x - pts[0][0], y - pts[0][1], H(x, y) + 0.03 - H(*pts[0])) @ kit.S(rng.uniform(0.7, 1.5), rng.uniform(0.5, 1.1), 1),
                    "soil_dk", segments=7, r1=0.9, r2=0.8, depth=0.03)
    ob = mb.obj("Puddles", c)
    ob.location = (pts[0][0], pts[0][1], H(*pts[0]))
    return ob


# ===================================================================== siege garrison and ring
def build_garrison(c, L, ev):
    """Dutch inside the finished stockade: sentries on the wall line, men at rest (S40-S48)."""
    rng = random.Random(40)
    end = ev["end"]
    n = 0
    for k in range(18):
        u = rng.uniform(-13, 13)
        v = rng.choice((-10.2, 10.2)) if k % 3 else rng.uniform(-8, 8)
        if abs(u) < 3.0 and v > 8:                      # keep the gate clear
            u += 4.5
        x, y = SW(u, v)
        rz = AX + (math.pi if v > 0 else 0.0) + rng.uniform(-0.5, 0.5)
        ob = put(L["dutch"][n % 3], f"Garrison{n}", c, x, y, rz)
        kit.animate_idle(ob, rng, 1, end, amount=0.03)
        n += 1
    for k, (u, v) in enumerate(((4.0, -2.0), (5.5, -1.0), (4.8, 0.6), (-9.0, -7.5), (-10.5, -6.8))):
        x, y = SW(u, v)
        ob = put(L["dutch_sit"][k % 3], f"GarrisonSit{k}", c, x, y, rng.uniform(0, 6.28))
        kit.animate_idle(ob, rng, 1, end, amount=0.02)


def rect_pts(off, step, jitter=0.0, rng=None):
    """Points round the stockade, `off` metres outside its wall (stockade frame), `step` metres apart."""
    hu, hv = ST["half_u"] + off, ST["half_v"] + off
    pts = []
    for (u0, v0), (u1, v1) in (((-hu, -hv), (hu, -hv)), ((hu, -hv), (hu, hv)), ((hu, hv), (-hu, hv)), ((-hu, hv), (-hu, -hv))):
        n = max(1, int(math.hypot(u1 - u0, v1 - v0) / step))
        for k in range(n):
            u, v = u0 + (u1 - u0) * k / n, v0 + (v1 - v0) * k / n
            if rng:
                u, v = u + rng.uniform(-jitter, jitter), v + rng.uniform(-jitter, jitter)
            pts.append((u, v))
    return pts


def build_ring(c, lib, L, ev):
    """The Travancore siege ring: a line of soldiers close round the wall, tents behind them, fires,
    patrols and the standard, all round the stockade (S41 on)."""
    rng = random.Random(41)
    end = ev["end"]
    f0 = ev["r41"][0]
    cx0, cy0 = ST["center"]
    gun_spots = [(beach(xx, dd), 7.0) for xx, dd in GUNS46]
    spots = [(SW(0, 0), 0.0)] + gun_spots

    def free(x, y, r):
        return all(math.hypot(x - a, y - b) > r + rb for (a, b), rb in spots)

    def ok_ground(x, y):
        return H(x, y) > 0.3 and (y - SY(x)) > 2.4 and x > 38.0 and not cw.in_stockade(x, y, 2.5)

    # a close line of sentries all round the wall, facing it
    n = 0
    for (u, v) in rect_pts(3.2, 2.3, 0.35, rng):
        x, y = SW(u, v)
        if not ok_ground(x, y) or not free(x, y, 0.7):
            continue
        spots.append(((x, y), 0.7))
        ob = put(L["nair"][n % 4], f"RingNair{n}", c, x, y, face(cx0 - x, cy0 - y) + rng.uniform(-0.25, 0.25))
        kit.animate_idle(ob, rng, f0, end, amount=0.03)
        n += 1
    # two rows of tents behind the line
    tents = []
    for row, off in enumerate((9.5, 16.5)):
        for k, (u, v) in enumerate(rect_pts(off, 6.8, 1.0, rng)):
            x, y = SW(u, v)
            if not ok_ground(x, y) or not free(x, y, 2.9):
                continue
            src = L["ridge"] if rng.random() < 0.25 else rng.choice(L["cone"])
            kit.instance(src, f"RingTent{len(tents)}", c, (x, y, H(x, y) - 0.03),
                         rot_z=face(cx0 - x, cy0 - y) + rng.uniform(-0.3, 0.3), scale=rng.uniform(0.9, 1.1))
            spots.append(((x, y), 2.9))
            tents.append((x, y))
    # camp fires between the line and the tents, with men sitting round them
    fires = []
    for k, (u, v) in enumerate(rect_pts(6.2, 9.0, 1.2, rng)):
        x, y = SW(u, v)
        if not ok_ground(x, y) or not free(x, y, 1.6):
            continue
        spots.append(((x, y), 1.6))
        fires.append((x, y))
        kit.instance(L["firering"], f"RingFireRing{len(fires)}", c, (x, y, H(x, y) - 0.02), rot_z=rng.uniform(0, 6))
        fl = kit.instance(L["flames"][len(fires) % 2], f"RingFire{len(fires)}", c, (x, y, H(x, y) + 0.05), scale=1.1)
        kit.animate_flicker(fl, rng, f0, end, amount=0.3, every=(2, 5))
        for j in range(rng.randint(3, 4)):
            a = j * math.tau / 4 + rng.uniform(-0.4, 0.4)
            sx, sy = x + math.cos(a) * 1.5, y + math.sin(a) * 1.5
            sit = put(L["nair_sit"][j % 2], f"RingSit{len(fires)}_{j}", c, sx, sy, face(x - sx, y - sy))
            kit.animate_idle(sit, rng, f0, end, amount=0.02)
        for j in range(5):                                # a thin thread of smoke from each fire
            born = f0 + j * 30 + rng.randint(0, 20)
            p = kit.instance(L["puff_dk"][j % 2], f"RingFireSmoke{len(fires)}_{j}", c, (x, y, H(x, y) + 1.0), scale=0.0)
            kit.animate_puff(p, born, end, (x, y, H(x, y) + 1.0), (0.9, 0.35, 1.6), s0=0.15, s1=0.55, grow=40.0,
                             drag=0.2, step=8, fade=(born + 70, born + 130))
    # more men standing about between the tents
    for i in range(200):
        t_ = rng.uniform(0, math.tau)
        x, y = SW(math.cos(t_) * rng.uniform(21.0, 31.0), math.sin(t_) * rng.uniform(17.0, 27.0))
        if not ok_ground(x, y) or not free(x, y, 0.8):
            continue
        spots.append(((x, y), 0.8))
        ob = put(L["nair"][i % 4], f"RingExtra{i}", c, x, y, rng.uniform(0, 6.28))
        kit.animate_idle(ob, rng, f0, end, amount=0.03)
        if i > 120:
            break
    # patrols walking the ring
    tpl = []
    for k in range(2):
        root, parts = kit.make_walker(f"LibSPatrol{k}", lib, "nair_spear" if k else "nair", seed=50 + k)
        root.location = (0, 0, -500)
        for p in parts.values():
            p.hide_render = True
        tpl.append(parts)
    ring_pts = [SW(u, v) for u, v in rect_pts(5.0, 5.0)]
    ring_pts = [p for p in ring_pts if ok_ground(*p)]
    for k in range(10):
        i0 = rng.randrange(max(1, len(ring_pts) - 6))
        wps = ring_pts[i0:i0 + 6]
        if len(wps) < 2:
            continue
        root, parts = kit.clone_walker(tpl[k % 2], f"RingPatrol{k}", c)
        kit.animate_walk(root, parts, wps, H, start=f0 - 60 + k * 11, end=end, stride_frames=15, swing=0.4, speed=0.9)
    # the Travancore standard and a commander's party where the track meets the ring
    x, y = SW(-6.0, 21.5)
    pw.flag_on_pole(c, "RingFlag", (x, y, H(x, y)), 7.0, 2.4, 1.5, "flag_r", heading=160)
    cm = put(L["cmdr"][0], "RingCommander0", c, x + 2.0, y - 1.0, face(cx0 - x, cy0 - y))
    kit.animate_idle(cm, rng, f0, end, amount=0.02)
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    for k, (x, y) in enumerate(tents[:14]):
        put((crate, barrel, L["sack"])[k % 3], f"RingStore{k}", c, x + 2.6, y + 0.8, rng.uniform(0, 3))
    return fires


# ===================================================================== S40
def build_s40(c, lib, L, ev):
    """The Travancore column drives the Dutch out of the hamlets, back down the track to the gate (K49)."""
    rng = random.Random(40)
    f0, f1 = ev["r40"]
    dt, nt = [], []
    for k in range(3):
        for kind, tpl in (("dutch", dt), ("nair" if k % 2 else "nair_spear", nt)):
            root, parts = kit.make_walker(f"LibS40{kind}{k}", lib, kind, seed=140 + k)
            root.location = (0, 0, -500)
            for p in parts.values():
                p.hide_render = True
            tpl.append(parts)
    puffs = L["puff"]
    # the Dutch: from the hamlets and the upper track, falling back toward the gate
    hams = lw.hamlet_centres()
    starts = [12.0, 17.0, 22.0, 27.0, 32.0, 37.0, 42.0, 47.0, 52.0, 57.0, 62.0, 67.0, 72.0, 77.0]
    n = 0
    for r, s0 in enumerate(starts):
        for fl in range(3 if r % 2 == 0 else 2):
            lat = (fl - 1) * 1.7 + rng.uniform(-0.6, 0.6)
            s_to = max(-2.0, s0 - rng.uniform(26.0, 40.0))
            root, parts = kit.clone_walker(dt[n % 3], f"S40Dutch{n}", c)
            kit.animate_walk(root, parts, route(s0, s_to, lat), H, start=f0 - 20 + rng.randint(0, 40), end=f1 + 6,
                             stride_frames=13, swing=0.45, speed=rng.uniform(1.5, 1.9))
            n += 1
    # a few Dutch halted at the hamlets, aiming back at the pursuers
    for hi, (hx, hy) in enumerate(hams):
        for k in range(3):
            x, y = hx + rng.uniform(-4, 4), hy + rng.uniform(-4, 4)
            put(L["dutch"][k], f"S40Rear{hi}_{k}", c, x, y, face(hx - x, hy - y + 8.0) + rng.uniform(-0.5, 0.5))
    # the Travancore column behind them, three abreast, and skirmishers fanned out to the sides
    m = 0
    for r in range(16):
        for fl in range(3):
            s0 = 104.0 - r * 3.2 + rng.uniform(-0.6, 0.6)
            lat = (fl - 1) * 1.5 + rng.uniform(-0.3, 0.3)
            root, parts = kit.clone_walker(nt[m % 3], f"S40Nair{m}", c)
            kit.animate_walk(root, parts, route(s0, max(-2.0, s0 - 52.0), lat), H, start=f0 - 30 + (r * 3 + fl) % 7,
                             end=f1 + 6, stride_frames=13, swing=0.45, speed=rng.uniform(1.9, 2.2))
            m += 1
    for k in range(16):
        s0 = rng.uniform(55.0, 105.0)
        lat = rng.choice((-1, 1)) * rng.uniform(5.0, 11.0)
        root, parts = kit.clone_walker(nt[k % 3], f"S40Skirm{k}", c)
        kit.animate_walk(root, parts, route(s0, s0 - 50.0, lat), H, start=f0 - 25 + k * 4, end=f1 + 6,
                         stride_frames=13, swing=0.45, speed=2.2)
    # a commander on the track and his standards
    cs = 112.0
    (px, py), (dx, dy) = lw.path_point(cs)
    pw.flag_on_pole(c, "S40Standard", (px + 2.4, py - 0.6, H(px + 2.4, py - 0.6)), 6.0, 2.0, 1.3, "flag_r", heading=200)
    # musket smoke bursts where the front of the column is (computed from its pace)
    for i in range(16):
        t = f0 + 12 + i * 20 + rng.randint(0, 8)
        s = 100.0 - 2.0 * (t - f0) / kit.FPS + rng.uniform(-6, 6)
        (px, py), (dx, dy) = lw.path_point(max(0.0, s))
        lat = rng.uniform(-4, 4)
        p0 = (px - dy * lat, py + dx * lat, H(px, py) + 1.3)
        ob = kit.instance(puffs[i % 3], f"S40Shot{i}", c, p0, scale=0.0)
        kit.animate_puff(ob, t, f1 + 10, p0, (-dx * 0.8 + 0.5, -dy * 0.8, 0.8), s0=0.25, s1=0.9, grow=18.0, drag=0.6,
                         step=5, fade=(t + 40, t + 90))
    # things dropped on the track by the retreating Dutch
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    for k in range(9):
        (px, py), _ = lw.path_point(rng.uniform(30, 120))
        x, y = px + rng.uniform(-2.2, 2.2), py + rng.uniform(-2.2, 2.2)
        put((crate, barrel, L["sack"])[k % 3], f"S40Dropped{k}", c, x, y, rng.uniform(0, 3))


# ===================================================================== S43
def build_s43(c, L, ev):
    """Fishermen turn their backs on a Dutch officer's bag of coins (K52)."""
    rng = random.Random(43)
    end = ev["end"]
    f0, f1 = ev["r43"]
    turn = ev["refuse"]
    gx, gy = beach(9.5, 3.8)
    # the fishermen stand in a loose arc by the beached boats, facing the officer
    offs = ((0.0, 0.0, 0), (1.4, 0.7, 1), (2.7, -0.2, 2), (4.0, 0.6, 3), (5.4, -0.1, 0), (-1.5, -0.8, 1))
    ox, oy = gx - TX * 1.9 + NX * 1.6, gy - TY * 1.9 + NY * 1.6        # the officer, at the left, nearest the huts
    for i, (dt_, dn, k) in enumerate(offs):
        x, y = gx + TX * dt_ + NX * dn, gy + TY * dt_ + NY * dn
        ob = put(L["fisher"][k], f"S43Fisher{i}", c, x, y, face(ox - x, oy - y) + rng.uniform(-0.15, 0.15))
        away = face(x - ox, y - oy) + rng.uniform(-0.5, 0.5)
        kit.animate_idle(ob, rng, f0, turn - 30, amount=0.02)
        turn_to(ob, turn + 3 * i, away, frames=16)
        ob.rotation_euler[2] = away
        kit.animate_idle(ob, rng, turn + 40, end, amount=0.02)
    # the Dutch officer holding out the bag, two soldiers behind him
    off = put(L["officer"], "S43Officer", c, ox, oy, face(gx + TX * 2.5 - ox, gy + TY * 2.5 - oy), s=1.04)
    kit.animate_idle(off, rng, f0, end, amount=0.015)
    bag_pos = Vector((ox, oy, H(ox, oy))) + kit.Rz(off.rotation_euler[2]) @ Vector((-0.36, 0.8, 1.27))
    bag = kit.instance(L["coin"], "S43Bag", c, bag_pos, rot_z=0.5, scale=1.6)
    for k, (db, dn) in enumerate(((-1.4, 1.2), (-2.4, 2.0))):
        x, y = ox + TX * db + NX * dn, oy + TY * db + NY * dn
        s = put(L["dutch"][k], f"S43Escort{k}", c, x, y, face(gx - x, gy - y))
        kit.animate_idle(s, rng, f0, end, amount=0.02)
    # nets drying, baskets of fish, boats pulled up, an oar or two
    for k, (dt_, dn, rz) in enumerate(((-4.5, 5.0, 0.0), (7.5, 6.5, 0.1), (14.0, 4.5, -0.1))):
        x, y = gx + TX * dt_ + NX * dn, gy + TY * dt_ + NY * dn
        put(L["net"][k % 2], f"S43Net{k}", c, x, y, face(TX, TY) - math.pi / 2 + rz)
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    for k in range(7):
        x, y = gx + TX * rng.uniform(1, 9) + NX * rng.uniform(3.0, 5.5), gy + TY * rng.uniform(1, 9) + NY * rng.uniform(3.0, 5.5)
        if math.hypot(x - ox, y - oy) < 1.6:
            continue
        put((crate, barrel)[k % 2], f"S43Gear{k}", c, x, y, rng.uniform(0, 3), s=0.8)
    boat = bpy.data.objects["LibBoat"]
    for k, (dt_, dn) in enumerate(((3.0, -3.4), (8.5, -3.2), (14.0, -3.0))):
        x, y = gx + TX * dt_ + NX * dn, gy + TY * dt_ + NY * dn
        put(boat, f"S43Boat{k}", c, x, y, face(NX, NY) + rng.uniform(-0.35, 0.35), sink=0.12)
    # villagers going about the beach behind
    for k, (xa, da, xb, db) in enumerate(((17, 11, 26, 10), (28, 12, 19, 12), (21, 9, 30, 8))):
        root, parts = kit.make_villager(f"S43Walker{k}", c, seed=80 + k, robe=k == 0, cloth=("cloth_t", "cloth_w", "cloth_r")[k])
        kit.animate_walk(root, parts, [beach(xa, da), beach(xb, db)], H, start=f0, end=end, stride_frames=15, speed=0.5)


# ===================================================================== S44
def cart_line(x0, x1, d):
    return beach(x0, d), beach(x1, d)


def build_s44(c, L, ev):
    """Fishermen push carts with painted palm-trunk 'cannons' toward the dunes (K53)."""
    rng = random.Random(44)
    end = ev["end"]
    f0, f1 = ev["r44"]
    for i, (x0, x1, d, t0, kv) in enumerate(((-2.0, -18.0, 4.8, f0 - 30, 0), (-8.0, -24.0, 6.6, f0 + 10, 1),
                                              (-14.0, -30.0, 8.2, f0 + 50, 2))):
        a, b = cart_line(x0, x1, d)
        root, wheels = kit.make_log_cannon(f"S44Cart{i}", c, seed=i)
        heading = math.atan2(b[1] - a[1], b[0] - a[0]) - math.pi / 2
        dur = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 1.2 * kit.FPS)
        kit.animate_cart(root, wheels, t0, t0 + dur, a, b, H, heading=heading)
        # two pushers behind, one hauling at the drag pole, in front
        for k, (side, back) in enumerate(((-0.75, -2.5), (0.75, -2.5), (0.0, -3.4))):
            lx = math.cos(heading) * side - math.sin(heading) * back
            ly = math.sin(heading) * side + math.cos(heading) * back
            fr, fkind = kit.make_villager(f"S44Push{i}_{k}", c, seed=100 + 3 * i + k, cloth=("cloth_w", "cloth_t", "cloth_r")[k])
            pa, pb = (a[0] + lx, a[1] + ly), (b[0] + lx, b[1] + ly)
            kit.animate_walk(fr, fkind, [pa, pb], H, start=t0, end=t0 + dur, stride_frames=14, swing=0.35, speed=1.2)
    # onlookers and more fishermen carrying logs and ropes toward the dunes
    for k in range(5):
        xa, xb = 14 - 5 * k, -8 - 6 * k
        root, parts = kit.make_villager(f"S44Hand{k}", c, seed=120 + k, robe=k == 2, cloth=("cloth_w", "cloth_t", "cloth_r")[k % 3])
        kit.animate_walk(root, parts, [beach(xa, 9.5 + 0.6 * k), beach(xb, 10.0 + 0.5 * k)], H, start=f0 + 10 * k,
                         end=end, stride_frames=15, speed=0.7)
    # palm trunks on the sand, ready to be cut and carried
    mb = kit.MB()
    for k in range(5):
        x0, y0 = rng.uniform(-6, 6), rng.uniform(-2.5, 2.5)
        mb.seg((x0, y0, 0.28), (x0 + rng.uniform(3.2, 4.4), y0 + rng.uniform(-0.4, 0.4), 0.28), 0.26, 0.24, "trunk", sides=6)
    logs = mb.obj("S44Logs", c)
    logs.location = (*beach(-4.0, 10.0), H(*beach(-4.0, 10.0)))
    for k, dx in enumerate((0.0, -22.0)):
        x, y = beach(dx, 12.0)
        put(L["net"][k % 2], f"S44Net{k}", c, x, y, face(TX, TY) - math.pi / 2)


# ===================================================================== S45
CANNON_ROW = [(-34.0 + 4.3 * k, 6.5 + 0.35 * math.sin(k * 1.7)) for k in range(6)]
FAKE_AIM = beach(62.0, -112.0)          # the fake guns point the way the ships will come


def build_s45(c, L, ev):
    """The row of palm-trunk 'cannons' on the dune, seen from behind (K54)."""
    rng = random.Random(45)
    end = ev["end"]
    f0, f1 = ev["r45"]
    for ob in [o for o in bpy.data.objects if o.name.startswith(("Palm", "GrovePalm", "Tree", "Bush", "GroveBush"))]:
        d_ = ob.location.y - SY(ob.location.x)
        if -52 < ob.location.x < -4 and 2.0 < d_ < 13.5:
            bpy.data.objects.remove(ob, do_unlink=True)
    for k, (xx, dd) in enumerate(CANNON_ROW):
        x, y = beach(xx, dd)
        root, wheels = kit.make_log_cannon(f"S45Fake{k}", c, seed=10 + k)
        root.location = (x, y, H(x, y) - 0.05)
        root.rotation_euler[2] = face(FAKE_AIM[0] - x, FAKE_AIM[1] - y) + rng.uniform(-0.06, 0.06)
        # a dune mound heaped round each gun
        dn = kit.instance(L["dune"], f"S45Dune{k}", c, (x + NX * 1.2, y + NY * 1.2, H(x, y) - 0.25), rot_z=face(TX, TY) - math.pi / 2,
                          scale=rng.uniform(0.7, 0.95))
        # a man by each gun, some fishermen, some soldiers
        for j, (side, back) in enumerate(((1.6, -1.3), (-1.7, -0.6))):
            sx, sy = x + TX * side - NX * back, y + TY * side - NY * back
            src = L["fisher"][(k + j) % 4] if (k + j) % 3 else L["nair"][(k + j) % 4]
            ob = put(src, f"S45Man{k}_{j}", c, sx, sy, SEA_HEAD + rng.uniform(-0.8, 0.8))
            kit.animate_idle(ob, rng, f0, end, amount=0.03)
    # extra dunes, tussocks and drift on the ridge
    for k in range(10):
        xx, dd = rng.uniform(-44, -8), rng.uniform(8.0, 13.0)
        x, y = beach(xx, dd)
        kit.instance(L["dune"], f"S45Ridge{k}", c, (x, y, H(x, y) - 0.2), rot_z=rng.uniform(0, 3), scale=rng.uniform(0.6, 1.2))
    bush = bpy.data.objects["LibBush0"]
    for k in range(18):
        xx, dd = rng.uniform(-46, -6), rng.uniform(5.0, 11.0)
        x, y = beach(xx, dd)
        if any(math.hypot(x - bx, y - by) < 2.0 for bx, by in [beach(a, b) for a, b in CANNON_ROW]):
            continue
        put(bush, f"S45Tussock{k}", c, x, y, rng.uniform(0, 6), s=rng.uniform(0.35, 0.6), sink=0.05)


# ===================================================================== S46
GUNS46 = [(84.0 + 3.6 * k, 3.3 + 0.25 * (k % 2)) for k in range(5)]
SHIPS46 = [(1, 62.0, -112.0, 24.0, 7.0), (2, 86.0, -128.0, 20.0, 6.0)]


def build_ships46(c, L, ev):
    """Two small Dutch ships come in from the sea, then turn back under the guns (S45 shows them far off, S46 on)."""
    rng = random.Random(46)
    end = ev["end"]
    f0, f1 = ev["r46"]
    t_start = ev["r45"][0]
    head_in = math.atan2(NY, NX)                           # bow toward the beach
    ships = []
    for i, (n, x, off, length, beam) in enumerate(SHIPS46):
        ship = lw.make_sailing_ship(f"S46Ship{i}", c, length, beam, {0: (1, 2), 1: (0, 1, 2)}, 1.3, 40 + i)
        turn_f = ev["turn46"] + i * 16
        pos, hd = {}, {}
        x_, y_ = x, SY(x) + off
        for f in range(t_start - 4, end + 12):
            u = min(1.0, max(0.0, (f - turn_f) / 80.0))
            u = u * u * (3 - 2 * u)
            h = head_in + math.radians(158.0) * u
            speed = 0.35 if f < f0 else (4.0 if f < turn_f else 3.4)
            x_ += math.cos(h) * speed / kit.FPS
            y_ += math.sin(h) * speed / kit.FPS
            pos[f], hd[f] = (x_, y_), h
        ph = rng.uniform(0, 10)
        for f in range(t_start - 4, end + 12, 4):
            (px, py), h = pos[f], hd[f]
            ship.location = (px, py, -0.4 + 0.18 * math.sin(f / 19.0 + ph))
            ship.rotation_euler = (math.radians(1.2 * math.sin(f / 21.0 + ph)),
                                   math.radians(1.8 * math.sin(f / 15.0 + 1 + ph)), h - math.pi / 2)
            ship.keyframe_insert("location", frame=f)
            ship.keyframe_insert("rotation_euler", frame=f)
        ships.append((ship, lambda f, pos=pos: pos[max(min(pos), min(max(pos), int(f)))]))
    return ships


def build_s46(c, L, ev, ships):
    """The shore guns fire; shot lands among the ships; they turn away (K55, K56)."""
    rng = random.Random(46)
    end = ev["end"]
    f0, f1 = ev["r46"]
    aim = SEA_HEAD
    guns = []
    for k, (xx, dd) in enumerate(GUNS46):
        x, y = beach(xx, dd)
        g = kit.instance(L["cannon"], f"S46Gun{k}", c, (x, y, H(x, y) - 0.03), rot_z=SEA_HEAD + 0.12 * (k - 2) / 2)
        guns.append((x, y, g.rotation_euler[2]))
        # an earth screen of sand, and two gunners
        for j in range(5):
            bx, by = x + TX * (j - 2) * 0.55 + NX * -1.5, y + TY * (j - 2) * 0.55 + NY * -1.5
            if j == 2:
                continue
            kit.instance(L["dune"], f"S46Mound{k}_{j}", c, (bx, by, H(bx, by) - 0.1), rot_z=face(TX, TY) - math.pi / 2, scale=0.28)
        for j, (sd, bk) in enumerate(((0.9, 1.2), (-0.9, 1.3))):
            gx, gy = x + TX * sd + NX * bk, y + TY * sd + NY * bk
            ob = put(L["nair"][(k + j) % 4], f"S46Gunner{k}_{j}", c, gx, gy, g.rotation_euler[2] + rng.uniform(-0.3, 0.3))
            kit.animate_idle(ob, rng, f0, end, amount=0.04)
    cmd = put(L["cmdr"][0], "S46Commander", c, *beach(GUNS46[2][0] - 2.0, 6.0), SEA_HEAD)
    kit.animate_idle(cmd, rng, f0, end, amount=0.02)
    # powder barrels and shot stacked behind the guns
    barrel = bpy.data.objects["LibBarrel"]
    for k, (xx, dd) in enumerate(((82.0, 6.4), (83.0, 6.7), (97.0, 6.5), (98.0, 6.2), (90.0, 7.2))):
        put(barrel, f"S46Barrel{k}", c, *beach(xx, dd), rz=rng.uniform(0, 3))
    # volleys: each gun fires a few times, ripple along the line
    for vi, vf in enumerate(ev["fire46"]):
        for k, (x, y, rz) in enumerate(guns):
            fire_gun(c, L, (x, y), rz, vf + 5 * k + rng.randint(0, 3), rng, end, f"S46G{vi}_{k}", size=1.0)
    # shot falls round the ships
    for vi, vf in enumerate(ev["fire46"]):
        for si, (ship, course) in enumerate(ships):
            for q in range(3):
                t = vf + 28 + q * 4 + si * 5
                sx, sy = course(t)
                px, py = sx + rng.uniform(-7, 7), sy + rng.uniform(-7, 7)
                sp = kit.instance(L["splash"][q % 3], f"S46Splash{vi}_{si}_{q}", c, (px, py, 0.0), rot_z=rng.uniform(0, 6), scale=0.0)
                kit.animate_splash(sp, t, size=rng.uniform(0.7, 1.1))


# ===================================================================== S47
def build_s47(c, L, ev):
    """Inside the stockade in the rain: the men count the last rice sacks (K57)."""
    rng = random.Random(47)
    end = ev["end"]
    f0, f1 = ev["r47"]
    crate, barrel = bpy.data.objects["LibCrate"], bpy.data.objects["LibBarrel"]
    sack = L["sack"]
    cu, cv = -2.0, -3.0
    cx, cyy = SW(cu, cv)
    # a few sacks heaped, a couple slumped and empty, open crate of grain
    for k, (du, dv, sc) in enumerate(((0, 0, 1.0), (0.7, 0.2, 1.0), (0.3, 0.8, 1.0), (-0.5, 0.6, 1.0), (0.2, 0.3, 1.0),
                                       (1.6, -0.6, 0.35), (-1.3, -0.5, 0.3))):
        x, y = SW(cu + du, cv + dv)
        z = H(x, y) - 0.02 + (0.45 if k == 4 else 0.0)
        kit.instance(sack, f"S47Sack{k}", c, (x, y, z), rot_z=rng.uniform(0, 6.28), scale=(1.0, 1.0, sc))
    for k, (du, dv) in enumerate(((3.0, 0.5), (3.6, -0.4), (-3.2, -1.0))):
        x, y = SW(cu + du, cv + dv)
        put((crate, barrel, barrel)[k], f"S47Store{k}", c, x, y, rng.uniform(0, 3))
    # the men: standing and crouched round the pile, one pointing at the sacks, others looking on
    men = ((0.0, -1.7, 0), (-1.9, -0.3, 1), (1.9, -0.8, 2), (-1.0, 1.9, 0), (1.3, 1.9, 1), (2.9, 0.5, 2), (-3.0, 1.1, 0))
    for k, (du, dv, i) in enumerate(men):
        x, y = SW(cu + du, cv + dv)
        look = face(cx - x, cyy - y)
        if k in (1, 2, 5):
            ob = put(L["dutch_sit"][i], f"S47Sit{k}", c, x, y, look)
        elif k == 0:
            ob = put(L["officer"], f"S47Count{k}", c, x, y, look)
        else:
            ob = put(L["dutch"][i], f"S47Stand{k}", c, x, y, look)
        kit.animate_idle(ob, rng, f0, end, amount=0.02)
    # a thatched store against the west wall, tents' guy ropes, muskets stacked
    x, y = SW(-12.3, 0.5)
    hut = put(bpy.data.objects["LibHutGable1"], "S47Store", c, x, y, AX + math.pi / 2, s=1.0, sink=0.1)
    mb = kit.MB()
    for q, (du, dv) in enumerate(((5.8, -2.3), (-6.0, -6.2), (8.0, 8.0))):
        for j in range(4):
            a = j * math.tau / 4 + 0.4 * q
            ux, uy = SW(du, dv)
            mb.seg((ux + math.cos(a) * 0.4, uy + math.sin(a) * 0.4, H(ux, uy)), (ux + 0.03, uy + 0.03, H(ux, uy) + 1.4),
                   0.03, 0.025, "iron", sides=4)
            mb.seg((ux + math.cos(a) * 0.4, uy + math.sin(a) * 0.4, H(ux, uy) + 0.55), (ux + math.cos(a) * 0.4 + 0.02, uy + 0.02, H(ux, uy) + 0.62),
                   0.045, 0.045, "plank", sides=4)
    mb.obj("S47Muskets", c)
    # the yard is churned to mud: a dark layer over the sand, and puddles
    mb = kit.MB()
    nu, nv = 15, 12
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            x, y = SW(-14.6 + 29.2 * i / nu + rng.uniform(-0.3, 0.3), -11.6 + 23.2 * j / nv + rng.uniform(-0.3, 0.3))
            row.append(mb.bm.verts.new((x, y, H(x, y) + 0.035 + 0.02 * rng.random())))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            mb.face([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]], "soil_dk" if (i * 7 + j * 3) % 5 else "soil")
    mb.obj("S47Mud", c)
    pts = [SW(rng.uniform(-12, 12), rng.uniform(-9, 9)) for _ in range(8)]
    puddles(c, rng, pts, n_each=3)


# ===================================================================== S48
def build_s48(c, L, ev):
    """The hillside battery fires on the stockade as it does every day (K58)."""
    rng = random.Random(48)
    end = ev["end"]
    f0, f1 = ev["r48"]
    # clear the grove off the hillock so the battery shows, then the battery of S06 (rampart, guns,
    # gunners, screening palms), one gun fires
    bx0, by0 = cw.BATTERY
    for ob in [o for o in bpy.data.objects if o.name.startswith(("Palm", "GrovePalm", "Tree", "Bush", "GroveBush"))]:
        if math.hypot(ob.location.x - bx0, ob.location.y - by0) < 17.0:
            bpy.data.objects.remove(ob, do_unlink=True)
    cw.build_battery(c, bpy.data.collections["Library"], end, shot=ev["shot48"])
    bx, by = cw.BATTERY
    # more gunners, a stack of shot and barrels, a flag
    barrel, crate = bpy.data.objects["LibBarrel"], bpy.data.objects["LibCrate"]
    for k, (dx, dy) in enumerate(((-3.2, 2.2), (-2.6, 3.0), (3.5, 2.0), (4.2, 2.6), (0.5, 4.0))):
        x, y = bx + dx, by + dy
        put((barrel, crate)[k % 2], f"S48Store{k}", c, x, y, rng.uniform(0, 3))
    for k in range(4):
        x, y = bx + rng.uniform(-6, 6), by + rng.uniform(1.0, 6.0)
        ob = put(L["nair"][k % 4], f"S48Man{k}", c, x, y, face(ST["center"][0] - x, ST["center"][1] - y) + rng.uniform(-0.4, 0.4))
        kit.animate_idle(ob, rng, f0, end, amount=0.03)
    x, y = bx + 6.0, by + 4.0
    pw.flag_on_pole(c, "S48Flag", (x, y, H(x, y)), 6.5, 2.2, 1.4, "flag_r", heading=170)
    # a second, quieter shot on the line of the stockade: smoke from the stockade side, a puff of dust from the hit
    sx, sy = SW(6.0, -4.0)
    for q in range(5):
        t = ev["shot48"] + 24 + q * 3
        ob = kit.instance(L["puff_dk"][q % 2], f"S48Dust{q}", c, (sx, sy, H(sx, sy) + 0.3), scale=0.0)
        kit.animate_puff(ob, t, end, (sx + rng.uniform(-0.6, 0.6), sy + rng.uniform(-0.6, 0.6), H(sx, sy) + 0.4),
                         (rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(1.2, 2.2)), s0=0.3, s1=rng.uniform(1.0, 1.8),
                         grow=14.0, drag=1.0, step=4, fade=(t + 30, t + 80))


# ===================================================================== whole set
def build_world(ev):
    end = ev["end"]
    pw.register_palette()
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
    cw.animate_sea(sea, rig_c, end, ev["storm"])
    sun = cw.scene_base(rig_c)
    cw.apply_weather(sun, bpy.data.objects["Haze"], {"storm": ev["storm_all"]})
    cw.build_village(village_c, props_c, plants_c, people_c, lib_c, end)
    lw.tidy_trees()
    lw.build_groves(plants_c, rng)
    lw.build_path(world_c)
    lw.build_hamlets(village_c, rng)
    for ob in [o for o in bpy.data.objects if o.name.startswith(("Palm", "GrovePalm", "Bush", "GroveBush"))]:
        if ob.location.y > 14 and lw.near_path(ob.location.x, ob.location.y, 7.0):
            bpy.data.objects.remove(ob, do_unlink=True)
    cw.build_clouds(kit.new_collection("Clouds"), {"storm": ev["storm"]})
    L = build_lib(lib_c)

    sets = {}
    sets["Stockade"] = kit.new_collection("Stockade_S40-S48")
    lw.build_stockade(sets["Stockade"], lib_c, dict(ev, build=(-300, -250)), full=True)
    build_garrison(sets["Stockade"], L, ev)
    sets["Ring"] = kit.new_collection("Ring_S41-S48")
    build_ring(sets["Ring"], lib_c, L, ev)
    sets["S40"] = kit.new_collection("S40_Column")
    build_s40(sets["S40"], lib_c, L, ev)
    sets["S43"] = kit.new_collection("S43_Fishermen")
    build_s43(sets["S43"], L, ev)
    sets["S44"] = kit.new_collection("S44_Carts")
    build_s44(sets["S44"], L, ev)
    sets["S45"] = kit.new_collection("S45_FakeGuns")
    build_s45(sets["S45"], L, ev)
    sets["Ships"] = kit.new_collection("Ships_S45-S46")
    ships = build_ships46(sets["Ships"], L, ev)
    sets["S46"] = kit.new_collection("S46_ShoreGuns")
    build_s46(sets["S46"], L, ev, ships)
    sets["S47"] = kit.new_collection("S47_Inside")
    build_s47(sets["S47"], L, ev)
    sets["S48"] = kit.new_collection("S48_Battery")
    build_s48(sets["S48"], L, ev)

    r = {k: ev[f"r{k}"] for k in (40, 41, 42, 43, 44, 45, 46, 47, 48)}
    set_vis(sets["Stockade"], [(r[40][0], end)])
    set_vis(sets["Ring"], [(r[41][0], end)])
    set_vis(sets["S40"], [r[40]])
    set_vis(sets["S43"], [r[43]])
    set_vis(sets["S44"], [r[44]])
    set_vis(sets["S45"], [r[45]])
    set_vis(sets["Ships"], [(r[45][0], r[46][1])])
    set_vis(sets["S46"], [r[46]])
    set_vis(sets["S47"], [r[47]])
    set_vis(sets["S48"], [r[48]])
    lw.sway_palms(r[40][0], end, ST["center"], 160, rng, amount=0.05)
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c, sun
