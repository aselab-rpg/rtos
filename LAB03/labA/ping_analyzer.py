"""
Phân tích log ping để lấy latency và jitter xấp xỉ.

Usage:
    python3 ping_analyzer.py ping_idle.log ping_busy.log
"""
import math
import re
import statistics
import sys
from pathlib import Path

TIME_RE = re.compile(r"time=([0-9]*\\.?[0-9]+)")


def extract_times_ms(text: str) -> list[float]:
    times = [float(m.group(1)) for m in TIME_RE.finditer(text)]
    return times


def analyze(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    times_ms = extract_times_ms(path.read_text())
    if not times_ms:
        raise ValueError(f"No time= entries found in {path}")

    avg = statistics.mean(times_ms)
    min_v = min(times_ms)
    max_v = max(times_ms)
    jitter_std = statistics.pstdev(times_ms)

    diffs = [abs(b - a) for a, b in zip(times_ms, times_ms[1:])]
    jitter_adj = statistics.mean(diffs) if diffs else 0.0

    return {
        "file": str(path),
        "count": len(times_ms),
        "avg_ms": avg,
        "min_ms": min_v,
        "max_ms": max_v,
        "jitter_std_ms": jitter_std,
        "jitter_adj_ms": jitter_adj,
    }


def print_table(results: list[dict]) -> None:
    headers = [
        "File",
        "Samples",
        "Avg (ms)",
        "Min (ms)",
        "Max (ms)",
        "Jitter std (ms)",
        "Avg |Δtime| (ms)",
    ]
    rows = [headers]
    for r in results:
        rows.append(
            [
                Path(r["file"]).name,
                str(r["count"]),
                f"{r['avg_ms']:.3f}",
                f"{r['min_ms']:.3f}",
                f"{r['max_ms']:.3f}",
                f"{r['jitter_std_ms']:.3f}",
                f"{r['jitter_adj_ms']:.3f}",
            ]
        )

    col_widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    for row in rows:
        print(" | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python3 ping_analyzer.py <ping_log> [more_logs...]")
        return 1

    results = []
    for name in argv[1:]:
        try:
            results.append(analyze(Path(name)))
        except Exception as exc:  # noqa: BLE001
            print(f"[!] {name}: {exc}")
    if not results:
        return 1

    print_table(results)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
