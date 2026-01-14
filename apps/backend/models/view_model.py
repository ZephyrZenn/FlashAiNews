from datetime import datetime
from typing import List, Optional

from .common import CamelModel, CommonResult



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
    groups: List[FeedGroupVO]
    content: str
    pub_date: datetime


class ModelSettingVO(CamelModel):
    """Model setting view object.
    
    Note: API keys are managed via environment variables, not exposed in API.
    Base URL is only present for 'other' provider.
    """
    model: str
    provider: str
    base_url: Optional[str] = None  # Only present for 'other' provider
    api_key_configured: bool = False  # Whether the API key is configured
    api_key_env_var: str = ""  # Environment variable name for the API key


class SettingVO(CamelModel):
    model: ModelSettingVO


class ScheduleVO(CamelModel):
    id: str
    time: str  # HH:MM format
    focus: str
    group_ids: List[int]
    enabled: bool


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


class ScheduleListResponse(CommonResult[List[ScheduleVO]]):
    pass


class ScheduleResponse(CommonResult[ScheduleVO]):
    pass


class GenerateBriefResponse(CommonResult[dict]):
    """生成任务创建响应"""
    pass


class BriefGenerationStatusResponse(CommonResult[dict]):
    """生成任务状态响应"""
    pass
