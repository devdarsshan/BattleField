"""The Royal Meeting under the Canopy (Beats S21, S22, S23, Clips 27-30).

Built in its own file Meeting.blend reusing meeting_world.py.
Matches Flow references:
- frames/flow_refs/K27.jpeg (S21: Dutch ultimatum standoff under canopy)
- frames/flow_refs/K30.jpeg (S23: Calm King close-up on throne)

Headless: blender -b -P meeting_film.py
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
import meeting_world as mw
for m in (kit, world, mw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("27",    "S21", 1,    310),
    ("28-29", "S22", 311,  884),
    ("30",    "S23", 885,  1158),
]

CAM_DESIGN = [
    # S21 (K27): Wide pavilion framing matching K27.jpeg
    (1,    (0.05, -5.30, 1.62), (0.05, 0.05, 1.25), 28),
    (150,  (0.05, -5.00, 1.58), (0.05, 0.05, 1.25), 28),
    (310,  (0.05, -4.70, 1.54), (0.05, 0.05, 1.25), 28),

    # S22: Tense dialogue movement between Imhoff and the King
    (311,  (-0.65, -3.80, 1.50), (-1.10, 0.00, 1.30), 32), # Framing Imhoff demanding
    (520,  (-0.15, -3.60, 1.45), (0.00, 0.00, 1.05),  32), # Panning across treaty table
    (700,  (0.55, -3.70, 1.48),  (1.40, 0.00, 1.30),  32), # Framing King refusing
    (884,  (0.15, -4.20, 1.55),  (0.10, 0.00, 1.20),  30), # Pull back to tense standoff

    # S23 (K30): Medium close-up on King Marthanda Varma matching K30.jpeg
    (885,  (0.80, -2.15, 1.48),  (1.55, 0.00, 1.38),  36),
    (1020, (0.86, -2.05, 1.47),  (1.55, 0.00, 1.38),  36),
    (1158, (0.92, -1.95, 1.46),  (1.55, 0.00, 1.38),  36),
]

K27_DESIGN = 150
K30_DESIGN = 1020


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


def build(samples=24):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.view_settings.exposure = 0.0

    w = mw.build_world(end + 20)

    # Idle breathing for Imhoff
    import random
    rng = random.Random(42)
    if "imhoff" in w and w["imhoff"]:
        kit.animate_idle(w["imhoff"], rng, 1, end, amount=0.006)

    # Camera setup
    cd = bpy.data.cameras.new("MeetingCamera")
    cd.lens = 28
    cd.clip_start = 0.1
    cd.clip_end = 500.0
    cam = bpy.data.objects.new("MeetingCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam

    target = bpy.data.objects.new("MeetingCamTarget", None)
    sc.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"

    for f_d, pos, look, lens in CAM_DESIGN:
        f_real = rt(f_d)
        cam.location = pos
        target.location = look
        cd.lens = lens
        cam.keyframe_insert("location", frame=f_real)
        target.keyframe_insert("location", frame=f_real)
        cd.keyframe_insert("lens", frame=f_real)

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    sc.timeline_markers.new("K27", frame=rt(K27_DESIGN))
    sc.timeline_markers.new("K30", frame=rt(K30_DESIGN))

    out_blend = os.path.join(HERE, "Meeting.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    with open(os.path.join(HERE, "renders", "timing_meeting.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Meeting film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
