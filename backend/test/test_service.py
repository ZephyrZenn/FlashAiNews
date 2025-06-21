import os
import unittest

from dotenv import load_dotenv

from app.config.loader import load_config
from app.crons import generate_daily_brief
from app.services import generate_today_brief
from app.services.brief_generator import build_generator
from app.services.feed_service import import_opml_config, retrieve_new_feeds
from app.services.group_service import create_group
from backend.app.config.email import init_email

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
        init_email(cfg.email)

    def test_generate_today_feed(self):
        # retrieve_new_feeds()
        generate_today_brief()

    def test_import_opml_config(self):
        import_opml_config("feed.opml")

    def test_create_group(self):
        create_group("Test", "Test Group", [1, 2])

    def test_llm_config(self):
        build_generator()

    def test_cron(self):
        generate_daily_brief()