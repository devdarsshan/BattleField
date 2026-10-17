"""Colachel, 5-10 August 1741: the powder barrel, the fire, the surrender, the march (S49-S54; clips 59-66).

The same beach, stockade and siege ring as the siege beats (siege_world), continuing in Surrender.blend.

  S49 (K59) a glowing ball flies in from the hillside battery and drops into a powder barrel in the yard.
  S50 (K60) the barrel goes up; fire runs through the yard, the rice store burns (shared camera with S49).
  S51 (K62) smoke drifts over the burnt stockade; dazed Dutch among the ruins.
  S52 (K64) the Dutch hoist a white flag over the smoking stockade.
  S53 (K65) De Lannoy and the Dutch officers hand their swords to the Travancore commanders on the beach.
  S54 (K66) the prisoners are marched inland along the track toward the hill fort.

New parts live here (stone hill fort, sword, charred stake); everything else is the kit.
"""
import math
import random

import bpy
from mathutils import Vector

import colachel_kit as kit
import colachel_world as cw
import landing_world as lw
import port_world as pw
import siege_world as sw

H = cw.height
SY = cw.shore_y
SW = cw.stockade_world
ST = cw.STOCKADE
AX = math.radians(ST["axis_deg"])
NX, NY, TX, TY = sw.NX, sw.NY, sw.TX, sw.TY
face = sw.face
put = sw.put
beach = sw.beach

POW = SW(1.0, -2.0)                                   # the powder barrels in the yard
RICE = SW(8.5, -0.5)                                  # the thatched rice store
HC = beach(98.0, 7.0)                                 # where the swords are handed over (S53)
FORT = (66.0, 150.0)                                  # the hill fort the prisoners are marched to (S54)
LAUNCH = (cw.BATTERY[0] - 1.0, cw.BATTERY[1] - 1.0)


def ball_pos(u):
    """The glowing ball's path from the battery muzzle to the top powder barrel (u 0..1)."""
    p0 = Vector((LAUNCH[0], LAUNCH[1], H(*LAUNCH) + 1.4))
    p1 = Vector((POW[0], POW[1], H(*POW) + 1.9))
    p = p0 + (p1 - p0) * u
    p.z += 16.0 * 4.0 * u * (1.0 - u)
    return p


def ball_dir(u):
    a, b = ball_pos(max(0.0, u - 0.01)), ball_pos(min(1.0, u + 0.01))
    return (b - a).normalized()


def flat_site(near, r, span=40.0, step=4.0):
    """The flattest ground within `span` metres of `near` for a fort of radius r (smallest height range)."""
    best = None
    x0, y0 = near
    gx = x0 - span
    while gx <= x0 + span:
        gy = y0 - span
        while gy <= y0 + span:
            hs = [H(gx, gy)] + [H(gx + math.cos(k * math.tau / 12) * r, gy + math.sin(k * math.tau / 12) * r) for k in range(12)]
            score = max(hs) - min(hs) + 0.02 * math.hypot(gx - x0, gy - y0)
            if best is None or score < best[0]:
                best = (score, gx, gy)
            gy += step
        gx += step
    return best[1], best[2]


# ===================================================================== new parts
def make_sword(name, c):
    """A sword lying across two hands: steel blade along +Y from a gold hilt at the origin."""
    mb = kit.MB(bevel=0.01)
    mb.box(kit.T(0, 0.42, 0) @ kit.S(0.045, 0.84, 0.012), "steel")
    mb.box(kit.T(0, -0.02, 0) @ kit.S(0.26, 0.035, 0.03), "gold")
    mb.seg((0, -0.04, 0), (0, -0.2, 0), 0.025, 0.02, "gold", sides=5)
    mb.ico(kit.T(0, -0.22, 0), "gold", r=0.035, sub=1)
    return mb.obj(name, c)


def make_char_stake(name, c, h=3.6, r=0.25, seed=0):
    rng = random.Random(seed)
    mb = kit.MB()
    mb.seg((0, 0, 0), (0, 0, h), r, r * 0.9, "char", sides=6, spin=rng.uniform(0, 1))
    mb.seg((0, 0, h), (0, 0, h + rng.uniform(0.3, 0.7)), r * 0.9, 0.04, "iron", sides=6)
    return mb.obj(name, c)


