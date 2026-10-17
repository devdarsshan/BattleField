## **Worked script for s30-s40:#Graphic load:
import os
!apt-get update -qq
!apt-get install -y -qq libxi6 libxrender1 libxkbcommon-x11-0 libglvnd0 libgl1 libegl1 ffmpeg libavcodec-extra

os.environ['__EGL_VENDOR_LIBRARY_FILENAMES'] = '/usr/share/glvnd/egl_vendor.d/10_nvidia.json'
os.environ['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
if 'DISPLAY' in os.environ:
    del os.environ['DISPLAY']
print('✓ Cloud GPU hardware acceleration configured successfully!')



# **import os, shutil, glob, zipfile
from google.colab import drive, files

# 1. Mount Drive
try:
    drive.mount('/content/drive')
except Exception as e:
    pass

# 2. Clean out old project directory completely
PROJECT_DIR = '/content/project'
if os.path.exists(PROJECT_DIR):
    shutil.rmtree(PROJECT_DIR)
os.makedirs(PROJECT_DIR, exist_ok=True)

# 3. Locate and unpack s30_to_s40_package.zip
drive_matches = glob.glob('/content/drive/MyDrive/**/s30_to_s40_package.zip', recursive=True) + \
                glob.glob('/content/drive/MyDrive/battlefield/colachel/*.zip')

extracted = False
for zpath in drive_matches:
    if os.path.exists(zpath) and 's30' in zpath.lower():
        print(f"✓ Found package on Drive: {zpath}")
        with zipfile.ZipFile(zpath, 'r') as z:
            z.extractall(PROJECT_DIR)
        extracted = True
        break

if not extracted:
    print("👉 s30_to_s40_package.zip not found on Drive. Please upload it now:")
    uploaded = files.upload()
    fname = list(uploaded.keys())[0]
    with zipfile.ZipFile(fname, 'r') as z:
        z.extractall(PROJECT_DIR)

print("\n✓ /content/project is ready! Active Manifest:")
!cat /content/project/manifW# Worked script for s56-s69
import os
import glob
import json
import shutil
import zipfile
from google.colab import drive, files

# 1. Mount Google Drive
try:
    drive.mount('/content/drive')
    print('✓ Google Drive mounted at /content/drive')
except Exception as e:
    print(f'Google Drive mount notice: {e}')

# 2. CLEAR the old project folder so old files never conflict
PROJECT_DIR = '/content/project'
if os.path.exists(PROJECT_DIR):
    shutil.rmtree(PROJECT_DIR)
os.makedirs(PROJECT_DIR, exist_ok=True)

# 3. Specifically search for the S56 package
def find_and_unpack_package():
    # Look for s56 package in Drive or local
    drive_zips = glob.glob('/content/drive/MyDrive/**/s56*.zip', recursive=True) + \
                 glob.glob('/content/drive/MyDrive/battlefield/colachel/*s56*.zip')
    local_zips = glob.glob('/content/*s56*.zip')
    
    candidate_zips = drive_zips + local_zips
    for zpath in candidate_zips:
        if os.path.exists(zpath):
            try:
                with zipfile.ZipFile(zpath, 'r') as z:
                    z.extractall(PROJECT_DIR)
                print(f'✓ Successfully extracted S56 package from: {zpath}')
                return True
            except Exception as e:
                print(f'Could not extract {zpath}: {e}')
    return False

found = find_and_unpack_package()

# 4. If s56_to_s69_package.zip isn't in Drive yet, prompt to upload it
if not found:
    print('\n👉 s56_to_s69_package.zip not detected on Drive yet.')
    print('Please upload "s56_to_s69_package.zip" now:')
    uploaded = files.upload()
    fname = list(uploaded.keys())[0]
    with zipfile.ZipFile(fname, 'r') as z:
        z.extractall(PROJECT_DIR)
    print(f'✓ Successfully extracted {fname}')

# 5. Verify and display Manifest
manifest_file = os.path.join(PROJECT_DIR, 'manifest.json')
if os.path.exists(manifest_file):
    with open(manifest_file, 'r', encoding='utf-8') as f:
        mdata = json.load(f)
    print('=' * 80)
    print(f'📋 ACTIVE BATCH: {mdata.get("batch_name", "Unknown")}')
    print(f'📝 Description:  {mdata.get("description", "")}')
    print('-' * 80)
    print(f'{"Clip":<10} {"Beat":<8} {"Blend File":<16} {"Range":<16} {"Audio":<16}')
    print('-' * 80)
    total_frames = 0
    for s in mdata.get('shots', []):
        fcount = s['end'] - s['start'] + 1
        total_frames += fcount
        print(f'{s["clip"]:<10} {s.get("beat", ""):<8} {s["blend"]:<16} {s["start"]}..{s["end"]} ({fcount}f)   {s.get("audio", ""):<16}')
    print('-' * 80)
    print(f'Total Frames to Render: {total_frames:,} frames across {len(mdata.get("shots", []))} shots')
    print('=' * 80)
else:cell2:

!python /content/project/colab_batch_engine.py \
  --quality 720p \
  --samples 16 \
  --out "/content/drive/MyDrive/battlefield/colachel/renders" \
  --project /content/pro
60,62,64  - Only the main scene area is designed! The background and surroundings are missing
81 - The clip ending showing the sky view, the render is not complete! The land, sea and sky texture is cut off!
82 - The clip is totally different! It's not following the other clip rendered area!! The colors are totally different!

ject


    print(f'⚠️ Warning: No manifest.json found at {manifest_file}.')


est.json | grep -E "batch_name|clip|beat|blend"

