"""GenPal Question Bank Factory — Streamlit prototype entry point."""

from __future__ import annotations

import streamlit as st

from services import config


def _password_gate() -> None:
    expected = config.get_app_password()
    if not expected:
        return

    if st.session_state.get("_genpal_authed"):
        return

    st.markdown("### GenPal Question Bank Factory")
    entered = st.text_input("Prototype access password", type="password")
    if not entered:
        st.stop()
    if entered != expected:
        st.warning("Incorrect password.")
        st.stop()
    st.session_state["_genpal_authed"] = True
    st.rerun()


def _render_sidebar_status() -> None:
    if "_genpal_langsmith_configured" not in st.session_state:
        st.session_state["_genpal_langsmith_configured"] = config.configure_langsmith()

    with st.sidebar:
        st.subheader("Status")
        if st.session_state["_genpal_langsmith_configured"]:
            st.success("LangSmith tracing enabled")
        else:
            st.info("LangSmith tracing not configured")

        if config.use_mock_data():
            st.info("Mock mode: OpenAI calls disabled")
        else:
            st.success("OpenAI configured")


def _require_openai_or_mock() -> None:
    if config.use_mock_data():
        return
    if not config.get_openai_api_key():
        st.error(
            "OPENAI_API_KEY is not configured. Set it in .env or Streamlit secrets, "
            "or set USE_MOCK_DATA=true to run in mock mode."
        )
        st.stop()


def main() -> None:
    st.set_page_config(page_title="GenPal Question Bank Factory", layout="wide")
    _password_gate()
    _render_sidebar_status()
    _require_openai_or_mock()

    st.title("GenPal Question Bank Factory")
    st.write(
        "Streamlit prototype for generating, deduplicating, and exporting question banks. "
        "Upload flows and generation controls will plug into this skeleton."
    )


if __name__ == "__main__":
    main()
