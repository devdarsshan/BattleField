"""Battle of the Earthworks & Powder Magazine Explosion (Beats S25, S26, Clips 32, 33).

Built in its own file Battle.blend reusing battle_world.py.
Matches Flow references:
- frames/flow_refs/K32.jpeg (S25: Allied columns advancing through paddy fields toward earthworks)
- frames/flow_refs/K33.jpeg (S26: Travancore 16 guns firing and powder store explosion)

Headless: blender -b -P battle_film.py
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
import battle_world as bw
for m in (kit, world, bw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("32", "S25", 1,   288),
    ("33", "S26", 289, 626),
]

# Camera design keys:
# S25 (K32): High elevated view looking east down the paddy fields and road
# S26 (K33): Dramatic medium view focusing on the battery and the powder magazine explosion
CAM_DESIGN = [
    # S25 (K32 framing): High wide isometric angle showing allied column, paddy fields, earthworks
    (1,    (-16.0, -32.0, 22.0), (-1.0, -2.0, 1.5), 34),
    (140,  (-13.0, -29.0, 20.5), (1.0, -2.0, 1.5),  34),
    (288,  (-10.0, -26.0, 19.0), (3.0, -2.0, 1.5),  34),

    # S26 (K33 framing): Dramatic medium elevated angle showing charging troops, exploding shed, and towering smoke plume
    (289,  (2.0, -25.0, 15.0),   (22.0, -4.0, 7.0), 32),
    (420,  (3.0, -23.5, 14.5),   (22.5, -4.0, 7.5), 32), # Moment of blast
    (520,  (4.0, -22.0, 14.0),   (23.0, -4.0, 8.0), 32), # Towering smoke column
    (626,  (5.0, -20.5, 13.5),   (23.5, -4.0, 8.5), 32),
]

K32_DESIGN = 140
K33_DESIGN = 420


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

    real_blast_frame = rt(K33_DESIGN)
    w = bw.build_world(end + 20, blast_frame=real_blast_frame)

    # Animate advancing allied soldiers along +X during S25
    s25_f0, s25_f1 = clips[0][2], clips[0][3]
    if "allied" in w:
        for d in w["allied"].get("dutch", []):
            base_x = d.location.x
            d.keyframe_insert("location", frame=s25_f0)
            d.location.x = base_x + 7.5
            d.keyframe_insert("location", frame=s25_f1)
        for a in w["allied"].get("allies", []):
            base_x = a.location.x
            a.keyframe_insert("location", frame=s25_f0)
            a.location.x = base_x + 7.0
            a.keyframe_insert("location", frame=s25_f1)
        for g in w["allied"].get("guns", []):
            base_x = g.location.x
            g.keyframe_insert("location", frame=s25_f0)
            g.location.x = base_x + 6.5
            g.keyframe_insert("location", frame=s25_f1)

    # Camera setup
    cd = bpy.data.cameras.new("BattleCamera")
    cd.lens = 32
    cd.clip_start = 0.5
    cd.clip_end = 800.0
    cam = bpy.data.objects.new("BattleCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam

    target = bpy.data.objects.new("BattleCamTarget", None)
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
    sc.timeline_markers.new("K32", frame=rt(K32_DESIGN))
    sc.timeline_markers.new("K33", frame=rt(K33_DESIGN))

    out_blend = os.path.join(HERE, "Battle.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    with open(os.path.join(HERE, "renders", "timing_battle.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Battle film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
