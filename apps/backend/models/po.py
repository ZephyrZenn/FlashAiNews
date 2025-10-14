from datetime import datetime

class FeedPO:
  def __init__(self, id: int, title: str, url: str, desc: str,
      last_used: datetime, limit: int = 10):
    self.id = id
    self.title = title
    self.url = url
    self.desc = desc
    self.last_used = last_used
    self.limit = limit

class FeedItemPO:
  def __init__(self, id: str, title: str, url: str, content: str,
      pub_date: datetime, feed_id: int):
    self.id = id
    self.title = title
    self.url = url
    self.content = content
    self.pub_date = pub_date
    self.feed_id = feed_id

class FeedGroupPO:
  def __init__(self, id: int, title: str, desc: str):
    self.id = id
    self.title = title
    self.desc = desc

class FeedGroupItemPO:
  def __init__(self, id: int, feed_id: int, group_id: int):
    self.id = id
    self.feed_id = feed_id
    self.group_id = group_id