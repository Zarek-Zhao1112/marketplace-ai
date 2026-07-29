import os
import streamlit as st

from src.config.settings import ARK_API_KEY, HUNTER_API_KEY, DEMO_MODE


def render():
    if DEMO_MODE:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <span style="background: #FF4655; color: white; padding: 0.2rem 0.8rem;
                  border-radius: 999px; font-size: 0.75rem; font-weight: 700;
                  letter-spacing: 1px; text-transform: uppercase;">演示模式</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="color: #8B9CB6; font-size: 0.85rem; text-align: center;">
            内置示例数据，无需配置 API Key
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("""
    <div style="color: white; margin-bottom: 1rem;">
        <h3 style="color: white; margin-bottom: 0.5rem; font-size: 1.1rem;">API 配置</h3>
        <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem;">配置所需的服务密钥</p>
    </div>
    """, unsafe_allow_html=True)

    hunter_input = st.text_input(
        "Hunter.io API Key",
        type="password",
        value=st.session_state.get("hunter_api_key", os.getenv("HUNTER_API_KEY", HUNTER_API_KEY)),
        help="前往 hunter.io 注册，可获免费额度",
    )
    if hunter_input:
        st.session_state.hunter_api_key = hunter_input
        st.success("✅ Hunter Key 已配置")
    else:
        st.warning("⚠️ 请配置 Hunter.io API Key")

    st.divider()

    doubao_input = st.text_input(
        "豆包 API Key (ARK_API_KEY)",
        type="password",
        value=st.session_state.get("doubao_api_key", os.getenv("ARK_API_KEY", ARK_API_KEY)),
        help="字节跳动火山引擎控制台 → API Key 管理",
    )
    if doubao_input:
        st.session_state.doubao_api_key = doubao_input
        st.success("✅ 豆包 Key 已配置")
    else:
        st.warning("⚠️ 请配置豆包 API Key（AI 功能需要）")
