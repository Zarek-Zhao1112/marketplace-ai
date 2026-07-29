import json
import re
import uuid
import urllib.parse
import requests
import streamlit as st
import os

from src.config.settings import NEWEGG_PITCHES, SCALE_VALUE_PROPS, CONTACT_PATHS
from src.web.utils import clean_domain, extract_emails_from_text
from src.web.web_scraper import fetch_website_content
from src.config.settings import ARK_API_URL, MODEL_ENDPOINT


def search_company_emails(domain: str, limit: int = 10):
    api_key = st.session_state.get("hunter_api_key", "")
    if not api_key:
        return None, "请先在左侧侧边栏配置 Hunter.io API Key"

    domain = clean_domain(domain)
    url = (f"https://api.hunter.io/v2/domain-search"
           f"?domain={domain}&limit={limit}&api_key={api_key}")
    try:
        resp = requests.get(url, timeout=15, verify=False)
        data = resp.json()
        if resp.status_code != 200:
            errors = data.get("errors", [{}])
            detail = errors[0].get("details", "未知错误") if errors else "未知错误"
            return None, f"API 请求失败：{detail}"
        emails = [
            {"邮箱": i.get("value", ""), "LinkedIn": i.get("linkedin", ""),
             "职位": i.get("position", ""), "来源": f"Hunter.io - {domain}"}
            for i in data.get("data", {}).get("emails", [])
        ]
        return emails, f"找到 {len(emails)} 个邮箱（域名：{domain}）"
    except requests.exceptions.Timeout:
        return None, "请求超时，请稍后重试"
    except requests.exceptions.ConnectionError:
        return None, "网络连接失败，请检查网络设置"
    except requests.exceptions.RequestException as e:
        return None, f"网络错误：{e}"
    except (KeyError, ValueError) as e:
        return None, f"数据解析失败：{e}"
    except Exception as e:
        return None, f"未知错误：{e}"


def search_company_emails_official_site(domain: str, limit: int = 10):
    domain = clean_domain(domain)
    base = f"https://{domain}"

    all_emails = {}
    pages_tried = 0
    pages_ok = 0

    for path in CONTACT_PATHS:
        if len(all_emails) >= limit:
            break
        url = base + path
        content, err = fetch_website_content(url)
        pages_tried += 1
        if err:
            continue
        pages_ok += 1
        found = extract_emails_from_text(content)
        for e in found:
            if e not in all_emails:
                all_emails[e] = url

    if pages_ok == 0:
        return None, f"无法访问 {domain} 及其常见联系页面，请检查域名是否正确"

    if not all_emails:
        return [], f"成功访问 {pages_ok} 个页面，但未在官网中发现公开邮箱地址"

    emails = [
        {"邮箱": email, "LinkedIn": "", "职位": "",
         "来源": f"官网爬取 - {src}"}
        for email, src in list(all_emails.items())[:limit]
    ]
    return emails, f"在官网中找到 {len(emails)} 个邮箱（共访问 {pages_ok}/{pages_tried} 个页面）"


def build_search_engine_links(company_name: str, domain: str = ""):
    links = []
    domain = clean_domain(domain) if domain else ""

    queries = []
    if domain:
        queries.append(("站内邮箱搜索", f"site:{domain} 邮箱"))
    if company_name:
        queries.append(("商务合作邮箱", f"{company_name} 商务合作 邮箱"))
        queries.append(("招聘HR邮箱", f"{company_name} 招聘 邮箱"))

    for label, q in queries:
        encoded = urllib.parse.quote(q)
        links.append({
            "用途": label,
            "查询语句": q,
            "百度": f"https://www.baidu.com/s?wd={encoded}",
            "Google": f"https://www.google.com/search?q={encoded}",
        })
    return links


def build_qcc_search_links(company_name: str = "", domain: str = ""):
    links = []
    domain = clean_domain(domain) if domain else ""

    keyword = company_name.strip() if company_name.strip() else domain
    if not keyword:
        return links

    encoded = urllib.parse.quote(keyword)

    links.append({
        "平台": "企查查",
        "关键词": keyword,
        "链接": f"https://www.qcc.com/web/search?key={encoded}",
    })
    links.append({
        "平台": "天眼查",
        "关键词": keyword,
        "链接": f"https://www.tianyancha.com/search?key={encoded}",
    })
    links.append({
        "平台": "爱企查",
        "关键词": keyword,
        "链接": f"https://aiqicha.baidu.com/s?q={encoded}",
    })

    if domain:
        combo_q = f"site:qcc.com {domain}"
        links.append({
            "平台": "百度搜「企查查 + 域名」",
            "关键词": combo_q,
            "链接": f"https://www.baidu.com/s?wd={urllib.parse.quote(combo_q)}",
        })

    return links


