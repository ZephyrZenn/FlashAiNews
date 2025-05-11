import unittest
from app.services.feed_service import generate_today_brief, import_opml_config, retrieve_new_feeds


class FeedServiceTest(unittest.TestCase):

    def test_generate_today_feed(self):
        # retrieve_new_feeds()
        generate_today_brief()

    def test_import_opml_config(self):
        import_opml_config("feed.opml")
