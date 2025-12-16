# GUIDELINE VIẾT BÁO CÁO CHO LAB03 - Real-Time Communication

## Tổng quan
LAB03 có 3 mini-labs về real-time communication. File này hướng dẫn cách viết báo cáo cho **từng mini-lab riêng lẻ**, với cấu trúc ngắn gọn nhưng đầy đủ (mỗi báo cáo 2-4 trang).

---

## 📝 Cấu trúc báo cáo chung

Mỗi mini-lab ngắn hơn LAB01/02, nên báo cáo **2-4 trang**:

1. **Mục tiêu & Phương pháp (Objective & Setup)** - 0.5 trang
2. **Kết quả (Results)** - 1 trang (có bảng + đồ thị)
3. **Phân tích (Analysis)** - 0.5-1 trang
4. **Kết luận (Conclusion)** - 0.5 trang

---

## 📊 Template báo cáo từng mini-lab

### Mini-Lab A: Ping Latency & Jitter Analysis (45 phút)

#### Report Template
```markdown
# Mini-Lab A Report: Network Latency & Jitter Measurement

## 1. Objective & Methodology
### 1.1 Objective
Đo latency và jitter của mạng LAN trong hai trạng thái:
- **Idle**: Không có traffic nền
- **Busy**: Có iperf3 UDP flood

### 1.2 Setup
- **Máy A** (Sender): IP 192.168.1.10
- **Máy B** (Receiver): IP 192.168.1.20
- **Network**: 1 Gbps Ethernet switch
- **Tools**: `ping`, `iperf3`, Python script

### 1.3 Commands
```bash
# Idle test
ping -i 0.01 -c 500 192.168.1.20 > ping_idle.log

# Busy test
# Terminal 1 (on Machine B): iperf3 -s
# Terminal 2 (on Machine C): iperf3 -c 192.168.1.20 -u -b 500M -t 60
# Terminal 3 (on Machine A): ping -i 0.01 -c 500 192.168.1.20 > ping_busy.log

# Analysis
python3 labA/ping_analyzer.py ping_idle.log ping_busy.log
```

### 1.4 Metrics
- **Latency**: Round-trip time (RTT)
- **Jitter**: Standard deviation của latency
- **Min/Avg/Max**: Distribution summary

## 2. Results
### 2.1 Latency Statistics

| Trạng thái | Avg (ms) | Min (ms) | Max (ms) | Jitter (stddev ms) | Samples |
|------------|----------|----------|----------|---------------------|---------|
| Idle       | 0.52     | 0.38     | 2.1      | 0.18                | 500     |
| Busy       | 3.85     | 0.45     | 28.7     | 4.23                | 500     |
| **Change** | **+640%**| +18%     | **+1267%**| **+2250%**         | -       |

**Key observations**:
- Avg latency tăng 7.4x khi có background traffic
- Max latency tăng 14x (0.52ms → 28.7ms)
- Jitter tăng 23x → mạng không predictable

### 2.2 Visualization
[Chèn histogram]
**Figure 1**: Distribution của ping latency. Idle (xanh) tập trung 0.3-0.8ms, Busy (đỏ) spread rộng 0.5-30ms.

[Chèn time-series]
**Figure 2**: Latency theo thời gian. Busy có spikes lên >25ms mỗi vài giây.

### 2.3 Packet Loss
| Trạng thái | Packets sent | Packets received | Loss rate |
|------------|--------------|------------------|-----------|
| Idle       | 500          | 500              | 0%        |
| Busy       | 500          | 487              | 2.6%      |

**Observation**: Background traffic gây 2.6% packet loss.

## 3. Analysis
### 3.1 Why Jitter Increases?
**Idle network**:
- Ping packets: Best-effort, but no contention
- Consistent path through switch
- Jitter ~0.18ms (mostly từ OS scheduler)

**Busy network**:
- iperf UDP flood: 500 Mbps = ~60k packets/sec
- Switch buffer queue build-up
- Ping packets chờ trong queue → variable delay
- **Queueing delay** là main source của jitter

**Theory**:
```
Total latency = Propagation + Transmission + Queueing + Processing
                (constant)     (constant)     (VARIABLE)   (constant)
