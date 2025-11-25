#!/usr/bin/env python3
"""
Lab 1: Benchmark Disk-based (PostgreSQL) vs In-Memory (Redis)
So sánh hiệu năng Insert và Read
"""

import time
import random
import psycopg2
import redis
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Cấu hình
NUM_RECORDS = 100000
NUM_READS = 10000

# Kết nối PostgreSQL
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'rtdb_benchmark',
    'user': 'rtdb_user',
    'password': 'rtdb_password'
}

# Kết nối Redis
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}


class SensorData:
    """Model dữ liệu cảm biến"""
    def __init__(self, sensor_id, value, timestamp):
        self.sensor_id = sensor_id
        self.value = value
        self.timestamp = timestamp


def generate_sensor_data(num_records):
    """Tạo dữ liệu cảm biến giả lập"""
    print(f"Đang tạo {num_records:,} bản ghi dữ liệu cảm biến...")
    data = []
    for i in range(num_records):
        sensor_id = f"SENSOR_{i:06d}"
        value = random.uniform(15.0, 35.0)  # Nhiệt độ từ 15-35°C
        timestamp = datetime.now().isoformat()
        data.append(SensorData(sensor_id, value, timestamp))
    return data


def setup_postgres():
    """Khởi tạo bảng PostgreSQL"""
    print("\n=== Khởi tạo PostgreSQL ===")
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Xóa bảng cũ nếu tồn tại
    cur.execute("DROP TABLE IF EXISTS sensor_data")
    
    # Tạo bảng mới
    cur.execute("""
        CREATE TABLE sensor_data (
            sensor_id VARCHAR(50) PRIMARY KEY,
            value FLOAT NOT NULL,
            timestamp TIMESTAMP NOT NULL
        )
    """)
    
    # Tạo index cho timestamp
    cur.execute("CREATE INDEX idx_timestamp ON sensor_data(timestamp)")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✓ PostgreSQL đã sẵn sàng")


def setup_redis():
    """Xóa dữ liệu cũ trong Redis"""
    print("\n=== Khởi tạo Redis ===")
    r = redis.Redis(**REDIS_CONFIG)
    r.flushdb()
    print("✓ Redis đã sẵn sàng")


def benchmark_postgres_insert(data):
    """Benchmark Insert vào PostgreSQL"""
    print("\n=== PostgreSQL INSERT ===")
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    start_time = time.time()
    
    # Batch insert để tối ưu
    batch_size = 1000
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        values = [(d.sensor_id, d.value, d.timestamp) for d in batch]
        
        cur.executemany(
            "INSERT INTO sensor_data (sensor_id, value, timestamp) VALUES (%s, %s, %s)",
            values
        )
        
        if (i + batch_size) % 10000 == 0:
            print(f"  Đã insert {i + batch_size:,} bản ghi...")
    
    conn.commit()
    elapsed_time = time.time() - start_time
    
    cur.close()
    conn.close()
    
    print(f"✓ Hoàn thành trong {elapsed_time:.2f} giây")
    print(f"  Throughput: {len(data)/elapsed_time:.0f} records/sec")
    
    return elapsed_time


def benchmark_redis_insert(data):
    """Benchmark Insert vào Redis"""
    print("\n=== Redis INSERT ===")
    r = redis.Redis(**REDIS_CONFIG)
    
    start_time = time.time()
    
    # Sử dụng pipeline để batch insert
    pipe = r.pipeline()
    for i, d in enumerate(data):
        pipe.hset(
            f"sensor:{d.sensor_id}",
            mapping={
                'value': str(d.value),
                'timestamp': d.timestamp
            }
        )
        
        # Execute pipeline mỗi 1000 records
        if (i + 1) % 1000 == 0:
            pipe.execute()
            pipe = r.pipeline()
            
            if (i + 1) % 10000 == 0:
                print(f"  Đã insert {i + 1:,} bản ghi...")
    
    # Execute remaining
    pipe.execute()
    
    elapsed_time = time.time() - start_time
    
    print(f"✓ Hoàn thành trong {elapsed_time:.2f} giây")
    print(f"  Throughput: {len(data)/elapsed_time:.0f} records/sec")
    
    return elapsed_time


