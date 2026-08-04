# Newegg Marketplace 运营工具集

内部效率工具，用于跨境电商BD日常运营。

## 功能

- 📊 **运营总览**：关键指标概览、趋势分析、转化漏斗
- 📒 **问题管理**：聊天记录自动提取、经验库、AI回复建议、KPI统计+问题类型/状态筛选
- 🔍 **品牌线索**：品牌信息抓取、线索管理、AI邮件生成、KPI统计+类目/状态筛选
- 📧 **商家通讯录**：Hunter.io邮箱搜索、官网爬取、LinkedIn
- 📊 **卖家分析**：卖家全景概览、分级治理、历史回看、数据保存、Excel导出(含图表)、时间筛选
- ✉️ **招商管理**：AI生成邮件、发送记录、邮件模板

## AI功能

- **聊天记录AI提取**：粘贴企业微信聊天记录，AI自动识别问题并结构化
- **AI回复建议**：基于Newegg Seller Academy知识库（17个模块）生成专业回复
- **AI学习闭环**：用户修改回复后可保存到经验库，AI持续学习
- **多模态支持**：支持上传截图，AI结合图片和文本分析问题

## 快速开始

### 1. 安装依赖

```bash
# Windows
py -m pip install -r requirements.txt

# macOS/Linux
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 3. 运行

```bash
# Windows
py -m streamlit run app.py

# macOS/Linux
streamlit run app.py
```

## 项目结构

```
marketplace-ai/
├── pages/                        # 多页面（薄包装，各模块独立，崩溃互不影响）
│   ├── 2_问题管理.py
│   ├── 3_品牌线索.py
│   ├── 4_商家通讯录.py
│   ├── 5_招商管理.py
│   └── 6_卖家分析.py            # 4行薄包装 → src/web/tabs/seller_tab.py
├── src/
│   ├── config/                   # 配置管理
│   │   └── settings.py
│   ├── knowledge/                # 知识库
│   │   ├── experience_library.py
│   │   └── newegg_seller_academy.py  # 17个模块的Seller Academy知识库
│   └── web/                      # 共享模块
│       ├── sidebar.py            # 侧边栏（API配置）
│       ├── utils.py              # Excel I/O + 文本工具（74行）
│       ├── excel_export.py       # Excel导出+图表（809行）
│       ├── web_scraper.py        # 网页抓取（66行）
│       ├── ai.py                 # AI功能（Hunter+品牌分析）
│       ├── data.py               # 数据处理（含mtime缓存）
│       ├── styles.py             # Valorant风格UI主题
│       ├── seller_analysis.py    # 卖家分析计算逻辑
│       └── tabs/                 # 页面逻辑模块
│           ├── seller_tab.py     # 卖家分析（1297行）
│           ├── issues.py         # 问题管理
│           ├── leads.py          # 品牌线索
│           ├── contacts.py       # 商家通讯录
│           ├── emails.py         # 招商管理
│           └── dashboard.py      # 运营总览
├── data/                         # 数据文件
│   ├── sku_analysis/             # SKU明细分析历史（JSON）
│   ├── competitor_analysis/      # 竞品数据（爬虫抓取）
│   ├── experience.json           # 运营经验库
│   └── *.xlsx                    # 品牌/问题/联系方式等数据
├── reports/                      # 运营报告
├── docs/                         # 文档
├── app.py                        # 主入口（运营总览）
├── .streamlit/config.toml        # Streamlit主题配置
├── requirements.txt
├── .env.example
└── README.md
```

## 架构说明

采用 Streamlit 多页面架构，每个功能模块是一个独立页面。一个模块崩溃不会影响其他模块正常使用。

共享模块位于 `src/web/` 目录下，按职责拆分：
- `utils.py`（74行）：Excel I/O、文本工具、UI辅助
- `excel_export.py`（809行）：所有openpyxl格式化导出+图表
- `web_scraper.py`（66行）：网页抓取（requests + Playwright）
- `data.py`：数据加载（含文件mtime感知缓存）
- `ai.py`：AI功能（Hunter邮箱、品牌分析）
- `seller_analysis.py`：核心计算逻辑
- `tabs/`：各页面逻辑模块（卖家分析、问题管理、品牌线索等）

页面采用薄包装模式：`pages/*.py` 只有3-4行，导入并调用 `tabs/` 中的 `render()` 函数。知识库模块位于 `src/knowledge/`。

## UI风格

采用 Valorant 游戏风格深色主题：深蓝黑背景 + 暖白文字 + 红色强调色。

## 卖家分析 - 功能说明

### 时间筛选器（页面顶部）
- **分析周期**：全部 / 本周 / 本月 / 最近30天 / 自定义日期
- 全局联动：筛选后，卖家全景概览、管理平台、历史回看、趋势分析全部跟随变化

### 卖家全景概览
- **等级分布饼图**：A/B/C/D四等级卖家占比
- **GMV vs RMA% 散点图**：定位高GMV高退货的问题卖家
- **各等级GMV总额柱状图**：对比不同等级卖家的销售贡献
- **全宽评分排名 + 低分卖家Top10**

### 数据保存与回看
- 上传数据后可选择**保存到项目**（JSON格式存入data/sku_analysis/）
- **历史回看区**：选择卖家+历史批次，展示完整的分级治理表+健康度对比+趋势图

### Excel导出（含图表）
- 卖家健康度历史：选中记录导出Excel（含趋势折线图+计算说明）
- SKU明细历史：选中批次导出Excel（含风险等级饼图、品类柱状图、库存分布图、效能等级图）
- **一键导出全部卖家**：生成4个可视化Sheet的全景报表

### 评判标准
- **卖家等级**：GMV($50K=30分) + 毛利($10K=25分) + RMA%(≤2%=20分) + 动销(10分) + SKU数(10分) + 毛利率(5分) = 满分100
- **等级划分**：A≥75(核心优质) / B≥60(高潜力) / C≥45(普通合规) / D<45(高风险)
- **行业基准**：3C/消费电子行业标准 + 内部数据混合
