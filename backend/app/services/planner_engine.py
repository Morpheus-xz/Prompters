"""A pure, deterministic planning engine computes every number and date.

Gemini only narrates creative ideas on top of data the engine already produced.
Gemini never does arithmetic. All functions accept their inputs, including today.
"""

from collections.abc import Iterable, Mapping
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
    ranked_categories = sorted(
        split_percent,
        key=lambda category: -(cents * split_percent[category] % PERCENT_TOTAL),
    )
    remaining_cents = cents - sum(shares.values())
    for category in ranked_categories[:remaining_cents]:
        shares[category] += 1
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


def _sum_money(amounts: Iterable[float]) -> float:
    """Sum decimal amounts before converting back to public JSON numbers."""
    return float(sum((Decimal(str(amount)) for amount in amounts), Decimal(0)))


def _budget_line(
    category: str, allocated: float, spent: float, warning_threshold: float
) -> BudgetLine:
    """Describe one category using the shared spending-state rule."""
    percent_used, state = _balance(allocated, spent, warning_threshold)
    return BudgetLine(
        category=category,
        label=CATEGORY_LABELS[category],
        allocated=allocated,
        spent=spent,
        remaining=round(allocated - spent, MONEY_DIGITS),
        percent_used=percent_used,
        state=state,
    )


def compute_budget_status(
    allocations: Mapping[str, float], expenses: list[Expense], warning_threshold: float
) -> BudgetStatus:
    """Aggregate expenses once, then build category and overall balances."""
    spending = dict.fromkeys(allocations, Decimal(0))
    for expense in expenses:
        spending[expense.category] += Decimal(str(expense.amount))
    lines = [
        _budget_line(category, allocated, float(spending[category]), warning_threshold)
        for category, allocated in allocations.items()
    ]
    total_allocated = _sum_money(allocations.values())
    total_spent = float(sum(spending.values(), Decimal(0)))
    percent_used, state = _balance(total_allocated, total_spent, warning_threshold)
    return BudgetStatus(
        lines=lines,
        total_allocated=total_allocated,
        total_spent=total_spent,
        total_remaining=round(total_allocated - total_spent, MONEY_DIGITS),
        percent_used=percent_used,
        state=state,
    )


def compute_progress(
    tasks: list[Task], vendors: list[Vendor], today: date, event_date: date
) -> Progress:
    """Weight completed tasks and essential bookings; empty groups contribute zero."""
    completed_tasks = sum(task.done for task in tasks)
    essential_vendors = [vendor for vendor in vendors if vendor.essential]
    booked_vendors = sum(
        vendor.status == VendorStatus.booked for vendor in essential_vendors
    )
    task_ratio = completed_tasks / len(tasks) if tasks else 0
    vendor_ratio = booked_vendors / len(essential_vendors) if essential_vendors else 0
    readiness = (
        task_ratio * READINESS_TASK_WEIGHT + vendor_ratio * READINESS_VENDOR_WEIGHT
    )
    return Progress(
        tasks_total=len(tasks),
        tasks_done=completed_tasks,
        overdue_count=sum(task.due_date < today and not task.done for task in tasks),
        essential_vendors_total=len(essential_vendors),
        essential_vendors_booked=booked_vendors,
        readiness_score=round(readiness),
        days_until_event=(event_date - today).days,
    )


def per_guest_budget(total: float, guests: int) -> float:
    """Return the indicative per-person allocation."""
    return round(total / guests, MONEY_DIGITS)
