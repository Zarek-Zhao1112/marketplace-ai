"""
Tab 5: 招商管理
- 邮件生成
- 发送记录
- 邮件模板库
"""
import streamlit as st
import pandas as pd
import traceback
from datetime import datetime

from src.config.settings import EMAILS_PATH, BRANDS_PATH
from src.web.utils import load_excel, save_excel, export_excel, render_copy_button
from src.web.ai import generate_outreach_email
from src.web.styles import inject_global_css, render_section_header

EMAIL_STATUS = ["待发送", "已发送", "已回复", "已关闭", "跟进中"]


def _init_emails():
    import os
    if not os.path.exists(EMAILS_PATH):
        cols = ["ID", "Brand", "Recipient", "Email", "Subject", "Body",
                "Status", "SentTime", "Note", "CreateTime"]
        pd.DataFrame(columns=cols).to_excel(EMAILS_PATH, index=False, engine="openpyxl")


def _load_emails():
    _init_emails()
    return load_excel(EMAILS_PATH)


def _save_emails(df):
    return save_excel(df, EMAILS_PATH, "✅ 邮件记录已保存！")


def _safe_brand_names(brands_df):
    """安全提取品牌名称列表，过滤 None / NaN / 空字符串"""
    if brands_df is None or brands_df.empty:
        return []
    col = "BrandName" if "BrandName" in brands_df.columns else None
    if col is None:
        for c in brands_df.columns:
            if "brand" in str(c).lower() and "name" in str(c).lower():
                col = c
                break
    if col is None:
        col = brands_df.columns[1] if len(brands_df.columns) > 1 else brands_df.columns[0]
    raw = brands_df[col].tolist()
    return [str(v).strip() for v in raw if v is not None and str(v).strip() and str(v).strip().lower() != "nan"]


def _safe_brand_info(brands_df, selected_brand):
    """安全提取品牌详情，所有异常统一返回默认值"""
    default = {
        "品牌名称": selected_brand or "",
        "所属类目": "其他",
        "品牌规模": "成长品牌",
        "Slogan": "",
        "品牌简介": "",
        "销售渠道": "",
    }
    try:
        col = "BrandName" if "BrandName" in brands_df.columns else None
        if col is None:
            for c in brands_df.columns:
                if "brand" in str(c).lower() and "name" in str(c).lower():
                    col = c
                    break
        if col is None:
            col = brands_df.columns[1] if len(brands_df.columns) > 1 else brands_df.columns[0]

        matches = brands_df[brands_df[col].astype(str).str.strip() == selected_brand.strip()]
        if matches.empty:
            return default

        row = matches.iloc[0]

        def val(col_name, fallback=""):
            try:
                v = row.get(col_name, fallback)
                if pd.isna(v) or str(v).strip().lower() in ("nan", "none", ""):
                    return fallback
                return str(v).strip()
            except Exception:
                return fallback

        return {
            "品牌名称": val("BrandName", selected_brand),
            "所属类目": val("Category", "其他"),
            "品牌规模": val("Scale", "成长品牌"),
            "Slogan": val("Slogan"),
            "品牌简介": val("Description"),
            "销售渠道": val("Channels"),
        }
    except Exception:
        return default


def render(tab):
    with tab:
        try:
            inject_global_css()

            st.markdown("""
            <div style="margin-bottom: 1rem;">
                <h2 style="margin-bottom: 0.25rem;">招商管理</h2>
                <p style="color: #8B9CB6; font-size: 0.9rem;">AI生成个性化招商邮件，跟踪发送状态</p>
            </div>
            """, unsafe_allow_html=True)

            tab1, tab2, tab3, tab4 = st.tabs(["✉️ 生成邮件", "📋 发送记录", "📚 邮件模板", "🤝 经销商招募"])

            # ── Tab 1 ──────────────────────────────────────────────
            with tab1:
                try:
                    render_section_header("AI 生成招商邮件", "选择品牌或手动输入，一键生成个性化邮件")
                    _render_compose_tab()
                except Exception as e:
                    st.error(f"❌ 生成邮件模块出错：{e}")
                    st.code(traceback.format_exc())

            # ── Tab 2 ──────────────────────────────────────────────
            with tab2:
                try:
                    render_section_header("邮件发送记录", "管理和跟踪所有邮件状态")
                    _render_records_tab()
                except Exception as e:
                    st.error(f"❌ 发送记录模块出错：{e}")
                    st.code(traceback.format_exc())

            # ── Tab 3 ──────────────────────────────────────────────
            with tab3:
                try:
                    render_section_header("邮件模板库", "预置模板，快速生成标准邮件")
                    _render_templates_tab()
                except Exception as e:
                    st.error(f"❌ 邮件模板模块出错：{e}")
                    st.code(traceback.format_exc())

            # ── Tab 4 ──────────────────────────────────────────────
            with tab4:
                try:
                    render_section_header("经销商招募", "生成招募话术，管理线索状态")
                    _render_dealer_recruitment_tab()
                except Exception as e:
                    st.error(f"❌ 经销商招募模块出错：{e}")
                    st.code(traceback.format_exc())
        except Exception as e:
            st.error(f"❌ 招商管理模块严重错误：{e}")
            st.code(traceback.format_exc())


