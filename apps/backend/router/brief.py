import datetime
from fastapi import APIRouter

from apps.backend.exception import BizException
from apps.backend.models.common import success_with_data, success_with_message
from apps.backend.models.view_model import FeedBriefListResponse, FeedBriefResponse
from apps.backend.services import brief_service, group_service, retrieve_and_generate_brief
from apps.backend.state import GENERATING_FLAG
from apps.backend.utils.thread_utils import submit_to_thread

router = APIRouter(prefix="/briefs")


@router.get("/default", response_model=FeedBriefListResponse)
async def get_default_group_briefs():
    """
    Get the briefs of the default group.
    """
    briefs = brief_service.get_default_group_briefs()
    if not briefs:
        return success_with_data([])
    group = group_service.get_group_detail(briefs[0].group_id)
    return success_with_data([brief.to_view_model(group) for brief in briefs])

@router.get("/{group_id}/today", response_model=FeedBriefResponse)
async def get_group_today_brief(group_id: int):
    """
    Get today brief of a feed group.
    """
    return success_with_data(
        brief_service.get_group_brief(group_id, datetime.date.today())
    )


@router.get("/{group_id}/history", response_model=FeedBriefListResponse)
async def get_history_brief(group_id: int):
    """
    Get the history brief of a feed group.
    """
    return success_with_data(brief_service.get_history_brief(group_id))


@router.post("/generate")
async def generate_today_brief():
    """
    Manually trigger today's brief generation.
    """
    if brief_service.has_today_brief():
        raise BizException("Today's brief is already available.")
    if GENERATING_FLAG.get():
        raise BizException("Brief generation is currently in progress.")
    submit_to_thread(retrieve_and_generate_brief)
    return success_with_message("Brief generation started.")
