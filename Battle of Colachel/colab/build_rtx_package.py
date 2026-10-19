"""Build the folder to upload to Google Drive and render on the RTX 4050 laptop: the finalised first-half clips (S29-S50),
their blend files, narration, render_cli.py, render_local.py and a manifest. Also writes <folder>.zip.

  python build_rtx_package.py            # beats S29-S50 (default)
  python build_rtx_package.py 29 50
"""
import json
import os
import shutil
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BL = os.path.join(ROOT, "blender")
AUD = os.path.join(ROOT, "audio")
lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else (29, 50)
OUT = os.path.join(ROOT, "colab", f"rtx4050_s{lo:02d}_s{hi:02d}")      # one folder and zip per batch

TIMING = {"Colachel.blend": "timing.json", "Pepper.blend": "timing_pepper.json", "Kochi.blend": "timing_kochi.json",
          "Palace.blend": "timing_palace.json", "Palace15.blend": "timing_palace15.json", "Port.blend": "timing_port.json",
          "Study.blend": "timing_study.json", "Meeting.blend": "timing_meeting.json", "Battle.blend": "timing_battle.json",
          "Varkala.blend": "timing_varkala.json", "Map.blend": "timing_map.json", "Landing.blend": "timing_landing.json", "Inland.blend": "timing_inland.json",
          "Siege.blend": "timing_siege.json", "Surrender.blend": "timing_surrender.json", "Udayagiri.blend": "timing_udayagiri.json",
          "Chapel.blend": "timing_chapel.json", "Treaty.blend": "timing_treaty.json", "Temple.blend": "timing_temple.json",
          "Today.blend": "timing_today.json"}

shots, files = [], {}
for blend, tj in TIMING.items():
    p = os.path.join(BL, "renders", tj)
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    for c in d["clips"]:
        n = int(c["beat"][1:])
        if not lo <= n <= hi:
            continue
        if blend == "Colachel.blend" and n > 6:      # S07 onward live in their own scene files (S07 is the Map.blend cloud dissolve)
            continue
        wav_src = c["wav"] if os.path.isabs(c["wav"]) else os.path.normpath(os.path.join(BL, c["wav"]))
        wav_name = f"{c['beat']}.wav"
        files[wav_name] = wav_src
        shots.append(dict(clip=f"clip{c['clip']}", beat=c["beat"], blend=blend, start=c["first"], end=c["last"], audio=wav_name,
                          voice="placeholder" if "placeholder" in c["wav"] else "final"))
        files[blend] = os.path.join(BL, blend)
shots.sort(key=lambda s: int(s["beat"][1:]))
if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for name, src in files.items():
    shutil.copy2(src, os.path.join(OUT, name))
shutil.copy2(os.path.join(BL, "render_cli.py"), os.path.join(OUT, "render_cli.py"))
shutil.copy2(os.path.join(ROOT, "colab", "rtx_template", "render_local.py"), os.path.join(OUT, "render_local.py"))
shutil.copy2(os.path.join(ROOT, "colab", "rtx_template", "README.md"), os.path.join(OUT, "README.md"))
json.dump(dict(batch_name=f"S{lo}_to_S{hi}", description=f"Finalised clips S{lo}-S{hi} for the RTX 4050 speed test", shots=shots),
          open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
zp = OUT + ".zip"
if os.path.exists(zp):
    os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for f in sorted(os.listdir(OUT)):
        z.write(os.path.join(OUT, f), f"rtx4050_test/{f}")
total = sum(s["end"] - s["start"] + 1 for s in shots)
print(f"{len(shots)} shots, {total} frames, folder {OUT} ({sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) / 1e6:.0f} MB), zip {os.path.getsize(zp) / 1e6:.0f} MB")
placeholders = [s["beat"] for s in shots if s["voice"] == "placeholder"]
print("placeholder-voice beats still in the package:", placeholders or "none")
