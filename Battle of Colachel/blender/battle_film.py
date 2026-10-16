"""Battle near Kollam (S25-S26, clips 32-33) in Battle.blend, one continuous camera.

S25 (K32): high over the allied army: Dutch blocks in blue coats and the rajas' soldiers in
coloured turbans; their guns fire ("the war goes the Dutch way"), the camera trucks east over
the paddies to the Travancore ramparts, 16 bronze guns and the powder store; the allies
march on ("march on the Travancore army near Kollam").
S26 (K33): the camera swings round to the south-east of the Travancore line. A mortar fires,
the shell lands on the powder store ("lands on the ... gunpowder store"), its fuse smokes,
and it blows up ("It blows up"): fireball, debris, a tall smoke column. The Nairs run
("soldiers run"), the Dutch storm the guns ("capture sixteen cannons"), and the camera
pushes in and holds on the burning store ("Remember that gunpowder store").

Headless: blender -b -P battle_film.py   (writes Battle.blend and renders/timing_battle.json)
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
import battle_world as bw
for m in (kit, world, pepper_world, kochi_world, port_world, bw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("32", "S25", 1, 322),
    ("33", "S26", 323, 694),
]

# Story events in design frames (clip time = narration time + 0.8 s lead; word times from the
# pauses in audio/S25.wav and S26.wav).
EVENTS = dict(
    s25_shots=[30, 44, 58, 72],          # allied guns fire: "At first, the war goes the Dutch way"
    t_shots=(70, 190),                   # the Travancore guns answer
    march=203,                           # S25 8.4 s: "...march on the Travancore army near Kollam"
    mortar=331,                          # S26 0.35 s: the mortar fires
    impact=383,                          # S26 2.5 s: "...shell lands on the Travancore gunpowder store"
    halt=443,                            # the rear blocks halt at the paddies
    blast=460,                           # S26 5.7 s: "It blows up."
    run=474,                             # S26 6.3 s: "The Travancore soldiers run"
    charge=489,                          # S26 6.9 s: the Dutch storm the guns
    taken=616,                           # S26 12.2 s: "...the Dutch capture sixteen cannons"
    end=694,
)

# Camera path: (design frame, position, look-at, lens mm)
CAM_DESIGN = [
    (1,   (-40.0, -46.0, 22.0), (-12.0, 14.0, 9.0), 30),
    (120, (-31.0, -50.0, 23.0), (-4.0, 15.0, 9.0), 30),
    (215, (-13.0, -54.0, 25.0), (9.0, 15.0, 9.0), 30),
    (322, (14.0, -51.0, 25.0), (27.0, 16.0, 8.0), 30),
    (383, (52.0, -31.0, 23.0), (40.0, 14.0, 4.5), 30),
    (460, (57.0, -28.0, 22.0), (42.0, 15.0, 5.5), 30),
    (560, (61.0, -26.0, 21.0), (41.0, 13.0, 6.5), 30),
    (633, (63.0, -22.0, 19.0), (45.0, 15.0, 7.5), 30),
    (694, (63.0, -19.0, 18.0), (46.0, 15.5, 8.0), 30),
]
K32_DESIGN = 300
K33_DESIGN = 500


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

    ev = {k: ([rt(f) for f in v] if isinstance(v, list) else tuple(rt(f) for f in v) if isinstance(v, tuple)
              else rt(v)) for k, v in EVENTS.items()}
    ev["end"] = end
    keep = [(p[0], p[1], 7.0) for _, p, _, _ in CAM_DESIGN]
    bw.build_world(ev, keep=keep)

    cd = bpy.data.cameras.new("BattleCamera")
    cd.lens = 30
    cd.clip_start = 0.5
    cd.clip_end = 1200.0
    cam = bpy.data.objects.new("BattleCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    shake = bpy.data.objects.new("CamShake", None)       # small jolt when the store blows
    sc.collection.objects.link(shake)
    target = bpy.data.objects.new("BattleCamTarget", None)
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
    cam.parent = shake
    b = ev["blast"]
    for k, (dx, dy, dz) in enumerate(((0, 0, 0), (0.35, -0.2, 0.3), (-0.3, 0.25, -0.2), (0.22, 0.1, 0.18),
                                      (-0.15, -0.12, -0.1), (0.08, 0.06, 0.05), (0, 0, 0))):
        shake.location = (dx, dy, dz)
        shake.keyframe_insert("location", frame=b + (0 if k == 0 else 1 + 2 * k))

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    sc.timeline_markers.new("K32", frame=rt(K32_DESIGN))
    sc.timeline_markers.new("K33", frame=rt(K33_DESIGN))
    sc.timeline_markers.new("blast", frame=ev["blast"])

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Battle.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_battle.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Battle film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
