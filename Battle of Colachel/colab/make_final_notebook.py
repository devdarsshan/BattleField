"""Generate colab_render_final.ipynb from the cells that were verified in Colab (see doc.md).

  python make_final_notebook.py

Cell order (as finalised after the Colab checks):
  1  GPU check
  2  Graphic load (apt libraries + NVIDIA EGL environment)          <- worked
  3  Install Blender 5.2.2 LTS for Linux
  4  Mount Drive, clear /content/project, unpack the chosen package, print its manifest   <- worked
  5  cell2: the batch render command exactly as finalised                                 <- worked
  6  Rescue copy: the render saved in the session but not in Drive, so copy it to Drive and/or download a zip
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text.strip("\n").splitlines(True)}


cells = []

cells.append(md("""
# Battle of Colachel: Cloud GPU batch render (final, verified)

Runs `colab_batch_engine.py` on a Colab NVIDIA GPU: renders each shot of a package with EEVEE, mixes in the narration
and writes one MP4 per clip plus a timing report.

**Order:** run cells 1 to 5 top to bottom. Cell 6 saves the finished MP4s to Drive and offers a zip download.

1. Runtime > Change runtime type > T4 GPU (or better).
2. Put the package zip (for example `s41_to_s55_package.zip`) in `My Drive/battlefield/colachel/`, or upload it when asked.
3. Change `PACKAGE` in cell 4 to the package you want, and `--quality` / `--samples` in cell 5.
"""))

cells.append(md("### Cell 1: check the GPU"))
cells.append(code("!nvidia-smi"))

cells.append(md("### Cell 2: graphic load (verified)\nInstalls the headless graphics libraries and points EGL at the NVIDIA driver so EEVEE does not fall back to CPU."))
cells.append(code("""
import os
!apt-get update -qq
!apt-get install -y -qq libxi6 libxrender1 libxkbcommon-x11-0 libglvnd0 libgl1 libegl1 ffmpeg libavcodec-extra xvfb