def benchmark_postgres_read(num_reads, total_records):
    """Benchmark Random Read từ PostgreSQL"""
    print(f"\n=== PostgreSQL READ ({num_reads:,} random reads) ===")
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Tạo danh sách sensor_id ngẫu nhiên
    sensor_ids = [f"SENSOR_{random.randint(0, total_records-1):06d}" for _ in range(num_reads)]
    
    start_time = time.time()
    
    for i, sensor_id in enumerate(sensor_ids):
        cur.execute(
            "SELECT sensor_id, value, timestamp FROM sensor_data WHERE sensor_id = %s",
            (sensor_id,)
        )
        result = cur.fetchone()
        
        if (i + 1) % 2000 == 0:
            print(f"  Đã đọc {i + 1:,} bản ghi...")
    
    elapsed_time = time.time() - start_time
    
    cur.close()
    conn.close()
    
    print(f"✓ Hoàn thành trong {elapsed_time:.2f} giây")
    print(f"  Throughput: {num_reads/elapsed_time:.0f} reads/sec")
    print(f"  Average Latency: {elapsed_time*1000/num_reads:.2f} ms/read")
    
    return elapsed_time


def benchmark_redis_read(num_reads, total_records):
    """Benchmark Random Read từ Redis"""
    print(f"\n=== Redis READ ({num_reads:,} random reads) ===")
    r = redis.Redis(**REDIS_CONFIG)
    
    # Tạo danh sách sensor_id ngẫu nhiên
    sensor_ids = [f"SENSOR_{random.randint(0, total_records-1):06d}" for _ in range(num_reads)]
    
    start_time = time.time()
    
    for i, sensor_id in enumerate(sensor_ids):
        result = r.hgetall(f"sensor:{sensor_id}")
        
        if (i + 1) % 2000 == 0:
            print(f"  Đã đọc {i + 1:,} bản ghi...")
    
    elapsed_time = time.time() - start_time
    
    print(f"✓ Hoàn thành trong {elapsed_time:.2f} giây")
    print(f"  Throughput: {num_reads/elapsed_time:.0f} reads/sec")
    print(f"  Average Latency: {elapsed_time*1000/num_reads:.2f} ms/read")
    
    return elapsed_time


def plot_results(pg_insert, redis_insert, pg_read, redis_read):
    """Vẽ biểu đồ kết quả"""
    print("\n=== Tạo biểu đồ ===")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Biểu đồ INSERT
    databases = ['PostgreSQL', 'Redis']
    insert_times = [pg_insert, redis_insert]
    colors_insert = ['#336699', '#DC382D']
    
    bars1 = ax1.bar(databases, insert_times, color=colors_insert, alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Thời gian (giây)', fontsize=12)
    ax1.set_title(f'So sánh INSERT - {NUM_RECORDS:,} bản ghi', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Thêm giá trị lên cột
    for bar, time in zip(bars1, insert_times):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.2f}s\n{NUM_RECORDS/time:.0f} rec/s',
                ha='center', va='bottom', fontsize=10)
    
    # Biểu đồ READ
    read_times = [pg_read, redis_read]
    colors_read = ['#336699', '#DC382D']
    
    bars2 = ax2.bar(databases, read_times, color=colors_read, alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Thời gian (giây)', fontsize=12)
    ax2.set_title(f'So sánh READ - {NUM_READS:,} random reads', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Thêm giá trị lên cột
    for bar, time in zip(bars2, read_times):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.2f}s\n{NUM_READS/time:.0f} reads/s\n{time*1000/NUM_READS:.2f}ms/read',
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('benchmark_results.png', dpi=300, bbox_inches='tight')
    print("✓ Đã lưu biểu đồ: benchmark_results.png")
    
    # Tính speedup
    print("\n=== SPEEDUP ===")
    print(f"Redis nhanh hơn PostgreSQL:")
    print(f"  INSERT: {pg_insert/redis_insert:.2f}x")
    print(f"  READ:   {pg_read/redis_read:.2f}x")


def main():
    print("=" * 70)
    print("LAB 1: BENCHMARK DISK-BASED vs IN-MEMORY DATABASE")
    print("=" * 70)
    
    # Tạo dữ liệu
    data = generate_sensor_data(NUM_RECORDS)
    
    # Setup databases
    setup_postgres()
    setup_redis()
    
    # Benchmark INSERT
    print("\n" + "=" * 70)
    print("PHẦN 1: BENCHMARK INSERT")
    print("=" * 70)
    pg_insert_time = benchmark_postgres_insert(data)
    redis_insert_time = benchmark_redis_insert(data)
    
    # Benchmark READ
    print("\n" + "=" * 70)
    print("PHẦN 2: BENCHMARK RANDOM READ")
    print("=" * 70)
    pg_read_time = benchmark_postgres_read(NUM_READS, NUM_RECORDS)
    redis_read_time = benchmark_redis_read(NUM_READS, NUM_RECORDS)
    
    # Vẽ biểu đồ
    print("\n" + "=" * 70)
    print("KẾT QUẢ")
    print("=" * 70)
    plot_results(pg_insert_time, redis_insert_time, pg_read_time, redis_read_time)
    
    print("\n✓ Hoàn thành Lab 1!")


if __name__ == "__main__":
    main()
