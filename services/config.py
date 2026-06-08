"""Configuration helper for the GenPal Streamlit prototype.

Resolution order for every key:
    1. ``st.secrets`` (Streamlit Cloud)
    2. environment variable (``.env`` is loaded via python-dotenv)
    3. a hard-coded safe default

Secrets are never printed, logged, or rendered to the UI.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=False)

try:
    import streamlit as st  # type: ignore
except Exception:  # pragma: no cover - streamlit always available in prototype
    st = None  # type: ignore


_GENERATION_MODEL_DEFAULT = "gpt-4o"
_EMBEDDING_MODEL_DEFAULT = "text-embedding-3-small"
_LANGSMITH_PROJECT_DEFAULT = "genpal-prototype"
_SIMILARITY_THRESHOLD_DEFAULT = 0.85
_MAX_REGEN_ATTEMPTS_DEFAULT = 3

# --- Final global duplicate repair tunables ---------------------------------
# These bound the post-merge 280-row repair so it can never loop forever.
MAX_GLOBAL_DUPLICATE_REPAIR_PASSES_DEFAULT = 2
MAX_GLOBAL_REWORK_ATTEMPTS_PER_ROW_DEFAULT = 2
MAX_GLOBAL_REWORK_ROWS_PER_PASS_DEFAULT = 15
MIN_IMPROVEMENT_DELTA_DEFAULT = 0.01


def _from_secrets(key: str) -> Optional[str]:
    if st is None:
        return None
    try:
        if key in st.secrets:
            value = st.secrets[key]
            return str(value) if value is not None else None
    except Exception:
        # st.secrets raises when no secrets.toml is present locally.
        return None
    return None


def _get(key: str, default: Optional[str] = None) -> Optional[str]:
    value = _from_secrets(key)
    if value is not None and value != "":
        return value
    env_value = os.getenv(key)
    if env_value is not None and env_value != "":
        return env_value
    return default


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"true", "1", "yes", "y", "on"}


def get_openai_api_key() -> Optional[str]:
    return _get("OPENAI_API_KEY")


def get_openai_generation_model() -> str:
    return _get("OPENAI_GENERATION_MODEL", _GENERATION_MODEL_DEFAULT) or _GENERATION_MODEL_DEFAULT


def get_openai_embedding_model() -> str:
    return _get("OPENAI_EMBEDDING_MODEL", _EMBEDDING_MODEL_DEFAULT) or _EMBEDDING_MODEL_DEFAULT


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
    raw = _get("DUPLICATE_SIMILARITY_THRESHOLD")
    if raw is None:
        return _SIMILARITY_THRESHOLD_DEFAULT
    try:
        return float(raw)
    except ValueError:
        return _SIMILARITY_THRESHOLD_DEFAULT


def get_max_regeneration_attempts() -> int:
    """How many times a career level may be auto-regenerated to clear duplicates.

    Counts regeneration retries only; the initial generation is always free.
    The run blocks (and shows the manual-resolve message) only after these
    retries are exhausted.
    """
    raw = _get("MAX_REGENERATION_ATTEMPTS")
    if raw is None:
        return _MAX_REGEN_ATTEMPTS_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        return _MAX_REGEN_ATTEMPTS_DEFAULT
    return value if value >= 0 else _MAX_REGEN_ATTEMPTS_DEFAULT


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


def get_max_global_duplicate_repair_passes() -> int:
    return _get_int(
        "MAX_GLOBAL_DUPLICATE_REPAIR_PASSES",
        MAX_GLOBAL_DUPLICATE_REPAIR_PASSES_DEFAULT,
        minimum=0,
    )


def get_max_global_rework_attempts_per_row() -> int:
    return _get_int(
        "MAX_GLOBAL_REWORK_ATTEMPTS_PER_ROW",
        MAX_GLOBAL_REWORK_ATTEMPTS_PER_ROW_DEFAULT,
        minimum=1,
    )


def get_max_global_rework_rows_per_pass() -> int:
    return _get_int(
        "MAX_GLOBAL_REWORK_ROWS_PER_PASS",
        MAX_GLOBAL_REWORK_ROWS_PER_PASS_DEFAULT,
        minimum=1,
    )


def get_min_improvement_delta() -> float:
    return _get_float("MIN_IMPROVEMENT_DELTA", MIN_IMPROVEMENT_DELTA_DEFAULT)


def get_app_password() -> Optional[str]:
    return _get("APP_PASSWORD")


def configure_langsmith() -> bool:
    """Wire LangSmith env vars when tracing is enabled. Returns the enabled flag.

    On Streamlit Cloud the values live in ``st.secrets`` (not ``os.environ``),
    so we copy them into ``os.environ`` here. Both the modern ``LANGSMITH_*``
    and the legacy ``LANGCHAIN_*`` names are set because the langsmith SDK reads
    whichever it finds first.

    Critically, langsmith caches env-var reads (``get_env_var`` is lru_cached).
    If the SDK read these vars before this function ran — which happens at
    import time when only ``st.secrets`` is populated — it cached "tracing
    disabled" and would ignore the values we set above. We clear that cache so
    the new values actually take effect and the pipeline shows up in LangSmith.
    """
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
    except Exception:  # never block the app if the SDK internals change
        pass
    return True
