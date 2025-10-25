import datetime
from pathlib import Path
import typer
import html2text

from core.config.loader import load_config
from core.constants import SUMMARY_LENGTH
from core.crawler.crawler import fetch_all_contents
from core.parsers import parse_feed, parse_opml
from core.pipeline import pipeline

cmd_tool = typer.Typer()


@cmd_tool.command()
def sumup(
    feed_path: str = typer.Argument(
        ..., exists=True, readable=True, help="Feeds opml path"
    ),
    out: Path = typer.Option("summary.md", "--out", "-o", help="Output path"),
    cfg: str = typer.Argument("config.toml"),
):
    load_config(path=cfg)
    print(feed_path)
    with open(feed_path, encoding="utf-8") as f:
        file_text = f.read()
        feeds = parse_opml(file_text)

    articles = parse_feed(feeds)
    for feed in articles.keys():
        recent_24h_articles = [
            a
            for a in articles[feed]
            if (
                a.pub_date - datetime.datetime.now()
            ).total_seconds()
            >= -24 * 3600
        ]
        articles[feed] = recent_24h_articles
    print(f"Get {len(articles)} articles")
    urls = {
        a.url: a for arts in articles.values() for a in arts if not a.has_full_content
    }
    contents = fetch_all_contents(list(urls.keys()))
    for url, content in contents.items():
        if not content:
            continue
        article = urls[url]
        article.content = content
        if not article.summary:
            article.summary = content[:SUMMARY_LENGTH]

    for _, al in articles.items():
        for article in al:
            article.summary = html2text.html2text(article.summary)
            if article.content:
                article.content = html2text.html2text(article.content)
    arts = []
    for a in articles.values():
        arts.extend(a)
    print("Prepare to generate summary")
    brief = pipeline.sum_pipeline(arts)
    with open(out, "w") as f:
        f.write(brief)


if __name__ == "__main__":
    cmd_tool()
