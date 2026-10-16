"""The Colachel film as one continuous Blender timeline (no cuts).

Each clip lasts as long as its narration (audio/Sxx.wav) plus a little air, with a
10 s minimum. A beat with no recording yet gets an estimated length from its text in
audio/lines.txt (and a placeholder voice from make_placeholders.py), so picture work
never waits on the voice quota. Camera keys and weather are written against
DESIGN_CLIPS and stretched to the real clip lengths, so re-recording the narration
never needs new keys.

Run inside Blender (MCP):  exec(open(r"<this file>").read())
or headless:               blender -b -P film.py
It saves Colachel.blend and renders/timing.json (used by make_video.py).
"""
import importlib
import json
import math
import os
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.path.abspath(os.getcwd())
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy
import colachel_kit as kit
import colachel_world as world
import kerala_geo as geo
importlib.reload(kit)
importlib.reload(geo)
importlib.reload(world)

AUDIO = os.path.join(HERE, "..", "audio")
FPS = kit.FPS
# (clip(s) in the shot list, beat, design first frame, design last frame). The design
# ranges are the frames the camera keys and weather below were written for.
DESIGN_CLIPS = [
    ("01", "S01", 1, 240),
    ("02", "S02", 241, 612),
    ("03", "S03", 613, 960),
    ("04", "S04", 961, 1296),
    ("05", "S05", 1297, 1690),
    ("06-07", "S06", 1691, 2170),
    ("08", "S07", 2171, 2410),
    ("09-10", "S08", 2411, 2860),
]
NARRATION_LEAD = 0.8   # seconds of picture before each beat's narration starts (S01 waits for the fade)
NARRATION_TAIL = 0.6   # seconds of picture after the narration ends
MIN_CLIP = 240         # 10 s minimum
CHARS_PER_SEC = 12.5   # measured on the Charon takes; used only until a beat is recorded


