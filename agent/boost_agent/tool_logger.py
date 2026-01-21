"""工具调用日志记录模块

提供工具调用的用户友好日志记录功能，不暴露内部函数名称。
"""

from typing import Any

# 工具名称到用户友好描述的映射（不暴露函数名）
_TOOL_DESCRIPTIONS = {
    "get_recent_group_update": "获取最新文章",
    "get_all_feeds": "获取所有订阅源",
    "get_recent_feed_update": "获取订阅源更新",
    "get_article_content": "获取文章内容",
    "search_memory": "搜索历史记忆",
    "save_execution_records": "保存执行记录",
    "backfill_embeddings": "补全向量嵌入",
    "fetch_web_contents": "抓取网页内容",
    "search_web": "搜索网络内容",
    "find_keywords": "提取关键词",
    "write_article": "撰写文章",
    "review_article": "审查文章",
    "boost_write_article": "撰写文章",
    "boost_review_article": "审查文章",
}


def get_tool_description(tool_name: str) -> str:
    """获取工具的用户友好描述"""
    return _TOOL_DESCRIPTIONS.get(tool_name, "执行操作")


def format_tool_args_summary(tool_name: str, tool_args: dict) -> str:
    """格式化工具参数摘要（不暴露敏感信息）"""
    summary_parts = []

    # 根据工具类型提取关键参数
    if tool_name in ("get_recent_group_update", "get_recent_feed_update"):
        if "hour_gap" in tool_args:
            summary_parts.append(f"时间范围: {tool_args['hour_gap']}小时")
        if "group_ids" in tool_args:
            count = (
                len(tool_args["group_ids"])
                if isinstance(tool_args["group_ids"], list)
                else 1
            )
            summary_parts.append(f"分组数: {count}")
        if "feed_ids" in tool_args:
            count = (
                len(tool_args["feed_ids"])
                if isinstance(tool_args["feed_ids"], list)
                else 1
            )
            summary_parts.append(f"订阅源数: {count}")

    elif tool_name == "get_article_content":
        if "article_ids" in tool_args:
            count = (
                len(tool_args["article_ids"])
                if isinstance(tool_args["article_ids"], list)
                else 1
            )
            summary_parts.append(f"文章数: {count}")

    elif tool_name == "search_memory":
        if "query" in tool_args:
            query = str(tool_args["query"])[:50]
            summary_parts.append(f"查询: {query}...")
        if "max_results" in tool_args:
            summary_parts.append(f"最大结果数: {tool_args['max_results']}")

    elif tool_name in ("fetch_web_contents", "search_web"):
        if "urls" in tool_args:
            count = len(tool_args["urls"]) if isinstance(tool_args["urls"], list) else 1
            summary_parts.append(f"URL数: {count}")
        if "query" in tool_args:
            query = str(tool_args["query"])[:50]
            summary_parts.append(f"查询: {query}...")
        if "max_results" in tool_args:
            summary_parts.append(f"最大结果数: {tool_args['max_results']}")

    elif tool_name == "find_keywords":
        if "articles" in tool_args:
            count = (
                len(tool_args["articles"])
                if isinstance(tool_args["articles"], list)
                else 1
            )
            summary_parts.append(f"文章数: {count}")

    elif tool_name in ("write_article", "boost_write_article"):
        wm = tool_args.get("writing_material") if isinstance(tool_args.get("writing_material"), dict) else {}
        if "topic" in wm:
            summary_parts.append(f"主题: {str(wm['topic'])[:30]}...")
        if "style" in wm:
            summary_parts.append(f"风格: {wm['style']}")
        if "articles" in wm:
            count = len(wm["articles"]) if isinstance(wm["articles"], list) else 1
            summary_parts.append(f"素材数: {count}")

    elif tool_name in ("review_article", "boost_review_article"):
        wm = tool_args.get("writing_material") if isinstance(tool_args.get("writing_material"), dict) else {}
        if "topic" in wm:
            summary_parts.append(f"主题: {str(wm['topic'])[:30]}...")

    if summary_parts:
        return " | ".join(summary_parts)
    return ""


def format_tool_result_summary(tool_name: str, result: Any) -> str:
    """格式化工具执行结果摘要"""
    if not result or not hasattr(result, "success"):
        return ""

    if not result.success:
        return "❌ 执行失败"

    if not hasattr(result, "data") or result.data is None:
        return "✅ 执行成功"

    data = result.data
    summary_parts = []

    # 根据工具类型提取结果摘要
    if tool_name in ("get_recent_group_update", "get_recent_feed_update"):
        if isinstance(data, tuple) and len(data) >= 2:
            groups_count = len(data[0]) if isinstance(data[0], list) else 0
            articles_count = len(data[1]) if isinstance(data[1], list) else 0
            summary_parts.append(f"分组: {groups_count}, 文章: {articles_count}")

    elif tool_name == "get_article_content":
        if isinstance(data, dict):
            summary_parts.append(f"获取 {len(data)} 篇文章")

    elif tool_name == "search_memory":
        if isinstance(data, dict):
            summary_parts.append(f"找到 {len(data)} 条记忆")

    elif tool_name in ("fetch_web_contents", "search_web"):
        if isinstance(data, list):
            summary_parts.append(f"获取 {len(data)} 条结果")
        elif isinstance(data, dict):
            summary_parts.append(f"获取 {len(data)} 条结果")

    elif tool_name == "find_keywords":
        if isinstance(data, list):
            summary_parts.append(f"提取 {len(data)} 个关键词")

    elif tool_name in ("write_article", "boost_write_article"):
        if isinstance(data, str):
            length = len(data)
            summary_parts.append(f"生成 {length} 字符")
        elif isinstance(data, dict) and "artifact_id" in data:
            summary_parts.append("生成文章")

    elif tool_name in ("review_article", "boost_review_article"):
        if isinstance(data, dict):
            if "status" in data:
                summary_parts.append(f"状态: {data['status']}")
            if "score" in data:
                summary_parts.append(f"评分: {data['score']}")

    if summary_parts:
        return "✅ " + " | ".join(summary_parts)
    return "✅ 执行成功"
