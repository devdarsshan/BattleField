"""The map segment of the film (S07 onward), built in its own file Map.blend.

The beach film (film.py) ends on the high storm shot at the end of S06; the map film
opens on storm clouds that part over the 3D Kerala coast, and the two are joined with
a short cross-dissolve (assemble.py), so the change of world reads as a cloud wipe.
Clip lengths follow the narration exactly as in film.py.

Headless:  blender -b -P map_film.py
"""
import importlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.abspath(os.getcwd())
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
import bmesh
import colachel_kit as kit
import colachel_world as world
import kerala_geo as geo
import map_world
for m in (kit, geo, world, map_world):
    importlib.reload(m)

sys.argv = sys.argv[:1]      # film.py helpers below are reused without running its build
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
# (clip, beat, design first frame, design last frame) for this segment
DESIGN_CLIPS = [
    ("08", "S07", 1, 240),
    ("09-10", "S08", 241, 690),
    ("13", "S10", 691, 1000),        # follows S09 (pepper garden, Pepper.blend) in the edit
    ("14-15", "S11", 1001, 1290),    # continues S10: push in on Dutch Kochi
    ("18", "S13", 1291, 1530),       # after S12 (Kochi courtyard, Kochi.blend): back on the map
    ("21-22", "S16", 1531, 1830),    # after S14-S15 (Padmanabhapuram, Palace.blend): Travancore grows
    ("24", "S18", 1831, 2070),       # after S17 (English port, Port.blend): big red Travancore, small orange Kochi
    ("25", "S19", 2071, 2375),       # after S18: Ceylon across the Gulf of Mannar, the governor's ship (K25)
    ("31", "S24", 2376, 2740),       # after S23 (the meeting): war banner over Kochi, column marches south (K31)
    ("35", "S28", 2741, 2935),       # after S27 (Varkala cliffs): the frontier near Kollam goes back and forth (K35)
]
# S19, S24 and S28 look a little down the map toward the north (as their Flow refs K25, K31,
# K35 do), so the sails, the war banner and the soldiers read; the earlier map shots are
# straight top-down. Camera keys for them are given as the ground point aimed at.
SHOT_TILT = {"MapCameraS19": 10.0, "MapCameraS24": 38.0, "MapCameraS28": 25.0}


def aim(x, y, h, tilt):
    """Camera position h metres up, tilted `tilt` degrees north, centred on ground (x, y)."""
    return (x, y - h * math.tan(math.radians(tilt)), h)


# camera keys: (frame, (x, y, height)). Straight top-down, north up.
# K08a_v2: the whole southern coast, tip at lower right -> K08b_v2: closer on the coast at Kollam.
CAM_KEYS = [
    (1,   (-700.0, 900.0, 7000.0)),
    (240, (-3900.0, 4480.0, 3500.0)),
    # S08: glide north along the coast to the Vembanad backwaters (K09)
    (465, (-4450.0, 6350.0, 3600.0)),
    (690, (-4950.0, 8300.0, 3550.0)),
    # S10: (cut in from the pepper hills) rise from low over the hills to see the whole coast,
    # the small kingdoms' forts popping up one by one, south to north
    (691, (-2600.0, 4400.0, 1500.0)),
    (1000, (-3500.0, 5100.0, 12000.0)),
    # S11: push in on Kochi; the Dutch fort turns orange as the line says so
    (1150, (-5000.0, 9100.0, 6000.0)),
    (1290, (-5450.0, 9850.0, 3400.0)),
    # S13: (cut in from the Kochi courtyard) high over Kochi, glide south down the strip and
    # settle over Travancore's red fort at the tip ("Meet Marthanda Varma")
    (1291, (-5300.0, 9500.0, 9500.0)),
    (1420, (-2300.0, 4200.0, 7000.0)),
    (1530, (420.0, 380.0, 2600.0)),
    # S16: (cut in from the palace) rise from Travancore and turn north as it takes
    # Attingal, the Nedumangad hills and Kottarakkara
    (1531, (470.0, 430.0, 2600.0)),
    (1660, (-700.0, 1900.0, 6500.0)),
    (1830, (-2000.0, 3400.0, 9500.0)),
    # S18: (cut in from the English port) pull back very wide: the red kingdom fills the south,
    # the little orange Dutch fort at Kochi sits at the top of frame
    (1831, (-3200.0, 5600.0, 9000.0)),
    (2070, (-3600.0, 5200.0, 17000.0)),
    # S19: (cut in from S18) high over the Gulf of Mannar: the Kerala tip top left, Ceylon on
    # the right; a slow glide south-east and down onto Ceylon for "the governor of Ceylon"
    (2071, aim(10000.0, -5400.0, 29500.0, 10.0)),
    (2250, aim(10500.0, -4300.0, 26800.0, 10.0)),
    (2375, aim(10800.0, -3800.0, 25500.0, 10.0)),
    # S24: (cut in from the meeting) the Kochi star fort, the war banner going up, then the
    # column marching south down the beach; the camera follows it south
    (2376, aim(-5340.0, 9720.0, 2600.0, 38.0)),
    (2520, aim(-5320.0, 9600.0, 2700.0, 38.0)),
    (2740, aim(-5260.0, 9020.0, 3100.0, 38.0)),
    # S28: (cut in from the Varkala cliffs) the frontier at the coast near Kollam
    (2741, aim(-2870.0, 3640.0, 2900.0, 25.0)),
    (2935, aim(-2850.0, 3600.0, 2600.0, 25.0)),
]
# Travancore's growth, S16. Frontiers run across the strip, perpendicular to the coast
# (t = distance along the coast from Colachel, w = distance inland), with a gentle wobble.
_CD = (-0.677, 0.735)                   # along the coast, Colachel -> Kollam
_CN = (0.735, 0.677)                    # inland


