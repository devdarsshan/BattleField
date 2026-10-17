"""Udayagiri (S55-S58; clips 67-70) in Udayagiri.blend.

One timeline, four beats, a clean cut between each (timeline markers switch the camera). Camera keys and
events are written as fractions of each beat (or as spoken words), so a re-recorded voice re-times everything.

S55 (K67) "...The king offers De Lannoy a job."     inside the hill fort: push in on the king, De Lannoy, the guards.
S56 (K68) "Train my army... De Lannoy says yes."     closer, hold with a slight orbit; the bow lands on "De Lannoy says yes".
S57 (K69) "He drills the Travancore soldiers..."     drill ground: volleys, guns, the works and the masons; pull out.
S58 (K70) "The king gives him a title. Valiya Kappithan..."  push in; the sash goes on at "Valiya Kappithan".

Headless: blender -b -P udayagiri_film.py   (writes Udayagiri.blend and renders/timing_udayagiri.json)
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
import port_world
import landing_world as lw
import udayagiri_world as uw
for m in (kit, world, port_world, lw, uw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
BEATS = [("67", "S55"), ("68", "S56"), ("69", "S57"), ("70", "S58")]
OX, OY = uw.DRILL


def D(u, v, z):
    """A point in drill-local coordinates."""
    return (OX + u, OY + v, z)


# camera keys per beat: (fraction of the beat, position, look-at, lens mm); Z is absolute (the ground is ~0)
CAMS = {
    "S55": [(0.0, (15.0, -17.0, 11.0), (-3.0, 1.5, 0.8), 30),
            (1.0, (8.5, -10.0, 6.2), (-4.5, 1.0, 0.9), 34)],
    "S56": [(0.0, (0.8, -0.3, 1.7), (1.5, 4.3, 1.2), 30),
            (1.0, (1.9, 0.0, 1.7), (1.6, 4.3, 1.25), 32)],
    "S57": [(0.0, D(11.0, -4.0, 3.8), D(0.0, 5.5, 1.4), 32),
            (0.5, D(20.0, -14.0, 9.0), D(0.0, 5.0, 0.8), 32),
            (1.0, D(26.0, -16.0, 14.5), D(1.5, 5.5, 0.5), 41)],
    "S58": [(0.0, D(-3.0, -10.5, 6.0), D(-3.7, -0.2, 0.9), 38),
            (1.0, D(-3.3, -8.0, 4.6), D(-3.8, -0.6, 1.2), 38)],
}
KEYFRAMES = {"K67": ("S55", 0.6), "K68": ("S56", 0.5), "K69": ("S57", 0.9), "K70": ("S58", 0.6)}
def cam_path():
    """Plan points along every camera path (world x, y), for keeping trees and palms off them."""
    pts = []
    for keys in CAMS.values():
        for (_, a, _, _), (_, b, _, _) in zip(keys, keys[1:]):
            for k in range(10):
                t = k / 10
                pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        pts.append(keys[-1][1][:2])
    return pts



def timed_clips():
    lines = F["beat_lines"]()
    out, f0 = [], 1
    for clip, beat in BEATS:
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


def word_frame(clips, beat, phrase, extra=0.0):
    """Frame at which `phrase` starts being spoken in the beat's line (narration starts 0.8 s in)."""
    text = F["beat_lines"]()[beat]
    c = next(c for c in clips if c[1] == beat)
    i = text.find(phrase)
    if i < 0:
        raise ValueError(f"{phrase!r} not in {beat}")
    return int(c[2] + (F["NARRATION_LEAD"] + c[5] * i / len(text) + extra) * FPS)


def make_camera(sc, name, keys, rng):
    cd = bpy.data.cameras.new(name)
    cd.clip_start = 0.1
    cd.clip_end = 3000.0
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    target = bpy.data.objects.new(name + "Target", None)
    sc.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    beat = name[3:]
    f0, f1 = rng[beat]
    for u, pos, look, lens in keys:
        f = round(f0 + u * (f1 - f0))
        cam.location = pos
        target.location = look
        cd.lens = lens
        cam.keyframe_insert("location", frame=f)
        target.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
    return cam


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rng = {c[1]: (c[2], c[3]) for c in clips}
    ev = dict(end=end)
    for beat, (a, b) in rng.items():
        ev[f"r{int(beat[1:])}"] = (a, b)
    ev["offer55"] = word_frame(clips, "S55", "offers", 0.0)
    ev["yes56"] = word_frame(clips, "S56", "De Lannoy says yes", 0.0)
    v0 = word_frame(clips, "S57", "fire muskets", 0.3)
    ev["volleys57"] = [v0, v0 + 100, v0 + 200]
    c0 = word_frame(clips, "S57", "work cannon", 0.2)
    ev["cannon57"] = [c0, c0 + 110]
    ev["title58"] = word_frame(clips, "S58", "Valiya Kappithan", 0.0)

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    uw.build_world(ev, cam_path())

    cams = {beat: make_camera(sc, f"Cam{beat}", keys, rng) for beat, keys in CAMS.items()}
    for clip, beat, f0, f1, _, _ in clips:
        mk = sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
        mk.camera = cams[beat]
    sc.camera = cams["S55"]
    for name, (beat, u) in KEYFRAMES.items():
        f0, f1 = rng[beat]
        sc.timeline_markers.new(name, frame=round(f0 + u * (f1 - f0)))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Udayagiri.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_udayagiri.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips],
                   "events": {k: v for k, v in ev.items() if k not in ("end",)}}, f, indent=1)
    print("Udayagiri film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")
    print("  events", {k: v for k, v in ev.items() if k != "end"})


build()
