**Lab 2: Priority Inversion Demo**  
**Tổng điểm:** 100  
**Thời gian:** 1-2 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm. Nếu nộp trước **11:59 PM** của ngày sau ngày đến hạn, bài sẽ vẫn được chấp nhận nhưng **bị trừ 20%** điểm.

**Lưu ý:** Báo cáo nộp cho lab này phải là **bài làm cá nhân của bạn**. Bất kỳ trường hợp **đạo văn** nào sẽ được xem như bài làm không hợp lệ.

---

## **Lab overview**

Mục tiêu lab là mô phỏng **priority inversion problem** và chứng minh hiệu quả của **Priority Inheritance Protocol (PIP)**.

Scenario:
* 3 threads: Low (L), Medium (M), High (H)
* L và H share mutex
* M không dùng mutex nhưng có priority giữa L và H
* **Vấn đề**: H bị block bởi M (priority thấp hơn) → unbounded blocking

Giải pháp: Priority Inheritance
* Khi H wait mutex, L được boost lên priority của H
* L không bị M preempt → release mutex nhanh
* H acquire mutex và continue

Deliverable:
* Code demo với/không Priority Inheritance
* Đo response time của H thread trong cả 2 cases
* Báo cáo 3-5 trang chứng minh PI hiệu quả

---

## **Part 1 — Problem Statement & Theory**

**Mục tiêu:** Hiểu rõ priority inversion problem và Priority Inheritance Protocol.

**Sinh viên cần làm và nộp:**

* **Priority Inversion definition**:
  - High priority task bị block bởi lower priority task (indirect)
  - Example: Mars Pathfinder incident (1997)
  
* **Scenario description**:
  1. Low (priority 10) acquires mutex
  2. High (priority 30) tries to acquire → blocked
  3. Medium (priority 20) preempts Low
  4. **Result**: High waits for Medium to finish (priority inversion!)

* **Priority Inheritance Protocol**:
  - When H blocks on mutex held by L:
    * L temporarily inherits priority of H (boost to 30)
    * M cannot preempt L anymore
    * L finishes critical section → releases mutex
    * L returns to original priority (10)
    * H acquires mutex
  - **Bounded blocking**: H waits at most duration of L's critical section

* **Expected improvement**:
  - Without PI: Response time of H = C_L + C_M + C_H (unbounded)
  - With PI: Response time of H = C_L + C_H (bounded)

**Bằng chứng bắt buộc:**

* Diagram: Timeline showing priority inversion (before PI)
* Diagram: Timeline showing priority inheritance (after PI)
* Formula: Expected blocking time calculation

---

## **Part 2 — Implementation**

**Mục tiêu:** Triển khai 3 threads với mutex và barrier synchronization.

**Sinh viên cần làm và nộp:**

* **Thread configuration**:
  ```
  Low thread:
    - Priority: 10 (SCHED_FIFO)
    - Work: 100ms computation
    - Critical section: 50ms (holding mutex)
  
  Medium thread:
    - Priority: 20 (SCHED_FIFO)
    - Work: 100ms computation
    - No mutex usage
  
  High thread:
    - Priority: 30 (SCHED_FIFO)
    - Work: 10ms computation
    - Critical section: 5ms (holding mutex)
  ```

* **Execution flow**:
  1. All threads wait at barrier
  2. Release barrier → all start simultaneously
  3. Low acquires mutex first (starts earlier)
  4. High tries to acquire → blocked
  5. Medium preempts Low (if no PI)
  6. Measure response time of High
  7. Repeat 100 iterations

* **Priority Inheritance setup**:
  ```c
  // Without PI (default)
  pthread_mutex_init(&mutex, NULL);
  
  // With PI
  pthread_mutexattr_t attr;
  pthread_mutexattr_init(&attr);
  pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);
  pthread_mutex_init(&mutex, &attr);
  ```

**Bằng chứng bắt buộc:**

