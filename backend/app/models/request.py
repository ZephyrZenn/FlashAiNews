from typing import Optional
from app.models.common import CamelModel

class ModifyGroupRequest(CamelModel):
    title: str
    desc: str
    feed_ids: list[int]

class ImportFeedsRequest(CamelModel):
    url: Optional[str] = None
    content: Optional[str] = None

