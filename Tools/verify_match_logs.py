"""Compare independent UE seed batches: python verify_match_logs.py run1.csv run2.csv."""
import csv
import sys
from pathlib import Path


def read(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].startswith("# run_id="), "Missing parameter snapshot"
    snapshot = lines[0].split(" seed=", 1)[1]
    rows = list(csv.DictReader(line for line in lines if not line.startswith("#")))
    assert len(rows) >= 24, "Need at least 24 complete matches per batch"
    assert [int(row["match"]) for row in rows] == list(range(1, len(rows) + 1))
    for row in rows:
        assert row["end_reason"] in {"ringout", "timeout"}
        assert 0 < float(row["end_t"]) <= 60
        assert int(row["hit_count"]) > 0
    return snapshot, rows


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Pass two independent CSV paths"
    first, second = (read(path) for path in sys.argv[1:])
    assert first == second, "Seed/parameters or per-match results differ"
    print(f"PASS: {len(first[1])} matches identical, including first_hit/hit_count/end_t/end_reason/winner")
