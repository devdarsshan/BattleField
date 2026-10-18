"""Join the finished clip MP4s of all batches into one film, in beat order (S01, S02, ... S69).

  python merge_clips.py FOLDER_WITH_MP4S OUT.mp4
File names look like clip53_S44_1080p.mp4; the Sxx in the name sets the order. All clips must share resolution, fps (24)
and codec (they do when rendered with render_local.py or the Colab engine at the same quality).
"""
import os, re, subprocess, sys
src, out = sys.argv[1], sys.argv[2]
clips = []
for f in os.listdir(src):
    m = re.search(r"_S(\d+)_", f)
    if f.endswith(".mp4") and m and "bench" not in f:
        clips.append((int(m.group(1)), f))
clips.sort()
lst = os.path.join(src, "_concat.txt")
with open(lst, "w") as fh:
    for _, f in clips:
        fh.write("file '" + os.path.join(src, f).replace("\\", "/") + "'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
print(f"{len(clips)} clips -> {out}; beats {clips[0][0]}..{clips[-1][0]}")
