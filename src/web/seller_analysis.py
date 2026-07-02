import math
import os, re
import numpy as np
import pandas as pd
from datetime import datetime

from src.web.config import RMA_RULES, GRADE_RULES

# ── 品类关键词映射 ──
CATEGORY_MAP = {
    "CASE FAN": "机箱风扇", "EXTSSD": "固态硬盘", "SSD": "固态硬盘",
    "VGA": "显卡", "MB": "主板", "CPU": "处理器",
    "LQCL": "水冷散热", "CASE": "机箱", "PSU": "电源",
    "CH": "电脑配件", "GMS": "外设", "GKB": "外设", "GM": "外设",
}
CATEGORY_ORDER = ["CASE FAN", "EXTSSD", "SSD", "VGA", "MB", "CPU", "LQCL", "CASE", "PSU", "CH", "GMS", "GKB", "GM"]

# 补充显卡/处理器型号关键词，避免被 "CH" 等前缀误匹配
VGA_KEYWORDS = ["RTX", "GTX", "RX 6", "RX 7", "7900", "7800", "7700", "7600",
                "6900", "6800", "6700", "6600", "4090", "4080", "4070", "4060",
                "3090", "3080", "3070", "3060", "RADEON", "GEFORCE"]
CPU_KEYWORDS = ["RYZEN", "THREADRIPPER", "EPYC", "XEON", "CORE I", "CORE ULTRA"]
# CASE 型号关键词，避免被 "CH" 前缀误匹配
CASE_KEYWORDS = ["HAF", "NZXT", "PHANTEKS", "FRactal", "CORSAIR 4", "CORSAIR 5",
                 "CORSAIR 7", "O11", "H510", "H710", "H7Flow", "GT301", "GT501"]

# ── 品牌关键词 ──
BRAND_KEYWORDS = [
    "MSI", "ASUS", "Noctua", "SAPPHIRE", "ASRock", "GIGABYTE",
    "AMD", "INTEL", "CornE", "CORSAIR", "Cooler Master", "DEEPCOOL",
    "NZXT", "Thermaltake", "EVGA", "ZOTAC", "XFX", "PowerColor",
    "Kingston", "Samsung", "WD", "Western Digital", "Seagate",
    "HyperX", "Razer", "Logitech", "SteelSeries", "Corsair",
]

CN_BRANDS = {"微星": "MSI", "华硕": "ASUS", "技嘉": "GIGABYTE", "蓝宝石": "SAPPHIRE"}


# ══════════════════════════════════════════════════════════
#  文本拆分类
# ══════════════════════════════════════════════════════════

def extract_sku_from_desc(item_desc):
    if pd.isna(item_desc):
        return ""
    s = str(item_desc).strip()
    if "__" in s:
        return s.split("__")[0].strip()
    return s


def extract_condition(item_desc):
    if pd.isna(item_desc):
        return "全新品"
    s = str(item_desc).strip().upper()
    if s.endswith(" R") or s.endswith("-R") or s.endswith("_R"):
        return "翻新品"
    return "全新品"


SUBCATEGORY_MAP = {
    "Video Card": "显卡", "Video Cards": "显卡",
    "Motherboard": "主板", "Motherboards": "主板",
    "Processor": "处理器", "Processors": "处理器",
    "Power Supply": "电源", "Power Supplies": "电源",
    "Case": "机箱", "Cases": "机箱",
    "Solid State": "固态硬盘", "SSD": "固态硬盘",
    "Memory": "内存", "RAM": "内存",
    "Cooling": "散热", "Cooler": "散热",
    "Liquid": "水冷散热",
    "Fan": "机箱风扇",
    "Network": "电脑配件",
    "Notebook": "电脑配件",
    "Keyboard": "外设", "Mouse": "外设",
}


