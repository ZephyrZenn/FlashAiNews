from agent.tools.base import BaseTool, ToolSchema, ToolParameter
from agent.models import RawArticle
from core.brief_generator import AIGenerator


class KeywordExtractorTool(BaseTool[list[str]]):
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
                "返回 list[str]，包含 5-8 个提取出的核心关键词，已去重和清理。"
            ),
            parameters=[
                ToolParameter(
                    name="articles",
                    type="list[RawArticle]",
                    description=(
                        "待分析的文章id列表，系统会自动从上下文中获取完整的文章信息。"
                        "工具会将所有文章的标题和摘要合并后一起分析"
                        "示例：['abc', 'ade', 'bvv']"
                    ),
                    required=True,
                ),
            ],
        )

    async def _execute(self, articles: list[RawArticle]) -> list[str]:
        """
        从文章中提取关键词

        Args:
            articles: 文章列表

        Returns:
            关键词列表
        """
        # TODO: LLM喜欢用这个Tool提取搜索结果的关键词，需要做兼容处理
        if not articles:
            return []

        combined_text = [
            {"title": article["title"], "summary": article["summary"]}
            for article in articles
        ]
        if not combined_text:
            return []

        prompt = f"""
        请从以下资讯摘要中提取 5-8 个最核心的实体词（公司、产品、技术、人物）或关键词。
        仅输出关键词，用逗号隔开，不要有任何解释。
        内容如下：
        {combined_text}
        """

        response = await self.client.completion(prompt)

        if not response:
            return []

        keywords = [
            k.strip() for k in response.replace("，", ",").split(",") if k.strip()
        ]
        return keywords


# 保留原有函数接口以兼容现有代码
async def find_keywords_with_llm(
    client: AIGenerator, articles: list[RawArticle]
) -> list[str]:
    """使用 LLM 提取关键词（兼容函数，异步版本）

    注意：此函数为兼容接口，直接返回数据而非 ToolResult。
    新代码建议使用 KeywordExtractorTool(client).execute(articles) 获取带错误处理的结果。

    Args:
        client: AI 生成器客户端
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

    response = await client.completion(prompt)

    if not response:
        return []

    keywords = [k.strip() for k in response.replace("，", ",").split(",") if k.strip()]
    return keywords
