**Lab 3: Data Freshness – iSARS Scenario**  
**Tổng điểm:** 100  
**Thời gian:** 1-2 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Lab này mô phỏng **intelligent Surveillance And Reconnaissance System (iSARS)** — hệ thống giám sát sử dụng sensors và drones để tracking objects.

Khái niệm quan trọng:
* **Absolute Validity Interval (AVI)**: Thời gian data còn valid từ khi sensor ghi nhận
* **Relative Validity Interval (RVI)**: Thời gian data còn valid sau khi derived data được tính toán

Problem:
* Sensor data (temperature, GPS, speed) có AVI/RVI khác nhau
* Khi compute derived data (e.g., threat assessment), phải check freshness của base data
* Nếu base data stale → derived data invalid → recompute

Deliverable:
* Simulation code (Python) với sensor updates, AVI/RVI tracking, staleness detection
* Báo cáo 4-6 trang

---

## **Part 1 — Data Freshness Theory**

**Mục tiêu:** Hiểu AVI, RVI, và freshness management trong RTDB.

**Sinh viên cần làm và nộp:**

* **Absolute Validity Interval (AVI)**:
  - **Definition**: Thời gian data còn valid kể từ khi sensor sample
  - **Example**: GPS location có AVI = 5s (vì object di chuyển)
  - **Timestamp**: t_sample + AVI = expiration time
  - **Check**: `current_time <= t_sample + AVI`

* **Relative Validity Interval (RVI)**:
  - **Definition**: Thời gian derived data còn valid sau khi compute
  - **Example**: Threat score computed từ GPS + speed, có RVI = 2s
  - **Dependency**: Nếu base data (GPS, speed) expired → derived data invalid
  - **Check**: `current_time <= t_compute + RVI` AND all base data fresh

* **iSARS scenario**:
  
  **Sensors**:
  - **GPS**: AVI = 5s (location changes fast)
  - **Temperature**: AVI = 30s (slow variation)
  - **Speed**: AVI = 3s (rapid acceleration)
  
  **Derived data**:
  - **Threat score** = f(GPS, temperature, speed)
    * RVI = 2s
    * Base data: GPS (5s), temperature (30s), speed (3s)
    * **Critical constraint**: Speed có AVI=3s > RVI=2s → phải update speed thường xuyên

* **Freshness violation scenarios**:
  | Case | GPS Age | Speed Age | Temp Age | Threat Valid? | Reason |
  |------|---------|-----------|----------|---------------|--------|
  | 1 | 2s | 1s | 10s | ✅ Yes | All base data fresh |
  | 2 | 6s | 1s | 10s | ❌ No | GPS expired (> 5s AVI) |
  | 3 | 2s | 4s | 10s | ❌ No | Speed expired (> 3s AVI) |
  | 4 | 2s | 1s | 35s | ❌ No | Temp expired (> 30s AVI) |

**Bằng chứng bắt buộc:**

* Định nghĩa AVI vs RVI (3-4 dòng mỗi khái niệm)
* iSARS scenario: 3 sensors + derived data với AVI/RVI values
* Table: 4 freshness violation cases

---

## **Part 2 — Simulation Design**

**Mục tiêu:** Implement simulator với sensor updates và freshness checking.

**Sinh viên cần làm và nộp:**

* **Data model**:
  ```python
  import time
  
  class SensorData:
      def __init__(self, name, value, avi):
          self.name = name
          self.value = value
          self.timestamp = time.time()
          self.avi = avi  # seconds
      
      def is_fresh(self):
          age = time.time() - self.timestamp
          return age <= self.avi
      
      def __repr__(self):
          age = time.time() - self.timestamp
          status = "FRESH" if self.is_fresh() else "STALE"
          return f"{self.name}={self.value} (age={age:.2f}s, AVI={self.avi}s) [{status}]"
  
  class DerivedData:
      def __init__(self, name, base_data_list, rvi):
          self.name = name
          self.base_data = base_data_list  # list of SensorData
          self.timestamp = time.time()
          self.rvi = rvi
          self.value = self.compute()
      
      def compute(self):
          # Check all base data fresh
          if not all(d.is_fresh() for d in self.base_data):
              return None  # Cannot compute
          
          # Example: Threat score = weighted sum
          gps, speed, temp = [d.value for d in self.base_data]
          return gps * 0.5 + speed * 0.3 + temp * 0.2
      
      def is_fresh(self):
          age = time.time() - self.timestamp
          rvi_valid = age <= self.rvi
          base_fresh = all(d.is_fresh() for d in self.base_data)
          return rvi_valid and base_fresh
  ```

