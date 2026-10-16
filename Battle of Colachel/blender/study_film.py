"""Van Imhoff in his study in the Dutch fort at Kochi, at night (S20, shot-list clip 26).

Built in its own file Study.blend; matches the Flow reference frames/flow_refs/K26.jpeg.
One slow push-in: it opens on the K26 view (Imhoff writing by the candle, bookcase behind,
the open orange window on the moonlit harbour and the ship at right) and drifts in toward
him while he writes. On the last sentence ("And he believes the answer is force.") he stops
writing, straightens and lifts his head.

Headless: blender -b -P study_film.py   (saves Study.blend and renders/timing_study.json)
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

import colachel_kit as kit
import colachel_world as world
import kochi_world as kw
import study_world as sw
for m in (kit, world, kw, sw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("26", "S20", 1, 331),
]

# Camera keys in design frames: (frame, position, look-at, lens).
CAM_KEYS = [
    (1,   (0.35, 2.45, 1.8), (-0.75, -1.1, 1.05), 21),
    (165, (0.4, 1.95, 1.74), (-0.5, -0.95, 1.08), 23),
    (331, (0.45, 1.5, 1.66), (-0.15, -0.85, 1.12), 26),
]
# Imhoff's action, design frames (voice 12.4 s; words estimated from audio/lines.txt):
# 0.8-4.7 s "Van Imhoff comes to Kochi ...", 4.9-9.8 s "He writes that Dutch business ... ruin"
# (pen dips at "He writes"), 10.2-12.4 s "And he believes the answer is force."
BEATS = {"dip": 112, "stop": 246, "look": 268}
K26 = 1


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
    sc.view_settings.look = "AgX - Base Contrast"
    sc.view_settings.exposure = 0.0

    sw.build_world(end, {k: rt(v) for k, v in BEATS.items()})

    cd = bpy.data.cameras.new("StudyCamera")
    cd.clip_start = 0.05
    cd.clip_end = 600.0
    cam = bpy.data.objects.new("StudyCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("StudyCamTarget", None)
    sc.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for f, pos, look, lens in CAM_KEYS:
        cam.location = pos
        target.location = look
        cd.lens = lens
        cam.keyframe_insert("location", frame=rt(f))
        target.keyframe_insert("location", frame=rt(f))
        cd.keyframe_insert("lens", frame=rt(f))

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    sc.timeline_markers.new("K26", frame=rt(K26))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Study.blend"))
    with open(os.path.join(HERE, "renders", "timing_study.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Study film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
