# Lab 4: Real-time App với Supabase

## Mục tiêu
Tiếp cận công nghệ RTDB hiện đại với mô hình **Publish/Subscribe** thay vì Polling truyền thống. Xây dựng ứng dụng Real-time tracking cho hệ thống Mission Control.

## Kiến trúc

```
[Mission Control Dashboard] ← WebSocket ← [Supabase Realtime]
                                                ↑
                                          [PostgreSQL]
                                                ↑
                                    [Data Simulator/Agents]
```

## Yêu cầu

### Backend
- Python 3.8+
- Thư viện: `supabase`, `python-dotenv`

### Frontend
- Trình duyệt web hiện đại (Chrome, Firefox, Safari)
- Hoặc Node.js (nếu muốn chạy local server)

## Setup

### 1. Tạo tài khoản Supabase

1. Truy cập [https://supabase.com](https://supabase.com)
2. Đăng ký tài khoản miễn phí
3. Tạo project mới
4. Lấy **Project URL** và **anon key** từ Settings → API

### 2. Cấu hình Database

Chạy SQL sau trong Supabase SQL Editor:

```sql
-- Tạo bảng mission_logs
CREATE TABLE mission_logs (
    id BIGSERIAL PRIMARY KEY,
    mission_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bật Row Level Security (RLS)
ALTER TABLE mission_logs ENABLE ROW LEVEL SECURITY;

-- Tạo policy để cho phép đọc public
CREATE POLICY "Allow public read access"
ON mission_logs FOR SELECT
USING (true);

-- Tạo policy để cho phép insert public (cho demo)
CREATE POLICY "Allow public insert access"
ON mission_logs FOR INSERT
WITH CHECK (true);

-- Bật Realtime cho bảng này
ALTER PUBLICATION supabase_realtime ADD TABLE mission_logs;
```

### 3. Cài đặt dependencies

```bash
pip install supabase python-dotenv
```

### 4. Tạo file .env

Tạo file `.env` với nội dung:

```
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
```

## Chạy ứng dụng

### 1. Khởi động Data Simulator (Terminal 1)

```bash
python mission_simulator.py
```

Script này sẽ tạo các mission logs giả lập liên tục.

### 2. Mở Dashboard (Trình duyệt)

Mở file `dashboard.html` trong trình duyệt:

```bash
# macOS
open dashboard.html

# Linux
xdg-open dashboard.html

# Windows
start dashboard.html
```

Hoặc chạy local server:

```bash
python -m http.server 8000
# Truy cập: http://localhost:8000/dashboard.html
```

## Tính năng

### Mission Control Dashboard
- ✅ Real-time updates (không cần reload trang)
- ✅ Hiển thị các mission logs theo thời gian thực
- ✅ Màu sắc theo mức độ (info, warning, error, critical)
- ✅ Bản đồ hiển thị vị trí agents
- ✅ Thống kê số lượng missions
- ✅ Auto-scroll khi có dữ liệu mới

### Data Simulator
- Tạo các mission events ngẫu nhiên
- Nhiều agents hoạt động song song
- Các mức độ nghiêm trọng khác nhau
- GPS coordinates giả lập

## So sánh với Polling

### ❌ Polling (Cách cũ)
```javascript
// Phải gọi API liên tục
setInterval(() => {
    fetch('/api/logs')
        .then(res => res.json())
        .then(data => updateUI(data));
}, 1000);  // Mỗi 1 giây
```

**Nhược điểm:**
- Tốn bandwidth (gọi API liên tục)
- Độ trễ cao (1-5 giây)
- Tải server cao
- Không truly real-time

### ✅ Supabase Realtime (Cách mới)
```javascript
// Subscribe một lần, nhận updates tự động
supabase
    .channel('mission-logs')
    .on('postgres_changes', 
        { event: 'INSERT', schema: 'public', table: 'mission_logs' },
        (payload) => updateUI(payload.new)
    )
    .subscribe();
```

**Ưu điểm:**
- Truly real-time (< 100ms)
- Tiết kiệm bandwidth
- Server push (WebSocket)
- Scalable

## Kiến trúc Supabase Realtime

```
[Client] ←WebSocket→ [Realtime Server] → [PostgreSQL WAL]
                           ↓
                    [Change Capture]
                           ↓
                    [Broadcast to all subscribers]
```

**Cơ chế:**
1. PostgreSQL ghi vào Write-Ahead Log (WAL)
2. Supabase Realtime đọc WAL
3. Parse changes và broadcast qua WebSocket
4. Tất cả clients đang subscribe nhận update ngay lập tức

## Bài học

1. **WebSocket > HTTP Polling**: Cho real-time applications
2. **Publish/Subscribe pattern**: Scalable và efficient
3. **Modern RTDB**: Kết hợp database truyền thống với real-time capabilities
4. **Change Data Capture (CDC)**: Cơ chế quan trọng cho real-time systems

## Mở rộng

### Thêm Authentication
```javascript
const { data, error } = await supabase.auth.signUp({
    email: 'user@example.com',
    password: 'password'
});
```

### Filter dữ liệu
```javascript
supabase
    .channel('critical-only')
    .on('postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'mission_logs',
          filter: 'severity=eq.critical' },
        handleCritical
    )
    .subscribe();
```

### Presence (Xem ai đang online)
```javascript
const channel = supabase.channel('room1');
channel.on('presence', { event: 'join' }, ({ key, newPresences }) => {
    console.log('New users joined:', newPresences);
});
```
