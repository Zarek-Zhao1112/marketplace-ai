"""卖家分析页面 - 重构版
提取重复UI组件为可复用函数，减少代码量，方便维护
"""
import os, sys, json, re, glob, math, shutil, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib3
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from src.web.sidebar import render as render_sidebar
from src.web.utils import export_excel
from src.web.excel_export import (
    export_sku_excel, export_sku_multi_month,
    export_seller_history_excel, export_sku_history_excel, export_all_sellers_pano,
)
from src.web.data import (
    load_seller_history, load_all_seller_ids,
    load_all_seller_history, calc_dynamic_benchmarks, calc_benchmark_with_industry,
    delete_seller_history, delete_sku_analysis_batch, delete_sku_analysis_seller,
    save_sku_analysis, load_sku_analysis_list, load_sku_analysis_batch,
)
from src.config.settings import INDUSTRY_BENCHMARKS, INDUSTRY_GRADE_THRESHOLDS, RMA_RULES, GRADE_RULES
from src.web.styles import inject_global_css
from src.web.seller_analysis import (
    process_sales_file, process_inventory_file, merge_and_generate,
    calc_seller_health_from_sku, extract_seller_id,
)


# ══════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════

def calc_period_days(date_period):
    try:
        parts = date_period.split("-")
        start = datetime.strptime(parts[0], "%Y%m%d")
        end = datetime.strptime(parts[1], "%Y%m%d")
        return max((end - start).days, 1)
    except Exception:
        return 20


def parse_date_any(d):
    """通用日期解析，支持多种格式"""
    s = str(d).strip()
    if not s or s == "N/A" or s == "未知":
        return None
    
    # 格式1: "2026/06/01 - 2026/06/30" 或 "2026/06/01"
    m = re.findall(r"\d{4}/\d{2}/\d{2}", s)
    if m:
        try:
            return datetime.strptime(m[0], "%Y/%m/%d")
        except Exception:
            pass
    
    # 格式2: "20260601-20260630" 或 "20260601"
    m = re.findall(r"\d{8}", s)
    if m:
        try:
            return datetime.strptime(m[0], "%Y%m%d")
        except Exception:
            pass
    
    # 格式3: "2026-06-01" 等标准格式
    try:
        return pd.to_datetime(s)
    except Exception:
        return None


def reorder_sku_columns(df):
    """按用户要求的顺序排列字段"""
    cols = list(df.columns)

    # 用户指定的前置字段顺序（按数据中的字段名）
    front_cols = [
        "AM/CM",              # AM/CM
        "Condition",          # Condition（成色）
        "Category",           # Category
        "Subcategory",        # Subcategory
        "SellerID",           # SellerID
        "SellerName",         # SellerName
        "NeweggSku#",         # NeweggSku#
        "Brand",              # Brand
        "ItemDescription",    # ItemDescription
        "FulfillmentType",    # shipping（履约方式）
    ]

    # 只保留数据中实际存在的字段
    front_cols = [c for c in front_cols if c in cols]

    # 其他字段保持原有顺序
    other_cols = [c for c in cols if c not in front_cols]

    # 组合：前置字段 + 其他字段
    new_order = front_cols + other_cols

    return df[new_order]


def to_date(d):
    return d.date() if hasattr(d, 'date') else d


def filter_history_by_time(history_dict, start_date, end_date):
    if start_date is None:
        return history_dict
    start_d, end_d = to_date(start_date), to_date(end_date)
    filtered = {}
    for sid, records in history_dict.items():
        matched = [r for r in records if (d := parse_date_any(r.get("日期", ""))) is None or start_d <= d.date() <= end_d]
        if matched:
            filtered[sid] = matched
    return filtered


def extract_seller_id_from_file(raw_df):
    """从销售表原始数据提取卖家ID"""
    for _, row in raw_df.iterrows():
        row_str = " ".join(str(x) for x in row.tolist() if str(x) != "nan")
        if "seller id" in row_str.lower() and "includes" in row_str.lower():
            match = re.search(r'seller id\s+includes\s*\(\s*["\']?([A-Z0-9]+)["\']?\s*\)', row_str, re.IGNORECASE)
            if match:
                return match.group(1)
    for _, row in raw_df.iterrows():
        for val in row.tolist():
            val_str = str(val).strip()
            if val_str.startswith("9SI") and len(val_str) > 6:
                return val_str[3:7]
    return None


# ══════════════════════════════════════════════════════════
#  可复用UI组件
# ══════════════════════════════════════════════════════════

def render_health_metrics(seller_row):
    rd = seller_row.iloc[0] if hasattr(seller_row, 'iloc') else seller_row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("健康度评分", f"{rd['健康度评分']:.1f}", help="满分100")
    with m2:
        grade = rd["等级"]
        label = GRADE_RULES[grade]["label"] if grade in GRADE_RULES else ""
        st.metric("等级", f"{grade} - {label}")
    with m3:
        st.metric("GMV", f"${rd['GMV']:,.2f}")
    with m4:
        st.metric("RMA%", f"{rd['RMA%']:.2f}%")
    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.metric("总毛利", f"${rd['总毛利']:,.2f}")
    with m6:
        st.metric("总销量", f"{rd['总销量']:.0f}")
    with m7:
        st.metric("SKU数", f"{rd['SKU数']}")
    with m8:
        margin_rate = (rd['总毛利'] / rd['GMV'] * 100) if rd['GMV'] > 0 else 0
        st.metric("毛利率", f"{margin_rate:.1f}%")


def render_benchmark_comparison(seller_row, benchmark):
    rd = seller_row.iloc[0] if hasattr(seller_row, 'iloc') else seller_row
    st.divider()
    st.subheader("📊 对标分析")
    st.caption(f"基准类型：{benchmark['类型']}（行业权重 {benchmark['权重']['行业']*100:.0f}%，内部权重 {benchmark['权重']['内部']*100:.0f}%）")
    bench_data = benchmark["数据"]
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**健康度评分对比**")
        st.metric("当前卖家", f"{rd['健康度评分']:.1f}")
        st.metric("基准值", f"{bench_data['健康度P50']:.1f}")
        diff = rd['健康度评分'] - bench_data['健康度P50']
        st.metric("差异", f"{diff:+.1f}", delta_color="normal")
    with cols[1]:
        st.markdown("**RMA%对比**")
        st.metric("当前卖家", f"{rd['RMA%']:.2f}%")
        st.metric("基准值", f"{bench_data['RMA平均']:.2f}%")
        rma_diff = rd['RMA%'] - bench_data['RMA平均']
        st.metric("差异", f"{rma_diff:+.2f}%", delta_color="inverse")
    with cols[2]:
        st.markdown("**GMV对比**")
        st.metric("当前卖家", f"${rd['GMV']:,.2f}")
        st.metric("基准值", f"${bench_data['GMV平均']:,.2f}")
        gmv_diff = rd['GMV'] - bench_data['GMV平均']
        st.metric("差异", f"${gmv_diff:+,.2f}", delta_color="normal")


def render_industry_benchmarks():
    st.divider()
    st.subheader("🌐 3C/消费电子行业基准参考")
    cols = st.columns(len(INDUSTRY_BENCHMARKS))
    for i, (key, bench) in enumerate(INDUSTRY_BENCHMARKS.items()):
        with cols[i]:
            st.markdown(f"**{bench['label']}**")
            st.caption(f"优秀: {bench['excellent']['label']}")
            st.caption(f"良好: {bench['good']['label']}")
            st.caption(f"一般: {bench['average']['label']}")
            st.caption(f"较差: {bench['poor']['label']}")


def render_history_trend(seller_history):
    st.subheader("📈 卖家健康度历史趋势")
    if not seller_history:
        st.info("该卖家暂无历史记录")
        return
    hist_df = pd.DataFrame(seller_history)
    hist_df["日期_dt"] = hist_df["日期"].apply(parse_date_any)
    valid = hist_df.dropna(subset=["日期_dt"])
    if not valid.empty:
        st.markdown("**健康度评分变化**")
        chart_data = valid.set_index("日期_dt")[["健康度评分"]]
        st.line_chart(chart_data, height=300)
    st.markdown("**历次记录明细**")
    display_hist = hist_df.copy()
    display_hist.insert(0, "序号", range(1, len(display_hist) + 1))
    st.dataframe(display_hist, width="stretch", height=300)
    if len(valid) >= 2:
        st.divider()
        st.subheader("📊 趋势分析")
        latest = valid.iloc[-1]
        prev = valid.iloc[-2]
        score_change = latest["健康度评分"] - prev["健康度评分"]
        gmv_change = latest["GMV"] - prev["GMV"]
        rma_change = latest["RMA%"] - prev["RMA%"]
        t1, t2, t3 = st.columns(3)
        with t1:
            st.metric("评分变化", f"{score_change:+.1f}", delta_color="normal")
        with t2:
            st.metric("GMV变化", f"${gmv_change:+,.2f}", delta_color="normal")
        with t3:
            st.metric("RMA变化", f"{rma_change:+.2f}%", delta_color="inverse")