def wav_seconds(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def beat_lines():
    out = {}
    with open(os.path.join(AUDIO, "lines.txt"), encoding="utf8") as f:
        for line in f:
            if "|" in line:
                b, t = line.strip().split("|", 1)
                out[b] = t
    return out


def estimate_seconds(text):
    return len(text) / CHARS_PER_SEC + 0.3


def timed_clips():
    """Real clip ranges: [(clip, beat, f0, f1, wav, seconds)]. Recorded beats use their
    real length; the rest use an estimate and point at the placeholder voice."""
    lines = beat_lines()
    out, f0 = [], 1
    for clip, beat, _, _ in DESIGN_CLIPS:
        wav = os.path.join(AUDIO, f"{beat}.wav")
        if os.path.exists(wav):
            secs = wav_seconds(wav)
        else:
            secs = estimate_seconds(lines[beat])
            wav = os.path.join(AUDIO, "placeholder", f"{beat}.wav")
        n = max(MIN_CLIP, math.ceil((NARRATION_LEAD + secs + NARRATION_TAIL) * FPS))
        out.append((clip, beat, f0, f0 + n - 1, wav, secs))
        f0 += n
    return out


def retime(frame, clips):
    """Map a design frame onto the real timeline, clip by clip."""
    for (_, _, d0, d1), (_, _, n0, n1, _, _) in zip(DESIGN_CLIPS, clips):
        if d0 <= frame <= d1:
            return round(n0 + (frame - d0) / (d1 - d0) * (n1 - n0))
    raise ValueError(frame)


SW = world.stockade_world
BX, BY = world.BATTERY
MZ = geo.MAP_Z

# camera keys: (frame, camera position, look-at point). On the diorama, Z is metres above
# the ground (or sea level), so keys survive terrain changes. Z above 300 or below 0 is
# absolute (map heights, and looking down at the map sheet).
CAM_KEYS = [
    # 01  dawn sea -> glide in over the fishing village
    (1,    (36.0, -34.0, 11.0), (-14.0, 14.0, 0.0)),
    (240,  (-5.0, -11.0, 6.0),  (-1.0, 15.0, 0.5)),
    # 02  truck right along the beach to the stockade, rise over the wall onto the garrison
    (330,  (12.0, -12.0, 6.5),  (24.0, 12.0, 1.2)),
    (440,  (30.0, -12.0, 4.5),  (52.0, 6.0, 2.0)),
    (540,  (37.0, -8.0, 7.0),   (55.0, 0.0, 1.5)),
    (612,  (40.0, -4.0, 10.5),  (58.0, -1.0, 0.0)),
    # 03  over the soldiers, out the back of the stockade, inland to the king's canopy
    (700,  (50.0, -2.0, 14.0),  (62.0, 20.0, 0.0)),
    (800,  (57.0, 14.0, 15.0),  (62.0, 48.0, 0.0)),
    (900,  (60.0, 34.0, 8.0),   (62.0, 56.0, 1.0)),
    (960,  (61.5, 46.0, 4.2),   (62.0, 56.5, 1.6)),
    # 04  close on Marthanda Varma, swing round behind him and out to the Dutch ships
    (1080, (61.8, 49.5, 3.4),   (62.0, 56.8, 1.7)),
    (1170, (72.0, 52.0, 6.0),   (62.0, 56.5, 1.5)),
    (1240, (69.0, 64.0, 8.5),   (58.0, 20.0, 0.0)),
    (1296, (63.0, 66.0, 9.0),   (56.0, -85.0, 0.0)),
    # 05  the monsoon rolls in: out over the wall to the pitching ships, then down inside
    #     the stockade to the hungry soldiers and the last rice
    (1390, (62.0, 30.0, 24.0),  (52.0, -110.0, 0.0)),
    (1500, (55.0, -32.0, 16.0), (45.0, -125.0, 2.0)),
    (1600, (*SW(16.0, -4.0), 8.0),  (*SW(11.0, 3.3), 0.5)),
    (1690, (*SW(13.8, -0.6), 2.4),  (*SW(11.0, 3.4), 0.5)),
    # 06-07  look over the wall: the Travancore gun fires from the hillock behind the palms;
    #        crane up and back, high over the beach, dark sky left for the title card
    (1760, (*SW(11.6, 0.6), 3.0),   (BX, BY, 2.0)),
    (1850, (*SW(11.0, -1.2), 3.8),  (BX, BY, 2.0)),
    (1990, (40.0, -45.0, 60.0),     (75.0, 20.0, 0.0)),
    (2170, (10.0, -170.0, 200.0),   (55.0, 5.0, 0.0)),
    # 08  rise through the clouds: the beach is a diorama on a parchment map, north up
    (2290, (-150.0, -700.0, 2200.0), (-150.0, 300.0, MZ)),
    (2410, (-700.0, 900.0, 9000.0),  (-700.0, 2400.0, MZ)),
    # 09-10  glide north along the coast: thin strip, sea to the west, the Ghats to the east
    (2640, (-2400.0, 3400.0, 8800.0), (-2400.0, 4900.0, MZ)),
    (2860, (-4300.0, 6200.0, 8500.0), (-4300.0, 7600.0, MZ)),
]
LENS = 30

# weather and events, in design frames
WEATHER = {
    "storm": [(1320, 0.0), (1480, 1.0), (2215, 1.0), (2330, 0.0)],   # build, hold, clear
    "map":   [(2215, 0), (2330, 1)],                                 # haze gone at map height
    "rain":  [(1380, 0.0), (1420, 1.0), (2040, 1.0), (2090, 0.0)],
    "shot":  1785,                                                    # the Travancore gun fires
}


def above_ground(p):
    x, y, z = p
    if z > 300 or z < 0 or not (world.TX0 < x < world.TX1 and world.TY0 < y < world.TY1):
        return (x, y, z)
    return (x, y, max(0.0, world.height(x, y)) + z)


def build(samples=32):
    clips = timed_clips()
    end = clips[-1][3]
    rt = lambda f: retime(f, clips)
    weather = {
        "storm": [(rt(f), v) for f, v in WEATHER["storm"]],
        "map": [(rt(f), v) for f, v in WEATHER["map"]],
        "shot": rt(WEATHER["shot"]),
    }
    kit.reset_scene()
    sc = world.setup_render(samples=samples)
    sc.frame_start, sc.frame_end = 1, end
    rig = world.build_world(end, weather)

    cd = bpy.data.cameras.new("Camera")
    cd.lens = LENS
    cam = bpy.data.objects.new("Camera", cd)
    rig.objects.link(cam)
    sc.camera = cam
    target = bpy.data.objects.new("CamTarget", None)
    rig.objects.link(target)
    c = cam.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    for f, pos, look in CAM_KEYS:
        cam.location = above_ground(pos)
        target.location = above_ground(look)
        cam.keyframe_insert("location", frame=rt(f))
        target.keyframe_insert("location", frame=rt(f))
    # near/far clipping: tight on the beach, very deep once the map is in view
    m0, m1 = weather["map"][0][0], weather["map"][1][0]
    for f, near, far in ((m0, 0.2, 3000.0), (m1, 5.0, 100000.0)):
        cd.clip_start, cd.clip_end = near, far
        cd.keyframe_insert("clip_start", frame=f)
        cd.keyframe_insert("clip_end", frame=f)

    world.build_rain(kit.new_collection("Rain"), cam, [(rt(f), v) for f, v in WEATHER["rain"]], end)

    # fade up from black over the first 1.5 s; lift exposure a little in the storm
    vs = sc.view_settings
    base = vs.exposure
    vs.exposure = base - 10
    vs.keyframe_insert("exposure", frame=1)
    vs.exposure = base
    vs.keyframe_insert("exposure", frame=36)
    for f, w in weather["storm"]:
        vs.exposure = base + 0.4 * w
        vs.keyframe_insert("exposure", frame=f)

    for clip, beat, f0, f1, _, _ in clips:
        sc.timeline_markers.new(f"{clip} {beat}", frame=f0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Colachel.blend"))
    with open(os.path.join(HERE, "renders", "timing.json"), "w") as f:
        json.dump({"fps": FPS, "lead": NARRATION_LEAD,
                   "clips": [dict(clip=c, beat=b, first=f0, last=f1, wav=w, seconds=round(s, 2),
                                  placeholder="placeholder" in w)
                             for c, b, f0, f1, w, s in clips]}, f, indent=1)
    print("film built:", end, "frames,", len(bpy.data.objects), "objects")
    for c, b, f0, f1, w, s in clips:
        tag = " (estimated, placeholder voice)" if "placeholder" in w else ""
        print(f"  clip {c} {b}: frames {f0}-{f1} ({(f1 - f0 + 1) / FPS:.1f} s, narration {s:.1f} s{tag})")


build()