```
Queueing delay phụ thuộc buffer occupancy → jitter.

### 3.2 Why Max Latency 28.7ms?
**Calculation**:
- Switch buffer: ~10 MB (typical)
- Line rate: 1 Gbps = 125 MB/s
- Max queueing: 10 MB / 125 MB/s = 80ms

**Measured**: 28.7ms << 80ms
- Lý do: Switch có QoS (weighted fair queuing)
- Ping packets (ICMP) không bị drop hoàn toàn

### 3.3 Implications for Real-Time
**"Fast network" ≠ "Real-time network"**:
- 1 Gbps bandwidth, nhưng jitter 4.2ms
- Max latency 28.7ms → không dùng cho control loop <10ms

**Solutions**:
1. **QoS/Priority**: Mark control traffic (DSCP, 802.1p)
2. **Dedicated VLAN**: Isolate real-time traffic
3. **TSN (Time-Sensitive Networking)**: IEEE 802.1 standards
4. **Rate limiting**: Cap background traffic

## 4. Conclusion
### 4.1 Findings
1. Idle LAN: 0.52ms latency, 0.18ms jitter → acceptable cho RT
2. Busy LAN: 3.85ms latency, 4.23ms jitter → **không phù hợp**
3. Max latency tăng 14x (2.1ms → 28.7ms)
4. Background traffic gây 2.6% packet loss

### 4.2 Recommendations
- **Không** dùng best-effort network cho real-time
- Enable QoS trên switch/router
- Monitor jitter continuously trong production
- Dedicated VLAN cho control traffic

### 4.3 Limitations
- Test trên LAN only (no WAN/internet)
- Single iperf stream (real workload phức tạp hơn)
- Không test với TCP congestion control
```

---

### Mini-Lab B: UDP Periodic Stream & Deadline Miss (90 phút)

#### Report Template
```markdown
# Mini-Lab B Report: End-to-End Deadline Monitoring

## 1. Objective & Methodology
### 1.1 Objective
Triển khai UDP stream chu kỳ với deadline detection:
- Period: 10ms (100 Hz)
- Deadline: 15ms
- Đo deadline miss rate với/không background load

### 1.2 Setup
- **Sender (S)**: IP 192.168.1.10
- **Receiver (R)**: IP 192.168.1.20
- **Protocol**: UDP (no reliability, low overhead)
- **Payload**: 128 bytes (seq number + timestamp)

### 1.3 Implementation
```python
# udp_sender.py (simplified)
PERIOD_MS = 10
DEADLINE_MS = 15

while running:
    t_send = time.time()
    payload = struct.pack('!Qd', seq, t_send)
    sock.sendto(payload, (DEST_IP, DEST_PORT))
    seq += 1
    time.sleep(PERIOD_MS / 1000)

# udp_receiver.py
while running:
    data, addr = sock.recvfrom(1024)
    t_recv = time.time()
    seq, t_send = struct.unpack('!Qd', data)
    delay_ms = (t_recv - t_send) * 1000
    deadline_met = 1 if delay_ms < DEADLINE_MS else 0
    log_csv(seq, t_send, t_recv, delay_ms, deadline_met)
