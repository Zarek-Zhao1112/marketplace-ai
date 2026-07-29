"""
知识库加载器 - 从MD文件加载知识库内容
支持YAML frontmatter + Markdown内容格式
"""
import os
import re
import yaml
from typing import Dict, Any, Optional, List

# 知识库数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def parse_md_file(file_path: str) -> Dict[str, Any]:
    """解析MD文件，提取YAML frontmatter和内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取YAML frontmatter
    frontmatter = {}
    body = content
    
    # 匹配 --- 包围的YAML内容
    yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(yaml_pattern, content, re.DOTALL)
    
    if match:
        yaml_content = match.group(1)
        body = match.group(2)
        try:
            frontmatter = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError:
            frontmatter = {}
    
    # 解析Markdown内容为结构化数据
    structured_data = parse_markdown_body(body)
    
    # 合并frontmatter和内容
    result = {**frontmatter, **structured_data}
    
    return result

def parse_markdown_body(body: str) -> Dict[str, Any]:
    """解析Markdown正文为结构化数据"""
    result = {}
    current_section = None
    current_content = []

    lines = body.split("\n")

    for line in lines:
        # 检测标题
        if line.startswith("# "):
            # 一级标题，跳过（通常是文件标题）
            continue
        elif line.startswith("## "):
            # 二级标题，作为section
            if current_section and current_content:
                # 检查是否是列表格式（统计以 - 或 #### 开头的行数）
                list_count = sum(1 for line in current_content if line.strip() and (line.strip().startswith("- ") or line.strip().startswith("#### ")))
                is_list = list_count > 1  # 至少有2个列表项才认为是列表
                if is_list:
                    # 转换为列表（移除空行）
                    result[current_section] = [line.strip() for line in current_content if line.strip()]
                else:
                    result[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        elif line.startswith("### "):
            # 三级标题，作为子section
            if current_section:
                subsection = line[4:].strip()
                current_content.append(f"\n### {subsection}")
        else:
            current_content.append(line)

    # 保存最后一个section
    if current_section and current_content:
        # 检查是否是列表格式（统计以 - 或 #### 开头的行数）
        list_count = sum(1 for line in current_content if line.strip() and (line.strip().startswith("- ") or line.strip().startswith("#### ")))
        is_list = list_count > 1  # 至少有2个列表项才认为是列表
        if is_list:
            # 转换为列表（移除空行）
            result[current_section] = [line.strip() for line in current_content if line.strip()]
        else:
            result[current_section] = "\n".join(current_content).strip()

    return result

def load_module(module_name: str) -> Optional[Dict[str, Any]]:
    """加载指定模块的知识库"""
    file_path = os.path.join(DATA_DIR, f"{module_name}.md")
    
    if not os.path.exists(file_path):
        return None
    
    return parse_md_file(file_path)

def load_all_modules() -> Dict[str, Dict[str, Any]]:
    """加载所有模块"""
    modules = {}
    
    if not os.path.exists(DATA_DIR):
        return modules
    
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".md"):
            module_name = filename[:-3]  # 去掉.md后缀
            modules[module_name] = load_module(module_name)
    
    return modules

def search_in_module(module_data: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """在模块中搜索关键词"""
    results = []
    query_lower = query.lower()
    
    for key, value in module_data.items():
        if isinstance(value, str) and query_lower in value.lower():
            results.append({
                "key": key,
                "content": value[:200] + "..." if len(value) > 200 else value
            })
    
    return results

# 兼容旧接口的映射
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
}

def get_knowledge_by_category(category: str) -> Optional[Dict[str, Any]]:
    """按分类获取知识库内容（兼容旧接口）"""
    module_name = MODULE_MAPPING.get(category, category)
    return load_module(module_name)

def search_knowledge_by_query(query: str) -> List[Dict[str, Any]]:
    """搜索知识库（兼容旧接口）"""
    results = []
    all_modules = load_all_modules()
    
    for module_name, module_data in all_modules.items():
        if module_data:
            module_results = search_in_module(module_data, query)
            for result in module_results:
                results.append({
                    "category": module_name,
                    "key": result["key"],
                    "content": result["content"]
                })
    
    return results

if __name__ == "__main__":
    # 测试加载器
    print("测试知识库加载器...")
    
    # 加载所有模块
    modules = load_all_modules()
    print(f"加载了 {len(modules)} 个模块")
    
    # 测试按分类获取
    platform_data = get_knowledge_by_category("platform")
    if platform_data:
        print(f"platform模块: {list(platform_data.keys())}")
    
    # 测试搜索
    results = search_knowledge_by_query("RMA")
    print(f"搜索'RMA'找到 {len(results)} 条结果")
