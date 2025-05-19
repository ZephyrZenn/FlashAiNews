from typing import Optional

from .common import CamelModel
from .setting import ModelSetting


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
    model: Optional[ModelSetting] = None
    prompt: Optional[str] = None