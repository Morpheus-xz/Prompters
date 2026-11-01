"""Owner-scoped persistence contract."""

from abc import ABC, abstractmethod

from app.models.domain import Plan


class PlanRepository(ABC):
    """Replaceable persistence boundary for planning aggregates."""

    @abstractmethod
    async def add(self, plan: Plan) -> None:
        """Insert a plan."""

    @abstractmethod
    async def get(self, owner_id: str, plan_id: str) -> Plan | None:
        """Read only within an owner's namespace."""

    @abstractmethod
    async def list(self, owner_id: str) -> list[Plan]:
        """List one owner's plans."""

    @abstractmethod
    async def save(self, plan: Plan) -> None:
        """Persist an updated aggregate."""

    @abstractmethod
    async def delete(self, owner_id: str, plan_id: str) -> None:
        """Remove within an owner's namespace."""
