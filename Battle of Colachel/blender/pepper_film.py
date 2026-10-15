"""The pepper hills (S09, shot-list clips 11-12), built in its own file Pepper.blend.

The map film ends looking straight down on the Kerala coast; this clip opens high over
the green hills looking steeply down, descends onto the terraced pepper garden (the
Flow reference K11a_v1), pushes past a vine-smothered post to the baskets of pepper,
then glides down the slope to the river landing, where sacks of pepper are hoisted
onto a waiting ship for "Ships have come for it for centuries."
Clip length follows the narration exactly as in film.py (estimate + placeholder voice
until S09 is recorded).

Headless:  blender -b -P pepper_film.py
It saves Pepper.blend and renders/timing_pepper.json.
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
from mathutils import Vector

import colachel_kit as kit
import colachel_world as world
import kerala_geo as geo
import pepper_world as pw
for m in (kit, geo, world, pw):
    importlib.reload(m)

sys.argv = sys.argv[:1]      # film.py helpers below are reused without running its build
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
# (clip, beat, design first frame, design last frame) for this segment
DESIGN_CLIPS = [
    ("11-12", "S09", 1, 288),
]
# camera keys: (frame, camera position, look-at point). Z up to 40 is metres above the
# ground under that point; higher Z is absolute.
CAM_KEYS = [
    # high over the hills, looking steeply down (the map shot before was straight down)
    (1,   (-6.0, -28.0, 105.0), (-2.0, 4.0, 0.0)),
    (60,  (-4.0, -34.0, 32.0),  (-1.0, 6.0, 1.0)),
    # settle on the K11a view: drying yard, terraces, hut, vine trees
    (125, (-2.4, -19.0, 7.4),   (-1.0, 10.0, 0.8)),
    # push past a vine-smothered post to the baskets of pepper
    (185, (-0.5, -6.8, 2.3),    (-0.5, -2.7, 0.3)),
    # whip left off the baskets, then glide down the bank onto the river landing (K11b):
    # pepper in the foreground, the jetty, and the ship hoisting the sacks aboard
    (207, (-4.2, -8.6, 3.6),    (-17.0, -6.5, 7.5)),
    (232, (-9.5, -11.0, 3.6),   (-26.0, -5.0, 3.0)),
    (288, (*pw.END_CAM, 1.7),   (*pw.END_LOOK, 3.3)),
]
LENS_KEYS = [(185, 30.0), (288, 24.0)]   # widen a little on the landing so the masts fit
HOIST = (192, 236, 262, 286)      # sling: lift, top, swing over, set down (design frames)
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
    return (x, y, z) if z > 40 else (x, y, max(pw.height(x, y), pw.WATER_Z) + z)


K11A = 125          # the key that matches the Flow reference K11a_v1


def keep_clear():
    """Where trees may not stand: corridors along the low part of the camera path, the
    lines of sight of the low keys after K11a (stopping short of what they look at),
    and the near 28 m of the K11a view, which is open yard and terraces in the reference."""
    out = []
    for (_, a, _), (_, b, _) in zip(CAM_KEYS, CAM_KEYS[1:]):
        a, b = Vector(above_ground(a)), Vector(above_ground(b))
        if min(a.z - pw.height(a.x, a.y), b.z - pw.height(b.x, b.y)) < 14.0:
            out.append(("seg", a.x, a.y, b.x, b.y, 5.0))
    for f, pos, look in CAM_KEYS:
        if pos[2] < 8.0 and f > K11A:
            p, q = Vector(pos[:2]), Vector(look[:2])
            q = p.lerp(q, 0.8)
            out.append(("seg", p.x, p.y, q.x, q.y, 7.0))
    f, pos, look = next(k for k in CAM_KEYS if k[0] == K11A)
    out.append(("cone", pos[0], pos[1], look[0], look[1], 30.0, 28.0))
    for f, pos, look in CAM_KEYS[2:]:
        out.append(("disc", pos[0], pos[1], 10.0))
    return out


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"   # a touch richer than the beach grade, like K11a
    rig = pw.build_world(end, hoist=[rt(f) for f in HOIST], keep_clear=keep_clear())

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
    for f, lens in LENS_KEYS:
        cd.lens = lens
        cd.keyframe_insert("lens", frame=rt(f))
    for f, pos, look in CAM_KEYS:
        cam.location = above_ground(pos)
        target.location = above_ground(look)
        cam.keyframe_insert("location", frame=rt(f))
        target.keyframe_insert("location", frame=rt(f))

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Pepper.blend"))
    with open(os.path.join(HERE, "renders", "timing_pepper.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("pepper film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
