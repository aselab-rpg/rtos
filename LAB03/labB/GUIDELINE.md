**Lab B: UDP Periodic Stream — Deadline Miss Detection**  
**Tổng điểm:** 100  
**Thời gian:** 90 phút

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Lab này implement **periodic UDP stream** để mô phỏng real-time data flow (e.g., sensor readings, video frames).

Objectives:
* Sender: Gửi UDP packets với period T (e.g., 100ms)
* Receiver: Detect deadline misses (packet arrival > T)
* Measure jitter, deadline miss rate, packet loss

Deliverable:
* UDP sender & receiver (Python)
* Báo cáo 3-4 trang

---

## **Part 1 — UDP & Real-Time Streaming Theory**

**Mục tiêu:** Hiểu UDP protocol và periodic streaming model.

**Sinh viên cần làm và nộp:**

* **UDP (User Datagram Protocol)**:
  - **Connectionless**: No handshake (vs TCP 3-way handshake)
  - **Unreliable**: No guaranteed delivery, no retransmission
  - **Unordered**: Packets có thể arrive out-of-order
  - **Low overhead**: Smaller header (8 bytes vs TCP 20 bytes)
  - **Use cases**: Real-time streaming (video, audio, sensor data)

* **Periodic streaming model**:
  ```
  Sender:
    for i in 0..N:
      send packet_i at time t_i = i × T
      (T = period, e.g., 100ms)
  
  Receiver:
    Receive packet_i at time t_recv
    Deadline: t_recv ≤ t_i + D (D = deadline, e.g., T)
    If t_recv > t_i + D → deadline miss
  ```

* **Metrics**:
  - **Period (T)**: Interval giữa 2 packets (ms)
  - **Jitter**: Variation in inter-arrival time (stddev of Δt)
  - **Deadline miss rate**: % packets arrive late (> T + D)
  - **Packet loss rate**: % packets never received

* **Comparison UDP vs TCP**:
  | Feature | UDP | TCP | Best for |
  |---------|-----|-----|----------|
  | Reliability | ❌ No | ✅ Yes | UDP: Real-time, TCP: File transfer |
  | Ordering | ❌ No | ✅ Yes | UDP: Live stream, TCP: HTTP |
  | Latency | ✅ Low | ❌ High (retransmit) | UDP: Gaming, TCP: Email |
  | Overhead | ✅ 8B header | ❌ 20B header | UDP: IoT sensors |

**Bằng chứng bắt buộc:**

* UDP protocol definition (4 characteristics)
* Periodic streaming model (sender/receiver pseudo-code)
* Metrics: Period, jitter, deadline miss rate, packet loss
* Comparison table: UDP vs TCP (4 features)

---

## **Part 2 — UDP Sender Implementation**

**Mục tiêu:** Implement sender gửi packets với period T.

**Sinh viên cần làm và nộp:**

* **UDP sender** (`udp_sender.py`):
  ```python
  import socket
  import time
  import json
  
  # Config
  HOST = '127.0.0.1'
  PORT = 5555
  PERIOD = 0.1  # 100ms
  NUM_PACKETS = 100
  
  # Create UDP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
  for i in range(NUM_PACKETS):
      # Packet payload
      t_send = time.time()
      payload = json.dumps({
          'seq': i,
          't_send': t_send,
          'period': PERIOD
      })
      
      # Send
      sock.sendto(payload.encode(), (HOST, PORT))
      print(f"[{t_send:.6f}] Sent packet {i}")
      
      # Wait for next period
      time.sleep(PERIOD)
  
  sock.close()
  ```

* **Packet format** (JSON):
  ```json
  {
    "seq": 42,
    "t_send": 1234567890.123456,
    "period": 0.1
  }
  ```

* **Timing precision**:
  - `time.sleep(PERIOD)` có error ±1-10ms (OS scheduler)
  - **Solution**: Compensate drift:
    ```python
    start_time = time.time()
    for i in range(NUM_PACKETS):
        target_time = start_time + i * PERIOD
        # Send packet
        now = time.time()
        sleep_time = target_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)
    ```

**Bằng chứng bắt buộc:**

* Code: `udp_sender.py` với timing compensation
* Command: `python3 udp_sender.py --period 0.1 --count 100`
* Screenshot: Terminal output showing 10 packets sent

---

## **Part 3 — UDP Receiver & Deadline Detection**

**Mục tiêu:** Implement receiver detect deadline misses và packet loss.

**Sinh viên cần làm và nộp:**

