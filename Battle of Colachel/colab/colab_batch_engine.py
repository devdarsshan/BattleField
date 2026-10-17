"""Universal Dynamic Batch Renderer & MP4 Multiplexer for Google Colab.
Supports dynamic quality (720p / 1080p), custom sample counts, Google Drive persistent sync,
incremental progress saving, and manifest-driven execution for any shot batch.
"""
import os
import sys
import glob
import json
import time
import shutil
import argparse
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description="Universal Colab Batch Renderer")
    parser.add_argument("--quality", choices=["720p", "1080p"], default="720p", help="Render resolution preset")
    parser.add_argument("--samples", type=int, default=16, help="EEVEE render samples (default: 16)")
    parser.add_argument("--manifest", default=None, help="Path to manifest JSON (optional, auto-detected if omitted)")
    parser.add_argument("--project", default="/content/project", help="Directory containing blend and audio files")
    parser.add_argument("--out", default="/content/drive/MyDrive/battlefield/colachel/renders", help="Output directory for MP4s and timing reports")
    parser.add_argument("--blender", default="/content/blender-5.2.2-linux-x64/blender", help="Path to Blender binary")
    parser.add_argument("--script", default="/content/project/colab_render_cli.py", help="Path to colab_render_cli.py")
    return parser.parse_args()

def get_resolution(quality_str):
    if quality_str == "1080p":
        return 1920, 1080
    return 1280, 720

def find_manifest(project_dir, explicit_path=None):
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path
    
    # Check default project dir
    p1 = os.path.join(project_dir, "manifest.json")
    if os.path.exists(p1):
        return p1
        
    # Check /content root
    p2 = "/content/manifest.json"
    if os.path.exists(p2):
        return p2

    # Check recursively inside project_dir
    matches = glob.glob(f"{project_dir}/**/manifest.json", recursive=True)
    if matches:
        return matches[0]

    return None

