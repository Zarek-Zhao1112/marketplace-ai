# 跨境电商BD智能助手 - 项目清单

> 单人使用的内部效率工具，Streamlit Web 界面

---

## 一、项目定位

| 项 | 内容 |
|---|---|
| 核心问题 | 跨境电商BD日常运营：企微问题整理、线索搜集、智能回复、跟进管理、卖家分析 |
| 用户 | 1人（自己） |
| 形态 | Streamlit Web Dashboard（多页面架构） |
| 存储 | Excel/JSON文件（data目录） |
| UI风格 | Valorant深色主题（深蓝黑背景 + 暖白文字 + 红色强调） |

---

## 二、功能模块状态

| 模块 | 页面文件 | 渲染函数 | 状态 | 说明 |
|------|----------|----------|------|------|
| 运营总览 | app.py | tabs/dashboard.py | ✅ 可用 | 关键指标、趋势分析、转化漏斗 |
| 问题管理 | pages/2_问题管理.py | tabs/issues.py | ✅ 可用 | 聊天记录自动提取、主笔记库编辑+KPI统计+筛选、经验库、AI回复 |
| 品牌线索 | pages/3_品牌线索.py | tabs/leads.py | ✅ 可用 | 品牌信息抓取、线索管理+KPI统计+筛选、AI邮件生成 |
| 商家通讯录 | pages/4_商家通讯录.py | tabs/contacts.py | ✅ 可用 | Hunter.io邮箱搜索、官网爬取、LinkedIn |
| 招商管理 | pages/5_招商管理.py | tabs/emails.py | ✅ 可用 | AI生成邮件、发送记录、邮件模板 |
| 卖家分析 | pages/6_卖家分析.py | (独立渲染) | ✅ 可用 | 卖家全景概览、分级治理、时间筛选、历史回看、数据保存、Excel导出(含图表) |

---

## 三、架构演进

### v6.2 项目命名优化（2026-06-29）

- [x] 统一项目命名：运营总览/问题管理/品牌线索/商家通讯录/招商管理/卖家分析
- [x] 文件重命名：2_问题管理.py/3_品牌线索.py/4_商家通讯录.py/5_招商管理.py/6_卖家分析.py
- [x] 所有页面page_title和h2标题统一

### v6.1 时间筛选 + 冗余清理（2026-06-29）

- [x] 卖家分析：新增「分析周期」时间筛选器（全部/本周/本月/最近30天/自定义日期）
- [x] 卖家分析：时间筛选全局联动（概览、管理平台、历史回看、趋势分析全部跟随变化）
- [x] 项目冗余清理：删除6个__pycache__目录、node_modules/、package.json、package-lock.json
- [x] 项目冗余清理：删除.idea/（PyCharm配置，不再使用）
- [x] 代码清理：移除未使用的render_section_header导入、LEADS_PATH死代码、load_leads()函数

### v6.0 卖家分析增强 + UI优化 + 代码清理（2026-06-26）

- [x] 卖家分析：新增「保存到项目」功能（SKU明细JSON存储）
- [x] 卖家分析：新增「历史回看」区（完整复现首次上传的分析结果）
- [x] 卖家分析：新增页面顶部「卖家全景概览」（5个Plotly深色主题图表）
- [x] 卖家分析：新增Excel导出含图表（卖家健康度趋势 + SKU风险/品类/库存/效能分布图）
- [x] 卖家分析：修复重复保存问题（st.session_state防重入）
- [x] 卖家分析：修复硬编码测试值（68836.14/6168.58改为0）
- [x] 问题管理：新增KPI统计卡片 + 问题类型/处理状态筛选
- [x] 品牌线索：新增KPI统计卡片 + 筛选结果美化
- [x] 全项目冗余代码清理（30处，涉及9个文件）

### v5.2 功能优化（2026-06-25）

- [x] 卖家分析页面标题更名（原"SKU分级治理"）
- [x] 问题管理页面 AI提取区域改为 st.fragment（修复滚动跳顶问题）
- [x] 运营总览移除 followups 引用（文件已删除）

### v5.1 冗余清理（2026-06-25）

- [x] 删除 src/core/ 目录（CLI遗留模块，3个文件）
- [x] 删除 src/utils/ 目录（空文件夹）
- [x] 删除 tests/ 目录（一次性调试脚本）
- [x] 删除 main.py（与app.py重复）
- [x] 删除 prompts/ 目录（未引用的静态文档）
- [x] 删除 data/sellers.xlsx + followups.xlsx（旧数据残留）
- [x] 合并 config.py 到 settings.py（统一配置管理）
- [x] 删除 data.py 中死代码（load_sellers, save_sellers, calculate_health_score_v2）
- [x] SKU页面删除重复常量定义，改用 import

