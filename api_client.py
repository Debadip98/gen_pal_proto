"""Thin httpx API client for GenPal Streamlit frontend.

All calls go to the FastAPI backend. BACKEND_URL defaults to localhost:8000
but can be overridden via the BACKEND_URL environment variable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080").rstrip("/")
API = f"{BACKEND_URL}/api/v1"
TIMEOUT = 600  # seconds — generation can take a while


def _client() -> "httpx.Client":
    if not _HAS_HTTPX:
        raise ImportError("httpx is required. Run: pip install httpx")
    return httpx.Client(timeout=TIMEOUT)


def health_check() -> dict:
    try:
        with _client() as c:
            r = c.get(f"{API}/health")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def create_job(payload: dict) -> dict:
    with _client() as c:
        r = c.post(f"{API}/jobs", json=payload)
        r.raise_for_status()
        return r.json()


def get_job(job_id: str) -> dict:
    with _client() as c:
        r = c.get(f"{API}/jobs/{job_id}")
        r.raise_for_status()
        return r.json()


def start_generation(job_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/jobs/{job_id}/generate")
        r.raise_for_status()
        return r.json()


def get_questions(
    job_id: str,
    *,
    career_level: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    params = {}
    if career_level:
        params["career_level"] = career_level
    if status:
        params["status"] = status
    with _client() as c:
        r = c.get(f"{API}/jobs/{job_id}/questions", params=params)
        r.raise_for_status()
        return r.json()


def discover_docs(job_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/jobs/{job_id}/discover-docs")
        r.raise_for_status()
        return r.json()


def select_docs(job_id: str, selected_source_ids: list[str]) -> dict:
    with _client() as c:
        r = c.post(
            f"{API}/jobs/{job_id}/select-docs",
            json={"selected_source_ids": selected_source_ids},
        )
        r.raise_for_status()
        return r.json()


def send_sme_review(job_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/jobs/{job_id}/send-sme-review")
        r.raise_for_status()
        return r.json()


def get_review_session(review_token: str) -> dict:
    with _client() as c:
        r = c.get(f"{API}/review/{review_token}")
        r.raise_for_status()
        return r.json()


def accept_question(review_token: str, question_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/review/{review_token}/questions/{question_id}/accept")
        r.raise_for_status()
        return r.json()


def reject_question(review_token: str, question_id: str, comment: str = "") -> dict:
    with _client() as c:
        r = c.post(
            f"{API}/review/{review_token}/questions/{question_id}/reject",
            json={"comment": comment},
        )
        r.raise_for_status()
        return r.json()


def get_suggestion(review_token: str, question_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/review/{review_token}/questions/{question_id}/suggestion")
        r.raise_for_status()
        return r.json()


def regenerate_question(
    review_token: str,
    question_id: str,
    sme_feedback: str,
    use_llm_suggestion: bool = False,
) -> dict:
    with _client() as c:
        r = c.post(
            f"{API}/review/{review_token}/questions/{question_id}/regenerate",
            json={"sme_feedback": sme_feedback, "use_llm_suggestion": use_llm_suggestion},
        )
        r.raise_for_status()
        return r.json()


def accept_version(review_token: str, version_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/review/{review_token}/versions/{version_id}/accept")
        r.raise_for_status()
        return r.json()


def reject_version(review_token: str, version_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/review/{review_token}/versions/{version_id}/reject")
        r.raise_for_status()
        return r.json()


def get_dashboard(job_token: str) -> dict:
    with _client() as c:
        r = c.get(f"{API}/dashboard/{job_token}")
        r.raise_for_status()
        return r.json()


def get_notifications(job_token: str) -> dict:
    with _client() as c:
        r = c.get(f"{API}/dashboard/{job_token}/notifications")
        r.raise_for_status()
        return r.json()


def mark_notification_read(job_token: str, notification_id: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/dashboard/{job_token}/notifications/{notification_id}/read")
        r.raise_for_status()
        return r.json()


def mark_all_notifications_read(job_token: str) -> dict:
    with _client() as c:
        r = c.post(f"{API}/dashboard/{job_token}/notifications/read-all")
        r.raise_for_status()
        return r.json()


def get_export_bytes(job_id: str, export_type: str = "draft") -> Optional[bytes]:
    with _client() as c:
        r = c.get(f"{API}/jobs/{job_id}/export", params={"type": export_type})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content


def get_cost_summary(job_id: str) -> dict:
    with _client() as c:
        r = c.get(f"{API}/jobs/{job_id}/cost-summary")
        r.raise_for_status()
        return r.json()


def is_backend_available() -> bool:
    """Check if the FastAPI backend is reachable."""
    try:
        result = health_check()
        return result.get("status") == "ok"
    except Exception:
        return False
