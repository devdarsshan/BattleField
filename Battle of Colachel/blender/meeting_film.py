"""The meeting under the royal canopy (S21, S22, S23 = shot-list clips 27, 28-29, 30), Meeting.blend.

One continuous camera:
  S21  K27 view from the front, slow push in. Van Imhoff points at the king from "He demands"
       and jabs his finger at "the Dutch will invade Travancore".
  S22  a slow orbit to the left round the meeting (the Koshy story). The king, calm, sweeps his
       hand toward the forests at "he will go into the forests"; Imhoff, stiff, points again at
       "the Dutch will follow him there"; the king answers with an easy open hand ("invading
       Europe one day").
  S23  the camera pushes in to the king (K30): he folds his arms and sits back, calm.

Headless: blender -b -P meeting_film.py   (saves Meeting.blend and renders/timing_meeting.json)
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
import palace_world as pw
import meeting_world as mw
for m in (kit, world, pw, mw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("27",    "S21", 1,   343),
    ("28-29", "S22", 344, 950),
    ("30",    "S23", 951, 1258),
]

# ---------------------------------------------------------------- camera (design frames)
ORBIT_C = Vector((0.1, 0.5, 0.0))      # orbit centre (between the table and the throne)
KING_HEAD = Vector((mw.THRONE[0] - 0.15, mw.THRONE[1] - 0.05, 1.45))
IMHOFF_HEAD = Vector((mw.IMHOFF[0], mw.IMHOFF[1], 1.6))
MID = Vector((0.1, 0.6, 1.1))


def orbit(angle_deg, r, z):
    a = math.radians(angle_deg)
    return ORBIT_C + Vector((r * math.cos(a), r * math.sin(a), z))


# (frame, position, look-at, lens)
CAM_KEYS = [
    # S21: the K27 view (front posts at the frame edges), pushing in slowly
    (1,    orbit(-90, 5.2, 1.45), MID, 25),
    (343,  orbit(-92, 4.7, 1.45), MID + Vector((0.05, 0, 0)), 25),
]
# S22: orbit to the left (toward the Dutch side) so the king's face turns to camera
for f, ang, r, z, look, lens in ((420, -95, 4.65, 1.48, MID, 25),
                                 (520, -101, 4.6, 1.5, MID + Vector((0.25, 0, 0.05)), 26),
                                 (640, -108, 4.55, 1.52, KING_HEAD.lerp(MID, 0.45), 27),    # "into the forests"
                                 (740, -114, 4.5, 1.52, IMHOFF_HEAD.lerp(MID, 0.5), 27),    # "follow him there"
                                 (850, -120, 4.45, 1.5, KING_HEAD.lerp(MID, 0.4), 28),      # "invading Europe"
                                 (950, -125, 4.4, 1.5, KING_HEAD.lerp(MID, 0.25), 28)):
    CAM_KEYS.append((f, orbit(ang, r, z), look, lens))
# S23: push in to the king from the front (K30 framing: seated full length, guard at the right)
CAM_KEYS += [
    (1060, Vector((-1.2, -2.7, 1.38)), KING_HEAD + Vector((0, 0, -0.4)), 28),
    (1258, Vector((0.3, -1.45, 1.25)), KING_HEAD + Vector((0.05, 0.05, -0.48)), 28),
]

# ---------------------------------------------------------------- acting (design frames)
# Word times estimated from the recordings (S21 12.9 s, S22 23.9 s, S23 11.4 s) and lines.txt.
IMHOFF_ACT = [   # (frame, pose)
    (1,   {"armL": (0.04, -0.06, 0), "armR": (0.04, 0.06, 0), "head": (0, 0, 0.1)}),
    (30,  {"armR": (0.05, 0.06, 0)}),
    (52,  {"armR": (1.45, 0.0, 0.12)}),                    # "He demands..."
    (250, {"armR": (1.42, 0.0, 0.12)}),
    (262, {"armR": (1.72, 0.0, 0.1), "head": (-0.05, 0, 0.1)}),   # jab: "the Dutch will invade"
    (272, {"armR": (1.42, 0.0, 0.12)}),
    (282, {"armR": (1.7, 0.0, 0.1)}),
    (294, {"armR": (1.45, 0.0, 0.12), "head": (0, 0, 0.1)}),
    (420, {"armR": (1.45, 0.0, 0.12)}),
    (450, {"armR": (0.05, 0.06, 0)}),                      # arm down during the narrator's aside
    (705, {"armR": (0.05, 0.06, 0)}),
    (728, {"armR": (1.5, 0.0, 0.15), "head": (-0.05, 0, 0.12)}),   # "the Dutch will follow him there"
    (800, {"armR": (1.5, 0.0, 0.15)}),
    (830, {"armR": (0.05, 0.06, 0), "head": (0, 0, 0.1)}),
]
KING_ACT = [
    (1,   {**kit.ARM_REST_SEATED, "head": (0, 0, 0)}),
    (600, {**kit.ARM_REST_SEATED, "head": (0, 0, 0)}),
    (628, {"armL": (1.25, -0.3, 0.0), "head": (0, 0, -0.15)}),    # lifts a hand, then sweeps it out
    (668, {"armL": (0.2, -1.5, 0.45), "head": (-0.05, 0, -0.55)}),   # ... toward the forests
    (700, {"armL": (0.25, -1.45, 0.4), "head": (-0.05, 0, -0.5)}),
    (720, {"armL": kit.ARM_REST_SEATED["armL"], "head": (0, 0, 0.0)}),
    (845, {"armR": kit.ARM_REST_SEATED["armR"], "head": (0.0, 0, 0.0)}),
    (870, {"armR": (1.0, 0.45, 0.2), "head": (-0.06, 0.05, 0.08)}),  # "invading Europe one day": open hand
    (920, {"armR": (0.95, 0.4, 0.15)}),
    (948, {"armR": kit.ARM_REST_SEATED["armR"], "head": (0, 0, 0)}),
]
FOLD = (958, 984)        # S23: arms fold as the push-in starts
K27_DESIGN = 150
K30_DESIGN = 1200


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


def act(parts, keys, rt):
    for f, pose in keys:
        kit.key_pose(parts, rt(f), pose)


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.look = "AgX - Base Contrast"      # close scene (Blender_Build_Rules: colour management)
    sc.view_settings.exposure = 0.0

    w = mw.build_world(end)
    rng = random.Random(21)
    _, ip = w["imhoff"]
    _, kp = w["king"]
    act(ip, IMHOFF_ACT, rt)
    act(kp, KING_ACT, rt)
    kit.pose_arms_folded(kp, rt(FOLD[0]), rt(FOLD[1]))
    kit.key_pose(kp, rt(FOLD[1]) + 40, {"head": (-0.04, 0, 0.12)})     # sits back, a small calm smile
    kit.key_pose(kp, rt(1150), {"head": (-0.06, 0, 0.05)})
    kit.key_pose(kp, end, {"head": (-0.05, 0, 0.08)})
    kit.animate_rig_idle(ip, rng, 1, end, body=0.004, head=0.0, skip=("head",))   # Imhoff: stiff
    kit.animate_rig_idle(kp, rng, 1, end, body=0.01, head=0.0, skip=("head",))

    cd = bpy.data.cameras.new("MeetingCamera")
    cd.clip_start = 0.1
    cd.clip_end = 1500.0
    cam = bpy.data.objects.new("MeetingCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("MeetingCamTarget", None)
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
    sc.timeline_markers.new("K27", frame=rt(K27_DESIGN))
    sc.timeline_markers.new("K30", frame=rt(K30_DESIGN))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Meeting.blend"))
    with open(os.path.join(HERE, "renders", "timing_meeting.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Meeting film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