def _t(x, y):
    return x * _CD[0] + y * _CD[1] + 260 * math.sin((x * _CN[0] + y * _CN[1]) / 900.0)


def _w(x, y):
    return x * _CN[0] + y * _CN[1]


# (stage, test(x, y), design frames the red tint fades in, frontier t for the border line)
TERRITORY = [
    ("Travancore", lambda x, y: _t(x, y) < 1500, (1531, 1560), 1500),
    ("Attingal", lambda x, y: _t(x, y) < 2900 and _w(x, y) < 1400, (1690, 1712), 2900),
    ("Nedumangad", lambda x, y: _t(x, y) < 2900, (1735, 1760), 2900),
    ("Kottarakkara", lambda x, y: _t(x, y) < 4700 and _w(x, y) > 1300, (1780, 1805), 4700),
]
FORTS_TAKEN = [("Attingal", (1690, 1712)), ("Kottarakkara", (1780, 1805))]
KOCHI_TURNS_ORANGE = (1200, 1235)
FORTS_APPEAR = (760, 930)
# shots that start after a cut get their own camera (bound with a timeline marker)
CUT_SHOTS = [
    (691, "MapCameraS10"), (1291, "MapCameraS13"), (1531, "MapCameraS16"),
    (1831, "MapCameraS18"), (2071, "MapCameraS19"), (2376, "MapCameraS24"),
    (2741, "MapCameraS28")
]
CLOUDS_PART = (1, 78)         # clouds hold for 0.5 s (the dissolve), then part by ~3.2 s
SHIPS = [(-1200.0, -650.0, 200), (-500.0, -1050.0, 160), (-2100.0, 250.0, 210), (-4700.0, 3900.0, 190),
         (-6300.0, 6500.0, 175), (-6700.0, 8400.0, 185)]
LENS = 30


def frontier_xy(T, w):
    """The point on the frontier t = T at inland distance w (solving the wobble)."""
    x, y = T * _CD[0] + w * _CN[0], T * _CD[1] + w * _CN[1]
    for _ in range(6):
        x, y = x + (T - _t(x, y)) * _CD[0], y + (T - _t(x, y)) * _CD[1]
    return x, y


