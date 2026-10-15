"""Encode the rendered picture and lay the narration over it, each beat starting
`lead` seconds into its clip. Timings come from renders/timing.json (written by film.py).

  python make_video.py PICTURE OUT.mp4
PICTURE is either a silent .mp4 or a folder of PNG frames (f_0001.png ...).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
timing = json.load(open(os.path.join(HERE, "renders", "timing.json")))
fps, lead, clips = timing["fps"], timing["lead"], timing["clips"]

picture, out = sys.argv[1], sys.argv[2]
if os.path.isdir(picture):
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(picture, "f_%04d.png")]
    vcodec = ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p"]
else:
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", picture]
    vcodec = ["-c:v", "copy"]
filters, labels = [], []
for i, c in enumerate(clips):
    cmd += ["-i", c["wav"]]
    ms = int(((c["first"] - 1) / fps + lead) * 1000)
    filters.append(f"[{i + 1}:a]adelay={ms}|{ms}[a{i}]")
    labels.append(f"[a{i}]")
filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,apad[aout]")
cmd += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]", *vcodec,
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print("wrote", out)
