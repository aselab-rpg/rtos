# 📁 Cấu trúc Project - RTDB Labs

```
rtdb/
│
├── 📄 README.md                    # Đề bài và yêu cầu tổng quan
├── 📄 QUICKSTART.md                # Hướng dẫn nhanh để bắt đầu
├── 📄 PROJECT_STRUCTURE.md         # File này - Giải thích cấu trúc
├── 🔧 check_environment.sh         # Script kiểm tra môi trường
├── 📄 .gitignore                   # Git ignore rules
│
├── 📂 Lab1/                        # Lab 1: Benchmark Performance
│   ├── 📄 README.md               # Hướng dẫn chi tiết Lab 1
│   ├── 🐍 benchmark.py            # Script chính - so sánh PostgreSQL vs Redis
│   ├── 🐳 docker-compose.yml      # Docker setup cho databases
│   └── 📄 requirements.txt        # Python dependencies
│
├── 📂 Lab2/                        # Lab 2: Transaction Scheduling
│   ├── 📄 README.md               # Hướng dẫn chi tiết Lab 2
│   ├── 🐍 scheduler_simulation.py # Mô phỏng FCFS vs EDF
│   └── 📄 requirements.txt        # Python dependencies
│
├── 📂 Lab3/                        # Lab 3: Data Freshness
│   ├── 📄 README.md               # Hướng dẫn chi tiết Lab 3
│   ├── 🐍 data_freshness_isars.py # Mô phỏng hệ thống iSARS
│   └── 📄 requirements.txt        # Python dependencies
│
└── 📂 Lab4/                        # Lab 4: Real-time App với Supabase
    ├── 📄 README.md               # Hướng dẫn chi tiết Lab 4
    ├── 🌐 dashboard.html          # Web dashboard real-time
    ├── 🐍 mission_simulator.py    # Data generator
    ├── 🗄️ setup.sql               # Database schema cho Supabase
    ├── 📄 .env.example            # Template cho environment variables
    └── 📄 requirements.txt        # Python dependencies
```

---

## 📋 Chi tiết từng thành phần

### Root Level Files

#### `README.md`
- **Mục đích**: Đề bài chính của bài thực hành
- **Nội dung**: 
  - Giới thiệu về RTDB
  - Yêu cầu chuẩn bị
  - Mô tả 4 labs
  - Yêu cầu nộp bài

#### `QUICKSTART.md`
- **Mục đích**: Hướng dẫn nhanh để bắt đầu
- **Nội dung**:
  - Cài đặt môi trường
  - Cấu trúc project
  - Lệnh chạy từng lab
  - Troubleshooting
  - Template báo cáo

#### `check_environment.sh`
- **Mục đích**: Kiểm tra môi trường tự động
- **Chức năng**:
  - Kiểm tra Python, pip
  - Kiểm tra Docker
  - Kiểm tra Python packages
  - Đưa ra khuyến nghị

**Cách dùng:**
```bash
./check_environment.sh
```

---

### Lab 1: Benchmark Disk-based vs In-Memory

**Mục tiêu**: So sánh hiệu năng PostgreSQL (Disk) vs Redis (Memory)

#### Files:
- `benchmark.py`: Script chính
  - Tạo 100,000 bản ghi dữ liệu cảm biến
  - Benchmark INSERT vào cả 2 databases
  - Benchmark READ ngẫu nhiên
  - Tạo biểu đồ so sánh
  
- `docker-compose.yml`: 
  - PostgreSQL container (port 5432)
  - Redis container (port 6379)
  
#### Output:
- `benchmark_results.png`: Biểu đồ so sánh

#### Khái niệm học được:
- In-Memory vs Disk-based architecture
- Latency & Throughput
- Buffer pool management
- Write-Ahead Logging

---

### Lab 2: Transaction Scheduling

**Mục tiêu**: So sánh FCFS vs EDF trong real-time systems

#### Files:
- `scheduler_simulation.py`: Script chính
  - Tạo transactions với deadline
  - Mô phỏng FCFS (First-Come First-Served)
  - Mô phỏng EDF (Earliest Deadline First)
  - Tính toán Miss Ratio
  - Vẽ Gantt Charts

