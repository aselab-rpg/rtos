# LAB 1 — So kè RMS vs EDF trên Linux

## 1. Mô tả bài lab
So sánh hai chính sách lập lịch thời gian thực phổ biến trên Linux: Rate Monotonic Scheduling (RMS, ưu tiên cố định dựa trên chu kỳ) và Earliest Deadline First (EDF, ưu tiên động). Người học tạo 3–4 tác vụ chu kỳ \(<C_i, T_i, D_i>\), tăng dần tổng tải sử dụng \(U = \sum C_i/T_i\), đo số lần trễ deadline và độ trễ thức dậy p99.9 (hoặc lớn nhất) để đối chiếu với lý thuyết Liu–Layland (RMS) và lý thuyết EDF/CBS.

## 2. Kiến thức nền tảng
- **RMS**: ưu tiên cố định theo chu kỳ, đảm bảo lập lịch nếu \(U \le n(2^{1/n}-1)\).
- **EDF/SCHED_DEADLINE**: ưu tiên động theo deadline gần nhất; về lý thuyết đạt tới 100% tải trên một CPU khi đủ điều kiện.
- **clock_nanosleep(TIMER_ABSTIME)**: gọi ngủ theo thời gian tuyệt đối giúp tránh drift.
- **cyclictest** (rt-tests): đo jitter/scheduling latency chuẩn trên Linux.
- **SCHED_FIFO** và **SCHED_DEADLINE** cần quyền root để đặt ưu tiên.

## 3. Chuẩn bị môi trường
```bash
sudo apt update
sudo apt install build-essential rt-tests linux-tools-common -y
```
Tùy kernel cần bật `CONFIG_SCHED_DEADLINE`. Kiểm tra nhanh: `grep SCHED_DEADLINE /boot/config-$(uname -r)`.

## 4. Cấu trúc thư mục
```
lab1_rms_vs_edf/
├── README.md                # Tài liệu lý thuyết + hướng dẫn chi tiết
└── src/
    └── periodic_demo.c      # Mẫu code tạo tác vụ RMS/EDF và log deadline miss
```
Log đầu ra mặc định được ghi vào file CSV trong cùng thư mục chạy.

## 5. Xây dựng và chạy thử nghiệm
### 5.1 Biên dịch
```bash
cd lab1_rms_vs_edf/src
gcc -O2 -Wall -pthread periodic_demo.c -o periodic_demo
```

### 5.2 Chạy ở chế độ RMS (SCHED_FIFO)
```bash
sudo ./periodic_demo --policy rms \
  --task "name=A,exec_ms=3,period_ms=10,deadline_ms=10" \
  --task "name=B,exec_ms=2,period_ms=15,deadline_ms=15" \
  --task "name=C,exec_ms=4,period_ms=25,deadline_ms=25" \
  --duration 30
```
Tuỳ chỉnh tham số `exec_ms/period_ms/deadline_ms` để tăng tải `U`. Công cụ tự gán ưu tiên RMS (chu kỳ càng ngắn ưu tiên càng cao).

### 5.3 Chạy ở chế độ EDF (SCHED_DEADLINE)
```bash
sudo ./periodic_demo --policy edf \
  --task "name=A,exec_ms=3,period_ms=10,deadline_ms=10" \
  --task "name=B,exec_ms=2,period_ms=15,deadline_ms=15" \
  --task "name=C,exec_ms=4,period_ms=25,deadline_ms=25" \
  --duration 30
```
Nếu kernel không hỗ trợ `SCHED_DEADLINE`, thêm `--policy edf-userspace` để sử dụng mô phỏng EDF nâng/giáng ưu tiên FIFO theo deadline gần nhất. 
Chế độ mô phỏng trong mã mẫu là heuristic đơn giản (điều chỉnh ưu tiên dựa trên lượt chạy) nên dùng để tham khảo khi không thể bật `SCHED_DEADLINE`. 

### 5.4 Đo jitter p99.9 bằng cyclictest
Mở terminal khác và chạy song song:
```bash
sudo cyclictest -p95 -t1 -n -i1000 -l200000 > rms_edf_probe.txt
```
Sau khi hoàn thành, `rms_edf_probe.txt` chứa phân phối latency để so khớp.

## 6. Phân tích kết quả
- Chương trình tạo file `schedule_log.csv` với các cột: `ts,task,iteration,deadline_hit,latency_us`
- Đếm số lần `deadline_hit=0` để biết miss deadline.
- Tính `U` dựa trên tham số đầu vào để so sánh với ngưỡng của RMS và EDF.
- So sánh với log `cyclictest` (p99.9, max) giữa hai chính sách.

## 7. Kỳ vọng & đánh giá
- RMS ổn định dưới ngưỡng lý thuyết (~69% khi n lớn). Khi vượt ngưỡng hoặc thêm nhiễu nền, deadline miss tăng.
- EDF có thể duy trì deadline tốt hơn gần ngưỡng 100% nhưng nhạy cảm với nhiễu kernel/IRQ.
- Khi bật tải nền (ví dụ `stress-ng --cpu 1`), tail latency tăng rõ rệt; ghi chú để báo cáo.

## 8. Mở rộng đề xuất
- Thêm tác vụ nền IO hoặc memory để quan sát ảnh hưởng.
- Dùng `perf sched` để quan sát timeline lập lịch.
- Thử nghiệm CBS (Constant Bandwidth Server) bằng cách thay đổi `runtime/deadline/period`.

## 9. Tài liệu tham khảo
- `man 7 sched`
- `man 2 sched_setattr`
- Linux Foundation RT Wiki – cyclictest test design
- Paper Liu & Layland (1973)
