# Bộ bài lab Real-Time & RTOS

Repo cung cấp 5 bài lab thực hành về lập lịch thời gian thực trên Linux và Zephyr RTOS. Mỗi lab có đủ phần lý thuyết nền, hướng dẫn setup, mã nguồn mẫu, cách chạy step-by-step và gợi ý phân tích kết quả.

## LAB 1 — So kè RMS vs EDF trên Linux (`lab1_rms_vs_edf/`)
- **Mục tiêu**: Tạo 3–4 tác vụ chu kỳ ⟨Cᵢ, Tᵢ, Dᵢ⟩, chạy với RMS (SCHED_FIFO) và EDF (SCHED_DEADLINE hoặc mô phỏng user-space), đo deadline miss và độ trễ p99.9 rồi đối chiếu điều kiện Liu–Layland.
- **Thành phần chính**: `src/periodic_demo.c` sinh luồng periodic dùng clock_nanosleep ABS time, log `schedule_log.csv` với latency, runtime, deadline hit.
- **Chuẩn bị**: `sudo apt install build-essential rt-tests`. Kiểm tra kernel có `CONFIG_SCHED_DEADLINE`. 
- **Cách chạy nhanh**: Biên dịch `gcc -O2 -Wall -pthread periodic_demo.c -o periodic_demo`; chạy `sudo ./periodic_demo --policy rms ...` rồi `--policy edf`; song song chạy `sudo cyclictest ...` để đo jitter nền.
- **Phân tích/Kỳ vọng**: RMS ổn định dưới ngưỡng ΣC/T ≤ n(2^{1/n}-1); EDF giữ deadline tốt gần 100% tải; log CSV và `cyclictest` giúp so tail latency giữa hai chế độ.

## LAB 2 — Priority inversion thực chiến (`lab2_priority_inversion/`)
- **Mục tiêu**: Mô phỏng ba luồng L/M/H cùng mutex để quan sát priority inversion và lợi ích của Priority Inheritance (PI) trên Linux.
- **Thành phần chính**: `src/priority_inversion_demo.c` tạo thread SCHED_FIFO với barrier đồng bộ, ghi `results.csv` cho từng iteration.
- **Chuẩn bị**: `sudo apt install build-essential`. Chạy trên Linux với quyền đặt SCHED_FIFO.
- **Cách chạy nhanh**: `gcc -O2 -Wall -pthread priority_inversion_demo.c -o priority_inversion_demo`; chạy `sudo ./priority_inversion_demo --policy none ...` rồi `--policy inherit`; so sánh response time của luồng H trong CSV.
- **Phân tích/Kỳ vọng**: Không PI → H bị kẹt khi M chiếm CPU; bật PI → L được nâng ưu tiên, mutex nhả sớm, response time co lại. Có thể thêm `--work-ms`/`--hold-ms` để tăng độ tương phản.

## LAB 3 — So găng SCHED_OTHER vs RR vs FIFO (`lab3_posix_policies/`)
- **Mục tiêu**: Đo jitter `cyclictest` cho ba chính sách POSIX (CFS, RR, FIFO) và tác động của CPU affinity, thêm tải nền.
- **Thành phần chính**: `run_experiments.sh` gom lệnh `cyclictest`, tự tạo thư mục `logs/<timestamp>/`, lưu raw output và `summary.txt`.
- **Chuẩn bị**: `sudo apt install rt-tests util-linux stress-ng`. Script yêu cầu `sudo` khi đặt chính sách realtime.
- **Cách chạy nhanh**: `./run_experiments.sh --cpu 2 --interval 1000 --loops 200000 --background`. Script sẽ lần lượt chạy OTHER/RR/FIFO (kèm stress nếu bật) và chốt bằng tóm tắt tail log.
- **Phân tích/Kỳ vọng**: SCHED_OTHER có tail cao nhất, SCHED_RR cải thiện phần nào, SCHED_FIFO + pin CPU giữ jitter thấp và ổn định hơn; khi bật stress-ng tail tăng mạnh, nhất là OTHER.

## LAB 4 — Zephyr k_msgq client ↔ server (`lab4_zephyr_msgq/`)
- **Mục tiêu**: Trên Zephyr (QEMU x86), triển khai client gửi chu kỳ qua `k_msgq` cho server; đổi ưu tiên server để quan sát độ trễ và backlog.
- **Thành phần chính**: `src/main.c` tạo hai thread, log `latency`, `backlog`, `drop`; `prj.conf` đặt default (server prio 1), `overlay-server-low.conf` hạ server xuống 3, `Kconfig` cho phép điều chỉnh thông số.
- **Chuẩn bị**: Cài Zephyr toolchain (`pip install west`, `west init/update`, `west zephyr-export`), đảm bảo `ZEPHYR_BASE`.
- **Cách chạy nhanh**: `west build -b qemu_x86 <repo>/lab4_zephyr_msgq -p always` rồi `west build -t run`; lặp lại với `-- -DOVERLAY_CONFIG=overlay-server-low.conf`.
- **Phân tích/Kỳ vọng**: Server prio cao → latency ≈ thời gian xử lý mô phỏng, backlog thấp; server prio thấp → backlog tăng, log cảnh báo drop khi queue đầy; phù hợp để đo tác động ưu tiên trong RTOS.

## LAB 5 — Zephyr k_mbox & deferred work (`lab5_zephyr_mbox/`)
- **Mục tiêu**: Mô phỏng deferred work: client ưu tiên thấp gửi burst thông điệp lớn qua `k_mbox`, server ưu tiên cao xử lý và báo hoàn tất qua `k_sem`.
- **Thành phần chính**: `src/main.c` định nghĩa mailbox, semaphore, payload linh hoạt; `prj.conf` (server prio 1) và `overlay-server-low.conf` (server prio 4); `Kconfig` cho phép chỉnh burst, payload, thời gian xử lý.
- **Chuẩn bị**: Dùng cùng môi trường Zephyr như LAB 4.
- **Cách chạy nhanh**: `west build -b qemu_x86 <repo>/lab5_zephyr_mbox -p always` rồi `west build -t run`; chạy lại với overlay để hạ ưu tiên server và so sánh log.
- **Phân tích/Kỳ vọng**: Server ưu tiên cao → mỗi burst hoàn tất nhanh, log server latency thấp; khi hạ ưu tiên → thời gian client đợi `k_sem` kéo dài, log cho thấy latency tăng và số message bị truncate (nếu payload vượt buffer).

> **Lưu ý**: README trong từng thư mục mở rộng thêm lý thuyết, lệnh chi tiết, biến cấu hình và gợi ý mở rộng. Hãy xem trực tiếp từng lab khi chuẩn bị báo cáo hoặc chạy thử nghiệm.
