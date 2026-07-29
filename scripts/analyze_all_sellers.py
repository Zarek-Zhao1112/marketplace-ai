"""分析77个seller数据，生成调研报告"""
import os
import sys
import json
from collections import defaultdict
from datetime import datetime

# 添加项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.web.data import load_all_seller_ids, load_all_seller_history
from src.web.seller_analysis import safe_float

def analyze_all_sellers():
    """分析所有seller数据"""
    all_ids = load_all_seller_ids()
    all_hist = load_all_seller_history()
    
    results = []
    category_stats = defaultdict(lambda: {"count": 0, "total_gmv": 0, "sellers": []})
    site_stats = {"B2C": {"count": 0, "total_gmv": 0}, "CA": {"count": 0, "total_gmv": 0}, "B2B": {"count": 0, "total_gmv": 0}}
    grade_stats = {"A": [], "B": [], "C": [], "D": []}
    
    for sid in all_ids:
        hist = all_hist.get(sid, [])
        if not hist:
            continue
        latest = hist[-1]
        
        # 读取最新数据
        seller_dir = os.path.join(PROJECT_ROOT, 'data', 'sku_analysis', sid)
        platform = 'B2C'
        seller_name = ''
        categories = []
        
        if os.path.exists(seller_dir):
            files = sorted([f for f in os.listdir(seller_dir) if f.endswith('.json')], reverse=True)
            if files:
                with open(os.path.join(seller_dir, files[0]), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = data.get('records', [])
                    if records:
                        p = str(records[0].get('Platform', '')).lower()
                        if 'ca' in p: platform = 'CA'
                        elif 'business' in p: platform = 'B2B'
                        seller_name = records[0].get('SellerName', '')
                        
                        # 收集品类信息
                        for r in records:
                            cat = r.get('品类', '其他')
                            if cat and cat != '其他':
                                categories.append(cat)
        
        gmv = safe_float(latest.get('GMV', 0))
        rma = safe_float(latest.get('RMA%', 0))
        health = safe_float(latest.get('健康度评分', 0))
        grade = latest.get('等级', 'D')
        sku_count = safe_float(latest.get('SKU数', 0))
        margin = safe_float(latest.get('总毛利', 0))
        margin_rate = round(margin / gmv * 100, 1) if gmv > 0 else 0
        
        seller_data = {
            'sid': sid,
            'name': seller_name,
            'site': platform,
            'gmv': gmv,
            'rma': rma,
            'health': health,
            'grade': grade,
            'sku_count': sku_count,
            'margin': margin,
            'margin_rate': margin_rate,
            'categories': list(set(categories)),
            'months': len(hist),
        }
        results.append(seller_data)
        
        # 统计品类
        for cat in set(categories):
            category_stats[cat]["count"] += 1
            category_stats[cat]["total_gmv"] += gmv
            category_stats[cat]["sellers"].append(sid)
        
        # 统计站点
        site_stats[platform]["count"] += 1
        site_stats[platform]["total_gmv"] += gmv
        
        # 统计等级
        if grade in grade_stats:
            grade_stats[grade].append(seller_data)
    
    # 按GMV排序
    results.sort(key=lambda x: x['gmv'], reverse=True)
    
    return results, category_stats, site_stats, grade_stats

def generate_report(results, category_stats, site_stats, grade_stats):
    """生成调研报告内容"""
    total_gmv = sum(r['gmv'] for r in results)
    
    report = {
        "summary": {
            "total_sellers": len(results),
            "total_gmv": total_gmv,
            "avg_gmv": round(total_gmv / len(results), 2) if results else 0,
            "date": datetime.now().strftime("%Y-%m-%d"),
        },
        "site_distribution": site_stats,
        "grade_distribution": {k: len(v) for k, v in grade_stats.items()},
        "top_sellers": results[:10],
        "bottom_sellers": results[-10:],
        "category_analysis": sorted(category_stats.items(), key=lambda x: x[1]["total_gmv"], reverse=True)[:10],
        "insights": generate_insights(results, category_stats, site_stats, grade_stats),
    }
    
    return report

def generate_insights(results, category_stats, site_stats, grade_stats):
    """生成洞察分析"""
    insights = []
    total_gmv = sum(r['gmv'] for r in results)
    
    # 站点分布洞察
    b2c_count = site_stats["B2C"]["count"]
    ca_count = site_stats["CA"]["count"]
    b2b_count = site_stats["B2B"]["count"]
    
    if b2c_count > ca_count * 3:
        insights.append(f"B2C站点卖家数量是CA的{b2c_count//ca_count}倍，CA站点有较大增长空间")
    
    # 等级分布洞察
    a_count = len(grade_stats.get("A", []))
    d_count = len(grade_stats.get("D", []))
    
    if d_count > len(results) * 0.7:
        insights.append(f"D级卖家占比{d_count/len(results)*100:.0f}%，需要重点关注运营支持")
    
    # GMV分布洞察
    top10_gmv = sum(r['gmv'] for r in results[:10])
    if top10_gmv > total_gmv * 0.5:
        insights.append(f"Top10卖家贡献了{top10_gmv/total_gmv*100:.0f}%的GMV，头部效应明显")
    
    # 品类洞察
    if category_stats:
        top_category = max(category_stats.items(), key=lambda x: x[1]["total_gmv"])
        insights.append(f"最热销品类是{top_category[0]}，总GMV ${top_category[1]['total_gmv']:,.0f}")
    
    return insights

def main():
    print("正在分析77个seller数据...")
    results, category_stats, site_stats, grade_stats = analyze_all_sellers()
    
    print(f"分析完成：{len(results)}个seller")
    print(f"总GMV: ${sum(r['gmv'] for r in results):,.0f}")
    
    # 生成报告
    report = generate_report(results, category_stats, site_stats, grade_stats)
    
    # 保存报告数据
    with open('data/seller_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("报告数据已保存到 data/seller_analysis_report.json")
    
    return report

if __name__ == "__main__":
    main()
