"""Stored mutable planning entities."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import EventType, VendorStatus


class Task(BaseModel):
    """A dated checklist item."""

    id: str
    title: str
    category: str
    due_date: date
    done: bool = False


class Vendor(BaseModel):
    """A vendor and booking stage."""

    id: str
    name: str
    category: str
    essential: bool
    status: VendorStatus = VendorStatus.to_contact


class Expense(BaseModel):
    """A recorded cost in the plan currency."""

    id: str
    category: str
    amount: float
    description: str
    logged_at: datetime


class Plan(BaseModel):
    """An owner's complete planning aggregate."""

    id: str
    owner_id: str
    title: str
    event_type: EventType
    event_date: date
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
    expenses: list[Expense] = Field(default_factory=list)
