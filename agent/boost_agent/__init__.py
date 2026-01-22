"""基于 Function Calling 的灵活决策 Agent

采用混合范式：
- Planning 阶段：P&S 范式，制定完整计划
- Execution 阶段：ReAct 范式，动态工具调用
"""

import json
import logging
from typing import Optional

from agent.boost_agent.arg_converter import ArgumentConverter
from agent.boost_agent.prompt_builder import PromptBuilder
from agent.boost_agent.prompts import EXECUTION_SYSTEM_PROMPT, PLANNING_SYSTEM_PROMPT
from agent.boost_agent.state_updater import StateUpdater
from agent.boost_agent.tool_handler import ToolHandler
from agent.boost_agent.tool_logger import (
    format_tool_args_summary,
    format_tool_result_summary,
    get_tool_description,
)
from agent.artifact_store import ArtifactStore
from agent.context import ContextManager, ContentOptimizer, MessageCompressor
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
from agent.tools.boost_writing_tool import (
    BoostReviewArticleTool,
    BoostWriteArticleTool,
)
from agent.utils import extract_json
from core.brief_generator import AIGenerator
from core.config import get_config
from core.models.llm import Message, ToolCall

logger = logging.getLogger(__name__)


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

        # 初始化上下文管理组件
        config = get_config()
        context_cfg = config.context

        self.context_manager = ContextManager(
            max_tokens=context_cfg.max_tokens,
            compress_threshold=context_cfg.compress_threshold,
            compress_strategy=context_cfg.compress_strategy,
        )

        self.content_optimizer = ContentOptimizer(
            article_max_length=context_cfg.article_max_length,
            summary_max_length=context_cfg.summary_max_length,
            memory_max_length=context_cfg.memory_max_length,
            client=client,  # 传入client以支持LLM关键词提取
        )

        # Artifact 存储（仅 Boost 路径使用）
        self.artifact_store = ArtifactStore(lambda: self.state)

        self.message_compressor = MessageCompressor(
            context_manager=self.context_manager,
            strategy=context_cfg.compression_strategy,
            max_messages=context_cfg.history_max_messages,
            keep_system=context_cfg.keep_system,
            keep_recent_tool_calls=context_cfg.keep_recent_tool_calls,
        )

        # 创建并注册 Boost 专用写作/审查工具（包装原始工具，返回 artifact 句柄）
        boost_write_tool = BoostWriteArticleTool(client, self.artifact_store)
        boost_review_tool = BoostReviewArticleTool(client, self.artifact_store)
        toolbox.register(boost_write_tool, tags=["writing", "llm", "boost"])
        toolbox.register(boost_review_tool, tags=["review", "quality", "llm", "boost"])

        # 初始化辅助组件（延迟初始化，需要 state）
        self._arg_converter: Optional[ArgumentConverter] = None
        self._state_updater: Optional[StateUpdater] = None
        self._tool_handler: Optional[ToolHandler] = None
        self._prompt_builder: Optional[PromptBuilder] = None

    def _init_helpers(self):
        """初始化辅助组件（需要 state）"""
        if self.state is None:
            return

        if self._arg_converter is None:
            self._arg_converter = ArgumentConverter(self.state, self.artifact_store)
        if self._state_updater is None:
            self._state_updater = StateUpdater(self.state)
        if self._tool_handler is None:
            self._tool_handler = ToolHandler(
                self.state, self._arg_converter, self.context_manager
            )
        if self._prompt_builder is None:
            self._prompt_builder = PromptBuilder(self.content_optimizer)

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

        # 初始化辅助组件
        self._init_helpers()

        log_step(
            self.state,
            f"🚀 Boost Agent 启动，关注点: {focus if focus else '无特定关注点'}",
        )

        # 1. Planning 阶段（P&S）- 现在会自主获取数据
        log_step(self.state, "📋 开始规划阶段...")
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
        log_step(self.state, "⚡ 开始执行阶段...")
        results = await self._execution_phase(plan)
        self.state["summary_results"] = results

        log_step(self.state, f"✅ Agent执行完成，共生成 {len(results)} 篇内容")

        # 记录上下文使用统计
        stats = self.context_manager.get_stats()
        log_step(
            self.state,
            f"📊 上下文使用统计: "
            f"最大使用 {stats['llm_calls']['max_tokens']} tokens, "
            f"平均 {stats['llm_calls']['avg_tokens']:.0f} tokens/次, "
            f"压缩 {stats.get('compression', {}).get('total_compressions', 0)} 次",
        )
        self.context_manager.log_stats()

        await save_current_execution_records(self.state)

        # 返回简报内容和外部搜索结果
        ext_info = self.state.get("ext_info", [])
        return "\n\n".join(results), ext_info

    async def _planning_phase(
        self,
        focus: str,
        hour_gap: int,
    ) -> AgentPlanResult:
        """Planning & Scheduling 阶段"""
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
            Message.system(PLANNING_SYSTEM_PROMPT),
            Message.user(self._prompt_builder.build_planning_prompt(focus, hour_gap)),
        ]

        # ReAct 循环：LLM 可以调用工具，然后基于结果继续规划
        iteration = 0
        while iteration < self.max_planning_iterations:
            # 检查并压缩消息历史（如果需要）
            if self.context_manager.should_compress(messages):
                log_step(self.state, "📦 规划阶段：压缩消息历史以节省上下文空间...")
                messages = self.message_compressor.compress_messages(messages)
                self.context_manager.update_tokens(messages)

            tools_schema = (
                tools_to_openai_format(planning_tools) if planning_tools else None
            )

            try:
                # 转换为dict格式用于API调用
                messages_dict = [msg.to_dict() for msg in messages]
                response = await self.client.completion_with_tools(
                    messages=messages_dict,
                    tools=tools_schema,
                )

                # 记录LLM调用
                call_tokens = self.context_manager.estimate_messages_tokens(messages)
                self.context_manager.record_llm_call(call_tokens)

                # 处理工具调用
                if response.get("tool_calls"):
                    messages = await self._handle_tool_calls_response(
                        response, messages, phase="规划"
                    )
                    # 更新token计数
                    self.context_manager.update_tokens(messages)
                    continue

                # 尝试解析最终计划
                plan = self._try_parse_plan(response)
                if plan:
                    return plan

                # 如果 LLM 返回了文本但没有工具调用，说明需要继续
                # 将响应添加到消息历史，并提示输出 JSON
                content = response.get("content", "")
                if content:
                    messages.append(Message.assistant(content))
                    messages.append(
                        Message.user(
                            "请直接输出 JSON 格式的执行计划，不要有任何解释或说明文字。格式必须严格按照要求。"
                        )
                    )
                    log_step(
                        self.state, "⚠️ 规划阶段：LLM 返回了文本而非 JSON，提示重新输出..."
                    )

            except Exception as e:
                logger.error(
                    f"Error in planning phase iteration {iteration}: {e}", exc_info=True
                )
                log_step(self.state, f"❌ 规划阶段出错：{str(e)}")
                if iteration == self.max_planning_iterations - 1:
                    return self._create_default_plan()

            iteration += 1

        # 如果达到最大迭代次数仍未完成，返回默认计划
        log_step(self.state, "⚠️ 规划阶段达到最大迭代次数，使用默认计划")
        return self._create_default_plan()

    async def _handle_tool_calls_response(
        self, response: dict, messages: list[Message], phase: str = "执行"
    ) -> list[Message]:
        """处理工具调用响应（通用方法）"""
        tool_calls = response["tool_calls"]
        tool_descriptions = [
            get_tool_description(tc["function"]["name"]) for tc in tool_calls
        ]
        
        # 记录工具调用开始
        if phase == "规划":
            log_step(
                self.state,
                f"🔧 规划阶段：{'、'.join(tool_descriptions)}",
            )
        else:
            log_step(
                self.state,
                f"   ↳ {'、'.join(tool_descriptions)}",
            )
        
        tool_messages = await self._handle_tool_calls(tool_calls)
        messages.append(self._build_assistant_message_with_tool_calls(response))
        messages.extend(tool_messages)
        
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

    def _build_assistant_message_with_tool_calls(self, response: dict) -> Message:
        """构建包含工具调用的 assistant 消息"""
        tool_calls = []
        for tc in response["tool_calls"]:
            tool_calls.append(
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"],
                )
            )
        return Message.assistant(
            content=response.get("content", ""),
            tool_calls=tool_calls,
        )

    async def _execution_phase(
        self,
        plan: AgentPlanResult,
    ) -> list[str]:
        """ReAct 执行阶段"""
        results = []

        execution_tools = [
            self.toolbox.get("search_web"),
            self.toolbox.get("fetch_web_contents"),
            self.toolbox.get("search_memory"),
            self.toolbox.get("boost_write_article"),
            self.toolbox.get("boost_review_article"),
        ]
        execution_tools = [t for t in execution_tools if t is not None]

        for focal_point in plan.get("focal_points", []):
            log_step(
                self.state,
                f"📰 [{focal_point['strategy']}] 处理话题: {focal_point['topic']}",
            )

            # 为每个任务创建独立的 ReAct 循环
            execution_prompt = await self._prompt_builder.build_execution_prompt(
                focal_point, self.state
            )
            messages = [
                Message.system(EXECUTION_SYSTEM_PROMPT),
                Message.user(execution_prompt),
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
        self, focal_point: FocalPoint, messages: list[Message], execution_tools: list
    ) -> str | None:
        """执行单个 focal point 的 ReAct 循环"""
        iteration = 0
        while iteration < self.max_iterations:
            # 检查并压缩消息历史（如果需要）
            if self.context_manager.should_compress(messages):
                log_step(
                    self.state,
                    f"📦 执行阶段：压缩消息历史以节省上下文空间（话题: {focal_point['topic']}）...",
                )
                messages = self.message_compressor.compress_messages(messages)
                self.context_manager.update_tokens(messages)

            tools_schema = (
                tools_to_openai_format(execution_tools) if execution_tools else None
            )

            try:
                # 转换为dict格式用于API调用
                messages_dict = [msg.to_dict() for msg in messages]
                response = await self.client.completion_with_tools(
                    messages=messages_dict,
                    tools=tools_schema,
                )

                # 记录LLM调用
                call_tokens = self.context_manager.estimate_messages_tokens(messages)
                self.context_manager.record_llm_call(call_tokens)

                # 处理工具调用
                if response.get("tool_calls"):
                    messages = await self._handle_tool_calls_response(
                        response, messages, phase="执行"
                    )
                    # 更新token计数
                    self.context_manager.update_tokens(messages)
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
                logger.error(
                    f"Error in execution phase iteration {iteration}: {e}", exc_info=True
                )
                log_step(self.state, f"   ↳ ❌ 执行出错：{str(e)}")

            iteration += 1

        return None

    async def _handle_tool_calls(self, tool_calls: list[dict]) -> list[Message]:
        """处理工具调用并返回结果到消息历史"""
        tool_messages = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_id = tool_call.get("id", f"call_{len(tool_messages)}")
            tool_description = get_tool_description(tool_name)

            # 解析参数
            tool_args = self._tool_handler.parse_tool_arguments(
                tool_call, tool_id, tool_name, tool_messages
            )
            if tool_args is None:
                log_step(self.state, f"      ❌ {tool_description}: 参数解析失败")
                continue

            # 记录工具调用参数摘要
            args_summary = format_tool_args_summary(tool_name, tool_args)
            if args_summary:
                log_step(self.state, f"      📋 {tool_description} ({args_summary})")
            else:
                log_step(self.state, f"      📋 {tool_description}")

            # 获取工具
            tool = self.toolbox.get(tool_name)
            if not tool:
                log_step(self.state, f"      ❌ {tool_description}: 工具不存在")
                tool_messages.append(
                    self._tool_handler.create_error_message(
                        tool_id, tool_name, f"工具 {tool_name} 不存在"
                    )
                )
                continue

            # 执行工具
            result = await self._tool_handler.execute_tool(tool_name, tool, tool_args)
            if result is None:
                log_step(self.state, f"      ❌ {tool_description}: 执行失败")
                tool_messages.append(
                    self._tool_handler.create_error_message(
                        tool_id, tool_name, "工具执行失败"
                    )
                )
                continue

            # 记录工具执行结果摘要
            result_summary = format_tool_result_summary(tool_name, result)
            if result_summary:
                log_step(self.state, f"      {result_summary}")

            # 更新 state（如果需要）
            if result.success:
                self._state_updater.update_from_tool_result(tool_name, result)

            # 构建响应消息
            content = self._tool_handler.serialize_tool_result(result)
            tool_messages.append(
                Message.tool(content, tool_name, tool_id)
            )

        return tool_messages

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

    def get_log_history(self) -> list[str]:
        """获取执行日志历史"""
        if self.state:
            return self.state.get("log_history", [])
        return []
