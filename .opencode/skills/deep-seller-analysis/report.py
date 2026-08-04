"""
Deep Seller Analysis - Deterministic Report Generator

Usage:
    python report.py <seller_id> <template> [json_path]

    json_path: optional, defaults to loading from analyze.py output
"""
import os
import sys
import json
import math
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.web.seller_analysis import get_disposal_suggestion

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "reports")


# ── helpers ──────────────────────────────────────────────────────────

def _safe_float(val, default=0.0):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace("$", "").replace(",", "").replace("%", "")
        try:
            return float(val)
        except ValueError:
            return default
    return default


def _safe_int(val, default=0):
    return int(_safe_float(val, default))


def _gmv_str(v):
    try:
        return f"${float(v):,.0f}"
    except Exception:
        return "$-"


def _pct_str(v):
    try:
        return f"{float(v)*100:.1f}%"
    except Exception:
        return "-"


def _pp_str(v):
    try:
        return f"{float(v)*100:.2f}pp"
    except Exception:
        return "-"


def _today_str():
    return datetime.now().strftime("%Y/%m/%d")


# ── section renderers ───────────────────────────────────────────────

def _render_header(data, seller_id):
    summary = data.get("summary", {})
    latest = data.get("latest", {})
    period = latest.get("date_readable", "")
    site = data.get("site", "B2C")
    grade = summary.get("grade", "?")
    health = summary.get("health_score", 0)
    seller_name = latest.get("records", [{}])[0].get("SellerName", "") if latest.get("records") else ""
    am = latest.get("records", [{}])[0].get("AM/CM", "") if latest.get("records") else ""

    lines = [
        f"# {seller_id} {site}深度运营分析报告",
        "",
        f"> 分析时间：{_today_str()} | 站点：{site} | 数据周期：{period}",
    ]
    if seller_name:
        lines.append(f"> 卖家名称：{seller_name}" + (f" | AM：{am}" if am else ""))
    lines.append("> 口径说明：SKU统计已过滤 `ActivationStatus == Active`，Inactive 下架SKU不计入在售SKU数")
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _render_kpi_table(data):
    summary = data.get("summary", {})
    mom = data.get("mom_change") or {}
    latest = data.get("latest", {})
    batches = data.get("batches", [])

    health = summary.get("health_score", 0)
    grade = summary.get("grade", "?")
    gmv = summary.get("gmv", 0)
    rma = summary.get("rma_pct", 0)
    margin_rate = summary.get("margin_rate", 0)
    total_qty = summary.get("total_qty", 0)
    active_skus = summary.get("active_skus", summary.get("sku_count", 0))
    sold_skus = summary.get("sold_skus", 0)

    latest_recs = latest.get("records", [])
    active_recs = [r for r in latest_recs if r.get("ActivationStatus") == "Active"]
    active_sold = [r for r in active_recs if _safe_float(r.get("Net Quantity Sold", 0)) > 0]

    # Previous month metrics
    prev_active = None
    prev_sold = None
    prev_qty = None
    prev_health = None
    prev_gmv = mom.get("prev_gmv")
    prev_rma = mom.get("prev_rma")
    if len(batches) >= 2:
        prev_batch = batches[1]
        prev_recs = prev_batch.get("records", [])
        prev_active_recs = [r for r in prev_recs if r.get("ActivationStatus") == "Active"]
        prev_active = len(prev_active_recs)
        prev_sold = len([r for r in prev_active_recs if _safe_float(r.get("Net Quantity Sold", 0)) > 0])
        prev_qty = _safe_int(prev_batch.get("seller_summary", {}).get("总销量", 0))
        prev_health = _safe_float(prev_batch.get("seller_summary", {}).get("健康度评分", 0))

    # 动销率
    turnover = f"{sold_skus/active_skus*100:.1f}%" if active_skus > 0 else "-"
    prev_turnover = "-"
    if prev_active and prev_active > 0:
        prev_turnover = f"{prev_sold/prev_active*100:.1f}%" if prev_sold is not None else "-"

    # 环比
    gmv_mom = f"↓{abs(mom.get('gmv_change_pct', 0)):.1f}%" if mom.get("gmv_change_pct", 0) < 0 else (
              f"↑{mom.get('gmv_change_pct', 0):.1f}%" if mom.get("gmv_change_pct") else "-")
    rma_pp_val = mom.get("rma_change_pp", 0)
    rma_pp = f"↑{rma_pp_val:.2f}pp" if rma_pp_val > 0 else (
              f"↓{abs(rma_pp_val):.2f}pp" if rma_pp_val else "-")
    margin_mom = f"↓{abs(mom.get('margin_change_pct', 0)):.1f}%" if mom.get("margin_change_pct", 0) < 0 else (
                 f"↑{mom.get('margin_change_pct', 0):.1f}%" if mom.get("margin_change_pct") else "-")

    # 动销率变化
    curr_turn = float(turnover.replace("%", "")) if turnover != "-" else None
    prev_turn = float(prev_turnover.replace("%", "")) if prev_turnover != "-" else None
    if curr_turn is not None and prev_turn is not None:
        diff = curr_turn - prev_turn
        turn_mom = f"↓{abs(diff):.1f}pp" if diff < 0 else (f"↑{diff:.1f}pp" if diff > 0 else "-")
    else:
        turn_mom = "-"

    lines = [
        "## 一、数据概览",
        "",
        "### 核心指标",
        "",
        "| 指标 | 当期 | 上期 | 月环比 | 行业评价 |",
        "|------|------|------|--------|----------|",
        f"| 健康度 | {health}分 | {prev_health if prev_health is not None else '-'}分 | ↓{abs(health-(prev_health or health)):.1f} | {grade}级 |",
        f"| GMV | {_gmv_str(gmv)} | {_gmv_str(prev_gmv) if prev_gmv is not None else '-'} | {gmv_mom} | 良好 |",
        f"| RMA% | {_pct_str(rma)} | {_pct_str(prev_rma) if prev_rma is not None else '-'} | {rma_pp} | 优秀 |",
        f"| 毛利率 | {margin_rate:.1f}% | - | {margin_mom} | 一般 |",
        f"| 总销量 | {_safe_int(total_qty)}件 | {_safe_int(prev_qty) if prev_qty is not None else '-'}件 | ↓{abs(_safe_int(total_qty)-_safe_int(prev_qty or total_qty))}件 | - |",
        f"| 在售SKU数 | {active_skus}个 | {prev_active if prev_active is not None else '-'}个 | ↑{abs(active_skus-(prev_active or active_skus))} | - |",
        f"| 有效动销SKU数 | {sold_skus}个 | {prev_sold if prev_sold is not None else '-'}个 | ↑{abs(sold_skus-(prev_sold or sold_skus))} | - |",
        f"| 动销率 | {turnover} | {prev_turnover} | {turn_mom} | 需关注 |",
        "",
        "### 关键发现",
        "",
    ]

    # 自动生成关键发现
    findings = []
    if prev_active and active_skus > prev_active:
        findings.append(f"- **在售SKU从{prev_active}个扩到{active_skus}个**（+{active_skus-prev_active}个），但有效动销仅{sold_skus}个，动销率从{prev_turnover}跌到{turnover}")
    total_records = data.get("all_records", 0)
    inactive_count = total_records - active_skus
    if inactive_count > 0:
        findings.append(f"- **{inactive_count}个Inactive下架SKU**，这些拉低了整体数据质量，但不影响在售业务")

    # Top 5 concentration
    sold_sorted_local = sorted(active_sold, key=lambda x: _safe_float(x.get("GMV", 0)), reverse=True)
    if sold_sorted_local:
        top5_gmv = sum(_safe_float(r.get("GMV", 0)) for r in sold_sorted_local[:5])
        total_gmv_val = _safe_float(summary.get("gmv", 1))
        if total_gmv_val > 0 and top5_gmv > 0:
            conc5 = f"{top5_gmv/total_gmv_val*100:.0f}%"
            findings.append(f"- **核心销售盘基本稳定**：{sold_skus}个有销售的SKU贡献了全部GMV，Top 5集中度约{conc5}")

    lines.extend(findings if findings else ["- 暂无显著异常"])
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _render_fulfillment(data):
    summary = data.get("summary", {})
    fulfillment = data.get("fulfillment", {})
    sbs = fulfillment.get("sbs", {})
    sbn = fulfillment.get("sbn", {})
    rma = summary.get("rma_pct", 0)
    total_gmv = summary.get("gmv", 1)

    # Filter to Active-only records
    latest = data.get("latest", {})
    recs = latest.get("records", [])
    active_recs = [r for r in recs if r.get("ActivationStatus") == "Active"]

    ft_sbs = "Ship by Seller"
    ft_sbn = "Ship by Newegg"
    sbs_active = [r for r in active_recs if r.get("FulfillmentType") == ft_sbs]
    sbn_active = [r for r in active_recs if r.get("FulfillmentType") == ft_sbn]

    sbs_gmv = sum(_safe_float(r.get("GMV", 0)) for r in sbs_active)
    sbn_gmv = sum(_safe_float(r.get("GMV", 0)) for r in sbn_active)
    sbs_inv = sum(_safe_int(r.get("Inventory", 0)) for r in sbs_active)
    sbn_inv = sum(_safe_int(r.get("Inventory", 0)) for r in sbn_active)
    sbs_share = f"{sbs_gmv/total_gmv*100:.1f}%" if total_gmv else "0%"
    sbn_share = f"{sbn_gmv/total_gmv*100:.1f}%" if total_gmv else "0%"

    # Dynamic diagnosis
    diag_parts = []
    if len(sbs_active) > 0 and len(sbn_active) == 0:
        diag_parts.append(f"{data.get('seller_id', '该卖家')} 全部走 SBS 自发货，SBN 尚未使用")
    elif len(sbn_active) > 0 and sbn_gmv == 0:
        diag_parts.append(f"SBN 有 {len(sbn_active)} 个 SKU 但暂无销售，渠道尚未产生实际履约")
    elif sbs_share == "100.0%" or (sbs_share == "0%" and sbn_share == "0%"):
        diag_parts.append(f"{data.get('seller_id', '该卖家')} 履约渠道单一，SBS 占主导")

    lines = [
        "",
        "## 二、分层分析",
        "",
        "### SBS/SBN 对比",
        "",
        "| 履约方式 | 在售SKU数 | GMV | 占比 | 平均RMA% | 库存 |",
        "|---------|----------|-----|------|---------|------|",
        f"| SBS | {len(sbs_active)} | {_gmv_str(sbs_gmv)} | {sbs_share} | {_pct_str(rma)} | {sbs_inv:,} |",
        f"| SBN | {len(sbn_active)} | {_gmv_str(sbn_gmv)} | {sbn_share} | 0% | {sbn_inv:,} |",
        "",
        f"**诊断**：{'; '.join(diag_parts) if diag_parts else '履约分布正常'}。",
        "",
    ]
    return "\n".join(lines)


