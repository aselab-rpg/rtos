"""
UDP sender định kỳ: gửi gói chứa seq và timestamp.

Usage:
    python3 udp_sender.py --dest-ip 192.168.1.20 --period-ms 10 --num 1000
"""
import argparse
import socket
import time


def send_loop(dest_ip: str, dest_port: int, period_ms: float, num_packets: int) -> None:
    addr = (dest_ip, dest_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    period_s = period_ms / 1000.0
    start = time.perf_counter()

    for seq in range(num_packets):
        target = start + seq * period_s
        now = time.perf_counter()
        if target > now:
            time.sleep(target - now)

        send_time = time.time()
        payload = f"{seq},{send_time}".encode("utf-8")
        sock.sendto(payload, addr)

    sock.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UDP periodic sender")
    parser.add_argument("--dest-ip", required=True, help="IP của Receiver")
    parser.add_argument("--dest-port", type=int, default=5005, help="UDP port (default: 5005)")
    parser.add_argument("--period-ms", type=float, default=10.0, help="Chu kỳ gửi (ms, default: 10)")
    parser.add_argument("--num", type=int, default=1000, help="Số packet cần gửi (default: 1000)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        f"Sending {args.num} packets to {args.dest_ip}:{args.dest_port} "
        f"every {args.period_ms} ms..."
    )
    send_loop(args.dest_ip, args.dest_port, args.period_ms, args.num)
    print("Done.")


if __name__ == "__main__":
    main()
