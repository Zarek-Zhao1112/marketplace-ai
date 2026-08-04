---
name: deep-seller-analysis
description: "深度卖家分析助手 - 基于真实数据+知识库+经验库，输出高质量运营诊断报告。支持单个卖家分析、分组分析、多站点报告。触发词：深度分析[卖家ID]、卖家深度分析、运营诊断报告。"
version: 2.0
updated: 2026-08-03
tags: newegg, seller, analysis, report, multi-site, knowledge-base
triggers:
  - 深度分析
  - 卖家深度分析
  - 运营诊断报告
  - 卖家分析报告
---

# 深度卖家分析助手 v2.0

基于真实数据 + 知识库 + 经验库，输出高质量运营诊断报告。

## 数据源

- SKU分析数据：`data/sku_analysis/{seller_id}/` 下的JSON文件
- 知识库：`src/knowledge/newegg_seller_academy.py`（17个模块）
- 经验库：`data/experience.json`

## 模板选择

| site/grade | 模板 | 说明 |
|-----------|------|------|
| B2C + A/B级 | `b2c` | 标准完整报告 |
| CA | `ca` | 站点对齐报告 |
| B2B | `b2b` | 批发定价报告 |
| 多站点公司 | `multi_site` | 跨站点综合 |
| C/D级 | `cd_grade` | 精简诊断 |

模板文件：`.opencode/skills/deep-seller-analysis/templates/*.md`

## 执行流程

```
safe_analyze(seller_id) → JSON
  ↓
render_report(json, template) → Markdown
  ↓
reports/{seller_id}_深度分析_{YYYYMMDD}.md
```

## 核心规则

1. **数据驱动** — 所有判断来自 analyze.py 真实数据，不编造数字
2. **Active-only 口径** — 在售 SKU 数 = `ActivationStatus == Active`，Inactive 不计入
3. **有效动销** — `ActivationStatus == Active` AND `Net Quantity Sold > 0`
4. **AI 补充** — 策略建议、沟通要点由 AI 在报告生成后补充，report.py 输出骨架
5. **知识库引用** — RMA/绩效/发货规则从 newegg_seller_academy.py 获取
6. **经验库参考** — 参考历史相似案例，避免重复分析

## 用法

```
深度分析 {seller_id}
深度分析 {seller_id} ca
深度分析 {seller_id} b2b
```

report.py 也可直接调用：
```bash
python .opencode/skills/deep-seller-analysis/report.py AKUY b2c
```
