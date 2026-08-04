"""深度卖家分析 - 数据读取+指标计算+错误处理

用法：
    python analyze.py ACP1          # 分析单个卖家
    python analyze.py --list        # 列出所有卖家
    python analyze.py --group "SenyTech Global"  # 按公司分组
"""
import os
import sys
import json
import glob
from datetime import datetime

# 添加项目根目录到path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.web.data import (
    load_sku_analysis_list, load_seller_history,
    load_all_seller_ids, load_all_seller_history,
    calc_dynamic_benchmarks, calc_benchmark_with_industry,
)
from src.web.seller_analysis import (
    merge_and_generate, calc_seller_health_from_sku,
    safe_float, safe_int,
)
from src.config.settings import INDUSTRY_BENCHMARKS


# ══════════════════════════════════════════════════════════
#  数据读取
# ══════════════════════════════════════════════════════════

def load_seller_data(seller_id):
    """读取卖家所有月份的SKU分析数据"""
    batches = load_sku_analysis_list(seller_id)
    if not batches:
        return None, "没有数据，请先上传BI+BSD数据"
    return batches, None


def load_seller_hist(seller_id):
    """读取卖家历史记录"""
    return load_seller_history(seller_id)


# ══════════════════════════════════════════════════════════
#  环比计算
# ══════════════════════════════════════════════════════════

def calc_mom_change(current, previous):
    """计算月环比"""
    curr_summary = current.get("seller_summary", {})
    prev_summary = previous.get("seller_summary", {})
    
    gmv_curr = safe_float(curr_summary.get("GMV", 0))
    gmv_prev = safe_float(prev_summary.get("GMV", 0))
    rma_curr = safe_float(curr_summary.get("RMA%", 0))
    rma_prev = safe_float(prev_summary.get("RMA%", 0))
    margin_curr = safe_float(curr_summary.get("总毛利", 0))
    margin_prev = safe_float(prev_summary.get("总毛利", 0))
    
    gmv_change = None
    if gmv_prev > 0:
        gmv_change = round((gmv_curr - gmv_prev) / gmv_prev * 100, 1)
    
    margin_change = None
    if margin_prev > 0:
        margin_change = round((margin_curr - margin_prev) / margin_prev * 100, 1)
    
    return {
        "gmv_change_pct": gmv_change,
        "rma_change_pp": round((rma_curr - rma_prev) * 100, 2),
        "margin_change_pct": margin_change,
        "periods": f"{previous.get('date_readable', '?')} → {current.get('date_readable', '?')}",
        "prev_gmv": gmv_prev,
        "prev_rma": rma_prev,
    }


# ══════════════════════════════════════════════════════════
#  分层分析
# ══════════════════════════════════════════════════════════

def analyze_by_fulfillment(records):
    """按履约方式分层分析"""
    sbs = [r for r in records if "seller" in str(r.get("FulfillmentType", "")).lower()]
    sbn = [r for r in records if "newegg" in str(r.get("FulfillmentType", "")).lower()]
    
    def summarize(skus, label):
        if not skus:
            return {"label": label, "count": 0, "gmv": 0, "rma": 0, "inventory": 0}
        gmv = sum(safe_float(r.get("GMV", 0)) for r in skus)
        rma_vals = [abs(safe_float(r.get("RMA %", 0))) for r in skus if safe_float(r.get("GMV", 0)) > 0]
        avg_rma = sum(rma_vals) / len(rma_vals) if rma_vals else 0
        inv = sum(safe_int(r.get("Inventory", 0)) for r in skus)
        return {"label": label, "count": len(skus), "gmv": round(gmv, 2), "rma": round(avg_rma, 2), "inventory": inv}
    
    return summarize(sbs, "SBS"), summarize(sbn, "SBN")