def extract_category(item_desc, subcategory_name=None):
    if pd.isna(item_desc):
        return "其他配件"

    # 优先用 SubcategoryName 分类
    if subcategory_name and not pd.isna(subcategory_name):
        sub_upper = str(subcategory_name).strip().upper()
        for keyword, category in SUBCATEGORY_MAP.items():
            if keyword.upper() in sub_upper:
                return category

    s = str(item_desc).strip().upper()

    # 先用型号关键词检测（RTX、RX、7900、HAF等），避免被 CH 等前缀误匹配
    for kw in VGA_KEYWORDS:
        if kw in s:
            return "显卡"
    for kw in CPU_KEYWORDS:
        if kw in s:
            return "处理器"
    for kw in CASE_KEYWORDS:
        if kw in s:
            return "机箱"

    # 再用 CATEGORY_ORDER 匹配，但跳过开头的 CH 前缀
    s_for_category = s
    if "|" in s:
        s_for_category = s.split("|", 1)[1]  # 取 | 后面
    else:
        # 没有 | 时，跳过开头的 9SIxxx__ 前缀
        m = re.match(r'^9SI[A-Z0-9]+__', s)
        if m:
            s_for_category = s[m.end():]

    for key in CATEGORY_ORDER:
        if key in s_for_category:
            return CATEGORY_MAP.get(key, "其他配件")

    # 最后检查完整字符串中的 CH（但要求 CH 后面是品牌名，不是独立前缀）
    if "CH " in s and "CH " != s[:3]:
        return "电脑配件"

    return "其他配件"


def extract_brand(item_desc):
    if pd.isna(item_desc):
        return "其他"
    s = str(item_desc).upper()
    for brand in BRAND_KEYWORDS:
        if brand.upper() in s:
            return brand.title() if brand.isupper() else brand
    for cn, en in CN_BRANDS.items():
        if cn in s:
            return en
    return "其他"


# ══════════════════════════════════════════════════════════
#  数值计算类
# ══════════════════════════════════════════════════════════

def calc_unit_price(gmv, qty):
    try:
        if float(qty) > 0:
            return round(float(gmv) / float(qty), 2)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return 0.0

def calc_unit_margin(total_margin, qty):
    try:
        if float(qty) > 0:
            return round(float(total_margin) / float(qty), 2)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return 0.0

