from datetime import datetime

from app.models.common import CamelModel, CommonResult


class FeedBriefVO(CamelModel):
    id: int
    group_id: int
    title: str
    content: str
    pub_date: datetime

class FeedBriefResponse(CommonResult[FeedBriefVO]):
    pass