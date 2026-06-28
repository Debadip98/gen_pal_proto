"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from backend.core import config

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "mock_mode": config.use_mock_data(),
        "langsmith_tracing": config.is_langsmith_tracing_enabled(),
        "email_configured": config.is_email_configured(),
    }