os.environ['__EGL_VENDOR_LIBRARY_FILENAMES'] = '/usr/share/glvnd/egl_vendor.d/10_nvidia.json'
os.environ['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
if 'DISPLAY' in os.environ:
    del os.environ['DISPLAY']
print('Cloud GPU hardware acceleration configured successfully!')
"""))

cells.append(md("### Cell 3: install Blender 5.2.2 LTS (Linux)\nThe batch engine expects it at `/content/blender-5.2.2-linux-x64/blender`."))
cells.append(code("""
import os
os.chdir('/content')
BLENDER_VERSION = '5.2.2'
BLENDER_DIR = f'blender-{BLENDER_VERSION}-linux-x64'
BLENDER_TAR = f'{BLENDER_DIR}.tar.xz'
BLENDER_URL = f'https://download.blender.org/release/Blender5.2/{BLENDER_TAR}'

if not os.path.exists(f'/content/{BLENDER_DIR}'):
    print(f'Downloading Blender {BLENDER_VERSION} LTS...')
    !wget -q --show-progress {BLENDER_URL}
    print(f'Extracting {BLENDER_TAR}...')
    !tar -xf {BLENDER_TAR}
    print('Blender installed.')
else:
    print('Blender already present.')

!/content/{BLENDER_DIR}/blender --version
"""))

cells.append(md("### Cell 4: load the package (verified)\nMounts Drive, clears `/content/project`, unpacks the package named in `PACKAGE`, and prints the manifest. If the package is not on Drive you are asked to upload it."))
cells.append(code("""
import os, glob, json, shutil, zipfile
from google.colab import drive, files

PACKAGE = 's41_to_s55'          # the package to render: matches <PACKAGE>*.zip on Drive or in /content

# 1. Mount Google Drive
try:
    drive.mount('/content/drive')
    print('Google Drive mounted at /content/drive')
except Exception as e:
    print(f'Google Drive mount notice: {e}')

# 2. Clear the old project folder so old files never conflict
PROJECT_DIR = '/content/project'
if os.path.exists(PROJECT_DIR):
    shutil.rmtree(PROJECT_DIR)
os.makedirs(PROJECT_DIR, exist_ok=True)

# 3. Find and unpack the package
def find_and_unpack_package():
    candidates = (glob.glob(f'/content/drive/MyDrive/**/{PACKAGE}*.zip', recursive=True) +
                  glob.glob(f'/content/drive/MyDrive/battlefield/colachel/*{PACKAGE}*.zip') +
                  glob.glob(f'/content/*{PACKAGE}*.zip'))
    for zpath in candidates:
        if os.path.exists(zpath):
            try:
                with zipfile.ZipFile(zpath, 'r') as z:
                    z.extractall(PROJECT_DIR)
                print(f'Extracted package from: {zpath}')
                return True
            except Exception as e:
                print(f'Could not extract {zpath}: {e}')
    return False

if not find_and_unpack_package():
    print(f'\\n{PACKAGE} package not found on Drive. Please upload it now:')
    uploaded = files.upload()
    fname = list(uploaded.keys())[0]
    with zipfile.ZipFile(fname, 'r') as z:
        z.extractall(PROJECT_DIR)
    print(f'Extracted {fname}')

# 4. Show the manifest
manifest_file = os.path.join(PROJECT_DIR, 'manifest.json')
if os.path.exists(manifest_file):
    with open(manifest_file, 'r', encoding='utf-8') as f:
        mdata = json.load(f)
    print('=' * 80)
    print(f'ACTIVE BATCH: {mdata.get("batch_name", "Unknown")}')
    print(f'Description:  {mdata.get("description", "")}')
    print('-' * 80)
    print(f'{"Clip":<10} {"Beat":<8} {"Blend File":<16} {"Range":<16} {"Audio":<16}')
    print('-' * 80)
    total_frames = 0
    for s in mdata.get('shots', []):
        fcount = s['end'] - s['start'] + 1
        total_frames += fcount
        print(f'{s["clip"]:<10} {s.get("beat", ""):<8} {s["blend"]:<16} {s["start"]}..{s["end"]} ({fcount}f)   {s.get("audio", ""):<16}')
    print('-' * 80)
    print(f'Total frames to render: {total_frames:,} across {len(mdata.get("shots", []))} shots')
    print('=' * 80)
else:
    print(f'Warning: no manifest.json found at {manifest_file}.')
"""))

cells.append(md("### Cell 5 (cell2): render the batch (verified)\n`--quality` is `720p` or `1080p`. Each clip is saved as an MP4 with narration; re-running skips clips that already exist."))
cells.append(code("""
!python /content/project/colab_batch_engine.py \\
  --quality 720p \\
  --samples 16 \\
  --out "/content/drive/MyDrive/battlefield/colachel/renders" \\
  --project /content/project
"""))

cells.append(md("### Cell 6: rescue copy\nThe render finished in the session but the Drive copy did not always appear. This copies every MP4 and timing report that the session holds to Drive (and flushes it), and builds a zip to download."))
cells.append(code("""
import os, glob, shutil
from google.colab import drive, files

OUT = '/content/drive/MyDrive/battlefield/colachel/renders'
os.makedirs(OUT, exist_ok=True)
found = sorted(set(glob.glob('/content/*.mp4') + glob.glob('/content/renders/*.mp4') + glob.glob(OUT + '/*.mp4')))
for src in found:
    dst = os.path.join(OUT, os.path.basename(src))
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copy2(src, dst)
    print('on Drive:', dst, f'{os.path.getsize(dst) / 1e6:.1f} MB')
for rep in glob.glob('/content/**/timing_*', recursive=True):
    if '/drive/' not in rep:
        shutil.copy2(rep, os.path.join(OUT, os.path.basename(rep)))
drive.flush_and_unmount()
print('Drive flushed.')

# a zip to download as well
os.makedirs('/content/download', exist_ok=True)
for src in found:
    shutil.copy2(src, '/content/download/' + os.path.basename(src))
shutil.make_archive('/content/colachel_renders', 'zip', '/content/download')
files.download('/content/colachel_renders.zip')
"""))

nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"gpuType": "T4", "provenance": []},
                                   "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
out = os.path.join(HERE, "colab_render_final.ipynb")
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("wrote", out)
