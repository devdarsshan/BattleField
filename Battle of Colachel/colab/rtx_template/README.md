# RTX 4050 render: finalised clips (see manifest.json for the beats)

Goal: time a 1080p render of the finalised first-half clips on the RTX 4050 laptop and compare with this PC
(Intel Arc: about 2.3 s per 720p frame).

## Setup on the laptop (once)
1. Download this folder from Google Drive (or the `.zip`) and keep it together, for example `C:\colachel\rtx4050_test`.
2. Install **Blender 5.2** (the same version as the project) and **ffmpeg** (it must be on PATH: `ffmpeg -version` works).
3. Make Blender use the NVIDIA GPU: Windows Settings > System > Display > Graphics > Add desktop app >
   `blender.exe` > Options > **High performance**. Without this a hybrid laptop renders on the integrated GPU.
4. Python 3 on PATH.

## Step 1: the speed test (about 5 minutes)
Renders only the first 48 frames of each different scene file at 1080p and prints seconds per frame:

```
python render_local.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --quality 1080p --bench 48
```
Send back `renders\timing_1080p_bench.json` (or the printed table).

## Step 2: the full finalised batch
```
python render_local.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --quality 1080p --samples 24
```
Options: `--only S41,S42` for chosen beats, `--quality 720p` for previews, `--samples 16` for faster previews.
It is resumable: frames already rendered are skipped. Each clip becomes `renders\clipNN_Sxx_1080p.mp4` with its narration
(0.8 s in), and `renders\timing_1080p.json` holds the totals. Upload the `renders` folder back to Google Drive when done.

## What is in the folder
- `manifest.json`: the clips (beat, scene file, frame range, narration file).
- `*.blend`: the scenes (Map, Landing, Inland, Siege, Surrender); one `Sxx.wav` per beat: the narration.
- `render_cli.py`: the frame renderer with a thermal guard that pauses if the GPU passes 76 C.
- `render_local.py`: the batch runner, encoder and timer.
