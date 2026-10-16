$ErrorActionPreference = "Stop"
$blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$renders = "E:\BattleField\Battle of Colachel\blender\renders"
$audioDir = "E:\BattleField\Battle of Colachel\audio"
$blenderDir = "E:\BattleField\Battle of Colachel\blender"
$tempFrames = "$renders\frames_S19_720p"
$audioFile = "$audioDir\S19.wav"
$OutputMp4 = "$renders\clip25_S19_review_720p.mp4"

Write-Host ">>> [S19 Resume] Checking frames in $tempFrames..."
$existing = (Get-ChildItem -Path $tempFrames -Filter "f_*.png" -ErrorAction SilentlyContinue).Count
Write-Host ">>> Existing valid frames: $existing / 339"

Write-Host ">>> [S19 Resume] Rendering remaining frames with Thermal Guard..."
& $blender -b "$blenderDir\Map.blend" --python-expr "import bpy; sc=bpy.context.scene; sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100; sc.eevee.taa_render_samples=24" -P "$blenderDir\render_cli.py" -- frames "$tempFrames" --range 2118 2456 --res 1280x720

$frameCount = 2456 - 2118 + 1
Write-Host ">>> [S19 Resume] Multiplexing video with narration..."
ffmpeg -y -framerate 24 -start_number 2118 -i "$tempFrames\f_%04d.png" -i "$audioFile" -filter_complex "[0:v]trim=end_frame=$frameCount,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest "$OutputMp4"

if ((Test-Path $OutputMp4) -and ((Get-Item $OutputMp4).Length -gt 102400)) {
    Remove-Item -Path $tempFrames -Recurse -Force | Out-Null
    Write-Host ">>> [S19 SUCCESS] Created $OutputMp4 (Size: $((Get-Item $OutputMp4).Length) bytes)"
} else {
    Write-Error ">>> Encoding check failed for $OutputMp4!"
}