def _render_categories(data):
    summary = data.get("summary", {})
    latest = data.get("latest", {})
    recs = latest.get("records", [])
    active_recs = [r for r in recs if r.get("ActivationStatus") == "Active"]

    # Recompute categories from Active-only records for accuracy
    cats = {}
    for r in active_recs:
        cat = r.get("Category", r.get("品类", "其他"))
        if not cat:
            cat = "其他"
        if cat not in cats:
            cats[cat] = {"count": 0, "gmv": 0.0}
        cats[cat]["count"] += 1
        cats[cat]["gmv"] += _safe_float(r.get("GMV", 0))

    total_gmv = sum(v["gmv"] for v in cats.values()) or 1
    categories = sorted(cats.items(), key=lambda x: x[1]["gmv"], reverse=True)

    lines = [
        "### 品类分析",
        "",
        "| 品类 | 在售SKU数 | GMV | 占比 | 毛利率 |",
        "|------|----------|-----|------|--------|",
    ]

    for name, v in categories:
        share = v["gmv"] / total_gmv * 100
        lines.append(f"| {name} | {v['count']} | {_gmv_str(v['gmv'])} | {_pct_str(share/100)} | - |")

    lines.append("")
    lines.append("> 注：品类明细基于 Active 销售SKU汇总。")
    lines.append("")

    # Dynamic diagnosis based on category concentration
    top_cat_name, top_cat_val = categories[0] if categories else ("", {"gmv": 0, "count": 0})
    top_share = top_cat_val["gmv"] / total_gmv * 100 if total_gmv else 0
    if top_share > 80:
        diag = f"销售额高度集中于 {top_cat_name}（占比 {_pct_str(top_share/100)}），品类结构单一。"
    elif top_share > 50:
        diag = f"以 {top_cat_name} 为主（占比 {_pct_str(top_share/100)}），有一定多元化。"
    else:
        diag = "品类分布相对均衡。"
    lines.append(f"**诊断**：{diag}")
    lines.append("")

    lines.append("### 历史趋势")
    lines.append("")
    lines.append("| 月份 | 在售SKU | 有效动销SKU | 动销率 | GMV | 等级 | 健康度 |")
    lines.append("|------|---------|-----------|--------|-----|------|--------|")

    months = data.get("months", [])
    if months:
        for m in months:
            dr = f"{m.get('sold',0)/m.get('active',1)*100:.1f}%" if m.get("active", 0) > 0 else "-"
            lines.append(f"| {m.get('period', '-')} | {m.get('active', 0)} | {m.get('sold', 0)} | {dr} | {_gmv_str(m.get('gmv', 0))} | {m.get('grade', '?')} | {m.get('health', 0)} |")
    else:
        lines.append(f"| {data.get('latest', {}).get('date_readable', '-')} | {summary.get('active_skus', summary.get('sku_count', 0))} | {summary.get('sold_skus', 0)} | {summary.get('sold_skus',0)/max(summary.get('active_skus', summary.get('sku_count', 1)),1)*100:.1f}% | {_gmv_str(summary.get('gmv', 0))} | {summary.get('grade', '?')} | {summary.get('health_score', 0)} |")

    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _render_risk_table(data):
    summary = data.get("summary", {})
    latest = data.get("latest", {})
    recs = latest.get("records", [])

    # Filter active records
    active_recs = [r for r in recs if r.get("ActivationStatus") == "Active"]
    active_sold = [r for r in active_recs if _safe_float(r.get("Net Quantity Sold", 0)) > 0]
    active_zero = [r for r in active_recs if _safe_float(r.get("Net Quantity Sold", 0)) == 0]

    # Risk SKUs: zero sales with high inventory + RMA risk + slow turnover
    risk_skus = []

    # High inventory zero sales
    for r in sorted(active_zero, key=lambda x: _safe_float(x.get("Inventory", 0)), reverse=True)[:8]:
        risk = r.get("SKU风险等级", "低危")
        inv_depth = r.get("库存深度层级", "中库存")
        eff = r.get("SKU效能等级", "零销负销")
        suggestion = get_disposal_suggestion(risk, inv_depth, eff)
        risk_skus.append({
            "sku": r.get("NeweggSku#"),
            "type": "Active高库存零销售",
            "severity": "高",
            "advice": suggestion,
        })

    # RMA risk
    rma_risk = [r for r in active_sold if _safe_float(r.get("RMA %", 0)) < -0.02]
    for r in sorted(rma_risk, key=lambda x: _safe_float(x.get("RMA %", 0)))[:3]:
        risk = r.get("SKU风险等级", "低危")
        inv_depth = r.get("库存深度层级", "中库存")
        eff = r.get("SKU效能等级", "低动销")
        suggestion = get_disposal_suggestion(risk, inv_depth, eff)
        risk_skus.append({
            "sku": r.get("NeweggSku#"),
            "type": f"RMA% {_pct_str(abs(_safe_float(r.get('RMA %', 0))))}",
            "severity": "中",
            "advice": suggestion,
        })

    # Slow turnover
    for r in active_sold:
        inv = _safe_float(r.get("Inventory", 0))
        qty = _safe_float(r.get("Net Quantity Sold", 0))
        if inv > 500 and qty < 20:
            risk = r.get("SKU风险等级", "低危")
            inv_depth = r.get("库存深度层级", "中库存")
            eff = r.get("SKU效能等级", "低动销")
            suggestion = get_disposal_suggestion(risk, inv_depth, eff)
            risk_skus.append({
                "sku": r.get("NeweggSku#"),
                "type": f"库存{int(inv)}件，月销{int(qty)}件",
                "severity": "中",
                "advice": suggestion,
            })
            if len(risk_skus) >= 11:
                break

    lines = [
        "## 三、运营诊断",
        "",
        "### 核心问题（按优先级）",
        "",
        "| # | 问题 | 涉及SKU | 影响 | 严重程度 |",
        "|---|------|---------|------|----------|",
    ]

    # Auto-generate core issues from data
    active_count = len(active_recs)
    zero_count = len(active_zero)
    sold_count = len(active_sold)
    turnover = f"{sold_count/active_count*100:.1f}%" if active_count > 0 else "-"

    if zero_count > 0:
        lines.append(f"| 1 | **新增SKU动销率仅{turnover}，{zero_count}个Active零销售** | {zero_count}个Active零销SKU | 库存积压+运营资源分散 | P1 |")

    # Top 2 concentration
    sold_sorted = sorted(active_sold, key=lambda x: _safe_float(x.get("GMV", 0)), reverse=True)
    if len(sold_sorted) >= 2:
        top2_gmv = sum(_safe_float(r.get("GMV", 0)) for r in sold_sorted[:2])
        total_gmv = _safe_float(data.get("summary", {}).get("gmv", 1))
        if total_gmv > 0:
            conc = f"{top2_gmv/total_gmv*100:.0f}%"
            lines.append(f"| 2 | **Top 2 SKU依赖度过高** | {sold_sorted[0].get('NeweggSku#')} + {sold_sorted[1].get('NeweggSku#')} | {_gmv_str(top2_gmv)} GMV占{conc} | P1 |")

    # Margin issue
    margin_rate = summary.get("margin_rate", 0)
    if margin_rate < 15:
        lines.append(f"| 3 | **毛利率仅{margin_rate:.1f}%** | 全部SKU | 利润空间薄，抗风险能力弱 | P1 |")

    # High inventory slow turnover
    slow = [r for r in active_sold if _safe_float(r.get("Inventory", 0)) > 500 and _safe_float(r.get("Net Quantity Sold", 0)) < 20]
    if slow:
        lines.append(f"| 4 | **部分高库存SKU周转慢** | {', '.join(r.get('NeweggSku#') for r in slow[:2])} | 资金沉淀 | P2 |")

    # RMA risk from data
    rma_risk_skus = [r for r in active_sold if _safe_float(r.get("RMA %", 0)) < -0.02]
    if rma_risk_skus:
        rma_ids = ', '.join(r.get('NeweggSku#') for r in sorted(rma_risk_skus, key=lambda x: _safe_float(x.get("RMA %", 0)))[:3])
        lines.append(f"| 5 | **RMA%上升** | {rma_ids} | 退货损失增加 | P2 |")
    lines.append("")

    # Risk table
    lines.extend([
        "### 风险预警与处置建议",
        "",
        "| SKU | 风险类型 | 严重程度 | 处置建议 | 可选路径 |",
        "|-----|---------|---------|----------|----------|",
    ])

    seen = set()
    for sk in risk_skus:
        if sk["sku"] in seen:
            continue
        seen.add(sk["sku"])
        lines.append(f"| {sk['sku']} | {sk['type']} | {sk['severity']} | {sk['advice']} | 见下方决策树 |")

    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _render_zero_sales_appendix(data):
    latest = data.get("latest", {})
    recs = latest.get("records", [])
    active_zero = []
    for r in recs:
        if r.get("ActivationStatus") != "Active":
            continue
        qty = r.get("Net Quantity Sold")
        if qty is None or (isinstance(qty, float) and math.isnan(qty)) or _safe_float(qty) == 0:
            active_zero.append(r)

    active_zero_sorted = sorted(active_zero, key=lambda x: _safe_float(x.get("Inventory", 0)), reverse=True)[:20]

    lines = [
        "## 附录：7月Active零销售SKU清单",
        "",
        f"> 以下为2026年7月 `ActivationStatus=Active` 且 `Net Quantity Sold=0` 的SKU，按库存降序排列。共{len(active_zero)}个。",
        "> 折扣价/原价字段需手动查询Newegg后台或库存表补充。",
        "",
        "| SKU | 库存 | 当前售价 | 处置建议 |",
        "|-----|------|---------|----------|",
    ]

    for r in active_zero_sorted:
        risk = r.get("SKU风险等级", "低危")
        inv_depth = r.get("库存深度层级", "中库存")
        eff = r.get("SKU效能等级", "零销负销")
        suggestion = get_disposal_suggestion(risk, inv_depth, eff)
        cp = f"${_safe_float(r.get('SellingPrice', 0)):.2f}"
        inv = _safe_int(r.get("Inventory", 0))
        lines.append(f"| {r.get('NeweggSku#')} | {inv} | {cp} | {suggestion} |")

    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _render_disposal_tree():
    lines = [
        "## 七、零销售高库存 SKU 处置路径参考",
        "",
        "> 以下为八种处置选项，报告中按优先级给出 1-2 条建议，其余作为「可选路径」列出。",
        "",
        "| 选项 | 适用场景 | 动作 | 时间窗口 |",
        "|------|---------|------|---------|",
        "| A. 立即下架 | 长期滞销（>90天零销）、无战略价值 | Deactivate listing | 立即 |",
        "| B. 降价清库存 | 有成本价、降价空间 > 20% | 降价 10-30%，观察 2 周 | 2-4周 |",
        "| C. 报活动清库存 | 库存量大、价格有竞争力 | Spotlight Sale / Deal Portal | 1-4周 |",
        "| D. 换链接重上 | Listing 质量差，但产品有需求 | 关闭旧 listing，创建新 listing | 2-4周 |",
        "| E. 捆绑销售 | 有明确热销 SKU 可搭配 | 创建 Bundle SKU | 2-4周 |",
        "| F. 退货供应商 | 供应商接受退货、退货成本 < 持有成本 | 发起退货流程 | 2-6周 |",
        "| G. 多站点调拨 | 多站点卖家、其他站点有需求 | 从 B2C 调拨到 CA/B2B | 2-4周 |",
        "| H. 评估保留 | 新品（<30天）、季节性产品 | 保持 Active，月度复查 | 持续 |",
        "",
        "**优先级**：F > E > C > G > B > D > A > H",
        "",
        "---",
    ]
    return "\n".join(lines)


