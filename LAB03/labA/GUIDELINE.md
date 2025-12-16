**Lab A: Ping Analysis — Network Latency Measurement**  
**Tổng điểm:** 100  
**Thời gian:** 45 phút (mini-lab)

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Mini-lab này đo **network latency** sử dụng `ping` command và phân tích kết quả.

Objectives:
* Measure RTT (Round-Trip Time) đến các servers (localhost, LAN gateway, public DNS)
* Analyze min/avg/max/stddev statistics
* Detect packet loss
* Compare latency across different network hops

Deliverable:
* Ping analyzer script (Python)
* Báo cáo 2-3 trang

---

## **Part 1 — Ping & RTT Theory**

**Mục tiêu:** Hiểu ICMP Echo Request/Reply và RTT measurement.

**Sinh viên cần làm và nộp:**

* **Ping protocol**:
  - **ICMP Echo Request**: Client gửi packet đến destination
  - **ICMP Echo Reply**: Destination gửi lại
  - **RTT (Round-Trip Time)**: Time từ gửi Request đến nhận Reply
  - **Packet loss**: % packets không nhận được Reply (timeout hoặc network error)

* **RTT components**:
  ```
  RTT = T_transmission + T_propagation + T_processing + T_queue
  
  - T_transmission: Time to transmit packet (depends on bandwidth)
  - T_propagation: Time for signal to travel (speed of light, distance)
  - T_processing: Router/switch processing time
  - T_queue: Queueing delay at intermediate routers
  ```

* **Typical RTT values**:
  | Destination | Expected RTT | Note |
  |-------------|--------------|------|
  | localhost (127.0.0.1) | <0.1ms | Loopback, no network |
  | LAN gateway (192.168.x.x) | 1-5ms | Single Ethernet hop |
  | ISP DNS (8.8.8.8) | 10-50ms | Internet, multiple hops |
  | International server | 100-300ms | Cross-continent |

* **Packet loss causes**:
  - Network congestion (router queues full)
  - Firewall blocking ICMP
  - Unstable wireless connection
  - Physical cable issues

**Bằng chứng bắt buộc:**

* Ping protocol explanation (ICMP Echo Request/Reply, 2-3 dòng)
* RTT components (4 factors)
* Expected RTT table (4 destinations)

---

## **Part 2 — Ping Experiments**

**Mục tiêu:** Chạy ping command và collect data.

**Sinh viên cần làm và nộp:**

* **Ping commands**:
  ```bash
  # Localhost (loopback)
  ping -c 100 127.0.0.1 > ping_localhost.txt
  
  # LAN gateway (check your router IP)
  ping -c 100 192.168.1.1 > ping_gateway.txt
  
  # Google DNS
  ping -c 100 8.8.8.8 > ping_google.txt
  
  # CloudFlare DNS
  ping -c 100 1.1.1.1 > ping_cloudflare.txt
  ```

* **Sample output**:
  ```
  PING 8.8.8.8 (8.8.8.8): 56 data bytes
  64 bytes from 8.8.8.8: icmp_seq=0 ttl=118 time=12.5 ms
  64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=13.2 ms
  ...
  --- 8.8.8.8 ping statistics ---
  100 packets transmitted, 98 received, 2.0% packet loss, time 99045ms
  rtt min/avg/max/mdev = 11.2/12.8/15.4/0.8 ms
  ```

* **Data collection** (for each destination):
  - min RTT (ms)
  - avg RTT (ms)
  - max RTT (ms)
  - stddev (mdev) (ms)
  - packet loss (%)

* **Expected results**:
  | Destination | Min | Avg | Max | Stddev | Loss |
  |-------------|-----|-----|-----|--------|------|
  | localhost | 0.04 | 0.05 | 0.08 | 0.01 | 0% |
  | gateway | 1.2 | 2.5 | 8.3 | 1.1 | 0% |
  | 8.8.8.8 | 11.2 | 12.8 | 15.4 | 0.8 | 2% |
  | 1.1.1.1 | 10.5 | 11.9 | 14.2 | 0.7 | 1% |