* Code snippet: Thread creation với priority setting
* Code snippet: Mutex initialization với PTHREAD_PRIO_INHERIT
* Code snippet: Barrier synchronization
* Command: `sudo ./priority_inversion_demo --policy inherit --iterations 100`

---

## **Part 3 — Measurement & Logging**

**Mục tiêu:** Đo response time của High thread và log kết quả.

**Sinh viên cần làm và nộp:**

* **Response time definition**:
  - Start: High thread ready (after barrier release)
  - End: High thread completes critical section
  - Response time = End - Start

* **Logging mechanism**:
  - Log mỗi iteration: `iteration, policy, low_time_ms, medium_time_ms, high_response_ms, blocking_ms`
  - Save to: `results.csv`

* **Metrics calculation**:
  - Average response time
  - p99 response time
  - Max response time
  - Standard deviation (jitter)
  - Improvement: (time_without_PI - time_with_PI) / time_without_PI × 100%

* **Run configuration**:
  - Iterations: 100 (minimum)
  - 2 runs: `--policy none` và `--policy inherit`
  - Hold time: 50ms (configurable: `--hold-ms 50`)
  - Work time: 100ms (configurable: `--work-ms 100`)

**Bằng chứng bắt buộc:**

* File `results_none.csv` (without PI)
* File `results_inherit.csv` (with PI)
* Script `analyze_results.py`: Tính avg, p99, improvement
* Raw data hoặc sample 20 iterations

---

## **Part 4 — Analysis & Comparison**

**Mục tiêu:** So sánh performance với/không PI, giải thích cải thiện.

**Sinh viên cần làm và nộp:**

* **Comparison table**:
  | Metric | Without PI | With PI | Improvement |
  |--------|-----------|---------|-------------|
  | Avg response time | XXX ms | YYY ms | ZZ% |
  | p99 response time | XXX ms | YYY ms | ZZ% |
  | Max response time | XXX ms | YYY ms | ZZ% |
  | Jitter (stddev) | XXX ms | YYY ms | ZZ% |

* **Root cause analysis**:
  - Without PI: Tại sao High thread response time cao?
    * L holds mutex, M preempts L
    * H waits for M to finish (~100ms) + L to finish (~50ms)
  - With PI: Tại sao response time giảm?
    * L boosted to priority 30 (same as H)
    * M cannot preempt L
    * H only waits for L's critical section (~50ms)

