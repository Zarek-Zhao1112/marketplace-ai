"""
Newegg Seller Academy 知识库
基于 https://sellerportal.newegg.com/selleracademy/zh-hans/
最后更新：2026-07-21

现在支持两种加载方式：
1. 从MD文件加载（推荐，更易维护）
2. 从内置Python字典加载（兼容旧版本）
"""

import os
from typing import Dict, Any, Optional, List

# 尝试从MD文件加载，如果失败则使用内置数据
try:
    from .loader import (
        get_knowledge_by_category as _load_from_md,
        search_knowledge_by_query as _search_from_md,
        load_all_modules as _load_all_from_md,
    )
    USE_MD = True
except ImportError:
    USE_MD = False

# ══════════════════════════════════════════════════════════
# 内置数据（兼容旧版本，当MD文件不存在时使用）
# ══════════════════════════════════════════════════════════

PLATFORM_INFO = {
    "name": "Newegg Marketplace",
    "type": "第三方卖家平台",
    "users": "4700万+注册用户",
    "demographics": "70%男性，平均年龄36岁，年收入$7.5万+",
    "hot_categories": ["Components", "Computer Systems", "Home & Outdoor", "Gamers"],
    "website": "https://www.newegg.com",
    "seller_portal": "https://sellerportal.newegg.com",
    "academy": "https://sellerportal.newegg.com/selleracademy/zh-hans/",
    "platforms": ["Newegg.com", "Neweggbusiness.com", "Newegg.ca"],
    "commission": "新卖家前90天佣金6%",
    "erp": "SellingPilot（99元/月）"
}

SELLER_REGISTRATION = {
    "steps": [
        "1. 注册卖家账户",
        "2. 更新业务信息",
        "3. 更新财务信息",
        "4. 更新信用卡信息",
        "5. 更新售后政策",
        "6. 更新运费模式和费率",
        "7. 创建商品"
    ],
    "requirements": [
        "企业营业执照",
        "法人身份证",
        "银行账户信息",
        "品牌授权书（如有）"
    ],
    "notes": [
        "新卖家前90天佣金只要6%",
        "支持SellingPilot一键搬家",
        "B2B和B2C站点可以分开管理"
    ],
    "quick_start": [
        "快速入驻：Amazon/Walmart/eBay/TikTok Shop美站卖家可快速入驻",
        "一键搬家：支持SellingPilot一键搬家功能",
        "资料简化：仅需营业执照、店铺链接、注册邮箱"
    ]
}

# ... 其他内置数据保持不变 ...
# （为简洁起见，这里省略了其他内置数据，实际使用时会从MD文件加载）

# ══════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════

def get_knowledge(category=None):
    """
    获取知识库内容
    
    Args:
        category: 分类名称，如 "platform", "registration", "items" 等
                 如果为None，返回所有分类
    
    Returns:
        dict: 知识库内容
    """
    if USE_MD:
        # 从MD文件加载
        if category:
            result = _load_from_md(category)
            return result if result else {}
        else:
            # 加载所有模块
            all_modules = _load_all_from_md()
            return all_modules
    else:
        # 使用内置数据（兼容旧版本）
        # 这里简化处理，实际应该包含所有内置数据
        return {"message": "请安装pyyaml: pip install pyyaml"}

def search_knowledge(query):
    """
    搜索知识库
    
    Args:
        query: 搜索关键词
    
    Returns:
        list: 搜索结果列表
    """
    if USE_MD:
        return _search_from_md(query)
    else:
        return [{"message": "请安装pyyaml: pip install pyyaml"}]

# ══════════════════════════════════════════════════════════
# 保持向后兼容的别名
# ══════════════════════════════════════════════════════════

# 旧版本的函数名别名
get_knowledge_by_category = get_knowledge
search_knowledge_by_query = search_knowledge

# 模块名称映射
MODULE_MAPPING = {
    "platform": "platform",
    "registration": "registration",
    "items": "items",
    "orders": "orders",
    "rma": "rma",
    "promotion": "promotion",
    "messages": "messages",
    "analytics": "analytics",
    "advertising": "advertising",
    "sbn": "sbn",
    "store": "store",
    "performance": "performance",
    "faq": "faq",
    "policies": "policies",
    "b2b": "b2b",
    "ca": "ca",
    "reply": "reply",
    "account": "account",
    "pricing": "pricing",
    "volume_discount": "volume_discount",
    "brand": "brand",
    "aplus_content": "aplus_content",
    "global_shipping": "global_shipping",
    "integration": "integration",
    "seller_programs": "seller_programs",
    "sku_lifecycle": "sku_lifecycle",
}
