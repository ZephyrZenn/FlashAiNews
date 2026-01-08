from agent.tools.base import SyncTool, ToolSchema, ToolParameter
from agent.models import RawArticle
from core.brief_generator import AIGenerator


class KeywordExtractorTool(SyncTool[list[str]]):
    """使用 LLM 从文章中提取关键词的工具"""

    def __init__(self, client: AIGenerator):
        self.client = client

    @property
    def name(self) -> str:
        return "find_keywords"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "使用大语言模型（LLM）从一批文章中智能提取核心关键词。"
                "关键词类型包括：公司名称、产品名称、技术术语、人物名称等实体词。"
                "该工具通过分析文章标题和摘要，识别出最具代表性的 5-8 个关键词，"
                "可用于后续的信息检索、分类聚合或主题分析。"
            ),
            parameters=[
                ToolParameter(
                    name="articles",
                    type="list[RawArticle]",
                    description=(
                        "待分析的文章列表。每篇文章需包含 title（标题）和 summary（摘要）字段。"
                        "工具会将所有文章的标题和摘要合并后一起分析"
                    ),
                    required=True,
                ),
            ],
            returns=(
                "返回 list[str]，包含 5-8 个提取出的核心关键词。"
                "关键词已去重和清理，不包含空白字符"
            ),
            when_to_use=(
                "在以下场景使用此工具：\n"
                "1. 需要从大量文章中提取热点话题关键词\n"
                "2. 为后续的 search_memory 搜索准备关键词\n"
                "3. 对文章进行分类或聚类时需要特征词\n"
                "4. 生成摘要前分析文章的主要主题"
            ),
            usage_examples=[
                "find_keywords(articles) - 从文章列表中提取关键词",
                "keywords = find_keywords(articles); search_memory(keywords) - 提取关键词后搜索相关记忆",
            ],
            notes=[
                "此工具使用 LLM 进行分析，会产生 API 调用开销",
                "输入文章数量过多时，可能因 token 限制而截断",
                "提取结果为中文关键词，支持中英文混合内容",
                "返回的关键词数量通常为 5-8 个，取决于内容的丰富程度",
            ],
        )

    def _execute(self, articles: list[RawArticle]) -> list[str]:
        """
        从文章中提取关键词

        Args:
            articles: 文章列表

        Returns:
            关键词列表
        """
        if not articles:
            return []

        combined_text = "\n".join(
            [f"{article['title']} | {article['summary']}" for article in articles]
        )

        if not combined_text.strip():
            return []

        prompt = f"""
        请从以下资讯摘要中提取 5-8 个最核心的实体词（公司、产品、技术、人物）或关键词。
        仅输出关键词，用逗号隔开，不要有任何解释。
        内容如下：
        {combined_text}
        """

        response = self.client.completion(prompt)

        if not response:
            return []

        keywords = [
            k.strip() for k in response.replace("，", ",").split(",") if k.strip()
        ]
        return keywords


# 保留原有函数接口以兼容现有代码
def find_keywords_with_llm(
    client: AIGenerator, articles: list[RawArticle]
) -> list[str]:
    """使用 LLM 提取关键词（兼容函数）

    注意：此函数为兼容接口，直接返回数据而非 ToolResult。
    新代码建议使用 KeywordExtractorTool(client).execute(articles) 获取带错误处理的结果。

    Args:
        client: AI 生成器客户端
        articles: 文章列表

    Returns:
        关键词列表
    """
    tool = KeywordExtractorTool(client)
    result = tool.execute(articles)
    if result.success:
        return result.data
    raise RuntimeError(result.error)
