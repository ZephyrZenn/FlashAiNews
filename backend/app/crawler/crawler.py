import asyncio
from typing import Optional

import httpx

from app.parsers import parse_html_content


async def get_content(url: str, client: httpx.AsyncClient) -> Optional[str]:
    """
    Get the content of a URL.
    """
    try:
        resp = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if not resp.is_success:
            print("Failed to fetch URL:", url, resp.status_code)
            return None
        return parse_html_content(resp.text)
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {url}: {e}")
        return None
    except httpx.HTTPError as e:
        print(f"HTTP error occurred while requesting {url}: {e}")
        return None


async def fetch_all_contents(urls: list[str]) -> dict[str, Optional[str]]:
    """
    Fetch content from a list of URLs concurrently.
    """
    async with httpx.AsyncClient() as client:
        tasks = [get_content(url, client) for url in urls]
        result = await asyncio.gather(*tasks)
        return {url: content for url, content in zip(urls, result)}
