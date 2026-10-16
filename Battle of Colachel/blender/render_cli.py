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
pause_s = 0.25
max_temp = 76
cooldown_temp = 68
i = 0
while i < len(rest):
    if rest[i] == "--res":
        res = tuple(int(v) for v in rest[i + 1].split("x"))
        i += 2
    elif rest[i] == "--range":
        frange = (int(rest[i + 1]), int(rest[i + 2]))
        i += 3
    elif rest[i] == "--pause":
        pause_s = float(rest[i + 1])
        i += 2
    elif rest[i] == "--max-temp":
        max_temp = int(rest[i + 1])
        i += 2
    else:
        frames.append(int(rest[i]))
        i += 1

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = res
sc.render.resolution_percentage = 100

def get_gpu_temp():
    import subprocess
    try:
        out_t = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            timeout=2
        )
        return int(out_t.strip())
    except Exception:
        return None

if mode == "stills":
    sc.render.image_settings.media_type = "IMAGE"
    sc.render.image_settings.file_format = "PNG"
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = f"{out}_f{f:03d}.png"
        bpy.ops.render.render(write_still=True)
elif mode == "frames":
    # Safe frame-by-frame render with Thermal Guard to prevent GPU overload / overheat.
    # Skips valid existing frames (> 2KB) so interrupted runs resume seamlessly.
    import os, time
    if frange:
        start_f, end_f = frange
    else:
        start_f, end_f = sc.frame_start, sc.frame_end

    s = sc.render.image_settings
    s.media_type = "IMAGE"
    s.file_format = "PNG"
    s.compression = 15

    out_dir = out.rstrip("\\/")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[Thermal Guard] Target: frames {start_f} to {end_f} -> {out_dir}")
    print(f"[Thermal Guard] Max temp: {max_temp}C | Cooldown: {cooldown_temp}C | Frame pause: {pause_s}s")

    for f in range(start_f, end_f + 1):
        target_file = os.path.join(out_dir, f"f_{f:04d}.png")
        if os.path.exists(target_file) and os.path.getsize(target_file) > 2048:
            continue  # Already rendered and valid, skip!

        # Check GPU temperature periodically
        if f % 5 == 0 or f == start_f:
            gpu_t = get_gpu_temp()
            if gpu_t is not None:
                if gpu_t >= max_temp:
                    print(f"\n[Thermal Guard] GPU temp {gpu_t}C >= {max_temp}C! Pausing to cool down...", flush=True)
                    while gpu_t is not None and gpu_t > cooldown_temp:
                        time.sleep(3)
                        gpu_t = get_gpu_temp()
                        print(f"[Thermal Guard] Cooling... currently {gpu_t}C", flush=True)
                    print(f"[Thermal Guard] Cooled to {gpu_t}C. Resuming render.\n", flush=True)

        sc.frame_set(f)
        sc.render.filepath = target_file
        bpy.ops.render.render(write_still=True)

        if pause_s > 0:
            time.sleep(pause_s)
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
