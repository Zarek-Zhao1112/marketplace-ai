"""
全局UI设计系统 - Valorant风格
深色背景 + 亮色文字 + 红色强调
"""

GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap');

    .stApp {
        background: #0F1923;
        font-family: 'Rajdhani', 'Segoe UI', sans-serif;
    }

    /* ── 全局文字 ── */
    .stApp .stMarkdown p,
    .stApp .stMarkdown li,
    .stApp .stMarkdown span,
    .stApp label,
    .stApp .stCaption,
    .stApp small,
    .stApp [data-testid="stWidgetLabel"],
    .stApp .stMarkdown h1,
    .stApp .stMarkdown h2,
    .stApp .stMarkdown h3,
    .stApp .stMarkdown h4,
    .stApp .stMarkdown h5,
    .stApp .stMarkdown h6,
    .stApp .stMarkdown code,
    .stApp .stMarkdown pre {
        color: #ECE8E1 !important;
    }

    /* ── 输入框文字 ── */
    .stApp .stTextInput > div > div > input,
    .stApp .stTextArea > div > div > textarea,
    .stApp .stNumberInput > div > div > input {
        color: #ECE8E1 !important;
        background: #1A2634 !important;
        border-color: #2C3E50 !important;
    }

    /* ── 标题 ── */
    h1, h2, h3, h4, h5, h6 {
        color: #ECE8E1 !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px !important;
    }

    h1 {
        background: linear-gradient(90deg, #FF4655 0%, #ECE8E1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ── 分割线 ── */
    hr {
        border: none;
        border-top: 1px solid #2C3E50;
        margin: 1.5rem 0;
    }

    /* ── 指标卡片 ── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1A2634 0%, #243447 100%);
        border: 1px solid #2C3E50;
        border-radius: 8px;
        padding: 16px 20px;
        border-left: 3px solid #FF4655;
        transition: all 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: #FF4655;
        box-shadow: 0 0 20px rgba(255, 70, 85, 0.15);
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] {
        color: #8B9CB6 !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    [data-testid="stMetricValue"] {
        color: #ECE8E1 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }

    [data-testid="stMetricDelta"] {
        color: #00D97E !important;
    }

    [data-testid="stMetricDelta"][style*="color: red"],
    [data-testid="stMetricDelta"][style*="color: #DC3545"] {
        color: #FF4655 !important;
    }

    /* ── 按钮 ── */
    .stButton > button {
        border-radius: 4px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.15s ease;
        border: none;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #FF4655 0%, #BD3944 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(255, 70, 85, 0.3);
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #FF5C6B 0%, #FF4655 100%);
        box-shadow: 0 6px 25px rgba(255, 70, 85, 0.5);
        transform: translateY(-1px);
    }

    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background: #1A2634;
        color: #ECE8E1 !important;
        border: 1px solid #2C3E50;
    }

    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        border-color: #FF4655;
        color: #FF4655 !important;
    }

    /* ── 标签页 ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #1A2634;
        border-radius: 6px;
        padding: 4px;
        border: 1px solid #2C3E50;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 4px;
        padding: 10px 20px;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        color: #8B9CB6 !important;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ECE8E1 !important;
        background: #243447;
    }

    .stTabs [aria-selected="true"] {
        background: #FF4655 !important;
        color: white !important;
        box-shadow: 0 2px 10px rgba(255, 70, 85, 0.3);
    }

    /* ── 数据表格 ── */
    [data-testid="stDataFrame"] {
        border: 1px solid #2C3E50;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    [data-testid="stDataFrame"] [role="gridcell"],
    [data-testid="stDataFrame"] [role="columnheader"] {
        color: #ECE8E1 !important;
        background: #1A2634 !important;
        padding: 12px 16px !important;
    }

    [data-testid="stDataFrame"] [role="columnheader"] {
        background: linear-gradient(180deg, #243447 0%, #1A2634 100%) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-size: 0.75rem !important;
        border-bottom: 2px solid #FF4655 !important;
        text-align: left !important;
    }

    [data-testid="stDataFrame"] [role="gridcell"] {
        border-bottom: 1px solid #2C3E50 !important;
        font-size: 0.9rem !important;
    }

    [data-testid="stDataFrame"] [role="gridcell"]:hover {
        background: #243447 !important;
    }

    [data-testid="stDataFrame"] tr:last-child [role="gridcell"] {
        border-bottom: none !important;
    }

    /* ── 输入框 ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 4px;
        border: 1px solid #2C3E50 !important;
        background: #1A2634 !important;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #FF4655 !important;
        box-shadow: 0 0 0 2px rgba(255, 70, 85, 0.2) !important;
    }

    .stSelectbox label,
    .stMultiSelect label,
    .stRadio label,
    .stCheckbox label,
    .stTextInput label,
    .stTextArea label,
    .stNumberInput label {
        color: #8B9CB6 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* ── 信息框 ── */
    .stAlert {
        border-radius: 6px;
        border-left-width: 4px;
        background: #1A2634 !important;
        border-color: #2C3E50 !important;
    }

    .stAlert p, .stAlert span {
        color: #ECE8E1 !important;
    }

    .stInfo {
        border-left-color: #00B4D8 !important;
        background: rgba(0, 180, 216, 0.1) !important;
    }

    .stWarning {
        border-left-color: #FFB800 !important;
        background: rgba(255, 184, 0, 0.1) !important;
    }

    .stError {
        border-left-color: #FF4655 !important;
        background: rgba(255, 70, 85, 0.1) !important;
    }

    .stSuccess {
        border-left-color: #00D97E !important;
        background: rgba(0, 217, 126, 0.1) !important;
    }

    /* ── 展开器 ── */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #ECE8E1 !important;
        background: #1A2634 !important;
        border: 1px solid #2C3E50 !important;
        border-radius: 6px !important;
    }

    .streamlit-expanderHeader:hover {
        border-color: #FF4655 !important;
    }

    /* ── 文件上传 ── */
    .stFileUploader label {
        color: #8B9CB6 !important;
    }

    .stFileUploader [data-testid="stFileUploaderDropzone"] {
        background: #1A2634 !important;
        border: 2px dashed #2C3E50 !important;
        border-radius: 8px !important;
    }

    .stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #FF4655 !important;
    }

    /* ── 进度条/Spinner ── */
    .stSpinner > div > div {
        border-color: #FF4655 !important;
    }

    /* ── 下载按钮 ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1A2634 0%, #243447 100%);
        color: #ECE8E1 !important;
        border: 1px solid #2C3E50;
    }

    .stDownloadButton > button:hover {
        border-color: #FF4655;
        color: #FF4655 !important;
    }

    /* ── 侧边栏 ── */
    [data-testid="stSidebar"] {
        background: #0D1520 !important;
        border-right: 1px solid #2C3E50;
    }

    [data-testid="stSidebar"] * {
        color: #ECE8E1 !important;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stPasswordInput label,
    [data-testid="stSidebar"] .stSelectbox label {
        color: #8B9CB6 !important;
    }

    [data-testid="stSidebar"] .stTextInput > div > div > input,
    [data-testid="stSidebar"] .stPasswordInput > div > div > input {
        background: #1A2634 !important;
        border: 1px solid #2C3E50 !important;
        color: #ECE8E1 !important;
    }

    [data-testid="stSidebar"] .stTextInput > div > div > input:focus,
    [data-testid="stSidebar"] .stPasswordInput > div > div > input:focus {
        border-color: #FF4655 !important;
        box-shadow: 0 0 0 2px rgba(255, 70, 85, 0.2) !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #2C3E50 !important;
    }

    [data-testid="stSidebar"] .stAlert,
    [data-testid="stSidebar"] .stAlert p,
    [data-testid="stSidebar"] .stAlert span {
        color: #ECE8E1 !important;
    }

    /* ── 区块标题 ── */
    .section-header {
        color: #FF4655 !important;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #FF4655;
        display: inline-block;
    }

    /* ── 滚动条 ── */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0F1923;
    }

    ::-webkit-scrollbar-thumb {
        background: #2C3E50;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #FF4655;
    }

    /* ── Plotly图表背景 ── */
    .stPlotlyChart {
        background: #1A2634;
        border: 1px solid #2C3E50;
        border-radius: 6px;
        padding: 8px;
    }
</style>
"""


def inject_global_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_section_header(title: str, subtitle: str = ""):
    import streamlit as st
    html = f'<div class="section-header">{title}</div>'
    if subtitle:
        html += f'<p style="color: #8B9CB6; font-size: 0.85rem; margin-top: 4px;">{subtitle}</p>'
    st.markdown(html, unsafe_allow_html=True)
