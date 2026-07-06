# Marketplace AI - Newegg跨境BD智能助手

## 项目简介

Streamlit Web应用，帮助Newegg Marketplace运营人员进行卖家分析和SKU管理。

- **技术栈**: Python + Streamlit + Plotly + openpyxl
- **AI后端**: 豆包(ARK) API（仅问题管理模块使用）
- **数据存储**: Excel + JSON文件，无数据库

## 核心规则

1. **中文回复** - 用户语言是中文
2. **简单优先** - 不过度设计，用户会主动删复杂功能
3. **先方案后行动** - 任何修改前先展示方案给用户确认
4. **数据安全** - 销售数据是隐私数据，读取前需提醒用户

## 目录结构

```
marketplace-ai/
├── app.py                 # 入口文件（运营总览）
├── pages/                 # Streamlit多页面
│   ├── 2_问题管理.py
│   ├── 3_品牌线索.py
│   ├── 4_商家通讯录.py
│   ├── 5_招商管理.py
│   └── 6_卖家分析.py      # 核心页面
├── src/
│   ├── config/settings.py # 配置集中
│   ├── web/
│   │   ├── seller_analysis.py  # 计算逻辑
│   │   ├── utils.py            # 导出函数
│   │   ├── data.py             # 数据加载
│   │   ├── styles.py           # UI样式
│   │   └── config.py           # 配置兼容层
│   └── knowledge/         # 知识库
├── data/                  # 数据文件
│   ├── sku_analysis/      # SKU分析JSON（80个seller）
│   └── competitor_analysis/ # 竞品数据（爬虫抓取）
├── reports/               # 运营报告
├── .opencode/skills/      # AI技能
│   ├── marketplace-analysis/ # 分析助手（含分层分析）
│   ├── superpowers-zh/       # AI编程方法论（20个skills）
│   ├── planning-with-files/  # 基于文件的持久化规划
│   └── agent-skill-creator/  # Skill创建和管理工具
├── docs/                  # 文档
└── marketplace-analysis-skill.zip  # skill压缩包（给同事用）
```

## 卖家分析模块

核心功能在 `pages/6_卖家分析.py` + `src/web/seller_analysis.py`：

- **健康度评分**: GMV(30分) + 毛利(25分) + RMA%(20分) + 销量(10分) + SKU数(10分) + 毛利率(5分)
- **等级划分**: A≥75 / B≥60 / C≥45 / D<45
- **优先级评分**: 退货损失(40%) + 毛利侵蚀(30%) + RMA严重度(20%) + 动销逆向(10%)
- **RMA%计算**: 必须排除退货记录(GMV<0)，只算正常销售

## 报告生成规则

- 报告文件放在 `reports/` 文件夹
- 报告文件不含"与导师沟通要点"
- "与导师沟通要点"单独在对话界面发给用户
- 报告必须包含"与卖家沟通指南"章节

## AI技能

### 已安装的Skills

| Skill | 来源 | 用途 |
|-------|------|------|
| **marketplace-analysis** | 项目内置 | Newegg卖家数据分析助手 |
| **superpowers-zh** | 第三方 | AI编程方法论（20个skills） |
| **planning-with-files** | 第三方 | 基于文件的持久化规划 |
| **agent-skill-creator** | 第三方 | Skill创建和管理工具 |

### marketplace-analysis（卖家分析助手）
- 合并了运营诊断报告和卖家增长策略
- 触发词："分析卖家"、"卖家分析"、"运营报告"、"SKU优化"、"竞品分析"、"评论分析"、"周报"
- 包含：SKILL.md、competitor-price-analysis.md、product-review-analysis.md、newegg-scraper.md
- 支持Excel输入：`[卖家ID]_[日期范围].xlsx`，每个Sheet一个时间段

### marketplace-analysis 迭代流程

```
1. 你用系统导出Excel（3个月数据，按月份分Sheet）
2. 把Excel给导师 → 导师用公司内部AI+skill → 生成报告
3. 你用报告跟卖家沟通 → 收到反馈
4. 你告诉我哪里不对 → 我修改skill
5. 下次导师用更新后的skill → 报告更准
```

**反馈记录位置**：skill文件末尾的"迭代反馈机制"章节

### superpowers-zh（AI编程超能力）
- 20个AI编程方法论skills
- 常用skills：
  - `/brainstorming` - 需求分析和头脑风暴
  - `/writing-plans` - 编写实施计划
  - `/executing-plans` - 按计划执行
  - `/systematic-debugging` - 系统化调试
  - `/test-driven-development` - 测试驱动开发
  - `/chinese-code-review` - 中文代码审查

### planning-with-files（持久化规划）
- 基于文件的任务规划，防止AI在长对话中忘记目标
- 会创建 `task_plan.md`、`findings.md`、`progress.md` 跟踪进度
- 适合复杂任务：批量数据导入、多步骤功能开发

### agent-skill-creator（Skill创建工具）
- 创建、验证和管理AI skills
- 用于开发和维护marketplace-analysis等自定义skill

### 分层分析框架
- **履约方式**：SBS（Ship by Seller）vs SBN（Ship by Newegg）
- **商品成色**：全新/翻新/二手
- **品类**：显卡/主板/处理器/固态硬盘/外设
- **卖家规模**：大卖家(>$50K)/中等($10K-50K)/小卖家(<$10K)

### 数据抓取规则
- 使用 requests + BeautifulSoup 抓取Newegg数据
- **先建议后执行**：告诉用户抓什么、为什么抓，等用户确认
- 数据保存到 `data/competitor_analysis/`
- 支持成色筛选：翻新品(`&N=100007709`)、全部
- 支持履约方式筛选：SBN(`&shippage=1`)、全部

## 关键函数

| 函数 | 位置 | 用途 |
|------|------|------|
| `calc_seller_health_score` | seller_analysis.py | 健康度评分 |
| `calc_return_qty` | seller_analysis.py | 退货件数（math.ceil，RMA%=0返回0） |
| `calc_priority_score` | seller_analysis.py | 优先级评分（四维度加权） |
| `calc_seller_health_from_sku` | seller_analysis.py | 卖家健康度（排除退货记录算RMA%） |
| `extract_category` | seller_analysis.py | 品类分类（跳过CH前缀） |
| `extract_condition` | seller_analysis.py | 商品成色（优先用ItemCondition） |
| `parse_date_any` | pages/6_卖家分析.py | 日期解析（支持多种格式） |
| `export_sku_excel` | utils.py | Excel导出 |

## 常见问题

1. **JSON损坏**: `load_sku_analysis_list` 已加错误处理，跳过损坏文件
2. **numpy序列化**: 写JSON前用 `float()`/`int()` 转换numpy类型
3. **Plotly样式**: 用 `DARK_LAYOUT` + `AXIS_STYLE` + `dark_title()`

## 用户信息

- **身份**: 电商专业实习生，负责80个Newegg卖家
- **工作**: AM（Account Manager）- PO控库存、调价格、抓新品
- **目标**: 帮卖家卖得更好，积累运营/数据/产品思维