def render_summary_stats(matched, result=None):
    st.divider()
    st.subheader("📈 汇总统计")
    total = len(result) if result is not None else len(matched)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("总SKU数", total)
    with s2:
        st.metric("已匹配", len(matched))
    with s3:
        st.metric("匹配率", f"{len(matched) / max(total, 1) * 100:.1f}%")
    with s4:
        high_risk = len(matched[matched["整改优先级"].isin(["极高", "高"])]) if "整改优先级" in matched.columns else 0
        st.metric("需整改SKU", high_risk)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**风险等级分布**")
        if "SKU风险等级" in matched.columns:
            st.bar_chart(matched["SKU风险等级"].value_counts())
    with c2:
        st.markdown("**库存深度分布**")
        if "库存深度层级" in matched.columns:
            st.bar_chart(matched["库存深度层级"].value_counts())


# ══════════════════════════════════════════════════════════
#  Plotly 配置
# ══════════════════════════════════════════════════════════

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(26,38,52,0.6)",
    font=dict(family="Rajdhani, Segoe UI, sans-serif", color="#ECE8E1", size=13),
    margin=dict(t=60, b=40, l=50, r=30),
    hoverlabel=dict(bgcolor="#1A2634", bordercolor="#FF4655", font=dict(color="#ECE8E1", size=13)),
)
DEFAULT_LEGEND = dict(bgcolor="rgba(26,38,52,0.8)", bordercolor="rgba(44,62,80,0.5)", borderwidth=1, font=dict(size=12))
AXIS_STYLE = dict(gridcolor="rgba(44,62,80,0.5)", zerolinecolor="rgba(44,62,80,0.8)")

def dark_title(text):
    return dict(text=text, font=dict(size=16, color="#ECE8E1", family="Rajdhani, sans-serif"), x=0.5, xanchor="center")


def get_time_range(option, custom_range=None):
    now = datetime.now()
    if option == "本周":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif option == "本月":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif option == "最近30天":
        return now - timedelta(days=30), now
    elif option == "自定义日期" and custom_range and len(custom_range) == 2:
        return custom_range[0], custom_range[1]
    return None, None


# ══════════════════════════════════════════════════════════
#  页面渲染
# ══════════════════════════════════════════════════════════

