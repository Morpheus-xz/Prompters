"""Budget expense tracking endpoints."""

from fastapi import APIRouter, Request, Response

from app.api.dependencies import OwnedPlan, Planner
from app.api.limiter import limiter
from app.config import RATE_LIMIT_WRITE
from app.models.requests import ExpenseRequest
from app.models.responses import PlanDetail

router = APIRouter(tags=["budget"])


@router.post("/plans/{plan_id}/expenses", response_model=PlanDetail)
@limiter.limit(RATE_LIMIT_WRITE)
async def add_expense(
    request: Request,
    response: Response,
    body: ExpenseRequest,
    plan: OwnedPlan,
    service: Planner,
) -> PlanDetail:
    """Record categorized spending and recompute all balances."""
    return await service.add_expense(plan, body)


@router.delete("/plans/{plan_id}/expenses/{expense_id}")
@limiter.limit(RATE_LIMIT_WRITE)
async def remove_expense(
    request: Request,
    response: Response,
    expense_id: str,
    plan: OwnedPlan,
    service: Planner,
) -> PlanDetail:
    """Remove a recorded expense."""
    return await service.remove_expense(plan, expense_id)
