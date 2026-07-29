# Project memory
_Durable project-level knowledge. Persists across all sessions in this project. Edit only content under italic instructions._

## Project context
_What is this project? What's its goal? High-level identity._

Newegg跨境BD智能助手 (Cross-border e-commerce BD Intelligent Assistant) for Newegg marketplace. A Python toolset that helps BD (business development) staff with:
- Enterprise WeChat issue processing and categorization (AI-powered)
- Brand lead scraping from Amazon new releases (AI-filtered)
- Seller follow-up tracking and timeline management
- Operational knowledge base (experience library) with keyword + AI semantic search
- AI reply suggestions based on historical conversation patterns

Streamlit Web UI (`streamlit run app.py`). AI backend: Volcengine ARK (豆包/Doubao) API.

**Single-person internal tool** — keep architecture simple, no over-engineering. **Web-only** — CLI mode has been removed.

## Rules
_Hard constraints from user that every session must respect._

- User language is Chinese — respond in Chinese
- Single-person tool — no auth, no multi-user, no complex deployment needed
- Simplicity over features — user actively removes features they find too complex. When adding features, prefer simpler approaches and check with user before adding complexity.
- Data should persist automatically in the project — user does not want to rely on manual file export to save data.
- Q&A-first approach — user repeatedly requests: ask one question at a time, follow up until 95% confident in understanding the real need, then give the final solution. Do not jump to implementation before confirming requirements. User also prefers to see the plan/approach first before any code changes ("先看方案再动手").
- **日报输出双版本格式**: 每次生成日报时必须提供两个版本：(1) 分析版——包含三角度分析（导师/HR/老板）、业务价值评估、改进建议，给用户自己看；(2) 复制版——简洁专业，去掉"业务价值""下一步""问题解决"等标签词，可直接粘贴使用。用户表达能力一般，依赖AI辅助写作。（2026-06-29）
- **AI协作五条核心规则**: (1) 发现方向偏了直接提醒，不要迎合；(2) 站在导师/HR/老板三个角度思考；(3) 有更好方案要说明为什么；(4) 工作没有业务价值要直接指出；(5) 帮助建立运营思维/数据思维/产品思维，而不是只帮完成任务。（2026-06-29）
- **用户画像文件**: 个人画像仓库 `github.com/Zarek-Zhao1112/Zarek-AI-Workspace`，含 ABOUT_ME/CAREER/INTERNSHIP/PROJECT/PROMPTS/WRITING_RULE/KNOWLEDGE/WEEKLY_GOAL/CHANGELOG.md。用户每天喂日报内容给AI，AI分析后更新画像文件（优势/不足/技能/知识）。（2026-06-29）
- **数据安全保护规范（2026-06-30）**: 公司明确销售数据等为隐私数据，不能交给AI分析。AI助手（MiMoCode）必须遵守以下规则：
  - 读取 `.xlsx`、`seller_history/*.json`、`sku_analysis/*.json` 等数据文件前，必须先提醒用户数据会经过AI处理
  - 编写涉及 `requests.post` 到外部API的功能时，必须说明数据流向
  - 卖家分析页面（pages/6_卖家分析.py）100%无AI调用，可放心使用
  - 问题管理页面的聊天记录AI提取和AI回复建议会发送数据到豆包API，需注意敏感信息
  - 详见 `Agent项目立项与架构准备清单.md` 第八章和 `功能清单-AI调用审计.md`
- **先方案后行动（2026-06-30）**: 任何功能开发、代码修改、文件更新前，必须先向用户展示方案（做什么、为什么这样做、有什么替代方案），获得用户确认后再执行。禁止未经确认直接动手。用户决策优先级高于AI判断。
- **卖家分析报告必须加载skill（2026-07-01）**: 每次生成卖家优化建议/分析报告时，必须先加载 `.opencode/skills/analyze-conclusion/SKILL.md`。报告目标是给mentor看，mentor再跟seller沟通执行。报告要问题导向（不是逐SKU罗列），每个问题附"跟seller沟通要点"，建议必须具体到SKU和操作。
- **用户核心需求是增长导向（2026-07-02）**: 用户需要的是"帮卖家卖得更好"的skill，不是只诊断问题。skill要能给出具体的增长建议（定价优化、listing优化、库存规划）。用户说"如果商家的listing做的不好我也可以跟seller说，我需要的skill是能不能让卖家卖的更好"。

## Architecture decisions
_Major design choices with rationale. The "why" matters more than the "what" for future sessions._

