from datetime import datetime
from typing import Optional

from core.constants import DEFAULT_FEED_LAST_USED_DATE


class Feed:
    def __init__(
        self,
        id: int,
        title: str,
        url: str,
        last_updated: datetime = DEFAULT_FEED_LAST_USED_DATE,
        desc: str = "",
        limit: int = 10,
    ):
        self.id = id
        self.title = title
        self.url = url
        self.last_updated = last_updated
        self.desc = desc
        self.limit = limit
        self.articles = []


class FeedArticle:
    def __init__(
        self,
        id: str,
        title: str,
        url: str,
        content: Optional[str],
        pub_date: datetime,
        summary: str,
        has_full_content: bool,
    ):
        self.id = id
        self.title = title
        self.url = url
        self.content = content
        self.summary = summary
        self.pub_date = pub_date
        self.has_full_content = has_full_content


class FeedGroup:
    def __init__(self, id: int, title: str, desc: str, feeds: list[Feed] | None = None):
        self.id = id
        self.title = title
        self.desc = desc
        self.feeds = feeds if feeds is not None else []


class FeedBrief:
    def __init__(
        self, id: int, group_id: int, content: str, pub_date: datetime
    ):
        self.id = id
        self.group_id = group_id
        self.content = content
        self.pub_date = pub_date

    def to_view_model(self, group: FeedGroup) -> dict:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "content": self.content,
            "pub_date": self.pub_date,
            "group": group,
        }