def write_reports(out_dir, batch_name, quality, res_x, res_y, samples, completed_mp4s, total_batch_time):
    os.makedirs(out_dir, exist_ok=True)
    total_render_time = sum(c["render_duration_sec"] for c in completed_mp4s)
    total_mux_time = sum(c["mux_duration_sec"] for c in completed_mp4s)
    total_frames = sum(c["frame_count"] for c in completed_mp4s)
    avg_sec_per_frame = total_render_time / total_frames if total_frames > 0 else 0

    # 1. JSON report
    timing_json_path = os.path.join(out_dir, f"timing_{batch_name}_{quality}.json")
    timing_data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "batch_name": batch_name,
        "quality": quality,
        "resolution": f"{res_x}x{res_y}",
        "samples": samples,
        "environment": "Google Colab",
        "hardware": "NVIDIA Tesla T4 GPU",
        "total_batch_duration_sec": round(total_batch_time, 2),
        "total_batch_duration_min": round(total_batch_time / 60, 2),
        "total_render_duration_sec": round(total_render_time, 2),
        "total_mux_duration_sec": round(total_mux_time, 2),
        "total_frames_rendered": total_frames,
        "avg_seconds_per_frame": round(avg_sec_per_frame, 3),
        "clips": completed_mp4s
    }
    with open(timing_json_path, "w", encoding="utf-8") as f:
        json.dump(timing_data, f, indent=2)

    # 2. Human-readable text table
    report_lines = [
        "=" * 105,
        f"📊 CLOUD GPU RENDER TIMING REPORT: {batch_name} [{quality.upper()}]",
        f"Hardware: NVIDIA Tesla T4 | Resolution: {res_x}x{res_y} | EEVEE Samples: {samples}",
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
        f"{total_render_time:>6.1f}s       "
        f"{avg_sec_per_frame:>5.2f}s/f     "
        f"{total_mux_time:>5.1f}s      "
        f"{total_batch_time:>6.1f}s ({total_batch_time/60:.1f}m)",
        "=" * 105
    ])
    report_text = "\n".join(report_lines)
    report_txt_path = os.path.join(out_dir, f"timing_report_{batch_name}_{quality}.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Ensure files are synced to disk (vital for Google Drive FUSE mount)
    try:
        if hasattr(os, "sync"):
            os.sync()
    except Exception:
        pass

    return timing_json_path, report_txt_path, report_text

def run_batch():
    args = parse_args()
    res_x, res_y = get_resolution(args.quality)
    os.makedirs(args.out, exist_ok=True)

    print("=" * 80, flush=True)
    print(f"🎬 Cloud GPU Batch Renderer | Preset: {args.quality} ({res_x}x{res_y}) | Samples: {args.samples}", flush=True)
    print(f"📁 Project Source: {args.project}", flush=True)
    print(f"💾 Output Destination: {args.out}", flush=True)
    print("=" * 80, flush=True)

    # 1. Locate and Load Manifest
    manifest_path = find_manifest(args.project, args.manifest)
    if not manifest_path:
        raise FileNotFoundError(f"Cannot find manifest.json in {args.project} or /content! Ensure package is extracted.")

    print(f"✓ Found manifest: {manifest_path}", flush=True)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    batch_name = manifest_data.get("batch_name", "batch")
    shots = manifest_data.get("shots", [])

    if not shots:
        raise ValueError(f"No shots defined in manifest: {manifest_path}!")

    print(f"✓ Loaded batch '{batch_name}' with {len(shots)} shots.", flush=True)

    total_start_time = time.time()
    completed_mp4s = []

    for idx, s in enumerate(shots, 1):
        clip_name = s["clip"]
        beat = s.get("beat", clip_name)
        blend_file = os.path.join(args.project, s["blend"])
        start_f = s["start"]
        end_f = s["end"]
        frame_count = end_f - start_f + 1
        audio_name = s.get("audio", f"{beat}.wav")
        audio_file = os.path.join(args.project, audio_name)
        
        # Name output MP4 according to the chosen quality preset
        mp4_filename = f"{clip_name}_{beat}_review_{args.quality}.mp4"
        output_mp4 = os.path.join(args.out, mp4_filename)
        temp_local_mp4 = f"/content/{mp4_filename}"
        temp_frames_dir = f"/content/renders/frames_{beat}_{args.quality}"

        print(f"\n▶ [{idx}/{len(shots)}] {clip_name} ({beat}): Frames {start_f}..{end_f} ({frame_count} frames) [{args.quality}]", flush=True)

        if not os.path.exists(blend_file):
            print(f"❌ Error: Cannot find blend file {blend_file}! Skipping.", flush=True)
            continue

        if not os.path.exists(audio_file):
            if os.path.exists(f"/content/{audio_name}"):
                audio_file = f"/content/{audio_name}"
            else:
                print(f"❌ Error: Cannot find audio file {audio_file}! Skipping.", flush=True)
                continue

        # Check for existing completed MP4 (resume support on Google Drive / local storage)
        if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 102400:
            print(f"✓ {mp4_filename} already exists ({os.path.getsize(output_mp4):,} bytes). Skipping.", flush=True)
            completed_mp4s.append({
                "clip": clip_name,
                "beat": beat,
                "blend": s["blend"],
                "start_frame": start_f,
                "end_frame": end_f,
                "frame_count": frame_count,
                "render_duration_sec": 0.0,
                "sec_per_frame": 0.0,
                "fps": 0.0,
                "mux_duration_sec": 0.0,
                "total_clip_duration_sec": 0.0,
                "mp4_file": mp4_filename,
                "mp4_size_mb": round(os.path.getsize(output_mp4) / (1024 * 1024), 2),
                "status": "already_existed"
            })
            # Incrementally update reports on Google Drive
            write_reports(args.out, batch_name, args.quality, res_x, res_y, args.samples, completed_mp4s, time.time() - total_start_time)
            continue

        os.makedirs(temp_frames_dir, exist_ok=True)
        t_shot_start = time.time()

        # Step A: Render PNG frames via EEVEE with Xvfb (proven working configuration)
        cmd_render = [
            "xvfb-run", "-a",
            args.blender, "-b", blend_file,
            "-P", args.script, "--",
            "frames", temp_frames_dir,
            "--range", str(start_f), str(end_f),
            "--engine", "EEVEE",
            "--samples", str(args.samples),
            "--res", f"{res_x}x{res_y}"
        ]

        print(f">>> Running Blender render on Cloud GPU ({args.quality}, {args.samples} samples)...", flush=True)
        t_render_start = time.time()
        ret = subprocess.run(cmd_render)
        render_duration = time.time() - t_render_start

        if ret.returncode != 0:
            print(f"❌ Blender render failed for {beat} with exit code {ret.returncode}!", flush=True)
            continue

        # Step B: Multiplex frames and audio into local MP4 with ffmpeg (auto-codec fallback)
        print(f">>> Multiplexing {frame_count} frames with narration audio ({audio_name})...", flush=True)
        t_mux_start = time.time()

        encoders_to_try = ["libx264", "h264_nvenc", "mpeg4"]
        success_enc = None
        last_error = ""

        # Remove stale temp file if present
        if os.path.exists(temp_local_mp4):
            os.remove(temp_local_mp4)

        for enc in encoders_to_try:
            extra_opts = ["-crf", "18"] if enc == "libx264" else ["-b:v", "5M" if args.quality == "1080p" else "3M"]
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
                temp_local_mp4
            ]
            ret_ff = subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if ret_ff.returncode == 0 and os.path.exists(temp_local_mp4) and os.path.getsize(temp_local_mp4) > 102400:
                success_enc = enc
                break
            else:
                last_error = ret_ff.stderr.decode("utf-8", errors="ignore")[-400:].strip()

        mux_duration = time.time() - t_mux_start

        if not success_enc:
            print(f"❌ ffmpeg multiplexing failed with all encoders! Last error:\n{last_error}", flush=True)
            continue

        # Step C: Safely copy validated MP4 to target storage (e.g. Google Drive)
        shutil.copy2(temp_local_mp4, output_mp4)
        if hasattr(os, "sync"):
            try:
                os.sync()
            except Exception:
                pass
        os.remove(temp_local_mp4)

        if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 102400:
            total_clip_duration = time.time() - t_shot_start
            sec_per_frame = render_duration / frame_count if frame_count > 0 else 0
            fps = frame_count / render_duration if render_duration > 0 else 0
            size_mb = os.path.getsize(output_mp4) / (1024 * 1024)

            print(f"✅ [SAVED TO STORAGE] {output_mp4} ({size_mb:.2f} MB, codec: {success_enc})", flush=True)
            print(f"   ⏱️ Render: {render_duration:.1f}s ({sec_per_frame:.2f}s/f | {fps:.2f} fps) | Mux: {mux_duration:.1f}s | Total: {total_clip_duration:.1f}s", flush=True)

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
                "mp4_file": mp4_filename,
                "mp4_size_mb": round(size_mb, 2),
                "status": "rendered_new"
            })

            # Clean raw frames to save storage space
            shutil.rmtree(temp_frames_dir, ignore_errors=True)

            # Incrementally update reports on Google Drive after each shot
            write_reports(args.out, batch_name, args.quality, res_x, res_y, args.samples, completed_mp4s, time.time() - total_start_time)
        else:
            print(f"❌ Output file invalid or copy failed: {output_mp4}", flush=True)

    # 4. Final Reports Summary
    total_time = time.time() - total_start_time
    json_path, txt_path, report_text = write_reports(
        args.out, batch_name, args.quality, res_x, res_y, args.samples, completed_mp4s, total_time
    )

    print("\n" + report_text, flush=True)
    print(f"\n✓ Saved JSON timings to: {json_path}", flush=True)
    print(f"✓ Saved text report to:  {txt_path}", flush=True)
    print(f"🎉 Batch '{batch_name}' completed! {len(completed_mp4s)}/{len(shots)} MP4s securely saved in:\n   👉 {args.out}", flush=True)

if __name__ == "__main__":
    run_batch()
