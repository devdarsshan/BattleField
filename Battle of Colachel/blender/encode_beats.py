"""Review videos for S41-S55: picture frames + narration (0.8 s lead) per beat -> renders/review_S41.mp4 ..."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "renders")
SETS = (("timing_siege.json", "frames_siege_720p", range(41, 49)), ("timing_surrender.json", "frames_surrender_720p", range(49, 55)),
        ("timing_udayagiri.json", "frames_uday_720p", range(55, 56)))
for tj, fd, beats in SETS:
    d = json.load(open(os.path.join(R, tj)))
    for c in d["clips"]:
        n = int(c["beat"][1:])
        if n not in beats:
            continue
        out = os.path.join(R, f"review_{c['beat']}_720p.mp4")
        sec = (c["last"] - c["first"] + 1) / d["fps"]
        ms = int(d["lead"] * 1000)
        cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(d["fps"]), "-start_number", str(c["first"]), "-i", os.path.join(R, fd, "f_%04d.png"),
               "-i", c["wav"], "-filter_complex", f"[1:a]adelay={ms}|{ms},apad[a]", "-map", "0:v", "-map", "[a]", "-frames:v", str(c["last"] - c["first"] + 1),
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-t", f"{sec:.2f}", out]
        subprocess.run(cmd, check=True)
        print("wrote", out)
