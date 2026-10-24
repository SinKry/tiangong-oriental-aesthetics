#!/usr/bin/env python3
"""Create timestamped evidence for visual shot review; candidates are not cuts."""
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:] or "Command failed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New directory; never overwrites an existing one")
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--end", type=float)
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--threshold", type=float, default=0.25)
    args = parser.parse_args()
    if not args.video.is_file():
        parser.error("Input video does not exist")
    if args.output.exists():
        parser.error("Output directory already exists; choose a new directory")
    if not all(shutil.which(tool) for tool in ("ffmpeg", "ffprobe")):
        parser.error("ffmpeg and ffprobe must be available on PATH")
    numeric = [args.start, args.interval, args.threshold]
    if args.end is not None:
        numeric.append(args.end)
    if not all(math.isfinite(n) for n in numeric) or args.interval <= 0 or not 0 < args.threshold < 1:
        parser.error("Use finite numbers, a positive interval, and threshold between 0 and 1")

    source = args.video.resolve()
    info = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source)]).stdout)
    stream = next((s for s in info["streams"] if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    if stream is None:
        parser.error("No video stream")
    duration = float(stream.get("duration") or info["format"]["duration"])
    rate = stream.get("avg_frame_rate", "0/1").split("/")
    fps = float(rate[0]) / float(rate[1]) if len(rate) == 2 and float(rate[1]) else 0
    frame_time = 1 / fps if fps > 0 else 0.04
    end = duration if args.end is None else min(args.end, duration)
    if not math.isfinite(duration) or not 0 <= args.start < end:
        parser.error("Require 0 <= start < end <= duration")

    # Decode from the beginning so frame-change candidates have original-relative timestamps.
    video_filter = f"setpts=PTS-STARTPTS,select='between(t,{args.start},{end})*gt(scene,{args.threshold})',showinfo"
    detection = run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(source), "-t", str(end), "-map", f"0:{stream['index']}", "-vf", video_filter, "-an", "-sn", "-f", "null", "-"])
    cuts = sorted(set(float(t) for t in re.findall(r"pts_time:([0-9.eE+\-]+)", detection.stderr)))
    cuts = [t for t in cuts if args.start <= t < end]
    last = max(args.start, end - frame_time)
    requested = {}

    def add(time, reason):
        time = round(min(last, max(args.start, time)), 6)
        requested.setdefault(time, set()).add(reason)

    add(args.start, "range_start")
    add(last, "range_last_frame_estimate")
    for i in range(math.ceil((end - args.start) / args.interval)):
        add(args.start + i * args.interval, "uniform_sample")
    for time in cuts:
        add(time - max(0.12, frame_time * 2), "before_candidate")
        add(time, "candidate")
        add(time + max(0.12, frame_time * 2), "after_candidate")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    frames_dir = output / "frames"
    frames_dir.mkdir()
    records = []
    for i, (time, reasons) in enumerate(sorted(requested.items()), 1):
        frame = frames_dir / f"frame-{i:05d}.jpg"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", str(time), "-i", str(source), "-map", f"0:{stream['index']}", "-vf", "scale=480:-2,setsar=1", "-frames:v", "1", "-q:v", "2", str(frame)])
        if not frame.is_file() or not frame.stat().st_size:
            raise RuntimeError(f"No frame extracted at {time}s; partial evidence preserved in {output}")
        records.append({"index": i, "requested_time_seconds": time, "file": frame.relative_to(output).as_posix(), "reasons": sorted(reasons)})

    # Fixed row-major order, 12 frames/page. Time mapping is in the manifest.
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-framerate", "1", "-start_number", "1", "-i", str(frames_dir / "frame-%05d.jpg"), "-vf", "scale=360:-2,tile=4x3:padding=4:margin=4", "-frames:v", str(math.ceil(len(records) / 12)), "-q:v", "2", str(output / "overview-%03d.jpg")])
    sheets = []
    for offset in range(0, len(records), 12):
        file = f"overview-{offset // 12 + 1:03d}.jpg"
        if not (output / file).is_file():
            raise RuntimeError(f"Missing contact sheet {file}")
        sheets.append({"file": file, "order": "left-to-right, then top-to-bottom; remaining cells are blank", "frames": records[offset:offset + 12]})
    manifest = {
        "source": str(source), "duration_seconds": duration,
        "range_seconds": [args.start, end], "video_stream": stream,
        "has_audio": any(s.get("codec_type") == "audio" for s in info["streams"]),
        "audio_reviewed": False, "interval_seconds": args.interval,
        "candidate_threshold": args.threshold, "candidate_times_seconds": cuts,
        "warning": "Scene-change candidates require visual confirmation. Requested extraction times are not verified shot boundaries. Short shots may be missed.",
        "frames": records, "sheets": sheets,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "duration_seconds": duration, "range_seconds": [args.start, end], "candidate_times_seconds": cuts, "frames": len(records), "sheets": len(sheets)}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
