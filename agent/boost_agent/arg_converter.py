"""参数转换工具

处理工具调用时的参数转换，将简化的参数（如ID列表）转换为完整的对象。
"""

import logging
from typing import Any

from agent.artifact_store import ArtifactStore
from agent.models import RawArticle, SummaryMemory

logger = logging.getLogger(__name__)


class ArgumentConverter:
    """处理工具参数转换"""

    def __init__(self, state: dict, artifact_store: ArtifactStore | None = None):
        """初始化参数转换器

        Args:
            state: AgentState 字典，用于查找文章和记忆
        """
        self.state = state
        self.artifact_store = artifact_store

    def convert_articles_arg(self, articles_arg: Any) -> list[RawArticle]:
        """转换 articles 参数

        支持多种输入格式：
        1. 完整的文章对象列表（dict with title, summary, etc.）
        2. 文章 ID 列表（数字或字符串）
        3. 文章标题列表（字符串）- 通过标题匹配查找文章

        Args:
            articles_arg: 文章参数（可能是ID列表、标题列表或文章对象列表）

        Returns:
            文章对象列表
        """
        if not articles_arg or not isinstance(articles_arg, list):
            return []

        # 如果已经是完整的文章对象，直接返回
        if (
            articles_arg
            and isinstance(articles_arg[0], dict)
            and "title" in articles_arg[0]
        ):
            return articles_arg
        raw_articles = self.state.get("raw_articles", [])
        # 如果第一个元素是字符串，可能是标题或 ID
        if isinstance(articles_arg[0], str):
            keys = {k.strip() for k in articles_arg if str(k).strip()}

            # 先按 id 匹配
            by_ids = [a for a in raw_articles if str(a.get("id", "")).strip() in keys]
            if by_ids:
                return by_ids

            # 再按 title 匹配
            by_titles = [a for a in raw_articles if str(a.get("title", "")).strip() in keys]
            if by_titles:
                return by_titles

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

    def convert_history_memory_list_arg(
        self, memory_arg: Any
    ) -> list[SummaryMemory] | None:
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

    def _convert_single_memory_arg(self, memory_arg: Any) -> SummaryMemory | None:
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

    def _extract_memory_id(self, memory_arg: Any) -> int | None:
        """从 memory 参数中提取 ID"""
        if isinstance(memory_arg, (int, str)):
            return int(memory_arg)
        if isinstance(memory_arg, dict) and "id" in memory_arg:
            return memory_arg["id"]
        return None

    def convert_writing_tool_args(self, tool_name: str, tool_args: dict) -> dict:
        """转换写作工具的参数，将简化的参数转换为完整的对象

        Args:
            tool_name: 工具名称
            tool_args: 原始参数（可能包含 ID 或简化数据）

        Returns:
            转换后的参数（包含完整的对象）
        """
        converted_args = tool_args.copy()
        converted_args["articles"] = self.convert_articles_arg(
            tool_args.get("articles")
        )
        converted_args["history_memory"] = self.convert_history_memory_list_arg(
            tool_args.get("history_memory")
        )

        # Boost 路径：如果 draft_content/review 传的是 artifact_id，则自动解引用
        if self.artifact_store:
            if tool_name in ("boost_review_article", "review_article"):
                draft_content = converted_args.get("draft_content")
                resolved = self._resolve_artifact_content(draft_content)
                if resolved is not None:
                    converted_args["draft_content"] = resolved

            if tool_name in ("boost_write_article", "write_article"):
                review_obj = converted_args.get("review")
                resolved_review = self._resolve_artifact_content(review_obj)
                if resolved_review is not None:
                    converted_args["review"] = resolved_review

        return converted_args

    def _resolve_artifact_content(self, value: Any) -> Any | None:
        """如果传入 artifact_id 或包含 artifact_id 的对象，则返回存储的完整内容。"""
        artifact_id = None
        if isinstance(value, str):
            artifact_id = value
        elif isinstance(value, dict) and "artifact_id" in value:
            artifact_id = value.get("artifact_id")

        if not artifact_id:
            return None

        if not self.artifact_store:
            return None

        entry = self.artifact_store.get(str(artifact_id))
        if not entry:
            logger.warning("Artifact %s not found when resolving content", artifact_id)
            return None

        return entry.get("content")
