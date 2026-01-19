"""状态更新工具

处理工具调用结果对 AgentState 的更新。
"""

import logging

logger = logging.getLogger(__name__)


class StateUpdater:
    """处理工具结果对 state 的更新"""

    def __init__(self, state: dict):
        """初始化状态更新器
        
        Args:
            state: AgentState 字典
        """
        self.state = state

    def update_from_tool_result(self, tool_name: str, result) -> None:
        """根据工具结果更新 state
        
        Args:
            tool_name: 工具名称
            result: 工具执行结果
        """
        if not self.state or not result.success:
            return

        # 使用策略模式处理不同类型的工具结果
        state_updaters = {
            "get_recent_feed_update": self._update_from_feed_update,
            "get_article_content": self._update_from_article_content,
        }

        updater = state_updaters.get(tool_name)
        if updater:
            updater(result)

    def _update_from_feed_update(self, result) -> None:
        """更新 state 中的 articles（新Agent不使用Group）"""
        _, articles = result.data

        # 合并文章（去重）
        existing_article_ids = {str(a["id"]) for a in self.state["raw_articles"]}
        new_articles = [
            article
            for article in articles
            if str(article["id"]) not in existing_article_ids
        ]
        self.state["raw_articles"].extend(new_articles)

    def _update_from_article_content(self, result) -> None:
        """更新 state 中文章的完整内容"""
        # result.data 是一个字典，key 是文章ID（字符串），value 是内容（字符串）
        content_dict = result.data

        # 创建文章ID到索引的映射，方便快速查找
        article_id_to_index = {
            str(article["id"]): idx
            for idx, article in enumerate(self.state["raw_articles"])
        }

        # 更新对应文章的内容
        for article_id, content in content_dict.items():
            if article_id in article_id_to_index:
                idx = article_id_to_index[article_id]
                self.state["raw_articles"][idx]["content"] = content
