import logging
import asyncio
import httpx
import trafilatura

logger = logging.getLogger(__name__)


async def get_content(url: str, client: httpx.AsyncClient) -> tuple[str, str | None]:
    """使用 httpx + trafilatura 实现的超轻量抓取."""
    try:
        # 1. 异步下载网页内容
        resp = await client.get(url, timeout=10.0, follow_redirects=True)
        resp.raise_for_status()

        # 2. trafilatura 提取正文并直接转为 Markdown
        # include_links=True 可以保留链接，方便 LLM 溯源
        content = trafilatura.extract(
            resp.text, include_links=True, output_format="markdown"
        )

        if content is None:
            error_msg = f"[CRAWLER] ⚠️ 内容提取失败 (trafilatura返回空): {url}"
            logger.warning(error_msg)
            print(error_msg)
            return url, None

        return url, content

    except httpx.TimeoutException:
        error_msg = f"[CRAWLER] ⏱️ 请求超时: {url}"
        logger.warning(error_msg)
        print(error_msg)
        return url, None

    except httpx.HTTPStatusError as exc:
        error_msg = f"[CRAWLER] ❌ HTTP错误 {exc.response.status_code}: {url}"
        logger.warning(error_msg)
        print(error_msg)
        return url, None

    except httpx.RequestError as exc:
        error_msg = f"[CRAWLER] 🔌 网络请求失败 ({type(exc).__name__}): {url}"
        logger.warning(error_msg)
        print(error_msg)
        return url, None

    except Exception as exc:
        error_msg = f"[CRAWLER] 💥 未知错误 ({type(exc).__name__}: {exc}): {url}"
        logger.error(error_msg)
        print(error_msg)
        return url, None

async def fetch_all_contents(urls: list[str]) -> dict[str, str]:
    """使用异步 IO 批量抓取."""
    if not urls:
        return {}

    # 使用异步 Client 共享连接池
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=20)) as client:
        tasks = [get_content(url, client) for url in urls]
        results_list = await asyncio.gather(*tasks)
        return {url: content for url, content in results_list if content}