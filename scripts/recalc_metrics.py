#!/usr/bin/env python3
"""
指标重算脚本 - 更新库存后重新计算所有衍生指标

使用方法：
    python recalc_metrics.py [seller_id]

如果不指定seller_id，则重算所有卖家的指标。
"""

import sys
import os
import json
import glob
import math
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sku_analysis')

# ── 衍生指标计算函数 ──

def calc_inventory_depth(inventory):
    """库存深度层级"""
    try:
        inv = float(inventory)
    except (ValueError, TypeError):
        inv = 0
    if inv <= 0: return "零库存"
    elif inv <= 9: return "浅库存"
    elif inv <= 49: return "中库存"
    else: return "深库存"

def calc_risk_level(rma_pct):
    """风险等级"""
    try:
        rma = abs(float(rma_pct))
    except (ValueError, TypeError):
        rma = 0
    if rma > 80: return "高危"
    elif rma >= 10: return "中危"
    else: return "低危"

def calc_efficiency_level(qty_sold):
    """效能等级"""
    try:
        qty = float(qty_sold)
    except (ValueError, TypeError):
        qty = 0
    if qty >= 10: return "核心主力"
    elif qty >= 3: return "潜力培育"
    elif qty >= 1: return "低动销"
    else: return "零销负销"

def calc_price_tier(unit_price):
    """客单价分层"""
    try:
        p = float(unit_price)
    except (ValueError, TypeError):
        p = 0
    if p > 500: return "高客单"
    elif p >= 100: return "中客单"
    else: return "低客单"

def calc_priority_score(return_loss, return_margin_erosion, rma_pct, qty_sold):
    """优先级评分"""
    try:
        loss_score = min(100, float(return_loss) / 100 * 100)
        erosion_score = min(100, float(return_margin_erosion) * 100)
        rma_score = min(100, abs(float(rma_pct)))
        qty = float(qty_sold) if qty_sold else 0
        if qty == 0: qty_score = 50
        elif qty <= 2: qty_score = 80
        elif qty <= 5: qty_score = 50
        elif qty <= 10: qty_score = 20
        else: qty_score = 0
        return round(loss_score * 0.4 + erosion_score * 0.3 + rma_score * 0.2 + qty_score * 0.1, 1)
    except:
        return 0

def calc_priority_level(score):
    """优先级等级"""
    if score >= 40: return "极高"
    elif score >= 25: return "高"
    elif score >= 10: return "中"
    else: return "低"

def calc_disposal_suggestion(rma_pct, inventory, efficiency_level):
    """处置建议"""
    try:
        rma = abs(float(rma_pct))
    except: rma = 0
    try:
        inv = float(inventory)
    except: inv = 0
    
    if rma > 80: risk = "高危"
    elif rma >= 10: risk = "中危"
    else: risk = "低危"
    
    if inv <= 0: inv_depth = "零库存"
    elif inv <= 9: inv_depth = "浅库存"
    elif inv <= 49: inv_depth = "中库存"
    else: inv_depth = "深库存"
    
    if risk == "高危" and inv_depth in ["浅库存", "零库存"]:
        return "立即下架止损"
    elif risk == "高危" and inv_depth == "中库存":
        return "整改观察+限量销售，7天未改善则下架"
    elif risk == "高危" and inv_depth == "深库存":
        return "整改+清库存，7天观察期"
    elif risk == "中危" and efficiency_level in ["低动销", "零销负销"]:
        return "限制补货，优先清理库存"
    elif risk == "中危" and efficiency_level in ["核心主力", "潜力培育"]:
        return "维持销售，加强品质监控"
    elif risk == "低危" and efficiency_level == "零销负销":
        return "直接清退下架"
    elif risk == "低危" and efficiency_level == "低动销":
        return "评估是否保留"
    else:
        return "正常运营，持续监控RMA变化"

def calc_health_score(gmv, total_margin, rma_pct, qty, sku_count, margin_rate):
    """健康度评分"""
    score = 0
    score += min(30, float(gmv) / 100000 * 30)
    score += min(25, float(total_margin) / 10000 * 25)
    rma = abs(float(rma_pct))
    if rma <= 0.5: score += 20
    elif rma <= 2: score += 16
    elif rma <= 5: score += 12
    elif rma <= 10: score += 8
    elif rma <= 20: score += 4
    if float(qty) >= 50: score += 10
    elif float(qty) >= 20: score += 7
    elif float(qty) >= 5: score += 4
    elif float(qty) > 0: score += 2
    if int(sku_count) >= 20: score += 10
    elif int(sku_count) >= 10: score += 7
    elif int(sku_count) >= 5: score += 4
    elif int(sku_count) > 0: score += 2
    if float(margin_rate) >= 10: score += 5
    elif float(margin_rate) >= 5: score += 4
    elif float(margin_rate) > 0: score += 2
    return round(score, 1)

