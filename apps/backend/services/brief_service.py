import asyncio
import datetime
import json
import logging
import re

from core.db.pool import get_connection
from core.models.feed import FeedBrief

logger = logging.getLogger(__name__)


def _extract_h2_headings(content: str) -> str:
    """从内容中提取所有二级标题（## 开头的行）作为概要"""
    headings = []
    lines = content.split("\n")
    for line in lines:
        trimmed = line.strip()
        # 匹配二级标题：## 标题
        match = re.match(r"^##\s+(.+)$", trimmed)
        if match:
            headings.append(match.group(1).strip())
    return "\n".join(headings) if headings else ""


def _replace_reference(brief_id: int, content: str) -> str:
    """替换内容中的引用标记为实际的 URL 链接

    Args:
        brief_id: 简报ID
        content: 简报内容

    Returns:
        替换后的内容
    """

    def _find_reference(prefix: str) -> list[str]:
        """从内容中提取指定前缀的引用ID列表"""
        pattern = rf"\[{prefix}:([^\]]+)\]"
        return re.findall(pattern, content)

    def _markdown_link_replacer(pattern: str, url_map: dict[str, tuple[str, str]]) -> callable:
        """创建 Markdown 链接替换函数

        Args:
            pattern: 正则表达式模式
            url_map: 映射字典，key 为引用ID，value 为 (title, url) 元组
        """

        def replacer(match: re.Match) -> str:
            key = match.group(1)
            value = url_map.get(key)
            if value:
                title, url = value
                if url:
                    return f"[{title}]({url})"
            return match.group(0)

        return lambda text: re.sub(pattern, replacer, text)

    # 提取所有引用ID
    article_ids = _find_reference("rss")

    # 初始化URL映射 (key: 引用ID, value: (title, url) 元组)
    article_urls: dict[str, tuple[str, str]] = {}
    ext_info_map: dict[str, tuple[str, str]] = {}

    # SQL 查询外部信息
    SQL_EXT_INFO_TITLE_URL = """
        SELECT
            elem->>'title' AS title,
            elem->>'url'   AS url
        FROM feed_brief fb
        CROSS JOIN LATERAL jsonb_array_elements(
            CASE
                WHEN fb.ext_info IS NULL THEN '[]'::jsonb
                WHEN jsonb_typeof(fb.ext_info) = 'array' THEN fb.ext_info
                ELSE '[]'::jsonb
            END
        ) AS elem
        WHERE fb.id = %s
          AND elem ? 'title'
          AND elem ? 'url'
          AND elem->>'title' <> ''
          AND elem->>'url' <> '';
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 查询文章URL（仅在有关联文章时查询）
                if article_ids:
                    cur.execute(
                        """SELECT id, title, link FROM feed_items WHERE id = ANY(%s::text[])""",
                        (article_ids,),
                    )
                    article_urls = {str(row[0]): (row[1], row[2]) for row in cur.fetchall()}
                    logger.debug(
                        "Found %d/%d article URLs for brief %d",
                        len(article_urls),
                        len(article_ids),
                        brief_id,
                    )

                # 查询外部搜索结果URL
                cur.execute(SQL_EXT_INFO_TITLE_URL, (brief_id,))
                ext_info_map = {row[0]: (row[0], row[1]) for row in cur.fetchall()}
                if ext_info_map:
                    logger.debug(
                        f"Found {len(ext_info_map)} external info URLs for brief {brief_id}"
                    )
    except Exception as e:
        logger.error(f"Error querying URLs for brief {brief_id}: {e}", exc_info=True)
        # 查询失败时继续执行，只是没有URL替换

    # 替换 [rss:xxx] 为 Markdown 链接
    content = _markdown_link_replacer(r"\[rss:([^\]]+)\]", article_urls)(content)

    # 替换 [ext:xxx] 为 Markdown 链接
    content = _markdown_link_replacer(r"\[ext:([^\]]+)\]", ext_info_map)(content)

    # 替换 [memory:xxx] 为历史总结链接
    content = re.sub(
        r"\[memory:([^\]]+)\]",
        lambda match: f"[历史总结{match.group(1)}](/memory/{match.group(1)})",
        content,
    )

    return content


def get_briefs(
    start_date: datetime.date, end_date: datetime.date, include_content: bool = False
):
    """获取简报列表

    Args:
        start_date: 开始日期
        end_date: 结束日期
        include_content: 是否包含完整内容（content 和 ext_info），默认 False
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if include_content:
                # 包含完整内容
                cur.execute(
                    """SELECT id, content, created_at, group_ids, summary, ext_info
                       FROM feed_brief
                       WHERE created_at::date BETWEEN %s AND %s
                       ORDER BY id DESC""",
                    (start_date, end_date),
                )
                return [
                    FeedBrief(
                        id=row[0],
                        content=row[1],
                        pub_date=row[2],
                        group_ids=row[3],
                        summary=row[4] or "",
                        ext_info=row[5] if row[5] else [],
                    )
                    for row in cur.fetchall()
                ]
            else:
                # 不包含完整内容，只返回基本信息
                cur.execute(
                    """SELECT id, created_at, group_ids, summary
                       FROM feed_brief
                       WHERE created_at::date BETWEEN %s AND %s
                       ORDER BY id DESC""",
                    (start_date, end_date),
                )
                return [
                    FeedBrief(
                        id=row[0],
                        content="",  # 列表页不返回内容
                        pub_date=row[1],
                        group_ids=row[2],
                        summary=row[3] or "",
                        ext_info=[],  # 列表页不返回外部信息
                    )
                    for row in cur.fetchall()
                ]


