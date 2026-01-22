"""写作和审查工具

直接实现写作和审查功能，不依赖 pipeline 中的 writer 和 critic
"""

import logging

from agent.tools.base import BaseTool, ToolSchema, ToolParameter
from agent.models import (
    WritingMaterial,
    AgentCriticResult,
)
from agent.prompts import (
    WRITER_FLASH_NEWS_PROMPT,
    WRITER_DEEP_DIVE_SYSTEM_PROMPT_TEMPLATE,
    WRITER_DEEP_DIVE_USER_PROMPT_TEMPLATE,
    CRITIC_SYSTEM_PROMPT_TEMPLATE,
    CRITIC_USER_PROMPT_TEMPLATE,
)
from agent.utils import extract_json
from core.brief_generator import AIGenerator
from core.models.llm import Message

logger = logging.getLogger(__name__)


class WriteArticleTool(BaseTool[str]):
    """撰写文章的工具"""

    def __init__(self, client: AIGenerator):
        self.client = client

    @property
    def name(self) -> str:
        return "write_article"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "根据提供的素材撰写文章。支持两种风格："
                "1. DEEP（深度文章）：整合多篇文章，生成逻辑严密的深度观察报告；"
                "2. FLASH（快讯）：用最简练的语言概括核心事件。"
                "返回 Markdown 格式的文章内容。"
            ),
            parameters=[
                ToolParameter(
                    name="writing_material",
                    type="WritingMaterial",
                    description=(
                        "写作素材对象（推荐用法）。包含：topic、style、match_type、"
                        "relevance_to_focus、writing_guide、reasoning、articles，以及可选的 ext_info/history_memory。"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="review",
                    type="dict",
                    description="审查结果（可选），包含 status、findings、score 等字段的对象。如果提供，将根据审查建议进行修改",
                    required=False,
                ),
            ],
        )

    async def _execute(
        self,
        writing_material: WritingMaterial,
        review: AgentCriticResult | None = None,
    ) -> str:
        """
        撰写文章

        Args:
            topic: 文章主题
            style: 文章风格
            writing_guide: 写作指南
            reasoning: 核心逻辑
            articles: 文章列表
            ext_info: 背景补全信息
            history_memory: 历史记忆
            review: 审查结果（用于修改）

        Returns:
            Markdown 格式的文章内容
        """
        # 直接构建 prompt 并调用 client
        prompt = self._build_prompt(writing_material, review)
        result = await self.client.completion(prompt)
        return result

    def _build_prompt(
        self, writing_material: WritingMaterial, review: AgentCriticResult | None = None
    ) -> str | list[Message]:
        """构建写作 prompt"""
        if writing_material["style"] == "FLASH":
            return WRITER_FLASH_NEWS_PROMPT.format(
                topic=writing_material["topic"],
                articles=writing_material["articles"],
            )

        ext_info = (
            writing_material["ext_info"]
            if "ext_info" in writing_material and writing_material["ext_info"]
            else []
        )
        # history_memory 现在统一为列表
        history_memories = writing_material.get("history_memory", [])
        system_prompt = Message(
            role="system",
            content=WRITER_DEEP_DIVE_SYSTEM_PROMPT_TEMPLATE.format(
                relevance_to_focus=writing_material["relevance_to_focus"],
                topic=writing_material["topic"],
            ),
        )
        user_prompt = Message(
            role="user",
            content=WRITER_DEEP_DIVE_USER_PROMPT_TEMPLATE.format(
                topic=writing_material["topic"],
                match_type=writing_material["match_type"],
                relevance_to_focus=writing_material["relevance_to_focus"],
                writing_guide=writing_material["writing_guide"],
                reasoning=writing_material["reasoning"],
                articles=writing_material["articles"],
                ext_info=ext_info,
                history_memories=history_memories,
                review=review if review else "",
            ),
        )
        system_prompt.set_priority(0)
        user_prompt.set_priority(0)
        return [
            system_prompt,
            user_prompt,
        ]


class ReviewArticleTool(BaseTool[AgentCriticResult]):
    """审查文章的工具"""

    def __init__(self, client: AIGenerator):
        self.client = client

    @property
    def name(self) -> str:
        return "review_article"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "审查文章初稿，检查事实准确性、逻辑性和完整性。"
                "返回审查结果，包含状态（APPROVED/REJECTED）、评分、发现的问题和修改建议。"
                "如果发现 CRITICAL 错误，必须返回 REJECTED 状态。"
            ),
            parameters=[
                ToolParameter(
                    name="draft_content",
                    type="str",
                    description="待审查的文章初稿内容（Markdown 格式）",
                    required=True,
                ),
                ToolParameter(
                    name="writing_material",
                    type="WritingMaterial",
                    description=(
                        "写作素材对象（推荐用法）。critic 会基于其中的 match_type/relevance_to_focus 做一致性审查。"
                        "注意：审查时 material.style 通常为 DEEP。"
                    ),
                    required=True,
                ),
            ],
        )

    async def _execute(
        self,
        draft_content: str,
        writing_material: WritingMaterial,
    ) -> AgentCriticResult:
        """
        审查文章

        Args:
            draft_content: 待审查的文章初稿
            topic: 文章主题
            writing_guide: 写作指南
            articles: 原始文章列表
            ext_info: 背景补全信息
            history_memory: 历史记忆

        Returns:
            审查结果
        """
        prompt = self._build_prompt(draft_content, writing_material)

        response = await self.client.completion(prompt)
        try:
            result: AgentCriticResult = extract_json(response)
            logger.info(
                "Parsed critic response successfully, status: %s", result.get("status")
            )
            return result
        except Exception as e:
            # Log a truncated version to avoid huge log entries
            response_preview = (
                response[:500] + "..." if len(response) > 500 else response
            )
            logger.error(
                "Failed to parse critic response. Error: %s\nResponse preview: %s",
                str(e),
                response_preview,
                exc_info=True,
            )
            print(response)
            raise ValueError(f"Failed to parse critic response: {str(e)}") from e

    def _build_prompt(
        self, draft_content: str, writing_material: WritingMaterial
    ) -> list[Message]:
        """构建审查 prompt"""
        system_prompt = Message(role="system", content=CRITIC_SYSTEM_PROMPT_TEMPLATE)
        system_prompt.set_priority(0)
        user_prompt = Message(
            role="user",
            content=CRITIC_USER_PROMPT_TEMPLATE.format(
                draft_content=draft_content,
                articles=writing_material["articles"],
                ext_info=writing_material.get("ext_info", []),
                history_memories=writing_material.get("history_memory", []),
                match_type=writing_material["match_type"],
                relevance_to_focus=writing_material["relevance_to_focus"],
                writing_guide=writing_material["writing_guide"],
            ),
        )
        user_prompt.set_priority(0)
        return [
            system_prompt,
            user_prompt,
        ]
