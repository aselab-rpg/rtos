**Lab 4: Supabase Real-Time Database**  
**Tổng điểm:** 100  
**Thời gian:** 1-2 tuần

**Late Policy:** Lab có hạn chót và phải được nộp trước **11:59 PM** vào đúng ngày đến hạn. Nếu nộp trước **1:00 AM** của ngày hôm sau, bài sẽ vẫn được chấp nhận nhưng **bị trừ 5%** điểm.

---

## **Lab overview**

Mục tiêu lab là xây dựng **real-time monitoring application** sử dụng **Supabase** — platform cung cấp PostgreSQL với real-time capabilities (Change Data Capture via WebSocket).

Scenario: **Mission Simulator**
* Database: `missions` table (id, name, status, latitude, longitude, updated_at)
* Backend: Simulator script update GPS location mỗi 1-2s
* Frontend: Dashboard HTML hiển thị map real-time (update qua WebSocket)

Metrics:
* **End-to-end latency**: Time từ DB update → WebSocket → UI render
* **CDC reliability**: % updates received vs expected
* **Scalability**: Performance với 1/10/50 concurrent missions

Deliverable:
* Supabase project + SQL schema
* Mission simulator (Python)
* Real-time dashboard (HTML/JS)
* Báo cáo 4-6 trang

---

## **Part 1 — Real-Time Database Theory**

**Mục tiêu:** Hiểu Change Data Capture (CDC) và real-time mechanisms.

**Sinh viên cần làm và nộp:**

* **Change Data Capture (CDC)**:
  - **Definition**: Mechanism to track and propagate database changes to external systems
  - **PostgreSQL implementation**: WAL (Write-Ahead Log) → logical decoding → replication slots
  - **Supabase Realtime**: Listens to WAL → publishes changes via WebSocket

* **Supabase Realtime architecture**:
  ```
  Client (JS)
    ↓ Subscribe to table (WebSocket connection)
  Supabase Realtime Server
    ↓ Listen to PostgreSQL replication slot
  PostgreSQL WAL
    ↓ INSERT/UPDATE/DELETE events
  Database Table
  ```

* **Real-time channels**:
  - **Table-level subscription**: Listen to all rows in `missions` table
  - **Row-level security (RLS)**: Client only receives updates for rows they have access to
  - **Filters**: Subscribe to specific conditions (e.g., `status=in_progress`)

* **Comparison với traditional polling**:
  | Approach | Mechanism | Latency | Scalability | Complexity |
  |----------|-----------|---------|-------------|------------|
  | **Polling** | Client queries DB every Ts | Ts/2 (avg) | Poor (DB load) | Simple |
  | **WebSocket** | Server pushes on change | <100ms | Good (event-driven) | Moderate |
  | **SSE** | Server pushes via HTTP stream | <200ms | Moderate | Simple |

* **Use cases**:
  - ✅ Real-time dashboards (stock prices, tracking)
  - ✅ Collaborative apps (Google Docs, Figma)
  - ✅ Notifications (chat, alerts)
  - ❌ Batch processing (better use cron jobs)

**Bằng chứng bắt buộc:**

* CDC definition + PostgreSQL WAL mechanism (3-5 dòng)
* Supabase architecture diagram (Client → Realtime → PostgreSQL)
* Comparison table: Polling vs WebSocket vs SSE
* 2 use cases cho real-time DB

---

## **Part 2 — Supabase Setup & Schema**

**Mục tiêu:** Tạo Supabase project, define schema, enable realtime.

**Sinh viên cần làm và nộp:**

* **Supabase project setup**:
  1. Đăng ký tại https://supabase.com (free tier)
  2. Create new project: `rtos-lab4-mission-tracker`
  3. Note down:
     - **Project URL**: `https://<project-id>.supabase.co`
     - **API Key (anon)**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

