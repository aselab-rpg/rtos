-- Lab 4: Supabase Database Setup
-- Chạy script này trong Supabase SQL Editor

-- 1. Tạo bảng mission_logs
CREATE TABLE IF NOT EXISTS mission_logs (
    id BIGSERIAL PRIMARY KEY,
    mission_id VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tạo indexes để tối ưu queries
CREATE INDEX IF NOT EXISTS idx_mission_logs_created_at ON mission_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mission_logs_severity ON mission_logs(severity);
CREATE INDEX IF NOT EXISTS idx_mission_logs_mission_id ON mission_logs(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_logs_agent_id ON mission_logs(agent_id);

-- 3. Bật Row Level Security (RLS)
ALTER TABLE mission_logs ENABLE ROW LEVEL SECURITY;

-- 4. Tạo policy để cho phép public đọc (cho demo)
CREATE POLICY "Allow public read access"
ON mission_logs FOR SELECT
USING (true);

-- 5. Tạo policy để cho phép public insert (cho demo)
-- Trong production, nên giới hạn quyền này
CREATE POLICY "Allow public insert access"
ON mission_logs FOR INSERT
WITH CHECK (true);

-- 6. Bật Realtime cho bảng này (QUAN TRỌNG!)
ALTER PUBLICATION supabase_realtime ADD TABLE mission_logs;

-- 7. Kiểm tra
-- Chạy query này để xác nhận table đã được tạo
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'mission_logs'
ORDER BY ordinal_position;

-- 8. Insert dữ liệu mẫu (optional)
INSERT INTO mission_logs (mission_id, agent_id, message, severity, latitude, longitude) VALUES
('RESCUE_001', 'ALPHA', 'Khởi động nhiệm vụ cứu hộ', 'info', 21.0285, 105.8542),
('PATROL_001', 'BRAVO', '⚠️ Phát hiện chướng ngại vật', 'warning', 21.0290, 105.8550),
('RESCUE_001', 'ALPHA', '🚨 KHẨN CẤP: Phát hiện nạn nhân!', 'critical', 21.0295, 105.8545);

-- Xác nhận dữ liệu
SELECT * FROM mission_logs ORDER BY created_at DESC LIMIT 10;
