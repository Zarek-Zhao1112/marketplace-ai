import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib3
import streamlit as st

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from src.web.sidebar import render as render_sidebar
from src.web.tabs.issues import render as render_issues

st.set_page_config(page_title="问题管理", layout="wide")

with st.sidebar:
    render_sidebar()


render_issues(st.container())
