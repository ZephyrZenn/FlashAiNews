from typing import Literal

from agent.artifact_store import ArtifactStore
from agent.tools.base import BaseTool, ToolParameter, ToolSchema, ToolResult
from agent.tools.writing_tool import ReviewArticleTool, WriteArticleTool


class BoostWriteArticleTool(BaseTool[dict]):
    """Boost 专用写作工具：内部调用原始写作工具，保存全文为 artifact，仅返回句柄+摘要。"""

    def __init__(self, client, artifact_store: ArtifactStore):
        self.client = client
        self.artifact_store = artifact_store
        self._write_tool = WriteArticleTool(client)

    @property
    def name(self) -> str:
        return "boost_write_article"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "撰写文章（DEEP/FLASH），返回 artifact 句柄+摘要，不直接返回全文。"
            ),
            parameters=[
                ToolParameter(name="topic", type="str", description="文章主题/标题"),
                ToolParameter(
                    name="style",
                    type="Literal['DEEP', 'FLASH']",
                    description="文章风格：DEEP 或 FLASH",
                ),
                ToolParameter(
                    name="writing_guide",
                    type="str",
                    description="写作指南，说明侧重点",
                ),
                ToolParameter(name="reasoning", type="str", description="核心逻辑"),
                ToolParameter(
                    name="articles",
                    type="list[str]",
                    description="文章 ID 或完整文章对象列表",
                ),
                ToolParameter(
                    name="ext_info",
                    type="list[dict]",
                    description="可选，补充信息列表",
                    required=False,
                ),
                ToolParameter(
                    name="history_memory",
                    type="list[dict]",
                    description="可选，历史记忆列表",
                    required=False,
                ),
                ToolParameter(
                    name="review",
                    type="dict",
                    description="可选，审查结果（可传 artifact_id 或完整对象）",
                    required=False,
                ),
            ],
        )

    async def _execute(  # pylint: disable=arguments-differ
        self,
        topic: str,
        style: Literal["DEEP", "FLASH"],
        writing_guide: str,
        reasoning: str,
        articles,
        ext_info=None,
        history_memory=None,
        review=None,
    ) -> dict:
        result: ToolResult = await self._write_tool.execute(
            topic=topic,
            style=style,
            writing_guide=writing_guide,
            reasoning=reasoning,
            articles=articles,
            ext_info=ext_info,
            history_memory=history_memory,
            review=review,
        )
        if not result.success:
            raise RuntimeError(f"写作失败: {result.error}")

        meta = {"topic": topic, "style": style}
        return self.artifact_store.put(
            artifact_type=self.name, content=result.data, meta=meta
        )


class BoostReviewArticleTool(BaseTool[dict]):
    """Boost 专用审查工具：内部调用原始审查工具，保存全文为 artifact，仅返回句柄+摘要。"""

    def __init__(self, client, artifact_store: ArtifactStore):
        self.client = client
        self.artifact_store = artifact_store
        self._review_tool = ReviewArticleTool(client)

    @property
    def name(self) -> str:
        return "boost_review_article"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description="审查文章，返回 artifact 句柄+摘要，不直接返回完整审查结果。",
            parameters=[
                ToolParameter(
                    name="draft_content",
                    type="str",
                    description="待审查的文章内容（可传 artifact_id）",
                ),
                ToolParameter(name="topic", type="str", description="文章主题"),
                ToolParameter(
                    name="writing_guide",
                    type="str",
                    description="原始写作指南",
                ),
                ToolParameter(
                    name="articles",
                    type="list[str]",
                    description="文章 ID 或完整文章对象列表",
                ),
                ToolParameter(
                    name="ext_info",
                    type="list[dict]",
                    description="可选，补充信息列表",
                    required=False,
                ),
                ToolParameter(
                    name="history_memory",
                    type="list[dict]",
                    description="可选，历史记忆列表",
                    required=False,
                ),
            ],
        )

    async def _execute(  # pylint: disable=arguments-differ
        self,
        draft_content: str,
        topic: str,
        writing_guide: str,
        articles,
        ext_info=None,
        history_memory=None,
    ) -> dict:
        result: ToolResult = await self._review_tool.execute(
            draft_content=draft_content,
            topic=topic,
            writing_guide=writing_guide,
            articles=articles,
            ext_info=ext_info,
            history_memory=history_memory,
        )
        if not result.success:
            raise RuntimeError(f"审查失败: {result.error}")

        meta = {"topic": topic}
        return self.artifact_store.put(
            artifact_type=self.name, content=result.data, meta=meta
        )
