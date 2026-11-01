"""Bounded input shapes; business rules live in PlanService."""

from datetime import date
from typing import Annotated, Literal, get_args

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.config import (
    CITY_MAX,
    EXPENSE_DESC_MAX,
    MAX_BUDGET,
    MAX_GUESTS,
    MONEY_STEP,
    PREFERENCES_MAX,
    SUPPORTED_CURRENCIES,
    TITLE_MAX,
)
from app.models.enums import EventType, IdeaFocus, VendorStatus


def _clean_text(value: str) -> str:
    """Trim every input text field and reject whitespace-only text."""
    value = value.strip()
    if not value:
        raise ValueError("Text must not be blank.")
    return value


Text = Annotated[str, AfterValidator(_clean_text)]
MoneyAmount = Annotated[float, Field(gt=0, le=MAX_BUDGET, multiple_of=MONEY_STEP)]
Currency = Literal["INR", "USD", "EUR", "GBP"]
assert get_args(Currency) == SUPPORTED_CURRENCIES


class RequestModel(BaseModel):
    """Reject unexpected fields and non-finite numeric values."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class CreatePlanRequest(RequestModel):
    """The user's event brief."""

    title: Annotated[Text, Field(min_length=1, max_length=TITLE_MAX)]
    event_type: EventType
    event_date: date
    guest_count: int = Field(ge=1, le=MAX_GUESTS, strict=True)
    total_budget: MoneyAmount
    currency: Currency = "INR"
    city: Annotated[Text, Field(max_length=CITY_MAX)] | None = None
    preferences: Annotated[Text, Field(max_length=PREFERENCES_MAX)] | None = None


class ExpenseRequest(RequestModel):
    """A categorized spend entry."""

    category: Annotated[Text, Field(max_length=TITLE_MAX)]
    amount: MoneyAmount
    description: Annotated[Text, Field(max_length=EXPENSE_DESC_MAX)]


class TaskUpdateRequest(RequestModel):
    """Checklist completion input."""

    done: bool = Field(strict=True)


class VendorUpdateRequest(RequestModel):
    """Booking stage input."""

    status: VendorStatus


class IdeasRequest(RequestModel):
    """An optional creative focus and refresh request."""

    focus: IdeaFocus = IdeaFocus.overall
    refresh: bool = Field(default=False, strict=True)
