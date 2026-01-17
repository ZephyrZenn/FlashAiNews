"""基于 Function Calling 的灵活决策 Agent

采用混合范式：
- Planning 阶段：P&S 范式，制定完整计划
- Execution 阶段：ReAct 范式，动态工具调用
"""

import json
import logging
from datetime import datetime
from typing import Optional

from agent.models import (
    AgentPlanResult,
    AgentState,
    FocalPoint,
    StepCallback,
    log_step,
)
from agent.tools import save_current_execution_records
from agent.tools.base import ToolBox
from agent.tools.function_calling import tools_to_openai_format
from agent.utils import extract_json
from core.brief_generator import AIGenerator

logger = logging.getLogger(__name__)

# Planning 阶段系统 Prompt
PLANNING_SYSTEM_PROMPT = """你是一位拥有全球视野的"首席新闻架构师"。你的职责是根据用户关注点，自主选择信息源，收集资讯，并制定执行计划。

你可以使用以下工具来辅助规划：
1. **get_all_feeds**: 获取所有可用的订阅源列表，了解有哪些信息源可用（每个订阅源包含 id、title、url、description）
2. **get_recent_feed_update**: 根据选择的订阅源ID列表，获取指定时间范围内的最新文章摘要（只包含 id、title、url、summary、pub_date，不包含全文内容）
3. **get_article_content**: 根据文章ID列表获取这些文章的完整内容（仅在需要详细内容时使用，避免上下文窗口过大）
4. **find_keywords**: 从文章中提取核心关键词
5. **search_memory**: 在历史记忆库中搜索相关内容
6. **search_web**: 搜索互联网获取补充信息，扩充内容
7. **fetch_web_contents**: 获取网页详细内容

规划流程：
1. 首先使用 get_all_feeds 了解所有可用的订阅源
2. 根据用户关注点，选择合适的订阅源（可以调用多次 get_recent_feed_update 获取不同订阅源的文章摘要）
3. 如果需要某些文章的详细内容，使用 get_article_content 获取完整内容（建议只获取关键文章）
4. 使用 find_keywords 提取关键词
5. 使用 search_memory 搜索相关历史记忆
6. 如果关注点需要补充信息，使用 search_web 搜索网络
7. 基于收集到的所有信息，制定完整的执行计划

输出格式必须是 JSON，包含：
{
  "daily_overview": "一句话概括今日整体资讯特征",
  "focal_points": [
    {
      "priority": 1,
      "topic": "专题名称",
      "strategy": "SUMMARIZE | SEARCH_ENHANCE | FLASH_NEWS",
      "article_ids": [文章ID列表],
      "reasoning": "解释文章间的潜在联系或重要性",
      "search_query": "如果strategy是SEARCH_ENHANCE，请给出关键词，否则为空字符串",
      "writing_guide": "告诉下级Agent写作侧重点",
      "history_memory_id": [历史记忆的id列表]
    }
  ],
  "discarded_items": [
    {"id": "文章id", "reason": "内容重复/广告/无实质意义"}
  ]
}

重要提示：
- 必须先调用工具获取信息，再制定计划
- 可以根据关注点选择性地获取相关订阅源的文章
- 如果关注点涉及的信息在订阅源中不足，应使用 search_web 补充
- **在工具调用后，必须继续调用工具或输出 JSON 计划，不要输出解释性文本**
- 规划完成后，**必须直接输出 JSON 格式的计划，不要有任何解释或说明文字**
- 确保 article_ids 是字符串列表
- **输出必须是纯 JSON，不要包含任何其他文字**
"""

