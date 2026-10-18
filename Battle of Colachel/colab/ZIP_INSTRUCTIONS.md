# What to zip (packages are not in git)

The `.zip` packages and the `rtx4050_test/` folder are generated files, so they are git-ignored (GitHub rejects files over 100 MB).
Rebuild them on any machine that has the repo, then upload the zip to Google Drive (`My Drive/battlefield/colachel/`).

## 1. Colab package (Google Colab, `colab_render_final.ipynb`)
Zip these files together (flat, no sub-folder) into `<name>_package.zip`, for example `s56_to_s69_package.zip`:

| File | From |
|---|---|
| `manifest.json` | `colab/manifest_<batch>.json` (renamed to `manifest.json`) |
| `colab_batch_engine.py`, `colab_render_cli.py` | `colab/` |
| every `.blend` the manifest names | `blender/` (for S56-S69: Udayagiri, Map, Chapel, Treaty, Temple, Today) |
| one `.wav` per beat in the manifest | `audio/Sxx.wav` (final voice) or `audio/placeholder/Sxx.wav` |

Build it with the script instead of by hand: `python colab/build_s56_s69_package.py` (edit its file list for another batch).
Set `PACKAGE = 's56_to_s69'` in cell 4 of the notebook to match the zip name.

## 2. RTX 4050 / local render folder
Zip the whole folder `colab/rtx4050_test/` (it already holds everything): `manifest.json`, `render_cli.py`, `render_local.py`,
`README.md`, the `.blend` files (Map, Landing, Inland, Siege) and the `Sxx.wav` narration of the finalised clips.

Build it with: `python colab/build_rtx_package.py 29 43` (beats S29 to S43). It writes `colab/rtx4050_test/` and `colab/rtx4050_test.zip`.
On the laptop follow `rtx4050_test/README.md` (`render_local.py --bench 48` for the timing test).

## Rules
- Do not commit any `.zip`, `.mp4`, rendered frames or the `rtx4050_test/` folder.
- Rebuild the package after any change to a scene (`film.py` scripts rewrite the `.blend` and `timing_*.json`) or to the narration.
