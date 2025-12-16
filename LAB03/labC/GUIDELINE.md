**Lab C: CAN Bus — Worst-Case Response Time Analysis**  
**Tổng điểm:** 100  
**Thời gian:** 90 phút

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Lab này phân tích **schedulability của CAN bus** — protocol dùng trong automotive systems để truyền messages giữa ECUs (Electronic Control Units).

Objectives:
* Understand CAN message structure (ID, priority, arbitration)
* Calculate Worst-Case Response Time (WCRT) cho mỗi message
* Determine schedulability (WCRT ≤ Deadline?)

Deliverable:
* WCRT calculation tool (Python)
* Báo cáo 3-4 trang

---

## **Part 1 — CAN Bus Theory**

**Mục tiêu:** Hiểu CAN protocol và priority-based arbitration.

**Sinh viên cần làm và nộp:**

* **CAN bus architecture**:
  - **Multi-master**: Any ECU có thể send messages
  - **Broadcast**: All ECUs nhận tất cả messages
  - **CSMA/CA**: Carrier Sense Multiple Access with Collision Avoidance
  - **Priority arbitration**: Message với ID nhỏ hơn có priority cao hơn

* **CAN message format**:
  ```
  [SOF] [ID (11-bit)] [RTR] [Control] [Data (0-8 bytes)] [CRC] [ACK] [EOF]
  
  - SOF: Start of Frame (1 bit)
  - ID: Identifier (11 bits for standard CAN, 29 bits for extended)
  - RTR: Remote Transmission Request (1 bit)
  - Control: Data Length Code (6 bits)
  - Data: 0-8 bytes payload
  - CRC: Cyclic Redundancy Check (16 bits)
  - ACK: Acknowledgment (2 bits)
  - EOF: End of Frame (7 bits)
  
  Total overhead: ~47 bits (for 0 data bytes)
  Total frame: 47 + 8×data_length bits
  ```

* **Bit stuffing**:
  - **Rule**: After 5 consecutive identical bits, insert 1 opposite bit
  - **Example**: `111110` → `1111100` (stuff bit = 0)
  - **Worst-case**: 20% overhead (every 5 bits → 1 stuff bit)
  - **Formula**: `stuffed_bits = original_bits × 1.2` (worst-case)

* **Priority arbitration**:
  ```
  Example: 3 ECUs gửi cùng lúc:
  - ECU A: ID = 0x100 (256 decimal)
  - ECU B: ID = 0x200 (512 decimal)
  - ECU C: ID = 0x050 (80 decimal)
  
  Bus:       0 0 0 0 1 0 1 0 0 0 0 (ID = 0x050)
  ECU A:     0 0 0 1 X            (loses at bit 4)
  ECU B:     0 0 1 X              (loses at bit 3)
  ECU C:     0 0 0 0 1 0 1 0 0 0 0 (wins, transmits)
  
  → Lower ID = higher priority
  ```

* **Real-time constraints**:
  - **Period (T_i)**: Message i generated mỗi T_i ms
  - **Deadline (D_i)**: Message phải arrive trong D_i ms
  - **WCRT (R_i)**: Worst-case response time
  - **Schedulability**: R_i ≤ D_i for all messages

**Bằng chứng bắt buộc:**

* CAN architecture (4 properties: multi-master, broadcast, CSMA/CA, priority)
* Message format (các fields + total overhead)
* Bit stuffing example (5 bits → 1 stuff bit)
* Priority arbitration example (3 ECUs)

---

## **Part 2 — WCRT Calculation Theory**

**Mục tiêu:** Học cách tính WCRT cho CAN messages.

**Sinh viên cần làm và nộp:**

* **Transmission time (C_i)**:
  ```
  C_i = (Frame_size + Stuff_bits) / Bitrate
  
  Frame_size = 47 + 8 × Data_length  (bits)
  Stuff_bits = Frame_size × 0.2       (worst-case)
  Bitrate = 500 kbps (typical CAN)
  
  Example: Data_length = 8 bytes
  Frame_size = 47 + 64 = 111 bits
  Stuff_bits = 111 × 0.2 = 22.2 ≈ 22 bits
  Total = 133 bits
  C_i = 133 / 500000 = 0.266 ms
  ```

