from datetime import datetime
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
    pub_date: datetime
    content: NotRequired[str]


class FocalPoint(TypedDict):
    priority: int
    topic: str
    strategy: str
    article_ids: list[str]
    reasoning: str
    search_query: str
    writing_guide: str
    history_memory_id: list[int]


class DiscardedItem(TypedDict):
    id: str
    reason: str


class AgentPlanResult(TypedDict):
    daily_overview: str
    focal_points: list[FocalPoint]
    discarded_items: list[DiscardedItem]

class SummaryMemory(TypedDict):
    id: int
    topic: str
    reasoning: str
    content: str

class WritingMaterial(TypedDict):
    topic: str
    style: Literal["DEEP", "FLASH"]
    writing_guide: str
    reasoning: str
    articles: list[RawArticle]
    ext_info: NotRequired[list[SearchResult]]
    history_memory: NotRequired[SummaryMemory]


class AgentState(TypedDict):
    focus: str
    groups: list[FeedGroup]
    raw_articles: list[RawArticle]
    plan: NotRequired[AgentPlanResult]
    writing_materials: NotRequired[list[WritingMaterial]]
    summary_results: NotRequired[list[str]]
    log_history: list[str]
    on_step: NotRequired[StepCallback]
    history_memories: dict[int, SummaryMemory]

def log_step(state: "AgentState", message: str) -> None:
    """记录执行步骤到历史，并触发回调（如果有）"""
    state["log_history"].append(message)
    if "on_step" in state and state["on_step"]:
        state["on_step"](message)
        
class AgentCriticFinding(TypedDict):
    severity: Literal["CRITICAL", "ADVISORY"]
    type: Literal["FACT_ERROR", "MISSING_INFO", "HALLUCINATION"]
    location: str
    correction_suggestion: str

class AgentCriticResult(TypedDict):
    status: Literal["APPROVED", "REJECTED"]
    score: int
    findings: list[AgentCriticFinding]
    overall_comment: str
    
