**Lab 3: So găng SCHED_OTHER vs RR vs FIFO**  
**Tổng điểm:** 100  
**Thời gian:** 1-2 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm. Nếu nộp trước **11:59 PM** của ngày sau ngày đến hạn, bài sẽ vẫn được chấp nhận nhưng **bị trừ 20%** điểm.

---

## **Lab overview**

Mục tiêu lab là đo và so sánh **jitter** của 3 scheduling policies trên Linux:
* **SCHED_OTHER** (CFS - Completely Fair Scheduler) - default policy
* **SCHED_RR** (Round-Robin real-time) - time-sliced RT policy
* **SCHED_FIFO** (First-In-First-Out real-time) - non-preemptive RT policy

Sử dụng tool **cyclictest** để đo latency với các cấu hình:
* Baseline: No CPU affinity, no background load
* Optimized: CPU pinning (affinity)
* Stress: Background load (stress-ng)

Deliverable:
* Log files từ cyclictest cho 3 policies
* KPI: p95/p99/max latency, jitter
* Báo cáo 3-5 trang so sánh performance

---

## **Part 1 — Theory & Policies**

**Mục tiêu:** Hiểu rõ 3 scheduling policies và trade-offs.

**Sinh viên cần làm và nộp:**

* **SCHED_OTHER (CFS)**:
  - Default Linux scheduler
  - Dynamic priority dựa trên vruntime (virtual runtime)
  - Goal: Fairness → all processes get equal CPU time
  - Trade-off: Fair nhưng **không deterministic**, latency cao

* **SCHED_RR (Round-Robin)**:
  - Real-time policy với time slice (default 100ms)
  - Fixed priority (1-99), preemptive
  - Threads cùng priority được round-robin
  - Trade-off: Better than CFS, nhưng vẫn có context switch overhead

* **SCHED_FIFO (First-In-First-Out)**:
  - Real-time policy **không có time slice**
  - Fixed priority (1-99), runs until block/yield/preempted by higher priority
  - Lowest latency, highest determinism
  - Trade-off: Risk of starvation (low priority tasks never run)

* **CPU Affinity**:
  - Pin thread/process vào specific CPU cores
  - Benefit: Cache locality, no migration overhead
  - Command: `taskset -c <cpu> <command>`

* **Background Load**:
  - Tool: `stress-ng --cpu N` (CPU stress)
  - Impact: Increases contention, jitter tăng
  - Real-time policies should resist better than CFS

**Bằng chứng bắt buộc:**

* Bảng so sánh: 3 policies (priority range, time slice, preemption)
* Dự đoán: Policy nào có latency thấp nhất? Jitter thấp nhất?

---

## **Part 2 — Tool Setup & Configuration**

**Mục tiêu:** Cài đặt và sử dụng cyclictest.

**Sinh viên cần làm và nộp:**

* **Install cyclictest**:
  ```bash
  sudo apt install rt-tests
  ```

* **Basic usage**:
  ```bash
  cyclictest -p <priority> -t 1 -n -i <interval_us> -l <loops> -m -a <cpu>
  ```
  - `-p`: Priority (0 for SCHED_OTHER, 1-99 for RT)
  - `-t`: Number of threads (dùng 1 cho simplicity)
  - `-n`: Use clock_nanosleep instead of nanosleep
  - `-i`: Interval in microseconds (1000 = 1ms)
  - `-l`: Number of loops (200,000 = ~3 phút với 1ms interval)
  - `-m`: Lock memory (mlockall) để tránh page faults
  - `-a`: CPU affinity

* **Scenarios**:
  1. **SCHED_OTHER, no affinity, no load**:
     ```bash
     cyclictest -p 0 -t 1 -n -i 1000 -l 200000 -m > logs/other_baseline.log
     ```
  
  2. **SCHED_RR priority 50, no affinity, no load**:
     ```bash
     sudo cyclictest -p 50 --policy rr -t 1 -n -i 1000 -l 200000 -m > logs/rr_baseline.log
     ```
  
  3. **SCHED_FIFO priority 99, no affinity, no load**:
     ```bash
     sudo cyclictest -p 99 -t 1 -n -i 1000 -l 200000 -m > logs/fifo_baseline.log
     ```
  
  4. **SCHED_FIFO priority 99, CPU affinity (core 2), no load**:
     ```bash
     sudo cyclictest -p 99 -t 1 -n -i 1000 -l 200000 -m -a 2 > logs/fifo_affinity.log
     ```
  
  5. **SCHED_FIFO priority 99, CPU affinity, WITH background load**:
     ```bash
     # Terminal 1: Start stress
     stress-ng --cpu 4 --timeout 300s
     
     # Terminal 2: Run cyclictest
     sudo cyclictest -p 99 -t 1 -n -i 1000 -l 200000 -m -a 2 > logs/fifo_stress.log
     ```

