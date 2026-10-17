"""Shared helpers for the small stand-alone dioramas (S60 chapel, S62 treaty tent): a floating ground tile with
earth strata on a plain backdrop, one sun + fill, a tracked camera with keys given as fractions of each beat,
and the timing/save boilerplate every film script has.  Used by chapel_film.py and treaty_film.py.
"""
import json
import math
import os
import random

import bpy
from mathutils import Vector

import colachel_kit as kit
from colachel_kit import T, Rx, Ry, Rz, S


def setup_backdrop(rgb, strength=1.0):
    """A flat studio-colour world (the diorama floats on it, as in the Flow refs)."""
    w = bpy.data.worlds.new("Backdrop")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    bg.inputs["Color"].default_value = (*kit.srgb_to_linear(rgb), 1)
    bg.inputs["Strength"].default_value = strength
    return w


def add_sun(coll, direction, energy, color=(1.0, 0.92, 0.80), angle=8.0):
    ld = bpy.data.lights.new("Sun", "SUN")
    ld.energy = energy
    ld.color = color
    ld.angle = math.radians(angle)
    sun = bpy.data.objects.new("Sun", ld)
    coll.objects.link(sun)
    sun.rotation_euler = Vector(direction).normalized().to_track_quat("-Z", "Y").to_euler()
    return sun


def make_tile(name, coll, w, d, top="grass", depth=1.6, seed=1, bump=0.06, cut=1.6, strata=(("sand", 0.18), ("soil", 0.7), ("soil_dk", 0.72))):
    """A floating ground tile centred on the origin, top at z=0. Corners are cut (a faceted outline) and the
    sides show earth strata. Returns (object, height function)."""
    rng = random.Random(seed)
    mb = kit.MB()
    hw, hd = w / 2, d / 2
    outline = [(-hw + cut, -hd), (hw - cut * 0.4, -hd), (hw, -hd + cut * 0.5), (hw, hd - cut), (hw - cut * 0.7, hd),
               (-hw + cut * 0.5, hd), (-hw, hd - cut * 0.6), (-hw, -hd + cut)]
    outline = [(x + rng.uniform(-0.15, 0.15), y + rng.uniform(-0.15, 0.15)) for x, y in outline]
    cen = mb.bm.verts.new((0, 0, 0))
    top_ring = [mb.bm.verts.new((x, y, rng.uniform(-bump, bump))) for x, y in outline]
    n = len(outline)
    for i in range(n):
        mb.face([cen, top_ring[i], top_ring[(i + 1) % n]], top)
    z = 0.0
    prev = top_ring
    for k, (m, th) in enumerate(strata):
        z -= th * depth / sum(t for _, t in strata)
        taper = 0.9 ** (k + 1)
        ring = [mb.bm.verts.new((x * (1.0 - 0.025 * (k + 1)) + rng.uniform(-0.05, 0.05), y * (1.0 - 0.025 * (k + 1)) + rng.uniform(-0.05, 0.05),
                                 z + rng.uniform(-0.04, 0.04))) for x, y in outline]
        for i in range(n):
            j = (i + 1) % n
            mb.face([prev[i], prev[j], ring[j], ring[i]], m)
        prev = ring
    bottom = mb.bm.verts.new((0, 0, z))
    for i in range(n):
        mb.face([prev[(i + 1) % n], prev[i], bottom], strata[-1][0])
    ob = mb.obj(name, coll)
    return ob


def make_camera(sc, name, keys, rng):
    """keys: (beat, fraction, position, look-at, lens)."""
    cd = bpy.data.cameras.new(name)
    cd.clip_start = 0.1
    cd.clip_end = 2000.0
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    target = bpy.data.objects.new(name + "Target", None)
    sc.collection.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for beat, u, pos, look, lens in keys:
        f0, f1 = rng[beat]
        f = round(f0 + u * (f1 - f0))
        cam.location = pos
        target.location = look
        cd.lens = lens
        cam.keyframe_insert("location", frame=f)
        target.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
    return cam


def timed_clips(F, beats):
    lines = F["beat_lines"]()
    out, f0 = [], 1
    for clip, beat in beats:
        wav = os.path.join(F["AUDIO"], f"{beat}.wav")
        if os.path.exists(wav):
            secs = F["wav_seconds"](wav)
        else:
            secs = F["estimate_seconds"](lines[beat])
            wav = os.path.join(F["AUDIO"], "placeholder", f"{beat}.wav")
        n = max(F["MIN_CLIP"], math.ceil((F["NARRATION_LEAD"] + secs + F["NARRATION_TAIL"]) * kit.FPS))
        out.append((clip, beat, f0, f0 + n - 1, wav, secs))
        f0 += n
    return out


def save(here, blend, timing, clips, label):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, blend))
    os.makedirs(os.path.join(here, "renders"), exist_ok=True)
    with open(os.path.join(here, "renders", timing), "w") as f:
        json.dump({"fps": kit.FPS, "lead": 0.8,
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2), placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print(label, "built:", clips[-1][3], "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / kit.FPS:.1f} s, narration {s:.1f} s)")


def flicker(obj_data_or_ob, attr, base, amp, f0, f1, rng, step=(3, 6)):
    f = f0
    while f <= f1:
        setattr(obj_data_or_ob, attr, base * (1.0 + rng.uniform(-amp, amp)))
        obj_data_or_ob.keyframe_insert(attr, frame=f)
        f += rng.randint(*step)
