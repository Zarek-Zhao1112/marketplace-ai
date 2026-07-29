"""
运营总览
- 关键指标概览
- 问题趋势分析
- 线索转化漏斗
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config.settings import ISSUES_PATH, BRANDS_PATH, CONTACTS_PATH, EMAILS_PATH
from src.web.utils import load_excel
from src.web.styles import inject_global_css, render_section_header


def _load_data():
    return {
        "issues": load_excel(ISSUES_PATH),
        "brands": load_excel(BRANDS_PATH),
        "contacts": load_excel(CONTACTS_PATH),
        "emails": load_excel(EMAILS_PATH),
        "leads": pd.DataFrame(),
    }


def render(tab):
    with tab:
        inject_global_css()

        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h2 style="margin-bottom: 0.25rem;">运营总览</h2>
            <p style="color: #8B9CB6; font-size: 0.9rem;">实时掌握运营全局状态</p>
        </div>
        """, unsafe_allow_html=True)

        data = _load_data()

        # ── 关键指标卡片 ────────────────────────────────────────
        render_section_header("关键指标", "当前数据概览")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            issues_count = len(data["issues"]) if not data["issues"].empty else 0
            st.metric("运营问题", issues_count)

        with col2:
            brands_count = len(data["brands"]) if not data["brands"].empty else 0
            st.metric("品牌线索", brands_count)

        with col3:
            contacts_count = len(data["contacts"]) if not data["contacts"].empty else 0
            st.metric("商家联系人", contacts_count)

        with col4:
            emails_count = len(data["emails"]) if not data["emails"].empty else 0
            st.metric("招商管理", emails_count)

        st.divider()

        # ── 两列布局 ────────────────────────────────────────────
        col_left, col_right = st.columns(2)

        # ── 左列：问题分析 ──────────────────────────────────────
        with col_left:
            render_section_header("问题分析", "运营问题统计")

            if not data["issues"].empty:
                issues_df = data["issues"]

                if "问题类型" in issues_df.columns:
                    type_counts = issues_df["问题类型"].value_counts()
                    fig_pie = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        title="问题类型分布",
                        hole=0.4
                    )
                    fig_pie.update_layout(height=300)
                    st.plotly_chart(fig_pie, width="stretch")

                if "处理状态" in issues_df.columns:
                    status_counts = issues_df["处理状态"].value_counts()
                    fig_bar = px.bar(
                        x=status_counts.index,
                        y=status_counts.values,
                        title="处理状态分布",
                        labels={"x": "状态", "y": "数量"},
                        color=status_counts.index,
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_bar.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_bar, width="stretch")

                if "时间" in issues_df.columns:
                    try:
                        issues_df["时间"] = pd.to_datetime(issues_df["时间"], errors="coerce")
                        monthly = issues_df.groupby(issues_df["时间"].dt.to_period("M")).size()
                        if len(monthly) > 1:
                            fig_line = px.line(
                                x=[str(p) for p in monthly.index],
                                y=monthly.values,
                                title="问题趋势（按月）",
                                labels={"x": "月份", "y": "数量"}
                            )
                            fig_line.update_layout(height=300)
                            st.plotly_chart(fig_line, width="stretch")
                    except Exception:
                        pass
            else:
                st.info("暂无问题数据")

        # ── 右列：邮件分析 ──────────────────────────────────────
        with col_right:
            render_section_header("邮件分析", "招商管理状态")

            if not data["emails"].empty:
                emails_df = data["emails"]

                if "Status" in emails_df.columns:
                    status_counts = emails_df["Status"].value_counts()
                    fig_status = px.pie(
                        values=status_counts.values,
                        names=status_counts.index,
                        title="邮件状态分布",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_status.update_layout(height=300)
                    st.plotly_chart(fig_status, width="stretch")

                if "Brand" in emails_df.columns:
                    brand_counts = emails_df["Brand"].value_counts().head(10)
                    fig_brand = px.bar(
                        x=brand_counts.index,
                        y=brand_counts.values,
                        title="品牌邮件数量 Top10",
                        labels={"x": "品牌", "y": "数量"},
                    )
                    fig_brand.update_layout(height=300, showlegend=False)
                    st.plotly_chart(fig_brand, width="stretch")
            else:
                st.info("暂无邮件数据")

        st.divider()

        # ── 线索转化漏斗 ────────────────────────────────────────
        render_section_header("线索转化漏斗", "从线索到合作的转化路径")

        funnel_data = {
            "阶段": ["线索搜集", "品牌入库", "联系触达", "邮件发送", "获得回复"],
            "数量": [
                len(data["leads"]) if not data["leads"].empty else 0,
                brands_count,
                contacts_count,
                emails_count,
                len(data["emails"][data["emails"]["Status"] == "已回复"]) if not data["emails"].empty and "Status" in data["emails"].columns else 0,
            ]
        }
        funnel_df = pd.DataFrame(funnel_data)

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_df["阶段"],
            x=funnel_df["数量"],
            textinfo="value+percent initial",
            marker={"color": ["#FF4655", "#BD3944", "#00B4D8", "#00D97E", "#FFB800"]}
        ))
        fig_funnel.update_layout(height=400, title="从线索到合作的转化漏斗")
        st.plotly_chart(fig_funnel, width="stretch")

        # ── 转化率计算 ──────────────────────────────────────────
        render_section_header("转化率统计", "各环节转化效率")

        col_r1, col_r2, col_r3 = st.columns(3)

        with col_r1:
            if funnel_data["数量"][0] > 0:
                rate = funnel_data["数量"][1] / funnel_data["数量"][0] * 100
                st.metric("线索→入库", f"{rate:.1f}%")
            else:
                st.metric("线索→入库", "N/A")

        with col_r2:
            if funnel_data["数量"][2] > 0:
                rate = funnel_data["数量"][3] / funnel_data["数量"][2] * 100
                st.metric("触达→邮件", f"{rate:.1f}%")
            else:
                st.metric("触达→邮件", "N/A")

        with col_r3:
            if funnel_data["数量"][3] > 0:
                rate = funnel_data["数量"][4] / funnel_data["数量"][3] * 100
                st.metric("邮件→回复", f"{rate:.1f}%")
            else:
                st.metric("邮件→回复", "N/A")

        st.divider()
        st.caption("运营总览基于本地数据生成，实时反映当前工作状态")
