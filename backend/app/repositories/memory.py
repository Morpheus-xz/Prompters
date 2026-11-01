"""Process-local storage with copy isolation."""

from app.models.domain import Plan
from app.repositories.base import PlanRepository


class InMemoryPlanRepository(PlanRepository):
    """Keep every read and write isolated by owner and deep copy."""

    def __init__(self) -> None:
        """Initialize empty owner namespaces."""
        self._plans: dict[str, dict[str, Plan]] = {}

    async def add(self, plan: Plan) -> None:
        """Store a detached copy."""
        self._plans.setdefault(plan.owner_id, {})[plan.id] = plan.model_copy(deep=True)

    async def get(self, owner_id: str, plan_id: str) -> Plan | None:
        """Read a detached aggregate or nothing."""
        plan = self._plans.get(owner_id, {}).get(plan_id)
        return plan.model_copy(deep=True) if plan else None

    async def list(self, owner_id: str) -> list[Plan]:
        """Return detached plans in insertion order."""
        return [
            plan.model_copy(deep=True)
            for plan in self._plans.get(owner_id, {}).values()
        ]

    async def save(self, plan: Plan) -> None:
        """Replace a stored aggregate with a detached copy."""
        await self.add(plan)

    async def delete(self, owner_id: str, plan_id: str) -> None:
        """Remove the plan and reclaim empty namespaces."""
        owned = self._plans.get(owner_id, {})
        owned.pop(plan_id, None)
        if not owned:
            self._plans.pop(owner_id, None)
