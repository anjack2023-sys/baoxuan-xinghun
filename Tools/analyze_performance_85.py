"""Summarize a completed UE CSV capture and its process memory samples."""
import csv
import json
import math
import statistics
import sys
from pathlib import Path


def analyze(frame_path, memory_path):
    with Path(frame_path).open(encoding="utf-8-sig", newline="") as f:
        raw = list(csv.reader(f))
    header_index = next(i for i, row in enumerate(raw) if "FrameTime" in row)
    header = raw[header_index]
    index = header.index("FrameTime")
    frames = []
    extras = {name: [] for name in header if name in {"GameThread", "RenderThread", "GPU FrameTime", "GPUTime"}}
    elapsed_ms = 0.0
    warmup = []
    for row in raw[header_index + 1:]:
        try:
            value = float(row[index])
        except (ValueError, IndexError):
            continue
        if value <= 0:
            continue
        frame_start_ms = elapsed_ms
        elapsed_ms += value
        if frame_start_ms < 5000:
            warmup.append(value)
            continue
        frames.append(value)
        for name in extras:
            try:
                extras[name].append(float(row[header.index(name)]))
            except (ValueError, IndexError):
                pass
    assert len(frames) >= 1000, "Insufficient rendered frames"
    ordered = sorted(frames)
    p99 = ordered[min(len(ordered)-1, math.ceil(len(ordered)*0.99)-1)]
    slow = ordered[-max(1, math.ceil(len(ordered)*0.01)):]
    with Path(memory_path).open(encoding="utf-8-sig", newline="") as f:
        memory = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
    steady_memory = [row for row in memory if row["elapsed_s"] >= 20]
    assert len(steady_memory) >= 10, "Insufficient memory samples"
    first = steady_memory[:min(30, len(steady_memory)//2)]
    last = steady_memory[-min(30, len(steady_memory)//2):]
    return {
        "frame_csv": str(frame_path), "memory_csv": str(memory_path),
        "warmup_budget_ms": 5000, "actual_warmup_excluded_ms": sum(warmup), "analyzed_frames": len(frames),
        "analyzed_seconds": sum(frames)/1000, "average_fps": 1000/statistics.mean(frames),
        "p99_frame_ms": p99, "one_percent_low_fps": 1000/statistics.mean(slow),
        "worst_frame_ms": max(frames),
        "frames_over_33ms": sum(v > 1000/30 for v in frames),
        "frames_over_50ms": sum(v > 50 for v in frames),
        "frames_over_100ms": sum(v > 100 for v in frames),
        "first_5s_worst_frame_ms": max(warmup) if warmup else None,
        "working_set_peak_mb": max(row["working_set_mb"] for row in memory),
        "private_peak_mb": max(row["private_mb"] for row in memory),
        "private_first_steady_median_mb": statistics.median(row["private_mb"] for row in first),
        "private_last_steady_median_mb": statistics.median(row["private_mb"] for row in last),
        "private_change_mb": statistics.median(row["private_mb"] for row in last)-statistics.median(row["private_mb"] for row in first),
        "timing_columns_mean_ms": {name: statistics.mean(values) for name, values in extras.items() if values},
    }


if __name__ == "__main__":
    assert len(sys.argv) == 4, "frame.csv memory.csv report.json"
    result = analyze(sys.argv[1], sys.argv[2])
    Path(sys.argv[3]).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
