$ErrorActionPreference = "Stop"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$startTime = Get-Date

Write-Host "=========================================================="
Write-Host "Starting Beat S12 (Clips 16-17) 720p Review Render"
Write-Host "Start Time: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "GPU: NVIDIA GeForce GTX 1050 Ti"
Write-Host "Target frames: 1 to 554 (554 frames total)"
Write-Host "=========================================================="

$blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$renders = "E:\BattleField\Battle of Colachel\blender\renders"
$framesDir = "$renders\frames_kochi_720p"

if (-not (Test-Path $framesDir)) {
    New-Item -ItemType Directory -Path $framesDir -Force | Out-Null
}

Write-Host "[1/3] Rendering 554 frames at 1280x720 (24 samples)..."
& $blender -b "E:\BattleField\Battle of Colachel\blender\Kochi.blend" --python-expr "import bpy; bpy.context.scene.eevee.taa_render_samples=24" -P "E:\BattleField\Battle of Colachel\blender\render_cli.py" -- frames "$framesDir" --res 1280x720

$renderTime = $sw.Elapsed
$frameCount = (Get-ChildItem -Path $framesDir -Filter "f_*.png").Count

Write-Host "[2/3] Frame render completed in $([Math]::Round($renderTime.TotalMinutes, 2)) min ($([Math]::Round($renderTime.TotalSeconds, 1))s total)."
Write-Host "Rendered frames: $frameCount. Average speed: $([Math]::Round($renderTime.TotalSeconds / $frameCount, 3)) s/frame."

# Verification / cleanup check
$corrupt = Get-ChildItem -Path $framesDir -Filter "f_*.png" | Where-Object { $_.Length -lt 2048 }
if ($corrupt) {
    Write-Warning "Found corrupt/empty frames, removing..."
    $corrupt | Remove-Item -Force
}

Write-Host "[3/3] Encoding video with narration (S12.wav)..."
$audio = "E:\BattleField\Battle of Colachel\audio\placeholder\S12.wav"
$outMp4 = "$renders\clip16-17_S12_review_720p.mp4"

ffmpeg -y -framerate 24 -start_number 1 -i "$framesDir\f_%04d.png" -i "$audio" -filter_complex "[0:v]trim=end_frame=554,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest "$outMp4"

$sw.Stop()
$endTime = Get-Date

Write-Host "=========================================================="
Write-Host "DONE: Review video successfully generated!"
Write-Host "Output: $outMp4"
Write-Host "End Time: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "Total Job Duration: $([Math]::Round($sw.Elapsed.TotalMinutes, 2)) minutes ($([Math]::Round($sw.Elapsed.TotalSeconds, 1))s)."
Write-Host "=========================================================="