def make_hill_fort(name, c, ground, cx, cy, r=13.0, seed=0):
    """A small stone hill fort: a 12-sided curtain wall with merlons, four round towers, a gate,
    a keep and a red standard (the Udayagiri of S54). Walls follow the slope."""
    rng = random.Random(seed)
    mb = kit.MB(bevel=0.04)
    n = 12
    pts = [(cx + math.cos(k * math.tau / n) * r, cy + math.sin(k * math.tau / n) * r) for k in range(n)]
    gz = [ground(x, y) for x, y in pts]
    top = max(gz) + 2.0
    for k in range(n):
        (ax, ay), (bx, by) = pts[k], pts[(k + 1) % n]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        L = math.hypot(bx - ax, by - ay)
        a = math.atan2(by - ay, bx - ax)
        zb = min(gz[k], gz[(k + 1) % n]) - 1.5
        hgt = (top - zb)
        mb.box(kit.T(mx, my, zb + hgt / 2) @ kit.Rz(a) @ kit.S(L + 0.2, 1.6, hgt), "stone")
        mb.box(kit.T(mx, my, top - 0.1) @ kit.Rz(a) @ kit.S(L + 0.3, 2.0, 0.3), "stone_lt" if "stone_lt" in kit.PALETTE else "stone")
        if k != 9:                                      # k == 9: the gate, facing the track
            for j in range(int(L / 1.2)):
                t = (j + 0.5) / int(L / 1.2) - 0.5
                px, py = mx + math.cos(a) * L * t, my + math.sin(a) * L * t
                mb.box(kit.T(px, py, top + 0.55) @ kit.Rz(a) @ kit.S(0.7, 1.7, 0.9), "stone")
    for k in range(0, n, 3):
        x, y = pts[k]
        zb = gz[k] - 1.5
        mb.cone(kit.T(x, y, (zb + top + 1.4) / 2), "stone", segments=8, r1=2.4, r2=2.2, depth=top + 1.4 - zb)
        mb.cone(kit.T(x, y, top + 2.0), "stone", segments=8, r1=2.6, r2=2.6, depth=0.3)
        mb.cone(kit.T(x, y, top + 3.2), "roof" if "roof" in kit.PALETTE else "stone", segments=8, r1=2.5, r2=0.1, depth=2.2)
    zc = ground(cx, cy)
    mb.box(kit.T(cx, cy, zc + 3.0) @ kit.S(5.5, 4.5, 6.0), "stone")                 # the keep
    mb.box(kit.T(cx, cy, zc + 6.15) @ kit.S(6.0, 5.0, 0.3), "stone")
    gx, gy = pts[9]
    mb.box(kit.T(gx * 0.99 + cx * 0.01, gy, gz[9] + 1.0) @ kit.Rz(math.atan2(gy - cy, gx - cx)) @ kit.S(0.5, 2.6, 2.2), "dark")
    ob = mb.obj(name, c)
    pw.flag_on_pole(c, name + "Flag", (cx, cy, zc + 6.3), 5.0, 2.2, 1.4, "flag_r", heading=200)
    return ob


# ===================================================================== library
def build_lib2(lib):
    """Parts for S49-S54 on top of siege_world's library."""
    L = {}
    L["sword"] = make_sword("LibSSword", lib)
    L["officer_hand"] = kit.make_figure("LibSOffHand", lib, "dutch", seed=7, pose="point")
    L["delannoy_hand"] = kit.make_figure("LibSDLHand", lib, "delannoy", seed=0, pose="point", armed=False)
    L["dutch_unarmed"] = [kit.make_figure(f"LibSDutchUn{k}", lib, "dutch", seed=40 + k, armed=False) for k in range(3)]
    L["char_stake"] = [make_char_stake(f"LibSChar{k}", lib, h=3.4 + 0.22 * k, r=0.24 + 0.014 * k, seed=k) for k in range(4)]
    L["ruin"] = [kit.make_ruin(f"LibSRuin{k}", lib, w=3.4 + k, d=3.0 + 0.6 * k, seed=k) for k in range(2)]
    L["puff_big"] = [kit.make_puff(f"LibSBig{k}", lib, seed=90 + k, m=("smoke_dk", "smoke_md", "smoke_dk")[k]) for k in range(3)]
    L["shell"] = kit.make_shell("LibSShell", lib, r=0.4)
    L["flames2"] = [kit.make_flames(f"LibSFl2_{k}", lib, seed=30 + k, size=0.75) for k in range(3)]
    L["fireball"] = [kit.make_fireball(f"LibSFB{k}", lib, seed=k + 1, r=2.6 + 0.4 * k) for k in range(4)]
    mb = kit.MB()
    mb.cone(kit.T(0, 0, 0.02), "char", segments=12, r1=1.0, r2=0.9, depth=0.04)
    L["scorch"] = mb.obj("LibSScorch", lib)
    mb = kit.MB()
    for k in range(5):
        mb.seg((0.12 * k - 0.24, 0, 0.0), (0.12 * k - 0.24, 0.0, 1.2), 0.03, 0.025, "iron", sides=4)
    mb.box(kit.T(0, 0, 0.5) @ kit.S(0.6, 0.06, 0.06), "plank")
    L["muskets"] = mb.obj("LibSMuskets", lib)
    for k in L["sword"], L["officer_hand"], L["delannoy_hand"], L["shell"], L["scorch"], L["muskets"]:
        kit.hide_source(k)
    for k in L["dutch_unarmed"] + L["char_stake"] + L["ruin"] + L["puff_big"] + L["flames2"] + L["fireball"]:
        kit.hide_source(k)
    return L


