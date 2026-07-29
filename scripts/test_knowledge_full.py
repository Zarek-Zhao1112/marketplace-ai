"""完整测试知识库"""
import sys
sys.path.insert(0, '.')

from src.knowledge import get_knowledge, search_knowledge

print('=== Newegg Seller Academy 知识库测试 ===')
print()

# 测试1: 获取所有模块
print('测试1: 获取所有模块')
all_modules = get_knowledge()
print(f'  模块数量: {len(all_modules)}')
print(f'  模块列表: {list(all_modules.keys())}')
print()

# 测试2: 按分类获取
print('测试2: 按分类获取')
test_modules = ['platform', 'registration', 'items', 'orders', 'rma', 
                'account', 'pricing', 'volume_discount', 'brand', 
                'aplus_content', 'global_shipping', 'integration', 'seller_programs']
for module in test_modules:
    data = get_knowledge(module)
    status = 'OK' if data else 'FAIL'
    print(f'  {module}: {status}')
print()

# 测试3: 搜索功能
print('测试3: 搜索功能')
search_terms = ['RMA', '价格保护', '阶梯价格', 'A+页面', '全球销售']
for term in search_terms:
    results = search_knowledge(term)
    print(f'  搜索"{term}": {len(results)}条结果')
print()

# 测试4: 查看具体内容
print('测试4: 查看具体内容')
platform_data = get_knowledge('platform')
if platform_data:
    print('  platform模块:')
    print(f'    内容键: {list(platform_data.keys())[:5]}')
print()

pricing_data = get_knowledge('pricing')
if pricing_data:
    print('  pricing模块:')
    for key in list(pricing_data.keys())[:3]:
        print(f'    - {key}')
print()

print('=== 测试完成 ===')
