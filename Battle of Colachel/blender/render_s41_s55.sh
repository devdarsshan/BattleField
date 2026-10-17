#!/bin/bash
# 720p review render of S41-S55 (Siege 263-2697, Surrender 1-2072, Udayagiri 1-240), then review videos per beat.
cd "$(dirname "$0")"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
R="$(cygpath -w "$PWD")\renders"
S24="import bpy; bpy.context.scene.eevee.taa_render_samples=24"
"$B" -b Siege.blend --python-expr "$S24" -P render_cli.py -- frames "$R\frames_siege_720p" --range 263 2697 --res 1280x720
"$B" -b Surrender.blend --python-expr "$S24" -P render_cli.py -- frames "$R\frames_surrender_720p" --range 1 2072 --res 1280x720
"$B" -b Udayagiri.blend --python-expr "$S24" -P render_cli.py -- frames "$R\frames_uday_720p" --range 1 240 --res 1280x720
find renders/frames_siege_720p renders/frames_surrender_720p renders/frames_uday_720p -size -2k -name '*.png' -delete
python encode_beats.py
echo ALL_DONE
