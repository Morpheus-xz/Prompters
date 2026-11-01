"""Explicit public contracts, excluding ownership secrets."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.config import (
    IDEA_DESCRIPTION_MAX,
    IDEA_TITLE_MAX,
    PRO_TIP_MAX,
    PROMPT_IDEAS_MAX,
    PROMPT_IDEAS_MIN,
)
from app.models.domain import Expense, Task, Vendor
from app.models.enums import BudgetState, CostLevel, EventType, IdeaFocus


class BudgetLine(BaseModel):
    """One category's computed balance."""

    category: str
    label: str
    allocated: float
    spent: float
    remaining: float
    percent_used: float
    state: BudgetState


class BudgetStatus(BaseModel):
    """Complete computed spending status."""

    lines: list[BudgetLine]
    total_allocated: float
    total_spent: float
    total_remaining: float
    percent_used: float
    state: BudgetState


class Progress(BaseModel):
    """Deterministic readiness and deadline metrics."""

    tasks_total: int
    tasks_done: int
    overdue_count: int
    essential_vendors_total: int
    essential_vendors_booked: int
    readiness_score: int
    days_until_event: int


class PlanSummary(BaseModel):
    """A sidebar entry."""

    id: str
    title: str
    event_type: EventType
    event_date: date


class PlanDetail(PlanSummary):
    """Full public event state, never containing owner_id."""

    guest_count: int
    total_budget: float
    currency: str
    city: str | None
    preferences: str | None
    created_at: datetime
    timeline_compressed: bool
    allocations: dict[str, float]
    tasks: list[Task]
    vendors: list[Vendor]
    expenses: list[Expense]
    per_guest_budget: float
    budget: BudgetStatus
    progress: Progress


class IdeaItem(BaseModel):
    """A validated qualitative suggestion."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=IDEA_TITLE_MAX)
    description: str = Field(min_length=1, max_length=IDEA_DESCRIPTION_MAX)
    budget_category: str = Field(min_length=1, max_length=IDEA_TITLE_MAX)
    cost_level: CostLevel


class IdeasDraft(BaseModel):
    """Strict model output before category filtering."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    ideas: list[IdeaItem] = Field(
        min_length=PROMPT_IDEAS_MIN, max_length=PROMPT_IDEAS_MAX
    )
    pro_tip: str = Field(min_length=1, max_length=PRO_TIP_MAX)


class IdeasResponse(BaseModel):
    """Filtered suggestions with explicit cache provenance."""

    ideas: list[IdeaItem]
    pro_tip: str
    focus: IdeaFocus
    from_cache: bool = False


class SplitInfo(BaseModel):
    """A labeled allocation percentage."""

    category: str
    label: str
    percent: int


class EventTypeInfo(BaseModel):
    """The UI's event template source of truth."""

    key: EventType
    label: str
    description: str
    budget_split: list[SplitInfo]


class HealthResponse(BaseModel):
    """Non-sensitive process health information."""

    status: str
    version: str
    model: str
    storage_backend: str
    ai_configured: bool
