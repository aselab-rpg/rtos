#!/usr/bin/env python3
"""
Lab 2: Mô phỏng Thuật toán Lập lịch (Scheduling)
So sánh FCFS vs EDF trong hệ thống Real-Time
"""

import random
import argparse
from dataclasses import dataclass, field
from typing import List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


@dataclass
class Transaction:
    """Đại diện cho một transaction/task"""
    transaction_id: str
    arrival_time: int  # ms
    execution_time: int  # ms
    deadline: int  # ms (absolute time)
    
    # Thông tin runtime (được cập nhật trong quá trình mô phỏng)
    start_time: int = -1
    finish_time: int = -1
    missed_deadline: bool = False
    
    def __repr__(self):
        return f"T{self.transaction_id[2:]}(arr={self.arrival_time}, exec={self.execution_time}, dl={self.deadline})"


def generate_transactions(num_transactions: int = 50, seed: int = 42) -> List[Transaction]:
    """
    Tạo danh sách transactions ngẫu nhiên
    
    Args:
        num_transactions: Số lượng transactions
        seed: Random seed để có thể tái tạo kết quả
    
    Returns:
        List các Transaction objects
    """
    random.seed(seed)
    transactions = []
    
    current_time = 0
    for i in range(num_transactions):
        # Arrival time: mỗi transaction đến cách nhau 10-50ms
        arrival_time = current_time + random.randint(10, 50)
        
        # Execution time: 20-100ms
        execution_time = random.randint(20, 100)
        
        # Deadline: arrival_time + (1.5 đến 4.0 lần execution_time)
        # Tạo áp lực về deadline
        slack = random.uniform(1.5, 4.0)
        deadline = arrival_time + int(execution_time * slack)
        
        transactions.append(Transaction(
            transaction_id=f"T_{i+1:03d}",
            arrival_time=arrival_time,
            execution_time=execution_time,
            deadline=deadline
        ))
        
        current_time = arrival_time
    
    return transactions


def simulate_fcfs(transactions: List[Transaction]) -> Tuple[List[Transaction], dict]:
    """
    Mô phỏng thuật toán FCFS (First-Come First-Served)
    
    Args:
        transactions: Danh sách transactions (sẽ được copy để không ảnh hưởng bản gốc)
    
    Returns:
        (executed_transactions, statistics)
    """
    # Copy để không ảnh hưởng dữ liệu gốc
    tasks = [Transaction(
        transaction_id=t.transaction_id,
        arrival_time=t.arrival_time,
        execution_time=t.execution_time,
        deadline=t.deadline
    ) for t in transactions]
    
    # Sắp xếp theo arrival time (FCFS)
    tasks.sort(key=lambda x: x.arrival_time)
    
    current_time = 0
    completed_tasks = []
    missed_count = 0
    
    for task in tasks:
        # Chờ đến khi task arrive
        if current_time < task.arrival_time:
            current_time = task.arrival_time
        
        # Bắt đầu thực thi
        task.start_time = current_time
        task.finish_time = current_time + task.execution_time
        
        # Kiểm tra deadline
        if task.finish_time > task.deadline:
            task.missed_deadline = True
            missed_count += 1
        
        completed_tasks.append(task)
        current_time = task.finish_time
    
    # Tính toán thống kê
    total_tasks = len(tasks)
    miss_ratio = (missed_count / total_tasks * 100) if total_tasks > 0 else 0
    avg_response_time = sum(t.finish_time - t.arrival_time for t in completed_tasks) / total_tasks
    
    stats = {
        'algorithm': 'FCFS',
        'total_tasks': total_tasks,
        'missed_tasks': missed_count,
        'miss_ratio': miss_ratio,
        'avg_response_time': avg_response_time,
        'total_time': current_time
    }
    
    return completed_tasks, stats


