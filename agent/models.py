from typing import TypedDict
from typing_extensions import NotRequired

from core.models.feed import FeedGroup


class RawArticle(TypedDict):
    id: str
    title: str
    url: str
    group_title: list[str]
    summary: str


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


class AgentState(TypedDict):
    groups: list[FeedGroup]
    raw_articles: list[RawArticle]
    plan: NotRequired[AgentPlanResult]
