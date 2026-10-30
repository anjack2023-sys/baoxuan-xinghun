import csv
import tempfile
from pathlib import Path
from analyze_performance_85 import analyze

with tempfile.TemporaryDirectory(prefix="beyblade-perf-test-") as directory:
    root = Path(directory)
    frame = root / "frames.csv"
    memory = root / "memory.csv"
    with frame.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["FrameTime"])
        writer.writerows([[100 if i == 800 else 1000/60] for i in range(1800)])
    with memory.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["elapsed_s", "working_set_mb", "private_mb", "cpu_s"])
        writer.writerows([[20+i, 400+i, 100+i, i] for i in range(50)])
    result = analyze(frame, memory)
    assert result["frames_over_50ms"] == 1
    assert abs(result["p99_frame_ms"] - 1000/60) < 1.e-6
    assert result["average_fps"] < 60
    assert result["working_set_peak_mb"] == 449
    assert result["private_change_mb"] == 25
print("PASS: CSV warmup, hitch, percentile and memory trend")
