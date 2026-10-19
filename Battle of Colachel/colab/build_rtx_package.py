"""Build the folder to upload to Google Drive and render on the RTX 4050 laptop.
Bundles blend files, narration audio, render_cli.py, render_local.py, colachel_kit.py, and manifest.json.
Also writes <folder>.zip.

Usage:
  python build_rtx_package.py 19 28               # builds rtx4050_s19_s28/ and rtx4050_s19_s28.zip
  python build_rtx_package.py 1 7                 # builds rtx4050_s01_s07/ and rtx4050_s01_s07.zip
  python build_rtx_package.py 44 60               # builds rtx4050_s44_s60/ and rtx4050_s44_s60.zip
  python build_rtx_package.py 29 43               # builds rtx4050_test/ and rtx4050_test.zip
"""
import json
import os
import shutil
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BL = os.path.join(ROOT, "blender")
AUD = os.path.join(ROOT, "audio")

lo = int(sys.argv[1]) if len(sys.argv) >= 2 else 19
hi = int(sys.argv[2]) if len(sys.argv) >= 3 else 28

if len(sys.argv) >= 4:
    out_name = sys.argv[3]
elif (lo, hi) == (29, 43):
    out_name = "rtx4050_test"
else:
    out_name = f"rtx4050_s{lo:02d}_s{hi:02d}"

OUT = os.path.join(ROOT, "colab", out_name)

TIMING = {
    "Colachel.blend": "timing.json",
    "Pepper.blend": "timing_pepper.json",
    "Kochi.blend": "timing_kochi.json",
    "Palace.blend": "timing_palace.json",
    "Palace15.blend": "timing_palace15.json",
    "Port.blend": "timing_port.json",
    "Study.blend": "timing_study.json",
    "Meeting.blend": "timing_meeting.json",
    "Battle.blend": "timing_battle.json",
    "Varkala.blend": "timing_varkala.json",
    "Map.blend": "timing_map.json",
    "Landing.blend": "timing_landing.json",
    "Inland.blend": "timing_inland.json",
    "Siege.blend": "timing_siege.json",
    "Surrender.blend": "timing_surrender.json",
    "Udayagiri.blend": "timing_udayagiri.json",
    "Chapel.blend": "timing_chapel.json",
    "Treaty.blend": "timing_treaty.json",
    "Temple.blend": "timing_temple.json",
    "Today.blend": "timing_today.json"
}

shots, files = [], {}
for blend, tj in TIMING.items():
    p = os.path.join(BL, "renders", tj)
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    for c in d["clips"]:
        n = int(c["beat"][1:])
        if not lo <= n <= hi:
            continue
        if blend == "Colachel.blend" and n > 6:
            # S07 onward live in their own scene files (S07 is the Map.blend cloud dissolve)
            continue
        wav_src = c["wav"] if os.path.isabs(c["wav"]) else os.path.normpath(os.path.join(BL, c["wav"]))
        wav_name = f"{c['beat']}.wav"
        files[wav_name] = wav_src
        shots.append(dict(
            clip=f"clip{c['clip']}",
            beat=c["beat"],
            blend=blend,
            start=c["first"],
            end=c["last"],
            audio=wav_name,
            voice="placeholder" if "placeholder" in c.get("wav", "") or c.get("placeholder", False) else "final"
        ))
        files[blend] = os.path.join(BL, blend)

shots.sort(key=lambda s: int(s["beat"][1:]))

if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

for name, src in files.items():
    shutil.copy2(src, os.path.join(OUT, name))

shutil.copy2(os.path.join(BL, "render_cli.py"), os.path.join(OUT, "render_cli.py"))
if os.path.exists(os.path.join(BL, "colachel_kit.py")):
    shutil.copy2(os.path.join(BL, "colachel_kit.py"), os.path.join(OUT, "colachel_kit.py"))
shutil.copy2(os.path.join(ROOT, "colab", "rtx_template", "render_local.py"), os.path.join(OUT, "render_local.py"))

