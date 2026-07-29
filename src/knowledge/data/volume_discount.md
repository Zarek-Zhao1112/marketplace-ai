---
module: volume_discount
title: 阶梯价格
last_updated: 2026-07-24
---

# 阶梯价格（Volume Discount）

允许卖家根据客户购买数量设置阶梯折扣价格。目前最多可设置3个阶梯。

**可用平台**：Newegg.com, Neweggbusiness.com, Newegg.ca

## 单个商品设置

### 步骤
1. 登录Seller Portal → 商品 → 阶梯价格
2. 在"Single Volume Discount"选项卡，点击"ADD VOLUME DISCOUNT"
3. 输入商品编号（NE Item# 或 Seller Part#）
4. 设置阶梯价格：
   - 第1阶梯：数量/价格/运费
   - 点击"+"添加第2、第3阶梯
5. 点击"SAVE"保存

### 注意事项
- 同步时间：最多15分钟
- 设置成功后会在商品页面显示阶梯价格表
- 状态显示：绿色=在线，黄色=下架

## 批量设置

### 下载模板
1. 选择"Download File Template"选项卡
2. 模板类型：VolumeDiscount
3. 文件格式：推荐Microsoft Excel Format
4. 勾选"Download template with data in the file"
5. 点击"DOWNLOAD FILE TEMPLATE"

### 填写模板
- **Activation**: True=添加/更新，False=删除
- 不要修改列名和工作表名

### 上传模板
1. 选择"Batch Create VolumeDiscount"选项卡
2. 点击"Select files…"上传文件
3. 点击"UPLOAD FILES"

### 查看结果
- 状态：Completed/Failed/Completed with errors
- 点击"View Details"查看失败原因

## 查看和编辑

### 查看
1. 在"Single Volume Discount"选项卡点击"SEARCH"
2. 查看所有已设置的阶梯价格

### 编辑
1. 点击操作列的编辑图标
2. 修改阶梯数量/价格/运费
3. 点击"SAVE"保存

## 删除

### 单个删除
1. 点击操作列的删除图标
2. 输入原因/备注
3. 点击"SAVE"确认

### 批量删除
1. 勾选要删除的商品
2. 点击"GO"
3. 输入原因
4. 点击"SAVE"确认

## 阶梯价格示例

| 数量 | 单价 | 运费 |
|------|------|------|
| 1-4件 | $100 | $10 |
| 5-9件 | $95 | $8 |
| 10件以上 | $90 | 免运费 |

## 最佳实践

1. **价格递减**：每阶梯降价5-10%
2. **运费优惠**：高阶梯可设置免运费
3. **数量设置**：根据目标客户群设置合理数量
4. **促销配合**：阶梯价格可与促销活动叠加
