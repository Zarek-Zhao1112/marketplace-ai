# Marketplace AI - Newegg跨境BD智能助手

## 项目简介

Streamlit Web应用, 帮Newegg运营做卖家分析+SKU管理。

- **技术栈**: Python + Streamlit + Plotly + openpyxl
- **AI后端**: 豆包(ARK) API（问题管理+AI回复建议）
- **数据存储**: Excel + JSON文件, 无数据库

## 核心规则

1. **中文回复**
2. **简单优先** - 用户删复杂功能
3. **先方案后行动** - 改前先展示方案
4. **数据安全** - 销售数据读取前提醒用户

## 目录结构

```
marketplace-ai/
├── app.py                 # 入口（运营总览）
├── pages/                 # Streamlit多页面（薄包装→tabs）
│   ├── 2_问题管理.py
│   ├── 3_品牌线索.py
│   ├── 4_商家通讯录.py
│   ├── 5_招商管理.py
│   └── 6_卖家分析.py      # 4行 → src/web/tabs/seller_tab.py
├── src/
│   ├── config/settings.py
│   ├── web/
│   │   ├── seller_analysis.py  # 计算逻辑（safe_float/safe_int）
│   │   ├── utils.py            # Excel I/O + 文本工具（74行）
│   │   ├── excel_export.py     # openpyxl导出+图表（809行）
│   │   ├── web_scraper.py      # requests+Playwright（66行）
│   │   ├── data.py             # 数据加载（mtime缓存）
│   │   ├── ai.py               # AI功能（Hunter邮箱+品牌分析）
│   │   ├── styles.py           # UI样式（Valorant深色主题）
│   │   ├── sidebar.py          # 侧边栏
│   │   └── tabs/
│   │       ├── seller_tab.py   # 卖家分析（1297行）
│   │       ├── issues.py       # 问题管理
│   │       ├── leads.py        # 品牌线索
│   │       ├── contacts.py     # 商家通讯录
│   │       ├── emails.py       # 招商管理
│   │       └── dashboard.py    # 运营总览
│   └── knowledge/
│       ├── experience_library.py
│       └── newegg_seller_academy.py  # 17个模块
├── data/
│   ├── sku_analysis/      # SKU分析JSON（80个seller）
│   └── competitor_analysis/
├── reports/
├── docs/
└── .opencode/skills/
```

## 卖家分析

核心: `pages/6_卖家分析.py` + `src/web/seller_analysis.py`：

- **健康度评分**: GMV(30) + 毛利(25) + RMA%(20) + 销量(10) + SKU数(10) + 毛利率(5)
  - GMV: $50K=30分（行业基准对齐）
  - RMA%: ≤2%→20, ≤5%→16, ≤8%→12, ≤15%→8, ≤25%→4
- **等级**: A≥75 / B≥60 / C≥45 / D<45
- **优先级评分**: 退货损失(40%) + 毛利侵蚀(30%) + RMA严重度(20%) + 动销逆向(10%)
- **RMA%计算**: 排除退货(GMV<0), 只算正常销售

## 问题管理 + AI回复建议

核心: `pages/2_问题管理.py` + `src/web/tabs/issues.py`：

- **聊天记录解析**: `_parse_chat()` 统一入口, 支持纯文本和图片+文本
- **AI提取问题**: 豆包AI从聊天记录自动提取结构化问题
- **经验库搜索**: 关键词匹配+AI语义检索
- **AI回复建议**: 基于Newegg Seller Academy知识库
- **AI学习闭环**: 用户修改回复→保存到经验库, AI学习风格
- **缓存**: 文件mtime感知, 删除/修改后自动失效

## 知识库（Newegg Seller Academy）

核心: `src/knowledge/newegg_seller_academy.py`（17个模块）

| 模块 | 内容 |
|------|------|
| platform | 平台基础 |
| registration | 卖家注册流程 |
| items | 商品创建/更新/批量/变体 |
| orders | 订单列表/发货/批量/多渠道 |
| rma | 退货授权/无退货退款/Marketplace Guarantee |
| promotion | 5种活动+折扣码+提交表 |
| messages | 消息3.0+模板功能 |
| analytics | 销售仪表盘+按日期/商品报表 |
| advertising | 5种广告+站外推广 |
| sbn | 多渠道拣配+仓库货件+库存警报 |
| store | 普通店铺+会员店铺 |
| performance | 账户健康Dashboard+绩效指标 |
| faq | 常见问题 |
| policies | 平台政策 |
| b2b/ca | B2B/CA特殊政策 |
| reply | AI回复建议模板 |

