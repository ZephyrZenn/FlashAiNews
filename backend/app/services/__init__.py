import logging

from app.services.brief_service import generate_today_brief
from app.services.feed_service import retrieve_new_feeds
from app.state import GENERATING_FLAG

logger = logging.getLogger(__name__)


def retrieve_and_generate_brief():
    if not GENERATING_FLAG.compare_and_set(False, True):
        logger.info("Brief is being generated. Returning")
        return

    try:
        logger.info("Retrieving and generating brief")
        retrieve_new_feeds()
        generate_today_brief()
    except Exception as e:
        logger.error(f"Error retrieving and generating brief: {e}")
    finally:
        GENERATING_FLAG.set(False)
