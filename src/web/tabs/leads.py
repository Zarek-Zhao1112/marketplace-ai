import datetime
import pandas as pd
import streamlit as st

from src.web.utils import (
    load_excel, save_excel, export_excel,
    merge_filtered_back,
)
from src.web.web_scraper import fetch_website_content, fetch_website_content_js
from src.web.ai import analyze_brand_info
from src.config.settings import (
    BRANDS_PATH, CATEGORY_OPTIONS, SCALE_MAP, SCALE_OPTIONS,
)
from src.web.styles import inject_global_css, render_section_header


def render(tab):
    with tab:
        inject_global_css()

        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h2 style="margin-bottom: 0.25rem;">品牌线索</h2>
            <p style="color: #8B9CB6; font-size: 0.9rem;">发现、评估和管理潜在合作品牌</p>
        </div>
        """, unsafe_allow_html=True)

        render_section_header("品牌信息自动抓取", "输入官网域名，AI自动提取品牌信息")
        crawl_domain = st.text_input("输入品牌官网域名（如：logitech.com）", key="crawl_domain")

        if st.button("🚀 一键抓取品牌信息", key="crawl_brand"):
            if not crawl_domain:
                st.error("❌ 请输入品牌官网域名！")
            else:
                with st.spinner("正在抓取官网内容…"):
                    website_content, err = fetch_website_content(crawl_domain)
                    if err or (website_content and len(website_content.strip()) < 100):
                        with st.spinner("检测到可能是JS渲染网站，正在使用浏览器渲染抓取…"):
                            js_content, js_err = fetch_website_content_js(crawl_domain)
                            if js_content:
                                website_content, err = js_content, None
                            elif err is None:
                                pass
                if err:
                    st.error(f"❌ {err}")
                else:
                    with st.spinner("AI 正在分析品牌信息…"):
                        brand_info_ai, msg = analyze_brand_info(website_content)

                    if brand_info_ai:
                        st.success(f"✅ {msg}")
                        st.session_state.crawled_brand = brand_info_ai
                        st.session_state.crawled_domain = crawl_domain

                        st.subheader("抓取结果预览")
                        p1, p2 = st.columns(2)
                        with p1:
                            st.write(f"**品牌名称：** {brand_info_ai.get('brand_name', '')}")
                            st.write(f"**Slogan：** {brand_info_ai.get('slogan', '')}")
                            st.write(f"**成立年份：** {brand_info_ai.get('founded_year', '')}")
                            st.write(f"**品牌规模：** {brand_info_ai.get('company_size', '')}")
                        with p2:
                            st.write(f"**主营类目：** {', '.join(brand_info_ai.get('main_categories', []))}")
                            st.write(f"**销售渠道：** {', '.join(brand_info_ai.get('sales_channels', []))}")
                        st.write("**品牌简介：**")
                        st.write(brand_info_ai.get("description", ""))
                        st.info("✅ 信息已自动填充到下方表单，确认后点击「添加品牌线索」保存")
                        for key in ["brand_name", "category", "slogan", "target_market", "scale",
                                    "website_domain", "brand_status", "sales_channels", "social_media",
                                    "brand_description", "brand_remark"]:
                            st.session_state.pop(key, None)
                            st.session_state["brand_name"] = brand_info_ai.get("brand_name", "")
                            st.session_state["slogan"] = brand_info_ai.get("slogan", "")
                            st.session_state["brand_description"] = brand_info_ai.get("description", "")

                            raw_cat = (brand_info_ai.get("main_categories") or ["其他"])[0]
                            st.session_state["category"] = raw_cat if raw_cat in CATEGORY_OPTIONS else "其他"

                            raw_scale = brand_info_ai.get("company_size", "成长品牌")
                            norm_scale = SCALE_MAP.get(raw_scale, raw_scale)
                            st.session_state["scale"] = norm_scale if norm_scale in SCALE_OPTIONS else "成长品牌"

                            st.session_state["website_domain"] = crawl_domain

                            social = brand_info_ai.get("social_media", {})
                            parts = [f"{lbl}: {social[k]}" for k, lbl in
                                     [("facebook", "Facebook"), ("twitter", "Twitter"),
                                      ("instagram", "Instagram"), ("linkedin", "LinkedIn")]
                                     if social.get(k)]
                            st.session_state["social_media"] = "\n".join(parts)

                            st.session_state["sales_channels"] = ", ".join(brand_info_ai.get("sales_channels", []))

                            st.session_state["target_market"] = []
                            st.session_state["brand_status"] = "待联系"
                            st.session_state["brand_remark"] = ""

                        st.rerun()

                    else:
                        st.error(f"❌ {msg}")

        st.divider()
        render_section_header("添加品牌线索", "填写品牌基本信息")

        f1, f2, f3 = st.columns(3)
        with f1:
            brand_name = st.text_input("品牌名称 *", key="brand_name")
            if "category" not in st.session_state:
                st.session_state["category"] = CATEGORY_OPTIONS[0]
            category = st.selectbox("所属类目", CATEGORY_OPTIONS, key="category")
            slogan = st.text_input("品牌 Slogan", key="slogan")

        with f2:
            target_market = st.multiselect(
                "目标市场",
                ["北美", "欧洲", "东南亚", "日本", "全球"],
                key="target_market",
            )

            if "scale" not in st.session_state:
                st.session_state["scale"] = SCALE_OPTIONS[0]
            scale = st.selectbox("品牌规模", SCALE_OPTIONS, key="scale")

            website_domain = st.text_input("官网域名", key="website_domain")

        with f3:
            if "brand_status" not in st.session_state:
                st.session_state["brand_status"] = "待联系"
            brand_status = st.selectbox("跟进状态",
                                        ["待联系", "已联系", "跟进中", "已合作", "已放弃"],
                                        key="brand_status")
            sales_channels = st.text_input("现有销售渠道", key="sales_channels")
            social_media = st.text_area("社交媒体账号", key="social_media")

        brand_description = st.text_area("品牌简介", key="brand_description")
        brand_remark = st.text_area("备注", key="brand_remark")

        if st.button("✅ 添加品牌线索", key="add_brand"):
            if not brand_name:
                st.error("❌ 品牌名称为必填项！")
            else:
                new_row = {
                    "品牌ID": f"B{int(datetime.datetime.now().timestamp())}",
                    "品牌名称": brand_name, "所属类目": category,
                    "目标市场": ",".join(target_market), "品牌规模": scale,
                    "官网域名": website_domain, "品牌简介": brand_description,
                    "Slogan": slogan, "社交媒体": social_media,
                    "销售渠道": sales_channels, "联系方式": "",
                    "跟进状态": brand_status, "备注": brand_remark,
                    "创建时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                old_brands = load_excel(BRANDS_PATH)
                total = pd.concat([old_brands, pd.DataFrame([new_row])], ignore_index=True)
                if save_excel(total, BRANDS_PATH, f"✅ 品牌「{brand_name}」添加成功！"):
                    st.session_state.pop("crawled_brand", None)
                    st.session_state.pop("crawled_domain", None)
                    st.rerun()

        st.divider()
        render_section_header("批量导入品牌线索", "上传Excel格式的品牌数据")
        brand_upload = st.file_uploader("上传 Excel 格式品牌线索表",
                                        type=["xlsx", "xls"], key="brand_upload")
        if brand_upload:
            try:
                upload_brands = pd.read_excel(brand_upload, engine="openpyxl")
                st.dataframe(upload_brands, width="stretch")
                if st.button("✅ 批量导入", key="batch_import_brands"):
                    old_brands = load_excel(BRANDS_PATH)
                    total = pd.concat([old_brands, upload_brands], ignore_index=True, sort=False)
                    if save_excel(total, BRANDS_PATH, f"✅ 成功导入 {len(upload_brands)} 条！"):
                        st.rerun()
            except Exception as e:
                st.error(f"❌ 导入失败：{e}")

        st.divider()
        render_section_header("品牌线索", "管理所有品牌线索数据")

        all_brands_df = load_excel(BRANDS_PATH)
        cat_col = "Category" if "Category" in all_brands_df.columns else all_brands_df.columns[2]
        status_col = "Status" if "Status" in all_brands_df.columns else all_brands_df.columns[6]
        name_col = "BrandName" if "BrandName" in all_brands_df.columns else all_brands_df.columns[1]

        if not all_brands_df.empty:
            status_colors = {
                "待联系": ("#FFB800", "#0F1923"),
                "已联系": ("#00B4D8", "#0F1923"),
                "跟进中": ("#FF4655", "#FFFFFF"),
                "已合作": ("#00D97E", "#0F1923"),
                "已放弃": ("#8B9CB6", "#0F1923"),
            }

            st.markdown("""
            <style>
            .brand-kpi-row { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
            .brand-kpi-card {
                background: linear-gradient(135deg, #1A2634 0%, #243447 100%);
                border: 1px solid #2C3E50; border-radius: 8px; padding: 14px 18px;
                border-left: 3px solid #FF4655; flex: 1; min-width: 120px; text-align: center;
            }
            .brand-kpi-label { color: #8B9CB6; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
            .brand-kpi-value { color: #ECE8E1; font-size: 1.5rem; font-weight: 700; }
            </style>
            """, unsafe_allow_html=True)

            total = len(all_brands_df)
            status_counts = all_brands_df[status_col].value_counts()

            kpi_html = '<div class="brand-kpi-row">'
            kpi_html += f'<div class="brand-kpi-card" style="border-left-color:#FF4655;"><div class="brand-kpi-label">总品牌数</div><div class="brand-kpi-value">{total}</div></div>'
            for s in ["待联系", "已联系", "跟进中", "已合作", "已放弃"]:
                cnt = status_counts.get(s, 0)
                bg, fg = status_colors.get(s, ("#2C3E50", "#ECE8E1"))
                pct = f"{cnt/total*100:.0f}%" if total > 0 else "0%"
                kpi_html += f'<div class="brand-kpi-card" style="border-left-color:{bg};"><div class="brand-kpi-label">{s}</div><div class="brand-kpi-value">{cnt}<span style="font-size:0.7rem;color:#8B9CB6;margin-left:4px;">{pct}</span></div></div>'
            kpi_html += '</div>'
            st.markdown(kpi_html, unsafe_allow_html=True)

        cat_opts = ["全部"] + sorted(all_brands_df[cat_col].dropna().unique().tolist())
        status_opts = ["全部"] + sorted(all_brands_df[status_col].dropna().unique().tolist())

        fc1, fc2 = st.columns(2)
        with fc1:
            filter_cat = st.selectbox("按类目筛选", cat_opts, key="filter_category")
        with fc2:
            filter_status = st.selectbox("按跟进状态筛选", status_opts, key="filter_status")

        is_filtered = filter_cat != "全部" or filter_status != "全部"
        view_brands = all_brands_df.copy()
        if filter_cat != "全部":
            view_brands = view_brands[view_brands[cat_col] == filter_cat]
        if filter_status != "全部":
            view_brands = view_brands[view_brands[status_col] == filter_status]
        if is_filtered:
            st.markdown(f'<div style="background:#1A2634;border:1px solid #2C3E50;border-radius:6px;padding:10px 16px;margin-bottom:12px;color:#8B9CB6;font-size:0.9rem;">🔍 筛选结果：<span style="color:#ECE8E1;font-weight:700;">{len(view_brands)}</span> 条 / 共 <span style="color:#ECE8E1;font-weight:700;">{len(all_brands_df)}</span> 条</div>', unsafe_allow_html=True)

        edit_df = view_brands.copy()
        edit_df["删除本条"] = False

        edit_brands = st.data_editor(
            edit_df,
            width="stretch",
            num_rows="dynamic",
            key="brands_editor",
        )

        bs1, bs2, bs3 = st.columns([1, 1, 3])
        with bs1:
            if st.button("💾 保存修改", key="save_brands"):
                final_df = merge_filtered_back(all_brands_df, view_brands, edit_brands) if is_filtered else edit_brands
                if "删除本条" in final_df.columns:
                    final_df = final_df.drop(columns=["删除本条"])
                save_excel(final_df, BRANDS_PATH, "✅ 品牌线索已保存！")

        with bs2:
            if st.button("🗑️ 执行勾选删除", key="del_brand_batch", type="secondary"):
                to_del_mask = edit_brands["删除本条"] == True
                del_count = to_del_mask.sum()
                if del_count == 0:
                    st.warning("⚠️ 没有勾选任何要删除的行！")
                else:
                    if is_filtered:
                        drop_index_list = view_brands.index[to_del_mask]
                        new_full_df = all_brands_df.drop(drop_index_list)
                    else:
                        new_full_df = edit_brands[~to_del_mask]

                    if "删除本条" in new_full_df.columns:
                        new_full_df = new_full_df.drop(columns=["删除本条"])

                    if save_excel(new_full_df, BRANDS_PATH, f"✅ 成功删除 {del_count} 条品牌线索！"):
                        st.rerun()

        with bs3:
            st.download_button(
                "📥 导出全部品牌线索",
                data=export_excel(edit_brands.drop(columns=["删除本条"], errors="ignore")),
                file_name=f"品牌线索_{datetime.date.today()}.xlsx",
                key="download_brands",
            )