查询: `get_knowledge(category)` + `search_knowledge(query)`

## 报告生成规则

- 报告放 `reports/` 文件夹
- 不含"与导师沟通要点"
- "沟通要点"单独对话界面发给用户
- 报告必须含"与卖家沟通指南"章节

## AI技能

| Skill | 来源 | 用途 |
|-------|------|------|
| **deep-seller-analysis** | 项目内置 | 深度卖家分析（多站点+知识库+经验库） |
| **sellingpilot-pitch** | 项目内置 | SellingPilot推销话术 |
| **dealer-recruitment** | 项目内置 | 经销商招募 |
| **humanizer-zh** | 第三方 | 去除AI痕迹 |
| **superpowers-zh** | 第三方 | AI编程方法论（20个skills） |
| **planning-with-files** | 第三方 | 文件式持久化规划 |
| **agent-skill-creator** | 第三方 | Skill创建和管理 |

### deep-seller-analysis
- 触发: `深度分析[卖家ID]`、`卖家深度分析`、`运营诊断报告`
- 数据: `data/sku_analysis/{seller_id}/` JSON
- 脚本: `.opencode/skills/deep-seller-analysis/analyze.py`
- 知识库: `newegg_seller_academy.py` 17个模块
- 经验库: `experience_library.py`
- 模板: B2C标准 / CA站点 / B2B站点 / 多站点综合 / C/D精简

### 分层分析
- **履约**: SBS vs SBN
- **成色**: 全新/翻新/二手
- **品类**: 显卡/主板/处理器/固态硬盘/外设
- **规模**: 大(>$50K)/中($10K-50K)/小(<$10K)

### 数据抓取
- requests + BeautifulSoup 抓Newegg
- **先建议后执行** - 告知抓什么、为何抓, 等确认
- 保存到 `data/competitor_analysis/`

## 关键函数

| 函数 | 位置 | 用途 |
|------|------|------|
| `calc_seller_health_score` | seller_analysis.py | 健康度评分 |
| `calc_return_qty` | seller_analysis.py | 退货件数（math.ceil, RMA%=0→0） |
| `calc_priority_score` | seller_analysis.py | 优先级评分（四维度加权） |
| `extract_category` | seller_analysis.py | 品类分类（跳过CH前缀） |
| `safe_float/safe_int` | seller_analysis.py | 安全类型转换 |
| `safe_analyze` | deep-seller-analysis/analyze.py | 深度卖家分析入口（错误+环比+分层） |
| `_parse_chat` | tabs/issues.py | 聊天记录解析（重试+缓存） |
| `parse_date_any` | tabs/seller_tab.py | 日期解析（多格式） |
| `export_sku_excel` | excel_export.py | SKU分级治理导出 |
| `export_all_sellers_pano` | excel_export.py | 全景报表（4个Sheet） |
| `_cached_read_json` | data.py | mtime感知JSON缓存 |
| `get_knowledge` | newegg_seller_academy.py | 知识库分类查询 |
| `search_knowledge` | newegg_seller_academy.py | 知识库关键词搜索 |

## 工具脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `scripts/sync_inventory.py` | BSD库存更新历史JSON | `python scripts/sync_inventory.py <bsd_excel_path>` |
| `scripts/recalc_metrics.py` | 更新指标 | `python recalc_metrics.py [seller_id]` |
| `scripts/track_inventory.py` | 库存变化历史 | `python track_inventory.py [seller_id]` |

## 常见问题

1. **JSON损坏**: `load_sku_analysis_list` 跳过损坏文件
2. **numpy序列化**: 写JSON前 `float()`/`int()` 转numpy类型
3. **Plotly样式**: `DARK_LAYOUT` + `AXIS_STYLE` + `dark_title()`
4. **Streamlit缓存**: 改代码重启Streamlit

## 用户

- **身份**: 电商实习生, 负责80个Newegg卖家
- **工作**: AM - PO控库存、调价格、抓新品
- **目标**: 帮卖家卖更好, 积累运营/数据/产品思维