* **Script automation**:
  - `run_experiments.sh`: Chạy tất cả 5+ scenarios tự động
  - Save logs vào thư mục `logs/<timestamp>/`
  - Gen summary với tail latency (p95, p99, max)

**Bằng chứng bắt buộc:**

* Script `run_experiments.sh` (hoặc commands list)
* 5 log files tương ứng với 5 scenarios
* Environment info: kernel version, CPU model, RT patch (nếu có)

---

## **Part 3 — Measurement & Metrics**

**Mục tiêu:** Trích xuất metrics từ cyclictest logs.

**Sinh viên cần làm và nộp:**

* **Cyclictest output format**:
  ```
  # /dev/cpu_dma_latency set to 0us
  T: 0 ( 1234) P:99 I:1000 C: 200000 Min:      8 Act:   12 Avg:   10 Max:      45
  ```
  - Min: Minimum latency (μs)
  - Avg: Average latency (μs)
  - Max: Maximum latency (μs)
  - Histogram data (trong log file)

* **Metrics extraction**:
  - Parse log file để lấy Min/Avg/Max
  - Histogram → calculate p95, p99
  - Jitter = standard deviation (nếu có raw data)

* **Summary table**:
  | Scenario | Policy | Affinity | Load | Avg (μs) | p95 (μs) | p99 (μs) | Max (μs) |
  |----------|--------|----------|------|----------|----------|----------|----------|
  | 1 | OTHER | No | No | XX | XX | XX | XX |
  | 2 | RR | No | No | XX | XX | XX | XX |
  | 3 | FIFO | No | No | XX | XX | XX | XX |
  | 4 | FIFO | Yes (CPU 2) | No | XX | XX | XX | XX |
  | 5 | FIFO | Yes (CPU 2) | Yes (stress-ng) | XX | XX | XX | XX |

* **Comparison analysis**:
  - Best case: SCHED_FIFO + affinity + no load
  - Worst case: SCHED_OTHER + no affinity + stress
  - Improvement: (Worst - Best) / Worst × 100%

**Bằng chứng bắt buộc:**

* Summary table với ≥5 scenarios
* Script hoặc commands parse logs
* Raw histogram data (hoặc sample)

---

## **Part 4 — Analysis & Visualization**

**Mục tiêu:** Visualize kết quả và giải thích findings.

**Sinh viên cần làm và nộp:**

* **Visualization 1: Histogram**
  - X-axis: Latency (μs)
  - Y-axis: Frequency
  - 3 curves: SCHED_OTHER, SCHED_RR, SCHED_FIFO (baseline)
  - Observation: FIFO distribution tập trung hơn (lower jitter)

* **Visualization 2: CDF (Cumulative Distribution Function)**
  - X-axis: Latency (μs)
  - Y-axis: Cumulative probability (0-1)
  - Compare 5 scenarios
  - Observation: FIFO+affinity có tail thấp nhất

* **Visualization 3: Max latency bar chart**
  - X-axis: Scenarios
  - Y-axis: Max latency (μs)
  - Show impact của policy, affinity, stress

* **Root cause analysis**:
  - **Why SCHED_OTHER has high jitter?**
    * CFS dynamic priority → variable scheduling delay
    * Time-sharing → preempted by other processes
  
  - **Why SCHED_FIFO best?**
    * No time slice → runs continuously
    * Highest priority → preempts all other tasks
    * Deterministic behavior
  
  - **Why CPU affinity helps?**
    * No migration → cache warm
    * Reduced context switch overhead
    * Improvement: ~40% reduction in p99 latency
  
  - **Why stress-ng increases latency?**
    * Even SCHED_FIFO affected (IRQ, cache contention)
    * SCHED_OTHER worst (directly contends with stress)

* **Trade-offs**:
  | Policy | Latency | Fairness | Risk |
  |--------|---------|----------|------|
  | OTHER | High | High | None |
  | RR | Medium | Medium | Low starvation |
  | FIFO | Low | Low | High starvation |

