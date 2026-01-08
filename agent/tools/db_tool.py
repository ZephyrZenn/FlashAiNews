from typing import Tuple, List

from agent.tools.base import BaseTool, ToolSchema, ToolParameter
from core.db.pool import get_async_connection
from core.models.feed import FeedGroup
from agent.models import RawArticle


class RecentGroupUpdateTool(BaseTool[Tuple[List[FeedGroup], List[RawArticle]]]):
    """获取最近更新的分组及其文章的工具"""

    @property
    def name(self) -> str:
        return "get_recent_group_update"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "从数据库中获取指定分组在指定时间范围内的最新文章。"
                "该工具会自动过滤掉已经被处理过的文章（通过 excluded_feed_item_ids 表），"
                "确保返回的都是尚未使用过的新鲜内容。"
            ),
            parameters=[
                ToolParameter(
                    name="hour_gap",
                    type="int",
                    description="时间范围，以小时为单位。例如 hour_gap=24 表示获取过去24小时内的文章",
                    required=True,
                ),
                ToolParameter(
                    name="group_ids",
                    type="list[int]",
                    description="要查询的分组ID列表。每个分组代表一个特定的信息源类别（如科技、财经等）",
                    required=True,
                ),
            ],
            returns=(
                "返回一个元组 (groups, articles):\n"
                "  - groups: FeedGroup 对象列表，包含分组的 id、title、desc\n"
                "  - articles: RawArticle 对象列表，包含文章的 id、title、url、summary、pub_date、content、group_title"
            ),
            when_to_use=(
                "当需要获取最新的新闻资讯进行摘要生成、热点分析或内容聚合时使用。"
                "这是 Agent 工作流的起始步骤，用于收集待处理的原始文章数据。"
            ),
            usage_examples=[
                "get_recent_group_update(hour_gap=12, group_ids=[1, 2, 3]) - 获取过去12小时内分组1/2/3的文章",
                "get_recent_group_update(hour_gap=24, group_ids=[5]) - 获取过去24小时内分组5的文章",
            ],
            notes=[
                "如果指定的分组ID不存在，对应的分组会被忽略",
                "已处理过的文章会被自动排除，避免重复处理",
                "返回的文章按发布时间排序",
            ],
        )

    async def _execute(
        self, hour_gap: int, group_ids: list[int]
    ) -> Tuple[List[FeedGroup], List[RawArticle]]:
        """
        获取最近更新的分组及其文章

        Args:
            hour_gap: 时间间隔（小时）
            group_ids: 分组ID列表

        Returns:
            (分组列表, 文章列表)
        """
        if not group_ids:
            return [], []

        if hour_gap <= 0:
            raise ValueError("hour_gap 必须大于 0")

        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                # 查询 1: 获取 groups
                await cur.execute(
                    """SELECT id, title, "desc" FROM feed_groups WHERE id = ANY(%s)""",
                    (group_ids,),
                )
                group_rows = await cur.fetchall()
                groups = [
                    FeedGroup(id=row[0], title=row[1], desc=row[2])
                    for row in group_rows
                ]

                if not groups:
                    return [], []

                # 查询 2: 一次性获取所有数据，使用 JOIN 和 array_agg
                await cur.execute(
                    """
                    WITH group_map AS (
                        SELECT
                            fgi.feed_id,
                            array_agg(DISTINCT fg.title) AS group_titles
                        FROM feed_group_items fgi
                        JOIN feed_groups fg ON fg.id = fgi.feed_group_id
                        WHERE fgi.feed_group_id = ANY(%s)
                        GROUP BY fgi.feed_id
                    )
                    SELECT
                    fi.id, fi.title, fi.link, fi.summary, fi.pub_date,
                    fic.content,
                    gm.group_titles
                    FROM feed_items fi
                    JOIN group_map gm ON gm.feed_id = fi.feed_id
                    JOIN feed_item_contents fic ON fic.feed_item_id = fi.id
                    WHERE fi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM excluded_feed_item_ids efi
                        WHERE efi.id = fi.id
                        AND efi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                    );
                    """,
                    (group_ids, hour_gap, hour_gap),
                )

                item_rows = await cur.fetchall()
                items = [
                    RawArticle(
                        id=row[0],
                        title=row[1],
                        url=row[2],
                        summary=row[3],
                        pub_date=row[4],
                        content=row[5],
                        group_title=row[6],
                    )
                    for row in item_rows
                ]

                return groups, items


# 创建工具实例
recent_group_update_tool = RecentGroupUpdateTool()


# 保留原有函数接口以兼容现有代码
async def get_recent_group_update(
    hour_gap: int, group_ids: list[int]
) -> Tuple[List[FeedGroup], List[RawArticle]]:
    """获取最近更新的分组及其文章（兼容函数）

    注意：此函数为兼容接口，直接返回数据而非 ToolResult。
    新代码建议使用 recent_group_update_tool.execute() 获取带错误处理的结果。
    """
    result = await recent_group_update_tool.execute(hour_gap, group_ids)
    if result.success:
        return result.data
    raise RuntimeError(result.error)
