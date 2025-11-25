# Lab 1: So sánh hiệu năng Disk-based vs In-Memory

## Mục tiêu
Hiểu rõ sự chênh lệch về **Latency (Độ trễ)** và **Throughput (Thông lượng)** giữa cơ sở dữ liệu truyền thống (PostgreSQL) và RTDB (Redis).

## Yêu cầu
- Docker & Docker Compose
- Python 3.8+
- Thư viện: `psycopg2-binary`, `redis`, `matplotlib`, `numpy`

## Cài đặt

### 1. Cài đặt thư viện Python
```bash
pip install psycopg2-binary redis matplotlib numpy
```

### 2. Khởi động Database
```bash
docker-compose up -d
```

## Chạy Benchmark

```bash
python benchmark.py
```

## Kết quả
Script sẽ:
1. Insert 100,000 bản ghi vào PostgreSQL và Redis
2. Đọc ngẫu nhiên 10,000 bản ghi từ cả hai
3. Vẽ biểu đồ so sánh hiệu năng (file `benchmark_results.png`)
4. In ra báo cáo chi tiết

## Giải thích kết quả

### Tại sao Redis nhanh hơn?
1. **In-Memory Architecture**: Redis lưu toàn bộ dữ liệu trong RAM, không cần truy cập disk
2. **Không có Buffer Pool**: PostgreSQL phải quản lý buffer pool phức tạp
3. **Không có Write-Ahead Log**: Redis không cần ghi log trước khi commit (hoặc ghi async)
4. **Cấu trúc dữ liệu đơn giản**: Redis sử dụng hash tables tối ưu cho key-value lookup
5. **Không có Query Parser**: Redis không cần parse SQL queries phức tạp

### So sánh hiệu năng dự kiến
- **Insert**: Redis nhanh hơn 5-10x
- **Read**: Redis nhanh hơn 10-50x (đặc biệt với random reads)
