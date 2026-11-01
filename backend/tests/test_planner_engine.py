from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.config import BUDGET_WARNING_THRESHOLD, EVENT_SPECS
from app.models.domain import Expense, Task, Vendor
from app.models.enums import EventType, VendorStatus
from app.services.planner_engine import (
    allocate_budget,
    compute_budget_status,
    compute_progress,
    generate_timeline,
    generate_vendors,
    per_guest_budget,
)


@pytest.mark.parametrize("event_type", list(EventType))
@pytest.mark.parametrize("total", [0.01, 0.02, 0.07, 1.01, 7.99, 100.03, 999999999.99])
def test_exact_allocation(event_type: EventType, total: float) -> None:
    """Verify exact allocation."""
    allocation = allocate_budget(total, EVENT_SPECS[event_type].budget_split)
    assert sum(Decimal(str(v)) for v in allocation.values()) == Decimal(str(total))
    assert allocation == allocate_budget(total, EVENT_SPECS[event_type].budget_split)


def test_ties() -> None:
    """Verify ties."""
    assert allocate_budget(0.01, {"first": 50, "second": 50}) == {
        "first": 0.01,
        "second": 0,
    }


@pytest.mark.parametrize("kind", list(EventType))
def test_registry_integrity(kind: EventType) -> None:
    """Verify registry integrity."""
    spec = EVENT_SPECS[kind]
    assert sum(spec.budget_split.values()) == 100
    assert all(
        t.category in spec.budget_split or t.category == "planning"
        for t in spec.timeline
    )
    assert all(v.category in spec.budget_split for v in spec.vendors)
    assert all(v.status == VendorStatus.to_contact for v in generate_vendors(kind))
    with pytest.raises(TypeError):
        spec.budget_split["venue"] = 0  # type: ignore[index]


@pytest.mark.parametrize("kind", list(EventType))
@pytest.mark.parametrize("lead", [1, 10, 500])
def test_timeline(kind: EventType, lead: int) -> None:
    """Verify timeline."""
    today = date(2026, 1, 1)
    tasks, compressed = generate_timeline(kind, today + timedelta(days=lead), today)
    assert compressed == (lead < max(t.days_before for t in EVENT_SPECS[kind].timeline))
    assert tasks == sorted(tasks, key=lambda t: (t.due_date, t.id))
    assert all(today <= task.due_date <= today + timedelta(days=lead) for task in tasks)
    assert len({t.id for t in tasks}) == len(tasks)
    expected = round(
        EVENT_SPECS[kind].timeline[0].days_before
        * min(lead / max(t.days_before for t in EVENT_SPECS[kind].timeline), 1)
    )
    assert tasks[0].due_date == today + timedelta(days=lead - expected)


@pytest.mark.parametrize(
    ("amount", "state"),
    [(79.99, "on_track"), (80, "warning"), (100, "warning"), (100.01, "over")],
)
def test_budget_threshold(amount: float, state: str) -> None:
    """Verify budget threshold."""
    expense = Expense(
        id="e",
        category="venue",
        amount=amount,
        description="Deposit",
        logged_at=datetime.now(UTC),
    )
    result = compute_budget_status({"venue": 100}, [expense], BUDGET_WARNING_THRESHOLD)
    assert result.state == state
    assert result.lines[0].state == state
    assert result.total_remaining == round(100 - amount, 2)


def test_zero_budget_and_empty_progress() -> None:
    """Verify zero budget and empty progress."""
    result = compute_budget_status({"venue": 0}, [], BUDGET_WARNING_THRESHOLD)
    assert result.percent_used == 0
    assert result.state == "on_track"
    progress = compute_progress([], [], date.today(), date.today())
    assert progress.readiness_score == 0
    assert per_guest_budget(100, 3) == 33.33


@pytest.mark.parametrize("done", [True, False])
@pytest.mark.parametrize("booked", [True, False])
def test_progress(done: bool, booked: bool) -> None:
    """Verify progress."""
    today = date(2026, 1, 1)
    task = Task(
        id="t",
        title="Book",
        category="venue",
        due_date=today - timedelta(days=1),
        done=done,
    )
    vendor = Vendor(
        id="v",
        name="Hall",
        category="venue",
        essential=True,
        status=VendorStatus.booked if booked else VendorStatus.contacted,
    )
    progress = compute_progress([task], [vendor], today, today + timedelta(days=5))
    assert progress.readiness_score == int(done) * 60 + int(booked) * 40
    assert 0 <= progress.readiness_score <= 100
    assert progress.overdue_count == int(not done)
    assert progress.days_until_event == 5