def get_brief_by_id(brief_id: int) -> FeedBrief | None:
    """根据ID获取单个简报的完整信息"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, content, created_at, group_ids, ext_info
                   FROM feed_brief
                   WHERE id = %s""",
                (brief_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return FeedBrief(
                id=row[0],
                content=_replace_reference(brief_id, row[1]),
                pub_date=row[2],
                group_ids=row[3],
                ext_info=row[4] if row[4] else [],
            )


def generate_brief_for_groups(group_ids: list[int], focus: str = ""):
    """
    Generate brief for specific groups with optional focus.
    Synchronous version for scheduled tasks.
    """
    if not group_ids:
        raise ValueError("group_ids cannot be empty")

    # 延迟导入避免循环依赖
    from agent import get_agent

    logger.info(f"Generating brief for groups {group_ids} with focus: {focus}")
    brief, ext_info = asyncio.run(get_agent().summarize(24, group_ids, focus))
    if not brief:
        logger.warning("No brief generated for groups %s", group_ids)
        return
    _insert_brief(group_ids, brief, ext_info)
    logger.info("Brief generation completed for groups %s", group_ids)


async def generate_brief_for_groups_async(
    group_ids: list[int], focus: str = "", on_step=None, boost_mode: bool = False
):
    """
    Generate brief for specific groups asynchronously with optional step callback.
    Returns the generated brief content.

    Args:
        group_ids: 分组ID列表（boost_mode 时可以为空）
        focus: 用户关注点
        on_step: 步骤回调函数
        boost_mode: 是否使用 BoostAgent（True）或原 workflow（False）
    """
    # BoostMode 需要填写 focus
    if boost_mode and not focus.strip():
        raise ValueError("focus cannot be empty when boost_mode is true")

    # BoostMode 不需要 group_ids，原模式需要至少一个分组
    if not boost_mode and not group_ids:
        raise ValueError("group_ids cannot be empty when boost_mode is false")

    logger.info(
        f"Generating brief for groups {group_ids} with focus: {focus}, boost_mode: {boost_mode}"
    )

    if boost_mode:
        # 使用 BoostAgent（BoostAgent 会自主选择所有可用的订阅源，不受 group_ids 限制）
        from agent import get_boost_agent

        agent = get_boost_agent()
        brief, ext_info = await agent.run(focus=focus, hour_gap=24, on_step=on_step)
        # BoostMode 时使用空数组作为 group_ids 保存到数据库
        save_group_ids = []
    else:
        # 使用原 workflow
        from agent import get_agent

        brief, ext_info = await get_agent().summarize(
            24, group_ids, focus, on_step=on_step
        )
        save_group_ids = group_ids
    if not brief:
        logger.warning("No brief generated for groups %s", group_ids)
        return ""
    _insert_brief(save_group_ids, brief, ext_info)
    logger.info("Brief generation completed for groups %s", save_group_ids)
    return brief


def _insert_brief(group_ids: list[int], brief: str, ext_info: list = None):
    """插入简报到数据库

    Args:
        group_ids: 分组ID列表
        brief: 简报内容
        ext_info: 外部搜索结果列表（SearchResult 对象或字典）
    """
    # 提取二级标题作为概要
    summary = _extract_h2_headings(brief)

    # 处理外部搜索结果：转换为可序列化的字典格式
    ext_info_list = []
    if ext_info:
        for item in ext_info:
            if isinstance(item, dict):
                # 已经是字典（TypedDict 或普通字典）
                ext_info_list.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                        "score": item.get("score", 0.0),
                    }
                )
            elif hasattr(item, "to_dict"):
                # 有 to_dict 方法的对象
                ext_info_list.append(item.to_dict())
            else:
                # 其他类型，尝试转换为字典
                ext_info_list.append(
                    {
                        "title": getattr(item, "title", ""),
                        "url": getattr(item, "url", ""),
                        "content": getattr(item, "content", ""),
                        "score": getattr(item, "score", 0.0),
                    }
                )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO feed_brief (group_ids, content, summary, ext_info) 
                   VALUES (%s::integer[], %s, %s, %s::jsonb)""",
                (group_ids, brief, summary, json.dumps(ext_info_list)),
            )
