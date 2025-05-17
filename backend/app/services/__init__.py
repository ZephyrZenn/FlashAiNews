import logging

from app.services.brief_service import generate_today_brief
from app.services.feed_service import retrieve_new_feeds
from app.utils.atomic import AtomicValue

logger = logging.getLogger(__name__)

# TODO: This is a global variable to avoid multiple threads generating brief at the same time.
is_generating_brief = AtomicValue(False)

def retrieve_and_generate_brief():
    global is_generating_brief
    if not is_generating_brief.compare_and_set(False, True):
        logger.info("Brief is being generated. Returning")
        return

    try:
        logger.info("Retrieving and generating brief")
        retrieve_new_feeds()
        generate_today_brief()
    except Exception as e:
        logger.error(f"Error retrieving and generating brief: {e}")
    finally:
        is_generating_brief.set(False)

