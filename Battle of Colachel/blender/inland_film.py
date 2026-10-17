"""Inland beats S33, S35, S36, S37 (clips 40, 42-43, 44-45, 46) in Inland.blend: one timeline, one
camera, a clean cut between beats (each beat is a different place; see inland_world.py).

S33 (K40) "Now look at the ground..." -> high over the sea off Colachel: the village and its
  beach, then a glide inland over the paddies and palm groves ("rice fields and palm groves") until
  Padmanabhapuram fills the top of the frame at the foot of the hills ("...the king's palace").
S35 (K42) "How big is their force?..." -> low beside the Dutch column on the palace's south-east
  road: the orange flag, the blue coats ("a few hundred European soldiers"), the rajas' men
  ("local troops beside them"); the camera rises and looks past them to the palace roofs
  ("And now the Dutch are close to his palace").
S36 (K44) "Marthanda Varma rushes south..." -> high over the field before the Kalkulam gate: the
  royal elephant comes through the crowd to the gate ("At Kalkulam"), the Nairs stamp and raise
  their arms ("he raises about two thousand more Nair fighters"), more stream in down the road.
S37 (K46) "Legend says..." -> dawn at Thiruvattar: push in past the flag-mast to the king kneeling
  before the shrine; he bows and lays his sword on the stone ("lays his sword before the god");
  the camera rises up the brass mast toward the gopuram for the date.

Clip lengths follow the narration (audio/Sxx.wav when recorded, else the text estimate and the
placeholder voice), exactly as film.py; camera keys and events are written in design frames and
retimed. Headless: blender -b -P inland_film.py  (writes Inland.blend and renders/timing_inland.json)
Optional env INLAND_SETS=A|B|C|AB... builds only those sets (quick tests).
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
import pepper_world
import port_world
import palace_world
import inland_world as iw
for m in (kit, world, pepper_world, port_world, palace_world, iw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("40", "S33", 1, 408),
    ("42-43", "S35", 409, 943),
    ("44-45", "S36", 944, 1255),
    ("46", "S37", 1256, 1696),
]

# story events, design frames (word times estimated over the line: 0.8 s lead + chars / 12.5 cps)
EVENTS = dict(
    arrive=1070,      # S36 "At Kalkulam" (3.2 s): the elephant reaches the gate a moment later
    raise_=1083,      # S36 "he raises about two thousand more Nair fighters" (5.8 s): they stamp
    lay=1468,         # S37 "...and lays his sword before the god" (8.8 s)
)

# camera per beat: (set origin, [(design frame, position, look-at, lens)]), positions relative
# to the set origin (set A uses the Colachel beach coordinates directly)
CAM = {
    "S33": ((0.0, 0.0, 0.0), [
        (1,   (95.0, -80.0, 45.0), (-10.0, 50.0, 0.0), 30),
        (200, (110.0, -75.0, 95.0), (0.0, 150.0, 0.0), 30),
        (320, (112.0, -35.0, 118.0), (36.0, 250.0, 0.0), 32),
        (408, (105.0, 30.0, 112.0), (38.0, 300.0, 6.0), 34),
    ]),
    # S35 positions are relative to the palace (inland_world.PAL), on its south-east road
    "S35": ((iw.PAL[0], iw.PAL[1], 0.0), [
        (409, (52.0, -100.0, 9.0), (46.0, -72.0, 1.4), 30),
        (620, (55.0, -108.0, 9.5), (50.0, -80.0, 1.6), 30),
        (800, (57.5, -115.0, 12.0), (44.0, -74.0, 3.0), 30),
        (943, (60.5, -123.5, 16.0), (18.0, -28.0, 0.0), 40),
    ]),
    "S36": ((iw.FO[0], iw.FO[1], 0.0), [
        (944,  (-44.0, -58.0, 24.0), (-18.0, 4.0, 3.0), 30),
        (1100, (-32.0, -46.0, 16.0), (-10.0, -2.0, 3.5), 30),
        (1255, (-24.0, -38.0, 11.0), (-6.0, -4.0, 4.0), 30),
    ]),
    "S37": ((iw.TO[0], iw.TO[1], 0.0), [
        (1256, (-9.5, -16.5, 3.3), (-4.0, 6.5, 2.8), 27),
        (1468, (-10.8, -10.5, 2.1), (-5.4, -0.4, 1.2), 30),
        (1530, (-10.6, -10.4, 2.2), (-5.4, -0.4, 1.3), 30),
        (1696, (-8.5, -13.5, 4.2), (3.5, 8.0, 8.5), 30),
    ]),
}
# sun per beat: (direction, energy, colour). S37 is the dawn: low, warmer, pink-gold.
SUN = {
    "S33": ((0.9, -0.1, -0.35), 8.0, (1.0, 0.86, 0.70)),
    "S35": ((0.45, -0.75, -0.45), 8.5, (1.0, 0.80, 0.58)),
    "S36": ((0.5, -0.6, -0.5), 8.5, (1.0, 0.82, 0.60)),
    "S37": ((0.7, 0.55, -0.38), 7.5, (1.0, 0.70, 0.50)),
}
SKY_FILL = {"S33": 1.2, "S35": 0.95, "S36": 0.95, "S37": 0.8}
SKY_DAWN = {"S33": 0.0, "S35": 0.0, "S36": 0.0, "S37": 0.8}
SUN_ANGLE = {"S33": 9.0, "S35": 9.0, "S36": 9.0, "S37": 22.0}
KEYFRAMES = {"K40": 380, "K42": 700, "K44": 1200, "K46": 1440}


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


def _flatten_cuts(obs, ends, starts):
    """Hard cuts: hold the last key of a beat (constant) and give the keys either side of a cut
    flat handles, so a far-away next set never bends the curve inside a beat."""
    for ob in obs:
        ad = ob.animation_data
        if not ad or not ad.action:
            continue
        for fc in iw._fcurves(ad.action):
            for kp in fc.keyframe_points:
                f = round(kp.co.x)
                if f in ends or f in starts:
                    kp.handle_left_type = kp.handle_right_type = "FREE"
                    kp.handle_left = (kp.co.x - 4.0, kp.co.y)
                    kp.handle_right = (kp.co.x + 4.0, kp.co.y)
                if f in ends:
                    kp.interpolation = "CONSTANT"
            fc.update()


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    rng_beats = {beat: (f0, f1) for _, beat, f0, f1, _, _ in clips}

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    sc.view_settings.look = "AgX - Base Contrast"

    ev = {"s33": rng_beats["S33"], "s35": rng_beats["S35"], "s36": rng_beats["S36"], "s37": rng_beats["S37"],
          "arrive": rt(EVENTS["arrive"]), "raise": rt(EVENTS["raise_"]), "lay": rt(EVENTS["lay"]), "end": end}
    rig_c, sun = iw.build_world(ev, sets=os.environ.get("INLAND_SETS", "ABC"))

    cd = bpy.data.cameras.new("InlandCamera")
    cd.lens = 30
    cd.clip_start = 0.3
    cd.clip_end = 3000.0
    cam = bpy.data.objects.new("InlandCamera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("InlandCamTarget", None)
    sc.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for beat, (org, keys) in CAM.items():
        o = Vector(org)
        for f_d, pos, look, lens in keys:
            f = rt(f_d)
            cam.location = o + Vector(pos)
            target.location = o + Vector(look)
            cd.lens = lens
            cam.keyframe_insert("location", frame=f)
            target.keyframe_insert("location", frame=f)
            cd.keyframe_insert("lens", frame=f)
    # the sun is re-aimed at each cut
    for beat, (d, energy, col) in SUN.items():
        f = rng_beats[beat][0]
        sun.rotation_euler = Vector(d).normalized().to_track_quat("-Z", "Y").to_euler()
        sun.data.energy = energy
        sun.data.color = col
        sun.keyframe_insert("rotation_euler", frame=f)
        sun.data.keyframe_insert("energy", frame=f)
        sun.data.keyframe_insert("color", frame=f)
        sun.data.angle = math.radians(SUN_ANGLE[beat])
        sun.data.keyframe_insert("angle", frame=f)
    bg = next(n for n in sc.world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
    for beat, k in SKY_FILL.items():
        bg.inputs["Strength"].default_value = k
        bg.inputs["Strength"].keyframe_insert("default_value", frame=rng_beats[beat][0])
        dm = sc.world.node_tree.nodes["DawnMix"].inputs["Factor"]
        dm.default_value = SKY_DAWN[beat]
        dm.keyframe_insert("default_value", frame=rng_beats[beat][0])
    for fc in iw._fcurves(sc.world.node_tree.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    for ob in (sun, sun.data):
        for fc in iw._fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    ends = {f1 for _, _, _, f1, _, _ in clips[:-1]}
    starts = {f0 for _, _, f0, _, _, _ in clips[1:]}
    _flatten_cuts([cam, target, cd], ends, starts)

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    for k, f in KEYFRAMES.items():
        sc.timeline_markers.new(k, frame=rt(f))
    sc.timeline_markers.new("elephant at the gate", frame=ev["arrive"])
    sc.timeline_markers.new("lays his sword", frame=ev["lay"])
    sc.frame_set(1)

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Inland.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_inland.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print(f"Inland film built: {end} frames, {len(bpy.data.objects)} objects")
    for clip, beat, f0, f1, wav, secs in clips:
        print(f"  clip {clip} {beat}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {secs:.1f} s)")


build()