**Bằng chứng bắt buộc:**

* 4 ping log files (localhost, gateway, 8.8.8.8, 1.1.1.1)
* Results table (min/avg/max/stddev/loss for 4 destinations)
* Script: `run_ping.sh` chạy tất cả 4 ping commands

---

## **Part 3 — Ping Analyzer Implementation**

**Mục tiêu:** Parse ping output và extract statistics.

**Sinh viên cần làm và nộp:**

* **Ping analyzer** (`ping_analyzer.py`):
  ```python
  import re
  import sys
  
  def parse_ping_log(filename):
      with open(filename) as f:
          content = f.read()
      
      # Extract individual RTTs
      rtts = []
      for line in content.split('\n'):
          match = re.search(r'time=([\d.]+) ms', line)
          if match:
              rtts.append(float(match.group(1)))
      
      # Extract summary statistics
      summary = re.search(r'(\d+) packets transmitted, (\d+) received, ([\d.]+)% packet loss', content)
      transmitted = int(summary.group(1))
      received = int(summary.group(2))
      packet_loss = float(summary.group(3))
      
      stats = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', content)
      min_rtt = float(stats.group(1))
      avg_rtt = float(stats.group(2))
      max_rtt = float(stats.group(3))
      mdev = float(stats.group(4))
      
      return {
          'rtts': rtts,
          'min': min_rtt,
          'avg': avg_rtt,
          'max': max_rtt,
          'stddev': mdev,
          'packet_loss': packet_loss,
          'transmitted': transmitted,
          'received': received
      }
  
  # Usage
  if __name__ == '__main__':
      filename = sys.argv[1]
      result = parse_ping_log(filename)
      print(f"Min: {result['min']}ms")
      print(f"Avg: {result['avg']}ms")
      print(f"Max: {result['max']}ms")
      print(f"Stddev: {result['stddev']}ms")
      print(f"Packet loss: {result['packet_loss']}%")
  ```

* **Command**:
  ```bash
  python3 ping_analyzer.py ping_google.txt
  ```
  Output:
  ```
  Min: 11.2ms
  Avg: 12.8ms
  Max: 15.4ms
  Stddev: 0.8ms
  Packet loss: 2.0%
  ```

**Bằng chứng bắt buộc:**

* Code: `ping_analyzer.py` với function `parse_ping_log()`
* Command: `python3 ping_analyzer.py ping_google.txt`
* Screenshot: Terminal output showing parsed statistics

---

## **Part 4 — Visualization & Analysis**

**Mục tiêu:** Visualize RTT distribution và compare destinations.

**Sinh viên cần làm và nộp:**

* **Visualization 1: CDF plot**
  - X-axis = RTT (ms), Y-axis = cumulative probability
  - 4 curves: localhost, gateway, 8.8.8.8, 1.1.1.1
  - **Observation**: localhost << gateway < public DNS

* **Visualization 2: Box plot**
  - X-axis = destination, Y-axis = RTT (ms)
  - Show min, Q1, median, Q3, max, outliers
  - **Observation**: localhost stable (small box), public DNS variable (large box)

* **Analysis**:
  - **Why localhost fastest?**
    * No physical network (loopback interface)
    * No routing, no propagation delay
    * RTT dominated by OS overhead (<0.1ms)
  
  - **Why gateway slower than localhost but faster than public DNS?**
    * Single Ethernet hop (1-2ms propagation + processing)
    * No internet routing
    * Stable LAN environment
  
  - **Why public DNS has higher variability?**
    * Multiple hops (traceroute shows 8-15 routers)
    * Queueing delay at intermediate routers
    * Internet congestion (shared links)
  
  - **Packet loss cause** (2% for 8.8.8.8):
    * ICMP de-prioritization at routers (not critical traffic)
    * Firewall dropping ICMP packets
    * Temporary network congestion

