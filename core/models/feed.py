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
        self, id: int, content: str, pub_date: datetime, group_ids: list[int] = None
    ):
        self.id = id
        self.content = content
        self.pub_date = pub_date
        self.group_ids = group_ids if group_ids is not None else []

    def to_view_model(self, groups_dict: dict[int, FeedGroup]) -> dict:
        groups = [groups_dict[gid] for gid in self.group_ids if gid in groups_dict]
        return {
            "id": self.id,
            "content": self.content,
            "pub_date": self.pub_date,
            "groups": groups,
        }
