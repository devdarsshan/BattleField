"""Gemini text-to-speech, the same call Flow MCP's flow_narrate makes (use it when that
tool can't reach Google). The key is read from ~/.flow-mcp/gemini-key and never printed.

  python tts.py OUT.wav "Line to speak" [--voice Charon] [--style "calm documentary narrator"]
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

MODEL = os.environ.get("FLOW_MCP_GEMINI_TTS", "gemini-2.5-flash-preview-tts")

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("text")
ap.add_argument("--voice", default="Charon")
ap.add_argument("--style", default="Calm, clear documentary narrator, unhurried, short pauses between sentences.")
a = ap.parse_args()

key = open(os.path.expanduser("~/.flow-mcp/gemini-key"), encoding="utf8").read().strip()
body = json.dumps({
    "contents": [{"parts": [{"text": f"Say {a.style}: {a.text}" if a.style else a.text}]}],
    "generationConfig": {"responseModalities": ["AUDIO"],
                         "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": a.voice}}}},
}).encode()
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
    data=body, headers={"content-type": "application/json", "x-goog-api-key": key})
try:
    resp = json.load(urllib.request.urlopen(req, timeout=120))
except urllib.error.HTTPError as e:
    sys.exit(f"Gemini TTS refused ({e.code}): {e.read().decode()[:2500]}")

part = next(p for p in resp["candidates"][0]["content"]["parts"] if p.get("inlineData", {}).get("data"))
mime = part["inlineData"].get("mimeType", "")
rate = mime.split("rate=")[1].split(";")[0] if "rate=" in mime else "24000"
raw = os.path.splitext(a.out)[0] + ".pcm"
with open(raw, "wb") as f:
    f.write(base64.b64decode(part["inlineData"]["data"]))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", rate, "-ac", "1", "-i", raw,
                "-af", "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", a.out],
               check=True)
os.remove(raw)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.out],
                     capture_output=True, text=True).stdout.strip()
print(f"{a.out} {dur}s")
