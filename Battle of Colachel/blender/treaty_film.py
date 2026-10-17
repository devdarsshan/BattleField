"""S62 (clip 75, ref K75): the treaty tent at Mavelikkara, in Treaty.blend.

"In seventeen fifty-three, the two sides sign the Treaty of Mavelikkara..."  The camera descends from high front-left
into the tent, over the long table and the scroll.
Headless: blender -b -P treaty_film.py   (writes Treaty.blend and renders/timing_treaty.json)
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
import treaty_world as trw
for m in (kit, world, md, trw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

BEATS = [("75", "S62")]
CAMS = {"Treaty": [("S62", 0.0, (-4.5, -17.0, 12.5), (0.0, 0.2, 1.5), 30),
                   ("S62", 0.55, (-3.0, -12.6, 8.2), (0.0, 0.5, 1.3), 31),
                   ("S62", 1.0, (-0.9, -8.2, 4.7), (0.0, 1.2, 1.0), 36)]}
KEYFRAMES = {"K75": ("S62", 0.6)}


def build(samples=32):
    clips = md.timed_clips(F, BEATS)
    end = clips[-1][3]
    rng = {c[1]: (c[2], c[3]) for c in clips}
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.look = "AgX - Base Contrast"
    pw.register_palette()
    md.setup_backdrop((0.80, 0.76, 0.72), 1.15)
    rig = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    c = kit.new_collection("Treaty")
    md.add_sun(rig, (0.45, 0.6, -0.65), 5.5, (1.0, 0.92, 0.80), angle=12.0)
    md.make_tile("Ground", c, 19.0, 17.5, top="grass", depth=2.4, seed=7)
    trw.build_treaty(c, lib_c, random.Random(62), dict(end=end))
    for ob in lib_c.objects:
        kit.hide_source(ob)
    cams = {n: md.make_camera(sc, f"Cam{n}", k, rng) for n, k in CAMS.items()}
    sc.camera = cams["Treaty"]
    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    for k, (b, u) in KEYFRAMES.items():
        f0, f1 = rng[b]
        sc.timeline_markers.new(k, frame=round(f0 + u * (f1 - f0)))
    md.save(HERE, "Treaty.blend", "timing_treaty.json", clips, "Treaty film")


build()
