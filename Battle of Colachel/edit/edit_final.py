"""Assemble the final film: title card + all clips + overlays + fades + loudness, one ffmpeg run.

  python edit_final.py MERGED.mp4 OUT.mp4 [--preview 120]      # preview = only the first N seconds (quick check)
MERGED.mp4 is the output of colab/merge_clips.py (all 69 clips, 1920x1080, 24 fps). Run make_overlays.py first.
Timing of every plate / label comes from overlays.json (edit PLATES / LABELS in make_overlays.py to change them).
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
merged, out = args[0], args[1]
preview = None
if "--preview" in sys.argv:
    preview = float(sys.argv[sys.argv.index("--preview") + 1]); args = [a for a in args if a != str(int(preview))]
ov = json.load(open(os.path.join(HERE, "overlays.json")))
intro = ov["intro_seconds"]
items = ov["overlays"]
inputs = ["-loop", "1", "-framerate", "24", "-t", str(intro), "-i", os.path.join(HERE, "title_card.png"),
          "-f", "lavfi", "-t", str(intro), "-i", "anullsrc=r=48000:cl=stereo", "-i", merged]
for it in items:
    inputs += ["-loop", "1", "-framerate", "24", "-t", str(it["t1"] - it["t0"]), "-i", os.path.join(HERE, it["file"])]
f = ["[0:v]scale=1920:1080,format=yuv420p,fade=in:st=0:d=1,fade=out:st=%.2f:d=1[tc]" % (intro - 1),
     "[2:v]scale=1920:1080,format=yuv420p[film]", "[tc][1:a][film][2:a]concat=n=2:v=1:a=1[v0][a0]"]
last = "v0"
for i, it in enumerate(items):
    n = 3 + i
    d = it["t1"] - it["t0"]
    f.append(f"[{n}:v]format=rgba,fade=in:st=0:d=0.6:alpha=1,fade=out:st={d - 0.6:.2f}:d=0.6:alpha=1,setpts=PTS+{it['t0']}/TB[o{i}]")
    f.append(f"[{last}][o{i}]overlay=0:0:eof_action=pass:enable='between(t,{it['t0']:.2f},{it['t1']:.2f})'[v{i + 1}]")
    last = f"v{i + 1}"
f.append(f"[{last}]fade=out:st=END_FADE:d=2[vout]")
f.append("[a0]loudnorm=I=-14:TP=-1.5:LRA=11,afade=out:st=END_FADE:d=2[aout]")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", merged], text=True)) + intro
graph = ";".join(f).replace("END_FADE", f"{dur - 2:.2f}")
cmd = ["ffmpeg", "-y", "-v", "error", "-stats"] + inputs + ["-filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "medium", "-b:v", "16M", "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "aac", "-b:a", "192k"]
if preview:
    cmd += ["-t", str(preview)]
subprocess.run(cmd + [out], check=True)
print("wrote", out)
