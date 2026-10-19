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

---

## Video format rules (read before any Colab render)

Every clip in the film must be **H.264 (libx264), 1920x1080, 24 fps, yuv420p, AAC audio, CRF 18**. The same as `rtx_template/render_local.py`.

**What went wrong once:** the clips for S08 to S18 were rendered on Colab with an older engine that quietly fell back to ffmpeg's
`mpeg4` (MPEG-4 Part 2) encoder at a fixed 5 Mbps when `libx264` failed. The pictures were fine, but the video came out softer and blockier
(about 8.7 Mbps against about 11.5 Mbps), and the files could not be joined with the others without re-encoding. You can spot them by the
name `..._review_1080p.mp4` and by `ffprobe` showing `codec_name=mpeg4`.

**What is fixed:** `colab_batch_engine.py` now
1. checks at the start that ffmpeg has `libx264` (or NVENC `h264_nvenc`), tries `apt-get install ffmpeg` once if not, and **stops** if it still has neither;
2. encodes with `libx264 -preset medium -crf 18` (NVENC only as a second choice, also H.264, constant quality 18);
3. never falls back to `mpeg4`. If H.264 fails for a clip, that clip is not saved and the log says so.

**How to render on Colab so this does not repeat**
1. Run the notebook's install cell (it installs `ffmpeg libavcodec-extra`), then cell 2 (`colab_batch_engine.py --quality 1080p --samples 24`).
   Use `--quality 1080p` for finals; 720p is for previews only.
2. Watch the log: each finished clip prints `[SAVED TO STORAGE] ... codec: libx264`. If you ever see another codec, or "STOP: this ffmpeg has no libx264", stop and fix ffmpeg first.
3. After the batch, check the files on Drive: `ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 FILE.mp4`
   must print `h264,1920,1080,24/1`. Anything else: re-render that clip.
4. The 4050 laptop (`render_local.py`) already follows the same rules.
5. `merge_nested.py` converts any non-H.264 clip before joining, but that only makes the join work. It cannot restore lost detail.
