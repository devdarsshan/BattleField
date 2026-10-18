"""Record a run of beats with Gemini TTS (Algieba), 25 s apart, stopping at the first quota refusal.
  python _tools/record_batch.py S41 S42 ... S50
"""
import os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(ROOT, "Battle of Colachel", "audio")
lines = dict(l.rstrip("\n").split("|", 1) for l in open(os.path.join(AUD, "lines.txt"), encoding="utf8") if "|" in l)
done = []
for b in sys.argv[1:]:
    out = os.path.join(AUD, b + ".wav")
    if os.path.exists(out):
        print(b, "already final, skipped", flush=True)
        continue
    r = subprocess.run([sys.executable, os.path.join(ROOT, "_tools", "tts.py"), out, lines[b], "--voice", "Algieba"], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        print(b, "FAILED:", (r.stderr or r.stdout)[:300].replace("\n", " "), flush=True)
        break
    print(b, "recorded", flush=True)
    done.append(b)
    time.sleep(25)
print("RECORDED:", done, flush=True)
