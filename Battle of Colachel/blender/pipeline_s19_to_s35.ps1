$ErrorActionPreference = "Stop"
$blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$renders = "E:\BattleField\Battle of Colachel\blender\renders"
$audioDir = "E:\BattleField\Battle of Colachel\audio"
$blenderDir = "E:\BattleField\Battle of Colachel\blender"

Write-Host "=========================================================="
Write-Host "Master Pipeline: S19 -> S38 (GPU Review Render)"
Write-Host "Thermal Guard: Max 90C | Cooldown 80C | Frame Breather 0.05s"
Write-Host "=========================================================="

if (-not (Test-Path $renders)) { New-Item -ItemType Directory -Path $renders -Force | Out-Null }

function Render-ReviewClip {
    param (
        [string]$ClipName,
        [string]$Beat,
        [string]$BlendFile,
        [int]$StartFrame,
        [int]$EndFrame,
        [string]$OutputMp4
    )

    if (Test-Path $OutputMp4) {
        Write-Host "`n>>> Clip already exists: $OutputMp4 (Skipping)"
        return
    }

    $frameCount = $EndFrame - $StartFrame + 1
    $audioFile = "$audioDir\$Beat.wav"
    if (-not (Test-Path $audioFile)) {
        $audioFile = "$audioDir\placeholder\$Beat.wav"
    }

    Write-Host "`n>>> [START] Rendering $ClipName ($Beat): Frames $StartFrame-$EndFrame ($frameCount frames) from $BlendFile..."
    $tempFrames = "$renders\frames_${Beat}_720p"
    if (-not (Test-Path $tempFrames)) {
        New-Item -ItemType Directory -Path $tempFrames -Force | Out-Null
    }
    # Clean incomplete frames (< 2KB) from an interrupted run so Blender can resume
    Get-ChildItem -Path $tempFrames -Filter "f_*.png" -ErrorAction SilentlyContinue | Where-Object { $_.Length -lt 2048 } | Remove-Item -Force

    # Pre-render thermal check (allow up to 88C)
    try {
        $gpuTemp = [int](nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>$null)
        if ($gpuTemp -gt 88) {
            Write-Host ">>> GPU temperature is ${gpuTemp}C. Waiting 10s to cool down before starting $Beat..."
            Start-Sleep -Seconds 10
        }
    } catch {}

    # Render PNG sequence at 720p, 24 samples with 90C thermal guard
    & $blender -b "$blenderDir\$BlendFile" --python-expr "import bpy; sc=bpy.context.scene; sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100; sc.eevee.taa_render_samples=24" -P "$blenderDir\render_cli.py" -- frames "$tempFrames" --range $StartFrame $EndFrame --res 1280x720 --max-temp 90 --cooldown-temp 80 --pause 0.05

    # Clean any incomplete frames
    Get-ChildItem -Path $tempFrames -Filter "f_*.png" | Where-Object { $_.Length -lt 2048 } | Remove-Item -Force

    # Multiplex with narration audio using ffmpeg
    Write-Host ">>> Multiplexing video and narration for $Beat..."
    ffmpeg -y -framerate 24 -start_number $StartFrame -i "$tempFrames\f_%04d.png" -i "$audioFile" -filter_complex "[0:v]trim=end_frame=$frameCount,setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac -shortest "$OutputMp4"

    # Verify output video before removing temporary PNG sequence
    if ((Test-Path $OutputMp4) -and ((Get-Item $OutputMp4).Length -gt 102400)) {
        Remove-Item -Path $tempFrames -Recurse -Force | Out-Null
        Write-Host ">>> [SUCCESS] Created $OutputMp4"
    } else {
        Write-Error "Encoding failed or output too small for $OutputMp4! Retaining frames in $tempFrames."
        return
    }

    # Inter-clip cooldown break
    Write-Host ">>> Quick breather (10s) before next beat..."
    Start-Sleep -Seconds 10
}

