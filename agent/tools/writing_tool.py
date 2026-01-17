"""写作和审查工具

直接实现写作和审查功能，不依赖 pipeline 中的 writer 和 critic
"""

import logging
from typing import Literal

from agent.tools.base import BaseTool, ToolSchema, ToolParameter
from agent.models import (
    WritingMaterial,
    AgentCriticResult,
    RawArticle,
    SummaryMemory,
)
from agent.prompts import (
    WRITER_FLASH_NEWS_PROMPT,
    WRITER_DEEP_DIVE_PROMPT_TEMPLATE,
    CRITIC_PROMPT_TEMPLATE,
)
from agent.utils import extract_json
from core.brief_generator import AIGenerator
from core.models.search import SearchResult

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
                    name="topic",
                    type="str",
                    description="文章主题/标题",
                    required=True,
                ),
                ToolParameter(
                    name="style",
                    type="Literal['DEEP', 'FLASH']",
                    description="文章风格：DEEP（深度文章）或 FLASH（快讯）",
                    required=True,
                ),
                ToolParameter(
                    name="writing_guide",
                    type="str",
                    description="写作指南，告诉撰稿人写作侧重点（如：对比不同来源的立场差异）",
                    required=True,
                ),
                ToolParameter(
                    name="reasoning",
                    type="str",
                    description="核心逻辑，解释文章间的潜在联系或重要性",
                    required=True,
                ),
                ToolParameter(
                    name="articles",
                    type="list[str]",
                    description="文章ID列表，系统会自动从上下文中获取完整的文章信息。也可以传递完整的文章对象数组（包含 id、title、url、summary、content 等字段）",
                    required=True,
                ),
                ToolParameter(
                    name="ext_info",
                    type="list[dict]",
                    description="背景补全信息（可选），从网络搜索获取的补充内容，每个对象包含 title、url、content 等字段",
                    required=False,
                ),
                ToolParameter(
                    name="history_memory",
                    type="list[dict]",
                    description="历史记忆列表（可选），每个对象包含 id、topic、reasoning、content 等字段。也可以传递 id 列表（数字或字符串），系统会自动获取完整信息",
                    required=False,
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
        topic: str,
        style: Literal["DEEP", "FLASH"],
        writing_guide: str,
        reasoning: str,
        articles: list[RawArticle],
        ext_info: list[SearchResult] | None = None,
        history_memory: list[SummaryMemory] | None = None,
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
        writing_material = WritingMaterial(
            topic=topic,
            style=style,
            writing_guide=writing_guide,
            reasoning=reasoning,
            articles=articles,
        )

        if ext_info:
            writing_material["ext_info"] = ext_info

        if history_memory:
            writing_material["history_memory"] = history_memory  # 现在已经是列表

        # 直接构建 prompt 并调用 client
        prompt = self._build_prompt(writing_material, review)
        result = await self.client.completion(prompt)
        return result

    def _build_prompt(
        self, writing_material: WritingMaterial, review: AgentCriticResult | None = None
    ) -> str:
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

        return WRITER_DEEP_DIVE_PROMPT_TEMPLATE.format(
            topic=writing_material["topic"],
            writing_guide=writing_material["writing_guide"],
            reasoning=writing_material["reasoning"],
            articles=writing_material["articles"],
            ext_info=ext_info,
            review=review if review else "",
            history_memories=history_memories,
        )


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
                    name="topic",
                    type="str",
                    description="文章主题",
                    required=True,
                ),
                ToolParameter(
                    name="writing_guide",
                    type="str",
                    description="原始写作指南，用于对比检查",
                    required=True,
                ),
                ToolParameter(
                    name="articles",
                    type="list[str]",
                    description="文章ID列表，系统会自动从上下文中获取完整的文章信息用于事实核查。也可以传递完整的文章对象数组",
                    required=True,
                ),
                ToolParameter(
                    name="ext_info",
                    type="list[dict]",
                    description="背景补全信息（可选），用于核查补充内容，每个对象包含 title、url、content 等字段",
                    required=False,
                ),
                ToolParameter(
                    name="history_memory",
                    type="list[dict]",
                    description="历史记忆列表（可选），用于检查历史连贯性，每个对象包含 id、topic、reasoning、content 等字段。也可以传递 id 列表",
                    required=False,
                ),
            ],
        )

    async def _execute(
        self,
        draft_content: str,
        topic: str,
        writing_guide: str,
        articles: list[RawArticle],
        ext_info: list[SearchResult] | None = None,
        history_memory: list[SummaryMemory] | None = None,
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
        writing_material = WritingMaterial(
            topic=topic,
            style="DEEP",  # 审查主要针对深度文章
            writing_guide=writing_guide,
            reasoning="",
            articles=articles,
        )

        if ext_info:
            writing_material["ext_info"] = ext_info

        if history_memory:
            writing_material["history_memory"] = history_memory  # 现在已经是列表

        # 直接构建 prompt 并调用 client
        source_material = {
            "articles": writing_material["articles"],
            "ext_info": writing_material.get("ext_info", []),
        }
        # history_memory 现在统一为列表
        history_memories = writing_material.get("history_memory", [])
        
        prompt = CRITIC_PROMPT_TEMPLATE.format(
            draft_content=draft_content,
            source_material=source_material,
            original_guide=writing_material["writing_guide"],
            history_memories=history_memories,
        )
        
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
            raise ValueError(f"Failed to parse critic response: {str(e)}") from e
