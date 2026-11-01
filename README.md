# Festiva

A thoughtful AI event-planning assistant: clear budgets, doable timelines, vendor checklists and ideas that feel like you.

Live demo: <ADD_RENDER_URL_AFTER_DEPLOY>

## Chosen vertical

Event planning for weddings, birthdays and community events. Built for Google Prompt Wars 2026 using Python 3.11, FastAPI, Pydantic v2, Gemini Developer API and vanilla browser ES modules.

> Problem statement: "Create a GenAI-powered planning assistant that helps users organize weddings, birthdays, and community events with budgets, timelines, vendor checklists, and personalized ideas."

## Problem-statement alignment

Each deliverable has one router, matching OpenAPI tag and UI section. Plan creation is instant and needs no API key.

| Deliverable | Feature | Endpoint | UI section | Router file / tag |
|---|---|---|---|---|
| Budget | Exact allocation, expense add/remove, category and overall overspend alerts | POST /plans/{plan_id}/expenses; DELETE /plans/{plan_id}/expenses/{expense_id} | Budget | backend/app/api/routers/budget.py / budget |
| Timeline | Backward scheduling, short-lead compression, completion and overdue indicators | PATCH /plans/{plan_id}/tasks/{item_id} | Timeline | backend/app/api/routers/timeline.py / timeline |
| Vendor checklist | Essential and optional providers; to contact, contacted, booked | PATCH /plans/{plan_id}/vendors/{item_id} | Vendor checklist | backend/app/api/routers/vendors.py / vendors |
| Personalized ideas | Focused Gemini suggestions grounded in the owner's computed plan | POST /plans/{plan_id}/ideas | Ideas for you | backend/app/api/routers/ideas.py / ideas |

Supporting routers: `plans` implements POST/GET /plans and GET/DELETE /plans/{plan_id}; `meta` exposes /health and /event-types. Full dashboard data includes allocations and schedules, so these need no additional GET endpoints.

## Approach and logic

A pure, deterministic planning engine computes every number and date; Gemini only narrates creative ideas on top of data the engine already produced. Gemini never does arithmetic.

- **Allocation:** convert a two-decimal budget to integer cents; assign floor shares; distribute leftover cents by descending fractional remainder, breaking ties in registry order. Values serialize as two-decimal money; cent totals reconcile exactly, verified with Decimal rather than binary-float summation.
- **Spending:** aggregate expenses once per category. Above allocation means Over budget; at or above 80% means Nearing limit; otherwise On track. A zero allocation cannot cause division by zero.
- **Scheduling:** subtract template offsets from the event date. If available lead time is shorter than the longest offset, multiply every offset by available/max, round, and flag compression. Dates stay between today and the event, ordered by date and template index.
- **Readiness:** round(completed-task ratio × 60 + booked-essential-vendor ratio × 40). Empty groups contribute zero; optional providers do not inflate readiness. Overdue means unfinished and due strictly before today.
- **AI grounding:** send event type, guest count, computed per-guest budget, currency, days remaining, allocations, allowed categories, sanitized city/preferences and focus as JSON data. No title, owner cookie, expense descriptions or vendor identities enter the prompt. Explicit instructions treat user fields as untrusted data and prohibit arithmetic and invented prices.
- **Validation:** Gemini returns JSON, then Pydantic validates 5–6 bounded items and a tip. Unknown budget categories are removed. At least three valid suggestions must remain; otherwise the same generic 502 is returned. Cost levels are qualitative. AI cannot modify the plan.

## How it works

```text
Browser ES modules → same-origin FastAPI router → owner dependency
                                              ↓
                                      PlanService → PlanRepository
                                              ↓
                                      pure planner_engine → PlanDetail
                                              ↓
For ideas only: computed facts → JSON prompt → lazy Gemini adapter
                                  → schema/category validation → TTL cache → UI
```

Create an event brief → receive the full deterministic plan → record expenses and check off tasks/bookings → optionally request ideas → refresh a creative focus when wanted → delete the plan and all cached focuses. Mutations return the full PlanDetail; deletion returns 204. The client renders server state and disables controls while a request is pending.

## Architecture

| Boundary | Implementation |
|---|---|
| Application wiring and one PlannerError handler | backend/app/main.py; backend/app/exceptions.py |
| Immutable registry, bounds and frozen cached environment settings | backend/app/config.py; backend/app/settings.py |
| Input shapes, domain entities and explicit public contracts | backend/app/models/ |
| Pure numeric/date functions and clock-injected business policy | backend/app/services/planner_engine.py; backend/app/services/plan_service.py |
| Abstract owner-scoped repository and detached in-memory copies | backend/app/repositories/base.py; backend/app/repositories/memory.py |
| Dependency injection, cookies, limits, headers and bounded request bodies | backend/app/api/ |
| Lazy model adapter, prompt policy, sanitization, validation and cache | backend/app/services/ai_client.py, prompts.py, sanitize.py, ideas_service.py, cache.py |
| One fetch boundary, client state, safe DOM builder and pure render modules | frontend/js/api.js, state.js, dom.js, render/; main.js orchestrates |

