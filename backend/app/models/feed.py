from datetime import datetime
from typing import Optional


class Feed:
    def __init__(self, id: int, title: str, url: str, last_updated: datetime,
                 desc: str = "",
                 limit: int = 10,
                 is_default: bool = False):
        self.id = id
        self.title = title
        self.url = url
        self.last_updated = last_updated
        self.desc = desc
        self.limit = limit
        self.articles = []

class FeedArticle:
    def __init__(self, id: str, title: str, url: str, content: Optional[str],
                 pub_date: datetime, summary: str, has_full_content: bool):
        self.id = id
        self.title = title
        self.url = url
        self.content = content
        self.summary = summary
        self.pub_date = pub_date
        self.has_full_content = has_full_content


class FeedGroup:
    def __init__(self, id: int, title: str, desc: str):
        self.id = id
        self.title = title
        self.desc = desc
        self.feeds = []


class FeedBrief:
    def __init__(self, id: int, group_id: int, title: str, content: str, pub_date: datetime):
        self.id = id
        self.group_id = group_id
        self.title = title
        self.content = content
        self.pub_date = pub_date
