"""Initialize the SQLite database by creating all tables."""

from __future__ import annotations

from backend.db.database import Base, engine
from backend.db import models  # noqa: F401 — registers all ORM models with Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