* **Sensor update loop**:
  ```python
  import random
  import time
  
  # Initialize sensors
  gps = SensorData("GPS", random.uniform(0, 100), avi=5)
  speed = SensorData("Speed", random.uniform(0, 50), avi=3)
  temp = SensorData("Temperature", random.uniform(20, 30), avi=30)
  
  # Update loop
  for i in range(100):
      # Update sensors at different rates
      if i % 2 == 0:  # Every 2 iterations
          gps = SensorData("GPS", random.uniform(0, 100), avi=5)
      if i % 1 == 0:  # Every iteration (most frequent)
          speed = SensorData("Speed", random.uniform(0, 50), avi=3)
      if i % 10 == 0:  # Every 10 iterations (least frequent)
          temp = SensorData("Temperature", random.uniform(20, 30), avi=30)
      
      # Compute derived data
      threat = DerivedData("Threat", [gps, speed, temp], rvi=2)
      
      # Log
      print(f"[{i}] GPS: {gps.is_fresh()}, Speed: {speed.is_fresh()}, Temp: {temp.is_fresh()}, Threat: {threat.is_fresh()}")
      
      time.sleep(0.5)  # 500ms per iteration
  ```

* **Freshness metrics**:
  - **Staleness count**: # times derived data invalid due to base data stale
  - **Recompute count**: # times recompute triggered
  - **Average age**: Mean age of base data when derived data computed

**Bằng chứng bắt buộc:**

* Code: `data_freshness_isars.py` với classes: SensorData, DerivedData
* Update loop với 3 sensors (GPS/Speed/Temp) + derived data (Threat)
* Command: `python3 data_freshness_isars.py --duration 60`

---

## **Part 3 — Experiments & Measurements**

**Mục tiêu:** Chạy simulation và collect freshness metrics.

**Sinh viên cần làm và nộp:**

* **Experiment matrix**:
  | Scenario | GPS Update Rate | Speed Update Rate | Temp Update Rate | Expected Staleness |
  |----------|-----------------|-------------------|------------------|--------------------|
  | Baseline | 2s | 1s | 10s | <5% |
  | Slow GPS | 6s | 1s | 10s | 50-70% (GPS expired) |
  | Slow Speed | 2s | 5s | 10s | 40-60% (Speed expired) |
  | All Slow | 6s | 5s | 40s | >80% (All stale) |

* **Log format**:
  ```
  [Time] [GPS: age=2.1s, AVI=5s, FRESH] [Speed: age=1.0s, AVI=3s, FRESH] [Temp: age=12s, AVI=30s, FRESH] [Threat: VALID]
  [Time] [GPS: age=6.5s, AVI=5s, STALE] [Speed: age=1.2s, AVI=3s, FRESH] [Temp: age=15s, AVI=30s, FRESH] [Threat: INVALID - GPS stale]
  ```

* **Metrics calculation**:
  ```python
  def analyze_log(log_file):
      valid_count = 0
      invalid_count = 0
      reasons = {"GPS": 0, "Speed": 0, "Temp": 0}
      
      with open(log_file) as f:
          for line in f:
              if "VALID" in line:
                  valid_count += 1
              elif "INVALID" in line:
                  invalid_count += 1
                  # Parse reason
                  if "GPS stale" in line:
                      reasons["GPS"] += 1
                  # etc.
      
      staleness_rate = invalid_count / (valid_count + invalid_count) * 100
      return {
          "staleness_rate": staleness_rate,
          "reasons": reasons
      }
  ```

* **Expected results** (example):
  | Scenario | Staleness Rate | Main Cause | Recompute Count |
  |----------|----------------|------------|-----------------|
  | Baseline | 3% | Speed (70%) | 5 |
  | Slow GPS | 65% | GPS (100%) | 130 |
  | Slow Speed | 55% | Speed (100%) | 110 |
  | All Slow | 85% | GPS (40%), Speed (35%), Temp (25%) | 170 |

**Bằng chứng bắt buộc:**

* Log files cho 4 scenarios: `baseline.log`, `slow_gps.log`, etc.
* Results table: Staleness rate, main cause, recompute count
* Script: `run_experiments.sh` chạy tất cả 4 scenarios

---

## **Part 4 — Analysis & Visualization**

**Mục tiêu:** Visualize và giải thích freshness violations.

**Sinh viên cần làm và nộp:**

* **Visualization 1: Staleness rate comparison**
  - Bar chart: X-axis = scenario, Y-axis = staleness rate (%)
  - **Observation**: Baseline <5%, Slow GPS/Speed 50-70%, All Slow >80%

* **Visualization 2: Root cause breakdown** (for Slow GPS scenario)
  - Pie chart: GPS expired (100%), Speed expired (0%), Temp expired (0%)
  - **Observation**: GPS là bottleneck vì AVI ngắn (5s) nhưng update rate chậm (6s)

* **Visualization 3: Timeline** (30s snapshot)
  - X-axis = time, Y-axis = 4 data items (GPS, Speed, Temp, Threat)
  - Color-code: Green = fresh, Red = stale
  - **Observation**: Threat turns red whenever any base data stale

* **Root cause analysis**:
  - **Why Speed critical?**
    * AVI = 3s (shortest) → requires most frequent updates (≤3s interval)
    * In Baseline: Update every 1s → OK
    * In Slow Speed: Update every 5s → 55% staleness
  
  - **Why Temp less critical?**
    * AVI = 30s (longest) → tolerate slow updates (≤30s interval)
    * Update every 10s → Always fresh
  
  - **RVI constraint**:
    * Threat RVI = 2s → even if base data fresh, Threat expires in 2s
    * Must recompute frequently even if base data unchanged