def simulate_edf(transactions: List[Transaction]) -> Tuple[List[Transaction], dict]:
    """
    Mô phỏng thuật toán EDF (Earliest Deadline First)
    
    Args:
        transactions: Danh sách transactions
    
    Returns:
        (executed_transactions, statistics)
    """
    # Copy để không ảnh hưởng dữ liệu gốc
    tasks = [Transaction(
        transaction_id=t.transaction_id,
        arrival_time=t.arrival_time,
        execution_time=t.execution_time,
        deadline=t.deadline
    ) for t in transactions]
    
    current_time = 0
    ready_queue = []
    completed_tasks = []
    missed_count = 0
    remaining_tasks = sorted(tasks, key=lambda x: x.arrival_time)
    
    while remaining_tasks or ready_queue:
        # Thêm các tasks đã arrive vào ready queue
        while remaining_tasks and remaining_tasks[0].arrival_time <= current_time:
            ready_queue.append(remaining_tasks.pop(0))
        
        if not ready_queue:
            # Không có task nào ready, nhảy đến arrival time của task tiếp theo
            if remaining_tasks:
                current_time = remaining_tasks[0].arrival_time
            continue
        
        # Chọn task có deadline gần nhất (EDF)
        ready_queue.sort(key=lambda x: x.deadline)
        task = ready_queue.pop(0)
        
        # Thực thi task
        task.start_time = current_time
        task.finish_time = current_time + task.execution_time
        
        # Kiểm tra deadline
        if task.finish_time > task.deadline:
            task.missed_deadline = True
            missed_count += 1
        
        completed_tasks.append(task)
        current_time = task.finish_time
    
    # Sắp xếp lại theo thứ tự thực thi
    completed_tasks.sort(key=lambda x: x.start_time)
    
    # Tính toán thống kê
    total_tasks = len(tasks)
    miss_ratio = (missed_count / total_tasks * 100) if total_tasks > 0 else 0
    avg_response_time = sum(t.finish_time - t.arrival_time for t in completed_tasks) / total_tasks
    
    stats = {
        'algorithm': 'EDF',
        'total_tasks': total_tasks,
        'missed_tasks': missed_count,
        'miss_ratio': miss_ratio,
        'avg_response_time': avg_response_time,
        'total_time': current_time
    }
    
    return completed_tasks, stats


