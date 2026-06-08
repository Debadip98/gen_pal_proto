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
_SIMILARITY_THRESHOLD_DEFAULT = 0.88


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


def get_app_password() -> Optional[str]:
    return _get("APP_PASSWORD")


def configure_langsmith() -> bool:
    """Wire LangSmith env vars when tracing is enabled. Returns the enabled flag."""
    if not is_langsmith_tracing_enabled():
        return False
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = get_langsmith_api_key() or ""
    os.environ["LANGCHAIN_PROJECT"] = get_langsmith_project()
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    return True
