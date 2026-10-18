"""Render a package of finalised clips on a local machine (made for the RTX 4050 laptop) and time it.

Reads manifest.json (clip, beat, blend, start, end, audio), renders each shot with Blender (EEVEE, headless, on the
NVIDIA GPU), encodes an MP4 with the narration (0.8 s in), and writes a timing report.

  python render_local.py --blender "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --quality 1080p
  python render_local.py --blender ... --bench 48          # timing test: first 48 frames of each different blend only
  python render_local.py --blender ... --only S41,S42      # just these beats
Needs: Blender 5.2, ffmpeg on PATH, Python 3.
On a laptop, set Blender to use the NVIDIA GPU first: Windows Settings > System > Display > Graphics > add blender.exe > High performance.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--blender", required=True)
ap.add_argument("--quality", choices=["720p", "1080p"], default="1080p")
ap.add_argument("--samples", type=int, default=32)
ap.add_argument("--only", default="")
ap.add_argument("--bench", type=int, default=0, help="benchmark: render only this many frames from the start of each distinct blend file")
ap.add_argument("--out", default=os.path.join(HERE, "renders"))
a = ap.parse_args()

res = "1920x1080" if a.quality == "1080p" else "1280x720"
manifest = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
shots = manifest["shots"]
if a.only:
    want = set(a.only.split(","))
    shots = [s for s in shots if s["beat"] in want]
if a.bench:
    seen, picked = set(), []
    for s in shots:
        if s["blend"] not in seen:
            seen.add(s["blend"])
            s = dict(s)
            s["end"] = s["start"] + a.bench - 1
            picked.append(s)
    shots = picked
os.makedirs(a.out, exist_ok=True)


def gpu_name():
    try:
        return subprocess.check_output(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], text=True, timeout=5).strip()
    except Exception:
        return "unknown (nvidia-smi not found)"


print("=" * 78)
print(f"GPU: {gpu_name()} | {a.quality} {res} | {a.samples} samples | {len(shots)} shots" + (" | BENCHMARK" if a.bench else ""))
print("=" * 78, flush=True)
rows = []
t_all = time.time()
for i, s in enumerate(shots, 1):
    beat, blend = s["beat"], os.path.join(HERE, s["blend"])
    n = s["end"] - s["start"] + 1
    frames = os.path.join(a.out, f"frames_{beat}_{a.quality}" + ("_bench" if a.bench else ""))
    mp4 = os.path.join(a.out, f"{s['clip']}_{beat}_{a.quality}" + ("_bench" if a.bench else "") + ".mp4")
    print(f"\n[{i}/{len(shots)}] {s['clip']} ({beat}) {s['blend']} frames {s['start']}..{s['end']} ({n})", flush=True)
    t0 = time.time()
    cmd = [a.blender, "-b", blend, "--python-expr", f"import bpy; bpy.context.scene.eevee.taa_render_samples={a.samples}",
           "-P", os.path.join(HERE, "render_cli.py"), "--", "frames", frames, "--range", str(s["start"]), str(s["end"]),
           "--res", res, "--pause", "0"]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL if not os.environ.get("VERBOSE") else None)
    t_render = time.time() - t0
    if r.returncode != 0:
        print("  Blender failed, exit code", r.returncode, flush=True)
        continue
    t1 = time.time()
    audio = os.path.join(HERE, s["audio"])
    ff = ["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-start_number", str(s["start"]), "-i", os.path.join(frames, "f_%04d.png")]
    if os.path.exists(audio) and not a.bench:
        ff += ["-i", audio, "-filter_complex", "[1:a]adelay=800|800,apad[a]", "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-shortest"]
    ff += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", mp4]
    subprocess.run(ff, check=False)
    t_mux = time.time() - t1
    rows.append(dict(clip=s["clip"], beat=beat, blend=s["blend"], frames=n, render_s=round(t_render, 1), s_per_frame=round(t_render / n, 3),
                     mux_s=round(t_mux, 1), mp4=os.path.basename(mp4)))
    print(f"  rendered {n} frames in {t_render:.0f} s = {t_render / n:.2f} s/frame, encode {t_mux:.0f} s", flush=True)

total = time.time() - t_all
frames_total = sum(r["frames"] for r in rows)
render_total = sum(r["render_s"] for r in rows)
report = dict(gpu=gpu_name(), quality=a.quality, samples=a.samples, bench=a.bench, shots=rows, total_frames=frames_total,
              total_render_s=round(render_total, 1), avg_s_per_frame=round(render_total / frames_total, 3) if frames_total else None,
              wall_clock_s=round(total, 1))
name = f"timing_{a.quality}" + ("_bench" if a.bench else "") + ".json"
json.dump(report, open(os.path.join(a.out, name), "w"), indent=2)
print("\n" + "=" * 78)
print(f"{'Beat':<6} {'Blend':<16} {'Frames':>7} {'Render':>9} {'s/frame':>9}")
for r in rows:
    print(f"{r['beat']:<6} {r['blend']:<16} {r['frames']:>7} {r['render_s']:>8.0f}s {r['s_per_frame']:>8.2f}s")
print("-" * 78)
print(f"TOTAL {frames_total} frames, render {render_total / 60:.1f} min, average {report['avg_s_per_frame']} s/frame, wall clock {total / 60:.1f} min")
print(f"Report: {os.path.join(a.out, name)}")
