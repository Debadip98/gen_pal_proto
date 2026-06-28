"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from backend.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