**Bằng chứng bắt buộc:**

* ≥2 plots (histogram/CDF + bar chart)
* 5-10 dòng phân tích root cause
* Trade-off table

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab3_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo nên dài khoảng **3-5 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Introduction & Theory** [20 points]
  - Định nghĩa 3 policies: SCHED_OTHER, SCHED_RR, SCHED_FIFO (1-2 dòng mỗi cái)
  - CPU affinity: lợi ích và cách setup
  - Dự đoán: Policy nào tốt nhất?

* **c. Methodology** [15 points]
  - Tool: cyclictest commands
  - 5 scenarios: policy, affinity, load
  - Parameters: interval 1ms, loops 200k
  - Environment: OS, kernel, CPU

* **d. Results** [30 points]
  - **Bảng 1**: Summary table (5+ scenarios với avg/p95/p99/max)
  - **Figure 1**: Histogram hoặc CDF (3+ curves)
  - **Figure 2**: Max latency bar chart (5 scenarios)
  - Mô tả kết quả (3-5 dòng)

* **e. Analysis** [25 points]
  - So sánh: FIFO vs RR vs OTHER
  - Impact của CPU affinity: % improvement
  - Impact của stress: % degradation
  - Root cause: Why FIFO best, why OTHER worst
  - Trade-offs: Latency vs Fairness

* **f. Conclusion** [10 points]
  - Summary: FIFO+affinity best (p99 = XX μs)
  - Recommendation: Dùng SCHED_FIFO cho real-time tasks
  - Limitations: Chưa test với multiple threads
  - Future work: Test với IRQ affinity, CPU isolation (isolcpus)

### 2. **Code & Data Package**

**Bắt buộc có:**

* `run_experiments.sh`: Script chạy tất cả scenarios
* `logs/`: Thư mục chứa 5+ log files từ cyclictest
* `parse_logs.py` (hoặc tương đương): Script extract metrics
* `plots/`: Histogram, CDF, bar chart
* `README.md`: Instructions để reproduce

### 3. **Demo** (optional, bonus +5)

* Video 1-2 phút: show cyclictest chạy, histogram plot

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 20 | 3 policies explained, affinity, prediction |
| **Methodology** | 15 | cyclictest commands, 5 scenarios, environment |
| **Results** | 30 | Summary table + 2 plots (histogram/CDF + bar) |
| **Analysis** | 25 | Comparison, root cause, trade-offs |
| **Conclusion** | 10 | Summary, recommendation, limitations |
| **Total** | **100** | |

**Bonus** (up to +10):
* CDF plot professionally formatted: +3
* Test với IRQ affinity (`/proc/irq/*/smp_affinity`): +4
* Comparison với RT kernel vs vanilla kernel: +3

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Disable CPU frequency scaling**: `cpupower frequency-set -g performance`
* **Disable IRQ balancing**: `sudo systemctl stop irqbalance`
* **Large sample size**: 200k loops minimum
* **Multiple runs**: Chạy 3 lần, lấy median để giảm noise
* **Isolate CPU**: `isolcpus=2,3` kernel parameter (advanced)

### ❌ Don'ts:
* **Không chạy trên laptop**: Battery mode, thermal throttling gây jitter
* **Không quên sudo**: Real-time policies cần root
* **Không run khi có background tasks**: Close browser, IDE trước khi test

### 🔧 Debugging:
* **Max latency >1ms**: Check IRQ, disable irqbalance, pin IRQ vào CPU khác
* **No difference giữa RR và FIFO**: Interval quá lớn (1ms OK, 100ms không thấy khác biệt)
* **Permission denied**: Cần sudo hoặc `setcap cap_sys_nice=eip cyclictest`

---

## **References**

1. Linux Foundation. (2024). *Real-Time Linux Wiki - cyclictest*. https://wiki.linuxfoundation.org/realtime/documentation/howto/tools/cyclictest

2. Rostedt, S. (2024). *RT-Tests Documentation*. https://git.kernel.org/pub/scm/utils/rt-tests/rt-tests.git

3. Linux Manual Pages. (2024). *sched(7) - Overview of CPU scheduling*. https://man7.org/linux/man-pages/man7/sched.7.html

4. Gleixner, T., & Niehaus, D. (2006). *Hrtimers and Beyond: Transforming the Linux Time Subsystems*. Linux Symposium.

---

**Good luck!** ⏱️