```

### 1.4 Scenarios
| Scenario | Background Load | Duration | Packets Expected |
|----------|-----------------|----------|------------------|
| Baseline | None            | 60s      | 6000             |
| Stressed | iperf3 -u 50M   | 60s      | 6000             |

## 2. Results
### 2.1 Baseline (No Background Load)

| Metric | Value |
|--------|-------|
| Total packets sent | 6000 |
| Total packets received | 5998 |
| Packet loss | 2 (0.03%) |
| Deadline met | 5996 |
| Deadline miss | 2 (0.03%) |
| **Miss rate** | **0.03%** |

**Delay statistics**:
| Metric | Value (ms) |
|--------|------------|
| Average | 3.2 |
| p95 | 6.8 |
| p99 | 8.5 |
| Max | 14.8 |
| Jitter (stddev) | 2.1 |

**Observation**: 
- 2 misses (max=14.8ms < 15ms deadline)
- Likely do OS scheduler preemption

### 2.2 Stressed (With iperf3 50 Mbps UDP)

| Metric | Value |
|--------|-------|
| Total packets sent | 6000 |
| Total packets received | 5932 |
| Packet loss | 68 (1.13%) |
| Deadline met | 5435 |
| Deadline miss | 497 (8.38%) |
| **Miss rate** | **8.38%** |

**Delay statistics**:
| Metric | Value (ms) |
|--------|------------|
| Average | 12.5 |
| p95 | 28.7 |
| p99 | 45.2 |
| Max | 78.3 |
| Jitter (stddev) | 8.9 |

**Observation**:
- Miss rate tăng 280x (0.03% → 8.38%)
- Max delay 78.3ms >> 15ms deadline
- Packet loss tăng 38x (0.03% → 1.13%)

### 2.3 Comparison Table

| Scenario | Miss Rate | Avg Delay | p99 Delay | Max Delay | Packet Loss |
|----------|-----------|-----------|-----------|-----------|-------------|
| Baseline | 0.03%     | 3.2ms     | 8.5ms     | 14.8ms    | 0.03%       |
| Stressed | 8.38%     | 12.5ms    | 45.2ms    | 78.3ms    | 1.13%       |
| **Δ**    | **+280x** | **+3.9x** | **+5.3x** | **+5.3x** | **+38x**    |

### 2.4 Visualization
[Chèn time-series: Delay theo thời gian]
**Figure 1**: Delay over time. Baseline (xanh) ổn định <10ms. Stressed (đỏ) có spikes lên >40ms.

[Chèn CDF]
**Figure 2**: CDF của delay. Stressed có long tail (5% packets >28ms).

## 3. Analysis
### 3.1 Why 8.38% Miss Rate?
**Root causes**:
1. **Network congestion**: 50 Mbps background → switch queue buildup
2. **Packet loss**: 1.13% → retransmit không có (UDP) → gap trong sequence
3. **OS buffering**: Receiver side `recvfrom()` block khi queue đầy

**Calculation**:
- Send rate: 100 packets/s × 128 bytes = 12.8 KB/s = 0.1 Mbps
- Background: 50 Mbps
- **Control traffic chỉ chiếm 0.2% bandwidth**, nhưng vẫn bị ảnh hưởng!

**Conclusion**: Best-effort UDP không đảm bảo deadline, dù bandwidth đủ.

### 3.2 Deadline Miss Distribution
Phân tích 497 misses:
- 40% xảy ra khi delay 15-20ms (slightly miss)
- 35% xảy ra khi delay 20-30ms
- 25% xảy ra khi delay >30ms (severe miss)

**Implication**: 
- Nhiều misses "nhẹ" (15-20ms) → increase deadline margin?
- Một số misses "nặng" (>50ms) → packet loss hoặc queue overflow

### 3.3 Mitigation Strategies
| Strategy | Expected Improvement | Complexity |
|----------|----------------------|------------|
| QoS marking (DSCP EF) | 80% reduction | Low |
| Dedicated VLAN | 90% reduction | Medium |
| TCP/SCTP with RT extensions | Variable | High |
| Increase deadline (15ms→30ms) | Mask problem, not fix | N/A |

**Recommendation**: Implement QoS marking (DSCP EF = 0xB8) cho control packets.

```python
# Sender side
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
```

### 3.4 End-to-End Latency Breakdown
**Measured components** (baseline):
- Sender timestamp: T1 = 0
- Network transmission: ~0.5ms
- Receiver recv: T2 = T1 + 3.2ms
- **Total**: 3.2ms

**Missing components** (not measured in this lab):
- Sensor acquisition: +5ms
- Preprocessing: +2ms
- Dashboard display: +10ms
- **True end-to-end**: ~20ms

**Learning**: "Network latency" chỉ là 1 phần của end-to-end!

## 4. Conclusion
### 4.1 Findings
1. UDP periodic baseline: 0.03% miss, avg 3.2ms delay
2. With 50 Mbps background: 8.38% miss, avg 12.5ms delay
3. Miss rate tăng 280x dù control traffic chỉ 0.2% bandwidth
4. Best-effort UDP không suitable cho hard real-time

### 4.2 Recommendations
- **Must**: Enable QoS/priority for control traffic
- **Should**: Monitor miss rate continuously
- **Consider**: Redundant paths (primary + backup)
- **Avoid**: Sharing network với high-volume traffic

### 4.3 If Hard RT Required (<10ms, <0.1% miss)
- Use TSN (Time-Sensitive Networking)
- Dedicated physical network
- Consider CAN bus (automotive) or EtherCAT (industrial)
```

---

### Mini-Lab C: CAN Bus Response Time Calculation

#### Report Template (ngắn gọn)
```markdown
# Mini-Lab C Report: CAN Bus Priority Scheduling

## 1. Objective
Tính worst-case response time (WCRT) cho messages trên CAN bus với priority scheduling.

## 2. Theory
### 2.1 CAN Bus
- **Priority**: Lower ID = Higher priority
- **Arbitration**: Non-destructive bitwise
- **Frame**: ~130 bits overhead + 8 bytes data = ~194 bits total

### 2.2 WCRT Formula (simplified)
```
R_i = C_i + B_i + I_i

