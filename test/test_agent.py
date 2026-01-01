

from collections import defaultdict
import os
import unittest
from dotenv import load_dotenv

from agent.models import AgentState, RawArticle
from agent.planner import AgentPlanner
from core.config.loader import load_config
from core.pipeline.brief_generator import build_generator
from apps.backend.services.group_service import get_all_groups_with_feeds
from apps.backend.services.feed_service import get_feed_items


class AgentTest(unittest.TestCase):
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

    def test_agent_planner(self):
        print(cfg)
        agent_planner = AgentPlanner(build_generator())
        groups = get_all_groups_with_feeds()
        feed_group_map: dict[int, list] = defaultdict(list)
        for group in groups:
            for feed in group.feeds:
                feed_group_map[feed.id].append(group.title)
        articles = get_feed_items(48, group_ids=[groups[0].id])
        # conver articles to list[RawArticle]
        raw_articles = [RawArticle(id=article["id"], title=article["title"], url=article["link"], group_title=feed_group_map.get(
            article['feed_id']), summary=article["summary"]) for article in articles]
        plan_result = agent_planner.plan(AgentState(groups=[groups[0]], raw_articles=raw_articles))
        print(plan_result)