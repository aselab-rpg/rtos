**Labs 4-5: Zephyr RTOS Message Passing (k_msgq & k_mbox)**  
**Tổng điểm:** 100  
**Thời gian:** 2-3 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Mục tiêu labs là thực hành message passing mechanisms trên **Zephyr RTOS**:

* **Lab 4 (k_msgq)**: Message queue với fixed-size messages
  - Client gửi chu kỳ (10ms period) → Server xử lý (15ms)
  - Đo latency, backlog, drop rate
  - So sánh: Server high priority vs low priority

* **Lab 5 (k_mbox)**: Mailbox với variable-size messages
  - Client gửi burst messages → Server xử lý bất đồng bộ
  - Dùng semaphore để báo completion
  - So sánh: Server priority impact

Deliverable:
* Code chạy được trên QEMU hoặc real board
* Log: latency, backlog, drops
* Báo cáo 4-6 trang (combined cho cả 2 labs)

---

## **Part 1 — Zephyr RTOS & Scheduling**

**Mục tiêu:** Hiểu Zephyr scheduling và message passing primitives.

**Sinh viên cần làm và nộp:**

* **Zephyr scheduling**:
  - Preemptive priority-based
  - Priority 0 = **highest** (ngược với Linux!)
  - Cooperative threads: priority < 0 (không preempt nhau)
  - Preemptive threads: priority ≥ 0

* **k_msgq (Message Queue)**:
  - Fixed-size messages (e.g., 32 bytes)
  - FIFO queue, bounded capacity (e.g., 10 messages)
  - Blocking send/receive
  - Use case: High-frequency periodic messages

  ```c
  K_MSGQ_DEFINE(my_msgq, MSG_SIZE, QUEUE_SIZE, 4);
  
  // Send (blocks if full)
  k_msgq_put(&my_msgq, &msg, K_FOREVER);
  
  // Receive (blocks if empty)
  k_msgq_get(&my_msgq, &msg, K_FOREVER);
  ```

* **k_mbox (Mailbox)**:
  - Variable-size messages
  - Sender-priority based (high priority sender → processed first)
  - Supports async send/receive
  - Use case: Variable payload, deferred work

  ```c
  K_MBOX_DEFINE(my_mbox);
  
  // Send
  k_mbox_put(&my_mbox, &send_msg, K_FOREVER);
  
  // Receive
  k_mbox_get(&my_mbox, &recv_msg, buffer, K_FOREVER);
  ```

* **Priority assignment principles**:
  - **Server ≥ Client priority**: Low latency, no backlog
  - **Server < Client priority**: High latency, backlog grows, drops possible

**Bằng chứng bắt buộc:**

* Bảng so sánh k_msgq vs k_mbox (fixed vs variable size, FIFO vs priority)
* Diagram: Client-Server architecture với message queue

---

## **Part 2 — Lab 4: k_msgq Implementation**

**Mục tiêu:** Triển khai client-server với message queue, đo impact của priority.

**Sinh viên cần làm và nộp:**

* **Configuration**:
  ```c
  #define MSG_SIZE 32          // bytes
  #define QUEUE_SIZE 10        // max messages
  #define CLIENT_PERIOD_MS 10  // send every 10ms
  #define SERVER_PROCESS_MS 15 // processing time
  ```

* **Client thread**:
  - Priority: 2 (preemptive)
  - Period: 10ms
  - Send message: sequence number + timestamp
  - Log: send time

* **Server thread**:
  - **Config 1 (Default)**: Priority 1 (higher than client)
  - **Config 2 (Overlay)**: Priority 3 (lower than client)
  - Receive message from queue
  - Simulate processing: 15ms
  - Log: receive time, latency, backlog, drops

* **Build & run**:
  ```bash
  # Default config (server priority 1)
  cd lab4_zephyr_msgq
  west build -b qemu_x86 -p always
  west build -t run
  
  # Overlay config (server priority 3)
  west build -b qemu_x86 -p always -- -DOVERLAY_CONFIG=overlay-server-low.conf
  west build -t run
  ```