* **UDP receiver** (`udp_receiver.py`):
  ```python
  import socket
  import time
  import json
  
  # Config
  HOST = '127.0.0.1'
  PORT = 5555
  DEADLINE_FACTOR = 1.5  # Deadline = 1.5 × Period
  
  # Create UDP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((HOST, PORT))
  
  print("Receiver listening on {}:{}".format(HOST, PORT))
  
  results = []
  
  while True:
      try:
          data, addr = sock.recvfrom(1024)
          t_recv = time.time()
          
          # Parse packet
          packet = json.loads(data.decode())
          seq = packet['seq']
          t_send = packet['t_send']
          period = packet['period']
          
          # Calculate latency and deadline
          latency = (t_recv - t_send) * 1000  # ms
          deadline = period * DEADLINE_FACTOR * 1000  # ms
          missed = latency > deadline
          
          # Log
          status = "MISS" if missed else "OK"
          print(f"[{t_recv:.6f}] Packet {seq}: latency={latency:.2f}ms, deadline={deadline:.0f}ms [{status}]")
          
          results.append({
              'seq': seq,
              'latency': latency,
              'missed': missed
          })
          
      except KeyboardInterrupt:
          break
  
  # Summary
  total = len(results)
  misses = sum(r['missed'] for r in results)
  miss_rate = misses / total * 100 if total > 0 else 0
  print(f"\nSummary: {misses}/{total} deadline misses ({miss_rate:.2f}%)")
  
  sock.close()
  ```

* **Deadline calculation**:
  ```
  Deadline = Period × Factor
  
  Examples:
  - Period = 100ms, Factor = 1.0 → Deadline = 100ms (strict)
  - Period = 100ms, Factor = 1.5 → Deadline = 150ms (relaxed)
  - Period = 100ms, Factor = 2.0 → Deadline = 200ms (very relaxed)
  ```

* **Packet loss detection**:
  ```python
  # After receiving all packets
  expected_seqs = set(range(NUM_PACKETS))
  received_seqs = set(r['seq'] for r in results)
  lost_seqs = expected_seqs - received_seqs
  packet_loss_rate = len(lost_seqs) / NUM_PACKETS * 100
  print(f"Packet loss: {len(lost_seqs)}/{NUM_PACKETS} ({packet_loss_rate:.2f}%)")
  ```

**Bằng chứng bắt buộc:**

* Code: `udp_receiver.py` với deadline detection + packet loss
* Command: `python3 udp_receiver.py --deadline-factor 1.5`
* Screenshot: Terminal output showing 10 packets received với deadline status

---

## **Part 4 — Experiments & Analysis**

**Mục tiêu:** Chạy experiments với different periods và analyze results.

**Sinh viên cần làm và nộp:**

* **Experiment matrix**:
  | Scenario | Period (ms) | Deadline Factor | Duration | Expected Miss Rate |
  |----------|-------------|-----------------|----------|-------------------|
  | Fast | 50 | 1.5 | 1 min | <1% |
  | Moderate | 100 | 1.5 | 1 min | <2% |
  | Slow | 500 | 1.5 | 1 min | <5% |
  | Strict | 100 | 1.0 | 1 min | 5-10% |

* **Run setup**:
  1. Terminal 1: `python3 udp_receiver.py --deadline-factor 1.5 > recv_moderate.log`
  2. Terminal 2: `python3 udp_sender.py --period 0.1 --count 600`
  3. Ctrl+C receiver sau 1 phút

* **Results** (example):
  | Scenario | Period | Deadline | Packets | Misses | Miss Rate | Packet Loss | Avg Latency | Jitter |
  |----------|--------|----------|---------|--------|-----------|-------------|-------------|--------|
  | Fast | 50ms | 75ms | 1200 | 8 | 0.67% | 0% | 1.2ms | 0.5ms |
  | Moderate | 100ms | 150ms | 600 | 10 | 1.67% | 1% | 2.1ms | 1.1ms |
  | Slow | 500ms | 750ms | 120 | 4 | 3.33% | 0% | 5.5ms | 2.3ms |
  | Strict | 100ms | 100ms | 600 | 58 | 9.67% | 1% | 2.1ms | 1.1ms |

* **Visualization 1: Latency over time**
  - X-axis = packet seq, Y-axis = latency (ms)
  - Horizontal line = deadline
  - Red points = misses, green = OK
  - **Observation**: Latency spikes occasionally → deadline misses

* **Visualization 2: CDF of latency**
  - X-axis = latency (ms), Y-axis = cumulative probability
  - 4 curves: Fast, Moderate, Slow, Strict
  - **Observation**: Most packets < 5ms, but tail extends to 20-50ms

