"""S60 (clip 73, ref K73): the chapel and the tomb inside Udayagiri fort, in Chapel.blend.

"De Lannoy ... is buried in a small chapel inside Udayagiri fort. His tomb is still there."
The camera descends from a high three-quarter view into the chapel and pushes in on the tomb.
Headless: blender -b -P chapel_film.py   (writes Chapel.blend and renders/timing_chapel.json)
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
import chapel_world as cwd
import scene_envs as envs
import surround
for m in (kit, world, md, cwd, surround, envs):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

BEATS = [("73", "S60")]
CAMS = {"Chapel": [("S60", 0.0, (9.5, -12.5, 11.5), (-0.2, 0.4, 2.4), 32),
                   ("S60", 0.55, (7.2, -9.6, 7.0), (0.1, -0.1, 1.6), 33),
                   ("S60", 1.0, (5.6, -7.6, 4.6), (0.2, -0.4, 1.3), 33)]}
KEYFRAMES = {"K73": ("S60", 0.5)}


def build(samples=32):
    clips = md.timed_clips(F, BEATS)
    end = clips[-1][3]
    rng = {c[1]: (c[2], c[3]) for c in clips}
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.look = "AgX - Base Contrast"
    pw.register_palette()
    rig = kit.new_collection("Rig")
    lib_c = kit.new_collection("Library")
    c = kit.new_collection("Chapel")
    md.add_sun(rig, (-0.45, 0.5, -0.6), 1.1, (1.0, 0.62, 0.42), angle=18.0)       # a cool fill from the camera side
    envs.fort_env(c, lib_c, random.Random(160))
    r = random.Random(60)
    cwd.build_chapel(c, lib_c, r, dict(end=end))
    for ob in lib_c.objects:
        kit.hide_source(ob)
    cams = {n: md.make_camera(sc, f"Cam{n}", k, rng) for n, k in CAMS.items()}
    sc.camera = cams["Chapel"]
    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    for k, (b, u) in KEYFRAMES.items():
        f0, f1 = rng[b]
        sc.timeline_markers.new(k, frame=round(f0 + u * (f1 - f0)))
    md.save(HERE, "Chapel.blend", "timing_chapel.json", clips, "Chapel film")


build()