* **Comparison**:
  | Destination | Avg RTT | Coefficient of Variation (CV) | Note |
  |-------------|---------|-------------------------------|------|
  | localhost | 0.05ms | 20% (0.01/0.05) | Very stable |
  | gateway | 2.5ms | 44% (1.1/2.5) | Moderately stable |
  | 8.8.8.8 | 12.8ms | 6% (0.8/12.8) | Stable (Google infra) |
  | 1.1.1.1 | 11.9ms | 6% (0.7/11.9) | Stable (CloudFlare) |

**Bằng chứng bắt buộc:**

* 2 plots: CDF, box plot
* 10-15 dòng phân tích: Why localhost fastest, why public DNS variable, packet loss cause
* Comparison table với CV (coefficient of variation)

---

## **What to turn in**

### 1. **PDF Report** (tên file: `LabA_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo dài **2-3 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Theory** [15 points]
  - Ping protocol (ICMP Echo Request/Reply)
  - RTT components (4 factors)
  - Expected RTT values table (4 destinations)

* **c. Experiments** [25 points]
  - 4 ping commands (localhost, gateway, 8.8.8.8, 1.1.1.1)
  - Results table (min/avg/max/stddev/loss)
  - Description (2-3 dòng)

* **d. Implementation** [20 points]
  - `ping_analyzer.py` code snippet (parse function)
  - Command output (parsed statistics for 1 destination)

* **e. Visualization** [25 points]
  - **Figure 1**: CDF plot (4 destinations)
  - **Figure 2**: Box plot (4 destinations)
  - Description (3-5 dòng)

* **f. Analysis** [15 points]
  - Why localhost fastest (no network)
  - Why public DNS variable (multiple hops, queueing)
  - Packet loss cause (ICMP de-prioritization)
  - Comparison table với CV

### 2. **Code & Data Package**

**Bắt buộc có:**

* `ping_analyzer.py`: Parser script
* `run_ping.sh`: 4 ping commands
* `ping_logs/`: 4 log files (localhost, gateway, google, cloudflare)
* `plots/`: 2 figures (CDF, box plot)
* `README.md`: How to run

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 15 | Ping protocol, RTT components, expected values |
| **Experiments** | 25 | 4 ping logs, results table |
| **Implementation** | 20 | `ping_analyzer.py` với parsing logic |
| **Visualization** | 25 | 2 plots (CDF, box plot) |
| **Analysis** | 15 | Root cause explanation, CV comparison |
| **Total** | **100** | |

**Bonus** (up to +5):
* Traceroute analysis (hop-by-hop RTT): +3
* Time series plot (RTT over time): +2

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Root permission**: Ping có thể cần `sudo` trên một số systems
* **Packet count**: 100 packets đủ cho statistical significance
* **Regex validation**: Test regex với sample ping output trước

### ❌ Don'ts:
* **Không check None**: `re.search()` return None nếu không match
* **Wrong regex**: `time=([\d.]+)` matches "12.5", nhưng không match "12" (int)

### 🔧 Debugging:
* **Parser fails**: Check ping output format (macOS vs Linux khác nhau)
* **100% packet loss**: Check firewall (allow ICMP)
* **High RTT to localhost**: Check loopback interface (`ifconfig lo0`)

---

## **References**

1. Postel, J. (1981). *Internet Control Message Protocol* (RFC 792). IETF.

2. Jacobson, V. (1988). *Congestion Avoidance and Control*. ACM SIGCOMM.

3. Kurose, J. F., & Ross, K. W. (2017). *Computer Networking: A Top-Down Approach* (7th ed.). Pearson. Chapter 1.6: Packet Switching.

4. Stevens, W. R. (1994). *TCP/IP Illustrated, Volume 1: The Protocols*. Addison-Wesley. Chapter 7: Ping.

---

**Good luck!** 🏓