# Execution 阶段系统 Prompt
EXECUTION_SYSTEM_PROMPT = """你是一位资深科技编辑，擅长将零散的资讯缝合为逻辑严密的深度观察报告。

当前任务：根据规划阶段确定的焦点话题，生成高质量的摘要内容。

你可以使用以下工具：
- search_web: 搜索互联网获取补充信息
- fetch_web_contents: 获取网页详细内容
- search_memory: 查询历史记忆获取上下文
- write_article: 撰写文章（支持 DEEP 和 FLASH 两种风格）
- review_article: 审查文章初稿，检查事实准确性和逻辑性

执行流程（ReAct 范式）：
1. **思考 (Think)**: 分析当前任务，判断需要哪些信息
2. **收集信息 (Act)**: 调用 search_web、fetch_web_contents、search_memory 获取必要信息
3. **撰写初稿 (Write)**: 调用 write_article 工具生成文章初稿
4. **审查初稿 (Review)**: 调用 review_article 工具审查初稿
5. **修改完善 (Revise)**: 
   - 如果审查结果为 REJECTED 或有 CRITICAL 错误，必须根据审查建议修改后重新撰写
   - 如果审查结果为 APPROVED，可以输出最终内容
   - 最多重试 3 次

重要提示：
- 必须先调用 write_article 生成初稿，再调用 review_article 审查
- 如果审查发现 CRITICAL 错误，必须修改后重新撰写
- 审查通过后，输出最终的文章内容（Markdown 格式）
- 不要在没有审查的情况下直接输出内容

输出要求：
- 使用 Markdown 格式
- 以 ## {topic} 开头
- 包含核心观点、关键数据和引用链接
- 在文末列出所有参考链接
"""


