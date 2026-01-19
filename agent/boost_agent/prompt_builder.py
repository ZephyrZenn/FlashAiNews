"""Prompt 构建工具

负责构建规划阶段和执行阶段的 prompt。
"""

import json
import logging
from datetime import datetime

from agent.context import ContentOptimizer
from agent.models import AgentState, FocalPoint

logger = logging.getLogger(__name__)


class PromptBuilder:
    """构建各种 prompt"""

    def __init__(self, content_optimizer: ContentOptimizer):
        """初始化 prompt 构建器
        
        Args:
            content_optimizer: ContentOptimizer 实例
        """
        self.content_optimizer = content_optimizer

    def build_planning_prompt(self, focus: str, hour_gap: int) -> str:
        """构建规划阶段的用户提示
        
        Args:
            focus: 用户关注点
            hour_gap: 时间范围（小时）
            
        Returns:
            规划阶段的 prompt
        """
        prompt = f"""当前日期: {datetime.now().strftime("%Y-%m-%d")}
用户关注点: {focus if focus else "无特定关注点"}
时间范围: 过去 {hour_gap} 小时

请根据用户关注点，自主选择相关的订阅源，获取文章更新，并搜索网络补充信息，然后制定完整的执行计划。

你可以：
1. 使用 get_all_feeds 查看所有可用的订阅源
2. 根据关注点选择相关订阅源，使用 get_recent_feed_update 获取文章摘要
3. 如果需要详细内容，使用 get_article_content 获取指定文章的完整内容
4. 使用 find_keywords 提取关键词
5. 使用 search_memory 搜索历史记忆
6. 使用 search_web 搜索网络获取补充信息
7. 制定完整的执行计划
"""
        return prompt

    async def build_execution_prompt(
        self, focal_point: FocalPoint, state: AgentState
    ) -> str:
        """构建执行阶段的用户提示
        
        Args:
            focal_point: 焦点话题
            state: AgentState
            
        Returns:
            执行阶段的 prompt
        """
        # 获取相关文章
        article_ids = [str(aid) for aid in focal_point.get("article_ids", [])]
        articles = [
            article
            for article in state["raw_articles"]
            if str(article["id"]) in article_ids
        ]

        # 使用内容优化器优化文章（现在是异步，自动检测是否有内容）
        articles = await self.content_optimizer.optimize_articles_for_prompt(
            articles,
            focus=state.get("focus", ""),
            # 函数会自动检测文章是否有完整内容，无需手动指定
        )

        # 获取历史记忆
        history_memory_ids = focal_point.get("history_memory_id", [])
        history_memories = [
            state["history_memories"][hid]
            for hid in history_memory_ids
            if hid in state["history_memories"]
        ]

        # 使用内容优化器优化历史记忆
        history_memories = self.content_optimizer.truncate_memories(history_memories)

        # 构建优化的文章摘要（只包含关键信息）
        article_summaries = [
            {
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "summary": self.content_optimizer.truncate_text(
                    a.get("summary", ""), self.content_optimizer.summary_max_length
                ),
            }
            for a in articles
        ]

        # 构建优化的历史记忆摘要
        memory_summaries = [
            {
                "topic": m.get("topic", ""),
                "reasoning": m.get("reasoning", ""),
                "content": self.content_optimizer.truncate_text(
                    m.get("content", ""), self.content_optimizer.memory_max_length
                ),
            }
            for m in history_memories
        ]

        prompt = f"""任务信息：
- 话题: {focal_point['topic']}
- 策略: {focal_point['strategy']}
- 推理: {focal_point['reasoning']}
- 写作指南: {focal_point.get('writing_guide', '')}
- 搜索查询: {focal_point.get('search_query', '')}

相关文章（{len(article_summaries)} 篇）:
{json.dumps(article_summaries, ensure_ascii=False, indent=2)}

历史记忆:
{json.dumps(memory_summaries, ensure_ascii=False, indent=2) if memory_summaries else "无"}

请根据任务信息，使用工具获取必要的补充信息，然后生成高质量的摘要内容。
"""
        return prompt
