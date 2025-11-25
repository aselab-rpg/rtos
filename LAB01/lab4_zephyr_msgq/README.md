# LAB 4 — Zephyr (QEMU): k_msgq client ↔ server, thay đổi ưu tiên server

## 1. Mô tả bài lab
Triển khai cặp client/server trao đổi dữ liệu qua `k_msgq` trong Zephyr RTOS, chạy trên QEMU x86. Thay đổi ưu tiên của server để quan sát ảnh hưởng tới độ trễ phục vụ và backlog hàng đợi.

## 2. Kiến thức nền tảng
- `k_msgq`: hàng đợi thông điệp kích thước cố định, phù hợp truyền dữ liệu nhỏ deterministically.
- Ưu tiên trong Zephyr: giá trị nhỏ hơn ⇒ ưu tiên cao hơn (0 là cao nhất trong miền preemptive).
- Thread API: `k_thread_create`, `k_msgq_get/put`, `k_msleep`.

## 3. Chuẩn bị môi trường (một lần)
```bash
pip install west
west init ~/zephyrproject && cd ~/zephyrproject
west update && west zephyr-export
west build -b qemu_x86 samples/hello_world && west build -t run
```
Đảm bảo biến `ZEPHYR_BASE` được thiết lập (`source zephyr-env.sh`).

## 4. Cấu trúc thư mục bài lab
```
lab4_zephyr_msgq/
├── CMakeLists.txt
├── Kconfig
├── README.md
├── overlay-server-low.conf   # Overlay đổi server priority = 3
├── prj.conf                  # Server priority = 1 (ưu tiên cao)
└── src/
    └── main.c
```

## 5. Bước chạy chuẩn (server ưu tiên cao)
```bash
cd ~/zephyrproject
west build -b qemu_x86 /Users/digifact/RTOS/lab4_zephyr_msgq -p always
west build -t run
```
Quan sát log: server xử lý gần như tức thì, backlog hàng đợi nhỏ.

## 6. Kịch bản đổi ưu tiên server xuống 3
```bash
west build -b qemu_x86 /Users/digifact/RTOS/lab4_zephyr_msgq \
  -p always -- -DOVERLAY_CONFIG=overlay-server-low.conf
west build -t run
```
So sánh log: server bị chậm lại, backlog tăng, độ trễ gửi từ client lớn hơn.

## 7. Phân tích log
Mỗi thông điệp in dạng:
```
[00:01:23.456] server seq=42 latency=5 ms backlog=0
```
- `latency`: thời gian từ lúc client put đến khi server xử lý.
- `backlog`: số phần tử còn lại trong `k_msgq` sau khi lấy ra.
Ghi log sang file bằng `west build -t run | tee run.log` để tính p50/p95.

## 8. Kỳ vọng kết quả
- Server priority = 1: hầu như không có backlog, latency ~ thời gian xử lý mô phỏng (CONFIG_APP_SERVER_WORK_MS).
- Server priority = 3: khi client gửi nhanh (period 50 ms) và server bận, backlog tăng, latency dao động > 20–30 ms.
- Điều chỉnh `CONFIG_APP_SERVER_WORK_MS` để tăng độ chênh.

## 9. Mở rộng
- Thêm tiến trình thứ ba tiêu thụ CPU (thread prio=2) để xem server bị giành CPU.
- Ghi số liệu sang `k_fifo` hoặc shell module để phân tích offline.
- Thử thay `k_msgq` bằng `k_fifo` để so sánh overhead.

## 10. Tài liệu tham khảo
- Zephyr API Reference: Message Queues
- Zephyr Documentation: Thread Priority and Scheduling
- Zephyr Getting Started Guide
