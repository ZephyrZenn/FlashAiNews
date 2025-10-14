import logging
from datetime import datetime


from apps.backend.services import retrieve_and_generate_brief

logger = logging.getLogger(__name__)

def generate_daily_brief():
    """
    Generate a daily brief for all groups.
    """
    # config = get_config()
    logger.info(f"Generating daily brief. Current time: {datetime.now()}")
    retrieve_and_generate_brief()
    logger.info(f"Finished generating daily brief. Current time: {datetime.now()}")
    
    # briefs = get_today_all_briefs()
