"""A pure, deterministic planning engine computes every number and date.

Gemini only narrates creative ideas on top of data the engine already produced.
Gemini never does arithmetic. All functions accept their inputs, including today.
"""

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal

from app.config import (
    CATEGORY_LABELS,
    EVENT_SPECS,
    MONEY_DIGITS,
    MONEY_SCALE,
    PERCENT_TOTAL,
    READINESS_TASK_WEIGHT,
    READINESS_VENDOR_WEIGHT,
)
from app.models.domain import Expense, Task, Vendor
from app.models.enums import BudgetState, EventType, VendorStatus
from app.models.responses import BudgetLine, BudgetStatus, Progress


def allocate_budget(total: float, split_percent: Mapping[str, int]) -> dict[str, float]:
    """Distribute integer cents by largest remainder, ties in registry order."""
    cents = int(Decimal(str(total)) * MONEY_SCALE)
    shares = {
        key: cents * percent // PERCENT_TOTAL for key, percent in split_percent.items()
    }
    ranked = sorted(
        split_percent, key=lambda k: -(cents * split_percent[k] % PERCENT_TOTAL)
    )
    for key in ranked[: cents - sum(shares.values())]:
        shares[key] += 1
    return {key: value / MONEY_SCALE for key, value in shares.items()}


def generate_timeline(
    event_type: EventType, event_date: date, today: date
) -> tuple[list[Task], bool]:
    """Build backward dates, proportionally compressing short lead times."""
    steps = EVENT_SPECS[event_type].timeline
    available = max(0, (event_date - today).days)
    longest = max(step.days_before for step in steps)
    compressed = available < longest
    ratio = min(available / longest, 1)
    tasks = [
        Task(
            id=f"task-{index:02d}",
            title=step.title,
            category=step.category,
            due_date=event_date - timedelta(days=round(step.days_before * ratio)),
        )
        for index, step in enumerate(steps, 1)
    ]
    return sorted(tasks, key=lambda task: (task.due_date, task.id)), compressed


def generate_vendors(event_type: EventType) -> list[Vendor]:
    """Copy registry vendors with stable identifiers."""
    return [
        Vendor(
            id=f"vendor-{index:02d}",
            name=spec.name,
            category=spec.category,
            essential=spec.essential,
        )
        for index, spec in enumerate(EVENT_SPECS[event_type].vendors, 1)
    ]


def _balance(
    allocated: float, spent: float, threshold: float
) -> tuple[float, BudgetState]:
    """Calculate a safe percentage and spending state."""
    percent = (
        round(spent / allocated * PERCENT_TOTAL, MONEY_DIGITS) if allocated else 0.0
    )
    if spent > allocated:
        return percent, BudgetState.over
    if percent >= threshold * PERCENT_TOTAL:
        return percent, BudgetState.warning
    return percent, BudgetState.on_track


def compute_budget_status(
    allocations: Mapping[str, float], expenses: list[Expense], warning_threshold: float
) -> BudgetStatus:
    """Aggregate costs once, then compute category and overall status."""
    spent = dict.fromkeys(allocations, Decimal(0))
    for expense in expenses:
        spent[expense.category] += Decimal(str(expense.amount))
    lines = []
    for category, allocated in allocations.items():
        amount = float(spent[category])
        percent, state = _balance(allocated, amount, warning_threshold)
        lines.append(
            BudgetLine(
                category=category,
                label=CATEGORY_LABELS[category],
                allocated=allocated,
                spent=amount,
                remaining=round(allocated - amount, MONEY_DIGITS),
                percent_used=percent,
                state=state,
            )
        )
    total = float(sum((Decimal(str(v)) for v in allocations.values()), Decimal(0)))
    used = float(sum(spent.values(), Decimal(0)))
    percent, state = _balance(total, used, warning_threshold)
    return BudgetStatus(
        lines=lines,
        total_allocated=total,
        total_spent=used,
        total_remaining=round(total - used, MONEY_DIGITS),
        percent_used=percent,
        state=state,
    )


def compute_progress(
    tasks: list[Task], vendors: list[Vendor], today: date, event_date: date
) -> Progress:
    """Weight checklist completion and essential bookings, safely on empty inputs."""
    done = sum(task.done for task in tasks)
    essential = [vendor for vendor in vendors if vendor.essential]
    booked = sum(vendor.status == VendorStatus.booked for vendor in essential)
    score = (done / len(tasks) if tasks else 0) * READINESS_TASK_WEIGHT + (
        booked / len(essential) if essential else 0
    ) * READINESS_VENDOR_WEIGHT
    return Progress(
        tasks_total=len(tasks),
        tasks_done=done,
        overdue_count=sum(t.due_date < today and not t.done for t in tasks),
        essential_vendors_total=len(essential),
        essential_vendors_booked=booked,
        readiness_score=round(score),
        days_until_event=(event_date - today).days,
    )


def per_guest_budget(total: float, guests: int) -> float:
    """Return the indicative per-person allocation."""
    return round(total / guests, MONEY_DIGITS)
