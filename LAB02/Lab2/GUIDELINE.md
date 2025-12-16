**Lab 2: Transaction Scheduling Simulation**  
**Tổng điểm:** 100  
**Thời gian:** 1-2 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Mục tiêu lab là mô phỏng **transaction scheduling** trong Real-Time Database Systems (RTDBS).

So sánh 2 policies:
* **FIFO** (First-In-First-Out): Process theo thứ tự arrival
* **EDF** (Earliest Deadline First): Priority theo deadline

Metrics:
* Deadline miss rate (%)
* Total value captured (transactions có value khi complete on-time)
* Average tardiness (cho missed transactions)

Deliverable:
* Simulation code (Python)
* Results cho multiple workloads (low/medium/high/overload)
* Báo cáo 3-5 trang

---

## **Part 1 — Transaction Model & Theory**

**Mục tiêu:** Hiểu transaction model và scheduling policies.

**Sinh viên cần làm và nộp:**

* **Transaction T_i definition**:
  - **Arrival time (a_i)**: Khi nào transaction enter system
  - **Execution time (e_i)**: Thời gian xử lý (ms)
  - **Deadline (d_i)**: Phải complete trước d_i
  - **Value (v_i)**: Giá trị nếu complete on-time (0 nếu miss)

* **Scheduling policies**:
  
  **FIFO (First-In-First-Out)**:
  - Process transactions theo arrival order
  - Simple, no starvation
  - Ignores deadline → high miss rate
  
  **EDF (Earliest Deadline First)**:
  - Priority = deadline sớm nhất
  - Dynamic priority (re-evaluate mỗi khi new transaction arrives)
  - Optimal cho single-resource systems
  - Minimizes deadline misses

