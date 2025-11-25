#!/usr/bin/env python3
"""
Lab 3: Quản lý Độ tươi Dữ liệu (Data Freshness)
Kịch bản: Hệ thống iSARS (intelligent Search And Rescue System)
"""

import time
import random
import argparse
from dataclasses import dataclass
from typing import List, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


@dataclass
class GPSData:
    """Dữ liệu GPS từ nạn nhân"""
    victim_id: str
    latitude: float
    longitude: float
    timestamp: float  # Unix timestamp
    
    def age(self, current_time: float) -> float:
        """Tính tuổi của dữ liệu (seconds)"""
        return current_time - self.timestamp
    
    def is_fresh(self, current_time: float, avi: float) -> bool:
        """Kiểm tra dữ liệu có tươi không"""
        return self.age(current_time) <= avi
    
    def __repr__(self):
        return f"GPS({self.victim_id}, lat={self.latitude:.4f}, lng={self.longitude:.4f}, ts={self.timestamp:.3f})"


@dataclass
class ProcessingResult:
    """Kết quả xử lý một GPS data point"""
    data: GPSData
    received_time: float
    processed_time: float
    is_fresh: bool
    age_at_processing: float
    
    @property
    def processing_delay(self) -> float:
        return self.processed_time - self.received_time


class FreshnessFilter:
    """Bộ lọc độ tươi dữ liệu"""
    
    def __init__(self, avi: float):
        """
        Args:
            avi: Absolute Validity Interval (seconds)
        """
        self.avi = avi
        self.accepted_count = 0
        self.rejected_count = 0
        self.results: List[ProcessingResult] = []
    
    def process(self, data: GPSData, current_time: float) -> Tuple[bool, str]:
        """
        Xử lý một GPS data point
        
        Args:
            data: GPS data
            current_time: Thời điểm xử lý
        
        Returns:
            (is_accepted, message)
        """
        age = data.age(current_time)
        is_fresh = data.is_fresh(current_time, self.avi)
        
        result = ProcessingResult(
            data=data,
            received_time=data.timestamp,
            processed_time=current_time,
            is_fresh=is_fresh,
            age_at_processing=age
        )
        
        self.results.append(result)
        
        if is_fresh:
            self.accepted_count += 1
            return True, f"✓ ACCEPTED - Age: {age*1000:.1f}ms (AVI: {self.avi*1000:.0f}ms)"
        else:
            self.rejected_count += 1
            return False, f"✗ REJECTED - Age: {age*1000:.1f}ms > AVI: {self.avi*1000:.0f}ms (STALE DATA!)"
    
    def get_statistics(self) -> dict:
        """Lấy thống kê"""
        total = self.accepted_count + self.rejected_count
        
        if total == 0:
            return {
                'total': 0,
                'accepted': 0,
                'rejected': 0,
                'rejection_rate': 0.0,
                'avg_age': 0.0,
                'max_age': 0.0
            }
        
        ages = [r.age_at_processing for r in self.results]
        
        return {
            'total': total,
            'accepted': self.accepted_count,
            'rejected': self.rejected_count,
            'rejection_rate': (self.rejected_count / total * 100),
            'avg_age': sum(ages) / len(ages),
            'max_age': max(ages),
            'avg_processing_delay': sum(r.processing_delay for r in self.results) / len(self.results)
        }