* **WCRT formula (Tindell et al., 1995)**:
  ```
  R_i = J_i + C_i + B_i + Σ_{j ∈ hp(i)} ⌈(R_i + J_j) / T_j⌉ × C_j
  
  Where:
  - R_i: WCRT of message i
  - J_i: Queuing jitter (release time variation)
  - C_i: Transmission time of message i
  - B_i: Blocking time (1 lower-priority message)
  - hp(i): Set of messages với priority > i (ID < i)
  - T_j: Period of message j
  - ⌈x⌉: Ceiling function
  ```

* **Blocking time (B_i)**:
  - **Definition**: Time message i bị blocked bởi 1 lower-priority message đang transmit
  - **Formula**: `B_i = max{C_k : priority(k) < priority(i)}`
  - **Example**: Message i có ID=100, messages với ID>100 có C_k = {0.2ms, 0.3ms, 0.25ms}
    → B_i = 0.3ms (longest lower-priority message)

* **Iterative calculation**:
  ```python
  def calculate_wcrt(i, messages):
      # Initial guess
      R_prev = messages[i].C
      
      while True:
          # Calculate interference
          interference = 0
          for j in hp(i):
              interference += math.ceil((R_prev + messages[j].J) / messages[j].T) * messages[j].C
          
          # New WCRT
          R_new = messages[i].J + messages[i].C + messages[i].B + interference
          
          # Converged?
          if R_new == R_prev:
              return R_new
          
          R_prev = R_new
  ```

* **Example calculation**:
  | Message | ID | Period (T) | Data (bytes) | C (ms) | J (ms) | B (ms) | hp(i) | WCRT (ms) | Deadline (ms) | Schedulable? |
  |---------|----|-----------:|-------------:|-------:|-------:|-------:|-------|----------:|--------------:|--------------|
  | M1 | 100 | 10 | 8 | 0.27 | 0 | 0 | {} | 0.27 | 5 | ✅ Yes |
  | M2 | 200 | 20 | 4 | 0.18 | 0 | 0.27 | {M1} | 0.72 | 15 | ✅ Yes |
  | M3 | 300 | 50 | 8 | 0.27 | 0 | 0.27 | {M1,M2} | 1.71 | 40 | ✅ Yes |

**Bằng chứng bắt buộc:**

* C_i calculation formula + example (8-byte message @ 500kbps)
* WCRT formula (Tindell) với tất cả terms explained
* Blocking time definition + example
* WCRT example table (3 messages)

---

## **Part 3 — WCRT Calculation Tool**

**Mục tiêu:** Implement tool tính WCRT và check schedulability.

**Sinh viên cần làm và nộp:**

* **Message definition** (`can_rt_calc.py`):
  ```python
  import math
  
  class CANMessage:
      def __init__(self, id, period, deadline, data_length, bitrate=500000):
          self.id = id
          self.period = period  # ms
          self.deadline = deadline  # ms
          self.data_length = data_length  # bytes
          
          # Calculate transmission time
          frame_size = 47 + 8 * data_length  # bits
          stuff_bits = frame_size * 0.2  # worst-case
          total_bits = frame_size + stuff_bits
          self.C = total_bits / bitrate * 1000  # ms
          
          self.J = 0  # queuing jitter (assume 0)
          self.B = 0  # blocking time (calculated later)
          self.wcrt = 0  # worst-case response time
      
      def __repr__(self):
          return f"M{self.id}: T={self.period}ms, D={self.deadline}ms, C={self.C:.3f}ms"
  ```

* **WCRT calculation**:
  ```python
  def calculate_wcrt(messages):
      # Sort by priority (lower ID = higher priority)
      messages = sorted(messages, key=lambda m: m.id)
      
      for i, msg_i in enumerate(messages):
          # Calculate blocking time (longest lower-priority message)
          lower_priority = [m for m in messages if m.id > msg_i.id]
          msg_i.B = max([m.C for m in lower_priority], default=0)
          
          # Iterative WCRT calculation
          R_prev = msg_i.C
          for _ in range(100):  # max 100 iterations
              interference = 0
              
              # Higher-priority messages
              higher_priority = [m for m in messages if m.id < msg_i.id]
              for msg_j in higher_priority:
                  n_instances = math.ceil((R_prev + msg_j.J) / msg_j.period)
                  interference += n_instances * msg_j.C
              
              R_new = msg_i.J + msg_i.C + msg_i.B + interference
              
              # Check convergence
              if abs(R_new - R_prev) < 0.001:
                  msg_i.wcrt = R_new
                  break
              
              R_prev = R_new
          
          # Check schedulability
          schedulable = msg_i.wcrt <= msg_i.deadline
          print(f"M{msg_i.id}: WCRT={msg_i.wcrt:.3f}ms, D={msg_i.deadline}ms [{('PASS' if schedulable else 'FAIL')}]")
      
      return messages
  ```

