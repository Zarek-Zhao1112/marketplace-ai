---
name: deep-seller-analysis
description: "深度卖家分析助手 - 基于真实数据+知识库+经验库，输出高质量运营诊断报告。支持单个卖家分析、分组分析、多站点报告。触发词：深度分析[卖家ID]、卖家深度分析、运营诊断报告。"
version: 2.0
updated: 2026-07-21
tags: newegg, seller, analysis, report, multi-site, knowledge-base
triggers:
  - 深度分析
  - 卖家深度分析
  - 运营诊断报告
  - 卖家分析报告
---

# 深度卖家分析助手 v2.0

> 基于真实数据 + 知识库 + 经验库，输出高质量运营诊断报告

---

## 核心原则

1. **数据驱动** — 所有判断必须有数据支撑，用 analyze.py 获取真实数据
2. **站点差异化** — B2C/CA/B2B 各有不同市场特性，用不同模板
3. **知识库引用** — 引用 Newegg 平台政策（绩效标准、RMA规则等）
4. **经验库参考** — 参考历史分析案例，避免重复分析
5. **可执行** — 建议必须具体到 SKU 和操作
6. **沟通友好** — 每个问题附带"跟 seller 沟通要点"

---

## 数据源

### 数据位置
- SKU分析数据：`data/sku_analysis/{seller_id}/` 下的JSON文件
- 卖家历史记录：`data/seller_history/{seller_id}.json`
- 经验库：`data/experience.json`
- 知识库：`src/knowledge/newegg_seller_academy.py`（17个模块）

### JSON数据结构
每个JSON文件 = 一个时间段的分析结果：
```json
{
  "seller_id": "ACP1",
  "date_period": "20260601-20260630",
  "date_readable": "2026/06/01 - 2026/06/30",
  "total_skus": 28,
  "seller_summary": { "GMV": 43895, "RMA%": -0.5, "健康度评分": 72, "等级": "B" },
  "records": [...]
}
```

---

## 执行流程

```
用户：深度分析ACP1
  ↓
Step 1: 读取数据
  python analyze.py ACP1 → 输出JSON（健康度、SKU分析、环比等）
  ↓
Step 2: 加载知识库
  get_knowledge() → 平台政策（绩效标准、RMA规则、发货要求）
  search_knowledge("RMA") → 相关政策
  ↓
Step 3: 加载经验库
  ExperienceLibrary().search(seller_id) → 历史相似案例
  ↓
Step 4: 确定站点类型
  - B2C → 用模板A（标准版）
  - CA → 用模板B（SKU同步版）
  - B2B → 用模板C（批发定价版）
  - 多站点公司 → 用模板D（综合版）
  - C/D级卖家 → 用模板E（精简版）
  ↓
Step 5: 生成报告
  按模板填写数据，引用知识库政策，参考经验库案例
  ↓
Step 6: 输出
  reports/{seller_id}_深度分析_{日期}.md
```

---

## 站点特性

| 维度 | B2C | CA | B2B |
|------|-----|-----|-----|
| 市场规模 | ~$1.9M/周 | ~$77K/周 | ~$88K/周 |
| 典型GMV | $5K-$50K | $100-$5K | $1K-$20K |
| 典型SKU数 | 10-30个 | 1-5个 | 5-15个 |
| 核心问题 | 运营优化、库存周转 | SKU太少、未充分利用 | 批发定价、企业客户 |
| 建议方向 | 调价/促销/下架低效SKU | 从B2C热销款同步 | 阶梯价格/B2B Deal Portal |

---

## 报告模板选择

根据 analyze.py 返回的 `site` 字段选择模板：

| site值 | 模板 | 适用场景 |
|--------|------|----------|
| B2C + 等级A/B | 模板A | B2C标准版（完整分析） |
| CA | 模板B | CA站点版（SKU同步清单） |
| B2B | 模板C | B2B站点版（批发定价） |
| 多站点公司 | 模板D | 综合版（跨站点汇总） |
| 等级C/D | 模板E | 精简版（快速诊断） |

---

## 模板A：B2C标准版

```markdown
# [卖家ID] B2C深度运营分析报告

> 分析时间：{日期} | 站点：B2C | 数据周期：{月份}

## 一、数据概览

### 核心指标
| 指标 | 数值 | 行业评价 | 月环比 |
|------|------|---------|--------|
| 健康度 | {XX}分 | {X}级 | - |
| GMV | ${XX,XXX} | {gmv_rating} | ↑/↓{XX}% |
| RMA% | {X.X}% | {rma_rating} | ↑/↓{XX}pp |
| 毛利率 | {X.X}% | {margin_rating} | - |
| SKU数 | {XX}个 | - | - |

## 二、分层分析

### SBS/SBN对比
| 履约方式 | SKU数 | GMV | 平均RMA% | 库存 |
|---------|-------|-----|---------|------|
| SBS | {XX} | ${XX,XXX} | {X.X}% | {XX} |
| SBN | {XX} | ${XX,XXX} | {X.X}% | {XX} |

### 品类分析
| 品类 | GMV | 占比 | 毛利率 | SKU数 |
|------|-----|------|--------|-------|

## 三、运营诊断

### 核心问题（按优先级）
| # | 问题 | 涉及SKU | 影响 | 建议 |
|---|------|---------|------|------|

### 风险预警
| SKU | 风险类型 | 严重程度 | 建议 |
|-----|---------|---------|------|

## 四、策略建议

### 本周行动（P0）
| 动作 | 涉及SKU | 目标 | 预期效果 |
|------|---------|------|----------|

### 本月优化（P1）
| 动作 | 涉及SKU | 目标 | 预期效果 |
|------|---------|------|----------|

## 五、与卖家沟通要点

> 开场：{建立信任的话术}
> 问题1：{引用平台政策的具体话术}
> 问题2：{具体话术}
> 结束：{留有余地的话术}

## 六、持续监控
| 指标 | 当前值 | 目标值 | 监控频率 |
|------|--------|--------|----------|
```

