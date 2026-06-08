"""GenPal Question Bank Factory — Streamlit prototype entry point."""

from __future__ import annotations

import streamlit as st

from services import config, genpal, plan


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


def _render_header() -> None:
    st.title("GenPal Question Bank Factory - Prototype")
    st.caption("AI-assisted question bank generation for GenPal-ready Excel output.")
    st.markdown(
        "**How it works**\n"
        "1. Enter question bank input\n"
        "2. Generate and validate questions\n"
        "3. Download GenPal-ready Excel"
    )
    if config.use_mock_data():
        st.info("Mock Mode is enabled. No OpenAI API calls will be made.")
    else:
        st.success(
            "Real API Mode is enabled. OpenAI API calls will be used for "
            "generation and embeddings."
        )


def _render_mode_and_levels() -> tuple[str, list[str]]:
    mode = st.radio(
        "Generation Mode",
        options=plan.GENERATION_MODES,
        index=0,
        key="genpal_mode",
    )

    if mode == plan.FULL_MODE:
        st.info(
            "Full GenPal Mode will generate all 7 career levels with 252 total questions."
        )
        st.multiselect(
            "Career Levels",
            options=plan.CAREER_LEVELS,
            default=list(plan.CAREER_LEVELS),
            disabled=True,
            key="genpal_levels_full",
        )
        levels = list(plan.CAREER_LEVELS)
    else:
        levels = st.multiselect(
            "Career Levels",
            options=plan.CAREER_LEVELS,
            default=list(plan.DEFAULT_PROTOTYPE_LEVELS),
            key="genpal_levels_proto",
        )
        if len(levels) > plan.MAX_PROTOTYPE_LEVELS:
            st.warning(
                "Prototype mode supports a maximum of 3 career levels. "
                "Please select up to 3 levels."
            )

    return mode, levels


def _render_input_form() -> tuple[bool, str, str, str]:
    with st.form("genpal_form"):
        skill = st.text_input(
            "Skill Name",
            placeholder="Example: Azure DevOps, Python, Generative AI, Snowflake, SAP ABAP",
        )
        topics_raw = st.text_area(
            "Topic List",
            help="Paste one topic per line.",
            placeholder="Azure Repos\nAzure Pipelines\nAzure Boards\nAzure Artifacts",
            height=160,
        )
        urls_raw = st.text_area(
            "Reference URL List",
            help="Paste one reference URL per line.",
            placeholder=(
                "https://learn.microsoft.com/en-us/azure/devops/repos/\n"
                "https://learn.microsoft.com/en-us/azure/devops/pipelines/\n"
                "https://learn.microsoft.com/en-us/azure/devops/boards/"
            ),
            height=160,
        )
        submitted = st.form_submit_button("Generate Question Bank", type="primary")
    return submitted, skill, topics_raw, urls_raw


def _render_output_panel(mode: str, levels: list[str]) -> None:
    current = plan.build_plan(mode, levels)
    inputs = st.session_state.get("_genpal_inputs")

    st.subheader("Expected Output")
    with st.container(border=True):
        st.markdown(f"**Mode:** {current.mode}")
        st.markdown(
            "**Selected skill:** "
            + (inputs["skill"] if inputs else "—")
        )
        st.markdown(
            "**Number of topics:** "
            + (str(inputs["topic_count"]) if inputs else "—")
        )
        st.markdown(
            "**Number of reference URLs:** "
            + (str(inputs["url_count"]) if inputs else "—")
        )
        st.markdown(
            "**Selected career levels:** "
            + (", ".join(current.levels) if current.levels else "—")
        )
        st.markdown(f"**Questions per level:** {current.per_level}")
        st.markdown(f"**Total expected questions:** {current.total_questions}")
        st.markdown(f"**Excel sheet name:** {current.sheet_name}")
        st.markdown(f"**Output columns:** {current.column_count}")


def _validate(
    mode: str, levels: list[str], skill: str, topics: list[str], urls: list[str]
) -> list[str]:
    errors: list[str] = []

    if not skill.strip():
        errors.append("Please enter a skill name before generation.")

    if not topics:
        errors.append("Please enter at least one topic.")

    if not urls:
        errors.append("Please enter at least one reference URL.")
    elif not all(plan.looks_like_url(u) for u in urls):
        errors.append("URLs should look like valid HTTP/HTTPS links.")

    if mode == plan.PROTOTYPE_MODE:
        if not levels:
            errors.append("Please select at least one career level.")
        elif len(levels) > plan.MAX_PROTOTYPE_LEVELS:
            errors.append(
                "Prototype mode supports a maximum of 3 career levels. "
                "Please select up to 3 levels."
            )

    return errors


def main() -> None:
    st.set_page_config(page_title="GenPal Question Bank Factory", layout="wide")
    _password_gate()
    _render_sidebar_status()

    _render_header()
    st.divider()

    left, right = st.columns([2, 1])
    with left:
        mode, levels = _render_mode_and_levels()
        submitted, skill, topics_raw, urls_raw = _render_input_form()
        status_area = st.container()
    with right:
        panel_area = st.container()

    if submitted:
        topics = plan.parse_lines(topics_raw)
        urls = plan.parse_lines(urls_raw)
        errors = _validate(mode, levels, skill, topics, urls)

        if errors:
            with status_area:
                st.error("Please fix the following before generating:")
                for message in errors:
                    st.warning(message)
        else:
            resolved = plan.build_plan(mode, levels)
            st.session_state["_genpal_inputs"] = {
                "skill": skill.strip(),
                "topics": topics,
                "topic_count": len(topics),
                "urls": urls,
                "url_count": len(urls),
                "mode": resolved.mode,
                "levels": resolved.levels,
                "total_questions": resolved.total_questions,
            }
            with status_area:
                st.success("Ready to generate.")
                _run_generation(skill.strip(), topics, urls, mode, levels)

    with panel_area:
        _render_output_panel(mode, levels)

    _render_results()


def _run_generation(
    skill: str, topics: list[str], urls: list[str], mode: str, levels: list[str]
) -> None:
    progress = st.progress(0.0, text="Generating question bank...")

    def on_progress(done: int, total: int) -> None:
        progress.progress(done / total, text=f"Generating... batch {done} of {total}")

    try:
        records = genpal.generate_question_bank(
            skill, topics, urls, mode, levels, progress_cb=on_progress
        )
    except Exception as exc:  # surface generation/API errors without crashing
        progress.empty()
        st.error(f"Generation failed: {exc}")
        return

    progress.empty()
    st.session_state["_genpal_records"] = records
    st.session_state["_genpal_xlsx"] = genpal.to_xlsx_bytes(records)


def _render_results() -> None:
    records = st.session_state.get("_genpal_records")
    if not records:
        return

    st.divider()
    st.subheader(f"Generated question bank ({len(records)} questions)")
    st.download_button(
        "Download GenPal Excel (.xlsx)",
        data=st.session_state["_genpal_xlsx"],
        file_name="genpal_question_bank.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
    st.caption(f"Sheet: {plan.EXCEL_SHEET_NAME} · Columns: {len(genpal.GENPAL_COLUMNS)}")
    st.dataframe(records[:50], use_container_width=True, hide_index=True)
    if len(records) > 50:
        st.caption(f"Showing first 50 of {len(records)} rows. Download for the full bank.")


if __name__ == "__main__":
    main()