* **SQL schema** (`setup.sql`):
  ```sql
  -- Missions table
  CREATE TABLE missions (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      status TEXT CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
      latitude REAL,
      longitude REAL,
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  
  -- Index for performance
  CREATE INDEX idx_missions_status ON missions(status);
  
  -- Enable realtime
  ALTER PUBLICATION supabase_realtime ADD TABLE missions;
  
  -- Insert sample data
  INSERT INTO missions (name, status, latitude, longitude) VALUES
      ('Mission Alpha', 'in_progress', 21.0285, 105.8542),  -- Hanoi
      ('Mission Beta', 'pending', 10.8231, 106.6297),       -- HCMC
      ('Mission Gamma', 'in_progress', 16.0544, 108.2022);  -- Da Nang
  ```

* **Realtime configuration**:
  - Enable realtime for `missions` table:
    ```sql
    ALTER PUBLICATION supabase_realtime ADD TABLE missions;
    ```
  - Row-level security (optional):
    ```sql
    ALTER TABLE missions ENABLE ROW LEVEL SECURITY;
    CREATE POLICY "Public read access" ON missions FOR SELECT USING (true);
    ```

* **Testing connection**:
  ```bash
  curl "https://<project-id>.supabase.co/rest/v1/missions?select=*" \
    -H "apikey: <anon-key>" \
    -H "Authorization: Bearer <anon-key>"
  ```
  Expected: JSON array with 3 missions

**Bằng chứng bắt buộc:**

* `setup.sql`: CREATE TABLE, ALTER PUBLICATION, INSERT sample data
* Screenshot: Supabase dashboard showing `missions` table (3 rows)
* Command: `curl` test (bỏ sensitive keys trong report)

---

## **Part 3 — Mission Simulator & Dashboard**

**Mục tiêu:** Implement backend simulator (Python) và frontend dashboard (HTML/JS).

**Sinh viên cần làm và nộp:**

* **Backend: Mission Simulator** (`mission_simulator.py`):
  ```python
  import os
  import time
  import random
  from supabase import create_client, Client
  
  # Config
  url = os.environ.get("SUPABASE_URL")
  key = os.environ.get("SUPABASE_KEY")
  supabase: Client = create_client(url, key)
  
  def update_mission(mission_id):
      # Simulate GPS movement (random walk)
      response = supabase.table("missions").select("*").eq("id", mission_id).execute()
      mission = response.data[0]
      
      new_lat = mission['latitude'] + random.uniform(-0.01, 0.01)
      new_lon = mission['longitude'] + random.uniform(-0.01, 0.01)
      
      # Update DB
      supabase.table("missions").update({
          "latitude": new_lat,
          "longitude": new_lon,
          "updated_at": "now()"
      }).eq("id", mission_id).execute()
      
      print(f"[{time.time()}] Updated mission {mission_id}: ({new_lat:.4f}, {new_lon:.4f})")
  
  # Main loop
  while True:
      missions = supabase.table("missions").select("id").eq("status", "in_progress").execute()
      for m in missions.data:
          update_mission(m['id'])
      time.sleep(2)  # Update every 2s
  ```

* **Frontend: Real-time Dashboard** (`dashboard.html`):
  ```html
  <!DOCTYPE html>
  <html>
  <head>
      <title>Mission Tracker</title>
      <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
      <style>
          #map { width: 800px; height: 600px; border: 1px solid black; }
          .mission { position: absolute; width: 10px; height: 10px; background: red; border-radius: 50%; }
      </style>
  </head>
  <body>
      <h1>Real-Time Mission Tracker</h1>
      <div id="map"></div>
      <div id="log"></div>
  
      <script>
          const SUPABASE_URL = 'https://<project-id>.supabase.co';
          const SUPABASE_KEY = 'eyJhbGci...';
          const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  
          // Initial load
          async function loadMissions() {
              const { data } = await supabase.from('missions').select('*');
              data.forEach(mission => renderMission(mission));
          }
  
          // Subscribe to realtime updates
          const channel = supabase.channel('missions-channel')
              .on('postgres_changes', {
                  event: 'UPDATE',
                  schema: 'public',
                  table: 'missions'
              }, (payload) => {
                  const mission = payload.new;
                  const latency = Date.now() - new Date(mission.updated_at).getTime();
                  console.log(`Received update for ${mission.name} (latency: ${latency}ms)`);
                  renderMission(mission);
              })
              .subscribe();
  
          function renderMission(mission) {
              let marker = document.getElementById(`mission-${mission.id}`);
              if (!marker) {
                  marker = document.createElement('div');
                  marker.id = `mission-${mission.id}`;
                  marker.className = 'mission';
                  document.getElementById('map').appendChild(marker);
              }
              // Simple projection (lat/lon to pixels)
              const x = (mission.longitude + 180) * 800 / 360;
              const y = (90 - mission.latitude) * 600 / 180;
              marker.style.left = `${x}px`;
              marker.style.top = `${y}px`;
          }
  
          loadMissions();
      </script>
  </body>
  </html>
  ```

