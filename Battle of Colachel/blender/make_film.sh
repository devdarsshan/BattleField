#!/usr/bin/env bash
# One-shot film job: record any missing narration (retrying until Google's daily
# free quota allows it), rebuild the timeline from the narration lengths, render
# PNG frames at 1080p (resumable), then encode the mp4 with the narration.
#
#   bash make_film.sh [VOICE] [OUT_NAME]
set -u
VOICE="${1:-Algieba}"
OUT="${2:-Colachel_clips01-04_1080p}"
cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
AUDIO="../audio"
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
RENDERS="$(cygpath -w "$PWD")\\renders"
log() { echo "[$(date '+%H:%M')] $*"; }

# 1. narration (one request per beat; 429 = quota used up, so wait and retry)
while IFS='|' read -r beat text; do
  [ -z "$beat" ] && continue
  until [ -f "$AUDIO/$beat.wav" ]; do
    if python "$ROOT/_tools/tts.py" "$AUDIO/$beat.wav" "$text" --voice "$VOICE" 2>/tmp/tts_err.txt; then
      log "recorded $beat"; sleep 25   # stay under the per-minute limit
    elif grep -q "429" /tmp/tts_err.txt; then
      log "voice quota used up; retrying $beat in 30 min"; sleep 1800
    else
      log "TTS failed for $beat:"; head -c 400 /tmp/tts_err.txt; exit 1
    fi
  done
done < "$AUDIO/lines.txt"

# 2. rebuild the timeline (clip lengths follow the narration)
"$BLENDER" -b -P film.py 2>&1 | grep -E "film built|  clip |Error|Traceback"

# 3. render 1080p frames (skips frames already on disk)
log "rendering frames"
"$BLENDER" -b Colachel.blend -P render_cli.py -- frames "$RENDERS\\frames_1080p" --res 1920x1080 \
  2>&1 | grep -E "Error|Traceback" | tail -5
log "frames done"

# 4. encode with narration
python make_video.py "renders/frames_1080p" "renders/$OUT.mp4" && log "wrote renders/$OUT.mp4"
