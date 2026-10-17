"""S64 (clip 77, ref K77): the king lays his sword down at the Padmanabha temple, in Temple.blend.

"In seventeen fifty, he gives his whole kingdom to Padmanabha... and rules from then on as the god's servant."
The camera descends from a wide three-quarter view of the whole tower to the king kneeling at the door.
Headless: blender -b -P temple64_film.py   (writes Temple.blend and renders/timing_temple.json)
"""
import importlib
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.abspath(os.getcwd())
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy

import colachel_kit as kit
import colachel_world as world
import port_world as pw
import mini_dio as md
import temple64_world as tw
for m in (kit, world, md, tw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

BEATS = [("77", "S64")]
TX, TY = tw.TOWER
CAMS = {"Temple": [("S64", 0.0, (-12.5, -17.5, 12.5), (TX - 0.5, TY - 0.5, 4.8), 24),
                   ("S64", 0.5, (-8.8, -13.2, 7.4), (TX - 1.0, TY - 2.0, 2.2), 28),
                   ("S64", 1.0, (-2.4, -6.2, 3.6), (TX - 0.8, TY - 3.6, 1.2), 34)]}
KEYFRAMES = {"K77": ("S64", 0.55)}


def build(samples=32):
    clips = md.timed_clips(F, BEATS)
    end = clips[-1][3]
    rng = {c[1]: (c[2], c[3]) for c in clips}
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.look = "AgX - Base Contrast"
    pw.register_palette()
    md.setup_backdrop((0.06, 0.07, 0.10), 0.5)
    rig = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    c = kit.new_collection("Temple")
    md.add_sun(rig, (0.55, 0.65, -0.45), 5.5, (1.0, 0.72, 0.44), angle=14.0)
    md.add_sun(rig, (-0.3, 0.5, -0.8), 1.6, (0.62, 0.70, 1.0), angle=30.0)
    tw.register_palette()
    md.make_tile("Ground", c, 14.5, 12.5, top="t_ground", depth=2.4, seed=11, strata=(("soil_dk", 0.35), ("soil", 0.75), ("soil_dk", 0.9)))
    tw.build_temple(c, lib_c, random.Random(64), dict(end=end, s64=(rng["S64"][0], rng["S64"][1])))
    for ob in lib_c.objects:
        kit.hide_source(ob)
    cams = {n: md.make_camera(sc, f"Cam{n}", k, rng) for n, k in CAMS.items()}
    sc.camera = cams["Temple"]
    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    for k, (b, u) in KEYFRAMES.items():
        f0, f1 = rng[b]
        sc.timeline_markers.new(k, frame=round(f0 + u * (f1 - f0)))
    md.save(HERE, "Temple.blend", "timing_temple.json", clips, "Temple film")


build()
