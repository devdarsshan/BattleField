"""Render from the saved Colachel.blend in a background Blender process.

  blender -b Colachel.blend -P render_cli.py -- stills OUT_PREFIX 1 120 240 [--res 1280x720]
  blender -b Colachel.blend -P render_cli.py -- video  OUT.mp4 [--res 1280x720] [--range 1 240]
"""
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
mode, out = args[0], args[1]
rest = args[2:]
res = (1280, 720)
frange = None
frames = []
i = 0
while i < len(rest):
    if rest[i] == "--res":
        res = tuple(int(v) for v in rest[i + 1].split("x"))
        i += 2
    elif rest[i] == "--range":
        frange = (int(rest[i + 1]), int(rest[i + 2]))
        i += 3
    else:
        frames.append(int(rest[i]))
        i += 1

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = res
sc.render.resolution_percentage = 100

if mode == "stills":
    sc.render.image_settings.media_type = "IMAGE"
    sc.render.image_settings.file_format = "PNG"
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = f"{out}_f{f:03d}.png"
        bpy.ops.render.render(write_still=True)
elif mode == "frames":
    # PNG sequence into folder `out`. Finished frames are skipped, so an interrupted
    # render resumes where it stopped (and several nights can share one job).
    if frange:
        sc.frame_start, sc.frame_end = frange
    s = sc.render.image_settings
    s.media_type = "IMAGE"
    s.file_format = "PNG"
    s.compression = 15
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    sc.render.filepath = out.rstrip("\\/") + "\\f_"
    bpy.ops.render.render(animation=True)
elif mode == "video":
    if frange:
        sc.frame_start, sc.frame_end = frange
    s = sc.render.image_settings
    s.media_type = "VIDEO"
    s.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = out
    bpy.ops.render.render(animation=True)
