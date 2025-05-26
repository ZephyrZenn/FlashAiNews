import logging
from datetime import datetime


from app.config.loader import get_config
from app.services.brief_service import generate_today_brief, get_today_all_briefs
from app.services.email_service import send_brief_email
from app.services.feed_service import retrieve_new_feeds

logger = logging.getLogger(__name__)

def generate_daily_brief():
    """
    Generate a daily brief for all groups.
    """
    config = get_config()
    logger.info(f"Generating daily brief. Current time: {datetime.now()}")
    retrieve_new_feeds()
    logger.info(f"Retrieved new feeds. Current time: {datetime.now()}")
    generate_today_brief()
    logger.info(f"Finished generating daily brief. Current time: {datetime.now()}")
    
    briefs = get_today_all_briefs()
    if config.global_.email_enabled:
        for brief, group_name in briefs:
            logger.info(f"Sending brief for group {group_name}")
            send_brief_email(brief, group_name, config.email)