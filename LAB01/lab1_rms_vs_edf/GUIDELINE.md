**Lab 1: RMS vs EDF trên Linux**  
**Tổng điểm:** 100  
**Thời gian:** 2-3 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm. Nếu nộp trước **11:59 PM** của ngày sau ngày đến hạn, bài sẽ vẫn được chấp nhận nhưng **bị trừ 20%** điểm.

**Lưu ý:** Báo cáo nộp cho lab này phải là **bài làm cá nhân của bạn** hoặc **được trích dẫn đúng quy định**. Bất kỳ trường hợp **bị nghi ngờ đạo văn** nào sẽ đều được xem như bài làm không hợp lệ.

---

## **Lab overview**

Mục tiêu lab là triển khai và so sánh hai thuật toán lập lịch thời gian thực:
* **Rate-Monotonic Scheduling (RMS)** - Fixed priority based on period
* **Earliest Deadline First (EDF)** - Dynamic priority based on deadline

Bạn sẽ tạo task set chu kỳ với {period, WCET, deadline}, chạy trên Linux với SCHED_FIFO (RMS) và SCHED_DEADLINE (EDF), sau đó đo và so sánh **deadline miss rate** và **latency distribution**.

Deliverable tối thiểu:
* Code chạy được + log/trace chứng minh
* KPI: deadline miss rate, p95/p99 latency, jitter
* Báo cáo 4-6 trang theo cấu trúc dưới đây

---

## **Part 1 — Task Model & Schedulability Analysis**

**Mục tiêu:** Định nghĩa task set và phân tích schedulability theo lý thuyết.

**Sinh viên cần làm và nộp:**

* **Mô hình tác vụ**: Bảng task set với:
  - Task ID, Period (T), WCET (C), Deadline (D)
  - Ví dụ: Task 1: C=5ms, T=50ms, D=50ms
* **Tính utilization**: U = Σ(Cᵢ/Tᵢ)
* **Liu-Layland bound**: Cho n tasks, bound = n(2^(1/n) - 1)
  - n=3: bound ≈ 0.78
  - Kết luận: Task set có schedulable với RMS không?
* **EDF schedulability**: U ≤ 1.0 (optimal)

**Bằng chứng bắt buộc:**

* Bảng task set đầy đủ
* Tính toán utilization và so sánh với bound
* Dự đoán: RMS có miss deadline không? EDF thì sao?

---

## **Part 2 — Implementation & Configuration**

**Mục tiêu:** Triển khai periodic tasks trên Linux với RMS và EDF policies.

**Sinh viên cần làm và nộp:**

* **RMS implementation**:
  - Dùng `SCHED_FIFO` với priority assignment theo period (T nhỏ → priority cao)
  - Code: `pthread_setschedparam()`, `sched_setscheduler()`
  - Priority mapping: Task 1 (T=50ms) → priority 30, Task 2 (T=80ms) → priority 20, Task 3 (T=200ms) → priority 10
  
* **EDF implementation**:
  - Dùng `SCHED_DEADLINE` với runtime, deadline, period parameters
  - Code: `sched_setattr()` với `struct sched_attr`
  - Hoặc mô phỏng EDF ở user-space nếu kernel không support

* **Periodic execution**:
  - Dùng `clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, ...)` để đảm bảo period chính xác
  - Không dùng `sleep()` vì drift accumulation

**Bằng chứng bắt buộc:**

* Code snippet: thread creation, priority setting, periodic loop
* Command để chạy: `sudo ./periodic_demo --policy rms --duration 60`
* Screenshot `chrt -p <pid>` hoặc `/proc/<pid>/sched` cho thấy policy/priority

---

## **Part 3 — Measurement & Logging**

**Mục tiêu:** Đo deadline hit/miss, latency, jitter cho cả RMS và EDF.

**Sinh viên cần làm và nộp:**

* **Logging mechanism**:
  - Log mỗi iteration: `timestamp, task_id, release_time, completion_time, deadline, hit/miss`
  - Save to CSV: `schedule_log.csv`
  