def calc_grade(score):
    """等级划分"""
    if score >= 75: return 'A', '核心优质卖家'
    elif score >= 60: return 'B', '高潜力卖家'
    elif score >= 45: return 'C', '普通合规卖家'
    else: return 'D', '高风险卖家'

# ── 重算单个JSON文件 ──
def recalc_json_file(json_path):
    """重算单个JSON文件的所有衍生指标"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data.get('records', [])
    total_gmv = 0
    total_margin = 0
    total_qty = 0
    total_rma_weighted = 0
    
    for record in records:
        gmv = record.get('GMV', 0) or 0
        margin = record.get('Total Margin', 0) or 0
        qty = record.get('Net Quantity Sold', 0) or 0
        rma = record.get('RMA %', 0) or 0
        inventory = record.get('Inventory', 0) or 0
        sku_count = record.get('SKU Count', 1) or 1
        
        total_gmv += gmv
        total_margin += margin
        total_qty += qty
        if gmv > 0:
            total_rma_weighted += abs(rma) * gmv
        
        # 计算衍生指标
        unit_price = gmv / qty if qty > 0 else 0
        unit_margin = margin / qty if qty > 0 else 0
        margin_rate = (margin / gmv * 100) if gmv > 0 else 0
        return_loss = abs(gmv) * abs(rma) / 100 if rma else 0
        return_qty = math.ceil(qty * abs(rma) / 100 / (1 - abs(rma) / 100)) if rma and abs(rma) < 100 else 0
        return_erosion = return_loss / margin if margin > 0 else 0
        daily_sales = qty / 20  # 默认20天
        
        # 更新记录
        record['客单价'] = round(unit_price, 2)
        record['单件毛利'] = round(unit_margin, 2)
        record['单SKU毛利率(%)'] = round(margin_rate, 2)
        record['退货损失金额'] = round(return_loss, 2)
        record['退货件数'] = return_qty
        record['退货毛利侵蚀率'] = round(return_erosion, 4)
        record['日均销量'] = round(daily_sales, 2)
        
        # 更新分级标签
        record['库存深度层级'] = calc_inventory_depth(inventory)
        record['SKU风险等级'] = calc_risk_level(rma)
        record['SKU效能等级'] = calc_efficiency_level(qty)
        record['客单价分层'] = calc_price_tier(unit_price)
        record['整改优先级得分'] = calc_priority_score(return_loss, return_erosion, rma, qty)
        record['整改优先级'] = calc_priority_level(record['整改优先级得分'])
        record['处置建议'] = calc_disposal_suggestion(rma, inventory, record['SKU效能等级'])
    
    # 更新卖家汇总
    avg_rma = total_rma_weighted / total_gmv if total_gmv > 0 else 0
    margin_rate = (total_margin / total_gmv * 100) if total_gmv > 0 else 0
    sku_count = len(records)
    
    health_score = calc_health_score(total_gmv, total_margin, avg_rma, total_qty, sku_count, margin_rate)
    grade, grade_desc = calc_grade(health_score)
    
    data['seller_summary'] = {
        'GMV': round(total_gmv, 2),
        'RMA%': round(avg_rma, 4),
        '总毛利': round(total_margin, 2),
        '总销量': total_qty,
        'SKU数': sku_count,
        '健康度评分': health_score,
        '等级': grade,
        '等级说明': grade_desc
    }
    
    # 保存
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {
        'gmv': total_gmv,
        'health_score': health_score,
        'grade': grade,
        'sku_count': sku_count
    }

# ── 主函数 ──
def main():
    seller_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f"开始重算指标...")
    print(f"数据目录: {DATA_DIR}")
    if seller_id:
        print(f"指定卖家: {seller_id}")
    
    total_files = 0
    total_sellers = 0
    
    for seller_dir in os.listdir(DATA_DIR):
        if seller_id and seller_dir != seller_id:
            continue
        
        seller_path = os.path.join(DATA_DIR, seller_dir)
        if not os.path.isdir(seller_path):
            continue
        
        seller_files = 0
        for json_file in glob.glob(os.path.join(seller_path, '*.json')):
            try:
                result = recalc_json_file(json_file)
                seller_files += 1
                total_files += 1
                print(f"  ✓ {seller_dir}/{os.path.basename(json_file)} - GMV ${result['gmv']:,.2f} 健康度{result['health_score']}({result['grade']})")
            except Exception as e:
                print(f"  ✗ {seller_dir}/{os.path.basename(json_file)} - 错误: {e}")
        
        if seller_files > 0:
            total_sellers += 1
    
    print(f"\n{'='*50}")
    print(f"指标重算完成")
    print(f"{'='*50}")
    print(f"重算文件数: {total_files}")
    print(f"重算卖家数: {total_sellers}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
