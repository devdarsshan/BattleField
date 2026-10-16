"""Varkala cliffs (S27, clip 34) in Varkala.blend, one continuous camera gliding along the
clifftop road (K34).

"The allies push south toward Attingal and Varkala." -> high behind the allied column as it
marches along the road, sea and red cliffs on the left.
"But at Varkala they meet about five thousand Nairs ..." -> the camera rises and looks ahead:
a solid wall of Nairs fills the road; the column halts.
"... men trained to fight with sword and shield from boyhood." -> the Nairs stamp and
brandish their swords; the front ranks step forward.
"The allies cannot break through, and they pull back." -> the column turns about and walks
back the way it came; the camera lifts away.

Headless: blender -b -P varkala_film.py   (writes Varkala.blend and renders/timing_varkala.json)
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
import pepper_world
import kochi_world
import port_world
import varkala_world as vw
for m in (kit, world, pepper_world, kochi_world, port_world, vw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("34", "S27", 1, 465),
]

# Story events in design frames (clip time = narration time + 0.8 s; pauses in audio/S27.wav at
# 3.9, 8.0, 14.0 and 16.5 s).
EVENTS = dict(
    march=8,          # the column is already on the move
    halt=168,         # 7.0 s, just after "...they meet about five thousand Nairs"
    brandish=221,     # 9.2 s: "men trained to fight with sword and shield ..."
    step=245,         # 10.2 s: the front ranks step forward
    back=392,         # 16.3 s: "The allies cannot break through, and they pull back."
    end=465,
)

# (design frame, camera position, look-at, lens mm)
CAM_DESIGN = [
    (1,   (-26.0, -68.0, 47.0), (-6.0, -40.0, 19.0), 30),
    (120, (-25.0, -55.0, 47.0), (-7.0, -27.0, 19.0), 30),
    (200, (-24.0, -45.0, 47.0), (-7.0, -14.5, 19.0), 30),
    (330, (-23.0, -42.5, 48.0), (-7.0, -13.0, 19.0), 30),
    (465, (-26.0, -52.0, 52.0), (-7.0, -23.0, 19.0), 30),
]
K34_DESIGN = 300


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

    ev = {k: rt(v) for k, v in EVENTS.items()}
    ev["end"] = end
    keep = [(p[0], p[1], 8.0) for _, p, _, _ in CAM_DESIGN]
    vw.build_world(ev, keep=keep)

    cd = bpy.data.cameras.new("VarkalaCamera")
    cd.lens = 30
    cd.clip_start = 0.5
    cd.clip_end = 1500.0
    cam = bpy.data.objects.new("VarkalaCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("VarkalaCamTarget", None)
    sc.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for f_d, pos, look, lens in CAM_DESIGN:
        f = rt(f_d)
        cam.location = pos
        target.location = look
        cd.lens = lens
        cam.keyframe_insert("location", frame=f)
        target.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    sc.timeline_markers.new("K34", frame=rt(K34_DESIGN))
    sc.timeline_markers.new("halt", frame=ev["halt"])
    sc.timeline_markers.new("turn back", frame=ev["back"])

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Varkala.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_varkala.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print(f"Varkala film built: {end} frames, {len(bpy.data.objects)} objects")
    for clip, beat, f0, f1, wav, secs in clips:
        print(f"  clip {clip} {beat}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {secs:.1f} s)")


build()
