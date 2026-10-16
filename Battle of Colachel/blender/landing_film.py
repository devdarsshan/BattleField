"""The Dutch come to Colachel (S30, S31, S32, S34, S38; clips 37, 38, 39, 41, 47) in Landing.blend.

One timeline for the five beach beats, with a clean cut between beats (each beat has its own
camera, switched by timeline markers). The set is the S01-S06 beach (colachel_world) before the
stockade; landing_world adds each beat's set and shows it only in that beat's frames.

S30 (K37) "...Dutch warships appear off the coast near Colachel. They fire on the shore." ->
     low over the water behind three warships sailing along the coast; on "They fire" the
     broadsides ripple down their sides, smoke rolls toward the beach, shot splashes in the
     shallows and throws up sand below the village; villagers run inland. The camera sinks to
     sea level as the ships hold their line ("blockade").
S31 (K38) "...seven large ships and a crowd of smaller boats come in close." -> high over the
     beach: seven ships at anchor, a stream of longboats rowing in; "Soldiers wade ashore" ->
     the men climb out of the grounded boats, wade up the sand and fall in at the back of the
     blocks; stores and guns piled on the beach.
S32 (K39) "Meet their commander, Eustachius De Lannoy." -> push in on him on the beach, posts
     and crates carried up behind him; "His speciality is building forts." -> he points out
     the line of the wall.
S34 (K41) "...the Dutch build a stockade, a wall of thick wooden posts driven into the sand." ->
     high over the site, posts going in one by one; "Then they march inland." -> the camera
     glides inland after the column; "Village after village falls, all the way to Kottar." ->
     fire and smoke rise from one village after another up the track.
S38 (S05 storm) "Then the weather changes. In June, the south-west monsoon arrives." -> behind
     the half-built stockade; clouds roll in, the light goes grey, rain; "Heavy rain, strong
     winds, and a sea that throws waves onto the beach" -> the camera rises over the wall as surf
     runs up the sand; "For months, big ships cannot safely come near this coast." -> it turns to
     sea: one ship pitching far out.

Headless: blender -b -P landing_film.py   (writes Landing.blend and renders/timing_landing.json)
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
for m in (kit, world, pepper_world, kochi_world, port_world, lw):
    importlib.reload(m)

sys.argv = sys.argv[:1]
film_src = open(os.path.join(HERE, "film.py"), encoding="utf8").read().split("\nbuild()")[0]
F = {}
exec(compile(film_src, "film.py", "exec"), F)

FPS = kit.FPS
DESIGN_CLIPS = [
    ("37", "S30", 1, 456),
    ("38", "S31", 457, 799),
    ("39", "S32", 800, 1192),
    ("41", "S34", 1193, 1556),
    ("47", "S38", 1557, 1997),
]

# Story events in design frames (clip time = 0.8 s lead + the word's share of the estimated line).
EVENTS = dict(
    volleys=[[205, 298], [214, 309], [223, 320]],   # S30 8.5 s "They fire on the shore", again at "blockade"
    wade=(640, 790),                                # S31 "Soldiers wade ashore on the sand" (from 10.1 s)
    point=1100,                                     # S32 12.4 s "His speciality is building forts."
    build=(1200, 1430),                             # S34 posts go in through "...driven into the sand"
    falls=[1440, 1474, 1508],                       # S34 "Village after village falls, all the way to Kottar"
    storm=[(1590, 0.0), (1695, 1.0)],               # S38 "the south-west monsoon arrives"
    rain=[(1612, 0.0), (1660, 1.0)],
)

SW = world.stockade_world
DLX, DLY = lw.DL_POS
NX, NY = 0.287, 0.958                               # inland, across the coast
TX, TY = 0.958, -0.287                              # along the coast (ESE)

# Cameras, one per beat: (design frame, position, look-at, lens mm). Z is metres above the ground
# (or above the sea), as in film.py.
CAMS = {
    "S30": [(1,   (162.0, -72.0, 26.0), (40.0, -70.0, 4.0), 30),
            (220, (153.0, -67.0, 18.0), (34.0, -66.0, 5.0), 30),
            (456, (140.0, -60.0, 7.0), (24.0, -60.0, 8.0), 30)],
    "S31": [(457, (180.0, -92.0, 52.0), (58.0, -52.0, 0.0), 30),
            (640, (170.0, -83.0, 45.0), (54.0, -45.0, 0.0), 30),
            (799, (160.0, -74.0, 38.0), (50.0, -38.0, 0.0), 30)],
    "S32": [(800, (DLX + NX * 8.0 + TX * 1.6, DLY + NY * 8.0 + TY * 1.6, 2.2), (DLX, DLY, 1.1), 35),
            (1100, (DLX + NX * 4.3 + TX * 0.8, DLY + NY * 4.3 + TY * 0.8, 1.55), (DLX - TX * 0.4, DLY - TY * 0.4, 1.05), 35),
            (1192, (DLX + NX * 3.8 + TX * 0.6, DLY + NY * 3.8 + TY * 0.6, 1.4), (DLX - TX * 0.6, DLY - TY * 0.6, 0.9), 35)],
    "S34": [(1193, (102.0, -42.0, 48.0), (58.0, -1.0, 0.0), 30),
            (1400, (86.0, -26.0, 30.0), (57.0, 0.0, 0.0), 30),
            (1480, (92.0, -22.0, 50.0), (62.0, 50.0, 2.0), 30),
            (1556, (82.0, -14.0, 64.0), (60.0, 118.0, 0.0), 30)],
    "S38": [(1557, (*SW(9.0, 32.0), 5.0), (*SW(0.0, -4.0), 1.5), 30),
            (1700, (*SW(4.0, 16.0), 6.5), (*SW(-1.0, -12.0), 1.0), 30),
            (1840, (*SW(1.0, 0.0), 10.0), (*SW(-6.0, -40.0), 0.0), 30),
            (1997, (*SW(-2.0, -8.0), 11.0), (30.0, -245.0, 6.0), 30)],
}
KEYFRAMES = {"K37": 260, "K38": 700, "K39": 1150, "K41": 1380}


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


def make_camera(sc, name, keys, rt):
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
    for f_d, pos, look, lens in keys:
        f = rt(f_d)
        cam.location = F["above_ground"](pos)
        target.location = F["above_ground"](look)
        cd.lens = lens
        cam.keyframe_insert("location", frame=f)
        target.keyframe_insert("location", frame=f)
        cd.keyframe_insert("lens", frame=f)
    return cam


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    rng = {c[1]: (c[2], c[3]) for c in clips}

    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end

    ev = dict(
        end=end, r30=rng["S30"], r31=rng["S31"], r32=rng["S32"], r34=rng["S34"], r38=rng["S38"],
        volleys=[[rt(f) for f in v] for v in EVENTS["volleys"]],
        wade=tuple(rt(f) for f in EVENTS["wade"]),
        point=rt(EVENTS["point"]),
        build=tuple(rt(f) for f in EVENTS["build"]),
        falls=[rt(f) for f in EVENTS["falls"]],
        # build, hold, and (past the end) clear: colachel_world's storm/cloud timeline format
        storm=[(rt(f), v) for f, v in EVENTS["storm"]] + [(end + 200, 1.0), (end + 300, 0.0)],
    )
    rig, sun, dl = lw.build_world(ev)
    lw.sea_light(sun, ev["r31"][1])                  # S30-S31: light from behind the camera, clear water
    # keep every camera out of the palms and trees it flies past
    path = []
    for keys in CAMS.values():
        for (fa, pa, _, _), (fb, pb, _, _) in zip(keys, keys[1:]):
            for k in range(12):
                u = k / 12
                path.append(F["above_ground"](tuple(a + (b - a) * u for a, b in zip(pa, pb))))
        path.append(F["above_ground"](keys[-1][1]))
    lw.clear_around(path)

    cams = {beat: make_camera(sc, f"Cam{beat}", keys, rt) for beat, keys in CAMS.items()}
    for clip, beat, f0, f1, _, _ in clips:
        mk = sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
        mk.camera = cams[beat]
    sc.camera = cams["S30"]
    world.build_rain(kit.new_collection("Rain"), cams["S38"],
                     [(rt(f), v) for f, v in EVENTS["rain"]] + [(end, 1.0)], end)

    # the storm light is lifted a little, as in the S05 monsoon
    vs = sc.view_settings
    base = vs.exposure
    for f, w in ev["storm"][:2]:
        vs.exposure = base + 0.4 * w
        vs.keyframe_insert("exposure", frame=f)
    for name, f in KEYFRAMES.items():
        sc.timeline_markers.new(name, frame=rt(f))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Landing.blend"))
    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    with open(os.path.join(HERE, "renders", "timing_landing.json"), "w") as f:
        json.dump({"fps": FPS, "lead": F["NARRATION_LEAD"],
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("Landing film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s)")


build()
