"""The siege of Colachel (S40-S48; clips 49-58) in Siege.blend.

One timeline for nine beach beats. Beats S41 and S42 share one camera (the orbit goes on from the
stockade ring to the fishing village); every other beat has its own camera, switched by timeline
markers (a clean cut). Camera keys and events are written as fractions of each beat, so a later
re-recorded voice re-times everything.

S40 (K49) "...pushes the Dutch out of the villages. Back to the coast. Back behind the wooden wall."
     high over the track, gliding seaward; the column drives the retreating Dutch to the gate.
S41 (K50) "...surrounds the stockade, and waits."  slow orbit above the ring of tents and fires.
S42 (K51) "...the people of the beach are against them."  the orbit runs on to the fishing village.
S43 (K52) "...the fishermen refuse Dutch bribes..."  push in on the officer's bag of coins; they turn away.
S44 (K53) "...palm tree trunks on carts, shaped and painted like cannons..."  track the carts onto the dunes.
S45 (K54) "That story is still told today. No record proves it."  the row of fake guns from behind.
S46 (K55-K56) "Two small Dutch ships try to sail in... The guns open fire, and the ships turn back."
S47 (K57) "June becomes July. Inside the stockade, the men count their rice."  descend into the yard.
S48 (K58) "The fifth of August... A Travancore gun fires at the stockade."  pull out to the battery.

Headless: blender -b -P siege_film.py   (writes Siege.blend and renders/timing_siege.json)
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
for m in (kit, world, pepper_world, kochi_world, port_world, lw, sw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
BEATS = [("49", "S40"), ("50", "S41"), ("51", "S42"), ("52", "S43"), ("53", "S44"), ("54", "S45"),
         ("55-56", "S46"), ("57", "S47"), ("58", "S48")]
H = world.height
SY = world.shore_y
SWP = world.stockade_world
C0 = world.STOCKADE["center"]
NX, NY, TX, TY = sw.NX, sw.NY, sw.TX, sw.TY


def B(x, d, z):
    """A point d metres inland of the waterline at x, z metres above the ground."""
    px, py = sw.beach(x, d)
    return (px, py, z)


def W(u, v, z):
    px, py = SWP(u, v)
    return (px, py, z)


def orbit(theta_deg, r, z):
    a = math.radians(theta_deg)
    return (C0[0] + r * math.cos(a), C0[1] + r * math.sin(a), z)


GX, GY = sw.beach(9.5, 3.8)                      # the fishermen's group (S43)
CAM_S43 = lambda back, side, z: (GX - NX * back + TX * side, GY - NY * back + TY * side, z)

# camera keys per camera: (beat, fraction of the beat, position, look-at, lens mm)
CAMS = {
    "S40": [("S40", 0.0, (70.0, 108.0, 62.0), (62.0, 62.0, 0.0), 36),
            ("S40", 0.5, (76.0, 70.0, 50.0), (62.0, 34.0, 0.0), 36),
            ("S40", 1.0, (84.0, 30.0, 44.0), (58.0, 0.0, 0.0), 34)],
    "S41": [("S41", 0.0, orbit(-12, 62, 38), (C0[0], C0[1], 0.0), 28),
            ("S41", 0.5, orbit(-68, 62, 36), (C0[0], C0[1], 0.0), 28),
            ("S41", 1.0, orbit(-122, 60, 34), (C0[0], C0[1], 0.0), 28),
            ("S42", 0.5, B(26.0, -30.0, 22.0), B(36.0, 10.0, 1.5), 28),
            ("S42", 1.0, B(16.0, -15.0, 12.0), B(30.0, 12.0, 1.5), 30)],
    "S43": [("S43", 0.0, CAM_S43(13.0, 1.5, 2.8), (GX + TX * 2.2, GY + TY * 2.2, 1.3), 38),
            ("S43", 1.0, CAM_S43(9.0, 1.5, 2.1), (GX + TX * 2.2, GY + TY * 2.2, 1.35), 38)],
    "S44": [("S44", 0.0, B(6.0, -13.0, 9.0), B(-8.0, 6.0, 1.0), 30),
            ("S44", 1.0, B(-18.0, -13.0, 8.0), B(-24.0, 6.5, 1.0), 30)],
    "S45": [("S45", 0.0, B(-41.0, 17.0, 4.6), B(-16.0, -10.0, 0.8), 30),
            ("S45", 1.0, B(-34.0, 17.0, 4.4), B(-9.0, -10.0, 0.8), 30)],
    "S46": [("S46", 0.0, B(76.0, 18.0, 12.0), B(92.0, 3.0, 0.5), 32),
            ("S46", 0.3, B(77.0, 18.0, 12.0), B(90.0, -6.0, 0.5), 30),
            ("S46", 0.85, B(78.0, 18.0, 12.0), B(88.0, -62.0, 2.0), 30),
            ("S46", 1.0, B(79.0, 18.0, 12.0), B(88.0, -80.0, 2.0), 30)],
    "S47": [("S47", 0.0, W(-4.0, -22.0, 15.0), W(-2.0, -3.0, 1.0), 28),
            ("S47", 0.45, W(-5.5, -14.0, 7.8), W(-2.0, -3.0, 1.0), 28),
            ("S47", 1.0, W(-7.5, -8.8, 3.6), W(-1.5, -3.0, 1.0), 30)],
    "S48": [("S48", 0.0, W(5.0, 3.0, 4.2), (87.5, 26.8, 6.0), 30),
            ("S48", 0.5, (76.0, 4.0, 19.0), (88.0, 25.0, 3.0), 32),
            ("S48", 1.0, (79.0, 3.0, 24.0), (88.0, 25.0, 3.0), 32)],
}
MARK_CAM = {"S40": "S40", "S41": "S41", "S42": "S41", "S43": "S43", "S44": "S44", "S45": "S45", "S46": "S46",
            "S47": "S47", "S48": "S48"}
KEYFRAMES = {"K49": ("S40", 0.5), "K50": ("S41", 0.5), "K51": ("S42", 0.8), "K52": ("S43", 0.6), "K53": ("S44", 0.5),
             "K54": ("S45", 0.5), "K55": ("S46", 0.15), "K56": ("S46", 0.8), "K57": ("S47", 0.8), "K58": ("S48", 0.7)}
RAIN = {"S40": 0.3, "S41": 0.35, "S42": 0.4, "S43": 0.4, "S44": 0.4, "S45": 0.5, "S46": 0.5, "S47": 1.0, "S48": 0.7}


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
    lines = F["beat_lines"]()
    text = lines[beat]
    c = next(c for c in clips if c[1] == beat)
    i = text.find(phrase)
    if i < 0:
        raise ValueError(f"{phrase!r} not in {beat}")
    secs = c[5]
    return int(c[2] + (F["NARRATION_LEAD"] + secs * i / len(text) + extra) * FPS)


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
    ev["refuse"] = word_frame(clips, "S43", "refuse Dutch bribes", 0.2)
    ev["fire46"] = [word_frame(clips, "S46", "The Travancore guns open fire", 0.3)]
    ev["fire46"] += [ev["fire46"][0] + 52, ev["fire46"][0] + 104]
    ev["turn46"] = word_frame(clips, "S46", "turn back to sea", -0.6)
    ev["shot48"] = word_frame(clips, "S48", "A Travancore gun fires", 0.4)
    # monsoon all through: clouds hold, light lifts toward the heavy rain of S47
    clouds = [(-300, 0.9), (-200, 0.9), (end + 200, 0.9), (end + 300, 0.0)]
    r47, r48 = rng["S47"], rng["S48"]
    allw = [(-300, 0.9), (-200, 0.9), (r47[0] - 30, 0.9), (r47[0] + 40, 1.0), (r48[0] - 20, 1.0),
            (r48[0] + 50, 0.85), (end + 200, 0.85), (end + 300, 0.0)]
    ev["storm"], ev["storm_all"] = clouds, allw

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    rig, sun = sw.build_world(ev)

    anchor_keys = []
    cams = {name: make_camera(sc, f"Cam{name}", keys, rng, anchor_keys) for name, keys in CAMS.items()}
    for clip, beat, f0, f1, _, _ in clips:
        mk = sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
        mk.camera = cams[MARK_CAM[beat]]
    sc.camera = cams["S40"]
    # keep every camera out of the palms and trees it flies past
    path = []
    for keys in CAMS.values():
        kk = [(round(rng[b][0] + u * (rng[b][1] - rng[b][0])), F["above_ground"](p)) for b, u, p, _, _ in keys]
        for (fa, pa), (fb, pb) in zip(kk, kk[1:]):
            for k in range(14):
                t = k / 14
                path.append(tuple(a + (b - a) * t for a, b in zip(pa, pb)))
        path.append(kk[-1][1])
    lw.clear_around(path)

    # rain follows whichever camera is live (an anchor that carries every camera's keys, in order)
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

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Siege.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_siege.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Siege film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
