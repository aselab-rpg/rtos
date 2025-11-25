# Lab 2: Mô phỏng Lập lịch Giao dịch (Transaction Scheduling)

## Mục tiêu
Hiểu cách hệ thống RTDB ưu tiên xử lý để giảm thiểu tỷ lệ trễ hạn (**Deadline Miss Ratio**) bằng cách so sánh 2 thuật toán:
- **FCFS (First-Come First-Served)**: Đến trước làm trước
- **EDF (Earliest Deadline First)**: Deadline gần nhất làm trước

## Yêu cầu
- Python 3.8+
- Thư viện: `matplotlib`, `numpy`

## Cài đặt

```bash
pip install matplotlib numpy
```

## Chạy mô phỏng

### Chạy với dữ liệu mẫu
```bash
python scheduler_simulation.py
```

### Tạo báo cáo chi tiết
```bash
python scheduler_simulation.py --detailed
```

### Tùy chỉnh số lượng transactions
```bash
python scheduler_simulation.py --num-transactions 100
```

## Cấu trúc Transaction

Mỗi transaction có các thuộc tính:
- `transaction_id`: Mã định danh
- `arrival_time`: Thời điểm đến hệ thống (ms)
- `execution_time`: Thời gian cần để xử lý (ms)
- `deadline`: Hạn chót phải hoàn thành (ms)

## Kết quả

Script sẽ:
1. Tạo danh sách các transactions ngẫu nhiên
2. Chạy mô phỏng với FCFS và EDF
3. Tính toán **Miss Ratio** (% tasks bị trượt deadline)
4. Vẽ biểu đồ Gantt Chart cho cả hai thuật toán
5. So sánh hiệu quả

## Giải thích kết quả

### FCFS (First-Come First-Served)
- **Ưu điểm**: Đơn giản, công bằng
- **Nhược điểm**: Không quan tâm đến deadline, dễ bỏ lỡ các task quan trọng
- **Use case**: Hệ thống không yêu cầu real-time nghiêm ngặt

### EDF (Earliest Deadline First)
- **Ưu điểm**: Tối ưu cho real-time systems, giảm miss ratio
- **Nhược điểm**: Phức tạp hơn, có thể gây starvation cho tasks có deadline xa
- **Use case**: RTDB, real-time control systems

### Kỳ vọng
- EDF thường có **Miss Ratio thấp hơn** FCFS 30-70%
- Càng tải cao (high load), EDF càng vượt trội
