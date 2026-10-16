"""Temporary DEVICE voice (Windows speech) for beats that have no final recording yet.

Voice files are kept strictly apart so the final edit can tell them apart:
  audio/Sxx.wav              FINAL voice (Gemini TTS, Algieba). Film scripts take the clip length from it.
  audio/placeholder/Sxx.wav  DEVICE voice (Windows "David"), stretched to the text-estimated clip timing,
                             used only until the final voice is recorded.
  audio/VOICES.md            which beat has which voice (this script updates it).

  python device_voice.py S29 S30 ... S38      (beats must be in audio/lines.txt)

The stretch target is film.py's estimate (characters / 12.5 + 0.3 s), the same number every film script uses
for a beat without a final recording, so picture timing and device voice always agree.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "..", "audio")
PH = os.path.join(AUDIO, "placeholder")
CHARS_PER_SEC = 12.5
os.makedirs(PH, exist_ok=True)
lines = dict(l.strip().split("|", 1) for l in open(os.path.join(AUDIO, "lines.txt"), encoding="utf8") if "|" in l)


def estimate(text):
    return len(text) / CHARS_PER_SEC + 0.3


for beat in sys.argv[1:]:
    text = lines[beat]
    out = os.path.join(PH, f"{beat}.wav")
    raw = out.replace(".wav", "_raw.wav")
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          "$s.SelectVoice('Microsoft David Desktop'); $s.Rate = -1; "
          f"$s.SetOutputToWaveFile('{raw}'); $s.Speak('{text.replace(chr(39), chr(39) * 2)}'); $s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw],
                               capture_output=True, text=True).stdout)
    target = estimate(text)
    tempo = max(0.5, min(2.0, dur / target))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", f"atempo={tempo:.4f},loudnorm=I=-16:TP=-1.5",
                    "-ar", "48000", "-ac", "2", out], check=True)
    os.remove(raw)
    print(f"{beat}: device voice {dur:.1f}s -> {target:.1f}s")

# rewrite the voice register
rows = []
for beat in sorted(lines, key=lambda b: int(b[1:])):
    final = os.path.exists(os.path.join(AUDIO, f"{beat}.wav"))
    device = os.path.exists(os.path.join(PH, f"{beat}.wav"))
    if final and int(beat[1:]) <= 4:
        kind = "FINAL? old Charon voice (re-record in Algieba at the end)"
    elif final:
        kind = "FINAL (Algieba)"
    elif device:
        kind = "DEVICE (Windows, temporary)"
    else:
        kind = "none"
    rows.append(f"| {beat} | {kind} |")
open(os.path.join(AUDIO, "VOICES.md"), "w", encoding="utf8").write(
    "# Voice register\n\n`audio/Sxx.wav` = final voice. `audio/placeholder/Sxx.wav` = temporary device voice.\n"
    "At the end, every beat must be FINAL (Algieba); re-record and re-time the rest.\n\n"
    "| Beat | Voice in use |\n|---|---|\n" + "\n".join(rows) + "\n")
print("wrote audio/VOICES.md")
