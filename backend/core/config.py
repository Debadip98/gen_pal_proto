"""Configuration helper for the GenPal FastAPI backend.

Resolution order for every key:
    1. Environment variable (.env loaded via python-dotenv)
    2. Hard-coded safe default

Secrets are never printed, logged, or returned in API responses.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=False)

_GENERATION_MODEL_DEFAULT = "gpt-4o"
_EMBEDDING_MODEL_DEFAULT = "text-embedding-3-small"
_REVIEW_MODEL_DEFAULT = "gpt-4o"
_LANGSMITH_PROJECT_DEFAULT = "genpal-prototype"
_SIMILARITY_THRESHOLD_DEFAULT = 0.85
_FUZZY_THRESHOLD_DEFAULT = 90
_MAX_REGEN_ATTEMPTS_DEFAULT = 3
_REVIEW_TOKEN_EXPIRY_HOURS_DEFAULT = 72

MAX_GLOBAL_DUPLICATE_REPAIR_PASSES_DEFAULT = 2
MAX_GLOBAL_REWORK_ATTEMPTS_PER_ROW_DEFAULT = 2
MAX_GLOBAL_REWORK_ROWS_PER_PASS_DEFAULT = 15
MIN_IMPROVEMENT_DELTA_DEFAULT = 0.01
MAX_CANDIDATE_ROUNDS_PER_BATCH_DEFAULT = 3


def _get(key: str, default: Optional[str] = None) -> Optional[str]:
    env_value = os.getenv(key)
    if env_value is not None and env_value != "":
        return env_value
    return default


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def _get_int(key: str, default: int, *, minimum: int = 0) -> int:
    raw = _get(key)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= minimum else default


def _get_float(key: str, default: float) -> float:
    raw = _get(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def get_openai_api_key() -> Optional[str]:
    return _get("OPENAI_API_KEY")


def get_openai_generation_model() -> str:
    return _get("OPENAI_GENERATION_MODEL", _GENERATION_MODEL_DEFAULT) or _GENERATION_MODEL_DEFAULT


def get_openai_embedding_model() -> str:
    return _get("OPENAI_EMBEDDING_MODEL", _EMBEDDING_MODEL_DEFAULT) or _EMBEDDING_MODEL_DEFAULT


def get_openai_review_model() -> str:
    return _get("OPENAI_REVIEW_MODEL", _REVIEW_MODEL_DEFAULT) or _REVIEW_MODEL_DEFAULT


def get_langsmith_api_key() -> Optional[str]:
    return _get("LANGSMITH_API_KEY")


def get_langsmith_project() -> str:
    return _get("LANGSMITH_PROJECT", _LANGSMITH_PROJECT_DEFAULT) or _LANGSMITH_PROJECT_DEFAULT


def is_langsmith_tracing_enabled() -> bool:
    if not get_langsmith_api_key():
        return False
    return _as_bool(_get("LANGSMITH_TRACING"), default=False)


def use_mock_data() -> bool:
    raw = _get("USE_MOCK_DATA")
    if raw is None:
        return get_openai_api_key() is None
    return _as_bool(raw, default=False)


def get_duplicate_similarity_threshold() -> float:
    return _get_float("DUPLICATE_SIMILARITY_THRESHOLD", _SIMILARITY_THRESHOLD_DEFAULT)


def get_fuzzy_duplicate_threshold() -> int:
    return _get_int("FUZZY_DUPLICATE_THRESHOLD", _FUZZY_THRESHOLD_DEFAULT, minimum=0)


def get_max_regeneration_attempts() -> int:
    raw = _get("MAX_REGENERATION_ATTEMPTS")
    if raw is None:
        return _MAX_REGEN_ATTEMPTS_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        return _MAX_REGEN_ATTEMPTS_DEFAULT
    return value if value >= 0 else _MAX_REGEN_ATTEMPTS_DEFAULT


def get_max_candidate_rounds_per_batch() -> int:
    return _get_int(
        "MAX_CANDIDATE_ROUNDS_PER_BATCH",
        MAX_CANDIDATE_ROUNDS_PER_BATCH_DEFAULT,
        minimum=1,
    )


def get_max_duplicate_passes_per_level() -> int:
    return _get_int(
        "MAX_DUPLICATE_PASSES_PER_LEVEL",
        _MAX_REGEN_ATTEMPTS_DEFAULT,
        minimum=0,
    )


def get_max_rework_attempts_per_row() -> int:
    return _get_int(
        "MAX_REWORK_ATTEMPTS_PER_ROW",
        MAX_GLOBAL_REWORK_ATTEMPTS_PER_ROW_DEFAULT,
        minimum=1,
    )


def get_max_final_duplicate_repair_passes() -> int:
    return _get_int(
        "MAX_FINAL_DUPLICATE_REPAIR_PASSES",
        MAX_GLOBAL_DUPLICATE_REPAIR_PASSES_DEFAULT,
        minimum=0,
    )


def get_max_final_rework_attempts_per_row() -> int:
    return _get_int(
        "MAX_FINAL_REWORK_ATTEMPTS_PER_ROW",
        MAX_GLOBAL_REWORK_ATTEMPTS_PER_ROW_DEFAULT,
        minimum=1,
    )


def get_max_global_duplicate_repair_passes() -> int:
    return get_max_final_duplicate_repair_passes()


def get_max_global_rework_attempts_per_row() -> int:
    return get_max_final_rework_attempts_per_row()


def get_max_global_rework_rows_per_pass() -> int:
    return _get_int(
        "MAX_GLOBAL_REWORK_ROWS_PER_PASS",
        MAX_GLOBAL_REWORK_ROWS_PER_PASS_DEFAULT,
        minimum=1,
    )


def get_min_improvement_delta() -> float:
    return _get_float("MIN_IMPROVEMENT_DELTA", MIN_IMPROVEMENT_DELTA_DEFAULT)


def get_review_token_expiry_hours() -> int:
    return _get_int(
        "REVIEW_TOKEN_EXPIRY_HOURS",
        _REVIEW_TOKEN_EXPIRY_HOURS_DEFAULT,
        minimum=1,
    )


def get_database_url() -> str:
    url = _get("DATABASE_URL", "sqlite:///./genpal_prototype.db") or "sqlite:///./genpal_prototype.db"
    # Railway provides postgres:// which SQLAlchemy 1.4+ requires as postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def get_app_base_url() -> str:
    return _get("APP_BASE_URL", "http://localhost:8501") or "http://localhost:8501"


def get_backend_url() -> str:
    return _get("BACKEND_URL", "http://localhost:8000") or "http://localhost:8000"


def get_email_provider() -> str:
    return (_get("EMAIL_PROVIDER") or "").lower()


def get_smtp_host() -> Optional[str]:
    return _get("SMTP_HOST")


def get_smtp_port() -> int:
    return _get_int("SMTP_PORT", 587, minimum=1)


def get_smtp_username() -> Optional[str]:
    # Accept both SMTP_USER (legacy .env) and SMTP_USERNAME
    return _get("SMTP_USER") or _get("SMTP_USERNAME")


def get_smtp_password() -> Optional[str]:
    return _get("SMTP_PASSWORD")


def get_email_from() -> Optional[str]:
    return _get("EMAIL_FROM")


def get_sendgrid_api_key() -> Optional[str]:
    return _get("SENDGRID_API_KEY")


def get_sendgrid_from_email() -> Optional[str]:
    return _get("SENDGRID_FROM_EMAIL")


def is_email_configured() -> bool:
    provider = get_email_provider()
    if provider == "smtp":
        return bool(get_smtp_host() and get_smtp_username())
    if provider == "sendgrid":
        return bool(get_sendgrid_api_key())
    return False


def is_openai_web_search_enabled() -> bool:
    return _as_bool(_get("ENABLE_OPENAI_WEB_SEARCH"), default=False)


def get_openai_generation_input_price_per_1m() -> float:
    return _get_float("OPENAI_GENERATION_INPUT_PRICE_PER_1M", 2.50)


def get_openai_generation_output_price_per_1m() -> float:
    return _get_float("OPENAI_GENERATION_OUTPUT_PRICE_PER_1M", 10.00)


def get_openai_embedding_price_per_1m() -> float:
    return _get_float("OPENAI_EMBEDDING_PRICE_PER_1M", 0.02)


def configure_langsmith() -> bool:
    """Wire LangSmith env vars when tracing is enabled. Returns the enabled flag."""
    if not is_langsmith_tracing_enabled():
        return False
    api_key = get_langsmith_api_key() or ""
    project = get_langsmith_project()
    endpoint = "https://api.smith.langchain.com"
    for prefix in ("LANGSMITH", "LANGCHAIN"):
        os.environ[f"{prefix}_TRACING"] = "true"
        os.environ[f"{prefix}_TRACING_V2"] = "true"
        os.environ[f"{prefix}_API_KEY"] = api_key
        os.environ[f"{prefix}_PROJECT"] = project
        os.environ.setdefault(f"{prefix}_ENDPOINT", endpoint)
    try:
        from langsmith import utils as _ls_utils
        _ls_utils.get_env_var.cache_clear()
    except Exception:
        pass
    return True