* **Example usage**:
  ```python
  # Define messages
  messages = [
      CANMessage(id=100, period=10, deadline=5, data_length=8),
      CANMessage(id=200, period=20, deadline=15, data_length=4),
      CANMessage(id=300, period=50, deadline=40, data_length=8),
  ]
  
  # Calculate WCRT
  calculate_wcrt(messages)
  
  # Output:
  # M100: WCRT=0.266ms, D=5ms [PASS]
  # M200: WCRT=0.718ms, D=15ms [PASS]
  # M300: WCRT=1.712ms, D=40ms [PASS]
  ```

**Bằng chứng bắt buộc:**

* Code: `can_rt_calc.py` với classes: CANMessage, calculate_wcrt()
* Command: `python3 can_rt_calc.py` (define 3 messages, print WCRT)
* Screenshot: Terminal output showing WCRT cho 3 messages

---

## **Part 4 — Experiments & Analysis**

**Mục tiêu:** Test schedulability với different message sets.

**Sinh viên cần làm và nộp:**

* **Experiment matrix**:
  | Scenario | # Messages | Utilization | Expected | Note |
  |----------|------------|-------------|----------|------|
  | Light | 3 | 30% | ✅ All schedulable | Simple case |
  | Moderate | 5 | 60% | ✅ All schedulable | Typical automotive |
  | Heavy | 10 | 85% | ⚠️ Some unschedulable | Near limit |
  | Overload | 15 | 120% | ❌ Many unschedulable | Exceeds capacity |

* **Utilization calculation**:
  ```
  U = Σ (C_i / T_i)
  
  Example (Light scenario):
  - M100: C=0.27ms, T=10ms → 0.027
  - M200: C=0.18ms, T=20ms → 0.009
  - M300: C=0.27ms, T=50ms → 0.0054
  Total U = 0.0414 (4.14%)
  ```

* **Results** (example for Moderate scenario):
  | Message | ID | Period | Data | C (ms) | B (ms) | WCRT (ms) | Deadline (ms) | Schedulable? |
  |---------|----:|-------:|-----:|-------:|-------:|----------:|--------------:|--------------|
  | M1 | 100 | 10 | 8 | 0.27 | 0 | 0.27 | 5 | ✅ Yes |
  | M2 | 200 | 20 | 4 | 0.18 | 0.27 | 0.72 | 15 | ✅ Yes |
  | M3 | 300 | 50 | 8 | 0.27 | 0.27 | 1.71 | 40 | ✅ Yes |
  | M4 | 400 | 100 | 2 | 0.13 | 0.27 | 3.42 | 80 | ✅ Yes |
  | M5 | 500 | 200 | 8 | 0.27 | 0.27 | 7.15 | 150 | ✅ Yes |

* **Visualization 1: WCRT vs Deadline**
  - Bar chart: X-axis = messages, Y-axis = time (ms)
  - 2 bars per message: WCRT (blue), Deadline (red dashed line)
  - **Observation**: All WCRT < Deadline → schedulable

* **Visualization 2: Utilization vs Schedulability**
  - X-axis = utilization (%), Y-axis = # unschedulable messages
  - **Observation**: U < 60% → all schedulable, U > 85% → some unschedulable

