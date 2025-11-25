#!/usr/bin/env python3
"""
Lab 4: Mission Simulator
Tạo dữ liệu mission logs giả lập cho hệ thống Real-time
"""

import os
import time
import random
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate credentials
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL và SUPABASE_KEY chưa được cấu hình!")
    print("\nTạo file .env với nội dung:")
    print("SUPABASE_URL=your_project_url")
    print("SUPABASE_KEY=your_anon_key")
    exit(1)

# Mission scenarios
MISSIONS = [
    "RESCUE_001", "RESCUE_002", "RESCUE_003",
    "PATROL_001", "PATROL_002",
    "SURVEY_001", "SURVEY_002"
]

AGENTS = [
    "ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT"
]

MESSAGES = {
    "info": [
        "Đang tiến về vị trí mục tiêu",
        "Đã xác định được tín hiệu",
        "Tiến hành quét khu vực",
        "Truyền dữ liệu về trung tâm",
        "Đã hoàn thành checkpoint",
        "Đang di chuyển theo route đã lập",
        "Cập nhật tọa độ GPS",
        "Kiểm tra thiết bị - All systems nominal",
        "Đang thực hiện nhiệm vụ theo kế hoạch",
        "Thu thập dữ liệu môi trường"
    ],
    "warning": [
        "⚠️ Phát hiện chướng ngại vật",
        "⚠️ Tín hiệu GPS yếu",
        "⚠️ Mức pin còn 30%",
        "⚠️ Gặp khó khăn địa hình",
        "⚠️ Thời tiết xấu ảnh hưởng",
        "⚠️ Nhiệt độ động cơ cao",
        "⚠️ Cần hỗ trợ thêm",
        "⚠️ Phát hiện anomaly",
    ],
    "error": [
        "🔴 Lỗi cảm biến radar",
        "🔴 Mất kết nối tạm thời",
        "🔴 Không thể tiếp cận mục tiêu",
        "🔴 Lỗi hệ thống điều hướng",
        "🔴 Thiết bị camera bị hỏng",
    ],
    "critical": [
        "🚨 KHẨN CẤP: Phát hiện nạn nhân!",
        "🚨 Mức pin cực thấp - Cần rescue ngay!",
        "🚨 Agent bị mắc kẹt",
        "🚨 Tín hiệu cấp cứu từ nạn nhân",
        "🚨 Thiết bị trục trặc nghiêm trọng",
    ]
}

# Coordinates around Hanoi
BASE_LAT = 21.0285
BASE_LNG = 105.8542


def create_mission_log(supabase: Client) -> dict:
    """Tạo một mission log ngẫu nhiên"""
    
    mission_id = random.choice(MISSIONS)
    agent_id = random.choice(AGENTS)
    
    # Weight severity (nhiều info hơn critical)
    severity = random.choices(
        ['info', 'warning', 'error', 'critical'],
        weights=[70, 20, 7, 3]
    )[0]
    
    message = random.choice(MESSAGES[severity])
    
    # Random GPS coordinates
    lat = BASE_LAT + random.uniform(-0.05, 0.05)
    lng = BASE_LNG + random.uniform(-0.05, 0.05)
    
    log_data = {
        "mission_id": mission_id,
        "agent_id": agent_id,
        "message": message,
        "severity": severity,
        "latitude": lat,
        "longitude": lng
    }
    
    try:
        result = supabase.table("mission_logs").insert(log_data).execute()
        return {"success": True, "data": log_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def print_log(log_data: dict, index: int):
    """In log ra console với màu sắc"""
    
    colors = {
        'info': '\033[94m',      # Blue
        'warning': '\033[93m',   # Yellow
        'error': '\033[91m',     # Red
        'critical': '\033[95m'   # Magenta
    }
    reset = '\033[0m'
    
    severity = log_data['severity']
    color = colors.get(severity, '')
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    print(f"{color}[{index:04d}] {timestamp} | {severity.upper():8} | "
          f"{log_data['mission_id']:12} | {log_data['agent_id']:8} | "
          f"{log_data['message'][:60]}{reset}")


def main():
    print("=" * 100)
    print("MISSION SIMULATOR - Real-time Data Generator")
    print("=" * 100)
    
    print(f"\n🔌 Đang kết nối đến Supabase...")
    print(f"   URL: {SUPABASE_URL}")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test connection
        supabase.table("mission_logs").select("count").limit(1).execute()
        print("✓ Kết nối thành công!")
        
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        print("\nKiểm tra:")
        print("1. SUPABASE_URL và SUPABASE_KEY trong file .env")
        print("2. Đã tạo bảng 'mission_logs' trong Supabase")
        print("3. Đã bật Realtime cho bảng mission_logs")
        return
    
    print(f"\n📊 Cấu hình:")
    print(f"   Missions: {', '.join(MISSIONS)}")
    print(f"   Agents: {', '.join(AGENTS)}")
    print(f"   Interval: 2-5 giây (ngẫu nhiên)")
    
    print(f"\n{'='*100}")
    print("BẮT ĐẦU SIMULATION (Nhấn Ctrl+C để dừng)")
    print(f"{'='*100}\n")
    
    print(f"{'INDEX':<6} | {'TIME':<8} | {'SEVERITY':<8} | {'MISSION':<12} | {'AGENT':<8} | {'MESSAGE':<60}")
    print("-" * 100)
    
    count = 0
    
    try:
        while True:
            count += 1
            
            # Tạo mission log
            result = create_mission_log(supabase)
            
            if result["success"]:
                print_log(result["data"], count)
            else:
                print(f"\033[91m[ERROR] Không thể insert: {result['error']}\033[0m")
            
            # Random delay 2-5 giây
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print(f"\n\n{'='*100}")
        print(f"✓ Đã dừng simulation")
        print(f"📊 Tổng số logs đã tạo: {count}")
        print(f"{'='*100}")


if __name__ == "__main__":
    main()