Với:
- C_i: Transmission time của message i
- B_i: Blocking time (từ lower-priority message)
- I_i: Interference (từ higher-priority messages)
```

## 3. Setup
### 3.1 Message Set
| Message | ID | Priority | Data Bytes | Period (ms) | Deadline (ms) |
|---------|----|----|------------|-------------|---------------|
| M1      | 100| 1 (highest) | 8 | 10 | 10 |
| M2      | 200| 2 | 8 | 20 | 20 |
| M3      | 300| 3 (lowest) | 8 | 50 | 50 |

### 3.2 CAN Parameters
- **Bitrate**: 500 kbps
- **Transmission time**: 194 bits / 500 kbps = 0.388ms per message

## 4. Results
### 4.1 WCRT Calculation

**Message M1 (highest priority)**:
- C_1 = 0.388ms
- B_1 = 0.388ms (worst case: M2 or M3 just started)
- I_1 = 0 (no higher priority)
- **R_1 = 0.776ms**

**Message M2**:
- C_2 = 0.388ms
- B_2 = 0.388ms (M3 just started)
- I_2 = 1 × 0.388ms (M1 can preempt once)
- **R_2 = 1.164ms**

**Message M3**:
- C_3 = 0.388ms
- B_3 = 0 (lowest priority, no blocking)
- I_3 = ?

**Iterative calculation** (considering period):
```
R_3^0 = C_3 = 0.388ms
R_3^1 = C_3 + ceil(R_3^0 / T_1) × C_1 + ceil(R_3^0 / T_2) × C_2
      = 0.388 + 1×0.388 + 1×0.388 = 1.164ms
R_3^2 = 0.388 + ceil(1.164/10)×0.388 + ceil(1.164/20)×0.388
      = 0.388 + 1×0.388 + 1×0.388 = 1.164ms
```
**R_3 = 1.164ms** (converged)

### 4.2 Schedulability Check

| Message | WCRT (ms) | Deadline (ms) | Schedulable? |
|---------|-----------|---------------|--------------|
| M1      | 0.776     | 10            | ✅ Yes       |
| M2      | 1.164     | 20            | ✅ Yes       |
| M3      | 1.164     | 50            | ✅ Yes       |

**Conclusion**: All messages schedulable (WCRT < Deadline).

### 4.3 Utilization
```
U = Σ(C_i / T_i)
  = 0.388/10 + 0.388/20 + 0.388/50
  = 0.0388 + 0.0194 + 0.0078
  = 0.066 (6.6%)
```

**Very low utilization** → comfortable margin.

## 5. Analysis
### 5.1 Impact of Priority
**If M3 had higher priority than M1**:
- M1 would be blocked by M3
- R_1 could increase to ~1.5ms
- Still <10ms deadline, but less margin

**Priority assignment matters**:
- Rate Monotonic (RM): Shortest period = highest priority
- Deadline Monotonic (DM): Earliest deadline = highest priority

### 5.2 Worst-Case Scenario
**When does M3 experience WCRT?**
1. M3 ready to send
2. M1 just started → M3 blocked 0.388ms
3. During M3 transmission:
   - M1 arrives → arbitration lost → restart after M1 done
   - M2 arrives → same
4. Total: 1.164ms

[Chèn timeline diagram]
**Figure 1**: Worst-case timeline cho M3. Shows blocking + preemptions.

## 6. Conclusion
### 6.1 Findings
1. CAN priority scheduling works well (6.6% utilization)
2. WCRT: M1=0.776ms, M2=1.164ms, M3=1.164ms
3. All deadlines met with large margin

### 6.2 If Adding High-Frequency Message
**Scenario**: Add M0 (ID=50, Period=5ms)
- M0 would preempt M1, M2, M3
- R_1 increases: 0.776ms → ~1.5ms
- R_2, R_3 increase similarly
- Utilization: 6.6% → 14.4%

**Still schedulable**, but margin reduces.

### 6.3 Limitations
- Simplified model (no bit stuffing, error frames)
- Assumes fixed message size (8 bytes)
- No sporadic messages considered
```

---

## ✅ Checklist chung cho báo cáo LAB03

### Mini-Lab A (Ping):
- [ ] Setup rõ ràng (IP addresses, tools)
- [ ] Bảng latency stats (idle vs busy)
- [ ] Đồ thị: histogram hoặc time-series
- [ ] Phân tích why jitter tăng
- [ ] Implications cho real-time

