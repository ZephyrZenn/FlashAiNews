from agent.models import RawArticle
from core.brief_generator import AIGenerator


def find_keywords_with_llm(client: AIGenerator, articles: list[RawArticle]) -> list[str]:
    combined_text = "\n".join([f"{article['title']} | {article['summary']}" for article in articles])
    prompt = f"""
    请从以下资讯摘要中提取 5-8 个最核心的实体词（公司、产品、技术、人物）或关键词。
    仅输出关键词，用逗号隔开，不要有任何解释。
    内容如下：
    {combined_text}
    """
    response = client.completion(prompt)
    keywords = [k.strip() for k in response.replace("，", ",").split(",") if k.strip()]
    return keywords