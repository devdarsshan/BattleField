"""Join finished clip MP4s found in a folder AND its sub-folders into one film, in beat order.
Clips whose video is not H.264 (for example the old mpeg4 "review" encodes) are re-encoded to H.264 first so the join can copy.

  python merge_nested.py OUTPUT_FOLDER OUT.mp4 [--max-beat 60]
"""
import os
import re
import subprocess
import sys

src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
max_beat = int(sys.argv[sys.argv.index("--max-beat") + 1]) if "--max-beat" in sys.argv else 999
tmp = os.path.join(src, "_h264")
clips = {}
for d, _, fs in os.walk(src):
    if os.path.basename(d) == "_h264":
        continue
    for f in fs:
        m = re.search(r"_S(\d+)_", f)
        if f.endswith(".mp4") and m and "bench" not in f and int(m.group(1)) <= max_beat:
            clips.setdefault(int(m.group(1)), []).append(os.path.join(d, f))
dups = {k: v for k, v in clips.items() if len(v) > 1}
if dups:
    sys.exit(f"more than one file for a beat: {dups}")
lines = []
for n in sorted(clips):
    p = clips[n][0]
    codec = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name",
                                     "-of", "csv=p=0", p], text=True).strip()
    if codec != "h264":
        os.makedirs(tmp, exist_ok=True)
        q = os.path.join(tmp, f"S{n:02d}.mp4")
        if not os.path.exists(q):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p",
                            "-r", "24", "-c:a", "copy", q], check=True)
        p = q
    lines.append("file '" + p.replace("\\", "/") + "'")
lst = os.path.join(src, "_concat.txt")
open(lst, "w").write("\n".join(lines) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
print(f"{len(clips)} clips -> {out}; beats {min(clips)}..{max(clips)}")