class BoostAgent:
    """基于 Function Calling 的灵活决策 Agent

    采用混合范式：
    - Planning 阶段：P&S 范式，制定完整计划
    - Execution 阶段：ReAct 范式，动态工具调用
    """

    def __init__(
        self,
        client: AIGenerator,
        toolbox: ToolBox,
        max_iterations: int = 20,
        max_planning_iterations: int = 5,
    ):
        """初始化 Agent

        Args:
            client: AI 生成器客户端
            toolbox: 工具箱实例
            max_iterations: 执行阶段最大迭代次数
            max_planning_iterations: 规划阶段最大迭代次数
        """
        self.client = client
        self.toolbox = toolbox
        self.max_iterations = max_iterations
        self.max_planning_iterations = max_planning_iterations
        self.state: Optional[AgentState] = None
        
        # 创建并注册写作和审查工具（需要 client）
        from agent.tools.writing_tool import WriteArticleTool, ReviewArticleTool
        write_tool = WriteArticleTool(client)
        review_tool = ReviewArticleTool(client)
        toolbox.register(write_tool, tags=["writing", "llm"])
        toolbox.register(review_tool, tags=["review", "quality", "llm"])

    async def run(
        self,
        focus: str = "",
        hour_gap: int = 24,
        on_step: Optional[StepCallback] = None,
    ) -> str:
        """执行完整的 Agent 工作流

        Args:
            focus: 用户关注点
            hour_gap: 获取文章的时间范围（小时），默认24小时
            on_step: 步骤回调函数

        Returns:
            生成的摘要内容
        """
        # 初始化空状态
        self.state = AgentState(
            groups=[],
            raw_articles=[],
            log_history=[],
            focus=focus,
            history_memories={},
        )
        if on_step:
            self.state["on_step"] = on_step

        log_step(
            self.state,
            f"🚀 Function Calling Agent 启动，关注点: {focus if focus else '无特定关注点'}",
        )

        # 1. Planning 阶段（P&S）- 现在会自主获取数据
        log_step(self.state, "📋 开始规划阶段（P&S 范式）...")
        plan = await self._planning_phase(focus, hour_gap)
        self.state["plan"] = plan

        focal_points = plan.get("focal_points", [])
        discarded = plan.get("discarded_items", [])
        log_step(
            self.state,
            f"📝 规划完成：识别出 {len(focal_points)} 个焦点话题，丢弃 {len(discarded)} 篇文章",
        )
        for i, point in enumerate(focal_points, 1):
            log_step(self.state, f"   {i}. [{point['strategy']}] {point['topic']}")

        # 2. Execution 阶段（ReAct）
        log_step(self.state, "⚡ 开始执行阶段（ReAct 范式）...")
        results = await self._execution_phase(plan)
        self.state["summary_results"] = results

        log_step(self.state, f"✅ Agent执行完成，共生成 {len(results)} 篇内容")
        await save_current_execution_records(self.state)

        return "\n\n".join(results)

    async def _planning_phase(
        self,
        focus: str,
        hour_gap: int,
    ) -> AgentPlanResult:
        """Planning & Scheduling 阶段

        现在 LLM 可以调用：
        - get_all_feeds: 获取所有可用订阅源
        - get_recent_feed_update: 根据选择的订阅源获取文章摘要（不包含全文）
        - get_article_content: 根据文章ID获取完整内容（仅在需要时使用）
        - find_keywords: 提取关键词
        - search_memory: 搜索历史记忆
        - search_web: 搜索网络获取补充信息
        - fetch_web_contents: 获取网页详细内容
        """
        # 准备可用工具（规划相关）
        planning_tools = [
            self.toolbox.get("get_all_feeds"),
            self.toolbox.get("get_recent_feed_update"),
            self.toolbox.get("get_article_content"),
            self.toolbox.get("find_keywords"),
            self.toolbox.get("search_memory"),
            self.toolbox.get("search_web"),
            self.toolbox.get("fetch_web_contents"),
        ]
        planning_tools = [t for t in planning_tools if t is not None]

        # 构建初始消息
        messages = [
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._build_planning_prompt(focus, hour_gap),
            },
        ]

        # ReAct 循环：LLM 可以调用工具，然后基于结果继续规划
        iteration = 0
        while iteration < self.max_planning_iterations:
            tools_schema = tools_to_openai_format(planning_tools) if planning_tools else None

            try:
                print(messages)
                response = await self.client.completion_with_tools(
                    messages=messages,
                    tools=tools_schema,
                )
                print(response)
                # 处理工具调用
                if response.get("tool_calls"):
                    messages = await self._handle_tool_calls_response(response, messages, phase="规划")
                    continue

                # 尝试解析最终计划
                plan = self._try_parse_plan(response)
                if plan:
                    return plan
                
                # 如果 LLM 返回了文本但没有工具调用，说明需要继续
                # 将响应添加到消息历史，并提示输出 JSON
                content = response.get("content", "")
                if content:
                    messages.append({
                        "role": "assistant",
                        "content": content,
                    })
                    messages.append({
                        "role": "user",
                        "content": "请直接输出 JSON 格式的执行计划，不要有任何解释或说明文字。格式必须严格按照要求。",
                    })
                    log_step(self.state, "⚠️ 规划阶段：LLM 返回了文本而非 JSON，提示重新输出...")

            except Exception as e:
                logger.error(f"Error in planning phase iteration {iteration}: {e}", exc_info=True)
                log_step(self.state, f"❌ 规划阶段出错：{str(e)}")
                if iteration == self.max_planning_iterations - 1:
                    return self._create_default_plan()

            iteration += 1

        # 如果达到最大迭代次数仍未完成，返回默认计划
        log_step(self.state, "⚠️ 规划阶段达到最大迭代次数，使用默认计划")
        return self._create_default_plan()

    async def _handle_tool_calls_response(self, response: dict, messages: list, phase: str = "执行") -> list:
        """处理工具调用响应（通用方法）
        
        Args:
            response: LLM 响应，包含 tool_calls
            messages: 当前消息历史
            phase: 阶段名称（用于日志），如 "规划" 或 "执行"
        
        Returns:
            更新后的消息历史
        """
        tool_messages = await self._handle_tool_calls(response["tool_calls"])
        messages.append(self._build_assistant_message_with_tool_calls(response))
        messages.extend(tool_messages)
        
        tool_names = [tc["function"]["name"] for tc in response["tool_calls"]]
        if phase == "规划":
            log_step(self.state, f"🔧 规划阶段：调用工具：{tool_names}")
        else:
            log_step(self.state, f"   ↳ 调用了工具：{tool_names}")
        return messages

    def _try_parse_plan(self, response: dict) -> AgentPlanResult | None:
        """尝试解析规划结果"""
        content = response.get("content", "")
        if not content:
            log_step(self.state, "⚠️ 规划阶段：LLM 未返回内容，继续尝试...")
            return None

        try:
            plan = extract_json(content)
            return self._validate_and_normalize_plan(plan)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse plan: {e}, content: {content[:500]}")
            log_step(self.state, "❌ 规划失败：无法解析LLM响应，尝试继续...")
            return None

    def _build_assistant_message_with_tool_calls(self, response: dict) -> dict:
        """构建包含工具调用的 assistant 消息"""
        return {
            "role": "assistant",
            "content": response.get("content"),
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                    },
                }
                for tc in response["tool_calls"]
            ],
        }

    async def _execution_phase(
        self,
        plan: AgentPlanResult,
    ) -> list[str]:
        """ReAct 执行阶段

        对每个 focal_point，LLM 动态决策：
        - 是否需要搜索补充信息？
        - 如何组织文章内容？
        - 如何撰写摘要？
        """
        results = []

        execution_tools = [
            self.toolbox.get("search_web"),
            self.toolbox.get("fetch_web_contents"),
            self.toolbox.get("search_memory"),
            self.toolbox.get("write_article"),
            self.toolbox.get("review_article"),
        ]
        execution_tools = [t for t in execution_tools if t is not None]

        for focal_point in plan.get("focal_points", []):
            log_step(
                self.state,
                f"📰 [{focal_point['strategy']}] 处理话题: {focal_point['topic']}",
            )

            # 为每个任务创建独立的 ReAct 循环
            messages = [
                {"role": "system", "content": EXECUTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_execution_prompt(focal_point),
                },
            ]

            # ReAct 循环
            final_result = await self._execute_focal_point(
                focal_point, messages, execution_tools
            )

            if final_result:
                results.append(final_result)
            else:
                log_step(
                    self.state,
                    f"   ↳ ⚠️ 话题 '{focal_point['topic']}' 生成失败，使用占位内容",
                )
                results.append(f"## {focal_point['topic']}\n\n生成失败，请重试。")

        return results

    async def _execute_focal_point(
        self, focal_point: FocalPoint, messages: list, execution_tools: list
    ) -> str | None:
        """执行单个 focal point 的 ReAct 循环"""
        iteration = 0
        while iteration < self.max_iterations:
            tools_schema = tools_to_openai_format(execution_tools) if execution_tools else None

            try:
                response = await self.client.completion_with_tools(
                    messages=messages,
                    tools=tools_schema,
                )

                # 处理工具调用
                if response.get("tool_calls"):
                    messages = await self._handle_tool_calls_response(response, messages, phase="执行")
                    iteration += 1
                    continue

                # 生成最终摘要
                final_result = response.get("content", "")
                if final_result:
                    log_step(
                        self.state,
                        f"   ↳ ✅ 话题 '{focal_point['topic']}' 撰写完成",
                    )
                    return final_result

                log_step(self.state, "   ↳ ⚠️ 未生成内容，继续尝试...")

            except Exception as e:
                logger.error(f"Error in execution phase iteration {iteration}: {e}", exc_info=True)
                log_step(self.state, f"   ↳ ❌ 执行出错：{str(e)}")

            iteration += 1

        return None


    async def _handle_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        """处理工具调用并返回结果到消息历史"""
        tool_messages = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_id = tool_call.get("id", f"call_{len(tool_messages)}")

            # 解析参数
            tool_args = self._parse_tool_arguments(tool_call, tool_id, tool_name, tool_messages)
            if tool_args is None:
                continue

            # 获取工具
            tool = self.toolbox.get(tool_name)
            if not tool:
                tool_messages.append(self._create_error_message(tool_id, tool_name, f"工具 {tool_name} 不存在"))
                continue

            # 执行工具
            result = await self._execute_tool(tool_name, tool, tool_args)
            if result is None:
                tool_messages.append(self._create_error_message(tool_id, tool_name, "工具执行失败"))
                continue

            # 更新 state（如果需要）
            if result.success:
                self._update_state_from_tool_result(tool_name, result)

            # 构建响应消息
            content = self._serialize_tool_result(result)
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": content,
            })

        return tool_messages

    def _parse_tool_arguments(self, tool_call: dict, tool_id: str, tool_name: str, tool_messages: list) -> dict | None:
        """解析工具参数"""
        try:
            tool_args_str = tool_call["function"]["arguments"]
            return json.loads(tool_args_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool arguments: {e}, args: {tool_call['function'].get('arguments', '')}")
            tool_messages.append(self._create_error_message(tool_id, tool_name, f"参数解析失败: {str(e)}"))
            return None

    def _create_error_message(self, tool_id: str, tool_name: str, error: str) -> dict:
        """创建错误消息"""
        return {
            "role": "tool",
            "tool_call_id": tool_id,
            "name": tool_name,
            "content": json.dumps({"error": error}),
        }

    async def _execute_tool(self, tool_name: str, tool, tool_args: dict):
        """执行工具并处理参数转换"""
        try:
            # 处理特殊参数
            if "state" in tool_args and isinstance(tool_args["state"], dict):
                tool_args["state"] = self.state

            # 处理写作工具的参数转换
            if tool_name in ("write_article", "review_article"):
                tool_args = self._convert_writing_tool_args(tool_name, tool_args)
            
            # 处理 find_keywords 的参数转换
            if tool_name == "find_keywords" and "articles" in tool_args:
                tool_args["articles"] = self._convert_articles_arg(tool_args["articles"])

            return await tool.execute(**tool_args)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return None

    def _update_state_from_tool_result(self, tool_name: str, result):
        """根据工具结果更新 state"""
        if not self.state or not result.success:
            return

        # 使用策略模式处理不同类型的工具结果
        state_updaters = {
            "get_recent_feed_update": self._update_state_from_feed_update,
            "get_article_content": self._update_state_from_article_content,
        }

        updater = state_updaters.get(tool_name)
        if updater:
            updater(result)

    def _update_state_from_feed_update(self, result):
        """更新 state 中的 articles（新Agent不使用Group）"""
        _, articles = result.data

        # 合并文章（去重）
        existing_article_ids = {str(a["id"]) for a in self.state["raw_articles"]}
        new_articles = [
            article
            for article in articles
            if str(article["id"]) not in existing_article_ids
        ]
        self.state["raw_articles"].extend(new_articles)

    def _update_state_from_article_content(self, result):
        """更新 state 中文章的完整内容"""
        # result.data 是一个字典，key 是文章ID（字符串），value 是内容（字符串）
        content_dict = result.data
        
        # 创建文章ID到索引的映射，方便快速查找
        article_id_to_index = {
            str(article["id"]): idx
            for idx, article in enumerate(self.state["raw_articles"])
        }
        
        # 更新对应文章的内容
        for article_id, content in content_dict.items():
            if article_id in article_id_to_index:
                idx = article_id_to_index[article_id]
                self.state["raw_articles"][idx]["content"] = content

    def _serialize_tool_result(self, result) -> str:
        """序列化工具结果"""
        if not result.success:
            return json.dumps({"error": result.error}, ensure_ascii=False)

        try:
            return json.dumps(result.data, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            return json.dumps({"data": str(result.data)}, ensure_ascii=False)

    def _build_planning_prompt(self, focus: str, hour_gap: int) -> str:
        """构建规划阶段的用户提示"""
        prompt = f"""当前日期: {datetime.now().strftime("%Y-%m-%d")}
用户关注点: {focus if focus else "无特定关注点"}
时间范围: 过去 {hour_gap} 小时

请根据用户关注点，自主选择相关的订阅源，获取文章更新，并搜索网络补充信息，然后制定完整的执行计划。

你可以：
1. 使用 get_all_feeds 查看所有可用的订阅源
2. 根据关注点选择相关订阅源，使用 get_recent_feed_update 获取文章摘要
3. 如果需要详细内容，使用 get_article_content 获取指定文章的完整内容
4. 使用 find_keywords 提取关键词
5. 使用 search_memory 搜索历史记忆
6. 使用 search_web 搜索网络获取补充信息
7. 制定完整的执行计划
"""
        return prompt

    def _build_execution_prompt(self, focal_point: FocalPoint) -> str:
        """构建执行阶段的用户提示"""
        # 获取相关文章
        article_ids = [str(aid) for aid in focal_point.get("article_ids", [])]
        articles = [
            article
            for article in self.state["raw_articles"]
            if str(article["id"]) in article_ids
        ]

        # 获取历史记忆
        history_memory_ids = focal_point.get("history_memory_id", [])
        history_memories = [
            self.state["history_memories"][hid]
            for hid in history_memory_ids
            if hid in self.state["history_memories"]
        ]

        prompt = f"""任务信息：
- 话题: {focal_point['topic']}
- 策略: {focal_point['strategy']}
- 推理: {focal_point['reasoning']}
- 写作指南: {focal_point.get('writing_guide', '')}
- 搜索查询: {focal_point.get('search_query', '')}

相关文章（{len(articles)} 篇）:
{json.dumps([{"title": a['title'], "url": a['url'], "summary": a.get('summary', '')[:200]} for a in articles], ensure_ascii=False, indent=2)}

历史记忆:
{json.dumps([{"topic": m['topic'], "reasoning": m['reasoning'], "content": m['content'][:300]} for m in history_memories], ensure_ascii=False, indent=2) if history_memories else "无"}

请根据任务信息，使用工具获取必要的补充信息，然后生成高质量的摘要内容。
"""
        return prompt

    def _validate_and_normalize_plan(self, plan: dict) -> AgentPlanResult:
        """验证并规范化计划格式"""
        # 确保所有 article_ids 是字符串
        for point in plan.get("focal_points", []):
            if "article_ids" in point:
                point["article_ids"] = [str(aid) for aid in point["article_ids"]]
            if "history_memory_id" not in point:
                point["history_memory_id"] = []

        return AgentPlanResult(
            daily_overview=plan.get("daily_overview", ""),
            focal_points=plan.get("focal_points", []),
            discarded_items=plan.get("discarded_items", []),
        )

    def _create_default_plan(self) -> AgentPlanResult:
        """创建默认计划（当规划失败时使用）"""
        # 将所有文章归类为一个 FLASH_NEWS 任务
        article_ids = [str(article["id"]) for article in self.state["raw_articles"]]

        return AgentPlanResult(
            daily_overview="规划阶段未完成，使用默认处理方式",
            focal_points=[
                {
                    "priority": 1,
                    "topic": "综合资讯",
                    "strategy": "FLASH_NEWS",
                    "article_ids": article_ids,
                    "reasoning": "默认处理所有文章",
                    "search_query": "",
                    "writing_guide": "生成快讯格式的摘要",
                    "history_memory_id": [],
                }
            ],
            discarded_items=[],
        )

    def _convert_writing_tool_args(self, tool_name: str, tool_args: dict) -> dict:  # noqa: ARG002
        """转换写作工具的参数，将简化的参数转换为完整的对象
        
        Args:
            tool_name: 工具名称
            tool_args: 原始参数（可能包含 ID 或简化数据）
        
        Returns:
            转换后的参数（包含完整的对象）
        """
        converted_args = tool_args.copy()
        converted_args["articles"] = self._convert_articles_arg(tool_args.get("articles"))
        converted_args["history_memory"] = self._convert_history_memory_list_arg(tool_args.get("history_memory"))
        return converted_args

    def _convert_articles_arg(self, articles_arg) -> list:
        """转换 articles 参数
        
        支持多种输入格式：
        1. 完整的文章对象列表（dict with title, summary, etc.）
        2. 文章 ID 列表（数字或字符串）
        3. 文章标题列表（字符串）- 通过标题匹配查找文章
        """
        if not articles_arg or not isinstance(articles_arg, list):
            return []

        # 如果已经是完整的文章对象，直接返回
        if articles_arg and isinstance(articles_arg[0], dict) and "title" in articles_arg[0]:
            return articles_arg

        # 如果第一个元素是字符串，可能是标题或 ID
        if isinstance(articles_arg[0], str):
            # 尝试作为 ID 处理
            try:
                # 如果所有元素都可以转换为数字，则视为 ID 列表
                article_ids = [str(int(aid)) for aid in articles_arg]
                articles = [
                    article
                    for article in self.state.get("raw_articles", [])
                    if str(article["id"]) in article_ids
                ]
                if articles:
                    return articles
            except (ValueError, TypeError):
                pass
            
            # 如果无法作为 ID 处理，则视为标题列表，通过标题匹配
            titles = articles_arg
            articles = [
                article
                for article in self.state.get("raw_articles", [])
                if article.get("title") in titles
            ]
            return articles

        # 尝试提取 article IDs（处理数字或包含 id 字段的字典）
        article_ids = self._extract_article_ids(articles_arg)
        if article_ids:
            return [
                article
                for article in self.state.get("raw_articles", [])
                if str(article["id"]) in article_ids
            ]

        return []

    def _extract_article_ids(self, articles_arg: list) -> list[str]:
        """从 articles 参数中提取 ID 列表"""
        if not articles_arg:
            return []

        first_item = articles_arg[0]
        if isinstance(first_item, (str, int)):
            return [str(aid) for aid in articles_arg]
        if isinstance(first_item, dict) and "id" in first_item:
            return [str(a.get("id", "")) for a in articles_arg if a.get("id")]

        return []

    def _convert_history_memory_list_arg(self, memory_arg) -> list | None:
        """转换 history_memory 参数（现在是列表）"""
        if not memory_arg:
            return None

        # 如果已经是列表，处理列表中的每个元素
        if isinstance(memory_arg, list):
            converted_list = []
            for item in memory_arg:
                converted = self._convert_single_memory_arg(item)
                if converted:
                    converted_list.append(converted)
            return converted_list if converted_list else None

        # 如果是单个对象或 ID，转换为列表
        converted = self._convert_single_memory_arg(memory_arg)
        return [converted] if converted else None

    def _convert_single_memory_arg(self, memory_arg) -> dict | None:
        """转换单个 history_memory 参数"""
        if not memory_arg:
            return None

        # 如果已经是完整的 memory 对象，直接返回
        if isinstance(memory_arg, dict) and "topic" in memory_arg:
            return memory_arg

        # 提取 memory ID
        memory_id = self._extract_memory_id(memory_arg)
        if memory_id is None:
            return None

        # 从 state 中获取完整的 memory 对象
        return self.state.get("history_memories", {}).get(memory_id)

    def _extract_memory_id(self, memory_arg) -> int | None:
        """从 memory 参数中提取 ID"""
        if isinstance(memory_arg, (int, str)):
            return int(memory_arg)
        if isinstance(memory_arg, dict) and "id" in memory_arg:
            return memory_arg["id"]
        return None

    def get_log_history(self) -> list[str]:
        """获取执行日志历史"""
        if self.state:
            return self.state.get("log_history", [])
        return []
