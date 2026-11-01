"""Plan lifecycle endpoints."""

from fastapi import APIRouter, Request, Response

from app.api.dependencies import Creative, OwnedPlan, Owner, Planner
from app.api.limiter import limiter
from app.config import RATE_LIMIT_WRITE
from app.models.requests import CreatePlanRequest
from app.models.responses import PlanDetail, PlanSummary

router = APIRouter(tags=["plans"])


@router.post("/plans", status_code=201, response_model=PlanDetail)
@limiter.limit(RATE_LIMIT_WRITE)
async def create_plan(
    request: Request,
    response: Response,
    body: CreatePlanRequest,
    owner: Owner,
    service: Planner,
) -> PlanDetail:
    """Create an instant deterministic plan on the first visit too."""
    return await service.create_plan(owner, body)


@router.get("/plans")
async def list_plans(owner: Owner, service: Planner) -> list[PlanSummary]:
    """List this anonymous owner's plans."""
    return await service.list_plans(owner)


@router.get("/plans/{plan_id}")
async def get_plan(plan: OwnedPlan, service: Planner) -> PlanDetail:
    """Return the authorized dashboard."""
    return service.detail(plan)


@router.delete("/plans/{plan_id}", status_code=204)
@limiter.limit(RATE_LIMIT_WRITE)
async def delete_plan(
    request: Request,
    response: Response,
    plan: OwnedPlan,
    service: Planner,
    ideas: Creative,
) -> None:
    """Delete state and forget all associated creative results."""
    await service.delete_plan(plan)
    ideas.forget_plan(plan.id)
