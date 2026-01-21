import datetime
import unittest
from core.crawler import fetch_all_contents
from core.models.feed import Feed
from core.parsers import parse_feed


class CrawlerServiceTest(unittest.TestCase):

    def test_download_content(self):
        t = fetch_all_contents(
            urls=["https://www.stcn.com/article/detail/3362713.html"]
        )
        print(t)

    def test_parse_feeds(self):
        feeds = parse_feed(
            [Feed(0, "ING", "https://think.ing.com/rss/", datetime.datetime.now(), "", "active")]
        )
