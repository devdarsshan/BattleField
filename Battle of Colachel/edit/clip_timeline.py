"""Where every beat starts in the merged film, from the real clip lengths (blender/renders/timing*.json)."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = os.path.join(ROOT, "blender", "renders")
LEAD = 0.8                      # narration starts this far into each clip


def load_clips():
    dur, wav = {}, {}
    for f in sorted(os.listdir(R)):
        if f.startswith("timing") and f.endswith(".json"):
            d = json.load(open(os.path.join(R, f)))
            for c in d["clips"]:
                n = int(c["beat"][1:])
                if f == "timing.json" and n > 6:
                    continue
                dur[n] = (c["last"] - c["first"] + 1) / d["fps"]
                wav[n] = c
    return dur, wav


def beat_starts(intro=0.0):
    dur, _ = load_clips()
    t, start = intro, {}
    for n in range(1, 70):
        start[n] = t
        t += dur[n]
    return start, dur


def narration():
    out = {}
    for line in open(os.path.join(ROOT, "audio", "lines.txt"), encoding="utf-8"):
        if "|" in line:
            b, t = line.rstrip("\n").split("|", 1)
            out[b] = t
    return out


def word_time(beat, phrase, start, dur):
    """Film time (s) at which `phrase` starts being spoken in `beat` (proportional to characters over the audio length)."""
    text = narration()[beat]
    i = text.find(phrase)
    if i < 0:
        raise ValueError(f"{phrase!r} not in {beat}")
    n = int(beat[1:])
    speech = dur[n] - LEAD - 1.0
    return start[n] + LEAD + speech * i / max(1, len(text))
