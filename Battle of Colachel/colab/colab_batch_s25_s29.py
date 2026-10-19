"""Automated batch renderer and MP4 multiplexer for S25 through S29 on Google Colab.
Renders each beat on Tesla T4 GPU (EEVEE 16 samples, 720p) and multiplexes with narration audio.
"""
import os
import sys
import time
import shutil
import subprocess

PROJECT_DIR = "/content/project"
OUTPUT_DIR = "/content/renders/mp4"
BLENDER_BIN = "/content/blender-5.2.2-linux-x64/blender"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "colab_render_cli.py")

os.makedirs(OUTPUT_DIR, exist_ok=True)

SHOTS = [
    {
        "clip": "clip32_S25",
        "beat": "S25",
        "blend": "Battle.blend",
        "start": 1,
        "end": 322,
        "audio": "S25.wav",
        "mp4": "clip32_S25_review_720p.mp4"
    },
    {
        "clip": "clip33_S26",
        "beat": "S26",
        "blend": "Battle.blend",
        "start": 323,
        "end": 695,
        "audio": "S26.wav",
        "mp4": "clip33_S26_review_720p.mp4"
    },
    {
        "clip": "clip34_S27",
        "beat": "S27",
        "blend": "Varkala.blend",
        "start": 1,
        "end": 465,
        "audio": "S27.wav",
        "mp4": "clip34_S27_review_720p.mp4"
    },
    {
        "clip": "clip35_S28",
        "beat": "S28",
        "blend": "Map.blend",
        "start": 2855,
        "end": 3094,
        "audio": "S28.wav",
        "mp4": "clip35_S28_review_720p.mp4"
    },
    {
        "clip": "clip36_S29",
        "beat": "S29",
        "blend": "Map.blend",
        "start": 3095,
        "end": 3540,
        "audio": "S29.wav",
        "mp4": "clip36_S29_review_720p.mp4"
    }
]