* **Analysis**:
  - **Why WCRT increases với message index?**
    * Higher ID (lower priority) → more interference từ higher-priority messages
    * M1 (ID=100) không có interference → WCRT = C + B ≈ C
    * M5 (ID=500) có 4 higher-priority messages → WCRT >> C
  
  - **Blocking time impact**:
    * Mỗi message bị block bởi 1 longest lower-priority message
    * Example: M2 blocked by M3 (C=0.27ms) → B_2 = 0.27ms
    * Blocking time adds ~0.27ms to WCRT
  
  - **Schedulability limit**:
    * CAN bus utilization limit ≈ 70-80% (due to arbitration overhead)
    * Beyond 80% → WCRT increases rapidly (interference dominates)
    * Comparison với CPU scheduling: Liu-Layland bound = 69% for n→∞
  
  - **Priority assignment strategy**:
    * Rate Monotonic (RM): Shorter period → higher priority (lower ID)
    * Deadline Monotonic (DM): Shorter deadline → higher priority
    * For CAN: Manually assign IDs according to criticality

**Bằng chứng bắt buộc:**

* Results table cho Moderate scenario (5 messages)
* 2 plots: WCRT vs Deadline, Utilization vs Schedulability
* 10-15 dòng phân tích: Why WCRT increases, blocking impact, schedulability limit

---

## **What to turn in**

### 1. **PDF Report** (tên file: `LabC_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo dài **3-4 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Theory** [25 points]
  - CAN architecture (multi-master, priority arbitration)
  - Message format (47 bits overhead + bit stuffing)
  - WCRT formula (Tindell) với all terms explained
  - Blocking time definition + example

* **c. Implementation** [20 points]
  - CANMessage class (C_i calculation)
  - calculate_wcrt() function (iterative method)
  - Example output (3 messages với WCRT)

* **d. Experiments** [30 points]
  - **Table 1**: Moderate scenario (5 messages, WCRT vs Deadline)
  - **Figure 1**: WCRT vs Deadline bar chart
  - **Figure 2**: Utilization vs Schedulability plot
  - Description (3-5 dòng)

* **e. Analysis** [25 points]
  - Why WCRT increases với message ID (interference)
  - Blocking time impact (~0.27ms per message)
  - Schedulability limit (70-80% utilization)
  - Priority assignment strategy (RM vs DM)

### 2. **Code & Data Package**

**Bắt buộc có:**

* `can_rt_calc.py`: WCRT calculation tool
* `README.md`: How to run, define custom message sets
* `results/`: CSV tables cho 4 scenarios (Light/Moderate/Heavy/Overload)
* `plots/`: 2 figures

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 25 | CAN protocol, WCRT formula, blocking time |
| **Implementation** | 20 | CANMessage class, calculate_wcrt() |
| **Experiments** | 30 | Table (5 messages) + 2 plots |
| **Analysis** | 25 | Interference, blocking, schedulability limit |
| **Total** | **100** | |

**Bonus** (up to +5):
* Extended CAN (29-bit ID): +2
* Comparison với FlexRay: +3

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Bit stuffing**: Always include 20% overhead (worst-case)
* **Convergence**: Check `abs(R_new - R_prev) < 0.001` để tránh infinite loop
* **Sorting**: Sort messages by ID trước khi tính WCRT

### ❌ Don'ts:
* **Không tính blocking**: B_i = max{C_k : ID_k > ID_i} (not min)
* **Wrong ceiling**: `math.ceil((R + J) / T)` not `math.floor()`
* **Ignore stuff bits**: Frame size phải include 20% overhead

### 🔧 Debugging:
* **WCRT not converging**: Check period values (too small → overflow)
* **All unschedulable**: Check bitrate (500kbps?) và frame size calculation
* **Negative B_i**: Check no lower-priority messages → B_i = 0

---

## **References**

1. Tindell, K., Burns, A., & Wellings, A. J. (1995). *Calculating Controller Area Network (CAN) Message Response Times*. Control Engineering Practice, 3(8), 1163-1169.

2. Davis, R. I., Burns, A., Bril, R. J., & Lukkien, J. J. (2007). *Controller Area Network (CAN) Schedulability Analysis: Refuted, Revisited and Revised*. Real-Time Systems, 35(3), 239-272.

3. Bosch. (1991). *CAN Specification Version 2.0*. Robert Bosch GmbH.

4. Nolte, T., Hansson, H., & Norstrom, C. (2005). *Probabilistic Worst-Case Response-Time Analysis for the Controller Area Network*. IEEE RTAS.

---

**Good luck!** 🚗
