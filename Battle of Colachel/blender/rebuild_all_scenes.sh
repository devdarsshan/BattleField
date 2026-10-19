#!/bin/bash
# Rebuild every scene file after new narration is recorded (clip lengths follow the audio), so the timing_*.json files are current.
cd "$(dirname "$0")"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
for f in film pepper kochi palace palace15 port study meeting battle varkala map landing inland siege surrender udayagiri chapel treaty temple64 today; do
  echo "== $f"; "$B" -b -P ${f}_film.py 2>&1 | grep -i "Traceback\|error" -A4 | head -6
done
