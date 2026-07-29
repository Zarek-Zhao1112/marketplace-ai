import os
import json
import numpy as np
import pandas as pd

from src.config.settings import (
    DATA_DIR, ISSUES_PATH, BRANDS_PATH, CONTACTS_PATH,
    INDUSTRY_BENCHMARKS, INDUSTRY_GRADE_THRESHOLDS, GRADE_RULES,
)

SELLER_HISTORY_DIR = os.path.join(str(DATA_DIR), "seller_history")
os.makedirs(SELLER_HISTORY_DIR, exist_ok=True)

SKU_ANALYSIS_DIR = os.path.join(str(DATA_DIR), "sku_analysis")
os.makedirs(SKU_ANALYSIS_DIR, exist_ok=True)


# ── 文件感知缓存 ──────────────────────────────────────────
_FILE_CACHE = {}


def _cached_read_json(filepath):
    """带文件修改时间校验的JSON缓存，文件被删除/修改后自动失效"""
    if not os.path.exists(filepath):
        _FILE_CACHE.pop(filepath, None)
        return None
    mtime = os.path.getmtime(filepath)
    cached = _FILE_CACHE.get(filepath)
    if cached and cached[1] == mtime:
        return cached[0]
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _FILE_CACHE[filepath] = (data, mtime)
        return data
    except (json.JSONDecodeError, OSError):
        _FILE_CACHE.pop(filepath, None)
        return None


def invalidate_cache(filepath=None):
    """手动清除缓存。filepath=None 清除全部"""
    if filepath:
        _FILE_CACHE.pop(filepath, None)
    else:
        _FILE_CACHE.clear()


# ══════════════════════════════════════════════════════════
#  文件初始化
# ══════════════════════════════════════════════════════════

def init_excel(path: str, columns: list):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_excel(path, index=False, engine="openpyxl")


os.makedirs(DATA_DIR, exist_ok=True)
init_excel(ISSUES_PATH, ["问题ID", "时间", "卖家名称", "问题类型", "问题描述",
                          "处理状态", "处理过程", "解决方案", "来源文件"])
init_excel(BRANDS_PATH, ["品牌ID", "品牌名称", "所属类目", "目标市场", "品牌规模",
                          "官网域名", "品牌简介", "Slogan", "社交媒体", "销售渠道",
                          "联系方式", "跟进状态", "备注", "创建时间"])
init_excel(CONTACTS_PATH, ["商家名称", "邮箱", "LinkedIn", "职位", "官网",
                            "国家", "来源", "备注", "添加时间"])


# ══════════════════════════════════════════════════════════
#  卖家历史记录管理
# ══════════════════════════════════════════════════════════

def save_seller_history(seller_id, record):
    filepath = os.path.join(SELLER_HISTORY_DIR, f"{seller_id}.json")
    history = []
    if os.path.exists(filepath):
        data = _cached_read_json(filepath)
        if data is not None:
            history = data
    new_date = record.get("日期", "")
    history = [h for h in history if h.get("日期", "") != new_date]
    history.append(record)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    invalidate_cache(filepath)
    return filepath


