# LAB 2 — Priority inversion: Mutex thường vs Priority Inheritance

## 1. Mô tả bài lab
Dựng kịch bản kinh điển với ba luồng L/M/H để quan sát hiện tượng priority inversion và cách cơ chế Priority Inheritance (PI) xử lý. Luồng thấp (L) giữ mutex, luồng cao (H) chờ mutex, luồng trung bình (M) chiếm CPU. Đo thời gian H hoàn tất công việc quan trọng trong hai trường hợp: mutex thường (`PTHREAD_PRIO_NONE`) và mutex bật PI (`PTHREAD_PRIO_INHERIT`).

## 2. Kiến thức nền tảng
- **Priority inversion**: luồng ưu tiên cao bị chặn bởi luồng ưu tiên thấp đang giữ tài nguyên, trong khi luồng ưu tiên trung bình chiếm CPU.
- **Priority Inheritance**: khi bật PI, kernel tạm thời nâng ưu tiên của luồng đang giữ mutex lên ngang ưu tiên cao nhất của bên chờ.
- POSIX định nghĩa ba protocol: `PTHREAD_PRIO_NONE`, `PTHREAD_PRIO_INHERIT`, `PTHREAD_PRIO_PROTECT`.

## 3. Chuẩn bị môi trường
```bash
sudo apt update
sudo apt install build-essential -y
```

## 4. Cấu trúc thư mục
```
lab2_priority_inversion/
├── README.md
└── src/
    └── priority_inversion_demo.c   # Chương trình đo thời gian phản hồi của luồng H
```

## 5. Các bước thực hiện
### 5.1 Biên dịch
```bash
cd lab2_priority_inversion/src
gcc -O2 -Wall -pthread priority_inversion_demo.c -o priority_inversion_demo
```

### 5.2 Chạy thử với mutex thường (không PI)
```bash
sudo ./priority_inversion_demo --policy none --iterations 20 --work-ms 200
```

### 5.3 Chạy lại với mutex PI
```bash
sudo ./priority_inversion_demo --policy inherit --iterations 20 --work-ms 200
```

Kết quả được ghi vào `results.csv` với các trường `iteration,policy,response_ms`. So sánh trung bình, p95, p99 giữa hai chế độ.

## 6. Phân tích & kỳ vọng
- Không PI: luồng M tranh CPU khiến H phải chờ đến khi M nhường, response time dài bất thường.
- Có PI: L được nâng ưu tiên, nhả mutex sớm → H hoàn tất critical section nhanh hơn và ổn định hơn.
- Có thể thử thêm tải nền (`stress-ng --cpu 1`) để tăng khả năng inversion kéo dài.

## 7. Mở rộng
- Bật `PTHREAD_PRIO_PROTECT` với priority ceiling để quan sát khác biệt.
- Thay `pthread_mutex_t` bằng `pthread_rwlock_t` và so sánh hiện tượng tương tự.
- Ghi trace bằng `trace-cmd` hoặc `perf sched record` để minh hoạ timeline.

## 8. Tài liệu tham khảo
- `man 3 pthread_mutexattr_setprotocol`
- IEEE 1003.1 POSIX Threads
- "Priority Inheritance for Real-Time Synchronization" — Linux kernel docs
