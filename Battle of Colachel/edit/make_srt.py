"""Build the English subtitle file (SRT) from the narration text and the real clip timings.

  python make_srt.py            # writes edit/Battle_of_Colachel.srt
Each beat's text is split into sentences, and the speech time (the clip minus the 0.8 s lead and a short tail) is shared
between the sentences by their length. Upload it in YouTube Studio > Subtitles > Upload file (With timing), then watch
once and nudge anything that drifts. INTRO must match the title card length used in make_overlays.py.
"""
import os, re
from clip_timeline import beat_starts, narration, LEAD
INTRO = 5.0
start, dur = beat_starts(INTRO)
text = narration()
HERE = os.path.dirname(os.path.abspath(__file__))


def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def chunks(sentence, limit=84):
    """Split a long sentence at commas / 'and' so a caption stays on at most two short lines."""
    if len(sentence) <= limit:
        return [sentence]
    parts = re.split(r"(?<=,)\s+", sentence)
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > limit:
            out.append(cur); cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        out.append(cur)
    return out


def wrap(line, width=42):
    if len(line) <= width:
        return line
    cut = line.rfind(" ", 0, width + 6)
    return line[:cut] + "\n" + line[cut + 1:]


cues = []
for n in range(1, 70):
    t = text.get(f"S{n:02d}", "").strip()
    if not t:
        continue
    sents = [s for s in re.split(r"(?<=[.!?])\s+", t) if s]
    pieces = [c for s in sents for c in chunks(s)]
    speech = dur[n] - LEAD - 1.0
    total = sum(len(p) for p in pieces)
    tt = start[n] + LEAD
    for p in pieces:
        d = speech * len(p) / total
        cues.append((tt + 0.05, tt + d - 0.05, wrap(p)))
        tt += d
with open(os.path.join(HERE, "Battle_of_Colachel.srt"), "w", encoding="utf-8") as f:
    for i, (a, b, p) in enumerate(cues, 1):
        f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{p}\n\n")
print(len(cues), "captions ->", os.path.join(HERE, "Battle_of_Colachel.srt"))
