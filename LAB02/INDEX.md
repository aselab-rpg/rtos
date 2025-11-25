# 🎓 RTDB Labs - Complete Practical Guide
## Real-Time Database System - Hands-on Labs

---

## 📖 BẮT ĐẦU TỪ ĐÂY!

### 🚀 Nếu bạn là sinh viên mới bắt đầu:

1. **Đọc đề bài tổng quan**: [`README.md`](README.md)
2. **Kiểm tra môi trường**: 
   ```bash
   ./check_environment.sh
   ```
3. **Đọc hướng dẫn nhanh**: [`QUICKSTART.md`](QUICKSTART.md)
4. **Bắt đầu với Lab 1**: [`Lab1/README.md`](Lab1/README.md)

---

## 📂 Danh sách Files và Mục đích

### 🎯 Documents chính (Đọc theo thứ tự này)

| File | Mục đích | Khi nào đọc |
|------|----------|-------------|
| [`README.md`](README.md) | Đề bài và yêu cầu tổng quan | Đọc đầu tiên |
| [`QUICKSTART.md`](QUICKSTART.md) | Hướng dẫn nhanh, troubleshooting | Trước khi bắt đầu code |
| [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) | Giải thích cấu trúc project | Khi muốn hiểu rõ cấu trúc |
| [`SUMMARY.md`](SUMMARY.md) | Tóm tắt toàn bộ project | Sau khi hoàn thành |
| [`INDEX.md`](INDEX.md) | File này - Điều hướng | Bất cứ lúc nào |

### 🧪 Labs (Làm theo thứ tự)

| Lab | Chủ đề | Files chính | Đầu ra |
|-----|--------|-------------|--------|
| **Lab 1** | Benchmark Performance | [`benchmark.py`](Lab1/benchmark.py)<br>[`docker-compose.yml`](Lab1/docker-compose.yml) | `benchmark_results.png` |
| **Lab 2** | Transaction Scheduling | [`scheduler_simulation.py`](Lab2/scheduler_simulation.py) | `scheduling_gantt_chart.png`<br>`scheduling_comparison.png` |
| **Lab 3** | Data Freshness | [`data_freshness_isars.py`](Lab3/data_freshness_isars.py) | `data_freshness_analysis.png` |
| **Lab 4** | Real-time App | [`dashboard.html`](Lab4/dashboard.html)<br>[`mission_simulator.py`](Lab4/mission_simulator.py)<br>[`setup.sql`](Lab4/setup.sql) | Web dashboard |

### 🔧 Utility Files

| File | Mục đích |
|------|----------|
| `check_environment.sh` | Kiểm tra môi trường tự động |
| `.gitignore` | Git ignore rules |
| `Lab*/requirements.txt` | Python dependencies cho từng lab |
| `Lab4/.env.example` | Template cho Supabase config |

---

## 🎯 Roadmap Học tập

```
TUẦN 1: Setup & Lab 1
├── Ngày 1: Đọc tài liệu, setup môi trường
├── Ngày 2: Cài Docker, chạy Lab 1
└── Ngày 3: Phân tích kết quả, viết báo cáo Lab 1

TUẦN 2: Lab 2 & Lab 3
├── Ngày 1: Làm Lab 2 (Scheduling)
├── Ngày 2: Làm Lab 3 (Data Freshness)
└── Ngày 3: Viết báo cáo Lab 2 & 3

TUẦN 3: Lab 4 & Hoàn thiện
├── Ngày 1-2: Setup Supabase, làm Lab 4
├── Ngày 3: Viết báo cáo Lab 4
└── Ngày 4: Hoàn thiện báo cáo tổng, screenshot
```

---

## 📝 Checklist Hoàn thành

### ✅ Lab 1: Benchmark Performance
- [ ] Đã cài Docker và Docker Compose
- [ ] Chạy thành công `docker-compose up -d`
- [ ] Chạy thành công `python benchmark.py`
- [ ] Có file `benchmark_results.png`
- [ ] Hiểu tại sao Redis nhanh hơn PostgreSQL
- [ ] Screenshot kết quả

### ✅ Lab 2: Transaction Scheduling
- [ ] Chạy thành công `python scheduler_simulation.py`
- [ ] Có file `scheduling_gantt_chart.png`
- [ ] Có file `scheduling_comparison.png`
- [ ] Hiểu sự khác biệt giữa FCFS và EDF
- [ ] Hiểu khái niệm Miss Ratio
- [ ] Screenshot kết quả

### ✅ Lab 3: Data Freshness
- [ ] Chạy thành công `python data_freshness_isars.py`
- [ ] Có file `data_freshness_analysis.png`
- [ ] Hiểu khái niệm AVI (Absolute Validity Interval)
- [ ] Hiểu khi nào dữ liệu bị "stale"
- [ ] Chạy thử với `--processing-delay` khác nhau
- [ ] Screenshot kết quả

