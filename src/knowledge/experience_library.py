"""
运营经验库 - 从已解决的运营问题中学习，积累领域知识，逐步成为运营专员。
支持关键词匹配和 AI 语义检索两种方式查找历史案例。
"""
import pandas as pd
import json
import os
import re
from datetime import datetime
from src.config.settings import ISSUES_PATH, EXPERIENCE_PATH
from src.knowledge.newegg_seller_academy import get_knowledge, search_knowledge


class ExperienceLibrary:
    """跨境电商运营经验库"""

    def __init__(self, issues_path=None,
                 experience_path=None):
        self.issues_path = issues_path or ISSUES_PATH
        self.experience_path = experience_path or EXPERIENCE_PATH
        self.knowledge_base = self._load()

    # ── 持久化 ──────────────────────────────────────────────
    def _load(self):
        if os.path.exists(self.experience_path):
            with open(self.experience_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"cases": [], "reply_pairs": [], "stats": {}, "last_updated": None}

    def _save(self):
        os.makedirs(os.path.dirname(self.experience_path), exist_ok=True)
        self.knowledge_base["last_updated"] = datetime.now().isoformat()
        with open(self.experience_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)

    # ── 重建经验库 ──────────────────────────────────────────
    def rebuild(self):
        """从 issues.xlsx 中提取所有已解决案例，重建经验库"""
        if not os.path.exists(self.issues_path):
            print(f"⚠️ 未找到 issues 文件：{self.issues_path}")
            return 0

        df = pd.read_excel(self.issues_path, engine="openpyxl")
        resolved = df[df['处理状态'].isin(['已解决', '已处理', '已归档'])]

        cases = []
        for _, row in resolved.iterrows():
            desc = str(row.get('问题描述', '')).strip()
            solution = str(row.get('解决方案', '')).strip()
            # 跳过无效记录
            if not desc or desc == 'nan' or not solution or solution == 'nan':
                continue

            cases.append({
                "问题类型": str(row.get('问题类型', '未知')),
                "问题描述": desc,
                "解决方案": solution,
                "处理过程": str(row.get('处理过程', '')),
                "卖家名称": str(row.get('卖家名称', '')),
                "时间": str(row.get('时间', '')),
            })

        # 统计各类型分布
        type_counts = {}
        for c in cases:
            t = c['问题类型']
            type_counts[t] = type_counts.get(t, 0) + 1

        self.knowledge_base = {
            "cases": cases,
            "stats": {
                "total_resolved": len(cases),
                "by_type": type_counts,
                "last_rebuilt": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            "last_updated": datetime.now().isoformat()
        }
        self._save()
        return len(cases)

    # ── 关键词搜索 ──────────────────────────────────────────
    def search(self, query: str, problem_type: str = None, top_k: int = 5):
        """基于关键词匹配搜索相似案例（快速，无需 API）"""
        cases = self.knowledge_base.get("cases", [])
        if not cases:
            return []

        if problem_type:
            cases = [c for c in cases if c['问题类型'] == problem_type]

        keywords = set(query.lower().split())
        scored = []
        for case in cases:
            text = (case['问题描述'] + ' ' + case['解决方案']).lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, case))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [case for _, case in scored[:top_k]]

    # ── AI 语义搜索 ─────────────────────────────────────────
    def search_with_ai(self, client, model_endpoint, query: str, top_k: int = 3):
        """使用 AI 进行语义相似度搜索，找到最相关的历史案例"""
        cases = self.knowledge_base.get("cases", [])
        if not cases:
            return []

        # 案例太多时只取最近 50 条
        pool = cases[-50:] if len(cases) > 50 else cases

        cases_text = "\n---\n".join([
            f"[案例{i+1}] 类型:{c['问题类型']} | "
            f"描述:{c['问题描述'][:100]} | "
            f"方案:{c['解决方案'][:200]}"
            for i, c in enumerate(pool)
        ])

        try:
            response = client.chat.completions.create(
                model=model_endpoint,
                messages=[{
                    "role": "system",
                    "content": (
                        "你是运营经验库检索助手。根据用户的新问题，从历史案例库中找出最相关的已解决案例，"
                        "按相关度排序。只输出案例编号（逗号分隔），如：1,3,5。没有相关案例则输出：无"
                    )
                }, {
                    "role": "user",
                    "content": f"新问题：{query}\n\n历史案例库：\n{cases_text}"
                }],
                temperature=0.1,
                max_tokens=50
            )
            result = response.choices[0].message.content.strip()
        except Exception:
            return []

        if result == "无" or not result:
            return []

        try:
            indices = [int(x.strip()) - 1 for x in result.split(',') if x.strip().isdigit()]
            return [pool[i] for i in indices if 0 <= i < len(pool)][:top_k]
        except (ValueError, IndexError):
            return []

    # ── 格式化上下文 ────────────────────────────────────────
    def format_context(self, similar_cases):
        """将相似案例格式化为 AI 可用的提示词上下文"""
        if not similar_cases:
            return ""

        lines = ["\n═══ 📚 历史相似案例参考 ═══"]
        for i, case in enumerate(similar_cases):
            lines.append(f"【参考案例 {i+1}】")
            lines.append(f"  问题类型：{case['问题类型']}")
            lines.append(f"  问题描述：{case['问题描述'][:200]}")
            lines.append(f"  解决方案：{case['解决方案'][:300]}")
            if case.get('处理过程') and case['处理过程'] != 'nan':
                lines.append(f"  处理过程：{case['处理过程'][:200]}")
            lines.append("")
        return "\n".join(lines)

    # ── 概览 ────────────────────────────────────────────────
    def get_summary(self):
        """获取经验库概览信息"""
        stats = self.knowledge_base.get("stats", {})
        return {
            "已解决问题总数": stats.get("total_resolved", 0),
            "问题类型分布": stats.get("by_type", {}),
            "最后更新": stats.get("last_rebuilt", "从未重建"),
        }

    # ── 智能建议 ────────────────────────────────────────────
    def get_suggestion(self, client, model_endpoint, query: str):
        """给定一个新问题，生成综合建议（融合历史经验）"""
        # 先用关键词搜，再用 AI 精排
        keyword_matches = self.search(query, top_k=10)
        ai_matches = self.search_with_ai(client, model_endpoint, query, top_k=3)

        # 合并去重
        seen = set()
        merged = []
        for case in ai_matches + keyword_matches:
            key = case['问题描述'][:50]
            if key not in seen:
                seen.add(key)
                merged.append(case)
        merged = merged[:5]

        context = self.format_context(merged)

        try:
            response = client.chat.completions.create(
                model=model_endpoint,
                messages=[{
                    "role": "system",
                    "content": (
                        "你是跨境电商运营专家。根据历史经验库中的相似案例，"
                        "为当前新问题提供专业建议。要结合历史案例的解决方案，"
                        "给出具体、可操作的建议。\n\n"
                        "去AI化写作规则（必须遵守）：\n"
                        "1. 直接陈述事实，禁止使用'此外'、'至关重要'、'深入探讨'、'强调'、'增强'等AI高频词汇\n"
                        "2. 禁止三段式结构（如'高效、专业和可靠'）\n"
                        "3. 句子长度要有变化，不要每句都差不多长\n"
                        "4. 用具体数据说话，不要用模糊形容词\n"
                        "5. 避免'不仅...而且...'等否定式排比\n"
                        "6. 语气要像真人写的建议，不要像AI模板"
                    )
                }, {
                    "role": "user",
                    "content": f"新问题：{query}\n{context}\n\n请给出综合建议（含具体步骤）："
                }],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"生成建议失败：{e}"

    # ════════════════════════════════════════════════════════
    #  📝 回复模式学习（卖家说 → 运营回）
    # ════════════════════════════════════════════════════════

    def learn_reply_from_chat(self, client, model_endpoint, chat_transcript: str):
        """从一段完整的聊天记录中提取「卖家消息 → 运营回复」的对话对"""
        if not chat_transcript.strip():
            return 0

        try:
            response = client.chat.completions.create(
                model=model_endpoint,
                messages=[{
                    "role": "system",
                    "content": (
                        "你是一个对话分析助手。从下面的聊天记录中，提取「卖家说的话 → 运营的回复」的对话对。\n"
                        "只提取运营有实质回复的对话对，跳过问候、表情、单纯的'好的''收到'等无实质内容的回复。\n"
                        "严格按照以下 JSON 数组格式输出，不要添加任何其他内容：\n"
                        '[{"seller_msg": "卖家说的原话", "operator_reply": "运营的回复原话", "context": "对话类型"}]\n'
                        "对话类型从以下选：产品问题、物流问题、售后问题、结算问题、日常沟通、其他"
                    )
                }, {
                    "role": "user",
                    "content": f"聊天记录：\n{chat_transcript}"
                }],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            data = json.loads(raw)

            # 兼容不同的 JSON 包裹格式
            pairs = data if isinstance(data, list) else None
            if pairs is None and isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        pairs = v
                        break
                if pairs is None:
                    pairs = []
        except Exception as e:
            print(f"⚠️ AI 提取回复对失败：{e}")
            return 0

        if not pairs:
            return 0

        new_count = 0
        existing = self.knowledge_base.get("reply_pairs", [])
        seen_keys = {(p.get("seller_message", "")[:80], p.get("operator_reply", "")[:80]) for p in existing}

        for pair in pairs:
            sm = str(pair.get("seller_msg", "")).strip()
            opr = str(pair.get("operator_reply", "")).strip()
            if not sm or not opr or len(sm) < 4 or len(opr) < 4:
                continue
            key = (sm[:80], opr[:80])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            existing.append({
                "seller_message": sm,
                "operator_reply": opr,
                "context": str(pair.get("context", "日常沟通")),
                "time": datetime.now().strftime('%Y-%m-%d %H:%M'),
            })
            new_count += 1

        self.knowledge_base["reply_pairs"] = existing
        self._update_stats()
        self._save()
        return new_count

    def search_replies(self, seller_message: str, top_k: int = 5):
        """搜索与卖家消息最相似的历史对话 → 返回对应的运营回复"""
        pairs = self.knowledge_base.get("reply_pairs", [])
        if not pairs:
            return []

        keywords = set(seller_message.lower().split())
        scored = []
        for pair in pairs:
            text = pair["seller_message"].lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, pair))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [pair for _, pair in scored[:top_k]]

    def search_replies_with_ai(self, client, model_endpoint, seller_message: str, top_k: int = 3):
        """AI 语义搜索最匹配的回复模式"""
        pairs = self.knowledge_base.get("reply_pairs", [])
        if not pairs:
            return []

        pool = pairs[-30:] if len(pairs) > 30 else pairs

        pairs_text = "\n---\n".join([
            f"[{i+1}] 卖家说：{p['seller_message'][:100]} → 运营回：{p['operator_reply'][:150]}"
            for i, p in enumerate(pool)
        ])

        try:
            response = client.chat.completions.create(
                model=model_endpoint,
                messages=[{
                    "role": "system",
                    "content": (
                        "你是对话检索助手。根据卖家新消息，从历史对话对中找出最相似的（最多3个），"
                        "按相关度排序。只输出编号（逗号分隔），如：1,3,5。没有相关则输出：无"
                    )
                }, {
                    "role": "user",
                    "content": f"卖家新消息：{seller_message}\n\n历史对话对：\n{pairs_text}"
                }],
                temperature=0.1,
                max_tokens=50
            )
            result = response.choices[0].message.content.strip()
        except Exception:
            return []

        if result == "无" or not result:
            return []

        try:
            indices = [int(x.strip()) - 1 for x in result.split(',') if x.strip().isdigit()]
            return [pool[i] for i in indices if 0 <= i < len(pool)][:top_k]
        except (ValueError, IndexError):
            return []

    def suggest_reply_web(self, api_key: str, model_endpoint: str, seller_message: str):
        """根据历史回复模式生成回复建议（Web 模式，使用原始 HTTP 请求）"""
        import requests as req

        def web_caller(msgs, temp, max_tok):
            resp = req.post(
                "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {api_key}"},
                json={"model": model_endpoint, "messages": msgs,
                       "temperature": temp, "max_tokens": max_tok},
                timeout=90
            )
            resp.raise_for_status()

            # 返回一个模拟的 SDK response 对象
            class FakeChoice:
                class Msg:
                    def __init__(self, c): self.content = c
                def __init__(self, c): self.message = self.Msg(c)
            class FakeResp:
                def __init__(self, c): self.choices = [FakeChoice(c)]

            raw = resp.json()["choices"][0]["message"]["content"]
            return FakeResp(raw)

        return self._do_suggest_reply(web_caller, seller_message)

    def _parse_performance_metrics(self, metrics_list):
        """解析核心指标列表，提取绩效信息"""
        if not isinstance(metrics_list, list):
            return ""

        performance_info = {}
        current_category = None

        for line in metrics_list:
            line = line.strip()
            if not line:
                continue

            # 检测三级标题（绩效分类）
            if line.startswith("### "):
                current_category = line[3:].strip()
                performance_info[current_category] = {}
                continue

            # 检测四级标题（具体指标）
            if line.startswith("#### "):
                metric_name = line[4:].strip()
                performance_info[current_category][metric_name] = []
                continue

            # 提取列表项（目标、公式、说明）
            if line.startswith("- ") and current_category and metric_name in performance_info[current_category]:
                metric_info = {}
                parts = line[2:].split("：", 1)  # 分割"键：值"
                if len(parts) == 2:
                    key, value = parts
                    metric_info[key] = value
                performance_info[current_category][metric_name].append(metric_info)

        # 构建显示文本
        result = []
        for category, metrics in performance_info.items():
            result.append(f"\n#### {category}")
            for metric_name, details in metrics.items():
                for detail in details:
                    result.append(f"- {metric_name}: 目标{detail.get('目标', '')}（{detail.get('说明', '')}）")
        return "\n".join(result)

    def _parse_section_list(self, section_list, max_items=3):
        """解析包含三级标题和列表项的section列表"""
        if not isinstance(section_list, list):
            return ""

        result = []
        current_section = None

        for line in section_list[:50]:  # 限制最多50项
            line = line.strip()
            if not line:
                continue

            # 检测三级标题
            if line.startswith("### "):
                current_section = line[3:].strip()
                result.append(f"\n#### {current_section}")
                continue

            # 提取列表项
            if line.startswith("- ") and current_section:
                result.append(f"- {line[2:]}")
                if len(result) >= max_items * 2:  # 限制总行数
                    break

        return "\n".join(result)

    def _do_suggest_reply(self, api_caller, seller_message: str):
        """核心回复建议逻辑，通过 api_caller 解耦调用方式"""
        kw_matches = self.search_replies(seller_message, top_k=5)

        # 合并去重
        seen = set()
        merged = []
        for p in kw_matches:
            key = p["seller_message"][:80]
            if key not in seen:
                seen.add(key)
                merged.append(p)
        merged = merged[:5]

        # 构建历史参考
        history_text = ""
        if merged:
            history_lines = ["═══ 📚 历史相似对话参考 ═══"]
            for i, p in enumerate(merged):
                history_lines.append(f"卖家说：{p['seller_message'][:200]}")
                history_lines.append(f"运营回：{p['operator_reply'][:300]}")
                history_lines.append("")
            history_text = "\n".join(history_lines)

        stats = self.knowledge_base.get("stats", {})
        expertise_hint = ""
        if stats.get("total_resolved", 0) > 0:
            top_types = sorted(stats.get("by_type", {}).items(), key=lambda x: x[1], reverse=True)[:3]
            expertise_hint = f"你已处理过 {stats['total_resolved']} 个问题，最擅长：{', '.join(f'{t}({c}次)' for t, c in top_types)}。"

        # 获取Newegg Seller Academy知识库
        academy_knowledge = get_knowledge()
        reply_knowledge = academy_knowledge.get("reply", {})
        faq_knowledge = academy_knowledge.get("faq", {})
        perf_knowledge = academy_knowledge.get("performance", {})
        rma_knowledge = academy_knowledge.get("rma", {})
        orders_knowledge = academy_knowledge.get("orders", {})

        # 构建知识库提示
        knowledge_hint = ""
        if reply_knowledge:
            knowledge_hint = "\n\n## Newegg平台知识库\n"
            knowledge_hint += "### 开场白模板\n"
            for template in reply_knowledge.get("开场白", [])[:3]:
                knowledge_hint += f"- {template}\n"
            knowledge_hint += "\n### 物流问题回复模板\n"
            for template in reply_knowledge.get("物流问题回复", [])[:3]:
                knowledge_hint += f"- {template}\n"
            knowledge_hint += "\n### 产品问题回复模板\n"
            for template in reply_knowledge.get("产品问题回复", [])[:3]:
                knowledge_hint += f"- {template}\n"
            knowledge_hint += "\n### 价格问题回复模板\n"
            for template in reply_knowledge.get("价格问题回复", [])[:3]:
                knowledge_hint += f"- {template}\n"
            knowledge_hint += "\n### 账号问题回复模板\n"
            for template in reply_knowledge.get("账号问题回复", [])[:3]:
                knowledge_hint += f"- {template}\n"
            knowledge_hint += "\n### 结束语\n"
            for template in reply_knowledge.get("结束语", [])[:2]:
                knowledge_hint += f"- {template}\n"

        # 卖家绩效指标（回复时引用具体标准更有说服力）
        if perf_knowledge:
            metrics_list = perf_knowledge.get("核心指标", [])
            knowledge_hint += "\n### 卖家绩效指标（Newegg官方标准）\n"
            knowledge_hint += self._parse_performance_metrics(metrics_list)

        # RMA退货流程（回复退货问题时引用）
        if rma_knowledge:
            knowledge_hint += "\n### RMA退货处理要点\n"
            rma_flow_list = rma_knowledge.get("RMA流程", [])
            for item in rma_flow_list[:5]:
                item = item.strip()
                if item.startswith("- "):
                    knowledge_hint += f"- {item[2:]}\n"
            no_return_list = rma_knowledge.get("无退货退款", [])
            if no_return_list:
                knowledge_hint += f"- 无退货退款条件：{', '.join(no_return_list[:3])}\n"

        # 订单关键规则（回复物流问题时引用）
        if orders_knowledge:
            ship_info_list = orders_knowledge.get("发货", [])
            if ship_info_list:
                knowledge_hint += "\n### 订单发货规则\n"
                # 提取注意事项部分
                notes = []
                for line in ship_info_list:
                    line = line.strip()
                    if line.startswith("### 注意事项"):
                        break
                    if line.startswith("- "):
                        notes.append(line[2:])
                        if len(notes) >= 2:
                            break
                for note in notes:
                    knowledge_hint += f"- {note}\n"

        try:
            response = api_caller(
                [{
                    "role": "system",
                    "content": (
                        "你是跨境电商运营专员（Newegg平台）。" + expertise_hint + "\n\n"
                        "## 你的角色\n"
                        "你是卖家的运营支持人员，负责解决卖家在Newegg平台上遇到的各种问题。\n\n"
                        "## 回复原则\n"
                        "1. **先共情，再解决**：先理解卖家的处境，再给出解决方案\n"
                        "2. **具体可执行**：给出明确的下一步行动，不要说'我们会处理'\n"
                        "3. **专业但不冷漠**：用专业术语但保持友好语气\n"
                        "4. **主动提供帮助**：预判卖家可能的后续问题\n\n"
                        "## 回复风格\n"
                        "- 每条回复 3-5 句话\n"
                        "- 直接给出解决方案或下一步行动\n"
                        "- 如果问题是技术/平台问题，先安抚卖家情绪，再给出明确操作步骤\n"
                        "- 如果问题是商务/价格问题，先肯定对方，再说明平台政策或给出可行方案\n"
                        "- 参考历史对话中的回复风格和措辞，但不要完全照搬\n\n"
                        "## 去AI化写作规则（必须遵守）\n"
                        "1. 直接陈述事实，禁止使用'此外'、'至关重要'、'深入探讨'、'强调'、'增强'等AI高频词汇\n"
                        "2. 禁止三段式结构（如'高效、专业和可靠'）\n"
                        "3. 句子长度要有变化，不要每句都差不多长\n"
                        "4. 避免'不仅...而且...'等否定式排比\n"
                        "5. 语气要像真人写的回复，不要像AI模板\n"
                        "6. 用具体数据或案例支撑观点，不要泛泛而谈\n\n"
                        "## 常见问题回复模板\n"
                        "- 物流问题：先道歉，说明原因，给出预计时间，提供追踪链接\n"
                        "- 产品问题：先确认问题，给出解决方案（换货/退款/补偿），说明流程\n"
                        "- 价格问题：先理解对方诉求，说明平台政策，给出可行方案\n"
                        "- 账号问题：先安抚情绪，给出具体操作步骤，提供技术支持联系方式\n"
                        "- 退货RMA：2个工作日内必须处理，否则系统自动退款。支持退货退款和更换两种方式\n"
                        "- 绩效问题：订单缺陷率<1%、退款率<5%、准时履约率>=95%、消息响应率>=95%(48h内)\n"
                        f"{knowledge_hint}"
                    )
                }, {
                    "role": "user",
                    "content": (
                        f"卖家消息：{seller_message}\n\n"
                        f"{history_text}\n\n"
                        f"请根据卖家消息和历史对话，给出专业的回复建议。直接输出回复内容，不含称呼和署名，3-5句话："
                    )
                }],
                0.5, 600
            )
            reply = response.choices[0].message.content.strip()
            return {
                "suggested_reply": reply,
                "references": merged[:3],
                "expertise": expertise_hint
            }
        except Exception as e:
            return {"suggested_reply": f"生成失败：{e}", "references": merged, "expertise": ""}

    def _update_stats(self):
        """更新统计信息（包含回复对统计）"""
        pairs = self.knowledge_base.get("reply_pairs", [])
        cases = self.knowledge_base.get("cases", [])

        type_counts = {}
        for c in cases:
            t = c.get('问题类型', '未知')
            type_counts[t] = type_counts.get(t, 0) + 1

        reply_context_counts = {}
        for p in pairs:
            ctx = p.get('context', '其他')
            reply_context_counts[ctx] = reply_context_counts.get(ctx, 0) + 1

        self.knowledge_base["stats"] = {
            "total_resolved": len(cases),
            "by_type": type_counts,
            "total_reply_pairs": len(pairs),
            "by_reply_context": reply_context_counts,
            "last_rebuilt": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def add_reply_pair(self, seller_message: str, operator_reply: str, context: str = "其他"):
        """添加一对卖家消息-运营回复到经验库"""
        pairs = self.knowledge_base.get("reply_pairs", [])
        new_pair = {
            "seller_message": seller_message,
            "operator_reply": operator_reply,
            "context": context,
            "added_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        pairs.append(new_pair)
        self.knowledge_base["reply_pairs"] = pairs

        # 更新统计信息
        self._update_stats()

        # 保存到文件
        self._save()