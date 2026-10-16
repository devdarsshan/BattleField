"""Varkala cliffs (S27, clip 34): the allies push along the clifftop road; a wall of Nair
warriors with swords raised and round shields blocks it; the allies halt and turn back.

Laid out to match the Flow reference frames/flow_refs/K34: tall stepped red laterite cliffs
drop to a strip of golden beach with fallen laterite boulders and the faceted turquoise sea
(left of frame); the dirt road runs along the clifftop between grass verges, with palms along
the cliff edge and on a higher terrace behind a second red laterite bank (right of frame).
A solid block of red-turbaned Nairs (many ranks, shields, swords up) fills the road; the
allied column (blue-coated Dutch with white cross-belts, the rajas' men in white mundus and
coloured turbans, an orange Dutch flag) marches up, halts, and turns back. No signs, no text.

Coordinates: metres, Z up. The road runs along +Y (the allies march toward +Y); the sea is
to -X. Sea level z = 0; the clifftop is at TOP. The cliff is a real heightfield with a sharp
stepped drop (cliff_e(y) is the edge), plus jutting laterite slabs and fallen boulders.
Reused: sky/sun/haze (colachel_world.scene_base), the faceted sea (make_faceted_sea),
palms, bushes, trees and every figure (colachel_kit), big-leaf plants (pepper_world), the
waving flag (port_world). New kit parts used: sword_up pose, allied soldiers, animate_route
(halt and turn back), animate_bob, make_boulder.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

import colachel_kit as kit
import colachel_world as cw
import pepper_world as pw
import port_world as ptw
from colachel_kit import T, Rx, Ry, Rz, S

TAU = math.tau
TOP = 22.0                 # clifftop level
ROAD = (-5.5, 5.5)         # x range of the dirt road
BANK_X = 8.5               # foot of the inland laterite bank (right of frame)
BANK_H = 6.5
NAIR_FRONT = -14.0         # y of the front rank of the Nair wall
NAIR_DEPTH = 19.0
ALLY_FRONT = -28.5         # y of the allied front rank at the start of the clip
HALT_FRONT = -20.0         # where the allied front halts


def _n(x, y, s, o=0.0):
    return noise.noise(Vector((x / s + o, y / s - o, o * 0.37)))


_smooth = cw._smooth


def cliff_e(y):
    """x of the cliff edge: a wavy line with headlands and sharp gullies."""
    return -9.5 + 2.2 * math.sin(y / 21.0 + 0.6) + 1.8 * _n(0.0, y, 9.0, 1.3) + 0.9 * _n(0.0, y, 2.6, 3.1)


def shore_x(y):
    return cliff_e(y) - 13.0 - 2.5 * math.sin(y / 31.0 + 1.0) - 1.2 * _n(0.0, y, 12.0, 5.5)


def height(x, y):
    e = cliff_e(y)
    if x >= e:
        h = TOP + 0.25 * _n(x, y, 6.0, 2.2) * min(1.0, (x - e) / 2.0)
        if ROAD[0] - 0.5 < x < ROAD[1] + 0.5:
            h -= 0.12
        b = BANK_X + 0.9 * _n(0.0, y, 7.0, 5.0) + 0.5 * _n(0.0, y, 2.2, 1.0)
        if x > b:
            h += BANK_H * _smooth(b, b + 1.6, x) + 0.6 * _n(x, y, 4.0, 9.0) * _smooth(b + 1.6, b + 4, x)
        return h
    u = e - x
    # stepped face: a sheer upper wall, a ledge, a second wall down to the foot of the cliff
    s1 = 1.2 + 0.4 * _n(0.0, y, 5.0, 7.0)
    l0 = 2.0 + 0.8 * _n(0.0, y, 6.0, 8.0)
    s2 = l0 + 1.6 + 0.4 * _n(0.0, y, 4.0, 2.0)
    mid = 9.5 + 2.0 * _n(0.0, y, 8.0, 4.0)
    z = TOP - mid * _smooth(0.0, s1, u) - (TOP - 2.6 - mid) * _smooth(l0, s2, u)
    z += 0.35 * _n(x, y, 1.6, 6.6) * (1 - _smooth(s2, s2 + 1, u))     # rough rock
    if u > s2:                                            # the beach, down to the sea
        d = x - shore_x(y)
        z = min(z, 2.6 * _smooth(-1.0, e - s2 - shore_x(y), d) + 0.04 * d - 0.3)
    return z


ground = height


def _axis(a0, a1, d0, d1, fine, coarse):
    vals, v = [], a0
    while v < a1:
        vals.append(v)
        v += fine if d0 <= v < d1 else coarse
    return vals + [a1]


def make_terrain(coll, seed=3):
    rng = random.Random(seed)
    xs = _axis(-130.0, 140.0, -24.0, 14.0, 0.5, 3.0)
    ys = _axis(-170.0, 260.0, -95.0, 70.0, 1.0, 3.0)
    bm = bmesh.new()
    grid = []
    for j, y in enumerate(ys):
        row = []
        for i, x in enumerate(xs):
            jx = jy = 0.0
            if 0 < i < len(xs) - 1 and 0 < j < len(ys) - 1:
                sx = 0.5 if -24 <= x < 14 else 3.0
                sy = 1.0 if -95 <= y < 70 else 3.0
                jx, jy = rng.uniform(-0.25, 0.25) * sx, rng.uniform(-0.25, 0.25) * sy
            px, py = x + jx, y + jy
            row.append(bm.verts.new((px, py, height(px, py))))
        grid.append(row)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    names = ["sand", "sand_wet", "laterite", "laterite_dk", "laterite_rd", "grass", "ghat_lo", "field_dirt", "sand"]
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        nz = f.normal.z
        e = cliff_e(c.y)
        if nz < 0.72:                                    # rock faces
            k = _n(c.x, c.y * 0.3, 2.0, 4.1) + rng.uniform(-0.35, 0.35)
            f.material_index = 3 if k < -0.2 else (4 if k > 0.45 else 2)
        elif c.z < 3.2:
            f.material_index = 1 if c.x - shore_x(c.y) < 2.5 else 0
        elif c.z < TOP - 0.6 and c.x < e:
            f.material_index = 4                          # ledges
        elif ROAD[0] < c.x < ROAD[1]:
            f.material_index = 7 if rng.random() > 0.15 else 8
        elif c.x < e + 0.8 or (BANK_X - 0.5 < c.x < BANK_X + 1.2 and c.z > TOP + 0.5):
            f.material_index = 4                          # the red lip of the cliff
        else:
            f.material_index = 5 if rng.random() > 0.35 else 6
    me = bpy.data.meshes.new("Terrain")
    bm.to_mesh(me)
    bm.free()
    for m in names:
        me.materials.append(kit.mat(m))
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new("Terrain", me)
    coll.objects.link(ob)
    return ob


def build_rock_facets(coll, seed=11):
    """Big angular laterite chunks embedded in the cliff face (the sharp facets and buttresses
    of K34), a few on the inland bank, and fallen blocks on the beach."""
    rng = random.Random(seed)
    mb = kit.MB()
    y = -150.0
    while y < 200.0:
        e = cliff_e(y)
        m = rng.choice(("laterite", "laterite_dk", "laterite_dk", "laterite_rd"))
        sx, sy, sz = rng.uniform(1.4, 2.6), rng.uniform(2.0, 5.0), rng.uniform(3.5, 8.0)
        z = rng.uniform(TOP - 9.0, TOP - 3.0) if rng.random() < 0.6 else rng.uniform(3.0, 8.0)
        z = min(z, TOP - 0.6 - sz * 0.9)                # never poke above the clifftop
        x = e - (1.0 if z > TOP - 12 else rng.uniform(3.2, 4.2)) - rng.uniform(-0.3, 0.5)
        mb.ico(T(x, y, z) @ Rz(rng.uniform(-0.35, 0.35)) @ Ry(rng.uniform(-0.25, 0.25)) @ S(sx, sy, sz), m,
               r=1.0, sub=1, jitter=0.18, rng=rng)
        y += rng.uniform(2.2, 4.5)
    mb.obj("CliffFacets", coll)
    rocks = [kit.make_boulder(f"LibBoulder{i}", coll, seed=i, size=1.0, m=("laterite", "laterite_dk")[i % 2])
             for i in range(4)]
    out = []
    for k in range(70):
        y = rng.uniform(-140, 180)
        x = cliff_e(y) - rng.uniform(4.2, 11.0)
        s = rng.uniform(0.5, 2.0) if rng.random() < 0.8 else rng.uniform(2.0, 3.2)
        out.append(kit.instance(rocks[k % 4], f"Boulder{k}", coll, (x, y, height(x, y) - 0.2 * s),
                                rot_z=rng.uniform(0, TAU), scale=s))
    for r in rocks:
        kit.hide_source(r)
    return out


def build_library(lib_c):
    pw.register_palette()
    lib = {}
    lib["palms"] = [kit.make_palm(f"LibPalm{i}", lib_c, seed=10 + i, height=7.5 + 0.6 * i) for i in range(6)]
    lib["bushes"] = [kit.make_bush(f"LibBush{i}", lib_c, seed=i, size=0.8 + 0.25 * i) for i in range(3)]
    lib["bigleaf"] = [pw.make_bigleaf(f"LibBigLeaf{i}", lib_c, seed=i, size=1.0 + 0.3 * i) for i in range(3)]
    lib["trees"] = [kit.make_tree(f"LibTree{i}", lib_c, seed=i, height=6 + i) for i in range(2)]
    lib["nair"] = [kit.make_figure(f"LibNairUp{i}", lib_c, "nair", seed=i, pose="sword_up") for i in range(4)]
    lib["nair_stand"] = [kit.make_figure(f"LibNair{i}", lib_c, "nair", seed=10 + i) for i in range(2)] + \
                        [kit.make_figure("LibNairSpear", lib_c, "nair_spear", seed=20)]
    lib["w_dutch"] = [kit.make_walker(f"LibWDutch{i}", lib_c, "dutch", seed=i) for i in range(3)]
    lib["w_officer"] = [kit.make_walker("LibWOfficer", lib_c, "dutch", seed=40)]
    kit.recolor(lib["w_officer"][0][1]["body"], strip=("steel", "post"))
    lib["w_ally"] = [kit.make_ally_walker(f"LibWAlly{i}", lib_c, seed=i, turban=t)
                     for i, t in enumerate(kit.ALLY_TURBANS)]
    for root, parts in lib["w_dutch"] + lib["w_officer"] + lib["w_ally"]:
        kit.hide_source(root)
        for p in parts.values():
            p.hide_render = p.hide_viewport = True
    return lib


def _put(src, name, coll, x, y, rz=0.0, s=1.0, sink=0.05):
    return kit.instance(src, name, coll, (x, y, height(x, y) - sink), rot_z=rz, scale=s)


def build_plants(coll, lib, keep=()):
    """Palms along the cliff edge and in rows on the higher terrace (K34), bushes and big
    leaves on the verges, a few palms on the beach below."""
    rng = random.Random(7)
    palms, bushes, bigleaf = lib["palms"], lib["bushes"], lib["bigleaf"]
    pts = []

    def free(x, y, r):
        return all((x - a) ** 2 + (y - b) ** 2 > (r + rb) ** 2 for a, b, rb in pts[-400:])

    def kept(x, y):
        return any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep)

    k = 0
    for i in range(9000):                               # terrace behind the bank: dense palm grove
        y = rng.uniform(-150, 220)
        x = BANK_X + rng.uniform(3.0, 70.0)
        if kept(x, y) or not free(x, y, 2.3):
            continue
        pts.append((x, y, 2.3))
        src = rng.choice(palms) if rng.random() < 0.85 else rng.choice(lib["trees"])
        _put(src, f"TerracePalm{k}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.95, 1.3), sink=0.2)
        k += 1
        if k > 1300:
            break
    for i in range(3000):                               # cliff-edge verge, thicker beyond the Nairs
        y = rng.uniform(-150, 220)
        x = rng.uniform(cliff_e(y) + 1.0, ROAD[0] - 0.6)
        if y < NAIR_FRONT + NAIR_DEPTH - 2 and not (y < -95):    # open verge where the armies meet (K34)
            continue
        if kept(x, y) or not free(x, y, 2.0):
            continue
        pts.append((x, y, 2.0))
        _put(rng.choice(palms), f"EdgePalm{k}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.9, 1.25), sink=0.2)
        k += 1
    for i in range(1400):                               # ground plants on both verges and under the palms
        y = rng.uniform(-110, 160)
        if rng.random() < 0.5:
            x = rng.uniform(cliff_e(y) + 0.8, ROAD[0] - 0.2)
        else:
            x = rng.uniform(ROAD[1] + 0.2, BANK_X + 30)
        if kept(x, y) or (BANK_X - 0.6 < x < BANK_X + 2.2):
            continue
        _put(rng.choice(bushes + bigleaf), f"Plant{i}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.4, 0.85))
    for i in range(30):                                 # a few palms on the beach below the cliff
        y = rng.uniform(-120, 160)
        x = cliff_e(y) - rng.uniform(5.5, 9.0)
        if not kept(x, y):
            _put(rng.choice(palms), f"BeachPalm{i}", coll, x, y, rng.uniform(0, TAU), rng.uniform(0.8, 1.1), sink=0.2)


def build_nairs(coll, lib, ev):
    """The Nair wall: a solid block across the road and verges, more ranks receding up the
    road out of sight. Swords up, shields forward, facing the allies (-Y). They stand ready,
    then stamp and brandish ("trained to fight with sword and shield"); the front ranks
    take a step forward."""
    rng = random.Random(41)
    end = ev["end"]
    men = []
    x0, x1 = None, BANK_X - 0.4
    y = NAIR_FRONT
    r = 0
    while y < NAIR_FRONT + NAIR_DEPTH:
        xa = cliff_e(y) + 1.6
        n = int((x1 - xa) / 0.62)
        for f in range(n):
            x = xa + (f + 0.5) * (x1 - xa) / n + rng.uniform(-0.08, 0.08)
            men.append((x, y + rng.uniform(-0.08, 0.08), r))
        y += 0.72
        r += 1
    while y < NAIR_FRONT + 95:                         # the rest of the five thousand, up the road
        xa = cliff_e(y) + 1.6
        for k in range(int((x1 - xa) / 0.9)):
            x = rng.uniform(xa, x1)
            men.append((x, y + rng.uniform(-0.3, 0.3), r))
        y += 1.0
        r += 1
    for i, (x, y, r) in enumerate(men):
        if r < 26 or rng.random() < 0.75:
            src = lib["nair"][rng.randrange(len(lib["nair"]))]
        else:
            src = lib["nair_stand"][rng.randrange(len(lib["nair_stand"]))]
        ob = _put(src, f"Nair{i}", coll, x, y, rz=math.pi + rng.uniform(-0.12, 0.12), sink=0.0)
        if r < 26:
            kit.animate_idle(ob, rng, 1, ev["brandish"] - 4, amount=0.025)
            if r < 2:                                  # the front ranks step forward
                ob.keyframe_insert("location", frame=ev["step"])
                ob.location.y -= 1.1
                ob.location.z = height(ob.location.x, ob.location.y)
                ob.keyframe_insert("location", frame=ev["step"] + 16)
            kit.animate_bob(ob, rng, ev["brandish"], end, height=0.14, period=(12, 18))
    return len(men)


def build_allies(coll, lib, ev):
    """The allied column on the road: Dutch and the rajas' men mixed, officers and an orange
    flag. It marches up (+Y), halts in front of the Nairs, the front shuffles back, and the
    whole column turns about and walks back the way it came."""
    rng = random.Random(5)
    end = ev["end"]
    files, ranks = 9, 20
    xs = ROAD[0] + 0.5, ROAD[1] - 0.3
    adv = HALT_FRONT - ALLY_FRONT
    out = 0
    for r in range(ranks):
        for f in range(files):
            x = xs[0] + (f + 0.5) * (xs[1] - xs[0]) / files + rng.uniform(-0.15, 0.15)
            y = ALLY_FRONT - r * 1.45 - rng.uniform(0, 0.35)
            if rng.random() < 0.5:
                tmpl = lib["w_dutch"][rng.randrange(3)]
            else:
                tmpl = lib["w_ally"][rng.randrange(len(lib["w_ally"]))]
            root, parts = kit.clone_walker(tmpl[1], f"Ally{r}_{f}", coll)
            for p in parts.values():
                p.hide_render = p.hide_viewport = False
            _route(root, parts, x, y, r, adv, ev, rng)
            out += 1
    # officers walking beside the column and the flag bearer in the middle
    for k, (x, r) in enumerate(((ROAD[1] + 0.6, 2), (ROAD[0] - 0.5, 6), (ROAD[1] + 0.6, 12))):
        root, parts = kit.clone_walker(lib["w_officer"][0][1], f"Officer{k}", coll)
        for p in parts.values():
            p.hide_render = p.hide_viewport = False
        _route(root, parts, x, ALLY_FRONT - r * 1.45, r, adv, ev, rng)
    root, parts = kit.clone_walker(lib["w_dutch"][0][1], "FlagBearer", coll)
    for p in parts.values():
        p.hide_render = p.hide_viewport = False
    _route(root, parts, 0.2, ALLY_FRONT - 4 * 1.45 - 0.6, 4, adv, ev, rng)
    pole = kit.MB()
    pole.seg((0.3, 0.05, 0.5), (0.3, 0.05, 4.6), 0.045, 0.04, "post", sides=6)
    pole.ico(T(0.3, 0.05, 4.68), "brass", r=0.07, sub=1)
    pole.obj("FlagPole", coll, parent=root)
    fl = ptw.make_flag("Flag", coll, w=1.9, h=1.25, m="flag_o")
    fl.parent = root
    fl.location = (0.33, 0.05, 4.5)
    fl.rotation_euler[2] = math.pi + 0.4
    return out


def _route(root, parts, x, y, r, adv, ev, rng):
    """March up, halt, (front ranks) shuffle back, turn about and walk back."""
    end = ev["end"]
    f0 = ev["march"]
    f_halt = ev["halt"] + min(18, r // 2) + rng.randint(0, 4)
    y1 = y + adv
    legs = [(f0, f_halt, (x, y), (x, y1))]
    t_back = ev["back"] + (8 if r < 3 else 0) + rng.randint(0, 10) + max(0, 10 - r)
    legs.append((t_back, end, (x, y1), (x + rng.uniform(-0.3, 0.3), y1 - 1.3 * (end - t_back) / kit.FPS)))
    kit.animate_route(root, parts, legs, height, stride_frames=14, swing=0.42, turn=16, heading=0.0,
                      phase=r * 3 + rng.randint(0, 2))


def build_world(ev, keep=()):
    """Everything but the camera. ev: real frames (march, halt, step, brandish, back, end)."""
    world_c = kit.new_collection("World")
    rocks_c = kit.new_collection("Rocks")
    plants_c = kit.new_collection("Plants")
    nairs_c = kit.new_collection("Nairs")
    allies_c = kit.new_collection("Allies")
    rig_c = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    # warm morning sun from inland (behind the Nairs): lit clifftop, shaded red faces, shadows
    # falling toward the sea; the sun glint on the water stays away from the camera
    cw.scene_base(rig_c, sun_dir=(-0.55, 0.45, -0.6), sun_energy=8.0, haze_density=0.0003)
    lib = build_library(lib_c)
    make_terrain(world_c)
    cw.make_faceted_sea(world_c, rig_c, ev["end"] + 20, (-420.0, -10.0, -320.0, 420.0),
                        lambda x, y: (shore_x(y) - x) * 2.5, step=2.0, far_step=10.0,
                        detail_box=(-130.0, -10.0, -160.0, 160.0))
    build_rock_facets(rocks_c)
    build_plants(plants_c, lib, keep)
    n_nairs = build_nairs(nairs_c, lib, ev)
    n_allies = build_allies(allies_c, lib, ev)
    for ob in lib_c.objects:
        if ob.type == "MESH":
            kit.hide_source(ob)
    print(f"Varkala: {n_nairs} Nairs, {n_allies} allied soldiers")
    return rig_c