def s28_sea_wash_and_border(coll, bvh, frames, coast_pt, t_min=1500.0, w_sea=-1500.0):
    """S28 (K35): Travancore's red wash carried out over the sea with a clean straight-edged
    outline (not the cell-stepped S16 sea wash), and the red frontier ribbon drawn from the
    sea up to where the S16 border starts inland."""
    from mathutils import Vector
    from mathutils.geometry import delaunay_2d_cdt
    T = TERRITORY[-1][3]
    w0 = _w(*coast_pt)
    poly = [coast_pt]
    n = 12
    poly += [frontier_xy(T, w0 + (w_sea - w0) * k / n) for k in range(1, n + 1)]
    t1 = _t(*poly[-1])
    poly += [(t * _CD[0] + w_sea * _CN[0], t * _CD[1] + w_sea * _CN[1])
             for t in [T - (T - t_min) * k / 8 for k in range(1, 9)]]
    coast = [(x, y) for x, y in geo.coast_detailed(45.0) if x < 0 and t_min - 200 < _t(x, y) < T and _w(x, y) > w_sea]
    coast.sort(key=lambda p: _t(*p))
    poly += [p for p in coast if _t(*p) < _t(*coast_pt) - 20]
    out = delaunay_2d_cdt([Vector(p) for p in poly], [], [list(range(len(poly)))], 1, 0.01)
    bm = bmesh.new()
    vs = [bm.verts.new((v.x, v.y, 44.0)) for v in out[0]]
    for f in out[2]:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    me = bpy.data.meshes.new("Territory_S28Sea")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(map_world.territory_material("TerritoryMat_S28Sea", map_world.TERRITORY_WASH,
                                                     (frames[0], frames[0] + 1)))
    ob = bpy.data.objects.new("Territory_S28Sea", me)
    ob.visible_shadow = False
    coll.objects.link(ob)
    pts = [frontier_xy(T, w_sea + k * 60.0) for k in range(int((1500 - w_sea) / 60) + 1)]
    bo = map_world.build_border(coll, bvh, pts, (frames[0], frames[0] + 1), None, name="Border_S28")
    for v in bo.data.vertices:
        if v.co.z < 20:
            v.co.z = 50.0
    map_world.show_only([ob, bo], *frames)
    return ob, bo


def timed_clips():
    lines = F["beat_lines"]()
    out, f0 = [], 1
    for clip, beat, _, _ in DESIGN_CLIPS:
        wav = os.path.join(F["AUDIO"], f"{beat}.wav")
        if os.path.exists(wav):
            secs = F["wav_seconds"](wav)
        else:
            secs = F["estimate_seconds"](lines[beat])
            wav = os.path.join(F["AUDIO"], "placeholder", f"{beat}.wav")
        n = max(F["MIN_CLIP"], math.ceil((F["NARRATION_LEAD"] + secs + F["NARRATION_TAIL"]) * FPS))
        out.append((clip, beat, f0, f0 + n - 1, wav, secs))
        f0 += n
    return out