def _render_compose_tab():
    brands_df = load_excel(BRANDS_PATH)

    if brands_df.empty:
        st.warning("⚠️ 暂无品牌数据，请先在「品牌线索」中添加品牌")
        _render_manual_input()
        return

    brand_names = _safe_brand_names(brands_df)

    if not brand_names:
        st.warning("⚠️ 品牌名称列表为空，请检查品牌数据")
        _render_manual_input()
        return

    options = ["手动输入"] + brand_names
    selected_brand = st.selectbox("选择品牌", options, key="email_brand_select_v2")

    if selected_brand == "手动输入":
        _render_manual_input()
    else:
        try:
            brand_info = _safe_brand_info(brands_df, selected_brand)
            st.info(
                f"已选择品牌：**{brand_info['品牌名称']}** "
                f"| 类目：{brand_info['所属类目']} "
                f"| 规模：{brand_info['品牌规模']}"
            )
            _render_email_form(brand_info)
        except Exception as e:
            st.error(f"❌ 读取品牌信息出错：{e}")
            st.code(traceback.format_exc())

    st.divider()


def _render_manual_input():
    brand_info = {
        "品牌名称": st.text_input("品牌名称", key="manual_brand_name_v2"),
        "所属类目": st.selectbox(
            "所属类目",
            ["电竞外设", "电脑硬件", "手机数码", "家居用品", "美妆个护", "其他"],
            key="manual_brand_cat_v2",
        ),
        "品牌规模": st.selectbox(
            "品牌规模",
            ["初创品牌", "成长品牌", "成熟品牌", "知名品牌"],
            key="manual_brand_scale_v2",
        ),
        "Slogan": st.text_input("Slogan（可选）", key="manual_brand_slogan_v2"),
        "品牌简介": st.text_area("品牌简介（可选）", key="manual_brand_desc_v2"),
        "销售渠道": st.text_input("现有销售渠道（可选）", key="manual_brand_channels_v2"),
    }
    _render_email_form(brand_info)