* **Expected behavior**:
  - **Server prio 1 (high)**: 
    * Latency ≈ 15ms (processing time)
    * Backlog ≤ 1
    * No drops
  
  - **Server prio 3 (low)**:
    * Latency >> 15ms (waits for client to yield)
    * Backlog → 10 (queue full)
    * Drops occur when queue full

**Bằng chứng bắt buộc:**

* Code: `src/main.c` với client/server threads
* Config files: `prj.conf`, `overlay-server-low.conf`
* Log output: 2 runs (default và overlay)
* Commands để build và run

---

## **Part 3 — Lab 5: k_mbox Implementation**

**Mục tiêu:** Triển khai deferred work pattern với mailbox.

**Sinh viên cần làm và nộp:**

* **Configuration**:
  ```c
  #define BURST_SIZE 5            // messages per burst
  #define MAX_PAYLOAD_SIZE 256    // bytes
  #define SERVER_PROCESS_MS 20    // per message
  ```

* **Client thread**:
  - Priority: 3 (lower than server in default)
  - Send burst: 5 messages với variable payload (64-256 bytes)
  - Wait for semaphore (server signals when done)
  - Log: send time, wait time

* **Server thread**:
  - **Config 1 (Default)**: Priority 1 (high)
  - **Config 2 (Overlay)**: Priority 4 (low)
  - Receive from mailbox
  - Process message (20ms simulated work)
  - Signal semaphore to client
  - Log: receive time, latency

* **Semaphore pattern**:
  ```c
  K_SEM_DEFINE(work_done, 0, 1);
  
  // Client: wait for completion
  k_sem_take(&work_done, K_FOREVER);
  
  // Server: signal completion
  k_sem_give(&work_done);
  ```

* **Build & run**: Tương tự Lab 4 với overlay config

**Bằng chứng bắt buộc:**

* Code: `src/main.c` với mailbox + semaphore
* Log output: 2 runs (default và overlay)
* Comparison: Burst completion time

---

## **Part 4 — Measurement & Analysis**

**Mục tiêu:** Đo metrics và so sánh priority impact.

**Sinh viên cần làm và nộp:**

* **Metrics (Lab 4 - k_msgq)**:
  | Config | Server Prio | Avg Latency | Max Latency | Backlog Max | Drops |
  |--------|-------------|-------------|-------------|-------------|-------|
  | Default | 1 (high) | ~16ms | ~18ms | 1 | 0 |
  | Overlay | 3 (low) | ~62ms | ~105ms | 10 (full) | 8 |

* **Metrics (Lab 5 - k_mbox)**:
  | Config | Server Prio | Burst Time | Avg Msg Latency | Max Msg Latency |
  |--------|-------------|------------|-----------------|-----------------|
  | Default | 1 (high) | ~110ms | 22ms | 25ms |
  | Overlay | 4 (low) | ~250ms | 50ms | 85ms |

* **Analysis**:
  - **High server priority**:
    * Server preempts client ngay sau send
    * Message processed immediately
    * Low latency, no backlog
  
  - **Low server priority**:
    * Client runs continuously
    * Server chỉ chạy khi client blocks/yields
    * Messages accumulate → queue full → drops
  
  - **Calculation (Lab 4)**:
    * Send rate: 100 msgs/s (period 10ms)
    * Process rate: 67 msgs/s (processing 15ms)
    * → Backlog grows at 33 msgs/s
    * → Queue (size 10) full trong ~0.3s

* **Visualization**:
  - Timeline diagram: Client send vs Server receive
  - Plot: Latency over time (show spikes when backlog grows)

**Bằng chứng bắt buộc:**

* 2 comparison tables (Lab 4 & Lab 5)
* Root cause analysis (5-10 dòng)
* Timeline diagram (1 burst hoặc 200ms window)

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab4-5_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo **combined** cho cả 2 labs, dài khoảng **4-6 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Introduction** [10 points]
  - Zephyr RTOS overview (2-3 dòng)
  - k_msgq vs k_mbox: use cases
  - Priority assignment: impact lên latency

