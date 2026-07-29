"""批量创建知识库MD文件"""
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "knowledge", "data")

# 17个模块的MD文件内容
MODULES = {
    "platform": """---
module: platform
title: 平台基础信息
last_updated: 2026-07-21
---

# 平台基础信息

## 基本信息
- **平台名称**: Newegg Marketplace
- **平台类型**: 第三方卖家平台
- **用户规模**: 4700万+注册用户
- **用户画像**: 70%男性，平均年龄36岁，年收入$7.5万+

## 热销品类
1. Components & Storage（CPU、显卡、主板、SSD、内存）
2. Computer Systems（台式机、笔记本、显示器）
3. Home & Outdoor（网络设备、智能家居、无人机）
4. Gamers（游戏设备、外设、VR）

## 平台链接
- 官网: https://www.newegg.com
- 卖家后台: https://sellerportal.newegg.com
- 学习中心: https://sellerportal.newegg.com/selleracademy/zh-hans/

## 站点
- Newegg.com（美国B2C）
- Neweggbusiness.com（美国B2B）
- Newegg.ca（加拿大）

## 费用
- 新卖家前90天佣金: 6%
- ERP工具: SellingPilot（99元/月）
""",
    
    "registration": """---
module: registration
title: 卖家入驻流程
last_updated: 2026-07-21
---

# 卖家入驻流程

## 入驻步骤
1. 注册卖家账户
2. 更新业务信息
3. 更新财务信息
4. 更新信用卡信息
5. 更新售后政策
6. 更新运费模式和费率
7. 创建商品

## 所需资料
- 企业营业执照
- 法人身份证
- 银行账户信息
- 品牌授权书（如有）

## 注意事项
- 新卖家前90天佣金只要6%
- 支持SellingPilot一键搬家
- B2B和B2C站点可以分开管理

## 快速入驻通道
- **适用对象**: Amazon/Walmart/eBay/TikTok Shop美站卖家
- **一键搬家**: 支持SellingPilot一键搬家功能
- **资料简化**: 仅需营业执照、店铺链接、注册邮箱
""",
    
    "items": """---
module: items
title: 商品管理
last_updated: 2026-07-21
---

# 商品管理

## 创建商品3.0

### 步骤
1. 登录Seller Portal → 商品 → 商品创建
2. 选择'Create an item not listed in Newegg'
3. 选择子类别（搜索或浏览）
4. 填写必填信息（基础、属性、销售、插图、描述）
5. 上传商品图片（最多7张）
6. 提交审核

### 必填字段
- 条件（Condition）
- 标题（Title）
- 制造商（Manufacturer）
- 制造商零件号（Manufacturer Part#）
- UPC（部分子类别强制要求）
- 包装或套装

### 图片要求
- **格式**: JPG, JPEG, GIF, PNG
- **尺寸**: 不小于 640 x 480（宽 x 高）
- **大小**: 不超过 5 MB
- **数量**: 最多7张

### UPC要求
- **强制UPC的子类别**: 硬盘、显示器、内存、处理器、固态硬盘
- **UPC Exempt申请**: 需提供品牌授权文件、USPTO注册号、产品照片等

### AI增强描述
- **功能**: AI自动生成商品描述、要点和图片
- **限制**: 每天每个账户50次提交
- **步骤**:
  1. 选择'Create an item not listed in Newegg (AI New)'
  2. 提供制造商、属性、产品特点
  3. 点击Start生成描述
  4. 审查并应用

### 注意事项
- 国际版本商品需标注'International Version'
- California Proposition 65警告可选择添加或移除

## 更新商品
1. 登录Seller Portal
2. 点击Items → View Items
3. 找到要更新的商品
4. 点击Edit进行修改
5. 保存更改

## 批量更新功能
- 批量创建新商品
- 批量跟卖商品
- 批量更新商品内容（基本信息和子类目信息）
- 批量更新商品内容（基本信息）
- 批量更新价格和库存
- 批量创建变体
- 批量删除商品

## 价格管理
- 批量更新商品价格
- 批量更新运费
- 批量更新限购数量
- 批量更新激活状态
- 国际价格同步

## 库存管理
- 查看可用库存
- 更新可用库存
- 批量更新库存
- 库存警报设置

## 产品变体
- 创建单个商品变体
- 批量创建变体
- 批量设置组合
""",
    
    "orders": """---
module: orders
title: 订单管理
last_updated: 2026-07-21
---

# 订单管理

## 查看订单

### 步骤
1. 登录Seller Portal → 订单 → 订单列表
2. 使用搜索工具查找订单（Order#、Item#、Ship-to Name等）
3. 使用订单状态筛选：Payment Pending, Unshipped, Shipped, Cancelled, All Orders
4. 使用Fulfilled-by筛选：Shipped By Seller, Shipped by Newegg, All Orders

### 功能
- 订单详情查看
- 订单备注/标记
- 批量操作控件
- 导出订单（Excel格式）

## 发货

### 步骤
1. 在订单列表中查看未发货订单（Unshipped筛选）
2. 点击'发货'按钮
3. 选择运输承运商
4. 输入运输服务和追踪号
5. 点击'发货'确认

### 发货场景
- 场景1：单个包裹 - 所有商品装入一个包裹
- 场景2：单个包裹（部分发货）- 只发部分商品
- 场景3：多个包裹 - 不同商品分开发
- 场景4：多个包裹 - 同一商品分批发

### 注意事项
- **Newegg强烈建议2天内处理订单**
- 订单将在14天后自动作废（自2024年12月1日起生效7天）
- 信用卡重新授权失败会导致订单自动作废

## 购买运单
1. 在订单列表点击'购买运单'按钮
2. 设置包裹尺寸和重量
3. 选择运输服务
4. 点击'购买运单'按钮
5. 确认地址

### 注意事项
- Newegg将收取运单标签服务费用
- 如需作废运单，联系SBN@newegg.com

## 批量发货
1. 登录Seller Portal → 管理订单 → 批量发货订单
2. 下载未发货订单模板（Excel格式）
3. 在模板中填写发货信息（承运商、追踪号等）
4. 上传填写好的模板
5. 查看上传状态和历史

### 注意事项
- Newegg强烈建议2天内处理订单
- 订单将在14天后自动作废
- Newegg不接受已订购商品数量的部分发货
- 每个发货包裹都需要新的跟踪号码

## 多渠道订单
- **适用范围**: 仅适用于使用Newegg配送(SBN)服务的卖家
- **功能**: 通过Newegg为其他销售渠道（如Amazon、eBay等）完成订单

### 步骤
1. 登录Seller Portal → 订单 → 创建多渠道订单
2. 填写Newegg发货信息
3. 添加SBN商品到订单
4. 点击确认并创建订单
""",
    
    "rma": """---
module: rma
title: RMA退货处理
last_updated: 2026-07-21
---

# RMA退货处理

## RMA流程

### 类型
- 未收到商品（Item Not Received）
- 商品损坏（Item Damage）
- 其他RMA原因（Other RMA Reasons）

### 处理时间
- **卖家必须在2个工作日内处理RMA**
- 2个工作日内未处理，系统将自动退款给客户

## 创建RMA

### 步骤
1. 登录Seller Portal → 订单 → 订单列表
2. 选择'已发货'标签查看已开发票的订单
3. 输入订单号，点击'创建退货请求'按钮
4. 选择退货类型：退货与退款 或 更换
5. 输入退款或更换的基本信息
6. 选择将用于退货处理的商品
7. 提供退货原因以及额外信息
8. 点击'提交退货请求'

### 注意事项
- 补货手续费全部免除，无论退货原因或商品重量如何
- 卖家RMA编号可选填，用于客户RMA处理参考

## 无退货退款
- **说明**: 卖家可设置规则，允许客户保留商品并退款

### 规则因素
- 商品价格限制：单个商品的最高价值
- 退货订单限制：最高总退款金额

### 条件
- 退货订单限制必须等于或大于商品价格限制
- 限制设置超过$100需卖家确认
- 即时退货退款适用于除'未收到商品'外的所有原因

## Marketplace Guarantee

### 适用条件
- 商品未收到、损坏、缺陷或与描述不符
- 买家在收到商品15天内通知卖家
- 买家按退货政策退回商品
- 卖家未退款

### 处理时间
- Newegg将在1-2周内批准或拒绝请求

### 卖家责任
- 管理和支持买家订单
- 处理发货、客服、换货和退货
- 2个工作日内响应买家
""",
    
    "promotion": """---
module: promotion
title: 促销活动
last_updated: 2026-07-21
---

# 促销活动

## 活动类型
1. Lightning Deal（闪购）
2. Spotlight Sale（聚光灯促销）
3. Email促销
4. WMT Flash Deal
5. BBY DOTD

## 提交流程

### 步骤
1. 登录Seller Portal → 营销 → 活动
2. 查看符合条件的活动
3. 点击'注册'添加商品
4. 填写活动信息（价格、库存等）
5. 提交审核

### 注意事项
- 提前2周提报
- 价格要有竞争力
- 库存要充足
- 注意活动时间

## 活动管理
- 查看活动状态
- 管理已注册产品
- 查看活动每日销量

## 折扣设置
- 单品折扣活动
- 批量创建单品折扣
- 创建折扣码
""",
    
    "messages": """---
module: messages
title: 消息管理
last_updated: 2026-07-21
---

# 消息管理

## 消息3.0

### 功能
通过捕获订单信息的新功能与Newegg客户互动

### 访问方式
- Seller Portal → 左上角列表图标 → 消息

### 可用平台
- Newegg.com
- Neweggbusiness.com
- Newegg.ca

### UI功能
1. 客户消息框摘要 - 自动根据内容、响应截止日期和垃圾邮件风险对消息分类
2. 消息列表 - 可标记为'未读'或'已标记'
3. 消息正文 - 显示消息历史记录
4. 客户绩效指标 - 消息处理统计信息
5. 客户信息 - AOV、有效订单率、购买统计
6. 订单详情 - 订单相关信息、退货详情、评论和索赔
7. 消息模板 - 快速响应常见问题

### 筛选功能
- 按日期筛选
- 需要回复
- 已标星
- 未读

## 消息模板

### 功能
设置回复模板，高效响应客户消息

### 步骤
1. 点击'Use Template'图标
2. 点击'管理模板' → 'CREATE TEMPLATE'
3. 配置模板详情（template name、message body、placeholders/variables、template tags）
4. 点击'SAVE'按钮

### 支持变量
可使用占位符/变量自动填充订单信息
""",
    
    "analytics": """---
module: analytics
title: 报表分析
last_updated: 2026-07-21
---

# 报表分析

## 销售仪表盘

### 访问方式
- Seller Portal → 报表 → Sales Dashboard

### 适用范围
- Elite会员

### 核心指标
- Sales（销售额）- 商品单价×数量
- Orders Sold（订单数）
- Avg. Units Sold Per Order（每单平均件数）
- Avg. Unit Price（平均单价）
- Avg. Order Amount（平均客单价）
- Page Views（商品页面浏览量）
- Sessions（访问次数）
- Order Session Percentage（订单转化率）
- Unit Session Percentage（件数转化率）
- Units Refunded（退款件数）
- Refund Rate（退款率）

### 日期范围
Today / WTD / MTD / YTD / Specify Date / Custom

### 筛选
Shipped By（All / SBN / SBS）

## 按日期销售和流量

### 访问方式
- Seller Portal → 报表 → Sales and Traffic by Date

### 分组方式
By Day / By Week / By Month

### 日期范围
Last 7/30/90 Days / Last 1/2 Years / 自定义

### 功能
支持CSV下载、图表展示、指标添加

## 按商品销售和流量

### 访问方式
- Seller Portal → 报表 → Sales and Traffic by Item

### 核心字段
- Item# / Seller Part# / Title
- Orders Sold / Units Sold / Sales
- Sessions / Session Percentage
- Unit Session Percentage
- Page Views / Page View Percentage

## 其他报表
- 查看销售额: Seller Portal → 报表 → 查看销售额
- 收支管理报表: Seller Portal → 报表 → 收支管理报表
- 佣金费率: Seller Portal → 报表 → 佣金费率
- 商品报表: Seller Portal → 报表 → 商品报表
- 作废订单报表: Seller Portal → 报表 → 作废订单报表
- 退货报表: Seller Portal → 报表 → 退货报表
- 订单分布报表: Seller Portal → 报表 → 订单分布报表
""",
    
    "advertising": """---
module: advertising
title: 广告推广
last_updated: 2026-07-21
---

# 广告推广

## 产品推广(Sponsored Products)

### 说明
关键词定位的搜索广告，客户点击时收费（CPC）

### 访问
- Seller Portal → Marketing → Sponsored Ads → 创建活动 → Sponsored Products

### 可用平台
- Newegg.com
- Newegg.ca

### 费用
每周一从付款余额扣费，无余额则从信用卡扣

### 创建步骤
1. Seller Portal → Marketing → Sponsored Ads → 创建活动 → Sponsored Products → CONTINUE
2. 填写活动设置：活动名称、开始/结束日期、每日预算、月度预算
3. 创建广告组：添加要推广的商品
4. 管理关键词定位
5. 点击SAVE完成

### 关键词定位类型

#### 自动定向
- 相似匹配 - 与商品密切相关的搜索词
- 宽松匹配 - 松散相关的搜索词
- 替代品 - 替代商品的搜索词
- 配件 - 互补商品的搜索词

#### 手动定向
- 广泛匹配 - 包含所有关键词，顺序不限
- 精确匹配 - 完全匹配关键词序列
- 短语匹配 - 包含确切短语

#### 产品定向
- 选择特定商品/类别/品牌
- 可细化到品牌、价格范围、egg评级

#### 否定关键词
指定不希望广告出现的关键词

### 出价选项
- Set default bid - 所有匹配类型统一出价
- Set bids for targeting group - 每种匹配类型单独出价

### 核心指标
- ACOS - 广告费用占比（支出/归因销售额）
- CPC - 每次点击费用
- CR - 转化率（订单数/点击数）
- CTR - 点击率（点击次数/展示次数）
- 展示次数、点击次数、订单数

### 注意
月度预算上限：整月最高支出，永远不会超出

## 头条推广(Sponsored Headlines)
品牌头条广告，在搜索结果顶部展示

## 视频推广(Sponsored Video)
视频广告，在搜索结果中展示视频内容

## 展示型推广(Sponsored Display)
展示广告，在商品详情页和搜索结果中展示

## 直播推广
直播中展示推广商品

## 站外广告(Offsite Ads)
- **说明**: Newegg自动投放到第三方网站的广告
- **特点**: 自动优化，按CPC收费
""",
    
    "sbn": """---
module: sbn
title: SBN管理
last_updated: 2026-07-21
---

# SBN管理

## 自动化多渠道订单拣配
- **说明**: 自动处理SBN的多渠道订单
- **功能**: 自动拣货、包装、发货

## 新蛋仓库货件列表
- **说明**: 管理发送到Newegg仓库的货件

### 步骤
1. 创建货件计划
2. 打印货件标签
3. 发送货件到仓库
4. 查看入仓状态

## 库存警报
- **说明**: 当SBN库存低于阈值或缺货时发送警报
- **设置**: 可设置最低库存阈值

## 库存分析
查看每日库存历史记录和分析

## 入仓报表
查看货件入仓历史记录

## 换货报表
查看换货处理报告
""",
    
    "store": """---
module: store
title: 店铺管理
last_updated: 2026-07-21
---

# 店铺管理

## 非精英会员店铺
- **功能**: 基本店铺设置和管理
- **访问**: Seller Portal → 店铺

## 会员店铺
- **功能**: Elite会员专属高级店铺功能

### 特点
- 自定义店铺页面
- 品牌展示
- 促销活动展示
""",
    
    "performance": """---
module: performance
title: 卖家绩效
last_updated: 2026-07-21
---

# 卖家绩效

## 账户健康仪表板

### 访问方式
- Seller Portal → 绩效 → 账户健康

### 审查频率
每月审查一次

### 风险
连续两个审查期未达标可能失去销售权限

## 核心指标

### 订单绩效

#### 订单缺陷率
- **目标**: < 1%
- **公式**: 负面卖家评分率 + 未解决Marketplace Guarantee索赔率 + 拒付率
- **说明**: 负面评分=1或2 eggs

#### 退款率
- **目标**: < 5%
- **公式**: 退款订单总数 / 已开票订单总数

### 发货绩效

#### 预发货订单作废率
- **目标**: <= 5%
- **说明**: 卖家作废的订单比例

#### 准时订单履约率
- **目标**: >= 95%
- **说明**: 2个工作日内发货（仅SBS订单）

#### 准时订单交付率
- **目标**: >= 90%
- **说明**: 在截止日期前送达（仅SBS订单）

#### 有效追踪号码比例
- **目标**: >= 98%
- **说明**: 承运商确认的可追踪包裹比例

### 消息性能

#### 准时响应率
- **目标**: >= 95%
- **说明**: 48小时内回复客户消息

### 店铺评分

#### 卖家评级
- **目标**: >= 3 eggs
- **说明**: 基于客户评价

## 店铺评价
- **说明**: 查看客户对店铺的评分和评价
- **影响**: 影响订单缺陷率和搜索排名
""",
    
    "faq": """---
module: faq
title: 常见问题
last_updated: 2026-07-21
---

# 常见问题

## 物流问题
- **问题**: 物流延迟、丢件、损坏
- **解决方案**:
  1. 及时更新物流信息
  2. 与物流公司沟通
  3. 必要时补发或退款

## 产品问题
- **问题**: 质量问题、功能故障、与描述不符
- **解决方案**:
  1. 确认问题原因
  2. 提供换货或退款
  3. 改进产品质量

## 价格问题
- **问题**: 价格争议、价格保护
- **解决方案**:
  1. 解释定价策略
  2. 提供价格证明
  3. 必要时调整价格

## 账号问题
- **问题**: 账号被封、权限问题
- **解决方案**:
  1. 联系客服
  2. 提供相关证明
  3. 申诉处理
""",
    
    "policies": """---
module: policies
title: 平台政策
last_updated: 2026-07-21
---

# 平台政策

## 禁止行为
- 虚假交易
- 刷单炒信
- 恶意评价
- 侵犯知识产权

## 违禁品
- 枪支武器
- 毒品
- 假冒伪劣产品
- 侵权商品

## 处罚措施
- 警告
- 罚款
- 暂停账号
- 永久封禁

## 商品政策
- 网站短标题政策和指南
- 产品描述政策和指南
- 产品图片、视频政策和指南
- 搜索引擎优化SEO指南
""",
    
    "b2b": """---
module: b2b
title: B2B特殊政策
last_updated: 2026-07-21
---

# B2B特殊政策

## 特点
- 面向企业客户
- 批量采购
- 定制化服务
- 更高的客单价

## 优势
- 客单价高（$508 vs B2C $129）
- 订单量大
- 长期合作
- 利润空间大

## 操作
- B2B Deal Portal提交促销
- 批量订单处理
- 企业客户沟通
""",
    
    "ca": """---
module: ca
title: CA站点特殊政策
last_updated: 2026-07-21
---

# CA站点特殊政策

## 特点
- 面向加拿大市场
- 本地化运营
- 加元结算

## 优势
- 竞争相对较小
- 本地化优势
- 物流成本可控

## 注意事项
- 需要符合加拿大法规
- 注意关税和税费
- 本地化商品描述
""",
    
    "reply": """---
module: reply
title: AI回复建议模板
last_updated: 2026-07-21
---

# AI回复建议模板

## 开场白
- 您好，感谢您联系Newegg卖家支持。
- 您好，我是Newegg的运营支持人员。
- 您好，感谢您的耐心等待。

## 物流问题回复
- 关于物流延迟的问题，我们已经为您查询了物流状态。预计XX天内送达。
- 非常抱歉给您带来不便。我们已经联系物流公司加急处理。
- 您的订单已经发货，物流单号是XXXXX，预计XX天内送达。

## 产品问题回复
- 关于产品质量问题，我们深表歉意。请提供产品照片，我们会为您处理。
- 我们可以为您安排换货或退款，请问您希望如何处理？
- 我们会将问题反馈给供应商，确保产品质量。

## 价格问题回复
- 关于价格问题，我们的定价基于市场行情和成本考虑。
- 如果您发现更低价格，请提供链接，我们会核实并调整。
- 我们提供价格保护服务，请放心购买。

## 账号问题回复
- 关于账号问题，我们会为您查询具体原因。
- 请提供相关证明材料，我们会协助您处理。
- 我们会尽快为您解决账号问题。

## 结束语
- 如有其他问题，请随时联系我们。
- 祝您生意兴隆！
- 感谢您的支持与合作。
""",
}

def main():
    """创建所有MD文件"""
    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 创建每个模块的MD文件
    for module_name, content in MODULES.items():
        file_path = os.path.join(DATA_DIR, f"{module_name}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 创建: {module_name}.md")
    
    print(f"\n共创建 {len(MODULES)} 个MD文件")

if __name__ == "__main__":
    main()
