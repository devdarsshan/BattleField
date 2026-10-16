"""Padmanabhapuram (S14, shot-list clip 19), built in its own file Palace.blend.

The map film ends top-down over Travancore's red fort; this clip cuts in high over the
palace town and settles on the Flow reference K19a_v1 view (birth year, "becomes the
ruler of Travancore"), descends over the laterite wall into the courtyard ("His capital
is Padmanabhapuram, a palace town built of carved wood"), and pushes in to the young
Marthanda Varma alone on his carved upper veranda (K19b_v2) for the end.
Clip length follows the narration exactly as in film.py (estimate + placeholder voice
until S14 is recorded).

Headless:  blender -b -P palace_film.py
It saves Palace.blend and renders/timing_palace.json.
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
from mathutils import Vector

import colachel_kit as kit
import colachel_world as world
import kerala_geo as geo
import palace_world as pw
for m in (kit, geo, world, pw):
    importlib.reload(m)

sys.argv = sys.argv[:1]      # film.py helpers below are reused without running its build
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
# (clip, beat, design first frame, design last frame) for this segment
DESIGN_CLIPS = [
    ("19", "S14", 1, 456),
]
# camera keys: (frame, camera position, look-at point), absolute metres. "K" marks a
# point relative to the king (his feet on the veranda floor), so the end framing follows
# him if the hall changes.
CAM_KEYS = [
    # cut in high and steep (the map shot before looked straight down), settle on K19a:
    # the compound's south-east corner nearest, the gate wall and tank to the left
    (1,   (120.0, -105.0, 150.0), (0.0, 6.0, 0.0)),
    (110, (62.0, -60.0, 40.0),    (-10.0, 12.0, 8.0)),
    # drift lower while "he becomes the ruler of Travancore"
    (215, (54.0, -54.0, 33.0),    (-7.0, 9.0, 6.0)),
    # descend over the south-east corner of the wall into the courtyard
    # ("a palace town built of carved wood")
    (300, (34.0, -36.0, 21.0),    (8.0, -4.0, 4.0)),
    (370, (19.0, -22.0, 12.0),    ("K", 0.0, 1.0, 0.8)),
    # push in to the young king on his veranda (K19b_v2), then a slow last drift
    (436, ("K", -4.6, -2.75, 1.65), ("K", 0.64, -0.49, 1.45)),
    (456, ("K", -4.3, -2.55, 1.62), ("K", 0.64, -0.49, 1.45)),
]
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


def resolve(p, king):
    return king + Vector(p[1:]) if p[0] == "K" else Vector(p)


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"     # as the map and pepper clips, close to K19a
    sc.eevee.volumetric_tile_size = "4"
    sc.eevee.volumetric_end = 1500
    sc.view_settings.exposure = 0.0
    rig, anchors, king = pw.build_world(end)

    cd = bpy.data.cameras.new("Camera")
    cd.lens = LENS
    cd.clip_start = 0.1
    cd.clip_end = 4000.0
    cam = bpy.data.objects.new("Camera", cd)
    rig.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("CamTarget", None)
    rig.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    k = anchors["king"]
    for f, pos, look in CAM_KEYS:
        cam.location = resolve(pos, k)
        target.location = resolve(look, k)
        cam.keyframe_insert("location", frame=rt(f))
        target.keyframe_insert("location", frame=rt(f))

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Palace.blend"))
    with open(os.path.join(HERE, "renders", "timing_palace.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("palace film built:", end, "frames,", len(bpy.data.objects), "objects; king at", tuple(round(v, 2) for v in k))
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
