
# Thực hành Hệ thống Thời gian thực: Real-Time Database (RTDB)

Chào mừng các bạn đến với chuỗi bài Lab thực hành về Cơ sở dữ liệu thời gian thực. Các bài tập này được thiết kế để hiện thực hóa các khái niệm lý thuyết đã học (ACID, Scheduling, Freshness, In-Memory Architecture).

## 📋 Mục lục

1.  [Yêu cầu chuẩn bị](#-yêu-cầu-chuẩn-bị)
2.  [Lab 1: Benchmark Disk-based vs In-Memory](#-lab-1-so-sánh-hiệu-năng-disk-based-vs-in-memory) - [Chi tiết](Lab1/README.md)
3.  [Lab 2: Mô phỏng thuật toán lập lịch (Scheduling)](#-lab-2-mô-phỏng-lập-lịch-giao-dịch-transaction-scheduling) - [Chi tiết](Lab2/README.md)
4.  [Lab 3: Quản lý độ tươi dữ liệu (Data Freshness) - Kịch bản iSARS](#-lab-3-quản-lý-độ-tươi-dữ-liệu-avi--data-freshness) - [Chi tiết](Lab3/README.md)
5.  [Lab 4: Xây dựng ứng dụng Real-time hiện đại](#-lab-4-real-time-app-với-supabase) - [Chi tiết](Lab4/README.md)

**📚 Tài liệu hướng dẫn:**
- [🚀 QUICKSTART.md](QUICKSTART.md) - Hướng dẫn nhanh để bắt đầu
- [📖 INDEX.md](INDEX.md) - Navigation và checklist đầy đủ
- [📂 PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Giải thích cấu trúc project
- [📊 SUMMARY.md](SUMMARY.md) - Tổng kết chi tiết

**🔧 Công cụ:**
- [check_environment.sh](check_environment.sh) - Script kiểm tra môi trường

-----

## 🛠 Yêu cầu chuẩn bị

Trước khi bắt đầu, sinh viên cần cài đặt môi trường sau:

  * **Ngôn ngữ:** Python 3.8+ (kèm thư viện `matplotlib`, `psycopg2`, `redis`).
  * **Database:** Docker & Docker Compose (để chạy PostgreSQL và Redis).
  * **Web:** Node.js (cho Lab 4) hoặc kiến thức HTML/JS cơ bản.
  * **Tài liệu tham khảo:** File bài giảng `slideRTDB.pdf`.

Cài đặt các thư viện Python cần thiết:

```bash
pip install matplotlib redis psycopg2-binary numpy
```

-----

## 🧪 Lab 1: So sánh hiệu năng Disk-based vs In-Memory

**Mục tiêu:** Hiểu rõ sự chênh lệch về **Latency (Độ trễ)** và **Throughput (Thông lượng)** giữa cơ sở dữ liệu truyền thống và RTDB.

  * **Tham khảo lý thuyết:** Slide 4 (Comparison) , Slide 11 (In-Memory OLTP).

### Nội dung thực hiện

1.  **Dựng môi trường:** Sử dụng Docker để khởi chạy 1 container PostgreSQL (đại diện Disk-based) và 1 container Redis (đại diện In-Memory).
2.  **Viết Script Benchmark:**
      * Tạo giả lập 100,000 bản ghi dữ liệu cảm biến (gồm `sensor_id`, `value`, `timestamp`).
      * Đo thời gian **Insert** toàn bộ dữ liệu vào PostgreSQL và Redis.
      * Đo thời gian **Read** ngẫu nhiên 10,000 bản ghi từ cả hai.
3.  **Báo cáo:**
      * Vẽ biểu đồ cột so sánh thời gian thực thi.
      * Giải thích tại sao Redis nhanh hơn dựa trên kiến trúc (gợi ý: buffer pool, logging, cấu trúc dữ liệu).

-----

## ⏱ Lab 2: Mô phỏng Lập lịch Giao dịch (Transaction Scheduling)

**Mục tiêu:** Hiểu cách hệ thống RTDB ưu tiên xử lý để giảm thiểu tỷ lệ trễ hạn (**Deadline Miss Ratio**).

  * **Tham khảo lý thuyết:** Slide 8 (Scheduling EDF/FCFS) , Slide 6 (Miss Ratio KPI).

### Nội dung thực hiện

1.  **Input:** Tạo một danh sách các Transaction giả lập ($T_1...T_n$), mỗi transaction có cấu trúc:
      * `arrival_time`: Thời điểm đến.
      * `execution_time`: Thời gian cần để xử lý.
      * `deadline`: Hạn chót phải hoàn thành.
2.  **Implementation:** Viết chương trình Python mô phỏng hàng đợi (Queue) xử lý theo 2 thuật toán:
      * **FCFS (First-Come First-Served):** Đến trước làm trước.
      * **EDF (Earliest Deadline First):** Deadline gần nhất làm trước.
3.  **Đánh giá:**
      * Chạy mô phỏng với cùng một tập dữ liệu đầu vào.
      * Tính toán và in ra **Miss Ratio** (Tỷ lệ % số task bị trượt deadline) của cả 2 thuật toán.
      * Nhận xét về hiệu quả của EDF trong môi trường thời gian thực.

-----

## 🚑 Lab 3: Quản lý độ tươi dữ liệu (AVI & Data Freshness)

**Mục tiêu:** Áp dụng khái niệm **AVI (Absolute Validity Interval)** trong bối cảnh thực tế (Hệ thống tìm kiếm cứu nạn iSARS).

  * **Tham khảo lý thuyết:** Slide 6 (AVI/RVI) , Slide 10 (QoS Freshness).

### Kịch bản (Scenario)

Hệ thống **iSARS** nhận tọa độ GPS từ thiết bị của nạn nhân. Để robot cứu hộ hoạt động chính xác, tọa độ chỉ có giá trị sử dụng trong vòng **200ms** (AVI = 0.2s). Nếu quá thời gian này, dữ liệu bị coi là "ôi thiu" (stale) và không an toàn để điều hướng robot.

### Nội dung thực hiện

1.  **Mô phỏng Stream:** Viết script sinh dữ liệu GPS (`victim_id`, `lat`, `long`, `timestamp`) liên tục với tốc độ cao.
2.  **Bộ lọc độ tươi (Freshness Filter):**
      * Viết hàm kiểm tra trước khi lưu vào DB hoặc xử lý:
        $$CurrentTime - DataTimestamp \le AVI$$
      * Nếu thỏa mãn: Chấp nhận (Commit).
      * Nếu vi phạm: Loại bỏ (Discard) và ghi Log cảnh báo.
3.  **Thử nghiệm:**
      * Tăng độ trễ xử lý nhân tạo (dùng `time.sleep()`) trong hệ thống.
      * Quan sát và thống kê tỷ lệ dữ liệu bị loại bỏ khi hệ thống bị quá tải.

-----

## ⚡ Lab 4: Real-time App với Supabase

**Mục tiêu:** Tiếp cận công nghệ RTDB hiện đại, mô hình Publish/Subscribe thay vì Polling.

  * **Tham khảo lý thuyết:** Slide 7 (Kiến trúc Netflix/Kafka) , Slide 13 (Supabase Realtime).

### Nội dung thực hiện

1.  **Setup:**
      * Tạo tài khoản [Supabase](https://supabase.com) (miễn phí) hoặc tự host bằng Docker.
      * Tạo bảng `mission_logs` (gồm `id`, `message`, `created_at`). Bật tính năng "Realtime" cho bảng này.
2.  **Client Application:**
      * Viết một trang HTML/JS đơn giản sử dụng `supabase-js`.
      * Đăng ký kênh (Subscribe) để lắng nghe sự kiện `INSERT` trên bảng `mission_logs`.
      * Khi có dữ liệu mới, tự động hiển thị lên giao diện **ngay lập tức** mà không cần reload trang.
3.  **Kiểm thử:**
      * Dùng SQL Editor của Supabase để Insert 1 dòng dữ liệu.
      * Xác nhận dữ liệu xuất hiện trên Client App gần như tức thời.
      * So sánh trải nghiệm này với mô hình Polling truyền thống (F5 liên tục).

-----

## 📝 Yêu cầu nộp bài

1.  Tạo thư mục theo định dạng: `MSSV_HoTen_RTDB_Labs`.
2.  Bên trong chứa 4 thư mục con tương ứng `Lab1`, `Lab2`, `Lab3`, `Lab4` chứa source code và ảnh chụp màn hình kết quả chạy.
3.  File báo cáo `REPORT.md` (hoặc PDF) tóm tắt kết quả đo đạc và trả lời các câu hỏi lý thuyết trong từng bài.
4.  Nén thành file `.zip` và nộp lên hệ thống quản lý lớp học.

**Chúc các bạn thực hành tốt\!**