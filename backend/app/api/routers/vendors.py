"""Vendors checklist endpoint."""

from fastapi import APIRouter, Request, Response

from app.api.dependencies import OwnedPlan, Planner
from app.api.limiter import limiter
from app.config import RATE_LIMIT_WRITE
from app.models.requests import VendorUpdateRequest
from app.models.responses import PlanDetail

router = APIRouter(tags=["vendors"])


@router.patch("/plans/{plan_id}/vendors/{item_id}")
@limiter.limit(RATE_LIMIT_WRITE)
async def update_vendor(
    request: Request,
    response: Response,
    item_id: str,
    body: VendorUpdateRequest,
    plan: OwnedPlan,
    service: Planner,
) -> PlanDetail:
    """Update one checklist item and return the complete dashboard."""
    return await service.update_vendor(plan, item_id, body.status)