The repository pattern isolates storage. FastAPI dependencies inject repository, clock-backed service and AI adapter. Tests replace dependencies with real in-memory storage and a schema-validating FakeAIClient. Registry entries contain every event-specific split, task and vendor: there are no event-type branches in the engine. Adding a vocabulary member to EventType and one registry entry supports another type without changing planning algorithms or UI choices.

## Security

- Same-origin application with no CORS middleware. Strict CSP permits local scripts/styles; only documentation paths relax script/style policy for Swagger/ReDoc initialization and jsDelivr.
- UUID owner cookies are validated and set HttpOnly, SameSite=Lax and Secure on HTTPS (including Render's forwarded protocol). A first-visit POST creates and owns its plan in the same request. Foreign and missing IDs both return 404; owner_id never appears in public plan responses.
- Pydantic rejects extra request fields, blank text, non-finite/fractional-cent money, unsupported currencies and out-of-range values. The service enforces future dates within five years and category membership against the injected date clock.
- 65,536-byte request cap checks both Content-Length and actual streamed bytes. Plans are capped at 10 per owner; expenses at 200 per plan. Cache capacity is 500.
- SlowAPI limits mutation endpoints to 60/minute per route/IP and ideas to 10/minute. Forwarded IP extraction follows Render's proxy; a direct-host reverse proxy must strip untrusted forwarded headers. Limits are disabled only with ENV=test.
- Sanitization removes control/format characters and bounds text. JSON quoting, untrusted-data instructions, schema validation and category allowlisting are layered defenses, not a guarantee of perfect semantic model behavior.
- Gemini failures are logged server-side and exposed as a generic 502 by the shared PlannerError handler. Request logging contains only method, path, status and elapsed milliseconds.
- Security headers cover normal responses and HTTP errors, including body-limit rejections. API responses use no-store; static files use a one-hour public cache; the index uses no-cache.
- DOM construction uses textContent/text nodes. No HTML-string injection, dynamic code execution, external frontend dependencies, fonts or CDN assets. Secrets are environment-only, .env is ignored, and the Docker process runs as a non-root user.

## Efficiency

Plan creation makes no model call. Budget calculations aggregate expenses once, O(expenses + categories); schedule sorting is O(tasks log tasks), allocation ranking O(categories log categories). Stored aggregates are small and detached on reads/writes.

Creative results use a bounded LRU TTL cache (30 minutes), keyed by globally unique plan ID and focus; refresh bypasses it and deletion removes every focus. Cache values are copied before exposure. The SDK is lazy and cached; synchronous requests run in asyncio.to_thread. Only APIError triggers Tenacity's bounded exponential retry, at most three attempts. SDK retries are disabled to avoid multiplying requests. Each HTTP attempt has a 15-second timeout and output is capped at 4096 tokens. GZip compresses responses above 1000 bytes.

## Testing

```sh
make -C backend install
make -C backend audit
```

`make -C backend audit` runs Ruff lint/format, strict mypy on backend/app/, Vulture and pytest with branch coverage and a hard 95% threshold. Runtime and test dependencies are separate and their direct versions are pinned. Structural tests guard referenced config constants, source sizes, function sizes, docstrings and Python type hints. Run targets from backend/: test, cov, lint, format, typecheck, deadcode. `make clean` removes tooling caches.

Tests use injected date/monotonic clocks and fresh repositories; two TestClients have separate cookie jars. FakeAIClient validates the actual schema, counts calls and accepts configurable payloads/failures. Adapter tests use an explicitly injected HTTP transport; there are no external network requests or monkeypatches. Coverage includes awkward cents and ties, every registry, compression, tomorrow, empty/overdue readiness, exact spending thresholds, TTL/LRU, request validation, lifecycle, caps, isolation, first-POST ownership, sanitization, AI filtering/failures/refresh/purge, retry bounds, headers, body-size enforcement and rate-limit restoration in finally.

## Accessibility

English document language, a first-element skip link, header/nav/main/footer landmarks, one visible h1, labeled sections and native controls. Budget health includes symbols and text, essential/overdue badges are textual, and progress has a label. Form hints and inline errors are linked with aria-describedby; invalid controls expose aria-invalid. Creation moves focus to the plan heading, mutation rerenders restore the active control, and deletion uses a native dialog. A polite status live region and aria-busy expose asynchronous states.

CSS provides visible focus rings, at least 44px control targets, rem-based responsive layout, high-contrast light/dark palettes, a reduced-motion override and bounded table scrolling. System fonts and local CSS require no downloads. Browser/assistive-technology behavior can vary; the native accessibility tree is used for landmark/control/live-region sanity checks.

## Assumptions

Budget percentages, vendor lists and timelines are general-purpose heuristics, not vendor quotes. Expenses use the plan's single currency; no conversion, taxes or currency-specific subunit rules are inferred. All four supported currencies use two decimals.

Identity is an anonymous bearer cookie, not an account. Clearing it loses access; another device cannot recover that identity. No authentication, sharing or account recovery is implied.

In-memory storage means a Render free-tier sleep or process restart clears plans. Run one worker. The exact one-file extension path is to replace the implementation in `backend/app/repositories/memory.py` while preserving its `InMemoryPlanRepository` constructor and PlanRepository methods; dependency wiring then stays unchanged. A persistent implementation must preserve owner scope, detached data and atomic mutation semantics; it is not included.

Ideas are creative suggestions, not guarantees. Enter only preferences you are comfortable sending to the Gemini Developer API. Google AI Studio associates its API keys with a project; this application provisions no GCP infrastructure and requires no billing integration.

## Limitations

No durable storage, authentication, real vendor search, payment, calendar sync or invitation delivery. The 500-entry cache and rate limiter are process-local; simultaneous requests for an uncached focus can generate twice. Per-owner caps do not impose a global storage quota. A server-side cap rejects creation of further plans even if a browser has old sidebar state. Existing plans retain their original generated schedule as days pass; overdue/readiness are recomputed on reads. Cached ideas can be up to 30 minutes old; refresh gets current computed countdown facts. AI needs a valid key, model access and available quota; missing keys leave planning usable and fail only when ideas are requested. Live Gemini quality is not certified by offline tests.

Festiva provides planning assistance and indicative estimates only. Confirm prices, feasibility, permits, accessibility and safety arrangements with appropriate providers.

## Local setup

Install Python 3.11, then from this repository root:

```sh
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp -n .env.example .env
```

Your local key belongs in backend/.env; an existing .env is preserved. Replace the placeholder value there if you want ideas. Run the following command from backend/. The application reads process environment variables; Uvicorn explicitly loads the local file:

```sh
uvicorn app.main:app --reload --env-file .env
```

Alternatively use `make -C backend dev` from the repository root. The dev target loads backend/.env when present; you can also export GEMINI_API_KEY in your shell. Open http://127.0.0.1:8000; API documentation is at /docs. `make -C backend dev` works without a key for every deterministic planning feature. Configuration also accepts ENV (production by default) and LOG_LEVEL (INFO by default). Python-dotenv is supplied by uvicorn[standard] for the optional CLI env-file loading, not by application startup.

## Deploy to Render

Deployment has not been performed. The supplied blueprint targets a free Python web service with no database or paid infrastructure. Create a public GitHub repository from this directory and push main yourself.

**Blueprint:** Render Dashboard → New → Blueprint → connect that repository → select main and render.yaml → supply GEMINI_API_KEY when prompted → create the service. The blueprint specifies Python 3.11.9, installs runtime requirements, binds $PORT, and checks /health. Follow [Render's Blueprint reference](https://render.com/docs/blueprint-spec) for the current dashboard flow.

**Manual alternative:** Leave Root Directory blank so both folders are included. New → Web Service → connect the repository → runtime Python, branch main, free instance → build `pip install -r backend/requirements.txt` → start `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT` → health check /health → environment PYTHON_VERSION=3.11.9 and GEMINI_API_KEY → deploy. This follows [Render's FastAPI guide](https://render.com/docs/deploy-fastapi). Use the [environment settings](https://render.com/docs/configure-environment-variables) to set the secret; never commit it.

Obtain a Gemini Developer API key through [Google AI Studio](https://aistudio.google.com/apikey). Availability and quotas depend on the account/region/model; consult [Google's key guide](https://ai.google.dev/gemini-api/docs/api-key). Use an eligible free-tier key without enabling paid billing. Once Render reports healthy, visit its assigned HTTPS URL, create a plan, request ideas, and replace the live-demo marker at the top of this README with that URL. Commit the README change and push it yourself. Render restarts discard in-memory data.

## Docker (optional alternative)

```sh
docker build -f backend/Dockerfile -t festiva .
docker run --rm -p 8000:8000 --env-file backend/.env festiva
```

The image uses python:3.11-slim, installs dependencies before source, runs as user festiva, honors PORT and checks /health with Python's standard library. Docker execution requires Docker locally and is independent of the Render Python blueprint.

## Project layout

The two application folders are frontend/ and backend/. Shared repository metadata and the Render blueprint stay at the root. Backend modules and tests retain their internal structure; the backend serves frontend/ at the existing same-origin URLs.

```text
frontend/
  index.html
  css/style.css
  js/             main.js api.js dom.js state.js
    render/       plans.js budget.js timeline.js vendors.js ideas.js
backend/
  app/
    __init__.py main.py config.py settings.py exceptions.py
    models/       enums.py domain.py requests.py responses.py
    services/     planner_engine.py plan_service.py ideas_service.py
                  ai_client.py prompts.py sanitize.py cache.py
    repositories/ base.py memory.py
    api/          dependencies.py limiter.py middleware.py
      routers/    meta.py plans.py budget.py timeline.py vendors.py ideas.py
  tests/          conftest.py and focused engine/cache/API/security tests
  pyproject.toml requirements.txt requirements-dev.txt Makefile Dockerfile
  .env.example .env (local, ignored) .venv (local, ignored)
README.md render.yaml .gitignore .dockerignore
```