* **Expected behavior**:
  1. Chạy `python3 mission_simulator.py` → Update GPS mỗi 2s
  2. Mở `dashboard.html` trong browser → Markers di chuyển real-time
  3. Console log: "Received update... (latency: XXms)"

**Bằng chứng bắt buộc:**

* Code: `mission_simulator.py`, `dashboard.html`
* Screenshot: Dashboard with moving markers (animated GIF nếu có)
* Console log: 10-20 lines showing latency measurements

---

## **Part 4 — Latency Measurement & Analysis**

**Mục tiêu:** Đo end-to-end latency và phân tích performance.

**Sinh viên cần làm và nộp:**

* **Latency definition**:
  ```
  End-to-end latency = t_render - t_update
  
  Where:
  - t_update: Timestamp khi DB update (mission.updated_at)
  - t_render: Timestamp khi client nhận WebSocket message (Date.now())
  ```

* **Instrumentation** (modify dashboard.html):
  ```javascript
  const latencies = [];
  
  supabase.channel('missions-channel')
      .on('postgres_changes', ..., (payload) => {
          const t_update = new Date(payload.new.updated_at).getTime();
          const t_render = Date.now();
          const latency = t_render - t_update;
          latencies.push(latency);
          
          document.getElementById('log').innerHTML += 
              `<p>Mission ${payload.new.name}: ${latency}ms</p>`;
      });
  
  // Export to CSV after 100 updates
  setTimeout(() => {
      console.log("Latencies (ms):", latencies);
      downloadCSV(latencies);
  }, 200000);  // 200s
  ```

* **Experiment matrix**:
  | Scenario | # Missions | Update Rate | Duration | Expected Latency |
  |----------|------------|-------------|----------|------------------|
  | Baseline | 1 | 2s | 2 min | 50-100ms |
  | Moderate | 10 | 2s | 5 min | 100-200ms |
  | High | 50 | 1s | 5 min | 200-500ms |

* **Results** (example):
  | Scenario | Mean Latency | P50 | P95 | P99 | Packet Loss |
  |----------|--------------|-----|-----|-----|-------------|
  | Baseline | 75ms | 68ms | 120ms | 150ms | 0% |
  | Moderate | 180ms | 150ms | 320ms | 450ms | 2% |
  | High | 420ms | 380ms | 720ms | 1200ms | 8% |

* **Visualization**:
  - **CDF plot**: X-axis = latency (ms), Y-axis = cumulative probability
  - **Time series**: X-axis = time, Y-axis = latency (ms), show spikes
  - **Observation**: Latency increases với # missions (contention)

* **Root cause analysis**:
  - **Why latency increases?**
    * Network round-trip: Client ↔ Supabase server (50-100ms baseline)
    * PostgreSQL WAL processing: More updates → higher WAL volume
    * WebSocket broadcasting: Server must fan-out to multiple clients
  
  - **Packet loss**:
    * High update rate → WebSocket buffer overflow
    * Server drops messages when queue full
    * Client misses some updates (staleness)
  
  - **Optimization strategies**:
    * Batching: Accumulate updates, send every 5s instead of 1s
    * Filtering: Only subscribe to nearby missions (reduce traffic)
    * Compression: Enable WebSocket compression (reduce bandwidth)

**Bằng chứng bắt buộc:**

* Latency measurements: CSV file với 100+ samples
* Results table: Mean, P50, P95, P99 for 3 scenarios
* 2 plots: CDF, time series
* Root cause analysis (5-10 dòng)

---

## **What to turn in**

### 1. **PDF Report** (tên file: `Lab4_Report_<MSSV>_<HoTen>.pdf`)

Báo cáo dài **4-6 trang**.