def analyze_by_category(records):
    """按品类分析"""
    cat_map = {}
    for r in records:
        cat = r.get("品类", "其他")
        if cat not in cat_map:
            cat_map[cat] = []
        cat_map[cat].append(r)
    
    total_gmv = sum(safe_float(r.get("GMV", 0)) for r in records)
    result = []
    for cat, skus in sorted(cat_map.items(), key=lambda x: sum(safe_float(r.get("GMV", 0)) for r in x[1]), reverse=True):
        gmv = sum(safe_float(r.get("GMV", 0)) for r in skus)
        margin = sum(safe_float(r.get("Total Margin (without EIMS)", 0)) for r in skus)
        margin_rate = round(margin / gmv * 100, 1) if gmv > 0 else 0
        share = round(gmv / total_gmv * 100, 1) if total_gmv > 0 else 0
        result.append({
            "category": cat,
            "sku_count": len(skus),
            "gmv": round(gmv, 2),
            "gmv_share": share,
            "margin_rate": margin_rate,
        })
    return result


def find_problem_skus(records, top_n=10):
    """找出问题SKU（高退货/零销/积压）"""
    problems = []
    for r in records:
        gmv = safe_float(r.get("GMV", 0))
        rma = abs(safe_float(r.get("RMA %", 0)))
        inv = safe_int(r.get("Inventory", 0))
        qty = safe_int(r.get("Net Quantity Sold", 0))
        
        issues = []
        if rma > 10:
            issues.append("高退货率")
        if qty == 0 and gmv == 0:
            issues.append("零销售")
        if inv > 100 and qty < 3:
            issues.append("库存积压")
        if gmv < 0:
            issues.append("负GMV")
        
        if issues:
            problems.append({
                "sku": r.get("NeweggItemNumber", ""),
                "desc": str(r.get("Item Description", ""))[:50],
                "gmv": round(gmv, 2),
                "rma": round(rma, 2),
                "inventory": inv,
                "qty_sold": qty,
                "issues": issues,
                "priority_score": safe_float(r.get("整改优先级得分", 0)),
            })
    
    problems.sort(key=lambda x: x["priority_score"], reverse=True)
    return problems[:top_n]


# ══════════════════════════════════════════════════════════
#  站点检测
# ══════════════════════════════════════════════════════════

def detect_site(seller_id, records):
    """检测站点类型"""
    # 根据WarehouseLocation判断
    for r in records:
        # 优先用Platform字段（最准确）
        platform = str(r.get("Platform", "")).lower()
        if "ca" in platform or "canada" in platform:
            return "CA"
        if "business" in platform or "b2b" in platform:
            return "B2B"
        # 降级用WarehouseLocation
        loc = str(r.get("WarehouseLocation", "")).lower()
        if "canada" in loc:
            return "CA"
        if "business" in loc or "b2b" in loc:
            return "B2B"
    return "B2C"


def find_cross_site_sellers(seller_id, all_history):
    """查找同公司其他站点（基于seller_id前缀匹配）"""
    # 简单方案：找同前缀的seller_id
    prefix = seller_id[:3] if len(seller_id) >= 3 else seller_id
    cross_site = []
    for sid in all_history:
        if sid != seller_id and sid.startswith(prefix):
            latest = all_history[sid][-1] if all_history[sid] else {}
            cross_site.append({
                "seller_id": sid,
                "gmv": safe_float(latest.get("GMV", 0)),
                "grade": latest.get("等级", "?"),
            })
    return cross_site


# ══════════════════════════════════════════════════════════
#  行业基准
# ══════════════════════════════════════════════════════════

def get_industry_rating(metric, value):
    """根据行业基准返回评价"""
    benchmarks = INDUSTRY_BENCHMARKS.get(metric, {})
    value = abs(value) if isinstance(value, (int, float)) else 0
    
    if metric == "RMA%":
        if value < 3: return "优秀"
        if value < 5: return "良好"
        if value < 8: return "一般"
        return "较差"
    elif metric == "毛利率%":
        if value > 15: return "优秀"
        if value > 10: return "良好"
        if value > 5: return "一般"
        return "较差"
    elif metric == "GMV":
        if value > 50000: return "优秀"
        if value > 20000: return "良好"
        if value > 5000: return "一般"
        return "较差"
    return "-"