* **c. Lab 4: k_msgq** [35 points]
  - **Design**: Client-server architecture, parameters
  - **Implementation**: Code snippet (thread creation, k_msgq_put/get)
  - **Results**: Comparison table (default vs overlay)
  - **Analysis**: Tại sao low priority server → backlog + drops?

* **d. Lab 5: k_mbox** [35 points]
  - **Design**: Burst pattern, semaphore for sync
  - **Implementation**: Code snippet (k_mbox, k_sem)
  - **Results**: Comparison table (burst completion time)
  - **Analysis**: Impact của variable payload size

* **e. Comparison & Lessons** [15 points]
  - k_msgq vs k_mbox: When to use which?
  - Priority assignment best practices
  - Real-time implications: Producer faster than consumer → need buffering + drop policy

* **f. Conclusion** [5 points]
  - Summary: High priority server → low latency
  - Recommendation: Server priority ≥ max client priority
  - Future work: Test với multiple clients, priority inheritance

### 2. **Code & Data Package**

**Bắt buộc có (cho mỗi lab):**

* `src/main.c`: Source code
* `prj.conf`: Default config (server high priority)
* `overlay-server-low.conf`: Overlay (server low priority)
* `CMakeLists.txt`, `Kconfig`: Build files
* `README.md`: Build instructions, run commands
* `logs/`: Output logs (default và overlay)

### 3. **Demo** (optional, bonus +5)

* Video 2 phút: Show 2 configs chạy trên QEMU, compare latency

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Introduction** | 10 | Zephyr overview, k_msgq vs k_mbox |
| **Lab 4: k_msgq** | 35 | Design, code, results table, analysis |
| **Lab 5: k_mbox** | 35 | Design, code, results table, analysis |
| **Comparison** | 15 | k_msgq vs k_mbox use cases, priority lessons |
| **Conclusion** | 5 | Summary, recommendations |
| **Total** | **100** | |

**Bonus** (up to +10):
* Timeline animation showing priority inversion: +5
* Test với real board (nRF52, STM32): +3
* Multiple clients (3 clients → 1 server): +2

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Use QEMU initially**: Faster iteration than real board
* **Logging**: Dùng `printk()` với timestamps
* **Kconfig**: Customize parameters (period, queue size) qua Kconfig
* **Multiple runs**: Chạy 3-5 lần để đảm bảo kết quả consistent

### ❌ Don'ts:
* **Không block trong ISR**: k_msgq_put với K_FOREVER trong ISR → deadlock
* **Không quên set priority**: Default priority = 0 → tất cả highest priority
* **Không dùng printf**: Dùng printk (kernel-level) thay vì printf (libc)

### 🔧 Debugging:
* **QEMU không chạy**: Check `west list`, `west update`
* **Priority không work**: Verify với CONFIG_NUM_PREEMPT_PRIORITIES trong prj.conf
* **Backlog không tăng**: Server priority cao hơn client → không có backlog (expected)

---

## **Environment Setup**

### Install Zephyr:
```bash
# 1. Install dependencies
pip3 install west

# 2. Init workspace
west init ~/zephyrproject
cd ~/zephyrproject
west update

# 3. Export Zephyr environment
west zephyr-export

# 4. Install Python requirements
pip3 install -r zephyr/scripts/requirements.txt

# 5. Install toolchain (Zephyr SDK)
# Follow: https://docs.zephyrproject.org/latest/develop/getting_started/
```

### Verify:
```bash
cd zephyr/samples/hello_world
west build -b qemu_x86
west build -t run
# Should print "Hello World!"
```

---

## **References**

1. Zephyr Project. (2024). *Kernel Services - Message Queues*. https://docs.zephyrproject.org/latest/kernel/services/data_passing/message_queues.html

2. Zephyr Project. (2024). *Kernel Services - Mailboxes*. https://docs.zephyrproject.org/latest/kernel/services/data_passing/mailboxes.html

3. Zephyr Project. (2024). *Scheduling*. https://docs.zephyrproject.org/latest/kernel/services/scheduling/index.html

4. Nordic Semiconductor. (2024). *Getting Started with Zephyr RTOS*. https://developer.nordicsemi.com/nRF_Connect_SDK/

---

**Good luck!** 📬
