"""Business rules and repository orchestration with an injected date clock."""

from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4

from app.config import (
    BUDGET_WARNING_THRESHOLD,
    EVENT_SPECS,
    MAX_EXPENSES_PER_PLAN,
    MAX_LEAD_DAYS,
    MAX_PLANS_PER_USER,
)
from app.exceptions import InvalidInputError, LimitExceededError, NotFoundError
from app.models.domain import Expense, Plan
from app.models.enums import VendorStatus
from app.models.requests import CreatePlanRequest, ExpenseRequest
from app.models.responses import PlanDetail, PlanSummary
from app.repositories.base import PlanRepository
from app.services.planner_engine import (
    allocate_budget,
    compute_budget_status,
    compute_progress,
    generate_timeline,
    generate_vendors,
    per_guest_budget,
)


class PlanService:
    """Apply business policy while delegating all calculations to pure functions."""

    def __init__(
        self, repo: PlanRepository, today: Callable[[], date] = date.today
    ) -> None:
        """Accept persistence and the single source of today's date."""
        self.repo = repo
        self.today = today

    async def create_plan(
        self, owner_id: str, request: CreatePlanRequest
    ) -> PlanDetail:
        """Validate policy and create a complete plan without contacting AI."""
        today = self.today()
        if not today < request.event_date <= today + timedelta(days=MAX_LEAD_DAYS):
            raise InvalidInputError(
                f"Event date must be within the next {MAX_LEAD_DAYS} days."
            )
        if len(await self.repo.list(owner_id)) >= MAX_PLANS_PER_USER:
            raise LimitExceededError("Plan limit reached. Delete a plan first.")
        tasks, compressed = generate_timeline(
            request.event_type, request.event_date, today
        )
        plan = Plan(
            **request.model_dump(),
            id=str(uuid4()),
            owner_id=owner_id,
            created_at=self._timestamp(),
            timeline_compressed=compressed,
            allocations=allocate_budget(
                request.total_budget, EVENT_SPECS[request.event_type].budget_split
            ),
            tasks=tasks,
            vendors=generate_vendors(request.event_type),
        )
        await self.repo.add(plan)
        return self.detail(plan)

    async def list_plans(self, owner_id: str) -> list[PlanSummary]:
        """Return public summaries for this owner."""
        return [
            PlanSummary.model_validate(p.model_dump())
            for p in await self.repo.list(owner_id)
        ]

    async def get_plan(self, owner_id: str, plan_id: str) -> Plan:
        """Load an owned plan, concealing foreign identifiers."""
        plan = await self.repo.get(owner_id, plan_id)
        if plan is None:
            raise NotFoundError()
        return plan

    async def delete_plan(self, plan: Plan) -> None:
        """Delete an already authorized aggregate."""
        await self.repo.delete(plan.owner_id, plan.id)

    async def add_expense(self, plan: Plan, request: ExpenseRequest) -> PlanDetail:
        """Record an expense only in an allocated category."""
        if request.category not in plan.allocations:
            raise InvalidInputError("Choose a category in this plan.")
        if len(plan.expenses) >= MAX_EXPENSES_PER_PLAN:
            raise LimitExceededError("Expense limit reached. Remove an expense first.")
        plan.expenses.append(
            Expense(
                **request.model_dump(), id=str(uuid4()), logged_at=self._timestamp()
            )
        )
        return await self._save(plan)

    async def remove_expense(self, plan: Plan, expense_id: str) -> PlanDetail:
        """Remove a known expense."""
        expense = next((e for e in plan.expenses if e.id == expense_id), None)
        if expense is None:
            raise NotFoundError()
        plan.expenses.remove(expense)
        return await self._save(plan)

    async def update_task(self, plan: Plan, task_id: str, done: bool) -> PlanDetail:
        """Update one task without changing its computed date."""
        task = next((t for t in plan.tasks if t.id == task_id), None)
        if task is None:
            raise NotFoundError()
        task.done = done
        return await self._save(plan)

    async def update_vendor(
        self, plan: Plan, vendor_id: str, status: VendorStatus
    ) -> PlanDetail:
        """Advance or reset a vendor's booking stage."""
        vendor = next((v for v in plan.vendors if v.id == vendor_id), None)
        if vendor is None:
            raise NotFoundError()
        vendor.status = status
        return await self._save(plan)

    def detail(self, plan: Plan) -> PlanDetail:
        """Build the sole public dashboard state from deterministic calculations."""
        return PlanDetail(
            **plan.model_dump(exclude={"owner_id"}),
            per_guest_budget=per_guest_budget(plan.total_budget, plan.guest_count),
            budget=compute_budget_status(
                plan.allocations, plan.expenses, BUDGET_WARNING_THRESHOLD
            ),
            progress=compute_progress(
                plan.tasks, plan.vendors, self.today(), plan.event_date
            ),
        )

    async def _save(self, plan: Plan) -> PlanDetail:
        """Persist before returning public state."""
        await self.repo.save(plan)
        return self.detail(plan)

    def _timestamp(self) -> datetime:
        """Use the injected day for stable UTC recording dates."""
        return datetime.combine(self.today(), time.min, UTC)