### Mini-Lab B (UDP):
- [ ] Implementation snippet (sender/receiver)
- [ ] Bảng: deadline miss rate baseline vs stressed
- [ ] CDF hoặc time-series của delay
- [ ] Root cause analysis
- [ ] Mitigation strategies (QoS, VLAN)

### Mini-Lab C (CAN):
- [ ] Message set table
- [ ] WCRT calculation (show steps)
- [ ] Schedulability check
- [ ] Timeline diagram (recommend)
- [ ] Utilization analysis

---

## 📏 Metrics cần có

### Lab A:
- Latency: avg, min, max, jitter (stddev)
- Packet loss rate
- Sample count

### Lab B:
- Deadline miss rate (%)
- Delay: avg, p95, p99, max
- Packet loss rate
- Jitter

### Lab C:
- WCRT per message
- Blocking time, Interference time
- Utilization (%)
- Schedulability (Yes/No)

**Good luck với báo cáo LAB03! 🌐**

**Các bài lab liên quan:**
- **Lab A (ping analyzer)**: Đo latency & jitter cơ bản
- **Lab B (UDP periodic stream)**: End-to-end deadline miss detection
- **Lab C (CAN RT calc)**: Priority-based bus scheduling

**Yêu cầu cần đáp ứng:**

1. **Thiết kế luồng message:**
   - **Từ Lab B**: UDP sender/receiver với period 10ms
   - Thông số cần nêu:
     * Kích thước message (bytes)
     * Tần suất gửi (Hz hoặc period ms)
     * Deadline (ms)
     * Quan hệ producer/consumer (1-to-1, 1-to-many, pub/sub)
   - **Ví dụ**: Sensor gửi 128 bytes mỗi 10ms, deadline 15ms, đến Dashboard

2. **Cơ chế giảm trễ/jitter:**
   - **Queue discipline:**
     * Lab B: UDP buffer vs TCP congestion control
     * FIFO vs Priority Queue
   - **Priority traffic:**
     * Lab C: CAN bus priority scheduling
     * VLAN priority tagging (802.1p)
   - **Batching vs immediate send:**
     * Trade-off: Latency vs bandwidth efficiency
   - **Retry policy:**
     * Timeout, max retries
     * Lab B: Không retry → datagram loss tracking

3. **Phân tích end-to-end:**
   - **Các thành phần tạo trễ:**
     * Queueing delay: Chờ trong buffer
     * Processing delay: CPU encode/decode
     * Transmission delay: Kích thước / bandwidth
     * Propagation delay: Distance / speed of light
     * I/O wait: Disk write, DB insert
   - **Lab A & B**: Đo từng thành phần với timestamp

**Bằng chứng bắt buộc:**

✅ **Đo latency/jitter theo thời gian:**
```
File: delay_log.csv từ Lab B
Columns: seq, send_time, recv_time, delay_ms, deadline_met

Summary:
- Avg delay: 3.2ms
- p99 delay: 8.5ms
- Max delay: 14.8ms
- Jitter (stddev): 2.1ms
- Deadline miss: 12/10000 (0.12%)
```

✅ **Timestamping points:**
```
Producer side:
  T1: Task ready to send
  T2: Socket send() return

Consumer side:
  T3: Socket recv() return
  T4: Processing complete

End-to-end latency = T4 - T1
Network latency = T3 - T2
Processing latency = T4 - T3
```

✅ **Thí nghiệm "xấu" (stress case):**
```
Scenario: Background iperf3 UDP flood 50Mbps

Results:
- Avg delay: 3.2ms → 12.5ms (tăng 4x)
- p99 delay: 8.5ms → 45ms
- Deadline miss: 0.12% → 8.3%

Cách chịu đựng:
- QoS marking (DSCP) cho control traffic
- Rate limiting background traffic
- Dedicated VLAN cho real-time stream
```

---

## 📝 Checklist cho báo cáo

### Section: Part 3 — Real-time Communication (15 điểm)

- [ ] **Thiết kế luồng message:**
  - [ ] Kích thước message (bytes)
  - [ ] Tần suất/period (ms hoặc Hz)
  - [ ] Deadline (ms)
  - [ ] Producer/consumer topology (diagram)
  - [ ] Protocol: UDP vs TCP vs custom

- [ ] **Cơ chế giảm trễ/jitter:**
  - [ ] Queue discipline (FIFO, Priority, RED)
  - [ ] Priority traffic (QoS, VLAN tag, CAN priority)
  - [ ] Batching policy (nếu có)
  - [ ] Retry/timeout policy
  - [ ] Code snippet hoặc config