* **Design recommendations**:
  - **Update rate heuristic**: Update interval ≤ 0.5 × AVI (safety margin)
    * GPS (AVI=5s) → update every ≤2.5s
    * Speed (AVI=3s) → update every ≤1.5s
    * Temp (AVI=30s) → update every ≤15s
  
  - **Priority scheduling**: Prioritize sensors with short AVI (Speed > GPS > Temp)
  
  - **On-demand update**: Trigger sensor update khi derived data request + base data near expiration

**Bằng chứng bắt buộc:**

* 3 plots: Staleness rate, root cause pie, timeline
* 10-15 dòng phân tích: Why Speed critical, RVI constraint, update rate heuristic
* Design recommendations (3-5 points)

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab3_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo dài **4-6 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Introduction & Theory** [20 points]
  - AVI vs RVI definitions
  - iSARS scenario (3 sensors + derived data)
  - Freshness violation conditions (4 cases table)

* **c. Simulation Design** [15 points]
  - SensorData class (avi, timestamp, is_fresh())
  - DerivedData class (base_data, rvi, compute())
  - Update loop (3 sensors with different rates)
  - Metrics: staleness rate, recompute count

* **d. Results** [30 points]
  - **Table 1**: 4 scenarios (update rates, staleness rate, main cause)
  - **Figure 1**: Staleness rate bar chart
  - **Figure 2**: Root cause pie chart (1 scenario)
  - **Figure 3**: Timeline (30s snapshot)
  - Description (3-5 dòng)

* **e. Analysis** [25 points]
  - Root cause: Speed là bottleneck (AVI=3s shortest)
  - RVI constraint: Threat expires in 2s regardless of base data
  - Update rate heuristic: ≤ 0.5 × AVI
  - Design recommendations: Priority scheduling, on-demand update
  - Comparison với baseline (85% vs 3% staleness)

* **f. Conclusion** [10 points]
  - Summary: Freshness critical in RTDB
  - Recommendation: Update rate matched to AVI/RVI
  - Limitations: Simulation only, no network delay, no concurrency
  - Future work: Multi-object tracking, sensor fusion, network jitter

### 2. **Code & Data Package**

**Bắt buộc có:**

* `data_freshness_isars.py`: Full simulator
* `requirements.txt`: (numpy, matplotlib, pandas nếu cần)
* `README.md`: How to run
* `run_experiments.sh`: Chạy 4 scenarios
* `logs/`: 4 log files (baseline.log, slow_gps.log, etc.)
* `plots/`: 3 figures

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 20 | AVI/RVI defined, iSARS scenario, violation cases |
| **Design** | 15 | SensorData/DerivedData classes, update loop |
| **Results** | 30 | Table + 3 plots (staleness, root cause, timeline) |
| **Analysis** | 25 | Root cause, update heuristic, recommendations |
| **Conclusion** | 10 | Summary, recommendations, future work |
| **Total** | **100** | |

**Bonus** (up to +10):
* Multi-object tracking (3 drones): +4
* Network delay simulation (packet loss): +3
* Real-time visualization (animated plot): +3

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Clock sync**: Dùng `time.time()` consistently (không mix với system clock)
* **Edge cases**: Test khi AVI = RVI (e.g., both 5s)
* **Logging**: Log mỗi staleness event với timestamp + reason
* **Validation**: Manually check 5-10 iterations với small example

### ❌ Don'ts:
* **Không check base data freshness**: DerivedData.compute() phải check `all(d.is_fresh())`
* **Không update timestamp**: Mỗi sensor update phải set `self.timestamp = time.time()`
* **Không handle None**: Nếu base data stale, return None hoặc raise exception

### 🔧 Debugging:
* **Staleness rate 0%**: Check AVI values (too large?) hoặc update rate (too fast?)
* **Staleness rate 100%**: Check AVI/RVI (too small?) hoặc update rate (too slow?)
* **Wrong root cause**: Check logic trong analyze_log() (parsing "GPS stale", etc.)

---

## **References**

1. Ramamritham, K., Son, S. H., & DiPippo, L. C. (2004). *Real-Time Databases and Data Services*. Real-Time Systems, 28(2-3), 179-215.

2. Song, X., & Liu, J. W. S. (1995). *Maintaining Temporal Consistency: Pessimistic vs. Optimistic Concurrency Control*. IEEE TKDE, 7(5), 786-796.

3. Gustafsson, T., & Hansson, J. (2004). *Data Management in Real-Time Systems: A Case of On-Demand Updates*. Real-Time Systems, 26(3), 235-261.

4. Xiong, M., Ramamritham, K., & Stankovic, J. A. (2002). *Scheduling Transactions with Temporal Constraints: Exploiting Data Semantics*. IEEE TPDS, 14(11), 1155-1166.

---

**Good luck!** 🕐
