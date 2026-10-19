# RTX 4050 render: finalised batch S44 to S60

Goal: render the finalised batch (S44 to S60: Siege, Surrender, Udayagiri, Map, Chapel) in 1080p on the RTX 4050 laptop at 24 samples.

## Setup on the laptop (once)
1. Download `rtx4050_test.zip` (or the folder) from Google Drive and unzip it, for example to `C:\colachel\rtx4050_test`.
2. Install **Blender 5.2** (same version as the project) and **ffmpeg** (ensure `ffmpeg -version` works in command prompt/PowerShell).
3. Set Blender to High Performance GPU:
   Windows Settings > System > Display > Graphics > Add desktop app >
   `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` > Options > **High performance (NVIDIA GeForce RTX 4050)**.
   *(Without this, a dual-GPU hybrid laptop will silently render on the slow integrated Intel/AMD GPU!)*
4. Python 3 on PATH (`python --version` works).

## Step 1: The Test Run (Benchmark ~2-5 minutes)
Renders only the first 48 frames (2 seconds) from each distinct scene file (`Siege.blend`, `Surrender.blend`, `Udayagiri.blend`, `Map.blend`, `Chapel.blend`) at 1080p to verify speed and thermal stability:

```powershell
python render_local.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --quality 1080p --bench 48
```
This writes `renders\timing_1080p_bench.json` and prints a summary table of render speed (seconds/frame).
Check the numbers and send back the results / timing json.

## Step 2: The Main Run (Full Batch S44-S60)
Once the benchmark is verified, render all 17 finalised shots (5,629 frames total at 1080p, 24 samples):

```powershell
python render_local.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --quality 1080p --samples 24
```

### Useful Options:
- `--quality 720p`: Render 720p previews instead of 1080p.
- `--samples 16`: Faster render for quick draft checks (default is 24 samples).
- `--only S49,S50`: Render only specific beats.
- Resumable: Frames already rendered (> 2 KB) are automatically skipped, so you can safely stop and resume anytime.
- Each finished clip generates `renders\<clip>_<beat>_1080p.mp4` with synced narration audio (0.8s lead).
- Full batch timing report is saved to `renders\timing_1080p.json`.
- When all batches are done, clips are merged with `merge_clips.py`.

## Package Contents
- `manifest.json`: 17 shot definitions (clip, beat, blend, frame range, narration audio).
- `*.blend`: 5 scene files (`Siege.blend`, `Surrender.blend`, `Udayagiri.blend`, `Map.blend`, `Chapel.blend`).
- `S44.wav` ... `S60.wav`: 17 finalized Algieba voice narration tracks.
- `colachel_kit.py`: Shared modular asset definitions.
- `render_cli.py`: Headless frame renderer with thermal guard (monitors GPU temp).
- `render_local.py`: Automated batch runner, frame sequencer, ffmpeg audio muxer, and benchmark timer.