### v5.0 UI风格改造（2026-06-25）

- [x] Valorant深色主题（config.toml + styles.py全量重写）
- [x] 所有页面副标题颜色适配新主题

### v4.0 多页面架构重构（2026-06-25）

- [x] 从单文件Tab架构迁移为Streamlit多页面架构
- [x] 每个功能模块独立页面，崩溃互不影响
- [x] 共享模块提取为 sidebar.py（侧边栏统一管理）
- [x] 聊天记录AI自动提取功能（企微聊天→问题表格）

### 历史优化

- [x] 项目目录重构、拆分大文件、统一配置管理、错误处理优化

---

## 四、项目结构

```
marketplace-ai/
├── pages/                        # 独立页面
│   ├── 2_问题管理.py
│   ├── 3_品牌线索.py
│   ├── 4_商家通讯录.py
│   ├── 5_招商管理.py
│   └── 6_卖家分析.py
├── src/
│   ├── config/
│   │   └── settings.py           # 统一配置（API Key、行业基准、等级规则）
│   ├── knowledge/
│   │   └── experience_library.py # 运营经验库（向量检索+AI回复建议）
│   └── web/
│       ├── sidebar.py            # 侧边栏
│       ├── utils.py              # 工具函数（Excel读写、图表导出）
│       ├── ai.py                 # AI功能（豆包大模型调用）
│       ├── data.py               # 数据处理（卖家/SKU数据存储）
│       ├── config.py             # 常量配置（邮箱、品类等）
│       ├── styles.py             # Valorant风格CSS
│       ├── seller_analysis.py    # 卖家分析计算逻辑
│       └── tabs/
│           ├── dashboard.py      # 运营总览渲染
│           ├── issues.py         # 问题管理渲染
│           ├── leads.py          # 品牌线索渲染
│           ├── contacts.py       # 商家通讯录渲染
│           └── emails.py         # 招商管理渲染
├── data/
│   ├── seller_history/           # 卖家健康度历史（JSON，已废弃，仅保留旧文件）
│   ├── sku_analysis/             # SKU明细分析历史（JSON，唯一存储）
│   ├── competitor_analysis/      # 竞品数据（爬虫抓取）
│   ├── experience.json           # 运营经验库（向量索引）
│   └── *.xlsx                    # 各模块数据文件
├── tests/                        # 测试
│   └── test_calc_return_qty.py
├── .opencode/skills/             # AI技能
│   └── marketplace-analysis/     # 分析助手（含分层分析）
├── docs/                         # 文档
├── app.py                        # 主入口
├── start.bat                     # 启动脚本（端口8502）
├── .streamlit/config.toml        # Streamlit主题
├── requirements.txt
├── .env.example
└── README.md
```

---

## 五、数据存储说明

| 数据 | 存储方式 | 路径 | 写入时机 |
|------|----------|------|----------|
| 卖家健康度历史 | JSON | data/sku_analysis/{seller_id}/{date}.json（含seller_summary） | 批量导入时自动保存 |
| SKU明细分析 | JSON | data/sku_analysis/{seller_id}/{date}.json | 批量导入时自动保存 |
| 运营经验库 | JSON | data/experience.json | 手动点击"重建经验库" |
| 问题管理 | Excel | data/issues.xlsx | 编辑后手动保存 |
| 品牌线索 | Excel | data/brands.xlsx | 编辑后手动保存 |
| 商家通讯录 | Excel | data/contacts.xlsx | 导入/编辑后保存 |
| 邮件记录 | Excel | data/emails.xlsx | 发送后自动保存 |

---

## 六、技术依赖

| 库 | 用途 |
|---|---|
| streamlit | Web界面框架 |
| pandas | 数据处理 |
| plotly | 交互式图表（卖家概览） |
| openpyxl | Excel读写+图表导出 |
| playwright | 网页抓取（JS渲染页面） |
| requests | HTTP请求（API调用、网页抓取） |
| beautifulsoup4 | HTML解析 |
| volcengine-python-sdk | 豆包大模型API |

---

## 七、待优化项

### P0 - 功能增强

- [ ] 运营总览实时更新（定时刷新）

### P1 - 提效功能

