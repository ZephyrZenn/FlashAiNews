from typing import Tuple, List

from agent.tools.base import BaseTool, ToolSchema, ToolParameter
from core.db.pool import get_async_connection
from core.models.feed import FeedGroup, Feed
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
                "确保返回的都是尚未使用过的新鲜内容。返回一个元组 (groups, articles)。"
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

                # 查询 2: 获取文章数据
                await cur.execute(
                    """
                    SELECT
                        fi.id, fi.title, fi.link, fi.summary, fi.pub_date,
                        fic.content
                    FROM feed_items fi
                    JOIN feed_group_items fgi ON fgi.feed_id = fi.feed_id
                    JOIN feed_item_contents fic ON fic.feed_item_id = fi.id
                    WHERE fgi.feed_group_id = ANY(%s)
                      AND fi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                      AND NOT EXISTS (
                          SELECT 1
                          FROM excluded_feed_item_ids efi
                          WHERE efi.id = fi.id
                            AND efi.group_ids @> %s::integer[] AND efi.group_ids <@ %s::integer[]
                            AND efi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                      );
                    """,
                    (group_ids, hour_gap, group_ids, group_ids, hour_gap),
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
                    )
                    for row in item_rows
                ]

                return groups, items


class GetAllFeedsTool(BaseTool[List[Feed]]):
    """获取所有订阅源的工具"""

    @property
    def name(self) -> str:
        return "get_all_feeds"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "获取系统中所有可用的订阅源列表。"
                "每个订阅源包含 id、title、url、description 等信息，用于了解可用的信息源。"
                "返回 list[Feed]，包含所有订阅源信息。"
            ),
            parameters=[],
        )

    async def _execute(self) -> List[Feed]:
        """
        获取所有订阅源

        Returns:
            订阅源列表
        """
        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT id, title, url, last_updated, description, "limit" FROM feeds ORDER BY id ASC"""
                )
                rows = await cur.fetchall()
                feeds = [
                    Feed(
                        id=row[0],
                        title=row[1],
                        url=row[2],
                        last_updated=row[3],
                        desc=row[4] or "",
                        limit=row[5] or 10,
                    )
                    for row in rows
                ]
                return feeds


class GetRecentFeedUpdateTool(BaseTool[Tuple[List[Feed], List[RawArticle]]]):
    """根据订阅源ID获取最近更新的文章的工具"""

    @property
    def name(self) -> str:
        return "get_recent_feed_update"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "从数据库中获取指定订阅源在指定时间范围内的最新文章摘要。"
                "返回一个元组 (feeds, articles)，其中 articles 只包含摘要信息（id、title、url、summary、pub_date），不包含全文内容。"
                "如果需要获取文章的完整内容，请使用 get_article_content 工具。"
                "注意：此工具不会过滤已处理过的文章，会返回所有符合条件的文章。"
            ),
            parameters=[
                ToolParameter(
                    name="hour_gap",
                    type="int",
                    description="时间范围，以小时为单位。例如 hour_gap=24 表示获取过去24小时内的文章",
                    required=True,
                ),
                ToolParameter(
                    name="feed_ids",
                    type="list[int]",
                    description="要查询的订阅源ID列表。每个订阅源代表一个特定的信息源（如某个博客、新闻网站等）",
                    required=True,
                ),
            ],
        )

    async def _execute(
        self, hour_gap: int, feed_ids: list[int]
    ) -> Tuple[List[Feed], List[RawArticle]]:
        """
        获取最近更新的订阅源及其文章

        Args:
            hour_gap: 时间间隔（小时）
            feed_ids: 订阅源ID列表

        Returns:
            (订阅源列表, 文章列表)
        """
        if not feed_ids:
            return [], []

        if hour_gap <= 0:
            raise ValueError("hour_gap 必须大于 0")

        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                # 查询 1: 获取 feeds
                await cur.execute(
                    """SELECT id, title, url, last_updated, description, "limit" FROM feeds WHERE id = ANY(%s)""",
                    (feed_ids,),
                )
                feed_rows = await cur.fetchall()
                feeds = [
                    Feed(
                        id=row[0],
                        title=row[1],
                        url=row[2],
                        last_updated=row[3],
                        desc=row[4] or "",
                        limit=row[5] or 10,
                    )
                    for row in feed_rows
                ]

                if not feeds:
                    return [], []

                # 查询 2: 获取文章摘要（不包含全文内容，避免上下文窗口被挤爆）
                await cur.execute(
                    """
                    SELECT
                        fi.id, fi.title, fi.link, fi.summary, fi.pub_date
                    FROM feed_items fi
                    WHERE fi.feed_id = ANY(%s)
                      AND fi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                    ORDER BY fi.pub_date DESC;
                    """,
                    (feed_ids, hour_gap),
                )

                item_rows = await cur.fetchall()
                items = [
                    RawArticle(
                        id=str(row[0]),
                        title=row[1],
                        url=row[2],
                        summary=row[3] or "",
                        pub_date=row[4],
                        # 不包含 content 字段，只返回摘要
                    )
                    for row in item_rows
                ]

                return feeds, items


class GetArticleContentTool(BaseTool[dict[str, str]]):
    """根据文章ID获取完整内容的工具"""

    @property
    def name(self) -> str:
        return "get_article_content"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "根据文章ID列表获取这些文章的完整内容。"
                "返回一个字典，key 是文章ID（字符串），value 是文章的完整内容（字符串）。"
                "如果某个文章ID不存在或没有内容，该ID对应的值为空字符串。"
                "建议只在需要详细内容时才调用此工具，避免上下文窗口过大。"
            ),
            parameters=[
                ToolParameter(
                    name="article_ids",
                    type="list[str]",
                    description="要获取内容的文章ID列表。可以是字符串或数字，系统会自动转换",
                    required=True,
                ),
            ],
        )

    async def _execute(self, article_ids: list[str]) -> dict[str, str]:
        """
        获取指定文章的完整内容

        Args:
            article_ids: 文章ID列表

        Returns:
            字典，key 是文章ID（字符串），value 是文章内容（字符串）
        """
        if not article_ids:
            return {}

        # 将 ID 转换为整数（数据库中的 ID 是整数）
        try:
            int_ids = [int(aid) for aid in article_ids]
        except (ValueError, TypeError):
            return {}

        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        fi.id, fic.content
                    FROM feed_items fi
                    JOIN feed_item_contents fic ON fic.feed_item_id = fi.id
                    WHERE fi.id = ANY(%s);
                    """,
                    (int_ids,),
                )

                rows = await cur.fetchall()
                # 构建字典，key 是字符串ID，value 是内容
                result = {str(row[0]): (row[1] or "") for row in rows}
                
                # 确保所有请求的 ID 都在结果中（不存在的设为空字符串）
                for aid in article_ids:
                    if aid not in result:
                        result[aid] = ""
                
                return result


# 创建工具实例
recent_group_update_tool = RecentGroupUpdateTool()
get_all_feeds_tool = GetAllFeedsTool()
get_recent_feed_update_tool = GetRecentFeedUpdateTool()
get_article_content_tool = GetArticleContentTool()


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

async def get_article_content(article_ids: list[str]) -> dict[str, str]:
    """获取文章内容（兼容函数）"""
    result = await get_article_content_tool.execute(article_ids)
    if result.success:
        return result.data
    raise RuntimeError(result.error)