* **Performance metrics**:
  - **Deadline miss rate**: (# missed / total) × 100%
  - **Total value**: Σ v_i (for completed on-time transactions)
  - **Average tardiness**: Avg(completion_time - deadline) for missed transactions
  - **Utilization**: Σ e_i / total_time

* **Expected results**:
  - EDF should have lower miss rate than FIFO
  - EDF captures more value
  - Under overload: EDF still better but both degrade

**Bằng chứng bắt buộc:**

* Transaction model definition (4 parameters: a, e, d, v)
* Bảng so sánh FIFO vs EDF (priority rule, complexity, starvation risk)
* Prediction: EDF better by XX%

---

## **Part 2 — Simulation Design**

**Mục tiêu:** Thiết kế simulator với transaction generator và scheduler.

**Sinh viên cần làm và nộp:**

* **Transaction generator**:
  ```python
  import random
  
  def generate_transactions(n=100, arrival_rate=10):
      """
      arrival_rate: transactions per second (Poisson distribution)
      """
      transactions = []
      time = 0
      for i in range(n):
          # Arrival time (Poisson)
          time += random.expovariate(arrival_rate)
          
          # Execution time (Uniform 10-50ms)
          exec_time = random.uniform(10, 50)
          
          # Deadline (arrival + slack)
          slack = random.uniform(50, 200)  # ms
          deadline = time + slack
          
          # Value (proportional to urgency?)
          value = 100  # or random
          
          transactions.append({
              'id': i,
              'arrival': time,
              'exec_time': exec_time,
              'deadline': deadline,
              'value': value
          })
      return transactions
  ```

* **FIFO scheduler**:
  ```python
  def schedule_fifo(transactions):
      queue = sorted(transactions, key=lambda t: t['arrival'])
      current_time = 0
      results = []
      
      for t in queue:
          # Wait for arrival
          if current_time < t['arrival']:
              current_time = t['arrival']
          
          # Execute
          start_time = current_time
          current_time += t['exec_time']
          completion_time = current_time
          
          # Check deadline
          missed = completion_time > t['deadline']
          value_captured = 0 if missed else t['value']
          
          results.append({
              'id': t['id'],
              'start': start_time,
              'completion': completion_time,
              'deadline': t['deadline'],
              'missed': missed,
              'value': value_captured
          })
      
      return results
  ```

* **EDF scheduler**:
  ```python
  def schedule_edf(transactions):
      # Sort by deadline (re-sort at each arrival in advanced version)
      queue = sorted(transactions, key=lambda t: t['deadline'])
      # Rest similar to FIFO
  ```

* **Workload scenarios**:
  | Scenario | Arrival Rate (λ) | System Capacity | Utilization | Expected Miss |
  |----------|------------------|-----------------|-------------|---------------|
  | Low | 5 trans/s | 20 trans/s | 25% | <5% |
  | Medium | 10 trans/s | 20 trans/s | 50% | 10-20% |
  | High | 18 trans/s | 20 trans/s | 90% | 30-50% |
  | Overload | 25 trans/s | 20 trans/s | 125% | >60% |

**Bằng chứng bắt buộc:**

* Code: `scheduler_simulation.py` với functions: generate, schedule_fifo, schedule_edf
* Command: `python3 scheduler_simulation.py --scheduler edf --load 0.5`
* 4 scenarios config (low/medium/high/overload)

---

## **Part 3 — Experiments & Measurements**

**Mục tiêu:** Chạy simulation cho tất cả scenarios và collect metrics.

**Sinh viên cần làm và nộp:**

* **Run matrix**:
  - 2 schedulers × 4 workloads = 8 runs
  - Each run: 100 transactions
  - Repeat 3 times, lấy average

* **Metrics calculation**:
  ```python
  def analyze_results(results):
      total = len(results)
      missed = sum(r['missed'] for r in results)
      miss_rate = missed / total * 100
      
      total_value = sum(r['value'] for r in results)
      
      missed_trans = [r for r in results if r['missed']]
      avg_tardiness = np.mean([r['completion'] - r['deadline'] 
                               for r in missed_trans]) if missed_trans else 0
      
      return {
          'miss_rate': miss_rate,
          'total_value': total_value,
          'avg_tardiness': avg_tardiness
      }
  ```

* **Expected results** (example):
  | Scenario | Scheduler | Miss Rate | Total Value | Avg Tardiness |
  |----------|-----------|-----------|-------------|---------------|
  | Medium | FIFO | 18% | 8200 | 45ms |
  | Medium | EDF | 8% | 9200 | 28ms |
  | High | FIFO | 42% | 5800 | 82ms |
  | High | EDF | 22% | 7800 | 51ms |

**Bằng chứng bắt buộc:**

* Results table (8 rows: 2 schedulers × 4 workloads)
* CSV log files: `results_fifo_medium.csv`, `results_edf_medium.csv`, etc.
* Script: `run_all_experiments.sh` chạy tất cả 8 scenarios

---

## **Part 4 — Analysis & Visualization**

**Mục tiêu:** Visualize và giải thích kết quả.

**Sinh viên cần làm và nộp:**

* **Visualization 1: Miss rate comparison**
  - Bar chart: X-axis = workload, Y-axis = miss rate (%)
  - 2 bars per workload: FIFO (red), EDF (blue)
  - **Observation**: EDF consistently lower miss rate

* **Visualization 2: Total value captured**
  - Bar chart: X-axis = workload, Y-axis = total value
  - **Observation**: EDF captures 10-50% more value than FIFO

* **Visualization 3: Timeline (1 second snapshot)**
  - Gantt chart: FIFO vs EDF side-by-side
  - Show transactions executing, deadline markers
  - **Observation**: FIFO processes in arrival order, EDF reorders by deadline

* **Root cause analysis**:
  - **Why EDF better?**
    * Dynamic priority adapts to urgency
    * Completes near-deadline transactions first
    * Optimal for single-resource systems (provably minimizes misses)
  
  - **When FIFO acceptable?**
    * All deadlines very loose (slack >> execution time)
    * Simplicity more important than performance
    * Fairness requirement (no priority)
  
  - **Limitations of EDF**:
    * Under overload: All transactions miss slightly (domino effect)
    * Starvation possible: Far-deadline transactions never run
    * Overhead: O(log n) priority queue vs FIFO O(1)

* **Theoretical analysis**:
  - **Liu-Layland bound** (for EDF): U ≤ 1.0
  - Medium workload: U = 0.5 → both schedulable theoretically
  - Actual miss rate > 0 due to random arrivals (not purely periodic)

**Bằng chứng bắt buộc:**

* 3 plots: Miss rate, value captured, timeline/Gantt
* 10-15 dòng phân tích: Why EDF better, when FIFO OK, EDF limitations
* Theoretical analysis: Utilization vs miss rate

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab2_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo dài **3-5 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Introduction & Theory** [20 points]
  - Transaction model (a, e, d, v)
  - FIFO vs EDF policies
  - Metrics: miss rate, value, tardiness
  - Prediction: EDF should outperform FIFO

* **c. Simulation Design** [15 points]
  - Transaction generator (Poisson arrivals, uniform exec time)
  - FIFO scheduler algorithm (pseudo-code hoặc flowchart)
  - EDF scheduler algorithm
  - 4 workload scenarios (low to overload)

* **d. Results** [30 points]
  - **Table 1**: Miss rate for 8 runs (2 schedulers × 4 workloads)
  - **Figure 1**: Miss rate bar chart
  - **Figure 2**: Total value bar chart
  - **Figure 3**: Timeline/Gantt (1 scenario)
  - Description (3-5 dòng)

* **e. Analysis** [25 points]
  - Comparison: EDF reduces miss rate by XX%
  - Root cause: Why EDF optimal (dynamic priority)
  - When FIFO acceptable (loose deadlines)
  - EDF limitations (overload, overhead)
  - Theoretical: Utilization analysis

* **f. Conclusion** [10 points]
  - Summary: EDF better for RTDB with tight deadlines
  - Recommendation: Implement EDF or hybrid (EDF + abort policy)
  - Limitations: Single-resource only, no concurrency control
  - Future work: Multi-resource, precedence constraints

### 2. **Code & Data Package**

**Bắt buộc có:**

* `scheduler_simulation.py`: Full simulator
* `requirements.txt`: numpy, matplotlib, pandas
* `README.md`: How to run
* `run_all_experiments.sh`: Chạy 8 scenarios
* `results/`: CSV logs cho tất cả runs
* `plots/`: 3 figures (miss rate, value, timeline)

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 20 | Transaction model, FIFO/EDF explained, metrics |
| **Design** | 15 | Generator, scheduler algorithms, workloads |
| **Results** | 30 | Table + 3 plots (miss rate, value, timeline) |
| **Analysis** | 25 | Why EDF better, root cause, limitations |
| **Conclusion** | 10 | Summary, recommendation, future work |
| **Total** | **100** | |

**Bonus** (up to +10):
* Priority Ceiling Protocol simulation: +5
* Concurrency control (2PL vs OCC): +3
* Animated timeline (video): +2

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Random seed**: Set `random.seed(42)` để reproducible
* **Multiple runs**: Average over 3-5 runs
* **Edge cases**: Test với U=0.1 (underload) và U=2.0 (severe overload)
* **Validation**: Check manually với small example (5 transactions)

### ❌ Don'ts:
* **Không sort đúng**: EDF sort by deadline, FIFO by arrival
* **Không update current_time**: Nếu current_time < arrival → wait
* **Không check deadline correctly**: Compare completion vs deadline

### 🔧 Debugging:
* **Miss rate 0% even in overload**: Check deadline calculation (too loose?)
* **EDF worse than FIFO**: Bug trong sorting logic
* **Negative tardiness**: Check completion_time - deadline calculation

---

## **References**

1. Haritsa, J. R., Carey, M. J., & Livny, M. (1993). *Value-Based Scheduling in Real-Time Database Systems*. VLDB Journal, 2(2), 117-152.

2. Abbott, R., & Garcia-Molina, H. (1992). *Scheduling Real-Time Transactions: A Performance Evaluation*. ACM TODS, 17(3), 513-560.

3. Ramamritham, K. (1993). *Real-Time Databases*. Distributed and Parallel Databases, 1(2), 199-226.

4. Liu, C. L., & Layland, J. W. (1973). *Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment*. JACM, 20(1), 46-61.

---

**Good luck!** 📊
