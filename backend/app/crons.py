import logging
from datetime import datetime

from app.services.feed_service import generate_today_brief, retrieve_new_feeds

logger = logging.getLogger(__name__)


def generate_daily_brief():
    """
    Generate a daily brief for all groups.
    """
    logger.info(f"Generating daily brief. Current time: {datetime.now()}")
    retrieve_new_feeds()
    logger.info(f"Retrieved new feeds. Current time: {datetime.now()}")
    generate_today_brief()
    logger.info(f"Finished generating daily brief. Current time: {datetime.now()}")
