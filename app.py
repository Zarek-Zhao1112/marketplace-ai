import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import urllib3
import streamlit as st

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from src.config.settings import DEMO_MODE
from src.web.sidebar import render as render_sidebar
from src.web.styles import inject_global_css


def render_demo_landing():
    st.set_page_config(page_title="Newegg 跨境 BD 智能助手", layout="wide", initial_sidebar_state="expanded")
    inject_global_css()

    with st.sidebar:
        render_sidebar()

    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;
         min-height: 70vh; text-align: center; padding: 3rem 1rem;">
        <div style="width: 80px; height: 80px; border-radius: 50%; 
             background: linear-gradient(135deg, #FF4655, #BD3944);
             display: flex; align-items: center; justify-content: center;
             font-size: 2.5rem; color: #ECE8E1; margin-bottom: 2rem;
             box-shadow: 0 0 40px rgba(255, 70, 85, 0.3);">
            👤
        </div>
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">Newegg 跨境 BD 智能助手</h1>
        <div style="width: 60px; height: 3px; background: #FF4655; margin: 1rem auto; border-radius: 2px;"></div>
        <p style="color: #8B9CB6; max-width: 500px; margin: 0 auto 2rem; font-size: 1.05rem; line-height: 1.6;">
            面向 Newegg 卖家运营的数据分析与智能管理平台 — 
            卖家健康度评分、SKU 分级治理、AI 回复建议、品牌线索挖掘
        </p>
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem;">
            <span style="background: rgba(255,70,85,0.1); border: 1px solid rgba(255,70,85,0.3);
                  color: #FF4655; padding: 0.3rem 1rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;">
                Python</span>
            <span style="background: rgba(255,70,85,0.1); border: 1px solid rgba(255,70,85,0.3);
                  color: #FF4655; padding: 0.3rem 1rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;">
                Streamlit</span>
            <span style="background: rgba(255,70,85,0.1); border: 1px solid rgba(255,70,85,0.3);
                  color: #FF4655; padding: 0.3rem 1rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;">
                Plotly</span>
            <span style="background: rgba(255,70,85,0.1); border: 1px solid rgba(255,70,85,0.3);
                  color: #FF4655; padding: 0.3rem 1rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;">
                AI</span>
        </div>
        <p style="color: #8B9CB6; font-size: 0.9rem;">
            👈 侧边栏选择功能模块浏览演示
        </p>
        <a href="https://github.com/Zarek-Zhao1112/marketplace-ai" target="_blank"
           style="display: inline-flex; align-items: center; gap: 0.5rem;
                  margin-top: 1.5rem; color: #FF4655; text-decoration: none;
                  font-weight: 600; font-size: 0.9rem;">
            💻 查看 GitHub 源码 →
        </a>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.divider()
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem;">
            <p style="color: #8B9CB6; font-size: 0.85rem; margin-bottom: 1.5rem;">核心功能一览</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="background: #1F2D3D; border: 1px solid #2C3E50; border-radius: 12px;
                  padding: 1.5rem; text-align: center; border-left: 3px solid #FF4655;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                <h3 style="font-size: 1rem; margin-bottom: 0.3rem;">卖家健康度</h3>
                <p style="color: #8B9CB6; font-size: 0.8rem;">六维评分 · A/B/C/D 分级</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background: #1F2D3D; border: 1px solid #2C3E50; border-radius: 12px;
                  padding: 1.5rem; text-align: center; border-left: 3px solid #FF4655;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
                <h3 style="font-size: 1rem; margin-bottom: 0.3rem;">AI 回复建议</h3>
                <p style="color: #8B9CB6; font-size: 0.8rem;">聊天记录解析 · 知识库匹配</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="background: #1F2D3D; border: 1px solid #2C3E50; border-radius: 12px;
                  padding: 1.5rem; text-align: center; border-left: 3px solid #FF4655;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
                <h3 style="font-size: 1rem; margin-bottom: 0.3rem;">全景报表</h3>
                <p style="color: #8B9CB6; font-size: 0.8rem;">Excel 一键导出 · 图表自动生成</p>
            </div>
            """, unsafe_allow_html=True)


def render_normal():
    st.set_page_config(page_title="运营总览", layout="wide", initial_sidebar_state="expanded")
    inject_global_css()

    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="margin-bottom: 0.25rem;">运营总览</h1>
        <p style="color: #8B9CB6; font-size: 1rem; margin-top: 0;">Newegg Marketplace 运营数据管理与分析平台</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        render_sidebar()

    from src.web.tabs.dashboard import render as render_dashboard
    render_dashboard(st.container())


if DEMO_MODE:
    render_demo_landing()
else:
    render_normal()
