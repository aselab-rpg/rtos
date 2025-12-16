**Lab 1: Benchmark PostgreSQL vs Redis**  
**Tổng điểm:** 100  
**Thời gian:** 2 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Mục tiêu lab là so sánh hiệu năng giữa **disk-based database** (PostgreSQL) và **in-memory database** (Redis) trong context của real-time systems.

Câu hỏi chính:
* PostgreSQL vs Redis: Latency khác nhau bao nhiêu?
* Batch operations có giúp giảm latency không?
* Trade-off: Durability (PostgreSQL) vs Speed (Redis)?

Deliverable:
* Benchmark code (Python) + Docker setup
* Log files: latency measurements
* Báo cáo 4-6 trang với plots

---

## **Part 1 — Theory & Motivation**

**Mục tiêu:** Hiểu kiến trúc disk-based vs in-memory databases.

**Sinh viên cần làm và nộp:**

* **Disk-based DB (PostgreSQL)**:
  - Data lưu trên disk (HDD/SSD)
  - Write-Ahead Logging (WAL) cho durability
  - Write path: Client → Parse SQL → Write WAL → fsync → Update buffer pool
  - Latency sources: **Disk fsync (5-15ms HDD, 0.1-1ms SSD)**, lock contention, connection overhead
  - ACID guarantees: Atomicity, Consistency, Isolation, Durability

* **In-memory DB (Redis)**:
  - All data in RAM
  - Optional persistence: RDB snapshot, AOF (Append-Only File)
  - Write path: Client → Parse command → Update in-memory → (Optional) AOF → Return
  - Latency sources: Network I/O (~0.1ms), command execution (<1ms)
  - BASE model: Basically Available, Soft-state, Eventually consistent

* **Use cases**:
  - PostgreSQL: Persistent critical data (transactions, audit logs)
  - Redis: High-frequency telemetry, session cache, real-time leaderboards

* **Hypothesis**:
  - Redis **10-50x** faster than PostgreSQL for writes
  - Batch operations reduce latency per record
  - PostgreSQL has higher variance (jitter)

**Bằng chứng bắt buộc:**

* Bảng so sánh: PostgreSQL vs Redis (storage, durability, latency, ACID/BASE)
* Diagram: Write path cho PostgreSQL và Redis

---

## **Part 2 — Environment Setup**

**Mục tiêu:** Dựng PostgreSQL và Redis qua Docker, chuẩn bị benchmark scripts.

**Sinh viên cần làm và nộp:**

* **Docker Compose setup**:
  ```yaml
  # docker-compose.yml
  version: '3.8'
  services:
    postgres:
      image: postgres:14
      environment:
        POSTGRES_USER: testuser
        POSTGRES_PASSWORD: testpass
        POSTGRES_DB: testdb
      ports:
        - "5432:5432"
    
    redis:
      image: redis:7
      ports:
        - "6379:6379"
  ```

* **Start containers**:
  ```bash
  docker-compose up -d
  # Check: docker ps
  ```

* **PostgreSQL schema**:
  ```sql
  CREATE TABLE logs (
      id SERIAL PRIMARY KEY,
      timestamp DOUBLE PRECISION,
      sensor_id INTEGER,
      value DOUBLE PRECISION
  );
  ```

* **Redis schema** (key-value):
  ```
  Key: log:<id>
  Value: JSON string {"timestamp": ..., "sensor_id": ..., "value": ...}
  ```

* **Python dependencies**:
  ```bash
  pip install psycopg2-binary redis matplotlib pandas
  ```

**Bằng chứng bắt buộc:**

* `docker-compose.yml` file
* `schema.sql` (PostgreSQL table creation)
* `requirements.txt` (Python packages)
* Commands để start và verify containers

---

## **Part 3 — Benchmark Implementation**

**Mục tiêu:** Viết script benchmark single writes và batch writes.

**Sinh viên cần làm và nộp:**

* **Workloads**:
  1. **Single write** (1000 records): 1 record → 1 INSERT/SET → 1 commit
  2. **Batch write** (1000 records): 100 records → 1 batch INSERT/MSET → 1 commit