- [ ] **Phân tích end-to-end:**
  - [ ] Diagram: timeline từ producer → network → consumer
  - [ ] Breakdown: queueing, processing, transmission, propagation
  - [ ] Timestamp ở mỗi stage (T1, T2, T3, T4)
  - [ ] Phần trăm: Network_time / Total_time

- [ ] **Đo latency/jitter:**
  - [ ] Time-series plot: latency theo thời gian
  - [ ] CDF hoặc histogram
  - [ ] Bảng: Avg, p95, p99, max, stddev (jitter)

- [ ] **Stress case:**
  - [ ] Mô tả scenario: iperf, packet loss, congestion
  - [ ] KPI trước/sau stress
  - [ ] Deadline miss rate tăng bao nhiêu
  - [ ] Cách hệ thống chịu đựng (QoS, retry, fallback)

- [ ] **End-to-end view:**
  - [ ] Không chỉ đo network → phải bao gồm task latency
  - [ ] Ví dụ: Sensor → Encode → Send → Receive → Decode → Process → DB
  - [ ] Total latency = sum of all stages

---

## 🔬 Thí nghiệm gợi ý

### Experiment 1: Ping Latency Baseline (Lab A)
```
Mục tiêu: Đo latency/jitter mạng idle vs busy

Setup:
- 2 máy A, B cùng LAN
- Idle: ping -i 0.01 -c 500
- Busy: iperf3 -c <IP> -t 60 (background) + ping

Kỳ vọng:
- Idle: avg ~1ms, jitter ~0.2ms
- Busy: avg ~5ms, jitter ~2ms, max >20ms

Code:
python3 labA/ping_analyzer.py ping_idle.log ping_busy.log
```

### Experiment 2: UDP Periodic with Deadline (Lab B)
```
Mục tiêu: Đo end-to-end delay và deadline miss rate

Setup:
- Sender: python3 udp_sender.py (period=10ms, deadline=15ms)
- Receiver: python3 udp_receiver.py
- Run 10000 packets

Kỳ vọng:
- No stress: miss rate <0.1%
- With iperf: miss rate >5%

Code:
python3 labB/delay_summary.py delay_log.csv
```

### Experiment 3: Priority Traffic (Extend Lab B)
```
Mục tiêu: Chứng minh QoS giảm jitter

Setup:
- Mark control traffic với DSCP EF (Expedited Forwarding)
- Background traffic: best-effort
- Router/switch hỗ trợ QoS

Kỳ vọng:
- Với QoS: jitter ổn định dù background load cao
- Không QoS: jitter tăng tuyến tính với load

Code:
# Sender side
sudo setsockopt(sock, IPPROTO_IP, IP_TOS, DSCP_EF)
```

### Experiment 4: CAN Bus Scheduling (Lab C)
```
Mục tiêu: Tính worst-case response time trên bus ưu tiên

Setup:
- 3 message: High (ID=100), Med (ID=200), Low (ID=300)
- CAN bitrate: 500kbps
- Message size: 8 bytes data

Kỳ vọng:
- High priority: response time ≈ transmission time
- Low priority: bị preempt bởi High/Med

Code:
python3 labC/can_rt_calc.py --bitrate 500000
```

---

## 🛠 Script & Tools

### Script phân tích ping log (Lab A)
```python
# ping_analyzer.py
import re
import sys
import numpy as np

def parse_ping_log(filename):
    latencies = []
    with open(filename) as f:
        for line in f:
            match = re.search(r'time=([\d.]+) ms', line)
            if match:
                latencies.append(float(match.group(1)))
    return latencies

def analyze(latencies):
    return {
        'avg': np.mean(latencies),
        'min': np.min(latencies),
        'max': np.max(latencies),
        'jitter': np.std(latencies),
        'p95': np.percentile(latencies, 95),
        'p99': np.percentile(latencies, 99)
    }

# Usage
idle = analyze(parse_ping_log('ping_idle.log'))
busy = analyze(parse_ping_log('ping_busy.log'))

print(f"Idle - Avg: {idle['avg']:.2f}ms, Jitter: {idle['jitter']:.2f}ms")
print(f"Busy - Avg: {busy['avg']:.2f}ms, Jitter: {busy['jitter']:.2f}ms")
```

