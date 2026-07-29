import os
import re
import json
import hashlib
import datetime
import time
import pandas as pd
import requests
import streamlit as st

from src.web.utils import load_excel, save_excel, export_excel, render_copy_button
from src.config.settings import ISSUES_PATH
from src.knowledge.experience_library import ExperienceLibrary
from src.config.settings import MODEL_ENDPOINT, ARK_API_URL
from src.web.styles import inject_global_css, render_section_header


PROBLEM_TYPES = ["产品问题", "物流问题", "售后问题", "结算问题", "日常沟通", "其他"]

_PARSE_PROMPT = """请分析以上聊天记录和图片，提取每一个问题。
对每个问题输出包含以下字段的 JSON 数组：
[{
  "时间": "问题的日期时间",
  "卖家名称": "卖家名称",
  "问题类型": "产品问题/物流问题/售后问题/结算问题/日常沟通",
  "问题描述": "问题详情（30-100字）",
  "处理状态": "待处理",
  "处理过程": "对话讨论总结（20-80字）",
  "解决方案": "讨论出的方案（20-80字）"
}]
如果没有问题则输出空数组[]。只输出 JSON，不要 Markdown 代码块。"""


def _extract_json_array(raw: str):
    """从AI返回的文本中提取JSON数组，容错各种格式"""
    raw = raw.strip()
    if not raw:
        return None

    # 先尝试直接解析
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    return v
        return None
    except json.JSONDecodeError:
        pass

    # 去除 ```json ... ``` 包裹
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    # 正则提取JSON数组
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def _call_doubao_api(messages, api_key, max_retries=3):
    """调用豆包API，带指数退避重试"""
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                ARK_API_URL,
                timeout=180,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {api_key}"},
                json={
                    "model": MODEL_ENDPOINT,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 3000,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"], None
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, "请求超时，内容可能太长，建议分段处理"
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, "连接被服务器断开，建议缩短后重试"
        except requests.exceptions.HTTPError as e:
            return None, f"API 错误({e.response.status_code})：请确认 API Key 和 MODEL_ENDPOINT 是否正确"
        except Exception as e:
            return None, f"未知错误：{e}"
    return None, "重试次数用尽"


def _get_image_base64(img_file):
    """将上传的图片转为base64"""
    import base64
    from PIL import Image
    import io

    img = Image.open(img_file)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


def _parse_chat(chat_text: str, images: list = None, api_key: str = ""):
    """统一的聊天记录解析入口，支持纯文本和图片+文本"""
    content = []

    # 添加文本
    if chat_text:
        text = chat_text[:4000] + "\n...(聊天记录已截断)" if len(chat_text) > 4000 else chat_text
        content.append({"type": "text", "text": text})

    # 添加图片
    if images:
        for img_file in images:
            img_b64 = _get_image_base64(img_file)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })

    if not content:
        return [], "没有输入内容"

    content.append({"type": "text", "text": _PARSE_PROMPT})

    # 缓存检查（基于内容hash，10分钟有效）
    content_str = json.dumps(content, ensure_ascii=False)
    cache_key = hashlib.md5(content_str.encode()).hexdigest()
    cache = st.session_state.get("_parse_cache", {})
    if cache_key in cache:
        cached_result, cache_time = cache[cache_key]
        if time.time() - cache_time < 600:
            return cached_result, None

    raw, err = _call_doubao_api([{"role": "user", "content": content}], api_key)
    if err:
        return [], err

    data = _extract_json_array(raw)
    if data is not None:
        # 写入缓存
        if "_parse_cache" not in st.session_state:
            st.session_state._parse_cache = {}
        st.session_state._parse_cache[cache_key] = (data, time.time())
        return data, None

    return [], "AI 返回格式异常，请重试"


