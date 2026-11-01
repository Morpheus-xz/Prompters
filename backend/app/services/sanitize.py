"""Reduce untrusted free text before JSON-quoting it into a prompt."""

import unicodedata

from app.config import PREFERENCES_MAX


def sanitize_free_text(value: str) -> str:
    """Strip control/format characters, collapse whitespace and bound length."""
    cleaned = "".join(
        char for char in value if not unicodedata.category(char).startswith("C")
    )
    return " ".join(cleaned.split())[:PREFERENCES_MAX]