def analyze_brand_info(website_content: str):
    api_key = st.session_state.get("doubao_api_key", "")
    if not api_key:
        return None, "请先在左侧侧边栏配置豆包 API Key"

    prompt = f"""
请分析下面的品牌官网内容，提取以下信息，以 JSON 格式输出：

{{
    "brand_name": "品牌名称",
    "slogan": "品牌 Slogan/口号",
    "description": "品牌简介（100-200字）",
    "main_categories": ["主营产品类目"],
    "founded_year": "成立年份（只写数字）",
    "company_size": "公司规模，必须从以下选项中选一个：初创品牌、成长品牌、成熟品牌、知名品牌",
    "target_market": ["目标市场，从以下选项中选择一个或多个：北美、欧洲、东南亚、日本、全球"],
    "social_media": {{
        "facebook": "Facebook 链接或空字符串",
        "twitter": "Twitter/X 链接或空字符串",
        "instagram": "Instagram 链接或空字符串",
        "linkedin": "LinkedIn 链接或空字符串"
    }},
    "sales_channels": ["现有销售渠道，如亚马逊、Best Buy、官网等"]
}}

要求：
1. 尽可能准确提取；找不到的字段设为空字符串或空数组
2. company_size 必须严格从四个选项中选一个
3. main_categories 从以下选项中选最匹配的：电竞外设、电脑硬件、手机数码、家居用品、美妆个护、其他
4. target_market 根据官网语言、货币、地址、物流范围等信息推断，找不到则为空数组
5. 只输出 JSON，不要包含任何说明文字或 Markdown 代码块

官网内容：
{website_content}
"""
    url = ARK_API_URL
    payload = {
        "model": MODEL_ENDPOINT,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3, "max_tokens": 2000,
        "response_format": {"type": "json_object"},
    }
    try:
        resp = requests.post(url, timeout=90,
                             headers={"Content-Type": "application/json",
                                      "Authorization": f"Bearer {api_key}"},
                             json=payload)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        raw = re.sub(r'\s*```$', '', raw)
        return json.loads(raw), "品牌信息分析成功！"
    except requests.exceptions.Timeout:
        return None, "AI 分析超时，请稍后重试"
    except requests.exceptions.HTTPError as e:
        return None, f"豆包 API 错误：{e.response.status_code}"
    except (KeyError, IndexError):
        return None, "AI 返回格式异常，请重试"
    except json.JSONDecodeError as e:
        return None, f"JSON 解析失败：{e}"
    except Exception as e:
        return None, f"分析失败：{e}"


