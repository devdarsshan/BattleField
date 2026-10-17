import json
import os
import zipfile

out_dir = r"E:\BattleField\Battle of Colachel\colab"
os.makedirs(out_dir, exist_ok=True)

notebook = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "accelerator": "GPU",
        "colab": {
            "provenance": [],
            "gpuType": "T4"
        },
        "language_info": {
            "name": "python"
        }
    },
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🎬 Battle of Colachel — Universal Cloud GPU Batch Renderer\n",
                "\n",
                "This Google Colab notebook offloads Blender rendering to a **cloud NVIDIA GPU (Tesla T4 / L4)**.\n",
                "\n",
                "### ⚡ Key Features:\n",
                "- **Dynamic Quality Presets:** Switch between **720p** (fast preview at ~0.50s/frame) and **1080p** (final delivery at ~1.1s/frame) with one click.\n",
                "- **Crash-Proof Google Drive Sync:** Rendered MP4s and timing reports are saved **directly to Google Drive as they finish**, so a session reset will never lose your progress.\n",
                "- **Smart Resume:** Re-running the batch automatically detects already-rendered clips on Google Drive and skips them in 0.1s.\n",
                "- **Universal Manifest-Driven:** Works dynamically with any input package (`manifest.json` defines shots, frames, blends, and narration audios).\n",
                "- **Inline Video Preview:** Watch completed review clips directly in your browser without leaving Colab."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 1: Verify GPU Allocation\n",
                "Ensure an NVIDIA Tesla T4 or L4 GPU is allocated by Colab."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "!nvidia-smi"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 2: Install Graphics & Video Codec Dependencies\n",
                "Installs Xvfb (virtual display buffer for headless EEVEE GPU acceleration) and H.264 video encoding libraries."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Install Xvfb virtual display buffer and Linux graphics + video libraries\n",
                "!apt-get update -qq\n",
                "!apt-get install -y -qq xvfb libxi6 libxrender1 libxkbcommon-x11-0 libgl1-mesa-glx ffmpeg libavcodec-extra\n",
                "print('✓ Cloud graphics libraries and video codecs installed successfully!')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 3: Download & Extract Blender 5.2.2 LTS\n",
                "Downloads the official Linux binary matching your project version (runs once per session; skips if already extracted)."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "\n",
                "BLENDER_VERSION = '5.2.2'\n",
                "BLENDER_DIR = f'blender-{BLENDER_VERSION}-linux-x64'\n",
                "BLENDER_TAR = f'{BLENDER_DIR}.tar.xz'\n",
                "BLENDER_URL = f'https://download.blender.org/release/Blender5.2/{BLENDER_TAR}'\n",
                "\n",
                "if not os.path.exists(BLENDER_DIR):\n",
                "    print(f'Downloading Blender {BLENDER_VERSION} LTS...')\n",
                "    !wget -q --show-progress {BLENDER_URL}\n",
                "    print(f'Extracting {BLENDER_TAR}...')\n",
                "    !tar -xf {BLENDER_TAR}\n",
                "    print(f'✓ Blender {BLENDER_VERSION} installed successfully!')\n",
                "else:\n",
                "    print(f'✓ Blender {BLENDER_VERSION} already installed.')\n",
                "\n",
                "!./{BLENDER_DIR}/blender --version"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 4: Mount Google Drive & Load Input Package\n",
                "Mounts your Google Drive so rendered videos are permanently saved across session crashes, then automatically unpacks the input package."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import glob\n",
                "import json\n",
                "import shutil\n",
                "import zipfile\n",
                "from google.colab import drive, files\n",
                "\n",
                "# 1. Mount Google Drive for persistent storage\n",
                "try:\n",
                "    drive.mount('/content/drive')\n",
                "    print('✓ Google Drive mounted at /content/drive')\n",
                "except Exception as e:\n",
                "    print(f'Google Drive mount notice: {e}')\n",
                "\n",
                "PROJECT_DIR = '/content/project'\n",
                "os.makedirs(PROJECT_DIR, exist_ok=True)\n",
                "\n",
                "# 2. Find and extract input package zip\n",
                "def find_and_unpack_package():\n",
                "    # Prioritize user's battlefield/colachel folder in Google Drive\n",
                "    drive_specific = glob.glob('/content/drive/MyDrive/battlefield/colachel/*.zip') + \\\n",
                "                     glob.glob('/content/drive/MyDrive/BattleField/Colachel/*.zip') + \\\n",
                "                     glob.glob('/content/drive/MyDrive/Battlefield/Colachel/*.zip') + \\\n",
                "                     glob.glob('/content/drive/MyDrive/battlefield/*.zip')\n",
                "    # Recursive search anywhere in MyDrive for s30, s25 or package zips\n",
                "    drive_recursive = glob.glob('/content/drive/MyDrive/**/s30*.zip', recursive=True) + \\\n",
                "                      glob.glob('/content/drive/MyDrive/**/s25*.zip', recursive=True) + \\\n",
                "                      glob.glob('/content/drive/MyDrive/**/*package*.zip', recursive=True)\n",
                "    # Local Colab /content root\n",
                "    local_zips = [z for z in glob.glob('/content/*.zip') if 'rendered' not in z and 'review' not in z and 'bundle' not in z]\n",
                "    \n",
                "    candidate_zips = drive_specific + drive_recursive + local_zips\n",
                "    for zpath in candidate_zips:\n",
                "        if os.path.exists(zpath) and ('package' in zpath.lower() or 's30' in zpath.lower() or 's25' in zpath.lower() or 'colachel' in zpath.lower()):\n",
                "            try:\n",
                "                with zipfile.ZipFile(zpath, 'r') as z:\n",
                "                    z.extractall(PROJECT_DIR)\n",
                "                print(f'✓ Successfully extracted package from: {zpath}')\n",
                "                print(f'  Target directory: {PROJECT_DIR}')\n",
                "                return True\n",
                "            except Exception as e:\n",
                "                print(f'Could not extract {zpath}: {e}')\n",
                "    return False\n",
                "\n",
                "found = find_and_unpack_package()\n",
                "\n",
                "# If no package found in Drive or /content, prompt for upload\n",
                "if not found and not os.path.exists(os.path.join(PROJECT_DIR, 'manifest.json')):\n",
                "    print('\\n👉 No input package detected in MyDrive/battlefield/colachel or /content.')\n",
                "    print('Please upload your batch package (e.g. \"s30_to_s40_package.zip\") below:')\n",
                "    uploaded = files.upload()\n",
                "    find_and_unpack_package()\n",
                "\n",
                "# 3. Verify and display Manifest\n",
                "manifest_file = os.path.join(PROJECT_DIR, 'manifest.json')\n",
                "if os.path.exists(manifest_file):\n",
                "    with open(manifest_file, 'r', encoding='utf-8') as f:\n",
                "        mdata = json.load(f)\n",
                "    print('=' * 80)\n",
                "    print(f'📋 ACTIVE BATCH: {mdata.get(\"batch_name\", \"Unknown\")}')\n",
                "    print(f'📝 Description:  {mdata.get(\"description\", \"\")}')\n",
                "    print('-' * 80)\n",
                "    print(f'{\"Clip\":<10} {\"Beat\":<8} {\"Blend File\":<16} {\"Range\":<16} {\"Audio\":<16}')\n",
                "    print('-' * 80)\n",
                "    total_frames = 0\n",
                "    for s in mdata.get('shots', []):\n",
                "        fcount = s['end'] - s['start'] + 1\n",
                "        total_frames += fcount\n",
                "        print(f'{s[\"clip\"]:<<10} {s.get(\"beat\", \"\"):<8} {s[\"blend\"]:<<16} {s[\"start\"]}..{s[\"end\"]} ({fcount}f)   {s.get(\"audio\", \"\"):<16}')\n",
                "    print('-' * 80)\n",
                "    print(f'Total Frames to Render: {total_frames:,} frames across {len(mdata.get(\"shots\", []))} shots')\n",
                "    print('=' * 80)\n",
                "else:\n",
                "    print(f'⚠️ Warning: No manifest.json found at {manifest_file}. Ensure your package contains manifest.json.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 5: Dynamic Cloud Batch Render (Direct Google Drive Storage)\n",
                "Set your desired quality (**720p** for fast review test or **1080p** for final production delivery). Rendered MP4s and timing reports are saved directly to Google Drive as each shot completes."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# @title 🎛️ Batch Render Configuration { run: \"auto\" }\n",
                "QUALITY = \"720p\"  # @param [\"720p\", \"1080p\"]\n",
                "SAMPLES = 16  # @param {type:\"integer\"}\n",
                "SAVE_TO_DRIVE = True  # @param {type:\"boolean\"}\n",
                "DRIVE_SUBFOLDER = \"battlefield/colachel/renders\"  # @param {type:\"string\"}\n",
                "\n",
                "import os\n",
                "\n",
                "if SAVE_TO_DRIVE:\n",
                "    OUTPUT_DIR = f'/content/drive/MyDrive/{DRIVE_SUBFOLDER}'\n",
                "else:\n",
                "    OUTPUT_DIR = '/content/renders/mp4'\n",
                "\n",
                "os.makedirs(OUTPUT_DIR, exist_ok=True)\n",
                "\n",
                "print(f'🚀 Starting Batch Render | Preset: {QUALITY} | EEVEE Samples: {SAMPLES}')\n",
                "print(f'💾 Destination: {OUTPUT_DIR}')\n",
                "print('=' * 80)\n",
                "\n",
                "# Run universal batch engine\n",
                "!python /content/project/colab_batch_engine.py \\\n",
                "  --quality {QUALITY} \\\n",
                "  --samples {SAMPLES} \\\n",
                "  --out \"{OUTPUT_DIR}\" \\\n",
                "  --project /content/project"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 6: Review Render Timings & Watch Inline Previews\n",
                "Displays the detailed render time report and provides inline video playback right inside the notebook."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import glob\n",
                "from IPython.display import display, HTML\n",
                "\n",
                "# 1. Display latest text report\n",
                "reports = sorted(glob.glob(f'{OUTPUT_DIR}/timing_report_*.txt'))\n",
                "if reports:\n",
                "    with open(reports[-1], 'r', encoding='utf-8') as f:\n",
                "        print(f.read())\n",
                "else:\n",
                "    print('No timing report found yet in', OUTPUT_DIR)\n",
                "\n",
                "# 2. Inline video playback for completed review MP4s\n",
                "mp4_files = sorted(glob.glob(f'{OUTPUT_DIR}/*.mp4'))\n",
                "if mp4_files:\n",
                "    import base64\n",
                "    print(f'\\nFound {len(mp4_files)} rendered video clips in {OUTPUT_DIR}:')\n",
                "    for mp4 in mp4_files:\n",
                "        fname = os.path.basename(mp4)\n",
                "        fsize_mb = os.path.getsize(mp4) / (1024 * 1024)\n",
                "        print(f'▶ {fname} ({fsize_mb:.2f} MB)')\n",
                "        try:\n",
                "            with open(mp4, 'rb') as f:\n",
                "                video_b64 = base64.b64encode(f.read()).decode('utf-8')\n",
                "            html = f'''\n",
                "            <div style=\"margin-bottom: 25px; border-bottom: 1px solid #444; padding-bottom: 15px;\">\n",
                "                <p style=\"font-size: 15px; font-weight: bold;\">🎬 {fname} <span style=\"color: #888; font-weight: normal;\">({fsize_mb:.2f} MB)</span></p>\n",
                "                <video width=\"640\" height=\"360\" controls controlsList=\"nodownload\" style=\"border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);\">\n",
                "                    <source src=\"data:video/mp4;base64,{video_b64}\" type=\"video/mp4\">\n",
                "                    Your browser does not support the video tag.\n",
                "                </video>\n",
                "            </div>\n",
                "            '''\n",
                "            display(HTML(html))\n",
                "        except Exception as e:\n",
                "            print(f'Could not load preview for {fname}: {e}')\n",
                "else:\n",
                "    print('No MP4 videos found in output directory.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Step 7: (Optional) Package & Download All MP4s as a Zip\n",
                "If you also want a local `.zip` copy downloaded directly to your PC, run this cell."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import shutil\n",
                "from google.colab import files\n",
                "\n",
                "zip_target = '/content/review_clips_bundle'\n",
                "if glob.glob(f'{OUTPUT_DIR}/*.mp4'):\n",
                "    print(f'Packaging MP4s from {OUTPUT_DIR}...')\n",
                "    shutil.make_archive(zip_target, 'zip', OUTPUT_DIR)\n",
                "    bundle_zip = f'{zip_target}.zip'\n",
                "    print(f'✓ Created {bundle_zip} ({os.path.getsize(bundle_zip):,} bytes)')\n",
                "    print('Starting browser download...')\n",
                "    files.download(bundle_zip)\n",
                "else:\n",
                "    print('No MP4 files to download. Check previous steps.')"
            ]
        }
    ]
}

ipynb_path = os.path.join(out_dir, "colab_render.ipynb")
with open(ipynb_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2)

print(f"Generated {ipynb_path} ({os.path.getsize(ipynb_path):,} bytes)")