- [ ] 批量操作（批量生成邮件）
- [ ] 智能提醒（定时提醒、冷却预警）

### P2 - 数据分析

- [x] 卖家健康度全景报表（4个可视化Sheet：计算说明、卖家概览、指标分布、风险矩阵）
- [x] 一键导出全部卖家功能（支持按批次筛选）
- [x] A4RE Top20商品优化建议报告（严格版，基于analyze-conclusion skill）

---

## 八、数据安全与隐私保护规范

> **本章节为项目宪法级规范，所有AI辅助开发必须遵守**

### 8.1 敏感数据定义

| 数据类型 | 敏感等级 | 存储位置 | 说明 |
|----------|----------|----------|------|
| 卖家GMV、毛利、RMA% | 🔴 高 | `data/seller_history/` | 核心销售数据 |
| SKU销售明细 | 🔴 高 | `data/sku_analysis/` | SKU级别财务数据 |
| 企业微信聊天记录 | 🔴 高 | 用户本地/页面输入 | 含订单、金额、卖家信息 |
| 卖家消息原文 | 🔴 高 | 页面输入 | 可能含具体订单详情 |
| 问题记录（含卖家名称） | 🟡 中 | `data/issues.xlsx` | 运营问题 |
| 联系人邮箱、职位 | 🟡 中 | `data/contacts.xlsx` | 商家联系方式 |
| 品牌跟进记录 | 🟡 中 | `data/brands.xlsx` | 品牌信息 |

### 8.2 页面AI调用清单

| 页面 | AI调用功能 | 发送的数据 | 风险 |
|------|------------|------------|------|
| 运营总览 | 无 | - | ✅ 安全 |
| 问题管理 | 聊天记录AI提取 | 聊天记录原文 | 🔴 高风险 |
| 问题管理 | AI回复建议 | 卖家消息+历史对话 | 🔴 高风险 |
| 品牌线索 | 品牌信息AI分析 | 品牌官网内容 | 🟡 中风险 |
| 商家通讯录 | 无 | - | ✅ 安全 |
| 招商管理 | AI邮件生成 | 品牌公开信息 | 🟡 中风险 |
| **卖家分析** | **无** | **纯本地计算** | ✅ **完全安全** |

### 8.3 AI辅助开发规范（MiMoCode遵守）

**⚠️ 以下规则适用于AI助手在本项目中的所有操作：**

#### 读取文件规范
1. **代码文件（.py/.js/.css）** → 可直接读取，不含业务数据
2. **配置文件（.env/.toml）** → 可读取结构，但不要读取实际API Key值
3. **数据文件（.xlsx/.json）** → ⚠️ **读取前必须提醒用户**，说明：
   - 我要读取哪个文件
   - 读取的目的是什么
   - 数据会经过AI模型处理
4. **卖家历史/SKU分析数据** → 🔴 **原则上不主动读取**，除非用户明确要求

#### 编写功能规范
1. **涉及AI调用的功能** → 必须在代码中添加注释说明数据流向
2. **新功能涉及敏感数据** → 主动提醒用户该功能是否涉及AI调用
3. **导出功能** → 不涉及AI，可自由实现

#### 提醒协议
当以下情况发生时，AI助手必须主动提醒用户：
- 需要读取 `.xlsx` 或 `seller_history/sku_analysis` 下的 `.json` 文件
- 编写涉及 `requests.post` 到外部API的功能
- 用户要求分析或处理销售数据
- 任何可能将敏感数据发送到外部服务的场景

### 8.4 本地数据安全存储

| 数据 | 存储方式 | 备份建议 |
|------|----------|----------|
| 卖家健康度历史 | `data/seller_history/*.json` | 定期备份整个目录 |
| SKU分析历史 | `data/sku_analysis/**/*.json` | 定期备份整个目录 |
| 经验库 | `data/experience.json` | 可从issues.xlsx重建 |
| Excel数据文件 | `data/*.xlsx` | 建议开启版本控制 |

### 8.5 环境变量安全

```env
# .env 文件（已加入.gitignore，不会被提交）
ARK_API_KEY=你的豆包APIKey      # 页面AI功能使用
HUNTER_API_KEY=你的HunterKey    # 邮箱搜索使用
MODEL_ENDPOINT=模型端点ID       # 豆包模型配置

# 安全开关
ENABLE_AI_ANALYSIS=true         # 设为false可禁用所有AI功能
```

---

*文档版本：v7.0*
*更新时间：2026-06-30*
*新增：数据安全与隐私保护规范*
