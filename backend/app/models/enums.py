"""Shared vocabulary; no application dependencies."""

from enum import Enum


class EventType(str, Enum):
    """Supported event templates."""

    wedding = "wedding"
    birthday = "birthday"
    community = "community"


class VendorStatus(str, Enum):
    """Vendor booking stages."""

    to_contact = "to_contact"
    contacted = "contacted"
    booked = "booked"


class IdeaFocus(str, Enum):
    """Creative request focus."""

    overall = "overall"
    theme = "theme"
    food = "food"
    entertainment = "entertainment"
    decor = "decor"
    activities = "activities"
    saving_money = "saving_money"


class CostLevel(str, Enum):
    """Qualitative cost bands."""

    low = "low"
    medium = "medium"
    high = "high"


class BudgetState(str, Enum):
    """Spending health indicators."""

    on_track = "on_track"
    warning = "warning"
    over = "over"
