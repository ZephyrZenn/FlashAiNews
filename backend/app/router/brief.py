import datetime
from fastapi import APIRouter

from app.models.common import success_with_data
from app.models.view_model import FeedBriefListResponse, FeedBriefResponse
from app.services import feed_service

router = APIRouter(prefix="/briefs")


@router.get("/default", response_model=FeedBriefListResponse)
async def get_default_group_briefs():
    """
    Get the briefs of the default group.
    """
    briefs, group = feed_service.get_default_group_briefs()
    for brief in briefs:
        brief.group = group
    return success_with_data(briefs)

@router.get("/{group_id}/today", response_model=FeedBriefResponse)
async def get_group_today_brief(group_id: int):
    """
    Get the today brief of a feed group.
    """
    return success_with_data(
        feed_service.get_group_brief(group_id, datetime.date.today())
    )


@router.get("/{group_id}/history", response_model=FeedBriefListResponse)
async def get_history_brief(group_id: int):
    """
    Get the history brief of a feed group.
    """
    return success_with_data(feed_service.get_history_brief(group_id))