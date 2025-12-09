"""
Tóm tắt log delay CSV từ udp_receiver.py.

Usage:
    python3 delay_summary.py delay_log.csv
"""
import csv
import statistics
import sys
from pathlib import Path


def summarize(path: Path) -> dict:
    delays = []
    misses = 0
    total = 0
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            delay = float(row["delay_s"])
            miss = int(row.get("miss", 0))
            delays.append(delay)
            misses += miss
            total += 1

    if not delays:
        raise ValueError("No rows found")

    return {
        "file": str(path),
        "total": total,
        "misses": misses,
        "miss_ratio": misses / total,
        "avg_ms": statistics.mean(delays) * 1000,
        "min_ms": min(delays) * 1000,
        "max_ms": max(delays) * 1000,
        "std_ms": statistics.pstdev(delays) * 1000,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python3 delay_summary.py <delay_log.csv>")
        return 1
    path = Path(argv[1])
    try:
        stats = summarize(path)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")
        return 1

    print(f"File: {Path(stats['file']).name}")
    print(f"Total: {stats['total']}, Misses: {stats['misses']} ({stats['miss_ratio']:.3%})")
    print(
        "Delay avg/min/max/std (ms): "
        f"{stats['avg_ms']:.3f} / {stats['min_ms']:.3f} / "
        f"{stats['max_ms']:.3f} / {stats['std_ms']:.3f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
