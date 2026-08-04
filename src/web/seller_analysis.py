import math
import os, re
import numpy as np
import pandas as pd
from datetime import datetime

from src.config.settings import RMA_RULES, GRADE_RULES


def safe_float(val, default=0.0):
    """安全转换为float，处理None/字符串/百分比等"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
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


def safe_int(val, default=0):
    """安全转换为int"""
    return int(safe_float(val, default))


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


def extract_condition(item_desc, item_condition=None):
    # 优先用原始 ItemCondition 列
    if item_condition and not pd.isna(item_condition):
        cond = str(item_condition).strip().lower()
        if "refurbish" in cond or "used" in cond:
            return "翻新品"
        if "new" in cond:
            return "全新品"
    # 降级：用 SKU 描述末尾判断
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
    "Tools": "其他配件",
    "Network": "电脑配件",
    "Notebook": "电脑配件",
    "Keyboard": "外设", "Mouse": "外设",
    # 中文关键词
    "显卡": "显卡", "主板": "主板", "处理器": "处理器",
    "电源": "电源", "机箱": "机箱", "固态硬盘": "固态硬盘",
    "内存": "内存", "散热": "散热", "外设": "外设",
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

    # 再用 CATEGORY_ORDER 匹配，但跳过 CH 前缀（CH是卖家分类前缀，不是品类）
    s_for_category = s
    if "|" in s:
        s_for_category = s.split("|", 1)[1]  # 取 | 后面
    else:
        # 没有 | 时，跳过开头的 9SIxxx__ 前缀
        m = re.match(r'^9SI[A-Z0-9]+__', s)
        if m:
            s_for_category = s[m.end():]

    # 从 CATEGORY_ORDER 中移除 "CH"，因为它不是品类
    keys_without_ch = [k for k in CATEGORY_ORDER if k != "CH"]
    for key in keys_without_ch:
        if key in s_for_category:
            return CATEGORY_MAP.get(key, "其他配件")

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
    """计算退货件数
    公式: returns = qty_sold * rma% / (1 - rma%)
    特殊情况: RMA%=0返回0, RMA%>=100%返回0, qty=0时尝试用GMV推算
    """
    try:
        q = float(qty_sold)
        r = abs(float(rma_pct)) / 100
        if r <= 0:
            return 0
        if r >= 1:
            return 0
        denominator = 1 - r
        if denominator <= 0:
            return 0
        # 用ceil确保有退货就算1件
        result = math.ceil(q * r / denominator)
        return result
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

def calc_priority_score(return_loss, return_margin_erosion, rma_pct, qty_sold):
    """优先级评分：退货损失(40%) + 毛利侵蚀率(30%) + RMA严重度(20%) + 动销逆向(10%)
    各维度归一化到0-100，加权求和
    """
    try:
        # 退货损失归一化：$100为满分基准
        loss_score = min(100, float(return_loss) / 100 * 100)
        # 毛利侵蚀率：本身就是百分比
        erosion_score = min(100, float(return_margin_erosion) * 100)
        # RMA严重度：用绝对值
        rma_score = min(100, abs(float(rma_pct)))
        # 动销逆向：销量越低越需要关注，但销量为0给中等分(50)而不是满分
        qty = float(qty_sold) if qty_sold else 0
        if qty == 0:
            qty_score = 50  # 零销给中等分，不代表最高优先级
        elif qty <= 2:
            qty_score = 80  # 低动销
        elif qty <= 5:
            qty_score = 50  # 潜力培育
        elif qty <= 10:
            qty_score = 20  # 核心主力
        else:
            qty_score = 0   # 高动销
        return round(loss_score * 0.4 + erosion_score * 0.3 + rma_score * 0.2 + qty_score * 0.1, 1)
    except (ValueError, TypeError):
        return 0.0

def calc_priority_label(score, scores_series=None):
    """基于绝对分数分级：>=40极高，>=25高，>=10中，<10低"""
    s = float(score)
    if s >= 40:
        return "极高"
    elif s >= 25:
        return "高"
    elif s >= 10:
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

def get_disposal_suggestion(risk, inventory_depth, efficiency, sku_age_days=None, can_return_to_supplier=False, has_bundle_sku=False, is_multi_site=False):
    """获取SKU处置建议，支持多维度决策树

    Args:
        risk: 风险等级（低危/中危/高危）
        inventory_depth: 库存深度（零库存/浅库存/中库存/深库存）
        efficiency: 效能等级（零销负销/低动销/潜力培育/核心主力）
        sku_age_days: SKU上架天数（None表示未知）
        can_return_to_supplier: 供应商是否接受退货
        has_bundle_sku: 是否有可捆绑的热销SKU
        is_multi_site: 是否多站点卖家
    """
    # 新品保护期
    if sku_age_days is not None and sku_age_days < 30:
        return "评估保留，新品保护期30天，到期复查"

    # 长期滞销直接下架
    if sku_age_days is not None and sku_age_days > 90 and efficiency == "零销负销":
        return "立即下架，长期滞销SKU"

    # 高危 SKU 保持原有逻辑
    if risk == "高危" and inventory_depth in ["浅库存", "零库存"]:
        return "立即下架止损"
    elif risk == "高危" and inventory_depth == "中库存":
        return "整改观察+限量销售，7天未改善则下架"
    elif risk == "高危" and inventory_depth == "深库存":
        return "整改+清库存，7天观察期，同步启动退货流程"

    # 中危 / 低危 + 零销负销：多维度决策
    if efficiency == "零销负销":
        if can_return_to_supplier:
            return "退货供应商，完全止损"
        if has_bundle_sku:
            return "捆绑销售，蹭流量清库存"
        if is_multi_site:
            return "多站点调拨或报活动清库存"
        if inventory_depth in ["深库存", "中库存"]:
            return "报活动清库存（Spotlight Sale / Deal Portal）"
        return "直接清退下架"

    # 中危 + 低动销
    if risk == "中危" and efficiency == "低动销":
        return "限制补货，优先清理库存，观察30天"

    # 低危 + 低动销
    if risk == "低危" and efficiency == "低动销":
        if inventory_depth in ["深库存", "中库存"]:
            return "降价10-20%或报活动，观察2周"
        return "评估是否保留，无战略价值建议清退"

    # 核心主力 / 潜力培育
    if efficiency in ["核心主力", "潜力培育"]:
        if risk == "中危":
            return "维持现有销售，加强品质监控，月度复查"
        return "正常运营，持续监控RMA变化"

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
    gmv_col = rma_col = margin_col = qty_col = return_qty_col = None
    for c in sales_df.columns:
        cl = str(c).lower()
        if "gmv" in cl:
            gmv_col = c
        elif "rma" in cl:
            rma_col = c
        elif "margin" in cl and "total" in cl:
            margin_col = c
        elif "quantity returned" in cl or "return quantity" in cl:
            return_qty_col = c
        elif "net quantity" in cl or "quantity sold" in cl:
            qty_col = c

    # 检查NeweggItemNumber列是否存在
    if "NeweggItemNumber" not in sales_df.columns:
        return pd.DataFrame()
    if "NeweggItemNumber" not in inventory_df.columns:
        # 如果库存表没有NeweggItemNumber，返回只有销售数据的DataFrame
        merged = sales_df.copy()
    else:
        merged = sales_df.merge(inventory_df, on="NeweggItemNumber", how="outer", suffixes=("", "_库存"))

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
    cond_col = next((c for c in merged.columns if "itemcondition" in str(c).lower().replace(" ", "")), None)

    # 提取新增字段
    cm_col = next((c for c in merged.columns if c == "CM"), None)
    category_col = next((c for c in merged.columns if "categoryname" in str(c).lower()), None)
    seller_name_col = next((c for c in merged.columns if "sellername" in str(c).lower()), None)
    platform_col = next((c for c in merged.columns if "platform" in str(c).lower()), None)

    # 添加SellerID字段（从NeweggItemNumber提取）
    if "NeweggItemNumber" in merged.columns:
        merged["SellerID"] = merged["NeweggItemNumber"].apply(extract_seller_id)

    # 添加用户需要的字段
    if cm_col:
        merged["AM/CM"] = merged[cm_col]
    if category_col:
        merged["Category"] = merged[category_col]
    if subcat_col:
        merged["Subcategory"] = merged[subcat_col]
    if seller_name_col:
        merged["SellerName"] = merged[seller_name_col]
    if platform_col:
        merged["Platform"] = merged[platform_col]

    # 重命名字段以匹配用户期望
    if desc_col_name:
        merged["ItemDescription"] = merged[desc_col_name]
        merged["商品成色"] = merged.apply(lambda r: extract_condition(r[desc_col_name], r.get(cond_col)), axis=1)
        merged["品类"] = merged.apply(lambda r: extract_category(r[desc_col_name], r.get(subcat_col)), axis=1)
        merged["Brand"] = merged[desc_col_name].apply(extract_brand)
    if cond_col:
        merged["Condition"] = merged[cond_col]

    # 添加NeweggSku#字段
    if "NeweggItemNumber" in merged.columns:
        merged["NeweggSku#"] = merged["NeweggItemNumber"]

    merged["客单价"] = merged.apply(lambda r: calc_unit_price(r.get(gmv_col, 0), r.get(qty_col, 0)) if gmv_col and qty_col else 0, axis=1)
    merged["单件毛利"] = merged.apply(lambda r: calc_unit_margin(r.get(margin_col, 0), r.get(qty_col, 0)) if margin_col and qty_col else 0, axis=1)
    merged["单SKU毛利率(%)"] = merged.apply(lambda r: calc_margin_rate(r.get(margin_col, 0), r.get(gmv_col, 0)) if gmv_col and margin_col else 0, axis=1)
    merged["GMV贡献占比(%)"] = merged.apply(lambda r: calc_gmv_share(r.get(gmv_col, 0), total_gmv) if gmv_col else 0, axis=1)
    merged["毛利贡献占比(%)"] = merged.apply(lambda r: calc_margin_share(r.get(margin_col, 0), total_margin) if margin_col else 0, axis=1)
    merged["退货损失金额"] = merged.apply(lambda r: calc_return_loss(r.get(gmv_col, 0), r.get(rma_col, 0)) if gmv_col and rma_col else 0, axis=1)
    if return_qty_col:
        # 有真实退货件数，直接用
        merged["退货件数"] = merged[return_qty_col].apply(lambda x: safe_int(x, 0))
    elif qty_col and rma_col:
        # 没有退货件数字段，用RMA%反推（有误差）
        merged["退货件数"] = merged.apply(lambda r: calc_return_qty(r.get(qty_col, 0), r.get(rma_col, 0)), axis=1)
    else:
        merged["退货件数"] = 0
    merged["退货毛利侵蚀率"] = merged.apply(
        lambda r: calc_return_margin_erosion(r["退货损失金额"], r.get(margin_col, 0)) if margin_col else 0, axis=1
    )
    merged["日均销量"] = merged.apply(lambda r: calc_daily_sales(r.get(qty_col, 0), period_days) if qty_col else 0, axis=1)

    merged["库存深度层级"] = merged[inv_col].apply(calc_inventory_depth) if inv_col else "未匹配"
    merged["SKU风险等级"] = merged[rma_col].apply(calc_risk_level) if rma_col else "低危"
    merged["SKU效能等级"] = merged[qty_col].apply(calc_efficiency_level) if qty_col else "零销负销"
    merged["客单价分层"] = merged["客单价"].apply(calc_price_tier)

    merged["整改优先级得分"] = merged.apply(
        lambda r: calc_priority_score(r["退货损失金额"], r["退货毛利侵蚀率"], r.get(rma_col, 0), r.get(qty_col, 0)), axis=1
    )
    merged["整改优先级"] = merged["整改优先级得分"].apply(calc_priority_label)

    merged["处置建议"] = merged.apply(
        lambda r: get_disposal_suggestion(r["SKU风险等级"], r["库存深度层级"], r["SKU效能等级"]), axis=1
    )

    # 按用户指定顺序排列列
    front_cols = ["AM/CM", "Condition", "Category", "Subcategory", "SellerID", "SellerName", "NeweggSku#", "Brand", "ItemDescription"]
    front_cols = [c for c in front_cols if c in merged.columns]

    # 排除原始字段（已被重命名），但保留NeweggItemNumber供后续计算使用
    exclude_cols = {"Item Description", "ItemCondition", "SubcategoryName", "CategoryName", "CM", "SellerName"}
    other_cols = [c for c in merged.columns if c not in front_cols and c not in exclude_cols]
    merged = merged[front_cols + other_cols]

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

    # GMV评分：线性比例，$50K=30分（与行业基准对齐）
    if total_gmv > 0:
        score += min(30, round(total_gmv / 50000 * 30, 1))

    # 毛利评分：线性比例，$10K=25分
    if total_margin > 0:
        score += min(25, round(total_margin / 10000 * 25, 1))

    # RMA%评分：与行业基准对齐（≤2%优秀）
    abs_rma = abs(avg_rma)
    if abs_rma <= 2:
        score += 20
    elif abs_rma <= 5:
        score += 16
    elif abs_rma <= 8:
        score += 12
    elif abs_rma <= 15:
        score += 8
    elif abs_rma <= 25:
        score += 4

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

    # 分离正常销售和退货记录
    normal_sales = matched_df[matched_df[gmv_col] >= 0].copy()
    return_records = matched_df[matched_df[gmv_col] < 0].copy()

    # 对正常销售记录计算RMA%均值
    if not normal_sales.empty:
        rma_by_seller = normal_sales.groupby("卖家ID")[rma_col].mean()
    else:
        rma_by_seller = pd.Series(dtype=float)

    # 如果卖家只有退货记录没有正常销售，用退货记录的RMA%均值
    if not return_records.empty:
        return_rma = return_records.groupby("卖家ID")[rma_col].mean()
        # 合并：优先用正常销售的RMA%，如果没有则用退货记录的
        for seller_id in return_rma.index:
            if seller_id not in rma_by_seller.index or pd.isna(rma_by_seller.get(seller_id)):
                rma_by_seller[seller_id] = return_rma[seller_id]

    # 对所有记录计算GMV、毛利、销量的总和
    agg_map = {gmv_col: "sum", qty_col: "sum"}
    rename_map = {qty_col: "Net Quantity Sold"}
    
    # 使用sku_col而不是硬编码NeweggItemNumber
    if sku_col in matched_df.columns:
        agg_map[sku_col] = "count"
        rename_map[sku_col] = "SKU Count"
    
    if margin_col:
        agg_map[margin_col] = "sum"
        rename_map[margin_col] = "Total Margin"

    agg_data = matched_df.groupby("卖家ID").agg(agg_map).rename(columns=rename_map)
    
    # 合并RMA%到聚合结果
    agg_data["RMA%"] = rma_by_seller.reindex(agg_data.index, fill_value=0)

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
