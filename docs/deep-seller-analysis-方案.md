# Deep Seller Analysis Skill 重建方案

> 2026-07-21 创建 | 最后更新: 2026-07-21
> 状态：方案确认，待执行

## 一、Skill架构

### 目录结构
```
.opencode/skills/deep-seller-analysis/
├── SKILL.md          # AI指令（告诉AI怎么分析）
├── analyze.py        # 分析脚本（数据读取+指标计算）
└── templates/
    └── seller_report.md  # 报告模板
```

### 执行流程
```
用户：深度分析ACP1
  ↓
AI读取SKILL.md（知道分析流程和规则）
  ↓
AI调用 analyze.py：
  1. load_sku_analysis_list("ACP1") → 读取所有月份数据
  2. merge_and_generate() → 合并BI+BSD数据
  3. calc_seller_health_from_sku() → 计算健康度
  4. load_seller_history("ACP1") → 读取历史趋势
  ↓
AI调用知识库：
  5. get_knowledge("performance") → 绩效指标标准
  6. search_knowledge("RMA") → RMA相关平台政策
  7. ExperienceLibrary.search() → 历史相似案例
  ↓
AI按模板生成报告（根据站点类型动态调整）
  ↓
输出：reports/{seller_id}_深度分析_{日期}.md
```

## 二、数据源

### 数据位置
- SKU分析数据：`data/sku_analysis/{seller_id}/` 下的JSON文件
- 卖家历史记录：`data/seller_history/{seller_id}.json`
- 经验库：`data/experience.json`

### JSON数据结构
```json
{
  "seller_id": "ACP1",
  "date_period": "20260601-20260630",
  "date_readable": "2026/06/01 - 2026/06/30",
  "total_skus": 28,
  "seller_summary": {
    "GMV": 43895,
    "RMA%": -0.5,
    "总毛利": 8200,
    "总销量": 156,
    "SKU数": 28,
    "健康度评分": 72,
    "等级": "B"
  },
  "records": [...],
  "inv_upload_time": "2026-07-15 10:30"
}
```

### 多站点结构
同一个公司（SellerName）可能有多个seller_id：

| SellerName | seller_id | 站点 | GMV |
|-----------|-----------|------|-----|
| SenyTech Global | C3U3 | B2C | $25,000 |
| SenyTech Global | C3U4 | B2C | $15,000 |
| SenyTech Global | VRD4 | CA | $2,000 |

分析时需要：
1. 先识别该seller_id属于哪个站点
2. 如果同一公司有多个seller_id，做跨站点汇总
3. B2C通常是主要站点（GMV最大），CA/B2B是补充

## 三、报告模板设计

### 设计原则
- **站点差异化**：B2C/CA/B2B各有不同的市场特性和核心问题
- **B2C为主**：数据最丰富，分析最详细，聚焦运营优化
- **CA为辅**：核心问题是SKU太少，聚焦跨站点同步
- **B2B为辅**：聚焦批发定价和企业客户
- **动态调整**：根据数据量和等级调整报告深度

### 站点特性对比

| 维度 | B2C | CA | B2B |
|------|-----|-----|-----|
| 市场规模 | ~$1.9M/周 | ~$77K/周 | ~$88K/周 |
| 典型GMV | $5K-$50K | $100-$5K | $1K-$20K |
| 典型SKU数 | 10-30个 | 1-5个 | 5-15个 |
| 核心问题 | 运营优化、库存周转 | SKU太少、未充分利用 | 批发定价、企业客户 |
| 建议方向 | 调价/促销/下架低效SKU | 从B2C热销款同步 | 阶梯价格/B2B Deal Portal |
| 健康度基准 | 按B2C标准评分 | 应单独评估（不与B2C比） | 按B2B标准评分 |

---

### 模板A：B2C站点报告（标准版）

适用于B2C站点的A/B级卖家，数据丰富。