def generate_outreach_email(brand_info: dict, sender_info: dict, email_config: dict = None):
    api_key = st.session_state.get("doubao_api_key", "")
    if not api_key:
        return None, "请先在左侧侧边栏配置豆包 API Key"

    if email_config is None:
        email_config = {}

    brand_name = brand_info.get("品牌名称", "the brand")
    category = brand_info.get("所属类目", "")
    scale = brand_info.get("品牌规模", "")
    markets = brand_info.get("目标市场", "")
    channels = brand_info.get("销售渠道", "")
    slogan = brand_info.get("Slogan", "")
    description = brand_info.get("品牌简介", "")

    sender_name = sender_info.get("name", "Our Team")
    sender_title = sender_info.get("position", "Marketplace Manager")
    sender_email = sender_info.get("email", "")
    sender_phone = sender_info.get("phone", "")

    tone = email_config.get("tone", "专业正式")
    language = email_config.get("language", "英文")
    extra_notes = email_config.get("notes", "").strip()
    if language == "中英双语":
        language_format_note = (
            "邮件语言：中英双语，采用「逐句对照」格式 —— 每写完一句中文，"
            "紧接着另起一行写该句对应的英文翻译，再写下一句中文，再写对应英文，"
            "依此类推，全篇都按「中文句 → 英文句」的顺序逐句交替排列。"
            "不要把中文和英文分成两个独立的段落或两部分（不要出现【中文】【English】这样的分区标题）。"
            "署名部分（姓名、职位、邮箱、电话）只需出现一次，无需中英重复。"
        )
        length_note = "中英文逐句对照，每句中文+对应英文为一组，全篇共6-8组对照句"
    else:
        language_format_note = f"邮件语言：{language}"
        length_note = "总字数 220-280 英文单词（英文邮件）/ 180-230 汉字（中文邮件）"

    # 用列表索引访问，避免乱码key问题
    # NEWEGG_PITCHES 顺序: 电竞外设, 电脑硬件, 手机数码, 家居用品, 美妆个护, 其他
    pitch_list = list(NEWEGG_PITCHES.values())
    pitch = pitch_list[-1]  # 默认用最后一个（其他）
    
    # SCALE_VALUE_PROPS 顺序: 初创品牌, 成长品牌, 成熟品牌, 知名品牌
    scale_list = list(SCALE_VALUE_PROPS.values())
    scale_vp = scale_list[1]  # 默认用第二个（成长品牌）

    channel_note = (
        f"品牌当前在 {channels} 销售，请在邮件中自然暗示新蛋是对其现有渠道的有益补充，"
        f"而非竞争关系。"
        if channels else ""
    )

    sig_lines = [sender_name, sender_title, "Newegg Marketplace Team"]
    if sender_email:
        sig_lines.append(sender_email)
    if sender_phone:
        sig_lines.append(sender_phone)
    signature = " | ".join(sig_lines)

    prompt = f"""
你是新蛋（Newegg）跨境招商专员，请撰写一封高质量的个性化首次触达邮件，邀请品牌入驻新蛋平台。

═══ 品牌信息 ═══
品牌名称：{brand_name}
所属类目：{category}
品牌规模：{scale}
目标市场：{markets}
Slogan：{slogan or "（未知）"}
品牌简介：{description or "（未知）"}
现有销售渠道：{channels or "（未知）"}

═══ 新蛋平台核心卖点（请自然融入正文，不要逐条列举）═══
平台定位：{pitch['platform']}
受众特点：{pitch['audience']}
类目优势：{pitch['category']}
服务支持：{pitch['support']}
品牌规模专属价值：{scale_vp}
{f"渠道策略：{channel_note}" if channel_note else ""}

═══ 额外备注 ═══
{extra_notes or "无"}

═══ 邮件撰写规范 ═══
语气：{tone}，真诚自然，避免过度营销话术
{language_format_note}


结构（严格按此顺序）：
1. Subject Line —— 个性化、抓眼球，必须包含品牌名称，暗示具体价值
2. 称呼 —— Dear {brand_name} Team,
3. 开场白（2-3句）—— 自我介绍 + 提及品牌具体亮点（Slogan/类目定位），
   体现你做过功课，让对方感受到这不是群发模板
4. 新蛋价值主张（3-4句）—— 将平台卖点和类目优势自然融合，
   突出对该品牌最相关的 2 个核心卖点
5. 品牌规模专属一句话 —— 自然引用上方规模专属价值主张
6. 行动号召（1-2句）—— 具体邀请（如 15 分钟介绍通话），语气友好不强迫
7. 署名 —— {signature}

约束：
- {length_note}
- 禁止使用通用套话如 "I hope this email finds you well"
- 禁止分点/列表，全程流畅段落
- 行动号召要有具体时间建议（如 "next week" 或 "this week"）

═══ 去AI化写作规则（必须遵守）═══
1. 直接陈述事实，禁止使用"此外"、"至关重要"、"深入探讨"、"强调"、"增强"、"培养"等AI高频词汇
2. 禁止三段式结构（如"无缝、直观和强大"、"高效、专业和可靠"）
3. 句子长度要有变化，不要每句都差不多长
4. 用具体数据说话（如"4700万用户"），不要用模糊形容词（如"庞大的用户群体"）
5. 避免"不仅...而且..."、"不仅仅是...更是..."等否定式排比
6. 避免"不断演变的格局"、"关键作用"、"重要时刻"等夸大象征意义的表达
7. 语气要像真人写的商务邮件，不要像AI模板

请严格按以下 JSON 格式输出（只输出 JSON，不含任何说明或代码块标记）：
{{
  "subject": "邮件主题行",
  "body": "邮件正文全文，换行用\\n表示，包含称呼到署名的完整内容"
}}
"""

    url = ARK_API_URL
    payload = {
        "model": MODEL_ENDPOINT,
        "messages": [{"role": "user", "content": prompt + f"\n\n[rid:{uuid.uuid4().hex[:6]}]"}],
        "temperature": 0.9,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(url, timeout=90,
                             headers={"Content-Type": "application/json",
                                      "Authorization": f"Bearer {api_key}"},
                             json=payload)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        raw = re.sub(r'^```(?:json)?\s*', '', raw.strip())
        raw = re.sub(r'\s*```$', '', raw)
        parsed = json.loads(raw)
        if "subject" not in parsed or "body" not in parsed:
            return None, "AI 返回数据缺少 subject 或 body 字段，请重试"
        return parsed, "邮件生成成功！"

    except requests.exceptions.Timeout:
        return None, "AI 生成超时，请稍后重试"
    except requests.exceptions.HTTPError as e:
        return None, f"豆包 API 错误：{e.response.status_code}"
    except (KeyError, IndexError):
        return None, "AI 返回格式异常，请重试"
    except json.JSONDecodeError as e:
        return None, f"JSON 解析失败：{e}"
    except Exception as e:
        return None, f"邮件生成失败：{e}"