def load_seller_history(seller_id):
    """从 sku_analysis 目录派生卖家历史记录（兼容旧 seller_history）"""
    # 优先从 sku_analysis 读取
    seller_dir = os.path.join(SKU_ANALYSIS_DIR, seller_id)
    if os.path.exists(seller_dir):
        batches = load_sku_analysis_list(seller_id)
        history = []
        for b in batches:
            summary = b.get("seller_summary", {})
            if summary and summary.get("日期"):
                history.append(summary)
            elif summary and summary.get("健康度评分"):
                summary.setdefault("日期", b.get("date_readable", b.get("date_period", "")))
                history.append(summary)
        if history:
            return history

    # 兼容旧 seller_history 文件
    filepath = os.path.join(SELLER_HISTORY_DIR, f"{seller_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return []


def delete_seller_history(seller_id, index=None):
    """删除旧 seller_history 目录中的记录（兼容用）"""
    filepath = os.path.join(SELLER_HISTORY_DIR, f"{seller_id}.json")
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        history = json.load(f)
    if index is not None and 0 <= index < len(history):
        history.pop(index)
    else:
        history = []
    if history:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    else:
        os.remove(filepath)


def delete_sku_analysis_batch(seller_id, date_period):
    """删除某个卖家的某个 SKU 分析批次"""
    filepath = os.path.join(SKU_ANALYSIS_DIR, seller_id, f"{date_period}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        invalidate_cache(filepath)
    # 如果该卖家目录为空，删除目录
    seller_dir = os.path.join(SKU_ANALYSIS_DIR, seller_id)
    if os.path.exists(seller_dir) and not os.listdir(seller_dir):
        os.rmdir(seller_dir)


def delete_sku_analysis_seller(seller_id):
    """删除某个卖家的所有 SKU 分析数据"""
    seller_dir = os.path.join(SKU_ANALYSIS_DIR, seller_id)
    if os.path.exists(seller_dir):
        # 先清除该目录下所有文件的缓存
        for fname in os.listdir(seller_dir):
            invalidate_cache(os.path.join(seller_dir, fname))
        import shutil
        shutil.rmtree(seller_dir)
    # 同时清理旧 seller_history
    delete_seller_history(seller_id)


def load_all_seller_ids():
    """获取所有卖家ID（合并 sku_analysis 和 seller_history）"""
    seller_ids = set()
    # 从 sku_analysis 目录取
    if os.path.exists(SKU_ANALYSIS_DIR):
        for d in os.listdir(SKU_ANALYSIS_DIR):
            if os.path.isdir(os.path.join(SKU_ANALYSIS_DIR, d)):
                seller_ids.add(d)
    # 兼容旧 seller_history 目录
    if os.path.exists(SELLER_HISTORY_DIR):
        for f in os.listdir(SELLER_HISTORY_DIR):
            if f.endswith(".json"):
                seller_ids.add(f.replace(".json", ""))
    return sorted(seller_ids)


def load_all_seller_history():
    """从 sku_analysis 目录派生所有卖家历史（兼容旧 seller_history）"""
    all_history = {}

    # 优先从 sku_analysis 读取
    if os.path.exists(SKU_ANALYSIS_DIR):
        for seller_dir_name in os.listdir(SKU_ANALYSIS_DIR):
            seller_dir = os.path.join(SKU_ANALYSIS_DIR, seller_dir_name)
            if os.path.isdir(seller_dir):
                history = load_seller_history(seller_dir_name)
                if history:
                    all_history[seller_dir_name] = history

    # 兼容旧 seller_history 文件（仅补充 sku_analysis 中没有的）
    if os.path.exists(SELLER_HISTORY_DIR):
        for fname in os.listdir(SELLER_HISTORY_DIR):
            if fname.endswith(".json"):
                seller_id = fname.replace(".json", "")
                if seller_id not in all_history:
                    filepath = os.path.join(SELLER_HISTORY_DIR, fname)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            all_history[seller_id] = json.load(f)
                    except json.JSONDecodeError:
                        continue
    return all_history


def calc_dynamic_benchmarks(all_history):
    all_scores = []
    all_rma = []
    all_gmv = []
    all_margin_rate = []

    for seller_id, records in all_history.items():
        for rec in records:
            if "健康度评分" in rec:
                all_scores.append(rec["健康度评分"])
            if "RMA%" in rec:
                all_rma.append(rec["RMA%"])
            if "GMV" in rec:
                all_gmv.append(rec["GMV"])
            if "毛利率%" in rec:
                all_margin_rate.append(rec["毛利率%"])

    if not all_scores:
        return None

    def percentile(data, p):
        if not data:
            return 0
        data_sorted = sorted(data)
        k = (len(data_sorted) - 1) * p / 100
        f = int(k)
        c = f + 1
        if c >= len(data_sorted):
            return data_sorted[-1]
        return data_sorted[f] + (k - f) * (data_sorted[c] - data_sorted[f])

    return {
        "卖家数量": len(all_history),
        "评分分布": {
            "P25": round(percentile(all_scores, 25), 1),
            "P50": round(percentile(all_scores, 50), 1),
            "P75": round(percentile(all_scores, 75), 1),
            "平均": round(np.mean(all_scores), 1),
        },
        "RMA分布": {
            "P25": round(percentile(all_rma, 25), 2),
            "P50": round(percentile(all_rma, 50), 2),
            "P75": round(percentile(all_rma, 75), 2),
            "平均": round(np.mean(all_rma), 2) if all_rma else 0,
        },
        "GMV分布": {
            "P25": round(percentile(all_gmv, 25), 2),
            "P50": round(percentile(all_gmv, 50), 2),
            "P75": round(percentile(all_gmv, 75), 2),
            "平均": round(np.mean(all_gmv), 2) if all_gmv else 0,
        },
        "毛利率分布": {
            "P25": round(percentile(all_margin_rate, 25), 2),
            "P50": round(percentile(all_margin_rate, 50), 2),
            "P75": round(percentile(all_margin_rate, 75), 2),
            "平均": round(np.mean(all_margin_rate), 2) if all_margin_rate else 0,
        },
    }


def calc_benchmark_with_industry(internal_bench, seller_count):
    if internal_bench is None:
        return {
            "类型": "行业基准(初始)",
            "权重": {"行业": 1.0, "内部": 0},
            "数据": {
                "健康度P50": INDUSTRY_GRADE_THRESHOLDS["B"],
                "RMA平均": 5.0,
                "GMV平均": 20000,
                "毛利率平均": 10.0,
            },
        }

    if seller_count < 10:
        ind_w, int_w = 0.6, 0.4
    elif seller_count < 20:
        ind_w, int_w = 0.3, 0.7
    else:
        ind_w, int_w = 0.1, 0.9

    return {
        "类型": "混合基准",
        "权重": {"行业": ind_w, "内部": int_w},
        "数据": {
            "健康度P50": round(INDUSTRY_GRADE_THRESHOLDS["B"] * ind_w + internal_bench["评分分布"]["P50"] * int_w, 1),
            "RMA平均": round(5.0 * ind_w + internal_bench["RMA分布"]["平均"] * int_w, 2),
            "GMV平均": round(20000 * ind_w + internal_bench["GMV分布"]["平均"] * int_w, 2),
            "毛利率平均": round(10.0 * ind_w + internal_bench["毛利率分布"]["平均"] * int_w, 2),
        },
        "内部基准": internal_bench,
    }


# ══════════════════════════════════════════════════════════
#  SKU 分析结果保存
# ══════════════════════════════════════════════════════════

def save_sku_analysis(seller_id, date_period, date_readable, matched_df, seller_summary=None, inv_upload_time=None):
    seller_dir = os.path.join(SKU_ANALYSIS_DIR, seller_id)
    os.makedirs(seller_dir, exist_ok=True)
    filename = f"{date_period}.json"
    filepath = os.path.join(seller_dir, filename)
    record = {
        "seller_id": seller_id,
        "date_period": date_period,
        "date_readable": date_readable,
        "total_skus": len(matched_df),
        "seller_summary": seller_summary or {},
        "records": matched_df.where(matched_df.notna(), None).to_dict(orient="records"),
    }
    if inv_upload_time:
        record["inv_upload_time"] = inv_upload_time
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return filepath


def load_sku_analysis_list(seller_id):
    seller_dir = os.path.join(SKU_ANALYSIS_DIR, seller_id)
    if not os.path.exists(seller_dir):
        return []
    batches = []
    for fname in sorted(os.listdir(seller_dir), reverse=True):
        if fname.endswith(".json"):
            fpath = os.path.join(seller_dir, fname)
            data = _cached_read_json(fpath)
            if data is not None:
                batches.append(data)
    return batches


def load_sku_analysis_batch(seller_id, date_period):
    filepath = os.path.join(SKU_ANALYSIS_DIR, seller_id, f"{date_period}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