# ══════════════════════════════════════════════════════════
#  主分析入口
# ══════════════════════════════════════════════════════════

def safe_analyze(seller_id):
    """安全分析入口，带完整错误处理"""
    # 1. 检查卖家是否存在
    batches, err = load_seller_data(seller_id)
    if err:
        return {"error": err, "seller_id": seller_id}
    
    # 2. 检查数据完整性
    latest = batches[0]
    if "seller_summary" not in latest:
        return {"error": "数据格式错误：缺少 seller_summary 字段", "seller_id": seller_id}
    records = latest.get("records", [])
    if not records:
        return {"error": "没有SKU明细数据", "seller_id": seller_id}
    
    # 3. 检查关键字段
    summary = latest["seller_summary"]
    required_fields = ["GMV", "RMA%", "健康度评分", "等级"]
    missing = [f for f in required_fields if f not in summary]
    if missing:
        return {"error": f"数据缺少字段：{', '.join(missing)}", "seller_id": seller_id}
    
    # 4. 计算月环比
    mom_change = None
    if len(batches) >= 2:
        mom_change = calc_mom_change(batches[0], batches[1])
    
    # 5. 站点检测
    site = detect_site(seller_id, records)
    
    # 6. 分层分析
    sbs, sbn = analyze_by_fulfillment(records)
    categories = analyze_by_category(records)
    problem_skus = find_problem_skus(records)
    
    # 7. 行业基准评价
    gmv = safe_float(summary.get("GMV", 0))
    rma = abs(safe_float(summary.get("RMA%", 0)))
    margin = safe_float(summary.get("总毛利", 0))
    margin_rate = round(margin / gmv * 100, 1) if gmv > 0 else 0
    
    # 8. 汇总结果
    result = {
        "seller_id": seller_id,
        "site": site,
        "date_period": latest.get("date_period", ""),
        "date_readable": latest.get("date_readable", ""),
        "total_months": len(batches),
        "batches": batches,
        "summary": {
            "health_score": safe_float(summary.get("健康度评分", 0)),
            "grade": summary.get("等级", "D"),
            "gmv": gmv,
            "gmv_rating": get_industry_rating("GMV", gmv),
            "rma_pct": rma,
            "rma_rating": get_industry_rating("RMA%", rma),
            "total_margin": margin,
            "margin_rate": margin_rate,
            "margin_rating": get_industry_rating("毛利率%", margin_rate),
            "total_qty": safe_int(summary.get("总销量", 0)),
            "sku_count": safe_int(summary.get("SKU数", 0)),
        },
        "mom_change": mom_change,
        "fulfillment": {"sbs": sbs, "sbn": sbn},
        "categories": categories,
        "problem_skus": problem_skus,
        "all_records": len(records),
    }
    
    return result


# ══════════════════════════════════════════════════════════
#  列出所有卖家
# ══════════════════════════════════════════════════════════

def list_all_sellers():
    """列出所有卖家ID和基本信息"""
    all_ids = load_all_seller_ids()
    all_hist = load_all_seller_history()
    
    result = []
    for sid in all_ids:
        hist = all_hist.get(sid, [])
        if hist:
            latest = hist[-1]
            result.append({
                "seller_id": sid,
                "health_score": safe_float(latest.get("健康度评分", 0)),
                "grade": latest.get("等级", "D"),
                "gmv": safe_float(latest.get("GMV", 0)),
                "months": len(hist),
            })
    
    result.sort(key=lambda x: x["health_score"], reverse=True)
    return result


# ══════════════════════════════════════════════════════════
#  CLI入口
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze.py <seller_id> | --list")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == "--list":
        sellers = list_all_sellers()
        print(json.dumps(sellers, ensure_ascii=False, indent=2))
    else:
        result = safe_analyze(arg)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