- **Directory structure**: `src/core/`, `src/knowledge/`, `src/web/` — modular but flat, no deep nesting
- **Entry point**: Root `app.py` (or `main.py`) → Streamlit Web. `app.py` and `main.py` are identical — both serve as dashboard landing page with sidebar. `src/web/app.py` was removed during multi-page rebuild.
- **Storage**: Excel + JSON files in `data/` directory. No database needed for single-person use.
- **Three-phase optimization plan**: P0 structure (done) → P1 basics (done: config, error handling) → P2 features (SQLite, tests, logging, more data sources)
- **Config centralization**: All paths and API config in `src/config/settings.py`. Load `.env` once there, import elsewhere.
- **Error handling pattern**: Use specific exception types (FileNotFoundError, ValueError, json.JSONDecodeError) instead of bare `except:`.
- **Tab module pattern**: Each tab in `src/web/tabs/` exposes `render(tab)` function. Import chain: config ← utils ← ai/data ← tabs ← app. NOTE: `sellers.py` tab was deleted (2026-06-25) — seller health merged into SKU grading page.
- **Multi-page architecture** (2026-06-25): Abandoned single-page `st.tabs()` model due to systemic white screen crashes. Rebuilt with Streamlit multi-page directory (`pages/`). Each module is an independent page — crash in one does not affect others. Entry: `app.py` / `main.py` (dashboard landing page). Shared modules in `src/` are reused unchanged. Data files untouched. **COMPLETED** — all pages working.
- **Shared sidebar pattern**: `src/web/sidebar.py` exports `render()` function. Each page imports and calls it inside `with st.sidebar:`. Ensures consistent API key configuration without code duplication.
- **Tab module render pattern**: Each page passes `st.container()` to tab module's `render(tab)` function. The `with tab:` block works correctly with `st.container()` — buttons, widgets, and all Streamlit elements render and respond properly. Do NOT use `_FakeTab` (no-op context manager) as it doesn't implement Streamlit container behavior.
- **SKU grading design**: `pages/6_卖家分析.py` (renamed from 8_SKU分级治理 → 8_卖家与SKU分析 → 6_卖家分析) implements SKU grading workflow. SKU extracted from `Item Description` by splitting on `__`. Sales table is base (left join), unmatched SKUs go to separate "异常SKU" sheet. Priority = risk × efficiency × inventory × loss. Disposal suggestions from risk × inventory 2D matrix.
- **Single-seller SKU grading**: SKU分级治理重构为单卖家模式。每次上传一个卖家的数据，系统自动识别卖家ID。3个Tab：SKU总表、卖家健康度对比（vs动态基准+3C行业基准）、历史趋势。
- **Unified storage (2026-07-01)**: `seller_history/` and `sku_analysis/` merged into single `sku_analysis/` directory. Seller summary (健康度评分/等级/GMV/RMA% etc.) stored as `seller_summary` metadata inside each SKU batch JSON. `seller_history/` directory deprecated — old files kept for backward compat but no longer written to. `load_seller_history()` reads from sku_analysis first, falls back to old files.
- **Dynamic benchmark design**: 卖家健康度基准=内部数据统计+3C行业基准。权重动态调整：<10个卖家行业60%+内部40%，10-20个行业30%+内部70%，>20个行业10%+内部90%。行业基准值来自3C/消费电子跨境电商公开数据。
- **Global UI design system** (2026-06-25): 所有CSS样式集中到`src/web/styles.py`。新增页面只需`inject_global_css()`+`render_section_header(title, subtitle)`即可自动应用统一视觉风格。主题配置在`.streamlit/config.toml`。
- **Valorant UI redesign (COMPLETED)**: Dark bg (#0F1923) + warm white text (#ECE8E1) + red accent (#FF4655). Config: `.streamlit/config.toml` + full CSS rewrite in `src/web/styles.py`. All pages call `inject_global_css()`. Rajdhani font.
- **`src/core/` deleted (2026-06-25)**: Was CLI-mode dead code. wechat_agent.py, lead_scraper.py, followup_manager.py — all superseded by web tab modules.
- **`src/utils/` deleted (2026-06-25)**: Was empty directory.
- **`main.py` deleted (2026-06-25)**: Was duplicate of app.py.
- **`tests/` deleted (2026-06-25)**: Was one-off API debug scripts, not a real test suite.
- **`prompts/` deleted (2026-06-25)**: Was outdated constitution.md referencing old CLI architecture.
- **Config consolidation (2026-06-25)**: Merged `src/web/config.py` into `src/config/settings.py`. All constants (EMAIL_PATTERN, RMA_RULES, GRADE_RULES, NEWEGG_PITCHES, INDUSTRY_BENCHMARKS, etc.) now in settings.py. `src/web/config.py` kept as compatibility shim (`from src.config.settings import *`). Removed: SELLERS_PATH, FOLLOWUPS_PATH, REQUIRED_COLUMNS, WEIGHTS.
- **data.py dead code removed (2026-06-25)**: Deleted load_sellers(), save_sellers(), calculate_health_score_v2() (~120 lines). data.py now: init_excel + seller history JSON + dynamic benchmarks only.
- **Dashboard followups removed (2026-06-25)**: FOLLOWUPS_PATH deleted from settings.py. dashboard.py right column refactored from followup analysis to email analysis. Funnel updated to Valorant theme colors.
- **`seller_analysis.py` module split (2026-06-29)**: Extracted all pure calculation functions from `pages/6_卖家分析.py` into `src/web/seller_analysis.py`. Page file reduced 1859→1151 lines(-24%). Module contains: text parsing, numerical calculations, grade/level logic, inventory suggestions, file processing, merge logic, seller health scoring. Constants (CATEGORY_MAP, BRAND_KEYWORDS, etc.) also moved. Page file now imports from module and contains only UI rendering. Rationale: separation of concerns, reusability, testability.

## Discovered durable knowledge
_Cross-task facts that survive across sessions. Promoted from session checkpoints' §7 when proven durable._

- **公司隐私政策（2026-06-30）**: 销售数据等为隐私数据，不能交给AI分析。已创建 `功能清单-AI调用审计.md` 文档，列出每个功能的AI调用状态。
- **AI调用分布审计（2026-06-30）**:
  - 🟢 无AI（数据安全）：运营总览、商家通讯录、卖家分析（全部功能）
  - 🟡 有AI（发送公开信息）：品牌线索（品牌官网内容）、招商管理（品牌公开信息）
  - 🔴 敏感AI（发送聊天记录）：问题管理（聊天记录提取、AI回复建议）
  - 卖家分析页面（pages/6_卖家分析.py）100%无AI调用，所有GMV/RMA%/毛利/SKU数据本地处理
- **健康度评分公式（v2.0 - 与行业基准对齐）**: GMV线性($50K=30分) + 毛利线性($10K=25分) + RMA%(≤2%得20分,≤5%得16分,≤8%得12分,≤15%得8分,≤25%得4分) + 销量(≥50件10分) + SKU数(≥20个10分) + 毛利率(≥10%得5分) = 满分100。等级: A≥75 / B≥60 / C≥45 / D<45。评分在 `src/web/seller_analysis.py:calc_seller_health_score()` 中。（2026-07-13更新：GMV阈值从$100K调整为$50K，RMA%阈值从≤0.5%调整为≤2%，与行业基准对齐）
- **动态基准权重**: <10卖家 行业60%+内部40%；10-20卖家 行业30%+内部70%；>20卖家 行业10%+内部90%。20+卖家时基准90%来自内部数据。
- **Excel导出函数位置**: `src/web/utils.py` 中 `export_seller_history_excel()` (数据+趋势折线图)、`export_sku_history_excel()` (数据+5个图表)、`export_all_sellers_pano()` (80个卖家全景报表，4个可视化Sheet)。
- See MEMORY-早期技术约定.md (19 entries) — Streamlit conventions, Python patterns, Excel encoding, early architecture notes
- **doubao API prompt optimization**: Shorter, more structured prompts with explicit JSON format produce faster responses. Verbose natural-language prompts cause timeouts. `response_format: {"type": "json_object"}` may be removed without breaking JSON output when the prompt explicitly requests JSON.
- **Input length for AI calls**: Chat records >4000 chars cause `RemoteDisconnected` connection resets from the doubao API. Truncate to 4000 chars with suffix "(聊天记录已截断)".
- **Newegg BI销售表Date Period提取**: 标签 `**Date Period:` 在列0，日期值在列1。需拼接整行文本后用正则 `\d{4}/\d{2}/\d{2}` 提取。标签和值跨单元格，不能逐cell检查。
- **历史记录日期语义**: 用户要求历史记录的日期列显示"数据覆盖周期"（如 `2026/05/23 - 2026/06/23`）而非分析执行时间。
- **SKU明细持久化**: `data.py` `SKU_ANALYSIS_DIR = data/sku_analysis` + `save_sku_analysis(seller_id, date_period, date_readable, matched_df, seller_summary=None)` / `load_sku_analysis_list()` / `load_sku_analysis_batch()` / `delete_sku_analysis_batch(seller_id, date_period)` / `delete_sku_analysis_seller(seller_id)`。文件名 `{date_period}.json`，含 seller_id, date_period, date_readable, total_skus, **seller_summary**（卖家汇总数据）, records。seller_summary 从 calc_seller_health_from_sku() 结果中提取。此为唯一存储，seller_history/已废弃。
- **卖家历史防重**: 原 `save_seller_history()` 写入前先移除同日期记录（已废弃）。新方案：`save_sku_analysis()` 写入时以 `{date_period}.json` 为文件名，同日期自动覆盖。页面用 `st.session_state` 标记防Streamlit rerun重复保存。
- **Excel带图表导出**: `utils.py` 新增 `export_seller_history_excel()` (数据+趋势折线图) 和 `export_sku_history_excel()` (数据+5个图表:风险等级饼图、品类销售柱状图、库存深度柱状图、效能等级柱状图)。使用openpyxl生成。
- **Plotly chart UI pattern for Valorant theme**: `DARK_LAYOUT` dict (paper_bgcolor transparent, plot_bgcolor #1A2634@0.6, Rajdhani font, #ECE8E1 text) + `AXIS_STYLE` dict (grid #2C3E50@0.5) + `dark_title(text)` helper + `DEFAULT_LEGEND` dict. Do NOT include `title`/`xaxis`/`yaxis`/`legend` in DARK_LAYOUT — use `**DARK_LAYOUT, title=dark_title(...)` pattern. Grade colors: A=#00D97E, B=#00B4D8, C=#FFB800, D=#FF4655. Defined in `pages/6_卖家分析.py`.
- **Plotly layout font/bgcolor pitfalls**: `DARK_LAYOUT` contains `font` dict — passing `**DARK_LAYOUT` to `update_layout()` conflicts with plotly's default `font` parameter. Pie charts don't support `hoverlabel.bgcolor`. Fix: pie charts use separate layout without font/hoverlabel; bar/scatter charts use full DARK_LAYOUT. (2026-07-01)
- **Plotly AXIS_STYLE gridcolor invalid for layout**: `gridcolor` and `zerolinecolor` are axis properties (xaxis/yaxis), NOT layout properties. Cannot use `fig.update_layout(**AXIS_STYLE)`. Must use `fig.update_xaxes(gridcolor=...)` and `fig.update_yaxes(gridcolor=..., zerolinecolor=...)` separately. (2026-07-01)
- **页面重构模式**: 重复UI代码提取为 `render_xxx()` 可复用函数。页面文件从1272→965行(-24%)。5个函数: `render_health_metrics()`(3x重复→1x)、`render_benchmark_comparison()`(3x→1x)、`render_industry_benchmarks()`(3x→1x)、`render_history_trend()`(2x→1x)、`render_summary_stats()`(3x→1x)。(2026-07-01)
- **Seller overview chart layout**: 3-row pattern for 49 sellers: Row1=pie+KPI cards, Row2=scatter+GMV bar, Row3=full-width dot plot+Top10 compact list with badges. Each row ~400px height for consistency. Bar charts fail with 49+ sellers (too tall). Top10 uses HTML compact list+badge style instead of dataframe.
- **Page UI beautification pattern**: KPI cards at top (gradient bg + colored left border + count/percent) + styled filter results (dark card) + colored status/type badges. Applied to: brand leads library (leads.py), operations notes (issues.py). Use `st.markdown(unsafe_allow_html=True)` for custom HTML components.
- **Dynamic benchmark weights confirmed**: seller<5: industry 60%+internal 40%; 5-20: industry 30%+internal 70%; >20: industry 10%+internal 90%. With 49 sellers, benchmarks are 90% internal data.
- **80 seller IDs** (updated from 78): IDs in DB as of 2026-06-30: A4RE, A9U6, AA3N, ACN5, ACP1, ADDZ, AE6G, AEVH, AKUY, AP1Z, AWKT, AYB7, AZUE, B0VT, B1N8, B1N9, B86X, BE6E, BKCF, BKSW, BM9S, BMNX, BNUR, BPBA, BSK6, BTK0, BUPM, BVER, BW2B, BW5V, BWNT, BWYX, BX22, BXUX, BZBE, BZDB, BZSW, BZSX, BZTS, BZTT, C00D, C00E, C01C, C04J, C04K, C0S0, C0U0, C0UB, C11Y, C12W, C2RB, C3D9, C3U3, C3U4, C45N, C4E9, C4SP, C4WS, C545, C55D, C5R2, C668, C68R, C68Z, C6JE, C6KU, C716, C74C, V06X, V137, VMBV, VBSN, VE6Z, VFM9, VG8G, VMN9, VNCN, VRD4, VS4A, VT4H.
- **Batch import architecture**: In `pages/6_卖家分析.py`, batch import section includes: (1) dual file uploaders (sales + inventory), (2) seller ID extraction from SKU prefix, (3) inventory merging + per-seller processing, (4) progress display + error reporting. Must be placed AFTER all function definitions. Uses `st.rerun()` at end to refresh page. Key functions called: `process_sales_file()`, `merge_and_generate()`, `calc_seller_health_from_sku()`, `save_sku_analysis(seller_id, date_period, date_readable, matched, seller_summary=health_record)`. `save_seller_history()` is no longer called from the page.
- **计算说明Sheet内容**: `export_seller_history_excel()` 新增"计算说明"sheet，含：评分公式（GMV线性$50K=30分+毛利线性$10K=25分+RMA% 20分≤2%+销量 10分≥50件+SKU数 10分≥20个+毛利率 5分≥10%=100）、等级划分（A≥75/B≥60/C≥45/D<45）、行业基准（3C/消费电子RMA%/毛利率/月GMV/SKU动销率/库存周转）、混合基准权重。（2026-07-15更新：GMV阈值$100K→$50K，RMA%阈值≤0.5%→≤2%）
- **export_sku_excel (2026-07-01)**: `src/web/utils.py` 新增 `export_sku_excel()` — SKU分级治理总表专用导出，第一个sheet为"数值说明"（字段来源、计算公式、分级规则、处置矩阵），第二个sheet为数据。原始 `export_excel()` 保留不动，供 contacts/leads/issues 等模块使用。
- **SKU分析删除功能（2026-07-01）**: `data.py` 新增 `delete_sku_analysis_batch(seller_id, date_period)` 和 `delete_sku_analysis_seller(seller_id)`。页面"历史卖家记录"和"SKU明细历史导出"两个区域均已加入删除UI（单条+清空）。删除操作同时清理旧 seller_history 文件。
- **SellingPrice叠加修复（2026-07-01）**: `process_inventory_file()` groupby时，BSD表同一SKU出现多行（不同仓库位置）会导致数字列被sum。修复：仅 `Inventory` 用 `"sum"`，其他数字列（SellingPrice等）用 `"first"`。之前的4199.97是1499×3被叠加的结果。**此bug存在于两处**：`process_inventory_file()` 和 batch import inventory合并（`pages/6_卖家分析.py:518-527`），均已修复。
- **日均销量计算（已修复）**: `calc_daily_sales(qty_sold, period_days=20)` 现在接受实际天数参数。`merge_and_generate()` 透传 `period_days`。页面新增 `calc_period_days(date_period)` 从 "20260524-20260624" 解析实际天数。默认fallback 20天。
- **reorder_sku_columns函数（2026-07-01）**: `pages/6_卖家分析.py` 新增列重排函数，将整改优先级得分、RMA%、退货件数、退货损失金额移到GMV之前。注意：不能先remove再if-in检查来re-insert，会导致列消失。正确做法：先收集有效列，统一remove，统一insert。
- **全量导出结构（已完成）**: `export_all_sellers_pano()` in `src/web/utils.py` 生成4个可视化Sheet：(1)计算说明 (2)卖家全景概览（饼图+GMV柱状图+Top10低分卖家） (3)指标分布分析（GMV/RMA%/毛利率分布，各含柱状图） (4)卖家风险矩阵（GMV vs RMA%散点图+风险解读）。不含80个卖家各自详情。支持按批次筛选导出，文件名自动包含日期范围。
- **analyze-conclusion skill（2026-06-30）**: 分析结论skill，规范卖家/商品分析报告格式。核心要求：先数据后结论、每个建议至少3种原因（数据/业务/竞品）、标注数据来源、区分事实和假设。文件位置：`.opencode/skills/analyze-conclusion/SKILL.md`。首个应用：A4RE Top20商品优化建议报告（严格版）。返回类型 `tuple[bytes, str]`（excel数据, 日期范围）。页面支持按批次筛选导出，文件名自动包含日期范围（如 `卖家健康度全景报表_20260524-20260624.xlsx`）。
- **卖家分析筛选条件（实操）**: 分析价值高的卖家应满足：SKU≥5个、GMV $100-$5000、RMA%>5%、C/D级。太小没代表性，太大难分析，A/B级优化空间小。分析流程：报表选卖家→Newegg前台看店铺→回报表看数据→记录结论。
- **卖家数据统计（2026-07-16）**: 总卖家77个，分组24个，多账号公司11个，无SellerName 40个。站点分布：未标记48个、B2C 16个、CA 8个、B2B 5个。等级分布：A级13个、B级4个、C级7个、D级53个。
- **多Agent分析工具**: seller-analysis-agent支持单个卖家分析和按SellerName分组分析。使用方法：`python .opencode/skills/seller-analysis-agent/run_analysis.py <seller_id>` 或 `--group "公司名"`。
- **评分公式v2.0**: GMV($50K=30分) + 毛利($10K=25分) + RMA%(≤2%=20分) + 销量(≥50件10分) + SKU数(≥20个10分) + 毛利率(≥10%得5分)。（2026-07-15更新，与行业基准对齐）
- **多账号公司（2026-07-16）**: SenyTech Global(3账号)、roboshine(2账号)、TERRAMASTER(2账号)、NUC PC Store(3账号)、Partaker(2账号)、HIGOLEPC(3账号)、Corn Electronics(2账号)、SONGCAN(2账号)、ELEC SPACE(2账号)、mailuna(3账号)。共11个多账号公司。
- **站点分布（2026-07-16）**: B2C 16个、CA 8个、B2B 5个、未标记 48个。需要从BSD导出确认SellerName的有40个。
- **周报框架**: 8个分析维度（业绩、风险、库存、SKU动态、价格、效率、总结）。用seller-analysis-agent生成，命令：`python .opencode/skills/seller-analysis-agent/run_analysis.py <seller_id>`。
- **B2B Deal Portal提报**: 已完成Flashforge促销提报。需要产品在其他平台有销售记录，每次最多3个产品。
- **ACN5分析（2026-07-16）**: TERRAMASTER OFFICIAL，CA站点，GMV $13,352，健康度52分（C级），20个SKU。核心SKU是TERRAMASTER NAS存储设备。月环比GMV增长449.4%。主要问题：14个SKU需要关注（库存积压），3个SKU零库存。建议：优化核心SKU的listing，评估低动销SKU是否保留。
- **CA站点卖家（2026-07-16）**: 共8个，总GMV $24,965。问题分析：C5R2(4个问题)、AE6G(3个问题)、B1N9(3个问题)、BUPM(3个问题)、C00E(3个问题)、BMNX(2个问题)、BZSX(2个问题)、ACN5(1个问题：3个零库存)。主要问题：健康度低、动销率低、GMV低。整体建议：CA站点需要更多支持，可考虑推广CA站点优势和举办促销活动。
- **ACN5 SKU列表（2026-07-16）**: TERRAMASTER品牌，CA站点，20个SKU。核心SKU：1.D4-320 NAS($2,751)、2.F6-424 Max NAS($2,408)、3.D9-320 NAS($1,285)、4.F2-425 NAS($928)。问题SKU：5-9号为低动销NAS产品。整体评估：RMA%=0%优秀，GMV月环比+449%增长强劲，主要问题是SKU动销率低（71%低动销）和库存管理。
- **周报模板（2026-07-16）**: 8个维度：业绩（GMV/销量/客单价）、风险（RMA%/退货）、库存（断货/积压）、SKU动态（新上架/下架/核心SKU）、价格（售价变动/定价异常）、效率（动销率/毛利率）、总结（关键发现/需要关注/下周建议）。用seller-analysis-agent生成。
- **各站点GMV数据（2026-07-16会议）**: 所有AM总计：B2C占92%($1.9M/周)，B2B占4%($88K/周，客单价$508)，CA占4%($77K/周，客单价$129)。B2B客单价是B2C的4.3倍，是最有价值的渠道。注意：这是所有AM的数据，不是单个seller的数据。用户的77个seller只是其中一部分，CA卖家占CA总盘约31%（$24K/$77K）。建议重点发展B2B渠道（客单价最高）和继续扩大CA份额。
- **有SellerName的卖家站点分布（2026-07-16）**: HIGOLEPC(B2B+B2C+CA)、mailuna(B2B+B2C+CA)、NUC PC Store(B2B+CA+未标记)、SenyTech Global(B2B+未标记)、Corn Electronics(B2B+未标记)、TERRAMASTER(CA+未标记)、Partaker(CA+未标记)、SONGCAN(CA+未标记)、ELEC SPACE(B2C+CA)。共23个有名字的卖家，11个多账号公司。待确认站点：ALCPOK、Frentosa、Suevery、Yeston、ZYNEEX、roboshine。
- **周度卖家分析（2026-07-16）**: 用seller-analysis-agent生成，支持单个卖家分析和按SellerName分组分析。命令：`python .opencode/skills/seller-analysis-agent/run_analysis.py <seller_id>` 或 `--group "公司名"`。周报8个维度：业绩、风险、库存、SKU动态、价格、效率、总结。
- **站点信息更新（2026-07-16）**: 已更新47个JSON文件的Platform字段。B2C: A4RE, BM9S, AA3N, ACP1, C00D, B1N8, AZUE, C68Z, C4WS, AYB7, BX22, C55D, BTK0。B2B: V0X6, V137, VMUM, VBHE, VE5W, VDZH, VHD9, VBSN, VG8G, VT2S, VS4A。CA: ADDZ, B3EJ。
- **Newegg Seller Academy**: https://sellerportal.newegg.com/selleracademy/zh-hans/ - 中文版卖家学院，包含促销、商品、SBN管理等模块。可用于了解B2B Deal Portal提交流程。
- **问题管理页面优化需求（2026-07-16）**: 用户想优化问题管理页面的AI回复建议模块，需要输入公司资料来改进AI回复质量。当前AI回复使用豆包(ARK) API，需要更好的prompt和公司背景信息。优化方向：增强系统提示（公司背景、产品信息、政策规则、沟通风格）。建议方案：在系统提示中加入公司信息，AI能立即使用。用户提供了Newegg Seller Academy网址作为参考。
- **今日工作总结（2026-07-16）**: 完成B2B Deal Portal促销提报；根据会议总结制定行动方向；更新站点数据（47个JSON文件）；分析ACN5卖家（CA站点）；分析CA站点8个卖家问题；更新评分公式v2.0；修复Streamlit显示bug（hist_list[-1]→hist_list[0]）；创建seller-analysis-agent多Agent分析工具；完成经销商招募skill和话术库；设计周度分析框架；用户提出优化问题管理页面AI回复模块需求，需要公司资料改进AI回复质量；用户分享Newegg Seller Academy网址，希望AI学习其中的指导内容来优化回复。
- **新蛋业务介绍PDF内容**: 包含Newegg发展历程（2001年成立，2021年纳斯达克上市）、客户画像（4700万用户，70%男性，36岁，$7.5万+收入）、热销品类（Components、Computer Systems、Home & Outdoor、Gamers）。可用于AI回复时强调平台优势。
- **CA站点卖家排名（2026-07-16）**: 10个CA卖家，GMV倒序：ADDZ($17,526 C级)、ACN5($13,352 C级)、C3U4($10,937 C级)、BMNX($9,574 D级)、C5R2($638 D级)、AE6G($496 D级)、C00E($254 D级)、BZSX($239 D级)、BUPM($230 D级)、B1N9($102 D级)。总计GMV $61,534。主要问题：健康度低、动销率低、GMV低。优化建议：ADDZ(C级，GMV最高，需要优化SKU结构)、ACN5(C级，GMV增长449%，需要扩大产品线)、BMNX(D级，NUC PC Store，需要优化listing)。
- **BMNX健康度低原因（2026-07-16）**: GMV $9,574（满分需$50K，得5.7/30）、毛利 $916（满分需$10K，得2.3/25）、销量 10件（满分需50件，得4/10）、SKU数 9个（满分需20个，得4/10）。RMA% 0%得满分20分，毛利率9.6%得4/5分。总分40分。主要问题是规模太小（GMV、毛利、销量、SKU数都低）。
- **健康度评分按站点细化需求（2026-07-16）**: 用户提出是否需要对CA站点和B2C站点有不同的健康度评分标准。因为GMV比例差异大（B2C 92% vs CA 4%），统一标准可能对小站点不公平。建议方案1：按站点比例调整GMV阈值（B2C $50K, B2B $5K, CA $5K）。但用户决定先不做，保持现状。
- **今日实习内容（2026-07-16）**: 1.完成B2B Deal Portal促销提报；2.根据会议总结制定行动方向（CA站点、B2B开通、闪铸促销、机械革命）；3.更新站点数据（47个JSON）；4.分析ACN5和BMNX卖家；5.修复Streamlit显示bug；6.创建seller-analysis-agent多Agent工具；7.完成经销商招募skill；8.讨论健康度评分是否需要按站点细化（暂不修改）。
- **BMNX分析（2026-07-16）**: NUC PC Store的CA站账号，GMV $9,574，健康度40分（D级），9个SKU。核心SKU：ASUS NUC 13 Pro（$2,753）。8个SKU需要关注（库存积压）。GMV月环比+122.4%，增长势头良好。建议：优化核心SKU listing，评估低动销SKU是否保留。报告已保存到reports/BMNX_运营报告_20260716.md。
- **今日工作总结（2026-07-16）**: 完成B2B Deal Portal促销提报；根据会议总结制定行动方向；更新站点数据（47个JSON文件）；分析ACN5卖家（CA站点）；分析CA站点8个卖家问题；更新评分公式v2.0；修复Streamlit显示bug（hist_list[-1]→hist_list[0]）；创建seller-analysis-agent多Agent分析工具；完成经销商招募skill和话术库；设计周度分析框架；用户提出优化问题管理页面AI回复模块需求；分析BMNX卖家（NUC PC Store CA站，GMV $9,574，D级，月环比+122.4%）。
- **用户提供的站点信息（2026-07-16）**: A4RE:B2C, ADDZ:CA, BM9S:B2C, AA3N:B2C, V0X6:B2B, V137:B2B, ACP1:B2C, C00D:B2C, VMUM:B2B, B1N8:B2C, VBHE:B2B, VE5W:B2B, VDZH:B2B, VHD9:B2B, AZUE:B2C, B3EJ:CA, VBSN:B2B, BTK0:B2C, VG8G:B2B, C68Z:B2C, VT2S:B2B, C4WS:B2C, VS4A:B2B, AYB7:B2C, BX22:B2C, C55D:B2C, VSA6:B2B。
- **各站点GMV数据（2026-07-16会议）**: B2C占92%($1.9M/周)，B2B占4%($88K/周，客单价$508)，CA占4%($77K/周，客单价$129)。B2B客单价是B2C的4.3倍，是最有价值的渠道。CA客单价比B2B高9%，有增长空间。
- **卖家角色关系（2026-07-01）**: 用户(intern) → mentor(导师，帮seller运营) → seller(平台卖家)。分析报告给mentor看，mentor再跟seller沟通执行。报告格式必须问题导向+沟通话术。
- **Newegg时区（2026-07-01）**: 平台按美国太平洋时间(PT)计算。周日-周六为一周，换算北京时间加15-16小时(夏令时15h/冬令时16h)。实际操作直接用BI导出的Date Period即可，不用手动换算。
- **周数据vs月数据特征差异（2026-07-01）**: A4RE周数据(6/21-6/27, 201 SKUs) vs 月数据(5/24-6/24, 480 SKUs)。周数据无退货、SKU数少、GMV集中度高(48.7%)、全部低动销。月数据有退货、SKU数多、GMV分散(30.3%)、有核心主力商品。周数据适合看趋势变化，月数据适合看整体问题。
- **用户个人画像**: Zarek，普通本科电子商务，Newegg Marketplace运营实习生，负责80个Seller。目标：AI Application Developer（AI+跨境电商+数据分析）。GitHub画像仓库：`github.com/Zarek-Zhao1112/Zarek-AI-Workspace`。57项优势（核心：数据分析/系统设计/产品思维），不足：英文一般、表达能力一般（依赖AI辅助写作）、Marketplace经验不足、业务视角待加强。
- **AI读取文件=数据经过AI**: AI助手读取的文件内容会进入对话上下文，发送到AI模型处理。用户已接受，但要求建立规范（详见Agent项目立项与架构准备清单.md第八章）。
- **公司数据安全政策（2026-07-01）**: 公司明确销售数据等为隐私数据，不能交给AI分析。用户是实习生，无AI权限。系统内pages/6_卖家分析.py 100%无AI调用是安全的。用户用AI分析导出的JSON数据属于灰色地带，需注意。
- **AM日常工作（2026-07-01）**: (1) PO控库存——通过采购订单控制库存深度 (2) 观察调价格——监控竞品定价 (3) BD抓新品——发现潜力新品。分析报告要围绕这三点展开。
- **退货必须看绝对量（2026-07-01）**: mentor明确要求不能只看RMA%比率，要看退货件数和退货金额。RMA%=100%但只退1件 vs RMA%=5%但退5件，后者影响更大。报告模板已更新。
- See MEMORY-legacy.md (10 entries) — Historical/completed items: feature roadmap, CLI dead code, completed cleanup, architectural context for single-page crash pattern
- See MEMORY-implementation-details.md (30 entries) — Streamlit patterns, Python conventions, stable paths, historical items, implementation patterns
- **商品信息提取必须用merged而非sales_df（2026-07-01）**: `seller_analysis.py` 中 extract_condition/extract_category/extract_brand 原先用 `sales_df[desc_col_name]`，改为 `merged[desc_col_name]`。虽然当前1:1 merge不会出错，但如果BSD有重复SKU导致merge膨胀，sales_df按原始index赋值会给merged产生错误的对齐。用merged直接提取更安全。
- **parse_date_any共享函数（2026-07-01）**: `pages/6_卖家分析.py` 中 `parse_date` 函数原先在rtab3和tab3重复定义。提取为模块级 `parse_date_any(d)` 共享函数，支持 "2026/05/24" 格式和 `pd.to_datetime` fallback。
- **历史回看保存需传seller_summary（2026-07-01）**: 历史回看区"保存到项目"按钮原先未传 `seller_summary`，导致重新保存会丢失卖家汇总数据。修复：从 batch 数据中读取 `batch.get("seller_summary", {})` 并传给 `save_sku_analysis()`。
- **已保存数据的评分更新（2026-07-01）**: 修改健康度评分公式后，已保存在 `data/sku_analysis/` 中的JSON文件不会自动更新。需要手动重新计算并写入。方法：从records中提取GMV/RMA%/毛利/销量/SKU数，调用新公式计算，更新seller_summary字段。A4RE三个月评分从88.6/88.6/88.6更新为81.9/78.4/78.8。
- **删除单卖家上传功能（2026-07-01）**: 批量导入已存在，单个上传冗余。`pages/6_卖家分析.py` 删除 lines 838-972（文件上传UI、处理逻辑、结果Tab、使用说明）。页面从972→836行(-14%)。保留：时间选择器、卖家全景概览、批量导入、一键导出、历史记录、SKU明细历史、历史回看。
- **卖家全景概览已改为Plotly图表（2026-07-02）**: 4个表格全部替换为Plotly图表：(1)各等级核心指标对比分组柱状图 (2)Top15卖家GMV柱状+毛利折线图 (3)风险卖家气泡散点图（RMA% vs GMV，气泡大小=健康度） (4)效能四象限散点图（GMV vs RMA%，带基准线）。用户明确要求"做成图表，不是表格"。
- **退货件数截断bug已修复（2026-07-02）**: `calc_return_qty` 旧公式 `int(round(q/(1-r)-q))` 对小qty（0-2）和低RMA%截断为0。修复为 `math.ceil(q*r/(1-r))`。公式等价：`q/(1-r)-q` = `q*r/(1-r)`。
- **退货损失金额公式**: `calc_return_loss(gmv, rma_pct) = |GMV| × |RMA%|`，按单个SKU维度计算。单SKU GMV小则结果自然小（如$50×10%=$5），数学上正确。
- **品类分类优先级（2026-07-02）**: SubcategoryName > 型号关键词(VGA/RTX/RX等) > CATEGORY_ORDER匹配。SKU前缀中的"CH"会误匹配，需跳过`|`前的前缀。`extract_category(item_desc, subcategory_name=None)` 现支持SubcategoryName参数。
- **商品成色优先级（2026-07-02）**: ItemCondition列 > SKU描述末尾"R"后缀。`extract_condition(item_desc, item_condition=None)` 优先用原始ItemCondition列判断。
- **优先级评分归一化（2026-07-02）**: 各维度需归一化到0-100范围再加权。旧公式被客单价($300-1500)主导。新公式：退货损失(40%, $100为满分) + 毛利侵蚀率(30%) + RMA严重度(20%) + 动销逆向(10%, 10件为满分)。
- **A4RE RMA%低是正常值**: RMA%来自Newegg BI系统，A4RE整体-0.35%，单SKU 0.7-1.37%，退货率本身很低，损失金额小是数学正确。
- **RMA%计算必须排除退货记录（2026-07-02）**: 退货记录(GMV<0)的RMA%=100%会拉高卖家汇总RMA%。`calc_seller_health_from_sku` 必须先 `matched_df[matched_df[gmv_col] >= 0]` 过滤，再计算RMA%均值。同理，页面中任何对RMA%的聚合统计都需排除退货记录。
- **优先级分级用绝对值阈值（2026-07-02）**: 旧逻辑用百分位 `rank >= 90` → 极高，导致分布永远偏斜。改为绝对值：>=40极高，>=25高，>=10中，<10低。跨卖家可比。
- **numpy类型JSON序列化（2026-07-02）**: pandas groupby/mean返回numpy.int64/float64，json.dump报TypeError。写JSON前必须用 `float()`, `int()` 转换所有值。迁移脚本已修复。
- **页面冗余清理模式（2026-07-02）**: `pages/6_卖家分析.py` 从990→780行(-21%)。清理内容：(1)合并parse_date_any+parse_record_date (2)提取extract_seller_id_from_file工具函数 (3)新增filter_by_time通用过滤 (4)合并"历史卖家记录"和"SKU明细历史导出"两个重叠模块 (5)统一Plotly配置 (6)删除重复import和目录读取。
- **load_sku_analysis_list错误保护（2026-07-02）**: `src/web/data.py` 中 `load_sku_analysis_list`、`load_seller_history`、`load_all_seller_history` 三处 `json.load(f)` 均加了 `try/except json.JSONDecodeError: continue`，跳过损坏JSON文件避免Streamlit崩溃。
- **批量导入错误持久化（2026-07-02）**: `pages/6_卖家分析.py` 批量导入用 `error_messages` 列表收集错误，导入完成后在 `st.expander("查看错误详情")` 中持久显示，避免 `st.error()` 闪现。
- **数值说明必须跟公式同步（2026-07-02）**: 修改退货件数/整改优先级等计算公式后，必须同步更新 `src/web/utils.py` 中 `export_sku_excel()` 的数值说明sheet，否则导出Excel说明与实际不符。
- **GitHub Claude Code skills生态（2026-07-02）**: `alirezarezvani/claude-skills`（19.6k stars，337个skills）是最大开源skill库，含marketing/business-operations/commercial/product等domain。支持Claude Code/Codex/Gemini CLI/Cursor等13个AI工具。
- **电商专用skill库（2026-07-02）**: `nexscope-ai/eCommerce-Skills`（309 stars，157+ skills）专门做电商，含competitor-price-analysis、ecommerce-growth-strategy、product-review-analysis等。比通用skill库更贴合Newegg卖家运营场景。
- **A4RE运营优化报告（2026-07-02）**: 生成 `A4RE_SKU优化建议_4-6月.md`，含4/5/6月Top20 GMV SKU明细、跨月分析、问题识别、优化建议。4个SKU连续3月Top20：RTX3090、CornE鼠标垫、CornE工具、RTX3060。
- **报告格式规则（2026-07-02）**: 生成运营报告时，"与导师沟通要点"部分不要写入报告文件，只在对话界面单独发给用户。报告文件保持干净格式，可直接发给导师。报告文件放在 `reports/` 文件夹。