* **PostgreSQL benchmark**:
  ```python
  import psycopg2
  import time
  
  conn = psycopg2.connect("postgresql://testuser:testpass@localhost/testdb")
  cur = conn.cursor()
  
  # Single write
  latencies = []
  for i in range(1000):
      t1 = time.time()
      cur.execute("INSERT INTO logs VALUES (%s, %s, %s, %s)", 
                  (i, time.time(), i%10, i*0.1))
      conn.commit()
      t2 = time.time()
      latencies.append((t2-t1)*1000)  # ms
  
  # Metrics
  print(f"Avg: {np.mean(latencies):.2f}ms")
  print(f"p99: {np.percentile(latencies, 99):.2f}ms")
  print(f"Max: {np.max(latencies):.2f}ms")
  ```

* **Redis benchmark**:
  ```python
  import redis
  import time
  
  r = redis.Redis(host='localhost', port=6379)
  
  # Single write
  latencies = []
  for i in range(1000):
      t1 = time.time()
      r.set(f"log:{i}", json.dumps({"timestamp": time.time(), "sensor_id": i%10, "value": i*0.1}))
      t2 = time.time()
      latencies.append((t2-t1)*1000)
  
  # Metrics (same as above)
  ```

* **Batch benchmarks**: Similar, nhưng commit sau mỗi 100 records

* **Metrics to collect**:
  - Latency: avg, p50, p95, p99, max
  - Jitter: standard deviation
  - Throughput: records/second

**Bằng chứng bắt buộc:**

* `benchmark.py`: Full script với 4 functions (PG single, PG batch, Redis single, Redis batch)
* Command: `python3 benchmark.py > benchmark_results.log`
* Log file với latency measurements

---

## **Part 4 — Results & Analysis**

**Mục tiêu:** Phân tích kết quả, visualize, và giải thích findings.

**Sinh viên cần làm và nộp:**

* **Results table**:
  | Database | Operation | Avg (ms) | p99 (ms) | Max (ms) | Jitter (stddev) | Throughput (ops/s) |
  |----------|-----------|----------|----------|----------|-----------------|---------------------|
  | PostgreSQL | Single | 12.5 | 24.3 | 52.1 | 5.8 | 80 |
  | PostgreSQL | Batch | 4.5 | 8.7 | 15.2 | 2.1 | 222 |
  | Redis | Single | 0.8 | 1.8 | 3.2 | 0.3 | 1250 |
  | Redis | Batch | 1.2 | 2.1 | 4.5 | 0.5 | 833 |

  **Observations**:
  - Redis **15-16x faster** than PostgreSQL (single writes)
  - PostgreSQL benefits từ batching (2.8x improvement)
  - Redis batching slightly slower (pipeline overhead)

* **Visualization 1: CDF plot**
  - X-axis: Latency (ms)
  - Y-axis: Cumulative probability
  - 4 curves: PG single, PG batch, Redis single, Redis batch
  - **Observation**: Redis distribution tập trung, PostgreSQL có long tail

* **Visualization 2: Bar chart**
  - X-axis: Database + Operation
  - Y-axis: p99 latency (ms)
  - **Observation**: PostgreSQL p99 = 24.3ms, Redis p99 = 1.8ms

* **Root cause analysis**:
  - **Why PostgreSQL slow?**
    1. Disk fsync: ~10ms per commit
    2. WAL write overhead
    3. Connection pooling overhead (if not used)
  
  - **Why Redis fast?**
    1. RAM access: ~100ns (vs 10ms disk)
    2. Simple protocol: SET command simpler than SQL parsing
    3. Single-threaded: No lock contention
  
  - **Why PostgreSQL batching helps?**
    - 1 commit for 100 records vs 100 commits
    - Amortized fsync overhead: 10ms / 100 = 0.1ms per record
  
  - **Why Redis batching slower?**
    - Pipeline overhead: packing/unpacking commands
    - Still faster than PostgreSQL single writes

* **Trade-offs**:
  | Aspect | PostgreSQL | Redis | Winner for RT? |
  |--------|------------|-------|----------------|
  | Latency | 10-50ms | <1ms | ✅ Redis |
  | Durability | Guaranteed | Optional | PostgreSQL |
  | Query complexity | SQL (joins, aggregates) | Simple KV | PostgreSQL |
  | Consistency | ACID (strong) | Eventual | PostgreSQL |
  | Memory footprint | Small (disk) | Large (RAM) | PostgreSQL |

* **Production recommendation**:
  ```
  Sensor → Redis (buffer, <1ms) → Background worker → PostgreSQL (persistence)
           Fast write for control                     Durable storage for audit
  ```

**Bằng chứng bắt buộc:**

