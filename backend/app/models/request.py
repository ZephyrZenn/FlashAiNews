from app.models.common import CamelModel

class ModifyGroupRequest(CamelModel):
    title: str
    desc: str
    feed_ids: list[int]