**Báo cáo phải gồm:**

* **a. Title page** [không tính điểm]

* **b. Introduction & Theory** [20 points]
  - CDC definition (PostgreSQL WAL → logical decoding)
  - Supabase Realtime architecture (Client → Realtime → PostgreSQL)
  - Comparison: Polling vs WebSocket (latency, scalability)
  - Use cases (2 examples)

* **c. Implementation** [20 points]
  - SQL schema (`missions` table với 5 columns)
  - Mission simulator (Python: random GPS walk, update every 2s)
  - Dashboard (HTML/JS: WebSocket subscription, render markers)
  - Screenshot: Dashboard with 3 missions

* **d. Latency Measurement** [30 points]
  - **Table 1**: 3 scenarios (# missions, mean, P95, P99, packet loss)
  - **Figure 1**: CDF plot (latency distribution)
  - **Figure 2**: Time series (latency over time)
  - Description (3-5 dòng)

* **e. Analysis** [20 points]
  - Root cause: Network RTT + WAL processing + WebSocket broadcast
  - Packet loss reason: Buffer overflow at high update rate
  - Optimization strategies: Batching, filtering, compression
  - Comparison với traditional polling (200ms vs 75ms latency)

* **f. Conclusion** [10 points]
  - Summary: Supabase Realtime enables <100ms latency for moderate workloads
  - Recommendation: Use for dashboards, avoid for high-frequency trading
  - Limitations: Packet loss at high scale, no guaranteed delivery
  - Future work: Compare với Firebase, Socket.io, self-hosted WebSocket

### 2. **Code & Data Package**

**Bắt buộc có:**

* `setup.sql`: CREATE TABLE, ALTER PUBLICATION, INSERT
* `mission_simulator.py`: Backend simulator
* `dashboard.html`: Frontend (WebSocket subscription)
* `requirements.txt`: supabase
* `README.md`: How to run (include Supabase project URL, setup steps)
* `latencies.csv`: Raw latency measurements (100+ samples)
* `plots/`: 2 figures (CDF, time series)

---

## **Grading Rubric**

| Section | Points | Criteria |
|---------|--------|----------|
| **Theory** | 20 | CDC explained, Supabase architecture, comparison table |
| **Implementation** | 20 | SQL schema, simulator, dashboard, screenshot |
| **Measurement** | 30 | Table (3 scenarios) + 2 plots (CDF, time series) |
| **Analysis** | 20 | Root cause, packet loss, optimization, comparison |
| **Conclusion** | 10 | Summary, recommendation, future work |
| **Total** | **100** | |

**Bonus** (up to +10):
* Row-level security (RLS) demo: +3
* Real map integration (Leaflet.js): +4
* Comparison với Firebase Realtime DB: +3

---

## **Tips & Common Pitfalls**

### ✅ Do's:
* **Environment variables**: Store Supabase URL/key in `.env` (don't hardcode)
* **Error handling**: Catch WebSocket disconnect, auto-reconnect
* **Clock sync**: Use server timestamp (`updated_at`) not client clock
* **Logging**: Log every WebSocket message với timestamp

### ❌ Don'ts:
* **Không enable realtime**: Phải chạy `ALTER PUBLICATION supabase_realtime ADD TABLE missions`
* **Hardcode credentials**: Không commit API keys vào Git
* **Ignore packet loss**: High update rate → buffer overflow → missed messages

### 🔧 Debugging:
* **No WebSocket messages**: Check `ALTER PUBLICATION` executed, table có data
* **High latency (>5s)**: Check network (VPN?), Supabase server location (Singapore vs US)
* **Dashboard not updating**: Check browser console errors, CORS policy

---

## **References**

1. Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media. Chapter 11: Stream Processing.

2. Supabase Documentation. (2024). *Realtime: Postgres Changes*. Retrieved from https://supabase.com/docs/guides/realtime

3. PostgreSQL Documentation. (2024). *Logical Decoding*. Retrieved from https://www.postgresql.org/docs/current/logicaldecoding.html

4. Fette, I., & Melnikov, A. (2011). *The WebSocket Protocol* (RFC 6455). IETF.

---

**Good luck!** 🚀