### Script UDP sender/receiver với timestamp (Lab B)
```python
# udp_sender.py (simplified)
import socket
import time
import struct

DEST_IP = "192.168.1.100"
DEST_PORT = 5000
PERIOD = 0.01  # 10ms
DEADLINE = 0.015  # 15ms

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
seq = 0

while True:
    t_send = time.time()
    payload = struct.pack('!Qd', seq, t_send)
    sock.sendto(payload, (DEST_IP, DEST_PORT))
    seq += 1
    time.sleep(PERIOD)

# udp_receiver.py (simplified)
import socket
import time
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5000))

with open('delay_log.csv', 'w') as f:
    f.write("seq,send_time,recv_time,delay_ms,deadline_met\n")
    while True:
        data, addr = sock.recvfrom(1024)
        t_recv = time.time()
        seq, t_send = struct.unpack('!Qd', data)
        delay = (t_recv - t_send) * 1000
        deadline_met = 1 if delay < DEADLINE*1000 else 0
        f.write(f"{seq},{t_send},{t_recv},{delay:.3f},{deadline_met}\n")
        f.flush()
```

### Script tính CAN response time (Lab C)
```python
# can_rt_calc.py
def calc_can_transmission_time(data_bytes, bitrate=500000):
    """CAN 2.0B frame overhead: ~130 bits for 8 bytes data"""
    bits = 130 + data_bytes * 8
    return bits / bitrate * 1000  # ms

def worst_case_response_time(msg, higher_priority_msgs):
    """Simplified WCRT for fixed-priority CAN"""
    C_i = msg['transmission_time']
    blocking = max([m['transmission_time'] for m in higher_priority_msgs] + [0])
    interference = sum([m['transmission_time'] for m in higher_priority_msgs])
    
    return C_i + blocking + interference

# Example
messages = [
    {'id': 100, 'priority': 1, 'data_bytes': 8, 'period': 10},
    {'id': 200, 'priority': 2, 'data_bytes': 8, 'period': 20},
    {'id': 300, 'priority': 3, 'data_bytes': 8, 'period': 50}
]

for msg in messages:
    msg['transmission_time'] = calc_can_transmission_time(msg['data_bytes'])
    higher = [m for m in messages if m['priority'] < msg['priority']]
    wcrt = worst_case_response_time(msg, higher)
    print(f"Msg ID={msg['id']}: WCRT={wcrt:.3f}ms")
```

### One-liner chạy toàn bộ Lab 3
```bash
#!/bin/bash
# run_all_lab3.sh

# Lab A: Ping analysis
ping -i 0.01 -c 500 192.168.1.100 > ping_idle.log
# (Start iperf in background)
ping -i 0.01 -c 500 192.168.1.100 > ping_busy.log
python3 labA/ping_analyzer.py ping_idle.log ping_busy.log

# Lab B: UDP periodic (run receiver on other machine first)
python3 labB/udp_sender.py &
sleep 10
pkill -f udp_sender
python3 labB/delay_summary.py delay_log.csv

# Lab C: CAN calculation
python3 labC/can_rt_calc.py --bitrate 500000 > can_wcrt.txt
```

---

## 📊 Visualizations cần có

1. **Latency Time-Series:**
   - X: Time (seconds), Y: Latency (ms)
   - Horizontal line: Deadline
   - Đánh dấu miss points màu đỏ

2. **CDF Latency:**
   - X: Latency (ms), Y: Cumulative probability
   - Compare: Idle vs Busy, No-QoS vs QoS

3. **Jitter Histogram:**
   - X: Jitter (ms), Y: Frequency
   - Before/After stress test

4. **End-to-End Breakdown:**
   - Stacked bar: Producer → Network → Consumer → Processing
   - Percentage của mỗi stage

5. **Deadline Miss Rate:**
   - Bar chart: Different scenarios
   - X: Scenario, Y: Miss rate (%)

6. **Priority Comparison (CAN):**
   - Bar chart: Message ID vs WCRT
   - Show blocking time từ lower priority

---

## 💡 Key Insights từ LAB03

### Lab A: Ping Analysis
```
Key findings:
- Idle LAN: latency ~0.5-2ms, jitter <1ms
- With iperf: latency tăng 5-10x, jitter >5ms
- Max latency có thể >100ms khi packet loss
- Jitter = stddev of latency → measure của unpredictability
```

### Lab B: UDP Periodic Stream
```
Key findings:
- UDP không đảm bảo delivery → cần application-level deadline detection
- Deadline miss tương quan với network congestion
- Period 10ms, deadline 15ms → 50% margin
- Timestamp ở sender/receiver → đo end-to-end accurate
```

