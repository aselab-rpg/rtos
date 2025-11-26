# 1. Mạng xã hội & Truyền thông (Social Media)
Đây là nhóm tận dụng triệt để tốc độ thấp (low latency) của Redis.

## Twitter (X):

Use case: Timeline Generation. Khi một người nổi tiếng tweet, Redis giúp đẩy bài viết đó vào timeline của hàng triệu followers gần như ngay lập tức.

Kỹ thuật: Sử dụng Redis Lists hoặc Sorted Sets để lưu trữ ID của các tweet mới nhất cho mỗi người dùng.

## Instagram:

Use case: Lưu trữ Activity Feed, Session người dùng và đếm like/tim theo thời gian thực.

Kỹ thuật: Kỹ sư của Instagram đã chia sẻ việc họ map hàng triệu ID người dùng vào Redis Hash để tiết kiệm bộ nhớ (memory optimization) thay vì lưu key đơn lẻ.

## Pinterest:

Use case: Quản lý User Graph (ai follow ai, ai ghim bài nào) và Caching ảnh.

Quy mô: Họ lưu trữ hàng tỷ quan hệ trong Redis để truy xuất cực nhanh khi người dùng lướt feed.

# 2. Nền tảng phát triển & Dịch vụ (Dev & SaaS)
## GitHub:

Use case: Job Queue (Hàng đợi công việc). Khi bạn push code, merge request, hoặc chạy CI/CD, các tác vụ này được đẩy vào hàng đợi (thường dùng thư viện Resque hoặc Sidekiq chạy trên nền Redis) để xử lý ngầm (background processing).

Tại sao: Redis xử lý thao tác Push/Pop cực nhanh, phù hợp làm Message Broker.

## StackOverflow:

Use case: Caching toàn diện. Mỗi câu hỏi, câu trả lời, profile người dùng đều được cache tầng tầng lớp lớp trên Redis để giảm tải cho SQL Server.

Hiệu quả: Giúp trang web phản hồi cực nhanh dù lượng truy cập khổng lồ.

# 3. Gọi xe & Vận chuyển (Ride-hailing)
## Uber / Grab:

Use case: Geospatial Indexing (Định vị không gian) & Real-time Matching.

Kỹ thuật: Sử dụng tính năng GEO của Redis (như GEOADD, GEORADIUS) để tìm các tài xế đang ở gần vị trí khách hàng nhất trong bán kính vài km chỉ trong tích tắc (mili-giây).

# 4. Game & Giải trí
## Discord:

Use case: Quản lý trạng thái online/offline (Presence) và hàng đợi tin nhắn.

Thách thức: Với hàng triệu user online cùng lúc, việc cập nhật ai đang "Sẵn sàng" hay "Đang chơi game" đòi hỏi tốc độ ghi cực cao mà CSDL truyền thống không chịu nổi.

## Riot Games (League of Legends):

Use case: Chat service, lưu trữ trạng thái trận đấu tạm thời và session của người chơi.