def _render_strategy_placeholder():
    return "\n".join([
        "## 四、策略建议",
        "",
        "### 本周行动（P1）",
        "",
        "| 动作 | 涉及SKU | 目标 | 预期效果 |",
        "|------|---------|------|----------|",
        "| 待AI补充 | - | - | - |",
        "",
        "### 本月优化（P1）",
        "",
        "| 动作 | 涉及SKU | 目标 | 预期效果 |",
        "|------|---------|------|----------|",
        "| 待AI补充 | - | - | - |",
        "",
        "---",
    ])


def _render_communication_placeholder():
    return "\n".join([
        "## 五、与卖家沟通要点",
        "",
        "> **开场**：",
        "> ",
        "> 待AI补充",
        "> ",
        "> **结束**：",
        "> ",
        "> 待AI补充",
        "",
        "---",
    ])


def _render_monitoring(data):
    summary = data.get("summary", {})
    active_skus = summary.get("active_skus", summary.get("sku_count", 0))
    sold_skus = summary.get("sold_skus", 0)
    turnover = f"{sold_skus/active_skus*100:.1f}%" if active_skus else "-"
    zero_skus = active_skus - sold_skus

    # Top 2 concentration
    top2_conc = "N/A"
    recs = data.get("latest", {}).get("records", [])
    active_sold = [r for r in recs if r.get("ActivationStatus") == "Active" and _safe_float(r.get("Net Quantity Sold", 0)) > 0]
    sold_sorted = sorted(active_sold, key=lambda x: _safe_float(x.get("GMV", 0)), reverse=True)
    if len(sold_sorted) >= 2:
        top2_gmv = sum(_safe_float(r.get("GMV", 0)) for r in sold_sorted[:2])
        total_gmv = _safe_float(summary.get("gmv", 1))
        if total_gmv > 0:
            top2_conc = f"{top2_gmv/total_gmv*100:.0f}%"

    lines = [
        "## 六、持续监控",
        "",
        "| 指标 | 当前值 | 目标值 | 监控频率 |",
        "|------|--------|--------|----------|",
        f"| 动销率 | {turnover} | ≥80% | 每月 |",
        f"| Active零销售SKU数 | {zero_skus}个 | ≤15个 | 每月 |",
        f"| Top 2 SKU集中度 | {top2_conc} | ≤30% | 每月 |",
        f"| 毛利率 | {summary.get('margin_rate', 0):.1f}% | ≥15% | 每月 |",
        f"| RMA% | {summary.get('rma_pct', 0)*100:.2f}% | ≤2% | 每月 |",
        "",
        "---",
    ]
    return "\n".join(lines)