# ===================================================================== yard (S49 on)
def build_yard(c, L, ev):
    """The Dutch yard before the blast: powder barrels, the rice store, soldiers, stores (S49)."""
    rng = random.Random(49)
    end = ev["end"]
    f0 = ev["r49"][0]
    barrel, crate, sack = bpy.data.objects["LibBarrel"], bpy.data.objects["LibCrate"], L["sack"]
    px, py = POW
    people, props = [], []
    # the powder: two barrels and one on top (the ball's target), more round them, covered with a sail
    for k, (dx, dy, z) in enumerate(((-0.45, 0.0, 0.0), (0.45, 0.0, 0.0), (0.0, 0.0, 0.95), (-1.1, 0.8, 0.0), (1.2, 0.7, 0.0),
                                      (0.1, 1.3, 0.0), (-0.3, -1.0, 0.0))):
        b = kit.instance(barrel, f"Powder{k}", c, (px + dx, py + dy, H(px + dx, py + dy) - 0.02 + z), rot_z=rng.uniform(0, 3), scale=1.18)
        props.append(b)
    for k, (dx, dy) in enumerate(((2.4, -0.6), (-2.6, 0.5), (1.6, 2.4), (-1.5, -2.2))):
        props.append(put(crate, f"YardCrate{k}", c, px + dx, py + dy, rng.uniform(0, 3)))
    # the rice store: a thatched shed with sacks heaped before it
    rx, ry = RICE
    hut = put(bpy.data.objects["LibHutGable0"], "RiceStore", c, rx, ry, AX + math.pi / 2, sink=0.1)
    for k in range(10):
        a = rng.uniform(-1.0, 1.0)
        sx, sy = SW(8.5 - 3.4 + rng.uniform(-0.9, 0.9), -0.5 + rng.uniform(-1.8, 1.8))
        props.append(put(sack, f"RiceSack{k}", c, sx, sy, rng.uniform(0, 3)))
    # the garrison in the yard: some about the powder, some sitting, a few on the wall line
    for k, (du, dv, kind) in enumerate(((-2.6, -4.2, "st"), (4.6, -4.4, "st"), (-4.2, -1.0, "sit"), (-3.8, 0.4, "sit"),
                                         (5.2, 1.4, "st"), (0.0, -5.8, "st"), (3.0, 1.8, "st"), (-1.0, 1.4, "sit"),
                                         (6.0, -3.6, "sit"), (-5.6, -3.4, "st"), (2.2, -5.0, "st"), (-6.5, 0.9, "st"))):
        x, y = SW(1.0 + du, -2.0 + dv)
        look = face(px - x, py - y) + rng.uniform(-0.6, 0.6)
        src = L["dutch_sit"][k % 3] if kind == "sit" else L["dutch"][k % 3]
        ob = put(src, f"YardMan{k}", c, x, y, look)
        thrown = math.hypot(x - px, y - py) < 7.5
        kit.animate_idle(ob, rng, f0, ev["boom"] - 3 if thrown else end, amount=0.025)
        people.append(ob)
    # tents near the blast are swapped for ruins when it goes
    tents = [o for o in bpy.data.objects if o.name.startswith("StockadeTent")]
    near = [o for o in tents if math.hypot(o.location.x - px, o.location.y - py) < 15.0]
    return dict(people=people, props=props, hut=hut, tents=near)


# ===================================================================== S49: the ball
def build_ball(c, L, ev):
    """The glowing ball from the battery to the powder, a trail of sparks and smoke behind it."""
    rng = random.Random(490)
    f0, f1 = ev["launch"], ev["hit"]
    kit.fx_materials()
    mb = kit.MB()
    mb.ico(kit.Matrix.Identity(4), "fx_core", r=0.42, sub=1, jitter=0.1, rng=rng)
    for k in range(8):
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
        mb.seg(d * 0.3, d * rng.uniform(0.8, 1.2), 0.1, 0.0, "fx_fire", sides=4)
    ball = mb.obj("GlowBall", c)
    ball.scale = (1.8, 1.8, 1.8)
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        ball.scale = (0, 0, 0)
        ball.keyframe_insert("scale", frame=f0 - 1)
        ball.scale = (1.8, 1.8, 1.8)
        ball.keyframe_insert("scale", frame=f0)
        for f in range(f0, f1 + 1, 2):
            u = (f - f0) / max(1, f1 - f0)
            ball.location = tuple(ball_pos(u))
            ball.rotation_euler = (u * 14, u * 9, 0)
            ball.keyframe_insert("location", frame=f)
            ball.keyframe_insert("rotation_euler", frame=f)
        ball.scale = (1.8, 1.8, 1.8)
        ball.keyframe_insert("scale", frame=f1)
        ball.scale = (0, 0, 0)
        ball.keyframe_insert("scale", frame=f1 + 1)
    finally:
        prefs.keyframe_new_interpolation_type = old
    # sparks and smoke left along the path
    ember = L["flames"]
    for k, f in enumerate(range(f0, f1, 3)):
        u = (f - f0) / max(1, f1 - f0)
        p = ball_pos(u)
        s = kit.instance(L["puff"][k % 3], f"BallSmoke{k}", c, tuple(p), scale=0.0)
        kit.animate_puff(s, f, min(ev["end"], f + 80), tuple(p), (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.5),
                         s0=0.15, s1=rng.uniform(0.35, 0.6), grow=14.0, drag=0.5, step=5, fade=(f + 20, f + 80))
    # a point of light travels with the ball
    ld = bpy.data.lights.new("BallLight", "POINT")
    ld.color = (1.0, 0.6, 0.2)
    ld.shadow_soft_size = 1.0
    lo = bpy.data.objects.new("BallLight", ld)
    c.objects.link(lo)
    for f in range(f0, f1 + 1, 4):
        lo.location = tuple(ball_pos((f - f0) / max(1, f1 - f0)))
        lo.keyframe_insert("location", frame=f)
        ld.energy = 1500.0
        ld.keyframe_insert("energy", frame=f)
    ld.energy = 0.0
    ld.keyframe_insert("energy", frame=f1 + 1)
    return ball


