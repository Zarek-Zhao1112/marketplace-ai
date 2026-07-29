"""测试知识库迁移是否成功"""
import sys
sys.path.insert(0, '.')

from src.knowledge.newegg_seller_academy import get_knowledge, search_knowledge

def main():
    print("=== 知识库迁移测试 ===")
    print()
    
    # 测试1: 按分类获取
    print("测试1: 按分类获取")
    platform_data = get_knowledge("platform")
    if platform_data:
        print("  ✅ platform模块加载成功")
        print("  内容键:", list(platform_data.keys())[:5])
    else:
        print("  ❌ platform模块加载失败")
    print()
    
    # 测试2: 获取所有模块
    print("测试2: 获取所有模块")
    all_data = get_knowledge()
    if all_data:
        print("  ✅ 所有模块加载成功")
        print("  模块数量:", len(all_data))
        print("  模块列表:", list(all_data.keys()))
    else:
        print("  ❌ 模块加载失败")
    print()
    
    # 测试3: 搜索功能
    print("测试3: 搜索功能")
    results = search_knowledge("RMA")
    if results:
        print("  ✅ 搜索功能正常")
        print("  搜索'RMA'找到", len(results), "条结果")
    else:
        print("  ❌ 搜索功能异常")
    print()
    
    # 测试4: 验证数据完整性
    print("测试4: 验证数据完整性")
    required_modules = ["platform", "registration", "items", "orders", "rma", 
                       "promotion", "messages", "analytics", "advertising", 
                       "sbn", "store", "performance", "faq", "policies", 
                       "b2b", "ca", "reply"]
    
    missing = []
    for module in required_modules:
        data = get_knowledge(module)
        if not data:
            missing.append(module)
    
    if not missing:
        print("  ✅ 所有17个模块都存在")
    else:
        print("  ❌ 缺少模块:", missing)
    print()
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    main()
