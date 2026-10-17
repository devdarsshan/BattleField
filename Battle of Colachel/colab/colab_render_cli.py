"""Headless Blender render script optimized for Google Colab / Linux cloud GPUs.

Usage examples:
  blender -b sample_scene.blend -P colab_render_cli.py -- stills /path/to/out 1 5 10
  blender -b sample_scene.blend -P colab_render_cli.py -- frames /path/to/frames_dir --range 1 100 --res 1280x720
  blender -b sample_scene.blend -P colab_render_cli.py -- video  /path/to/clip.mp4 --range 1 100 --res 1280x720
"""
import os
import sys
import time
import bpy

# 1. Parse command line arguments passed after '--'
argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = []

mode = args[0] if len(args) > 0 else "frames"
out = args[1] if len(args) > 1 else "./renders"
rest = args[2:] if len(args) > 2 else []

res = (1280, 720)
frange = None
frames = []
samples = None
engine = None  # None = keep scene default

i = 0
while i < len(rest):
    if rest[i] == "--res":
        res = tuple(int(v) for v in rest[i + 1].split("x"))
        i += 2
    elif rest[i] == "--range":
        frange = (int(rest[i + 1]), int(rest[i + 2]))
        i += 3
    elif rest[i] == "--samples":
        samples = int(rest[i + 1])
        i += 2
    elif rest[i] == "--engine":
        engine = rest[i + 1].upper()
        i += 2
    else:
        frames.append(int(rest[i]))
        i += 1

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = res
sc.render.resolution_percentage = 100

# 2. Configure Render Engine & GPU Acceleration
if engine:
    if "CYCLE" in engine:
        sc.render.engine = "CYCLES"
    elif "EEVEE" in engine:
        sc.render.engine = "BLENDER_EEVEE"

current_engine = sc.render.engine
print(f"[Colab Render] Render Engine: {current_engine} | Resolution: {res[0]}x{res[1]}", flush=True)

if current_engine == "CYCLES":
    sc.cycles.device = "GPU"
    prefs = bpy.context.preferences
    cprefs = prefs.addons["cycles"].preferences
    cprefs.refresh_devices()
    activated = []
    # Try OPTIX first, then CUDA
    for compute_type in ["OPTIX", "CUDA"]:
        try:
            cprefs.compute_device_type = compute_type
            for device in cprefs.devices:
                if device.type == compute_type:
                    device.use = True
                    activated.append(f"{device.name} ({compute_type})")
                else:
                    device.use = False
            if activated:
                break
        except Exception as e:
            pass
    if activated:
        print(f"[Colab Render] Enabled Cycles GPU Devices: {', '.join(activated)}", flush=True)
    else:
        print("[Colab Render] Warning: No CUDA/OPTIX devices found for Cycles, using CPU.", flush=True)
    if samples:
        sc.cycles.samples = samples
elif "EEVEE" in current_engine:
    if samples:
        try:
            sc.eevee.taa_render_samples = samples
            print(f"[Colab Render] EEVEE Render Samples set to: {samples}", flush=True)
        except Exception:
            pass

# 3. Render Execution
if mode == "stills":
    sc.render.image_settings.media_type = "IMAGE"
    sc.render.image_settings.file_format = "PNG"
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = f"{out}_f{f:04d}.png"
        t0 = time.time()
        print(f"[Colab Render] Rendering frame {f}...", flush=True)
        bpy.ops.render.render(write_still=True)
        print(f"[Colab Render] Frame {f} saved to {sc.render.filepath} in {time.time()-t0:.2f}s", flush=True)

elif mode == "frames":
    start_f, end_f = frange if frange else (sc.frame_start, sc.frame_end)
    s = sc.render.image_settings
    s.media_type = "IMAGE"
    s.file_format = "PNG"
    s.compression = 15

    out_dir = out.rstrip("\\/")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[Colab Render] Rendering frames {start_f}..{end_f} -> {out_dir}", flush=True)

    total_frames = end_f - start_f + 1
    rendered_count = 0

    for f in range(start_f, end_f + 1):
        target_file = os.path.join(out_dir, f"f_{f:04d}.png")
        if os.path.exists(target_file) and os.path.getsize(target_file) > 2048:
            continue  # Resume support: skip already rendered valid frames

        t0 = time.time()
        sc.frame_set(f)
        sc.render.filepath = target_file
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        rendered_count += 1
        print(f"[Colab Render] Frame {f}/{end_f} rendered in {dt:.2f}s -> {target_file}", flush=True)

    print(f"[Colab Render] Completed! Rendered {rendered_count} new frames in {out_dir}", flush=True)

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
    t0 = time.time()
    print(f"[Colab Render] Rendering video frames {sc.frame_start}..{sc.frame_end} to {out}...", flush=True)
    bpy.ops.render.render(animation=True)
    print(f"[Colab Render] Video render complete in {time.time()-t0:.2f}s!", flush=True)
