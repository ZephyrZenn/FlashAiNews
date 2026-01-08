import logging

logger = logging.getLogger(__name__)


def generate_scheduled_brief(schedule_id: str, group_ids: list[int], focus: str):
    """
    Generate a brief for specific groups with custom focus.
    """
    from apps.backend.services.brief_service import generate_brief_for_groups
    from apps.backend.services.feed_service import retrieve_new_feeds
    
    logger.info(f"Generating scheduled brief {schedule_id} for groups {group_ids} with focus: {focus}")
    try:
        retrieve_new_feeds(group_ids=group_ids)
        generate_brief_for_groups(group_ids=group_ids, focus=focus)
        logger.info(f"Finished generating scheduled brief {schedule_id}")
    except Exception as e:
        logger.exception(f"Error generating scheduled brief {schedule_id}: {e}")