def retime(frame, clips):
    for (_, _, d0, d1), (_, _, n0, n1, _, _) in zip(DESIGN_CLIPS, clips):
        if d0 <= frame <= d1:
            return round(n0 + (frame - d0) / (d1 - d0) * (n1 - n0))
    raise ValueError(frame)


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.view_transform = "AgX"           # softer than Standard, richer than the beach grade
    sc.view_settings.look = "AgX - Base Contrast"     # close to the beach grade, a touch richer
    sc.view_settings.exposure = 0.05
    coll, land, bvh = map_world.build_map_world(end)
    map_world.build_ships(coll, SHIPS)
    map_world.build_kingdoms(coll, bvh, (rt(FORTS_APPEAR[0]), rt(FORTS_APPEAR[1])), scale=26.0)
    map_world.build_dutch_kochi(coll, bvh, (rt(KOCHI_TURNS_ORANGE[0]), rt(KOCHI_TURNS_ORANGE[1])), coll)
    land_ob = bpy.data.objects["MapLand"]
    land_poly = geo.land_polygon_detailed(120.0)
    sea_band = lambda x, y: x < 1200 and _w(x, y) > -1500 and not geo.point_in_poly(x, y, land_poly)
    map_world.build_territory(coll, land_ob, bvh, [(n, t, (rt(a), rt(b))) for n, t, (a, b), _ in TERRITORY],
                              sea_test=sea_band)
    # frontier lines: each appears with its stage and goes when the next frontier is drawn
    for i, (n, test, (a, b), T) in enumerate(TERRITORY):
        pts = []
        for k in range(0, 260):
            w = -400 + k * 60.0
            # walk inland along the frontier t = T (solve the wobble by a few iterations)
            x, y = T * _CD[0] + w * _CN[0], T * _CD[1] + w * _CN[1]
            for _ in range(4):
                x, y = x + (T - _t(x, y)) * _CD[0], y + (T - _t(x, y)) * _CD[1]
            if test(x - _CD[0] * 40, y - _CD[1] * 40) and geo.point_in_poly(x, y, land_poly):
                pts.append((x, y))
        if len(pts) > 2:
            nxt = TERRITORY[i + 1][2] if i + 1 < len(TERRITORY) else None
            map_world.build_border(coll, bvh, pts, (rt(a), rt(b)),
                                   (rt(nxt[0]), rt(nxt[0]) + 1) if nxt else None, name=f"Border_{n}")
    for name, (a, b) in FORTS_TAKEN:
        map_world.recolor_fort(name, map_world.TRAVANCORE_RED, (rt(a), rt(b)))

    # ---- S19, S24, S28 (each shown only in its own beat; S07-S18 above are untouched)
    beat = {b: (c0, c1) for _, b, c0, c1, _, _ in clips}
    lib_c = bpy.data.collections["MapLibrary"]
    word = lambda b, sec: beat[b][0] + round((F["NARRATION_LEAD"] + sec) * FPS)   # frame of a word
    # S19 (K25): Ceylon, the Colombo fort, the governor's ship sailing for India
    map_world.build_s19(coll, lib_c, beat["S19"], end, ((12650.0, -6150.0), (8200.0, -3450.0)))
    # S24 (K31): "Van Imhoff leaves" (ship sails, 0-3 s); the banner goes up through "In November
    # seventeen thirty-nine, the Dutch in Kerala declare war" (~2.6-5.9 s); then the column marches
    map_world.build_s24(coll, lib_c, land, bvh, beat["S24"], end, hoist=(word("S24", 2.6), word("S24", 5.9)),
                        march=word("S24", 6.1), leave=(word("S24", -0.4), word("S24", 4.0)))
    # S28 (K35): the frontier where it meets the coast near Kollam; back and forth all beat
    fx, fy = 0.0, 0.0
    best = 1e9
    for x, y in geo.coast_detailed(45.0):
        if x < 0 and abs(_t(x, y) - TERRITORY[-1][3]) < best:
            best, fx, fy = abs(_t(x, y) - TERRITORY[-1][3]), x, y
    map_world.build_s28(coll, lib_c, bvh, beat["S28"], end, (fx + _CN[0] * 130, fy + _CN[1] * 130))
    # S28: Travancore's land up to the frontier tinted as in K35 (the S16 washes swap out)
    s28 = beat["S28"]
    near = lambda x, y: -7000 < x < 1500 and 500 < y < 7000
    map_world.build_territory(coll, land_ob, bvh, [("S28", lambda x, y: _t(x, y) < TERRITORY[-1][3] and near(x, y),
                                                     (s28[0], s28[0] + 1))])
    map_world.show_only([bpy.data.objects["Territory_S28"]], *s28)
    s28_sea_wash_and_border(coll, bvh, s28, (fx, fy))
    map_world.hide_during([o for o in bpy.data.objects if o.name.startswith("Territory_") and not o.name.startswith("Territory_S28")],
                          *s28)
    # S24 and S28 see the approved sea low and tilted: the same sea with softer highlights
    map_world.matte_sea_copy(coll, [beat["S24"], beat["S28"]])

    cd = bpy.data.cameras.new("MapCamera")
    cd.lens = LENS
    cd.clip_start = 10.0
    cd.clip_end = 60000.0
    cam = bpy.data.objects.new("MapCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.rotation_euler = (0, 0, 0)          # looking straight down, north up
    shots = [(1, cam)]
    for f0, name in CUT_SHOTS:
        c2 = bpy.data.objects.new(name, cd)
        sc.collection.objects.link(c2)
        c2.rotation_euler = (math.radians(SHOT_TILT.get(name, 0.0)), 0, 0)
        shots.append((f0, c2))
    for f, pos in CAM_KEYS:
        shot_cam = [c for s0, c in shots if f >= s0][-1]
        shot_cam.location = pos
        shot_cam.keyframe_insert("location", frame=rt(f))
    for s0, c in shots:
        m = sc.timeline_markers.new(c.name, frame=rt(s0))
        m.camera = c
    map_world.build_clouds(coll, cam, (rt(CLOUDS_PART[0]), rt(CLOUDS_PART[1])))
    # soft clouds in the corners of the S19 and S24 shots (K25, K31)
    shot = dict((n, c) for (s0, c), n in zip(shots, ["MapCamera"] + [n for _, n in CUT_SHOTS]))
    map_world.build_corner_clouds(coll, shot["MapCameraS19"], beat["S19"], seed=19, depth=4200.0,
                                  spots=((-1, 1, 0.7), (1, 1, 1.15), (-1, -1, 1.0), (1, -1, 1.1)))
    map_world.build_corner_clouds(coll, shot["MapCameraS24"], beat["S24"], seed=24, depth=1900.0,
                                  spots=((-1, 1, 0.8), (1, 1, 0.85), (-1, -1, 0.9), (1, -1, 0.75)))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Map.blend"))
    with open(os.path.join(HERE, "renders", "timing_map.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("map film built:", end, "frames,", len(bpy.data.objects), "objects")


build()
