"""
UDP receiver: đo delay và deadline miss, ghi log CSV.

Usage:
    python3 udp_receiver.py --listen-ip 0.0.0.0 --listen-port 5005 --deadline-ms 15
"""
import argparse
import socket
import time
from pathlib import Path


def receive_loop(
    listen_ip: str,
    listen_port: int,
    deadline_ms: float,
    outfile: Path,
    timeout_s: float,
    expected_packets: int | None,
) -> tuple[int, int, float, float, float]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_ip, listen_port))
    sock.settimeout(timeout_s)

    deadline_s = deadline_ms / 1000.0
    miss_count = 0
    total = 0
    min_delay = float("inf")
    max_delay = 0.0
    sum_delay = 0.0

    with outfile.open("w", encoding="utf-8") as f:
        f.write("seq,send_time,recv_time,delay_s,miss\n")
        while True:
            if expected_packets is not None and total >= expected_packets:
                break
            try:
                data, _addr = sock.recvfrom(2048)
            except socket.timeout:
                break

            recv_time = time.time()
            try:
                decoded = data.decode("utf-8")
                seq_str, send_str = decoded.split(",")
                seq = int(seq_str)
                send_time = float(send_str)
            except Exception:
                continue

            delay = recv_time - send_time
            miss = int(delay > deadline_s)
            total += 1
            miss_count += miss
            min_delay = min(min_delay, delay)
            max_delay = max(max_delay, delay)
            sum_delay += delay
            f.write(f"{seq},{send_time:.9f},{recv_time:.9f},{delay:.9f},{miss}\n")

    sock.close()
    avg_delay = sum_delay / total if total else 0.0
    return total, miss_count, min_delay, max_delay, avg_delay


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UDP receiver with deadline check")
    parser.add_argument("--listen-ip", default="0.0.0.0", help="IP bind (default: 0.0.0.0)")
    parser.add_argument("--listen-port", type=int, default=5005, help="UDP port (default: 5005)")
    parser.add_argument("--deadline-ms", type=float, default=15.0, help="Deadline (ms, default: 15)")
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=5.0,
        help="Dừng nếu không nhận thêm gói (s, default: 5)",
    )
    parser.add_argument(
        "--expected",
        type=int,
        default=None,
        help="Số gói dự kiến (tùy chọn, để dừng sớm)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("delay_log.csv"),
        help="CSV output file (default: delay_log.csv)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        f"Listening on {args.listen_ip}:{args.listen_port}, deadline {args.deadline_ms} ms, "
        f"logging to {args.out}..."
    )
    total, miss_count, min_delay, max_delay, avg_delay = receive_loop(
        args.listen_ip,
        args.listen_port,
        args.deadline_ms,
        args.out,
        args.timeout_s,
        args.expected,
    )

    if total == 0:
        print("No packets received.")
        return

    miss_ratio = miss_count / total
    print(f"Total packets: {total}")
    print(f"Deadline misses: {miss_count} ({miss_ratio:.3%})")
    print(f"Delay avg/min/max: {avg_delay*1000:.3f} / {min_delay*1000:.3f} / {max_delay*1000:.3f} ms")
    print("CSV saved at:", args.out)


if __name__ == "__main__":
    main()
