#!/usr/bin/env python3
"""
库存变化追踪脚本 - 记录每次库存变化，生成库存变化历史

使用方法：
    python track_inventory.py [seller_id]

功能：
    1. 读取所有JSON文件的库存数据
    2. 生成库存变化历史记录
    3. 输出库存变化报告
"""

import sys
import os
import json
import glob
from datetime import datetime
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sku_analysis')
HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'inventory_history')

# ── 读取库存数据 ──
def read_inventory_data(seller_id=None):
    """读取所有卖家的库存数据"""
    all_data = {}
    
    for seller_dir in os.listdir(DATA_DIR):
        if seller_id and seller_dir != seller_id:
            continue
        
        seller_path = os.path.join(DATA_DIR, seller_dir)
        if not os.path.isdir(seller_path):
            continue
        
        seller_data = []
        for json_file in sorted(glob.glob(os.path.join(seller_path, '*.json'))):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                date_period = data.get('date_period', '')
                date_readable = data.get('date_readable', '')
                records = data.get('records', [])
                
                for record in records:
                    sku = record.get('NeweggItemNumber') or record.get('NeweggSku#')
                    if not sku:
                        continue
                    
                    seller_data.append({
                        'date_period': date_period,
                        'date_readable': date_readable,
                        'sku': sku,
                        'inventory': record.get('Inventory', 0) or 0,
                        'fulfillment': record.get('FulfillmentType', ''),
                        'price': record.get('SellingPrice', 0) or 0,
                        'gmv': record.get('GMV', 0) or 0,
                        'qty': record.get('Net Quantity Sold', 0) or 0,
                        'short_title': record.get('ShortTitle', '')
                    })
            except Exception as e:
                pass
        
        if seller_data:
            all_data[seller_dir] = seller_data
    
    return all_data

# ── 分析库存变化 ──
def analyze_inventory_changes(seller_data):
    """分析单个卖家的库存变化"""
    # 按SKU分组
    sku_history = defaultdict(list)
    for record in seller_data:
        sku_history[record['sku']].append(record)
    
    changes = []
    for sku, history in sku_history.items():
        if len(history) < 2:
            continue
        
        # 按时间排序
        history.sort(key=lambda x: x['date_period'])
        
        # 分析变化
        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            
            inv_change = curr['inventory'] - prev['inventory']
            inv_change_pct = (inv_change / prev['inventory'] * 100) if prev['inventory'] > 0 else 0
            
            changes.append({
                'sku': sku,
                'short_title': curr['short_title'],
                'prev_date': prev['date_readable'],
                'curr_date': curr['date_readable'],
                'prev_inventory': prev['inventory'],
                'curr_inventory': curr['inventory'],
                'inv_change': inv_change,
                'inv_change_pct': round(inv_change_pct, 1),
                'fulfillment': curr['fulfillment'],
                'price': curr['price']
            })
    
    return changes

# ── 生成报告 ──
def generate_report(all_changes, seller_id=None):
    """生成库存变化报告"""
    # 创建目录
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # 生成报告文件
    report_file = os.path.join(HISTORY_DIR, f'inventory_changes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'seller_filter': seller_id or 'all',
        'total_sellers': len(all_changes),
        'total_changes': sum(len(v) for v in all_changes.values()),
        'changes_by_seller': {}
    }
    
    for seller, changes in all_changes.items():
        # 统计
        inv_increased = sum(1 for c in changes if c['inv_change'] > 0)
        inv_decreased = sum(1 for c in changes if c['inv_change'] < 0)
        inv_unchanged = sum(1 for c in changes if c['inv_change'] == 0)
        
        # 找出变化最大的SKU
        top_increases = sorted(changes, key=lambda x: -x['inv_change'])[:5]
        top_decreases = sorted(changes, key=lambda x: x['inv_change'])[:5]
        
        report['changes_by_seller'][seller] = {
            'total_changes': len(changes),
            'inv_increased': inv_increased,
            'inv_decreased': inv_decreased,
            'inv_unchanged': inv_unchanged,
            'top_increases': [{'sku': c['sku'], 'title': c['short_title'], 'change': c['inv_change']} for c in top_increases],
            'top_decreases': [{'sku': c['sku'], 'title': c['short_title'], 'change': c['inv_change']} for c in top_decreases],
            'changes': changes
        }
    
    # 保存报告
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report_file, report

# ── 打印报告 ──
def print_report(report):
    """打印库存变化报告"""
    print(f"\n{'='*60}")
    print(f"库存变化追踪报告")
    print(f"{'='*60}")
    print(f"生成时间: {report['generated_at']}")
    print(f"卖家范围: {report['seller_filter']}")
    print(f"涉及卖家: {report['total_sellers']}个")
    print(f"库存变化: {report['total_changes']}条")
    
    for seller, data in report['changes_by_seller'].items():
        print(f"\n--- {seller} ---")
        print(f"  变化总数: {data['total_changes']}")
        print(f"  库存增加: {data['inv_increased']}个SKU")
        print(f"  库存减少: {data['inv_decreased']}个SKU")
        print(f"  库存不变: {data['inv_unchanged']}个SKU")
        
        if data['top_increases']:
            print(f"  库存增加Top5:")
            for item in data['top_increases'][:3]:
                print(f"    {item['sku']}: +{item['change']}件")
        
        if data['top_decreases']:
            print(f"  库存减少Top5:")
            for item in data['top_decreases'][:3]:
                print(f"    {item['sku']}: {item['change']}件")

# ── 主函数 ──
def main():
    seller_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f"开始追踪库存变化...")
    print(f"数据目录: {DATA_DIR}")
    
    # 1. 读取数据
    all_data = read_inventory_data(seller_id)
    if not all_data:
        print("错误: 未找到数据")
        sys.exit(1)
    
    print(f"读取到 {len(all_data)} 个卖家的数据")
    
    # 2. 分析变化
    all_changes = {}
    for seller, data in all_data.items():
        changes = analyze_inventory_changes(data)
        if changes:
            all_changes[seller] = changes
    
    if not all_changes:
        print("未发现库存变化")
        sys.exit(0)
    
    # 3. 生成报告
    report_file, report = generate_report(all_changes, seller_id)
    
    # 4. 打印报告
    print_report(report)
    
    print(f"\n报告已保存到: {report_file}")

if __name__ == '__main__':
    main()