```markdown
# [卖家ID] B2C深度运营分析报告

> 分析时间：{日期} | 站点：B2C | 数据周期：{月份}

## 一、数据概览

### 核心指标
| 指标 | 数值 | 行业评价 | 月环比 |
|------|------|---------|--------|
| 健康度 | {XX}分 | {X}级 | - |
| GMV | ${XX,XXX} | {X}级 | ↑/↓{XX}% |
| RMA% | {X.X}% | {X}级 | ↑/↓{XX}pp |
| 毛利率 | {X.X}% | {X}级 | - |
| SKU数 | {XX}个 | - | - |
| 总销量 | {XX}件 | - | - |

## 二、分层分析

### SBS库存分析
| SKU | 商品 | 成色 | GMV | 库存 | 日均销量 | 问题 |
|-----|------|------|-----|------|---------|------|
| {top5问题SKU} |

### SBN库存分析
| SKU | 商品 | 成色 | GMV | 库存 | 日均销量 | 问题 |
|-----|------|------|-----|------|---------|------|

### 品类分析
| 品类 | GMV | 占比 | 毛利率 | SKU数 | 主要问题 |
|------|-----|------|--------|-------|---------|

## 三、运营诊断

### 核心问题（按优先级）
| # | 问题 | 涉及范围 | 影响 | 建议 |
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
> 问题1：{针对问题1的具体话术，引用平台政策}
> 问题2：{针对问题2的具体话术}
> 结束：{留有余地的话术}

## 六、持续监控
| 指标 | 当前值 | 目标值 | 监控频率 |
|------|--------|--------|----------|
```

---

### 模板B：CA站点报告

CA卖家的核心问题不是"运营不好"，而是**"SKU太少，没有充分利用CA市场"**。

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
| RMA% | {X.X}% | {X.X}% | - |

## CA站点SKU分析

| SKU | 商品 | 成色 | GMV | 库存 | 日均销量 | 建议 |
|-----|------|------|-----|------|---------|------|
| {当前CA站点的所有SKU} |

## 建议

1. **P0**：将B2C Top{XX}热销SKU同步到CA上架
2. **P1**：检查CA站点的定价是否与B2C一致
3. **P2**：评估CA站点的物流成本和利润空间

### B2C热销SKU同步清单（建议上架到CA）

| SKU | 商品 | B2C月GMV | B2C日均销量 | CA同步建议 |
|-----|------|----------|------------|-----------|
| {B2C Top10但CA没有的SKU} |

## 与卖家沟通要点

> "我们在CA站点目前只上了{XX}个SKU，但B2C这边有{XX}个在卖。
> 建议先把B2C卖得好的{XX}个同步过去，CA市场竞争小，
> 同样的产品在CA可能更容易出单。"
```

---

### 模板C：B2B站点报告

B2B的核心是**批量采购和企业客户**。

```markdown
# [卖家ID] B2B站点运营分析报告

> 分析时间：{日期} | 站点：B2B | 数据周期：{月份}

## 核心发现

- B2B订单特征：{大单/小单/混合}
- 平均客单价：${XX}（B2C为${XX}）
- SKU数：{XX}个

## B2B SKU分析

| SKU | 商品 | GMV | 订单数 | 平均客单价 | 建议 |
|-----|------|-----|--------|-----------|------|
| {所有B2B SKU} |

## 建议

1. 开通B2B Deal Portal促销
2. 设置阶梯价格（批量折扣）
3. 优化B2B专属listing（强调规格参数、兼容性）

## 与卖家沟通要点

> "B2B这边目前{XX}个SKU在卖，平均客单价${XX}。
> 建议开通Deal Portal做批量促销，企业客户对价格敏感，
> 阶梯折扣能有效提升转化。"
```

---

### 模板D：多站点公司综合报告

同一个公司有多个seller_id时，先做跨站点汇总。

```markdown
# {公司名} 综合运营分析报告

> 分析时间：{日期} | 公司：{SellerName}

## 公司概览

| 站点 | seller_id | GMV | 占比 | 等级 | SKU数 |
|------|-----------|-----|------|------|-------|
| B2C | {id} | ${XX,XXX} | {XX}% | {X} | {XX} |
| CA | {id} | ${XXX} | {XX}% | {X} | {XX} |
| B2B | {id} | ${XXX} | {XX}% | {X} | {XX} |
| **合计** | - | **${XX,XXX}** | **100%** | - | **{XX}** |

## 各站点详细分析

### B2C站点（{seller_id}）
{引用B2C模板的分析内容，精简版}

### CA站点（{seller_id}）
{引用CA模板的分析内容}

### B2B站点（{seller_id}）
{引用B2B模板的分析内容}

## 跨站点建议

| 建议 | 依据 | 预期效果 |
|------|------|----------|
| {如：CA同步B2C热销款} | B2C有{XX}个SKU，CA只有{XX}个 | CA GMV预计提升{XX}% |
| {如：B2B开通Deal Portal} | B2B客单价${XX}，适合批量促销 | B2B订单量预计提升{XX}% |

## 综合沟通要点

> 开场：{针对公司整体情况的话术}
> B2C问题：{B2C站点的沟通要点}
> CA机会：{CA站点的沟通要点}
> B2B建议：{B2B站点的沟通要点}
```

---

### 模板E：C/D级卖家精简版

数据少或问题严重时，用精简版。

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

## 四、知识库集成

### 引用平台知识
在报告中引用具体的Newegg平台政策：

```python
knowledge = get_knowledge()

