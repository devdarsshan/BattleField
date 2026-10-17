# Google Colab Cloud GPU Batch Renderer for Blender

This folder contains everything needed to render Blender scenes on **Google Colab's cloud NVIDIA GPUs (Tesla T4 / L4)** with automatic video multiplexing, Google Drive persistence, and dynamic resolution presets.

---

## 📁 Files in This Folder

| File | Purpose |
| :--- | :--- |
| **`colab_render.ipynb`** | The complete Google Colab notebook ready to upload and run. Includes dynamic quality controls, Google Drive persistence, and inline video playback. |
| **`colab_batch_engine.py`** | Universal batch rendering engine: reads `manifest.json`, executes headless EEVEE via `xvfb-run`, encodes H.264 MP4s with audio narration, logs timings, and syncs directly to Google Drive. |
| **`s25_to_s29_package.zip`** | **Production batch bundle** for beats S25 through S29 (1,846 frames across `Battle.blend`, `Varkala.blend`, `Map.blend`, narration audios `S25.wav`..`S29.wav`, and `manifest.json`). |
| **`manifest.json`** | Declarative shot manifest specifying clips, beats, blend files, frame ranges, and audio tracks. |
| **`colab_render_cli.py`** | Cloud-adapted headless Blender render script (EEVEE/Cycles, GPU auto-selection, resumable frame skips). |
| **`make_colab_notebook.py`** | Script used to generate/update `colab_render.ipynb`. |

---

## ⚡ Key Highlights of the New Dynamic Pipeline

1. **Crash-Proof Google Drive Sync:**
   - Mounts Google Drive (`/content/drive/MyDrive/Colachel_Renders/`).
   - Every completed MP4 and timing report is saved **directly to Google Drive immediately upon completion**.
   - If Colab disconnects or the session restarts, you lose **zero progress**.
2. **Automatic Smart Resume:**
   - When you re-run the batch, the script detects already completed MP4s on Google Drive and skips them in 0.1s.
3. **Dynamic Quality Switching:**
   - Easily toggle between **`720p`** (~0.50s/frame, ideal for rapid previewing/testing) and **`1080p`** (~1.1s/frame for final delivery).
   - In Step 5, simply set `QUALITY = "720p"` or `QUALITY = "1080p"`.
4. **Universal Package Support:**
   - Any future batch (e.g. S30..S38 or the entire film) uses this exact same script and notebook. You only need to provide a new package `.zip` with a `manifest.json`.

---

## 🚀 How to Run the S25..S29 Batch in Google Colab

### Step 1: Open Notebook in Google Colab
1. Go to [Google Colab](https://colab.research.google.com/).
2. Click **Upload** and select `colab_render.ipynb`.

### Step 2: Ensure GPU is Enabled
1. In Colab's menu: **Runtime > Change runtime type**.
2. Choose **T4 GPU** (or L4/A100 if subscribed) and save.

### Step 3: Run the Cells
1. **Step 1:** Verifies the allocated GPU (`nvidia-smi`).
2. **Step 2:** Installs Xvfb, Mesa, ffmpeg, and `libavcodec-extra`.
3. **Step 3:** Downloads and extracts official Blender 5.2.2 LTS for Linux.
4. **Step 4:** Mounts Google Drive and unzips `s25_to_s29_package.zip` (either placed in Google Drive or uploaded directly via the interactive button).
5. **Step 5:** Starts the batch render. Set `QUALITY = "720p"` (or `"1080p"`). All MP4s are saved to `My Drive/Colachel_Renders/`.
6. **Step 6:** Review the timing table and watch the rendered MP4s directly inline.
7. **Step 7:** (Optional) Download all rendered MP4s as a single `.zip`.
