"""
Tính gần đúng worst-case response time (Rᵢ) cho bus ưu tiên (giống CAN).

Mặc định dùng 3 message trong handout. Có thể chỉnh nhanh:
    python3 can_rt_calc.py --c3 2.5        # tăng thời gian truyền M3
    python3 can_rt_calc.py --t1 8          # giảm period M1
Hoặc dùng file JSON: [{"name": "M1", "priority": 1, "period_ms": 10, "deadline_ms": 10, "c_ms": 1.0}, ...]
"""
import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Message:
    name: str
    priority: int  # 1 = cao nhất
    period_ms: float
    deadline_ms: float
    c_ms: float  # thời gian chiếm bus


DEFAULT_MESSAGES = [
    Message("M1", 1, 10.0, 10.0, 1.0),
    Message("M2", 2, 20.0, 20.0, 1.2),
    Message("M3", 3, 50.0, 50.0, 1.5),
]


def load_messages(config_path: Path | None) -> List[Message]:
    if config_path is None:
        return list(DEFAULT_MESSAGES)
    data = json.loads(config_path.read_text())
    messages = []
    for entry in data:
        messages.append(
            Message(
                name=entry["name"],
                priority=int(entry["priority"]),
                period_ms=float(entry["period_ms"]),
                deadline_ms=float(entry["deadline_ms"]),
                c_ms=float(entry["c_ms"]),
            )
        )
    return messages


def override(messages: List[Message], name: str, attr: str, value: float) -> None:
    for m in messages:
        if m.name == name:
            setattr(m, attr, value)
            return


def compute_response_times(messages: List[Message]) -> list[dict]:
    msgs = sorted(messages, key=lambda m: m.priority)
    results = []
    for m in msgs:
        higher = [h for h in msgs if h.priority < m.priority]
        interference = sum(math.ceil(m.deadline_ms / h.period_ms) * h.c_ms for h in higher)
        r_i = m.c_ms + interference
        results.append(
            {
                "name": m.name,
                "priority": m.priority,
                "period_ms": m.period_ms,
                "deadline_ms": m.deadline_ms,
                "c_ms": m.c_ms,
                "r_ms": r_i,
                "meets": r_i <= m.deadline_ms,
                "slack_ms": m.deadline_ms - r_i,
            }
        )
    return results


def print_table(results: list[dict]) -> None:
    headers = [
        "Msg",
        "Prio",
        "T (ms)",
        "D (ms)",
        "C (ms)",
        "R est (ms)",
        "Meets?",
        "Slack (ms)",
    ]
    rows = [headers]
    for r in results:
        rows.append(
            [
                r["name"],
                str(r["priority"]),
                f"{r['period_ms']:.2f}",
                f"{r['deadline_ms']:.2f}",
                f"{r['c_ms']:.2f}",
                f"{r['r_ms']:.2f}",
                "Yes" if r["meets"] else "No",
                f"{r['slack_ms']:.2f}",
            ]
        )
    col_widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    for row in rows:
        print(" | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CAN-like response time estimator")
    parser.add_argument("--config", type=Path, default=None, help="JSON file for messages")
    parser.add_argument("--t1", type=float, default=None, help="Override period of M1 (ms)")
    parser.add_argument("--t2", type=float, default=None, help="Override period of M2 (ms)")
    parser.add_argument("--t3", type=float, default=None, help="Override period of M3 (ms)")
    parser.add_argument("--c1", type=float, default=None, help="Override C of M1 (ms)")
    parser.add_argument("--c2", type=float, default=None, help="Override C of M2 (ms)")
    parser.add_argument("--c3", type=float, default=None, help="Override C of M3 (ms)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    messages = load_messages(args.config)

    overrides = {
        ("M1", "period_ms"): args.t1,
        ("M2", "period_ms"): args.t2,
        ("M3", "period_ms"): args.t3,
        ("M1", "c_ms"): args.c1,
        ("M2", "c_ms"): args.c2,
        ("M3", "c_ms"): args.c3,
    }
    for (name, attr), value in overrides.items():
        if value is not None:
            override(messages, name, attr, value)

    results = compute_response_times(messages)
    print_table(results)


if __name__ == "__main__":
    main()