@st.fragment
def _chat_extract_fragment():
    render_section_header("聊天记录 → 自动提取问题", "粘贴企业微信聊天记录，AI自动识别")

    # 初始化session_state
    if "pasted_images" not in st.session_state:
        st.session_state.pasted_images = []

    # 聊天记录输入
    chat_input = st.text_area(
        "粘贴聊天记录",
        key="chat_import",
        placeholder="""从企业微信复制聊天记录粘贴到这里...

提示：如果聊天记录中有图片，请在文本中标记位置，例如：
卖家说：这个产品有问题
[图片1]
卖家说：你看看这个截图""",
        height=200,
    )

    # 图片上传（支持多张）
    uploaded_images = st.file_uploader(
        "上传截图（可选，按顺序上传）",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="chat_images",
        help="按顺序上传截图，AI会根据文本中的[图片1][图片2]标记识别对应位置"
    )

    # 显示已上传的图片
    all_images = list(uploaded_images) if uploaded_images else []
    if st.session_state.pasted_images:
        all_images.extend(st.session_state.pasted_images)

    if all_images:
        st.info(f"✅ 已有 {len(all_images)} 张图片（请按顺序上传，AI会根据[图片1][图片2]标记识别）")
        cols = st.columns(min(len(all_images), 3))
        for i, img in enumerate(all_images[:3]):
            with cols[i]:
                st.image(img, caption=f"图片 {i+1}", use_container_width=True)

    if st.button("🤖 AI 提取问题", key="parse_chat", width="stretch"):
        # 合并文本和图片
        full_text = chat_input.strip()

        if not full_text and not all_images:
            st.warning("请先粘贴聊天记录或上传图片")
        else:
            api_key = st.session_state.get("doubao_api_key", os.getenv("ARK_API_KEY", ""))
            if not api_key:
                st.error("请先在左侧配置豆包 API Key")
            else:
                with st.spinner("AI 正在分析聊天记录和图片，提取问题..."):
                    rows, err = _parse_chat(full_text, all_images, api_key)
                if err:
                    st.error(f"❌ {err}")
                elif rows:
                    df = pd.DataFrame(rows)
                    st.success(f"✅ 识别到 {len(df)} 个问题，请确认后保存")
                    st.dataframe(df, width="stretch")
                    st.session_state.chat_parsed_df = df
                else:
                    st.info("未从聊天记录中识别出明确的问题")

    if st.session_state.get("chat_parsed_df") is not None and not st.session_state.chat_parsed_df.empty:
        df = st.session_state.chat_parsed_df
        if st.button("💾 保存到主笔记库", key="save_chat_import", width="stretch", type="primary"):
            old_df = load_excel(ISSUES_PATH)
            df_insert = df.copy()
            df_insert.insert(0, "问题ID", [f"I{int(datetime.datetime.now().timestamp())}{i}" for i in range(len(df))])
            df_insert["来源文件"] = "聊天记录导入"
            for col in ["问题ID", "时间", "卖家名称", "问题类型", "问题描述", "处理状态", "处理过程", "解决方案", "来源文件"]:
                if col not in df_insert.columns:
                    df_insert[col] = ""
            merged = pd.concat([old_df, df_insert[["问题ID", "时间", "卖家名称", "问题类型", "问题描述", "处理状态", "处理过程", "解决方案", "来源文件"]]], ignore_index=True)
            if save_excel(merged, ISSUES_PATH, f"✅ 成功导入 {len(df_insert)} 条问题！"):
                st.session_state.pop("chat_parsed_df", None)
                st.rerun()