### Lab C: CAN Bus Priority
```
Key findings:
- Lower ID = Higher priority trong CAN
- WCRT = transmission + blocking + interference
- High priority message: WCRT ≈ transmission time
- Low priority: bị preempt nhiều → WCRT tăng
- Schedulability: WCRT_i < Deadline_i
```

---

## ⚠️ Common Pitfalls

1. **Không đo end-to-end:**
   - Chỉ đo network latency → thiếu processing time
   - Solution: Timestamp ở producer start và consumer complete

2. **Clock không đồng bộ:**
   - Sender/receiver khác máy → clock skew
   - Solution: NTP sync hoặc relative timestamp

3. **UDP buffer overflow:**
   - Receiver chậm → kernel buffer đầy → packet loss
   - Solution: Tăng SO_RCVBUF hoặc faster processing

4. **Ignore queueing delay:**
   - Network idle nhưng vẫn có jitter từ OS scheduler
   - Solution: SCHED_FIFO cho sender/receiver threads

5. **Không test stress case:**
   - Chỉ test ideal condition → không real-time
   - Solution: Background iperf, packet loss emulation

---

## 🌐 Network Setup Tips

### VLAN for Real-time Traffic
```bash
# Create VLAN 100 for control traffic
sudo ip link add link eth0 name eth0.100 type vlan id 100
sudo ip addr add 192.168.100.1/24 dev eth0.100
sudo ip link set eth0.100 up

# QoS marking
sudo tc qdisc add dev eth0 root handle 1: prio
sudo tc filter add dev eth0 parent 1:0 protocol ip prio 1 u32 match ip tos 0xb8 0xff flowid 1:1
```

### UDP Socket Options
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Increase buffer size
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*1024)

# Set TOS for QoS (DSCP EF = 0xB8)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)

# Set priority (Linux)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_PRIORITY, 6)
```

### NTP Time Sync
```bash
# Install NTP
sudo apt install ntp

# Check sync status
ntpq -p

# Stratum 1 = best (GPS/atomic clock)
# Stratum 2 = sync to stratum 1
# Typical LAN: offset <1ms
```

---

## 📚 References cho báo cáo

1. Kopetz, H., & Bauer, G. (2003). *The time-triggered architecture*. Proceedings of the IEEE, 91(1), 112-126.

2. Tindell, K., & Burns, A. (1994). *Guaranteeing message latencies on controller area network (CAN)*. Proceedings of 1st ICCCN.

3. IEEE 802.1Q. (2018). *Virtual LANs and Priority Tagging*. IEEE Standards.

4. Blake, S., et al. (1998). *An Architecture for Differentiated Services*. RFC 2475.

5. Mills, D. L. (1991). *Internet time synchronization: the network time protocol*. IEEE Transactions on Communications, 39(10), 1482-1493.

---

## ✅ Final Checklist

Trước khi nộp Part 3 của project, đảm bảo:

- [ ] Thiết kế luồng message: kích thước, tần suất, deadline
- [ ] Producer/consumer topology (diagram)
- [ ] Protocol: UDP/TCP/custom, giải thích tại sao
- [ ] Cơ chế giảm trễ: queue discipline, priority, batching
- [ ] Timestamp points: nêu rõ T1, T2, T3, T4
- [ ] End-to-end breakdown: queueing, processing, transmission, propagation
- [ ] Đo latency/jitter: time-series, CDF, histogram
- [ ] Bảng KPI: avg, p95, p99, max, stddev (jitter)
- [ ] Stress case: iperf hoặc packet loss, deadline miss tăng
- [ ] Cách hệ thống chịu đựng: QoS, retry, rate limit
- [ ] Code sender/receiver trong reproducibility package
- [ ] Log file: delay_log.csv với timestamp
- [ ] Không chỉ đo network → bao gồm task/processing latency

**Điểm tối đa Part 3: 15/100**

---

## 🚀 Tips nâng cao

1. **TSN (Time-Sensitive Networking):**
   - IEEE 802.1Qbv: Time-aware shaping
   - IEEE 802.1Qbu: Frame preemption
   - Cho Ethernet deterministic

2. **PTP (Precision Time Protocol):**
   - IEEE 1588
   - Sub-microsecond clock sync
   - Dùng cho distributed systems

3. **Zero-Copy Networking:**
   - Kernel bypass (DPDK, AF_XDP)
   - Giảm latency ~50%
   - Phức tạp hơn standard socket

4. **Protocol Alternatives:**
   - DDS (Data Distribution Service): Real-time pub/sub
   - SOME/IP: Automotive Ethernet
   - OPC UA: Industrial automation

**Good luck với Real-time Communication! 🌐**
