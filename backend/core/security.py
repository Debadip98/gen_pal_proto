"""Token generation and validation for GenPal prototype security.

Both job_token and review_token use URL-safe random tokens. No JWT, no
signatures — adequate for a prototype with token-based access control.
"""

from __future__ import annotations

import secrets


def generate_job_token() -> str:
    """Generate a stable requestor dashboard token (never expires)."""
    return secrets.token_urlsafe(32)


def generate_review_token() -> str:
    """Generate a time-limited SME review token (expires per config)."""
    return secrets.token_urlsafe(32)


def generate_id() -> str:
    """Generate a unique identifier for DB primary keys."""
    return secrets.token_hex(16)
