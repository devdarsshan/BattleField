$ErrorActionPreference = "Stop"
$blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$renders = "E:\BattleField\Battle of Colachel\blender\renders"
$audioDir = "E:\BattleField\Battle of Colachel\audio\placeholder"

Write-Host "=========================================================="
Write-Host "Master Pipeline: S15 -> S16 -> S17 -> S18"
Write-Host "=========================================================="

# 1. Wait for S14 to complete
$s14Mp4 = "$renders\clip19_S14_review_720p.mp4"
Write-Host "Waiting for S14 ($s14Mp4) to complete..."
while (-not (Test-Path $s14Mp4)) {
    Start-Sleep -Seconds 10
}
Write-Host "Found S14 output! Proceeding with S15..."

# 2. Build Palace15.blend and render S15
Write-Host "`n>>> [STEP 1/4] Building Palace15.blend & Rendering Beat S15..."
& $blender -b -P "E:\BattleField\Battle of Colachel\blender\palace15_film.py"

$s15Frames = "$renders\frames_palace15_720p"
if (-not (Test-Path $s15Frames)) { New-Item -ItemType Directory -Path $s15Frames -Force | Out-Null }

& $blender -b "E:\BattleField\Battle of Colachel\blender\Palace15.blend" --python-expr "import bpy; bpy.context.scene.eevee.taa_render_samples=24" -P "E:\BattleField\Battle of Colachel\blender\render_cli.py" -- frames "$s15Frames" --range 1 350 --res 1280x720

Get-ChildItem -Path $s15Frames -Filter "f_*.png" | Where-Object { $_.Length -lt 2048 } | Remove-Item -Force
$s15Audio = "$audioDir\S15.wav"
$s15Mp4 = "$renders\clip20_S15_review_720p.mp4"
ffmpeg -y -framerate 24 -start_number 1 -i "$s15Frames\f_%04d.png" -i "$s15Audio" -filter_complex "[0:v]trim=end_frame=350,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest "$s15Mp4"
Write-Host "SUCCESS: S15 review video created: $s15Mp4"

# 3. Render S16 (Map)
Write-Host "`n>>> [STEP 2/4] Rendering Beat S16 (Map, frames 1554-1877)..."
$mapFrames = "$renders\frames_map_720p"
& $blender -b "E:\BattleField\Battle of Colachel\blender\Map.blend" --python-expr "import bpy; bpy.context.scene.eevee.taa_render_samples=24" -P "E:\BattleField\Battle of Colachel\blender\render_cli.py" -- frames "$mapFrames" --range 1554 1877 --res 1280x720

Get-ChildItem -Path $mapFrames -Filter "f_*.png" | Where-Object { $_.Length -lt 2048 } | Remove-Item -Force
$s16Audio = "$audioDir\S16.wav"
$s16Mp4 = "$renders\clip21-22_S16_review_720p.mp4"
ffmpeg -y -framerate 24 -start_number 1554 -i "$mapFrames\f_%04d.png" -i "$s16Audio" -filter_complex "[0:v]trim=end_frame=324,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest "$s16Mp4"
Write-Host "SUCCESS: S16 review video created: $s16Mp4"

# 4. Render S17 (Port)
Write-Host "`n>>> [STEP 3/4] Rendering Beat S17 (English Port, frames 1-508)..."
$portFrames = "$renders\frames_port_720p"
if (-not (Test-Path $portFrames)) { New-Item -ItemType Directory -Path $portFrames -Force | Out-Null }

& $blender -b "E:\BattleField\Battle of Colachel\blender\Port.blend" --python-expr "import bpy; bpy.context.scene.eevee.taa_render_samples=24" -P "E:\BattleField\Battle of Colachel\blender\render_cli.py" -- frames "$portFrames" --range 1 508 --res 1280x720

Get-ChildItem -Path $portFrames -Filter "f_*.png" | Where-Object { $_.Length -lt 2048 } | Remove-Item -Force
$s17Audio = "$audioDir\S17.wav"
$s17Mp4 = "$renders\clip23_S17_review_720p.mp4"
ffmpeg -y -framerate 24 -start_number 1 -i "$portFrames\f_%04d.png" -i "$s17Audio" -filter_complex "[0:v]trim=end_frame=508,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest "$s17Mp4"
Write-Host "SUCCESS: S17 review video created: $s17Mp4"

# 5. Render S18 (Map)
Write-Host "`n>>> [STEP 4/4] Rendering Beat S18 (Map, frames 1878-2117)..."
& $blender -b "E:\BattleField\Battle of Colachel\blender\Map.blend" --python-expr "import bpy; bpy.context.scene.eevee.taa_render_samples=24" -P "E:\BattleField\Battle of Colachel\blender\render_cli.py" -- frames "$mapFrames" --range 1878 2117 --res 1280x720

Get-ChildItem -Path $mapFrames -Filter "f_*.png" | Where-Object { $_.Length -lt 2048 } | Remove-Item -Force
$s18Audio = "$audioDir\S18.wav"
$s18Mp4 = "$renders\clip24_S18_review_720p.mp4"
ffmpeg -y -framerate 24 -start_number 1878 -i "$mapFrames\f_%04d.png" -i "$s18Audio" -filter_complex "[0:v]trim=end_frame=240,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest "$s18Mp4"
Write-Host "SUCCESS: S18 review video created: $s18Mp4"

Write-Host "`n=========================================================="
Write-Host "ALL SCENES TILL S18 COMPLETED SUCCESSFULLY!"
Write-Host "=========================================================="
