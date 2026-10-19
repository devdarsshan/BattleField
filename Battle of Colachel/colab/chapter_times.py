"""Print YouTube chapter timestamps for the merged film, from the real clip lengths.

  python chapter_times.py [extra_seconds_before_S01]
Clips are joined back to back in beat order (merge_clips.py), so a chapter starts at the sum of the earlier clip lengths.
Add an intro length (title card) as the argument if you put one before S01.
"""
import json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = os.path.join(ROOT, "blender", "renders")
dur = {}
for f in os.listdir(R):
    if f.startswith("timing") and f.endswith(".json"):
        d = json.load(open(os.path.join(R, f)))
        for c in d["clips"]:
            n = int(c["beat"][1:])
            if f == "timing.json" and n > 6:        # S07+ come from their own scene files
                continue
            dur[n] = (c["last"] - c["first"] + 1) / d["fps"]
offset = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
script = open(os.path.join(ROOT, "Colachel_Script.md"), encoding="utf-8").read()
names = {"HOOK": "The beach at Colachel", "THE PEPPER COAST": "The pepper coast", "THE KING WHO GREW": "The king who grew",
         "THE THREAT": "The threat", "THE FIRST ROUND": "The first round", "THE LANDING": "The landing",
         "THE KING COMES HOME": "The king comes home", "THE FISHERMEN": "The fishermen", "ONE SHOT": "One shot",
         "THE PRISONER WHO STAYED": "The prisoner who stayed", "THE END OF THE DUTCH PLAN": "The end of the Dutch plan", "ENDING": "Why the Dutch lost"}
marks = []
for m in re.finditer(r"^## (?:SEGMENT \d+: )?(.+?)\s*$", script, re.M):
    title = m.group(1).strip()
    if title.startswith("END-SCREEN") or title not in names:
        continue
    b = re.search(r"\[S(\d+)\]", script[m.end():])
    marks.append((int(b.group(1)), names[title]))
missing = [n for n in range(1, 70) if n not in dur]
if missing:
    print("WARNING: no timing for beats", missing)
t = offset
start = {}
for n in range(1, 70):
    start[n] = t
    t += dur.get(n, 0.0)
def fmt(s):
    s = int(round(s)); return f"{s // 60}:{s % 60:02d}"
print("CHAPTERS (paste into the description)")
for i, (n, name) in enumerate(marks):
    print(fmt(0 if i == 0 else start[n]), name)      # YouTube needs the first chapter at 0:00 (it covers the title card)
print(f"\nTotal length: {fmt(t)} ({t / 60:.1f} min); S69 end-screen clip starts at {fmt(start[69])}")