def calc_margin_rate(total_margin, gmv):
    try:
        g = float(gmv)
        if g > 0:
            return round(float(total_margin) / g * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return 0.0

def calc_gmv_share(gmv, total_gmv):
    try:
        t = float(total_gmv)
        if t > 0:
            return round(float(gmv) / t * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return 0.0

def calc_margin_share(total_margin, total_margin_all):
    try:
        t = float(total_margin_all)
        if t > 0:
            return round(float(total_margin) / t * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return 0.0

def calc_return_loss(gmv, rma_pct):
    try:
        return round(abs(float(gmv)) * abs(float(rma_pct)) / 100, 2)
    except (ValueError, TypeError):
        return 0.0

def calc_return_qty(qty_sold, rma_pct):
    try:
        q = float(qty_sold)
        r = abs(float(rma_pct)) / 100
        if r <= 0 or r >= 1:
            return 0
        denominator = 1 - r
        if denominator <= 0:
            return 0
        return math.ceil(q / denominator - q)
    except (ValueError, TypeError):
        return 0

def calc_return_margin_erosion(return_loss, total_margin):
    try:
        tm = float(total_margin)
        if tm > 0:
            return round(float(return_loss) / tm, 4)
    except (ValueError, TypeError):
        pass
    return 0.0

def calc_daily_sales(qty_sold, period_days=20):
    try:
        days = max(int(period_days), 1) if period_days else 20
        return round(float(qty_sold) / days, 2)
    except (ValueError, TypeError):
        return 0.0


# ══════════════════════════════════════════════════════════
#  分级标签类
# ══════════════════════════════════════════════════════════

def calc_risk_level(rma_pct):
    try:
        rma = abs(float(rma_pct))
    except (ValueError, TypeError):
        rma = 0
    if rma > 80:
        return "高危"
    elif rma >= 10:
        return "中危"
    else:
        return "低危"

def calc_efficiency_level(qty_sold):
    try:
        qty = float(qty_sold)
    except (ValueError, TypeError):
        qty = 0
    if qty >= 10:
        return "核心主力"
    elif qty >= 3:
        return "潜力培育"
    elif qty >= 1:
        return "低动销"
    else:
        return "零销负销"

def calc_price_tier(unit_price):
    try:
        p = float(unit_price)
    except (ValueError, TypeError):
        p = 0
    if p > 500:
        return "高客单"
    elif p >= 100:
        return "中客单"
    else:
        return "低客单"

def calc_priority_score(return_loss, return_margin_erosion, unit_price):
    try:
        return round(float(return_loss) * 0.5 + float(return_margin_erosion) * 0.3 + float(unit_price) * 0.2, 2)
    except (ValueError, TypeError):
        return 0.0

def calc_priority_label(score, scores_series):
    try:
        rank = (scores_series <= score).sum() / len(scores_series) * 100
    except Exception:
        rank = 100
    if rank >= 90:
        return "极高"
    elif rank >= 70:
        return "高"
    elif rank >= 40:
        return "中"
    else:
        return "低"


# ══════════════════════════════════════════════════════════
#  库存深度 & 处置建议
# ══════════════════════════════════════════════════════════

def calc_inventory_depth(inventory):
    try:
        inv = float(inventory) if inventory is not None else 0
    except (ValueError, TypeError):
        inv = 0
    if inv <= 0:
        return "零库存"
    elif inv <= 9:
        return "浅库存"
    elif inv <= 49:
        return "中库存"
    else:
        return "深库存"

def get_disposal_suggestion(risk, inventory_depth, efficiency):
    if risk == "高危" and inventory_depth in ["浅库存", "零库存"]:
        return "立即下架止损"
    elif risk == "高危" and inventory_depth == "中库存":
        return "整改观察+限量销售，7天未改善则下架"
    elif risk == "高危" and inventory_depth == "深库存":
        return "整改+清库存，7天观察期，同步启动退货流程"
    elif risk == "中危" and efficiency in ["低动销", "零销负销"]:
        return "限制补货，优先清理库存，观察30天"
    elif risk == "中危" and efficiency in ["核心主力", "潜力培育"]:
        return "维持现有销售，加强品质监控，月度复查"
    elif risk == "低危" and efficiency == "零销负销":
        return "直接清退下架"
    elif risk == "低危" and efficiency == "低动销":
        return "评估是否保留，无战略价值建议清退"
    elif risk == "低危" and efficiency in ["核心主力", "潜力培育"]:
        return "正常运营，持续监控RMA变化"
    else:
        return "需人工评估"


# ══════════════════════════════════════════════════════════
#  核心处理流程
# ══════════════════════════════════════════════════════════

def find_header_row(uploaded_file):
    raw = pd.read_excel(uploaded_file, engine="openpyxl", header=None)
    uploaded_file.seek(0)
    for i in range(min(25, len(raw))):
        row_vals = [str(x).strip().lower() for x in raw.iloc[i].tolist() if str(x).strip() != "" and str(x).strip().lower() != "nan"]
        if row_vals and "item description" in row_vals[0]:
            return i
    return 11


def extract_date_period(uploaded_file):
    raw = pd.read_excel(uploaded_file, engine="openpyxl", header=None, nrows=10)
    uploaded_file.seek(0)
    for i in range(min(10, len(raw))):
        row_str = " ".join(str(x) for x in raw.iloc[i].tolist() if str(x) != "nan")
        if "date period" in row_str.lower():
            dates = re.findall(r"\d{4}/\d{2}/\d{2}", row_str)
            if len(dates) == 2:
                compact = dates[0].replace("/", "") + "-" + dates[1].replace("/", "")
                readable = dates[0] + " - " + dates[1]
                return compact, readable
    now = datetime.now().strftime("%Y%m%d")
    return now, now


def process_sales_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding="gbk")
    else:
        header_row = find_header_row(uploaded_file)
        uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file, engine="openpyxl", skiprows=header_row)

    df.columns = df.columns.str.strip()

    desc_col = None
    for c in df.columns:
        if "item description" in str(c).lower():
            desc_col = c
            break
    if desc_col is None:
        return None, None, None, None, None

    df = df[df[desc_col].notna()].copy()
    grand_total_row = df[df[desc_col].astype(str).str.lower().str.contains("grand total", na=False)]
    data_rows = df[~df[desc_col].astype(str).str.lower().str.contains("grand total", na=False)].copy()

    total_gmv = 0
    total_margin = 0
    if not grand_total_row.empty:
        gmv_candidates = [c for c in data_rows.columns if "gmv" in str(c).lower()]
        margin_candidates = [c for c in data_rows.columns if "margin" in str(c).lower() and "total" in str(c).lower()]
        if gmv_candidates:
            try:
                total_gmv = float(grand_total_row.iloc[0][gmv_candidates[0]])
            except (ValueError, TypeError):
                pass
        if margin_candidates:
            try:
                total_margin = float(grand_total_row.iloc[0][margin_candidates[0]])
            except (ValueError, TypeError):
                pass

    data_rows = data_rows.copy()
    data_rows["NeweggItemNumber"] = data_rows[desc_col].apply(extract_sku_from_desc)

    for col_name in ["GMV", "RMA %", "Total Margin", "Net Quantity Sold", "SKU Count"]:
        for c in data_rows.columns:
            if col_name.lower() in str(c).lower():
                data_rows[c] = pd.to_numeric(data_rows[c].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    compact, readable = extract_date_period(uploaded_file)
    return data_rows, total_gmv, total_margin, compact, readable


def process_inventory_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding="gbk")
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.columns = df.columns.str.strip()

    if "NeweggItemNumber" in df.columns:
        df["NeweggItemNumber"] = df["NeweggItemNumber"].astype(str).str.strip()

    if "Inventory" in df.columns and "NeweggItemNumber" in df.columns:
        agg_cols = {}
        for c in df.columns:
            if c == "NeweggItemNumber":
                continue
            if c == "Inventory":
                agg_cols[c] = "sum"
            elif df[c].dtype in ["int64", "float64"]:
                agg_cols[c] = "first"
            else:
                agg_cols[c] = "first"
        df = df.groupby("NeweggItemNumber", as_index=False).agg(agg_cols)

    return df


def merge_and_generate(sales_df, inventory_df, total_gmv, total_margin, period_days=20):
    gmv_col = rma_col = margin_col = qty_col = None
    for c in sales_df.columns:
        cl = str(c).lower()
        if "gmv" in cl:
            gmv_col = c
        elif "rma" in cl:
            rma_col = c
        elif "margin" in cl and "total" in cl:
            margin_col = c
        elif "net quantity" in cl or "quantity sold" in cl:
            qty_col = c

    merged = sales_df.merge(inventory_df, on="NeweggItemNumber", how="left", suffixes=("", "_库存"))

    inv_col = None
    for c in merged.columns:
        if c == "Inventory":
            inv_col = c
            break
        if "inventory" in str(c).lower() and "库存" not in str(c):
            inv_col = c
            break

    desc_col_name = next((c for c in merged.columns if "item description" in str(c).lower()), None)
    subcat_col = next((c for c in merged.columns if "subcategory" in str(c).lower()), None)
    if desc_col_name:
        merged["商品成色"] = merged[desc_col_name].apply(extract_condition)
        merged["品类"] = merged.apply(lambda r: extract_category(r[desc_col_name], r.get(subcat_col)), axis=1)
        merged["品牌"] = merged[desc_col_name].apply(extract_brand)

    merged["客单价"] = merged.apply(lambda r: calc_unit_price(r.get(gmv_col, 0), r.get(qty_col, 0)) if gmv_col and qty_col else 0, axis=1)
    merged["单件毛利"] = merged.apply(lambda r: calc_unit_margin(r.get(margin_col, 0), r.get(qty_col, 0)) if margin_col and qty_col else 0, axis=1)
    merged["单SKU毛利率(%)"] = merged.apply(lambda r: calc_margin_rate(r.get(margin_col, 0), r.get(gmv_col, 0)) if gmv_col and margin_col else 0, axis=1)
    merged["GMV贡献占比(%)"] = merged.apply(lambda r: calc_gmv_share(r.get(gmv_col, 0), total_gmv) if gmv_col else 0, axis=1)
    merged["毛利贡献占比(%)"] = merged.apply(lambda r: calc_margin_share(r.get(margin_col, 0), total_margin) if margin_col else 0, axis=1)
    merged["退货损失金额"] = merged.apply(lambda r: calc_return_loss(r.get(gmv_col, 0), r.get(rma_col, 0)) if gmv_col and rma_col else 0, axis=1)
    merged["退货件数"] = merged.apply(lambda r: calc_return_qty(r.get(qty_col, 0), r.get(rma_col, 0)) if qty_col and rma_col else 0, axis=1)
    merged["退货毛利侵蚀率"] = merged.apply(
        lambda r: calc_return_margin_erosion(r["退货损失金额"], r.get(margin_col, 0)) if margin_col else 0, axis=1
    )
    merged["日均销量"] = merged.apply(lambda r: calc_daily_sales(r.get(qty_col, 0), period_days) if qty_col else 0, axis=1)

    merged["库存深度层级"] = merged[inv_col].apply(calc_inventory_depth) if inv_col else "未匹配"
    merged["SKU风险等级"] = merged[rma_col].apply(calc_risk_level) if rma_col else "低危"
    merged["SKU效能等级"] = merged[qty_col].apply(calc_efficiency_level) if qty_col else "零销负销"
    merged["客单价分层"] = merged["客单价"].apply(calc_price_tier)

    merged["整改优先级得分"] = merged.apply(
        lambda r: calc_priority_score(r["退货损失金额"], r["退货毛利侵蚀率"], r["客单价"]), axis=1
    )
    scores = merged["整改优先级得分"]
    merged["整改优先级"] = merged["整改优先级得分"].apply(lambda s: calc_priority_label(s, scores))

    merged["处置建议"] = merged.apply(
        lambda r: get_disposal_suggestion(r["SKU风险等级"], r["库存深度层级"], r["SKU效能等级"]), axis=1
    )

    return merged


# ══════════════════════════════════════════════════════════
#  卖家健康度计算
# ══════════════════════════════════════════════════════════

def extract_seller_id(sku):
    s = str(sku).strip()
    if s.startswith("9SI") and len(s) > 6:
        return s[3:7]
    return s[:4] if len(s) >= 4 else s


def calc_seller_health_score(seller_data):
    try:
        total_gmv = float(seller_data.get("GMV", 0))
        total_margin = float(seller_data.get("Total Margin", 0))
        avg_rma = float(seller_data.get("RMA%", 0))
        total_qty = float(seller_data.get("Net Quantity Sold", 0))
        sku_count = int(seller_data.get("SKU Count", 0))
    except (ValueError, TypeError):
        return 0, "D", "计算异常"

    score = 0

    # GMV评分：线性比例，$100K=30分
    if total_gmv > 0:
        score += min(30, round(total_gmv / 100000 * 30, 1))

    # 毛利评分：线性比例，$10K=25分
    if total_margin > 0:
        score += min(25, round(total_margin / 10000 * 25, 1))

    abs_rma = abs(avg_rma)
    for threshold, rma_score in RMA_RULES:
        if abs_rma <= threshold:
            score += rma_score
            break

    if total_qty >= 50:
        score += 10
    elif total_qty >= 20:
        score += 7
    elif total_qty >= 5:
        score += 4
    elif total_qty > 0:
        score += 2

    if sku_count >= 20:
        score += 10
    elif sku_count >= 10:
        score += 7
    elif sku_count >= 5:
        score += 4
    elif sku_count > 0:
        score += 2

    margin_rate = total_margin / total_gmv if total_gmv > 0 else 0
    if margin_rate >= 0.10:
        score += 5
    elif margin_rate >= 0.05:
        score += 4
    elif margin_rate > 0:
        score += 2

    score = round(min(100, max(0, score)), 1)

    grade = "D"
    label = "高风险卖家"
    for g, rule in GRADE_RULES.items():
        if score >= rule["min"]:
            grade = g
            label = rule["label"]
            break

    return score, grade, label


def calc_seller_health_from_sku(matched_df):
    matched_df = matched_df.copy()

    sku_col = next((c for c in matched_df.columns if "newegg" in c.lower() or "item" in c.lower()), None)
    if sku_col is None and "NeweggItemNumber" not in matched_df.columns:
        return pd.DataFrame()
    
    sku_col = sku_col or "NeweggItemNumber"
    seller_id_col = matched_df[sku_col].apply(extract_seller_id)
    matched_df["卖家ID"] = seller_id_col

    gmv_col = next((c for c in matched_df.columns if c.upper() == "GMV"), "GMV")
    rma_col = next((c for c in matched_df.columns if "rma" in c.lower()), "RMA %")
    margin_col = next((c for c in matched_df.columns if "margin" in c.lower() and "total" in c.lower()), None)
    qty_col = next((c for c in matched_df.columns if "quantity" in c.lower() or "net quantity" in c.lower()), "Net Quantity Sold")

    agg_map = {gmv_col: "sum", rma_col: "mean", qty_col: "sum", "NeweggItemNumber": "count"}
    rename_map = {rma_col: "RMA%", qty_col: "Net Quantity Sold", "NeweggItemNumber": "SKU Count"}
    if margin_col:
        agg_map[margin_col] = "sum"
        rename_map[margin_col] = "Total Margin"

    agg_data = matched_df.groupby("卖家ID").agg(agg_map).rename(columns=rename_map)

    health_results = []
    for seller_id, row in agg_data.iterrows():
        score, grade, label = calc_seller_health_score(row.to_dict())
        health_results.append({
            "卖家ID": seller_id,
            "健康度评分": score,
            "等级": grade,
            "标签": label,
            "GMV": row["GMV"],
            "RMA%": row["RMA%"],
            "总毛利": row["Total Margin"],
            "总销量": row["Net Quantity Sold"],
            "SKU数": int(row["SKU Count"]),
        })

    return pd.DataFrame(health_results)
