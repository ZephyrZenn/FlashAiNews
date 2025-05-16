from fastapi import APIRouter

from app.models.common import success_with_data
from app.models.request import ImportFeedsRequest, ModifyFeedRequest
from app.models.view_model import FeedListResponse
from app.services import feed_service

router = APIRouter(prefix="/feeds")

@router.get("/", response_model=FeedListResponse)
async def get_all_feeds():
    """
    Get all feeds.
    """
    return success_with_data(feed_service.get_all_feeds())

@router.post("/import")
async def import_feeds(request: ImportFeedsRequest):
    """
    Import feeds from an OPML file URL.
    """
    feed_service.import_opml_config(request.url, request.content)
    return success_with_data()


@router.post("/")
async def add_feed(request: ModifyFeedRequest):
    """
    Add a feed.
    """
    feed_service.add_feed(
        title=request.title, description=request.desc, url=request.url
    )
    return success_with_data()


@router.put("/{feed_id}")
async def update_feed(feed_id: int, request: ModifyFeedRequest):
    """
    Update a feed.
    """
    feed_service.update_feed(
        id=feed_id, title=request.title, description=request.desc, url=request.url
    )
    return success_with_data()


@router.delete("/{feed_id}")
async def delete_feed(feed_id: int):
    """
    Delete a feed.
    """
    feed_service.delete_feed(feed_id)
    return success_with_data()
