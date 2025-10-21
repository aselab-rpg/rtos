#!/usr/bin/env bash
set -euo pipefail

INTERVAL=1000
LOOPS=200000
CPU_PIN=""
RUN_STRESS=0
STRESS_OPTS="--cpu 2 --timeout 9999"
SUDO_BIN=${SUDO_BIN:-sudo}

usage() {
  cat <<USAGE
Usage: $0 [--interval us] [--loops N] [--cpu ID] [--background]
  --interval    Khoảng giữa hai wake-up (µs), mặc định 1000
  --loops       Số vòng lặp, mặc định 200000
  --cpu         Ghim vào CPU cụ thể (vd 2). Bỏ trống = không ghim
  --background  Bật thêm stress-ng nền (kết thúc sau khi đo xong)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --loops)
      LOOPS="$2"
      shift 2
      ;;
    --cpu)
      CPU_PIN="$2"
      shift 2
      ;;
    --background)
      RUN_STRESS=1
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v cyclictest >/dev/null 2>&1; then
  echo "cyclictest chưa cài. Vui lòng chạy: sudo apt install rt-tests" >&2
  exit 1
fi

LOG_ROOT="logs"
mkdir -p "$LOG_ROOT"
STAMP=$(date +%Y%m%d_%H%M%S)
RUN_DIR="$LOG_ROOT/$STAMP"
mkdir -p "$RUN_DIR"

echo "Lưu log vào $RUN_DIR"

run_cmd() {
  local name="$1"
  shift
  echo "[INFO] Chạy $name"
  "$@"
}

wrap_with_affinity() {
  if [[ -n "$CPU_PIN" ]]; then
    taskset -c "$CPU_PIN" "$@"
  else
    "$@"
  fi
}

start_stress() {
  if [[ $RUN_STRESS -eq 1 ]]; then
    if ! command -v stress-ng >/dev/null 2>&1; then
      echo "WARNING: stress-ng không có, bỏ qua tải nền" >&2
      RUN_STRESS=0
      return
    fi
    echo "[INFO] Khởi chạy stress-ng nền" >&2
    stress-ng $STRESS_OPTS >/dev/null 2>&1 &
    echo $! > "$RUN_DIR/stress.pid"
  fi
}

stop_stress() {
  if [[ $RUN_STRESS -eq 1 && -f "$RUN_DIR/stress.pid" ]]; then
    local pid
    pid=$(cat "$RUN_DIR/stress.pid")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      wait "$pid" 2>/dev/null || true
    fi
    rm -f "$RUN_DIR/stress.pid"
  fi
}

trap stop_stress EXIT

CBASE=(cyclictest -t1 -n -i"$INTERVAL" -l"$LOOPS")

run_case() {
  local name="$1"
  local outfile="$RUN_DIR/$2"
  shift 2
  local -a prefix=()
  if [[ $# -gt 0 ]]; then
    prefix=("$@")
  fi
  local -a full_cmd=()
  if [[ ${#prefix[@]} -gt 0 ]]; then
    full_cmd=("${prefix[@]}" "${CBASE[@]}")
  else
    full_cmd=("${CBASE[@]}")
  fi
  run_cmd "$name" wrap_with_affinity "${full_cmd[@]}" >"$outfile"
}

start_stress

run_case "SCHED_OTHER" other.txt
run_case "SCHED_RR (prio 80)" rr.txt $SUDO_BIN chrt -r 80
run_case "SCHED_FIFO (prio 90)" fifo.txt $SUDO_BIN chrt -f 90

if [[ $RUN_STRESS -eq 1 ]]; then
  run_case "SCHED_FIFO + stress-ng" fifo_stress.txt $SUDO_BIN chrt -f 90
fi

stop_stress

summary_file="$RUN_DIR/summary.txt"
{
  echo "=== Tham số ==="
  echo "interval_us=$INTERVAL"
  echo "loops=$LOOPS"
  [[ -n "$CPU_PIN" ]] && echo "cpu=$CPU_PIN"
  echo
  for f in "$RUN_DIR"/*.txt; do
    [[ "$f" == *summary.txt ]] && continue
    echo "--- $(basename "$f") ---"
    tail -n5 "$f"
    echo
  done
} >"$summary_file"

echo "Hoàn tất. Xem tóm tắt: $summary_file"
