"""Grounded creative suggestions endpoint."""

from fastapi import APIRouter, Request, Response

from app.api.dependencies import Creative, OwnedPlan, Planner
from app.api.limiter import limiter
from app.config import RATE_LIMIT_AI
from app.models.requests import IdeasRequest
from app.models.responses import IdeasResponse

router = APIRouter(tags=["ideas"])


@router.post("/plans/{plan_id}/ideas", response_model=IdeasResponse)
@limiter.limit(RATE_LIMIT_AI)
async def generate_ideas(
    request: Request,
    response: Response,
    body: IdeasRequest,
    plan: OwnedPlan,
    service: Planner,
    ideas: Creative,
) -> IdeasResponse:
    """Generate or reuse validated creative ideas grounded in this plan."""
    return await ideas.generate(service.detail(plan), body.focus, body.refresh)
