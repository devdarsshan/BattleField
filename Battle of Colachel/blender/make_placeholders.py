"""Temporary narration for beats that have no Gemini recording yet: the Windows voice
reads the line, stretched or squeezed to the estimated length film.py used, so the
review cut has words in the right places. Real takes replace these automatically.

  python make_placeholders.py [TIMING.json]   (default renders/timing.json, written by film.py)
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "..", "audio")
import sys
timing_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "renders", "timing.json")
timing = json.load(open(timing_path))
lines = dict(l.strip().split("|", 1) for l in open(os.path.join(AUDIO, "lines.txt"), encoding="utf8") if "|" in l)
os.makedirs(os.path.join(AUDIO, "placeholder"), exist_ok=True)

for c in timing["clips"]:
    if not c["placeholder"]:
        continue
    out = c["wav"]
    raw = out.replace(".wav", "_raw.wav")
    text = lines[c["beat"]].replace("'", "''")
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          "$s.SelectVoice('Microsoft David Desktop'); $s.Rate = -1; "
          f"$s.SetOutputToWaveFile('{raw}'); $s.Speak('{text}'); $s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw],
                               capture_output=True, text=True).stdout)
    tempo = max(0.5, min(2.0, dur / c["seconds"]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", f"atempo={tempo:.4f},loudnorm=I=-16:TP=-1.5",
                    "-ar", "48000", "-ac", "2", out], check=True)
    os.remove(raw)
    print(f"{c['beat']}: placeholder {dur:.1f}s -> {c['seconds']:.1f}s")