# RMA问题 → 引用处理时效
if rma_pct > 5:
    rma_info = knowledge["rma"]["RMA流程"]
    report += f"**平台规则**：RMA必须在{rma_info['处理时间']}，否则系统自动退款\n"

# 绩效问题 → 引用目标值
perf = knowledge["performance"]["账户健康仪表板"]["核心指标"]
report += f"**绩效标准**：订单缺陷率{perf['订单绩效']['订单缺陷率']['目标']}，"
report += f"退款率{perf['订单绩效']['退款率']['目标']}\n"

# 发货问题 → 引用发货规则
ship = knowledge["orders"]["发货"]["注意事项"]
report += f"**发货要求**：{ship[0]}\n"

# CA/B2B特殊政策
ca_policy = knowledge["ca"]
b2b_policy = knowledge["b2b"]
```

### 引用历史案例
```python
lib = ExperienceLibrary()
similar = lib.search(seller_id, top_k=3)
if similar:
    report += "\n### 历史参考\n"
    for case in similar:
        report += f"- {case['问题描述'][:60]}... → {case['解决方案'][:60]}...\n"
```

## 五、错误处理

```python
def safe_analyze(seller_id):
    """安全分析入口，带完整错误处理"""
    # 1. 检查卖家是否存在
    batches = load_sku_analysis_list(seller_id)
    if not batches:
        return {"error": f"卖家 {seller_id} 没有数据，请先上传BI+BSD数据"}
    
    # 2. 检查数据完整性
    latest = batches[0]
    if "seller_summary" not in latest:
        return {"error": "数据格式错误：缺少 seller_summary 字段"}
    if "records" not in latest or not latest["records"]:
        return {"error": "没有SKU明细数据"}
    
    # 3. 检查关键字段
    summary = latest["seller_summary"]
    required_fields = ["GMV", "RMA%", "健康度评分", "等级"]
    missing = [f for f in required_fields if f not in summary]
    if missing:
        return {"error": f"数据缺少字段：{', '.join(missing)}"}
    
    # 4. 计算月环比（需要至少2个月数据）
    mom_change = None
    if len(batches) >= 2:
        mom_change = calc_mom_change(batches[0], batches[1])
    
    # 5. 检查同公司其他站点
    cross_site = find_cross_site_sellers(seller_id)
    
    # 6. 执行分析
    return perform_analysis(seller_id, batches, mom_change, cross_site)
```

## 六、月环比/周环比

### 数据存储策略
- Streamlit工具：每次上传BI+BSD → 保存JSON（按月）
- 文件名格式：`{YYYYMMDD}-{YYYYMMDD}.json`
- 自动识别时间范围

### 环比计算
```python
def calc_mom_change(current, previous):
    """计算月环比"""
    curr = current.get("seller_summary", {})
    prev = previous.get("seller_summary", {})
    
    gmv_curr = curr.get("GMV", 0)
    gmv_prev = prev.get("GMV", 0)
    
    if gmv_prev > 0:
        gmv_change = (gmv_curr - gmv_prev) / gmv_prev * 100
    else:
        gmv_change = None
    
    return {
        "gmv_change_pct": gmv_change,
        "rma_change_pp": curr.get("RMA%", 0) - prev.get("RMA%", 0),
        "periods": f"{previous.get('date_readable', '?')} → {current.get('date_readable', '?')}"
    }
```

### 周环比
需要额外的周数据源。方案：
- 每周从BI拉一次数据
- 保存为 `weekly/{seller_id}_{YYYYMMDD}.json`
- 分析时自动对比上周数据

## 七、反馈机制

用户手动筛选 = 最高质量反馈：

```
流程：
1. AI生成初版报告
2. 用户修改/筛选/调整（企业微信沟通）
3. 最终版保存到 reports/{seller_id}_深度分析_{日期}.md
4. 用户把修改后的沟通话术保存到 experience.json
5. 下次分析同一卖家时，AI自动参考历史
```

## 八、Excel导出

不在skill中重复。Streamlit工具的"一键导出全部卖家"功能已覆盖。

## 九、执行计划

| 步骤 | 内容 | 工作量 |
|------|------|--------|
| 1 | 重写SKILL.md（引用现有代码+知识库+经验库） | 1小时 |
| 2 | 创建analyze.py（数据读取+指标计算+错误处理+环比） | 2小时 |
| 3 | 更新CLAUDE.md（修正skill引用） | 10分钟 |
| 4 | 测试：用ACP1跑一次完整分析 | 30分钟 |