def render(tab):
    with tab:
        inject_global_css()

        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h2 style="margin-bottom: 0.25rem;">问题管理</h2>
            <p style="color: #8B9CB6; font-size: 0.9rem;">记录和管理运营问题，AI自动提取聊天记录</p>
        </div>
        """, unsafe_allow_html=True)

        _chat_extract_fragment()

        st.divider()
        render_section_header("主笔记库", "可直接编辑、删行，勾选「保留」批量操作")
        main_df = load_excel(ISSUES_PATH)

        if not main_df.empty:
            issue_type_col = "问题类型" if "问题类型" in main_df.columns else None
            status_col_issues = "处理状态" if "处理状态" in main_df.columns else None

            type_colors = {
                "产品问题": "#FF4655", "物流问题": "#00B4D8", "售后问题": "#FFB800",
                "结算问题": "#00D97E", "日常沟通": "#8B9CB6", "其他": "#2C3E50",
            }
            status_colors_issues = {
                "待处理": ("#FFB800", "#0F1923"), "处理中": ("#FF4655", "#FFFFFF"),
                "已解决": ("#00D97E", "#0F1923"), "已关闭": ("#8B9CB6", "#0F1923"),
            }

            st.markdown("""
            <style>
            .issue-kpi-row { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
            .issue-kpi-card {
                background: linear-gradient(135deg, #1A2634 0%, #243447 100%);
                border: 1px solid #2C3E50; border-radius: 8px; padding: 12px 14px;
                border-left: 3px solid #FF4655; min-width: 90px; text-align: center;
            }
            .issue-kpi-label { color: #8B9CB6; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 3px; }
            .issue-kpi-value { color: #ECE8E1; font-size: 1.3rem; font-weight: 700; }
            </style>
            """, unsafe_allow_html=True)

            total_notes = len(main_df)

            kpi_html = '<div class="issue-kpi-row">'
            kpi_html += f'<div class="issue-kpi-card" style="border-left-color:#FF4655;"><div class="issue-kpi-label">总笔记数</div><div class="issue-kpi-value">{total_notes}</div></div>'

            if issue_type_col:
                type_counts = main_df[issue_type_col].value_counts()
                for t in ["产品问题", "物流问题", "售后问题", "结算问题", "日常沟通", "其他"]:
                    cnt = type_counts.get(t, 0)
                    color = type_colors.get(t, "#2C3E50")
                    kpi_html += f'<div class="issue-kpi-card" style="border-left-color:{color};"><div class="issue-kpi-label">{t}</div><div class="issue-kpi-value">{cnt}</div></div>'

            if status_col_issues:
                stat_counts = main_df[status_col_issues].value_counts()
                for s in ["待处理", "处理中", "已解决"]:
                    cnt = stat_counts.get(s, 0)
                    bg, _ = status_colors_issues.get(s, ("#2C3E50", "#ECE8E1"))
                    kpi_html += f'<div class="issue-kpi-card" style="border-left-color:{bg};"><div class="issue-kpi-label">{s}</div><div class="issue-kpi-value">{cnt}</div></div>'

            kpi_html += '</div>'
            st.markdown(kpi_html, unsafe_allow_html=True)

            filter_cols = st.columns(2)
            with filter_cols[0]:
                if issue_type_col:
                    type_opts = ["全部"] + sorted(main_df[issue_type_col].dropna().unique().tolist())
                    filter_type = st.selectbox("按问题类型筛选", type_opts, key="filter_issue_type")
                else:
                    filter_type = "全部"
            with filter_cols[1]:
                if status_col_issues:
                    stat_opts = ["全部"] + sorted(main_df[status_col_issues].dropna().unique().tolist())
                    filter_status = st.selectbox("按处理状态筛选", stat_opts, key="filter_issue_status")
                else:
                    filter_status = "全部"

            is_filtered_issues = filter_type != "全部" or filter_status != "全部"
            view_issues = main_df.copy()
            if filter_type != "全部" and issue_type_col:
                view_issues = view_issues[view_issues[issue_type_col] == filter_type]
            if filter_status != "全部" and status_col_issues:
                view_issues = view_issues[view_issues[status_col_issues] == filter_status]
            if is_filtered_issues:
                st.markdown(f'<div style="background:#1A2634;border:1px solid #2C3E50;border-radius:6px;padding:10px 16px;margin-bottom:12px;color:#8B9CB6;font-size:0.9rem;">🔍 筛选结果：<span style="color:#ECE8E1;font-weight:700;">{len(view_issues)}</span> 条 / 共 <span style="color:#ECE8E1;font-weight:700;">{len(main_df)}</span> 条</div>', unsafe_allow_html=True)

            display_df = view_issues.copy()
            display_df.insert(0, "保留", True)
        else:
            display_df = main_df.copy()
            if not display_df.empty:
                display_df.insert(0, "保留", True)

        edit_df = st.data_editor(display_df, width="stretch",
                                  num_rows="dynamic", key="issues_editor")

        keep_count = edit_df["保留"].sum() if "保留" in edit_df.columns else len(edit_df)
        total = len(edit_df)
        to_del = total - keep_count

        c1, c2, c3 = st.columns([1, 2, 3])
        with c1:
            if st.button("💾 保存修改", key="save_issues"):
                if is_filtered_issues and not main_df.empty:
                    savedf = edit_df.drop(columns=["保留"], errors="ignore")
                    final_df = pd.concat([main_df.drop(view_issues.index, errors="ignore"), savedf], ignore_index=True)
                else:
                    savedf = edit_df.drop(columns=["保留"], errors="ignore")
                    final_df = savedf
                save_excel(final_df, ISSUES_PATH, "✅ 问题管理已保存！")
        with c2:
            if to_del > 0:
                danger_label = f"🗑️ 仅保留勾选（删除未勾选 {to_del} 条）"
                if st.button(danger_label, key="keep_only", type="primary"):
                    kept = edit_df[edit_df["保留"] == True].drop(columns=["保留"], errors="ignore")
                    save_excel(kept, ISSUES_PATH, f"✅ 已保留 {len(kept)} 条，删除 {to_del} 条")
                    st.rerun()
            else:
                st.button("✅ 全部已保留", disabled=True, key="keep_only_disabled")
        with c3:
            st.download_button("📥 导出完整 Excel", data=export_excel(edit_df.drop(columns=["保留"], errors="ignore")),
                               file_name=f"问题管理_{datetime.date.today()}.xlsx",
                               key="download_issues")

        st.divider()
        render_section_header("运营经验库", "基于历史问题的智能检索和回复建议")

        exp_lib = ExperienceLibrary(ISSUES_PATH)
        summary = exp_lib.get_summary()

        col_exp1, col_exp2 = st.columns([1, 1])
        with col_exp1:
            st.metric("📊 已解决问题总数", summary["已解决问题总数"])
            if summary["问题类型分布"]:
                st.write("**问题类型分布：**")
                for ptype, count in sorted(summary["问题类型分布"].items(), key=lambda x: x[1], reverse=True):
                    st.write(f"- {ptype}：{count} 条")
            st.caption(f"最后更新：{summary['最后更新']}")

        with col_exp2:
            if st.button("🔄 重建经验库", key="rebuild_exp", width="stretch"):
                count = exp_lib.rebuild()
                st.success(f"✅ 经验库已重建！共收录 {count} 条已解决案例")
                st.rerun()

            st.divider()
            st.write("**🔍 查询历史经验**")
            exp_query = st.text_area("输入问题描述，搜索相似案例", key="exp_query",
                                      placeholder="例如：卖家反馈物流延迟、库存数据不对...")
            exp_type = st.selectbox("筛选问题类型（可选）",
                                    ["全部"] + [t for t in summary["问题类型分布"].keys()],
                                    key="exp_type_filter")
            if st.button("🔍 搜索经验", key="search_exp", width="stretch"):
                if not exp_query.strip():
                    st.warning("请先输入问题描述")
                else:
                    ptype = None if exp_type == "全部" else exp_type
                    results = exp_lib.search(exp_query, problem_type=ptype, top_k=5)
                    if results:
                        st.success(f"找到 {len(results)} 个相似案例")
                        for i, case in enumerate(results):
                            with st.expander(f"📌 案例 {i+1}：{case['问题类型']} — {case['问题描述'][:50]}..."):
                                st.write(f"**问题类型：** {case['问题类型']}")
                                st.write(f"**问题描述：** {case['问题描述']}")
                                st.write(f"**解决方案：** {case['解决方案']}")
                                if case.get('处理过程') and case['处理过程'] != 'nan':
                                    st.write(f"**处理过程：** {case['处理过程']}")
                                st.caption(f"卖家：{case['卖家名称']} | 时间：{case['时间']}")
                    else:
                        st.info("未找到相关案例，试试用更通用的关键词")

            st.divider()
            st.write("**💬 AI 回复建议**")
            st.caption("输入卖家消息，AI 基于历史回复模式生成建议")
            reply_msg = st.text_area("卖家消息", key="reply_msg",
                                      placeholder="粘贴卖家发来的消息...")
            if st.button("🤖 生成回复建议", key="gen_reply", width="stretch"):
                if not reply_msg.strip():
                    st.warning("请先输入卖家消息")
                else:
                    api_key = st.session_state.get("doubao_api_key", os.getenv("ARK_API_KEY", ""))
                    if not api_key:
                        st.error("请先在左侧配置豆包 API Key")
                    else:
                        with st.spinner("AI 正在生成回复..."):
                            result = exp_lib.suggest_reply_web(
                                api_key=api_key,
                                model_endpoint=MODEL_ENDPOINT,
                                seller_message=reply_msg,
                            )
                        refs = result.get("references", [])
                        if refs:
                            with st.expander(f"📚 参考了 {len(refs)} 组历史对话"):
                                for i, r in enumerate(refs):
                                    st.caption(f"卖家：{r['seller_message'][:80]}...")
                                    st.caption(f"运营：{r['operator_reply'][:80]}...")
                                    st.divider()
                        st.success("✅ 回复生成成功")
                        st.text_area("建议回复（可编辑）", value=result["suggested_reply"], height=200, key="reply_output")
                        render_copy_button(result["suggested_reply"], "copy_reply", "📋 复制回复到剪贴板")

                        # 学习功能：保存用户修改后的回复
                        st.divider()
                        st.write("**💾 保存学习**")
                        st.caption("如果你修改了回复内容，点击保存可以让AI学习你的回复风格")
                        if st.button("💾 保存到经验库", key="save_learned_reply", width="stretch"):
                            edited_reply = st.session_state.get("reply_output", result["suggested_reply"])
                            if edited_reply and edited_reply != result["suggested_reply"]:
                                # 保存到经验库
                                try:
                                    exp_lib.add_reply_pair(seller_message, edited_reply)
                                    st.success("✅ 已保存到经验库，AI会学习你的回复风格")
                                except Exception as e:
                                    st.error(f"❌ 保存失败：{e}")
                            else:
                                st.info("回复内容没有修改，无需保存")