* **Metrics calculation**:
  - **Deadline miss rate**: (số miss / tổng số jobs) × 100%
  - **Latency**: completion_time - release_time
  - **Jitter**: standard deviation của latency
  - **Percentiles**: p50, p95, p99, p99.9, max

* **Run configuration**:
  - Duration: 60 seconds minimum (đủ data cho phân tích)
  - Iterations: ≥1000 jobs per task
  - Environment: Linux RT kernel (nếu có), isolate CPU (khuyến nghị)

**Bằng chứng bắt buộc:**

* File `schedule_log_rms.csv` và `schedule_log_edf.csv`
* Script phân tích: `analyze_log.py` tính miss rate, percentiles
* Raw log data (hoặc sample 100 dòng đầu tiên)

---

## **Part 4 — Comparison & Analysis**

**Mục tiêu:** So sánh RMS vs EDF, giải thích kết quả, và test stress scenario.

**Sinh viên cần làm và nộp:**

* **Baseline comparison**:
  - Bảng so sánh: RMS vs EDF
  - Metrics: deadline miss rate, p99 latency, max latency, jitter
  - Kết luận: Policy nào tốt hơn? Tại sao?

* **Stress test** (ít nhất 1):
  - **Scenario 1**: Tăng utilization (thêm task hoặc tăng WCET)
  - **Scenario 2**: Background load (stress-ng, compile kernel)
  - **Scenario 3**: CPU frequency scaling (disable turbo boost)
  - Đo lại miss rate và latency
  - So sánh: Policy nào robust hơn?

* **Root cause analysis**:
  - Nếu có deadline miss: tại sao? (preemption, IRQ, cache miss?)
  - Timestamp analysis: chỉ ra event gây miss
  - Trade-off: RMS đơn giản vs EDF optimal

**Bằng chứng bắt buộc:**

* Bảng KPI: Baseline (RMS/EDF) và Stress case
* Timeline hoặc Gantt chart (200-500ms snapshot) cho thấy task execution
* 1 đoạn phân tích (5-10 dòng) giải thích kết quả

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab1_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo nên dài khoảng **4-6 trang** (không tính phụ lục), có hình/bảng/đồ thị.

**Báo cáo phải gồm:**

* **a. Title page**: Lab 1: RMS vs EDF + Tên + MSSV + Ngày nộp [không tính điểm]

* **b. Introduction & Theory** [15 points]
  - Định nghĩa RMS và EDF (2-3 dòng mỗi cái)
  - Liu-Layland bound formula và ý nghĩa
  - Tại sao EDF optimal nhưng RMS vẫn được dùng?

* **c. Task Set & Schedulability Analysis** [15 points]
  - Bảng task set: Task ID, C, T, D, Priority (RMS)
  - Tính U = Σ(C/T)
  - So sánh với Liu-Layland bound (cho RMS) và 100% (cho EDF)
  - Dự đoán schedulability

* **d. Implementation** [15 points]
  - Mô tả cách implement RMS (SCHED_FIFO + priority)
  - Mô tả cách implement EDF (SCHED_DEADLINE hoặc user-space)
  - Code snippet: priority setting và periodic loop (5-10 dòng)
  - Command để chạy

* **e. Results** [25 points]
  - **Bảng 1**: Deadline miss rate (RMS vs EDF)
  - **Bảng 2**: Latency statistics (p50/p95/p99/max, jitter)
  - **Figure 1**: CDF của latency (2 curves: RMS và EDF)
  - **Figure 2**: Timeline/Gantt chart (optional nhưng recommend)
  - Mô tả ngắn kết quả (3-5 dòng)

* **f. Stress Test** [15 points]
  - Scenario: Tăng U lên 85% hoặc background load
  - Bảng KPI: Baseline vs Stress (cho cả RMS và EDF)
  - Quan sát: Policy nào chịu stress tốt hơn?

* **g. Analysis & Discussion** [10 points]
  - Tại sao EDF tốt hơn RMS? (hoặc ngược lại trong case nào?)
  - Root cause cho deadline misses (nếu có)
  - Trade-off: Complexity vs Performance
  - So sánh với lý thuyết: Kết quả match với Liu-Layland bound không?

