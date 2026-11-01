"""Process health and UI template metadata."""

from fastapi import APIRouter

from app.config import CATEGORY_LABELS, EVENT_SPECS, GEMINI_MODEL, VERSION
from app.models.responses import EventTypeInfo, HealthResponse, SplitInfo
from app.settings import get_settings

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health() -> HealthResponse:
    """Report process health without credentials."""
    return HealthResponse(
        status="ok",
        version=VERSION,
        model=GEMINI_MODEL,
        storage_backend="in-memory",
        ai_configured=bool(get_settings().gemini_api_key),
    )


@router.get("/event-types")
async def event_types() -> list[EventTypeInfo]:
    """Expose the registry for form choices and allocation previews."""
    return [
        EventTypeInfo(
            key=key,
            label=spec.label,
            description=spec.description,
            budget_split=[
                SplitInfo(category=cat, label=CATEGORY_LABELS[cat], percent=pct)
                for cat, pct in spec.budget_split.items()
            ],
        )
        for key, spec in EVENT_SPECS.items()
    ]
