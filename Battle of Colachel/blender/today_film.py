"""Colachel today (S65-S69; clips 78-82) in Today.blend.

One camera runs S65-S67 (glide in to the victory pillar, slow orbit, rise out over the sea); S68 and S69 share a
second camera for the sunset over the empty beach, ending in a fade to dark under the end screen.
Camera keys are fractions of each beat, so the real voice re-times everything.

Headless: blender -b -P today_film.py   (writes Today.blend and renders/timing_today.json)
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
import landing_world as lw
import siege_world as sw
import today_world as tw
for m in (kit, world, pepper_world, kochi_world, port_world, lw, sw, tw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
BEATS = [("78", "S65"), ("79", "S66"), ("80-81", "S67"), ("82", "S68"), ("82b", "S69")]
NX, NY, TX, TY = sw.NX, sw.NY, sw.TX, sw.TY
PX, PY = tw.PILLAR
SEA = math.atan2(-NY, -NX)                 # direction from the land out to sea


def at(theta, r, z):
    return (PX + r * math.cos(theta), PY + r * math.sin(theta), z)


def orbit(beat, a0, a1, r0, r1, z0, z1, look, n=6, lens=30, u0=0.0, u1=1.0):
    keys = []
    for i in range(n + 1):
        t = i / n
        a, r, z = a0 + (a1 - a0) * t, r0 + (r1 - r0) * t, z0 + (z1 - z0) * t
        keys.append((beat, u0 + (u1 - u0) * t, at(a, r, z), look, lens))
    return keys


PIL_TOP = (PX, PY, 5.0)
S65_A0, S65_A1 = SEA + 1.15, SEA + 0.55
S66_A1 = SEA - 1.65
SUN_POS = (PX - NX * 0.0, PY, 0.0)


def sunset_cam(dz=0.0):
    sx, sy = world.stockade_world(0.0, 11.0)
    return sx, sy


def pp(a, b, z):
    """A point a metres along the coast and b metres inland of the pillar, z metres up."""
    return (PX + TX * a + NX * b, PY + TY * a + NY * b, z)


S67_END = pp(-6, -16, 32.0)
S67_LOOK = pp(8, 75, 5.0)
CAMS = {
    # one camera for the whole of Colachel today: S65-S67 glide in, circle the pillar and rise, then turn to look
    # INLAND over the monument (the village, road and palm groves are all built there); S68-S69 drift on over them
    "Today": (orbit("S65", S65_A0, S65_A1, 52, 33, 21, 14, PIL_TOP, n=4, lens=30)
              + orbit("S66", S65_A1, S66_A1, 33, 27, 14, 12, PIL_TOP, n=8, lens=30)
              + [("S67", 0.0, at(S66_A1, 27, 12.0), PIL_TOP, 30),
                 ("S67", 0.30, at(SEA - 1.1, 40, 40.0), (PX, PY, 3.0), 30),
                 ("S67", 0.62, at(SEA - 0.45, 42, 38.0), (PX, PY, 6.0), 30),
                 ("S67", 1.0, S67_END, S67_LOOK, 30),
                 ("S68", 0.5, pp(4, 8, 17.0), pp(10, 85, 6.0), 30),
                 ("S68", 1.0, pp(14, 40, 12.0), pp(12, 120, 9.0), 30),
                 ("S69", 0.5, pp(10, 26, 20.0), pp(0, 0, 6.0), 30),
                 ("S69", 1.0, pp(-4, 30, 26.0), pp(-2, -30, 3.0), 30)]),
}
MARK_CAM = {b: "Today" for b in ("S65", "S66", "S67", "S68", "S69")}
KEYFRAMES = {"K78": ("S65", 0.7), "K79": ("S66", 0.5), "K80": ("S67", 0.55), "K82": ("S68", 0.5)}


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


def make_camera(sc, name, keys, rng):
    cd = bpy.data.cameras.new(name)
    cd.clip_start = 0.3
    cd.clip_end = 120000.0
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
        cam.location = F["above_ground"](pos)
        target.location = F["above_ground"](look)
        cd.lens = lens
        cam.keyframe_insert("location", frame=f)
        target.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
    for ob in (cam, target):
        for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
    return cam


def world_fcurves(nt):
    ad = nt.animation_data
    act = ad.action
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                out += list(strip.channelbag(ad.action_slot).fcurves)
        return out


def key_sunset(sun, disc, rng, end):
    """Daylight until S68, then the sun goes down over the sea (S68) and the light fades (S69)."""
    s68, s69 = rng["S68"], rng["S69"]
    day_dir = (0.7, -0.42, -0.26)
    ld = sun.data
    from mathutils import Vector

    def sun_state(f, direction, energy, color):
        sun.rotation_euler = Vector(direction).normalized().to_track_quat("-Z", "Y").to_euler()
        sun.keyframe_insert("rotation_euler", frame=f)
        ld.energy = energy
        ld.keyframe_insert("energy", frame=f)
        ld.color = color
        ld.keyframe_insert("color", frame=f)

    s67 = rng["S67"]
    warm0 = round(s67[0] + 0.70 * (s67[1] - s67[0]))
    sun_state(1, day_dir, 11.0, (1.0, 0.78, 0.48))
    sun_state(warm0, day_dir, 11.0, (1.0, 0.78, 0.48))
    # golden hour: the light comes low from the sea side and travels inland over the monument and the village
    sun_state(s68[0], (NX * 0.95, NY * 0.95, -0.42), 13.0, (1.0, 0.66, 0.34))
    sun_state(s69[0], (NX * 0.95, NY * 0.95, -0.34), 11.0, (1.0, 0.58, 0.28))
    sun_state(end, (NX * 0.95, NY * 0.95, -0.28), 9.0, (1.0, 0.52, 0.26))
    # a faint warm tint on the sea and the haze, never the violet of a full sunset
    sm = bpy.data.materials["Sea"].node_tree.nodes["StormMix"]
    world._sock(sm.inputs, "B_Color").default_value = (*kit.srgb_to_linear((0.42, 0.40, 0.50)), 1)
    for f, v in ((1, 0.0), (warm0, 0.0), (s68[0], 0.18), (end, 0.28)):
        sm.inputs["Factor"].default_value = v
        sm.inputs["Factor"].keyframe_insert("default_value", frame=f)
    haze = bpy.data.objects["Haze"]
    haze.visible_shadow = False
    vol = next(n for n in haze.data.materials[0].node_tree.nodes if n.bl_idname == "ShaderNodeVolumePrincipled")
    for f, d, col in ((1, 0.00006, (0.88, 0.92, 0.96)), (warm0, 0.00006, (0.88, 0.92, 0.96)),
                      (s68[0], 0.00007, (0.96, 0.80, 0.62)), (end, 0.00008, (0.94, 0.70, 0.52))):
        vol.inputs["Density"].default_value = d
        vol.inputs["Density"].keyframe_insert("default_value", frame=f)
        vol.inputs["Color"].default_value = (*kit.srgb_to_linear(col), 1)
        vol.inputs["Color"].keyframe_insert("default_value", frame=f)
    disc.scale = (0.0, 0.0, 0.0)                 # no sun disc: the film stays over the built ground


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rng = {c[1]: (c[2], c[3]) for c in clips}
    ev = dict(end=end)
    for beat, (a, b) in rng.items():
        ev[f"r{int(beat[1:])}"] = (a, b)

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    rig, sun, disc = tw.build_world(ev)
    world.apply_weather(sun, bpy.data.objects["Haze"], {"storm": [(-300, 0.0), (end + 300, 0.0)]})
    key_sunset(sun, disc, rng, end)
    cams = {name: make_camera(sc, f"Cam{name}", keys, rng) for name, keys in CAMS.items()}
    for clip, beat, f0, f1, _, _ in clips:
        mk = sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
        mk.camera = cams[MARK_CAM[beat]]
    sc.camera = cams["Today"]
    path = []
    for keys in CAMS.values():
        kk = [(round(rng[b][0] + u * (rng[b][1] - rng[b][0])), F["above_ground"](p)) for b, u, p, _, _ in keys]
        for (fa, pa), (fb, pb) in zip(kk, kk[1:]):
            for k in range(14):
                t = k / 14
                path.append(tuple(a + (b - a) * t for a, b in zip(pa, pb)))
        path.append(kk[-1][1])
    low = [p for p in path if p[2] < 70]
    lw.clear_around(low, r=13.0, clearance=24.0)
    for ob in [o for o in bpy.data.objects if o.name.startswith(("MonPalm", "SunsetPalm")) is False and o.name.startswith("MonBush")]:
        pass
    for ob in [o for o in bpy.data.objects if o.name.startswith("MonPalm")]:
        if any(math.hypot(ob.location.x - a, ob.location.y - b) < 14.0 and c < 30 for a, b, c in low):
            bpy.data.objects.remove(ob, do_unlink=True)

    vs = sc.view_settings
    base = vs.exposure
    s69 = rng["S69"]
    for f, e in ((1, 0.0), (s69[0] + 120, 0.0), (end - 24, -1.6), (end, -5.0)):
        vs.exposure = base + e
        vs.keyframe_insert("exposure", frame=f)
    for name, (beat, u) in KEYFRAMES.items():
        f0, f1 = rng[beat]
        sc.timeline_markers.new(name, frame=round(f0 + u * (f1 - f0)))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Today.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_today.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Today film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
