"""GenPal FastAPI backend entry point.

Local demo — one process serves BOTH the API and the static frontend:
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

Then open http://127.0.0.1:8000  (API under /api/v1).

Because the frontend is served from the same origin and calls relative
/api/v1 paths, there is no reverse proxy and no cross-origin/connection-refused
class of errors. Apache (deploy/apache/) remains an OPTIONAL alternative.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import (
    routes_docs,
    routes_export,
    routes_health,
    routes_jobs,
    routes_notifications,
    routes_review,
)
from backend.core.config import configure_langsmith
from backend.db.init_db import init_db

app = FastAPI(
    title="GenPal Question Bank Factory API",
    description="FastAPI backend for AI-assisted GenPal question bank generation.",
    version="1.0.0",
)

# The frontend is served from the same origin as the API, so CORS is moot for
# the demo. These origins only matter if you call the API from a separate dev
# server or the optional Apache host.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(routes_health.router, prefix=API_PREFIX)
app.include_router(routes_jobs.router, prefix=API_PREFIX)
app.include_router(routes_review.router, prefix=API_PREFIX)
app.include_router(routes_export.router, prefix=API_PREFIX)
app.include_router(routes_notifications.router, prefix=API_PREFIX)
app.include_router(routes_docs.router, prefix=API_PREFIX)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    configure_langsmith()


# --- Static frontend (mounted LAST so /api/v1 routes take precedence) --------
# Serves index.html at "/" and all assets (css/, js/, assets/). The SPA uses
# hash routing, so the server only needs to serve "/" plus static files.
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
else:  # pragma: no cover - safety net if frontend is missing
    @app.get("/")
    def _no_frontend():
        return {
            "message": "GenPal API is running, but frontend/public was not found.",
            "api_docs": "/docs",
            "health": "/api/v1/health",
        }
