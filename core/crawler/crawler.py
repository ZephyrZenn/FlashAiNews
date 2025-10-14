import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from newspaper import Article
import html2text
from readability import Document

logger = logging.getLogger(__name__)


def get_content(url: str) -> tuple[str, Optional[str]]:
    """Fetch article HTML content for a single URL."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        doc = Document(article.html)
        return url, doc.summary()
    except Exception as exc:
        logger.error("Failed to download %s: %s", url, exc)
        return url, None


def fetch_all_contents(urls: list[str]) -> dict[str, Optional[str]]:
    """Fetch content from a list of URLs concurrently using worker threads."""
    if not urls:
        return {}

    logger.info("Fetching %d URLs concurrently", len(urls))
    results: dict[str, Optional[str]] = {}
    max_workers = min(10, len(urls))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for fetched_url, html in executor.map(get_content, urls):
            if html:
                results[fetched_url] = html2text.html2text(html)

    return results