# ===================================================================== S50: the blast
def build_blast(c, L, ev, yard):
    rng = random.Random(50)
    end = ev["end"]
    boom = ev["boom"]
    px, py = POW
    gz = H(px, py)
    kit.fx_materials()
    # fireballs
    for k, (off, seed) in enumerate((((0, 0, 2.4), 0), ((1.4, -0.9, 4.2), 1), ((-1.5, 1.0, 3.8), 2), ((0.3, 1.5, 6.0), 3))):
        fb = kit.instance(L["fireball"][seed], f"Blast{k}", c, (px + off[0], py + off[1], gz + off[2]), scale=0.0)
        fb.rotation_euler = (rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 6))
        for f, s in ((boom - 1, 0.0), (boom + 2 + k, 0.75), (boom + 7 + k, 1.0), (boom + 26, 1.1), (boom + 44, 0.8),
                     (boom + 76 - 6 * k, 0.0)):
            fb.scale = (s, s, s)
            fb.keyframe_insert("scale", frame=f)
        fb.keyframe_insert("rotation_euler", frame=boom)
        fb.rotation_euler.z += 0.5
        fb.keyframe_insert("rotation_euler", frame=boom + 76)
    ld = bpy.data.lights.new("BlastLight", "POINT")
    ld.color = (1.0, 0.62, 0.25)
    ld.shadow_soft_size = 3.0
    lo = bpy.data.objects.new("BlastLight", ld)
    c.objects.link(lo)
    lo.location = (px, py, gz + 5.0)
    for f, e in ((boom - 1, 0.0), (boom + 2, 30000.0), (boom + 12, 20000.0), (boom + 40, 8000.0), (boom + 90, 4000.0), (end, 2500.0)):
        ld.energy = e
        ld.keyframe_insert("energy", frame=f)
    # barrels, crates and sacks near the powder are thrown outward
    for ob in yard["props"]:
        if ob.name.startswith("RiceSack"):
            continue
        d = Vector((ob.location.x - px, ob.location.y - py, 0))
        d = d.normalized() if d.length > 0.1 else Vector((1, 0, 0))
        sp = rng.uniform(4, 9)
        kit.animate_ballistic(ob, boom + rng.randint(0, 2), tuple(ob.location), (d.x * sp, d.y * sp, rng.uniform(5, 11)), H, end,
                              spin=(rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(-3, 3)), hide_before=False)
    # the men nearest are thrown back; the rest are knocked about
    for ob in yard["people"]:
        dist = math.hypot(ob.location.x - px, ob.location.y - py)
        d = Vector((ob.location.x - px, ob.location.y - py, 0)).normalized()
        if dist < 7.5:
            sp = 6.5 - 0.6 * dist
            kit.animate_ballistic(ob, boom + 1, tuple(ob.location), (d.x * sp, d.y * sp, 5.5), H, end, spin=(2.2, 0.5, 1.0),
                                  hide_before=False)
    # debris: planks, thatch, beams flung outward
    for k in range(34):
        mb = kit.MB(bevel=0.01)
        kind = k % 3
        if kind == 0:
            mb.box(kit.S(0.22, rng.uniform(1.2, 2.4), 0.07), "plank")
        elif kind == 1:
            mb.box(kit.S(rng.uniform(0.6, 1.2), rng.uniform(0.5, 1.0), 0.14), rng.choice(("thatch", "thatch_dk")))
        else:
            mb.box(kit.S(0.12, rng.uniform(0.6, 1.3), 0.12), "beam")
        ob = mb.obj(f"Debris{k}", c)
        a = rng.uniform(0, math.tau)
        sp = rng.uniform(5, 12)
        kit.animate_ballistic(ob, boom, (px, py, gz + rng.uniform(1.5, 3.5)), (math.cos(a) * sp, math.sin(a) * sp, rng.uniform(6, 14)),
                              H, end, spin=(rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(-4, 4)))
    # smoke: a burst, then columns that keep rising
    for k in range(18):
        a = rng.uniform(0, math.tau)
        ob = kit.instance(L["puff_big"][k % 3], f"BlastSmoke{k}", c, (px, py, gz + 3), scale=0.0)
        v = (math.cos(a) * rng.uniform(1.5, 3.5), math.sin(a) * rng.uniform(1.5, 3.5), rng.uniform(2.0, 6.0))
        kit.animate_puff(ob, boom + 2 + k % 5, boom + 400, (px + math.cos(a), py + math.sin(a), gz + rng.uniform(2.5, 6)), v,
                         s0=0.7, s1=rng.uniform(1.4, 2.2), grow=20, drag=0.35, fade=(boom + 260, boom + 400))
    for col, (cx, cy) in enumerate(((px, py), (RICE[0], RICE[1]))):
        f = boom + 6 if col == 0 else ev["rice"]
        k = 0
        while f < ev["r52"][0] - 40:
            ob = kit.instance(L["puff_big"][k % 3], f"Column{col}_{k}", c, (cx, cy, H(cx, cy) + 3), scale=0.0)
            life = 300
            kit.animate_puff(ob, f, min(end, f + life), (cx + rng.uniform(-1.2, 1.2), cy + rng.uniform(-1.2, 1.2), H(cx, cy) + rng.uniform(2.5, 4.5)),
                             (0.55 + rng.uniform(-0.3, 0.3), 0.35 + rng.uniform(-0.3, 0.3), rng.uniform(3.2, 4.4)), drag=0.15,
                             s0=0.9, s1=rng.uniform(1.8, 2.8), grow=34, step=8, fade=(f + life - 120, f + life))
            k += 1
            f += 7
    # the yard burns: flames at the blast, then spreading to the tents and the rice store
    r51 = ev["r51"][0]

    def burn(fl, start, s):
        kit.animate_flicker(fl, rng, start, r51)
        for f, k in ((r51, 1.0), (r51 + 160, 0.32), (ev["r52"][0], 0.26)):
            fl.scale = (s * 1.5 * k, s * 1.5 * k, s * 1.5 * k)
            fl.keyframe_insert("scale", frame=f)
    for k, (dx, dy, s) in enumerate(((0.0, 0.0, 1.6), (-1.6, 1.0, 1.1), (1.5, -0.8, 1.2), (1.2, 1.3, 0.9), (-1.4, -1.2, 1.0))):
        fl = kit.instance(L["flames2"][k % 3], f"YardFlames{k}", c, (px + dx, py + dy, gz + 0.1), scale=0.0)
        fl.keyframe_insert("scale", frame=boom + 7)
        fl.scale = (s, s, s)
        fl.keyframe_insert("scale", frame=boom + 14)
        burn(fl, boom + 16, s / 1.5)
    sc = kit.instance(L["scorch"], "BlastScorch", c, (px, py, gz + 0.06), scale=0.0)
    for f, s in ((boom - 1, 0.0), (boom + 4, 5.0)):
        sc.scale = (s, s, 1)
        sc.keyframe_insert("scale", frame=f)
    # tents and the rice store: flames first, then they are swapped for ruins
    items = [(t.location.x, t.location.y, t, 4.0, ev["spread"] + 10 * i) for i, t in enumerate(yard["tents"])]
    items.append((RICE[0], RICE[1], yard["hut"], 5.2, ev["rice"]))
    for i, (x, y, ob, w, t0) in enumerate(items):
        for j in range(3):
            fl = kit.instance(L["flames2"][(i + j) % 3], f"Burn{i}_{j}", c, (x + rng.uniform(-1.2, 1.2), y + rng.uniform(-1.2, 1.2), H(x, y) + 0.4),
                              scale=0.0)
            fl.keyframe_insert("scale", frame=t0 + j * 5 - 1)
            fl.scale = (1.5, 1.5, 1.5)
            fl.keyframe_insert("scale", frame=t0 + j * 5 + 10)
            burn(fl, t0 + j * 5 + 12, 1.0)
        swap = t0 + 60
        ob.scale = (1, 1, 1)
        ob.keyframe_insert("scale", frame=swap - 1)
        ob.scale = (0, 0, 0)
        ob.keyframe_insert("scale", frame=swap)
        ru = kit.instance(L["ruin"][i % 2], f"Ruin{i}", c, (x, y, H(x, y)), rot_z=ob.rotation_euler[2], scale=0.0)
        ru.keyframe_insert("scale", frame=swap - 1)
        ru.scale = (1, 1, 1)
        ru.keyframe_insert("scale", frame=swap)
    for ob in [o for o in bpy.data.objects if o.name.startswith("StockadeFlag")]:    # the orange flag burns down
        ob.keyframe_insert("scale", frame=boom + 20)
        ob.scale = (0, 0, 0)
        ob.keyframe_insert("scale", frame=boom + 21)
    for k in range(10):                                                    # embers and scattered fires about the yard
        a = rng.uniform(0, math.tau)
        r = rng.uniform(5, 11)
        x, y = px + math.cos(a) * r, py + math.sin(a) * r
        fl = kit.instance(L["flames"][k % 2], f"SpotFire{k}", c, (x, y, H(x, y) + 0.05), scale=0.0)
        fl.keyframe_insert("scale", frame=boom + 20 + k * 5)
        fl.scale = (1.3, 1.3, 1.3)
        fl.keyframe_insert("scale", frame=boom + 26 + k * 5)
        burn(fl, boom + 30 + k * 5, 0.87)
    # charred posts: the wall blackens near the blast, post by post
    from_siege = kit.stockade_posts(ST["center"], ST["axis_deg"], ST["half_u"], ST["half_v"], 3.5, 3)
    n = 0
    for (x, y, side, s, Lw, inw) in from_siege:
        d = math.hypot(x - px, y - py)
        if d > 14.5:
            continue
        ob = kit.instance(L["char_stake"][n % 4], f"Charred{n}", c, (x, y, H(x, y) - 0.3), rot_z=rng.uniform(0, 6.28), scale=(1.12, 1.12, 1.02))
        t0 = boom + 12 + int(d * 4.0)
        ob.scale = (0, 0, 0)
        ob.keyframe_insert("scale", frame=t0 - 1)
        ob.scale = (1.12, 1.12, 1.02)
        ob.keyframe_insert("scale", frame=t0)
        n += 1


