"""Surrender and march (S49-S54; clips 59-66) in Surrender.blend.

S49 (K59) "...a burning hot shot hit the gunpowder barrel, by accident."  follow the glowing ball in.
S50 (K60) "The barrel explodes. Fire spreads through the camp. The rice stores burn..."  pull back.
S51 (K62) "...Now a lucky shot breaks the Dutch."  smoke over the burnt stockade, slow rise.
S52 (K64) "...the garrison surrendered on the seventh of August..."  push in on the white flag.
S53 (K65) "About twenty-four Dutch officers are taken prisoner..."  slow orbit of the sword handover.
S54 (K66) "The prisoners are marched inland to Udayagiri..."  track the column toward the hill fort.
S49+S50 share one camera (no cut). Camera keys and events are fractions of a beat, so a later voice re-times everything.

Headless: blender -b -P surrender_film.py   (writes Surrender.blend and renders/timing_surrender.json)
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
import surrender_world as su
for m in (kit, world, pepper_world, kochi_world, port_world, lw, sw, su):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
BEATS = [("59", "S49"), ("60-61", "S50"), ("62-63", "S51"), ("64", "S52"), ("65", "S53"), ("66", "S54")]
SWP = world.stockade_world
C0 = world.STOCKADE["center"]
NX, NY, TX, TY = sw.NX, sw.NY, sw.TX, sw.TY
RAIN = {"S49": 0.9, "S50": 1.0, "S51": 0.7, "S52": 0.5, "S53": 0.4, "S54": 0.15}


def B(x, d, z):
    px, py = sw.beach(x, d)
    return (px, py, z)


def W(u, v, z):
    px, py = SWP(u, v)
    return (px, py, z)


def orbit(center, theta_deg, r, z):
    a = math.radians(theta_deg)
    return (center[0] + r * math.cos(a), center[1] + r * math.sin(a), z)


def ball_cam(u, back=24.0, up=3.0, side=5.0):
    """Camera trailing the ball, off to one side of its trail of smoke."""
    p, d = su.ball_pos(u), su.ball_dir(u)
    hz = math.hypot(d.x, d.y) or 1.0
    q = p - d * back
    q.x += -d.y / hz * side
    q.y += d.x / hz * side
    return (q.x, q.y), (p.x, p.y, p.z), q.z - world.height(q.x, q.y) + up


def blast_keys():
    """One camera over S49 and S50: trails the ball, then pulls back from the explosion."""
    keys = []
    for u_beat, u_ball in ((0.0, 0.0), (0.25, 0.28), (0.5, 0.55), (0.75, 0.82), (1.0, 1.0)):
        (qx, qy), look, z = ball_cam(u_ball)
        keys.append(("S49", u_beat, (qx, qy, max(z, 2.5)), (look[0], look[1], max(look[2] - world.height(look[0], look[1]), 0.0)), 30))
    (qx, qy), _, z1 = ball_cam(1.0)
    q1 = (qx, qy, max(z1, 2.5))
    px, py = su.POW
    hx, hy = su.LAUNCH[0] - px, su.LAUNCH[1] - py
    hl = math.hypot(hx, hy)
    hx, hy = hx / hl, hy / hl
    for u_beat, k, up in ((0.0, 0.0, 0.0), (0.35, 10.0, 6.0), (0.7, 22.0, 14.0), (1.0, 34.0, 22.0)):
        keys.append(("S50", u_beat, (q1[0] + hx * k, q1[1] + hy * k, q1[2] + up), (px, py, 2.5), 30))
    return keys


CAMS = {
    "S49": blast_keys,
    "S51": [("S51", 0.0, B(30.0, -34.0, 22.0), W(0.0, 0.0, 3.0), 30),
            ("S51", 1.0, B(36.0, -46.0, 44.0), W(0.0, 0.0, 3.0), 30)],
    "S52": [("S52", 0.0, W(-3.0, 14.0, 16.0), W(-6.0, -9.0, 6.0), 26),
            ("S52", 1.0, W(-4.0, 4.0, 10.5), W(-6.0, -9.0, 6.8), 30)],
    "S53": [("S53", 0.0, orbit(su.HC, -28, 14.0, 6.0), (su.HC[0], su.HC[1], 1.5), 30),
            ("S53", 1.0, orbit(su.HC, 38, 14.0, 6.5), (su.HC[0], su.HC[1], 1.5), 30)],
    "S54": [("S54", 0.0, (70.0, -26.0, 26.0), (62.0, 36.0, 0.0), 32),
            ("S54", 0.5, (78.0, -16.0, 40.0), (62.0, 60.0, 2.0), 32),
            ("S54", 1.0, (80.0, -12.0, 54.0), (58.0, 96.0, 8.0), 32)],
}
MARK_CAM = {"S49": "S49", "S50": "S49", "S51": "S51", "S52": "S52", "S53": "S53", "S54": "S54"}
KEYFRAMES = {"K59": ("S49", 0.6), "K60": ("S50", 0.25), "K62": ("S51", 0.5), "K64": ("S52", 0.8), "K65": ("S53", 0.5),
             "K66": ("S54", 0.5)}


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
    text = F["beat_lines"]()[beat]
    c = next(c for c in clips if c[1] == beat)
    i = text.find(phrase)
    if i < 0:
        raise ValueError(f"{phrase!r} not in {beat}")
    return int(c[2] + (F["NARRATION_LEAD"] + c[5] * i / len(text) + extra) * FPS)


def make_camera(sc, name, keys, rng, anchor_keys):
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
    for beat, u, pos, look, lens in keys:
        f0, f1 = rng[beat]
        f = round(f0 + u * (f1 - f0))
        cam.location = F["above_ground"](pos)
        target.location = F["above_ground"](look)
        cd.lens = lens
        cam.keyframe_insert("location", frame=f)
        target.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
        anchor_keys.append((f, cam.location.copy()))
    return cam


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rng = {c[1]: (c[2], c[3]) for c in clips}
    ev = dict(end=end)
    for beat, (a, b) in rng.items():
        ev[f"r{int(beat[1:])}"] = (a, b)
    r49, r50, r52 = rng["S49"], rng["S50"], rng["S52"]
    ev["launch"] = r49[0] + 10
    ev["hit"] = r49[1] - 2
    ev["boom"] = r50[0] + 4
    ev["spread"] = word_frame(clips, "S50", "Fire spreads", 0.1)
    ev["rice"] = word_frame(clips, "S50", "The rice stores burn", 0.1)
    ev["hoist"] = word_frame(clips, "S52", "the garrison surrendered", 0.0)
    r54 = rng["S54"]
    clouds = [(-300, 0.95), (-200, 0.95), (end + 200, 0.95), (end + 300, 0.0)]
    r51, r53 = rng["S51"], rng["S53"]
    allw = [(-300, 0.95), (-200, 0.95), (r50[1], 0.95), (r51[1], 0.8), (r52[1], 0.65), (r53[1], 0.4), (r54[1], 0.08),
            (end + 200, 0.3), (end + 300, 0.0)]
    ev["storm"], ev["storm_all"] = clouds, allw

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    rig, sun = su.build_world(ev)

    anchor_keys = []
    cams = {}
    for name, keys in CAMS.items():
        cams[name] = make_camera(sc, f"Cam{name}", keys() if callable(keys) else keys, rng, anchor_keys)
    for clip, beat, f0, f1, _, _ in clips:
        mk = sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
        mk.camera = cams[MARK_CAM[beat]]
    sc.camera = cams["S49"]
    path = []
    for name, keys in CAMS.items():
        ks = keys() if callable(keys) else keys
        kk = [(round(rng[b][0] + u * (rng[b][1] - rng[b][0])), F["above_ground"](p)) for b, u, p, _, _ in ks]
        for (fa, pa), (fb, pb) in zip(kk, kk[1:]):
            for k in range(14):
                t = k / 14
                path.append(tuple(a + (b - a) * t for a, b in zip(pa, pb)))
        path.append(kk[-1][1])
    lw.clear_around(path)

    anchor = bpy.data.objects.new("RainAnchor", None)
    sc.collection.objects.link(anchor)
    for f, loc in sorted(anchor_keys, key=lambda t: t[0]):
        anchor.location = loc
        anchor.keyframe_insert("location", frame=f)
    rain_pts = []
    for clip, beat, f0, f1, _, _ in clips:
        rain_pts += [(f0, RAIN[beat]), (f1, RAIN[beat])]
    world.build_rain(kit.new_collection("Rain"), anchor, rain_pts, end)

    vs = sc.view_settings
    base = vs.exposure
    for f, w in allw[:-2]:
        vs.exposure = base + 0.1 * w
        vs.keyframe_insert("exposure", frame=f)
    for name, (beat, u) in KEYFRAMES.items():
        f0, f1 = rng[beat]
        sc.timeline_markers.new(name, frame=round(f0 + u * (f1 - f0)))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Surrender.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_surrender.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Surrender film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
