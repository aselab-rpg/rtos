# LAB 3 — So găng SCHED_OTHER vs SCHED_RR vs SCHED_FIFO (+ affinity)

## 1. Mô tả bài lab
Đánh giá chất lượng lập lịch trên Linux khi đo jitter bằng `cyclictest` với ba chính sách POSIX chính: `SCHED_OTHER` (CFS), `SCHED_RR` (round-robin realtime) và `SCHED_FIFO` (fixed-priority realtime). Bài lab hướng dẫn cách ghim CPU (CPU affinity) và thêm tải nền để quan sát p99.9/max latency.

## 2. Kiến thức nền tảng
- **SCHED_OTHER (CFS)**: chính sách mặc định, bảo đảm fairness nhưng không tối ưu tail latency.
- **SCHED_RR**: realtime time-slice; các luồng cùng ưu tiên chia thời gian theo quantum.
- **SCHED_FIFO**: realtime ưu tiên cố định, không time-slice; luồng chạy tới khi tự yield/block.
- **CPU affinity**: ghim tiến trình vào một CPU giúp giảm nhiễu do migration.

## 3. Chuẩn bị môi trường
```bash
sudo apt update
sudo apt install rt-tests util-linux stress-ng -y
```
`rt-tests` cung cấp `cyclictest`; `util-linux` cung cấp `chrt`; `stress-ng` dùng tạo tải nền (tùy chọn).

## 4. Cấu trúc thư mục
```
lab3_posix_policies/
├── README.md
└── run_experiments.sh   # Script tự động hóa chuỗi phép đo và gom log
```

## 5. Các bước chạy thủ công
1. **SCHED_OTHER (mặc định)**
   ```bash
   cyclictest -t1 -n -i1000 -l200000 > other.txt
   ```
2. **SCHED_RR, ưu tiên 80**
   ```bash
   sudo chrt -r 80 cyclictest -t1 -n -i1000 -l200000 > rr.txt
   ```
3. **SCHED_FIFO, ưu tiên 90, ghim CPU2**
   ```bash
   sudo taskset -c 2 chrt -f 90 cyclictest -t1 -n -i1000 -l200000 > fifo_cpu2.txt
   ```
4. **Thêm tải nền (tùy chọn)**
   ```bash
   stress-ng --cpu 2 --timeout 120 &
   STRESS_PID=$!
   sudo taskset -c 2 chrt -f 90 cyclictest -t1 -n -i1000 -l200000 > fifo_stress.txt
   kill $STRESS_PID
   ```
5. Trích xuất thống kê:
   ```bash
   for f in *.txt; do
     echo "==== $f ===="
     tail -n5 $f
   done
   ```

## 6. Dùng script tự động
Script `run_experiments.sh` gom đủ bước, thêm timestamp và tóm tắt nhanh.
```bash
cd lab3_posix_policies
chmod +x run_experiments.sh
./run_experiments.sh --cpu 2 --interval 1000 --loops 200000
```
Tùy chọn `--background` khởi chạy `stress-ng` tự động.

## 7. Phân tích & kỳ vọng
- `SCHED_OTHER`: jitter cao nhất, p99.9 dễ vượt 300–500 µs khi có tải.
- `SCHED_RR`: cải thiện tail do ưu tiên realtime nhưng vẫn bị ảnh hưởng quantum.
- `SCHED_FIFO + affinity`: tail thấp nhất khi hệ thống vắng, duy trì dưới 100 µs.
- Khi thêm tải nền, quan sát sự tăng mạnh của max latency, đặc biệt ở `SCHED_OTHER`.

## 8. Báo cáo kết quả
Gửi kèm: bảng p50/p95/p99/p99.9, biểu đồ histogram từ log `cyclictest` (dùng `plot_cyclictest.py` nếu muốn tự viết), so sánh có/không ghim CPU.

## 9. Tài liệu tham khảo
- `man chrt`
- `man sched`
- Red Hat Real-Time Tuning Guide
- Linux Foundation RT Wiki — cyclictest methodology
