"""The English port (S17, shot-list clip 23), built in its own file Port.blend.

The map shot before it has Travancore's red territory spreading north up the coast;
this clip cuts down to a small port in the conquered land. It opens low over the heaps
of pepper ("And here is the problem for the Dutch"), rises and tracks right to the Flow
reference view K23_v2 (the white English fort with its red flag, porters carrying
sacks along the jetty to the English ship, and far out the Dutch ship with its orange
flag sailing away empty: "Each of those little kingdoms had signed a pepper contract
with them"), then follows the porters out along the jetty to the English ship as its
red flag fills the frame and the Dutch sails shrink on the horizon ("The pepper goes to
whoever pays the most, and often that means the English").
Clip length follows the narration exactly as in film.py (estimate + placeholder voice
until S17 is recorded).

Headless:  blender -b -P port_film.py
It saves Port.blend and renders/timing_port.json.
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
import kochi_world as kw
import pepper_world as pw
import port_world as pt
for m in (kit, geo, world, kw, pw, pt):
    importlib.reload(m)

sys.argv = sys.argv[:1]      # film.py helpers below are reused without running its build
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
# (clip, beat, design first frame, design last frame) for this segment
DESIGN_CLIPS = [
    ("23", "S17", 1, 509),
]
# camera keys: (frame, camera position, look-at point). Z is metres above the ground
# (or the sea) under that point.
CAM_KEYS = [
    # low over the pepper heaps, porters taking sacks, the fort gate beyond
    (1,   (-11.0, -15.5, 4.2),  (-2.0, 0.0, 0.8)),
    # rise and track right to the K23_v2 view: fort, heaps, jetty, ship, the Dutch sails far out
    (150, (-6.0, -24.0, 12.5),  (6.0, 7.0, 1.0)),
    # out along the jetty over the porters
    (330, (3.0, -17.0, 8.5),    (16.0, 4.0, 2.5)),
    # the English ship: red flag, sacks going aboard; the Dutch ship small on the horizon
    (509, (10.0, -9.5, 5.5),    (22.0, 6.0, 6.0)),
]
K23 = 150            # the key that matches the Flow reference K23_v2
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


def above_ground(p):
    x, y, z = p
    return (x, y, max(pt.height(x, y), pt.SEA_Z) + z)


def keep_clear():
    """Tree-free corridors: under the camera path, and the near part of each key's line
    of sight (so no palm trunk crosses the heaps, the jetty or the ship)."""
    out = []
    for (_, a, _), (_, b, _) in zip(CAM_KEYS, CAM_KEYS[1:]):
        out.append((a[0], a[1], b[0], b[1], 6.0))
    for f, pos, look in CAM_KEYS:
        p, q = Vector(pos[:2]), Vector(look[:2])
        q = p.lerp(q, 0.85)
        out.append((p.x, p.y, q.x, q.y, 4.0))
    return out


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"   # matches the pepper, Kochi and map clips
    rig = pt.build_world(end + 40, keep=keep_clear())

    cd = bpy.data.cameras.new("Camera")
    cd.lens = LENS
    cd.clip_start = 0.05
    cd.clip_end = 3000.0
    cam = bpy.data.objects.new("Camera", cd)
    rig.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("CamTarget", None)
    rig.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for f, pos, look in CAM_KEYS:
        cam.location = above_ground(pos)
        target.location = above_ground(look)
        cam.keyframe_insert("location", frame=rt(f))
        target.keyframe_insert("location", frame=rt(f))

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    sc.timeline_markers.new("K23", frame=rt(K23))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Port.blend"))
    with open(os.path.join(HERE, "renders", "timing_port.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("port film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
