# 🚀 Hướng dẫn Nhanh - RTDB Labs

## Cài đặt Môi trường

### 1. Cài đặt Python & Dependencies
```bash
# Kiểm tra Python version (cần >= 3.8)
python3 --version

# Cài đặt pip packages cho tất cả labs
pip install matplotlib numpy psycopg2-binary redis supabase python-dotenv
```

### 2. Cài đặt Docker (cho Lab 1)
- **macOS**: Tải Docker Desktop từ [docker.com](https://www.docker.com/products/docker-desktop)
- **Linux**: 
  ```bash
  sudo apt-get update
  sudo apt-get install docker.io docker-compose
  ```

---

## 📂 Cấu trúc Project

```
rtdb/
├── README.md                    # Đề bài tổng quan
├── QUICKSTART.md               # File này
├── .gitignore
│
├── Lab1/                       # Benchmark Disk vs Memory
│   ├── README.md              # Hướng dẫn chi tiết
│   ├── docker-compose.yml     # PostgreSQL + Redis
│   ├── benchmark.py           # Script chính
│   └── requirements.txt
│
├── Lab2/                       # Scheduling Algorithms
│   ├── README.md
│   ├── scheduler_simulation.py
│   └── requirements.txt
│
├── Lab3/                       # Data Freshness
│   ├── README.md
│   ├── data_freshness_isars.py
│   └── requirements.txt
│
└── Lab4/                       # Real-time App với Supabase
    ├── README.md
    ├── dashboard.html         # Web dashboard
    ├── mission_simulator.py   # Data generator
    ├── setup.sql              # Database schema
    ├── .env.example
    └── requirements.txt
```

---

## 🧪 Chạy từng Lab

### Lab 1: Benchmark Performance

```bash
cd Lab1

# 1. Khởi động databases
docker-compose up -d

# 2. Đợi databases sẵn sàng (khoảng 10 giây)
sleep 10

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Chạy benchmark
python benchmark.py

# 5. Xem kết quả trong file benchmark_results.png
```

**Dừng databases:**
```bash
docker-compose down
```

---

### Lab 2: Transaction Scheduling

```bash
cd Lab2

# 1. Cài dependencies
pip install -r requirements.txt

# 2. Chạy mô phỏng cơ bản
python scheduler_simulation.py

# 3. Chạy với options
python scheduler_simulation.py --num-transactions 100 --detailed

# 4. Xem kết quả trong:
#    - scheduling_gantt_chart.png
#    - scheduling_comparison.png
```

---

### Lab 3: Data Freshness

```bash
cd Lab3

# 1. Cài dependencies
pip install -r requirements.txt

# 2. Chạy mô phỏng bình thường
python data_freshness_isars.py

# 3. Mô phỏng hệ thống quá tải (high delay)
python data_freshness_isars.py --processing-delay 0.3 --verbose

# 4. Thử nghiệm AVI khác nhau
python data_freshness_isars.py --avi 0.1  # AVI = 100ms

# 5. Xem kết quả trong data_freshness_analysis.png
```

---

### Lab 4: Real-time App với Supabase

#### Bước 1: Setup Supabase
1. Truy cập [supabase.com](https://supabase.com) → Đăng ký/Đăng nhập
2. Tạo project mới
3. Vào **SQL Editor** → Copy/paste nội dung file `setup.sql` → Run
4. Vào **Settings** → **API** → Copy:
   - Project URL
   - anon/public key

#### Bước 2: Cấu hình Local
```bash
cd Lab4

# 1. Cài dependencies
pip install -r requirements.txt

# 2. Tạo file .env
cp .env.example .env

# 3. Mở .env và điền thông tin Supabase
nano .env
# hoặc
code .env
```

#### Bước 3: Chạy ứng dụng

**Terminal 1 - Data Simulator:**
```bash
python mission_simulator.py
```

**Terminal 2 hoặc Trình duyệt - Dashboard:**
```bash
# Option 1: Mở trực tiếp
open dashboard.html

# Option 2: Dùng web server
python -m http.server 8000
# Truy cập: http://localhost:8000/dashboard.html
```

---

## 🎯 Tips & Troubleshooting

### Lab 1 - PostgreSQL/Redis không kết nối được
```bash
# Kiểm tra Docker đang chạy
docker ps

# Xem logs
docker-compose logs postgres
docker-compose logs redis

# Reset hoàn toàn
docker-compose down -v
docker-compose up -d
```

### Lab 2 - Muốn thay đổi số lượng transactions
```bash
python scheduler_simulation.py --num-transactions 200
```

### Lab 3 - Muốn xem log chi tiết
```bash
python data_freshness_isars.py --verbose
```

### Lab 4 - Lỗi "Import supabase could not be resolved"
```bash
# Cài đúng package
pip install supabase==2.3.4 python-dotenv==1.0.0

# Hoặc
pip install -r requirements.txt
```

### Lab 4 - Dashboard không nhận real-time updates
1. Kiểm tra đã chạy SQL setup chưa
2. Xác nhận đã enable Realtime:
   ```sql
   ALTER PUBLICATION supabase_realtime ADD TABLE mission_logs;
   ```
3. Check browser console (F12) để xem lỗi

---

## 📊 Yêu cầu Báo cáo

Sau khi hoàn thành các lab, tạo báo cáo theo cấu trúc:

```
MSSV_HoTen_RTDB_Labs/
├── Lab1/
│   ├── benchmark.py
│   ├── benchmark_results.png
│   └── screenshot.png
├── Lab2/
│   ├── scheduler_simulation.py
│   ├── scheduling_gantt_chart.png
│   └── scheduling_comparison.png
├── Lab3/
│   ├── data_freshness_isars.py
│   ├── data_freshness_analysis.png
│   └── screenshot.png
├── Lab4/
│   ├── dashboard.html
│   ├── mission_simulator.py
│   └── screenshot.png
└── REPORT.md (hoặc REPORT.pdf)
```

### Nội dung REPORT.md

```markdown
# Báo cáo Thực hành RTDB Labs

**Sinh viên:** [Họ tên]
**MSSV:** [Mã số]
**Lớp:** [Lớp]

## Lab 1: Benchmark Performance

### Kết quả đo đạc
- Insert PostgreSQL: X giây
- Insert Redis: Y giây
- Speedup: Z lần

### Phân tích
[Giải thích tại sao Redis nhanh hơn...]

### Screenshot
[Chèn ảnh benchmark_results.png]

---

## Lab 2: Scheduling

### Kết quả
- FCFS Miss Ratio: X%
- EDF Miss Ratio: Y%

### Phân tích
[So sánh 2 thuật toán...]

### Screenshot
[Chèn ảnh Gantt charts]

---

## Lab 3: Data Freshness

### Kết quả
- AVI: 200ms
- Rejection Rate: X%

### Phân tích
[Giải thích về freshness...]

---

## Lab 4: Real-time App

### Setup
[Mô tả quá trình setup Supabase]

### Kết quả
[Chụp màn hình dashboard đang hoạt động]

### So sánh Polling vs WebSocket
[Phân tích ưu/nhược điểm]

---

## Kết luận
[Tổng kết những gì học được]
```

---

## 🆘 Liên hệ & Support

Nếu gặp vấn đề:
1. Đọc kỹ README.md trong từng lab
2. Check logs/errors trong terminal
3. Google error message
4. Hỏi giảng viên/trợ giảng

**Chúc các bạn thực hành thành công! 🎉**
