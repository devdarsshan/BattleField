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

HERE = r"C:\Users\sdevdarsshan\Desktop\Dev\Devv\BattleField\Battle of Colachel\blender"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
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
]
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
CUT_SHOTS = [(691, "MapCameraS10"), (1291, "MapCameraS13"), (1531, "MapCameraS16"), (1831, "MapCameraS18")]
CLOUDS_PART = (1, 78)         # clouds hold for 0.5 s (the dissolve), then part by ~3.2 s
SHIPS = [(-1200.0, -650.0, 200), (-500.0, -1050.0, 160), (-2100.0, 250.0, 210), (-4700.0, 3900.0, 190),
         (-6300.0, 6500.0, 175), (-6700.0, 8400.0, 185)]
LENS = 30


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
    sea_band = lambda x, y: _w(x, y) > -1500 and not geo.point_in_poly(x, y, land_poly)
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
        c2.rotation_euler = (0, 0, 0)
        shots.append((f0, c2))
    for f, pos in CAM_KEYS:
        shot_cam = [c for s0, c in shots if f >= s0][-1]
        shot_cam.location = pos
        shot_cam.keyframe_insert("location", frame=rt(f))
    for s0, c in shots:
        m = sc.timeline_markers.new(c.name, frame=rt(s0))
        m.camera = c
    map_world.build_clouds(coll, cam, (rt(CLOUDS_PART[0]), rt(CLOUDS_PART[1])))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Map.blend"))
    with open(os.path.join(HERE, "renders", "timing_map.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("map film built:", end, "frames,", len(bpy.data.objects), "objects")


build()