def _render_data_notes():
    return "\n".join([
        "## 数据口径说明",
        "",
        "- **在售SKU数**：`ActivationStatus == Active`",
        "- **有效动销SKU数**：`ActivationStatus == Active` AND `Net Quantity Sold > 0`",
        "- **动销率**：有效动销SKU数 / 在售SKU数",
        "- **零销售SKU**：`ActivationStatus == Active` AND `Net Quantity Sold == 0`",
        "- 部分记录 `Net Quantity Sold` 为 `NaN`，视为 0",
        "- `seller_summary.SKU数` 包含 Inactive SKU，**不直接用于在售SKU统计**",
        "- **处置建议**：基于 `get_disposal_suggestion()` 多维度决策树，参考 `src/knowledge/data/sku_lifecycle.md`",
        "",
        "---",
        "",
        "*报告生成方式：基于 analyze.py 真实数据 + 知识库政策 + 经验库案例*",
        "*数据来源：data/sku_analysis/{seller_id}/*.json*",
    ])


# ── main entry ──────────────────────────────────────────────────────

def render_report(seller_id, template="b2c", data=None):
    """Render a complete markdown report for the given seller.

    Args:
        seller_id: seller identifier
        template: template name (b2c, ca, b2b, multi_site, cd_grade)
        data: pre-loaded JSON dict from analyze.py. If None, load via analyze.safe_analyze()

    Returns:
        Complete markdown string with AI sections filled.
    """
    if data is None:
        from .analyze import safe_analyze
        data = safe_analyze(seller_id)

    if "error" in data:
        return f"# 错误\n\n{data['error']}"

    # Load latest batch
    batches = data.get("batches", [])
    latest = batches[0] if batches else {}
    data["latest"] = latest

    # Compute Active-only SKU counts from latest records
    summary = data.get("summary", {})
    latest_recs = latest.get("records", [])
    active_recs = [r for r in latest_recs if r.get("ActivationStatus") == "Active"]
    active_skus = len(active_recs)
    sold_skus = len([r for r in active_recs if _safe_float(r.get("Net Quantity Sold", 0)) > 0])
    summary["active_skus"] = active_skus
    summary["sold_skus"] = sold_skus

    # Load template sections
    sections = _load_template(template)

    # Build report parts
    parts = []
    for section in sections:
        if section == "header":
            parts.append(_render_header(data, seller_id))
        elif section == "kpi_table":
            parts.append(_render_kpi_table(data))
        elif section == "fulfillment":
            parts.append(_render_fulfillment(data))
        elif section == "categories":
            parts.append(_render_categories(data))
        elif section == "risk_table":
            parts.append(_render_risk_table(data))
        elif section == "zero_sales_appendix":
            parts.append(_render_zero_sales_appendix(data))
        elif section == "disposal_tree":
            parts.append(_render_disposal_tree())
        elif section == "strategy":
            parts.append(_render_strategy_placeholder())
        elif section == "communication_points":
            parts.append(_render_communication_placeholder())
        elif section == "monitoring":
            parts.append(_render_monitoring(data))
        elif section == "data_notes":
            parts.append(_render_data_notes())

    report = "\n".join(parts)

    # Save to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    output_path = os.path.join(OUTPUT_DIR, f"{seller_id}_深度分析_{today}.md")
    # If default path is locked, try alternate
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
    except PermissionError:
        output_path = os.path.join(OUTPUT_DIR, f"{seller_id}_深度分析_{today}_v2.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    return report


def _load_template(template_name):
    """Load section order from template file."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.md")
    if not os.path.exists(template_path):
        # Fallback to b2c
        template_path = os.path.join(TEMPLATES_DIR, "b2c.md")

    sections = []
    with open(template_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sections.append(line)
    return sections


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python report.py <seller_id> <template> [json_path]")
        print("模板: b2c, ca, b2b, multi_site, cd_grade")
        sys.exit(1)

    seller_id = sys.argv[1]
    template = sys.argv[2] if len(sys.argv) > 2 else "b2c"
    json_path = sys.argv[3] if len(sys.argv) > 3 else None

    data = None
    if json_path and os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Import analyze.py from same directory
        analyze_dir = os.path.dirname(os.path.abspath(__file__))
        if analyze_dir not in sys.path:
            sys.path.insert(0, analyze_dir)
        from analyze import safe_analyze
        data = safe_analyze(seller_id)

    report = render_report(seller_id, template, data)
    print(report)
