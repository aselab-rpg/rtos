# Lab 3: Quản lý Độ tươi Dữ liệu (Data Freshness)

## Mục tiêu
Áp dụng khái niệm **AVI (Absolute Validity Interval)** trong bối cảnh thực tế - Hệ thống tìm kiếm cứu nạn **iSARS (intelligent Search And Rescue System)**.

## Kịch bản

Hệ thống **iSARS** nhận tọa độ GPS từ thiết bị của nạn nhân. Để robot cứu hộ hoạt động chính xác, tọa độ chỉ có giá trị sử dụng trong vòng **200ms** (AVI = 0.2s).

**Quy tắc:**
- Nếu `CurrentTime - DataTimestamp ≤ AVI` → Dữ liệu **FRESH** (tươi) → Chấp nhận
- Nếu `CurrentTime - DataTimestamp > AVI` → Dữ liệu **STALE** (ôi thiu) → Loại bỏ

## Yêu cầu
- Python 3.8+
- Thư viện: `matplotlib`, `numpy`

## Cài đặt

```bash
pip install matplotlib numpy
```

## Chạy mô phỏng

### Mô phỏng cơ bản
```bash
python data_freshness_isars.py
```

### Mô phỏng với độ trễ cao (quá tải)
```bash
python data_freshness_isars.py --processing-delay 0.3
```

### Tùy chỉnh AVI
```bash
python data_freshness_isars.py --avi 0.1
```

### Chạy thử nghiệm đầy đủ
```bash
python data_freshness_isars.py --duration 10 --data-rate 100
```

## Các tham số

- `--avi`: Absolute Validity Interval (giây, default: 0.2)
- `--data-rate`: Số lượng GPS updates/giây (default: 50)
- `--processing-delay`: Độ trễ xử lý (giây, default: 0.05)
- `--duration`: Thời gian mô phỏng (giây, default: 5)

## Kết quả

Script sẽ:
1. Mô phỏng stream dữ liệu GPS liên tục
2. Áp dụng bộ lọc độ tươi (Freshness Filter)
3. Thống kê tỷ lệ dữ liệu:
   - **Accepted**: Được chấp nhận (fresh)
   - **Rejected**: Bị loại bỏ (stale)
4. Vẽ biểu đồ timeline và phân tích

## Kiến trúc Hệ thống

```
[Nạn nhân + GPS Device] 
        ↓ (Stream GPS data)
[Data Generator] 
        ↓
[Freshness Filter] ← Kiểm tra AVI
        ↓
    ┌───────┴───────┐
    ↓               ↓
[Accept]      [Reject]
    ↓               ↓
[Database]      [Log Warning]
    ↓
[Robot Control System]
```

## Phân tích

### Khi hệ thống hoạt động tốt (Low Load)
- Processing delay < AVI
- Hầu hết dữ liệu được chấp nhận
- Rejection rate < 5%

### Khi hệ thống quá tải (High Load)
- Processing delay ≥ AVI
- Nhiều dữ liệu bị loại bỏ
- Rejection rate > 50%
- **Nguy hiểm**: Robot có thể đi sai hướng!

## Bài học

1. **AVI phải phù hợp với use case**: 200ms cho rescue robot là hợp lý
2. **Monitor freshness metrics**: Cần cảnh báo khi rejection rate cao
3. **Scaling**: Khi overload, cần scale hệ thống hoặc tăng resources
4. **Trade-offs**: AVI nhỏ = Độ chính xác cao nhưng rejection rate cao hơn
