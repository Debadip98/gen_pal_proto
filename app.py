"""GenPal Question Bank Factory — Streamlit prototype entry point."""

from __future__ import annotations

import streamlit as st

from services import config, dedup, export, generation, ingest


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
        "Enter a prompt and/or upload source material to generate short-answer questions."
    )

    _render_generation()


def _render_generation() -> None:
    with st.form("generation_form"):
        prompt = st.text_area(
            "Prompt / instructions",
            placeholder="e.g. Generate short-answer questions on the causes of World War I "
            "for a high-school history exam.",
            height=140,
        )
        uploaded = st.file_uploader(
            "Source material (optional)",
            type=list(ingest.SUPPORTED_EXTENSIONS),
            help="Upload a document to ground the questions in its content. "
            "Supported: " + ", ".join("." + e for e in ingest.SUPPORTED_EXTENSIONS),
        )
        col_count, col_difficulty = st.columns(2)
        with col_count:
            count = st.number_input(
                "Number of questions", min_value=1, max_value=50, value=5, step=1
            )
        with col_difficulty:
            difficulty = st.selectbox(
                "Difficulty", options=generation.VALID_DIFFICULTIES, index=1
            )
        submitted = st.form_submit_button("Generate questions")

    if submitted:
        source_text = ""
        if uploaded is not None:
            try:
                source_text = ingest.extract_text(uploaded.name, uploaded.getvalue())
            except Exception as exc:  # surface extraction errors without crashing
                st.error(f"Could not read uploaded file: {exc}")
                return
            if not source_text.strip():
                st.warning("No readable text found in the uploaded file.")
                return

        if not prompt.strip() and not source_text:
            st.warning("Enter a prompt or upload source material before generating.")
            return

        try:
            with st.spinner("Generating questions..."):
                questions = generation.generate_questions(
                    prompt=prompt,
                    count=int(count),
                    difficulty=difficulty,
                    source_text=source_text,
                )
            st.session_state["_genpal_questions"] = [q.to_dict() for q in questions]
            st.session_state["_genpal_grounded"] = bool(source_text)
            st.session_state.pop("_genpal_removed", None)
        except Exception as exc:  # surface generation/API errors without crashing
            st.error(f"Generation failed: {exc}")
            return

    _render_results()


def _render_results() -> None:
    questions = st.session_state.get("_genpal_questions")
    if not questions:
        return

    st.subheader(f"Generated questions ({len(questions)})")
    if st.session_state.get("_genpal_grounded"):
        st.caption("Grounded in uploaded source material.")
    if st.button("Remove duplicates"):
        try:
            with st.spinner("Checking for duplicates..."):
                result = dedup.deduplicate(questions)
            st.session_state["_genpal_questions"] = result.kept
            st.session_state["_genpal_removed"] = result.removed
            st.rerun()
        except Exception as exc:  # surface embedding/API errors without crashing
            st.error(f"Deduplication failed: {exc}")

    col_xlsx, col_csv = st.columns(2)
    with col_xlsx:
        st.download_button(
            "Download Excel (.xlsx)",
            data=export.to_xlsx_bytes(questions),
            file_name="question_bank.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col_csv:
        st.download_button(
            "Download CSV",
            data=export.to_csv_bytes(questions),
            file_name="question_bank.csv",
            mime="text/csv",
        )

    removed = st.session_state.get("_genpal_removed")
    if removed:
        st.info(f"Removed {len(removed)} duplicate question(s).")
        with st.expander("Show removed duplicates"):
            for q in removed:
                st.markdown(f"- {q['question']}")

    for i, q in enumerate(questions, start=1):
        with st.expander(f"Q{i}. {q['question']}"):
            st.markdown(f"**Answer:** {q['answer']}")
            st.caption(f"Difficulty: {q['difficulty']}")


if __name__ == "__main__":
    main()