#### Output:
- `scheduling_gantt_chart.png`: Gantt chart so sánh
- `scheduling_comparison.png`: Biểu đồ thống kê

#### Khái niệm học được:
- Transaction scheduling algorithms
- Deadline miss ratio
- Real-time constraints
- QoS metrics

---

### Lab 3: Data Freshness Management

**Mục tiêu**: Hiểu và áp dụng AVI (Absolute Validity Interval)

#### Files:
- `data_freshness_isars.py`: Script chính
  - Mô phỏng GPS stream từ nạn nhân
  - Áp dụng Freshness Filter (AVI = 200ms)
  - Thống kê acceptance/rejection rate
  - Phân tích độ tươi dữ liệu

#### Output:
- `data_freshness_analysis.png`: Biểu đồ phân tích

#### Khái niệm học được:
- Absolute Validity Interval (AVI)
- Relative Validity Interval (RVI)
- Data staleness
- Quality of Service (QoS)
- Trade-offs trong real-time systems

---

### Lab 4: Real-time Application với Supabase

**Mục tiêu**: Xây dựng ứng dụng real-time hiện đại

#### Files:

**`setup.sql`**
- Tạo bảng `mission_logs`
- Setup indexes
- Cấu hình Row Level Security
- Enable Realtime

**`dashboard.html`**
- Web dashboard với WebSocket
- Subscribe to real-time updates
- Hiển thị mission logs theo thời gian thực
- Statistics & visualization

**`mission_simulator.py`**
- Tạo dữ liệu mission logs ngẫu nhiên
- Insert vào Supabase
- Mô phỏng nhiều agents và missions

**`.env.example`**
- Template cho Supabase credentials

#### Khái niệm học được:
- Publish/Subscribe pattern
- WebSocket vs HTTP Polling
- Change Data Capture (CDC)
- Modern RTDB architecture
- Supabase Realtime engine

---

## 🔄 Workflow Thực hiện

### Bước 1: Setup môi trường
```bash
./check_environment.sh
```

### Bước 2: Cài đặt dependencies
```bash
# Cài tất cả
pip install matplotlib numpy psycopg2-binary redis supabase python-dotenv

# Hoặc từng lab
cd Lab1 && pip install -r requirements.txt
cd Lab2 && pip install -r requirements.txt
cd Lab3 && pip install -r requirements.txt
cd Lab4 && pip install -r requirements.txt
```

### Bước 3: Thực hiện từng lab
Xem chi tiết trong `QUICKSTART.md`

### Bước 4: Tạo báo cáo
Template trong `QUICKSTART.md`

---

## 📦 Dependencies Summary

### Lab 1
- `psycopg2-binary` - PostgreSQL driver
- `redis` - Redis client
- `matplotlib` - Plotting
- `numpy` - Numerical computing

### Lab 2
- `matplotlib` - Plotting
- `numpy` - Numerical computing

### Lab 3
- `matplotlib` - Plotting
- `numpy` - Numerical computing

### Lab 4
- `supabase` - Supabase client
- `python-dotenv` - Environment variables

---

## 🎯 Learning Outcomes

Sau khi hoàn thành 4 labs, sinh viên sẽ:

1. ✅ Hiểu sự khác biệt giữa Disk-based và In-Memory databases
2. ✅ Nắm vững các thuật toán scheduling cho real-time systems
3. ✅ Biết cách quản lý độ tươi dữ liệu (freshness)
4. ✅ Có kinh nghiệm với modern real-time technology stack
5. ✅ Hiểu kiến trúc và trade-offs của RTDB
6. ✅ Biết so sánh Polling vs WebSocket
7. ✅ Thực hành với Docker, PostgreSQL, Redis, Supabase

---

## 💡 Tips

- Đọc README.md của từng lab trước khi bắt đầu
- Chạy `check_environment.sh` để đảm bảo môi trường đúng
- Screenshot kết quả để làm báo cáo
- Thử thay đổi tham số để hiểu rõ hơn
- Lab 4 cần Internet để kết nối Supabase

---

## 🆘 Troubleshooting

Xem phần **Tips & Troubleshooting** trong `QUICKSTART.md`

---

**Happy coding! 🚀**
