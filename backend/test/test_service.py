import unittest

from app.config.llm import llm_config, get_model, init_llm_config
from app.services import generate_today_brief
from app.services.brief_generator import build_generator
from app.services.feed_service import import_opml_config, retrieve_new_feeds
from app.services.group_service import create_group



class FeedServiceTest(unittest.TestCase):

    def test_generate_today_feed(self):
        init_llm_config()
        retrieve_new_feeds()
        generate_today_brief()

    def test_import_opml_config(self):
        import_opml_config("feed.opml")

    def test_create_group(self):
        create_group("Test", "Test Group", [1, 2])

    def test_llm_config(self):
        init_llm_config()
        build_generator()
