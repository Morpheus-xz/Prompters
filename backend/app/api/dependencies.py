"""Owner identity and dependency-injected application services."""

from functools import lru_cache
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, Request, Response

from app.config import (
    IDEAS_CACHE_TTL_SECONDS,
    MAX_CACHE_ENTRIES,
    OWNER_COOKIE_MAX_AGE,
    OWNER_COOKIE_NAME,
)
from app.models.domain import Plan
from app.models.enums import IdeaFocus
from app.models.responses import IdeasResponse
from app.repositories.base import PlanRepository
from app.repositories.memory import InMemoryPlanRepository
from app.services.ai_client import AIClient, GeminiClient
from app.services.cache import TTLCache
from app.services.ideas_service import IdeasService
from app.services.plan_service import PlanService


def get_owner_id(request: Request, response: Response) -> str:
    """Validate anonymous identity and issue a secure first-visit cookie."""
    raw = request.cookies.get(OWNER_COOKIE_NAME)
    try:
        return str(UUID(raw)) if raw else _new_owner(request, response)
    except ValueError:
        return _new_owner(request, response)


def _new_owner(request: Request, response: Response) -> str:
    """Set identity directly on the dependency response."""
    owner = str(uuid4())
    secure = (
        request.headers.get("x-forwarded-proto") == "https"
        or request.url.scheme == "https"
    )
    response.set_cookie(
        OWNER_COOKIE_NAME,
        owner,
        max_age=OWNER_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=secure,
    )
    return owner


@lru_cache
def get_repository() -> PlanRepository:
    """Share the process-local repository."""
    return InMemoryPlanRepository()


def get_plan_service(
    repo: Annotated[PlanRepository, Depends(get_repository)],
) -> PlanService:
    """Construct orchestration around the injected repository."""
    return PlanService(repo)


@lru_cache
def get_ai_client() -> AIClient:
    """Share a lazy Gemini adapter."""
    return GeminiClient()


@lru_cache
def _ideas_cache() -> TTLCache[tuple[str, IdeaFocus], IdeasResponse]:
    """Share bounded creative storage for this process."""
    return TTLCache(IDEAS_CACHE_TTL_SECONDS, MAX_CACHE_ENTRIES)


def get_ideas_service(ai: Annotated[AIClient, Depends(get_ai_client)]) -> IdeasService:
    """Wire creative generation without constructing an SDK client."""
    return IdeasService(ai, _ideas_cache())


async def get_owned_plan(
    plan_id: str,
    owner: Annotated[str, Depends(get_owner_id)],
    service: Annotated[PlanService, Depends(get_plan_service)],
) -> Plan:
    """Return 404 for both absent and foreign aggregates."""
    return await service.get_plan(owner, plan_id)


Owner = Annotated[str, Depends(get_owner_id)]
Planner = Annotated[PlanService, Depends(get_plan_service)]
OwnedPlan = Annotated[Plan, Depends(get_owned_plan)]
Creative = Annotated[IdeasService, Depends(get_ideas_service)]
