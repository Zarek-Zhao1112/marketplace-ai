"""通用工具 — Excel I/O、文本工具、UI辅助"""
import io
import re
import os
import pandas as pd
import streamlit as st

from src.config.settings import EMAIL_PATTERN, INVALID_EMAIL_SUFFIX


def clean_domain(raw: str) -> str:
    d = re.sub(r'^https?://', '', raw.strip())
    d = re.sub(r'^www\.', '', d)
    return d.split('/')[0].split('?')[0]


def load_excel(path: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        st.error(f"❌ 读取文件失败（{os.path.basename(path)}）：{e}")
        return pd.DataFrame()


def save_excel(df: pd.DataFrame, path: str, success_msg: str = "✅ 数据已保存！") -> bool:
    try:
        df.to_excel(path, index=False, engine="openpyxl")
        st.success(success_msg)
        return True
    except PermissionError:
        st.error(f"❌ 保存失败：{os.path.basename(path)} 正被其他程序占用，请关闭后重试")
        return False
    except Exception as e:
        st.error(f"❌ 保存失败：{e}")
        return False


def export_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()


def merge_filtered_back(all_df: pd.DataFrame,
                         original_filtered: pd.DataFrame,
                         edited_filtered: pd.DataFrame) -> pd.DataFrame:
    remaining = all_df.drop(index=original_filtered.index)
    return pd.concat([remaining, edited_filtered], ignore_index=True)


def render_copy_button(text: str, btn_id: str, label: str = "📋 一键复制到剪贴板"):
    if st.button(label, key=btn_id):
        try:
            import pyperclip
            pyperclip.copy(text)
            st.success("✅ 已复制到剪贴板！")
        except Exception:
            st.code(text)
            st.info("💡 请手动选中上方文本复制")


def extract_emails_from_text(text: str):
    found = EMAIL_PATTERN.findall(text)
    emails = []
    for e in found:
        e_clean = e.strip().strip('.')
        if e_clean.lower().endswith(INVALID_EMAIL_SUFFIX):
            continue
        if any(x in e_clean.lower() for x in ["example.com", "yourname", "yourdomain", "test@test"]):
            continue
        if e_clean not in emails:
            emails.append(e_clean)
    return emails
