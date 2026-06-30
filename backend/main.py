"""GenPal FastAPI backend entry point.

Start with:
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

The static frontend is served by Apache HTTPD on http://localhost:8080,
which reverse-proxies /api/* to this backend. See deploy/apache/.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# When served through the Apache reverse proxy the browser calls the same
# origin (/api/...), so CORS does not apply. These origins only matter for
# direct-to-backend testing during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://127.0.0.1",
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


@app.get("/")
def root():
    return {"message": "GenPal API is running. See /docs for API documentation."}
