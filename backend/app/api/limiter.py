"""Shared rate limiter keyed to Render's forwarded client address."""

from fastapi import Request
from slowapi import Limiter

from app.settings import get_settings


def client_address(request: Request) -> str:
    """Use Render's proxy header; direct hosts must strip untrusted forwarding."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_address, enabled=get_settings().rate_limit_enabled)