* **Analysis**:
  - **Why deadline misses?**
    * OS scheduler delays (CPU busy)
    * Network stack queueing (send buffer full)
    * Python GIL (Global Interpreter Lock) contention
  
  - **Why fast period has lower miss rate?**
    * Smaller period → smaller deadline window → more misses expected
    * But in practice: Fast period triggers more frequent context switches → more consistent timing
  
  - **Packet loss cause**:
    * UDP socket receive buffer overflow (receiver slow to process)
    * No retransmission mechanism
    * Network congestion (rare in localhost)
  
  - **Comparison với TCP**:
    * TCP would have 0% packet loss (retransmit)
    * But TCP latency higher (50-100ms due to ACK, retransmit)
    * For real-time: UDP better (tolerate 1-2% loss)

* **Jitter analysis**:
  ```python
  inter_arrivals = [results[i+1]['t_recv'] - results[i]['t_recv'] 
                    for i in range(len(results)-1)]
  jitter = np.std(inter_arrivals) * 1000  # ms
  print(f"Jitter: {jitter:.2f}ms")
  ```

**Bằng chứng bắt buộc:**

* Results table (4 scenarios: miss rate, packet loss, avg latency, jitter)
* 2 plots: Latency over time, CDF
* 10-15 dòng phân tích: Why misses, packet loss cause, UDP vs TCP

---

## **What to turn in**

### 1. **PDF Report** (tên file: `LabB_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo dài **3-4 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Theory** [20 points]
  - UDP protocol (4 characteristics)
  - Periodic streaming model (sender/receiver)
  - Metrics: Jitter, deadline miss rate, packet loss
  - Comparison: UDP vs TCP (table)

* **c. Implementation** [25 points]
  - Sender code snippet (timing compensation)
  - Receiver code snippet (deadline detection + packet loss)
  - Packet format (JSON example)

* **d. Experiments** [30 points]
  - **Table 1**: 4 scenarios (period, miss rate, packet loss, jitter)
  - **Figure 1**: Latency over time (1 scenario)
  - **Figure 2**: CDF of latency (4 scenarios)
  - Description (3-5 dòng)

* **e. Analysis** [25 points]
  - Why deadline misses (OS scheduler, network stack)
  - Packet loss cause (buffer overflow)
  - Comparison UDP vs TCP (0% loss but higher latency)
  - Jitter analysis (stddev of inter-arrivals)

### 2. **Code & Data Package**

**Bắt buộc có:**

* `udp_sender.py`: Periodic sender
* `udp_receiver.py`: Receiver với deadline detection
* `README.md`: How to run (2 terminals)
* `logs/`: 4 log files (fast, moderate, slow, strict)
* `plots/`: 2 figures (latency over time, CDF)

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 20 | UDP protocol, streaming model, metrics, comparison |
| **Implementation** | 25 | Sender + receiver code, timing compensation |
| **Experiments** | 30 | Table (4 scenarios) + 2 plots |
| **Analysis** | 25 | Root cause, UDP vs TCP, jitter |
| **Total** | **100** | |

**Bonus** (up to +5):
* Adaptive deadline (adjust based on history): +3
* Multi-threaded receiver (parallel processing): +2

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Timing compensation**: Adjust sleep để compensate drift
* **Large buffer**: `sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)`
* **JSON validation**: Try/except cho `json.loads()`

### ❌ Don'ts:
* **Không bind receiver**: `sock.bind()` required for receiver
* **Wrong deadline formula**: Deadline = Period × Factor (not + Factor)
* **Ignore packet loss**: Check lost sequence numbers

### 🔧 Debugging:
* **100% packet loss**: Check PORT match between sender/receiver
* **High latency**: Run sender & receiver trên cùng machine (localhost)
* **Clock sync**: Dùng `time.time()` consistently (not `time.monotonic()`)

---

## **References**

1. Postel, J. (1980). *User Datagram Protocol* (RFC 768). IETF.

2. Jacobson, V., & Karels, M. J. (1988). *Congestion Avoidance and Control*. ACM SIGCOMM.

3. Kurose, J. F., & Ross, K. W. (2017). *Computer Networking: A Top-Down Approach* (7th ed.). Pearson. Chapter 3.3: UDP.

4. Schulzrinne, H., Casner, S., Frederick, R., & Jacobson, V. (2003). *RTP: A Transport Protocol for Real-Time Applications* (RFC 3550). IETF.

---

**Good luck!** 📡
