# Real-Time Communication Labs

Ba bài lab thực hành về độ trễ, jitter, ưu tiên và deadline trên mạng/bus thời gian thực. Mỗi nhóm 2 SV, nộp một báo cáo chung gồm 3 phần.

## Cấu trúc repo
- `labA/ping_analyzer.py`: script rút trích latency & jitter từ log `ping`.
- `labB/udp_sender.py`, `labB/udp_receiver.py`: gửi/nhận UDP định kỳ và ghi log deadline miss.
- `labB/delay_summary.py`: tóm tắt log delay CSV.
- `labC/can_rt_calc.py`: tính gần đúng worst-case response time trên bus ưu tiên.

## Mini-Lab A (45’) – Đo latency & jitter với ping
**Mục tiêu:** thấy rõ latency/jitter khi mạng nhàn vs bận.  
**Setup:** 2 máy A, B cùng LAN; có `ping`, `python3`, `iperf3`.

1) **Đo trạng thái nhàn**  
   Trên máy A: `ping -i 0.01 -c 500 <IP_B> > ping_idle.log`
2) **Đo trạng thái bận**  
   - Một máy chạy `iperf3 -s`  
   - Máy khác: `iperf3 -c <IP_server> -t 60`  
   - Đồng thời trên A: `ping -i 0.01 -c 500 <IP_B> > ping_busy.log`
3) **Phân tích log**  
   - Trích giá trị `time=` rồi tính Avg/Min/Max và jitter xấp xỉ (stddev).  
   - Dùng script: `python3 labA/ping_analyzer.py ping_idle.log ping_busy.log`
4) **Báo cáo**  
   - Bảng: `Trạng thái | Avg (ms) | Min (ms) | Max (ms) | Jitter (stddev ms)`  
   - 5–7 dòng nhận xét: jitter thay đổi ra sao với iperf; vì sao “tốc độ mạng cao” chưa đủ cho real-time.

## Mini-Lab B (90’) – UDP periodic stream & deadline miss
**Mục tiêu:** đo end-to-end delay, jitter, deadline miss khi có nhiễu.

1) **Setup**  
   - Máy S (Sender) → R (Receiver) qua LAN.  
   - Chỉnh `DEST_IP` trong `labB/udp_sender.py` thành IP của R.  
   - Tham số chính: `PERIOD` (chu kỳ gửi, mặc định 10 ms), `DEADLINE` (15 ms).
2) **Chạy baseline**  
   - Trên R: `python3 labB/udp_receiver.py`  
   - Trên S: `python3 labB/udp_sender.py`  
   - Kết quả: màn hình hiển thị tổng gói, số miss; file `delay_log.csv`.
3) **Phân tích**  
   - Tóm tắt log: `python3 labB/delay_summary.py delay_log.csv`  
   - Ghi bảng: `Scenario | Avg delay (ms) | Max delay (ms) | Miss count / total | Miss ratio`
4) **Tạo nhiễu**  
   - `iperf3 -s` trên R (hoặc máy khác).  
   - `iperf3 -c <IP_server> -u -b 50M -t 60` trên một máy.  
   - Lặp lại bước chạy sender/receiver trong lúc iperf chạy, lấy `delay_log.csv` lần 2.
5) **Báo cáo**  
   - 1 đoạn mô tả setup (IP, period, deadline).  
   - 2 bảng số liệu (nhàn vs nhiễu).  
   - 5–10 dòng trả lời: vì sao nhiễu làm miss tăng; nếu yêu cầu hard RT <10 ms thì hệ thống có đạt không; 1–2 biện pháp cải thiện (ưu tiên, VLAN riêng, TSN,…).

## Mini-Lab C (45’) – Bài tập CAN / bus RT
**Mục tiêu:** tính gần đúng worst-case response time (Rᵢ) với ưu tiên bus.

### Đề
| Msg | Priority (1 cao) | Period T (ms) | Deadline D (ms) | Time on bus C (ms) |
| --- | --- | --- | --- | --- |
| M1 | 1 | 10 | 10 | 1.0 |
| M2 | 2 | 20 | 20 | 1.2 |
| M3 | 3 | 50 | 50 | 1.5 |

Giả sử một chu kỳ gửi một lần, priority quyết định truy cập bus. Công thức gần đúng:  
`R1 ≈ C1`  
`R2 ≈ C2 + ceil(D2 / T1) * C1`  
`R3 ≈ C3 + ceil(D3 / T1) * C1 + ceil(D3 / T2) * C2`

### Yêu cầu
- SV tự tính R1, R2, R3; so sánh Rᵢ với Dᵢ (Rᵢ > Dᵢ ⇒ miss deadline).  
- Thử thay đổi tham số: tăng C3 (frame dài hơn) hoặc giảm T1 (M1 dày hơn) và xem schedulable không.  
- Liên hệ Mini-Lab B: luồng UDP là message định kỳ; thêm luồng ưu tiên cao sẽ gây gì?

### Script kiểm tra nhanh
`python3 labC/can_rt_calc.py --help`  
Ví dụ: `python3 labC/can_rt_calc.py` (dùng bảng mặc định) hoặc chỉnh JSON trong file.