* **Theoretical vs Measured**:
  - Expected without PI: 100ms (M) + 50ms (L) = 150ms
  - Measured without PI: ~XXX ms (should be close to 150ms)
  - Expected with PI: 50ms (L's critical section only)
  - Measured with PI: ~YYY ms (should be close to 50ms)
  - If mismatch: explain (context switch overhead, cache miss, etc.)

* **Variation analysis**:
  - Plot: Box plot hoặc histogram của response time
  - Without PI: High variance (depends on when M arrives)
  - With PI: Low variance (predictable blocking time)

**Bằng chứng bắt buộc:**

* Comparison table (4 metrics minimum)
* 1 plot: Box plot hoặc CDF của response time
* 5-10 dòng phân tích: Why PI works, theoretical match
* Timeline diagram (1 iteration) showing blocking pattern

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab2_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo nên dài khoảng **3-5 trang** (không tính phụ lục).

**Báo cáo phải gồm:**

* **a. Title page**: Lab 2: Priority Inversion + Tên + MSSV + Ngày [không tính điểm]

* **b. Problem Statement** [15 points]
  - Định nghĩa priority inversion (2-3 dòng)
  - Scenario: L, M, H và mutex
  - Tại sao đây là vấn đề? (mention Mars Pathfinder)
  - Priority Inheritance Protocol: cơ chế hoạt động (3-5 dòng)

* **c. Design & Implementation** [20 points]
  - Bảng thread configuration (priority, work time, hold time)
  - Execution flow (6 bước)
  - Code snippet: Mutex init với PTHREAD_PRIO_INHERIT (5 dòng)
  - Command để chạy 2 cases

* **d. Results** [30 points]
  - **Bảng 1**: Response time comparison (avg/p99/max/stddev)
  - **Figure 1**: Box plot hoặc CDF (2 curves: with/without PI)
  - **Figure 2**: Timeline diagram (1 iteration, showing blocking)
  - Mô tả kết quả (3-5 dòng)

* **e. Analysis** [25 points]
  - Tại sao without PI → response time cao?
  - Tại sao with PI → response time thấp?
  - Theoretical vs Measured: compare expected 150ms (no PI) and 50ms (with PI)
  - Root cause cho variance: context switch, scheduling delay
  - Trade-off: PI overhead nhỏ (~1-2μs) vs benefit lớn (50-100ms)

* **f. Conclusion** [10 points]
  - Summary: PI reduces response time XX%
  - Limitations: Chỉ test với 1 mutex, không test deadlock
  - Recommendations: Luôn dùng PI cho real-time mutexes
  - Future work: Test với nested locks, Priority Ceiling Protocol

### 2. **Code & Data Package**

**Bắt buộc có:**

* `priority_inversion_demo.c` (hoặc `.cpp`)
* `Makefile` hoặc compile instructions
* `README.md`: Build và run instructions
* `results_none.csv`: Log without PI
* `results_inherit.csv`: Log with PI
* `analyze_results.py`: Script tính metrics và gen plots
* `plots/`: Box plot, timeline diagram

### 3. **Demo** (optional, bonus +5)

* Video 1 phút: show 2 runs (with/without PI), so sánh response time

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Problem Statement** | 15 | Priority inversion & PI protocol explained clearly |
| **Design & Implementation** | 20 | Thread config, mutex init code, execution flow |
| **Results** | 30 | Comparison table + 2 figures (box plot + timeline) |
| **Analysis** | 25 | Root cause, theoretical vs measured, trade-off |
| **Conclusion** | 10 | Summary, limitations, recommendations |
| **Total** | **100** | |

**Bonus** (up to +10):
* Timeline animation (GIF/video): +5
* Test với multiple hold times (20ms, 50ms, 100ms): +3
* Comparison với Priority Ceiling Protocol: +2

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Barrier sync**: Dùng `pthread_barrier_wait()` để all threads start đồng thời
* **Large iterations**: ≥100 để có distribution rõ ràng
* **Vary parameters**: Test với hold time 20ms, 50ms, 100ms để thấy trend
* **Timestamp precision**: `clock_gettime(CLOCK_MONOTONIC)` với nanosecond

### ❌ Don'ts:
* **Không dùng `sleep()` trong critical section**: Sẽ release CPU, mutex vẫn hold → deadlock risk
* **Không run mà không sudo**: SCHED_FIFO cần root
* **Không quên set priority**: Nếu không set, all threads default priority → không có inversion

### 🔧 Debugging:
* **Response time không khác nhau**: Check priority setting (dùng `chrt -p <pid>`)
* **Deadlock**: Check barrier usage, mutex unlock
* **PI không work**: Verify `pthread_mutexattr_setprotocol()` return 0

---

## **References**

1. Sha, L., Rajkumar, R., & Lehoczky, J. P. (1990). *Priority Inheritance Protocols: An Approach to Real-Time Synchronization*. IEEE Transactions on Computers, 39(9), 1175-1185.

2. Reeves, G. (1997). *What Really Happened on Mars?* (Mars Pathfinder priority inversion incident). https://cs.unc.edu/~anderson/teach/comp790/papers/mars_pathfinder_long_version.html

3. POSIX. (2024). *pthread_mutexattr_setprotocol()*. https://pubs.opengroup.org/onlinepubs/9699919799/

4. Linux Manual Pages. (2024). *pthread_mutexattr_setprotocol(3)*. https://man7.org/linux/man-pages/man3/pthread_mutexattr_setprotocol.3.html

---

**Good luck!** 🔒