def render_and_multiplex_all():
    print("=" * 65, flush=True)
    print("🎬 Batch Pipeline: Rendering Review Clips S25 -> S29 (720p MP4)", flush=True)
    print("=" * 65, flush=True)
    
    total_start_time = time.time()
    completed_mp4s = []

    for idx, s in enumerate(SHOTS, 1):
        clip_name = s["clip"]
        beat = s["beat"]
        blend_file = os.path.join(PROJECT_DIR, s["blend"])
        start_f = s["start"]
        end_f = s["end"]
        frame_count = end_f - start_f + 1
        audio_file = os.path.join(PROJECT_DIR, s["audio"])
        output_mp4 = os.path.join(OUTPUT_DIR, s["mp4"])
        temp_frames_dir = f"/content/renders/frames_{beat}_720p"
        
        print(f"\n▶ [{idx}/{len(SHOTS)}] Processing {clip_name} ({beat}): Frames {start_f}..{end_f} ({frame_count} frames)...", flush=True)
        
        if not os.path.exists(blend_file):
            print(f"❌ Error: Cannot find blend file {blend_file}! Skipping.", flush=True)
            continue
            
        if not os.path.exists(audio_file):
            print(f"⚠️ Warning: Cannot find {audio_file}, checking without path...", flush=True)
            # Check root /content
            if os.path.exists(f"/content/{s['audio']}"):
                audio_file = f"/content/{s['audio']}"
            else:
                print(f"❌ Audio file {s['audio']} not found! Skipping multiplex.", flush=True)
                continue

        # Check if already rendered
        if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 102400:
            print(f"✓ {output_mp4} already exists ({os.path.getsize(output_mp4)} bytes). Skipping.", flush=True)
            completed_mp4s.append(output_mp4)
            continue

        os.makedirs(temp_frames_dir, exist_ok=True)
        t_shot_start = time.time()

        # Step A: Render PNG frames via EEVEE with Xvfb
        cmd_render = [
            "xvfb-run", "-a",
            BLENDER_BIN, "-b", blend_file,
            "-P", SCRIPT_PATH, "--",
            "frames", temp_frames_dir,
            "--range", str(start_f), str(end_f),
            "--engine", "EEVEE",
            "--samples", "16",
            "--res", "1280x720"
        ]
        
        print(f">>> Running Blender render...", flush=True)
        t_render_start = time.time()
        ret = subprocess.run(cmd_render)
        render_duration = time.time() - t_render_start

        if ret.returncode != 0:
            print(f"❌ Blender render failed for {beat} with code {ret.returncode}!", flush=True)
            continue

        # Step B: Multiplex frames and audio into MP4 with ffmpeg (auto-detects working codec)
        print(f">>> Multiplexing {frame_count} frames with narration audio ({audio_file})...", flush=True)
        t_mux_start = time.time()
        
        encoders_to_try = ["libx264", "h264_nvenc"]          # H.264 only, never mpeg4
        success_enc = None
        last_error = ""

        for enc in encoders_to_try:
            extra_opts = ["-crf", "18"] if enc == "libx264" else ["-cq", "18", "-b:v", "0"]
            cmd_ffmpeg = [
                "ffmpeg", "-y",
                "-framerate", "24",
                "-start_number", str(start_f),
                "-i", os.path.join(temp_frames_dir, "f_%04d.png"),
                "-i", audio_file,
                "-filter_complex", f"[0:v]trim=end_frame={frame_count},setpts=PTS-STARTPTS,format=yuv420p[v];[1:a]adelay=800|800,apad[a]",
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", enc
            ] + extra_opts + [
                "-c:a", "aac",
                "-shortest",
                output_mp4
            ]
            ret_ff = subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if ret_ff.returncode == 0:
                success_enc = enc
                break
            else:
                last_error = ret_ff.stderr.decode("utf-8", errors="ignore")[-400:].strip()

        mux_duration = time.time() - t_mux_start

        if not success_enc:
            print(f"❌ ffmpeg multiplexing failed with all encoders! Error:\n{last_error}", flush=True)
            continue

        # Step C: Verify MP4, record timings, and clean up raw frames
        if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 102400:
            total_clip_duration = time.time() - t_shot_start
            sec_per_frame = render_duration / frame_count if frame_count > 0 else 0
            fps = frame_count / render_duration if render_duration > 0 else 0
            size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
            
            print(f"✅ [SUCCESS] Created {s['mp4']} ({size_mb:.2f} MB)", flush=True)
            print(f"   ⏱️ Render: {render_duration:.1f}s ({sec_per_frame:.2f}s/frame | {fps:.2f} fps) | Mux: {mux_duration:.1f}s | Total: {total_clip_duration:.1f}s", flush=True)
            
            completed_mp4s.append({
                "clip": clip_name,
                "beat": beat,
                "blend": s["blend"],
                "start_frame": start_f,
                "end_frame": end_f,
                "frame_count": frame_count,
                "render_duration_sec": round(render_duration, 2),
                "sec_per_frame": round(sec_per_frame, 3),
                "fps": round(fps, 2),
                "mux_duration_sec": round(mux_duration, 2),
                "total_clip_duration_sec": round(total_clip_duration, 2),
                "mp4_file": s["mp4"],
                "mp4_size_mb": round(size_mb, 2)
            })
            
            # Remove heavy raw PNG frames to keep Colab disk lean
            shutil.rmtree(temp_frames_dir, ignore_errors=True)
        else:
            print(f"❌ Output file invalid or too small: {output_mp4}", flush=True)

    total_time = time.time() - total_start_time
    total_render_time = sum(c["render_duration_sec"] for c in completed_mp4s)
    total_mux_time = sum(c["mux_duration_sec"] for c in completed_mp4s)
    total_frames = sum(c["frame_count"] for c in completed_mp4s)
    avg_sec_per_frame = total_render_time / total_frames if total_frames > 0 else 0

    # 1. Save structured JSON timing file
    import json
    timing_json_path = os.path.join(OUTPUT_DIR, "timing_colab_s25_s29.json")
    timing_data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "environment": "Google Colab",
        "hardware": "NVIDIA Tesla T4 GPU",
        "resolution": "1280x720",
        "engine": "BLENDER_EEVEE (16 samples)",
        "total_batch_duration_sec": round(total_time, 2),
        "total_batch_duration_min": round(total_time / 60, 2),
        "total_render_duration_sec": round(total_render_duration, 2),
        "total_mux_duration_sec": round(total_mux_time, 2),
        "total_frames_rendered": total_frames,
        "avg_seconds_per_frame": round(avg_sec_per_frame, 3),
        "clips": completed_mp4s
    }
    with open(timing_json_path, "w", encoding="utf-8") as f:
        json.dump(timing_data, f, indent=2)
    print(f"\n✓ Saved JSON timings to: {timing_json_path}", flush=True)

    # 2. Save formatted text report
    report_lines = [
        "=" * 105,
        "📊 CLOUD GPU RENDER TIMING REPORT (S25 -> S29)",
        "Hardware: NVIDIA Tesla T4 | Resolution: 1280x720 | Engine: EEVEE (16 samples)",
        "=" * 105,
        f"{'Clip':<12} {'Beat':<6} {'Frames':<8} {'Render Time':<13} {'Sec/Frame':<12} {'Mux Time':<11} {'Total Time':<12} {'Size':<10} {'File':<25}",
        "-" * 105
    ]
    for c in completed_mp4s:
        report_lines.append(
            f"{c['clip']:<12} {c['beat']:<6} {c['frame_count']:<8} "
            f"{c['render_duration_sec']:>6.1f}s       "
            f"{c['sec_per_frame']:>5.2f}s/f     "
            f"{c['mux_duration_sec']:>5.1f}s      "
            f"{c['total_clip_duration_sec']:>6.1f}s      "
            f"{c['mp4_size_mb']:>5.2f} MB   "
            f"{c['mp4_file']:<25}"
        )
    report_lines.extend([
        "-" * 105,
        f"{'TOTAL':<12} {'':<6} {total_frames:<8} "
        f"{total_render_duration:>6.1f}s       "
        f"{avg_sec_per_frame:>5.2f}s/f     "
        f"{total_mux_time:>5.1f}s      "
        f"{total_time:>6.1f}s ({total_time/60:.1f}m)",
        "=" * 105
    ])
    report_text = "\n".join(report_lines)
    report_txt_path = os.path.join(OUTPUT_DIR, "timing_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    # Print the report to the console
    print("\n" + report_text, flush=True)
    print(f"\n🎉 All {len(completed_mp4s)} review clips and timing logs generated in {OUTPUT_DIR}!", flush=True)

if __name__ == "__main__":
    render_and_multiplex_all()

