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
!cat /content/project/manifest.json | grep -E "batch_name|clip|beat|blend"