def _render_email_form(brand_info):
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        recipient_name = st.text_input("收件人姓名", key="email_recipient_name_v2")
        recipient_email = st.text_input("收件人邮箱", key="email_recipient_email_v2")
    with col2:
        sender_name = st.text_input("你的姓名", value="BD Team", key="email_sender_name_v2")
        sender_title = st.text_input("你的职位", value="Marketplace Manager", key="email_sender_title_v2")

    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        tone = st.selectbox("邮件语气", ["专业正式", "友好轻松", "简洁直接"], key="compose_email_tone_v2")
    with col4:
        language = st.selectbox("邮件语言", ["英文", "中文", "中英双语"], key="compose_email_lang_v2")

    extra_notes = st.text_area("额外备注（可选）", placeholder="如：希望安排15分钟通话介绍...", key="compose_email_notes_v2")

    if st.button("🤖 生成邮件", key="compose_gen_email_btn_v2", width="stretch", type="primary"):
        if not brand_info.get("品牌名称"):
            st.error("请填写品牌名称")
        elif not recipient_email:
            st.error("请填写收件人邮箱")
        else:
            with st.spinner("AI 正在生成邮件..."):
                sender_info = {"name": sender_name, "position": sender_title, "email": "", "phone": ""}
                email_config = {"tone": tone, "language": language, "notes": extra_notes}
                result, msg = generate_outreach_email(brand_info, sender_info, email_config)

            if result:
                st.success(f"✅ {msg}")
                st.subheader("邮件主题")
                st.text_input("Subject", value=result["subject"], key="email_subject_display_v2", disabled=True)
                st.subheader("邮件正文")
                st.text_area("Body", value=result["body"], height=300, key="compose_email_body_display_v2", disabled=True)
                render_copy_button(result["subject"] + "\n\n" + result["body"], "copy_email_v2", "📋 复制邮件到剪贴板")

                if st.button("💾 保存到发送记录", key="save_email_record_v2"):
                    _init_emails()
                    df = _load_emails()
                    new_row = pd.DataFrame([{
                        "ID": f"E{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "Brand": brand_info["品牌名称"],
                        "Recipient": recipient_name,
                        "Email": recipient_email,
                        "Subject": result["subject"],
                        "Body": result["body"],
                        "Status": "待发送",
                        "SentTime": "",
                        "Note": extra_notes,
                        "CreateTime": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    _save_emails(df)
                    st.rerun()
            else:
                st.error(f"❌ {msg}")


def _render_records_tab():
    emails_df = _load_emails()

    if emails_df.empty:
        st.info("📭 暂无邮件记录")
        return

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.selectbox("状态筛选", ["全部"] + EMAIL_STATUS, key="email_status_filter_v2")
    with col_f2:
        brand_search = st.text_input("品牌搜索", key="email_brand_search_v2")
    with col_f3:
        st.write("")
        st.write("")

    filtered = emails_df.copy()
    if status_filter != "全部" and "Status" in filtered.columns:
        filtered = filtered[filtered["Status"] == status_filter]
    if brand_search and "Brand" in filtered.columns:
        filtered = filtered[filtered["Brand"].str.contains(brand_search, case=False, na=False)]

    st.caption(f"共 {len(filtered)} 条记录")

    if filtered.empty:
        st.info("📭 没有匹配的记录")
        return

    edit_df = st.data_editor(filtered, width="stretch", num_rows="dynamic", key="emails_editor_v2")

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("💾 保存修改", key="save_emails_v2"):
            _save_emails(edit_df)
    with col_b2:
        if st.button("📥 导出 Excel", key="export_emails_v2"):
            excel_data = export_excel(edit_df)
            st.download_button(
                "下载文件", data=excel_data,
                file_name=f"邮件记录_{datetime.now().strftime('%Y%m%d')}.xlsx",
                key="download_emails_btn_v2",
            )

    st.divider()
    st.subheader("查看详情")
    email_ids = filtered["ID"].tolist() if "ID" in filtered.columns else []
    if not email_ids:
        return

    selected_id = st.selectbox("选择邮件", email_ids, key="email_detail_select_v2")
    if not selected_id:
        return

    match = emails_df[emails_df["ID"] == selected_id]
    if match.empty:
        st.warning("未找到该邮件记录")
        return

    row = match.iloc[0]
    st.write(f"**品牌：** {row.get('Brand', '')}")
    st.write(f"**收件人：** {row.get('Recipient', '')} ({row.get('Email', '')})")
    st.write(f"**状态：** {row.get('Status', '')}")
    st.write(f"**创建时间：** {row.get('CreateTime', '')}")

    st.subheader("邮件主题")
    st.text(row.get("Subject", ""))

    st.subheader("邮件正文")
    st.text_area("内容", value=row.get("Body", ""), height=300, disabled=True, key="detail_content_v2")

    current_status = row.get("Status", "待发送")
    new_status = st.selectbox(
        "更新状态", EMAIL_STATUS,
        index=EMAIL_STATUS.index(current_status) if current_status in EMAIL_STATUS else 0,
        key="update_status_v2",
    )
    note = st.text_input("备注", value=str(row.get("Note", "")) if pd.notna(row.get("Note")) else "", key="update_note_v2")

    if st.button("✅ 更新状态", key="btn_update_status_v2"):
        idx = emails_df[emails_df["ID"] == selected_id].index[0]
        emails_df.at[idx, "Status"] = new_status
        if new_status == "已发送":
            emails_df.at[idx, "SentTime"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        emails_df.at[idx, "Note"] = note
        _save_emails(emails_df)
        st.rerun()


def _render_templates_tab():
    builtin_templates = {
        "首次触达": {
            "subject": "Partnership Opportunity: {brand_name} x Newegg",
            "body": (
                "Dear {brand_name} Team,\n\n"
                "I'm reaching out from Newegg's marketplace partnership team. We've been following "
                "{brand_name}'s growth in the {category} space and believe your products would resonate "
                "strongly with our tech-savvy North American audience.\n\n"
                "Newegg is home to over 40 million registered customers who actively seek quality "
                "{category} products. We'd love to explore how we can help {brand_name} expand its "
                "reach in the North American market.\n\n"
                "Would you be open to a 15-minute call next week to discuss potential collaboration?\n\n"
                "Best regards,\n{sender_name}\n{sender_title}\nNewegg Marketplace Team"
            ),
        },
        "跟进邮件": {
            "subject": "Following up: {brand_name} x Newegg Collaboration",
            "body": (
                "Dear {brand_name} Team,\n\n"
                "I wanted to follow up on my previous email regarding a potential partnership between "
                "{brand_name} and Newegg.\n\n"
                "We're currently running our {category} promotional campaign and think this could be a "
                "great opportunity for {brand_name} to gain visibility among our engaged customer base.\n\n"
                "Please let me know if you'd like to schedule a brief call to discuss further.\n\n"
                "Best regards,\n{sender_name}\n{sender_title}\nNewegg Marketplace Team"
            ),
        },
        "节日促销": {
            "subject": "Invitation: {brand_name} - Exclusive Newegg Campaign",
            "body": (
                "Dear {brand_name} Team,\n\n"
                "As we approach our upcoming sales event, we'd like to extend an exclusive invitation "
                "to {brand_name} to participate in our {category} featured promotion.\n\n"
                "Our previous campaigns have delivered strong results for similar brands, with average "
                "sales lifts of 3-5x during promotional periods.\n\n"
                "We'd be happy to share more details and discuss how we can tailor the campaign to "
                "maximize {brand_name}'s success on Newegg.\n\n"
                "Looking forward to hearing from you.\n\n"
                "Best regards,\n{sender_name}\n{sender_title}\nNewegg Marketplace Team"
            ),
        },
    }

    for name, template in builtin_templates.items():
        with st.expander(f"📧 {name}", expanded=False):
            st.write("**主题模板：**")
            st.code(template["subject"], language=None)
            st.write("**正文模板：**")
            st.code(template["body"], language=None)

    st.divider()
    st.info("💡 提示：使用「生成邮件」功能可以基于品牌信息自动生成个性化邮件，比模板更精准。")


def _render_dealer_recruitment_tab():
    """经销商招募标签页"""
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h3 style="margin-bottom: 0.25rem;">🤝 经销商招募话术生成器</h3>
        <p style="color: #8B9CB6; font-size: 0.9rem;">输入品牌/品类和渠道，生成个性化招募话术</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        brand_name = st.text_input("品牌名称", key="dealer_brand_name")
        category = st.text_input("品类", placeholder="如：显卡、智能家居、小家电", key="dealer_category")
    with col2:
        channel = st.selectbox(
            "渠道类型",
            ["1688/义乌工厂", "亚马逊/Walmart卖家", "老卖家转介绍", "蓝海品类（智能家居/小家电）"],
            key="dealer_channel"
        )
        contact_name = st.text_input("联系人姓名（可选）", key="dealer_contact_name")

    if st.button("🎯 生成招募话术", key="generate_dealer_pitch", type="primary"):
        if not brand_name and not category:
            st.error("请填写品牌名称或品类")
        else:
            pitch = _generate_dealer_pitch(brand_name, category, channel, contact_name)
            st.success("✅ 话术生成成功！")
            st.subheader("招募话术")
            st.text_area("话术内容", value=pitch, height=250, key="dealer_pitch_display")
            render_copy_button(pitch, "copy_dealer_pitch", "📋 复制话术到剪贴板")

    st.divider()

    # Newegg平台核心数据
    st.subheader("📊 Newegg平台核心数据（话术素材）")
    with st.expander("用户画像", expanded=False):
        st.markdown("""
        | 指标 | 数据 | 话术价值 |
        |------|------|---------|
        | 总用户数 | 4700万+ | "北美第二大电商平台" |
        | 男性占比 | 70%+ | "科技品类精准用户" |
        | 平均年龄 | 36岁 | "成熟消费者，购买力强" |
        | 本科以上 | 62%+ | "高学历高收入人群" |
        | 年收入$7.5万+ | 42% | "高消费力用户" |
        | 客单价$200+ | - | "高客单价，利润空间大" |
        """)

    with st.expander("招商优势", expanded=False):
        st.markdown("""
        | 优势 | 话术 |
        |------|------|
        | 佣金低 | 新卖家前90天佣金只要6%，比亚马逊低一半 |
        | 用户精准 | 4700万+用户，70%男性，年收入$7.5万+，客单价$200+ |
        | 竞争小 | 非硬件品类（智能家居、小家电）竞争还不大 |
        | 工具有支持 | SellingPilot官方ERP，库存同步、AI客服、AI作图都能用 |
        | 物流有保障 | SBN新蛋发货标识，排名更高，24/7客服 |
        | 营销有支持 | 站内促销+谷歌广告+联盟营销+72万粉丝社媒 |
        | 入驻快 | 当天开店，最快3天上线 |
        | 中国区支持 | 跨国开店专属运营团队，全程人民币结算 |
        """)

    with st.expander("蓝海品类推荐", expanded=False):
        st.markdown("""
        | 品类 | 佣金 | 适合经销商类型 |
        |------|------|--------------|
        | Smart Home & Security | 12-14% | 安防摄像头、智能门锁 |
        | Appliances | 12-14% | 小家电、厨房电器 |
        | Home & Outdoors | 12-14% | 游戏椅、办公椅 |
        | Health & Sports | 12-14% | 健康设备、运动器材 |
        | Toys/Drones/Maker | 12-14% | 无人机、3D打印机 |
        """)

    with st.expander("开店资料清单", expanded=False):
        st.markdown("""
        | 资料 | 说明 |
        |------|------|
        | 营业执照 | 中国大陆/香港/美国 |
        | 法人身份证/护照 | 正反面 |
        | 外币收款账号 | +开户许可证+银行信息证明 |
        | W8表格 | 税务表格 |
        | 外币信用卡 | 支付平台费用 |
        """)


def _generate_dealer_pitch(brand_name, category, channel, contact_name):
    """生成经销商招募话术"""
    display_name = f"@{contact_name}" if contact_name else "@[联系人]"
    display_brand = brand_name if brand_name else category
    display_category = category if category else "产品"

    if channel == "1688/义乌工厂":
        return f"""{display_name}，你们{display_category}在1688上做得挺好的吧？

Newegg是北美第二大电商平台，4700万+用户，70%是男性，平均年龄36岁，年收入$7.5万+，客单价$200+。{display_category}品类现在竞争还不大。

新卖家前90天佣金只要6%，比亚马逊低一半。你们有货源优势，在Newegg上应该很有竞争力。

要不要了解一下入驻流程？"""

    elif channel == "亚马逊/Walmart卖家":
        return f"""{display_name}，你们在亚马逊/Walmart做得挺好的吧？

Newegg是纳斯达克上市公司（NEGG），4700万+用户，70%男性，年收入$7.5万+，高客单价$200+。{display_category}品类用户特别精准。

新卖家前90天佣金只要6%，比你们现在平台低。而且有SellingPilot官方ERP，库存同步、AI客服、AI作图都能用，99块一个月，三杯奶茶钱。

SBN官方物流发货，排名更高，24/7客服支持。要不要多一个销售渠道？"""

    elif channel == "老卖家转介绍":
        return f"""{display_name}，听说你们{display_category}做得挺好的，我们这边有一些Newegg的资源想对接。

Newegg是北美第二大电商平台，4700万+用户，客单价$200+。新卖家前90天佣金只要6%，还有SellingPilot官方ERP工具支持。

SBN官方物流，排名更高。你们有货源优势，在Newegg上应该很有竞争力。要不要了解一下？"""

    else:  # 蓝海品类
        return f"""{display_name}，你们{display_category}在北美市场做得挺好的吧？

Newegg现在Home & Outdoor品类竞争还不大，4700万+用户，70%男性，年收入$7.5万+，对{display_category}需求很大。

新卖家前90天佣金只要6%，还有站内促销、谷歌广告、联盟营销支持。你们有产品优势，在Newegg上应该很有机会。

要不要了解一下？"""