def render():
    st.set_page_config(page_title="卖家分析", layout="wide", initial_sidebar_state="expanded")
    inject_global_css()

    with st.sidebar:
        render_sidebar()

    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="margin-bottom: 0.25rem;">卖家分析</h1>
        <p style="color: #8B9CB6; font-size: 1rem; margin-top: 0;">上传销售表 + 库存表，自动生成运营分析报告</p>
    </div>
    """, unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════
    #  时间选择器
    # ══════════════════════════════════════════════════════════

    st.divider()
    filter_col_a, filter_col_b = st.columns([1, 3])
    with filter_col_a:
        time_option = st.radio(
            "📅 分析周期",
            options=["全部", "本周", "本月", "最近30天", "自定义日期"],
            horizontal=True,
            key="time_filter_option",
        )
    with filter_col_b:
        custom_dates = None
        if time_option == "自定义日期":
            custom_dates = st.date_input(
                "选择日期范围",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                key="custom_date_range",
            )

    start_date, end_date = get_time_range(time_option, custom_dates)
    all_seller_hist_raw = load_all_seller_history()
    all_seller_hist = filter_history_by_time(all_seller_hist_raw, start_date, end_date)

    grade_order = ["A", "B", "C", "D"]
    grade_colors = {"A": "#00D97E", "B": "#00B4D8", "C": "#FFB800", "D": "#FF4655"}
    grade_labels = {"A": "核心优质", "B": "高潜力", "C": "普通合规", "D": "高风险"}


    # ══════════════════════════════════════════════════════════
    #  卖家全景概览
    # ══════════════════════════════════════════════════════════

    if all_seller_hist:
        st.divider()
        st.subheader("📊 卖家全景概览")

        overview_records = []
        for sid, hist_list in all_seller_hist.items():
            if not hist_list:
                continue
            latest = hist_list[0]  # 历史记录倒序排列，第0条是最新数据
            grade = latest.get("等级", "D")
            need_followup = grade == "D"
            followup_reason = ["D级卖家"] if need_followup else []
            if len(hist_list) >= 2:
                current_rma = abs(float(latest.get("RMA%", 0)))
                prev_rma = abs(float(hist_list[-2].get("RMA%", 0)))
                if prev_rma > 0 and current_rma > prev_rma * 1.05:
                    need_followup = True
                    followup_reason.append("RMA%上升")
            overview_records.append({
                "卖家ID": sid,
                "健康度评分": latest.get("健康度评分", 0),
                "等级": grade,
                "最后一次分析": latest.get("日期", "未知"),
                "待跟进": "⚠️" if need_followup else "✅",
                "跟进原因": "、".join(followup_reason) if followup_reason else "-",
                "GMV": latest.get("GMV", 0),
                "RMA%": latest.get("RMA%", 0),
                "总毛利": latest.get("总毛利", 0),
                "SKU数": latest.get("SKU数", 0),
            })

        filtered_df = pd.DataFrame(overview_records).sort_values("健康度评分", ascending=False)

        if not filtered_df.empty:
            avg_score = filtered_df["健康度评分"].mean()
            total_gmv = filtered_df["GMV"].sum()

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("卖家总数", len(filtered_df))
            with k2:
                st.metric("平均健康度", f"{avg_score:.1f}")
            with k3:
                st.metric("总GMV", f"${total_gmv:,.0f}")
            with k4:
                st.metric("平均RMA%", f"{filtered_df['RMA%'].mean():.2f}%")

            # 等级分布饼图
            grade_counts = filtered_df["等级"].value_counts()
            fig_pie = px.pie(values=[grade_counts.get(g, 0) for g in grade_order],
                             names=[f"{g}-{grade_labels[g]}" for g in grade_order],
                             color_discrete_sequence=[grade_colors[g] for g in grade_order])
            fig_pie.update_layout(**DARK_LAYOUT, title=dark_title("卖家等级分布"), showlegend=True, legend=DEFAULT_LEGEND)

            # GMV柱状图
            top10 = filtered_df.nlargest(10, "GMV")
            fig_bar = px.bar(top10, x="卖家ID", y="GMV", color="等级", color_discrete_map=grade_colors)
            fig_bar.update_layout(**DARK_LAYOUT, title=dark_title("Top10卖家GMV"), xaxis_title="", yaxis_title="GMV ($)")
            fig_bar.update_xaxes(**AXIS_STYLE)
            fig_bar.update_yaxes(**AXIS_STYLE)

            col_pie, col_bar = st.columns(2)
            with col_pie:
                st.plotly_chart(fig_pie, width="stretch")
            with col_bar:
                st.plotly_chart(fig_bar, width="stretch")

            # 等级详细对比 - 分开的图表
            st.divider()
            st.subheader("📋 卖家等级详细对比")
            grade_stats = []
            for g in grade_order:
                g_df = filtered_df[filtered_df["等级"] == g]
                if not g_df.empty:
                    grade_stats.append({
                        "等级": f"{g}-{grade_labels[g]}",
                        "卖家数": len(g_df),
                        "平均健康度": g_df["健康度评分"].mean(),
                        "平均GMV": g_df["GMV"].mean(),
                        "平均RMA%": abs(g_df["RMA%"].mean()),
                        "平均毛利": g_df["总毛利"].mean(),
                        "平均SKU数": g_df["SKU数"].mean(),
                    })
            if grade_stats:
                gs_df = pd.DataFrame(grade_stats)

                # 图1：平均健康度
                fig_health = go.Figure()
                fig_health.add_trace(go.Bar(
                    x=gs_df["等级"], y=gs_df["平均健康度"],
                    marker_color=[grade_colors.get(g.split("-")[0], "#8B9CB6") for g in gs_df["等级"]],
                    text=gs_df["平均健康度"].apply(lambda x: f"{x:.1f}"),
                    textposition="auto"
                ))
                fig_health.update_layout(**DARK_LAYOUT, title=dark_title("各等级平均健康度"), height=300)
                fig_health.update_xaxes(**AXIS_STYLE)
                fig_health.update_yaxes(**AXIS_STYLE)

                # 图2：平均GMV
                fig_gmv = go.Figure()
                fig_gmv.add_trace(go.Bar(
                    x=gs_df["等级"], y=gs_df["平均GMV"],
                    marker_color=[grade_colors.get(g.split("-")[0], "#8B9CB6") for g in gs_df["等级"]],
                    text=gs_df["平均GMV"].apply(lambda x: f"${x:,.0f}"),
                    textposition="auto"
                ))
                fig_gmv.update_layout(**DARK_LAYOUT, title=dark_title("各等级平均GMV"), height=300)
                fig_gmv.update_xaxes(**AXIS_STYLE)
                fig_gmv.update_yaxes(**AXIS_STYLE)

                # 图3：平均RMA%
                fig_rma = go.Figure()
                fig_rma.add_trace(go.Bar(
                    x=gs_df["等级"], y=gs_df["平均RMA%"],
                    marker_color=[grade_colors.get(g.split("-")[0], "#8B9CB6") for g in gs_df["等级"]],
                    text=gs_df["平均RMA%"].apply(lambda x: f"{x:.2f}%"),
                    textposition="auto"
                ))
                fig_rma.update_layout(**DARK_LAYOUT, title=dark_title("各等级平均RMA%"), height=300)
                fig_rma.update_xaxes(**AXIS_STYLE)
                fig_rma.update_yaxes(**AXIS_STYLE)

                col_h, col_g, col_r = st.columns(3)
                with col_h:
                    st.plotly_chart(fig_health, width="stretch")
                with col_g:
                    st.plotly_chart(fig_gmv, width="stretch")
                with col_r:
                    st.plotly_chart(fig_rma, width="stretch")

            # GMV贡献排名
            st.divider()
            st.subheader("💰 卖家GMV贡献排名 Top15")
            top15 = filtered_df.nlargest(15, "GMV")
            fig_top15 = go.Figure()
            fig_top15.add_trace(go.Bar(x=top15["卖家ID"], y=top15["GMV"], marker_color=[grade_colors.get(g, "#8B9CB6") for g in top15["等级"]], text=top15["GMV"].apply(lambda x: f"${x:,.0f}"), textposition="auto", name="GMV"))
            fig_top15.add_trace(go.Scatter(x=top15["卖家ID"], y=top15["总毛利"], mode="lines+markers", name="总毛利", line=dict(color="#FFB800", width=3), marker=dict(size=8, color="#FFB800")))
            fig_top15.update_layout(**DARK_LAYOUT, title=dark_title("Top15卖家GMV与毛利趋势"), legend=DEFAULT_LEGEND, height=400)
            fig_top15.update_xaxes(title="卖家ID", **AXIS_STYLE)
            fig_top15.update_yaxes(title="金额 ($)", **AXIS_STYLE)
            st.plotly_chart(fig_top15, width="stretch")

            # 风险卖家监控
            st.divider()
            st.subheader("⚠️ 风险卖家监控")
            risk_df = filtered_df[(filtered_df["等级"] == "D") | (filtered_df["RMA%"] > 15) | (filtered_df["待跟进"] == "⚠️")].copy()
            if not risk_df.empty:
                st.markdown(f"**共 {len(risk_df)} 个风险卖家需要关注**")
                fig_risk = go.Figure()
                fig_risk.add_trace(go.Scatter(
                    x=risk_df["RMA%"], y=risk_df["GMV"], mode="markers+text", text=risk_df["卖家ID"],
                    textposition="top center", textfont=dict(size=11, color="#ECE8E1"),
                    marker=dict(size=risk_df["健康度评分"] * 0.8, color=risk_df["健康度评分"],
                                colorscale=[[0, "#FF4655"], [0.5, "#FFB800"], [1, "#00D97E"]],
                                showscale=True, colorbar=dict(title="健康度", tickfont=dict(color="#ECE8E1")),
                                line=dict(width=2, color="#2C3E50")),
                    name="卖家"))
                fig_risk.update_layout(**DARK_LAYOUT, title=dark_title("风险卖家分布（气泡大小=健康度）"), xaxis_title="RMA%", yaxis_title="GMV ($)", height=450)
                fig_risk.update_xaxes(**AXIS_STYLE)
                fig_risk.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig_risk, width="stretch")
            else:
                st.success("✅ 当前无风险卖家，运营状态良好")

            # 效能矩阵
            st.divider()
            st.subheader("🎯 卖家效能矩阵")
            avg_gmv_threshold = total_gmv / len(filtered_df) * 2
            filtered_df["效能分类"] = filtered_df.apply(lambda r:
                "高GMV低RMA" if r["GMV"] > avg_gmv_threshold and r["RMA%"] < 10 else
                "高GMV高RMA" if r["GMV"] > avg_gmv_threshold and r["RMA%"] >= 10 else
                "低GMV低RMA" if r["GMV"] <= avg_gmv_threshold and r["RMA%"] < 10 else
                "低GMV高RMA", axis=1)
            perf_colors = {"高GMV低RMA": "#00D97E", "高GMV高RMA": "#FFB800", "低GMV低RMA": "#00B4D8", "低GMV高RMA": "#FF4655"}
            fig_perf = go.Figure()
            for cat, color in perf_colors.items():
                cat_df = filtered_df[filtered_df["效能分类"] == cat]
                if not cat_df.empty:
                    fig_perf.add_trace(go.Scatter(x=cat_df["GMV"], y=cat_df["RMA%"], mode="markers", name=cat,
                        marker=dict(size=12, color=color, line=dict(width=1.5, color="#2C3E50")),
                        text=cat_df["卖家ID"], hovertemplate="卖家: %{text}<br>GMV: $%{x:,.0f}<br>RMA: %{y:.2f}%"))
            fig_perf.add_vline(x=avg_gmv_threshold, line_dash="dash", line_color="rgba(139,156,182,0.5)", annotation_text="GMV基准线", annotation_font_color="#8B9CB6")
            fig_perf.add_hline(y=10, line_dash="dash", line_color="rgba(139,156,182,0.5)", annotation_text="RMA基准线(10%)", annotation_font_color="#8B9CB6")
            fig_perf.update_layout(**DARK_LAYOUT, title=dark_title("卖家效能四象限矩阵"), xaxis_title="GMV ($)", yaxis_title="RMA%", legend=DEFAULT_LEGEND, height=450)
            fig_perf.update_xaxes(**AXIS_STYLE)
            fig_perf.update_yaxes(**AXIS_STYLE, range=[0, max(filtered_df["RMA%"].max() * 1.2, 20)])
            st.plotly_chart(fig_perf, width="stretch")

            # 卖家选择
            st.divider()
            detail_seller = st.selectbox(
                "选择卖家查看详情", options=[""] + list(filtered_df["卖家ID"]), key="detail_seller_select",
                format_func=lambda x: f"{x} - {grade_labels.get(filtered_df[filtered_df['卖家ID']==x]['等级'].iloc[0] if not filtered_df[filtered_df['卖家ID']==x].empty else 'D', '')}" if x else "请选择卖家...")
            if detail_seller:
                st.info(f"💡 请向下滚动到「历史回看」区域，选择卖家 **{detail_seller}** 查看详细分析")
        else:
            st.info("没有符合条件的卖家数据")


    # ══════════════════════════════════════════════════════════
    #  批量导入功能
    # ══════════════════════════════════════════════════════════

    st.divider()
    st.subheader("📦 批量导入卖家数据")

    # 显示上次导入结果（如果有）
    if st.session_state.get("batch_done"):
        st.divider()
        st.subheader("📊 上次导入结果")
        inv_upload_time = st.session_state.get("batch_inv_upload_time")
        if inv_upload_time:
            st.caption(f"📦 库存表上传时间：{inv_upload_time}")
        results = st.session_state.get("batch_results", [])
        errors = st.session_state.get("batch_errors", [])
        if results:
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, width="stretch")
            success_count = len(results_df[results_df["状态"] == "✅ 成功"])
            st.success(f"🎉 批量导入完成！成功处理 {success_count}/{len(results)} 条记录")
            if errors:
                with st.expander("❌ 查看错误详情", expanded=True):
                    for msg in errors:
                        st.error(msg)
        # 清除状态
        if st.button("🗑️ 清除结果", key="clear_batch_results"):
            st.session_state.pop("batch_done", None)
            st.session_state.pop("batch_results", None)
            st.session_state.pop("batch_errors", None)
            st.session_state.pop("batch_inv_upload_time", None)
            st.rerun()

    with st.expander("📖 批量导入说明", expanded=False):
        st.markdown("""
        **批量导入流程：**
        1. **上传多个销售表** - 每个卖家一个销售表文件（从BI系统导出）
        2. **上传库存表** - 支持单个或多个库存表文件（从BSD系统导出）
        3. **自动识别卖家ID** - 系统从销售表的Filter Info行或SKU编号自动提取卖家ID
        4. **自动匹配库存** - 根据SKU编号前缀自动匹配对应卖家的库存数据
        5. **一键处理** - 批量处理所有卖家数据并保存
        
        **库存-only模式（无销售数据）：**
        - 适用于已开通但暂无销售数据的站点（如新开通的B2B/CA站点）
        - 只上传库存表，系统自动创建空销售数据（GMV=0, RMA%=0）
        - 生成的JSON文件仅包含库存信息，用于后续销售数据同步
        """)

    # 导入模式选择
    import_mode = st.radio(
        "选择导入模式",
        ["标准模式（销售表 + 库存表）", "库存-only模式（仅库存表，无销售数据）"],
        key="import_mode",
        horizontal=True,
        help="库存-only模式适用于已开通但暂无销售数据的站点"
    )
    
    is_inventory_only = import_mode.startswith("库存-only")
    
    if is_inventory_only:
        st.info("💡 库存-only模式：只上传库存表，系统自动创建空销售数据（GMV=0, RMA%=0）")
        batch_sales_files = []
        batch_inv_files = st.file_uploader(
            "选择库存表文件（支持多文件）",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key="batch_inv_files_inv_only",
            help="上传BSD库存表，系统将为每个SKU创建空销售记录"
        )
    else:
        batch_col1, batch_col2 = st.columns(2)
        with batch_col1:
            st.markdown("**📤 上传销售表（支持多文件）**")
            batch_sales_files = st.file_uploader("选择销售表文件", type=["xlsx", "xls"], accept_multiple_files=True, key="batch_sales_files", help="每个卖家一个销售表，支持同时上传多个文件")
        with batch_col2:
            st.markdown("**📤 上传库存表（支持多文件）**")
            batch_inv_files = st.file_uploader("选择库存表文件", type=["xlsx", "xls"], accept_multiple_files=True, key="batch_inv_files", help="库存表可以是单个卖家的，也可以是所有卖家汇总的")

    if is_inventory_only and batch_inv_files:
        # 库存-only模式：只上传库存表
        st.info(f"已选择 {len(batch_inv_files)} 个库存表文件")
        inv_upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_inv_dfs = []
        for inv_file in batch_inv_files:
            try:
                inv_file.seek(0)
                inv_df = process_inventory_file(inv_file)
                all_inv_dfs.append(inv_df)
            except Exception as e:
                st.error(f"❌ 读取库存表 {inv_file.name} 失败: {e}")

        if all_inv_dfs:
            combined_inv_df = pd.concat(all_inv_dfs, ignore_index=True)
            if "Inventory" in combined_inv_df.columns and "NeweggItemNumber" in combined_inv_df.columns:
                agg_cols = {c: ("sum" if c == "Inventory" else "first") for c in combined_inv_df.columns if c != "NeweggItemNumber"}
                agg_cols["NeweggItemNumber"] = "first"
                combined_inv_df = combined_inv_df.groupby("NeweggItemNumber", as_index=False).agg(agg_cols)
            st.success(f"✅ 库存表合并完成，共 {len(combined_inv_df)} 条SKU记录")
            st.caption(f"📦 库存表上传时间：{inv_upload_time}")

            # 从库存表中提取卖家ID（通过NeweggItemNumber前缀）
            seller_mapping_inv = {}
            for _, row in combined_inv_df.iterrows():
                sku = str(row.get("NeweggItemNumber", ""))
                if sku.startswith("9SI") and len(sku) > 6:
                    seller_id = sku[3:7]
                    if seller_id not in seller_mapping_inv:
                        seller_mapping_inv[seller_id] = []
                    seller_mapping_inv[seller_id].append(row)
            
            if seller_mapping_inv:
                st.success(f"✅ 从库存表识别到 {len(seller_mapping_inv)} 个卖家")
                display_data = [{"卖家ID": sid, "SKU数": len(skus)} for sid, skus in seller_mapping_inv.items()]
                st.dataframe(pd.DataFrame(display_data), width="stretch")

                if st.button("🚀 开始库存-only导入", key="inv_only_import_btn", type="primary"):
                    batch_progress = st.progress(0)
                    batch_status = st.empty()
                    results = []
                    error_messages = []
                    total_tasks = len(seller_mapping_inv)
                    task_idx = 0

                    for seller_id, seller_skus in seller_mapping_inv.items():
                        task_idx += 1
                        batch_progress.progress(task_idx / total_tasks)
                        batch_status.text(f"正在处理 {seller_id} ({task_idx}/{total_tasks})...")

                        try:
                            # 创建空销售数据DataFrame
                            empty_sales_data = []
                            for sku_row in seller_skus:
                                empty_sales_data.append({
                                    "NeweggItemNumber": sku_row.get("NeweggItemNumber", ""),
                                    "Item Description": f"库存商品-{sku_row.get('NeweggItemNumber', '')}",
                                    "GMV": 0,
                                    "RMA %": 0,
                                    "Total Margin": 0,
                                    "Net Quantity Sold": 0,
                                    "SKU Count": 1,
                                })
                            sales_df = pd.DataFrame(empty_sales_data)
                            
                            # 创建卖家库存DataFrame
                            seller_inv_df = pd.DataFrame([{
                                "NeweggItemNumber": sku_row.get("NeweggItemNumber", ""),
                                "Inventory": sku_row.get("Inventory", 0),
                            } for sku_row in seller_skus])
                            
                            # 合并数据
                            merged = merge_and_generate(sales_df, seller_inv_df, 0, 0, 30)
                            
                            if not merged.empty:
                                # 计算健康度
                                seller_health = calc_seller_health_from_sku(merged)
                                seller_row = seller_health[seller_health["卖家ID"] == seller_id] if not seller_health.empty else pd.DataFrame()
                                
                                if not seller_row.empty:
                                    health_record = {
                                        "日期": f"{datetime.now().strftime('%Y/%m/%d')} (库存-only)",
                                        "健康度评分": float(seller_row.iloc[0]["健康度评分"]),
                                        "等级": seller_row.iloc[0]["等级"],
                                        "GMV": float(seller_row.iloc[0]["GMV"]),
                                        "RMA%": float(seller_row.iloc[0]["RMA%"]),
                                        "总毛利": float(seller_row.iloc[0]["总毛利"]),
                                        "总销量": float(seller_row.iloc[0]["总销量"]),
                                        "SKU数": int(seller_row.iloc[0]["SKU数"]),
                                    }
                                    date_period = datetime.now().strftime("%Y%m01") + "-" + datetime.now().strftime("%Y%m%d")
                                    save_sku_analysis(seller_id, date_period, health_record["日期"], merged, seller_summary=health_record, inv_upload_time=inv_upload_time)
                                    results.append({"卖家ID": seller_id, "状态": "✅ 成功", "健康度": f"{seller_row.iloc[0]['健康度评分']:.1f}", "等级": seller_row.iloc[0]["等级"], "SKU数": len(merged)})
                                else:
                                    results.append({"卖家ID": seller_id, "状态": "⚠️ 警告", "原因": "无法计算健康度"})
                            else:
                                results.append({"卖家ID": seller_id, "状态": "❌ 失败", "原因": "数据合并失败"})
                        except Exception as e:
                            error_msg = f"{seller_id}: {str(e)}"
                            error_messages.append(error_msg)
                            results.append({"卖家ID": seller_id, "状态": "❌ 失败", "原因": str(e)})

                    batch_progress.empty()
                    batch_status.empty()

                    # 保存结果到session_state，防止刷新丢失
                    st.session_state["batch_results"] = results
                    st.session_state["batch_errors"] = error_messages
                    st.session_state["batch_inv_upload_time"] = inv_upload_time
                    st.session_state["batch_done"] = True
                    st.rerun()
            else:
                st.warning("⚠️ 未能从库存表中识别任何卖家ID，请检查库存表格式")
    elif batch_sales_files:
        st.info(f"已选择 {len(batch_sales_files)} 个销售表文件")
        seller_mapping = {}  # {seller_id: [(filename, date_period, date_readable), ...]}
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i, file in enumerate(batch_sales_files):
            progress_bar.progress((i + 1) / len(batch_sales_files))
            status_text.text(f"正在分析: {file.name}")
            try:
                raw = pd.read_excel(file, engine="openpyxl", header=None, nrows=25)
                file.seek(0)
                seller_id = extract_seller_id_from_file(raw)
                if seller_id:
                    # 提取日期区间
                    from src.web.seller_analysis import extract_date_period
                    date_period, date_readable = extract_date_period(file)
                    if seller_id not in seller_mapping:
                        seller_mapping[seller_id] = []
                    seller_mapping[seller_id].append((file.name, date_period, date_readable))
                else:
                    st.warning(f"⚠️ 无法从 {file.name} 中识别卖家ID")
            except Exception as e:
                st.error(f"❌ 读取 {file.name} 失败: {e}")
        progress_bar.empty()
        status_text.empty()

        if seller_mapping:
            st.success(f"✅ 成功识别 {len(seller_mapping)} 个卖家")
            # 显示每个卖家的文件列表
            display_data = []
            for sid, files_info in seller_mapping.items():
                for fname, dp, dr in files_info:
                    display_data.append({"卖家ID": sid, "销售表文件": fname, "日期区间": dr})
            st.dataframe(pd.DataFrame(display_data), width="stretch")

            if batch_inv_files:
                st.info(f"已选择 {len(batch_inv_files)} 个库存表文件")
                inv_upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_inv_dfs = []
                for inv_file in batch_inv_files:
                    try:
                        inv_file.seek(0)
                        inv_df = process_inventory_file(inv_file)
                        all_inv_dfs.append(inv_df)
                    except Exception as e:
                        st.error(f"❌ 读取库存表 {inv_file.name} 失败: {e}")

                if all_inv_dfs:
                    combined_inv_df = pd.concat(all_inv_dfs, ignore_index=True)
                    if "Inventory" in combined_inv_df.columns and "NeweggItemNumber" in combined_inv_df.columns:
                        agg_cols = {c: ("sum" if c == "Inventory" else "first") for c in combined_inv_df.columns if c != "NeweggItemNumber"}
                        agg_cols["NeweggItemNumber"] = "first"
                        combined_inv_df = combined_inv_df.groupby("NeweggItemNumber", as_index=False).agg(agg_cols)
                    st.success(f"✅ 库存表合并完成，共 {len(combined_inv_df)} 条SKU记录")
                    st.caption(f"📦 库存表上传时间：{inv_upload_time}")

                    if st.button("🚀 开始批量导入", key="batch_import_btn", type="primary"):
                        batch_progress = st.progress(0)
                        batch_status = st.empty()
                        results = []
                        error_messages = []
                        total_tasks = sum(len(files) for files in seller_mapping.values())
                        task_idx = 0

                        for seller_id, files_info in seller_mapping.items():
                            for fname, date_period, date_readable in files_info:
                                task_idx += 1
                                batch_progress.progress(task_idx / total_tasks)
                                batch_status.text(f"正在处理 {seller_id} - {date_readable} ({task_idx}/{total_tasks})...")

                                # 查找对应的文件对象
                                sales_file = None
                                for f in batch_sales_files:
                                    if f.name == fname:
                                        sales_file = f
                                        break

                                if sales_file is None:
                                    error_msg = f"找不到文件: {fname}"
                                    error_messages.append(error_msg)
                                    results.append({"卖家ID": seller_id, "日期": date_readable, "状态": "❌ 失败", "原因": error_msg})
                                    continue

                                try:
                                    sales_file.seek(0)
                                    sales_result = process_sales_file(sales_file)
                                    if sales_result[0] is None:
                                        error_msg = "销售表解析失败"
                                        results.append({"卖家ID": seller_id, "日期": date_readable, "状态": "❌ 失败", "原因": error_msg})
                                        continue
                                    sales_df, total_gmv, total_margin, _, _ = sales_result

                                    # 检查库存表是否有NeweggItemNumber列
                                    if "NeweggItemNumber" in combined_inv_df.columns:
                                        seller_inv_df = combined_inv_df[combined_inv_df["NeweggItemNumber"].str.startswith(f"9SI{seller_id}", na=False)]
                                    else:
                                        # 如果库存表没有NeweggItemNumber列，创建一个空的库存表
                                        seller_inv_df = pd.DataFrame(columns=["NeweggItemNumber", "Inventory"])
                                    merged = merge_and_generate(sales_df, seller_inv_df, total_gmv, total_margin, calc_period_days(date_period))
                                    inv_col = next((c for c in merged.columns if "inventory" in str(c).lower() or c == "Inventory"), None)
                                    matched = merged[merged[inv_col].notna() & (merged[inv_col].astype(str).str.strip() != "") & (merged[inv_col].astype(str).str.strip() != "nan")] if inv_col else merged
                                    matched = matched.sort_values("整改优先级得分", ascending=False)
                                    seller_health = calc_seller_health_from_sku(matched)
                                    seller_row = seller_health[seller_health["卖家ID"] == seller_id] if not seller_health.empty else pd.DataFrame()
                                    if not seller_row.empty:
                                        health_record = {
                                            "日期": date_readable,
                                            "健康度评分": float(seller_row.iloc[0]["健康度评分"]),
                                            "等级": seller_row.iloc[0]["等级"],
                                            "GMV": float(seller_row.iloc[0]["GMV"]),
                                            "RMA%": float(seller_row.iloc[0]["RMA%"]),
                                            "总毛利": float(seller_row.iloc[0]["总毛利"]),
                                            "总销量": float(seller_row.iloc[0]["总销量"]),
                                            "SKU数": int(seller_row.iloc[0]["SKU数"]),
                                        }
                                        save_sku_analysis(seller_id, date_period, date_readable, matched, seller_summary=health_record, inv_upload_time=inv_upload_time)
                                        results.append({"卖家ID": seller_id, "日期": date_readable, "状态": "✅ 成功", "健康度": f"{seller_row.iloc[0]['健康度评分']:.1f}", "等级": seller_row.iloc[0]["等级"], "SKU数": len(matched)})
                                    else:
                                        results.append({"卖家ID": seller_id, "日期": date_readable, "状态": "⚠️ 警告", "原因": "无法计算健康度"})
                                except Exception as e:
                                    import traceback
                                    error_msg = f"{seller_id} {date_readable}: {str(e)}"
                                    error_messages.append(error_msg)
                                    results.append({"卖家ID": seller_id, "日期": date_readable, "状态": "❌ 失败", "原因": str(e)})

                        batch_progress.empty()
                        batch_status.empty()

                        # 保存结果到session_state，防止刷新丢失
                        st.session_state["batch_results"] = results
                        st.session_state["batch_errors"] = error_messages
                        st.session_state["batch_inv_upload_time"] = inv_upload_time
                        st.session_state["batch_done"] = True
                        st.rerun()
            else:
                st.warning("⚠️ 请先上传库存表文件")
        else:
            st.warning("⚠️ 未能识别任何卖家ID，请检查销售表格式")
    else:
        st.info("💡 请上传销售表文件开始批量导入")


    # ══════════════════════════════════════════════════════════
    #  ══════════════════════════════════════════════════════════
    #  库存管理（统一入口：智能判断更新/创建）
    # ══════════════════════════════════════════════════════════

    st.divider()
    st.subheader("📦 库存管理")
    st.caption("上传库存表，系统自动判断：已有数据→更新库存，没有数据→创建新记录")

    inv_update_col1, inv_update_col2 = st.columns([2, 1])
    with inv_update_col1:
        inv_update_file = st.file_uploader("选择库存表文件", type=["xlsx", "xls"], key="inv_update_file", help="上传BSD库存表，系统自动处理更新或创建")
    with inv_update_col2:
        st.write("")
        st.write("")
        if inv_update_file and st.button("🔄 处理库存", key="inv_update_btn", type="primary"):
            with st.spinner("正在处理库存数据..."):
                try:
                    # 读取库存表
                    inv_update_file.seek(0)
                    inv_df = process_inventory_file(inv_update_file)

                    if inv_df is None or inv_df.empty:
                        st.error("❌ 库存表解析失败或为空")
                    else:
                        # 检查必要的列
                        if "NeweggItemNumber" not in inv_df.columns:
                            st.error("❌ 库存表缺少 NeweggItemNumber 列")
                        else:
                            # 处理库存数据
                            sku_analysis_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "sku_analysis")
                            updated_count = 0
                            created_count = 0
                            files_updated = 0
                            files_created = 0
                            update_details = []
                            create_details = []

                            # 按卖家分组库存数据
                            seller_inv_map = {}
                            for _, inv_row in inv_df.iterrows():
                                sku = str(inv_row.get("NeweggItemNumber", "")).strip()
                                if sku and sku.startswith("9SI") and len(sku) > 6:
                                    seller_id = sku[3:7]
                                    if seller_id not in seller_inv_map:
                                        seller_inv_map[seller_id] = []
                                    seller_inv_map[seller_id].append(inv_row)

                            # 处理每个卖家
                            for seller_id, inv_rows in seller_inv_map.items():
                                seller_path = os.path.join(sku_analysis_dir, seller_id)
                                json_files = glob.glob(os.path.join(seller_path, "*.json")) if os.path.exists(seller_path) else []

                                if json_files:
                                    # 已有数据 → 更新库存
                                    for json_file in json_files:
                                        try:
                                            with open(json_file, "r", encoding="utf-8") as f:
                                                data = json.load(f)

                                            records = data.get("records", [])
                                            file_updated = False
                                            skus_updated = 0

                                            # 获取JSON中已有的SKU列表
                                            existing_skus = set()
                                            for record in records:
                                                sku = record.get("NeweggItemNumber") or record.get("NeweggSku#")
                                                if sku:
                                                    existing_skus.add(str(sku).strip())

                                            # 更新已有SKU的库存
                                            for record in records:
                                                sku = record.get("NeweggItemNumber") or record.get("NeweggSku#")
                                                if not sku:
                                                    continue

                                                sku = str(sku).strip()
                                                inv_match = [r for r in inv_rows if str(r.get("NeweggItemNumber", "")).strip() == sku]

                                                if inv_match:
                                                    inv_row = inv_match[0]

                                                    # 更新库存相关字段
                                                    for field in ["Inventory", "FulfillmentType", "SellingPrice", "WarehouseLocation", "ItemCondition", "ActivationStatus", "Platform"]:
                                                        if field in inv_row.index and pd.notna(inv_row[field]):
                                                            val = inv_row[field]
                                                            # 转换numpy类型为Python原生类型
                                                            if hasattr(val, 'item'):
                                                                val = val.item()
                                                            elif isinstance(val, (np.integer,)):
                                                                val = int(val)
                                                            elif isinstance(val, (np.floating,)):
                                                                val = float(val)
                                                            record[field] = val

                                                    # 更新库存深度层级
                                                    inventory = record.get("Inventory", 0)
                                                    try:
                                                        inv_val = float(inventory)
                                                    except:
                                                        inv_val = 0
                                                    if inv_val <= 0:
                                                        record["库存深度层级"] = "零库存"
                                                    elif inv_val <= 9:
                                                        record["库存深度层级"] = "浅库存"
                                                    elif inv_val <= 49:
                                                        record["库存深度层级"] = "中库存"
                                                    else:
                                                        record["库存深度层级"] = "深库存"

                                                    # 更新处置建议
                                                    rma_pct = record.get("RMA %", 0) or 0
                                                    efficiency = record.get("SKU效能等级", "低动销")
                                                    try:
                                                        rma = abs(float(rma_pct))
                                                    except:
                                                        rma = 0
                                                    if rma > 80:
                                                        risk = "高危"
                                                    elif rma >= 10:
                                                        risk = "中危"
                                                    else:
                                                        risk = "低危"

                                                    if risk == "高危" and record["库存深度层级"] in ["浅库存", "零库存"]:
                                                        record["处置建议"] = "立即下架止损"
                                                    elif risk == "高危" and record["库存深度层级"] == "中库存":
                                                        record["处置建议"] = "整改观察+限量销售，7天未改善则下架"
                                                    elif risk == "高危" and record["库存深度层级"] == "深库存":
                                                        record["处置建议"] = "整改+清库存，7天观察期"
                                                    elif risk == "中危" and efficiency in ["低动销", "零销负销"]:
                                                        record["处置建议"] = "限制补货，优先清理库存"
                                                    elif risk == "中危" and efficiency in ["核心主力", "潜力培育"]:
                                                        record["处置建议"] = "维持销售，加强品质监控"
                                                    elif risk == "低危" and efficiency == "零销负销":
                                                        record["处置建议"] = "直接清退下架"
                                                    elif risk == "低危" and efficiency == "低动销":
                                                        record["处置建议"] = "评估是否保留"
                                                    else:
                                                        record["处置建议"] = "正常运营，持续监控RMA变化"

                                                    file_updated = True
                                                    skus_updated += 1

                                            # 添加库存中有但JSON中没有的新SKU
                                            new_skus_added = 0
                                            for inv_row in inv_rows:
                                                sku = str(inv_row.get("NeweggItemNumber", "")).strip()
                                                if sku and sku not in existing_skus:
                                                    # 创建新SKU记录
                                                    new_record = {
                                                        "AM/CM": "",
                                                        "Condition": inv_row.get("ItemCondition", "New"),
                                                        "Category": "",
                                                        "Subcategory": "",
                                                        "SellerID": seller_id,
                                                        "SellerName": "",
                                                        "NeweggSku#": sku,
                                                        "Brand": "",
                                                        "ItemDescription": inv_row.get("ItemDescription", ""),
                                                        "GMV": 0,
                                                        "RMA %": 0,
                                                        "Total Margin": 0,
                                                        "Net Quantity Sold": 0,
                                                        "SKU Count": 1,
                                                        "NeweggItemNumber": sku,
                                                        "ActivationStatus": inv_row.get("ActivationStatus", "Active"),
                                                        "FulfillmentType": inv_row.get("FulfillmentType", ""),
                                                        "WarehouseLocation": inv_row.get("WarehouseLocation", ""),
                                                        "Inventory": inv_row.get("Inventory", 0),
                                                        "SellingPrice": inv_row.get("SellingPrice", 0),
                                                        "Platform": inv_row.get("Platform", ""),
                                                        "ShortTitle": inv_row.get("ItemDescription", ""),
                                                        "商品成色": "全新品",
                                                        "品类": "其他配件",
                                                        "客单价": 0,
                                                        "单件毛利": 0,
                                                        "单SKU毛利率(%)": 0,
                                                        "GMV贡献占比(%)": 0,
                                                        "毛利贡献占比(%)": 0,
                                                        "退货损失金额": 0,
                                                        "退货件数": 0,
                                                        "退货毛利侵蚀率": 0,
                                                        "日均销量": 0,
                                                        "库存深度层级": "深库存" if inv_row.get("Inventory", 0) > 49 else "中库存",
                                                        "SKU风险等级": "低危",
                                                        "SKU效能等级": "零销负销",
                                                        "客单价分层": "中客单",
                                                        "整改优先级得分": 5.0,
                                                        "整改优先级": "低",
                                                        "处置建议": "评估是否保留",
                                                        "ItemCondition": inv_row.get("ItemCondition", "New")
                                                    }
                                                    records.append(new_record)
                                                    new_skus_added += 1
                                                    file_updated = True

                                            if file_updated:
                                                # 更新库存上传时间
                                                data['inv_upload_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                # 先写入临时文件，验证成功后再替换原文件
                                                import tempfile
                                                temp_file = json_file + ".tmp"
                                                try:
                                                    with open(temp_file, "w", encoding="utf-8") as f:
                                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                                    # 验证临时文件可以正常读取
                                                    with open(temp_file, "r", encoding="utf-8") as f:
                                                        json.load(f)
                                                    # 验证通过，替换原文件
                                                    import shutil
                                                    shutil.move(temp_file, json_file)
                                                    files_updated += 1
                                                    updated_count += skus_updated
                                                    update_details.append(f"{seller_id}: 更新{skus_updated}个SKU" + (f", 新增{new_skus_added}个" if new_skus_added > 0 else ""))
                                                except Exception as e:
                                                    # 写入失败，清理临时文件
                                                    if os.path.exists(temp_file):
                                                        os.remove(temp_file)

                                        except Exception as e:
                                            pass
                                else:
                                    # 没有数据 → 创建新记录
                                    try:
                                        # 创建卖家目录
                                        os.makedirs(seller_path, exist_ok=True)

                                        # 创建空销售数据
                                        records = []
                                        for inv_row in inv_rows:
                                            sku = str(inv_row.get("NeweggItemNumber", "")).strip()
                                            if sku:
                                                new_record = {
                                                    "AM/CM": "",
                                                    "Condition": inv_row.get("ItemCondition", "New"),
                                                    "Category": "",
                                                    "Subcategory": "",
                                                    "SellerID": seller_id,
                                                    "SellerName": "",
                                                    "NeweggSku#": sku,
                                                    "Brand": "",
                                                    "ItemDescription": inv_row.get("ItemDescription", ""),
                                                    "GMV": 0,
                                                    "RMA %": 0,
                                                    "Total Margin": 0,
                                                    "Net Quantity Sold": 0,
                                                    "SKU Count": 1,
                                                    "NeweggItemNumber": sku,
                                                    "ActivationStatus": inv_row.get("ActivationStatus", "Active"),
                                                    "FulfillmentType": inv_row.get("FulfillmentType", ""),
                                                    "WarehouseLocation": inv_row.get("WarehouseLocation", ""),
                                                    "Inventory": inv_row.get("Inventory", 0),
                                                    "SellingPrice": inv_row.get("SellingPrice", 0),
                                                    "Platform": inv_row.get("Platform", ""),
                                                    "ShortTitle": inv_row.get("ItemDescription", ""),
                                                    "商品成色": "全新品",
                                                    "品类": "其他配件",
                                                    "客单价": 0,
                                                    "单件毛利": 0,
                                                    "单SKU毛利率(%)": 0,
                                                    "GMV贡献占比(%)": 0,
                                                    "毛利贡献占比(%)": 0,
                                                    "退货损失金额": 0,
                                                    "退货件数": 0,
                                                    "退货毛利侵蚀率": 0,
                                                    "日均销量": 0,
                                                    "库存深度层级": "深库存" if inv_row.get("Inventory", 0) > 49 else "中库存",
                                                    "SKU风险等级": "低危",
                                                    "SKU效能等级": "零销负销",
                                                    "客单价分层": "中客单",
                                                    "整改优先级得分": 5.0,
                                                    "整改优先级": "低",
                                                    "处置建议": "评估是否保留",
                                                    "ItemCondition": inv_row.get("ItemCondition", "New")
                                                }
                                                records.append(new_record)

                                        # 创建JSON文件
                                        date_period = datetime.now().strftime("%Y%m01") + "-" + datetime.now().strftime("%Y%m%d")
                                        data = {
                                            "seller_id": seller_id,
                                            "date_period": date_period,
                                            "date_readable": f"{datetime.now().strftime('%Y/%m/%d')} (库存-only)",
                                            "total_skus": len(records),
                                            "seller_summary": {
                                                "日期": f"{datetime.now().strftime('%Y/%m/%d')} (库存-only)",
                                                "健康度评分": 28.0,
                                                "等级": "D",
                                                "GMV": 0,
                                                "RMA%": 0,
                                                "总毛利": 0,
                                                "总销量": 0,
                                                "SKU数": len(records)
                                            },
                                            "records": records,
                                            "inv_upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }

                                        # 保存JSON文件
                                        json_file = os.path.join(seller_path, f"{date_period}.json")
                                        import tempfile
                                        temp_file = json_file + ".tmp"
                                        try:
                                            with open(temp_file, "w", encoding="utf-8") as f:
                                                json.dump(data, f, ensure_ascii=False, indent=2)
                                            # 验证临时文件可以正常读取
                                            with open(temp_file, "r", encoding="utf-8") as f:
                                                json.load(f)
                                            # 验证通过，替换原文件
                                            import shutil
                                            shutil.move(temp_file, json_file)
                                            files_created += 1
                                            created_count += len(records)
                                            create_details.append(f"{seller_id}: 创建{len(records)}个SKU")
                                        except Exception as e:
                                            # 写入失败，清理临时文件
                                            if os.path.exists(temp_file):
                                                os.remove(temp_file)

                                    except Exception as e:
                                        pass

                            # 显示结果
                            if files_updated > 0 or files_created > 0:
                                st.success(f"✅ 库存处理完成！")
                                if files_updated > 0:
                                    st.info(f"📊 更新了 {files_updated} 个JSON文件，共 {updated_count} 条SKU记录")
                                    for detail in update_details:
                                        st.write(f"  - {detail}")
                                if files_created > 0:
                                    st.info(f"🆕 创建了 {files_created} 个JSON文件，共 {created_count} 条SKU记录")
                                    for detail in create_details:
                                        st.write(f"  - {detail}")
                            else:
                                st.warning("⚠️ 没有找到需要处理的SKU，请检查库存表格式")

                except Exception as e:
                    st.error(f"❌ 处理失败: {e}")
                    st.code(traceback.format_exc())


    # ══════════════════════════════════════════════════════════
    #  重算指标功能
    # ══════════════════════════════════════════════════════════

    st.divider()
    st.subheader("🔢 重算指标")
    st.caption("更新库存后，重新计算所有衍生指标（健康度、库存深度、处置建议等）")

    recalc_col1, recalc_col2 = st.columns([2, 1])
    with recalc_col1:
        recalc_seller = st.text_input("指定卖家ID（留空=重算所有）", key="recalc_seller", placeholder="如：VRD4")
    with recalc_col2:
        st.write("")
        st.write("")
        if st.button("🔄 重算指标", key="recalc_btn", type="primary"):
            with st.spinner("正在重算指标..."):
                try:
                    sku_analysis_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "sku_analysis")
                    recalc_count = 0
                    recalc_sellers = 0

                    for seller_dir in os.listdir(sku_analysis_dir):
                        if recalc_seller and seller_dir != recalc_seller:
                            continue

                        seller_path = os.path.join(sku_analysis_dir, seller_dir)
                        if not os.path.isdir(seller_path):
                            continue

                        for json_file in glob.glob(os.path.join(seller_path, "*.json")):
                            try:
                                with open(json_file, "r", encoding="utf-8") as f:
                                    data = json.load(f)

                                records = data.get("records", [])
                                total_gmv = 0
                                total_margin = 0
                                total_qty = 0

                                for record in records:
                                    gmv = record.get("GMV", 0) or 0
                                    margin = record.get("Total Margin", 0) or 0
                                    qty = record.get("Net Quantity Sold", 0) or 0
                                    rma = record.get("RMA %", 0) or 0
                                    inventory = record.get("Inventory", 0) or 0

                                    total_gmv += gmv
                                    total_margin += margin
                                    total_qty += qty

                                    # 计算衍生指标
                                    unit_price = gmv / qty if qty > 0 else 0
                                    unit_margin = margin / qty if qty > 0 else 0
                                    margin_rate = (margin / gmv * 100) if gmv > 0 else 0
                                    return_loss = abs(gmv) * abs(rma) / 100 if rma else 0
                                    return_qty = math.ceil(qty * abs(rma) / 100 / (1 - abs(rma) / 100)) if rma and abs(rma) < 100 else 0
                                    return_erosion = return_loss / margin if margin > 0 else 0
                                    daily_sales = qty / 20

                                    record['客单价'] = round(unit_price, 2)
                                    record['单件毛利'] = round(unit_margin, 2)
                                    record['单SKU毛利率(%)'] = round(margin_rate, 2)
                                    record['退货损失金额'] = round(return_loss, 2)
                                    record['退货件数'] = return_qty
                                    record['退货毛利侵蚀率'] = round(return_erosion, 4)
                                    record['日均销量'] = round(daily_sales, 2)

                                    # 更新分级标签
                                    try:
                                        inv_val = float(inventory)
                                    except:
                                        inv_val = 0
                                    if inv_val <= 0:
                                        record['库存深度层级'] = "零库存"
                                    elif inv_val <= 9:
                                        record['库存深度层级'] = "浅库存"
                                    elif inv_val <= 49:
                                        record['库存深度层级'] = "中库存"
                                    else:
                                        record['库存深度层级'] = "深库存"

                                    try:
                                        rma_val = abs(float(rma))
                                    except:
                                        rma_val = 0
                                    if rma_val > 80:
                                        record['SKU风险等级'] = "高危"
                                    elif rma_val >= 10:
                                        record['SKU风险等级'] = "中危"
                                    else:
                                        record['SKU风险等级'] = "低危"

                                    if qty >= 10:
                                        record['SKU效能等级'] = "核心主力"
                                    elif qty >= 3:
                                        record['SKU效能等级'] = "潜力培育"
                                    elif qty >= 1:
                                        record['SKU效能等级'] = "低动销"
                                    else:
                                        record['SKU效能等级'] = "零销负销"

                                    if unit_price > 500:
                                        record['客单价分层'] = "高客单"
                                    elif unit_price >= 100:
                                        record['客单价分层'] = "中客单"
                                    else:
                                        record['客单价分层'] = "低客单"

                                # 更新卖家汇总
                                avg_rma = sum(abs(r.get("RMA %", 0) or 0) for r in records) / len(records) if records else 0
                                margin_rate = (total_margin / total_gmv * 100) if total_gmv > 0 else 0
                                sku_count = len(records)

                                # 健康度评分
                                score = 0
                                score += min(30, total_gmv / 50000 * 30)
                                score += min(25, total_margin / 10000 * 25)
                                if avg_rma <= 2: score += 20
                                elif avg_rma <= 5: score += 16
                                elif avg_rma <= 8: score += 12
                                elif avg_rma <= 15: score += 8
                                elif avg_rma <= 25: score += 4
                                if total_qty >= 50: score += 10
                                elif total_qty >= 20: score += 7
                                elif total_qty >= 5: score += 4
                                elif total_qty > 0: score += 2
                                if sku_count >= 20: score += 10
                                elif sku_count >= 10: score += 7
                                elif sku_count >= 5: score += 4
                                elif sku_count > 0: score += 2
                                if margin_rate >= 10: score += 5
                                elif margin_rate >= 5: score += 4
                                elif margin_rate > 0: score += 2

                                if score >= 75: grade = 'A'
                                elif score >= 60: grade = 'B'
                                elif score >= 45: grade = 'C'
                                else: grade = 'D'

                                data['seller_summary'] = {
                                    'GMV': round(total_gmv, 2),
                                    'RMA%': round(avg_rma, 4),
                                    '总毛利': round(total_margin, 2),
                                    '总销量': total_qty,
                                    'SKU数': sku_count,
                                    '健康度评分': round(score, 1),
                                    '等级': grade
                                }

                                # 写入临时文件
                                temp_file = json_file + ".tmp"
                                try:
                                    with open(temp_file, "w", encoding="utf-8") as f:
                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                    with open(temp_file, "r", encoding="utf-8") as f:
                                        json.load(f)
                                    shutil.move(temp_file, json_file)
                                    recalc_count += 1
                                except:
                                    if os.path.exists(temp_file):
                                        os.remove(temp_file)

                            except:
                                pass

                        if recalc_count > 0:
                            recalc_sellers += 1

                    st.success(f"✅ 指标重算完成！")
                    st.info(f"📊 重算 {recalc_sellers} 个卖家，共 {recalc_count} 个JSON文件")

                except Exception as e:
                    st.error(f"❌ 重算失败: {e}")
                    st.code(traceback.format_exc())


    # ══════════════════════════════════════════════════════════
    #  数据质量检查
    # ══════════════════════════════════════════════════════════

    st.divider()
    st.subheader("🔍 数据质量检查")
    st.caption("检测损坏的JSON文件，防止数据分析出错")

    if st.button("🔍 检查数据质量", key="check_quality_btn", type="primary"):
        with st.spinner("正在检查..."):
            try:
                sku_analysis_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "sku_analysis")
                corrupted = []
                total_files = 0

                for seller_dir in os.listdir(sku_analysis_dir):
                    seller_path = os.path.join(sku_analysis_dir, seller_dir)
                    if not os.path.isdir(seller_path):
                        continue

                    for json_file in glob.glob(os.path.join(seller_path, "*.json")):
                        total_files += 1
                        try:
                            with open(json_file, "r", encoding="utf-8") as f:
                                json.load(f)
                        except:
                            corrupted.append(json_file.replace(sku_analysis_dir + "/", ""))

                if corrupted:
                    st.warning(f"⚠️ 发现 {len(corrupted)} 个损坏的JSON文件：")
                    for f in corrupted:
                        st.error(f"❌ {f}")
                    st.info("💡 请重新导入这些卖家的数据")
                else:
                    st.success(f"✅ 检查完成！共 {total_files} 个文件，全部正常")

            except Exception as e:
                st.error(f"❌ 检查失败: {e}")


    # ══════════════════════════════════════════════════════════
    #  模块1：一键导出全部卖家
    # ══════════════════════════════════════════════════════════

    all_seller_ids = load_all_seller_ids()
    sku_analysis_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "sku_analysis")

    if all_seller_ids:
        st.divider()
        st.subheader("📊 模块1：一键导出全部卖家")
        st.caption(f"当前共 {len(all_seller_ids)} 个卖家数据，点击按钮导出包含计算说明、全景概览、指标分布、风险矩阵的Excel报表")

        all_dates = sorted(set(rec.get("日期", "") for hist in all_seller_hist_raw.values() for rec in hist if rec.get("日期", "")))

        if len(all_dates) > 1:
            selected_batch = st.selectbox("选择数据批次", ["全部"] + all_dates, key="export_batch_select")
        else:
            selected_batch = all_dates[0] if all_dates else "全部"
            st.info(f"数据批次：{selected_batch}")

        if st.button("📥 导出全部卖家全景报表", key="export_all_sellers_btn", type="primary"):
            with st.spinner("正在生成报表..."):
                filtered_history = all_seller_hist_raw if selected_batch == "全部" else {sid: [r for r in hist if r.get("日期", "") == selected_batch] for sid, hist in all_seller_hist_raw.items()}
                excel_data, date_range = export_all_sellers_pano(filtered_history)
            date_part = selected_batch.replace("/", "").replace(" ", "").replace("-", "-") if selected_batch != "全部" else (date_range or datetime.now().strftime('%Y%m%d'))
            file_name = f"卖家健康度全景报表_{date_part}.xlsx"
            st.download_button("📥 点击下载", data=excel_data, file_name=file_name, key="download_all_sellers_excel")
            st.success(f"✅ 报表已生成，包含 {len(filtered_history)} 个卖家数据，批次：{selected_batch}")


    # ══════════════════════════════════════════════════════════
    #  模块2：历史回看区（含删除操作）
    # ══════════════════════════════════════════════════════════

    existing_sku_sellers = sorted([d for d in os.listdir(sku_analysis_dir) if os.path.isdir(os.path.join(sku_analysis_dir, d))]) if os.path.exists(sku_analysis_dir) else []

    st.divider()
    st.subheader("🔍 历史回看")

    if existing_sku_sellers:
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            review_seller = st.selectbox("选择卖家", [""] + existing_sku_sellers, key="review_seller")
        with rcol2:
            # 加载该卖家的所有批次，不经过时间筛选
            review_batches = load_sku_analysis_list(review_seller) if review_seller else []
            review_batch_idx = st.selectbox(
                "选择历史批次", list(range(len(review_batches))) if review_batches else [],
                format_func=lambda x: f"{review_batches[x].get('date_readable', review_batches[x].get('date_period', '未知'))} ({review_batches[x].get('total_skus', 0)}个SKU)" if x < len(review_batches) else "",
                key="review_batch_select") if review_batches else None

        if review_seller and review_batches and review_batch_idx is not None:
            batch = review_batches[review_batch_idx]
            review_matched = pd.DataFrame(batch.get("records", []))
            review_matched = review_matched.sort_values("整改优先级得分", ascending=False) if "整改优先级得分" in review_matched.columns else review_matched
            review_seller_history = load_seller_history(review_seller)
            if start_date:
                review_seller_history = [r for r in review_seller_history if (d := parse_date_any(r.get("日期", ""))) is None or to_date(start_date) <= d.date() <= to_date(end_date)]
            review_date_readable = batch.get("date_readable", batch.get("date_period", ""))
            review_date_period = batch.get("date_period", "")
            all_history = load_all_seller_history()
            benchmark = calc_benchmark_with_industry(calc_dynamic_benchmarks(all_history), len(all_history))
            review_seller_health = calc_seller_health_from_sku(review_matched) if len(review_matched) > 0 else pd.DataFrame()
            review_seller_row = review_seller_health[review_seller_health["卖家ID"] == review_seller] if not review_seller_health.empty else pd.DataFrame()

            st.divider()
            st.subheader(f"📊 卖家 [{review_seller}] 历史分析：{review_date_readable}（{len(review_matched)} 个SKU）")
            inv_time = batch.get("inv_upload_time")
            if inv_time:
                st.caption(f"📦 库存表上传时间：{inv_time}")
            rtab1, rtab2, rtab3 = st.tabs(["✅ SKU销售数据表", "🏆 卖家健康度对比", "📈 历史趋势"])

            with rtab1:
                st.dataframe(reorder_sku_columns(review_matched), width="stretch", height=500)
                r_export_action = st.selectbox("操作", ["📥 导出当前月份", "📥 导出多月份", "💾 保存到项目"], key="r_export_action", label_visibility="collapsed")
                if r_export_action == "📥 导出当前月份":
                    st.download_button("📥 导出当前月份SKU数据", data=export_sku_excel(reorder_sku_columns(review_matched)), file_name=f"{review_seller}_{review_date_period}.xlsx", key="r_download_main")
                elif r_export_action == "📥 导出多月份":
                    # 多月份导出选项
                    all_batches = load_sku_analysis_list(review_seller)
                    if all_batches:
                        batch_options = {b.get("date_readable", b.get("date_period", "未知")): b for b in all_batches}
                        selected_months = st.multiselect(
                            "选择要导出的月份",
                            options=list(batch_options.keys()),
                            default=[review_date_readable] if review_date_readable in batch_options else [],
                            key="r_multi_month_select"
                        )
                        if selected_months:
                            selected_batches = [batch_options[m] for m in selected_months]
                            st.info(f"已选择 {len(selected_batches)} 个月份")
                            st.download_button(
                                f"📥 导出{len(selected_batches)}个月份到一个Excel",
                                data=export_sku_multi_month(selected_batches, review_seller),
                                file_name=f"{review_seller}_{'_'.join(selected_months[:3])}.xlsx",
                                key="r_download_multi"
                            )
                elif r_export_action == "💾 保存到项目":
                    if st.button("💾 确认保存", key="r_save_to_project"):
                        filepath = save_sku_analysis(review_seller, review_date_period, date_readable, review_matched, seller_summary=batch.get("seller_summary", {}))
                        st.success(f"✅ 已保存到项目：`{filepath}`")

            with rtab2:
                st.subheader("🏆 卖家健康度评分")
                st.caption("按GMV、毛利、RMA、动销、SKU数、毛利率6维度加权评分，满分100")
                if not review_seller_row.empty:
                    render_health_metrics(review_seller_row)
                    render_benchmark_comparison(review_seller_row, benchmark)
                    render_industry_benchmarks()
                else:
                    st.info("暂无卖家数据")

            with rtab3:
                render_history_trend(review_seller_history)

            # 删除操作
            st.divider()
            st.markdown("**🗑️ 数据管理**")
            dc1, dc2 = st.columns(2)
            with dc1:
                seller_history_all = load_seller_history(review_seller)
                sku_batches_all = load_sku_analysis_list(review_seller)
                del_options = [(f"第{i+1}条 - {r.get('日期', '未知')}", i, next((b.get("date_period", "") for b in sku_batches_all if b.get("date_readable") == r.get("日期", "") or b.get("date_period", "").replace("-", "/") in r.get("日期", "")), "")) for i, r in enumerate(seller_history_all)]
                if del_options:
                    del_idx = st.selectbox("选择要删除的记录", list(range(len(del_options))), format_func=lambda x: del_options[x][0], key="del_record_idx")
                    if st.button("🗑️ 删除该条记录（含SKU明细）", key="del_one"):
                        _, sel_i, batch_period = del_options[del_idx]
                        if batch_period:
                            delete_sku_analysis_batch(review_seller, batch_period)
                        delete_seller_history(review_seller, sel_i)
                        st.success(f"已删除第{del_idx+1}条记录及其SKU明细")
                        st.rerun()
            with dc2:
                st.write("")
                st.write("")
                if st.button("⚠️ 清空该卖家所有记录", key="del_all"):
                    delete_sku_analysis_seller(review_seller)
                    st.success(f"已清空 {review_seller} 的所有记录")
                    st.rerun()

            render_summary_stats(review_matched)
    else:
        st.info("暂无历史数据可回看，请先上传数据并保存")
