"""
知识库模块
提供Newegg Seller Academy知识库和运营经验库的访问接口
"""

# 导出知识库接口
from .newegg_seller_academy import (
    get_knowledge,
    search_knowledge,
    get_knowledge_by_category,
    search_knowledge_by_query,
)

# 导出MD文件加载器（如果需要直接访问）
try:
    from .loader import (
        load_module,
        load_all_modules,
    )
except ImportError:
    pass

# 导出经验库
try:
    from .experience_library import ExperienceLibrary
except ImportError:
    pass

__all__ = [
    "get_knowledge",
    "search_knowledge",
    "get_knowledge_by_category",
    "search_knowledge_by_query",
    "load_module",
    "load_all_modules",
    "ExperienceLibrary",
]