* **h. Conclusion** [5 points]
  - Tóm tắt findings (3-5 dòng)
  - Limitations (ví dụ: không test với sporadic tasks)
  - Future work (ví dụ: test với precedence constraints)

### 2. **Code & Data Package** (nộp dạng .zip hoặc repo link)

**Bắt buộc có:**

* `periodic_demo.c` (hoặc `.cpp`, `.py`): Source code
* `Makefile` hoặc `compile.sh`: Cách build
* `README.md`: 
  - Environment requirements (OS, kernel version, tools)
  - Build instructions: `make` hoặc `gcc -o ...`
  - Run instructions: `sudo ./periodic_demo --policy rms --duration 60`
* `schedule_log_rms.csv`: Log từ RMS run
* `schedule_log_edf.csv`: Log từ EDF run
* `analyze_log.py` (hoặc tương đương): Script tính metrics
* `plots/`: Thư mục chứa đồ thị (CDF, timeline) đã dùng trong report

**Optional nhưng recommend:**

* `run_all.sh`: Script chạy cả RMS và EDF, gen logs và plots
* `stress_test.sh`: Script chạy stress scenarios
* `configs/`: Các task set khác nhau (baseline, high-load, etc.)

### 3. **Demo** (optional cho lab, bắt buộc cho project)

Nếu muốn điểm bonus:
* Video 1-2 phút: show code chạy, deadline miss trong log, CDF plot
* Hoặc live demo trong buổi lab

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Introduction & Theory** | 15 | RMS/EDF definition rõ ràng, Liu-Layland explained |
| **Task Set & Analysis** | 15 | Task set đầy đủ, utilization calculated, schedulability analysis |
| **Implementation** | 15 | Code snippet, priority setting correct, command clear |
| **Results** | 25 | 2 tables + 1 CDF plot, miss rate & latency stats |
| **Stress Test** | 15 | 1 stress scenario, KPI before/after |
| **Analysis** | 10 | Explain why, root cause, trade-offs |
| **Conclusion** | 5 | Summary, limitations, future work |
| **Total** | **100** | |

**Bonus points** (up to +10):
* Timeline/Gantt chart visualization: +5
* Multiple stress scenarios (≥2): +3
* Clean reproducible code với `run_all.sh`: +2

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Isolate CPU**: `isolcpus=2,3` kernel parameter để giảm noise
* **RT kernel**: Dùng PREEMPT_RT patch nếu có
* **Pin threads**: `pthread_setaffinity_np()` để tránh migration
* **Large sample**: ≥1000 iterations để có data đủ cho percentile analysis
* **Timestamp precision**: Dùng `clock_gettime(CLOCK_MONOTONIC)` thay vì `gettimeofday()`

### ❌ Don'ts:
* **Không dùng `sleep()`**: Sẽ có drift, dùng `clock_nanosleep()` với ABSTIME
* **Không run mà không sudo**: SCHED_FIFO/DEADLINE cần root privilege
* **Không quên fsync log**: Flush CSV ngay để không mất data khi crash
* **Không test trên laptop**: Frequency scaling, thermal throttling gây jitter cao

### 🔧 Debugging:
* **Deadline miss không match lý thuyết**: Check kernel preemption, IRQ affinity
* **Jitter cao**: Disable irqbalance, cpufreq governor = performance
* **SCHED_DEADLINE not found**: Kernel không compile với CONFIG_SCHED_DEADLINE

---

## **References**

1. Liu, C. L., & Layland, J. W. (1973). *Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment*. Journal of the ACM, 20(1), 46-61.

2. Linux Manual Pages. (2024). *sched(7) - Overview of CPU scheduling*. https://man7.org/linux/man-pages/man7/sched.7.html

3. Linux Foundation. (2024). *Real-Time Linux Wiki*. https://wiki.linuxfoundation.org/realtime/

4. Reghenzani, F., Massari, G., & Fornaciari, W. (2019). *The Real-Time Linux Kernel: A Survey on PREEMPT_RT*. ACM Computing Surveys, 52(1).

---

## **Contact & Support**

* **Office hours**: [TBD]
* **Email**: [TBD]
* **Forum**: Teams channel

**Good luck!** 🚀
