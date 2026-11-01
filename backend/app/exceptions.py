"""Typed failures safe to expose at the API boundary."""


class PlannerError(Exception):
    """A client-safe application failure."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Store the response status and safe description."""
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class NotFoundError(PlannerError):
    """An absent or foreign resource."""

    def __init__(self) -> None:
        """Avoid revealing whether another owner has this ID."""
        super().__init__(404, "Resource not found.")


class InvalidInputError(PlannerError):
    """A business rule violation."""

    def __init__(self, detail: str) -> None:
        """Describe the invalid input."""
        super().__init__(422, detail)


class LimitExceededError(PlannerError):
    """A bounded collection reached capacity."""

    def __init__(self, detail: str) -> None:
        """Describe the capacity limit."""
        super().__init__(409, detail)


class AIServiceError(PlannerError):
    """A private upstream failure."""

    def __init__(self) -> None:
        """Expose no model, credentials or upstream error details."""
        super().__init__(502, "Ideas are temporarily unavailable. Please try again.")
