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
                ToolParameter(
                    name="writing_material",
                    type="WritingMaterial",
                    description="写作素材对象（topic/style/match_type/relevance_to_focus/writing_guide/reasoning/articles...）",
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
        writing_material,
        review=None,
    ) -> dict:
        result: ToolResult = await self._write_tool.execute(
            writing_material=writing_material,
            review=review,
        )
        if not result.success:
            raise RuntimeError(f"写作失败: {result.error}")

        meta = {"topic": writing_material.get("topic"), "style": writing_material.get("style")}
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
                ToolParameter(
                    name="writing_material",
                    type="WritingMaterial",
                    description="写作素材对象（topic/match_type/relevance_to_focus/writing_guide/articles...）",
                ),
            ],
        )

    async def _execute(  # pylint: disable=arguments-differ
        self,
        draft_content: str,
        writing_material,
    ) -> dict:
        result: ToolResult = await self._review_tool.execute(
            draft_content=draft_content,
            writing_material=writing_material,
        )
        if not result.success:
            raise RuntimeError(f"审查失败: {result.error}")

        meta = {"topic": writing_material.get("topic")}
        return self.artifact_store.put(
            artifact_type=self.name, content=result.data, meta=meta
        )
