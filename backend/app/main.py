"""Application factory, shared exception handling and static entry point."""

import logging
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware

from app.api.limiter import limiter
from app.api.middleware import RequestPolicyMiddleware, response_headers
from app.api.routers import budget, ideas, meta, plans, timeline, vendors
from app.config import APP_NAME, GZIP_MIN_SIZE, MILLISECONDS_PER_SECOND, VERSION
from app.exceptions import PlannerError
from app.settings import get_settings

logging.basicConfig(level=get_settings().log_level)


def create_app() -> FastAPI:
    """Wire routes and wrap all responses with the request policy."""
    application = FastAPI(
        title=APP_NAME,
        version=VERSION,
        openapi_tags=[
            {"name": name, "description": description}
            for name, description in (
                ("budget", "Category allocations, spending and overspend alerts."),
                ("timeline", "Backward scheduling and task completion."),
                ("vendors", "Essential and optional booking checklists."),
                ("ideas", "Validated Gemini suggestions grounded in your plan."),
                ("plans", "Anonymous owner-scoped plan lifecycle."),
                ("meta", "Health and event template metadata."),
            )
        ],
    )
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    application.add_exception_handler(PlannerError, planner_error_handler)
    application.add_exception_handler(Exception, unexpected_error_handler)
    for module in (meta, plans, budget, timeline, vendors, ideas):
        application.include_router(module.router)
    application.mount(
        "/static", StaticFiles(directory=frontend_directory()), name="static"
    )
    application.add_api_route("/", index, include_in_schema=False)
    application.add_middleware(GZipMiddleware, minimum_size=GZIP_MIN_SIZE)
    application.add_middleware(RequestPolicyMiddleware)
    return application


async def rate_limit_handler(request: Request, exc: Exception) -> Response:
    """Adapt SlowAPI’s typed handler to the ASGI exception contract."""
    assert isinstance(exc, RateLimitExceeded)
    return _rate_limit_exceeded_handler(request, exc)


async def planner_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert every typed application failure at one boundary."""
    assert isinstance(exc, PlannerError)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Keep unexpected failures generic and retain security headers on 500s."""
    elapsed = (
        perf_counter() - request.scope["festiva_started"]
    ) * MILLISECONDS_PER_SECOND
    logging.getLogger(__name__).error(
        "%s %s 500 %.2fms", request.method, request.url.path, elapsed, exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
        headers=response_headers(request.url.path),
    )


def frontend_directory() -> Path:
    """Locate frontend assets independently of the process working directory."""
    return Path(__file__).resolve().parents[2] / "frontend"


async def index() -> FileResponse:
    """Serve the same-origin accessible dashboard."""
    return FileResponse(frontend_directory() / "index.html")


app = create_app()