# ===================================================================== S51-S53 aftermath in the yard
def build_aftermath(c, L, ev):
    """After the blast: the dazed garrison among the ruins (S51), the flag party (S52)."""
    rng = random.Random(51)
    end = ev["end"]
    f0 = ev["r51"][0]
    px, py = POW
    for k in range(16):
        u, v = rng.uniform(-11, 11), rng.uniform(-8.5, 8.5)
        x, y = SW(u, v)
        if math.hypot(x - px, y - py) < 3.0:
            continue
        look = rng.uniform(0, 6.28)
        r = rng.random()
        if r < 0.25:
            ob = put(L["dutch_sit"][k % 3], f"DazedSit{k}", c, x, y, look)
        else:
            ob = put(L["dutch"][k % 3], f"Dazed{k}", c, x, y, look)
            if r > 0.88:                                        # a few men lie where they fell
                ob.rotation_euler[0] = math.radians(-82)
                ob.location.z += 0.25
        kit.animate_idle(ob, rng, f0, end, amount=0.02)
    # blackened ground and scattered scorch about the yard
    for k in range(8):
        x, y = SW(rng.uniform(-11, 11), rng.uniform(-8, 8))
        s = kit.instance(L["scorch"], f"Scorch{k}", c, (x, y, H(x, y) + 0.05), scale=(rng.uniform(1.5, 3.2),) * 2 + (1,))
    for k in range(6):                                          # smoke thread from the ruins
        x, y = SW(rng.uniform(-10, 10), rng.uniform(-6, 6))
        for j in range(12):
            born = f0 + j * 36 + rng.randint(0, 20)
            ob = kit.instance(L["puff_dk"][j % 2], f"RuinSmoke{k}_{j}", c, (x, y, H(x, y) + 0.6), scale=0.0)
            kit.animate_puff(ob, born, min(end, born + 200), (x, y, H(x, y) + 0.6), (0.6, 0.3, 1.5), s0=0.3, s1=0.9, grow=40.0,
                             drag=0.2, step=8, fade=(born + 100, born + 200))


