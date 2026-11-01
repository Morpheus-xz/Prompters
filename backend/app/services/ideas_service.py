"""Ground creative requests in computed plan facts and cache validated results."""

import json
import logging

from app.config import MIN_IDEAS
from app.exceptions import AIServiceError
from app.models.enums import IdeaFocus
from app.models.responses import IdeasDraft, IdeasResponse, PlanDetail
from app.services.ai_client import AIClient
from app.services.cache import TTLCache
from app.services.prompts import IDEAS_PROMPT
from app.services.sanitize import sanitize_free_text

logger = logging.getLogger(__name__)


class IdeasService:
    """Validate categories and manage bounded per-plan creative results."""

    def __init__(
        self, ai: AIClient, cache: TTLCache[tuple[str, IdeaFocus], IdeasResponse]
    ) -> None:
        """Accept interchangeable generation and caching implementations."""
        self.ai = ai
        self.cache = cache

    async def generate(
        self, plan: PlanDetail, focus: IdeaFocus, refresh: bool = False
    ) -> IdeasResponse:
        """Return cached suggestions or validate a fresh creative response."""
        key = (plan.id, focus)
        cached = self.cache.get(key)
        if cached is not None and not refresh:
            return cached.model_copy(deep=True, update={"from_cache": True})
        draft = await self.ai.generate_json(self._prompt(plan, focus), IdeasDraft)
        ideas = [
            idea for idea in draft.ideas if idea.budget_category in plan.allocations
        ]
        if len(ideas) < MIN_IDEAS:
            logger.error("AI response did not contain enough valid categories")
            raise AIServiceError()
        result = IdeasResponse(ideas=ideas, pro_tip=draft.pro_tip, focus=focus)
        self.cache.set(key, result.model_copy(deep=True))
        return result

    def forget_plan(self, plan_id: str) -> None:
        """Remove every focus for a deleted plan."""
        for focus in IdeaFocus:
            self.cache.delete((plan_id, focus))

    def _prompt(self, plan: PlanDetail, focus: IdeaFocus) -> str:
        """Serialize untrusted fields as JSON values, never prompt instructions."""
        facts = {
            "event_type": plan.event_type.value,
            "guest_count": plan.guest_count,
            "per_guest_budget": plan.per_guest_budget,
            "currency": plan.currency,
            "days_until_event": plan.progress.days_until_event,
            "allocations": plan.allocations,
            "allowed_categories": list(plan.allocations),
            "city": sanitize_free_text(plan.city or ""),
            "preferences": sanitize_free_text(plan.preferences or ""),
            "focus": focus.value,
        }
        return IDEAS_PROMPT + json.dumps(facts, ensure_ascii=True)
