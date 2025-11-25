# LAB 5 — Zephyr (QEMU): k_mbox, deferred work & đồng bộ

## 1. Mô tả bài lab
Mô phỏng "deferred work" trong Zephyr bằng cách cho client ưu tiên thấp gửi burst thông điệp lớn qua `k_mbox` tới server ưu tiên cao. So sánh thời gian hoàn tất của client khi đổi ưu tiên server.

## 2. Kiến thức nền tảng
- `k_mbox`: IPC hỗ trợ thông điệp kích thước linh hoạt, có thể gửi kèm payload lớn hơn kích thước con trỏ.
- Deferred work: ISR/producer gửi yêu cầu, server ưu tiên cao lấy và xử lý sau.
- `k_sem`: đồng bộ để client biết khi nào server đã xử lý xong.

## 3. Chuẩn bị
dùng lại môi trường ở LAB 4 (Zephyr QEMU).

## 4. Cấu trúc thư mục
```
lab5_zephyr_mbox/
├── CMakeLists.txt
├── Kconfig
├── README.md
├── overlay-server-low.conf   # Server priority = 4
├── prj.conf                  # Server priority = 1
└── src/
    └── main.c
```

## 5. Chạy với server ưu tiên 1 (cao)
```bash
cd ~/zephyrproject
west build -b qemu_x86 /Users/digifact/RTOS/lab5_zephyr_mbox -p always
west build -t run
```
Client báo thời gian hoàn tất mỗi burst.

## 6. Đổi server xuống ưu tiên 4
```bash
west build -b qemu_x86 /Users/digifact/RTOS/lab5_zephyr_mbox \
  -p always -- -DOVERLAY_CONFIG=overlay-server-low.conf
west build -t run
```
Quan sát thời gian hoàn tất burst tăng rõ khi server kém ưu tiên.

## 7. Log mẫu
```
client burst seq=0..4 done in 18 ms (server_prio=1)
server handled seq=3 latency=5 ms payload=32 B
```

## 8. Kỳ vọng & phân tích
- Server priority cao: mỗi burst 5 thông điệp hoàn tất nhanh (<20 ms) vì server preempt client.
- Server priority thấp: client phải chờ lâu hơn để nhận `k_sem`, backlog mailbox tăng, latency server log lớn.
- Điều chỉnh `CONFIG_APP_PAYLOAD_BYTES` và `CONFIG_APP_SERVER_WORK_MS` để mô phỏng xử lý nặng.

## 9. Mở rộng
- Thêm thread mô phỏng ISR: sử dụng `k_timer` và callback gửi vào mailbox.
- Dùng `k_mbox_async_put` để client không block khi mailbox đầy.
- Ghi thống kê sang shell module hoặc UART để phân tích offline.

## 10. Tài liệu tham khảo
- Zephyr API: Mailbox (`k_mbox_*`)
- Zephyr Synchronization Primitives
- Zephyr Scheduling Concepts