def generate_gps_stream(victim_id: str, duration: float, data_rate: int) -> List[GPSData]:
    """
    Tạo stream dữ liệu GPS giả lập
    
    Args:
        victim_id: ID nạn nhân
        duration: Thời gian mô phỏng (seconds)
        data_rate: Số lượng GPS updates per second
    
    Returns:
        List GPS data points
    """
    print(f"Đang tạo GPS stream (duration={duration}s, rate={data_rate} updates/s)...")
    
    stream = []
    num_points = int(duration * data_rate)
    interval = 1.0 / data_rate
    
    # Tọa độ xuất phát (giả lập nạn nhân ở Hà Nội)
    base_lat = 21.0285
    base_lng = 105.8542
    
    start_time = time.time()
    
    for i in range(num_points):
        # Mô phỏng chuyển động: nạn nhân di chuyển ngẫu nhiên
        lat = base_lat + random.uniform(-0.001, 0.001)
        lng = base_lng + random.uniform(-0.001, 0.001)
        
        timestamp = start_time + (i * interval)
        
        stream.append(GPSData(
            victim_id=victim_id,
            latitude=lat,
            longitude=lng,
            timestamp=timestamp
        ))
    
    print(f"✓ Đã tạo {len(stream)} GPS data points")
    return stream


def simulate_processing(stream: List[GPSData], freshness_filter: FreshnessFilter,
                       processing_delay: float, verbose: bool = False):
    """
    Mô phỏng xử lý stream với độ trễ
    
    Args:
        stream: Stream GPS data
        freshness_filter: Bộ lọc độ tươi
        processing_delay: Độ trễ xử lý (seconds)
        verbose: Hiển thị log chi tiết
    """
    print(f"\nĐang xử lý stream với processing delay = {processing_delay*1000:.0f}ms...")
    print("=" * 80)
    
    for i, data in enumerate(stream):
        # Chờ đến thời điểm data được tạo ra
        current_time = time.time()
        if data.timestamp > current_time:
            time.sleep(data.timestamp - current_time)
        
        # Mô phỏng độ trễ xử lý
        time.sleep(processing_delay)
        
        # Xử lý qua freshness filter
        process_time = time.time()
        is_accepted, message = freshness_filter.process(data, process_time)
        
        if verbose and (i < 5 or i % 20 == 0):  # Chỉ hiển thị một số messages
            status = "✓" if is_accepted else "✗"
            print(f"[{i+1:04d}] {status} {data.victim_id} | {message}")
    
    print("=" * 80)
    print("✓ Hoàn thành xử lý stream")