def build_s52(c, L, ev):
    """The white flag goes up the pole while the Dutch stand about with lowered muskets (K64)."""
    rng = random.Random(52)
    end = ev["end"]
    f0, f1 = ev["r52"]
    bx, by = SW(-6.0, -9.0)
    gz = H(bx, by)
    mb = kit.MB()
    mb.seg((bx, by, gz), (bx, by, gz + 10.4), 0.12, 0.08, "post", sides=6)
    mb.ico(kit.T(bx, by, gz + 10.5), "brass", r=0.16, sub=1)
    mb.obj("WhitePole", c)
    flag = pw.make_flag("WhiteFlag", c, w=2.8, h=1.7, m="white")
    flag.rotation_euler[2] = math.radians(200)
    h0, h1 = ev["hoist"], ev["hoist"] + 100
    for f, z in ((f0 - 1, gz + 2.3), (h0, gz + 2.3), (h1, gz + 10.0), (end, gz + 10.0)):
        flag.location = (bx + 0.1, by, z)
        flag.keyframe_insert("location", frame=f)
    # men round the foot of the pole: one hauling the halyard, the rest standing with muskets lowered
    hand = bpy.data.objects.get("LibSDutchSwordUp")
    for k in range(10):
        a = k * math.tau / 10 + rng.uniform(-0.2, 0.2)
        r = rng.uniform(1.8, 4.0)
        x, y = bx + math.cos(a) * r, by + math.sin(a) * r
        ob = put(L["dutch"][k % 3], f"FlagMan{k}", c, x, y, face(bx - x, by - y) + rng.uniform(-0.4, 0.4))
        kit.animate_idle(ob, rng, f0, end, amount=0.02)
    # Travancore soldiers looking in over the wall, high on the ground outside (visible over the posts)
    for k, (u, v) in enumerate(((-8.0, -15.0), (-3.0, -15.5), (3.0, -15.0), (9.0, -15.5), (-12.0, 15.5), (-6.0, 15.2), (6.0, 15.3))):
        x, y = SW(u, v)
        if H(x, y) < 0.15:
            continue
        ob = put(L["nair"][k % 4], f"FlagWatcher{k}", c, x, y, face(bx - x, by - y))
        kit.animate_idle(ob, rng, f0, end, amount=0.03)


