"""Padmanabhapuram Courtyard - Disloyal Nobles Led Away (S15, shot-list clip 20).

Built in its own file Palace15.blend reusing palace_world.py.
Opens on the tense standoff in the palace courtyard (Flow reference K20_v1):
a group of disloyal nobles facing the palace steps where young Marthanda Varma
stands watching. Nair guards advance with spears and shields ("He spends his
first years fighting powerful families at home..."), surround and march the nobles away,
and on "He wins" the camera orbits and pushes in on the young king standing resolute
and alone on his veranda.

Headless: blender -b -P palace15_film.py
Saves Palace15.blend and renders/timing_palace15.json.
"""
import importlib
import json
import math
import os
import random
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
import palace_world as pw
for m in (kit, geo, world, kw, pw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("20", "S15", 1, 350),
]
# Camera orbit around courtyard matching K20_v1:
# starts high-angle over the south-west courtyard looking toward the veranda stairs
CAM_KEYS = [
    (1,   (0.5, -17.5, 7.8),   (8.5, -8.5, 2.8)),   # K20_v1 view: nobles left, guards right, king above
    (100, (2.2, -16.8, 7.2),   (8.0, -8.6, 2.7)),   # guards advance
    (200, (5.0, -15.2, 6.6),   (7.5, -8.8, 2.6)),   # nobles escorted away
    (280, (8.5, -13.5, 6.0),   (13.0, -8.7, 4.0)),  # following movement
    (350, (11.5, -11.8, 5.7),  ("K", 0.0, 0.0, 1.2)), # push in on king alone
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


def build_s15_figures(coll, frames, anchors, rng):
    """Add the disloyal nobles and Nair guards to the courtyard."""
    kw.register_palette()
    cast_c = kit.new_collection("S15_Cast")

    # The 6 disloyal nobles in the courtyard facing the veranda (towards +X/+Y)
    noble_spots = [
        (6.8, -8.8, math.radians(25)),
        (6.0, -9.6, math.radians(35)),
        (7.4, -9.8, math.radians(15)),
        (5.5, -10.5, math.radians(45)),
        (6.8, -10.6, math.radians(30)),
        (6.2, -11.4, math.radians(40)),
    ]
    nobles = []
    for i, (x, y, rz) in enumerate(noble_spots):
        root, parts = kw.make_raja(f"Noble{i}", cast_c, seed=200 + i, sash_tilt=0.1 * i)
        root.location = (x, y, 0.0)
        root.rotation_euler[2] = rz
        # Tense posture: arms folded or at sides
        kw.pose(parts, {"armR": (0.1, 0, 0.05), "armL": (0.1, 0, -0.05), "foreR": (0.4, 0, 0), "foreL": (0.4, 0, 0)})
        kit.animate_idle(root, rng, 1, frames, amount=0.015)
        # Animate marching away on frame 160-310 towards the gate
        gate_target = (pw.GATE_X + rng.uniform(-1.0, 1.0), pw.WALL[2] + 2.0)
        root.keyframe_insert("location", frame=160)
        root.location = (gate_target[0], gate_target[1], 0.0)
        root.rotation_euler[2] = math.radians(270)
        root.keyframe_insert("location", frame=310)
        root.keyframe_insert("rotation_euler", frame=180)
        nobles.append(root)

    # The Nair guards with shields and spears advancing in two ranks
    guard_spots = [
        (2.6, -8.5, math.radians(0)),
        (2.6, -9.7, math.radians(0)),
        (2.6, -10.9, math.radians(0)),
        (1.2, -8.5, math.radians(0)),
        (1.2, -9.7, math.radians(0)),
        (1.2, -10.9, math.radians(0)),
    ]
    guards = []
    for i, (x, y, rz) in enumerate(guard_spots):
        g = kit.make_figure(f"NairGuard{i}", cast_c, "nair_spear", seed=300 + i, cloth="cloth_r" if i % 2 else "cloth_w")
        g.location = (x, y, 0.0)
        g.rotation_euler[2] = rz
        # Advance toward nobles from frame 80 to 160
        g.keyframe_insert("location", frame=80)
        g.location = (x + 2.5, y, 0.0)
        g.keyframe_insert("location", frame=160)
        # Then escort them towards the gate
        gate_target = (pw.GATE_X + (i % 2) * 1.5 - 0.75, pw.WALL[2] + 3.0 - (i // 2) * 1.2)
        g.keyframe_insert("location", frame=170)
        g.location = (gate_target[0], gate_target[1], 0.0)
        g.rotation_euler[2] = math.radians(270)
        g.keyframe_insert("location", frame=315)
        g.keyframe_insert("rotation_euler", frame=180)
        guards.append(g)


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.eevee.volumetric_tile_size = "4"
    sc.eevee.volumetric_end = 1500
    sc.view_settings.exposure = 0.0
    rig, anchors, king = pw.build_world(end)
    rng = random.Random(7)
    build_s15_figures(rig, end, anchors, rng)

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
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Palace15.blend"))
    with open(os.path.join(HERE, "renders", "timing_palace15.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                              for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("palace15 film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
