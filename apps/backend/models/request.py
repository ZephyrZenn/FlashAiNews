from datetime import datetime, time, date
from typing import Optional, Union

from pydantic import validator, Field

from .common import CamelModel
from core.models.generator import ModelProvider


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


class ModelConfigRequest(CamelModel):
    """Pydantic model for model configuration in requests"""
    model: str = Field(..., description="Model name")
    provider: str = Field(..., description="Model provider (openai, deepseek, gemini)")
    api_key: str = Field(..., description="API key for the model provider")
    base_url: Optional[str] = Field(None, description="Base URL for the model provider")

    @validator("model", "provider", "api_key")
    def validate_required_fields(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError("Field cannot be empty")
        return v.strip() if isinstance(v, str) else v

    @validator("provider")
    def validate_provider(cls, v):
        try:
            ModelProvider(v)
        except ValueError as e:
            raise ValueError(f"Invalid provider: {e}")
        return v


class ModifySettingRequest(CamelModel):
    model: Optional[ModelConfigRequest] = None


class CreateScheduleRequest(CamelModel):
    time: str  # HH:MM format
    focus: str
    group_ids: list[int]

    @validator("time")
    def validate_time(cls, value):
        return _normalize_brief_time(value)

    @validator("group_ids")
    def validate_group_ids(cls, value):
        if not value:
            raise ValueError("group_ids cannot be empty")
        return value


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

    @validator("group_ids")
    def validate_group_ids(cls, value):
        if value is not None and len(value) == 0:
            raise ValueError("group_ids cannot be empty")
        return value

class GetBriefsRequest(CamelModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None