def plot_gantt_chart(fcfs_tasks: List[Transaction], edf_tasks: List[Transaction], 
                     fcfs_stats: dict, edf_stats: dict):
    """Vẽ Gantt Chart so sánh FCFS và EDF"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    
    # Màu sắc
    color_success = '#2ecc71'  # Xanh lá - hoàn thành đúng hạn
    color_missed = '#e74c3c'    # Đỏ - trượt deadline
    
    def draw_gantt(ax, tasks, title, stats):
        """Vẽ Gantt chart cho một thuật toán"""
        y_pos = 0
        
        for task in tasks:
            color = color_missed if task.missed_deadline else color_success
            
            # Vẽ thanh thực thi
            ax.barh(y_pos, task.execution_time, left=task.start_time, 
                   height=0.8, color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
            
            # Vẽ deadline marker (đường đứng đỏ)
            ax.plot([task.deadline, task.deadline], [y_pos - 0.4, y_pos + 0.4], 
                   'r--', linewidth=2, alpha=0.7)
            
            # Label transaction ID
            ax.text(task.start_time + task.execution_time/2, y_pos, 
                   task.transaction_id.replace('T_', 'T'), 
                   ha='center', va='center', fontsize=6, fontweight='bold')
            
            y_pos += 1
        
        # Cấu hình axes
        ax.set_xlabel('Thời gian (ms)', fontsize=11)
        ax.set_ylabel('Transactions', fontsize=11)
        ax.set_title(f'{title}\n'
                    f'Miss Ratio: {stats["miss_ratio"]:.1f}% '
                    f'({stats["missed_tasks"]}/{stats["total_tasks"]} tasks) | '
                    f'Avg Response: {stats["avg_response_time"]:.1f}ms',
                    fontsize=13, fontweight='bold', pad=15)
        ax.set_ylim(-1, len(tasks))
        ax.set_yticks([])
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Legend
        success_patch = mpatches.Patch(color=color_success, label='Hoàn thành đúng hạn')
        missed_patch = mpatches.Patch(color=color_missed, label='Trượt deadline')
        deadline_line = mpatches.Patch(color='red', label='Deadline', linestyle='--')
        ax.legend(handles=[success_patch, missed_patch, deadline_line], 
                 loc='upper right', fontsize=9)
    
    # Vẽ cả hai thuật toán
    draw_gantt(ax1, fcfs_tasks, 'FCFS (First-Come First-Served)', fcfs_stats)
    draw_gantt(ax2, edf_tasks, 'EDF (Earliest Deadline First)', edf_stats)
    
    plt.tight_layout()
    plt.savefig('scheduling_gantt_chart.png', dpi=300, bbox_inches='tight')
    print("✓ Đã lưu Gantt Chart: scheduling_gantt_chart.png")


def plot_comparison(fcfs_stats: dict, edf_stats: dict):
    """Vẽ biểu đồ so sánh tổng quan"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    algorithms = ['FCFS', 'EDF']
    
    # Biểu đồ Miss Ratio
    miss_ratios = [fcfs_stats['miss_ratio'], edf_stats['miss_ratio']]
    colors = ['#e74c3c', '#2ecc71']
    
    bars1 = ax1.bar(algorithms, miss_ratios, color=colors, alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Miss Ratio (%)', fontsize=12)
    ax1.set_title('So sánh Deadline Miss Ratio', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, max(miss_ratios) * 1.2)
    ax1.grid(axis='y', alpha=0.3)
    
    for bar, ratio in zip(bars1, miss_ratios):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{ratio:.1f}%',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Biểu đồ Average Response Time
    avg_response = [fcfs_stats['avg_response_time'], edf_stats['avg_response_time']]
    
    bars2 = ax2.bar(algorithms, avg_response, color=['#3498db', '#9b59b6'], alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Average Response Time (ms)', fontsize=12)
    ax2.set_title('So sánh Thời gian Phản hồi Trung bình', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, time in zip(bars2, avg_response):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.1f}ms',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('scheduling_comparison.png', dpi=300, bbox_inches='tight')
    print("✓ Đã lưu biểu đồ so sánh: scheduling_comparison.png")


def print_statistics(fcfs_stats: dict, edf_stats: dict):
    """In ra thống kê chi tiết"""
    
    print("\n" + "=" * 70)
    print("THỐNG KÊ CHI TIẾT")
    print("=" * 70)
    
    print("\n┌─── FCFS (First-Come First-Served) ───────────────────────────┐")
    print(f"│  Tổng số tasks:           {fcfs_stats['total_tasks']:>4} tasks                      │")
    print(f"│  Tasks hoàn thành:        {fcfs_stats['total_tasks'] - fcfs_stats['missed_tasks']:>4} tasks                      │")
    print(f"│  Tasks trượt deadline:    {fcfs_stats['missed_tasks']:>4} tasks                      │")
    print(f"│  Miss Ratio:              {fcfs_stats['miss_ratio']:>6.2f}%                       │")
    print(f"│  Avg Response Time:       {fcfs_stats['avg_response_time']:>6.1f} ms                       │")
    print(f"│  Total Time:              {fcfs_stats['total_time']:>6} ms                       │")
    print("└───────────────────────────────────────────────────────────────┘")
    
    print("\n┌─── EDF (Earliest Deadline First) ────────────────────────────┐")
    print(f"│  Tổng số tasks:           {edf_stats['total_tasks']:>4} tasks                      │")
    print(f"│  Tasks hoàn thành:        {edf_stats['total_tasks'] - edf_stats['missed_tasks']:>4} tasks                      │")
    print(f"│  Tasks trượt deadline:    {edf_stats['missed_tasks']:>4} tasks                      │")
    print(f"│  Miss Ratio:              {edf_stats['miss_ratio']:>6.2f}%                       │")
    print(f"│  Avg Response Time:       {edf_stats['avg_response_time']:>6.1f} ms                       │")
    print(f"│  Total Time:              {edf_stats['total_time']:>6} ms                       │")
    print("└───────────────────────────────────────────────────────────────┘")
    
    # So sánh
    print("\n" + "=" * 70)
    print("SO SÁNH")
    print("=" * 70)
    
    miss_improvement = fcfs_stats['miss_ratio'] - edf_stats['miss_ratio']
    improvement_pct = (miss_improvement / fcfs_stats['miss_ratio'] * 100) if fcfs_stats['miss_ratio'] > 0 else 0
    
    print(f"\n✓ EDF giảm Miss Ratio: {miss_improvement:.2f}% (giảm {improvement_pct:.1f}%)")
    
    if edf_stats['avg_response_time'] < fcfs_stats['avg_response_time']:
        time_improvement = fcfs_stats['avg_response_time'] - edf_stats['avg_response_time']
        print(f"✓ EDF cải thiện Response Time: -{time_improvement:.1f}ms")
    else:
        time_degradation = edf_stats['avg_response_time'] - fcfs_stats['avg_response_time']
        print(f"⚠ EDF có Response Time cao hơn: +{time_degradation:.1f}ms")
    
    print(f"\n{'='*70}")
    print("KẾT LUẬN")
    print(f"{'='*70}")
    print(f"EDF là thuật toán tốt hơn cho Real-Time Systems vì:")
    print(f"  • Giảm thiểu deadline misses (quan trọng nhất trong RTDB)")
    print(f"  • Đảm bảo các task quan trọng (deadline gần) được ưu tiên")
    print(f"  • Phù hợp với yêu cầu QoS của hệ thống thời gian thực")


def main():
    parser = argparse.ArgumentParser(description='Lab 2: Transaction Scheduling Simulation')
    parser.add_argument('--num-transactions', type=int, default=50, 
                       help='Số lượng transactions (default: 50)')
    parser.add_argument('--detailed', action='store_true',
                       help='Hiển thị thông tin chi tiết từng transaction')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("LAB 2: MÔ PHỎNG THUẬT TOÁN LẬP LỊCH (TRANSACTION SCHEDULING)")
    print("=" * 70)
    
    # Tạo transactions
    print(f"\nĐang tạo {args.num_transactions} transactions...")
    transactions = generate_transactions(args.num_transactions, args.seed)
    print(f"✓ Đã tạo {len(transactions)} transactions")
    
    if args.detailed:
        print("\nDanh sách Transactions:")
        for t in transactions[:10]:  # Chỉ hiển thị 10 cái đầu
            print(f"  {t}")
        if len(transactions) > 10:
            print(f"  ... và {len(transactions) - 10} transactions khác")
    
    # Chạy mô phỏng FCFS
    print("\n" + "=" * 70)
    print("CHẠY MÔ PHỎNG FCFS...")
    print("=" * 70)
    fcfs_tasks, fcfs_stats = simulate_fcfs(transactions)
    print(f"✓ Hoàn thành FCFS - Miss Ratio: {fcfs_stats['miss_ratio']:.1f}%")
    
    # Chạy mô phỏng EDF
    print("\n" + "=" * 70)
    print("CHẠY MÔ PHỎNG EDF...")
    print("=" * 70)
    edf_tasks, edf_stats = simulate_edf(transactions)
    print(f"✓ Hoàn thành EDF - Miss Ratio: {edf_stats['miss_ratio']:.1f}%")
    
    # In thống kê
    print_statistics(fcfs_stats, edf_stats)
    
    # Vẽ biểu đồ
    print("\n" + "=" * 70)
    print("TẠO BIỂU ĐỒ...")
    print("=" * 70)
    
    # Chỉ vẽ Gantt chart cho 30 transactions đầu tiên (để dễ nhìn)
    display_count = min(30, args.num_transactions)
    plot_gantt_chart(fcfs_tasks[:display_count], edf_tasks[:display_count], 
                     fcfs_stats, edf_stats)
    plot_comparison(fcfs_stats, edf_stats)
    
    print("\n✓ Hoàn thành Lab 2!")


if __name__ == "__main__":
    main()
