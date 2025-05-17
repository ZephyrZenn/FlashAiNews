from fastapi import APIRouter

from app.models.common import success_with_data
from app.models.request import ModifyGroupRequest
from app.models.view_model import FeedGroupDetailResponse, FeedGroupListResponse
from app.services import group_service

router = APIRouter(prefix="/groups")


@router.get("/", response_model=FeedGroupListResponse)
async def get_all_feed_groups():
    """
    Get all feed groups.
    """
    return success_with_data(group_service.get_feed_groups())


@router.get("/{group_id}", response_model=FeedGroupDetailResponse)
async def get_feed_group_detail(group_id: int):
    """
    Get the detail of a feed group.
    """
    group = group_service.get_group_detail(group_id)
    return success_with_data(group)


@router.post("/")
async def add_group(request: ModifyGroupRequest):
    """
    Add a feed group.
    """
    gid = group_service.create_group(request.title, request.desc, request.feed_ids)
    return success_with_data(gid)


@router.put("/{group_id}")
async def update_group(group_id: int, request: ModifyGroupRequest):
    """
    Update a feed group.
    """
    group_service.update_group(group_id, request.title, request.desc, request.feed_ids)
    return success_with_data()
