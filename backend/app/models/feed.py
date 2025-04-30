from datetime import datetime


class RSSFeed:
  def __init__(self, id: int, title: str, url: str, last_updated: datetime,
      desc: str = "",
      limit: int = 10):
    self.id = id
    self.title = title
    self.url = url
    self.last_updated = last_updated
    self.desc = desc
    self.limit = limit
    self.articles = []

class FeedArticle:
  def __init__(self, id: str, title: str, url: str, content: str,
      pub_date: datetime):
    self.id = id
    self.title = title
    self.url = url
    self.content = content
    self.pub_date = pub_date