"""The Varkala Cliff Halt & Nair Shield Wall (Beat S27, Clip 34).

Built in its own file Varkala.blend reusing varkala_world.py.
Matches Flow reference:
- frames/flow_refs/K34.jpeg (S27: Sheer red laterite cliffs, turquoise sea, coconut palms,
  massive Nair warrior shield wall halting the advancing Dutch and allied column).

Headless: blender -b -P varkala_film.py
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
import varkala_world as vw
for m in (kit, world, vw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("34", "S27", 1, 460),
]

CAM_DESIGN = [
    # Elevated 3/4 view looking down along the clifftop road and Arabian sea (K34 framing)
    (1,   (16.0, -25.0, 26.0), (2.0, 4.0, 12.0), 32),
    (220, (14.0, -19.0, 23.0), (2.0, 6.0, 12.0), 32),
    (460, (12.0, -13.0, 20.0), (2.0, 8.0, 12.0), 32),
]


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

    w = vw.build_world(end_frame=end + 20)

    # Animate allied column advancing and then coming to a dead halt
    halt_frame = round(end * 0.45)
    if "allies" in w:
        figs = w["allies"].get("figures", [])
        for fig in figs:
            base_y = fig.location.y
            fig.keyframe_insert("location", frame=1)
            # Advance +3.8m
            fig.location.y = base_y + 3.8
            fig.keyframe_insert("location", frame=halt_frame)
            # Halted until end of scene
            fig.keyframe_insert("location", frame=end)

        banner = w["allies"].get("banner")
        if banner:
            base_y = banner.location.y
            banner.keyframe_insert("location", frame=1)
            banner.location.y = base_y + 3.8
            banner.keyframe_insert("location", frame=halt_frame)
            banner.keyframe_insert("location", frame=end)

    # Camera setup
    cd = bpy.data.cameras.new("VarkalaCamera")
    cd.lens = 38
    cd.clip_start = 0.5
    cd.clip_end = 800.0
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
        f_real = rt(f_d)
        cam.location = pos
        target.location = look
        cd.lens = lens
        cam.keyframe_insert("location", frame=f_real)
        target.keyframe_insert("location", frame=f_real)
        cd.keyframe_insert("lens", frame=f_real)

    out_blend = os.path.join(HERE, "Varkala.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print(f"Varkala film built: {end} frames, {len(bpy.data.objects)} objects")
    for clip, beat, f0, f1, wav, secs in clips:
        dur = (f1 - f0 + 1) / FPS
        print(f"  clip {clip} {beat}: frames {f0}-{f1} ({dur:.1f} s, narration {secs:.1f} s)")


if __name__ == "__main__":
    build()