# ===================================================================== S53: the swords
def build_s53(c, L, ev):
    """Dutch officers, De Lannoy first, hand their swords hilt-first to Travancore commanders (K65)."""
    rng = random.Random(53)
    end = ev["end"]
    f0, f1 = ev["r53"]
    hx, hy = HC
    pairs = 6
    for i in range(pairs):
        t = (i - (pairs - 1) / 2) * 2.3
        ox, oy = hx + TX * t - NX * 1.25, hy + TY * t - NY * 1.25            # Dutch, seaward side, facing inland
        cx_, cy_ = hx + TX * t + NX * 1.25, hy + TY * t + NY * 1.25          # Travancore commander, facing the sea
        dl = i == 2
        src = L["delannoy_hand"] if dl else L["officer_hand"]
        rz = face(NX, NY)
        o = put(src, "DeLannoy" if dl else f"Officer{i}", c, ox, oy, rz, s=1.02)
        kit.animate_idle(o, rng, f0, end, amount=0.012)
        cmd = put(L["cmdr"][i % 2], f"Commander{i}", c, cx_, cy_, face(-NX, -NY), s=1.03)
        kit.animate_idle(cmd, rng, f0, end, amount=0.012)
        # the sword across the officer's hand, hilt toward the commander
        hand = Vector((ox, oy, H(ox, oy))) + kit.Rz(rz) @ Vector((-0.5, 0.7, 1.36))
        sw_ = kit.instance(L["sword"], f"Sword{i}", c, tuple(hand), rot_z=rz + math.pi / 2 + 0.2)
    # Travancore ranks behind the commanders, standing to attention
    n = 0
    for r in range(4):
        for k in range(17):
            t = (k - 8) * 1.55 + rng.uniform(-0.1, 0.1)
            d = 4.0 + r * 1.55
            x, y = hx + TX * t + NX * d, hy + TY * t + NY * d
            ob = put(L["nair"][n % 4], f"Rank{n}", c, x, y, face(-NX, -NY) + rng.uniform(-0.06, 0.06))
            kit.animate_idle(ob, rng, f0, end, amount=0.015)
            n += 1
    # Dutch prisoners drawn up on the left and right of the handover, unarmed, heads down
    for side, tt in ((-1, -9.5), (1, 9.5)):
        for r in range(3):
            for k in range(6):
                x = hx + TX * (tt + side * r * 1.3) - NX * (1.0 - 1.4 * k + 0.0) - NX * 0.0
                y = hy + TY * (tt + side * r * 1.3) - NY * (1.0 - 1.4 * k)
                if H(x, y) < 0.2:
                    continue
                ob = put(L["dutch_unarmed"][(r + k) % 3], f"Prisoner{side}_{r}_{k}", c, x, y, face(-side * TX, -side * TY) + rng.uniform(-0.2, 0.2))
                ob.rotation_euler[0] = 0.12
                kit.animate_idle(ob, rng, f0, end, amount=0.015)
    # their muskets stacked on the sand, a drum, a flag
    for k in range(6):
        x, y = hx + TX * (rng.uniform(-3, 3)) - NX * rng.uniform(5.5, 6.5), hy + TY * rng.uniform(-3, 3) - NY * rng.uniform(5.5, 6.5)
        if H(x, y) > 0.2:
            put(L["muskets"], f"MuskStack{k}", c, x, y, rng.uniform(0, 6))
    x, y = hx + NX * 7.5 + TX * 4.0, hy + NY * 7.5 + TY * 4.0
    pw.flag_on_pole(c, "S53Standard", (x, y, H(x, y)), 6.5, 2.4, 1.5, "flag_r", heading=160)


