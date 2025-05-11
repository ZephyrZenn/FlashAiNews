from datetime import datetime
from typing import List

from app.models.common import CamelModel, CommonResult


class FeedBriefVO(CamelModel):
    id: int
    group_id: int
    title: str
    content: str
    pub_date: datetime


class FeedVO(CamelModel):
    id: int
    title: str
    url: str
    desc: str


class FeedGroupVO(CamelModel):
    id: int
    title: str
    desc: str
    feeds: List[FeedVO]


class BriefWithGroupVO(CamelModel):
    brief: FeedBriefVO
    group: FeedGroupVO


class FeedBriefResponse(CommonResult[FeedBriefVO]):
    pass


class FeedGroupListResponse(CommonResult[List[FeedGroupVO]]):
    pass


class FeedGroupDetailResponse(CommonResult[FeedGroupVO]):
    pass


class FeedListResponse(CommonResult[List[FeedVO]]):
    pass


class GroupBriefResponse(CommonResult[BriefWithGroupVO]):
    pass
