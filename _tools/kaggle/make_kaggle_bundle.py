"""Build the upload bundle for rendering on Kaggle.

Run with Blender on your PC (it opens each .blend, packs every external file into it,
and saves a self-contained copy):

  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P _tools/kaggle/make_kaggle_bundle.py -- Map Kochi Port

(names are .blend files in "Battle of Colachel/blender", without .blend; no names = all of them)

Output: _tools/kaggle/colachel_bundle.zip  ->  upload it to Kaggle as a Dataset named "colachel-blender".
"""
import glob
import os
import shutil
import sys
import zipfile

import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BL = os.path.join(ROOT, "Battle of Colachel", "blender")
OUT_DIR = os.path.join(ROOT, "_tools", "kaggle", "bundle")
ZIP = os.path.join(ROOT, "_tools", "kaggle", "colachel_bundle.zip")

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
names = args or [os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(BL, "*.blend"))]

shutil.rmtree(OUT_DIR, ignore_errors=True)
os.makedirs(OUT_DIR)
for n in names:
    src = os.path.join(BL, n + ".blend")
    bpy.ops.wm.open_mainfile(filepath=src)
    try:
        bpy.ops.file.pack_all()                 # embed textures (map sea, parchment, ...)
    except RuntimeError as e:
        print("pack warning:", n, e)
    missing = [i.filepath for i in bpy.data.images if i.source == "FILE" and not i.packed_file]
    if missing:
        print("WARNING unpacked images in", n, missing)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, n + ".blend"), copy=True, compress=True)
    print("packed", n)
shutil.copy(os.path.join(BL, "render_cli.py"), OUT_DIR)

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    for f in os.listdir(OUT_DIR):
        z.write(os.path.join(OUT_DIR, f), f)
print("wrote", ZIP, round(os.path.getsize(ZIP) / 1e6, 1), "MB")