def plot_results(results: List[ProcessingResult], avi: float, stats: dict):
    """Vẽ biểu đồ phân tích"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Timeline - Data Age
    times = [(r.processed_time - results[0].processed_time) for r in results]
    ages_ms = [r.age_at_processing * 1000 for r in results]
    colors = ['green' if r.is_fresh else 'red' for r in results]
    
    ax1.scatter(times, ages_ms, c=colors, alpha=0.6, s=20)
    ax1.axhline(y=avi*1000, color='orange', linestyle='--', linewidth=2, label=f'AVI = {avi*1000:.0f}ms')
    ax1.set_xlabel('Thời gian (s)', fontsize=11)
    ax1.set_ylabel('Data Age (ms)', fontsize=11)
    ax1.set_title('Timeline - Độ tuổi dữ liệu khi xử lý', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 2. Histogram - Age Distribution
    ages_accepted = [r.age_at_processing * 1000 for r in results if r.is_fresh]
    ages_rejected = [r.age_at_processing * 1000 for r in results if not r.is_fresh]
    
    bins = 30
    ax2.hist(ages_accepted, bins=bins, color='green', alpha=0.7, label='Accepted (Fresh)', edgecolor='black')
    ax2.hist(ages_rejected, bins=bins, color='red', alpha=0.7, label='Rejected (Stale)', edgecolor='black')
    ax2.axvline(x=avi*1000, color='orange', linestyle='--', linewidth=2, label=f'AVI = {avi*1000:.0f}ms')
    ax2.set_xlabel('Data Age (ms)', fontsize=11)
    ax2.set_ylabel('Số lượng', fontsize=11)
    ax2.set_title('Phân bố độ tuổi dữ liệu', fontsize=13, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    # 3. Pie Chart - Accept/Reject Ratio
    sizes = [stats['accepted'], stats['rejected']]
    labels = [f"Accepted\n{stats['accepted']} ({100-stats['rejection_rate']:.1f}%)",
              f"Rejected\n{stats['rejected']} ({stats['rejection_rate']:.1f}%)"]
    colors_pie = ['#2ecc71', '#e74c3c']
    explode = (0.05, 0.05)
    
    ax3.pie(sizes, explode=explode, labels=labels, colors=colors_pie, autopct='',
           shadow=True, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax3.set_title('Tỷ lệ chấp nhận / loại bỏ', fontsize=13, fontweight='bold')
    
    # 4. Statistics Table
    ax4.axis('off')
    
    stats_text = f"""
    ╔══════════════════════════════════════════════════╗
    ║          THỐNG KÊ ĐỘ TƯƠI DỮ LIỆU               ║
    ╠══════════════════════════════════════════════════╣
    ║                                                  ║
    ║  AVI (Validity Interval):  {avi*1000:>6.0f} ms          ║
    ║                                                  ║
    ║  Tổng số data points:      {stats['total']:>6} points     ║
    ║  Accepted (Fresh):         {stats['accepted']:>6} points     ║
    ║  Rejected (Stale):         {stats['rejected']:>6} points     ║
    ║                                                  ║
    ║  Rejection Rate:           {stats['rejection_rate']:>6.2f} %          ║
    ║                                                  ║
    ║  Average Data Age:         {stats['avg_age']*1000:>6.1f} ms         ║
    ║  Maximum Data Age:         {stats['max_age']*1000:>6.1f} ms         ║
    ║  Avg Processing Delay:     {stats['avg_processing_delay']*1000:>6.1f} ms         ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝
    """
    
    ax4.text(0.5, 0.5, stats_text, fontsize=11, ha='center', va='center',
            family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig('data_freshness_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Đã lưu biểu đồ phân tích: data_freshness_analysis.png")


def print_statistics(stats: dict, avi: float):
    """In thống kê chi tiết"""
    
    print("\n" + "=" * 80)
    print("THỐNG KÊ ĐỘ TƯƠI DỮ LIỆU - iSARS SYSTEM")
    print("=" * 80)
    
    print(f"\n┌─── Cấu hình ────────────────────────────────────────────────────────┐")
    print(f"│  AVI (Absolute Validity Interval):  {avi*1000:>6.0f} ms                    │")
    print(f"└─────────────────────────────────────────────────────────────────────┘")
    
    print(f"\n┌─── Kết quả xử lý ───────────────────────────────────────────────────┐")
    print(f"│  Tổng số GPS data points:            {stats['total']:>6} points            │")
    print(f"│  Accepted (Fresh data):              {stats['accepted']:>6} points            │")
    print(f"│  Rejected (Stale data):              {stats['rejected']:>6} points            │")
    print(f"│                                                                     │")
    print(f"│  Rejection Rate:                     {stats['rejection_rate']:>6.2f} %               │")
    print(f"└─────────────────────────────────────────────────────────────────────┘")
    
    print(f"\n┌─── Thống kê thời gian ──────────────────────────────────────────────┐")
    print(f"│  Average Data Age:                   {stats['avg_age']*1000:>6.1f} ms              │")
    print(f"│  Maximum Data Age:                   {stats['max_age']*1000:>6.1f} ms              │")
    print(f"│  Average Processing Delay:           {stats['avg_processing_delay']*1000:>6.1f} ms              │")
    print(f"└─────────────────────────────────────────────────────────────────────┘")
    
    # Phân tích và cảnh báo
    print("\n" + "=" * 80)
    print("PHÂN TÍCH & CẢNH BÁO")
    print("=" * 80)
    
    if stats['rejection_rate'] < 5:
        print("\n✓ HỆ THỐNG HOẠT ĐỘNG TỐT")
        print("  • Rejection rate thấp (< 5%)")
        print("  • Dữ liệu đủ tươi cho robot navigation")
        print("  • Hệ thống xử lý kịp thời")
    elif stats['rejection_rate'] < 20:
        print("\n⚠ CẢNH BÁO: HỆ THỐNG BẮT ĐẦU QUÁ TẢI")
        print("  • Rejection rate trung bình (5-20%)")
        print("  • Một số dữ liệu bị loại bỏ")
        print("  • Nên tối ưu hóa processing hoặc tăng resources")
    else:
        print("\n✗ NGUY HIỂM: HỆ THỐNG QUÁ TẢI")
        print("  • Rejection rate cao (> 20%)")
        print("  • Nhiều dữ liệu ôi thiu bị loại bỏ")
        print("  • Robot có thể nhận thông tin sai → Nguy hiểm cho nhiệm vụ cứu hộ!")
        print("  • CẦN: Scale hệ thống hoặc tăng AVI (nếu chấp nhận được)")
    
    # Khuyến nghị
    print(f"\n{'='*80}")
    print("KHUYẾN NGHỊ")
    print(f"{'='*80}")
    
    if stats['avg_processing_delay'] * 1000 > avi * 1000 * 0.8:
        print("• Processing delay quá cao so với AVI")
        print(f"  → Giảm processing delay xuống dưới {avi*1000*0.5:.0f}ms")
    
    if stats['rejection_rate'] > 10:
        print("• Rejection rate cao")
        print("  → Option 1: Tối ưu hóa code xử lý (giảm processing delay)")
        print("  → Option 2: Scale hệ thống (thêm workers)")
        print(f"  → Option 3: Tăng AVI lên {avi*1000*1.5:.0f}ms (nếu use case cho phép)")


def main():
    parser = argparse.ArgumentParser(description='Lab 3: Data Freshness - iSARS System')
    parser.add_argument('--avi', type=float, default=0.2,
                       help='Absolute Validity Interval in seconds (default: 0.2)')
    parser.add_argument('--data-rate', type=int, default=50,
                       help='GPS data rate (updates/second, default: 50)')
    parser.add_argument('--processing-delay', type=float, default=0.05,
                       help='Processing delay in seconds (default: 0.05)')
    parser.add_argument('--duration', type=float, default=5.0,
                       help='Simulation duration in seconds (default: 5)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed processing logs')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LAB 3: QUẢN LÝ ĐỘ TƯƠI DỮ LIỆU (DATA FRESHNESS)")
    print("Kịch bản: iSARS - intelligent Search And Rescue System")
    print("=" * 80)
    
    print(f"\nCấu hình:")
    print(f"  • AVI (Validity Interval):  {args.avi*1000:.0f} ms")
    print(f"  • GPS Data Rate:            {args.data_rate} updates/second")
    print(f"  • Processing Delay:         {args.processing_delay*1000:.0f} ms")
    print(f"  • Simulation Duration:      {args.duration:.1f} seconds")
    
    # Tạo GPS stream
    print("\n" + "=" * 80)
    print("PHẦN 1: TẠO GPS STREAM")
    print("=" * 80)
    stream = generate_gps_stream("VICTIM_001", args.duration, args.data_rate)
    
    # Khởi tạo Freshness Filter
    print("\n" + "=" * 80)
    print("PHẦN 2: XỬ LÝ VỚI FRESHNESS FILTER")
    print("=" * 80)
    freshness_filter = FreshnessFilter(avi=args.avi)
    
    # Chạy mô phỏng
    simulate_processing(stream, freshness_filter, args.processing_delay, args.verbose)
    
    # Lấy thống kê
    stats = freshness_filter.get_statistics()
    
    # In kết quả
    print_statistics(stats, args.avi)
    
    # Vẽ biểu đồ
    print("\n" + "=" * 80)
    print("PHẦN 3: TẠO BIỂU ĐỒ PHÂN TÍCH")
    print("=" * 80)
    plot_results(freshness_filter.results, args.avi, stats)
    
    print("\n✓ Hoàn thành Lab 3!")


if __name__ == "__main__":
    main()
