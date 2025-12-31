import os
import unittest

from dotenv import load_dotenv

from core.config.loader import load_config
from apps.backend.crons import generate_daily_brief
from core.pipeline.brief_generator import build_generator
from apps.backend.services import retrieve_and_generate_brief
from apps.backend.services.feed_service import import_opml_config, retrieve_new_feeds
from apps.backend.services.group_service import create_group

# Load environment variables before importing any modules that might use them
load_dotenv()

cfg = None

class FeedServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global cfg
        # Ensure environment variables are loaded
        load_dotenv()
        # Verify required environment variables
        required_vars = [
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_HOST",
            "POSTGRES_DB",
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        cfg = load_config()

    def test_generate_today_feed(self):
        # retrieve_and_generate_brief()
        # generate_today_brief()
        retrieve_new_feeds()

    def test_import_opml_config(self):
        import_opml_config("feed.opml")

    def test_create_group(self):
        create_group("Test", "Test Group", [1, 2])

    def test_llm_config(self):
        build_generator()

    def test_cron(self):
        generate_daily_brief()
        
    def test_retrieve_new_feeds(self):
        retrieve_new_feeds()