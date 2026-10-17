"""Build the deployment package for Google Colab batch render S30..S40.
Bundles blend files, audio narrations, manifest, and runner scripts.
"""
import os
import sys
import zipfile
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COLAB_DIR = os.path.join(PROJECT_ROOT, "colab")
BLENDER_DIR = os.path.join(PROJECT_ROOT, "blender")
AUDIO_DIR = os.path.join(PROJECT_ROOT, "audio")

ZIP_NAME = "s30_to_s40_package.zip"
ZIP_PATH = os.path.join(COLAB_DIR, ZIP_NAME)

FILES_TO_PACK = [
    # Config & Runners
    (os.path.join(COLAB_DIR, "manifest.json"), "manifest.json"),
    (os.path.join(COLAB_DIR, "colab_batch_engine.py"), "colab_batch_engine.py"),
    (os.path.join(COLAB_DIR, "colab_render_cli.py"), "colab_render_cli.py"),
    (os.path.join(BLENDER_DIR, "colachel_kit.py"), "colachel_kit.py"),
    # Blend files
    (os.path.join(BLENDER_DIR, "Landing.blend"), "Landing.blend"),
    (os.path.join(BLENDER_DIR, "Inland.blend"), "Inland.blend"),
    (os.path.join(BLENDER_DIR, "Map.blend"), "Map.blend"),
    (os.path.join(BLENDER_DIR, "Siege.blend"), "Siege.blend"),
    # Audio wav files
    (os.path.join(AUDIO_DIR, "S30.wav"), "S30.wav"),
    (os.path.join(AUDIO_DIR, "S31.wav"), "S31.wav"),
    (os.path.join(AUDIO_DIR, "S32.wav"), "S32.wav"),
    (os.path.join(AUDIO_DIR, "S33.wav"), "S33.wav"),
    (os.path.join(AUDIO_DIR, "S34.wav"), "S34.wav"),
    (os.path.join(AUDIO_DIR, "S35.wav"), "S35.wav"),
    (os.path.join(AUDIO_DIR, "S36.wav"), "S36.wav"),
    (os.path.join(AUDIO_DIR, "S37.wav"), "S37.wav"),
    (os.path.join(AUDIO_DIR, "S38.wav"), "S38.wav"),
    (os.path.join(AUDIO_DIR, "S39.wav"), "S39.wav"),
    (os.path.join(AUDIO_DIR, "S40.wav"), "S40.wav"),
]

def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("=" * 70)
    print("[*] Building Colab Batch Package: S30 to S40")
    print(f"Target archive: {ZIP_PATH}")
    print("=" * 70)

    # 1. Verify all sources exist
    missing = []
    total_raw_bytes = 0
    for src, arcname in FILES_TO_PACK:
        if not os.path.exists(src):
            missing.append(src)
        else:
            sz = os.path.getsize(src)
            total_raw_bytes += sz
            print(f"  + {arcname:<22} ({sz / (1024*1024):>6.2f} MB)")

    if missing:
        print("\n[!] Error: Missing required files:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    print("-" * 70)
    print(f"Total uncompressed size: {total_raw_bytes / (1024*1024):.2f} MB ({len(FILES_TO_PACK)} files)")
    print("Compressing archive...")

    t0 = time.time()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arcname in FILES_TO_PACK:
            zf.write(src, arcname=arcname)
    dt = time.time() - t0

    zip_size = os.path.getsize(ZIP_PATH)
    ratio = (1.0 - zip_size / total_raw_bytes) * 100

    print("=" * 70)
    print(f"[OK] Successfully built: {ZIP_PATH}")
    print(f"   Size: {zip_size / (1024*1024):.2f} MB ({zip_size:,} bytes)")
    print(f"   Compression savings: {ratio:.1f}% | Time: {dt:.1f}s")
    print("=" * 70)

if __name__ == "__main__":
    main()
