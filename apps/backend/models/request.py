from datetime import datetime, time, date
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


class CreateScheduleRequest(CamelModel):
    time: str  # HH:MM format
    focus: str
    group_ids: list[int]

    @validator("time")
    def validate_time(cls, value):
        return _normalize_brief_time(value)


class UpdateScheduleRequest(CamelModel):
    time: Optional[str] = None  # HH:MM format
    focus: Optional[str] = None
    group_ids: Optional[list[int]] = None
    enabled: Optional[bool] = None

    @validator("time")
    def validate_time(cls, value):
        if value is None:
            return value
        return _normalize_brief_time(value)

class GetBriefsRequest(CamelModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None