from typing import Callable, Literal, TypedDict
from typing_extensions import NotRequired

from core.models.feed import FeedGroup
from core.models.search import SearchResult

# 步骤回调函数类型
StepCallback = Callable[[str], None]


class RawArticle(TypedDict):
    id: str
    title: str
    url: str
    group_title: list[str]
    summary: str
    content: NotRequired[str]


class FocalPoint(TypedDict):
    priority: int
    topic: str
    strategy: str
    article_ids: list[str]
    reasoning: str
    search_query: str
    writing_guide: str


class DiscardedItem(TypedDict):
    id: str
    reason: str


class AgentPlanResult(TypedDict):
    daily_overview: str
    focal_points: list[FocalPoint]
    discarded_items: list[DiscardedItem]


class WritingMaterial(TypedDict):
    topic: str
    style: Literal["DEEP", "FLASH"]
    writing_guide: str
    reasoning: str
    articles: list[RawArticle]
    ext_info: NotRequired[list[SearchResult]]


class AgentState(TypedDict):
    groups: list[FeedGroup]
    raw_articles: list[RawArticle]
    plan: NotRequired[AgentPlanResult]
    writing_materials: NotRequired[list[WritingMaterial]]
    history: list[str]
    on_step: NotRequired[StepCallback]


def log_step(state: "AgentState", message: str) -> None:
    """记录执行步骤到历史，并触发回调（如果有）"""
    state["history"].append(message)
    if "on_step" in state and state["on_step"]:
        state["on_step"](message)