total = sum(s["end"] - s["start"] + 1 for s in shots)
distinct_blends = sorted(set(s["blend"] for s in shots))

readme_text = f"""# RTX 4050 render: finalised batch S{lo:02d} to S{hi:02d}

Goal: render the finalised batch (S{lo:02d} to S{hi:02d}: {', '.join(b.replace('.blend', '') for b in distinct_blends)}) in 1080p on the RTX 4050 laptop at 24 samples.

## Setup on the laptop (once)
1. Download `{out_name}.zip` (or the folder) from Google Drive and unzip it, for example to `C:\\colachel\\{out_name}`.
2. Install **Blender 5.2** (same version as the project) and **ffmpeg** (ensure `ffmpeg -version` works in command prompt/PowerShell).
3. Set Blender to High Performance GPU:
   Windows Settings > System > Display > Graphics > Add desktop app >
   `C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe` > Options > **High performance (NVIDIA GeForce RTX 4050)**.
   *(Without this, a dual-GPU hybrid laptop will silently render on the slow integrated Intel/AMD GPU!)*
4. Python 3 on PATH (`python --version` works).

## Step 1: The Test Run (Benchmark ~2-5 minutes)
Renders only the first 48 frames (2 seconds) from each distinct scene file ({', '.join(distinct_blends)}) at 1080p to verify speed and thermal stability:

```powershell
python render_local.py --blender "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --quality 1080p --bench 48
```
This writes `renders\\timing_1080p_bench.json` and prints a summary table of render speed (seconds/frame).
Check the numbers and send back the results / timing json.

## Step 2: The Main Run (Full Batch S{lo:02d}-S{hi:02d})
Once the benchmark is verified, render all {len(shots)} finalised shots ({total:,} frames total at 1080p, 24 samples):

```powershell
python render_local.py --blender "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --quality 1080p --samples 24
```

### Useful Options:
- `--quality 720p`: Render 720p previews instead of 1080p.
- `--samples 16`: Faster render for quick draft checks (default is 24 samples).
- `--only Sxx,Syy`: Render only specific beats.
- Resumable: Frames already rendered (> 2 KB) are automatically skipped, so you can safely stop and resume anytime.
- Each finished clip generates `renders\\<clip>_<beat>_1080p.mp4` with synced narration audio (0.8s lead).
- Full batch timing report is saved to `renders\\timing_1080p.json`.
- When all batches are done, clips are merged with `merge_clips.py`.

## Package Contents
- `manifest.json`: {len(shots)} shot definitions (clip, beat, blend, frame range, narration audio).
- `*.blend`: {len(distinct_blends)} scene files ({', '.join(distinct_blends)}).
- Narration audio tracks: S{lo:02d}.wav ... S{hi:02d}.wav.
- `colachel_kit.py`: Shared modular asset definitions.
- `render_cli.py`: Headless frame renderer with thermal guard (monitors GPU temp).
- `render_local.py`: Automated batch runner, frame sequencer, ffmpeg audio muxer, and benchmark timer.
"""
with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_text)

json.dump(dict(
    batch_name=f"S{lo:02d}_to_S{hi:02d}",
    description=f"Finalised clips S{lo:02d}-S{hi:02d} for the RTX 4050 render",
    shots=shots
), open(os.path.join(OUT, "manifest.json"), "w"), indent=2)

zp = OUT + ".zip"
if os.path.exists(zp):
    os.remove(zp)

with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for f in sorted(os.listdir(OUT)):
        z.write(os.path.join(OUT, f), f"{out_name}/{f}")

print(f"{len(shots)} shots, {total} frames, folder {OUT} ({sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) / 1e6:.0f} MB), zip {os.path.getsize(zp) / 1e6:.0f} MB")
placeholders = [s["beat"] for s in shots if s["voice"] == "placeholder"]
print("placeholder-voice beats still in the package:", placeholders or "none")