### ✅ Lab 4: Real-time App
- [ ] Đã tạo tài khoản Supabase
- [ ] Chạy thành công `setup.sql`
- [ ] Cấu hình file `.env`
- [ ] Chạy thành công `python mission_simulator.py`
- [ ] Dashboard hiển thị real-time updates
- [ ] Hiểu sự khác biệt giữa WebSocket và Polling
- [ ] Screenshot dashboard đang hoạt động

### ✅ Báo cáo
- [ ] Có báo cáo `REPORT.md` hoặc `REPORT.pdf`
- [ ] Đầy đủ 4 phần cho 4 labs
- [ ] Có screenshots cho tất cả labs
- [ ] Có phân tích và giải thích kết quả
- [ ] Có phần kết luận tổng quan

---

## 🎓 Learning Path

### 1️⃣ Concepts trước khi bắt đầu

**Cần biết:**
- Python cơ bản
- SQL cơ bản
- Command line basics

**Nên biết:**
- Docker basics
- Database fundamentals
- Web development basics (cho Lab 4)

### 2️⃣ Concepts học được từ Labs

**Lab 1:**
- In-Memory vs Disk-based architecture
- Latency & Throughput metrics
- Buffer pool management
- Write-Ahead Logging (WAL)

**Lab 2:**
- Real-time scheduling algorithms
- FCFS (First-Come First-Served)
- EDF (Earliest Deadline First)
- Deadline constraints
- Miss Ratio calculation

**Lab 3:**
- Data freshness management
- AVI (Absolute Validity Interval)
- RVI (Relative Validity Interval)
- Quality of Service (QoS)
- Staleness detection

**Lab 4:**
- Modern RTDB architecture
- Publish/Subscribe pattern
- WebSocket technology
- Change Data Capture (CDC)
- Supabase platform

---

## 🔗 Quick Links

### Documentation
- [Đề bài tổng quan](README.md)
- [Hướng dẫn nhanh](QUICKSTART.md)
- [Cấu trúc project](PROJECT_STRUCTURE.md)
- [Tổng kết](SUMMARY.md)

### Labs
- [Lab 1 README](Lab1/README.md)
- [Lab 2 README](Lab2/README.md)
- [Lab 3 README](Lab3/README.md)
- [Lab 4 README](Lab4/README.md)

### Source Code
- [Lab 1 Source](Lab1/benchmark.py)
- [Lab 2 Source](Lab2/scheduler_simulation.py)
- [Lab 3 Source](Lab3/data_freshness_isars.py)
- [Lab 4 Dashboard](Lab4/dashboard.html)
- [Lab 4 Simulator](Lab4/mission_simulator.py)

---

## 🆘 Cần giúp đỡ?

### Bước 1: Kiểm tra môi trường
```bash
./check_environment.sh
```

### Bước 2: Đọc README của lab
Mỗi lab có README riêng với hướng dẫn chi tiết

### Bước 3: Xem Troubleshooting
File [`QUICKSTART.md`](QUICKSTART.md) có phần Troubleshooting

### Bước 4: Kiểm tra logs
- Terminal output
- Browser console (F12) cho Lab 4
- Docker logs: `docker-compose logs`

---

## 📊 Progress Tracker

Đánh dấu khi hoàn thành:

```
Setup môi trường          [ ]
Lab 1 hoàn thành          [ ]
Lab 2 hoàn thành          [ ]
Lab 3 hoàn thành          [ ]
Lab 4 hoàn thành          [ ]
Báo cáo hoàn thành        [ ]
Screenshot đầy đủ         [ ]
Nén file để nộp           [ ]
```

---

## 🎯 Tips để đạt điểm cao

1. ✅ **Chạy thành công tất cả labs** - 40%
2. ✅ **Screenshots rõ ràng** - 15%
3. ✅ **Báo cáo chi tiết, có phân tích** - 30%
4. ✅ **Thử nghiệm với parameters khác nhau** - 10%
5. ✅ **Code sạch, có comments** - 5%

---

## 📧 Submit Format

```
MSSV_HoTen_RTDB_Labs.zip
├── Lab1/
├── Lab2/
├── Lab3/
├── Lab4/
└── REPORT.md (hoặc REPORT.pdf)
```

---

## 🏆 Final Words

> "The best way to learn is by doing."

Các labs này được thiết kế để bạn:
- ✅ **Hiểu** concepts thông qua thực hành
- ✅ **Trải nghiệm** với real technologies
- ✅ **Áp dụng** lý thuyết vào thực tế
- ✅ **Xây dựng** portfolio projects

**Chúc bạn học tốt và thành công! 🚀**

---

*Last updated: 2024*
*Course: Real-Time Database Systems*