# ===================================================================== S54: the march
def build_s54(c, lib, L, ev):
    """The prisoners marched inland along the track, guarded; the hill fort ahead (K66)."""
    rng = random.Random(54)
    end = ev["end"]
    f0, f1 = ev["r54"]
    dt, nt = [], []
    for k in range(3):
        for kind, tpl in (("dutch", dt), ("nair" if k % 2 else "nair_spear", nt)):
            root, parts = kit.make_walker(f"LibS54{kind}{k}", lib, kind, seed=240 + k)
            root.location = (0, 0, -500)
            for p in parts.values():
                p.hide_render = True
            tpl.append(parts)
    n = 0
    spd = 1.55
    for r in range(18):
        for fl in range(3):
            s0 = 40.0 - r * 2.3
            lat = (fl - 1) * 1.2
            root, parts = kit.clone_walker(dt[n % 3], f"S54Prisoner{n}", c)
            wps = sw.route(max(s0, -2.0), max(s0, -2.0) + spd * (f1 + 20 - (f0 - 60)) / kit.FPS, lat)
            kit.animate_walk(root, parts, wps, H, start=f0 - 60 + (r + fl) % 4, end=f1 + 20, stride_frames=15, swing=0.4, speed=spd)
            n += 1
    m = 0
    for r in range(11):
        for side in (-1, 1):
            s0 = 40.0 - r * 3.6
            lat = side * 3.2
            root, parts = kit.clone_walker(nt[m % 3], f"S54Guard{m}", c)
            wps = sw.route(max(s0, -2.0), max(s0, -2.0) + spd * (f1 + 20 - (f0 - 60)) / kit.FPS, lat)
            kit.animate_walk(root, parts, wps, H, start=f0 - 60 + m % 5, end=f1 + 20, stride_frames=15, swing=0.4, speed=spd)
            m += 1
    (px, py), _ = lw.path_point(10.0)
    pw.flag_on_pole(c, "S54Standard", (px + 4.0, py, H(px + 4.0, py)), 6.0, 2.2, 1.4, "flag_r", heading=200)
    fx, fy = flat_site(FORT, 15.0)
    for ob in [o for o in bpy.data.objects if o.name.startswith(("Hamlet", "Tree", "Palm", "GrovePalm", "Bush", "GroveBush"))]:
        if math.hypot(ob.location.x - fx, ob.location.y - fy) < 19.0:
            bpy.data.objects.remove(ob, do_unlink=True)
    make_hill_fort("HillFort", c, H, fx, fy, r=15.0, seed=5)


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
    cw.animate_sea(sea, rig_c, end, ev["storm_all"])
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
    L = sw.build_lib(lib_c)
    L.update(build_lib2(lib_c))

    sets = {}
    sets["Stockade"] = kit.new_collection("Stockade")
    lw.build_stockade(sets["Stockade"], lib_c, dict(ev, build=(-300, -250)), full=True)
    sw.dim_stockade_tents()
    sw.build_low_clouds(kit.new_collection("LowClouds"), random.Random(12))
    sets["Ring"] = kit.new_collection("Ring")
    sw.build_ring(sets["Ring"], lib_c, L, dict(ev, r41=(ev["r49"][0], end)))
    sets["Yard"] = kit.new_collection("Yard_S49")
    yard = build_yard(sets["Yard"], L, ev)
    sets["Ball"] = kit.new_collection("Ball_S49")
    build_ball(sets["Ball"], L, ev)
    sets["Blast"] = kit.new_collection("Blast_S50")
    build_blast(sets["Blast"], L, ev, yard)
    sets["After"] = kit.new_collection("Aftermath_S51")
    build_aftermath(sets["After"], L, ev)
    sets["S52"] = kit.new_collection("S52_Flag")
    build_s52(sets["S52"], L, ev)
    sets["S53"] = kit.new_collection("S53_Swords")
    build_s53(sets["S53"], L, ev)
    sets["S54"] = kit.new_collection("S54_March")
    build_s54(sets["S54"], lib_c, L, ev)

    r = {k: ev[f"r{k}"] for k in range(49, 55)}
    lw.set_vis(sets["Ring"], [(r[49][0], end)])
    lw.set_vis(sets["Ball"], [r[49]])
    lw.set_vis(sets["Blast"], [(r[50][0] - 2, end)])
    lw.set_vis(sets["After"], [(r[51][0], r[53][1])])
    lw.set_vis(sets["S52"], [(r[52][0], r[53][1])])
    lw.set_vis(sets["S53"], [r[53]])
    lw.set_vis(sets["S54"], [r[54]])
    # the yard is only seen to S53 (people are swapped by the aftermath crowd) - leave it visible; blast moves it
    lw.set_vis(sets["Yard"], [(r[49][0], r[53][1])])
    lw.sway_palms(r[49][0], end, ST["center"], 160, rng, amount=0.05)
    for ob in lib_c.objects:
        kit.hide_source(ob)
    return rig_c, sun
