from datetime import datetime
from typing import List, Optional

from app.models.common import CamelModel, CommonResult



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

class FeedBriefVO(CamelModel):
    id: int
    group_id: int
    content: str
    pub_date: datetime
    group: Optional[FeedGroupVO] = None


class ModelSettingVO(CamelModel):
    model: str
    provider: str
    api_key: str
    base_url: str

class SettingVO(CamelModel):
    model: ModelSettingVO
    prompt: str


class FeedBriefResponse(CommonResult[FeedBriefVO]):
    pass


class FeedBriefListResponse(CommonResult[List[FeedBriefVO]]):
    pass

class FeedGroupListResponse(CommonResult[List[FeedGroupVO]]):
    pass


class FeedGroupDetailResponse(CommonResult[FeedGroupVO]):
    pass


class FeedListResponse(CommonResult[List[FeedVO]]):
    pass

class SettingResponse(CommonResult[SettingVO]):
    pass
