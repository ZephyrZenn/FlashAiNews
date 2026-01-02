from datetime import datetime, time
from typing import Optional, Union

from pydantic import validator

from .common import CamelModel
from core.models.config import ModelConfig


def _normalize_brief_time(value: Union[time, str]) -> time:
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    if isinstance(value, str):
        text = value.strip()
        try:
            parsed = datetime.strptime(text, "%H:%M")
        except ValueError as exc:
            raise ValueError("brief_time must be in HH:MM format") from exc
        return parsed.time()
    raise ValueError("brief_time must be a string or time value")


class ModifyGroupRequest(CamelModel):
    title: str
    desc: str
    feed_ids: list[int]


class ImportFeedsRequest(CamelModel):
    url: Optional[str] = None
    content: Optional[str] = None


class ModifyFeedRequest(CamelModel):
    title: str
    desc: str
    url: str

class ModifySettingRequest(CamelModel):
    model: Optional[ModelConfig] = None
    brief_time: Optional[time] = None

    @validator("brief_time")
    def validate_brief_time(cls, value):
        if value is None:
            return value
        return _normalize_brief_time(value)


class UpdateBriefTimeRequest(CamelModel):
    brief_time: time

    @validator("brief_time")
    def validate_brief_time(cls, value):
        return _normalize_brief_time(value)
