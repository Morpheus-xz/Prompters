"""Timeline checklist endpoint."""

from fastapi import APIRouter, Request, Response

from app.api.dependencies import OwnedPlan, Planner
from app.api.limiter import limiter
from app.config import RATE_LIMIT_WRITE
from app.models.requests import TaskUpdateRequest
from app.models.responses import PlanDetail

router = APIRouter(tags=["timeline"])


@router.patch("/plans/{plan_id}/tasks/{item_id}")
@limiter.limit(RATE_LIMIT_WRITE)
async def update_task(
    request: Request,
    response: Response,
    item_id: str,
    body: TaskUpdateRequest,
    plan: OwnedPlan,
    service: Planner,
) -> PlanDetail:
    """Update one checklist item and return the complete dashboard."""
    return await service.update_task(plan, item_id, body.done)
