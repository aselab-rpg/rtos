# FreeRTOS HVAC Control Framework

Khung mã mẫu này mô tả cách tổ chức firmware FreeRTOS cho bộ điều khiển quạt/điều hòa có 4 tác vụ chu kỳ và một ngắt sporadic:

| Task/ISR | Mô tả | Chu kỳ/Đặc tả | Ưu tiên |
| --- | --- | --- | --- |
| `control_task` (T1) | PID → PWM điều khiển quạt/dàn lạnh | 20 ms, WCET≈2 ms, deadline cứng 20 ms | 5 (cao nhất) |
| `sensor_task` (T2) | Lấy mẫu Nhiệt/Ẩm/RPM (Modbus/UART/ADC) | 100 ms, WCET≈2 ms | 4 |
| `led_task` (T3) | Hiển thị trạng thái nội bộ (LED/UI) | 200 ms, WCET≈1 ms | 3 |
| `database_task` (T4) | Gom dữ liệu & gửi lên RT-DB/cloud | 1000 ms, WCET≈5 ms, deadline mềm 50–200 ms | 2 |
| `command_task` (Server) | Xử lý lệnh từ app (deferred) | Sporadic Server (ps = 50 ms, e = 2 ms) | 4 |
| ISR `app_command_isr_enqueue` (I1) | Ngắt nhận lệnh từ Gateway/App | Sporadic ≥100 ms, exec≈2 ms | — |

## Tổ chức mã

```
include/
  app_config.h        # Thông số thời gian thực: period, WCET, ưu tiên, queue depth
  app_tasks.h         # API tạo task, hàm ISR enqueue
  app_types.h         # Kiểu dữ liệu dùng chung (sensor, command, telemetry, PID)
  ring_buffer.h       # Ring buffer lock-free đơn giản cho RT-DB
  sporadic_server.h   # Cấp phát ngân sách cho lệnh sporadic
src/
  main.c              # Khởi tạo phần cứng sơ bộ và start scheduler
  app_tasks.c         # Toàn bộ tác vụ FreeRTOS, hàng đợi, PID, ghi log
  ring_buffer.c       # Cài đặt vòng đệm
  sporadic_server.c   # Cài đặt sporadic server (budget/period)
```

Các phần hook `board_*` trong `app_tasks.c` cần gán vào driver thực tế: PWM, ADC, UART/Modbus, MQTT/HTTP client, v.v.

## Đảm bảo thời gian thực

* Lập lịch: sử dụng fixed-priority preemptive (FreeRTOS mặc định) với tick 1 kHz, phù hợp xét theo điều kiện Liu–Layland (U=0.13 < 0.693).
* Ngắt: ISR `app_command_isr_enqueue` chỉ copy dữ liệu vào queue và nhờ sporadic server kiểm soát băng thông; xử lý sâu nằm ở task `command_task`.
* Tránh priority inversion: khi dùng mutex bảo vệ thiết bị ngoại vi chậm, bật `configUSE_MUTEXES` và `configUSE_PRIORITIES_INHERITANCE`.

## CSDL thời gian thực

* T1 đẩy log vào vòng đệm `telemetry_entry_t`. Khi vòng đầy, bản ghi cũ bị bỏ để không chặn tác vụ ưu tiên cao.
* T4 (`database_task`) gom lô, gọi `board_database_flush()` với deadline mềm 200 ms. Hãy thay thế bằng RT-DB driver (ví dụ eXtremeDB/Edge) hoặc pass sang gateway.

## Truyền thông

* `board_sample_sensors()` có thể thực hiện Modbus RTU/RS-485. Đảm bảo timing inter-frame ≥ 3.5 ký tự, inter-char ≤ 1.5 ký tự theo tiêu chuẩn.
* `board_database_flush()` có thể publish MQTT: chọn QoS 0/1 tùy criticality, tránh QoS2 nếu latency quá lớn.

## Tích hợp phần cứng

1. Cập nhật `prv_setup_clocks()` và `prv_setup_peripherals()` trong `src/main.c` cho MCU cụ thể.
2. Thay thế các hook `board_*` trong `app_tasks.c` bằng driver thực.
3. Bật FreeRTOS tick 1 kHz trong `FreeRTOSConfig.h` (`configTICK_RATE_HZ 1000`) và đảm bảo `configMAX_PRIORITIES ≥ 6`.
4. Nếu đo được jitter thấp, có thể bật chế độ tickless để tiết kiệm năng lượng (cần đo lại deadline).
5. Bật trace (SEGGER SystemView, Percepio Tracealyzer, …) để đo WCET thực tế.

## Xây dựng & Kiểm thử

* Thêm mã nguồn FreeRTOS (official hoặc ESP-IDF/STM32Cube) vào dự án và include path tương ứng.
* Biên dịch với toolchain MCU, ví dụ CMake hoặc Makefile tùy BSP.
* Kiểm thử từng task với profiler/timer để xác nhận WCET.
* Thử nghiệm stress command ISR ≥ 100 ms để kiểm tra sporadic server không bào mòn ngân sách T1.

## Mở rộng

* Thêm watchdog (task/bsp) để reset nếu T1/T2 bỏ chu kỳ.
* Sử dụng QueueSet nếu cần kết hợp nhiều nguồn dữ liệu cho T1.
* Tận dụng event groups để đồng bộ giữa sensor và database khi thêm batching lớn.