* Results table (4 rows × 6 metrics)
* 2 plots: CDF + bar chart
* 10-15 dòng phân tích root cause
* Trade-off table
* Architecture diagram cho hybrid approach

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab1_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo dài **4-6 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Introduction & Theory** [20 points]
  - Disk-based vs In-memory architectures
  - ACID vs BASE
  - Write path comparison (diagram)
  - Hypothesis: Redis 10-50x faster

* **c. Methodology** [15 points]
  - Docker Compose setup (PostgreSQL + Redis)
  - Schema design (SQL table, Redis keys)
  - Benchmark workloads: Single vs Batch (1000 records)
  - Metrics: latency (avg/p99/max), jitter, throughput

* **d. Results** [30 points]
  - **Table 1**: Performance comparison (4 rows × 6 metrics)
  - **Figure 1**: CDF plot (4 curves)
  - **Figure 2**: p99 latency bar chart
  - Description (3-5 dòng)

* **e. Analysis** [25 points]
  - Root cause: Why PostgreSQL slow (fsync), why Redis fast (RAM)
  - Batching impact: PG 2.8x improvement, Redis slight degradation
  - Theoretical vs measured: Expected ~10ms fsync → measured 12.5ms ✓
  - Trade-offs: Latency vs Durability vs Query complexity
  - Hybrid architecture recommendation (diagram)

* **f. Conclusion** [10 points]
  - Summary: Redis 15x faster, PostgreSQL more durable
  - Use case: Redis for hot path, PostgreSQL for cold storage
  - Limitations: Test trên localhost (no network latency), single-threaded client
  - Future work: Test với concurrent clients, replication overhead

### 2. **Code & Data Package**

**Bắt buộc có:**

* `docker-compose.yml`: Database containers
* `schema.sql`: PostgreSQL table creation
* `benchmark.py`: Full benchmark script
* `requirements.txt`: Python dependencies
* `README.md`: Setup và run instructions
* `logs/`: Benchmark results (CSV hoặc JSON)
* `plots/`: CDF, bar chart (PNG hoặc PDF)

### 3. **Reproducibility**

* `run_benchmark.sh`: One-command để chạy tất cả
  ```bash
  #!/bin/bash
  docker-compose up -d
  sleep 5  # wait for DB ready
  python3 benchmark.py > results.log
  python3 plot_results.py
  echo "Done! Check plots/ and results.log"
  ```

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 20 | Disk vs in-memory, ACID vs BASE, write path diagram |
| **Methodology** | 15 | Docker setup, schema, workloads, metrics |
| **Results** | 30 | Table + 2 plots (CDF + bar chart) |
| **Analysis** | 25 | Root cause, batching, trade-offs, hybrid architecture |
| **Conclusion** | 10 | Summary, use cases, limitations |
| **Total** | **100** | |

**Bonus** (up to +10):
* Test với SSD vs HDD cho PostgreSQL: +3
* Connection pooling (PgBouncer) impact: +4
* Concurrent clients benchmark: +3

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Warm-up**: Chạy 100 records trước để warm cache
* **Multiple runs**: Chạy 3 lần, lấy median
* **fsync check**: PostgreSQL default synchronous_commit = on (ensure durability)
* **Redis persistence**: Test với AOF enabled và disabled

### ❌ Don'ts:
* **Không test trên laptop**: Disk-based DB sensitive to disk speed
* **Không quên connection pooling**: PostgreSQL connection overhead ~10ms
* **Không so sánh unfairly**: Redis no persistence vs PostgreSQL fsync (apples to oranges)

### 🔧 Debugging:
* **PostgreSQL slow connection**: Use connection pooling (PgBouncer)
* **Redis timeout**: Check `redis.conf` timeout settings
* **Latency spike**: Check Docker resource limits (`docker stats`)

---

## **References**

1. PostgreSQL Documentation. (2024). *Write-Ahead Logging (WAL)*. https://www.postgresql.org/docs/current/wal-intro.html

2. Redis Documentation. (2024). *Persistence*. https://redis.io/docs/management/persistence/

3. Ramamritham, K., & Chrysanthis, P. K. (1996). *Advances in Real-Time Database Systems*. Kluwer Academic Publishers.

4. Corbett, J. C., et al. (2013). *Spanner: Google's Globally Distributed Database*. ACM TOCS, 31(3).

---

**Good luck!** 💾