---

## 模板B：CA站点版

CA卖家的核心问题：**SKU太少，B2C有28个但CA只有1个**。

```markdown
# [卖家ID] CA站点运营分析报告

> 分析时间：{日期} | 站点：CA | 数据周期：{月份}

## 核心发现

- CA站点GMV：${XX}/月（仅占公司总GMV的{X}%）
- SKU数：{XX}个（B2C有{XX}个SKU）
- **机会：B2C热销SKU尚未同步到CA**

## B2C vs CA对比

| 指标 | B2C（{seller_id}） | CA（{seller_id}） | 差距 |
|------|-------------------|-------------------|------|
| GMV | ${XX,XXX} | ${XXX} | {XX}倍 |
| SKU数 | {XX} | {XX} | {XX}个未同步 |
| 等级 | {X} | {X} | - |

## 建议

1. **P0**：将B2C Top{XX}热销SKU同步到CA上架
2. **P1**：检查CA站点定价是否与B2C一致
3. **P2**：评估CA物流成本和利润空间

### B2C热销SKU同步清单
| SKU | 商品 | B2C月GMV | CA同步建议 |
|-----|------|----------|-----------|

## 与卖家沟通要点
> "我们在CA站点目前只上了{XX}个SKU，但B2C这边有{XX}个在卖。
> 建议先把B2C卖得好的{XX}个同步过去。"
```

---

## 模板C：B2B站点版

```markdown
# [卖家ID] B2B站点运营分析报告

> 分析时间：{日期} | 站点：B2B | 数据周期：{月份}

## 核心发现
- 平均客单价：${XX}（B2C为${XX}）
- SKU数：{XX}个

## 建议
1. 开通B2B Deal Portal促销
2. 设置阶梯价格（批量折扣）
3. 优化B2B专属listing

## 与卖家沟通要点
> "B2B这边建议开通Deal Portal做批量促销。"
```

---

## 模板D：多站点综合版

```markdown
# {公司名} 综合运营分析报告

> 分析时间：{日期} | 公司：{SellerName}

## 公司概览
| 站点 | seller_id | GMV | 占比 | 等级 | SKU数 |
|------|-----------|-----|------|------|-------|

## 各站点分析
### B2C站点
{精简版B2C分析}
### CA站点
{CA分析}
### B2B站点
{B2B分析}

## 跨站点建议
| 建议 | 依据 | 预期效果 |
|------|------|----------|

## 综合沟通要点
```

---

## 模板E：C/D级精简版

```markdown
# [卖家ID] 运营诊断报告

## 快速诊断
- 等级：{D} | 健康度：{XX}分 | 主要问题：{XXX}
- 站点：{B2C/CA/B2B} | SKU数：{XX} | 月GMV：${XX}

## 关键问题
1. {问题1}
2. {问题2}

## 建议
- {建议1}
- {建议2}

## 沟通要点
{简短直接的沟通话术}
```

---

## 知识库引用

在报告中引用具体平台政策：

```python
from src.knowledge.newegg_seller_academy import get_knowledge, search_knowledge

knowledge = get_knowledge()

# RMA问题 → 引用处理时效
if rma_pct > 5:
    rma_info = knowledge["rma"]["RMA流程"]
    # "平台规则：RMA必须在2个工作日内处理，否则系统自动退款"

# 绩效问题 → 引用目标值
perf = knowledge["performance"]["账户健康仪表板"]["核心指标"]
# "绩效标准：订单缺陷率<1%，退款率<5%"

# 发货问题 → 引用发货规则
ship = knowledge["orders"]["发货"]["注意事项"]
# "发货要求：Newegg强烈建议2天内处理订单"

# CA/B2B特殊政策
ca_policy = knowledge["ca"]
b2b_policy = knowledge["b2b"]
```

---

## 经验库引用

```python
from src.knowledge.experience_library import ExperienceLibrary

lib = ExperienceLibrary()
similar = lib.search(seller_id, top_k=3)
# 在报告中引用历史相似案例
```

---

## 错误处理

analyze.py 的 safe_analyze() 已包含：
- 卖家不存在 → 提示上传数据
- 数据格式错误 → 提示字段缺失
- 无SKU数据 → 提示重新导入
- 月环比需要至少2个月数据

---

## 使用方法

### 分析单个卖家
告诉AI：`深度分析ACP1`
AI会自动调用 analyze.py，按模板生成报告。

### 分析多站点公司
告诉AI：`深度分析SenyTech Global的所有站点`
AI会用模板D生成综合报告。

### 列出所有卖家
```bash
python .opencode/skills/deep-seller-analysis/analyze.py --list
```

---

## 注意事项

1. 报告输出到 `reports/` 目录
2. 用户修改后的沟通话术可保存到经验库
3. 知识库政策引用要准确，不要编造
4. CA/B2B报告不要硬套B2C模板
5. C/D级卖家用精简版，不要塞空表格
