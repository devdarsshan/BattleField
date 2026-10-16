"""Dutch Kochi (S12, shot-list clips 16-17), built in its own file Kochi.blend.

The map film ends pushing in top-down on the orange Dutch star fort at Kochi; this
clip cuts inside it. It opens close on the treaty table, over the officials'
shoulders toward the rajas ("Their method is simple"), orbits round the table as the
terms are set, rises to the Flow reference view K16_v1 looking west through the open
sea gate as porters carry pepper out along the jetty to the ship ("Sell your pepper
only to us, at our price"), drifts down past the rajas ("none of them is strong
enough to refuse"), then on "The whole Dutch plan depends..." cranes up and back to a
high angle over the fort, swinging round so north is up and the sea on the left,
ready for the cut back to the map.
Clip length follows the narration exactly as in film.py (estimate + placeholder voice
until S12 is recorded).

Headless:  blender -b -P kochi_film.py
It saves Kochi.blend and renders/timing_kochi.json.
"""
import importlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.abspath(os.getcwd())
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import random

import bpy

import colachel_kit as kit
import colachel_world as world
import kerala_geo as geo
import kochi_world as kw
for m in (kit, geo, world, kw):
    importlib.reload(m)

sys.argv = sys.argv[:1]      # film.py helpers below are reused without running its build
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
# (clip, beat, design first frame, design last frame) for this segment
DESIGN_CLIPS = [
    ("16-17", "S12", 1, 554),
]
# narration moments in design frames (from the estimated line timing)
BEATS = {"contracts": 65, "sell": 146, "price": 202, "refuse": 228, "remember": 369, "whole": 397}
# camera keys: (frame, camera position, look-at point), metres; the courtyard floor is z = 0
CAM_KEYS = [
    # "Their method is simple." over the officials' shoulders toward the rajas
    (1,   (-2.2, -7.0, 2.7),  (0.2, -2.0, 0.9)),
    (65,  (-1.6, -6.4, 2.5),  (0.2, -2.1, 0.9)),
    # "They sign contracts with the small rajas." orbit round to the south-east of the table
    (146, (3.1, -5.4, 2.7),   (-0.6, -2.3, 0.9)),
    # "Sell your pepper only to us, at our price." rise to the K16_v1 view: the gate, the porters, the ship
    (215, (8.0, -4.6, 5.2),   (-3.4, -0.9, 1.2)),
    (300, (5.0, -2.2, 4.8),   (-9.0, 2.4, 0.8)),
    # "...none of them is strong enough to refuse. Remember that." down past the rajas
    (369, (4.8, 2.9, 3.6),    (-0.9, -2.4, 1.0)),
    (397, (4.6, 2.3, 3.9),    (-0.9, -2.5, 0.9)),
    # "The whole Dutch plan depends on the kings of this coast staying small." crane up and back
    (470, (20.0, -12.0, 22.0), (-2.0, 0.0, 0.0)),
    (554, (2.0, -44.0, 60.0),  (-5.0, 0.0, 0.0)),
]
K16 = 215            # the key that matches the Flow reference K16_v1
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
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"   # matches the pepper and map clips
    w = kw.build_world(end + 40)
    rng = random.Random(12)
    cast_c = kit.new_collection("Cast")
    kw.build_meeting(cast_c, end + 40, rng, {k: rt(v) for k, v in BEATS.items()})
    kw.build_porters(kit.new_collection("Porters"), end + 40, rng)

    cd = bpy.data.cameras.new("Camera")
    cd.lens = LENS
    cd.clip_start = 0.05
    cd.clip_end = 3000.0
    cam = bpy.data.objects.new("Camera", cd)
    w["rig"].objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("CamTarget", None)
    w["rig"].objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for f, pos, look in CAM_KEYS:
        cam.location = pos
        target.location = look
        cam.keyframe_insert("location", frame=rt(f))
        target.keyframe_insert("location", frame=rt(f))

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    sc.timeline_markers.new("K16", frame=rt(K16))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Kochi.blend"))
    with open(os.path.join(HERE, "renders", "timing_kochi.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("kochi film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
