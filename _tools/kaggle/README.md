# Rendering on Kaggle (free GPU, ~30 h/week)

Status: **untested**. Whether Blender's EEVEE renderer can use Kaggle's GPU headless is not confirmed anywhere;
the notebook tests it first. Only render real frames if the test says a mode works on the NVIDIA GPU and its test
image matches the PC render.

## One-time setup
1. kaggle.com → sign in → **Settings → Phone verification** (needed for GPUs).
2. Make the bundle on your PC (packs textures into the .blend copies so nothing points to Windows paths):
   ```
   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P _tools/kaggle/make_kaggle_bundle.py -- Kochi
   ```
   (list the .blend names you want; no names = all). Output: `_tools/kaggle/colachel_bundle.zip`.
3. Kaggle → **Create → New Dataset** → upload `colachel_bundle.zip` (Kaggle unzips it) → title
   **colachel-blender** → Create. To update later: dataset page → **New Version** → upload the new zip.
4. Kaggle → **Create → New Notebook** → **File → Import Notebook** → `_tools/kaggle/colachel_kaggle_render.ipynb`.
5. Right panel: **Accelerator: GPU T4 x2** (or P100), **Internet: On**, **Add Input** → your `colachel-blender` dataset.

## First run: the test
- Run cells 1-4 (the defaults are `Kochi`, test frame 230).
- Cell 4 tries three ways to run EEVEE without a screen and prints, for each: did it render, seconds per frame,
  and which GPU Blender used. It picks a mode only if the GPU line names NVIDIA/Tesla/T4/P100.
- Compare `test_<mode>_f230.png` (shown in the notebook) with `_tools/kaggle/local_reference_f230.png` on your PC.
  They should look the same (lighting, haze, colours). If Kaggle's looks different or no mode uses the NVIDIA GPU,
  stop: Kaggle can't render this project, and we fall back to the two PCs.

## Rendering a range
- Set `BLEND`, `START`, `END`, `RES`, `SAMPLES` in cell 1 (e.g. Kochi 147-368 is the pending S12 re-render).
- Interactive: run cells 5-6, download the zip from the link.
- Long jobs: **Save Version → Save & Run All (Commit)**. It runs in the background (max 12 h per run); the zip
  appears in the notebook's **Output** tab when done. Frames resume if you re-run with the same range.
- Unzip the frames into `Battle of Colachel/blender/renders/frames_<scene>_720p/` on the PC that encodes the
  reviews (frame numbers are kept: `f_0147.png` ...).

## Limits to remember
- ~30 GPU hours per week (resets weekly), 12 h per session, sessions may queue when Kaggle is busy.
- Map.blend beats share one timeline: render only the frame range of the beat you need.
