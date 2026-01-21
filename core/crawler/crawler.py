import logging
import os
import asyncio
import httpx
import trafilatura

logger = logging.getLogger(__name__)


def _is_jina_configured() -> bool:
    """检查是否配置了 Jina API Key."""
    api_key = os.getenv("JINA_API_KEY")
    return bool(api_key and api_key.strip())


async def _get_content_with_jina(
    url: str, client: httpx.AsyncClient
) -> tuple[str, str | None]:
    """使用 Jina Reader API 获取内容."""
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        return url, None

    try:
        # Jina Reader API: https://r.jina.ai/{url}
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "text/markdown",
        }

        resp = await client.get(
            jina_url, headers=headers, timeout=30.0, follow_redirects=True
        )
        resp.raise_for_status()

        content = resp.text.strip()
        if not content:
            logger.warning("[CRAWLER] ⚠️ Jina 返回空内容: %s", url)
            return url, None

        logger.info("[CRAWLER] ✅ 使用 Jina 成功获取内容: %s", url)
        return url, content

    except httpx.TimeoutException:
        logger.warning("[CRAWLER] ⏱️ Jina 请求超时: %s", url)
        return url, None

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "[CRAWLER] ❌ Jina HTTP错误 %d: %s", exc.response.status_code, url
        )
        return url, None

    except httpx.RequestError as exc:
        logger.warning(
            "[CRAWLER] 🔌 Jina 网络请求失败 (%s): %s", type(exc).__name__, url
        )
        return url, None

    except Exception as exc:
        logger.error(
            "[CRAWLER] 💥 Jina 未知错误 (%s: %s): %s", type(exc).__name__, exc, url
        )
        return url, None


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
            logger.warning("[CRAWLER] ⚠️ 内容提取失败 (trafilatura返回空): %s", url)

            # Fallback to Jina if configured
            if _is_jina_configured():
                logger.info("[CRAWLER] 🔄 尝试使用 Jina 作为 fallback: %s", url)
                return await _get_content_with_jina(url, client)

            return url, None

        return url, content

    except httpx.TimeoutException:
        error_msg = f"[CRAWLER] ⏱️ 请求超时: {url}"
        logger.warning("[CRAWLER] ⏱️ 请求超时: %s", url)
        print(error_msg)

        # Fallback to Jina if configured
        if _is_jina_configured():
            logger.info("[CRAWLER] 🔄 尝试使用 Jina 作为 fallback: %s", url)
            return await _get_content_with_jina(url, client)

        return url, None

    except httpx.HTTPStatusError as exc:
        error_msg = f"[CRAWLER] ❌ HTTP错误 {exc.response.status_code}: {url}"
        logger.warning("[CRAWLER] ❌ HTTP错误 %d: %s", exc.response.status_code, url)
        print(error_msg)

        # Fallback to Jina if configured (only for client errors, not server errors)
        if exc.response.status_code < 500 and _is_jina_configured():
            logger.info("[CRAWLER] 🔄 尝试使用 Jina 作为 fallback: %s", url)
            return await _get_content_with_jina(url, client)

        return url, None

    except httpx.RequestError as exc:
        error_msg = f"[CRAWLER] 🔌 网络请求失败 ({type(exc).__name__}): {url}"
        logger.warning(
            "[CRAWLER] 🔌 网络请求失败 (%s): %s", type(exc).__name__, url
        )
        print(error_msg)

        # Fallback to Jina if configured
        if _is_jina_configured():
            logger.info("[CRAWLER] 🔄 尝试使用 Jina 作为 fallback: %s", url)
            return await _get_content_with_jina(url, client)

        return url, None

    except Exception as exc:
        error_msg = f"[CRAWLER] 💥 未知错误 ({type(exc).__name__}: {exc}): {url}"
        logger.error(
            "[CRAWLER] 💥 未知错误 (%s: %s): %s", type(exc).__name__, exc, url
        )
        print(error_msg)

        # Fallback to Jina if configured
        if _is_jina_configured():
            logger.info("[CRAWLER] 🔄 尝试使用 Jina 作为 fallback: %s", url)
            return await _get_content_with_jina(url, client)

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
