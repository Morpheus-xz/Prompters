"""Central policy values and immutable event templates."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.models.enums import EventType

APP_NAME = "Festiva - AI Event Planner"
VERSION = "1.0.0"
GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
SDK_NETWORK_ATTEMPTS = 1
AI_THINKING_BUDGET = 0
AI_TIMEOUT_MS = 15000
AI_MAX_OUTPUT_TOKENS = 4096
MAX_BODY_BYTES = 65_536
MAX_PLANS_PER_USER = 10
MAX_EXPENSES_PER_PLAN = 200
MAX_GUESTS = 5000
MAX_BUDGET = 1_000_000_000
MAX_LEAD_DAYS = 1825
TITLE_MAX = 80
CITY_MAX = 60
PREFERENCES_MAX = 300
EXPENSE_DESC_MAX = 120
BUDGET_WARNING_THRESHOLD = 0.8
READINESS_TASK_WEIGHT = 60
READINESS_VENDOR_WEIGHT = 40
IDEAS_CACHE_TTL_SECONDS = 1800
MAX_CACHE_ENTRIES = 500
OWNER_COOKIE_NAME = "festiva_uid"
OWNER_COOKIE_MAX_AGE = 31_536_000
RATE_LIMIT_WRITE = "60/minute"
RATE_LIMIT_AI = "10/minute"
SUPPORTED_CURRENCIES = ("INR", "USD", "EUR", "GBP")
MILLISECONDS_PER_SECOND = 1000
MONEY_STEP = 0.01
PERCENT_TOTAL = 100
MONEY_SCALE = 100
MONEY_DIGITS = 2
MIN_IDEAS = 3
PROMPT_IDEAS_MIN = 5
PROMPT_IDEAS_MAX = 6
IDEA_TITLE_MAX = 120
IDEA_DESCRIPTION_MAX = 500
PRO_TIP_MAX = 500
STATIC_MAX_AGE = 3600
GZIP_MIN_SIZE = 1000
RETRY_MIN_SECONDS = 1
RETRY_MAX_SECONDS = 8
HSTS_MAX_AGE = 31_536_000
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
    "form-action 'self'; frame-ancestors 'none'"
)
DOCS_CSP = CSP.replace(
    "script-src 'self'", "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'"
).replace(
    "style-src 'self'", "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'"
)
CATEGORY_LABELS = {
    "venue": "Venue",
    "catering": "Food & catering",
    "photography": "Photography & video",
    "decor": "Decor & styling",
    "attire_beauty": "Attire & beauty",
    "entertainment": "Entertainment",
    "invitations": "Invitations & stationery",
    "transport": "Transport & logistics",
    "gifts_favors": "Gifts & favors",
    "cake_desserts": "Cake & desserts",
    "equipment_av": "Equipment & AV",
    "marketing": "Marketing & outreach",
    "volunteers_supplies": "Volunteers & supplies",
    "safety_insurance": "Safety & insurance",
    "contingency": "Contingency buffer",
    "planning": "Planning",
}


@dataclass(frozen=True)
class TimelineStep:
    """A relative deadline."""

    title: str
    category: str
    days_before: int


@dataclass(frozen=True)
class VendorSpec:
    """A vendor template."""

    name: str
    category: str
    essential: bool


@dataclass(frozen=True)
class EventSpec:
    """An immutable event planning policy."""

    label: str
    description: str
    budget_split: Mapping[str, int]
    timeline: tuple[TimelineStep, ...]
    vendors: tuple[VendorSpec, ...]

    def __post_init__(self) -> None:
        """Freeze the nested allocation mapping."""
        object.__setattr__(
            self, "budget_split", MappingProxyType(dict(self.budget_split))
        )


EVENT_SPECS: Mapping[EventType, EventSpec] = MappingProxyType(
    {
        EventType.wedding: EventSpec(
            "Wedding",
            "A thoughtful celebration, from first booking to final vows.",
            {
                "venue": 25,
                "catering": 30,
                "photography": 10,
                "decor": 8,
                "attire_beauty": 7,
                "entertainment": 5,
                "invitations": 2,
                "transport": 3,
                "gifts_favors": 2,
                "contingency": 8,
            },
            (
                TimelineStep("Fix budget and priorities", "planning", 365),
                TimelineStep("Draft guest list", "planning", 350),
                TimelineStep("Shortlist and book venue", "venue", 335),
                TimelineStep("Book photographer and videographer", "photography", 280),
                TimelineStep("Book caterer and schedule tasting", "catering", 250),
                TimelineStep("Book DJ or live band", "entertainment", 225),
                TimelineStep(
                    "Order attire and book beauty trials", "attire_beauty", 196
                ),
                TimelineStep("Send save-the-dates", "invitations", 182),
                TimelineStep("Plan decor and flowers", "decor", 140),
                TimelineStep("Arrange guest transport and stay", "transport", 112),
                TimelineStep("Order guest favors", "gifts_favors", 60),
                TimelineStep("Send formal invitations", "invitations", 56),
                TimelineStep("Finalize menu and headcount", "catering", 28),
                TimelineStep("Confirm every vendor in writing", "planning", 14),
                TimelineStep(
                    "Prepare day-of schedule and emergency kit", "planning", 7
                ),
                TimelineStep("Final venue walkthrough", "venue", 2),
            ),
            (
                VendorSpec("Venue", "venue", True),
                VendorSpec("Caterer", "catering", True),
                VendorSpec("Photographer and videographer", "photography", True),
                VendorSpec("Decorator or florist", "decor", False),
                VendorSpec("Makeup and hair artist", "attire_beauty", False),
                VendorSpec("DJ or live band", "entertainment", False),
                VendorSpec("Invitation printer", "invitations", False),
                VendorSpec("Guest transport provider", "transport", False),
            ),
        ),
        EventType.birthday: EventSpec(
            "Birthday",
            "Make their day personal, playful and easy to host.",
            {
                "venue": 20,
                "catering": 35,
                "cake_desserts": 8,
                "decor": 12,
                "entertainment": 12,
                "invitations": 2,
                "gifts_favors": 4,
                "photography": 2,
                "contingency": 5,
            },
            (
                TimelineStep("Set budget and guest count", "planning", 56),
                TimelineStep("Pick date and book venue", "venue", 49),
                TimelineStep("Choose a theme", "decor", 42),
                TimelineStep("Book entertainment or activities", "entertainment", 35),
                TimelineStep("Book caterer or plan home menu", "catering", 30),
                TimelineStep("Send invitations", "invitations", 28),
                TimelineStep("Order cake", "cake_desserts", 21),
                TimelineStep("Buy decor and favors", "gifts_favors", 14),
                TimelineStep("Confirm RSVPs and headcount", "planning", 7),
                TimelineStep("Confirm vendors and delivery times", "planning", 3),
                TimelineStep("Set up the venue", "venue", 0),
            ),
            (
                VendorSpec("Venue or party hall", "venue", True),
                VendorSpec("Caterer or restaurant", "catering", True),
                VendorSpec("Cake maker", "cake_desserts", True),
                VendorSpec("Decorator", "decor", False),
                VendorSpec("Entertainer or DJ", "entertainment", False),
                VendorSpec("Photographer", "photography", False),
            ),
        ),
        EventType.community: EventSpec(
            "Community",
            "Bring people together with purpose and a practical plan.",
            {
                "venue": 20,
                "catering": 25,
                "equipment_av": 15,
                "marketing": 10,
                "entertainment": 10,
                "volunteers_supplies": 8,
                "safety_insurance": 5,
                "contingency": 7,
            },
            (
                TimelineStep("Define goals, audience and budget", "planning", 120),
                TimelineStep("Secure venue and permits", "venue", 105),
                TimelineStep(
                    "Recruit volunteers and assign roles", "volunteers_supplies", 90
                ),
                TimelineStep(
                    "Arrange insurance and safety plan", "safety_insurance", 75
                ),
                TimelineStep("Book AV equipment", "equipment_av", 60),
                TimelineStep("Line up performers and speakers", "entertainment", 55),
                TimelineStep("Launch marketing and outreach", "marketing", 50),
                TimelineStep("Confirm food and refreshments", "catering", 30),
                TimelineStep(
                    "Brief volunteers and share run-of-show", "volunteers_supplies", 7
                ),
                TimelineStep("Final site safety check", "safety_insurance", 1),
            ),
            (
                VendorSpec("Venue or permit authority", "venue", True),
                VendorSpec("Caterer or food vendors", "catering", True),
                VendorSpec("AV and equipment supplier", "equipment_av", True),
                VendorSpec("First-aid and security provider", "safety_insurance", True),
                VendorSpec("Printer for posters and flyers", "marketing", False),
                VendorSpec("Performers or speakers", "entertainment", False),
            ),
        ),
    }
)
