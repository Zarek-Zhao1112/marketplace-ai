import datetime
import pandas as pd
import streamlit as st

from src.web.utils import load_excel, save_excel, export_excel, clean_domain, merge_filtered_back
from src.web.ai import (
    search_company_emails, search_company_emails_official_site,
    build_search_engine_links, build_qcc_search_links,
)
from src.config.settings import CONTACTS_PATH
from src.web.styles import inject_global_css, render_section_header


def render(tab):
    with tab:
        inject_global_css()

        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h2 style="margin-bottom: 0.25rem;">商家通讯录</h2>
            <p style="color: #8B9CB6; font-size: 0.9rem;">自动搜索邮箱 + LinkedIn，建立商家联系人库</p>
        </div>
        """, unsafe_allow_html=True)

        if "search_results" not in st.session_state:
            st.session_state.search_results = []
        if "search_domain_value" not in st.session_state:
            st.session_state.search_domain_value = ""

        render_section_header("自动搜索品牌邮箱", "输入官网域名，自动发现联系方式")
        sd1, sd2, sd3 = st.columns([2, 2, 1])
        with sd1:
            search_domain_input = st.text_input(
                "输入品牌官网域名（如 razer.com）", key="search_domain_widget"
            )
        with sd2:
            search_source = st.selectbox(
                "数据源", ["官网爬取", "Hunter.io"], key="search_source"
            )
        with sd3:
            search_limit = st.number_input("最多搜索数量", min_value=1, max_value=50,
                                           value=5, key="search_limit_input")

        if st.button("🚀 开始搜索", key="start_search"):
            if not search_domain_input:
                st.error("❌ 请输入品牌官网域名！")
            else:
                with st.spinner(f"正在通过【{search_source}】搜索邮箱，请稍候…"):
                    if search_source == "Hunter.io":
                        emails, msg = search_company_emails(search_domain_input, search_limit)
                    else:
                        emails, msg = search_company_emails_official_site(search_domain_input, search_limit)
                if emails is None:
                    st.error(f"❌ {msg}")
                else:
                    st.success(f"✅ {msg}")
                    st.session_state.search_results = emails
                    st.session_state.search_domain_value = search_domain_input

        with st.expander("🔎 搜索引擎高级语法辅助（手动核实更全）"):
            se_name = st.text_input("公司全称（可选）", key="se_company_name")
            if st.button("生成搜索链接", key="gen_search_links"):
                domain_for_link = search_domain_input or ""
                links = build_search_engine_links(se_name, domain_for_link)
                if not links:
                    st.warning("请至少填写公司全称或官网域名")
                else:
                    for item in links:
                        st.markdown(f"**{item['用途']}**：`{item['查询语句']}`")
                        lc1, lc2 = st.columns(2)
                        with lc1:
                            st.markdown(f"[在百度中搜索]({item['百度']})")
                        with lc2:
                            st.markdown(f"[在Google中搜索]({item['Google']})")
                        st.divider()

            st.divider()
            st.markdown("**📇 工商信息平台查询（企查查 / 天眼查 / 爱企查）**")
            qcc_name = st.text_input("公司全称（用于精准匹配）", key="qcc_company_name")
            if st.button("生成工商信息查询链接", key="gen_qcc_links"):
                domain_for_qcc = search_domain_input or ""
                qcc_links = build_qcc_search_links(qcc_name, domain_for_qcc)
                if not qcc_links:
                    st.warning("请至少填写公司全称或官网域名")
                else:
                    for item in qcc_links:
                        st.markdown(f"**{item['平台']}**：`{item['关键词']}`")
                        st.markdown(f"[点击跳转]({item['链接']})")
                        st.divider()

        if st.session_state.search_results:
            st.subheader(f"搜索结果预览（{len(st.session_state.search_results)} 条）")
            st.dataframe(pd.DataFrame(st.session_state.search_results), width="stretch")

            rb1, rb2 = st.columns([1, 5])
            with rb1:
                if st.button("✅ 全部保存", key="save_search_results"):
                    try:
                        old_contacts = load_excel(CONTACTS_PATH)
                        valid_items = [e for e in st.session_state.search_results
                                       if e.get("邮箱") and str(e["邮箱"]).strip()]
                        existing = set(
                            old_contacts["邮箱"].str.strip().str.lower().dropna()
                        ) if not old_contacts.empty else set()
                        c_domain = clean_domain(st.session_state.search_domain_value)
                        auto_name = c_domain.split(".")[0].title()
                        new_rows = []
                        for item in valid_items:
                            ce = item["邮箱"].strip().lower()
                            if ce not in existing:
                                new_rows.append({
                                    "商家名称": auto_name, "邮箱": item["邮箱"].strip(),
                                    "LinkedIn": str(item.get("LinkedIn", "")).strip(),
                                    "职位": str(item.get("职位", "")).strip(),
                                    "官网": f"https://{c_domain}", "国家": "",
                                    "来源": item.get("来源", "Hunter.io"), "备注": "",
                                    "添加时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                })
                                existing.add(ce)
                        if new_rows:
                            total = pd.concat([old_contacts, pd.DataFrame(new_rows)],
                                              ignore_index=True)
                            if save_excel(total, CONTACTS_PATH,
                                          f"✅ 成功保存 {len(new_rows)} 个新联系方式！"):
                                st.session_state.search_results = []
                                st.session_state.search_domain_value = ""
                                st.rerun()
                        else:
                            st.info("ℹ️ 所有邮箱均已存在于联系方式库，无需重复添加")
                            st.session_state.search_results = []
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ 保存失败：{e}")
            with rb2:
                if st.button("🗑️ 清空搜索结果", key="clear_search"):
                    st.session_state.search_results = []
                    st.session_state.search_domain_value = ""
                    st.rerun()

        st.divider()
        render_section_header("手动添加联系人", "填写联系人信息")
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            merchant_name = st.text_input("商家名称 *", key="merchant_name")
            email = st.text_input("邮箱", key="merchant_email")
        with mc2:
            linkedin = st.text_input("LinkedIn 链接", key="merchant_linkedin")
            website = st.text_input("官网", key="merchant_website")
        with mc3:
            country = st.text_input("国家 / 地区", key="merchant_country")
            position = st.text_input("联系人职位", key="merchant_position")
        contact_remark = st.text_input("备注", key="contact_remark")

        if st.button("✅ 添加联系方式", key="add_contact"):
            if not merchant_name:
                st.error("❌ 商家名称为必填项！")
            else:
                new_row = {
                    "商家名称": merchant_name, "邮箱": email, "LinkedIn": linkedin,
                    "职位": position, "官网": website, "国家": country,
                    "来源": "手动添加", "备注": contact_remark,
                    "添加时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                old_contacts = load_excel(CONTACTS_PATH)
                total = pd.concat([old_contacts, pd.DataFrame([new_row])], ignore_index=True)
                if save_excel(total, CONTACTS_PATH, f"✅ 商家「{merchant_name}」添加成功！"):
                    st.rerun()

        st.divider()
        render_section_header("联系方式库", "管理所有商家联系人")
        search_kw = st.text_input("搜索商家名称 / 邮箱 / LinkedIn 关键词", key="search_contact")

        all_contacts_df = load_excel(CONTACTS_PATH)
        is_kw_filtered = bool(search_kw)
        if search_kw:
            mask = all_contacts_df.apply(
                lambda row: row.astype(str).str.contains(search_kw, case=False, na=False).any(),
                axis=1,
            )
            view_contacts = all_contacts_df[mask]
            st.info(f"🔍 找到 {len(view_contacts)} 条匹配结果")
        else:
            view_contacts = all_contacts_df

        edit_contacts = st.data_editor(view_contacts, width="stretch",
                                        num_rows="dynamic", key="contacts_editor")
        cs1, cs2 = st.columns([1, 4])
        with cs1:
            if st.button("💾 保存修改", key="save_contacts"):
                final_contacts = merge_filtered_back(all_contacts_df, view_contacts, edit_contacts) \
                                 if is_kw_filtered else edit_contacts
                save_excel(final_contacts, CONTACTS_PATH, "✅ 联系方式已保存！")
        with cs2:
            st.download_button("📥 导出全部联系方式", data=export_excel(edit_contacts),
                               file_name=f"商家通讯录_{datetime.date.today()}.xlsx",
                               key="download_contacts")