# --- BATCH 1: S19 to S28 (The Threat & The First Round) ---
Render-ReviewClip -ClipName "clip25_S19" -Beat "S19" -BlendFile "Map.blend" -StartFrame 2118 -EndFrame 2456 -OutputMp4 "$renders\clip25_S19_review_720p.mp4"
Render-ReviewClip -ClipName "clip26_S20" -Beat "S20" -BlendFile "Study.blend" -StartFrame 1 -EndFrame 331 -OutputMp4 "$renders\clip26_S20_review_720p.mp4"
Render-ReviewClip -ClipName "clip27_S21" -Beat "S21" -BlendFile "Meeting.blend" -StartFrame 1 -EndFrame 343 -OutputMp4 "$renders\clip27_S21_review_720p.mp4"
Render-ReviewClip -ClipName "clip28-29_S22" -Beat "S22" -BlendFile "Meeting.blend" -StartFrame 344 -EndFrame 950 -OutputMp4 "$renders\clip28-29_S22_review_720p.mp4"
Render-ReviewClip -ClipName "clip30_S23" -Beat "S23" -BlendFile "Meeting.blend" -StartFrame 951 -EndFrame 1258 -OutputMp4 "$renders\clip30_S23_review_720p.mp4"
Render-ReviewClip -ClipName "clip31_S24" -Beat "S24" -BlendFile "Map.blend" -StartFrame 2457 -EndFrame 2854 -OutputMp4 "$renders\clip31_S24_review_720p.mp4"
Render-ReviewClip -ClipName "clip32_S25" -Beat "S25" -BlendFile "Battle.blend" -StartFrame 1 -EndFrame 322 -OutputMp4 "$renders\clip32_S25_review_720p.mp4"
Render-ReviewClip -ClipName "clip33_S26" -Beat "S26" -BlendFile "Battle.blend" -StartFrame 323 -EndFrame 695 -OutputMp4 "$renders\clip33_S26_review_720p.mp4"
Render-ReviewClip -ClipName "clip34_S27" -Beat "S27" -BlendFile "Varkala.blend" -StartFrame 1 -EndFrame 465 -OutputMp4 "$renders\clip34_S27_review_720p.mp4"
Render-ReviewClip -ClipName "clip35_S28" -Beat "S28" -BlendFile "Map.blend" -StartFrame 2855 -EndFrame 3094 -OutputMp4 "$renders\clip35_S28_review_720p.mp4"

# --- BATCH 2: S29 to S35 (Reinforcements, Colachel Landing & Inland March) ---
Render-ReviewClip -ClipName "clip36_S29" -Beat "S29" -BlendFile "Map.blend" -StartFrame 3095 -EndFrame 3540 -OutputMp4 "$renders\clip36_S29_review_720p.mp4"
Render-ReviewClip -ClipName "clip37_S30" -Beat "S30" -BlendFile "Landing.blend" -StartFrame 1 -EndFrame 456 -OutputMp4 "$renders\clip37_S30_review_720p.mp4"
Render-ReviewClip -ClipName "clip38_S31" -Beat "S31" -BlendFile "Landing.blend" -StartFrame 457 -EndFrame 799 -OutputMp4 "$renders\clip38_S31_review_720p.mp4"
Render-ReviewClip -ClipName "clip39_S32" -Beat "S32" -BlendFile "Landing.blend" -StartFrame 800 -EndFrame 1192 -OutputMp4 "$renders\clip39_S32_review_720p.mp4"
Render-ReviewClip -ClipName "clip40_S33" -Beat "S33" -BlendFile "Inland.blend" -StartFrame 1 -EndFrame 408 -OutputMp4 "$renders\clip40_S33_review_720p.mp4"
Render-ReviewClip -ClipName "clip41_S34" -Beat "S34" -BlendFile "Landing.blend" -StartFrame 1193 -EndFrame 1556 -OutputMp4 "$renders\clip41_S34_review_720p.mp4"
Render-ReviewClip -ClipName "clip42-43_S35" -Beat "S35" -BlendFile "Inland.blend" -StartFrame 409 -EndFrame 943 -OutputMp4 "$renders\clip42-43_S35_review_720p.mp4"

# --- BATCH 3: S36 to S38 (Kalkulam Fort, Thiruvattar Temple & Beach Monsoon) ---
Render-ReviewClip -ClipName "clip44-45_S36" -Beat "S36" -BlendFile "Inland.blend" -StartFrame 944 -EndFrame 1255 -OutputMp4 "$renders\clip44-45_S36_review_720p.mp4"
Render-ReviewClip -ClipName "clip46_S37" -Beat "S37" -BlendFile "Inland.blend" -StartFrame 1256 -EndFrame 1696 -OutputMp4 "$renders\clip46_S37_review_720p.mp4"
Render-ReviewClip -ClipName "clip47_S38" -Beat "S38" -BlendFile "Landing.blend" -StartFrame 1557 -EndFrame 1997 -OutputMp4 "$renders\clip47_S38_review_720p.mp4"

Write-Host "`n=========================================================="
Write-Host "ALL REVIEW CLIPS S19-S38 COMPLETED SUCCESSFULLY!"
Write-Host "=========================================================="
